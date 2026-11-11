"""Run the unsold-estimate recovery agency from the command line.

Client work
  python agency.py new "Cool Air HVAC" --input their_export.csv --sender Mike --phone "(214) 555-0100"
  python agency.py send cool-air-hvac              # preview what's due today (sends nothing)
  python agency.py send cool-air-hvac --live       # send by Twilio/SMTP
  python agency.py send cool-air-hvac --mark       # you sent them another way; just log them
  python agency.py reply cool-air-hvac --from "+12145550142" --body "Yes, can you come Tuesday?"
  python agency.py book cool-air-hvac "Maria Lopez" --amount 8450
  python agency.py close cool-air-hvac "James Carter" --reason "went with another company"
  python agency.py report cool-air-hvac            # weekly report + invoice
  python agency.py status cool-air-hvac
  python agency.py set cool-air-hvac pilot=false price_per_booking=250
  python agency.py serve --port 8080               # receive replies from Twilio

Finding clients
  python agency.py outreach --leads leads.csv --name "Jade" --agency "Recover Ready"

AI: --provider nvidia (default, NVIDIA_API_KEY), claude (ANTHROPIC_API_KEY) or mock (no key).
Client data lives in ./clients (git-ignored: it holds customers' personal details).
"""

import argparse
import csv
import json
import os
import sys
from datetime import date

from estimate_recovery.campaign import DEFAULT_SETTINGS, Campaign, open_campaign, slugify
from estimate_recovery.clean import clean, load_csv
from estimate_recovery.messages import write_all
from estimate_recovery.report import build_report

ROOT = os.environ.get("AGENCY_CLIENTS_DIR", "clients")
CONTACT_FIELDS = [
    "contact_id", "customer_name", "phone", "email", "channels", "job_type", "quote_amount",
    "quote_date", "notes", "day_1_text", "day_4_email_subject", "day_4_email_body", "day_10_text",
]


def cmd_new(a):
    slug = a.slug or slugify(a.business)
    c = Campaign(os.path.join(ROOT, slug))
    if os.path.exists(c.settings_path) and not a.force:
        sys.exit(f"{c.path} already exists. Use --force to rebuild its messages.")
    settings = {**DEFAULT_SETTINGS, "business": a.business, "trade": a.trade, "sender": a.sender,
                "phone": a.phone, "timezone": a.timezone, "price_per_booking": a.price,
                "owner_email": a.owner_email, "booking_link": a.booking_link,
                "start_date": a.start or date.today().isoformat(), "pilot": not a.paid}
    c.save_settings(settings)

    rows = load_csv(a.input)
    cleaned = clean(rows)
    if a.limit:
        cleaned.contacts = cleaned.contacts[:a.limit]
    print(f"{len(rows)} estimates: {len(cleaned.contacts)} ready, {len(cleaned.removed)} removed.")
    print("Writing follow-up messages...")
    contacts = write_all(cleaned.contacts, c.business(), a.provider)
    c.save_contacts(contacts, CONTACT_FIELDS)
    with open(os.path.join(c.path, "plan.html"), "w", encoding="utf-8") as f:
        f.write(build_report(contacts, cleaned.removed, c.business(), a.close_rate, a.provider))
    print(f"\nCampaign ready: {c.path}\n  Review messages: {c.contacts_path}\n"
          f"  Client-facing plan: {os.path.join(c.path, 'plan.html')}\n"
          f"  Next: python agency.py send {slug}")


def cmd_send(a):
    from estimate_recovery.sender import send_due
    c = open_campaign(ROOT, a.slug)
    mode = "live" if a.live else "mark" if a.mark else "dry-run"
    try:
        results = send_due(c, mode=mode, limit=a.limit)
    except RuntimeError as e:
        sys.exit(str(e))
    if not results:
        print("Nothing due right now.")
    for out, ref in results:
        print(f"[{out.step} via {out.channel}] {out.contact['customer_name']} <{out.to}> -> {ref}")
        if mode == "dry-run":
            if out.subject:
                print(f"    Subject: {out.subject}")
            print("    " + out.body.replace("\n", "\n    "))
    if mode == "dry-run" and results:
        print(f"\n{len(results)} message(s) due. Nothing was sent. Use --live to send or --mark to log.")


