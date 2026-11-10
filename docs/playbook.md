# Operating Playbook

How to run the agency day to day with these tools. Commands use `python agency.py ...`.

## 1. Finding clients (weeks 1–2)

1. **Build a lead list.** Search Google Maps for "HVAC [city]". For each company with **20+ reviews**, note: company, owner name (website "About" page or LinkedIn), city, website, review count, rating, email, and anything distinctive. Save it as a CSV with the columns in `sample_data/hvac_leads.csv`.
2. **Write the pitches:**
   ```bash
   python agency.py outreach --leads my_leads.csv --name "Your Name" --agency "Your Agency"
   ```
   You get `output/outreach.csv` with a subject, first message, 60-second video script and day 3, 7 and 14 follow-ups for every lead.
3. **Send 10–15 a day by hand** (email, Facebook or LinkedIn DM). Read each one first and fill in any `[placeholder]`. For your best leads, record the video script with a free screen recorder (Loom or similar) while showing their website.
4. **Follow-up rhythm:** day 1 first message, day 3 video, day 7 tip, day 14 "close your file?" note. Stop as soon as they reply.
5. **Track it** in a simple sheet: lead, date contacted, stage, next step.

**Weekly targets:** 60–75 messages sent, 5–10 replies, 2–3 conversations, a new pilot every 1–2 weeks. If replies stay under 3 a week, change the message, not the niche.

## 2. Signing a pilot

1. Send `docs/pilot-agreement.md` (after your lawyer reviews it) and get it signed.
2. Ask for their unsold estimates as a CSV with: `customer_name, phone, email, job_type, quote_amount, quote_date, status, notes`. Most CRMs (Jobber, Housecall Pro, ServiceTitan) can export this. A spreadsheet works too.

## 3. Running a pilot

```bash
# 1. Set up: cleans the list and writes every customer's messages (first 100 for a pilot)
python agency.py new "Cool Air HVAC" --input their_export.csv --sender Mike \
    --phone "(214) 555-0100" --owner-email mike@coolair.example --limit 100

# 2. Review: open clients/cool-air-hvac/contacts.csv and plan.html. Send plan.html to the
#    owner to approve the messages. Fix anything odd directly in contacts.csv.

# 3. Every morning, preview then send what's due
python agency.py send cool-air-hvac
python agency.py send cool-air-hvac --live

# 4. When replies come in by email or phone, log them (texts are logged automatically
#    once the webhook is running)
python agency.py reply cool-air-hvac --from "maria@example.com" --body "Can you call me?"

# 5. Check who to call and pass hot leads to the owner fast
python agency.py status cool-air-hvac

# 6. Record bookings the owner tells you about
python agency.py book cool-air-hvac "Maria Lopez" --amount 8450

# 7. Every Friday: weekly report + invoice
python agency.py report cool-air-hvac
```

The sequence stops automatically for anyone who replies, opts out, books or is closed. Texts go out only between 9am and 8pm Monday to Saturday in the client's timezone, and never on back-to-back days.

## 4. Converting to paid

At the end of the pilot, send the weekly report. Offer pay-per-result on their full list by setting up a new, paid campaign. Pilot bookings stay free.
```bash
python agency.py new "Cool Air HVAC" --slug cool-air-hvac-full --input full_list.csv --paid \
    --price 200 --sender Mike --phone "(214) 555-0100" --owner-email mike@coolair.example
```
Ask for a testimonial and two referrals. Turn the best result into a case study for your outreach.

## 5. Daily routine (about 1–2 hours)

| When | What |
|---|---|
| Morning | `send --live` for each client, `status` for each client, call or text the owner about hot leads |
| Midday | 10–15 personalized outreach messages to new leads |
| Afternoon | Reply to prospects, post one helpful tip in a contractor community |
| Friday | `report` for each client, send reports and invoices |
