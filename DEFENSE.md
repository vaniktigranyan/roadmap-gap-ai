# Live Defence Cheat Sheet — Orbot

> Generated from `gaps_org_torproject_android.db`. Every figure below is straight from the data.

## The 30-second answer to "what did you build?"

We cross-analysed **932 roadmap issues** from `guardianproject/orbot-android` against **2329 real user reviews**, and surfaced the needs users never stated outright. We found **41 candidate needs**, ranked the top 5, and — this is the finding — measured how long the roadmap took to answer each one. **2 of 5 were never framed as a ticket at all.** The worst wait was **9y 6m**.

## The five needs, with the answer to "why this rank?"

| # | Need | Verdict | Conf. | Evidence | Roadmap response |
|---|---|---|---|---|---|
| 1 | Users are looking for clarity and education on how to safe | IGNORED | 72.3% | 15 reviews | **never** (closest #570, sim 0.35) |
| 2 | Users want clear communication and transparency about expe | UNDER-PRIORITIZED | 71.2% | 15 reviews | #1772 after 9y 6m (open) |
| 3 | More intuitive user interface and reduced complexity in VP | MISUNDERSTOOD | 68.5% | 15 reviews | #116 after 8m (resolved) |
| 4 | Improved connectivity and faster connection times when usi | MISUNDERSTOOD | 68.1% | 15 reviews | #68 after 20d (resolved) |
| 5 | Need for improved speed and performance | IGNORED | 67.8% | 15 reviews | **never** (closest #473, sim 0.32) |

**Ranking is strictly by confidence** — 72.3 > 71.2 > 68.5 > 68.1 > 67.8. No verdict-type override: a harsh verdict cannot jump the queue.

## Per-need talking points

### #1 — Users are looking for clarity and education on how to safely navigate the deep web while minimizing risks.
- **Verdict IGNORED, confidence 72.3%**
- Score = 0.35×0.807 (volume) + 0.15×0.667 (rating spread) + 0.25×0.601 (consistency) + 0.25×0.76 (gap certainty)
- **15 reviews** back it (0.64% of corpus), average rating 4.5★
  - *Use this:* average 4.5★ means this is **not** angry 1-star venting — satisfied users are asking for it too.
- Users voiced it **Mar 2016 – Apr 2017**
- **The roadmap never opened a ticket for this.** Nearest is #570 at similarity 0.35, below our 0.40 match floor, and it only appeared Jan 2022.
- Sample evidence: `[4354]`, `[2947]`, `[3426]`, `[2501]`, `[2693]`, `[3015]`

### #2 — Users want clear communication and transparency about expected speeds and performance, as many seem confused about Tor’s inherent slowness versus their app’s performance.
- **Verdict UNDER-PRIORITIZED, confidence 71.2%**
- Score = 0.35×0.807 (volume) + 0.15×1.0 (rating spread) + 0.25×0.564 (consistency) + 0.25×0.554 (gap certainty)
- **15 reviews** back it (0.64% of corpus), average rating 4.2★
  - *Use this:* average 4.2★ means this is **not** angry 1-star venting — satisfied users are asking for it too.
- Users voiced it **Dec 2015 – Jan 2017**
- Ticket #1772 opened Jul 2026 — **9y 6m after** users spoke; status *open*
- Sample evidence: `[3297]`, `[3621]`, `[2727]`, `[3144]`, `[2411]`, `[3565]`

### #3 — More intuitive user interface and reduced complexity in VPN configuration.
- **Verdict MISUNDERSTOOD, confidence 68.5%**
- Score = 0.35×0.807 (volume) + 0.15×1.0 (rating spread) + 0.25×0.565 (consistency) + 0.25×0.443 (gap certainty)
- **15 reviews** back it (0.64% of corpus), average rating 4.3★
  - *Use this:* average 4.3★ means this is **not** angry 1-star venting — satisfied users are asking for it too.
- Users voiced it **Jan 2016 – Apr 2017**
- Ticket #116 opened Jan 2018 — **8m after** users spoke; status *resolved*, closed Nov 2020
- Sample evidence: `[4512]`, `[3136]`, `[3808]`, `[4609]`, `[3078]`, `[2566]`

### #4 — Improved connectivity and faster connection times when using Tor network.
- **Verdict MISUNDERSTOOD, confidence 68.1%**
- Score = 0.35×0.807 (volume) + 0.15×1.0 (rating spread) + 0.25×0.553 (consistency) + 0.25×0.439 (gap certainty)
- **15 reviews** back it (0.64% of corpus), average rating 3.7★
  - *Use this:* average 3.7★ means this is **not** angry 1-star venting — satisfied users are asking for it too.
- Users voiced it **Dec 2015 – Mar 2017**
- Ticket #68 opened Mar 2017 — **20d after** users spoke; status *resolved*, closed Nov 2020
- Sample evidence: `[2656]`, `[3072]`, `[3297]`, `[3814]`, `[3895]`, `[2961]`

### #5 — Need for improved speed and performance
- **Verdict IGNORED, confidence 67.8%**
- Score = 0.35×0.807 (volume) + 0.15×1.0 (rating spread) + 0.25×0.364 (consistency) + 0.25×0.619 (gap certainty)
- **15 reviews** back it (0.64% of corpus), average rating 4.0★
  - *Use this:* average 4.0★ means this is **not** angry 1-star venting — satisfied users are asking for it too.
- Users voiced it **Dec 2015 – Nov 2016**
- **The roadmap never opened a ticket for this.** Nearest is #473 at similarity 0.32, below our 0.40 match floor, and it only appeared Jun 2021.
- Sample evidence: `[2817]`, `[2786]`, `[3873]`, `[2571]`, `[3757]`, `[3566]`

## The questions they will actually ask

### "Your reviews are from 2016. Isn't this obsolete?"
Say it before they do. The corpus runs **Dec 2015 – May 2017**; the roadmap runs to 2026. That asymmetry is not a weakness — it is the measurement. **889 of the 932 issues were opened after the last review**, so we can state exactly how long each need waited. And when the team *did* eventually ship a fix, we credit it: **6 needs were excluded as COVERED** for that reason.

### "Why rank #1 first and not #2?"
Purely on confidence: **72.3% vs 71.2%**. #1 is ahead on consistency (0.601 vs 0.564) and gap certainty (0.76 vs 0.554). #2 is actually ahead on rating spread (0.667 vs 1.0) — concede that, then point out it is outweighed. The decisive factor: #1 has **no ticket at all**, while #2 has one that is merely late.

### "What about the gap you missed / why isn't X in the top 5?"
Open **Analyst mode → All candidates**. We kept every one of the **41** needs we found, with its score and evidence, precisely so this question has an answer.
Coverage is systematic, not selective: **all 14 of 14 functional clusters** in the shared taxonomy were mined and every one produced candidates — no area of the corpus was skipped. If a proposed "missed gap" is real, it is either in the candidates table with a score explaining its rank, or it lacks evidence in this corpus.
The nearest miss was *"Users need assurance that their data and identity are fully protected "* at **66.7%** — 1.1 points below the #5 cutoff.

### "Defend that confidence score — why not 90%?"
Because the formula will not award it on this evidence. The top score here is **72.3%**. To reach 90% a need would have to be backed by ~30 reviews spanning every star rating, with high semantic consistency, **and** have no roadmap ticket at all. Nothing in this corpus clears that bar — which is the point of a calibrated score rather than a decorative one.

### "Isn't this just summarising complaints?"
No — and the difference is visible in the wording. A complaint is *"it's slow"*. The need we extract is *why* that matters and what would resolve it. Each need is required to rest on second-order signals — workarounds, comparisons, contradictions — across multiple reviews, never a single one.

### "How do I know the evidence is real?"
Every review ID on screen is clickable back to its full text in **Raw data**, and the issue numbers link to GitHub. Pick any one and check it live. Better yet, run `python compliance_check.py` — an 18-point automated audit that re-verifies every evidence ID, issue number, verdict guard and the ranking order straight from the database, in seconds, with no LLM involved.

## Verdict logic (asked when they see the mix)

Current mix across all 41 candidates: **COVERED** 6 · **IGNORED** 10 · **MISUNDERSTOOD** 22 · **UNDER-PRIORITIZED** 3

| Evidence about the roadmap | Verdict |
|---|---|
| No ticket above cosine 0.40 | IGNORED — never even framed |
| Match 0.40–0.55 (same topic, different problem) | MISUNDERSTOOD — COVERED unavailable |
| Open, stale, no milestone | UNDER-PRIORITIZED |
| Closed as `not_planned` | UNDER-PRIORITIZED — seen and declined |
| Closed as `completed`, strong match | COVERED — excluded from ranking |
| Closed as `completed`, wrong framing | MISUNDERSTOOD — the need survives the fix |

These are **deterministic guards in code**, not LLM discretion — ticket state and match strength are facts, so the code overrides the model when it strays.

## The adversarial panel (if they ask how you validated)

Four agents — User Advocate, Roadmap Owner, Evidence Auditor and a Judge — argued across 5 rounds (11 statements). Verdict per need: #1 **UPHELD** · #2 **UPHELD** · #3 **UPHELD** · #4 **UPHELD** · #5 **OVERTURNED**

The panel flagged these for you specifically:
- How to support the educational gap's robustness amidst varying user perceptions of its urgency?

**Be honest about this:** the panel is a reviewer, not an oracle. In an earlier round an agent miscompared two numbers and raised a false alarm. That is exactly why every figure it sees is now precomputed in Python — the agents interpret, they never calculate.

## "Did you find any bugs in your own method?" — say yes

This is a strength, not an admission. The panel caught three real defects:

1. **Closed tickets labelled neglected backlog.** 16 of 18 UNDER-PRIORITIZED gaps pointed at *closed* issues. Calling a closed ticket "stale backlog" is simply false.
2. **No distinction between shipped and declined.** We were not reading `state_reason`. Once added: **838 issues closed as completed** (this team ships), **13 as not_planned**.
3. **Coverage claimed on weak matches.** COVERED verdicts had a median cosine of only **0.53**. A 0.42 match means "same topic area", not "same problem".

All three are fixed, and the ranking changed as a result.

## "Does this only work for this one app?"

No. The catalogue holds **21 verified products** — each needs both a large review corpus and a real GitHub issue tracker. We have already run the full pipeline on **3** of them:

- **PPSSPP** — `hrydgard/ppsspp` (source: `sealuzh`)
- **WordPress for Android** — `wordpress-mobile/WordPress-Android` (source: `sealuzh`)
- **Orbot** — `guardianproject/orbot-android` (source: `sealuzh`)

Switch products from the sidebar and press Re-run. Nothing is hardcoded: the product is resolved once in `product.py` and flows into the review query, the GitHub fetch, every LLM prompt, the database filename and the UI.

## "Why not use all five datasets from the brief?"

Because three of them **cannot** satisfy the brief's own "same product, both sides" rule, and we verified that rather than assuming:

- **Trustpilot (123k)** — checked all 1,579 companies; every one is UK retail/services, none has a public issue tracker.
- **Tobi-Bueck support tickets** — the columns are subject/body/queue only. The tickets **name no product**, so they cannot be paired with any roadmap.
- **Kaggle 200k tickets** — the API returns 403 without credentials, so the schema is unverifiable.

The two that *can* identify a product are both wired in: `sealuzh` (most products) and `play2025` (Bluesky). `sources.py` is a registry — adding a sixth dataset is one function.

---

## Final checklist before you present

- [ ] App running at http://localhost:8501
- [ ] Language set the way you want it
- [ ] Analyst mode toggle tested (candidates / panel / raw data all load)
- [ ] Chat tested with one question
- [ ] You can name need #1 and its evidence count from memory
- [ ] You can say the headline: *2 of 5 needs were never framed; the worst wait was 9y 6m*