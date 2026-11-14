"""Make sample quotes and follow-up texts for any trade, to show owners "here's what I'd send".

    python agency.py samples --trade roofing          # hand-written templates, no key needed
    python agency.py samples --trade roofing --provider nvidia
"""

import csv
import os
import random
from datetime import date, timedelta

OPT_OUT = "Reply STOP to opt out."

FIRST = ["Maria", "James", "Priya", "Robert", "Linda", "Kevin", "Angela", "Daniel", "Sofia", "Thomas",
         "Emily", "Marcus", "Grace", "Brian", "Rachel", "Luis", "Hannah", "Omar", "Denise", "Tyler"]
LAST = ["Lopez", "Carter", "Shah", "King", "Nguyen", "Brooks", "White", "Reed", "Martinez", "Hill",
        "Davis", "Johnson", "Kim", "Scott", "Walsh", "Ortiz", "Meyer", "Haddad", "Price", "Novak"]

# (job, low $, high $, a line written for that specific job)
JOBS = {
    "hvac": [
        ("AC replacement (3 ton)", 6500, 9800, "Still thinking about the AC replacement for that hot upstairs? Happy to go over the quote or options."),
        ("Furnace replacement", 4200, 7500, "Checking in on the furnace replacement quote before it gets colder. Any questions I can answer?"),
        ("Heat pump install", 9000, 14000, "Still weighing the heat pump? Glad to walk through running costs or answer anything about the quote."),
        ("Ductless mini-split (2 zones)", 6000, 9500, "Still want to fix that bonus room with the mini-split? Happy to answer questions on the quote."),
        ("Water heater replacement", 1800, 3200, "Following up on the water heater quote. Is the old one still holding up?"),
        ("Indoor air quality package", 1200, 2600, "Checking in on the air quality quote you asked about for the allergies. Any questions?"),
        ("Ductwork replacement", 4000, 8000, "Still dealing with uneven temperatures room to room? Happy to go over the ductwork quote again."),
        ("Smart thermostat + zoning", 900, 2400, "Following up on the zoning quote for upstairs and downstairs. Want to talk it through?"),
    ],
    "roofing": [
        ("Full roof replacement", 11000, 22000, "Following up on your roof replacement quote. Glad to answer questions or go over shingle options again."),
        ("Roof repair (storm damage)", 1200, 4500, "Checking in on the storm damage repair over the garage. Want help sorting it out before winter?"),
        ("Gutter replacement + guards", 1800, 4200, "Still having trouble with the overflowing gutters? Happy to go over the gutter quote."),
        ("Siding replacement", 12000, 28000, "Still thinking about the new siding? Glad to walk through colors or the quote anytime."),
        ("Flat roof recoat", 3500, 8000, "Following up on the flat roof recoat quote. Is water still pooling on that section?"),
        ("Skylight replacement", 1500, 3800, "Checking in on the leaky skylight quote. Any questions I can answer?"),
        ("Chimney flashing repair", 900, 2200, "Following up on the chimney leak repair quote. Want to get it looked at?"),
        ("Soffit and fascia repair", 1400, 3600, "Still want the fascia and soffit fixed up front? Happy to answer questions on the quote."),
    ],
    "remodeling": [
        ("Kitchen remodel", 28000, 65000, "Still dreaming about opening up the kitchen? Happy to revisit the design or the quote anytime."),
        ("Bathroom remodel", 14000, 32000, "Following up on the bathroom remodel and that walk-in shower. Any questions on the quote?"),
        ("Basement finishing", 25000, 55000, "Still thinking about finishing the basement? Glad to walk through the plan or the quote again."),
        ("Deck build (composite)", 12000, 26000, "Checking in on the composite deck quote. Want to talk it through for next season?"),
        ("Primary suite addition", 60000, 120000, "Following up on the primary suite addition. Happy to answer questions or adjust the plan."),
        ("Flooring (main level)", 7000, 16000, "Still planning new floors on the main level? Glad to go over materials or the quote."),
        ("Laundry/mudroom remodel", 9000, 18000, "Checking in on the mudroom remodel with the built-in lockers. Any questions?"),
        ("Window replacement (12 windows)", 11000, 22000, "Still feeling drafts from those windows? Happy to go over the replacement quote again."),
    ],
    "plumbing": [
        ("Sewer line replacement", 6000, 15000, "Following up on the sewer line quote. Is it still backing up? Happy to answer questions."),
        ("Whole-house repipe", 7000, 16000, "Still thinking about replacing the old galvanized pipes? Glad to walk through the repipe quote."),
        ("Tankless water heater install", 3200, 5500, "Checking in on the tankless water heater quote. Any questions I can answer?"),
        ("Sump pump + backup battery", 900, 2400, "Following up on the sump pump and backup quote. Want it in before the next heavy rain?"),
        ("Bathroom rough-in (basement)", 3500, 8000, "Still planning the basement bathroom? Happy to go over the rough-in quote."),
        ("Water softener install", 1500, 3500, "Checking in on the water softener quote for the hard water. Any questions?"),
        ("Main water line replacement", 3500, 8000, "Still dealing with low water pressure? Glad to go over the main line quote again."),
        ("Drain tile / overhead sewer", 9000, 18000, "Following up on the drain tile quote to keep the basement dry. Want to talk it through?"),
    ],
}

