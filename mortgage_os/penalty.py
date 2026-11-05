"""Simplified Canadian prepayment-penalty math.

This is an educational explainer, not a lender quote. Real lender
penalties use the lender's own posted-rate history, exact day counts,
and contract-specific rules. The simplifications used here:

- IRD (interest rate differential), fixed-rate mortgages:
      (posted_rate_for_comparable_term - contract_rate)
          x outstanding_balance x years_remaining
  floored at zero. This approximates the common Canadian IRD method.
- Three months' interest:
      outstanding_balance x contract_rate x 3/12
- Fixed-rate penalty  = the GREATER of IRD and three months' interest.
- Variable-rate penalty = three months' interest (the standard rule).
"""

from __future__ import annotations


def three_months_interest(balance: float, contract_rate_pct: float) -> float:
    return balance * (contract_rate_pct / 100.0) * (3.0 / 12.0)


def interest_rate_differential(
    balance: float,
    contract_rate_pct: float,
    posted_rate_pct: float,
    months_remaining: int,
) -> float:
    diff_pct = max(0.0, posted_rate_pct - contract_rate_pct)
    years = months_remaining / 12.0
    return balance * (diff_pct / 100.0) * years


def estimate_penalty(scenario: dict) -> dict:
    """Estimate the prepayment penalty for a scenario dict.

    Expected keys: balance, contract_rate_pct, posted_rate_pct,
    months_remaining, rate_type ("fixed" or "variable").
    """
    balance = float(scenario["balance"])
    contract = float(scenario["contract_rate_pct"])
    posted = float(scenario.get("posted_rate_pct", contract))
    months = int(scenario.get("months_remaining", 0))

    three_mo = three_months_interest(balance, contract)
    ird = interest_rate_differential(balance, contract, posted, months)

    if str(scenario.get("rate_type", "fixed")).lower() == "variable":
        penalty = three_mo
        method = "three months' interest (standard for variable-rate mortgages)"
    else:
        penalty = max(ird, three_mo)
        method = (
            "greater of IRD and three months' interest (standard for "
            "fixed-rate mortgages)"
        )

    return {
        "three_months_interest": round(three_mo, 2),
        "interest_rate_differential": round(ird, 2),
        "estimated_penalty": round(penalty, 2),
        "method": method,
        "caveat": (
            "Simplified educational estimate. Lenders calculate penalties "
            "with their own posted rates and day counts; always request the "
            "exact figure from the lender in writing."
        ),
    }
