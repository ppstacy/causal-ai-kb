"""Render scored items into daily picks/firehose markdown and weekly newsletter."""

from __future__ import annotations

import datetime as dt
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REPO_URL = "https://github.com/ppstacy/causal-ai-kb"

PICKS_PER_DAY = 5

TOPIC_LABEL = {
    "causal-inference": "Causal Inference",
    "uplift": "Uplift / HTE",
    "experimentation": "Experimentation",
    "causal-lm": "Causal LMs",
    "tools": "Tools",
    "other": "Other",
}


def _format_authors(authors: list[str], limit: int = 4) -> str:
    if not authors:
        return ""
    if len(authors) <= limit:
        return ", ".join(authors)
    return ", ".join(authors[:limit]) + f" et al. ({len(authors)} authors)"


def render_picks(items: list[dict], date: dt.date) -> str:
    """Top-N picks for the day with summaries."""
    picks = items[:PICKS_PER_DAY]
    if not picks:
        return f"# Daily picks — {date.isoformat()}\n\n_No picks today._\n"

    lines = [
        f"# Daily picks — {date.isoformat()}",
        "",
        f"Top {len(picks)} of {len(items)} items today, ranked by relevance.",
        "",
    ]
    for i, item in enumerate(picks, 1):
        topic = TOPIC_LABEL.get(item.get("topic", "other"), item.get("topic", "other"))
        authors = _format_authors(item.get("authors", []))
        lines.append(f"## {i}. [{item['title']}]({item['url']})")
        lines.append("")
        meta_bits = [f"**{topic}**", f"score {item['score']}", item["source_name"]]
        if authors:
            meta_bits.append(authors)
        lines.append(" · ".join(meta_bits))
        lines.append("")
        lines.append(item.get("llm_summary", "").strip())
        why = item.get("why_relevant", "").strip()
        if why:
            lines.append("")
            lines.append(f"_Why:_ {why}")
        lines.append("")
    return "\n".join(lines)


def render_firehose(items: list[dict], date: dt.date) -> str:
    """Full collected-and-scored list for the day."""
    if not items:
        return f"# Firehose — {date.isoformat()}\n\n_No items today._\n"

    by_topic: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_topic[item.get("topic", "other")].append(item)

    lines = [f"# Firehose — {date.isoformat()}", "", f"{len(items)} items total.", ""]
    for topic in ("causal-inference", "uplift", "experimentation", "causal-lm", "tools", "other"):
        bucket = by_topic.get(topic, [])
        if not bucket:
            continue
        lines.append(f"## {TOPIC_LABEL[topic]} ({len(bucket)})")
        lines.append("")
        for item in bucket:
            authors = _format_authors(item.get("authors", []), limit=2)
            tail = f" — {authors}" if authors else ""
            lines.append(
                f"- **[{item['score']}]** [{item['title']}]({item['url']}) "
                f"_{item['source_name']}_{tail}"
            )
        lines.append("")
    return "\n".join(lines)


def render_weekly(daily_items_by_date: dict[dt.date, list[dict]], week_label: str) -> str:
    """Roll up the past week's picks into a newsletter."""
    all_items: list[dict] = []
    for items in daily_items_by_date.values():
        all_items.extend(items)
    all_items.sort(key=lambda x: x["score"], reverse=True)

    lines = [
        f"# Weekly digest — {week_label}",
        "",
        f"Top items from the past week ({len(all_items)} scored items across "
        f"{len(daily_items_by_date)} days).",
        "",
    ]

    top_picks = all_items[:10]
    if top_picks:
        lines.append("## Top picks of the week")
        lines.append("")
        for i, item in enumerate(top_picks, 1):
            topic = TOPIC_LABEL.get(item.get("topic", "other"))
            authors = _format_authors(item.get("authors", []))
            lines.append(f"### {i}. [{item['title']}]({item['url']})")
            lines.append("")
            meta = [f"**{topic}**", f"score {item['score']}", item["source_name"]]
            if authors:
                meta.append(authors)
            lines.append(" · ".join(meta))
            lines.append("")
            lines.append(item.get("llm_summary", "").strip())
            lines.append("")

    by_topic: dict[str, list[dict]] = defaultdict(list)
    for item in all_items:
        by_topic[item.get("topic", "other")].append(item)

    lines.append("## By topic")
    lines.append("")
    for topic in ("causal-inference", "uplift", "experimentation", "causal-lm", "tools"):
        bucket = sorted(by_topic.get(topic, []), key=lambda x: x["score"], reverse=True)[:5]
        if not bucket:
            continue
        lines.append(f"### {TOPIC_LABEL[topic]}")
        lines.append("")
        for item in bucket:
            lines.append(f"- **[{item['score']}]** [{item['title']}]({item['url']})")
        lines.append("")
    return "\n".join(lines)


def write_daily(out_dir: Path, date: dt.date, picks: str, firehose: str) -> None:
    day_dir = out_dir / "daily" / date.isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)
    (day_dir / "picks.md").write_text(picks)
    (day_dir / "firehose.md").write_text(firehose)


def write_weekly(out_dir: Path, week_label: str, body: str) -> None:
    weekly_dir = out_dir / "weekly"
    weekly_dir.mkdir(parents=True, exist_ok=True)
    (weekly_dir / f"{week_label}.md").write_text(body)


def _extract_lead_paragraph(body: str, max_chars: int = 500) -> str:
    """First non-header content paragraph from the markdown body."""
    out: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if out:
                break
            continue
        out.append(stripped)
        if sum(len(x) + 1 for x in out) > max_chars:
            break
    return " ".join(out)[: max_chars + 100]


def render_feed(weekly_dir: Path, limit: int = 20) -> str:
    """Generate an RSS 2.0 feed of recent weekly digests for Slack `/feed subscribe`."""
    files = sorted(weekly_dir.glob("[0-9]*-W[0-9]*.md"), reverse=True)[:limit]

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Causal AI weekly digest"
    ET.SubElement(channel, "link").text = REPO_URL
    ET.SubElement(channel, "description").text = (
        "Weekly roundup of new research and engineering posts on causal "
        "inference, causal ML, causal language models, and online experimentation."
    )
    ET.SubElement(channel, "language").text = "en-us"

    for f in files:
        stem = f.stem  # e.g. 2026-W19
        try:
            year_s, week_s = stem.split("-W")
            year, week = int(year_s), int(week_s)
            pub_date = dt.date.fromisocalendar(year, week, 5)  # Friday
        except (ValueError, IndexError):
            continue

        body = f.read_text()
        description = _extract_lead_paragraph(body) or stem
        link = f"{REPO_URL}/blob/main/weekly/{stem}.md"

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"Causal AI weekly digest — {stem}"
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid", isPermaLink="true").text = link
        # RFC 822 / RFC 2822 — Friday 22:00 UTC = 3pm PDT (2pm PST)
        ET.SubElement(item, "pubDate").text = pub_date.strftime(
            "%a, %d %b %Y 22:00:00 +0000"
        )
        ET.SubElement(item, "description").text = description

    ET.indent(rss, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode")


def write_feed(out_dir: Path) -> None:
    weekly_dir = out_dir / "weekly"
    weekly_dir.mkdir(parents=True, exist_ok=True)
    feed_xml = render_feed(weekly_dir)
    (weekly_dir / "feed.xml").write_text(feed_xml)
