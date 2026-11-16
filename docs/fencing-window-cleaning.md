# New Focus: Fencing and Window Cleaning

## What you sell each one

| Trade | Their problem | Your offer |
|---|---|---|
| **Fencing** | Homeowners get 2–3 quotes and go quiet. Big tickets ($3k–$15k). | "I follow up on your old fence quotes and send you the ones still interested. Free on 100 quotes; after that you only pay per booked job." |
| **Window cleaning** | Customers need cleaning every spring or fall, but nobody reminds them. | "I message your past customers when they're due and fill your schedule. Free on your first 100 past customers; after that you pay per booked job." |

The same tool runs both: `python agency.py new ...` with their list. For window cleaning, the list is **past customers**, not unsold quotes.

## Finding warm leads (owners who already want more work)

Put each one in `leads/warm-leads-template.csv` with **where you found them** and **why they're warm**.

| Where | How | Why they're warm |
|---|---|---|
| **Facebook Ad Library** | facebook.com/ads/library → All ads → your state → search "fence" or "window cleaning" | Already paying for leads |
| **Google "Sponsored" results** | Search "fence company [city]" and "window cleaning [city]" | Paying per click |
| **Angi / Thumbtack / HomeAdvisor** | Browse pros in your area | Paying for shared leads, and most hate it |
| **Owner groups** | Facebook: "Window Cleaning Business Owners", "Fence Contractors", "Fence Company Owners". Reddit: r/windowcleaning, r/sweatystartup. Search posts for "leads", "slow", "marketing" | Asking for help out loud |
| **Indeed** | "fence installer" / "window cleaner" near you | Hiring means growing |
| **Google Maps** | Businesses with under 20 reviews but a real site and photos | New and hungry |
| **Reviews** | Look for "never called back" or "slow to quote" | They lose leads you could save |
| **Supply yards and associations** | Fence supply counters, American Fence Association, IWCA | They know who's busy and growing |

**Timing:** contact them in winter and early spring, when they're planning their season.

## Messages

### Fencing: direct message
> Hi [Name], quick question: of the fence quotes you send, how many never get a yes or no? Most homeowners get 2–3 quotes and go quiet. I follow up on those for you and send back anyone still interested. Free on 100 old quotes, and after that you only pay for jobs that book. Worth trying?

### Window cleaning: direct message
> Hi [Name], how many past customers do you have who haven't booked again this year? I message them when they're due for a clean ("time for your spring windows?") and send you the bookings. Free on your first 100 past customers, and after that you only pay per booked job. Want to try it before spring?

### To companies running ads
> Hi [Name], saw your ads for [fence installs / window cleaning]. You're already paying for new leads, so quick question: does anyone follow up on the quotes (or past customers) that went quiet? That's usually the cheapest job you'll get. I'll do it free on 100 to show you.

### To Angi / Thumbtack pros
> Hi [Name], are you still paying for shared leads on [Angi/Thumbtack]? Before spending more there, your old quotes and past customers are usually cheaper jobs. I'll follow up on 100 of them free. You only pay later, and only for jobs that book.

### Facebook group post (ask, don't pitch)
> Question for [fence / window cleaning] owners: what % of your quotes never answer? And for repeat work, do you remind past customers when they're due, or wait for them to call?

### Follow-up (3 days later)
> Hi [Name], bumping this in case it got buried. Happy to show you exactly what the messages would look like first.

## Samples to show owners

Ready in `samples/`:
- `fencing-sample-messages.csv`: follow-ups on fence quotes
- `window_cleaning-sample-messages.csv`: "you're due" messages for past customers

With their company name in them:
```
python agency.py samples --trade fencing --business "Their Fence Co" --sender "Their Name"
python agency.py samples --trade window_cleaning --business "Their Window Co" --sender "Their Name"
```
