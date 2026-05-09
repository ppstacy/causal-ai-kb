---
layout: default
title: Causal AI
---

# Causal AI

A daily-curated knowledge base of new research, engineering posts, and
tools at the intersection of **causal inference**, **causal machine
learning**, **causal language models**, and **online experimentation**.

Two cadences:

- **Daily picks** — top 5 every weekday morning, plus a longer "also worth
  checking" list. [Browse the daily archive]({{ '/daily/' | relative_url }}).
- **Weekly digest** — published every Friday afternoon, rolling up the
  week's picks. [Browse the weekly archive]({{ '/weekly/' | relative_url }}).

The KB ingests from arXiv (with abstract-level keyword filtering),
conference / workshop pages (KDD CMI, NeurIPS, ICML, AISTATS), RSS feeds
(engineering blogs from Netflix, Uber, Microsoft Research, DoorDash,
Booking, Spotify, Stitch Fix; industry-trend feeds like DeepLearning.AI,
The Gradient, Stanford HAI, BAIR), GitHub trending (newly created repos)
and releases of canonical libraries (DoWhy, EconML, CausalML, GeoLift,
CausalPy, …), and Semantic Scholar paper search. Every item is scored
for relevance and tagged by topic.

## Latest

{% assign dailies = site.pages | where_exp: "p", "p.path contains '/daily/'" | where_exp: "p", "p.path contains '/picks.md'" | sort: 'path' | reverse %}
{% if dailies.size > 0 %}
{% assign latest_daily = dailies | first %}
- **Today's picks** — [{{ latest_daily.date | default: latest_daily.title }}]({{ latest_daily.url | relative_url }})
{% endif %}

{% assign weeklies = site.pages | where_exp: "p", "p.path contains 'weekly/'" | where_exp: "p", "p.name contains '-W'" | sort: "name" | reverse %}
{% if weeklies.size > 0 %}
{% assign latest = weeklies | first %}
- **Latest weekly digest** — [{{ latest.title | default: latest.name | replace: '.md', '' }}]({{ latest.url | relative_url }})
{% else %}
- _The first weekly digest publishes on the next Friday._
{% endif %}

Browse [daily picks]({{ '/daily/' | relative_url }}) and [weekly archive]({{ '/weekly/' | relative_url }}).

## Topics

- [Causal Inference]({{ '/topics/causal-inference/' | relative_url }}) — CATE, DML, IV, RDD, DiD, propensity methods, sensitivity analysis
- [Uplift / HTE]({{ '/topics/uplift/' | relative_url }}) — meta-learners, conformal HTE, policy learning, incrementality
- [Experimentation]({{ '/topics/experimentation/' | relative_url }}) — A/B testing, variance reduction, sequential testing, geo experiments
- [Causal LMs]({{ '/topics/causal-lm/' | relative_url }}) — counterfactual reasoning in LLMs, causal discovery via language models

## Subscribe

In the Slack channel where you want delivery (or DM `@Slackbot` for a
DM-only feed), paste these — copy-paste exactly:

**Daily picks** (top 5 each weekday):

```
/feed subscribe https://raw.githubusercontent.com/ppstacy/causal-ai-kb/main/daily/feed.xml
```

**Weekly digest** (Friday afternoon roll-up):

```
/feed subscribe https://raw.githubusercontent.com/ppstacy/causal-ai-kb/main/weekly/feed.xml
```

Each feed entry's preview includes the top picks inline, so the Slack
card shows the headlines without click-through. The link goes to the
rendered page on this site.

To unsubscribe later, run `/feed list` in the same channel and
`/feed remove <URL>` for the one you want to stop. To pull the feed
into a desktop reader (Reeder, NetNewsWire, Feedly), use the same URLs.

[About this site →]({{ '/about/' | relative_url }})
