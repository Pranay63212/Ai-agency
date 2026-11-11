"""Automatic cold email to contractor leads, and the website email finder."""

import csv
from datetime import date, datetime, timezone

import pytest

from estimate_recovery import find_emails, prospecting
from estimate_recovery.campaign import Campaign

FIELDS = ["company", "email", "website", "subject", "first_touch", "day_3_followup",
          "day_7_tip", "day_14_breakup"]


@pytest.fixture
def plist(tmp_path, monkeypatch):
    src = tmp_path / "outreach.csv"
    with open(src, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for i, (co, em) in enumerate([("Alpha HVAC", "Info@Alpha.example"), ("Beta Plumbing", ""),
                                      ("Gamma Roofing", "owner@gamma.example")]):
            w.writerow({"company": co, "email": em, "website": f"{co.split()[0].lower()}.example",
                        "subject": f"old quotes {i}", "first_touch": f"Hi {co} team, first.",
                        "day_3_followup": "bump", "day_7_tip": "tip", "day_14_breakup": "close?"})
    c, total, with_email = prospecting.create(str(tmp_path), "Chicago", str(src), {
        "business": "Quote Recovery Co", "sender": "Jade", "phone": "(312) 555-0100",
        "mailing_address": "PO Box 1, Chicago, IL 60601"})
    assert (total, with_email) == (3, 2)
    # Pretend the leads were added on Monday Nov 2, 2026.
    leads = c.contacts()
    for lead in leads:
        lead["added"] = "2026-11-02"
    c.save_contacts(leads, list(leads[0].keys()))
    return c


def steps(c, day):
    return [(lead["company"], step) for lead, step, _, _ in prospecting.due(c, day)]


def log_sent(c, day):
    for lead, step, _, _ in prospecting.due(c, day):
        c.log(lead["contact_id"], "sent", step, when=datetime(day.year, day.month, day.day, 15, tzinfo=timezone.utc))


def test_sequence_and_footer(plist):
    assert steps(plist, date(2026, 11, 2)) == [("Alpha HVAC", "first"), ("Gamma Roofing", "first")]
    _, _, subject, body = prospecting.due(plist, date(2026, 11, 2))[0]
    assert subject == "old quotes 0" and not subject.startswith("Re:")
    assert "PO Box 1, Chicago" in body and "unsubscribe" in body
    log_sent(plist, date(2026, 11, 2))
    assert steps(plist, date(2026, 11, 4)) == []                        # bump waits until day 3
    assert steps(plist, date(2026, 11, 5)) == [("Alpha HVAC", "bump"), ("Gamma Roofing", "bump")]
    log_sent(plist, date(2026, 11, 5))
    assert steps(plist, date(2026, 11, 5)) == []                        # one email per lead per day
    log_sent(plist, date(2026, 11, 9))
    log_sent(plist, date(2026, 11, 16))
    assert prospecting.summary(plist)["finished"] == 2
    assert steps(plist, date(2026, 12, 1)) == []


def test_replies_stop_and_unsubscribes_stick(plist):
    r = prospecting.handle_prospect_reply(plist, "info@alpha.example", "Sure, tell me more")
    assert r["hot"]
    r = prospecting.handle_prospect_reply(plist, "owner@gamma.example", "Please unsubscribe me")
    assert r["intent"] == "unsubscribe"
    assert steps(plist, date(2026, 11, 2)) == []
    s = prospecting.summary(plist)
    assert (s["replied"], s["unsubscribed"]) == (1, 1)


def test_live_send_needs_mailing_address_and_business_hours(plist):
    with pytest.raises(RuntimeError, match="Outside business hours"):
        prospecting.send(plist, live=True, now=datetime(2026, 11, 8, 17, tzinfo=timezone.utc))  # Sunday
    plist.save_settings({**plist.settings(), "mailing_address": ""})
    with pytest.raises(RuntimeError, match="mailing address"):
        prospecting.send(plist, live=True, now=datetime(2026, 11, 3, 17, tzinfo=timezone.utc))


def test_daily_limit(plist, monkeypatch):
    plist.save_settings({**plist.settings(), "daily_limit": 1})
    monkeypatch.setattr("estimate_recovery.sender.email_account", lambda c: {})
    monkeypatch.setattr("estimate_recovery.sender.send_email", lambda *a, **k: "ok")
    now = datetime(2026, 11, 3, 16, tzinfo=timezone.utc)   # Tue 10am Chicago
    assert len(prospecting.send(plist, live=True, now=now)) == 1
    assert prospecting.send(plist, live=True, now=now) == []  # limit reached today


def test_find_email_prefers_own_domain_and_contact_page():
    pages = {
        "https://acme.example/": '<a href="mailto:jobs@gmail.com">x</a> <img src="logo@2x.png">',
        "https://acme.example/contact": "Email us: office&#64;acme.example or sales@partner.example",
    }
    def fetch(url):
        if url not in pages:
            raise OSError("404")
        return pages[url]
    assert find_emails.find_email("acme.example", fetch=fetch, pause=0) == ("office@acme.example", "found")
    assert find_emails.find_email("", fetch=fetch, pause=0) == ("", "no website")
    assert find_emails.find_email("none.example", fetch=fetch, pause=0) == ("", "none on site")


def test_prospect_list_is_a_campaign(plist):
    assert isinstance(plist, Campaign) and plist.find_contact("alpha hvac")["email"] == "info@alpha.example"
