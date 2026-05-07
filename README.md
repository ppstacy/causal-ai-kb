# causal-ai-kb

Daily-refreshed knowledge base covering **causal inference, causal ML, causal
LMs, and online experimentation**. Scrapes ~30 sources, scores everything
against a personal interest profile with Claude, commits the top 5 picks plus
a full firehose, and posts a weekly digest to Slack.

## How it works

```
       ┌────────── arXiv ──────────┐
       │  stat.ML / stat.ME /      │
       │  econ.EM / cs.LG / cs.CL  │
       └───────────────────────────┘
       ┌─── RSS (Netflix, Uber, ──┐         ┌──────────────────┐
       │   Microsoft, Spotify,    │ ──────► │  Claude scoring  │
       │   DoorDash, Booking, …)  │         │  (cached profile │ ────► daily/<date>/
       └──────────────────────────┘         │   + rubric)      │       ├── picks.md  (top 5)
       ┌─── GitHub trending ──────┐ ──────► │                  │       └── firehose.md
       │   topics: causal-*, …    │         └──────────────────┘
       └──────────────────────────┘
       ┌─── Semantic Scholar ─────┐                                     weekly/<YYYY-Www>.md
       │   queries + tracked     │                                     └─► Slack (Fri 3pm PT)
       │   authors               │
       └──────────────────────────┘
       ┌─── Watched websites ─────┐
       │   OCIS seminar, …        │
       └──────────────────────────┘
       ┌─── User submissions ─────┐
       │   inbox URLs (LinkedIn,  │
       │   blog posts, etc.)      │
       └──────────────────────────┘
```

## Layout

```
config/
  sources.yaml            # what to fetch from
  interests.yaml          # reader profile + scoring rubric + tracked authors
  learned_keywords.yaml   # auto-extended from saved URLs
scripts/
  fetch.py                # arxiv, rss, github, semantic scholar, websites
  score.py                # Claude scoring with prompt caching
  render.py               # markdown rendering
  slack_post.py           # Slack webhook poster
  ingest_url.py           # one-shot URL → submission + keyword learning
  daily.py                # daily entry point
  weekly.py               # weekly entry point
daily/<YYYY-MM-DD>/
  picks.md                # top 5 deep-dive picks
  firehose.md             # full collected list, grouped by topic
  items.json              # scored payload (used by weekly)
weekly/<YYYY-Www>.md      # weekly digest
submissions/<YYYY-MM-DD>/ # user-saved URLs
topics/                   # topic README stubs
.github/workflows/
  daily.yml               # cron: every day 13:00 UTC (06:00 PT)
  weekly.yml              # cron: Friday 22:00 UTC (15:00 PDT / 14:00 PST)
  ingest.yml              # workflow_dispatch + repository_dispatch
```

## Setup

1. **Create the repo** on GitHub (`ppstacy/causal-ai-kb`), then push:

   ```bash
   cd ~/path/to/causal-ai-kb
   git init && git add . && git commit -m "initial scaffold"
   git branch -M main
   git remote add origin https://github.com/ppstacy/causal-ai-kb.git
   git push -u origin main
   ```

2. **Add one repo secret** (Settings → Secrets and variables → Actions):

   - `ANTHROPIC_API_KEY` — personal Anthropic key from console.anthropic.com

   No Slack secret. Slack delivery uses the workspace's built-in
   `/feed subscribe` against the committed `weekly/feed.xml` (see
   "Weekly Slack delivery" below) — no bot, no token, no IT approval.

3. **Trigger a first run** manually to verify (Actions → Daily refresh →
   Run workflow). The schedule will then take over.

## Weekly Slack delivery

The `weekly.yml` GitHub Action runs Friday 21:30 UTC (2:30 PM PDT) and
generates two committed artifacts:

- `weekly/<YYYY-Www>.md` — the human-readable digest
- `weekly/feed.xml` — RSS 2.0 feed listing the most recent 20 digests

Slack delivery uses the workspace's built-in **`/feed subscribe`**
integration. **One-time setup:** in `#causal-ai`, run

