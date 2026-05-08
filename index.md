---
layout: default
title: Causal AI Weekly
---

# Causal AI Weekly

A weekly-published digest of new research, engineering posts, and tools at the
intersection of **causal inference**, **causal machine learning**, **causal
language models**, and **online experimentation**.

The KB ingests from arXiv, conference workshops, RSS feeds (engineering blogs
from Netflix, Uber, Microsoft Research, DoorDash, Booking, Spotify, Stitch
Fix, and others), GitHub trending, and Semantic Scholar. Every item is scored
by a calibrated LLM rubric for relevance to the four areas above; the top
items each day get short editorial summaries, and the most relevant of the
week land here.

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

- **RSS**: [feed.xml]({{ '/weekly/feed.xml' | relative_url }})
  — drop into any reader, or in Slack run
  `/feed subscribe https://raw.githubusercontent.com/ppstacy/causal-ai-kb/main/weekly/feed.xml`
- **Browse the archive**: [Weekly digests]({{ '/weekly/' | relative_url }})
- **About this site**: [About]({{ '/about/' | relative_url }})
