# AI Agency: Unsold Estimate Recovery

AI follow-up that turns home service contractors' old, unsold estimates into booked jobs.

## Week 1 demo

Takes a CSV of unsold estimates and:

1. **Cleans it:** removes duplicates, bad phone numbers and emails, and anyone already booked or opted out.
2. **Writes follow-ups with Claude:** each customer gets a day 1 text, a day 4 email and a day 10 text that mention their actual job.
3. **Builds a report:** `output/report.html` shows the unsold pipeline, estimated recovered revenue and the follow-up plan.

### Run it

```bash
pip install -r requirements.txt

# No API key needed: template messages
python run_demo.py --mock

# AI messages with NVIDIA (free key at build.nvidia.com)
export NVIDIA_API_KEY=nvapi-...
python run_demo.py --provider nvidia

# AI messages with Claude
export ANTHROPIC_API_KEY=sk-ant-...
python run_demo.py
```

Change the NVIDIA model with `NVIDIA_MODEL` (default `nvidia/nemotron-3-ultra-550b-a55b`). Never commit keys.

Outputs:
- `output/follow_up_messages.csv`: every customer's message sequence
- `output/report.html`: open in a browser and screen-record it for the demo video

### Use a client's list

```bash
python run_demo.py --input their_export.csv --business "Cool Air HVAC" --sender Mike --phone "(214) 555-0100"
```

The CSV needs these columns: `customer_name, phone, email, job_type, quote_amount, quote_date, status, notes`.
`status` values `booked`, `won`, `sold`, `opted_out` and `do_not_contact` are skipped.

## Layout

| Path | What it does |
|---|---|
| `run_demo.py` | Command line entry point |
| `estimate_recovery/clean.py` | List cleaning |
| `estimate_recovery/messages.py` | Prompt and message writing (Claude, NVIDIA or mock) |
| `estimate_recovery/report.py` | HTML client report |
| `sample_data/` | Fake HVAC estimates for demos |

## Compliance

Only text customers who gave the business their number, keep "Reply STOP" in every text, and register for A2P 10DLC before sending real texts. This demo only writes messages; it doesn't send anything.
