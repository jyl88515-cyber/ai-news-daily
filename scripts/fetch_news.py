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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import feedparser
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import (  # noqa: E402
    FEEDS,
    CATEGORY_LABELS,
    is_health_topic,
    is_arxiv_health,
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
    """返回最终分类；返回 None 表示丢弃。"""
    cat = feed_meta["category"]
    text = f"{item['title']} {item['summary']}"

    # arXiv 通用类目 -> 只保留医疗相关的
    if "arxiv" in feed_meta["url"]:
        if is_arxiv_health(text):
            return "ai_health_research"
        return None

    # 通用 AI 源里如果强医疗信号，晋升到 health_product
    if cat == "ai_product" and is_health_topic(text):
        return "ai_health_product"

    return cat


def run(days: int) -> dict:
    now_cst = datetime.now(CST)
    # 目标窗口：昨天 00:00 到 今天 00:00 (CST)
    today_start = now_cst.replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = today_start - timedelta(days=days)
    window_end = today_start

    print(f"Window (CST): {window_start.isoformat()} ~ {window_end.isoformat()}")
    print(f"LLM summary: {'ON' if summarize.enabled() else 'off'}")

    buckets: dict[str, list[dict]] = {k: [] for k in CATEGORY_LABELS}
    seen: set[str] = set()

    for meta in FEEDS:
        print(f"[feed] {meta['name']}  ({meta['url']})")
        parsed = fetch_feed(meta["url"])
        if not parsed or not parsed.entries:
            continue

        kept = 0
        for e in parsed.entries:
            pub = entry_time(e)
            if not pub:
                continue
            pub_cst = pub.astimezone(CST)
            if pub_cst < window_start or pub_cst >= window_end:
                continue

            item = build_item(e, meta, pub)
            if not item["link"]:
                continue
            if item["id"] in seen:
                continue

            final_cat = classify(item, meta)
            if not final_cat:
                continue

            seen.add(item["id"])
            item["category"] = final_cat
            buckets[final_cat].append(item)
            kept += 1
        print(f"   kept {kept}")

    # 每类按时间倒序
    for k in buckets:
        buckets[k].sort(key=lambda x: x["published_ts"], reverse=True)

    return {
        "generated_at": now_cst.isoformat(timespec="minutes"),
        "window_start": window_start.isoformat(timespec="minutes"),
        "window_end": window_end.isoformat(timespec="minutes"),
        "category_labels": CATEGORY_LABELS,
        "counts": {k: len(v) for k, v in buckets.items()},
        "items": buckets,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=1,
                    help="窗口向前展开的天数（默认 1 = 昨天）")
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
