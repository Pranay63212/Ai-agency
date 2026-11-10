"""Handle a customer's reply: log it, honor opt-outs, classify it, draft an answer, alert the owner."""

import os
import re

from .campaign import Campaign
from .clean import normalize_email, normalize_phone
from .llm import chat_json

# Carrier-standard opt-out keywords. Matched before any AI runs so they can never be missed.
STOP_WORDS = {"stop", "stopall", "unsubscribe", "cancel", "end", "quit", "optout", "opt out", "remove me"}
INTENTS = ["interested", "question", "not_now", "not_interested", "already_done", "wrong_number", "other"]
HOT_INTENTS = {"interested", "question"}

SYSTEM_PROMPT = f"""You read replies from customers of a home service contractor. The contractor \
had sent them a follow-up about an old quote they never booked.

Classify the reply as one of: {", ".join(INTENTS)}.
- interested: wants to move forward, schedule, or talk
- question: asks about price, timing, details, financing, etc.
- not_now: maybe later
- not_interested: no, or went with someone else
- already_done: job already done by someone
- wrong_number: not the right person
- other: anything else

Then write draft_reply: a short, friendly text (under 300 characters) from the business. Rules:
- Never quote prices, discounts, financing terms, warranties or availability. Say the owner \
will confirm those details.
- If interested or asking a question: thank them and offer to set a time (use the booking link \
if one is given), or say the owner will call them today.
- If not_now: thank them and say you'll check back later.
- If not_interested, already_done or wrong_number: thank them politely and close it out.
- No pressure. Don't mention AI.

Also return: hot ("yes" if the business should call them quickly, else "no") and summary \
(one short line for the owner)."""

FIELDS = ["intent", "hot", "summary", "draft_reply"]


def is_stop(body: str) -> bool:
    text = re.sub(r"[^a-z ]", "", (body or "").lower()).strip()
    return text in STOP_WORDS or text.split(" ")[0] in {"stop", "unsubscribe", "stopall"}


def classify(body: str, contact: dict | None, settings: dict, provider: str | None) -> dict:
    details = (
        f"Business: {settings['business']} ({settings['trade']}), owner/sender: {settings['sender']}\n"
        f"Booking link: {settings.get('booking_link') or 'none'}\n"
        f"Customer: {(contact or {}).get('customer_name') or 'unknown'}\n"
        f"Job quoted: {(contact or {}).get('job_type') or 'unknown'}\n"
        f"Customer's reply: {body}"
    )
    data = chat_json(provider, SYSTEM_PROMPT, details, FIELDS)
    intent = str(data["intent"]).strip().lower()
    return {
        "intent": intent if intent in INTENTS else "other",
        "hot": str(data["hot"]).strip().lower() in {"yes", "true", "1"} or intent in HOT_INTENTS,
        "summary": str(data["summary"]).strip(),
        "draft_reply": str(data["draft_reply"]).strip(),
    }


def fallback_classify(body: str) -> dict:
    """Keyword rules used if the AI is unreachable. Errs toward flagging the owner."""
    t = (body or "").lower()
    if any(w in t for w in ("wrong number", "who is this", "don't know")):
        intent = "wrong_number"
    elif any(w in t for w in ("no thanks", "not interested", "went with", "someone else")):
        intent = "not_interested"
    elif any(w in t for w in ("later", "next month", "not right now", "spring", "after")):
        intent = "not_now"
    else:
        intent = "question" if "?" in t else "interested"
    return {"intent": intent, "hot": intent in HOT_INTENTS, "summary": body[:120],
            "draft_reply": "Thanks for getting back to us! The owner will reach out shortly."}


def alert_owner(campaign: Campaign, contact: dict | None, from_: str, body: str, result: dict) -> str:
    """Email the owner about a hot lead if SMTP + owner_email are set; always logs an alert event."""
    s = campaign.settings()
    name = (contact or {}).get("customer_name") or from_
    job = (contact or {}).get("job_type") or "unknown job"
    text = (f"HOT LEAD: {name} ({from_}) about {job}.\n\nThey said: \"{body}\"\n\n"
            f"Summary: {result['summary']}\nSuggested reply: {result['draft_reply']}")
    how = "logged"
    if s.get("owner_email") and os.environ.get("SMTP_HOST"):
        from .sender import send_email
        try:
            send_email(s["owner_email"], f"Hot lead: {name} - {job}", text)
            how = f"emailed {s['owner_email']}"
        except Exception as e:
            how = f"email failed: {e}"
    campaign.log((contact or {}).get("contact_id") or from_, "alert", "", f"{how}: {result['summary']}")
    return how


def handle_reply(campaign: Campaign, from_: str, body: str, provider: str | None = None,
                 auto_reply: bool = False) -> dict:
    """Process one inbound reply. Returns what happened, including any text to send back."""
    contact = campaign.find_contact(from_)
    cid = (contact or {}).get("contact_id") or normalize_phone(from_) or normalize_email(from_) or from_
    campaign.log(cid, "reply", "", body)

    if is_stop(body):
        campaign.log(cid, "opt_out", "", "customer replied STOP")
        # Carriers send the STOP confirmation themselves; send nothing else.
        return {"contact_id": cid, "intent": "stop", "hot": False, "summary": "Opted out",
                "draft_reply": "", "send_back": "", "alert": ""}

    try:
        result = classify(body, contact, campaign.settings(), provider)
    except Exception as e:
        result = fallback_classify(body)
        result["summary"] = f"(AI unavailable: {e}) {result['summary']}"

    campaign.log(cid, "note", "", f"intent={result['intent']} hot={result['hot']} | draft: {result['draft_reply']}")
    if result["intent"] in {"not_interested", "already_done", "wrong_number"}:
        campaign.log(cid, "closed", "", result["intent"])
    alert = alert_owner(campaign, contact, from_, body, result) if result["hot"] else ""
    send_back = result["draft_reply"] if auto_reply and result["draft_reply"] else ""
    return {"contact_id": cid, **result, "send_back": send_back, "alert": alert}
