"""Render scored items into daily picks/firehose markdown and weekly newsletter."""

from __future__ import annotations

import datetime as dt
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REPO_URL = "https://github.com/ppstacy/causal-ai-kb"
PAGES_URL = "https://ppstacy.github.io/causal-ai-kb"

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


def _frontmatter(**fields) -> str:
    """Render a YAML frontmatter block. Handles strings, lists, and dates."""
    lines = ["---"]
    for k, v in fields.items():
        if v is None or v == "":
            continue
        if isinstance(v, list):
            if not v:
                continue
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def render_picks(items: list[dict], date: dt.date) -> str:
    """Top-N picks for the day with summaries."""
    picks = items[:PICKS_PER_DAY]
    fm = _frontmatter(
        layout="default",
        title=f"Daily picks — {date.isoformat()}",
        permalink=f"/daily/{date.isoformat()}/",
        date=date.isoformat(),
        aliases=[f"Picks {date.isoformat()}"],
        tags=["daily", "picks"],
    )
    if not picks:
        return f"{fm}# Daily picks — {date.isoformat()}\n\n_No picks today._\n"

    lines = [
        fm.rstrip("\n"),
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
        lines.append("")

    # "Also worth checking" — items 6 onward, scored by relevance, no full
    # summary. Caps at 25 to keep the page readable; full firehose still
    # has everything.
    rest = items[PICKS_PER_DAY:][:20]
    if rest:
        lines.append("---")
        lines.append("")
        lines.append("## Also worth checking")
        lines.append("")
        for item in rest:
            topic = TOPIC_LABEL.get(item.get("topic", "other"), item.get("topic", "other"))
            authors_short = _format_authors(item.get("authors", []), limit=2)
            tail = f" — {authors_short}" if authors_short else ""
            lines.append(
                f"- **[{item['score']}]** [{item['title']}]({item['url']}) "
                f"— *{topic}* · {item['source_name']}{tail}"
            )
        lines.append("")
        lines.append(f"_Browse the full {len(items)}-item firehose: [firehose.md]"
                     f"({REPO_URL}/blob/main/daily/{date.isoformat()}/firehose.md)._")
        lines.append("")
    return "\n".join(lines)


def render_firehose(items: list[dict], date: dt.date) -> str:
    """Full collected-and-scored list for the day."""
    fm = _frontmatter(
        title=f"Firehose — {date.isoformat()}",
        date=date.isoformat(),
        tags=["daily", "firehose"],
    )
    if not items:
        return f"{fm}# Firehose — {date.isoformat()}\n\n_No items today._\n"

    by_topic: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_topic[item.get("topic", "other")].append(item)

    lines = [fm.rstrip("\n"), f"# Firehose — {date.isoformat()}", "", f"{len(items)} items total.", ""]
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

    fm = _frontmatter(
        layout="default",
        title=f"Weekly digest — {week_label}",
        permalink=f"/weekly/{week_label}/",
        aliases=[f"Weekly {week_label}"],
        tags=["weekly", "digest"],
    )

    lines = [
        fm.rstrip("\n"),
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


def _extract_picks_summary(body: str, max_picks: int = 3, max_chars: int = 1500) -> str:
    """Pull the top-N pick titles + meta from a picks/digest markdown body
    so the RSS feed `<description>` (and therefore the Slack card preview)
    contains the actual headlines, not just an intro sentence."""
    import re
    lines = body.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                start = j + 1
                break
    body_text = "\n".join(lines[start:])

    # Match `## N. [title](url)` followed by the meta line (e.g.
    # "**Topic** · score 88 · arXiv stat.ME · Susan Athey").
    pattern = re.compile(
        r'^## (\d+)\. \[([^\]]+)\]\(([^)]+)\)\s*\n\s*\n([^\n]+)',
        re.MULTILINE,
    )
    out: list[str] = []
    for m in pattern.finditer(body_text):
        idx = m.group(1)
        title = m.group(2).strip()
        meta = m.group(4).strip()
        # Strip markdown bold/italic from meta for plain-text RSS
        meta = re.sub(r"\*+", "", meta)
        # Truncate over-long titles (some GitHub repo "titles" are paragraph length)
        if len(title) > 130:
            title = title[:130].rsplit(" ", 1)[0] + "…"
        out.append(f"{idx}. {title} — {meta}")
        if int(idx) >= max_picks:
            break
    text = "\n".join(out)
    return text[:max_chars]


def _extract_lead_paragraph(body: str, max_chars: int = 500) -> str:
    """First non-header content paragraph from the markdown body, skipping YAML frontmatter."""
    lines = body.splitlines()
    # Skip YAML frontmatter if present
    start = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                start = j + 1
                break
    out: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(">"):
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
        description = (
            _extract_picks_summary(body, max_picks=5)
            or _extract_lead_paragraph(body)
            or stem
        )
        link = f"{PAGES_URL}/weekly/{stem}/"

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


def render_daily_feed(daily_dir: Path, limit: int = 21) -> str:
    """Generate an RSS 2.0 feed of recent daily picks for Slack `/feed subscribe`."""
    pick_files: list[tuple[str, Path]] = []
    if daily_dir.exists():
        for sub in sorted(daily_dir.iterdir(), reverse=True):
            if not sub.is_dir():
                continue
            picks = sub / "picks.md"
            if picks.exists():
                pick_files.append((sub.name, picks))
            if len(pick_files) >= limit:
                break

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Causal AI daily picks"
    ET.SubElement(channel, "link").text = REPO_URL
    ET.SubElement(channel, "description").text = (
        "Top-5 daily picks from new research, engineering posts, and tools "
        "across causal inference, causal ML, causal language models, and "
        "online experimentation."
    )
    ET.SubElement(channel, "language").text = "en-us"

    for date_str, path in pick_files:
        try:
            pub = dt.date.fromisoformat(date_str)
        except ValueError:
            continue
        body = path.read_text()
        description = (
            _extract_picks_summary(body, max_picks=5)
            or _extract_lead_paragraph(body)
            or f"Daily picks for {date_str}"
        )
        link = f"{PAGES_URL}/daily/{date_str}/"
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"Causal AI daily picks — {date_str}"
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid", isPermaLink="true").text = link
        # Daily run targets 13:00 UTC = 06:00 PT
        ET.SubElement(item, "pubDate").text = pub.strftime(
            "%a, %d %b %Y 13:00:00 +0000"
        )
        ET.SubElement(item, "description").text = description

    ET.indent(rss, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode")


def write_daily_feed(out_dir: Path) -> None:
    daily_dir = out_dir / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    feed_xml = render_daily_feed(daily_dir)
    (daily_dir / "feed.xml").write_text(feed_xml)
