# 🕵️ THE SILENT STAKEHOLDER — Hackathon Project

## 🎯 Mission Brief

Every product has a stakeholder who never files a ticket, never joins sprint planning, never gets a seat in the room: the user whose real need quietly diverges from what the team is building.

**Complaints are easy** — anyone can read a review.  
**Your job:** surface the needs users **DIDN'T say out loud** — and prove you're right.

---

## 📥 What We Work With

We assemble **two sides of ONE real product**:

1. **What the team is BUILDING** — roadmap / backlog
   - GitHub issues + milestones = planned features, epics, priorities
   
2. **What users are SIGNALING** — large, noisy corpus
   - Reviews, support tickets, feedback, churn notes
   - Expect contradictions, duplicates, sarcasm, conflicting requests
   - Cutting through that noise is part of the work

### Data Sources Used

- **Product:** `guardianproject/orbot-android` (GitHub roadmap)
- **Reviews:** `org.torproject.android` from `sealuzh/app_reviews` (HuggingFace dataset)
- **Scope:** 932 GitHub issues + 2329 reviews from same app

---

## 🛠️ What We Build

An AI system that reads across both sources and surfaces the **TOP 3–5 unmet needs** the roadmap is missing or under-serving.

### ⚠️ Not a Summarizer

Listing frequent complaints scores poorly. Value is inferring **LATENT needs** — the ones that only show up as second-order patterns.

### Required Output for EVERY Gap

```
🔹 The need            → clearly, in user's terms
🔹 Confidence score    → calibrated, justified (90% vs 55% must differ visibly)
🔹 Evidence trace      → linked to specific signals by ID (no evidence = no gap)
🔹 Gap verdict         → IGNORED / UNDER-PRIORITIZED / MISUNDERSTOOD
```

Ranked by strength of evidence (strongest first).

---

## ⚖️ Scoring Criteria

### ✅ Correctness & Rigor
- Every gap must be **provable from data**
- Judges follow evidence trace
- Plausible-but-wrong gaps hurt; missing obvious ones hurt

### 🎤 Live Defense
- **"Why rank this #1?"** → must answer immediately
- **"Here's a gap you missed — why?"** → must have reasoning
- **"Defend this confidence score"** → must justify numbers
- If you can't reason about output → you built a demo, not a system

---

## 🏆 The Bar

Anyone can tell us what users complained about.  
**WIN by telling us what users needed and never said — and proving it from the data.**

---

## 🏗️ Architecture

### Main Pipeline: `gap_analyzer.py`

1. **Embedding** — local `sentence-transformers` (all-MiniLM-L6-v2), no quota limits
2. **Clustering** — KMeans to build shared taxonomy of issues + reviews
3. **Latent Need Extraction** — LLM-based, requires second-order signals
4. **Matching & Verdict** — global semantic match + LLM classification
5. **Confidence Scoring** — 4-component weighted formula (not LLM opinion)
   - Evidence volume (35%) — log(supporting_reviews)
   - Rating spread (15%) — diversity of star ratings
   - Consistency (25%) — semantic similarity across reviews
   - Roadmap gap certainty (25%) — verdict type weight

### Post-Pipeline: Multi-Turn Debate (Version 1)

After main pipeline produces 5 gaps + candidates, run 4-round debate between two agents:

**Round 1: Evidence Validator**
- Assesses top-5 evidence (verify review IDs exist)
- Validates confidence calculations (are 4 components justified?)
- Checks verdict classifications (IGNORED/UNDER-PRIORITIZED/MISUNDERSTOOD)
- Spot-checks non-top-5 candidates

**Round 2: Challenger**
- Questions ranking ("why #1 at 67.9% vs #2 at 66.4%?")
- Challenges runner-ups ("why not candidate #6?")
- Identifies suspicious patterns or hallucinations
- Proposes alternative interpretations

**Round 3: Evidence Validator Responds**
- Defends each point from Round 2
- Explains component trade-offs
- Concedes if challenger found real issue

**Round 4: Challenger Final Check**
- Confirms validation or escalates concern
- Prepares talking points for live defense

**Consensus:** Final agreement on whether top-5 is defensible + reasoning documented

**Output:** `debate_result.json` with:
- `rounds`: all 4 agent statements
- `consensus`: {top_5_valid, confidence_justified, verdicts_sound, main_finding, concerns, ready_for_live_defense}
- `live_defense_talking_points`: prepared answers for judge questions

**UI Integration:** Streamlit dashboard displays debate metrics + debate rounds + talking points

---

## 📊 Current Results

