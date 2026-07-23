"""RSS 源清单与分类映射（AI 医疗健康 5 大类版本）。

分类（按判定优先级从高到低）：
  1. ai_health_gov_speech  关于 AI 卫健委讲话（主体命中卫健委即分类）
  2. ai_hospital_speech    关于 AI 院长讲话（命中"院长"）
  3. ai_health_funding     AI 医疗健康投融资（融资/并购/IPO/估值等）
  4. ai_health_project     AI 医疗健康项目（研究/试点/合作/临床试验等）
  5. ai_health_product     AI 医疗健康产品（默认）

条目留存条件：必须同时包含 AI 关键词 + 医疗关键词（或主体本身命中院长/卫健委）。
"""


def _gnews(q: str, days: int = 7) -> str:
    from urllib.parse import quote
    return f"https://news.google.com/rss/search?q={quote(q)}+when:{days}d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"


# 每条：url, name, category(展示分组用，非最终分类), lang
# 真正的分类由 fetch_news.classify() 按内容关键词决定。
FEEDS = [
    # ---------- AI 医疗健康产品 ----------
    {"url": _gnews("AI 医疗 产品"),        "name": "GN·AI 医疗产品",    "category": "ai_health_product", "lang": "zh"},
    {"url": _gnews("AI 医疗器械"),         "name": "GN·AI 医疗器械",    "category": "ai_health_product", "lang": "zh"},
    {"url": _gnews("大模型 医疗 落地"),    "name": "GN·大模型医疗落地", "category": "ai_health_product", "lang": "zh"},
    {"url": _gnews("AI 影像 诊断"),        "name": "GN·AI 影像诊断",    "category": "ai_health_product", "lang": "zh"},
    {"url": _gnews("AI 医生 应用"),        "name": "GN·AI 医生应用",    "category": "ai_health_product", "lang": "zh"},

    # ---------- AI 医疗健康项目 ----------
    {"url": _gnews("AI 医学 研究"),        "name": "GN·AI 医学研究",    "category": "ai_health_project", "lang": "zh"},
    {"url": _gnews("AI 临床 研究"),        "name": "GN·AI 临床研究",    "category": "ai_health_project", "lang": "zh"},
    {"url": _gnews("AI 药物 研发"),        "name": "GN·AI 药物研发",    "category": "ai_health_project", "lang": "zh"},
    {"url": _gnews("AI 医院 合作"),        "name": "GN·AI 医院合作",    "category": "ai_health_project", "lang": "zh"},
    {"url": _gnews("AI 医疗 试点"),        "name": "GN·AI 医疗试点",    "category": "ai_health_project", "lang": "zh"},

    # ---------- AI 医疗健康投融资 ----------
    {"url": _gnews("AI 医疗 融资"),        "name": "GN·AI 医疗融资",    "category": "ai_health_funding", "lang": "zh"},
    {"url": _gnews("AI 医疗 投资"),        "name": "GN·AI 医疗投资",    "category": "ai_health_funding", "lang": "zh"},
    {"url": _gnews("医疗 AI 上市"),        "name": "GN·医疗 AI 上市",   "category": "ai_health_funding", "lang": "zh"},
    {"url": _gnews("AI 医疗 并购"),        "name": "GN·AI 医疗并购",    "category": "ai_health_funding", "lang": "zh"},
    {"url": _gnews("AI 医药 IPO"),         "name": "GN·AI 医药 IPO",    "category": "ai_health_funding", "lang": "zh"},

    # ---------- 关于 AI 院长讲话（低频事件，扩窗口 14 天） ----------
    {"url": _gnews("院长 AI 医疗", 14),        "name": "GN·院长谈 AI",      "category": "ai_hospital_speech", "lang": "zh"},
    {"url": _gnews("医院 院长 人工智能", 14),  "name": "GN·医院院长 AI",    "category": "ai_hospital_speech", "lang": "zh"},
    {"url": _gnews("院长 大模型", 14),         "name": "GN·院长谈大模型",   "category": "ai_hospital_speech", "lang": "zh"},
    {"url": _gnews("院长 谈 AI", 14),          "name": "GN·院长讲话 AI",    "category": "ai_hospital_speech", "lang": "zh"},

    # ---------- 关于 AI 卫健委讲话（低频事件，扩窗口 14 天 + 更多同义查询） ----------
    {"url": _gnews("卫健委 人工智能", 14),     "name": "GN·卫健委 AI",       "category": "ai_health_gov_speech", "lang": "zh"},
    {"url": _gnews("国家卫健委 AI", 14),       "name": "GN·国家卫健委 AI",   "category": "ai_health_gov_speech", "lang": "zh"},
    {"url": _gnews("卫健委 大模型", 14),       "name": "GN·卫健委大模型",    "category": "ai_health_gov_speech", "lang": "zh"},
    {"url": _gnews("卫生健康委 AI 医疗", 14),  "name": "GN·卫健委医疗 AI",   "category": "ai_health_gov_speech", "lang": "zh"},
    {"url": _gnews("卫健委 智慧医疗", 14),     "name": "GN·卫健委智慧医疗",  "category": "ai_health_gov_speech", "lang": "zh"},
    {"url": _gnews("卫健委 数字医疗", 14),     "name": "GN·卫健委数字医疗",  "category": "ai_health_gov_speech", "lang": "zh"},
]

