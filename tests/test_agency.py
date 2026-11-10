"""Tests for the estimate recovery tools. No network: AI calls are replaced with stubs."""

import base64
import hashlib
import hmac
from datetime import date, datetime, timedelta, timezone

import pytest

from estimate_recovery import replies
from estimate_recovery.campaign import DEFAULT_SETTINGS, Campaign
from estimate_recovery.clean import clean, normalize_phone
from estimate_recovery.messages import OPT_OUT, ensure_opt_out, write_all
from estimate_recovery.sender import due_messages, in_send_window, send_due
from estimate_recovery.webhook import twilio_signature_ok
from estimate_recovery.weekly import invoice_text, open_hot_leads, stats
from estimate_recovery.llm import AIError, parse_json

BUSINESS = {"name": "Test HVAC", "trade": "HVAC", "sender": "Sam", "phone": "(214) 555-0100"}


def row(name, phone="", email="", job="AC replacement", status="open", amount="5000"):
    return {"customer_name": name, "phone": phone, "email": email, "job_type": job,
            "quote_amount": amount, "quote_date": "2026-01-01", "status": status, "notes": ""}


@pytest.fixture
def camp(tmp_path):
    c = Campaign(str(tmp_path / "test-hvac"))
    c.save_settings({**DEFAULT_SETTINGS, "business": "Test HVAC", "start_date": "2026-11-02"})
    rows = [row("Ann Lee", phone="2145550101", email="ann@example.com"),
            row("Bob Ray", phone="2145550102"),
            row("Cal Fox", email="cal@example.com")]
    contacts = write_all(clean(rows).contacts, BUSINESS, "mock")
    c.save_contacts(contacts, list(contacts[0].keys()))
    return c


# cleaning ------------------------------------------------------------------

def test_normalize_phone():
    assert normalize_phone("(214) 555-0101") == "+12145550101"
    assert normalize_phone("1-214-555-0101") == "+12145550101"
    assert normalize_phone("555-12") is None


def test_clean_removes_bad_rows():
    result = clean([
        row("A", phone="2145550101"),
        row("A dup", phone="214.555.0101"),
        row("Booked", phone="2145550103", status="booked"),
        row("Opted", phone="2145550104", status="opted_out"),
        row("No contact", phone="12"),
        row("Email only", email="X@Example.com"),
    ])
    assert [c["customer_name"] for c in result.contacts] == ["A", "Email only"]
    assert result.contacts[1]["email"] == "x@example.com"
    reasons = sorted(r for _, r in result.removed)
    assert reasons == ["duplicate", "no valid phone or email", "status is 'booked'", "status is 'opted_out'"]


# messages ------------------------------------------------------------------

def test_every_text_has_opt_out():
    assert ensure_opt_out("Hi there").endswith(OPT_OUT)
    assert ensure_opt_out("Hi. Reply STOP to opt out.") == "Hi. Reply STOP to opt out."


def test_ai_failure_falls_back_to_template(monkeypatch):
    def boom(*a, **k):
        raise AIError("down")
    monkeypatch.setattr("estimate_recovery.messages.chat_json", boom)
    out = write_all(clean([row("Ann", phone="2145550101")]).contacts, BUSINESS, "nvidia")
    assert out[0]["day_1_text"].startswith("Hi Ann")


def test_parse_json_handles_fences_and_missing_fields():
    assert parse_json('Sure:\n```json\n{"a": "1", "b": "2"}\n```', ["a", "b"]) == {"a": "1", "b": "2"}
    with pytest.raises(AIError):
        parse_json('{"a": "1"}', ["a", "b"])
    with pytest.raises(AIError):
        parse_json("", ["a"])


# sending -------------------------------------------------------------------

def steps(camp, day):
    return {(o.contact["customer_name"], o.step, o.channel) for o in due_messages(camp, day)}


def test_nothing_due_before_start(camp):
    assert steps(camp, date(2026, 11, 1)) == set()


def test_day_one_uses_text_or_falls_back_to_email(camp):
    assert steps(camp, date(2026, 11, 2)) == {
        ("Ann Lee", "day_1", "text"), ("Bob Ray", "day_1", "text"), ("Cal Fox", "day_1", "email")}


def test_sequence_respects_gap_and_skips_day4_without_email(camp):
    day1 = datetime(2026, 11, 2, 15, tzinfo=timezone.utc)
    for o in due_messages(camp, date(2026, 11, 2)):
        camp.log(o.contact["contact_id"], "sent", o.step, when=day1)
    assert steps(camp, date(2026, 11, 3)) == set()  # 2-day gap
    # Day 5: day_4 email is due for Ann and Cal; Bob has no email so nothing until day_10.
    assert steps(camp, date(2026, 11, 6)) == {("Ann Lee", "day_4", "email"), ("Cal Fox", "day_4", "email")}
    assert steps(camp, date(2026, 11, 11)) >= {("Bob Ray", "day_10", "text")}


