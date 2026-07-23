"""RSS 源清单与分类映射。

三大分类：
  - ai_product      AI 产品应用（通用 AI 产品 / 大模型 / 应用落地）
  - ai_health_product   AI 医疗健康产品应用（医疗 AI 落地、公司、监管）
  - ai_health_research  AI 医疗健康项目 / 研究（论文、临床研究）
"""

# 每条：url, name, category, lang
FEEDS = [
    # ---------------- AI 产品应用 ----------------
    {"url": "https://www.jiqizhixin.com/rss", "name": "机器之心", "category": "ai_product", "lang": "zh"},
    {"url": "https://rsshub.app/qbitai", "name": "量子位", "category": "ai_product", "lang": "zh"},
    {"url": "https://rsshub.app/36kr/motif/327686782977", "name": "36氪·AI", "category": "ai_product", "lang": "zh"},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "name": "The Verge · AI", "category": "ai_product", "lang": "en"},
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "name": "TechCrunch · AI", "category": "ai_product", "lang": "en"},
    {"url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "name": "MIT Tech Review · AI", "category": "ai_product", "lang": "en"},
    {"url": "https://venturebeat.com/category/ai/feed/", "name": "VentureBeat · AI", "category": "ai_product", "lang": "en"},

    # ---------------- AI 医疗健康产品应用 ----------------
    {"url": "https://www.statnews.com/category/health-tech/feed/", "name": "STAT · Health Tech", "category": "ai_health_product", "lang": "en"},
    {"url": "https://www.fiercehealthcare.com/rss/xml", "name": "Fierce Healthcare", "category": "ai_health_product", "lang": "en"},
    {"url": "https://www.mobihealthnews.com/feed", "name": "MobiHealthNews", "category": "ai_health_product", "lang": "en"},
    {"url": "https://www.healthcareitnews.com/home/feed", "name": "Healthcare IT News", "category": "ai_health_product", "lang": "en"},
    {"url": "https://www.beckershospitalreview.com/healthcare-information-technology.feed?type=rss", "name": "Becker's Hospital Review · IT", "category": "ai_health_product", "lang": "en"},

    # ---------------- AI 医疗健康研究 / 项目 ----------------
    {"url": "https://www.nature.com/npjdigitalmed.rss", "name": "npj Digital Medicine", "category": "ai_health_research", "lang": "en"},
    {"url": "https://www.thelancet.com/rssfeed/landig_current.xml", "name": "Lancet Digital Health", "category": "ai_health_research", "lang": "en"},
    {"url": "https://ai.nejm.org/action/showFeed?type=etoc&feed=rss&jc=aioa", "name": "NEJM AI", "category": "ai_health_research", "lang": "en"},
    {"url": "https://rss.arxiv.org/rss/cs.LG", "name": "arXiv · cs.LG", "category": "ai_health_research", "lang": "en"},
    {"url": "https://rss.arxiv.org/rss/eess.IV", "name": "arXiv · eess.IV", "category": "ai_health_research", "lang": "en"},
]

CATEGORY_LABELS = {
    "ai_product": "AI 产品应用",
    "ai_health_product": "AI 医疗健康产品",
    "ai_health_research": "AI 医疗健康研究",
}

# 医疗白名单：来自通用源(ai_product)的条目如命中这些关键词，可以晋升到 ai_health_product
HEALTH_KEYWORDS = [
    "health", "medical", "medicine", "clinic", "clinical", "hospital", "patient",
    "diagnos", "radiolog", "pathology", "oncolog", "cardiolog", "pulmonar",
    "surgery", "drug", "pharma", "biotech", "fda", "ehr", "emr", "genomic",
    "医疗", "医院", "临床", "诊断", "药", "基因", "健康", "影像",
    " ct ", " mri ", "x-ray", "ultrasound",
]

# arXiv 类目里只保留医疗健康相关论文的关键词过滤
ARXIV_HEALTH_KEYWORDS = [
    "medical", "medicine", "clinical", "hospital", "patient", "diagnos",
    "radiolog", "pathology", "oncolog", "cardio", "pulmonar", "surg",
    "drug", "pharma", "biotech", "genom", "ehr", "emr", "health",
    "ct scan", " ct ", " mri", "ultrasound", "x-ray", "xray", "biomed",
    "ecg", "eeg", "chest", "lesion", "tumor", "cancer",
]


def is_health_topic(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in HEALTH_KEYWORDS)


def is_arxiv_health(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in ARXIV_HEALTH_KEYWORDS)
