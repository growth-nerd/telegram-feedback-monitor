# Telegram Feedback Monitor

> Automated signal detection from community chats — built to close the feedback loop on product experiments faster and with less noise.

## The Problem

When you ship a new feature, you need to know how users actually feel about it — not just what the metrics say, but what they're *saying*.

For products with active Telegram communities (common in Eastern Europe), those conversations are happening right now, in real time. But reading them manually is:

- ⏱ **Time-consuming** — hours per week scanning multiple chats
- 📉 **Low signal quality** — easy to miss mentions, hard to spot patterns
- 🧠 **Cognitively biased** — you notice what confirms what you already think
- 🐌 **Slow** — by the time you've read everything, the experiment has moved on

## What It Does

Automatically monitors public Telegram chats for mentions of specific keywords, classifies each mention by sentiment, and delivers a structured report to Notion — on a schedule, without manual effort.

**Three stages run in sequence:**
1. **Collect** — scans all messages within a configurable time window across multiple chats
2. **Analyze** — classifies each mention as positive / neutral / negative using a multilingual transformer model
3. **Report** — appends a formatted summary to Notion with sentiment breakdown and sample quotes

## Why This Matters for Product & Growth

| Before | After |
|---|---|
| Manual chat reading, 2-3 hrs/week | Automated daily report, 0 hrs |
| Subjective, memory-based signal | Structured sentiment data |
| Delayed reaction to user concerns | Same-day signal on experiment perception |
| No historical record | Full Notion history per keyword/feature |

## Setup
```bash
pip install telethon vaderSentiment notion-client pyyaml schedule python-dotenv
pip install transformers torch sentencepiece protobuf
cp references/config.example.yaml config.yaml
python3 run.py
```

## Tech Stack
- Telegram API: Telethon
- Sentiment: Cardiff NLP XLM-RoBERTa (multilingual)
- Reporting: Notion API
- Language: Python 3.9+

## Roadmap
- [ ] Slack report output
- [ ] Keyword trend charts over time
- [ ] Experiment tagging (link mentions to specific A/B tests)
- [ ] Alert on sentiment spike (>30% negative in 24h)

## About
Built by a Senior Growth PM to solve a real workflow problem: getting faster, higher-quality signal from community conversations without the manual overhead.
