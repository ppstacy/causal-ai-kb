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

## Latest digest

{% assign weeklies = site.pages | where_exp: "p", "p.path contains 'weekly/' and p.name contains '.md' and p.name != 'index.md'" | sort: 'name' | reverse %}
{% if weeklies.size > 0 %}
{% assign latest = weeklies | first %}
> **[{{ latest.title | default: latest.name | replace: '.md', '' }}]({{ latest.url | relative_url }})**
{% if latest.excerpt %}{{ latest.excerpt | markdownify }}{% endif %}

[Read the full digest →]({{ latest.url | relative_url }})
{% else %}
_The first weekly digest will publish on the next Friday after this site's
launch. Check back then._
{% endif %}

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