def cmd_reply(a):
    from estimate_recovery.replies import handle_reply
    c = open_campaign(ROOT, a.slug)
    r = handle_reply(c, a.from_, a.body, a.provider if a.provider != "mock" else None, auto_reply=False)
    print(json.dumps({k: v for k, v in r.items() if k != "send_back"}, indent=2))


def _contact_or_exit(c: Campaign, key: str) -> dict:
    contact = c.find_contact(key)
    if not contact:
        sys.exit(f"No contact matching {key!r} in {c.path}")
    return contact


def cmd_book(a):
    c = open_campaign(ROOT, a.slug)
    contact = _contact_or_exit(c, a.contact)
    amount = a.amount if a.amount is not None else contact.get("quote_amount", "")
    c.log(contact["contact_id"], "booked", "", a.note or "", amount)
    print(f"Booked: {contact['customer_name']} ({contact['job_type']}) ${float(amount or 0):,.0f}")


def cmd_close(a):
    c = open_campaign(ROOT, a.slug)
    contact = _contact_or_exit(c, a.contact)
    c.log(contact["contact_id"], "opt_out" if a.opt_out else "closed", "", a.reason or "")
    print(f"{'Opted out' if a.opt_out else 'Closed'}: {contact['customer_name']}")


def cmd_report(a):
    from estimate_recovery.weekly import build_weekly, invoice_text
    c = open_campaign(ROOT, a.slug)
    stamp = date.today().isoformat()
    report = os.path.join(c.path, f"weekly-{stamp}.html")
    invoice = os.path.join(c.path, f"invoice-{stamp}.txt")
    with open(report, "w", encoding="utf-8") as f:
        f.write(build_weekly(c))
    with open(invoice, "w", encoding="utf-8") as f:
        f.write(invoice_text(c))
    print(f"Report:  {report}\nInvoice: {invoice}")


def cmd_status(a):
    from estimate_recovery.weekly import open_hot_leads, stats
    c = open_campaign(ROOT, a.slug)
    s = stats(c)
    print(f"{c.settings()['business']}  (started {c.settings()['start_date']})")
    for k in ("contacts", "customers_reached", "messages_sent", "replies", "hot_leads",
              "bookings", "revenue", "opt_outs", "amount_due"):
        print(f"  {k.replace('_', ' '):<18} {s[k]:,.0f}" if isinstance(s[k], float) else f"  {k.replace('_', ' '):<18} {s[k]}")
    hot = open_hot_leads(c)
    if hot:
        print("\nCall these:")
        for h in hot:
            print(f"  {h['name']} {h['phone']} - {h['summary']}")


def cmd_set(a):
    c = open_campaign(ROOT, a.slug)
    s = c.settings()
    for pair in a.pairs:
        k, _, v = pair.partition("=")
        if k not in DEFAULT_SETTINGS:
            sys.exit(f"Unknown setting {k!r}. Options: {', '.join(DEFAULT_SETTINGS)}")
        try:
            s[k] = json.loads(v)
        except json.JSONDecodeError:
            s[k] = v
    c.save_settings(s)
    print(json.dumps(s, indent=2))


def cmd_serve(a):
    from estimate_recovery.webhook import serve
    serve(ROOT, a.host, a.port, a.provider if a.provider != "mock" else None, a.auto_reply)


