"""Build a one-page HTML report a contractor can read in 30 seconds."""

import html
from datetime import date


def _money(x: float) -> str:
    return f"${x:,.0f}"


def build_report(contacts: list[dict], removed: list[tuple[dict, str]], business: dict,
                 close_rate: float, provider: str) -> str:
    pipeline = sum(c["quote_amount"] for c in contacts)
    expected = pipeline * close_rate
    expected_jobs = max(1, round(len(contacts) * close_rate)) if contacts else 0

    rows = "\n".join(
        f"<tr><td>{html.escape(c['customer_name'])}</td><td>{html.escape(c['job_type'])}</td>"
        f"<td class=num>{_money(c['quote_amount'])}</td><td>{html.escape(c['channels'])}</td>"
        f"<td class=msg>{html.escape(c['day_1_text'])}</td></tr>"
        for c in sorted(contacts, key=lambda c: -c["quote_amount"])
    )
    removed_rows = "\n".join(
        f"<li>{html.escape(r.get('customer_name') or '(no name)')}: {html.escape(why)}</li>"
        for r, why in removed
    ) or "<li>None</li>"
    mode = {"mock": "Demo mode: template messages (no AI).", "claude": "Messages written by Claude.",
            "nvidia": "Messages written by AI."}.get(provider, "")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Estimate Recovery Report</title>
<style>
:root {{ --bg:#f7f7f5; --card:#fff; --ink:#1c1c1a; --muted:#6b6b66; --accent:#1f6f50; --line:#e4e4df; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#151514; --card:#1e1e1c; --ink:#eeeeea; --muted:#a0a09a; --accent:#5fc49a; --line:#33332f; }} }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 system-ui, sans-serif; }}
main {{ max-width:1000px; margin:0 auto; padding:24px 16px 48px; }}
h1 {{ margin:0 0 4px; font-size:24px; }} .sub {{ color:var(--muted); margin:0 0 24px; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin-bottom:24px; }}
.stat {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; }}
.stat b {{ display:block; font-size:26px; color:var(--accent); }} .stat span {{ color:var(--muted); font-size:13px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; margin-bottom:16px; overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; min-width:640px; }} th,td {{ text-align:left; padding:8px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ font-size:12px; text-transform:uppercase; color:var(--muted); }} .num {{ text-align:right; white-space:nowrap; }} .msg {{ font-size:13px; color:var(--muted); }}
h2 {{ font-size:16px; margin:0 0 8px; }} ul {{ margin:0; padding-left:20px; color:var(--muted); }}
</style></head><body><main>
<h1>{html.escape(business['name'])}: Unsold Estimate Recovery</h1>
<p class="sub">Prepared {date.today():%B %d, %Y} · {mode}</p>
<div class="stats">
  <div class="stat"><b>{len(contacts)}</b><span>customers ready for follow-up</span></div>
  <div class="stat"><b>{_money(pipeline)}</b><span>in unsold quotes</span></div>
  <div class="stat"><b>~{expected_jobs}</b><span>jobs if {close_rate:.0%} rebook</span></div>
  <div class="stat"><b>{_money(expected)}</b><span>estimated recovered revenue</span></div>
</div>
<div class="card"><h2>Follow-up plan</h2>
<table><thead><tr><th>Customer</th><th>Job</th><th class=num>Quote</th><th>Channels</th><th>First message</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<div class="card"><h2>Removed before sending ({len(removed)})</h2><ul>{removed_rows}</ul></div>
<p class="sub">Estimate assumes {close_rate:.0%} of contacted customers book. Texts go only to customers who gave their number to the business, and every text includes an opt-out.</p>
</main></body></html>"""
