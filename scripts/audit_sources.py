"""Check curated excerpts against local baseline snapshots; no downloading or approval.

Run after installing the project, with the unredistributed source snapshots available:
python scripts/audit_sources.py --people paul-graham james-clear --snapshots .open-mentor/revisions
This verifies hashes and text presence, not authorship, context or factual correctness.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections import defaultdict
from pathlib import Path

from open_mentor.library import Library
from open_mentor.updates import normalize, sha256


def audit(library: Library, people: list[str], snapshots: Path) -> dict:
    people = {library.person(p)['id'] for p in people}
    records, quotations = [], defaultdict(set)
    for source in library.sources.values():
        if source['person_id'] not in people:
            continue
        digest = source['content_sha256']
        if not digest:
            raise ValueError(f"No baseline hash: {source['id']}")
        path = snapshots / source['id'] / (digest + '.txt')
        text = path.read_text(encoding='utf-8')
        if sha256(text) != digest:
            raise ValueError(f"Snapshot hash mismatch: {source['id']}")
        normalized = normalize(text)
        evidence = [e for e in library.evidence.values() if e['source_id'] == source['id']]
        for e in evidence:
            if normalize(e['excerpt']) not in normalized:
                raise ValueError(f"Excerpt missing from baseline: {e['id']}")
            quotations[source['url'].rstrip('/')].add(normalize(e['excerpt']))
        records.append({'source_id': source['id'], 'person_id': source['person_id'], 'url': source['url'],
                        'content_sha256': digest, 'evidence_count': len(evidence)})
    # Combine duplicate URLs across people (e.g. independently authored essays in one report).
    for url, quotes in quotations.items():
        words = sum(len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", q)) +
                    len(re.findall(r'[\u3400-\u9fff]', q)) for q in quotes)
        if words > 25:
            raise ValueError(f"Short-excerpt budget exceeded: {url} ({words})")
    return {'status': 'passed', 'people': len(people), 'source_records': len(records),
            'distinct_urls': len(quotations), 'evidence': sum(r['evidence_count'] for r in records),
            'checks': ['baseline_sha256', 'normalized_excerpt_presence', 'short_excerpts_per_url'],
            'limits': 'Text checks do not verify authorship, context, facts or method effectiveness.', 'sources': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--people', nargs='+', required=True)
    parser.add_argument('--snapshots', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as state:
        library = Library(state_dir=Path(state))
        try:
            print(json.dumps(audit(library, args.people, args.snapshots), ensure_ascii=False, indent=2))
        finally:
            library.close()


if __name__ == '__main__':
    main()
