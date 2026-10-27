"""Evidence-backed consultation protocols. Synthesis belongs to the calling AI."""
from __future__ import annotations

from itertools import combinations

from .retrieval import analyze_guidance
from .routing import resolve_people

INTERVIEW = {
    "goal": "你这次要做哪个决定？目标、期限和成功指标分别是什么？",
    "resources": "你有哪些可用技能、时间、资金及必须遵守的约束？",
    "downside": "最坏结果是什么？最多能损失多少时间或资金，何时应停止？",
}
PROTOCOL = """先引用各视角的具体证据，再指出假设和适用条件。对其他视角提出有针对性的反问；只有证据支持时才说观点冲突，不能编造人物之间的对话或固定性格。最后输出决策备忘录：选项、权衡矩阵、关键未知、72小时可逆实验、成功指标、停止条件。数值阈值需由用户确认。尖锐地审视计划和假设，不羞辱用户。所有交叉质询和行动方案明确标为助手推演。"""


def consult_board(library, question, people=None, limit=3, allow_secondary=False, situation=None):
    analysis = analyze_guidance(question, situation, library._aliases)
    if type(limit) is not int or not 1 <= limit <= 5 or type(allow_secondary) is not bool:
        raise ValueError("board limit must be 1-5 and allow_secondary must be boolean")
    if people is not None and (not isinstance(people, list) or not 2 <= len(people) <= 3 or
                               any(not isinstance(p, str) for p in people)):
        raise ValueError("people must contain 2-3 distinct mentor names")
    routing = resolve_people(question, library.people)
    if people is not None:
        profiles = [library.person(p) for p in people]
        if len({p["id"] for p in profiles}) != len(profiles):
            raise ValueError("people must contain distinct mentors")
    elif routing["reason"] == "requested_person_unavailable":
        return {"status": "needs_person_selection", "artifact_type": "board_context", "question": question,
                "requested_names": routing["requested_names"], "perspectives": [], "citations": {},
                "questions_to_resolve": ["请求的人物未收录，请明确指定2-3位已收录导师。"]}
    else:
        profiles = routing["people"]
        if len(profiles) > 3:
            raise ValueError("board supports at most 3 mentors")
    base = {"artifact_type": "board_context", "question": question, "user_situation": situation,
            "instructions": library.rules + "\n" + PROTOCOL, "perspectives": [], "citations": {},
            "selection_method": "requested" if profiles else "evidence_relevance_and_topic_diversity",
            "selection_note": "根据本次匹配原则的主题增加视角差异，不代表人物立场相反或本人参与辩论。"}
    if analysis["needs_context"]:
        return {**base, "status": "needs_context", "questions_to_resolve": ["请补充原问题及处境。"]}
    candidates = []
    for profile in library.people.values():
        if profile["id"] in routing["excluded_person_ids"] and people is None:
            continue
        context = library.guidance_context(profile["id"], question, limit, allow_secondary, situation)
        if context["status"] == "ready":
            terms = {t for p in context["principles"] for t in p["topics"]}
            candidates.append((context["principles"][0]["relevance"], terms, context))
    chosen = [c for p in profiles for c in candidates if c[2]["person"]["id"] == p["id"]]
    # Explicit selection must never be silently replaced with another mentor.
    if not profiles:
        candidates.sort(key=lambda c: (-c[0], c[2]["person"]["id"]))
        if candidates:
            chosen.append(candidates[0])
        while len(chosen) < 3:
            remaining = [c for c in candidates if c not in chosen]
            if not remaining:
                break
            seen = set().union(*(c[1] for c in chosen))
            # Select within the relevant candidates, balancing rank and new topics.
            candidate = max(enumerate(remaining), key=lambda row: (
                .6 / (row[0] + 1) + .4 * len(row[1][1] - seen) / max(1, len(row[1][1])),
                row[1][2]["person"]["id"]))[1]
            chosen.append(candidate)
    contexts = [c[2] for c in chosen]
    for context in contexts:
        profile = context["person"]
        automatic = not profiles
        context["request_resolution"] = {
            "method": "automatic_evidence_match" if automatic else "explicit_board",
            "person_id": profile["id"],
            "reason": (f"根据当前可引用原则的相关性和主题差异，采用{profile['name']}的“{context['principles'][0]['title']}”等资料。"
                       if automatic else f"按请求使用{profile['name']}的公开资料。"),
        }
    base["perspectives"] = contexts
    base["unavailable_people"] = [p["id"] for p in profiles if p["id"] not in {c["person"]["id"] for c in contexts}]
    base["citations"] = {eid: e for c in contexts for eid, e in c["citations"].items()}
    base["status"] = "ready" if len(contexts) >= 2 and not base["unavailable_people"] else "insufficient_evidence"
    base["questions_to_resolve"] = list(dict.fromkeys(q for c in contexts for q in c["questions_to_resolve"]))[:9]
    base["tradeoff_matrix"] = [{"person_id": c["person"]["id"], "focus": p["title"],
        "application_questions": p["application"]["questions"], "suggested_actions": p["application"]["steps"],
        "limits": p["application"]["limits"], "evidence_ids": [e["id"] for e in p["evidence"]]}
        for c in contexts for p in c["principles"][:2]]
    base["cross_examination"] = [{"perspectives": [a["person"]["id"], b["person"]["id"]],
        "prompt": f"“{a['principles'][0]['title']}”和“{b['principles'][0]['title']}”在本次决策中各依赖什么条件？资源不足时如何取舍，哪些证据能推翻你的选择？",
        "kind": "editorial_question", "evidence_ids": list(dict.fromkeys(
            e["id"] for c in (a, b) for e in c["principles"][0]["evidence"]))}
        for a, b in combinations(contexts, 2)]
    return base


