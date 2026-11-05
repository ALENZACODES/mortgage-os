"""Renewal scenario analysis.

Combines local, deterministic mortgage math (penalty estimate, payment
math, offer comparison) with a Muse Spark narrative brief from the
Meta Model API. In demo mode the narrative is a canned, clearly
labelled text; every number in the brief is still computed locally.
"""

from __future__ import annotations

import json

from .meta_client import MetaClient
from .penalty import estimate_penalty

SYSTEM_PROMPT = (
    "You are a Canadian mortgage renewal analyst inside a broker's "
    "operating system. You write plain, specific renewal briefs for a "
    "licensed mortgage broker to review before speaking with a client. "
    "You never give regulated advice as a final decision; you lay out "
    "options, numbers, risks, and questions. Use Canadian context: "
    "stress test (B-20), IRD and three-months-interest penalties, "
    "fixed vs variable trade-offs, amortization, and lump-sum "
    "prepayment privileges. Be concise and concrete."
)


def monthly_payment(balance: float, annual_rate_pct: float, amortization_years: float) -> float:
    """Canadian mortgage payment (semi-annual compounding), monthly pay."""
    if balance <= 0 or amortization_years <= 0:
        return 0.0
    j2 = annual_rate_pct / 100.0
    i = (1 + j2 / 2) ** (2 / 12) - 1  # equivalent monthly rate
    n = int(round(amortization_years * 12))
    if i == 0:
        return balance / n
    return balance * i / (1 - (1 + i) ** (-n))


def compare_offers(scenario: dict) -> dict:
    """Compare the lender renewal offer against a market alternative."""
    balance = float(scenario["balance"])
    amort = float(scenario.get("amortization_years", 20))
    offer_rate = float(scenario["renewal_offer_rate_pct"])
    market_rate = float(scenario.get("market_rate_pct", offer_rate))
    term_years = int(scenario.get("new_term_years", 5))

    offer_pay = monthly_payment(balance, offer_rate, amort)
    market_pay = monthly_payment(balance, market_rate, amort)
    months = term_years * 12
    return {
        "renewal_offer_rate_pct": offer_rate,
        "market_rate_pct": market_rate,
        "offer_monthly_payment": round(offer_pay, 2),
        "market_monthly_payment": round(market_pay, 2),
        "monthly_difference": round(offer_pay - market_pay, 2),
        "term_payment_difference": round((offer_pay - market_pay) * months, 2),
        "term_years": term_years,
    }


def analyze_scenario(scenario: dict, client: MetaClient | None = None) -> dict:
    client = client or MetaClient()
    penalty = estimate_penalty(scenario)
    offers = compare_offers(scenario)

    user_prompt = (
        "Write a renewal brief for this synthetic scenario. Cover: "
        "(1) stay-with-lender vs switch comparison, (2) whether paying "
        "the penalty to switch could pay off, (3) fixed vs variable "
        "considerations, (4) questions to ask the current lender, "
        "(5) next steps for the broker.\n\nScenario (fictional):\n"
        + json.dumps(scenario, indent=2)
        + "\n\nLocally computed penalty estimate:\n"
        + json.dumps(penalty, indent=2)
        + "\n\nLocally computed offer comparison:\n"
        + json.dumps(offers, indent=2)
    )
    result = client.complete(SYSTEM_PROMPT, user_prompt)

    return {
        "borrower": scenario.get("borrower", "Fictional borrower"),
        "property": scenario.get("property", "Fictional property"),
        "mode": result["mode"],
        "model": client.model if result["mode"] == "live" else "demo (no live model called)",
        "penalty_estimate": penalty,
        "offer_comparison": offers,
        "advisor_notes": result["text"],
        "usage": result["usage"],
        "disclaimer": (
            "Fictional scenario for software demonstration. Not mortgage "
            "advice. Figures are simplified estimates; a licensed broker "
            "must verify all numbers with the lenders involved."
        ),
    }


def triage_book(scenarios: list[dict]) -> list[dict]:
    """Rank a small broker book by renewal urgency and potential savings.

    Deterministic and local: no model call. Urgency = days to maturity;
    opportunity = term payment difference minus the penalty to switch.
    """
    rows = []
    for s in scenarios:
        offers = compare_offers(s)
        penalty = estimate_penalty(s)
        net = offers["term_payment_difference"] - penalty["estimated_penalty"]
        rows.append(
            {
                "borrower": s.get("borrower", "Fictional borrower"),
                "days_to_maturity": int(s.get("days_to_maturity", 9999)),
                "balance": float(s["balance"]),
                "term_payment_difference": offers["term_payment_difference"],
                "estimated_penalty": penalty["estimated_penalty"],
                "net_switch_benefit": round(net, 2),
                "priority": (
                    "call this week"
                    if int(s.get("days_to_maturity", 9999)) <= 60
                    else "schedule review"
                    if int(s.get("days_to_maturity", 9999)) <= 120
                    else "monitor"
                ),
            }
        )
    rows.sort(key=lambda r: (r["days_to_maturity"], -r["net_switch_benefit"]))
    return rows
