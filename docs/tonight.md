# Tonight's Outreach Kit

Copy, fill in the [brackets], send. Everything here is a message you send by hand.

---

## 1. The owner with 300 cold quotes (send first)

> Hi [Name], thanks again for telling me about the quotes that go cold. I'm testing something: I follow up with those old quotes for you and send you the people who are still interested, so you don't lift a finger.
>
> Want me to run it free on 100 of them? If nothing books, you owe nothing.
>
> All I'd need is a list (name, phone or email, what the job was, the amount and the date). A spreadsheet or an export from your system is fine.

**If they say yes:** reply with the short agreement (section 6) and ask for the list.
**If no answer in 2 days:**
> Hi [Name], just bumping this. Happy to show you exactly what the messages would look like first.

Then send them 3 samples from `samples/[trade]-sample-messages.csv`.

---

## 2. Facebook group post (ask, don't pitch)

Post in 2–3 groups for the trade (search "[trade] business owners", "[trade] contractors"):

> Question for owners: of the quotes you send, roughly how many never get a yes or no? And does anyone on your team follow up on the old ones, or do they just die?
>
> Curious how others handle it. I'm looking at this for a project.

Don't link anything or pitch in the post. When someone comments, reply to them in the comments, then DM:

> Hey [Name], saw your comment on the quotes post. I'm actually testing a free follow-up service for old quotes. Would you want me to try it on 100 of yours? No cost, and if nothing books you owe nothing.

---

## 3. Direct message to companies (Facebook page, website form, or email)

> Hi [Name or "there"], quick question for the owner: of the quotes you send, how many never get an answer? And does anyone follow up on them?
>
> I'm asking because I'm running a free trial where I follow up on old quotes for contractors and pass back anyone still interested. Happy to share what I'm seeing.
>
> [Your name]

**Follow-up (3 days later, if no reply):**
> Hi [Name], bumping this in case it got buried. Even a rough number helps: how many quotes a month go quiet?

---

## 4. When they answer the question

| They say | You say |
|---|---|
| "A lot / I don't know / we don't follow up" | "That's exactly what I'm testing. Want me to run it free on 100 of your old quotes? You'd just send me a list." |
| "We follow up already" | "Nice, most don't. Do you go back to quotes older than a month or two? That's usually where it helps." |
| "They're gone, they hired someone else" | "Some are, for sure. But on bigger jobs people often just stall. The free test shows how many. If nothing books, you've lost nothing." |
| "How much does it cost?" | "The test is free. After that it's only paid per job that books, so if nothing books you pay nothing." |
| "What would you send my customers?" | Send 3 samples from `samples/[trade]-sample-messages.csv`. |

---

## 5. Samples to show owners

Ready-made for **HVAC, roofing, remodeling and plumbing** in `samples/`:
- `[trade]-sample-quotes.csv`: 20 fake quotes
- `[trade]-sample-messages.csv`: a short, specific follow-up for each

Make a new set with your client's name in it:
```
python agency.py samples --trade roofing --business "Their Company" --sender "Their Name"
```

---

## 6. Short pilot agreement

See `docs/pilot-agreement-short.md`. Paste it into an email or a Google Doc, fill in the brackets, and have the owner reply "I agree" or sign it.

---

## 7. Log everything

Use `leads/tracker.csv` (open in Google Sheets: File → Import → Upload). One row per company: what they said and the next step.
