"""Write personalized outreach for contractor leads (your prospects, not their customers)."""

import csv

from .llm import chat_json

FIELDS = ["subject", "first_touch", "video_script", "day_3_followup", "day_7_tip", "day_14_breakup"]
MIN_REVIEWS = 20  # fewer reviews usually means too few quotes to be worth a pilot

SYSTEM_PROMPT = """You write cold outreach for a one-person agency that recovers unsold \
estimates for home service contractors. The offer: the agency runs AI follow-up on the \
contractor's old, unsold quotes. Free pilot on up to 100 old estimates over 14 days. After that, \
they pay only for jobs that get booked. No upfront cost.

Rules: plain, friendly, short, written owner to owner. Name the problem in the first line \
(quotes that went silent). Use the lead details to make it specific, but never invent facts, \
numbers or results. Where you'd need a detail you weren't given (like their phone number), \
write a [placeholder] in brackets. No hype words ("revolutionary", "game-changer"), no fake urgency, no emojis.

Write:
- subject: email subject under 8 words, lowercase is fine
- first_touch: email/DM under 70 words ending with a low-effort yes/no question
- video_script: a 60-second screen-recording script (what to say while showing their website \
and a sample follow-up message written for their business)
- day_3_followup: under 40 words, mentions a short video
- day_7_tip: under 60 words, one genuinely useful tip about following up quotes, no pitch \
except one closing line
- day_14_breakup: under 40 words, polite "should I close your file?" note
"""


def load_leads(path: str) -> tuple[list[dict], list[tuple[dict, str]]]:
    keep, skipped = [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            row = {k.strip(): (v or "").strip() for k, v in row.items()}
            try:
                reviews = int(row.get("review_count") or 0)
            except ValueError:
                reviews = 0
            if reviews < MIN_REVIEWS:
                skipped.append((row, f"only {reviews} reviews"))
            else:
                keep.append(row)
    return keep, skipped


def _describe(lead: dict, me: dict) -> str:
    return (
        f"Sender: {me['name']}, {me['agency']}\n"
        f"Lead company: {lead['company']} ({lead.get('trade') or 'HVAC'}) in {lead.get('city') or 'their area'}\n"
        f"Owner first name: {(lead.get('owner_name') or 'there').split()[0]}\n"
        f"Google reviews: {lead.get('review_count')} at {lead.get('rating')} stars\n"
        f"Website: {lead.get('website') or 'unknown'}\n"
        f"Notes: {lead.get('notes') or 'none'}"
    )


def template(lead: dict, me: dict) -> dict:
    first = (lead.get("owner_name") or "there").split()[0]
    co = lead["company"]
    return {
        "subject": "old quotes at " + co.lower(),
        "first_touch": (
            f"Hey {first}, quick question: how many estimates did {co} send last year that never "
            f"got a yes? I set up AI follow-up that re-contacts those customers and books jobs. "
            f"Happy to run it free on 100 of your old quotes. If nothing books, you owe nothing. "
            f"Worth a look?"
        ),
        "video_script": (
            f"Hi {first}, I'm {me['name']}. I'm on the {co} website now. Most HVAC shops send a "
            f"quote, follow up once, and move on. Here's what a follow-up from {co} would look "
            f"like for a customer who got an AC replacement quote and went quiet: [show sample "
            f"text]. My system sends a short sequence like this to every old quote, answers "
            f"replies and books interested customers on your calendar. I'll run it free on 100 "
            f"old estimates. Reply if you want to see it on your own list."
        ),
        "day_3_followup": f"Hi {first}, I recorded a 60-second video showing what this would look like for {co}. Want me to send it?",
        "day_7_tip": (
            f"Hi {first}, one quick tip: quotes followed up within 48 hours and again at 7 days "
            f"close noticeably more often than quotes followed up once. Even a short text works. "
            f"If you'd rather not do it by hand, that's what I do."
        ),
        "day_14_breakup": f"Hi {first}, I haven't heard back, so I'll assume the timing's off. Should I close your file? Happy to reconnect anytime.",
    }


def write_outreach(leads: list[dict], me: dict, provider: str) -> list[dict]:
    out = []
    for i, lead in enumerate(leads, 1):
        print(f"  [{i}/{len(leads)}] {lead['company']}")
        if provider == "mock":
            msgs = template(lead, me)
        else:
            try:
                data = chat_json(provider, SYSTEM_PROMPT, _describe(lead, me), FIELDS)
                msgs = {k: str(data[k]).strip() for k in FIELDS}
            except Exception as e:
                print(f"    ! AI failed ({e}); using template")
                msgs = template(lead, me)
        out.append({**lead, **msgs})
    return out
