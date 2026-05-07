---
title: Heterogeneous Causal Learning for Effectiveness Optimization in User Marketing
aliases:
  - Heterogeneous Causal Learning Uber
  - HCL User Marketing
source: arXiv (Uber)
arxiv: "2004.09702"
url: https://arxiv.org/abs/2004.09702
saved: seed
created: 2026-05-06
tags:
  - submission
  - seed
  - uplift
  - meta-learner
  - policy-learning
related:
  - "[[uplift]]"
  - "[[causal-inference]]"
---

# Heterogeneous Causal Learning for Effectiveness Optimization in User Marketing

| Field | Value |
| --- | --- |
| **Paper** | https://arxiv.org/abs/2004.09702 |
| **PDF** | https://arxiv.org/pdf/2004.09702.pdf |
| **Source** | arXiv (Uber) |
| **Topic** | [[uplift]] |
| **Notes (PDF)** | [Notes from paper_reading](https://github.com/ppstacy/paper_reading/blob/master/causal_inference/Heterogeneous%20causal%20learning%20for%20effectiveness.pdf) |
| **Annotated paper** | [With margin notes](https://github.com/ppstacy/paper_reading/blob/master/causal_inference/Studying%20Heterogeneous%20Causal%20Learning%20for%20Effectiveness%20Optimization%20in%20User%20Marketing%20(1)_withMarginNotes.pdf) |

## Summary

Industry paper on applying heterogeneous causal learning (uplift / CATE
estimation) to optimize the effectiveness of user-marketing interventions.
Combines treatment-effect estimators with a downstream targeting policy
under a budget constraint.

## Why relevant

> [!note] Why this is here
> Direct precedent for the targeted-marketing / incrementality use case:
> identify users for whom a marketing treatment causally increases the
> outcome and allocate spend accordingly. The paper's stack
> (meta-learners → policy → constrained optimization) is a canonical
> pattern for production uplift systems.

## Keywords

#uplift-modeling #heterogeneous-treatment-effects #user-marketing
#incremental-targeting #meta-learner #policy-learning
#treatment-effect-estimation #conversion-lift #budget-constrained-allocation
