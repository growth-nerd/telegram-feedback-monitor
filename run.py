"""
run.py — Entrypoint. Runs collect → analyze → report, once or on a schedule.

Usage:
    python run.py                          # single run
    python run.py --schedule               # run now, then on cron schedule
    python run.py --config my_config.yaml  # use a custom config file
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run")

# Allow running from the project root regardless of cwd
sys.path.insert(0, str(Path(__file__).parent))
from scripts.collector import collect_mentions
from scripts.analyzer import analyze, aggregate
from scripts.notion_reporter import publish


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def save_local(aggregated: dict, config: dict) -> None:
    out_path = config.get("output", {}).get("local_file", "")
    if not out_path:
        return
    run_at = datetime.now(tz=timezone.utc).isoformat()
    report = {
        "run_at": run_at,
        "keywords": config["monitor"]["keywords"],
        "chats": config["monitor"]["chats"],
        **aggregated,
    }
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info("Report saved to %s", out_path)


async def run_once(config: dict) -> None:
    logger.info("=== Starting feedback collection run ===")

    # Stage 1: collect
    messages = await collect_mentions(config)
    if not messages:
        logger.info("No matching mentions found — nothing to report.")
        return

    # Stage 2: analyze
    top_n = config.get("output", {}).get("top_samples_per_bucket", 3)
    classified = analyze(messages, config)
    aggregated = aggregate(classified, top_n=top_n)

    pos = aggregated["positive"]
    neu = aggregated["neutral"]
    neg = aggregated["negative"]
    logger.info(
        "Total: %d | Positive: %d (%.1f%%) | Neutral: %d (%.1f%%) | Negative: %d (%.1f%%)",
        aggregated["total"],
        pos["count"], pos["pct"],
        neu["count"], neu["pct"],
        neg["count"], neg["pct"],
    )

    # Stage 3: report
    save_local(aggregated, config)
    publish(aggregated, config)

    logger.info("=== Run complete ===")


def main():
    parser = argparse.ArgumentParser(description="Telegram Feedback Monitor")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    parser.add_argument("--schedule", action="store_true", help="Run on cron schedule")
    args = parser.parse_args()

    config = load_config(args.config)

    if not args.schedule:
        asyncio.run(run_once(config))
        return

    import schedule
    import time

    cron = config["monitor"].get("schedule_cron", "0 9 * * *")
    # Parse simple "H M * * *" cron into schedule library call
    parts = cron.split()
    hour, minute = parts[1], parts[0]
    schedule.every().day.at(f"{int(hour):02d}:{int(minute):02d}").do(
        lambda: asyncio.run(run_once(config))
    )

    logger.info("Scheduled to run daily at %s:%s UTC. Running immediately first.", hour, minute)
    asyncio.run(run_once(config))

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
