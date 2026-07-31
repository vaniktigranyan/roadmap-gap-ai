# -*- coding: utf-8 -*-
"""
Adversarial review panel.

Four specialists argue over the FULL analysis - every candidate, every piece of
evidence, both sides of the product - and a judge cross-examines them and rules
on each gap. Each agent sees the running transcript, so this is a real discussion
rather than four isolated opinions.

A deterministic FACTS block is computed in Python and handed to every agent. An
earlier 2-agent version of this let a model do arithmetic in its head and it
hallucinated a ranking inconsistency that did not exist; the facts block exists
so no agent ever has to compute - only interpret.
"""
import os
import json
import statistics
from typing import List, Dict, Callable, Optional

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GEN_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

PANEL = {
    'user_advocate': {
        'label': 'User Advocate',
        'emoji': '🙋',
        'brief': (
            "You represent the users who wrote these reviews and will never be in the room. "
            "Read the evidence as lived experience, not as data points. Your questions: does each "
            "stated need actually match what these people are struggling with? Is any need a "
            "paraphrase of a complaint rather than the deeper thing behind it? Is there a need "
            "screaming from the reviews that the analysis flattened or missed entirely? "
            "Push back hard when a need is stated in product-speak instead of user terms."
        ),
    },
    'roadmap_owner': {
        'label': 'Roadmap Owner',
        'emoji': '🗺️',
        'brief': (
            "You own the Orbot roadmap and must defend it. For every gap, your job is to check "
            "whether the roadmap really is failing users or whether the analysis simply failed to "
            "find the right issue. Scrutinise each verdict: is IGNORED fair when the closest issue "
            "sits just under the match threshold? Is UNDER-PRIORITIZED fair for an issue that is "
            "open and recently active? Is MISUNDERSTOOD a real framing mismatch or a semantic "
            "quibble? Concede honestly when the roadmap genuinely has a hole."
        ),
    },
    'evidence_auditor': {
        'label': 'Evidence Auditor',
        'emoji': '🔍',
        'brief': (
            "You audit rigour, not opinions. Check that each gap's evidence genuinely supports it "
            "and is not topically-similar noise pulled in by embedding search. Check that the "
            "confidence components are consistent with the evidence you can see. Flag any gap whose "
            "score is inflated by volume while its reviews say little, and any gap whose score "
            "understates unusually strong evidence. Cite specific review IDs when you object."
        ),
    },
}

JUDGE = {
    'label': 'Judge',
    'emoji': '⚖️',
    'brief': (
        "You are the hackathon judge. You do not accept assertions - you follow evidence traces. "
        "Your standard: every gap must be provable from the data; a plausible-but-unproven gap is a "
        "failure, and so is missing an obvious one."
    ),
}


def _stars(reviews: List[Dict]) -> str:
    s = [r['star'] for r in reviews if r.get('star') is not None]
    if not s:
        return "n/a"
    dist = {v: s.count(v) for v in sorted(set(s))}
    return f"avg {statistics.mean(s):.2f} [" + " ".join(f"{k}*:{v}" for k, v in dist.items()) + "]"


