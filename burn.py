#!/usr/bin/env python3
"""Batch credit-burn runner.

Processes every synthetic renewal scenario in a folder through Muse
Spark on the Meta Model API, writes one brief per scenario to
outputs/, and keeps a running token/cost tally in outputs/summary.json.

This is deliberate, useful work per call — a real renewal brief for
each scenario — and it is how the hackathon API credit is spent
productively once a key exists. A spend cap stops the run before the
tally passes the budget.

A live key is required. Without MODEL_API_KEY this script refuses to
run: a "burn" in demo mode would spend nothing and prove nothing.

Usage:
    MODEL_API_KEY=... python3 burn.py --input samples/ --cap-usd 150
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from mortgage_os.analyzer import analyze_scenario
from mortgage_os.meta_client import MetaClient, estimate_cost_usd


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-run scenarios through Muse Spark")
    parser.add_argument("--input", default="samples", help="folder of scenario JSON files")
    parser.add_argument("--out", default="outputs", help="output folder")
    parser.add_argument("--cap-usd", type=float, default=150.0, help="stop before exceeding this spend")
    parser.add_argument("--repeat", type=int, default=1, help="passes over the folder")
    args = parser.parse_args()

    client = MetaClient()
    if client.demo_mode:
        print(
            "ERROR: MODEL_API_KEY is not set. burn.py only runs live — "
            "it exists to spend real API credit on real briefs.",
            file=sys.stderr,
        )
        return 2

    files = sorted(Path(args.input).glob("*.json"))
    if not files:
        print(f"ERROR: no scenario JSON files in {args.input}", file=sys.stderr)
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    totals = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "est_cost_usd": 0.0}
    run_log = []

    for pass_no in range(1, args.repeat + 1):
        for path in files:
            if totals["est_cost_usd"] >= args.cap_usd:
                print(f"Spend cap ${args.cap_usd:.2f} reached — stopping.")
                _write_summary(out_dir, totals, run_log, capped=True)
                return 0
            with path.open("r", encoding="utf-8") as fh:
                scenario = json.load(fh)
            started = time.time()
            brief = analyze_scenario(scenario, client)
            cost = estimate_cost_usd(brief["usage"])
            totals["calls"] += 1
            totals["prompt_tokens"] += brief["usage"].get("prompt_tokens", 0)
            totals["completion_tokens"] += brief["usage"].get("completion_tokens", 0)
            totals["est_cost_usd"] = round(totals["est_cost_usd"] + cost, 6)

            name = f"{path.stem}-pass{pass_no}.brief.json"
            with (out_dir / name).open("w", encoding="utf-8") as fh:
                json.dump(brief, fh, indent=2)
            run_log.append(
                {
                    "file": name,
                    "borrower": brief["borrower"],
                    "seconds": round(time.time() - started, 2),
                    "usage": brief["usage"],
                    "est_cost_usd": round(cost, 6),
                    "running_total_usd": totals["est_cost_usd"],
                }
            )
            print(
                f"[{totals['calls']}] {name}  "
                f"in={brief['usage'].get('prompt_tokens', 0)} "
                f"out={brief['usage'].get('completion_tokens', 0)}  "
                f"call=${cost:.4f}  total=${totals['est_cost_usd']:.4f} / cap ${args.cap_usd:.2f}"
            )

    _write_summary(out_dir, totals, run_log, capped=False)
    print(f"Done. {totals['calls']} briefs, estimated total ${totals['est_cost_usd']:.4f}.")
    return 0


def _write_summary(out_dir: Path, totals: dict, run_log: list, capped: bool) -> None:
    with (out_dir / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump({"totals": totals, "stopped_at_cap": capped, "runs": run_log}, fh, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
