"""Readable evidence and editor-curated actions, without pretending to call a model."""
from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def citation_url(evidence: dict) -> str:
    source, locator = evidence["source"], evidence["locator"]
    url = source.get("origin_url") if locator["value"].startswith("YouTube ") else source["url"]
    url = url or source["url"]
    parsed = urlsplit(url)
    time = re.search(r"(\d{2}):(\d{2}):(\d{2})", locator["value"])
    if locator["type"] == "timestamp" and time and parsed.hostname in {"www.youtube.com", "youtube.com", "youtu.be"}:
        seconds = sum(int(value) * factor for value, factor in zip(time.groups(), (3600, 60, 1)))
        params = [(k, v) for k, v in parse_qsl(parsed.query) if k != "t"] + [("t", str(seconds))]
        url = urlunsplit(parsed._replace(query=urlencode(params)))
    return url


def render_guidance(result: dict) -> str:
    if result["status"] == "needs_person_selection":
        choices = "、".join(p["name"] for p in result["people"])
        reason = "请求的导师尚未收录。" if result.get("reason") == "requested_person_unavailable" else "请求提到了多位导师。"
        return f"{reason}请指定希望使用的人物知识库：{choices}。"
    profile = result.get("person")
    lines = [f"# OpenMentor · {profile['name']}" if profile else "# OpenMentor", "", f"问题：{result['question']}", ""]
    if result.get("user_situation"):
        lines += ["用户提供的背景：" + result["user_situation"], ""]
    if profile:
        automatic = result.get("request_resolution", {}).get("method") == "automatic_evidence_match"
        lines += [f"本次采用的导师资料：**{profile['name']}**（{'自动匹配' if automatic else '按请求指定'}）。", ""]
        if automatic:
            lines += ["选择理由：" + result["request_resolution"]["reason"], ""]
    if result["status"] == "needs_context":
        return "\n".join(lines + ["这条追问缺少原问题，暂不匹配资料。", "", *result["questions_to_resolve"]])
    if result["status"] != "ready":
        return "\n".join(lines + ["当前知识库没有足够的相关已复核证据，不能据此给出人物观点。", "", *result["questions_to_resolve"]])
    lines += ["以下为公开资料支持的相关原则与编辑整理的应用步骤；由调用的 AI 结合实际情况继续分析。", ""]
    if "earning_income" in result.get("query_analysis", {}).get("intents", []):
        lines += ["这些资料不提供目标金额或达成期限的保证；融资、营业额和个人净积累须分别计算。", ""]
    for index, p in enumerate(result["principles"], 1):
        lines += [f"{index}. **{p['title']}**", "", p["summary"], ""]
        for step in p["application"]["steps"]:
            lines += [f"- 编辑应用：{step}"]
        lines.append("")
        for e in p["evidence"]:
            date = e["source"]["published_at"] or "日期未确认"
            lines += [f"证据 [{e['id']}]({e.get('citation_url') or citation_url(e)})：{e['speaker']}，登记来源日期 {date}，{e['locator']['value']}。短摘录：{e['excerpt']}", ""]
        if p["application"]["limits"]:
            lines += ["边界：" + "；".join(s.rstrip("。；") for s in p["application"]["limits"]) + "。", ""]
    lines += ["需要确认的条件：", "", *["- " + q for q in result["questions_to_resolve"]]]
    return "\n".join(lines)
