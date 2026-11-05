# Hackathon Submission — Mortgage OS: Renewal Radar Reimagined

**Event:** Meta Global AI Developer Hackathon
**Builder:** John Khan (solo)
**Repository:** https://github.com/ALENZACODES/mortgage-os-meta

## The problem

In Canada, most mortgages renew every five years, and most homeowners
sign whatever renewal letter their lender mails them — often at a rate
well above what the market would give them, because the letter arrives
late, the penalty for leaving is opaque, and nobody does the comparison
math for them. Brokers who want to protect their clients face the same
wall from the other side: a book of dozens of renewals, each needing a
penalty calculation, an offer comparison, and a clear client brief,
produced under deadline pressure in the weeks before maturity.

The costly part is not any single calculation. It is the workflow:
triage the book, run the numbers, explain the penalty, write the brief —
repeatedly, accurately, and in plain language.

## The solution

Mortgage OS is a working slice of a broker operating system that runs
that workflow:

- **Book triage** ranks every renewal by days to maturity and net
  switching benefit, so the broker calls the right client this week.
- **A penalty explainer** computes the Canadian prepayment penalty
  locally — interest rate differential vs three months' interest, the
  fixed-rate "greater of" rule, the variable-rate rule — with every
  intermediate figure shown.
- **A renewal analyzer** turns one scenario into a structured brief:
  stay-vs-switch comparison over the new term, whether paying the
  penalty to switch actually pays off, fixed vs variable
  considerations, questions to put to the current lender, and next
  steps.
- **A batch runner** produces briefs for an entire folder of scenarios
  with a running token/cost tally and a spend cap, the way a broker
  would prepare a week's call list.

## How it uses the Meta Model API

- **Muse Spark 1.3** (Meta Model API, OpenAI-compatible endpoint
  `https://api.meta.ai/v1`) writes the advisor narrative inside every
  brief. It receives the scenario plus the locally computed penalty and
  comparison figures, and reasons over them: trade-offs, risks,
  questions, next steps.
- **A deliberate split of labour:** all money math — Canadian
  semi-annual-compounding payments, IRD, three months' interest, term
  comparisons — is deterministic local Python. The model explains and
  reasons; it never generates the numbers. That separation is the
  design principle of the whole system: in regulated financial work,
  the arithmetic must be auditable and the language can be generative.
- **Demo mode:** with no `MODEL_API_KEY` set, the app runs end to end
  with the narrative replaced by a clearly labelled canned text, so the
  full workflow can be run and judged without an account. With a key,
  the identical commands run Muse Spark live.
- Standard library only: the client is a small `urllib` wrapper, so the
  project runs anywhere Python 3 runs, with nothing to install.

## What was built during the window

Everything in this repository was written fresh for this hackathon as a
small original slice inspired by the renewal-workflow concept: the Meta
Model API client with demo mode, the penalty engine, the brief
analyzer, the book triage, the batch runner with cost tallying, four
fictional sample scenarios, smoke tests that run the demo path end to
end, and this submission text. No client data is used anywhere; every
borrower and lender in the samples is invented.

## Why it matters

A renewal brief that used to take a broker the better part of an hour —
penalty math, offer comparison, client-ready explanation — is produced
in seconds, with the math auditable line by line. Multiplied across a
broker's book, that is the difference between clients being called
before their renewal letter arrives and clients silently overpaying for
another five-year term.

## Roadmap: the full Mortgage OS

1. **Renewal-letter analysis** — parse a lender's renewal letter (PDF or
   photo) into a scenario automatically, using multimodal model input
   for the document and local code for verification of every figure
   extracted.
2. **Lender penalty library** — per-lender penalty rules and posted-rate
   histories behind the explainer, with each estimate traced to the
   lender's published method.
3. **Client-facing briefs** — the same brief rendered for the homeowner:
   plain language, both options costed over the full term, and a clear
   statement of what to ask the current lender before signing.
4. **Book monitoring** — nightly triage over a broker's whole book with
   rate-move alerts when a client's net switching benefit crosses a
   threshold.
5. **Compliance trail** — every brief stored with its inputs, model
   version, and computed figures, so advice files can be reconstructed
   exactly as produced.

## Try it

```bash
python3 app.py triage samples/
python3 app.py analyze samples/scenario-01.json
MODEL_API_KEY=your-key python3 burn.py --input samples/ --cap-usd 150
python3 -m unittest discover -s tests -v
```
