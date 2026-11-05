#!/usr/bin/env python3
"""Mortgage OS — Renewal Radar Reimagined (command line).

Usage:
    python3 app.py analyze samples/scenario-01.json
    python3 app.py penalty samples/scenario-01.json
    python3 app.py triage samples/

Without a MODEL_API_KEY environment variable the analyzer runs in
DEMO mode: all numbers are computed locally for real, and the advisor
narrative is a canned, clearly-labelled text. With a key set, the
narrative comes from Muse Spark on the Meta Model API.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mortgage_os.analyzer import analyze_scenario, triage_book
from mortgage_os.meta_client import MetaClient
from mortgage_os.penalty import estimate_penalty


def load_scenario(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_book(folder: Path) -> list[dict]:
    return [load_scenario(p) for p in sorted(folder.glob("*.json"))]


def cmd_analyze(args: argparse.Namespace) -> int:
    scenario = load_scenario(Path(args.scenario))
    client = MetaClient()
    client.resolve_model()
    brief = analyze_scenario(scenario, client)
    print(json.dumps(brief, indent=2))
    if brief["mode"] == "demo":
        print(
            "\n[DEMO MODE] No MODEL_API_KEY set — numbers are real local "
            "math, narrative is canned. Set MODEL_API_KEY to run Muse "
            "Spark live.",
            file=sys.stderr,
        )
    return 0


def cmd_penalty(args: argparse.Namespace) -> int:
    scenario = load_scenario(Path(args.scenario))
    print(json.dumps(estimate_penalty(scenario), indent=2))
    return 0


def cmd_triage(args: argparse.Namespace) -> int:
    scenarios = load_book(Path(args.folder))
    print(json.dumps(triage_book(scenarios), indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Mortgage OS — renewal tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p_an = sub.add_parser("analyze", help="full renewal brief for one scenario")
    p_an.add_argument("scenario")
    p_an.set_defaults(func=cmd_analyze)

    p_pe = sub.add_parser("penalty", help="prepayment-penalty explainer only")
    p_pe.add_argument("scenario")
    p_pe.set_defaults(func=cmd_penalty)

    p_tr = sub.add_parser("triage", help="rank a folder of scenarios by urgency")
    p_tr.add_argument("folder")
    p_tr.set_defaults(func=cmd_triage)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
