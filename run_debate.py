#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run the adversarial review panel over the current analysis.
Usage: python run_debate.py
"""
import sys
import os
import json
import time

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import GapAnalysisDB
from debate_orchestrator import DebatePanel
from product import CURRENT

# Per-product output: analyses of different products must never overwrite
# each other's panel rulings.
OUT = CURRENT.debate_path


def main():
    db = GapAnalysisDB()
    gaps = db.get_gaps()
    candidates = db.get_candidates()
    reviews = db.get_reviews()
    issues = db.get_issues()
    clusters = db.get_clusters()

    if not gaps:
        print("No gaps in the database. Run the analysis first.")
        return

    print(f"Panel input: {len(gaps)} gaps, {len(candidates)} candidates, "
          f"{len(reviews)} reviews, {len(issues)} issues, {len(clusters)} clusters\n")

    def on_event(entry):
        print(f"\n{'='*78}\n{entry['emoji']}  {entry['label']}  —  round {entry['round']} "
              f"({entry['phase']})\n{'='*78}\n{entry['statement']}\n")

    panel = DebatePanel(on_event=on_event)
    t0 = time.time()
    result = panel.run(gaps, candidates, reviews, issues, clusters)
    elapsed = time.time() - t0

    r = result['rulings']
    print(f"\n{'#'*78}")
    print(f"RULING  ({elapsed:.0f}s, {len(result['transcript'])} statements)")
    print('#'*78)
    print(f"\n{r.get('headline', 'n/a')}\n")
    print(f"Would survive live defence: {r.get('defensible')}")

    for pg in r.get('per_gap', []):
        print(f"  #{pg.get('rank')}  {pg.get('ruling', '?'):<11} {pg.get('note', '')}")

    if r.get('must_prepare_for'):
        print("\nMust be ready for:")
        for m in r['must_prepare_for']:
            print(f"  - {m}")

    if r.get('disputes'):
        print("\nUnresolved disagreements:")
        for d in r['disputes']:
            print(f"  - {d}")

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved -> {OUT}")


if __name__ == "__main__":
    main()