| Rank | Need | Verdict | Confidence | Issue |
|------|------|---------|------------|-------|
| 1 | Clarity and education on how to safely navigate the deep web | IGNORED | 72.3% | — |
| 2 | Clear communication about expected speed and performance | UNDER-PRIORITIZED | 71.2% | #1772 (open) |
| 3 | More intuitive UI and reduced complexity | MISUNDERSTOOD | 68.5% | #116 (closed) |
| 4 | Improved connectivity and faster connection times | MISUNDERSTOOD | 68.1% | #68 (closed) |
| 5 | Need for improved speed and performance | IGNORED | 67.8% | — |

Every gap carries 15 evidence reviews. **41 candidates total** — verdict mix:
IGNORED 10 · UNDER-PRIORITIZED 3 · MISUNDERSTOOD 22 · COVERED 6 (excluded from ranking, kept for audit).

---

## 🧑‍⚖️ The Verdict Bug the Panel Caught (the big one)

The four-agent panel's most valuable finding. The original verdict logic looked only at whether a
matching issue existed — never at **what the team actually did with it**. Consequences:

**Bug 1 — closed tickets labelled "neglected backlog".** 16 of 18 UNDER-PRIORITIZED gaps pointed at
*closed* issues. Calling a closed ticket "stale backlog the team is ignoring" is simply false.

**Bug 2 — no distinction between "shipped" and "declined".** `state_reason` was never fetched. Once
added: **838 issues closed as `completed`** (this team genuinely ships), **13 as `not_planned`**
(consciously declined), 81 open. Those are completely different facts about the roadmap.

**Bug 3 — coverage claimed on weak matches.** COVERED verdicts had a median cosine of only **0.53**,
many at 0.40–0.45. A 0.42 cosine on short text means "same topic area", not "same problem" — claiming
the roadmap *covers* a need on that basis is indefensible.

### The corrected rule

| Evidence about the roadmap | Verdict |
|---|---|
| No issue above cosine 0.40 | **IGNORED** — never even framed |
| Match 0.40–0.55 (topical adjacency only) | **MISUNDERSTOOD** — COVERED is unavailable at this strength |
| Open, stale, no milestone | **UNDER-PRIORITIZED** |
| Closed as `not_planned` | **UNDER-PRIORITIZED** — seen and declined; COVERED unavailable, nothing shipped |
| Closed as `completed`, strong match, right framing | **COVERED** — excluded from ranking |
| Closed as `completed`, but framed around a different problem | **MISUNDERSTOOD** — the need survives the fix |

Enforced by deterministic guards in `gap_analyzer.match_and_verdict`, not left to the LLM's discretion:
ticket state and match strength are facts, so the code overrides the model when it strays.

### ⚠️ Temporal caveat — know this before the defence

The review corpus is from **2016**; the roadmap runs 2016→2026. So "the roadmap never served this"
means *not in ten years*. A judge may fairly ask whether a 2016 complaint was fixed later — the
`completed` + strong-match → COVERED path is exactly how that is handled, and 6 needs were excluded
on those grounds. Say this openly rather than being caught by it.

### 🔍 Evidence Expansion (post-fix)

**Problem:** Initial evidence trace only had 3-6 review IDs per gap — the LLM only saw a
capped ~60-review sample per cluster during need extraction, so real corroborating evidence
elsewhere in the 2329-review corpus was invisible.

**Fix:** `expand_evidence.py` — after need extraction, do a local (free, no LLM) semantic
search across ALL reviews for each need, union with the LLM's original picks, cap at 15,
similarity threshold 0.4. Also computes `closest_issue_number`/`similarity` even for IGNORED
verdicts (previously showed nothing) so the UI can display "closest issue considered, but
below match threshold" instead of a blank section.

**Validation:** Spot-checked new #1 ("deep web browsing guidance", 77.2%, 15 reviews) —
every review genuinely mentions "deep web" with a consistent theme (danger warnings,
confusion on how to use it, privacy concerns). Not noise; a stronger, better-evidenced
signal than before. Ranking shifted substantially since evidence volume is now a much
more meaningful signal (previously 3-6 reviews barely differentiated gaps).

**All candidates:** 33 total (24 real gaps ranked 33.5%–61.6% + 9 COVERED, excluded from ranking but kept for traceability)
**Candidates table:** Stored in DB with in_top5 flag for live defense traceability

### 🔧 Confidence Formula Fix (post-debate, round 1)

**Bug found by Multi-Turn Debate (Challenger agent):** `roadmap_gap_certainty` was a fixed
value per verdict type (IGNORED=1.0 always), independent of how consistent the supporting
evidence actually was. This let a weak-evidence IGNORED gap (consistency=0.38) outrank a
well-evidenced UNDER-PRIORITIZED gap (consistency=0.58) — Gap #1 (67.9%) beat Gap #2 (66.4%)
purely on verdict severity, not evidence strength.

