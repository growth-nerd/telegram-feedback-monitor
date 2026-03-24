"""
analyzer.py — Sentiment classification + aggregation.
Supports VADER (fast, English) and transformer models (multilingual).
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "neutral", "negative"]


def _vader_label(compound: float, threshold: float) -> SentimentLabel:
    if compound >= threshold:
        return "positive"
    if compound <= -threshold:
        return "negative"
    return "neutral"


def analyze_vader(messages: list[dict], min_confidence: float = 0.05) -> list[dict]:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    sia = SentimentIntensityAnalyzer()
    results = []
    for msg in messages:
        scores = sia.polarity_scores(msg["text"])
        label = _vader_label(scores["compound"], min_confidence)
        results.append({**msg, "sentiment": label, "score": scores["compound"]})
    return results


def analyze_transformers(messages: list[dict], model_name: str) -> list[dict]:
    from transformers import pipeline

    logger.info("Loading transformer model: %s (first run may download ~500 MB)", model_name)
    classifier = pipeline("text-classification", model=model_name, truncation=True)

    label_map = {
        "LABEL_0": "negative",
        "LABEL_1": "neutral",
        "LABEL_2": "positive",
        # Cardiff NLP models use these labels directly:
        "negative": "negative",
        "neutral": "neutral",
        "positive": "positive",
    }

    results = []
    texts = [m["text"][:512] for m in messages]  # truncate for model limit
    preds = classifier(texts, batch_size=16)
    for msg, pred in zip(messages, preds):
        raw_label = pred["label"].lower()
        label: SentimentLabel = label_map.get(raw_label, "neutral")
        results.append({**msg, "sentiment": label, "score": pred["score"]})
    return results


def analyze(messages: list[dict], config: dict) -> list[dict]:
    """Classify a list of messages. Returns messages with 'sentiment' and 'score' added."""
    if not messages:
        return []
    engine = config["sentiment"]["engine"]
    if engine == "transformers":
        return analyze_transformers(messages, config["sentiment"]["model"])
    return analyze_vader(messages, config["sentiment"].get("min_confidence", 0.05))


def aggregate(classified: list[dict], top_n: int = 3) -> dict:
    """
    Aggregate classified messages into a report dict:
    {
        "total": int,
        "positive": { "count": int, "pct": float, "samples": [str] },
        "neutral":  { ... },
        "negative": { ... },
    }
    """
    buckets: dict[SentimentLabel, list[dict]] = {
        "positive": [],
        "neutral": [],
        "negative": [],
    }
    for msg in classified:
        buckets[msg["sentiment"]].append(msg)

    total = len(classified)
    report: dict = {"total": total}
    for label, msgs in buckets.items():
        # Sort by absolute score so strongest signals surface first
        sorted_msgs = sorted(msgs, key=lambda m: abs(m["score"]), reverse=True)
        report[label] = {
            "count": len(msgs),
            "pct": round(len(msgs) / total * 100, 1) if total else 0.0,
            "samples": [m["text"][:300] for m in sorted_msgs[:top_n]],
        }
    return report
