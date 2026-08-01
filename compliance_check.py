# -*- coding: utf-8 -*-
"""
Automated compliance audit against the hackathon brief.

Every requirement the judges score on is checked directly against the stored
analysis (not against documentation): the four required outputs per gap, the
reality of every evidence ID and issue number, ranking monotonicity, confidence
calibration, deterministic verdict guards, and cluster coverage (the answer to
"here's a gap you missed").

Run any time — read-only, no LLM calls, no cost:
    python compliance_check.py
"""
import json
import sqlite3
import sys
import io
from collections import Counter

from product import CURRENT

VALID_GAP_VERDICTS = ('IGNORED', 'UNDER-PRIORITIZED', 'MISUNDERSTOOD')
MATCH_FLOOR = 0.4
STRONG_MATCH_THRESHOLD = 0.55

results = []


def check(name: str, ok: bool, detail: str):
    results.append((ok, name, detail))


def run(db_path: str):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    reviews = {r['id'] for r in con.execute("SELECT id FROM reviews")}
    issues = {r['number']: dict(r) for r in con.execute(
        "SELECT number, state, state_reason FROM issues")}
    gaps = [dict(r) for r in con.execute("SELECT * FROM gaps ORDER BY rank")]
    cands = [dict(r) for r in con.execute("SELECT * FROM candidates")]
    clusters = [dict(r) for r in con.execute("SELECT * FROM clusters")]

    # -- Brief: "Pick ONE app. Pull its reviews AND its GitHub roadmap."
    check("One product, both sides", bool(issues) and bool(reviews),
          f"{len(issues)} roadmap issues + {len(reviews)} user reviews for {CURRENT.label}")

    # -- Brief: "TOP 3-5 unmet needs"
    check("Top 3-5 gaps", 3 <= len(gaps) <= 5, f"{len(gaps)} gaps ranked")

    # -- Brief: "For EVERY gap, produce all four" (need / confidence / evidence / verdict)
    for g in gaps:
        ev = json.loads(g.get('evidence_review_ids') or '[]')
        missing = []
        if not g.get('need_text'):
            missing.append('need')
        if g.get('confidence') is None:
            missing.append('confidence')
        if not ev:
            missing.append('evidence')
        if g.get('verdict') not in VALID_GAP_VERDICTS:
            missing.append('verdict')
        check(f"Gap #{g['rank']}: four required outputs", not missing,
              f"{g['verdict']}, {g['confidence']:.1f}%, {len(ev)} evidence ids"
              + (f" — MISSING {missing}" if missing else ""))

    # -- Brief: "Evidence trace ... by ID. No evidence, no gap." IDs must be real.
    for g in gaps:
        ev = json.loads(g.get('evidence_review_ids') or '[]')
        fake = [i for i in ev if i not in reviews]
        check(f"Gap #{g['rank']}: evidence IDs exist in corpus", not fake,
              "all real" if not fake else f"FABRICATED: {fake}")
        for field in ('matched_issue_number', 'closest_issue_number'):
            n = g.get(field)
            if n is not None and n not in issues:
                check(f"Gap #{g['rank']}: {field} exists", False, f"#{n} not in DB")

    # -- Brief: "Output ranked by strength of evidence, strongest first"
    confs = [g['confidence'] for g in gaps]
    check("Ranking monotonic (strongest first)",
          confs == sorted(confs, reverse=True),
          " > ".join(f"{c:.1f}" for c in confs))

    # -- Brief: "calibrated, not decorative. 90%-sure and 55%-sure must differ"
    allc = [c['confidence'] for c in cands if c.get('confidence') is not None]
    spread_ok = (max(confs) - min(confs)) > 2 and (max(allc) - min(allc)) > 15
    check("Confidence calibrated, not decorative", spread_ok,
          f"top-5 span {min(confs):.1f}-{max(confs):.1f}%, "
          f"all {len(allc)} candidates span {min(allc):.1f}-{max(allc):.1f}%")

    comp = json.loads(gaps[0].get('confidence_components') or '{}')
    check("Confidence formula components stored", len(comp) >= 4,
          f"{len(comp)} components per gap (auditable, not an LLM opinion)")

    # -- Deterministic verdict guards must hold on EVERY candidate
    violations = []
    for c in cands:
        v = c.get('verdict')
        sim = c.get('closest_issue_similarity')
        n = c.get('matched_issue_number')
        iss = issues.get(n) if n else None
        if v == 'IGNORED' and sim is not None and sim >= MATCH_FLOOR:
            violations.append(f"IGNORED with sim {sim}: {c['need_text'][:45]}")
        if v == 'COVERED' and not (
                sim is not None and sim >= STRONG_MATCH_THRESHOLD
                and iss and iss.get('state_reason') == 'completed'):
            violations.append(f"weak COVERED: {c['need_text'][:45]}")
        if v == 'UNDER-PRIORITIZED' and iss and iss.get('state_reason') == 'completed':
            violations.append(f"UNDER-PRIORITIZED on completed #{n}: {c['need_text'][:45]}")
    check("Verdict guards hold on all candidates", not violations,
          f"{len(cands)} candidates checked"
          + ("; " + "; ".join(violations) if violations else ""))

    covered_in_top = [c for c in cands if c.get('verdict') == 'COVERED' and c.get('in_top5')]
    check("COVERED excluded from ranking", not covered_in_top,
          f"{sum(1 for c in cands if c['verdict'] == 'COVERED')} covered kept for audit only")

    # -- Live-defense: "here's a gap you missed" — every cluster must be mined
    per_cluster = Counter(c['cluster_id'] for c in cands)
    unmined = [c['label'] for c in clusters if per_cluster.get(c['id'], 0) == 0]
    check("Every cluster mined for needs", not unmined,
          f"all {len(clusters)} functional clusters produced candidates"
          if not unmined else f"UNMINED clusters: {unmined}")

    # -- report
    passed = sum(1 for ok, _, _ in results if ok)
    print(f"\nCompliance audit — {CURRENT.label} ({db_path})")
    print("=" * 60)
    for ok, name, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        print(f"        {detail}")
    print("=" * 60)
    print(f"{passed}/{len(results)} checks passed")
    return passed == len(results)


if __name__ == '__main__':
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    ok = run(CURRENT.db_path)
    sys.exit(0 if ok else 1)
