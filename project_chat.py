# -*- coding: utf-8 -*-
"""
Grounded Q&A over the gap analysis: lets a user (or a judge) interrogate the
results in natural language. All answers are built from the actual DB contents
that are passed in as context, so the assistant can cite review IDs, issue
numbers and the exact confidence components behind any claim.
"""
import os
import statistics
from typing import List, Dict

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GEN_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

SYSTEM_PROMPT = """You are the analyst behind a "Silent Stakeholder" gap analysis of Orbot
(the Tor proxy app for Android). You cross-analyzed the team's GitHub roadmap against real
user reviews to surface LATENT unmet needs — needs users never stated outright.

You are being questioned by a user or a hackathon judge. Answer from the CONTEXT below only.

Rules:
- Ground every claim in the data: cite review IDs like [1234], issue numbers like #1517,
  and exact confidence numbers when relevant.
- If the context does not contain the answer, say so plainly. Never invent review IDs,
  issue numbers, or statistics.
- Be concise and direct. A few sentences is usually right; use short bullets for lists.
- Explain reasoning when asked "how did you conclude this" — walk through the actual
  evidence chain (which reviews, why they imply the latent need, what the roadmap does
  or doesn't say).
- Answer in the same language the user writes in (Russian or English).
"""


def _star_summary(reviews: List[Dict]) -> str:
    stars = [r['star'] for r in reviews if r.get('star') is not None]
    if not stars:
        return "no ratings"
    dist = {s: stars.count(s) for s in sorted(set(stars))}
    dist_str = ", ".join(f"{s}star:{c}" for s, c in dist.items())
    return f"avg {statistics.mean(stars):.1f}, distribution {dist_str}"


def build_context(gaps: List[Dict], candidates: List[Dict], reviews: List[Dict],
                  issues: List[Dict], clusters: List[Dict]) -> str:
    """Assemble a compact but evidence-rich snapshot of the whole analysis."""
    reviews_by_id = {r['id']: r for r in reviews}
    issues_by_number = {i['number']: i for i in issues}

    lines = []
    lines.append("=== CORPUS ===")
    lines.append(f"Product: Orbot (guardianproject/orbot-android), reviews for org.torproject.android")
    lines.append(f"Roadmap: {len(issues)} GitHub issues. User signals: {len(reviews)} reviews.")
    lines.append(f"Shared functional taxonomy: {len(clusters)} clusters "
                 f"({', '.join(c['label'] for c in clusters[:14])}).")

    lines.append("\n=== METHOD ===")
    lines.append(
        "1) Both issues and reviews are embedded locally (all-MiniLM-L6-v2) and KMeans-clustered "
        "into one shared taxonomy. 2) Per cluster, an LLM mines LATENT needs (second-order "
        "patterns: workarounds, comparisons, contradictions), not surface complaints. "
        "3) Evidence is then expanded by semantic search across ALL reviews (cosine >= 0.4, "
        "capped at 15) so the trace is not limited to the LLM's initial sample. "
        "4) Each need is matched against the FULL issue pool; if best cosine < 0.4 the verdict "
        "is IGNORED, otherwise an LLM classifies COVERED / UNDER-PRIORITIZED / MISUNDERSTOOD. "
        "5) Confidence = 0.35*evidence_volume + 0.15*rating_spread + 0.25*consistency + "
        "0.25*effective_gap_certainty, where effective_gap_certainty = "
        "base_verdict_weight * (0.4 + 0.6*consistency). The dampening exists because a harsh "
        "verdict (IGNORED=1.0) must not mask weak, inconsistent evidence — this bug was caught "
        "by an adversarial agent debate and fixed."
    )
    lines.append(
        "Verdict meanings: IGNORED = no roadmap issue addresses it; UNDER-PRIORITIZED = an issue "
        "exists but is stale/unscheduled/low-engagement; MISUNDERSTOOD = an issue exists in the "
        "same area but is framed around a different problem than the real user need; "
        "COVERED = roadmap already fully addresses it (excluded from the ranking, kept for audit)."
    )

    lines.append("\n=== TOP-5 UNMET NEEDS (ranked by confidence) ===")
    for rank, g in enumerate(gaps, 1):
        comp = g.get('confidence_components', {})
        ev_ids = g.get('evidence_review_ids', [])
        ev_reviews = [reviews_by_id[i] for i in ev_ids if i in reviews_by_id]
        pct = 100.0 * len(ev_reviews) / len(reviews) if reviews else 0

        lines.append(f"\n--- #{rank}. {g['need_text']}")
        lines.append(f"Verdict: {g['verdict']} | Confidence: {g['confidence']:.1f}%")
        lines.append(
            f"Components: evidence_volume={comp.get('evidence_count_norm')}, "
            f"rating_spread={comp.get('rating_spread')}, "
            f"consistency={comp.get('cross_signal_consistency')}, "
            f"base_verdict_weight={comp.get('roadmap_gap_certainty')}, "
            f"effective_gap_certainty={comp.get('effective_gap_certainty')}"
        )
        lines.append(f"Users signalling this: {len(ev_reviews)} reviews "
                     f"({pct:.2f}% of the {len(reviews)}-review corpus); ratings: {_star_summary(ev_reviews)}")
        lines.append(f"Reasoning: {g.get('reasoning', '')}")

        if g.get('matched_issue_number'):
            iss = issues_by_number.get(g['matched_issue_number'])
            if iss:
                lines.append(
                    f"Matched roadmap issue: #{iss['number']} \"{iss['title']}\" "
                    f"(state={iss['state']}, milestone={iss.get('milestone_title') or 'none'}, "
                    f"+1 reactions={iss.get('reactions_plus1', 0)}, comments={iss.get('comments', 0)})"
                )
        else:
            closest = issues_by_number.get(g.get('closest_issue_number'))
            if closest:
                lines.append(
                    f"No matching issue. Closest considered: #{closest['number']} "
                    f"\"{closest['title']}\" at similarity {g.get('closest_issue_similarity')} "
                    f"(below the 0.4 match threshold) -> verdict IGNORED."
                )

        lines.append("Evidence reviews:")
        for r in ev_reviews:
            lines.append(f"  [{r['id']}] {r.get('star', '?')}star: {r['review_text'][:220]}")

    other = [c for c in candidates if not c.get('in_top5')]
    lines.append(f"\n=== OTHER CANDIDATES CONSIDERED ({len(other)}) ===")
    lines.append("These were found but ranked below the top-5, or excluded as already COVERED "
                 "by the roadmap. Kept for auditability.")
    for c in other:
        conf = f"{c['confidence']:.1f}%" if c.get('confidence') is not None else "n/a (COVERED)"
        matched = f"#{c['matched_issue_number']}" if c.get('matched_issue_number') else "no match"
        lines.append(f"  - {c['need_text']} | {c['verdict']} | {conf} | "
                     f"{len(c.get('evidence_review_ids', []))} reviews | issue {matched}")

    return "\n".join(lines)


class ProjectChat:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)

    def ask(self, question: str, context: str, history: List[Dict] = None) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n=== CONTEXT ===\n" + context}]
        for turn in (history or [])[-6:]:
            messages.append({"role": turn['role'], "content": turn['content']})
        messages.append({"role": "user", "content": question})

        response = self.client.chat.completions.create(
            model=GEN_MODEL,
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content
