---
name: telegram-feedback-monitor
description: >
  Monitor and analyze customer feedback from public Telegram groups and channels.
  Use this skill whenever the user wants to: track product mentions in Telegram,
  analyze sentiment of Telegram messages, collect customer feedback from Telegram,
  monitor brand or feature mentions in Telegram chats, or generate a feedback
  report from Telegram data. Triggers on any mention of "Telegram feedback",
  "Telegram monitoring", "Telegram sentiment", "Telegram mentions", or requests
  to "watch", "track", or "analyze" Telegram groups/channels. Even if the user
  just says "check what people are saying on Telegram" — use this skill.
---

# Telegram Feedback Monitor

This tool watches public Telegram groups for mentions of your product, automatically
decides whether each message is positive, neutral, or negative, and posts a
neat summary report to a Notion page — all without you having to read every
message yourself.

It does three things in order:
1. **Collect** — reads messages from Telegram chats that mention your keywords
2. **Analyze** — labels each message as positive / neutral / negative
3. **Report** — adds a formatted summary to your Notion page

---

## Before you begin — what you'll need

You need three things set up before running the tool. Don't worry, each one
takes about 5 minutes and the steps below walk you through them one at a time.

**Checklist:**
- [ ] Telegram API credentials (API ID + API Hash)
- [ ] Notion integration token + page ID
- [ ] Python installed on your computer

---

## Step 1 — Get your Telegram API credentials

Telegram requires you to register an "app" to use their API. This is free and
takes about 2 minutes. The tool only *reads* public messages — it never posts,
joins private groups, or stores your data anywhere permanent.

1. Open https://my.telegram.org in your browser and log in with your phone number
2. Click **"API development tools"**
3. Fill in the form — the app name and description can be anything (e.g. "My Monitor")
4. Click **Create application**
5. You'll see two values — copy both and keep them somewhere safe:
   - **App api_id** — a short number, e.g. `12345678`
   - **App api_hash** — a long string of letters and numbers

> ⚠️ Treat these like a password. Don't share them or post them online.

---

## Step 2 — Set up Notion

You need to create a "integration" in Notion so the tool has permission to
write to your page.

1. Go to https://www.notion.so/my-integrations and click **"+ New integration"**
2. Give it a name (e.g. "Telegram Monitor"), select your workspace, click **Submit**
3. Copy the **"Internal Integration Token"** — it starts with `secret_`
4. Now open the Notion page where you want reports to appear
5. Click the `•••` menu in the top-right corner → **"Add connections"** → select
   the integration you just created
6. Look at the URL in your browser — it looks like:
   `https://www.notion.so/My-Page-**abc123def456abc123def456abc123de**`
   Copy the bold part (the 32-character string at the end) — that's your **Page ID**

---

## Step 3 — Install Python and the required packages

**Do you have Python installed?**
Open a terminal (on Mac: search "Terminal"; on Windows: search "Command Prompt")
and type `python --version` then press Enter. If you see a version number like
`Python 3.11.4`, you're good. If you get an error, download Python from
https://www.python.org/downloads/ and install it first.

Once Python is ready, install the required packages by copying and running this
command in your terminal:

```bash
pip install telethon vaderSentiment notion-client pyyaml schedule python-dotenv
```

> 💡 **What is pip?** It's Python's built-in package installer — think of it
> like an app store for Python tools. The command above installs everything
> this skill needs.

**If your chats are not in English** (e.g. Ukrainian, Russian, Spanish), also run:
```bash
pip install transformers torch
```
This downloads a smarter multilingual sentiment model (~500 MB, one-time).

---

## Step 4 — Configure the tool

1. Find the file called `config.example.yaml` in the `references/` folder
2. Make a copy of it and rename the copy to `config.yaml` (in the same folder
   as `run.py`)
3. Open `config.yaml` in a text editor and fill in your values:

