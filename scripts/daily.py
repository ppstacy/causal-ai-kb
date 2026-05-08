"""Daily entry point: fetch → score → write picks + firehose markdown."""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import sys
from pathlib import Path

# Auto-load a local .env file so `python scripts/daily.py` works without
# explicit env-var prefix. .env is gitignored. The repo-root path is computed
# relative to this script so it works regardless of CWD.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass  # dotenv is optional; explicit env vars still work

from fetch import fetch_all, load_sources
from render import render_firehose, render_picks, write_daily, write_daily_feed
from score import load_interests, merge, score_all

DEDUP_WINDOW_DAYS = 14

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("daily")

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning(
            "ANTHROPIC_API_KEY not set — running with free heuristic scoring "
            "(no LLM summaries, lower-quality picks). Set the key in .env when you can."
        )

    sources = load_sources(ROOT / "config" / "sources.yaml")
    interests = load_interests(ROOT / "config" / "interests.yaml")

    # If there's a learned-keywords file (from inbox ingestion), merge into arxiv keyword filters
    learned_path = ROOT / "config" / "learned_keywords.yaml"
    if learned_path.exists():
        import yaml
        learned = yaml.safe_load(learned_path.read_text()) or {}
        extra = learned.get("keywords", [])
        if extra:
            sources.setdefault("arxiv", {}).setdefault("keyword_filters", []).extend(extra)
            logger.info("merged %d learned keywords into arxiv filters", len(extra))

    raw_items = fetch_all(sources, days_lookback=sources.get("arxiv", {}).get("days_lookback", 1))
    logger.info("fetched %d unique items", len(raw_items))

    # Cross-day dedup: drop items that already appeared in any of the past
    # DEDUP_WINDOW_DAYS daily runs. Keeps each day's picks genuinely fresh.
    today = dt.date.today()
    seen_ids: set[str] = set()
    daily_root = ROOT / "daily"
    for offset in range(1, DEDUP_WINDOW_DAYS + 1):
        prior = daily_root / (today - dt.timedelta(days=offset)).isoformat() / "items.json"
        if prior.exists():
            try:
                prior_items = json.loads(prior.read_text())
                seen_ids.update(it.get("id") for it in prior_items if it.get("id"))
            except json.JSONDecodeError:
                pass
    pre_dedup = len(raw_items)
    raw_items = [it for it in raw_items if it.id not in seen_ids]
    if pre_dedup != len(raw_items):
        logger.info(
            "dropped %d already-seen items (last %d days); %d remaining",
            pre_dedup - len(raw_items), DEDUP_WINDOW_DAYS, len(raw_items),
        )

    if not raw_items:
        logger.info("nothing fresh to score today — exiting cleanly")
        return

    item_dicts = [it.to_dict() for it in raw_items]
    scored = score_all(item_dicts, interests)
    merged = merge(item_dicts, scored)
    logger.info("scored %d items, top score = %s", len(merged), merged[0]["score"] if merged else "n/a")

    today = dt.date.today()
    picks_md = render_picks(merged, today)
    firehose_md = render_firehose(merged, today)
    write_daily(ROOT, today, picks_md, firehose_md)

    # Persist scored payload for the weekly job to roll up
    state_dir = ROOT / "daily" / today.isoformat()
    (state_dir / "items.json").write_text(json.dumps(merged, indent=2))

    write_daily_feed(ROOT)
    logger.info("wrote daily/%s/{picks.md,firehose.md,items.json} + daily/feed.xml", today.isoformat())


if __name__ == "__main__":
    main()
