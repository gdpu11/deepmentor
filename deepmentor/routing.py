"""Bounded mentor-name routing. These rules do not interpret arbitrary natural language."""
from __future__ import annotations

import re
import unicodedata

from .retrieval import retrieval_question


NEGATIVE = re.compile(
    r"(?:不要|别|不用|不想用|不使用|不采用|不参考|排除|不是|do not|don't|not)"
    r"\s*(?:再|使用|采用|根据|基于|参考|用|问问|问|咨询|ask|consult|use)?\s*$", re.I
)
DIRECTIVE = re.compile(r"(?:使用|采用|根据|基于|参考|用|请教|咨询|问问|问|ask|consult|use)\s*$", re.I)
CONNECTORS = re.compile(r"(?:和|与|及|以及|或|的|and|or|[\s、,&/])*", re.I)
NAMED_REQUESTS = [
    re.compile(r"(?:使用|根据|基于|用)\s*([^，,:：？?。；;\n]{2,50}?)(?:的)?(?:知识库|公开资料|公开表达|思想|观点)"),
    re.compile(r"(?:问问|请教|咨询)\s*([^，,:：？?\s]{2,12})\s*[,，:：]"),
    re.compile(r"(?:ask|consult|use)\s+([A-Za-z][A-Za-z .'-]{0,50}?)\s*(?:about\b|[:,]|'s\s+(?:knowledge|ideas|views))", re.I),
]


def _mentions(text: str, people: dict) -> list[tuple[int, int, str]]:
    hits = []
    aliases = [(alias, p["id"]) for p in people.values() for alias in [p["id"], p["name"], *p["aliases"]]]
    for alias, person_id in sorted(aliases, key=lambda item: len(item[0]), reverse=True):
        pattern = re.escape(unicodedata.normalize("NFKC", alias))
        if alias.isascii():
            pattern = r"(?<![A-Za-z0-9_-])" + pattern + r"(?![A-Za-z0-9_-])"
        for hit in re.finditer(pattern, text, re.I):
            if not any(start < hit.end() and end > hit.start() for start, end, _ in hits):
                hits.append((hit.start(), hit.end(), person_id))
    return sorted(hits)


def resolve_people(request: str, people: dict) -> dict:
    text = retrieval_question(unicodedata.normalize("NFKC", request))
    hits = _mentions(text, people)
    excluded, positive, mentioned = set(), set(), set()
    previous_end, previous_negative, previous_positive = 0, False, False
    for start, end, person_id in hits:
        negative = bool(NEGATIVE.search(text[:start])) or (
            previous_negative and bool(CONNECTORS.fullmatch(text[previous_end:start])))
        directed = bool(DIRECTIVE.search(text[:start])) or (
            previous_positive and bool(CONNECTORS.fullmatch(text[previous_end:start])))
        if negative:
            excluded.add(person_id)
        else:
            mentioned.add(person_id)
            if directed:
                positive.add(person_id)
        previous_end, previous_negative, previous_positive = end, negative, directed and not negative

    unavailable = []
    for pattern in NAMED_REQUESTS:
        for match in pattern.finditer(text):
            if NEGATIVE.search(text[:match.start()]):
                continue
            target = match[1].strip()
            if target.casefold() in ("openmentor", "deepmentor"):
                continue
            target_hits = _mentions(target, people)
            remainder, end = [], 0
            for start, stop, person_id in target_hits:
                remainder.append(target[end:start])
                end = stop
            remainder.append(target[end:])
            if target_hits and CONNECTORS.fullmatch("".join(remainder)):
                positive.update(person_id for _, _, person_id in target_hits)
            else:
                unavailable.append(target)

    selected = (positive or mentioned) - excluded
    reason = "requested_person_unavailable" if unavailable else (
        "multiple_people_mentioned" if len(selected) > 1 else "resolved")
    return {"person": people[next(iter(selected))] if len(selected) == 1 and not unavailable else None,
            "reason": reason, "requested_names": list(dict.fromkeys(unavailable)),
            "people": [p for p in people.values() if p["id"] in selected] if not unavailable else list(people.values()),
            "excluded_person_ids": sorted(excluded)}
