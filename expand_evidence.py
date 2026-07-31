# -*- coding: utf-8 -*-
"""
Expand evidence trace (search full review pool, not just cluster sample) and
add closest-issue transparency for IGNORED verdicts, for candidates already
in the DB. Pure local computation (embeddings only) - no LLM calls, no cost.
"""
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
from database import GapAnalysisDB
from gap_analyzer import GapAnalyzer, VERDICT_GAP_CERTAINTY, WEIGHTS


def compute_confidence(support_reviews, review_embeddings, verdict):
    import math
    n = len(support_reviews)
    evidence_count = min(1.0, math.log(1 + n) / math.log(1 + 30))
    stars = set(r.get('star') for r in support_reviews if r.get('star') is not None)
    rating_spread = min(1.0, len(stars) / 3)

    if len(review_embeddings) >= 2:
        norm = review_embeddings / (np.linalg.norm(review_embeddings, axis=1, keepdims=True) + 1e-9)
        sim_matrix = norm @ norm.T
        iu = np.triu_indices(len(norm), k=1)
        consistency = float(np.mean(sim_matrix[iu])) if len(iu[0]) > 0 else 1.0
        consistency = max(0.0, min(1.0, consistency))
    else:
        consistency = 0.5

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
            'evidence_count_norm': round(evidence_count, 3),
            'rating_spread': round(rating_spread, 3),
            'cross_signal_consistency': round(consistency, 3),
            'roadmap_gap_certainty': base_gap_certainty,
            'effective_gap_certainty': round(effective_gap_certainty, 3),
            'supporting_review_count': n,
        },
    }


def main():
    db = GapAnalysisDB()
    issues = db.get_issues()
    reviews = db.get_reviews()
    candidates = db.get_candidates()

    if not candidates:
        print("No candidates in DB. Run the main pipeline first.")
        return

    print(f"Loaded {len(issues)} issues, {len(reviews)} reviews, {len(candidates)} candidates")
    print("Embedding all reviews + issues locally (free, no API calls)...")

    ga = GapAnalyzer()
    issue_texts = [f"{i['title']}\n{(i.get('body') or '')[:500]}" for i in issues]
    review_texts = [r['review_text'][:500] for r in reviews]
    issue_emb = ga.embed_texts(issue_texts)
    review_emb = ga.embed_texts(review_texts)
    issues_by_number = {i['number']: i for i in issues}
    reviews_by_id = {r['id']: r for r in reviews}
    full_idx_map = {r['id']: i for i, r in enumerate(reviews)}

    updated = []
    for c in candidates:
        need_emb = ga.embed_texts([c['need_text']])[0]

        # Expand evidence: search full review pool, union with existing evidence
        sims = review_emb @ need_emb / (
            np.linalg.norm(review_emb, axis=1) * np.linalg.norm(need_emb) + 1e-9
        )
        expanded_ids = set(c['evidence_review_ids'])
        ranked_idx = np.argsort(-sims)
        for idx in ranked_idx:
            if len(expanded_ids) >= 15:
                break
            if sims[idx] < 0.4:
                break
            expanded_ids.add(reviews[idx]['id'])

        support_global_idx = [full_idx_map[rid] for rid in expanded_ids if rid in full_idx_map]
        support_reviews = [reviews[i] for i in support_global_idx]
        support_emb = review_emb[support_global_idx]

        c2 = dict(c)
        c2['evidence_review_ids'] = [r['id'] for r in support_reviews]

        # Closest issue for transparency, even when no match (IGNORED) or already matched
        issue_sims = issue_emb @ need_emb / (
            np.linalg.norm(issue_emb, axis=1) * np.linalg.norm(need_emb) + 1e-9
        )
        best_idx = int(np.argmax(issue_sims))
        c2['closest_issue_number'] = issues[best_idx]['number']
        c2['closest_issue_similarity'] = round(float(issue_sims[best_idx]), 3)

        if c['verdict'] != 'COVERED':
            result = compute_confidence(support_reviews, support_emb, c['verdict'])
            c2['confidence'] = result['confidence']
            c2['confidence_components'] = result['components']

        updated.append(c2)
        old_n = len(c['evidence_review_ids'])
        new_n = len(c2['evidence_review_ids'])
        print(f"  {c['need_text'][:55]:<55} evidence {old_n}->{new_n}  "
              f"closest_issue=#{c2['closest_issue_number']} (sim={c2['closest_issue_similarity']:.2f})")

    gap_candidates = [c for c in updated if c['verdict'] != 'COVERED']
    gap_candidates.sort(key=lambda c: c['confidence'], reverse=True)
    top5 = gap_candidates[:5]
    top5_texts = {g['need_text'] for g in top5}
    all_sorted = sorted(updated, key=lambda c: (c['confidence'] is None, -(c['confidence'] or 0)))

    print("\n=== NEW TOP-5 (after evidence expansion) ===")
    for i, g in enumerate(top5, 1):
        print(f"#{i} {g['confidence']:.1f}% {g['verdict']:<18} evidence={len(g['evidence_review_ids'])} {g['need_text'][:55]}")

    db.replace_gaps(top5)
    db.replace_candidates(all_sorted, top5_texts)
    print(f"\nSaved: {len(top5)} gaps, {len(all_sorted)} candidates")


if __name__ == "__main__":
    main()
