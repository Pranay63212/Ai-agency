"""Write a personalized follow-up sequence for each unsold estimate with an AI model.

Providers:
  claude  - Anthropic API (needs ANTHROPIC_API_KEY)
  nvidia  - NVIDIA API catalog, OpenAI-compatible (needs NVIDIA_API_KEY)
  mock    - fixed templates, no key needed
"""

import json
import os
import re

MODEL = "claude-opus-5-5"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

SYSTEM_PROMPT = """You write follow-up messages for a home service contractor reaching out to \
customers who received a quote but never booked.

Write like the owner or office manager of a local business: warm, plain, short. Reference the \
customer's actual job and any notes. No pressure tactics, no fake urgency, no discounts unless \
the business offers one. Never invent facts about the customer or the business.

Write three messages:
1. day_1_text: an SMS under 300 characters that ends with "Reply STOP to opt out."
2. day_4_email: an email with a subject line and a body under 120 words.
3. day_10_text: a final, low-pressure SMS under 250 characters asking if they'd still like help, \
ending with "Reply STOP to opt out."
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "day_1_text": {"type": "string"},
        "day_4_email_subject": {"type": "string"},
        "day_4_email_body": {"type": "string"},
        "day_10_text": {"type": "string"},
    },
    "required": ["day_1_text", "day_4_email_subject", "day_4_email_body", "day_10_text"],
    "additionalProperties": False,
}


def _first_name(contact: dict) -> str:
    return (contact.get("customer_name") or "there").split()[0]


def _describe(contact: dict, business: dict) -> str:
    return (
        f"Business: {business['name']} ({business['trade']}), sender: {business['sender']}, "
        f"phone: {business['phone']}\n"
        f"Customer first name: {_first_name(contact)}\n"
        f"Job quoted: {contact['job_type']}\n"
        f"Quote amount: ${contact['quote_amount']:,.0f}\n"
        f"Quote date: {contact['quote_date']}\n"
        f"Notes: {contact.get('notes') or 'none'}"
    )


def write_with_claude(client, contact: dict, business: dict) -> dict:
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_PROMPT,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": _describe(contact, business)}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined to write messages for {contact['customer_name']}")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def write_mock(contact: dict, business: dict) -> dict:
    """Template messages so the demo runs without an API key."""
    name, job, biz = _first_name(contact), contact["job_type"], business["name"]
    return {
        "day_1_text": (
            f"Hi {name}, it's {business['sender']} from {biz}. Just checking in on the {job} "
            f"quote we sent. Any questions I can answer? Reply STOP to opt out."
        ),
        "day_4_email_subject": f"Your {contact['job_type']} quote",
        "day_4_email_body": (
            f"Hi {name},\n\nI wanted to follow up on the {job} estimate from {contact['quote_date']}. "
            f"If timing or budget was the holdup, I'm happy to talk through options. "
            f"Just reply here or call {business['phone']}.\n\nThanks,\n{business['sender']}\n{biz}"
        ),
        "day_10_text": (
            f"Hi {name}, last check-in from {biz} about your {job}. Want me to hold a spot "
            f"for you, or close out the quote? Reply STOP to opt out."
        ),
    }


def _parse_json(text: str) -> dict:
    """Pull the JSON object out of a reply that may wrap it in prose or code fences."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in model reply: {text[:200]}")
    data = json.loads(match.group(0))
    missing = [k for k in SCHEMA["required"] if not isinstance(data.get(k), str)]
    if missing:
        raise ValueError(f"Model reply missing fields: {missing}")
    return {k: data[k] for k in SCHEMA["required"]}


def write_with_nvidia(client, contact: dict, business: dict) -> dict:
    prompt = (
        _describe(contact, business)
        + "\n\nReturn only a JSON object with these string fields: "
        + ", ".join(SCHEMA["required"])
        + ". No other text."
    )
    last_error = None
    for _ in range(2):  # one retry if the reply isn't valid JSON
        response = client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1024,
        )
        try:
            return _parse_json(response.choices[0].message.content or "")
        except ValueError as e:
            last_error = e
    raise RuntimeError(f"{contact['customer_name']}: {last_error}")


def make_writer(provider: str):
    if provider == "mock":
        return write_mock
    if provider == "claude":
        import anthropic
        client = anthropic.Anthropic()
        return lambda c, b: write_with_claude(client, c, b)
    if provider == "nvidia":
        from openai import OpenAI
        client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=os.environ.get("NVIDIA_API_KEY", "set-by-proxy"))
        return lambda c, b: write_with_nvidia(client, c, b)
    raise ValueError(f"Unknown provider: {provider}")


def write_all(contacts: list[dict], business: dict, provider: str) -> list[dict]:
    write = make_writer(provider)
    out = []
    for i, contact in enumerate(contacts, 1):
        print(f"  [{i}/{len(contacts)}] {contact['customer_name']} - {contact['job_type']}")
        out.append({**contact, **write(contact, business)})
    return out