OPENERS = ["Hi {first}, it's {sender} from {biz}.", "Hi {first}, {sender} with {biz} here."]


def make_quotes(trade: str, n: int = 20, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    jobs = JOBS[trade]
    today = date.today()
    rows = []
    for i in range(n):
        job, lo, hi, line = jobs[i % len(jobs)]
        rows.append({
            "customer_name": f"{FIRST[i % len(FIRST)]} {LAST[(i * 7) % len(LAST)]}",
            "job_type": job,
            "quote_amount": round(rng.uniform(lo, hi), -1),
            "quote_date": (today - timedelta(days=rng.randint(21, 330))).isoformat(),
            "line": line,
        })
    return rows


def template_message(q: dict, i: int, biz: dict) -> str:
    opener = OPENERS[(i // 8) % len(OPENERS)].format(
        first=q["customer_name"].split()[0], sender=biz["sender"], biz=biz["name"])
    return f"{opener} {q['line']} {OPT_OUT}"


def ai_message(q: dict, biz: dict, provider: str) -> str:
    from .llm import chat_json
    from .messages import ensure_opt_out
    system = ("You write one short, friendly follow-up text from a local contractor to a customer who got "
              "a quote but never booked. Under 40 words. Mention their specific job. No pressure, no "
              "discounts, no made-up facts. End with 'Reply STOP to opt out.'")
    user = (f"Business: {biz['name']}, sender: {biz['sender']}\nCustomer first name: "
            f"{q['customer_name'].split()[0]}\nJob: {q['job_type']}\nExample angle: {q['line']}")
    return ensure_opt_out(chat_json(provider, system, user, ["text"])["text"].strip())


def build(trade: str, out_dir: str, biz: dict, provider: str = "mock", n: int = 20) -> tuple[str, str, list[dict]]:
    trade = trade.lower()
    if trade not in JOBS:
        raise SystemExit(f"Trade must be one of: {', '.join(JOBS)}")
    quotes = make_quotes(trade, n)
    msgs = []
    for i, q in enumerate(quotes):
        text = template_message(q, i, biz)
        if provider != "mock":
            try:
                text = ai_message(q, biz, provider)
            except Exception as e:
                print(f"  ! AI failed for {q['customer_name']} ({e}); using template")
        msgs.append({**q, "message": text, "words": len(text.split())})
    os.makedirs(out_dir, exist_ok=True)
    qpath = os.path.join(out_dir, f"{trade}-sample-quotes.csv")
    mpath = os.path.join(out_dir, f"{trade}-sample-messages.csv")
    with open(qpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["customer_name", "job_type", "quote_amount", "quote_date"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(quotes)
    with open(mpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["customer_name", "job_type", "quote_amount", "message", "words"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(msgs)
    # "Best three": the biggest quotes, one per job type, since big jobs are what owners care about.
    best, seen = [], set()
    for m in sorted(msgs, key=lambda m: -m["quote_amount"]):
        if m["job_type"] not in seen:
            best.append(m)
            seen.add(m["job_type"])
        if len(best) == 3:
            break
    return qpath, mpath, best
