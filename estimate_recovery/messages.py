"""Write a personalized follow-up sequence for each unsold estimate with an AI model.

Providers: "nvidia" (NVIDIA_API_KEY), "claude" (ANTHROPIC_API_KEY), "mock" (templates, no key).
"""

from .llm import chat_json

OPT_OUT = "Reply STOP to opt out."
FIELDS = ["day_1_text", "day_4_email_subject", "day_4_email_body", "day_10_text"]

SYSTEM_PROMPT = """You write follow-up messages for a home service contractor reaching out to \
customers who received a quote but never booked.

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
    return (
        f"Business: {business['name']} ({business['trade']}), sender: {business['sender']}, "
        f"phone: {business['phone']}\n"
        f"Customer first name: {first_name(contact)}\n"
        f"Job quoted: {contact['job_type']}\n"
        f"Quote amount: ${float(contact['quote_amount']):,.0f}\n"
        f"Quote date: {contact['quote_date']}\n"
        f"Notes: {contact.get('notes') or 'none'}"
    )


def ensure_opt_out(text: str) -> str:
    """Every text must carry an opt-out line, whatever the model wrote."""
    text = (text or "").strip()
    return text if "stop" in text.lower() else f"{text} {OPT_OUT}"


def write_mock(contact: dict, business: dict) -> dict:
    """Template messages so the demo runs without an API key."""
    name, job, biz = first_name(contact), contact["job_type"], business["name"]
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
