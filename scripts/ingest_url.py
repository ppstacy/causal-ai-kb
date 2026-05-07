"""Ingest a user-submitted URL: fetch, summarize, save, learn keywords for future tracking.

Used by:
  - manual run:        `python scripts/ingest_url.py <url> ["optional note"]`
  - GitHub Action:     workflow_dispatch with `url` and `note` inputs (mobile-friendly)
  - Slack slash command: posts to a forwarder that fires `repository_dispatch`

LinkedIn note: posts/articles behind a login wall (e.g. saved-posts pages) can't
be scraped — submit individual public post URLs instead.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import re
import sys
from pathlib import Path

import anthropic
import requests
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ingest_url")

ROOT = Path(__file__).resolve().parents[1]
MODEL = os.environ.get("CAUSAL_KB_MODEL", "claude-opus-4-7")
UA = "causal-ai-kb/0.1 (+https://github.com/ppstacy/causal-ai-kb)"

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "authors_or_source": {"type": "string"},
        "published": {"type": "string", "description": "ISO date or free-form, '' if unknown"},
        "summary": {"type": "string", "description": "2-3 sentences, contribution-first"},
        "topic": {
            "type": "string",
            "enum": ["causal-inference", "uplift", "experimentation", "causal-lm", "tools", "other"],
        },
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "description": "5-10 lowercase phrases that describe the post's substance — used to surface similar items in future fetches",
        },
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "why_relevant": {"type": "string"},
    },
    "required": [
        "title", "authors_or_source", "published", "summary",
        "topic", "keywords", "score", "why_relevant",
    ],
    "additionalProperties": False,
}


def fetch_url(url: str) -> tuple[str, str]:
    """Fetch a URL and return (title_guess, cleaned_text). Best-effort."""
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=30, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"could not fetch {url}: {exc}") from exc
    html = resp.text

    title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE | re.DOTALL)
    title_guess = title_match.group(1).strip() if title_match else ""

    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return title_guess, text[:25_000]


def extract(url: str, note: str, page_text: str, title_guess: str, interests: dict) -> dict:
    client = anthropic.Anthropic()
    profile = interests["profile"]
    user_msg = (
        f"URL: {url}\n"
        f"Title hint: {title_guess}\n"
        f"User note: {note or '(none)'}\n\n"
        f"Page text:\n{page_text}\n"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=[
            {"type": "text", "text": f"Reader profile:\n\n{profile}", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": (
                "You are extracting structured metadata from a URL the reader saved. "
                "Score the relevance per the rubric (0-100). Extract 5-10 lowercase "
                "keyword phrases that capture the post's substance — they will seed "
                "future searches. Be specific (e.g. 'switchback experiments', "
                "'doubly robust estimator', 'cuped variance reduction'); avoid "
                "vague phrases like 'machine learning' or 'data science'."
            )},
        ],
        messages=[{"role": "user", "content": user_msg}],
        output_config={"format": {"type": "json_schema", "schema": EXTRACT_SCHEMA}},
    )
    payload = next((b.text for b in response.content if b.type == "text"), "")
    return json.loads(payload)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s[:60] or "submission"


def write_submission(url: str, data: dict, note: str) -> Path:
    today = dt.date.today()
    sub_dir = ROOT / "submissions" / today.isoformat()
    sub_dir.mkdir(parents=True, exist_ok=True)
    title = data.get("title") or "(no title)"
    slug = slugify(title)
    path = sub_dir / f"{slug}.md"

    topic = data.get("topic", "other")
    keywords = data.get("keywords", [])
    # Obsidian frontmatter — tags are a flat list; topic is its own tag too
    tag_list = ["submission", topic] + [
        re.sub(r"[^a-z0-9]+", "-", k.lower()).strip("-") for k in keywords if k
    ]

    fm_lines = ["---", f"title: {title.replace(chr(10), ' ')}"]
    if data.get("authors_or_source"):
        fm_lines.append(f"source: {data['authors_or_source']}")
    if data.get("published"):
        fm_lines.append(f"published: {data['published']}")
    fm_lines += [
        f"url: {url}",
        f"saved: {today.isoformat()}",
        f"score: {data.get('score', 0)}",
        f"topic: {topic}",
    ]
    if note:
        fm_lines.append(f"note: {note}")
    fm_lines.append("tags:")
    for t in tag_list:
        fm_lines.append(f"  - {t}")
    fm_lines.append(f"related:")
    fm_lines.append(f'  - "[[{topic}]]"')
    fm_lines.append("---")
    fm = "\n".join(fm_lines) + "\n\n"

    body = (
        f"# {title}\n\n"
        f"| Field | Value |\n"
        f"| --- | --- |\n"
        f"| **URL** | {url} |\n"
        f"| **Source** | {data.get('authors_or_source', '')} |\n"
        f"| **Published** | {data.get('published', '')} |\n"
        f"| **Topic** | [[{topic}]] |\n"
        f"| **Score** | {data.get('score', 0)} |\n"
        f"| **Saved** | {today.isoformat()} |\n"
        f"| **Note** | {note or '(none)'} |\n\n"
        f"## Summary\n\n{data.get('summary', '').strip()}\n\n"
        f"## Why relevant\n\n"
        f"> [!note] Why this is here\n"
        f"> {data.get('why_relevant', '').strip().replace(chr(10), chr(10) + '> ')}\n\n"
        f"## Keywords\n\n"
        f"{' '.join('#' + re.sub(r'[^a-z0-9]+', '-', k.lower()).strip('-') for k in keywords if k)}\n"
    )
    path.write_text(fm + body)
    return path


def update_learned_keywords(new_keywords: list[str]) -> int:
    """Merge new keywords into config/learned_keywords.yaml. Return count added."""
    path = ROOT / "config" / "learned_keywords.yaml"
    existing = yaml.safe_load(path.read_text()) if path.exists() else {}
    existing = existing or {}
    current = set(existing.get("keywords", []))
    additions = [k.lower().strip() for k in new_keywords if k.lower().strip() not in current]
    if additions:
        merged = sorted(current | set(additions))
        path.write_text(yaml.safe_dump(
            {"keywords": merged, "updated": dt.datetime.utcnow().isoformat()},
            sort_keys=False,
        ))
    return len(additions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a saved URL into the KB.")
    parser.add_argument("url")
    parser.add_argument("note", nargs="?", default="")
    args = parser.parse_args()

    interests = yaml.safe_load((ROOT / "config" / "interests.yaml").read_text())

    logger.info("fetching %s", args.url)
    title_guess, text = fetch_url(args.url)
    if not text:
        logger.error("empty page content — cannot ingest")
        sys.exit(2)

    logger.info("extracting metadata via %s", MODEL)
    data = extract(args.url, args.note, text, title_guess, interests)

    path = write_submission(args.url, data, args.note)
    added = update_learned_keywords(data.get("keywords", []))
    logger.info("wrote %s (score %s, +%d new keywords)", path, data.get("score"), added)
    print(json.dumps({"path": str(path.relative_to(ROOT)), "score": data.get("score"), "keywords_added": added}))


if __name__ == "__main__":
    main()
