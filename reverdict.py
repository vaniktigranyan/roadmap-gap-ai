# -*- coding: utf-8 -*-
"""
Re-classify verdicts for the candidates already in the DB, using the corrected
rule that a CLOSED issue cannot be "UNDER-PRIORITIZED" (neglected backlog).

Keeps the discovered needs and their evidence intact - only the verdict, the
confidence that depends on it, and the ranking change. Much cheaper and more
stable than re-running the whole pipeline.
"""
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import math
import numpy as np

from database import GapAnalysisDB
from gap_analyzer import GapAnalyzer, VERDICT_GAP_CERTAINTY, WEIGHTS


def confidence_from(support_reviews, support_emb, verdict):
    n = len(support_reviews)
    evidence_count = min(1.0, math.log(1 + n) / math.log(1 + 30))
    stars = set(r.get('star') for r in support_reviews if r.get('star') is not None)
    rating_spread = min(1.0, len(stars) / 3)

    if len(support_emb) >= 2:
        norm = support_emb / (np.linalg.norm(support_emb, axis=1, keepdims=True) + 1e-9)
        sim = norm @ norm.T
        iu = np.triu_indices(len(norm), k=1)
        consistency = float(np.mean(sim[iu])) if len(iu[0]) else 1.0
        consistency = max(0.0, min(1.0, consistency))
    else:
        consistency = 0.5

    base = VERDICT_GAP_CERTAINTY.get(verdict, 0.5)
    effective = base * (0.4 + 0.6 * consistency)
    conf = (WEIGHTS['evidence_count'] * evidence_count +
            WEIGHTS['rating_spread'] * rating_spread +
            WEIGHTS['consistency'] * consistency +
            WEIGHTS['roadmap_gap_certainty'] * effective)
    return {
        'confidence': round(conf * 100, 1),
        'components': {
            'evidence_count_norm': round(evidence_count, 3),
            'rating_spread': round(rating_spread, 3),
            'cross_signal_consistency': round(consistency, 3),
            'roadmap_gap_certainty': base,
            'effective_gap_certainty': round(effective, 3),
            'supporting_review_count': n,
        },
    }


def main():
    db = GapAnalysisDB()
    issues = db.get_issues()
    reviews = db.get_reviews()
    candidates = db.get_candidates()
    issues_by_number = {i['number']: i for i in issues}
    idx_of = {r['id']: i for i, r in enumerate(reviews)}

    print(f"Re-verdicting {len(candidates)} candidates against {len(issues)} issues\n")

    ga = GapAnalyzer()
    review_emb = ga.embed_texts([r['review_text'][:500] for r in reviews])

    changes = {'UNDER-PRIORITIZED->MISUNDERSTOOD': 0, 'other': 0, 'same': 0}
    updated = []

    for c in candidates:
        old_verdict = c['verdict']
        num = c.get('matched_issue_number')

        if not num or num not in issues_by_number:
            new_verdict, reasoning = 'IGNORED', c.get('reasoning', '')
        else:
            issue = issues_by_number[num]
            need_emb = ga.embed_texts([c['need_text']])[0]
            issue_emb = ga.embed_texts([f"{issue['title']}\n{(issue.get('body') or '')[:500]}"])
            res = ga.match_and_verdict(c['need_text'], need_emb, [issue], issue_emb)
            new_verdict, reasoning = res['verdict'], res.get('reasoning', '')

        key = f"{old_verdict}->{new_verdict}"
        if old_verdict == new_verdict:
            changes['same'] += 1
        elif key == 'UNDER-PRIORITIZED->MISUNDERSTOOD':
            changes[key] += 1
        else:
            changes['other'] += 1

        c2 = dict(c)
        c2['verdict'] = new_verdict
        if old_verdict != new_verdict:
            c2['reasoning'] = reasoning
            state = issues_by_number[num]['state'] if num in issues_by_number else 'n/a'
            print(f"  {old_verdict:<18} -> {new_verdict:<18} (issue #{num} {state}) {c['need_text'][:50]}")

        if new_verdict == 'COVERED':
            c2['confidence'] = None
            c2['confidence_components'] = {}
        else:
            gi = [idx_of[r] for r in c['evidence_review_ids'] if r in idx_of]
            support = [reviews[i] for i in gi]
            res = confidence_from(support, review_emb[gi], new_verdict)
            c2['confidence'] = res['confidence']
            c2['confidence_components'] = res['components']

        updated.append(c2)

    ranked = sorted([c for c in updated if c['confidence'] is not None],
                    key=lambda c: c['confidence'], reverse=True)
    top5 = ranked[:5]
    top5_texts = {g['need_text'] for g in top5}
    all_sorted = sorted(updated, key=lambda c: (c['confidence'] is None, -(c['confidence'] or 0)))

    print(f"\nChanges: {changes}")
    print(f"\nVerdict mix now: ", end="")
    for v in ['IGNORED', 'UNDER-PRIORITIZED', 'MISUNDERSTOOD', 'COVERED']:
        print(f"{v}={sum(1 for c in updated if c['verdict'] == v)} ", end="")
    print("\n\n=== NEW TOP-5 ===")
    for i, g in enumerate(top5, 1):
        num = g.get('matched_issue_number')
        state = issues_by_number[num]['state'] if num in issues_by_number else '-'
        print(f"#{i} {g['confidence']:.1f}% {g['verdict']:<18} issue={num or 'none'} ({state}) "
              f"ev={len(g['evidence_review_ids'])} {g['need_text'][:52]}")

    db.replace_gaps(top5)
    db.replace_candidates(all_sorted, top5_texts)
    print(f"\nSaved: {len(top5)} gaps, {len(all_sorted)} candidates")


if __name__ == "__main__":
    main()
