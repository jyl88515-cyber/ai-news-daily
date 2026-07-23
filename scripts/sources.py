"""RSS 源清单与分类映射（全中文来源版本）。

三大分类：
  - ai_product           AI 产品应用
  - ai_health_product    AI 医疗健康产品应用
  - ai_health_research   AI 医疗健康项目 / 研究

数据源策略：
  * 直接 RSS：机器之心 / InfoQ / 少数派 / IT 之家 / 虎嗅 等主流中文科技媒体
  * Google News RSS 搜索：用中文关键词补充医疗类内容，聚合全网中文新闻
  * rsshub 备用：多个公共实例并列，任一可用即可

分类逻辑：
  * 通用中文 AI 源 → ai_product；若命中医疗关键词 → 晋升为 ai_health_product/research
  * 中文医疗媒体 → 必须命中 AI 关键词才保留；命中"研究"关键词则归入 ai_health_research
"""


def _gnews(q: str) -> str:
    from urllib.parse import quote
    return f"https://news.google.com/rss/search?q={quote(q)}+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"


# 每条：url, name, category(源默认分类), lang, kind(general|medical)
FEEDS = [
    # ---------------- 通用中文 AI 媒体（官方 RSS） ----------------
    {"url": "https://www.jiqizhixin.com/rss",       "name": "机器之心",   "category": "ai_product", "lang": "zh", "kind": "general"},
    {"url": "https://www.infoq.cn/feed.xml",        "name": "InfoQ 中国", "category": "ai_product", "lang": "zh", "kind": "general"},
    {"url": "https://sspai.com/feed",               "name": "少数派",     "category": "ai_product", "lang": "zh", "kind": "general"},
    {"url": "https://www.ithome.com/rss/",          "name": "IT之家",     "category": "ai_product", "lang": "zh", "kind": "general"},
    {"url": "https://www.huxiu.com/rss/0.xml",      "name": "虎嗅网",     "category": "ai_product", "lang": "zh", "kind": "general"},

    # rsshub（多实例并列，允许失败）
    {"url": "https://rsshub.rssforever.com/qbitai",                  "name": "量子位",  "category": "ai_product", "lang": "zh", "kind": "general"},
    {"url": "https://rsshub.rssforever.com/36kr/motif/327686782977", "name": "36氪·AI", "category": "ai_product", "lang": "zh", "kind": "general"},
    {"url": "https://rsshub.app/qbitai",                             "name": "量子位(备)",  "category": "ai_product", "lang": "zh", "kind": "general"},
    {"url": "https://rsshub.app/36kr/motif/327686782977",            "name": "36氪·AI(备)", "category": "ai_product", "lang": "zh", "kind": "general"},

    # ---------------- Google News 中文搜索：AI 产品应用补充 ----------------
    {"url": _gnews("人工智能 产品发布"),  "name": "Google 新闻·AI 产品", "category": "ai_product", "lang": "zh", "kind": "general"},
    {"url": _gnews("大模型 应用"),        "name": "Google 新闻·大模型",  "category": "ai_product", "lang": "zh", "kind": "general"},
    {"url": _gnews("AI 智能体 Agent"),   "name": "Google 新闻·AI Agent", "category": "ai_product", "lang": "zh", "kind": "general"},

    # ---------------- Google News：AI 医疗健康产品 ----------------
    {"url": _gnews("AI 医疗 产品"),       "name": "Google 新闻·AI 医疗产品",     "category": "ai_health_product", "lang": "zh", "kind": "medical"},
    {"url": _gnews("人工智能 医院"),      "name": "Google 新闻·AI 医院应用",     "category": "ai_health_product", "lang": "zh", "kind": "medical"},
    {"url": _gnews("大模型 医疗"),        "name": "Google 新闻·大模型医疗",      "category": "ai_health_product", "lang": "zh", "kind": "medical"},
    {"url": _gnews("AI 医疗器械 获批"),   "name": "Google 新闻·AI 医疗器械",     "category": "ai_health_product", "lang": "zh", "kind": "medical"},
    {"url": _gnews("AI 影像 诊断"),       "name": "Google 新闻·AI 影像诊断",     "category": "ai_health_product", "lang": "zh", "kind": "medical"},

    # ---------------- Google News：AI 医疗健康研究 ----------------
    {"url": _gnews("AI 医学 研究 发表"),  "name": "Google 新闻·AI 医学研究",     "category": "ai_health_research", "lang": "zh", "kind": "medical"},
    {"url": _gnews("人工智能 临床 研究"), "name": "Google 新闻·AI 临床研究",     "category": "ai_health_research", "lang": "zh", "kind": "medical"},
    {"url": _gnews("AI 药物 研发"),       "name": "Google 新闻·AI 药物研发",     "category": "ai_health_research", "lang": "zh", "kind": "medical"},
    {"url": _gnews("AI 医学影像 论文"),   "name": "Google 新闻·AI 医学影像论文", "category": "ai_health_research", "lang": "zh", "kind": "medical"},
]

CATEGORY_LABELS = {
    "ai_product": "AI 产品应用",
    "ai_health_product": "AI 医疗健康产品",
    "ai_health_research": "AI 医疗健康研究",
}

# 医疗关键词
HEALTH_KEYWORDS = [
    "医疗", "医院", "临床", "诊断", "诊疗", "医生", "患者", "病人",
    "药", "制药", "药企", "药物", "药品", "疾病", "肿瘤", "癌症",
    "基因", "健康", "影像", "放射", "病理", "手术", "外科", "内科",
    "生物医药", "生物制药", "医学", "医械", "医疗器械", "FDA", "NMPA",
    "CT", "MRI", "PET", "超声", "X 射线", "X光", "内窥", "内镜",
]

# AI 关键词
AI_KEYWORDS = [
    "AI", "A.I.", "人工智能", "大模型", "大语言模型", "生成式",
    "GPT", "ChatGPT", "LLM", "机器学习", "深度学习", "神经网络",
    "多模态", "智能体", "Agent", "算法模型", "Transformer", "扩散模型",
    "文心", "通义", "豆包", "Kimi", "DeepSeek", "Claude", "Gemini",
    "Sora", "Copilot", "智能诊断", "AI 医生", "AI医生",
]

# 研究关键词（用于把医疗类进一步分流到 research）
RESEARCH_KEYWORDS = [
    "研究", "论文", "试验", "队列", "综述", "meta 分析", "meta-analysis",
    "发表", "期刊", "Nature", "Lancet", "NEJM", "JAMA", "预印本",
    "arXiv", "medRxiv", "bioRxiv", "研究人员", "研究组", "课题组",
    "文献", "回顾性", "前瞻性", "临床试验",
]


def _hit(text: str, keywords) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)


def is_health_topic(text: str) -> bool:
    return _hit(text, HEALTH_KEYWORDS)


def is_ai_topic(text: str) -> bool:
    return _hit(text, AI_KEYWORDS)


def is_research_topic(text: str) -> bool:
    return _hit(text, RESEARCH_KEYWORDS)
