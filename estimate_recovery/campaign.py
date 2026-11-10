"""A campaign is one client's folder: settings, contacts with their messages, and an event log.

clients/<slug>/
    client.json    business details, timezone, start date, pricing, owner contact
    contacts.csv   cleaned contacts plus their AI-written messages
    events.csv     append-only log: sends, replies, bookings, opt-outs, alerts
"""

import csv
import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import date, datetime, timezone

_LOG_LOCK = threading.Lock()  # the webhook server handles requests on several threads

EVENT_FIELDS = ["time", "contact_id", "type", "step", "detail", "amount"]
EVENT_TYPES = {"sent", "reply", "booked", "closed", "opt_out", "alert", "note"}

# Follow-up sequence: (step name, days after campaign start, channel preference)
SEQUENCE = [
    ("day_1", 0, "text"),
    ("day_4", 3, "email"),
    ("day_10", 9, "text"),
]

DEFAULT_SETTINGS = {
    "business": "Comfort Pro HVAC",
    "trade": "HVAC",
    "sender": "Mike",
    "phone": "(214) 555-0100",
    "timezone": "America/Chicago",
    "start_date": None,
    "price_per_booking": 200,
    "pilot": True,
    "owner_email": "",
    "owner_phone": "",
    "booking_link": "",
    "send_hours": [9, 20],
    "send_days": [0, 1, 2, 3, 4, 5],  # Mon-Sat
    "min_gap_days": 2,  # never message the same customer on back-to-back days
}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "client"


@dataclass
class Campaign:
    path: str

    @property
    def settings_path(self): return os.path.join(self.path, "client.json")
    @property
    def contacts_path(self): return os.path.join(self.path, "contacts.csv")
    @property
    def events_path(self): return os.path.join(self.path, "events.csv")

    # settings ---------------------------------------------------------
    def settings(self) -> dict:
        with open(self.settings_path, encoding="utf-8") as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}

    def save_settings(self, settings: dict) -> None:
        os.makedirs(self.path, exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    def business(self) -> dict:
        s = self.settings()
        return {"name": s["business"], "trade": s["trade"], "sender": s["sender"], "phone": s["phone"]}

    def start_date(self) -> date | None:
        raw = self.settings().get("start_date")
        return date.fromisoformat(raw) if raw else None

    # contacts ---------------------------------------------------------
    def contacts(self) -> list[dict]:
        if not os.path.exists(self.contacts_path):
            return []
        with open(self.contacts_path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def save_contacts(self, rows: list[dict], fields: list[str]) -> None:
        os.makedirs(self.path, exist_ok=True)
        with open(self.contacts_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    def find_contact(self, key: str) -> dict | None:
        """Match by contact id, phone, email or (case-insensitive) customer name."""
        from .clean import normalize_email, normalize_phone
        key = (key or "").strip()
        phone, email = normalize_phone(key), normalize_email(key)
        contacts = self.contacts()
        for c in contacts:
            if key == c.get("contact_id") or (phone and phone == c.get("phone")) \
                    or (email and email == c.get("email")) \
                    or key.lower() == (c.get("customer_name") or "").lower():
                return c
        # Fall back to a partial name ("marcus"), but only if exactly one contact matches.
        partial = [c for c in contacts if len(key) >= 3 and key.lower() in (c.get("customer_name") or "").lower()]
        return partial[0] if len(partial) == 1 else None

    # events -----------------------------------------------------------
    def events(self) -> list[dict]:
        if not os.path.exists(self.events_path):
            return []
        with open(self.events_path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def log(self, contact_id: str, type_: str, step: str = "", detail: str = "",
            amount: float | str = "", when: datetime | None = None) -> dict:
        if type_ not in EVENT_TYPES:
            raise ValueError(f"Unknown event type {type_!r}")
        os.makedirs(self.path, exist_ok=True)
        row = {
            "time": (when or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
            "contact_id": contact_id, "type": type_, "step": step,
            "detail": (detail or "").replace("\r", " ").replace("\n", " ")[:2000],
            "amount": amount,
        }
        with _LOG_LOCK:
            new = not os.path.exists(self.events_path)
            with open(self.events_path, "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=EVENT_FIELDS)
                if new:
                    w.writeheader()
                w.writerow(row)
        return row

    def status(self) -> dict[str, dict]:
        """Per-contact summary derived from the event log."""
        out: dict[str, dict] = {}
        for e in self.events():
            s = out.setdefault(e["contact_id"], {"sent_steps": set(), "replies": 0, "booked": False,
                                                 "booked_amount": 0.0, "opted_out": False, "closed": False,
                                                 "last_sent": None})
            if e["type"] == "sent":
                s["sent_steps"].add(e["step"])
                s["last_sent"] = datetime.fromisoformat(e["time"])
            elif e["type"] == "reply":
                s["replies"] += 1
            elif e["type"] == "booked":
                s["booked"] = True
                try:
                    s["booked_amount"] += float(e["amount"] or 0)
                except ValueError:
                    pass
            elif e["type"] == "opt_out":
                s["opted_out"] = True
            elif e["type"] == "closed":
                s["closed"] = True
        return out


def open_campaign(root: str, slug: str) -> Campaign:
    c = Campaign(os.path.join(root, slug))
    if not os.path.exists(c.settings_path):
        raise SystemExit(f"No campaign at {c.path}. Create one with: python agency.py new ...")
    return c