```
/feed subscribe https://raw.githubusercontent.com/ppstacy/causal-ai-kb/main/weekly/feed.xml
```

Slack polls that URL every ~10–30 minutes and auto-posts a card with
the new digest's title + lead paragraph + link whenever a new entry
appears. No bot, no token, no IT approval, no repo secret.

To change destination channel: re-run `/feed subscribe …` in the new
channel and `/feed remove …` in the old one. To stop entirely:
`/feed remove` with the URL.

## Editing what gets fetched

- **Add a blog/RSS feed:** add to `rss:` in `config/sources.yaml` with
  optional `keyword_filter` to keep noise out.
- **Add an arXiv keyword filter:** edit `arxiv.keyword_filters`. Items must
  hit at least one keyword to make it through.
- **Add a tracked author:** add to `interests.yaml` `tracked_authors:` —
  anything by them is floored at score 80. Also add a Semantic Scholar
  query in `sources.yaml` to widen coverage.
- **Add a watched website (e.g. seminar pages):** add to `websites:` in
  `sources.yaml`. Claude scrapes the page and extracts structured items.

## Saving URLs (LinkedIn, Twitter, blog posts, etc.)

LinkedIn's saved-posts page is behind a login wall and can't be scraped,
so submit individual URLs as you save them. Three ways:

**1. From your phone (mobile-friendly):**
GitHub Actions → "Ingest URL" → Run workflow → paste URL + optional note.

**2. From terminal:**

```bash
python scripts/ingest_url.py "https://www.linkedin.com/posts/..." "doubly robust ad attribution"
```

**3. Slack slash command** (one-time setup):

Create a Slack app with a slash command (`/track`) that POSTs to a small
forwarder (Cloudflare Worker, Vercel function, etc.) which calls GitHub's
`repository_dispatch` API:

```http
POST https://api.github.com/repos/ppstacy/causal-ai-kb/dispatches
Authorization: token <github PAT with repo scope>
Content-Type: application/json

{"event_type": "ingest_url",
 "client_payload": {"url": "<url>", "note": "<text>"}}
```

The `ingest.yml` workflow is already wired to listen for this event.

**What ingestion does:**
1. Fetches the page, extracts text
2. Asks Claude to summarize, score, tag, and extract 5–10 substantive
   keywords ("switchback experiments", "doubly robust estimator", etc.)
3. Saves a markdown record under `submissions/<date>/`
4. Appends new keywords to `config/learned_keywords.yaml` — the next
   daily fetch uses them, so you start surfacing similar content
   automatically.

## Cost notes

Scoring uses `claude-opus-4-7` with prompt caching on the interests profile,
so the system prompt only pays the write cost on the first batch each run.
Per item the variable cost is small (~1–3K tokens of abstract + the
JSON-schema overhead). To trade quality for cost, set
`CAUSAL_KB_MODEL=claude-haiku-4-5` as a repo variable — works the same way.

## Using as an Obsidian vault

The repo is also a working Obsidian vault. Clone it and open the directory
in Obsidian — `.obsidian/` config is checked in so the graph view, tag
pane, and backlinks work out of the box.

What you get:

- **Graph view** with color-coded nodes by tag (`#topic`, `#weekly`,
  `#daily`, `#submission`)
- **Backlinks** between weekly digests, topic pages, and submissions
  (links use standard markdown so both Obsidian and the public Pages site
  render them)
- **Tags**: every auto-generated note carries semantic tags
  (`#daily`, `#picks`, `#weekly`, `#causal-inference`, etc.)
- **Aliases**: short forms for quick `[[wikilink]]` autocomplete
- **Callouts**: "Why relevant" sections render as styled callouts
  (`> [!note]`)

`.obsidian/workspace.json` and the plugins dir are gitignored so personal
layout state stays per-machine.

## Tuning

After a week, look at items scored 60–80 and decide whether you want them
in or out. If `topic` tags drift, edit the rubric in `interests.yaml`.
The Claude system prompt is built from that file at every run, so changes
take effect on the next cron tick.
