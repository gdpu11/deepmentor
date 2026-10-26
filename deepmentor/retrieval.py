"""Small, explicit query normalization; expansions are search hints, never evidence."""
from __future__ import annotations

import re
import unicodedata

STOP = set("我想 我的 这个 一个 什么 怎么 如何 现在 可以 是否 问题 应该 没有 自己 一下 我们 你们 根据 帮我 处理 进行 需要 通过 怎样 觉得 认为 方法 建议 你的 他的 她的 他们 我的 我们 你们 请问 问问 谢谢 第一个 第一 己的 的第 要不要 获得 有效 改变 人生 成功 变得 其他 容易 也要 分析 解释 不想".split())
EN_STOP = set("the and how what with for this that my to i a of is help please use ask me you your can first openmentor deepmentor".split())
CHINESE_STOP = re.compile("|".join(re.escape(word) for word in sorted(STOP, key=len, reverse=True)) + "|[的了呢吗啊]")
INCOME = re.compile(
    r"赚|挣(?=钱|到|出|个|自己|[一二三四五六七八九十百千万\d])|第一桶金|第一笔(?:钱|收入)|变现|盈利|增收|(?:增加|提升|提高|获得).{0,5}收入"
    r"|make\s+(?:some\s+)?money|\bearn(?:ing)?\b|\bfirst\s+million\b", re.I
)
INCOME_TERMS = "客户 价值 需求 用户 产品 商业 试错 成本 验证 能力"
NON_MONEY_AMOUNT = re.compile(r"\b(?:million|\d+\s*[kw]?)\s+(?:words|characters|users|followers|views)\b|\d+(?:[kw]|万)?\s*(?:字|粉丝|用户|播放)", re.I)
MONEY_CONTEXT = re.compile(r"赚钱|挣钱|盈利|收入|利润|变现|\b(?:money|income|profit|revenue|dollars?|usd)\b|人民币|元", re.I)
TOPICS = [
    ("reading_habit", re.compile(r"读书|看书|阅读|reading\s+habit", re.I), "阅读 学习 习惯 兴趣"),
    ("career_direction", re.compile(r"转行|跳槽|职业方向|擅长|自己的优势|适合干什么", re.I), "专长 职业 方向 能力 兴趣 选择"),
    ("business_understanding", re.compile(r"(?:不懂|看不懂|理解|研究).{0,10}(?:生意|股票|商业)|跟风买|商业模式"), "商业 模式 理解 判断 价值 风险 资金 长期 纠错"),
    ("incentive_judgment", re.compile(r"激励|提成|奖金|利益冲突"), "激励 利益 冲突 判断 组织"),
    ("decision_reversibility", re.compile(r"可逆|撤回|撤销|难以逆转|决策.{0,5}(?:太慢|速度)|层层审批"), "可逆 决策 速度 纠错 不确定性"),
    ("cooperation_trust", re.compile(r"失信|诚信|信誉|信任"), "信任 长期 合作 博弈"),
]
TASK_REQUIREMENTS = [
    ("trustworthiness", re.compile(r"失信|诚信|信誉|信任"), "信任 诚信 信誉 失信 可靠 诚实"),
    ("cross_field_learning", re.compile(r"(?:跨行业|跨领域|跨学科|其他行业|其他领域|不同领域).{0,15}学|学.{0,15}(?:跨行业|跨领域|跨学科|其他行业|其他领域|不同领域)"), "跨领域 跨行业 跨学科"),
    ("medical_treatment", re.compile(r"吃什么药|用药|药量|胸(?:口)?痛"), "医疗 临床 治疗 诊断 用药 处方"),
    ("legal_remedy", re.compile(r"起诉|维权|仲裁|法律责任|合同审查"), "法律 诉讼 维权 仲裁 合同"),
    ("market_prediction", re.compile(r"(?=.*(?:股票|股价|股市|币价))(?=.*(?:明天|下周|下个月|一定|必|稳赚))(?=.*(?:涨|跌|翻倍|走势)).*"), "股价 价格预测 行情预测 走势预测"),
    ("math_solution", re.compile(r"(?:求解|怎么解|如何解|解出|证明).{0,20}(?:方程|积分|定理|数学题)"), "数学 解题 求解 积分 定理"),
]
INCOME_QUESTIONS = [
    "目标金额的币种和口径是什么：营业额、净利润、累计税后收入还是可支配净资产？",
    "希望在多久内达成？现有技能、收入来源和每周可投入时间是什么？",
    "有哪些可用资源，试验最多能损失多少时间和资金？",
]
INVOCATION = re.compile(
    r"(?:(?:请教|请|帮忙|帮我|给我|我想|能不能|可以|使用|用|根据|基于|通过|调用|问问|问|找|一下|的)"
    r"|不要|别|不用|不想用|不使用|不采用|不参考|不是|排除|使用|采用|参考|和|与|及"
    r"|do not|don't|not|and|or|DeepMentor|OpenMentor|please|using|use|ask|consult|to|[\s,:：，、;；])*", re.I
)
FOLLOWUP = re.compile(
    r"(?:那|那么|接下来|然后|所以)?(?:我|我们)?(?:下一步|接下来)?(?:应该|该|要|能)?(?:先|再)?"
    r"(?:做什么|做啥|干啥|做哪一步|做哪步|怎么做|怎么办|如何做|如何开始|怎么开始|继续(?:说|分析)?)"
    r"(?:呢|啊|吗)?|(?:接下来|下一步|然后)(?:呢|啊)?"
    r"|(?:what\s+(?:should\s+i\s+do|do\s+i\s+do)(?:\s+(?:next|first|now))?|how\s+do\s+i\s+start)", re.I
)