def build_facts(gaps: List[Dict], candidates: List[Dict], reviews: List[Dict],
                issues: List[Dict], clusters: List[Dict]) -> str:
    """Deterministic, pre-computed facts. Agents interpret these; they never recompute them."""
    reviews_by_id = {r['id']: r for r in reviews}
    issues_by_number = {i['number']: i for i in issues}
    L = []

    L.append("### CORPUS")
    L.append(f"Product: Orbot (guardianproject/orbot-android) vs reviews of org.torproject.android.")
    L.append(f"{len(issues)} roadmap issues, {len(reviews)} user reviews, "
             f"{len(clusters)} shared functional clusters.")
    open_issues = sum(1 for i in issues if i['state'] == 'open')
    completed = sum(1 for i in issues if i['state'] == 'closed' and i.get('state_reason') != 'not_planned')
    declined = sum(1 for i in issues if i['state'] == 'closed' and i.get('state_reason') == 'not_planned')
    milestoned = sum(1 for i in issues if i.get('milestone_title'))
    L.append(f"Issues: {open_issues} open, {completed} closed as COMPLETED (the team ships), "
             f"{declined} closed as NOT PLANNED (declined); {milestoned} have a milestone.")
    L.append("Verdict rules: no ticket above cosine 0.4 -> IGNORED. A match between 0.4 and 0.55 is "
             "only topical adjacency and can never earn COVERED. UNDER-PRIORITIZED requires the ticket "
             "to be open-and-stale or closed as not-planned; delivered work is never 'neglected backlog'.")
    all_stars = [r['star'] for r in reviews if r.get('star') is not None]
    if all_stars:
        dist = {v: all_stars.count(v) for v in sorted(set(all_stars))}
        L.append(f"Review ratings overall: avg {statistics.mean(all_stars):.2f}, "
                 + " ".join(f"{k}*:{v}" for k, v in dist.items()))

    L.append("\n### RANKING (verified - this ordering is correct by construction)")
    for i, g in enumerate(gaps, 1):
        delta = "" if i == 1 else f" (-{gaps[i-2]['confidence'] - g['confidence']:.1f} vs #{i-1})"
        L.append(f"#{i}  {g['confidence']:.1f}%{delta}  {g['verdict']:<18}  {g['need_text']}")
    if len(gaps) >= 2:
        L.append(f"Spread across top-5: {gaps[0]['confidence'] - gaps[-1]['confidence']:.1f} points. "
                 f"Ranking is strictly descending by confidence - there is no verdict-type override.")

    ranked = [c for c in candidates if c.get('confidence') is not None]
    if len(ranked) > len(gaps):
        nxt = ranked[len(gaps)]
        L.append(f"Highest excluded candidate: {nxt['confidence']:.1f}% \"{nxt['need_text']}\" "
                 f"- {gaps[-1]['confidence'] - nxt['confidence']:.1f} points below the #5 cutoff.")

    L.append("\n### SCORING FORMULA")
    L.append("confidence = 0.35*evidence_volume + 0.15*rating_spread + 0.25*consistency "
             "+ 0.25*effective_gap_certainty")
    L.append("effective_gap_certainty = base_verdict_weight * (0.4 + 0.6*consistency), where "
             "base weight is IGNORED 1.0 / UNDER-PRIORITIZED 0.75 / MISUNDERSTOOD 0.6.")
    L.append("The consistency dampening exists so a harsh verdict cannot mask weak evidence.")
    L.append("Evidence is expanded by cosine>=0.4 semantic search over ALL reviews, capped at 15.")
    L.append("A need with best issue-similarity < 0.4 is IGNORED; otherwise an LLM assigns "
             "COVERED / UNDER-PRIORITIZED / MISUNDERSTOOD.")

    L.append("\n### TOP-5 IN FULL (with complete evidence)")
    for rank, g in enumerate(gaps, 1):
        comp = g.get('confidence_components', {})
        ev = [reviews_by_id[i] for i in g.get('evidence_review_ids', []) if i in reviews_by_id]
        L.append(f"\n[#{rank}] {g['need_text']}")
        L.append(f"  verdict={g['verdict']}  confidence={g['confidence']:.1f}%")
        L.append(f"  components: volume={comp.get('evidence_count_norm')} "
                 f"spread={comp.get('rating_spread')} consistency={comp.get('cross_signal_consistency')} "
                 f"base_certainty={comp.get('roadmap_gap_certainty')} "
                 f"effective_certainty={comp.get('effective_gap_certainty')}")
        L.append(f"  evidence: {len(ev)} reviews, {100.0*len(ev)/max(len(reviews),1):.2f}% of corpus, "
                 f"ratings {_stars(ev)}")
        L.append(f"  stated rationale: {g.get('reasoning', '')}")
        if g.get('matched_issue_number'):
            iss = issues_by_number.get(g['matched_issue_number'])
            if iss:
                L.append(f"  matched issue #{iss['number']} \"{iss['title']}\" "
                         f"state={iss['state']}/{iss.get('state_reason')} "
                         f"milestone={iss.get('milestone_title') or 'NONE'} "
                         f"+1={iss.get('reactions_plus1', 0)} comments={iss.get('comments', 0)} "
                         f"created={iss.get('created_at')}")
        else:
            cl = issues_by_number.get(g.get('closest_issue_number'))
            if cl:
                L.append(f"  NO match. closest was #{cl['number']} \"{cl['title']}\" at similarity "
                         f"{g.get('closest_issue_similarity')} (threshold 0.4) state={cl['state']}")
        L.append("  reviews:")
        for r in ev:
            L.append(f"    [{r['id']}] {r.get('star','?')}* {r['review_text'][:200]}")

    other = [c for c in candidates if not c.get('in_top5')]
    ranked_other = [c for c in other if c.get('confidence') is not None]
    covered = [c for c in other if c.get('confidence') is None]
    L.append(f"\n### EXCLUDED CANDIDATES ({len(other)})")
    L.append(f"{len(ranked_other)} ranked below the cutoff, {len(covered)} dropped as already COVERED.")
    for c in ranked_other:
        L.append(f"  {c['confidence']:.1f}% {c['verdict']:<18} ev={len(c.get('evidence_review_ids', [])):>2} "
                 f"{c['need_text']}")
    L.append("  --- dropped as COVERED by the roadmap: ---")
    for c in covered:
        L.append(f"  issue #{c.get('matched_issue_number')}  {c['need_text']}")

    L.append("\n### CLUSTER BALANCE (roadmap attention vs user volume)")
    for c in sorted(clusters, key=lambda x: -x.get('review_count', 0)):
        L.append(f"  {c['label']}: {c.get('issue_count', 0)} issues / {c.get('review_count', 0)} reviews")

    return "\n".join(L)


