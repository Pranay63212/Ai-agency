# AI Agency: Unsold Estimate Recovery

AI follow-up that turns home service contractors' old, unsold estimates into booked jobs.

## What's here

| Tool | Command | What it does |
|---|---|---|
| Demo | `python run_demo.py` | Sample HVAC list in, personalized messages and a client-ready report out. Use it for your demo video. |
| Outreach | `python agency.py outreach` | Personalized pitches, video scripts and follow-ups for contractor leads |
| Campaign setup | `python agency.py new` | Cleans a client's estimate export and writes each customer's day 1, 4 and 10 messages |
| Sending | `python agency.py send` | Sends what's due by text (Twilio) or email. Previews by default; respects sending hours and opt-outs. |
| Replies | `python agency.py serve` / `reply` | Reads replies, honors STOP, drafts answers, alerts the owner about hot leads |
| Tracking | `book`, `close`, `status` | Bookings, closed contacts, who to call today |
| Reporting | `python agency.py report` | Weekly results page and invoice |

Run `python agency.py -h` for every option.

## Quick start

```bash
pip install -r requirements.txt

# Demo with no API key
python run_demo.py --mock

# Demo with AI messages (NVIDIA)
export NVIDIA_API_KEY=nvapi-...
python run_demo.py --provider nvidia

# A full (preview-only) client campaign on the sample data
python agency.py new "Comfort Pro HVAC" --input sample_data/hvac_unsold_estimates.csv \
    --sender Mike --phone "(214) 555-0100"
python agency.py send comfort-pro-hvac
```

AI provider: `--provider nvidia` (default, uses `NVIDIA_API_KEY`), `claude` (`ANTHROPIC_API_KEY`) or `mock` (templates).

## Docs

- [docs/playbook.md](docs/playbook.md): finding clients, running pilots, daily routine
- [docs/setup.md](docs/setup.md): Twilio, email, webhook hosting, scheduling
- [docs/pilot-agreement.md](docs/pilot-agreement.md): pilot agreement template (get it reviewed by a lawyer)

## Layout

| Path | Purpose |
|---|---|
| `agency.py` | Main command line tool |
| `run_demo.py` | One-shot demo |
| `estimate_recovery/clean.py` | List cleaning |
| `estimate_recovery/messages.py` | Follow-up message writing |
| `estimate_recovery/llm.py` | NVIDIA / Claude helper |
| `estimate_recovery/campaign.py` | Client folders, contacts, event log |
| `estimate_recovery/sender.py` | Sequence timing, Twilio and SMTP sending |
| `estimate_recovery/replies.py` | Reply sorting, opt-outs, owner alerts |
| `estimate_recovery/webhook.py` | Reply web server |
| `estimate_recovery/weekly.py`, `report.py` | Client reports and invoices |
| `estimate_recovery/outreach.py` | Prospect outreach writer |
| `sample_data/` | Fake estimates and leads |
| `tests/` | `python -m pytest` |

## Compliance

Only text customers who gave the business their number. Every text carries "Reply STOP to opt out", STOP replies are honored before any AI runs, and sending happens only 9am–8pm Monday to Saturday. Register for A2P 10DLC before sending texts. Client data lives in `clients/`, which is git-ignored.