def retrieval_question(query: str, aliases=()) -> str:
    """Separate the mentor invocation from the actual problem, retaining the raw request elsewhere."""
    # Try a named mentor before the product-only invocation. Unnamed queries use the latter.
    while query:
        for alias in sorted(set(aliases), key=len, reverse=True) + ["DeepMentor", "OpenMentor"]:
            pattern = re.escape(alias)
            if alias.isascii():
                pattern = r"(?<![A-Za-z0-9_-])" + pattern + r"(?![A-Za-z0-9_-])"
            match = re.search(pattern, query, re.I)
            if not match or match.start() > 100 or not INVOCATION.fullmatch(query[:match.start()]):
                continue
            tail = query[match.end():]
            query = re.sub(
                r"^\s*(?:的\s*)?(?:知识库|知识|公开资料|公开表达|思想|观点)?\s*[,，:：;；]?\s*"
                r"(?:(?:来)?(?:帮我)?(?:分析一下|分析下|分析|解释一下|解释下|解释|回答一下|回答|聊聊|看看|看下)\s*[,，:：]?\s*)?", "", tail
            ).strip()
            break
        else:
            break
    return query


def tokens(text: str) -> list[str]:
    result = []
    for part in re.findall(r"[a-z0-9]+|[\u3400-\u9fff]+", unicodedata.normalize("NFKC", text).lower()):
        if part.isascii():
            if part not in EN_STOP:
                result.append(part)
        else:
            # Split at complete filler phrases, avoiding cross-boundary fragments such as 己的.
            for content in CHINESE_STOP.split(part):
                result.extend(content[i:i + 2] for i in range(len(content) - 1) if content[i:i + 2] not in STOP)
    return result


def analyze_query(query: str, aliases=()) -> dict:
    if not isinstance(query, str) or not query.strip() or len(query) > 10000:
        raise ValueError("query must contain 1-10000 characters")
    normalized = retrieval_question(unicodedata.normalize("NFKC", query), aliases)
    # Do not turn a request explicitly excluding money into an income question.
    intent_text = re.sub(r"(?:不想|不是问|不谈|不要谈|不是要).{0,2}(?:赚钱|挣钱|盈利|变现)", "", normalized)
    income = bool(INCOME.search(intent_text))
    if NON_MONEY_AMOUNT.search(intent_text) and not MONEY_CONTEXT.search(intent_text):
        income = False
    intents = ["earning_income"] if income else []
    hints = [INCOME_TERMS] if income else []
    for name, pattern, related in TOPICS:
        if pattern.search(intent_text):
            intents.append(name)
            hints.append(related)
    terms = list(dict.fromkeys(tokens(normalized)))[:256]
    expanded = [t for t in dict.fromkeys(tokens(" ".join(hints))) if t not in terms]
    requirements = [{"task": name, "required_core_terms": list(dict.fromkeys(tokens(topics)))}
                    for name, pattern, topics in TASK_REQUIREMENTS if pattern.search(normalized)]
    for requirement in requirements:
        if requirement["task"] == "cross_field_learning":
            requirement["required_core_phrases"] = ["跨领域", "跨行业", "跨学科"]
        if requirement["task"] == "math_solution":
            # General problem solving or learning mathematics does not solve an equation.
            requirement["required_core_phrases"] = ["数学解题", "数学求解", "求解方程", "方程求解", "积分", "证明定理", "定理证明"]
        if requirement["task"] == "market_prediction":
            # A price/risk principle does not supply a price forecast.
            requirement["required_core_phrases"] = ["股价预测", "价格预测", "行情预测", "走势预测"]
    return {"strategy": "fts5_with_explicit_topic_expansion", "retrieval_query": normalized, "terms": terms, "expanded_terms": expanded,
            "intents": intents, "task_requirements": requirements,
            "expansion_note": "主题扩展只用于寻找相关原则，不证明人物对该问题给过直接答案或结果承诺。" if intents else None}


def analyze_guidance(question: str, situation: str | None = None, aliases=()) -> dict:
    analysis = analyze_query(question, aliases)
    if situation is not None:
        if not isinstance(situation, str) or not situation.strip() or len(question) + len(situation) > 10000:
            raise ValueError("situation must be nonempty text; question and situation together must not exceed 10000 characters")
    followup = bool(FOLLOWUP.fullmatch(analysis["retrieval_query"].strip(" \t\r\n，,。.!！?？:：")))
    if followup and situation is not None:
        analysis = analyze_query(situation, aliases)
    return {**analysis, "retrieval_basis": "situation" if followup and situation is not None else "request",
            "needs_context": followup and situation is None}
