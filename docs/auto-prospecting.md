# Automatic Lead Emails

Sends your outreach emails and follow-ups to contractor leads by itself, about 20 a day. You only answer the replies.

## The rules it follows (US CAN-SPAM law)

- Honest sender name and subject line (no fake "Re:").
- **Your mailing address in every email.** It's required. A PO box or virtual mailbox (about $10–20/month) is fine if you don't want to use your home address.
- An easy opt-out ("reply unsubscribe"), honored forever.
- Business days and hours only, and a daily cap so you don't look like spam.

It only emails. Automated texts or calls to their phones, and bots filling in website forms, are against the law or the sites' rules, so do those by hand.

## Steps

1. **Get emails for your leads.** Add a `website` column (from their Google Maps listing) to your lead CSV, or type emails straight into the `email` column.
2. **Write the messages** (if you haven't already):
   ```
   python agency.py outreach --leads leads/chicago-suburbs.csv --name "Jade" --agency "Your Agency" --out leads/chicago-suburbs-outreach.csv
   ```
   Open the `.md` version, read them, and fix anything. Any `[placeholder]` left in a message blocks that email from sending.
3. **Make the prospect list:**
   ```
   python agency.py prospect new "Chicago suburbs" --outreach leads/chicago-suburbs-outreach.csv \
       --agency "Your Agency" --sender "Jade" --phone "(312) 555-0100" --address "PO Box 123, Chicago, IL 60601"
   python agency.py prospect find-emails chicago-suburbs     # looks on each website for a contact email
   ```
4. **Preview:**
   ```
   python agency.py prospect send chicago-suburbs --show
   ```
5. **Go live, once a day** (schedule it like `docs/free-setup.md` shows, at around 9am on weekdays):
   ```
   python agency.py prospect daily chicago-suburbs --live
   ```
   It reads replies first, so anyone who answered is never emailed again, then sends what's due.

## Every day

```
python agency.py prospect status chicago-suburbs
```
shows who replied. **Answer them yourself, the same day.** That's where clients come from.

## Tips

- Use a separate Gmail for prospecting, not your personal one, and keep it to **20–30 a day**. Sending lots of cold email from a brand new account gets it flagged.
- Read the first few emails yourself before going live.
- Add new leads anytime: rerun `outreach`, then `prospect new` with a new name (for example "Chicago week 2").