def test_reply_optout_and_booking_stop_sequence(camp):
    ann, bob, cal = (c["contact_id"] for c in camp.contacts())
    camp.log(ann, "reply", detail="maybe")
    camp.log(bob, "opt_out")
    camp.log(cal, "booked", amount=5000)
    assert steps(camp, date(2026, 11, 2)) == set()


def test_email_versions_drop_sms_optout(camp):
    out = [o for o in due_messages(camp, date(2026, 11, 2)) if o.channel == "email"][0]
    assert OPT_OUT not in out.body and "unsubscribe" in out.body


def test_send_window():
    s = DEFAULT_SETTINGS
    assert in_send_window(s, datetime(2026, 11, 10, 16, tzinfo=timezone.utc))      # Tue 10am CST
    assert not in_send_window(s, datetime(2026, 11, 10, 4, tzinfo=timezone.utc))   # Mon 10pm CST
    assert not in_send_window(s, datetime(2026, 11, 8, 18, tzinfo=timezone.utc))   # Sunday


def test_live_send_refused_outside_hours(camp):
    with pytest.raises(RuntimeError):
        send_due(camp, "live", now=datetime(2026, 11, 10, 4, tzinfo=timezone.utc))


def test_dry_run_logs_nothing(camp):
    send_due(camp, "dry-run", now=datetime(2026, 11, 3, 16, tzinfo=timezone.utc))
    assert camp.events() == []


# replies -------------------------------------------------------------------

@pytest.mark.parametrize("body,expected", [
    ("STOP", True), ("stop.", True), ("Unsubscribe", True), ("Stop texting me", True),
    ("Don't stop, I want the quote", False), ("yes please", False)])
def test_is_stop(body, expected):
    assert replies.is_stop(body) is expected


def test_stop_reply_opts_out_without_ai(camp, monkeypatch):
    monkeypatch.setattr(replies, "classify", lambda *a: pytest.fail("AI must not run for STOP"))
    r = replies.handle_reply(camp, "(214) 555-0102", "STOP")
    assert r["intent"] == "stop"
    assert camp.status()["+12145550102"]["opted_out"]


def test_hot_reply_alerts_owner(camp, monkeypatch):
    monkeypatch.setattr(replies, "classify", lambda *a: {
        "intent": "interested", "hot": True, "summary": "wants Tuesday", "draft_reply": "Great!"})
    r = replies.handle_reply(camp, "+12145550101", "Yes can you come Tuesday?", auto_reply=True)
    assert r["send_back"] == "Great!"
    assert [h["name"] for h in open_hot_leads(camp)] == ["Ann Lee"]


def test_not_interested_closes_contact(camp, monkeypatch):
    monkeypatch.setattr(replies, "classify", lambda *a: {
        "intent": "not_interested", "hot": False, "summary": "no", "draft_reply": "Thanks"})
    replies.handle_reply(camp, "cal@example.com", "no thanks")
    assert camp.status()["cal@example.com"]["closed"]


def test_ai_outage_still_flags_owner(camp, monkeypatch):
    def boom(*a):
        raise AIError("down")
    monkeypatch.setattr(replies, "classify", boom)
    r = replies.handle_reply(camp, "+12145550101", "Can you call me?")
    assert r["hot"] and "AI unavailable" in r["summary"]


# contacts, reports, webhook -----------------------------------------------

def test_find_contact(camp):
    assert camp.find_contact("ann lee")["customer_name"] == "Ann Lee"
    assert camp.find_contact("bob")["customer_name"] == "Bob Ray"
    assert camp.find_contact("214-555-0101")["customer_name"] == "Ann Lee"
    assert camp.find_contact("zz") is None


def test_stats_and_invoice(camp):
    ann = camp.contacts()[0]["contact_id"]
    camp.log(ann, "sent", "day_1")
    camp.log(ann, "booked", amount=8000)
    s = stats(camp)
    assert (s["bookings"], s["revenue"], s["amount_due"]) == (1, 8000, 0)  # pilot: free
    assert "Pilot period: no charge" in invoice_text(camp)
    camp.save_settings({**camp.settings(), "pilot": False, "price_per_booking": 250})
    assert stats(camp)["amount_due"] == 250
    assert "TOTAL DUE: $250" in invoice_text(camp)


def test_stats_window_excludes_old_events(camp):
    ann = camp.contacts()[0]["contact_id"]
    camp.log(ann, "booked", amount=1, when=datetime.now(timezone.utc) - timedelta(days=30))
    assert stats(camp, 7)["bookings"] == 0 and stats(camp)["bookings"] == 1


def test_twilio_signature():
    url, params, token = "https://x.example/sms/a", {"From": "+1", "Body": "hi"}, "secret"
    sig = base64.b64encode(hmac.new(token.encode(), (url + "Bodyhi" + "From+1").encode(),
                                    hashlib.sha1).digest()).decode()
    assert twilio_signature_ok(url, params, sig, token)
    assert not twilio_signature_ok(url, params, "forged", token)