def stress_test(library, question, person=None, limit=3, allow_secondary=False, situation=None):
    context = library.ask(question, person, limit, allow_secondary, situation)
    result = {**context, "artifact_type": "stress_test_context", "instructions": library.rules + "\n" + PROTOCOL,
              "failure_modes": []}
    for p in context["principles"][:3]:
        result["failure_modes"].append({"principle_id": p["id"], "kind": "editorial_stress_question",
            "assumption_to_challenge": p["application"]["questions"],
            "failure_conditions": p["application"]["limits"],
            "probe_candidates": p["application"]["steps"],
            "evidence_ids": [e["id"] for e in p["evidence"]],
            "pre_mortem": "假设计划失败：上述适用条件中哪一条最可能不成立？72小时内用什么低成本证据检查？",
            "stop_criteria": "先与用户约定可测量的失败阈值和复查日期，不编造数值。"})
    return result


def diagnose(library, question, answers=None, person=None, allow_secondary=False, situation=None):
    analyze_guidance(question, situation)
    if answers is None:
        answers = {}
    if not isinstance(answers, dict) or set(answers) - INTERVIEW.keys():
        raise ValueError("answers must be an object with goal, resources and downside only")
    if any(not isinstance(v, str) or not v.strip() or len(v) > 2000 for v in answers.values()):
        raise ValueError("each answer must contain 1-2000 characters")
    if type(allow_secondary) is not bool:
        raise ValueError("allow_secondary must be boolean")
    if person is not None:
        library.person(person)
    missing = [{"id": k, "question": v} for k, v in INTERVIEW.items() if k not in answers]
    if missing:
        return {"status": "needs_clarification", "artifact_type": "diagnostic_interview", "question": question,
                "answers": answers, "questions": missing, "citations": {},
                "note": "由调用方收集回答后重调 diagnose；不自动保存访谈。"}
    combined = "\n".join([situation or "", *(f"{INTERVIEW[k]} {v}" for k, v in answers.items())]).strip()
    context = library.ask(question, person, 5, allow_secondary, combined)
    return {**context, "artifact_type": "decision_memo_context", "answers": answers,
            "instructions": library.rules + "\n" + PROTOCOL,
            "memo_sections": ["处境与目标", "可选方案", "证据与适用条件", "权衡与未知", "72小时实验", "成功/停止指标与复查日期"]}
