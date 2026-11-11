"""Automatic cold email to contractor leads, following the US CAN-SPAM rules.

Sequence per lead: first email (day 0), bump (day 3), tip (day 7), close-the-file (day 14),
on business days, a capped number per day. Anyone who replies stops getting emails and is
flagged for you; anyone who says "unsubscribe" is never emailed again.

CAN-SPAM requirements this enforces: a real sender name and address, honest subject lines
(written by you/the AI, never "Re:" tricks), your physical mailing address in every email,
and a clear way to opt out that is honored.
"""

import csv
import os
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .campaign import Campaign, slugify
from .clean import normalize_email
from .replies import is_stop

SEQUENCE = [  # (step, days after the lead is added, field holding the body)
    ("first", 0, "first_touch"),
    ("bump", 3, "day_3_followup"),
    ("tip", 7, "day_7_tip"),
    ("close", 14, "day_14_breakup"),
]

PLACEHOLDER = re.compile(r"\[[^\]\n]{1,40}\]")  # e.g. [Your name], [website]

PROSPECT_DEFAULTS = {
    "kind": "prospects",
    "business": "",          # your agency name
    "sender": "",            # your name
    "phone": "",
    "mailing_address": "",   # required by CAN-SPAM (a PO box or virtual mailbox is fine)
    "timezone": "America/Chicago",
    "daily_limit": 20,
    "send_hours": [8, 17],
    "send_days": [0, 1, 2, 3, 4],  # Mon-Fri: these are businesses
    "start_date": None,
    "email_user": "", "email_from": "", "email_host": "",
}


def footer(settings: dict) -> str:
    return (f"\n\n{settings['sender']}\n{settings['business']}"
            + (f"\n{settings['phone']}" if settings.get("phone") else "")
            + f"\n{settings['mailing_address']}"
            + "\n\nNot interested? Reply \"unsubscribe\" and I won't email again.")


def subject_for(lead: dict, step: str) -> str:
    # Same honest subject on every email. No fake "Re:" (the FTC treats that as deceptive).
    return (lead.get("subject") or "Old quotes").strip()


def create(root: str, name: str, outreach_csv: str, settings: dict) -> tuple[Campaign, int, int]:
    """Make a prospect list from an outreach CSV. Leads without an email are kept but skipped."""
    c = Campaign(os.path.join(root, slugify(name)))
    c.save_settings({**PROSPECT_DEFAULTS, **settings, "start_date": date.today().isoformat()})
    rows = []
    with open(outreach_csv, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            email = normalize_email(r.get("email", ""))
            rows.append({**r, "email": email or "", "contact_id": email or slugify(r["company"]),
                         "customer_name": r["company"], "added": date.today().isoformat()})
    fields = list(rows[0].keys()) if rows else ["contact_id"]
    c.save_contacts(rows, fields)
    return c, len(rows), sum(1 for r in rows if r["email"])


def due(c: Campaign, today: date) -> list[tuple[dict, str, str, str]]:
    """(lead, step, subject, body) for every email due today, oldest leads first."""
    s = c.settings()
    status = c.status()
    tz = ZoneInfo(s["timezone"])
    out = []
    for lead in c.contacts():
        if not lead.get("email"):
            continue
        st = status.get(lead["contact_id"], {})
        if st.get("opted_out") or st.get("replies") or st.get("closed") or st.get("booked"):
            continue
        last = st.get("last_sent")
        if last and last.astimezone(tz).date() >= today:
            continue  # one email per lead per day
        added = date.fromisoformat(lead.get("added") or s["start_date"])
        sent = st.get("sent_steps", set())
        for step, offset, field in SEQUENCE:
            if step in sent:
                continue
            if today >= added + timedelta(days=offset) and lead.get(field):
                body = lead[field].strip() + footer(s)
                out.append((lead, step, subject_for(lead, step), body))
            break
    return out


def in_window(s: dict, now: datetime) -> bool:
    local = now.astimezone(ZoneInfo(s["timezone"]))
    return local.weekday() in s["send_days"] and s["send_hours"][0] <= local.hour < s["send_hours"][1]


def send(c: Campaign, live: bool = False, now: datetime | None = None, limit: int | None = None):
    from .sender import email_account, send_email
    s = c.settings()
    now = now or datetime.now(ZoneInfo(s["timezone"]))
    today = now.astimezone(ZoneInfo(s["timezone"])).date()
    if live:
        if not s.get("mailing_address"):
            raise RuntimeError("Add your mailing address first (required by law): "
                               "python agency.py prospect set <list> mailing_address=\"...\"")
        if not in_window(s, now):
            raise RuntimeError("Outside business hours (Mon-Fri, "
                               f"{s['send_hours'][0]}:00-{s['send_hours'][1]}:00). Nothing sent.")
    sent_today = sum(1 for e in c.events() if e["type"] == "sent"
                     and datetime.fromisoformat(e["time"]).astimezone(ZoneInfo(s["timezone"])).date() == today)
    room = max(0, min(limit or s["daily_limit"], s["daily_limit"]) - sent_today)
    batch = due(c, today)[:room]
    account = email_account(c) if live and batch else None
    results = []
    for lead, step, subject, body in batch:
        holes = PLACEHOLDER.findall(subject + body)
        if holes:
            results.append((lead, step, subject, body, f"SKIPPED: fill in {', '.join(sorted(set(holes)))} first"))
            continue
        if not live:
            results.append((lead, step, subject, body, "preview"))
            continue
        try:
            ref = send_email(lead["email"], subject, body, account)
            c.log(lead["contact_id"], "sent", step, ref, when=now)
            results.append((lead, step, subject, body, "sent"))
        except Exception as e:
            results.append((lead, step, subject, body, f"FAILED: {e}"))
    return results


def handle_prospect_reply(c: Campaign, sender: str, body: str) -> dict:
    """Any reply stops the sequence. Unsubscribes are permanent; everything else is flagged."""
    lead = c.find_contact(sender) or {}
    cid = lead.get("contact_id") or sender
    c.log(cid, "reply", "", body)
    if is_stop(body) or "unsubscribe" in body.lower() or "remove me" in body.lower():
        c.log(cid, "opt_out", "", "asked not to be emailed")
        return {"intent": "unsubscribe", "hot": False, "summary": f"{lead.get('company', sender)} unsubscribed"}
    c.log(cid, "alert", "", f"{lead.get('company', sender)} replied: {body[:200]}")
    return {"intent": "replied", "hot": True, "summary": f"{lead.get('company', sender)} replied - answer them today!"}


def summary(c: Campaign) -> dict:
    status = c.status()
    leads = c.contacts()
    with_email = [lead for lead in leads if lead.get("email")]
    st = [status.get(lead["contact_id"], {}) for lead in with_email]
    return {
        "leads": len(leads),
        "with_email": len(with_email),
        "contacted": sum(1 for x in st if x.get("sent_steps")),
        "replied": sum(1 for x in st if x.get("replies") and not x.get("opted_out")),
        "unsubscribed": sum(1 for x in st if x.get("opted_out")),
        "finished": sum(1 for x in st if len(x.get("sent_steps", ())) == len(SEQUENCE)),
    }
