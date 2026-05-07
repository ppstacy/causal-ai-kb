---
layout: default
title: About
permalink: /about/
---

# About

Causal AI Weekly is an auto-curated, hand-tuned reading list. It exists
because the four areas it covers — causal inference, causal ML, causal
language models, and online experimentation — sit between several
disciplines (statistics, ML, econometrics, applied advertising) and don't
have a single canonical news source.

## How it works

1. Every day, a GitHub Action fetches recent items from a configured set
   of sources: arXiv categories (stat.ML, stat.ME, econ.EM, cs.LG, cs.CL),
   engineering blogs via RSS, GitHub trending in topics like
   `causal-inference`, Semantic Scholar queries, and a small set of
   watched seminar / paper-list pages.

2. Every item is sent to a calibrated LLM rubric that scores
   relevance 0–100 against four clearly-defined areas, and assigns a
   primary topic tag and a short why-relevant note. The system prompt is
   prompt-cached, so the marginal cost is roughly the abstract length.

3. The top five items each day get a 2–3 sentence editorial summary;
   everything scored gets listed in a "firehose" archive.

4. Each Friday afternoon a weekly digest is rolled up from the day-level
   data and published here, plus to an RSS feed that any reader (or
   Slack `/feed subscribe`) can consume.

## Source code

The full pipeline is open: [github.com/ppstacy/causal-ai-kb](https://github.com/ppstacy/causal-ai-kb).
Sources, the scoring rubric, and the watched-author list live as YAML
files under `config/`. PRs welcome if you want to suggest sources or
authors to track.

## Why "Causal AI" as the umbrella

The four areas aren't usually grouped under one name in academia. In
industry, **Causal AI** has emerged as a workable umbrella that covers
causal inference, causal ML, and causal applications of large language
models. Online experimentation sits naturally alongside, since
randomized experiments are how most of us actually generate the
identification we then estimate from.
