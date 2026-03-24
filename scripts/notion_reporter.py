"""
notion_reporter.py — Append a structured feedback report to a Notion page.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_BAR_WIDTH = 20  # characters for the visual sentiment bar


def _sentiment_bar(pos_pct: float, neu_pct: float, neg_pct: float) -> str:
    p = round(pos_pct / 100 * _BAR_WIDTH)
    nu = round(neu_pct / 100 * _BAR_WIDTH)
    ne = _BAR_WIDTH - p - nu
    bar = "🟢" * p + "⬜" * nu + "🔴" * max(ne, 0)
    return f"{bar}  +{pos_pct}% / ~{neu_pct}% / -{neg_pct}%"


def _text_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        },
    }


def _quote_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "quote",
        "quote": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        },
    }


def _heading_block(text: str, level: int = 2) -> dict:
    htype = f"heading_{level}"
    return {
        "object": "block",
        "type": htype,
        htype: {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        },
    }


def _divider_block() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def build_blocks(aggregated: dict, config: dict, run_at: datetime) -> list[dict]:
    mon = config["monitor"]
    pos = aggregated["positive"]
    neu = aggregated["neutral"]
    neg = aggregated["negative"]

    blocks: list[dict] = [
        _heading_block(f"📊 Feedback Report — {run_at.strftime('%Y-%m-%d %H:%M UTC')}"),
        _text_block(
            f"Keywords: {', '.join(mon['keywords'])} | "
            f"Chats: {', '.join(str(c) for c in mon['chats'])} | "
            f"Total mentions: {aggregated['total']}"
        ),
        _text_block(_sentiment_bar(pos["pct"], neu["pct"], neg["pct"])),
    ]

    for label, emoji, bucket in [
        ("Positive", "🟢", pos),
        ("Neutral", "⬜", neu),
        ("Negative", "🔴", neg),
    ]:
        blocks.append(_heading_block(f"{emoji} {label} ({bucket['count']})", level=3))
        if bucket["samples"]:
            for sample in bucket["samples"]:
                blocks.append(_quote_block(sample))
        else:
            blocks.append(_text_block("No samples."))

    blocks.append(_divider_block())
    return blocks


def publish(aggregated: dict, config: dict) -> None:
    notion_cfg = config.get("notion", {})
    token = notion_cfg.get("token", "")
    page_id = notion_cfg.get("page_id", "")

    if not token or not page_id:
        logger.info("Notion output skipped (no token/page_id configured)")
        return

    from notion_client import Client

    client = Client(auth=token)
    run_at = datetime.now(tz=timezone.utc)
    blocks = build_blocks(aggregated, config, run_at)

    client.blocks.children.append(block_id=page_id, children=blocks)
    logger.info("Report published to Notion page %s", page_id)
