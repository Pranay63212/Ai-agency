"""Work out which follow-ups are due and send them by text (Twilio) or email (SMTP).

Safe by default: nothing is sent unless send_due(..., mode="live") is called.

Text:  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM (your registered A2P 10DLC number)
Email: SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM
"""

import base64
import json
import os
import re
import smtplib
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from .campaign import SEQUENCE, Campaign
from .messages import OPT_OUT

EMAIL_UNSUB = "If you'd rather not hear from us, just reply \"unsubscribe\"."


@dataclass
class Outgoing:
    contact: dict
    step: str
    channel: str  # "text" or "email"
    to: str
    subject: str
    body: str


def _content(contact: dict, step: str, channel: str) -> tuple[str, str] | None:
    job = contact.get("job_type") or "your project"
    if step == "day_4":
        if channel != "email":
            return None
        body = contact.get("day_4_email_body", "")
        return contact.get("day_4_email_subject") or f"Your {job} quote", f"{body}\n\n{EMAIL_UNSUB}"
    text = contact.get(f"{step}_text", "")
    if channel == "text":
        return "", text
    # Text content going out by email: drop the SMS opt-out line, add an email one.
    body = text.replace(OPT_OUT, "").strip()
    return f"Following up on your {job} quote", f"{body}\n\n{EMAIL_UNSUB}"


def _pick_channel(contact: dict, step: str, preferred: str,
                  allowed: tuple[str, ...] = ("text", "email")) -> str | None:
    has = {"text": bool(contact.get("phone")) and "text" in allowed,
           "email": bool(contact.get("email")) and "email" in allowed}
    if step == "day_4":
        return "email" if has["email"] else None
    if has[preferred]:
        return preferred
    other = "email" if preferred == "text" else "text"
    return other if has[other] else None


def in_send_window(settings: dict, now: datetime) -> bool:
    local = now.astimezone(ZoneInfo(settings["timezone"]))
    start_h, end_h = settings["send_hours"]
    return local.weekday() in settings["send_days"] and start_h <= local.hour < end_h


def due_messages(campaign: Campaign, today: date) -> list[Outgoing]:
    start = campaign.start_date()
    if not start:
        return []
    settings = campaign.settings()
    tz = ZoneInfo(settings["timezone"])
    gap = timedelta(days=int(settings.get("min_gap_days", 2)))
    status = campaign.status()
    due = []
    for c in campaign.contacts():
        s = status.get(c["contact_id"], {})
        # Stop the automated sequence once the customer opted out, replied, booked or was closed.
        if s.get("opted_out") or s.get("booked") or s.get("closed") or s.get("replies"):
            continue
        last = s.get("last_sent")
        if last and today < last.astimezone(tz).date() + gap:
            continue
        sent = s.get("sent_steps", set())
        for step, offset, preferred in SEQUENCE:
            if step in sent:
                continue
            if today < start + timedelta(days=offset):
                break
            channel = _pick_channel(c, step, preferred, tuple(settings.get("channels") or ("text", "email")))
            content = _content(c, step, channel) if channel else None
            if not content:
                continue  # step doesn't apply to this contact (e.g. no email for day_4)
            subject, body = content
            to = c["phone"] if channel == "text" else c["email"]
            due.append(Outgoing(c, step, channel, to, subject, body))
            break  # at most one message per contact per run
    return due


# transports ---------------------------------------------------------------

def send_text(to: str, body: str) -> str:
    sid, token, from_ = (os.environ.get(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM"))
    if not (sid and token and from_):
        raise RuntimeError("Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and TWILIO_FROM to send texts")
    req = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data=urllib.parse.urlencode({"To": to, "From": from_, "Body": body}).encode(),
        headers={"Authorization": "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode()},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp).get("sid", "")


def password_var(campaign: Campaign) -> str:
    slug = os.path.basename(os.path.normpath(campaign.path))
    return "EMAIL_PASSWORD_" + re.sub(r"\W", "_", slug).upper()


def email_account(campaign: Campaign | None = None) -> dict:
    """Which mailbox to send from (and read replies from).

    A client with "email_user" set in its settings uses its own mailbox; its password comes
    from .env as EMAIL_PASSWORD_<CLIENT_SLUG>. Otherwise the shared SMTP_* settings are used.
    Either way the sender name defaults to "<Sender> at <Business>".
    """
    s = campaign.settings() if campaign else {}
    if s.get("email_user"):
        user = s["email_user"]
        password = os.environ.get(password_var(campaign), "")
        if not password:
            raise RuntimeError(f"Add {password_var(campaign)}=<app password> to .env for {user}")
        host = s.get("email_host") or "smtp.gmail.com"
        port = 587
    else:
        user, password = os.environ.get("SMTP_USER", ""), os.environ.get("SMTP_PASSWORD", "")
        host, port = os.environ.get("SMTP_HOST", ""), int(os.environ.get("SMTP_PORT", "587"))
        if not (host and user):
            raise RuntimeError("Set SMTP_HOST, SMTP_USER and SMTP_PASSWORD in .env to send email")
    named = f"{s['sender']} at {s['business']} <{user}>" if s.get("sender") and s.get("business") else user
    from_ = s.get("email_from") or (os.environ.get("SMTP_FROM") if not s.get("email_user") else "") or named
    return {"host": host, "port": port, "user": user, "password": password, "from": from_}


def send_email(to: str, subject: str, body: str, account: dict | None = None) -> str:
    acct = account or email_account()
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = acct["from"], to, subject
    msg.set_content(body)
    with smtplib.SMTP(acct["host"], acct["port"], timeout=30) as s:
        s.starttls()
        if acct["password"]:
            s.login(acct["user"], acct["password"])
        s.send_message(msg)
    return msg.get("Message-ID", "") or "sent"


def deliver(out: Outgoing, account: dict | None = None) -> str:
    if out.channel == "text":
        return send_text(out.to, out.body)
    return send_email(out.to, out.subject, out.body, account)


def send_due(campaign: Campaign, mode: str = "dry-run", now: datetime | None = None,
             limit: int = 200) -> list[tuple[Outgoing, str]]:
    """mode: "dry-run" (show only), "mark" (log as sent, you sent them elsewhere), "live" (send)."""
    settings = campaign.settings()
    now = now or datetime.now(ZoneInfo(settings["timezone"]))
    today = now.astimezone(ZoneInfo(settings["timezone"])).date()
    if mode == "live" and not in_send_window(settings, now):
        raise RuntimeError(
            f"Outside sending hours ({settings['send_hours'][0]}:00-{settings['send_hours'][1]}:00 "
            f"{settings['timezone']}, Mon-Sat). Nothing sent.")
    results = []
    due = due_messages(campaign, today)[:limit]
    account = email_account(campaign) if mode == "live" and any(o.channel == "email" for o in due) else None
    for out in due:
        if mode == "dry-run":
            results.append((out, "preview"))
            continue
        try:
            ref = deliver(out, account) if mode == "live" else "marked"
        except Exception as e:
            results.append((out, f"FAILED: {e}"))
            continue
        campaign.log(out.contact["contact_id"], "sent", out.step, f"{out.channel} {ref}")
        results.append((out, ref))
    return results
