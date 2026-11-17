# New Focus: Fencing and Window Cleaning

## The offer: dead lead revival

"Send me your dead leads. I follow up with every one in your company's name and send you the ones ready to book. Free on your first 100; after that you only pay per booked job."

**Dead leads** come in three kinds, so ask owners for all three:

| Kind | What it is | Fencing | Window cleaning |
|---|---|---|---|
| **Inquiries** | Called, filled out a form or answered an ad, never got a quote or booked | Very common: missed calls, slow callbacks | Common in spring rush |
| **Quotes** | Got a price, went quiet | The big one: $3k–$15k jobs | Commercial and one-off jobs |
| **Past customers** | Used them before, haven't come back | Stain and seal, repairs, gates | The big one: yearly and seasonal cleans |

The same tool handles all three. Add a `lead_type` column (`inquiry`, `quote` or `past_customer`) to the list, or leave it out: rows with a quote amount count as quotes, and the rest count as inquiries. Example: `sample_data/fencing_dead_leads.csv`.

**Ask every owner:** "Where do your missed calls, old form fills, old quotes and past customers live? A spreadsheet, your CRM, your phone? I can work with any of it."

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
> Hi [Name], quick question: how many fence leads went quiet this year: missed calls, web forms nobody got back to, quotes that never got a yes? I follow up on those dead leads in your company's name and send you the ones ready to book. Free on your first 100, and after that you only pay for jobs that book. Worth trying?

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
