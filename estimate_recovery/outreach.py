"""Write personalized outreach for contractor leads (your prospects, not their customers)."""

import csv
import re
import time

from .llm import chat_json

FIELDS = ["subject", "first_touch", "facebook_message", "linkedin_note", "call_script",
          "video_script", "day_3_followup", "day_7_tip", "day_14_breakup"]
MIN_REVIEWS = 20  # fewer reviews usually means too few quotes to be worth a pilot

SYSTEM_PROMPT = """You write cold outreach for a one-person agency that recovers unsold \
estimates for home service contractors. The offer: the agency runs AI follow-up on the \
contractor's old, unsold quotes. Free pilot on up to 100 old estimates over 14 days. After that, \
they pay only for jobs that get booked. No upfront cost.

Rules: plain, friendly, short, written owner to owner, with normal capitalization. Open each \
message with "Hi <first name>," when the owner's name is known, otherwise just "Hi," or \
"Hi <company> team,". Name the problem in the first line \
(quotes that went silent). Use the lead details to make it specific, but never invent facts, \
numbers or results. Where you'd need a detail you weren't given (like their phone number), \
write a [placeholder] in brackets. No hype words ("revolutionary", "game-changer"), no fake urgency, no emojis.

Write:
- subject: email subject under 8 words, lowercase is fine
- first_touch: email or website contact form message, under 70 words, ending with a \
low-effort yes/no question
- facebook_message: Facebook page message, under 45 words, casual, ending with a yes/no question
- linkedin_note: LinkedIn connection request note, under 280 characters, no hard pitch
- call_script: a short phone script. Goal: get the name and email of whoever handles \
estimates, not to sell. Include what to say to whoever answers, and a 2-sentence version if \
the owner picks up. Use line breaks between parts.
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
        f"Owner first name: {(lead.get('owner_name') or 'unknown').split()[0]}\n"
        f"Google reviews: {lead.get('review_count')} at {lead.get('rating')} stars\n"
        f"Website: {lead.get('website') or 'unknown'}\n"
        f"Notes: {lead.get('notes') or 'none'}"
    )


def greeting(lead: dict) -> str:
    name = (lead.get("owner_name") or "").split()
    return f"Hi {name[0]}" if name else f"Hi {lead['company']} team"


def template(lead: dict, me: dict) -> dict:
    hi, co = greeting(lead), lead["company"]
    first = hi[3:]
    return {
        "subject": "old quotes at " + co.lower(),
        "first_touch": (
            f"{hi}, quick question: how many estimates did {co} send last year that never "
            f"got a yes? I set up AI follow-up that re-contacts those customers and books jobs. "
            f"Happy to run it free on 100 of your old quotes. If nothing books, you owe nothing. "
            f"Worth a look?"
        ),
        "facebook_message": (
            f"{hi}! Quick one: do you have old quotes that never got a yes? I follow up on them "
            f"with AI and book the jobs. Free on 100 old quotes, you only pay if jobs book. Interested?"
        ),
        "linkedin_note": (
            f"{hi}, I help home service companies win back quotes that went silent, using AI "
            f"follow-up. Would love to connect."
        ),
        "call_script": (
            f"To whoever answers: \"Hi, quick question, who handles your estimates there? "
            f"And what's the best email to reach them?\"\n\n"
            f"If the owner answers: \"I help {lead.get('trade') or 'contractors'} companies win back "
            f"quotes that went silent. I'd run it free on 100 of your old estimates. Can I email "
            f"you the details?\""
        ),
        "video_script": (
            f"Hi {first}, I'm {me['name']}. I'm on the {co} website now. Most contractors send a "
            f"quote, follow up once, and move on. Here's what a follow-up from {co} would look "
            f"like for a customer whose quote went quiet: [show sample text]. My system sends a short sequence like this to every old quote, answers "
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


def tidy(text: str) -> str:
    """Fix models that write in all lowercase: capitalize sentence starts, 'I' and 'AI'."""
    text = re.sub(r"\bi\b", "I", text)
    text = re.sub(r"\bai\b", "AI", text)
    return re.sub(r"(^|[.!?]\s+|\n\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)


def write_outreach(leads: list[dict], me: dict, provider: str,
                   existing: dict[str, dict] | None = None) -> list[dict]:
    """existing: rows from an earlier run, keyed by company. AI-written ones are kept as they are."""
    out = []
    for i, lead in enumerate(leads, 1):
        print(f"  [{i}/{len(leads)}] {lead['company']}")
        prev = (existing or {}).get(lead["company"])
        if prev and prev.get("source") == "ai" and all(prev.get(k) for k in FIELDS):
            out.append({**lead, **{k: prev[k] for k in FIELDS}, "source": "ai"})
            continue
        source = "template"
        if provider == "mock":
            msgs = template(lead, me)
        else:
            msgs = None
            for attempt in range(4):  # the NVIDIA service sometimes returns empty or 5xx replies
                try:
                    data = chat_json(provider, SYSTEM_PROMPT, _describe(lead, me), FIELDS)
                    msgs = {k: tidy(str(data[k]).strip()) if k != "subject" else str(data[k]).strip()
                            for k in FIELDS}
                    source = "ai"
                    break
                except Exception as e:
                    if attempt == 3:
                        print(f"    ! AI failed ({e}); using template")
                    else:
                        time.sleep(3 * (attempt + 1))
            msgs = msgs or template(lead, me)
        out.append({**lead, **msgs, "source": source})
    return out


def to_markdown(rows: list[dict]) -> str:
    """One readable sheet: every company with each message ready to copy."""
    parts = ["# Outreach messages", "",
             "Each company has a version for every channel. Pick the channel you can reach them on, "
             "fill in any [placeholders], and send. Follow up on day 3, 7 and 14 if they don't reply.", ""]
    for i, r in enumerate(rows, 1):
        meta = " · ".join(x for x in (r.get("trade"), f"{r['review_count']} reviews" if r.get("review_count") else "",
                                     r.get("phone"), r.get("email")) if x)
        parts += [f"## {i}. {r['company']}", f"*{meta}*", "",
                  "### Email / website contact form", f"**Subject:** {r['subject']}", "", r["first_touch"], "",
                  "### Facebook message", r["facebook_message"], "",
                  "### LinkedIn connection note", r["linkedin_note"], "",
                  "### Phone script (to get a name and email)", r["call_script"], "",
                  "### Follow-ups",
                  f"- **Day 3:** {r['day_3_followup']}",
                  f"- **Day 7:** {r['day_7_tip']}",
                  f"- **Day 14:** {r['day_14_breakup']}", "",
                  "<details><summary>60-second video script</summary>", "", r["video_script"], "", "</details>",
                  "", "---", ""]
    return "\n".join(parts)
