# 每日 AI 资讯聚合

每天自动抓取前一天全网 RSS 中三大主题的最新资讯，生成静态网页浏览：

- **AI 产品应用** — 通用 AI 产品 / 大模型 / 应用落地
- **AI 医疗健康产品** — 医疗 AI 产品、公司、监管
- **AI 医疗健康研究** — 论文、临床研究、arXiv 相关

## 目录结构

```
.
├── .github/workflows/daily.yml   # GitHub Actions 定时任务（北京 08:30）
├── scripts/
│   ├── sources.py                # RSS 源清单 + 分类规则
│   ├── fetch_news.py             # 抓取 & 分类 & 去重 & 写 JSON
│   └── summarize.py              # 可选：LLM 摘要
├── data/
│   ├── latest.json               # 前端读这个
│   └── YYYY-MM-DD.json           # 每日归档
├── index.html                    # 前端（单页，Tailwind CDN）
└── requirements.txt
```

## 本地运行

```bash
pip install -r requirements.txt
python scripts/fetch_news.py            # 抓昨天
python scripts/fetch_news.py --days 3   # 想看更多可扩窗口
python -m http.server 8080              # 浏览器打开 http://localhost:8080
```

## 部署到 GitHub Pages

1. 新建 GitHub 仓库，推送本项目。
2. Repo → **Settings → Pages → Source: GitHub Actions**。
3. Repo → **Settings → Actions → General → Workflow permissions**：勾选 *Read and write permissions*。
4. 首次可在 Actions 页手动 **Run workflow**，此后每天 UTC 00:30（北京 08:30）自动运行。

## 可选：启用 LLM 中文摘要

若 RSS 自带的 description 太短，会调用 LLM 生成中文摘要。在 Repo → **Settings → Secrets and variables → Actions** 添加：

- `OPENAI_API_KEY` — 必需
- `OPENAI_BASE_URL` — 可选（默认 `https://api.openai.com/v1`；国内可换成兼容 OpenAI 协议的其他厂商）
- `OPENAI_MODEL` — 可选（默认 `gpt-4o-mini`）

不设也能正常工作，只是摘要短的条目会退化为使用标题。

## 定制来源

编辑 `scripts/sources.py` 的 `FEEDS` 列表即可增删源。每条包含：

```python
{"url": "...", "name": "显示名", "category": "ai_product|ai_health_product|ai_health_research", "lang": "zh|en"}
```

- 通用 AI 源里如果条目命中 `HEALTH_KEYWORDS`，会自动晋升到"AI 医疗健康产品"分类。
- arXiv 通用类目会用 `ARXIV_HEALTH_KEYWORDS` 过滤，只保留医疗相关论文。