CATEGORY_LABELS = {
    "ai_health_product":     "AI 医疗健康产品",
    "ai_health_project":     "AI 医疗健康项目",
    "ai_health_funding":     "AI 医疗健康投融资",
    "ai_hospital_speech":    "关于 AI 院长讲话",
    "ai_health_gov_speech":  "关于 AI 卫健委讲话",
}

# 展示顺序（前端按这个顺序渲染 tab）
CATEGORY_ORDER = [
    "ai_health_product",
    "ai_health_project",
    "ai_health_funding",
    "ai_hospital_speech",
    "ai_health_gov_speech",
]

# --- 关键词表 ---
AI_KEYWORDS = [
    "AI", "A.I.", "人工智能", "大模型", "大语言模型", "生成式",
    "GPT", "ChatGPT", "LLM", "机器学习", "深度学习", "神经网络",
    "多模态", "智能体", "Agent", "算法模型", "Transformer", "扩散模型",
    "文心", "通义", "豆包", "Kimi", "DeepSeek", "Claude", "Gemini",
    "Sora", "Copilot", "智能诊断", "AI 医生", "AI医生",
]

HEALTH_KEYWORDS = [
    "医疗", "医院", "临床", "诊断", "诊疗", "医生", "患者", "病人",
    "药", "制药", "药企", "药物", "药品", "疾病", "肿瘤", "癌症",
    "基因", "健康", "影像", "放射", "病理", "手术", "外科", "内科",
    "生物医药", "生物制药", "医学", "医械", "医疗器械", "FDA", "NMPA",
    "CT", "MRI", "PET", "超声", "内窥", "内镜", "卫健", "卫生健康",
]

# 卫健委主体
GOV_KEYWORDS = [
    "卫健委", "国家卫健委", "国家卫生健康委", "卫生健康委员会",
    "卫健局", "省卫健委", "市卫健委", "卫生健康委",
]

# 院长主体
HOSPITAL_HEAD_KEYWORDS = ["院长"]

# 投融资
FUNDING_KEYWORDS = [
    "融资", "轮融资", "天使轮", "A 轮", "A轮", "B 轮", "B轮", "C 轮", "C轮",
    "Pre-A", "Pre-B", "Pre A", "Pre B", "Series A", "Series B",
    "领投", "跟投", "投资方", "估值",
    "并购", "收购", "M&A",
    "IPO", "上市", "递表", "招股", "港股", "科创板", "纳斯达克",
    "亿元", "亿美元", "亿港元", "千万美元", "百万美元",
]

# 项目 / 研究
PROJECT_KEYWORDS = [
    "研究", "论文", "临床试验", "队列", "综述", "预印本", "发表",
    "项目", "试点", "合作", "签约", "揭牌", "落地", "启动", "推进",
    "开展", "研究人员", "研究者", "研究组", "课题", "医联体",
    "meta 分析", "meta-analysis",
]


def _hit(text: str, keywords) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)


def is_ai_topic(text: str) -> bool:
    return _hit(text, AI_KEYWORDS)


def is_health_topic(text: str) -> bool:
    return _hit(text, HEALTH_KEYWORDS)


def is_gov(text: str) -> bool:
    return _hit(text, GOV_KEYWORDS)


def is_hospital_head(text: str) -> bool:
    return _hit(text, HOSPITAL_HEAD_KEYWORDS)


def is_funding(text: str) -> bool:
    return _hit(text, FUNDING_KEYWORDS)


def is_project(text: str) -> bool:
    return _hit(text, PROJECT_KEYWORDS)
