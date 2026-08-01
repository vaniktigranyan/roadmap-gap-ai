# TODO — final state before submission

## Done
- [x] Multi-turn debate → upgraded to 4-agent adversarial panel (4/5 upheld, defensible=True)
- [x] Confidence formula fix (verdict severity can no longer mask weak evidence)
- [x] Evidence expansion to 15 reviews per gap (semantic search over full corpus)
- [x] Verdict guards: state_reason-aware, deterministic, 0 violations on 41 candidates
- [x] Response-latency timeline (headline: 2/5 never ticketed, worst 9y 6m)
- [x] Multi-product support (Orbot, PPSSPP, WordPress, AlarmClock analysed; Bluesky via play2025)
- [x] `compliance_check.py` — 18/18 brief requirements verified from the DB
- [x] `DEFENSE.md` regenerated with cluster-coverage answer
- [x] EN/RU parity (0 mismatches), tooltips on all hero stats
- [x] Per-product debate files; cross-product fallback bug removed
- [x] README.md written

## Before the demo (manual, in the browser)
- [ ] Open http://localhost:8501 — check gap cards, evidence expanders, candidates table
- [ ] Toggle language EN → RU, spot-check labels
- [ ] Switch product dropdown to PPSSPP and back (panel section must show "no panel yet", not Orbot's)
- [ ] Skim DEFENSE.md once more before going in

## Live defense crib
- Why #1? Highest confidence 72.3%, no ticket at all (nearest #570 only 0.35 similar)
- Missed gap? All 14 clusters mined; all 41 candidates kept with scores — show Analyst mode
- Old data? That's the point: latency is measurable; "fixed later" is handled by COVERED (6 excluded)
- Evidence real? Run `python compliance_check.py` in front of them
