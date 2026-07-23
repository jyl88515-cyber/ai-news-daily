"""可选 LLM 摘要模块。

若环境变量 OPENAI_API_KEY 存在则启用；否则 summarize() 返回 None。
兼容任意 OpenAI 协议端点，默认 OPENAI_BASE_URL=https://api.openai.com/v1，模型=gpt-4o-mini。
"""
from __future__ import annotations

import os
import json
import urllib.request
import urllib.error

_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def enabled() -> bool:
    return bool(_API_KEY)


def summarize(title: str, body: str) -> str | None:
    """把 title+body 压成 ~120 字中文摘要。失败返回 None。"""
    if not _API_KEY:
        return None
    body = (body or "")[:4000]
    prompt = (
        "请用简洁中文（80-140 字）为下面这条资讯写一段摘要，只输出摘要正文，"
        "不要加'摘要：'等前缀，不要编造原文不存在的信息。\n\n"
        f"标题：{title}\n正文：{body}"
    )
    payload = {
        "model": _MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 300,
    }
    req = urllib.request.Request(
        f"{_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        return None