def cmd_outreach(a):
    from estimate_recovery.outreach import FIELDS, load_leads, to_markdown, write_outreach
    leads, skipped = load_leads(a.leads)
    print(f"{len(leads)} leads to contact, {len(skipped)} skipped (under 20 reviews).")
    rows = write_outreach(leads, {"name": a.name, "agency": a.agency}, a.provider)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        fields = list(leads[0].keys()) + FIELDS if leads else FIELDS
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    md = os.path.splitext(a.out)[0] + ".md"
    with open(md, "w", encoding="utf-8") as f:
        f.write(to_markdown(rows))
    print(f"Saved: {a.out}\n       {md} (easy to read)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    ai = argparse.ArgumentParser(add_help=False)
    ai.add_argument("--provider", choices=["nvidia", "claude", "mock"],
                    default=os.environ.get("AI_PROVIDER", "nvidia"))

    n = sub.add_parser("new", parents=[ai], help="set up a client campaign from their estimate export")
    n.add_argument("business")
    n.add_argument("--input", required=True)
    n.add_argument("--slug")
    n.add_argument("--trade", default="HVAC")
    n.add_argument("--sender", required=True, help="who the messages come from, e.g. the owner's first name")
    n.add_argument("--phone", required=True, help="business phone shown in messages")
    n.add_argument("--timezone", default="America/Chicago")
    n.add_argument("--price", type=float, default=200, help="your fee per booked job")
    n.add_argument("--owner-email", default="", help="where hot-lead alerts go")
    n.add_argument("--booking-link", default="")
    n.add_argument("--start", help="campaign start date YYYY-MM-DD (default today)")
    n.add_argument("--paid", action="store_true", help="not a free pilot; bill bookings")
    n.add_argument("--close-rate", type=float, default=0.08)
    n.add_argument("--limit", type=int, help="only use the first N contacts (pilot = 100)")
    n.add_argument("--force", action="store_true")
    n.set_defaults(func=cmd_new)

    s = sub.add_parser("send", help="send (or preview) follow-ups due today")
    s.add_argument("slug")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--live", action="store_true")
    g.add_argument("--mark", action="store_true")
    s.add_argument("--limit", type=int, default=200)
    s.set_defaults(func=cmd_send)

    r = sub.add_parser("reply", parents=[ai], help="process a reply by hand (email, phone call notes)")
    r.add_argument("slug")
    r.add_argument("--from", dest="from_", required=True)
    r.add_argument("--body", required=True)
    r.set_defaults(func=cmd_reply)

    b = sub.add_parser("book", help="record a booked job")
    b.add_argument("slug")
    b.add_argument("contact", help="name, phone or email")
    b.add_argument("--amount", type=float, help="job value (default: the quote amount)")
    b.add_argument("--note")
    b.set_defaults(func=cmd_book)

    cl = sub.add_parser("close", help="stop following up with a contact")
    cl.add_argument("slug")
    cl.add_argument("contact")
    cl.add_argument("--reason")
    cl.add_argument("--opt-out", action="store_true", help="they asked not to be contacted")
    cl.set_defaults(func=cmd_close)

    rp = sub.add_parser("report", help="weekly report + invoice")
    rp.add_argument("slug")
    rp.set_defaults(func=cmd_report)

    st = sub.add_parser("status", help="quick numbers and who to call")
    st.add_argument("slug")
    st.set_defaults(func=cmd_status)

    se = sub.add_parser("set", help="change client settings, e.g. pilot=false")
    se.add_argument("slug")
    se.add_argument("pairs", nargs="+")
    se.set_defaults(func=cmd_set)

    sv = sub.add_parser("serve", parents=[ai], help="webhook server for replies")
    sv.add_argument("--host", default="0.0.0.0")
    sv.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    sv.add_argument("--auto-reply", action="store_true", help="text the AI draft back automatically")
    sv.set_defaults(func=cmd_serve)

    o = sub.add_parser("outreach", parents=[ai], help="write pitches for contractor leads")
    o.add_argument("--leads", required=True)
    o.add_argument("--name", required=True, help="your name")
    o.add_argument("--agency", required=True, help="your agency name")
    o.add_argument("--out", default="output/outreach.csv")
    o.set_defaults(func=cmd_outreach)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
