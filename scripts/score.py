"""Score items for relevance using Claude with prompt caching on the interests profile."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Iterable

import anthropic
import yaml

logger = logging.getLogger(__name__)

MODEL = os.environ.get("CAUSAL_KB_MODEL", "claude-opus-4-7")
BATCH_SIZE = 12  # items per scoring call


@dataclass
class Scored:
    item_id: str
    score: int
    topic: str
    why_relevant: str
    summary: str


SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string"},
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "topic": {
                        "type": "string",
                        "enum": ["causal-inference", "uplift", "experimentation",
                                 "causal-lm", "tools", "other"],
                    },
                    "why_relevant": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["item_id", "score", "topic", "why_relevant", "summary"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["scores"],
    "additionalProperties": False,
}


def load_interests(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _build_system(interests: dict) -> list[dict]:
    """System blocks: stable profile + rubric + style. Cache the whole thing."""
    text = (
        "You are a research-radar assistant scoring new items for a single reader.\n\n"
        "## Reader profile\n\n"
        f"{interests['profile'].strip()}\n\n"
        "## Scoring rubric\n\n"
        f"{interests['scoring_rubric'].strip()}\n\n"
        "## Summary style\n\n"
        f"{interests['summary_style'].strip()}\n"
    )
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def _format_batch(items: list[dict]) -> str:
    parts = ["Score the following items. Return JSON matching the schema."]
    for item in items:
        parts.append(
            f"---\n"
            f"item_id: {item['id']}\n"
            f"source: {item['source_name']}\n"
            f"title: {item['title']}\n"
            f"authors: {', '.join(item.get('authors', []))[:300]}\n"
            f"abstract_or_summary: {(item.get('summary') or '')[:1800]}\n"
            f"url: {item['url']}\n"
        )
    return "\n".join(parts)


def score_batch(client: anthropic.Anthropic, system: list[dict], items: list[dict]) -> list[Scored]:
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": _format_batch(items)}],
        output_config={"format": {"type": "json_schema", "schema": SCORE_SCHEMA}},
    )
    text = next((b.text for b in response.content if b.type == "text"), "")
    if not text:
        logger.warning("empty scoring response")
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("malformed scoring JSON: %s", exc)
        return []
    return [
        Scored(
            item_id=row["item_id"],
            score=row["score"],
            topic=row["topic"],
            why_relevant=row["why_relevant"],
            summary=row["summary"],
        )
        for row in data.get("scores", [])
    ]


_TOPIC_KEYWORDS = {
    "causal-lm": [
        "language model", "llm", "large language", "counterfactual generation",
        "transformer", "decoder-only", "autoregressive",
    ],
    "uplift": [
        "uplift", "heterogeneous treatment", "cate", "ite ", " hte", "meta-learner",
        "policy learning", "incremental", "incrementality", "conversion lift",
        "doubly robust", "x-learner", "r-learner", "dr-learner",
    ],
    "experimentation": [
        "a/b test", "ab test", "experimentation", "switchback", "geo experiment",
        "geolift", "variance reduction", "cuped", "cupac", "sequential testing",
        "interference", "sutva", "marketplace experiment", "randomized",
    ],
    "causal-inference": [
        "causal inference", "double machine learning", "dml ", "instrumental variable",
        "regression discontinuity", "difference-in-differences", "synthetic control",
        "propensity", "treatment effect", "counterfactual", "do-calculus",
        "sensitivity analysis", "structural causal",
    ],
}

_HIGH_QUALITY_SOURCE_HINTS = (
    "arXiv stat.ME", "arXiv stat.ML", "arXiv econ.EM", "Microsoft Research",
    "Netflix Tech", "Uber Engineering", "DoorDash", "Booking", "Airbnb",
    "Spotify", "KDD", "NeurIPS", "ICML", "WSDM",
)


def _topic_for(blob: str) -> str:
    """Pick the topic with the most keyword hits; ties broken by enum order."""
    counts = {t: sum(1 for kw in kws if kw in blob) for t, kws in _TOPIC_KEYWORDS.items()}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else "other"


def score_heuristic(items: list[dict], interests: dict) -> list[Scored]:
    """Free, no-LLM scoring. Quality is lower than the Claude path but works
    when no API key is available. Score = base + tracked-author boost +
    keyword density + source-quality bump."""
    tracked_authors = {a.lower() for a in interests.get("tracked_authors", [])}
    out: list[Scored] = []
    for item in items:
        title = (item.get("title") or "").lower()
        summary = (item.get("summary") or "").lower()
        blob = f"{title} {summary}"
        authors = {a.lower() for a in item.get("authors", [])}

        score = 30  # base — every fetched item already passed the keyword filter
        why_bits: list[str] = []

        if tracked_authors & authors:
            matched = (tracked_authors & authors).pop()
            score += 50
            why_bits.append(f"tracked author ({matched.title()})")

        # keyword density across all topics — capped so it can't dominate
        kw_hits = sum(1 for kws in _TOPIC_KEYWORDS.values() for kw in kws if kw in blob)
        if kw_hits:
            score += min(kw_hits, 5) * 4
            why_bits.append(f"{kw_hits} keyword hits")

        if any(h in item.get("source_name", "") for h in _HIGH_QUALITY_SOURCE_HINTS):
            score += 8
            why_bits.append("trusted source")

        score = min(score, 100)
        topic = _topic_for(blob)

        # No-LLM "summary" — first ~400 chars of the abstract/post excerpt
        excerpt = (item.get("summary") or "").strip()
        if len(excerpt) > 400:
            excerpt = excerpt[:400].rsplit(" ", 1)[0] + "…"
        why_relevant = "; ".join(why_bits) if why_bits else "matches keyword filter"

        out.append(Scored(
            item_id=item["id"], score=score, topic=topic,
            why_relevant=why_relevant, summary=excerpt or item.get("title", ""),
        ))
    return out


def score_all(items: list[dict], interests: dict) -> list[Scored]:
    """LLM scoring if ANTHROPIC_API_KEY is set, else free heuristic fallback."""
    if not items:
        return []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning(
            "ANTHROPIC_API_KEY not set — using free heuristic scoring "
            "(lower quality than LLM scoring; set the key when you can)."
        )
        return score_heuristic(items, interests)

    client = anthropic.Anthropic()
    system = _build_system(interests)
    out: list[Scored] = []
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i : i + BATCH_SIZE]
        try:
            scored = score_batch(client, system, batch)
        except anthropic.APIError as exc:
            logger.error("scoring batch failed: %s", exc)
            continue
        out.extend(scored)
        logger.info("scored %d/%d", min(i + BATCH_SIZE, len(items)), len(items))
    return out


def merge(items: list[dict], scores: list[Scored]) -> list[dict]:
    """Attach score data to each item. Drop items with no score."""
    by_id = {s.item_id: s for s in scores}
    out = []
    for item in items:
        s = by_id.get(item["id"])
        if s is None:
            continue
        out.append({
            **item,
            "score": s.score,
            "topic": s.topic,
            "why_relevant": s.why_relevant,
            "llm_summary": s.summary,
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out
