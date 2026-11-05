"""Smoke tests — demo mode, end to end. No network, no API key.

Run:  python3 -m unittest discover -s tests -v
"""

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.pop("MODEL_API_KEY", None)  # force demo mode

from mortgage_os.analyzer import analyze_scenario, monthly_payment, triage_book
from mortgage_os.meta_client import MetaClient
from mortgage_os.penalty import estimate_penalty

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def load(name):
    with (SAMPLES / name).open(encoding="utf-8") as fh:
        return json.load(fh)


class TestPenaltyMath(unittest.TestCase):
    def test_three_months_interest(self):
        # $400,000 at 4% for 3 months = $4,000
        result = estimate_penalty(
            {
                "balance": 400000,
                "contract_rate_pct": 4.0,
                "posted_rate_pct": 4.0,
                "months_remaining": 12,
                "rate_type": "variable",
            }
        )
        self.assertAlmostEqual(result["three_months_interest"], 4000.00)
        self.assertAlmostEqual(result["estimated_penalty"], 4000.00)

    def test_fixed_penalty_is_greater_of_ird_and_three_months(self):
        result = estimate_penalty(load("scenario-04.json"))
        self.assertEqual(
            result["estimated_penalty"],
            max(result["interest_rate_differential"], result["three_months_interest"]),
        )
        self.assertGreater(result["interest_rate_differential"], result["three_months_interest"])


class TestPayments(unittest.TestCase):
    def test_zero_rate_is_straight_line(self):
        self.assertAlmostEqual(monthly_payment(120000, 0.0, 10), 1000.0)

    def test_payment_positive(self):
        self.assertGreater(monthly_payment(500000, 5.0, 20), 0)


class TestDemoEndToEnd(unittest.TestCase):
    def test_client_is_demo_without_key(self):
        self.assertTrue(MetaClient().demo_mode)

    def test_analyze_runs_in_demo_mode(self):
        brief = analyze_scenario(load("scenario-01.json"), MetaClient())
        self.assertEqual(brief["mode"], "demo")
        self.assertIn("DEMO MODE", brief["advisor_notes"])
        self.assertGreater(brief["penalty_estimate"]["estimated_penalty"], 0)
        self.assertIn("term_payment_difference", brief["offer_comparison"])

    def test_triage_ranks_most_urgent_first(self):
        book = [load(n) for n in sorted(os.listdir(SAMPLES))]
        rows = triage_book(book)
        self.assertEqual(rows[0]["days_to_maturity"], 41)
        self.assertEqual(rows[0]["priority"], "call this week")


if __name__ == "__main__":
    unittest.main()
