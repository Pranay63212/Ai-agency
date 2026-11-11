"""Check an email inbox (IMAP) for customer replies and process them automatically.

Uses the same account you send from. For Gmail: turn on 2-step verification, create an app
password, and set:
    SMTP_USER=you@gmail.com  SMTP_PASSWORD=<app password>
IMAP_HOST defaults to imap.gmail.com when SMTP_HOST is smtp.gmail.com. Set IMAP_HOST,
IMAP_USER, IMAP_PASSWORD to use different settings.
"""

import email
import email.policy
import imaplib
import os
import re
from email.utils import parseaddr

from .campaign import Campaign
from .replies import handle_reply

QUOTE_MARKERS = [
    re.compile(r"^On .+wrote:\s*$", re.M),             # Gmail, Apple Mail
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}", re.M | re.I),  # Outlook
    re.compile(r"^From: .+$", re.M),                   # Outlook header block
    re.compile(r"^Sent from my ", re.M),               # phone signatures
]


def _imap_settings(campaign: Campaign | None = None) -> tuple[str, str, str]:
    """Same mailbox the campaign sends from; IMAP_* overrides the shared account."""
    from .sender import email_account
    if campaign is not None and campaign.settings().get("email_user"):
        acct = email_account(campaign)
        return acct["host"].replace("smtp.", "imap.", 1), acct["user"], acct["password"]
    smtp_host = os.environ.get("SMTP_HOST", "")
    host = os.environ.get("IMAP_HOST") or (smtp_host.replace("smtp.", "imap.", 1) if smtp_host else "")
    user = os.environ.get("IMAP_USER") or os.environ.get("SMTP_USER", "")
    password = os.environ.get("IMAP_PASSWORD") or os.environ.get("SMTP_PASSWORD", "")
    if not (host and user and password):
        raise RuntimeError("Set SMTP_HOST, SMTP_USER and SMTP_PASSWORD (or IMAP_*) to check replies")
    return host, user, password


def reply_text(msg: email.message.EmailMessage) -> str:
    """The new part of a reply: plain text, without the quoted earlier message or signature."""
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    text = part.get_content()
    if part.get_content_type() == "text/html":
        text = re.sub(r"<(br|p|div)[^>]*>", "\n", text, flags=re.I)
        text = re.sub(r"<[^>]+>", "", text)
    cut = len(text)
    for marker in QUOTE_MARKERS:
        m = marker.search(text)
        if m:
            cut = min(cut, m.start())
    lines = [ln for ln in text[:cut].splitlines() if not ln.lstrip().startswith(">")]
    return "\n".join(lines).strip()


def check_replies(campaign: Campaign, provider: str | None = None, dry_run: bool = False,
                  handler=None) -> list[dict]:
    """Process unread replies from this campaign's contacts. Other mail is left untouched.

    handler(campaign, sender, body) -> dict lets other workflows (prospecting) reuse this;
    by default customer replies go through replies.handle_reply.
    """
    emails = {c["email"].lower() for c in campaign.contacts() if c.get("email")}
    host, user, password = _imap_settings(campaign)
    results = []
    with imaplib.IMAP4_SSL(host) as imap:
        imap.login(user, password)
        imap.select("INBOX")
        _, data = imap.search(None, "UNSEEN")
        for num in data[0].split():
            # Peek at the sender first so mail from anyone else stays unread.
            _, head = imap.fetch(num, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
            sender = parseaddr(email.message_from_bytes(head[0][1]).get("From", ""))[1].lower()
            if sender not in emails:
                continue
            _, raw = imap.fetch(num, "(BODY.PEEK[])")
            msg = email.message_from_bytes(raw[0][1], policy=email.policy.default)
            body = reply_text(msg)
            if dry_run:
                results.append({"from": sender, "body": body})
                continue
            if handler:
                result = handler(campaign, sender, body or "(empty reply)")
            else:
                result = handle_reply(campaign, sender, body or "(empty reply)", provider)
            imap.store(num, "+FLAGS", "\\Seen")
            results.append({"from": sender, "body": body, **result})
    return results
