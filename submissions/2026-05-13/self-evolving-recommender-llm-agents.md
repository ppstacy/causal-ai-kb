---
title: "Self-Evolving Recommendation System: End-To-End Autonomous Model Optimization With LLM Agents"
aliases:
  - Self-Evolving Recommender YouTube
  - Autonomous ML LLM Agents YouTube
source: arXiv 2602.10226 (YouTube / Google)
arxiv: "2602.10226"
url: https://arxiv.org/abs/2602.10226
pdf: https://arxiv.org/pdf/2602.10226
authors:
  - Haochen Wang
  - Yi Wu
  - Daryl Chang
  - Li Wei
  - Lukasz Heldt
published: 2026-02-10
saved: 2026-05-13
note: "Not directly causal ML, but the agent-orchestrated Inner/Outer loop (offline hypothesis generation + online A/B validation) could be generalized to autonomously evolve uplift/HTE/incrementality models."
topic: causal-lm
tags:
  - submission
  - causal-lm
  - llm-agents
  - autonomous-ml
  - recommender-systems
  - hypothesis-generation
  - online-experimentation
  - reward-design
related:
  - "[[causal-lm]]"
  - "[[experimentation]]"
  - "[[uplift]]"
---

# Self-Evolving Recommendation System: End-To-End Autonomous Model Optimization With LLM Agents

| Field | Value |
| --- | --- |
| **Paper** | https://arxiv.org/abs/2602.10226 |
| **PDF** | https://arxiv.org/pdf/2602.10226 |
| **Source** | arXiv 2602.10226 (YouTube / Google) |
| **Authors** | Haochen Wang, Yi Wu, Daryl Chang, Li Wei, Lukasz Heldt |
| **Published** | 2026-02-10 |
| **Topic** | [[causal-lm]] (with [[experimentation]] + [[uplift]] adjacency) |

## Summary

Two-loop agent architecture that autonomously discovers, trains, and deploys
ML system improvements at YouTube scale, using Gemini-family LLMs as the
reasoning core:

- **Offline Agent (Inner Loop)** — high-throughput hypothesis generation
  scored against fast proxy metrics. The agent proposes new optimizers,
  architectures, and reward functions, runs them, and iterates.
- **Online Agent (Outer Loop)** — promotes candidates from the inner loop
  into live production and validates against delayed "north star" business
  metrics.

Agents are framed as specialized MLEs: they exhibit non-trivial reasoning,
discover novel optimization algorithms / architectures, and formulate new
reward functions targeting long-term engagement. The paper reports
successful production launches at YouTube as the existence proof.

## Why relevant

> [!note] Generalizing to causal ML
> The user's framing: not directly causal-ML, but the **Inner/Outer agent
> loop is the right shape** for autonomous evolution of an incrementality
> / uplift system. Specifically:
>
> 1. **Offline Agent → HTE-estimator hypothesis generation.** Propose new
>    meta-learners (R-, X-, DR-), new nuisance models, new feature
>    representations; score on proxy metrics like AUUC, Qini, PEHE on
>    held-out semi-simulated data or matched-cohort backtests.
> 2. **Online Agent → A/B validation against business north stars.**
>    Promote winners into ranking-budget AB tests or geo experiments;
>    validate against SSP rates and incremental revenue rather than just
>    prediction loss.
> 3. **Reward-function discovery → policy-objective design.** The paper's
>    most interesting bit. An agent that can reformulate
>    uplift-with-budget-constraint objectives, or weight short-term lift
>    vs long-term retention, would directly improve targeted-marketing
>    decisions where the right objective is itself uncertain.
>
> Closest published analogue in causal-ML is OpportunityFinder (Amazon,
> KDD CMI 2023) but that's automated *analysis*, not autonomous
> *improvement*. A YouTube-style self-evolving causal-ML system is, as
> far as I can tell, unbuilt.

## Open questions for adaptation

- How does the Online Agent handle confounding when promoted candidates
  ride on top of an existing ranker? Paper presumably assumes the A/B
  experiment cleanly identifies the lift; in causal-measurement land
  we'd want the agent itself to reason about identification.
- What's the cost-quality curve of proxy metrics for HTE? AUUC on
  semi-simulated data is a known leaky proxy (Panagopoulos 2026 raised
  exactly this — see daily 2026-05-11 pick #1).
- Reward-function discovery in a causal setting risks Goodharting the
  validation experiment — the agent could propose objectives that look
  great on the AB outcome but degrade downstream.

## Keywords

#llm-agents #autonomous-ml #recommender-systems #hypothesis-generation
#reward-design #online-experimentation #ab-testing #youtube #gemini
#offline-online-loop #policy-learning #automated-ml