class DebatePanel:
    def __init__(self, api_key: str = None, on_event: Optional[Callable] = None):
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        self.client = OpenAI(api_key=api_key)
        self.on_event = on_event or (lambda *a, **k: None)
        self.transcript: List[Dict] = []

    # ---- plumbing ----
    def _say(self, agent_key: str, label: str, emoji: str, round_no: int, phase: str,
             system: str, user: str, temperature: float = 0.6) -> str:
        resp = self.client.chat.completions.create(
            model=GEN_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
        )
        text = resp.choices[0].message.content.strip()
        entry = {'agent': agent_key, 'label': label, 'emoji': emoji,
                 'round': round_no, 'phase': phase, 'statement': text}
        self.transcript.append(entry)
        self.on_event(entry)
        return text

    def _transcript_text(self, limit: int = None) -> str:
        rows = self.transcript if limit is None else self.transcript[-limit:]
        return "\n\n".join(f"--- {e['label']} (round {e['round']}) ---\n{e['statement']}" for e in rows)

    def _system(self, brief: str, facts: str) -> str:
        return (
            "You are on an adversarial review panel auditing a 'Silent Stakeholder' analysis: it "
            "cross-analyses Orbot's GitHub roadmap against real user reviews to surface LATENT unmet "
            "needs - needs users never stated outright. The bar is: prove it from the data.\n\n"
            f"YOUR ROLE: {brief}\n\n"
            "HARD RULES:\n"
            "- The FACTS block is computed deterministically from the database. Every number and the "
            "ranking order in it are correct. Never recompute or dispute them; if your intuition "
            "disagrees with a number, you are wrong, not the number.\n"
            "- Cite review IDs like [1234] and issues like #1517. Never invent one.\n"
            "- Argue with the other panellists by name. Concede explicitly when they are right.\n"
            "- Be specific and compact. No preamble, no restating your role, no bullet-point padding.\n\n"
            f"=== FACTS ===\n{facts}"
        )

    # ---- phases ----
    def run(self, gaps, candidates, reviews, issues, clusters) -> Dict:
        facts = build_facts(gaps, candidates, reviews, issues, clusters)

        # Round 1 - opening reads, each specialist sees what came before
        for key, spec in PANEL.items():
            prior = self._transcript_text()
            prompt = (
                "ROUND 1 - opening statement.\n"
                "Give your independent read of this analysis from your role. Name the single thing "
                "that most concerns you and the single thing you think is strongest. Be concrete "
                "about which gap numbers and review IDs you mean.\n"
            )
            if prior:
                prompt += f"\nPanellists before you said:\n{prior}\n\nDo not repeat them - add or contest."
            self._say(key, spec['label'], spec['emoji'], 1, 'opening',
                      self._system(spec['brief'], facts), prompt)

        # Round 2 - cross-examination between specialists
        for key, spec in PANEL.items():
            prompt = (
                "ROUND 2 - cross-examination.\n\n"
                f"Full transcript so far:\n{self._transcript_text()}\n\n"
                "Respond directly to the other two panellists. Where do you disagree, and on what "
                "evidence? Where do you concede? If you think a top-5 gap should be replaced by an "
                "excluded candidate, name both and say why."
            )
            self._say(key, spec['label'], spec['emoji'], 2, 'cross',
                      self._system(spec['brief'], facts), prompt)

        # Round 3 - judge interrogates
        judge_q = self._say(
            'judge', JUDGE['label'], JUDGE['emoji'], 3, 'interrogation',
            self._system(JUDGE['brief'], facts),
            "ROUND 3 - interrogation.\n\n"
            f"Transcript:\n{self._transcript_text()}\n\n"
            "You have heard the panel. Put your three sharpest questions to them - the ones that "
            "would break this analysis if unanswered. Target the weakest gap, the shakiest verdict, "
            "and the ranking decision you find least defensible. Ask, do not rule yet.",
        )

        # Round 4 - specialists answer the judge
        for key, spec in PANEL.items():
            prompt = (
                "ROUND 4 - answer the judge.\n\n"
                f"The judge asked:\n{judge_q}\n\n"
                f"Transcript:\n{self._transcript_text(6)}\n\n"
                "Answer whichever of the judge's questions falls in your remit. Give the evidence "
                "chain, or concede the point plainly if you cannot."
            )
            self._say(key, spec['label'], spec['emoji'], 4, 'rebuttal',
                      self._system(spec['brief'], facts), prompt)

        # Round 5 - ruling
        ruling_text = self._say(
            'judge', JUDGE['label'], JUDGE['emoji'], 5, 'ruling',
            self._system(JUDGE['brief'], facts),
            "ROUND 5 - ruling.\n\n"
            f"Full transcript:\n{self._transcript_text()}\n\n"
            "Deliver your ruling. For each of the five gaps say whether it stands and why, in one "
            "or two sentences. Then state plainly whether this analysis would survive a live "
            "defence, and name what its defender must be ready for.",
        )

        rulings = self._structured_ruling(facts, gaps, ruling_text)

        return {
            'transcript': self.transcript,
            'facts': facts,
            'ruling_text': ruling_text,
            'rulings': rulings,
            'panel': {k: {'label': v['label'], 'emoji': v['emoji']} for k, v in PANEL.items()},
        }

    def _structured_ruling(self, facts: str, gaps: List[Dict], ruling_text: str) -> Dict:
        need_list = "\n".join(
            f"#{i} (current verdict {g['verdict']}): {g['need_text']}" for i, g in enumerate(gaps, 1)
        )
        prompt = (
            f"THE JUDGE'S RULING:\n{ruling_text}\n\nTHE FIVE GAPS:\n{need_list}\n\n"
            "Encode the ruling as JSON.\n\n"
            "The `ruling` field is NOT the gap's verdict. It records what the judge decided about "
            "the gap itself, and must be exactly one of:\n"
            "  UPHELD     - the judge let the gap stand as analysed\n"
            "  CONTESTED  - the judge let it stand but flagged a real doubt or wanted it reclassified\n"
            "  OVERTURNED - the judge rejected the gap or said it should be replaced\n\n"
            "`disputes` must list actual disagreements the panellists never resolved, quoted from the "
            "discussion. If every disagreement was settled, return an empty list - never echo this "
            "instruction back as text.\n\n"
            "Return exactly this shape:\n"
            '{"per_gap":[{"rank":1,"ruling":"UPHELD","note":"one sentence in the judge\'s own terms"}],'
            '"defensible":true,'
            '"headline":"one sentence summarising the ruling overall",'
            '"strongest_gap_rank":1,"weakest_gap_rank":5,'
            '"must_prepare_for":["concrete question the defender must answer"],'
            '"disputes":[]}'
        )
        try:
            resp = self.client.chat.completions.create(
                model=GEN_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            return {'per_gap': [], 'defensible': None, 'headline': f'(could not encode ruling: {e})',
                    'must_prepare_for': [], 'disputes': []}
