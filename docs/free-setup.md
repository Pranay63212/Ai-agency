# Run It Free on Your Own Computer (Email)

Everything here is free: Gmail sends and receives, NVIDIA's free tier writes the messages, and your computer runs it once a day. Texting is the only part that costs money, and you don't need it to start.

## One-time setup (about 20 minutes)

1. **Install Python** (3.11 or newer) from python.org. On Windows, tick "Add Python to PATH".
2. **Download this project** from GitHub (green "Code" button, then "Download ZIP") and unzip it.
3. **Install the requirements:** open a terminal in the project folder and run
   ```
   pip install -r requirements.txt
   ```
4. **Make the email account.** Create a new Gmail just for this work (don't use your personal one). Then:
   - Google Account > Security > turn on **2-Step Verification**
   - Google Account > Security > **App passwords** > create one (name it "agency"). Copy the 16-letter password.
5. **Add your keys.** Copy `.env.example` to a new file named `.env` and fill in your NVIDIA key, Gmail address and app password.
6. **Test it:**
   ```
   python agency.py new "Test HVAC" --input sample_data/hvac_unsold_estimates.csv --sender Mike --phone "(214) 555-0100" --email-only --provider mock
   python agency.py daily test-hvac
   ```
   This only previews. Nothing is sent without `--live`.

## For each client

```
python agency.py new "Their Company" --input their_list.csv --sender [Owner first name] --phone "[their phone]" --email-only --limit 100
```
Send them `clients/their-company/plan.html` to approve the messages. Then start the daily run below.

## Run it automatically every day

The `daily` command does everything in the right order: reads new replies, alerts you about hot leads, then sends what's due, skipping anyone who replied.

**Windows (Task Scheduler)**
1. Open Task Scheduler > Create Basic Task > name it "Agency daily" > Daily > 10:00 AM.
2. Action: Start a program.
   - Program: `python`
   - Arguments: `agency.py daily their-company --live`
   - Start in: the project folder path (for example `C:\Users\you\Ai-agency`)
3. Tick "Run whether user is logged on or not" if you want it to run with the screen locked.

**Mac (cron)**
Open Terminal, run `crontab -e`, and add:
```
0 10 * * 1-6 cd ~/Ai-agency && /usr/bin/env python3 agency.py daily their-company --live >> daily.log 2>&1
```

Your computer must be on (not asleep) at that time. If it was off, just run the same command when you're back. It catches up safely, and never messages someone on back-to-back days.

## Checking in

```
python agency.py status their-company     # who to call today
python agency.py report their-company     # Friday report + invoice
```

## Good habits

- **Which email sends?** By default every client uses your Gmail from `.env`, shown as "<Owner> at <Their Company>". Better: ask the client to create a Gmail just for this (like `quotes.theircompany@gmail.com`) and send you an app password. Then:
  ```
  python agency.py new "Their Company" ... --email-user quotes.theircompany@gmail.com
  ```
  and add the line it prints (`EMAIL_PASSWORD_THEIR_COMPANY=...`) to `.env`. Replies are read from that same mailbox. The owner can change the password any time to cut off access.
- **Stay under Gmail's limits:** about 500 emails a day. A 100-quote pilot sends roughly 30 a day at most.
- **Hot leads:** set `--owner-email` when you create a campaign so the owner gets an email the moment someone is interested.
- **Back up `clients/`** somewhere private. It holds customers' names and contact details. Never upload it to GitHub (it's already excluded).
