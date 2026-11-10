# Setup Guide

What you need before sending real messages. Until then, everything works in preview mode.

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. AI key (for writing messages and reading replies)

- **NVIDIA (what you use now):** create a key at build.nvidia.com, then `export NVIDIA_API_KEY=nvapi-...`.
  The default model is `nvidia/nemotron-3-ultra-550b-a55b`. Change it with `NVIDIA_MODEL=...`.
- **Claude (optional):** `export ANTHROPIC_API_KEY=sk-ant-...` and add `--provider claude`.
- **No key:** add `--provider mock` to use templates.

Never paste keys into chat, code or GitHub. Put them in a `.env` file (already git-ignored) or your hosting provider's secret settings.

## 3. Texting (Twilio)

1. Create a Twilio account and buy a local number in your client's area code.
2. **Register for A2P 10DLC** in the Twilio console (brand + campaign, use case "customer care / account notifications"). US carriers block unregistered business texting. Approval can take several days, so start early.
3. Set these environment variables:
   ```bash
   export TWILIO_ACCOUNT_SID=AC...
   export TWILIO_AUTH_TOKEN=...
   export TWILIO_FROM=+12145550100
   ```

## 4. Email (any SMTP provider)

Use a sending service (Google Workspace, Postmark, Mailgun, SendGrid). Send from a domain you own with SPF and DKIM set up, so mail doesn't land in spam.
```bash
export SMTP_HOST=smtp.example.com SMTP_PORT=587
export SMTP_USER=... SMTP_PASSWORD=... SMTP_FROM="Mike at Cool Air HVAC <mike@coolair.example>"
```
Hot-lead alerts to the owner also use these settings.

## 5. Receiving text replies (webhook)

Run the reply server somewhere with a public web address (Render, Railway, Fly.io, or a small VPS):
```bash
export PUBLIC_URL=https://your-app.example.com   # enables Twilio signature checks
python agency.py serve --port 8080
```
In Twilio, set your number's **"A message comes in"** webhook to `https://your-app.example.com/sms/<client-slug>` (HTTP POST).

- Replies are logged, opt-outs are recorded, and hot leads alert the owner by email.
- Add `--auto-reply` to text the AI's draft back automatically. Start without it and read the drafts with `status` first.
- Email replies: forward them (for example with Zapier) as JSON `{"from": ..., "body": ...}` to `/email/<client-slug>?key=WEBHOOK_KEY`, with `WEBHOOK_KEY` set.

## 6. Run sending every morning

On your server, a cron job such as the one below (cron uses the server's clock, so pick an hour that falls inside 9am–8pm for the client; outside those hours `--live` refuses to send):
```
0 10 * * 1-6  cd /path/to/Ai-agency && python agency.py send cool-air-hvac --live >> send.log 2>&1
```

## 7. Keep client data safe

`clients/` holds customers' names, phones and emails. It's git-ignored: never commit it. Back it up privately, and delete a client's folder when they ask or when the engagement ends.
