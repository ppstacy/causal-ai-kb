"""Weekly entry point: roll up the last 7 days of items.json into a markdown
digest plus an RSS feed at weekly/feed.xml.

Slack delivery uses the workspace's built-in `/feed subscribe` integration
against the committed feed.xml — no bot, no token, no secret needed.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

from render import render_weekly, write_feed, write_weekly

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("weekly")

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    today = dt.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    week_label = f"{iso_year}-W{iso_week:02d}"

    items_by_date: dict[dt.date, list[dict]] = {}
    for offset in range(7):
        day = today - dt.timedelta(days=offset)
        path = ROOT / "daily" / day.isoformat() / "items.json"
        if path.exists():
            try:
                items_by_date[day] = json.loads(path.read_text())
            except json.JSONDecodeError as exc:
                logger.warning("could not parse %s: %s", path, exc)

    if not items_by_date:
        logger.info("no daily items found in the last 7 days — skipping")
        return

    body = render_weekly(items_by_date, week_label)
    write_weekly(ROOT, week_label, body)
    logger.info("wrote weekly/%s.md", week_label)

    write_feed(ROOT)
    logger.info("wrote weekly/feed.xml")


if __name__ == "__main__":
    main()
