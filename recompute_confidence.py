# -*- coding: utf-8 -*-
"""
Recompute confidence for all stored candidates using the fixed formula
(gap_certainty now dampened by consistency), without re-calling the LLM
or re-embedding anything. Re-selects top-5 and saves back to DB.
"""
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import GapAnalysisDB
from gap_analyzer import WEIGHTS, VERDICT_GAP_CERTAINTY


def recompute(components: dict, verdict: str) -> dict:
    evidence_count = components['evidence_count_norm']
    rating_spread = components['rating_spread']
    consistency = components['cross_signal_consistency']
    base_gap_certainty = VERDICT_GAP_CERTAINTY.get(verdict, 0.5)
    effective_gap_certainty = base_gap_certainty * (0.4 + 0.6 * consistency)

    confidence = (
        WEIGHTS['evidence_count'] * evidence_count +
        WEIGHTS['rating_spread'] * rating_spread +
        WEIGHTS['consistency'] * consistency +
        WEIGHTS['roadmap_gap_certainty'] * effective_gap_certainty
    )

    return {
        'confidence': round(confidence * 100, 1),
        'components': {
            'evidence_count_norm': evidence_count,
            'rating_spread': rating_spread,
            'cross_signal_consistency': consistency,
            'roadmap_gap_certainty': base_gap_certainty,
            'effective_gap_certainty': round(effective_gap_certainty, 3),
            'supporting_review_count': components.get('supporting_review_count'),
        },
    }


def main():
    db = GapAnalysisDB()
    candidates = db.get_candidates()
    if not candidates:
        print("No candidates found in DB. Run the main pipeline first.")
        return

    print(f"Loaded {len(candidates)} candidates from DB")
    print("\n=== BEFORE (old formula) ===")
    old_sorted = sorted(
        [c for c in candidates if c['verdict'] != 'COVERED'],
        key=lambda c: c['confidence'], reverse=True
    )
    for i, c in enumerate(old_sorted[:5], 1):
        print(f"#{i} {c['confidence']:.1f}% {c['verdict']:<18} {c['need_text'][:60]}")

    updated = []
    for c in candidates:
        if c['verdict'] == 'COVERED':
            updated.append(c)
            continue
        result = recompute(c['confidence_components'], c['verdict'])
        c2 = dict(c)
        c2['confidence'] = result['confidence']
        c2['confidence_components'] = result['components']
        updated.append(c2)

    gap_candidates = [c for c in updated if c['verdict'] != 'COVERED']
    gap_candidates.sort(key=lambda c: c['confidence'], reverse=True)
    top5 = gap_candidates[:5]
    top5_texts = {g['need_text'] for g in top5}

    all_sorted = sorted(updated, key=lambda c: (c['confidence'] is None, -(c['confidence'] or 0)))

    print("\n=== AFTER (fixed formula: gap_certainty dampened by consistency) ===")
    for i, c in enumerate(top5, 1):
        print(f"#{i} {c['confidence']:.1f}% {c['verdict']:<18} {c['need_text'][:60]}")

    print("\n=== FULL RANKING (non-COVERED) ===")
    for c in gap_candidates:
        marker = "TOP5" if c['need_text'] in top5_texts else "    "
        print(f"[{marker}] {c['confidence']:.1f}% {c['verdict']:<18} {c['need_text'][:65]}")

    db.replace_gaps(top5)
    db.replace_candidates(all_sorted, top5_texts)
    print(f"\nSaved: {len(top5)} gaps, {len(all_sorted)} candidates")


if __name__ == "__main__":
    main()
