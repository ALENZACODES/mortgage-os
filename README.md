# Mortgage OS — Renewal Radar Reimagined

A working slice of a Canadian mortgage **operating system** for brokers,
built for the Meta Global AI Developer Hackathon on the **Meta Model API**
(**Muse Spark 1.3**).

Most renewal tools show a homeowner one number. A broker's real job is a
workflow: spot the renewals coming due, work out what leaving the current
lender would cost, compare the renewal offer against the market, and write
the client a clear brief before the conversation. Mortgage OS does that
workflow end to end on fictional data.

## What it does

1. **Renewal scenario analyzer**: takes a mortgage scenario (balance,
   rates, dates, lender offer) and returns a structured renewal brief:
   locally computed penalty estimate and offer comparison, plus a
   narrative analysis from Muse Spark covering stay-vs-switch, whether
   paying the penalty to switch pays off, fixed vs variable, questions
   for the current lender, and next steps.
2. **Prepayment-penalty explainer**: Canadian penalty math done locally
   in deterministic code (never by the model): the interest rate
   differential (IRD) vs three months' interest, with the fixed-rate
   "greater of" rule and the variable-rate rule, each figure shown so a
   broker can explain it line by line.
3. **Broker book triage**: ranks a folder of client scenarios by days
   to maturity and net switching benefit, so the broker knows who to
   call this week.
4. **Batch brief runner (`burn.py`)**: runs a whole folder of scenarios
   through Muse Spark, writes one brief per file to `outputs/`, and
   keeps a running token/cost tally against a spend cap.

## How Meta models are used

- **Muse Spark 1.3** via the Meta Model API's OpenAI-compatible endpoint
  (`https://api.meta.ai/v1`, model `muse-spark-1.3`) writes the advisor
  narrative in every brief.
- All money math (payments with Canadian semi-annual compounding,
  penalties, offer comparisons) is computed locally in Python. The model
  explains and reasons; it never invents the numbers.
- The API key is read from the `MODEL_API_KEY` environment variable.

## Demo mode (no key needed)

If `MODEL_API_KEY` is not set, the app runs in an honestly labelled
**DEMO mode**: every number is still computed locally for real, and the
advisor narrative is a canned text that says so in its first line. Demo
mode exists so anyone can run and judge the full workflow without an
account. Nothing in demo output pretends a live model was called.

## Run it

Python 3.10+, standard library only; nothing to install.

```bash
# Full renewal brief for one fictional scenario
python3 app.py analyze samples/scenario-01.json

# Penalty explainer only
python3 app.py penalty samples/scenario-04.json

# Broker book triage over all samples
python3 app.py triage samples/

# Live mode: same commands with a key set
MODEL_API_KEY=your-key python3 app.py analyze samples/scenario-01.json

# Batch: briefs for the whole folder, with a token/cost tally
MODEL_API_KEY=your-key python3 burn.py --input samples/ --cap-usd 150

# Smoke tests (demo mode, no network)
python3 -m unittest discover -s tests -v
```

## Data

Everything under `samples/` is synthetic and fictional: invented
borrowers, invented lenders, plausible numbers. No real client data is
in this repository, and the outputs are demonstrations, not mortgage
advice.

## Project structure

```text
mortgage-os-meta/
├── demo/                     # Demo video
│   └── mortgage-os-demo.mp4
├── mortgage_os/              # Core package
│   ├── __init__.py
│   ├── analyzer.py           # Brief assembly and book triage
│   ├── meta_client.py        # Meta Model API client (stdlib urllib) and demo mode
│   └── penalty.py            # IRD vs three-months-interest penalty math
├── samples/                  # Fictional renewal scenarios (JSON)
│   ├── scenario-01.json
│   ├── scenario-02.json
│   ├── scenario-03.json
│   └── scenario-04.json
├── tests/                    # Smoke tests (demo mode, end to end)
│   └── test_smoke.py
├── .gitignore
├── app.py                    # CLI: analyze / penalty / triage
├── burn.py                   # Batch runner with token/cost tally and spend cap
├── LICENSE                   # Licence
├── README.md                 # This file
├── requirements.txt          # Python dependencies
└── SUBMISSION.md             # Submission write-up
```

## License

MIT. See `LICENSE`.