```yaml
telegram:
  api_id: "12345678"           # ← paste your API ID here
  api_hash: "abc123..."        # ← paste your API Hash here
  session_name: "feedback_monitor"   # leave this as-is

notion:
  token: "secret_xxxx..."      # ← paste your Notion token here
  page_id: "abc123..."         # ← paste your Notion page ID here

monitor:
  keywords:
    - "your_product_name"      # ← words to search for (one per line, with the dash)
    - "your_feature_name"
  chats:
    - "channel_username"       # ← Telegram channel usernames WITHOUT the @ symbol
  lookback_hours: 24           # how many hours back to scan on first run
  schedule_cron: "0 9 * * *"   # when to run automatically (9am daily by default)

sentiment:
  engine: "vader"              # use "vader" for English, "transformers" for other languages
  model: "cardiffnlp/twitter-roberta-base-sentiment-latest"
  min_confidence: 0.05

output:
  top_samples_per_bucket: 3    # how many example quotes to show per sentiment category
```

> ⚠️ Never share this file with anyone — it contains your secret tokens.
> If you use Git, add `config.yaml` to your `.gitignore` file.

**Which engine should I use?**

| Your situation | Setting to use |
|---|---|
| Chats are mostly English | `engine: "vader"` — fast, no extra download |
| Chats are multilingual or non-English | `engine: "transformers"` — slower but smarter |

---

## Step 5 — Run it!

Open your terminal, navigate to the folder where `run.py` lives, and run:

```bash
python run.py
```

**The very first time only:** The tool will ask for your Telegram phone number
and then send you a confirmation code in Telegram. Type them in when prompted.
After that, a `.session` file is saved and you'll never be asked again.

After a minute or so, check your Notion page — a new section should have appeared
with the sentiment summary!

**To run it automatically every day:**
```bash
python run.py --schedule
```
Keep this terminal window open (or run it on a server). It will run itself
on the schedule you set in `config.yaml` (default: 9am daily).

---

## What the Notion report looks like

Each run adds a section like this to your page:

```
📊 Feedback Report — 2025-09-01 09:00 UTC
Keywords: your_product | Chats: channel_name | Total mentions: 42

🟢🟢🟢🟢🟢🟢🟢🟢⬜⬜⬜⬜⬜⬜🔴🔴🔴🔴🔴🔴  +42.9% / ~35.7% / -21.4%

🟢 Positive (18)
  "This feature saved me so much time!"
  "Finally works perfectly on mobile"
  "Really impressed with the latest update"

⬜ Neutral (15)
  "Does anyone know how to configure X?"
  ...

🔴 Negative (9)
  "Still crashing on Android"
  ...
```

Older reports stay on the page below each new one, so you have a full history.

---

## Troubleshooting

**"No module named telethon"** — You haven't installed the packages yet.
Run the `pip install ...` command from Step 3 again.

**"No mentions found"** — Check that your channel usernames in `config.yaml`
have no `@` symbol, and that the channels are public. Try increasing
`lookback_hours` to `72` to scan further back.

**"APIResponseError" from Notion** — Your token may be wrong, or you forgot
Step 2.5 (connecting the integration to the page). Go back to your Notion page,
click `•••` → Add connections.

**"FloodWaitError" from Telegram** — You're scanning too many chats too quickly.
The tool already adds a 1-second pause between chats; if this keeps happening,
reduce the number of chats in your config.

**Keeps asking for my phone number every time** — The `.session` file was
deleted or moved. Just run `python run.py` once more interactively to
re-authenticate.

**Wrong sentiment on my language** — Switch to `engine: "transformers"` in
`config.yaml` and use model
`cardiffnlp/twitter-xlm-roberta-base-sentiment` for multilingual support.

---

## Files in this skill

| File | What it does |
|---|---|
| `run.py` | Start here — runs the whole pipeline |
| `config.yaml` | Your personal settings (you create this in Step 4) |
| `scripts/collector.py` | Connects to Telegram and collects matching messages |
| `scripts/analyzer.py` | Classifies messages as positive / neutral / negative |
| `scripts/notion_reporter.py` | Formats and posts the report to Notion |
| `references/config.example.yaml` | Template to copy for your config |
