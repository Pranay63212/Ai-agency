"""Clean an exported list of unsold estimates before any follow-up is sent."""

import csv
import re
from dataclasses import dataclass, field

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SKIP_STATUSES = {"booked", "won", "sold", "opted_out", "do_not_contact", "lost_permanently"}


@dataclass
class CleanResult:
    contacts: list[dict] = field(default_factory=list)
    removed: list[tuple[dict, str]] = field(default_factory=list)


def normalize_phone(raw: str) -> str | None:
    """Return a US phone as +1XXXXXXXXXX, or None if it isn't a valid 10-digit number."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return f"+1{digits}" if len(digits) == 10 else None


def normalize_email(raw: str) -> str | None:
    email = (raw or "").strip().lower()
    return email if EMAIL_RE.match(email) else None


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def clean(rows: list[dict]) -> CleanResult:
    result = CleanResult()
    seen: set[tuple] = set()

    for row in rows:
        status = row.get("status", "").lower()
        if status in SKIP_STATUSES:
            result.removed.append((row, f"status is '{status}'"))
            continue

        phone = normalize_phone(row.get("phone", ""))
        email = normalize_email(row.get("email", ""))
        if not phone and not email:
            result.removed.append((row, "no valid phone or email"))
            continue

        key = (phone or email, row.get("job_type", "").lower())
        if key in seen:
            result.removed.append((row, "duplicate"))
            continue
        seen.add(key)

        try:
            amount = float(row.get("quote_amount", "0").replace("$", "").replace(",", ""))
        except ValueError:
            amount = 0.0

        result.contacts.append({
            **row,
            "contact_id": phone or email,
            "phone": phone or "",
            "email": email or "",
            "quote_amount": amount,
            "channels": ", ".join(c for c, ok in (("text", phone), ("email", email)) if ok),
        })

    return result
