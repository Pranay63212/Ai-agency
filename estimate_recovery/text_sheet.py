"""A phone-friendly page of today's texts. Each button opens Messages with the number and text
filled in, so a person sends them one by one from the business's own phone."""

import html
import os
import urllib.parse
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .campaign import Campaign
from .sender import due_messages


def sms_link(phone: str, body: str) -> str:
    # "sms:<number>?&body=" opens prefilled on both iPhone and Android.
    return f"sms:{phone}?&body={urllib.parse.quote(body)}"


def build_text_sheet(c: Campaign, today: date | None = None) -> tuple[str, int]:
    s = c.settings()
    today = today or datetime.now(ZoneInfo(s["timezone"])).date()
    texts = [o for o in due_messages(c, today) if o.channel == "text"]
    cards = "\n".join(
        f'''<div class="card"><div class="who"><b>{html.escape(o.contact["customer_name"])}</b>
<span>{html.escape(o.contact.get("job_type", ""))} · {html.escape(o.step.replace("_", " "))}</span></div>
<p>{html.escape(o.body)}</p>
<a class="btn" href="{html.escape(sms_link(o.to, o.body))}" onclick="this.closest('.card').classList.add('done')">Text {html.escape(o.contact["customer_name"].split()[0])}</a></div>'''
        for o in texts)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Today's Texts</title>
<style>
:root {{ --bg:#f7f7f5; --card:#fff; --ink:#1c1c1a; --muted:#6b6b66; --accent:#1f6f50; --line:#e4e4df; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#151514; --card:#1e1e1c; --ink:#eeeeea; --muted:#a0a09a; --accent:#5fc49a; --line:#33332f; }} }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.45 system-ui, sans-serif; }}
main {{ max-width:560px; margin:0 auto; padding:20px 16px 40px; }}
h1 {{ font-size:22px; margin:0 0 4px; }} .sub {{ color:var(--muted); margin:0 0 16px; font-size:14px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; margin-bottom:12px; }}
.card.done {{ opacity:.45; }} .who span {{ display:block; color:var(--muted); font-size:13px; }}
.card p {{ margin:8px 0 12px; }}
.btn {{ display:block; text-align:center; background:var(--accent); color:#fff; text-decoration:none; font-weight:600;
       padding:12px; border-radius:10px; }}
</style></head><body><main>
<h1>{html.escape(s['business'])}: texts for {today:%b %d}</h1>
<p class="sub">{len(texts)} to send. Tap a button, check the message, press send in Messages, then come back for the next one.</p>
{cards or '<p class="sub">Nothing due today.</p>'}
</main></body></html>"""
    path = os.path.join(c.path, f"texts-{today.isoformat()}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path, len(texts)
