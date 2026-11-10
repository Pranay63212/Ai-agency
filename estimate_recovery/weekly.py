"""Weekly results report and bill for one client, built from the event log."""

import html
from datetime import date, datetime, timedelta, timezone

from .campaign import Campaign


def _money(x: float) -> str:
    return f"${x:,.0f}"


def _since(events: list[dict], days: int | None) -> list[dict]:
    if days is None:
        return events
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [e for e in events if datetime.fromisoformat(e["time"]) >= cutoff]


def stats(campaign: Campaign, days: int | None = None) -> dict:
    events = _since(campaign.events(), days)
    by_type = lambda t: [e for e in events if e["type"] == t]  # noqa: E731
    booked = by_type("booked")
    revenue = 0.0
    for e in booked:
        try:
            revenue += float(e["amount"] or 0)
        except ValueError:
            pass
    s = campaign.settings()
    return {
        "contacts": len(campaign.contacts()),
        "messages_sent": len(by_type("sent")),
        "customers_reached": len({e["contact_id"] for e in by_type("sent")}),
        "replies": len({e["contact_id"] for e in by_type("reply")}),
        "hot_leads": len({e["contact_id"] for e in by_type("alert")}),
        "bookings": len(booked),
        "revenue": revenue,
        "opt_outs": len({e["contact_id"] for e in by_type("opt_out")}),
        "amount_due": 0 if s.get("pilot") else len(booked) * float(s["price_per_booking"]),
        "value_at_price": len(booked) * float(s["price_per_booking"]),
    }


def open_hot_leads(campaign: Campaign) -> list[dict]:
    """Hot leads not yet booked or closed: the owner should call these."""
    status = campaign.status()
    contacts = {c["contact_id"]: c for c in campaign.contacts()}
    out, seen = [], set()
    for e in reversed(campaign.events()):
        cid = e["contact_id"]
        if e["type"] != "alert" or cid in seen:
            continue
        seen.add(cid)
        st = status.get(cid, {})
        if not (st.get("booked") or st.get("closed") or st.get("opted_out")):
            c = contacts.get(cid, {})
            out.append({"name": c.get("customer_name") or cid, "phone": c.get("phone") or cid,
                        "job": c.get("job_type", ""), "summary": e["detail"].split(": ", 1)[-1],
                        "time": e["time"][:10]})
    return out


def bookings(campaign: Campaign) -> list[dict]:
    contacts = {c["contact_id"]: c for c in campaign.contacts()}
    rows = []
    for e in campaign.events():
        if e["type"] == "booked":
            c = contacts.get(e["contact_id"], {})
            rows.append({"date": e["time"][:10], "name": c.get("customer_name") or e["contact_id"],
                         "job": c.get("job_type", ""), "amount": float(e["amount"] or 0),
                         "detail": e["detail"]})
    return rows


def build_weekly(campaign: Campaign) -> str:
    s = campaign.settings()
    week, total = stats(campaign, 7), stats(campaign)
    hot, booked = open_hot_leads(campaign), bookings(campaign)
    price = float(s["price_per_booking"])

    def tile(v, label):
        return f'<div class="stat"><b>{v}</b><span>{label}</span></div>'

    hot_rows = "".join(
        f"<tr><td>{html.escape(h['name'])}</td><td>{html.escape(h['phone'])}</td>"
        f"<td>{html.escape(h['job'])}</td><td class=msg>{html.escape(h['summary'])}</td></tr>"
        for h in hot) or '<tr><td colspan="4" class=msg>None right now.</td></tr>'
    book_rows = "".join(
        f"<tr><td>{b['date']}</td><td>{html.escape(b['name'])}</td><td>{html.escape(b['job'])}</td>"
        f"<td class=num>{_money(b['amount']) if b['amount'] else '-'}</td></tr>"
        for b in booked) or '<tr><td colspan="4" class=msg>No bookings yet.</td></tr>'
    if s.get("pilot"):
        bill = (f"Free pilot: nothing owed. At {_money(price)} per booking, these results would "
                f"be worth {_money(total['value_at_price'])}.")
    else:
        bill = (f"{total['bookings']} booked jobs x {_money(price)} = "
                f"<b>{_money(total['amount_due'])}</b> due.")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Weekly Recovery Report</title>
<style>
:root {{ --bg:#f7f7f5; --card:#fff; --ink:#1c1c1a; --muted:#6b6b66; --accent:#1f6f50; --line:#e4e4df; --hot:#b4471d; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#151514; --card:#1e1e1c; --ink:#eeeeea; --muted:#a0a09a; --accent:#5fc49a; --line:#33332f; --hot:#f08a5d; }} }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 system-ui, sans-serif; }}
main {{ max-width:1000px; margin:0 auto; padding:24px 16px 48px; }}
h1 {{ margin:0 0 4px; font-size:24px; }} .sub {{ color:var(--muted); margin:0 0 20px; }}
h2 {{ font-size:16px; margin:0 0 8px; }} h3 {{ font-size:13px; text-transform:uppercase; color:var(--muted); margin:20px 0 8px; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }}
.stat {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px; }}
.stat b {{ display:block; font-size:24px; color:var(--accent); }} .stat span {{ color:var(--muted); font-size:13px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; margin-top:16px; overflow-x:auto; }}
.card.hot h2 {{ color:var(--hot); }}
table {{ border-collapse:collapse; width:100%; min-width:560px; }} th,td {{ text-align:left; padding:8px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ font-size:12px; text-transform:uppercase; color:var(--muted); }} .num {{ text-align:right; }} .msg {{ color:var(--muted); font-size:13px; }}
</style></head><body><main>
<h1>{html.escape(s['business'])}: Weekly Recovery Report</h1>
<p class="sub">Week ending {date.today():%B %d, %Y}</p>
<h3>This week</h3>
<div class="stats">{tile(week['customers_reached'], 'customers contacted')}{tile(week['replies'], 'replied')}{tile(week['hot_leads'], 'hot leads')}{tile(week['bookings'], 'jobs booked')}{tile(_money(week['revenue']), 'booked revenue')}</div>
<h3>Since the start</h3>
<div class="stats">{tile(total['customers_reached'], f"of {total['contacts']} contacted")}{tile(total['replies'], 'replied')}{tile(total['bookings'], 'jobs booked')}{tile(_money(total['revenue']), 'booked revenue')}{tile(total['opt_outs'], 'opted out')}</div>
<div class="card hot"><h2>Call these today ({len(hot)})</h2>
<table><thead><tr><th>Customer</th><th>Phone</th><th>Job</th><th>What they said</th></tr></thead><tbody>{hot_rows}</tbody></table></div>
<div class="card"><h2>Booked jobs</h2>
<table><thead><tr><th>Date</th><th>Customer</th><th>Job</th><th class=num>Job value</th></tr></thead><tbody>{book_rows}</tbody></table></div>
<div class="card"><h2>Billing</h2><p>{bill}</p></div>
</main></body></html>"""


def invoice_text(campaign: Campaign) -> str:
    s, rows = campaign.settings(), bookings(campaign)
    price = float(s["price_per_booking"])
    lines = [f"Invoice: {s['business']}", f"Date: {date.today():%Y-%m-%d}", ""]
    for b in rows:
        lines.append(f"{b['date']}  {b['name']:<22} {b['job']:<34} {_money(price):>8}")
    total = 0 if s.get("pilot") else price * len(rows)
    lines += ["", f"Booked jobs: {len(rows)} x {_money(price)}"]
    if s.get("pilot"):
        lines.append("Pilot period: no charge")
    lines.append(f"TOTAL DUE: {_money(total)}")
    return "\n".join(lines) + "\n"
