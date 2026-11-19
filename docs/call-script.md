# Call Script: Gatekeepers and Owners

For fencing and window cleaning. Keep calls short: under 2 minutes unless they keep you talking.

## Before you call

- Know the owner's first name (website "About" page, Google reviews where owners reply, Facebook, LinkedIn). Asking for someone by name gets you through far more often.
- Best times: **7:30–8:30am** (owners are in the office before crews leave) or **4–5:30pm** (after jobs). Avoid midday.
- Small shops: the owner often answers. Be ready.

## Getting past the gatekeeper

Be friendly, brief and honest. Never pretend to be a customer or claim you've talked before. It backfires and burns the lead.

**Opener (with a name)**
> "Hi, this is [Your name]. Is [Owner first name] around?"

Say it like you expect to be put through. Short and calm.

**"What's this about?"**
> "I help fence companies get jobs back from leads that went quiet: missed calls, old quotes, that kind of thing. Quick question for [Owner]. Is now a bad time to grab them?"

**"They're busy / out on a job"**
> "No problem. When's the best time to catch them? And is there an email that gets to them directly?"

Write down both. Call back at that time, and say "[Name] said this was a good time."

**"Send us an email"**
> "Will do. What's the best address so it reaches [Owner] and not a general inbox?"

Then send it within the hour (template at the bottom).

**"We're not interested"**
> "Totally fair. Can I ask one thing? Who handles your leads and follow-ups, so I can send them a short note?"

If still no: "Thanks for your time, have a good one." Move on.

**Make the gatekeeper your ally.** They often *are* the person who handles leads.
> "Are you the one who handles the calls and quotes? … How do you keep up with all the ones that go quiet?"

## Version 2 opener: no "do you have a minute", not a typical cold call

Don't ask for their time. Open with a question that's easy to answer and gives them an easy out. People relax when you hand them the "no".

**Fencing**
> "Hey [Name], [Your name] here. I'm looking for a fence company that's got a pile of old quotes nobody ever followed up on. Is that you, or are you guys on top of that?"

**Window cleaning**
> "Hey [Name], [Your name] here. I'm looking for a window cleaning company with a bunch of past customers who never booked again this year. Is that you, or do you have that covered?"

Then **stop talking**. Whatever they say, you have a next line:

| They say | You say |
|---|---|
| "Ha, yeah, probably us." | "Most are. Roughly how many would you guess? A dozen, a hundred?" |
| "We're on top of it." | "Respect, that's rare. Do you go back to the ones from 3–6 months ago too, or just the recent ones?" |
| "Who is this? What are you selling?" | "Fair question. I bring back leads that went quiet. Not new leads, your old ones. I'll show you on 10 of them for free before you decide anything." |

**The small ask: 10 leads, not 100**
> "Here's what I'd do. Send me 10 old quotes, just names, numbers and what the job was. I'll reach out to them this week as your company and tell you exactly how many answer. Takes you two minutes. If it works, we talk. If not, you've lost nothing."

10 is an easy yes. Once they see replies, scale up to 100 and then the paid plan.

**Why it's different from every other cold call:**
- You're not selling ads or "more leads". You're bringing back customers they already paid to get.
- You hand them the "no" up front, so they don't feel pushed.
- The first step is tiny, free and over in a week.

**Voicemail (version 2)**
> "Hey [Name], [Your name]. Quick one: I'm looking for a [fence / window cleaning] company with old [quotes / customers] nobody's followed up on. If that's you, I'll bring back 10 of them for free this week. [Number]."

## Talking to the owner (original version)

### 1. Permission opener (10 seconds)
> "Hi [Name], this is [Your name]. I know I'm catching you out of the blue. Can I take 30 seconds to tell you why I called, and then you can tell me if it's worth talking?"

Most say "sure."

### 2. The problem (ask, don't tell)
**Fencing:**
> "Quick question: how many people this year called, filled out a form, or got a quote from you and then just went quiet?"

**Window cleaning:**
> "Quick question: how many past customers do you have who haven't booked again this year?"

Then **stop talking**. Let them answer. Follow with:
> "Does anyone go back and follow up on those?"

### 3. The offer (only after they admit the problem)
> "That's what I do. I follow up with those dead leads in your company's name (texts or emails that sound like you) and send you the ones ready to book. I'll do the first 100 free. If jobs book and you want to keep going, it's only paid per booked job. If nothing books, you owe nothing."

### 4. Ask for the next step
> "Want to try it? All I'd need is a list: names, phone or email, and what they asked about. A spreadsheet or a CRM export is fine."

Or, if they're unsure:
> "Can I send you 3 sample messages for your company so you can see exactly what customers would get?"

## Common answers

| They say | You say |
|---|---|
| "We already follow up." | "That's great, most don't. Do you go back to ones from 2–6 months ago? That's where I usually find jobs." |
| "Those people hired someone else." | "Some did. But plenty just got busy or put it off. The free 100 shows you exactly how many come back. If none do, you've lost nothing." |
| "We're too busy for more work." | "Makes sense now. How about in [spring / your slow season]? I can line these up so your slow months fill first." |
| "How much?" | "First 100 free. After that it's [$150–$300] per booked job, only when a job actually books." |
| "Is this AI? Will it sound like a robot?" | "It's written to sound like you, short and friendly, and you approve every message before anything goes out." |
| "What do you need from me?" | "Just the list. About 10 minutes of your time. I handle everything else and send you the interested ones." |
| "Send me something." | "Sure. What's your direct email? I'll send 3 sample messages for [Company] today." |
| "Not interested." | "No problem. Mind if I check back before [spring]?" (Write down the date.) |

## Voicemail (under 20 seconds)

> "Hi [Name], it's [Your name] at [your number]. I help [fence / window cleaning] companies get jobs back from leads that went quiet, and I'll do the first 100 free. I'll send you a quick email too. Again, [number]."

## Email to send after the call

> **Subject:** [Company]: leads that went quiet
>
> Hi [Name],
>
> Thanks for [taking my call / the quick chat with your team] today. As promised: I follow up with your dead leads (missed calls, old quotes, past customers) in your company's name and send you the ones ready to book.
>
> The first 100 are free. After that, you only pay for jobs that book.
>
> Here are 3 examples of what your customers would get:
> 1. [sample]
> 2. [sample]
> 3. [sample]
>
> Want to try it? Just reply with a list, or tell me where your leads live and I'll work with it.
>
> [Your name]
> [Your phone]

Make the samples with: `python agency.py samples --trade fencing --business "Their Company" --sender "Owner Name"`

## After every call

Log it in `leads/tracker.csv`: who you spoke to, what they said, and the next step with a date.
