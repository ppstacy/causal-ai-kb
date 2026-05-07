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


def score_all(items: list[dict], interests: dict) -> list[Scored]:
    if not items:
        return []
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