**Fix:** `effective_gap_certainty = base_gap_certainty * (0.4 + 0.6 * consistency)` — a harsh
verdict can no longer fully mask weak, inconsistent evidence. See `gap_analyzer.py::compute_confidence`.

**Result:** Two former runner-ups ("Improved reliability and connection speed", "Improved
functionality in the new version" — previously #6/#7 at 61.7%/61.5%) now correctly enter
top-5, displacing the two weakest-consistency IGNORED gaps. Ranking is now strictly
monotonic with confidence (61.6% > 60.2% > 59.0% > 58.6% > 56.8%) — no verdict-type bypass.

**Second debate round (validation):** Re-ran the 4-round debate on the fixed ranking.
Math inconsistency is gone, but note: **the Challenger agent itself made a factual error**
in round 2 (claimed Gap #1 was ranked above #2/#3 "despite a lower confidence score" — false,
61.6% is in fact the highest). Its `top_5_valid: false` verdict rests partly on that error —
do not treat debate-agent output as ground truth without a human sanity check.

The one *legitimate* concern that survived: Gap #1 ("reliable connection status indicators")
is an inferred latent need — reviews complain about connectivity generally but don't
explicitly ask for status indicators. That's the intended behavior (latent need extraction,
not complaint summarization per the brief), but be ready to explain that inference chain live.

---

## 🚀 Next Steps

### Immediate
- [ ] Run Multi-Turn Debate (Version 1) between Evidence Validator + Challenger agents
- [ ] Validate top-5 + collect counter-arguments for live defense
- [ ] Spot-check 2–3 evidence traces manually

### If Time Permits
- [ ] Add Adversarial Agent (Version 5) — devil's advocate
- [ ] Run Ensemble approach (Version 2) — 2–3 runs with different hyperparameters
- [ ] Build confidence distribution visualization for judges

### Pre-Defense
- [ ] Verify all review IDs and issue numbers exist
- [ ] Test Streamlit UI rendering (metrics, gap cards, candidates table)
- [ ] Prepare talking points for each gap + counter-arguments
- [ ] Practice live defense scenarios

---

## 💰 Cost Notes

- **Embeddings:** Free (local sentence-transformers)
- **LLM calls:** gpt-4o-mini only (~0.15¢ per run, including debate agents)
- **Budget:** $5 OpenAI → plenty of margin

---

## 🔐 Key Files

- `gap_analyzer.py` — Core pipeline (embed, cluster, extract needs, expand evidence, match, confidence)
- `database.py` — SQLite persistence (issues, reviews, clusters, gaps, candidates)
- `app.py` — Streamlit dashboard (bilingual EN/RU, gap cards, grounded chat, analyst mode)
- `project_chat.py` — Grounded Q&A: builds an evidence-rich context from the DB so the
  assistant can answer judge questions citing real review IDs / issue numbers
- `debate_orchestrator.py` + `run_debate.py` — 4-round adversarial audit of the results
- `expand_evidence.py` — Retrofit evidence expansion onto already-stored candidates (no LLM cost)
- `recompute_confidence.py` — Recompute scores from stored components after a formula change
- `i18n.py` — Translation dictionary (EN/RU, 80 keys, parity-checked)
- `github_client.py` — Fetch from guardianproject/orbot-android
- `reviews_source.py` — Fetch org.torproject.android from sealuzh/app_reviews

## 🎨 UI Design

Default view is deliberately minimal — only what a judge needs to evaluate the claim:
hero framing, then five gap cards (rank, need, verdict pill, confidence bar, key stats,
and two expanders: evidence trace + score breakdown), then the chat.

Everything else lives behind the **Analyst mode** toggle in the sidebar: all candidates,
the shared taxonomy chart, the adversarial debate, and raw issue/review/milestone tables.
This keeps the main page defensible-at-a-glance while the full audit trail stays one click away.

---

## 📝 Rules

✅ **DO:**
- Prove every gap from data (evidence trace)
- Justify confidence scores (formula, not guessing)
- Be ready to defend on the spot
- Show all work (gap reasoning, verdict logic, evidence list)

❌ **DON'T:**
- Summarize complaints (only latent needs)
- Make up review IDs or issue numbers
- Use decorative confidence (50% for everything)
- Skip live defense scenarios (judges will ask)

---

## 🕐 Timeline

- **Deadline:** Tomorrow 12:00
- **Now:** Multi-turn debate implementation + validation (done, see debate_result.json)
- **Next:** Resolve debate concerns (ranking inconsistency, IGNORED harshness, runner-up threshold)
- **Then:** Visual UI test in browser, live defense prep
- **Optional (time permitting):** Ensemble validation (Version 2), Adversarial agent (Version 5)
- **Defense:** Answer "why #1?", "why not X?", "defend confidence" in real-time

Good luck. 🔥
