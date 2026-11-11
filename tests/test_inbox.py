"""Email-only campaigns and reading replies from an inbox (with a fake IMAP server)."""

import email
import email.policy
from datetime import date
from email.message import EmailMessage

import pytest

from estimate_recovery import inbox, replies
from estimate_recovery.campaign import DEFAULT_SETTINGS, Campaign
from estimate_recovery.clean import clean
from estimate_recovery.messages import write_all
from estimate_recovery.sender import due_messages

BUSINESS = {"name": "Test HVAC", "trade": "HVAC", "sender": "Sam", "phone": "(214) 555-0100"}


def row(name, phone="", email_=""):
    return {"customer_name": name, "phone": phone, "email": email_, "job_type": "Furnace repair",
            "quote_amount": "900", "quote_date": "2026-01-01", "status": "open", "notes": ""}


@pytest.fixture
def camp(tmp_path):
    c = Campaign(str(tmp_path / "t"))
    c.save_settings({**DEFAULT_SETTINGS, "start_date": "2026-11-02", "channels": ["email"]})
    contacts = write_all(clean([row("Ann Lee", "2145550101", "ann@example.com"),
                                row("Bob Ray", "2145550102")]).contacts, BUSINESS, "mock")
    c.save_contacts(contacts, list(contacts[0].keys()))
    return c


def test_email_only_never_texts(camp):
    due = due_messages(camp, date(2026, 11, 2))
    assert [(o.contact["customer_name"], o.channel) for o in due] == [("Ann Lee", "email")]


def make_mail(sender, body, html=False):
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = sender, "me@example.com", "Re: Your quote"
    m.set_content(body, subtype="html" if html else "plain")
    return m.as_bytes()


def parsed(raw):
    return email.message_from_bytes(raw, policy=email.policy.default)


def test_reply_text_strips_quoted_history():
    raw = make_mail("ann@example.com", "Yes, call me tomorrow.\n\nOn Mon, Nov 2, 2026 Sam wrote:\n> Hi Ann\n")
    assert inbox.reply_text(parsed(raw)) == "Yes, call me tomorrow."
    raw = make_mail("ann@example.com", "Sounds good\n\nSent from my iPhone")
    assert inbox.reply_text(parsed(raw)) == "Sounds good"
    raw = make_mail("ann@example.com", "<div>Interested!</div><div>Thanks</div>", html=True)
    assert inbox.reply_text(parsed(raw)) == "Interested!\nThanks"


class FakeIMAP:
    def __init__(self, mails):
        self.mails = mails  # {num: raw bytes}
        self.seen = set()

    def __call__(self, host):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self, user, pw):
        pass

    def select(self, box):
        pass

    def search(self, charset, criterion):
        return "OK", [b" ".join(k for k in self.mails if k not in self.seen)]

    def fetch(self, num, what):
        raw = self.mails[num]
        if "HEADER.FIELDS" in what:
            raw = f"From: {parsed(raw)['From']}\r\n\r\n".encode()
        return "OK", [(b"", raw)]

    def store(self, num, flags, value):
        self.seen.add(num)


def test_check_replies_processes_only_campaign_customers(camp, monkeypatch):
    fake = FakeIMAP({b"1": make_mail("Ann Lee <ann@example.com>", "unsubscribe"),
                     b"2": make_mail("newsletter@shop.example", "Big sale!")})
    monkeypatch.setattr(inbox.imaplib, "IMAP4_SSL", fake)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "me@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "x")
    monkeypatch.setattr(replies, "classify", lambda *a: pytest.fail("STOP must not use AI"))

    results = inbox.check_replies(camp)
    assert [r["from"] for r in results] == ["ann@example.com"]
    assert fake.seen == {b"1"}                       # other mail stays unread
    assert camp.status()["+12145550101"]["opted_out"]  # Ann is keyed by her phone
    assert due_messages(camp, date(2026, 11, 2)) == []


def test_imap_settings_follow_smtp(monkeypatch):
    for k in ("IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_USER", "me@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-pass")
    assert inbox._imap_settings() == ("imap.gmail.com", "me@gmail.com", "app-pass")


def test_email_account_shared_and_per_client(camp, monkeypatch):
    from estimate_recovery.sender import email_account, password_var
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_USER", "me@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "shared")
    monkeypatch.delenv("SMTP_FROM", raising=False)
    shared = email_account(camp)
    assert shared["user"] == "me@gmail.com" and shared["from"] == "Mike at Comfort Pro HVAC <me@gmail.com>"

    camp.save_settings({**camp.settings(), "email_user": "quotes.co@gmail.com"})
    assert password_var(camp) == "EMAIL_PASSWORD_T"
    with pytest.raises(RuntimeError, match="EMAIL_PASSWORD_T"):
        email_account(camp)
    monkeypatch.setenv("EMAIL_PASSWORD_T", "client-pass")
    own = email_account(camp)
    assert (own["user"], own["password"], own["host"]) == ("quotes.co@gmail.com", "client-pass", "smtp.gmail.com")
    assert own["from"] == "Mike at Comfort Pro HVAC <quotes.co@gmail.com>"
    assert inbox._imap_settings(camp) == ("imap.gmail.com", "quotes.co@gmail.com", "client-pass")
