"""每日抓取 AI 资讯并写入 data/latest.json + data/YYYY-MM-DD.json。

运行：
    python scripts/fetch_news.py

窗口默认为 "昨天 00:00 (Asia/Shanghai) 至 今天 00:00"，可通过 --days N 扩大。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import feedparser
import requests

try:
    from googlenewsdecoder import gnewsdecoder  # type: ignore
except Exception:
    gnewsdecoder = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import (  # noqa: E402
    FEEDS,
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    EXTENDED_WINDOW_CATS,
    is_ai_topic,
    is_health_topic,
    is_gov,
    is_hospital_head,
    is_funding,
    is_bidding,
    is_competitor,
)
import summarize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

CST = timezone(timedelta(hours=8))  # Asia/Shanghai
UA = "Mozilla/5.0 (compatible; ai-news-aggregator/1.0)"

HTML_TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def clean_text(s: str) -> str:
    if not s:
        return ""
    s = html.unescape(HTML_TAG.sub(" ", s))
    return WS.sub(" ", s).strip()


def normalize_url(u: str) -> str:
    try:
        parts = urlsplit(u)
        # 去掉常见 utm 参数
        query = "&".join(
            p for p in parts.query.split("&")
            if p and not p.lower().startswith(("utm_", "ref=", "ref_"))
        )
        return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), query, ""))
    except Exception:
        return u


def entry_time(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
            except Exception:
                continue
    return None


def fetch_feed(url: str):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=12)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:
        print(f"  [warn] fetch fail {url}: {e}", file=sys.stderr)
        return None


def resolve_google_links(buckets: dict) -> None:
    """把 Google News 跳转链接解码为真实原文链接。

    带缓存：解码结果写入 data/link_cache.json，下次运行同一条目直接命中缓存。
    带时间预算：单次调用最多花 RESOLVE_BUDGET 秒，超时未解码的条目保持原链接。
    """
    cache_file = DATA_DIR / "link_cache.json"
    cache: dict[str, str] = {}
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    # 分类：命中缓存 & 需要在线解码
    hits: list[dict] = []
    to_decode: list[dict] = []
    for bucket in buckets.values():
        for it in bucket:
            link = it.get("link", "")
            if "news.google.com" not in link:
                continue
            if link in cache:
                it["link"] = cache[link]
                it["id"] = hashlib.md5(it["link"].encode("utf-8")).hexdigest()[:12]
                hits.append(it)
            else:
                to_decode.append(it)

    print(f"Google News links: cache hits={len(hits)}, need online decode={len(to_decode)}")
    if not to_decode or gnewsdecoder is None:
        return

    def _decode(orig_url: str):
        try:
            r = gnewsdecoder(orig_url, interval=1)
            if r.get("status") and r.get("decoded_url"):
                return orig_url, r["decoded_url"]
        except Exception:
            pass
        return orig_url, None

    RESOLVE_BUDGET = 240  # 秒；剩余未完成的直接放弃，下次再解
    t0 = time.time()
    ok = 0
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_decode, it["link"]): it for it in to_decode}
        by_url = {it["link"]: it for it in to_decode}
        try:
            for fut in as_completed(futures, timeout=RESOLVE_BUDGET):
                orig, real = fut.result()
                if real:
                    it = by_url.get(orig)
                    if it:
                        cache[orig] = real
                        it["link"] = real
                        it["id"] = hashlib.md5(real.encode("utf-8")).hexdigest()[:12]
                        ok += 1
        except TimeoutError:
            print(f"  [warn] decode budget {RESOLVE_BUDGET}s exhausted, remaining fall back to Google News URLs")
            for fut in futures:
                fut.cancel()

    print(f"  decoded {ok}/{len(to_decode)} in {time.time() - t0:.1f}s (cache now {len(cache)} entries)")

    # 限制缓存大小
    if len(cache) > 5000:
        cache = dict(list(cache.items())[-5000:])
    cache_file.write_text(
        json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8"
    )


def build_item(entry, feed_meta, pub_dt: datetime) -> dict:
    title = clean_text(entry.get("title", "")) or "(无标题)"
    link = normalize_url(entry.get("link", ""))
    raw_summary = entry.get("summary") or entry.get("description") or ""
    if not raw_summary and entry.get("content"):
        try:
            raw_summary = entry["content"][0].get("value", "")
        except Exception:
            raw_summary = ""
    summary = clean_text(raw_summary)

    # 摘要策略：原生够长直接截断；否则 LLM；否则用标题兜底
    if len(summary) >= 80:
        summary = summary[:260] + ("…" if len(summary) > 260 else "")
    elif summarize.enabled():
        llm = summarize.summarize(title, summary or title)
        if llm:
            summary = llm
        elif summary:
            summary = summary[:260]
        else:
            summary = title
    else:
        summary = summary or title

    uid = hashlib.md5(link.encode("utf-8")).hexdigest()[:12] if link else \
          hashlib.md5(title.encode("utf-8")).hexdigest()[:12]

    return {
        "id": uid,
        "title": title,
        "link": link,
        "summary": summary,
        "source": feed_meta["name"],
        "lang": feed_meta.get("lang", "en"),
        "published": pub_dt.astimezone(CST).isoformat(timespec="minutes"),
        "published_ts": int(pub_dt.timestamp()),
    }


def classify(item: dict, feed_meta: dict) -> str | None:
    """按内容关键词判定最终分类；返回 None 表示丢弃。

    优先级：卫健委 > 院长 > 招投标 > 竞品 > 融资 > 产品(兜底)。
    招投标优先于竞品：竞品公司的中标消息更适合放"项目"tab 供统一浏览招投标动态。
    所有条目要求 AI 关键词命中；除卫健委/院长/竞品外，还要求医疗关键词命中。
    """
    text = f"{item['title']} {item['summary']}"

    if not is_ai_topic(text):
        return None

    # 1) 卫健委讲话
    if is_gov(text):
        return "ai_health_gov_speech"

    # 2) 院长讲话
    if is_hospital_head(text):
        return "ai_hospital_speech"

    # 3) 招投标项目（要求医疗上下文）
    if is_bidding(text) and is_health_topic(text):
        return "ai_health_project"

    # 4) 竞品分析（命中任一公司名 或 源本身就是竞品源）
    if is_competitor(text) or feed_meta.get("category") == "competitor_analysis":
        return "competitor_analysis"

    # 其余分类要求医疗关键词命中
    if not is_health_topic(text):
        return None

    # 5) 投融资
    if is_funding(text):
        return "ai_health_funding"

    # 6) 兜底：产品
    return "ai_health_product"


def run(days: int) -> dict:
    now_cst = datetime.now(CST)
    # 窗口：过去 N 天的 00:00 至 今天 00:00 (CST)
    today_start = now_cst.replace(hour=0, minute=0, second=0, microsecond=0)
    window_end = today_start
    default_start = today_start - timedelta(days=days)

    # 每个分类的窗口起点（低频事件用更长窗口）
    cat_windows: dict[str, datetime] = {}
    for cat in CATEGORY_LABELS:
        d = EXTENDED_WINDOW_CATS.get(cat, days)
        cat_windows[cat] = today_start - timedelta(days=max(d, days))
    # 全局最宽窗口（先粗筛条目）
    widest_start = min(cat_windows.values())

    print(f"Default window (CST): {default_start.isoformat()} ~ {window_end.isoformat()}")
    for cat, start in cat_windows.items():
        print(f"  [{cat}] {start.date()} ~ {window_end.date()}")
    print(f"LLM summary: {'ON' if summarize.enabled() else 'off'}")

    buckets: dict[str, list[dict]] = {k: [] for k in CATEGORY_LABELS}
    seen: set[str] = set()

    for meta in FEEDS:
        print(f"[feed] {meta['name']}  ({meta['url'][:80]})")
        parsed = fetch_feed(meta["url"])
        if not parsed or not parsed.entries:
            continue

        kept = 0
        for e in parsed.entries:
            pub = entry_time(e)
            if not pub:
                continue
            pub_cst = pub.astimezone(CST)
            # 先按最宽窗口粗筛
            if pub_cst < widest_start or pub_cst >= window_end:
                continue

            item = build_item(e, meta, pub)
            if not item["link"]:
                continue
            if item["id"] in seen:
                continue

            final_cat = classify(item, meta)
            if not final_cat:
                continue

            # 二次窗口校验：条目必须落在该分类允许的窗口内
            if pub_cst < cat_windows[final_cat]:
                continue

            seen.add(item["id"])
            item["category"] = final_cat
            buckets[final_cat].append(item)
            kept += 1
        print(f"   kept {kept}")

    # 每类按时间倒序
    for k in buckets:
        buckets[k].sort(key=lambda x: x["published_ts"], reverse=True)

    # 解码 Google News 跳转链接为真实原文链接
    resolve_google_links(buckets)

    # 按最终链接再次去重
    for k in buckets:
        seen_links: set[str] = set()
        deduped = []
        for it in buckets[k]:
            if it["link"] in seen_links:
                continue
            seen_links.add(it["link"])
            deduped.append(it)
        buckets[k] = deduped

    return {
        "generated_at": now_cst.isoformat(timespec="minutes"),
        "window_start": default_start.isoformat(timespec="minutes"),
        "window_end": window_end.isoformat(timespec="minutes"),
        "category_labels": CATEGORY_LABELS,
        "category_order": CATEGORY_ORDER,
        "counts": {k: len(buckets[k]) for k in CATEGORY_ORDER},
        "items": {k: buckets[k] for k in CATEGORY_ORDER},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3,
                    help="窗口向前展开的天数（默认 3 = 最近 3 天）")
    args = ap.parse_args()

    result = run(days=args.days)

    date_tag = (datetime.fromisoformat(result["window_start"])).date().isoformat()
    (DATA_DIR / f"{date_tag}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA_DIR / "latest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\nCounts:", result["counts"])
    print(f"Wrote data/{date_tag}.json and data/latest.json")


if __name__ == "__main__":
    main()
