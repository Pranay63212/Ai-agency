"""Write a personalized follow-up sequence for each dead lead with an AI model.

Lead types: quote (got a price, went quiet), inquiry (reached out, never got a quote or booked),
past_customer (used the business before, due again).

Providers: "nvidia" (NVIDIA_API_KEY), "claude" (ANTHROPIC_API_KEY), "mock" (templates, no key).
"""

from .llm import chat_json

OPT_OUT = "Reply STOP to opt out."
FIELDS = ["day_1_text", "day_4_email_subject", "day_4_email_body", "day_10_text"]

SYSTEM_PROMPT = """You write follow-up messages for a home service business reaching back out to \
"dead leads": people who never booked. The lead type tells you which kind:
- quote: they got a quote and went quiet. Check in on that quote.
- inquiry: they reached out (call, form, ad) but never got a quote or booked. Apologize lightly \
if it fits ("wanted to make sure you got taken care of") and offer to help or give a quote.
- past_customer: they used the business before. Friendly "you're due" reminder for the same \
service. Don't claim a specific last visit date unless it's given.

Write like the owner or office manager of a local business: warm, plain, short. Reference the \
customer's actual job and any notes. No pressure tactics, no fake urgency, no discounts unless \
the business offers one. Never invent facts about the customer or the business: don't promise \
financing, warranties, prices, rebates or availability that aren't in the details below. If the \
customer raised a concern (like price), offer to talk it through instead.

The notes are the business's internal notes. Use what the customer said or wanted to personalize \
the message, but never mention record-keeping details (a wrong phone number, duplicates, CRM \
status, "per our notes").

Write three messages:
1. day_1_text: an SMS under 300 characters that ends with "Reply STOP to opt out."
2. day_4_email: an email with a subject line and a body under 120 words.
3. day_10_text: a final, low-pressure SMS under 250 characters asking if they'd still like help, \
ending with "Reply STOP to opt out."
"""


def first_name(contact: dict) -> str:
    return (contact.get("customer_name") or "there").split()[0]


def _describe(contact: dict, business: dict) -> str:
    kind = contact.get("lead_type") or "quote"
    amount = float(contact.get("quote_amount") or 0)
    lines = [
        f"Business: {business['name']} ({business['trade']}), sender: {business['sender']}, "
        f"phone: {business['phone']}",
        f"Lead type: {kind}",
        f"Customer first name: {first_name(contact)}",
        f"Job / service: {contact['job_type']}",
    ]
    if amount and kind == "quote":
        lines.append(f"Quote amount: ${amount:,.0f}")
    if contact.get("quote_date"):
        lines.append(f"{'Last service' if kind == 'past_customer' else 'Date'}: {contact['quote_date']}")
    lines.append(f"Notes: {contact.get('notes') or 'none'}")
    return "\n".join(lines)


def ensure_opt_out(text: str) -> str:
    """Every text must carry an opt-out line, whatever the model wrote."""
    text = (text or "").strip()
    return text if "stop" in text.lower() else f"{text} {OPT_OUT}"


def write_mock(contact: dict, business: dict) -> dict:
    """Template messages so the demo runs without an API key."""
    name, job, biz = first_name(contact), contact["job_type"], business["name"]
    kind = contact.get("lead_type") or "quote"
    if kind == "inquiry":
        return {
            "day_1_text": (f"Hi {name}, it's {business['sender']} from {biz}. You reached out about {job} "
                           f"a while back and I wanted to make sure you got taken care of. Still need help? {OPT_OUT}"),
            "day_4_email_subject": f"Still need help with {job}?",
            "day_4_email_body": (f"Hi {name},\n\nYou asked us about {job} a while ago, and I want to make sure "
                                 f"you got what you needed. If it's still on your list, I'm happy to come take a "
                                 f"look and give you a quote. Just reply here or call {business['phone']}.\n\n"
                                 f"Thanks,\n{business['sender']}\n{biz}"),
            "day_10_text": (f"Hi {name}, last check-in from {biz} about {job}. Want a quote, or should I "
                            f"close this out? {OPT_OUT}"),
        }
    if kind == "past_customer":
        return {
            "day_1_text": (f"Hi {name}, it's {business['sender']} from {biz}. Thanks again for having us out for "
                           f"{job}. Want to get on the schedule again this season? {OPT_OUT}"),
            "day_4_email_subject": f"Time for your {job}?",
            "day_4_email_body": (f"Hi {name},\n\nThanks again for choosing {biz} for {job}. We're booking the "
                                 f"season now, and I'd be glad to get you back on the schedule. Just reply here or "
                                 f"call {business['phone']}.\n\nThanks,\n{business['sender']}\n{biz}"),
            "day_10_text": (f"Hi {name}, {business['sender']} from {biz} again. Want us back for {job} this "
                            f"season? Just reply and I'll find a time. {OPT_OUT}"),
        }
    return {
        "day_1_text": (
            f"Hi {name}, it's {business['sender']} from {biz}. Just checking in on the {job} "
            f"quote we sent. Any questions I can answer? {OPT_OUT}"
        ),
        "day_4_email_subject": f"Your {job} quote",
        "day_4_email_body": (
            f"Hi {name},\n\nI wanted to follow up on the {job} estimate from {contact['quote_date']}. "
            f"If timing or budget was the holdup, I'm happy to talk through options. "
            f"Just reply here or call {business['phone']}.\n\nThanks,\n{business['sender']}\n{biz}"
        ),
        "day_10_text": (
            f"Hi {name}, last check-in from {biz} about your {job}. Want me to hold a spot "
            f"for you, or close out the quote? {OPT_OUT}"
        ),
    }


def write_one(contact: dict, business: dict, provider: str) -> dict:
    if provider == "mock":
        msgs = write_mock(contact, business)
    else:
        data = chat_json(provider, SYSTEM_PROMPT, _describe(contact, business), FIELDS)
        msgs = {k: str(data[k]).strip() for k in FIELDS}
    msgs["day_1_text"] = ensure_opt_out(msgs["day_1_text"])
    msgs["day_10_text"] = ensure_opt_out(msgs["day_10_text"])
    return msgs


def write_all(contacts: list[dict], business: dict, provider: str) -> list[dict]:
    out = []
    for i, contact in enumerate(contacts, 1):
        print(f"  [{i}/{len(contacts)}] {contact['customer_name']} - {contact['job_type']}")
        try:
            msgs = write_one(contact, business, provider)
        except Exception as e:  # keep going; one bad reply shouldn't stop a 500-row list
            print(f"    ! AI failed ({e}); using template for this customer")
            msgs = write_one(contact, business, "mock")
        out.append({**contact, **msgs})
    return out
