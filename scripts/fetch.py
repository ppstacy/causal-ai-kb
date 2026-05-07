"""Pull items from arXiv, RSS feeds, GitHub trending, and Semantic Scholar."""

from __future__ import annotations

import datetime as dt
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Iterable

import arxiv
import feedparser
import requests
import yaml
from dateutil import parser as dateparser

logger = logging.getLogger(__name__)

UA = "causal-ai-kb/0.1 (+https://github.com/ppstacy/causal-ai-kb)"


@dataclass
class Item:
    source: str          # arxiv | rss | github | semantic_scholar
    source_name: str     # human-readable origin (e.g. "arXiv stat.ML", "Netflix Tech Blog")
    id: str              # stable identifier (arxiv id, url, repo full_name)
    title: str
    url: str
    summary: str = ""
    authors: list[str] = field(default_factory=list)
    published: str = ""  # ISO 8601 date
    extras: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in keywords)


def fetch_arxiv(cfg: dict, since: dt.datetime) -> Iterable[Item]:
    categories = cfg.get("categories", [])
    max_per = cfg.get("max_results_per_category", 80)
    keywords = cfg.get("keyword_filters", [])

    client = arxiv.Client(page_size=100, delay_seconds=3, num_retries=3)
    seen_ids: set[str] = set()

    for cat in categories:
        search = arxiv.Search(
            query=f"cat:{cat}",
            max_results=max_per,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        try:
            for result in client.results(search):
                pub = result.published.replace(tzinfo=None) if result.published else None
                if pub is None or pub < since:
                    continue
                short_id = result.get_short_id()
                if short_id in seen_ids:
                    continue
                blob = f"{result.title}\n{result.summary}"
                if not _matches_keywords(blob, keywords):
                    continue
                seen_ids.add(short_id)
                yield Item(
                    source="arxiv",
                    source_name=f"arXiv {cat}",
                    id=f"arxiv:{short_id}",
                    title=result.title.strip(),
                    url=result.entry_id,
                    summary=result.summary.strip().replace("\n", " "),
                    authors=[a.name for a in result.authors],
                    published=pub.isoformat(),
                    extras={"category": cat, "primary_category": result.primary_category},
                )
        except Exception as exc:
            logger.warning("arxiv fetch failed for %s: %s", cat, exc)


def fetch_rss(cfg: list[dict], since: dt.datetime) -> Iterable[Item]:
    for feed_cfg in cfg:
        url = feed_cfg["url"]
        name = feed_cfg["name"]
        keywords = feed_cfg.get("keyword_filter", [])
        try:
            parsed = feedparser.parse(url, agent=UA)
        except Exception as exc:
            logger.warning("rss fetch failed for %s: %s", name, exc)
            continue
        for entry in parsed.entries:
            pub_str = entry.get("published") or entry.get("updated") or ""
            try:
                pub = dateparser.parse(pub_str).replace(tzinfo=None) if pub_str else None
            except (ValueError, TypeError):
                pub = None
            if pub and pub < since:
                continue
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            summary_html = entry.get("summary", "") or entry.get("description", "")
            summary = re.sub(r"<[^>]+>", " ", summary_html).strip()
            if not _matches_keywords(f"{title} {summary}", keywords):
                continue
            yield Item(
                source="rss",
                source_name=name,
                id=f"rss:{link}",
                title=title,
                url=link,
                summary=summary[:1500],
                published=pub.isoformat() if pub else "",
            )


def fetch_github_trending(cfg: dict, since: dt.datetime) -> Iterable[Item]:
    topics = cfg.get("topics", [])
    min_stars = cfg.get("min_stars", 5)
    cutoff = since.strftime("%Y-%m-%d")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    seen: set[str] = set()
    for topic in topics:
        q = f"topic:{topic} pushed:>={cutoff} stars:>={min_stars}"
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": q, "sort": "stars", "order": "desc", "per_page": 25},
                headers=headers,
                timeout=20,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("github fetch failed for topic %s: %s", topic, exc)
            continue
        for repo in resp.json().get("items", []):
            full = repo["full_name"]
            if full in seen:
                continue
            seen.add(full)
            yield Item(
                source="github",
                source_name=f"GitHub topic:{topic}",
                id=f"github:{full}",
                title=f"{full} — {repo.get('description') or '(no description)'}",
                url=repo["html_url"],
                summary=repo.get("description") or "",
                published=repo.get("pushed_at", ""),
                extras={
                    "stars": repo.get("stargazers_count", 0),
                    "language": repo.get("language"),
                    "topic": topic,
                },
            )


def fetch_semantic_scholar(cfg: dict, since: dt.datetime) -> Iterable[Item]:
    queries = cfg.get("queries", [])
    limit = cfg.get("limit_per_query", 25)
    fields = "title,abstract,authors,url,publicationDate,externalIds,venue"
    seen: set[str] = set()
    for query in queries:
        try:
            resp = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": query, "limit": limit, "fields": fields},
                headers={"User-Agent": UA},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("semantic scholar fetch failed for %r: %s", query, exc)
            continue
        for paper in resp.json().get("data", []):
            pub_date = paper.get("publicationDate")
            try:
                pub = dateparser.parse(pub_date).replace(tzinfo=None) if pub_date else None
            except (ValueError, TypeError):
                pub = None
            if pub and pub < since:
                continue
            paper_id = paper.get("paperId") or paper.get("url") or paper.get("title")
            if not paper_id or paper_id in seen:
                continue
            seen.add(paper_id)
            yield Item(
                source="semantic_scholar",
                source_name=f"Semantic Scholar: {query}",
                id=f"s2:{paper_id}",
                title=(paper.get("title") or "").strip(),
                url=paper.get("url") or "",
                summary=(paper.get("abstract") or "").strip()[:1500],
                authors=[a.get("name", "") for a in paper.get("authors", [])],
                published=pub.isoformat() if pub else "",
                extras={"venue": paper.get("venue"), "query": query},
            )


def fetch_github_releases(cfg: dict, since: dt.datetime) -> Iterable[Item]:
    """Track new releases on canonical causal-ML libraries."""
    repos = cfg.get("repos", [])
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    for repo in repos:
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{repo}/releases",
                params={"per_page": 5},
                headers=headers,
                timeout=20,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("github releases fetch failed for %s: %s", repo, exc)
            continue
        for rel in resp.json():
            published = rel.get("published_at") or rel.get("created_at") or ""
            try:
                pub = dateparser.parse(published).replace(tzinfo=None) if published else None
            except (ValueError, TypeError):
                pub = None
            if pub and pub < since:
                continue
            tag = rel.get("tag_name", "")
            name = rel.get("name") or tag or "release"
            body = (rel.get("body") or "").strip()[:1500]
            yield Item(
                source="github_release",
                source_name=f"{repo} releases",
                id=f"ghrel:{repo}:{tag}",
                title=f"{repo} {tag} — {name}" if name != tag else f"{repo} {tag}",
                url=rel.get("html_url") or f"https://github.com/{repo}/releases",
                summary=body,
                published=pub.isoformat() if pub else "",
                extras={"repo": repo, "tag": tag, "prerelease": rel.get("prerelease", False)},
            )


def fetch_websites(cfg: list[dict]) -> Iterable[Item]:
    """Scrape arbitrary HTML pages and use Claude to extract structured events/talks/papers.

    Each entry in cfg is {name, url, type} where type is a hint like
    'seminar' or 'page' that gets passed to the extraction prompt.
    """
    if not cfg:
        return
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic not installed — skipping website extraction")
        return

    import json as _json
    import os

    client = anthropic.Anthropic()
    model = os.environ.get("CAUSAL_KB_MODEL", "claude-opus-4-7")

    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "speaker_or_authors": {"type": "string"},
                        "date": {"type": "string", "description": "ISO 8601 if known, else free-form"},
                        "url": {"type": "string", "description": "absolute URL if present, else page URL"},
                        "summary": {"type": "string"},
                    },
                    "required": ["title", "speaker_or_authors", "date", "url", "summary"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["items"],
        "additionalProperties": False,
    }

    for site in cfg:
        url = site["url"]
        name = site["name"]
        kind = site.get("type", "page")
        try:
            resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("website fetch failed for %s: %s", name, exc)
            continue
        text = re.sub(r"<script[^>]*>.*?</script>", " ", resp.text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()[:18000]

        try:
            r = client.messages.create(
                model=model,
                max_tokens=2048,
                system=(
                    f"Extract upcoming and recent {kind} entries from the page text. "
                    "Each entry should be a paper, talk, seminar, or post. "
                    "Use absolute URLs when present, otherwise the page URL itself. "
                    "Skip navigation and boilerplate. Return JSON matching the schema."
                ),
                messages=[{
                    "role": "user",
                    "content": f"Page: {name} ({url})\n\n{text}",
                }],
                output_config={"format": {"type": "json_schema", "schema": schema}},
            )
            payload = next((b.text for b in r.content if b.type == "text"), "")
            data = _json.loads(payload) if payload else {"items": []}
        except (anthropic.APIError, _json.JSONDecodeError) as exc:
            logger.warning("website extraction failed for %s: %s", name, exc)
            continue

        for entry in data.get("items", []):
            entry_url = entry.get("url") or url
            yield Item(
                source="website",
                source_name=name,
                id=f"web:{name}:{entry.get('title', '')[:80]}",
                title=entry.get("title", "").strip(),
                url=entry_url,
                summary=(entry.get("summary") or "").strip()[:1500],
                authors=[a.strip() for a in (entry.get("speaker_or_authors") or "").split(",") if a.strip()],
                published=entry.get("date", ""),
                extras={"page": url, "kind": kind},
            )


def fetch_all(sources_cfg: dict, days_lookback: int = 1) -> list[Item]:
    """Fetch from every configured source. Dedup by id."""
    since = dt.datetime.utcnow() - dt.timedelta(days=days_lookback)
    items: dict[str, Item] = {}

    fetchers = [
        ("arxiv", lambda: fetch_arxiv(sources_cfg.get("arxiv", {}), since)),
        ("rss", lambda: fetch_rss(sources_cfg.get("rss", []), since)),
        (
            "github",
            lambda: fetch_github_trending(
                sources_cfg.get("github_trending", {}),
                dt.datetime.utcnow()
                - dt.timedelta(days=sources_cfg.get("github_trending", {}).get("days_lookback", 7)),
            ),
        ),
        (
            "semantic_scholar",
            lambda: fetch_semantic_scholar(
                sources_cfg.get("semantic_scholar", {}),
                dt.datetime.utcnow()
                - dt.timedelta(days=sources_cfg.get("semantic_scholar", {}).get("days_lookback", 2)),
            ),
        ),
        ("websites", lambda: fetch_websites(sources_cfg.get("websites", []))),
        (
            "github_releases",
            lambda: fetch_github_releases(
                sources_cfg.get("github_releases", {}),
                dt.datetime.utcnow()
                - dt.timedelta(days=sources_cfg.get("github_releases", {}).get("days_lookback", 7)),
            ),
        ),
    ]
    for name, fn in fetchers:
        count = 0
        for item in fn():
            if item.id not in items:
                items[item.id] = item
                count += 1
        logger.info("fetched %d items from %s", count, name)

    return list(items.values())


def load_sources(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)
