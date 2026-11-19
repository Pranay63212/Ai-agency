# How It Works (know this cold)

## The service in one sentence

"Your business has people who called, got a quote, or used you before and never booked again. I contact them for you in your company's name and send you the ones ready to book."

## "Tell me more": what to say (30 seconds)

> "Sure. It's 4 simple steps:
> 1. You send me a list of old leads: people who asked for a quote and went quiet, or past customers. A spreadsheet or an export from your system is fine.
> 2. I write a short, friendly message for each person, mentioning their actual job, and you approve them before anything goes out.
> 3. Over 2 weeks, each person gets 3 messages by email (or text, if you have texting set up), sent as your company.
> 4. When someone replies interested, I send them straight to you the same day, with their name, number and what they want. You call them and close the job.
>
> The first 100 are free. If jobs book and you want to keep going, it's [$150–$300] per booked job. If nothing books, you owe nothing."

## The full plan after they say yes

| Day | What you do | What the owner does | Time for the owner |
|---|---|---|---|
| **Day 0** | Send the short agreement (`docs/pilot-agreement-short.md`). Ask for the list. | Replies "I agree" and sends the list. | 10 min |
| **Day 1** | Run `python agency.py new "Their Co" --input list.csv --sender [Owner] --phone "[their #]" --email-only --limit 100 --owner-email [their email]`. Send them `plan.html` to approve. | Reads the messages and says "looks good" (or asks for changes). | 10 min |
| **Day 2** | Start the daily run: `python agency.py daily their-co --live`. It sends message 1 to everyone. | Nothing. | 0 |
| **Day 2–14** | Every morning: run `daily` (checks replies, sends what's due), then `status`. Text or email the owner each hot lead the same day. | Calls back interested people. Tells you when one books. | A few calls |
| **Day 5** | Message 2 goes out automatically. | Nothing. | 0 |
| **Day 11** | Message 3 (last one) goes out automatically. | Nothing. | 0 |
| **Day 14–16** | Run `python agency.py report their-co`. Send the report: who replied, who booked, how much money it brought back. | Reads it. | 5 min |
| **Day 16** | Offer to continue: their full list at $[200] per booked job. Ask for a testimonial and 2 referrals. | Decides. | 5 min |

The whole pilot costs the owner about **30 minutes** plus the callbacks they'd want anyway.

## Texting without a texting account

Texts should come from the **business's own number**, which customers recognize, not your phone. Set the campaign up with `--manual-texts`: emails still go out automatically, and texts go on a daily tap-to-send page:

```
python agency.py text-sheet their-co                  # makes clients/their-co/texts-<date>.html
python agency.py send their-co --mark --only text     # after they're sent, log them
```

**Automatic:** if the campaign has `--owner-email`, the morning `daily --live` run emails the page to the owner by itself and logs those texts, so they don't repeat tomorrow. Otherwise, send the page to whoever holds the business phone yourself (email or AirDrop). Each "Text Megan" button opens Messages with the number and message filled in, and they press send. 10–20 texts take about 5 minutes. Never blast texts automatically from a personal phone: it reads as spam, replies go to the wrong person, and carriers flag it.

## What customers actually receive (example, fencing)

1. **Day 1:** "Hi Megan, Dave from Oak Ridge Fence here. Checking in on the 150-ft cedar privacy fence quote from May. Any questions, or ready to schedule?"
2. **Day 4 (email):** a short note offering to answer questions or go over options.
3. **Day 10:** "Hi Megan, last check-in from Oak Ridge Fence about your cedar fence. Want help with it, or should I close it out?"

Anyone who replies stops getting messages. Anyone who says "stop" or "unsubscribe" is removed permanently.

## What you need to deliver

- Your laptop with the project set up (`docs/free-setup.md`, about 20 minutes, once)
- A Gmail with an app password (yours, or one the owner creates for this)
- Your NVIDIA key (you already have it)

That's it. No texting account, no servers, no paid tools.

## Questions owners will ask

| Question | Answer |
|---|---|
| "Where do you get the messages?" | "I write them with AI for each customer, based on their actual job, and you approve every one before anything is sent." |
| "Will it come from my company?" | "Yes, it's sent in your company's name. Ideally from an email you create for this, so replies come to you too." |
| "What do you need from me?" | "A list (names, phone or email, what the job was, roughly when), your OK on the messages, and calling back the interested ones." |
| "How do you know who booked?" | "You tell me, and I keep a shared log. It's on trust, which is why the first 100 are free." |
| "What if customers get annoyed?" | "It's 3 short, polite messages over 2 weeks, and anyone can opt out instantly. Most people either reply or ignore them." |
| "Is my customer list safe?" | "I only use it for this, never share it, and delete it when you ask." |
| "What results should I expect?" | "Honestly, I'm early, which is why it's free. The test shows you real numbers from your own list." |
| "How is this different from a CRM?" | "A CRM stores leads. I actually do the follow-up for you." |
| "Can you do texts?" | "Yes, through your system if it can text. Otherwise I start with email, and texting can be added later." |

## Be honest about being new

You don't need a track record to run a free test. Say it plainly:
> "I'm just starting, so I'm doing a few free pilots to prove it works. You risk nothing, and you see the results on your own customers."

Owners respect that more than made-up numbers.
