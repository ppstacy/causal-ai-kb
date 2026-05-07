# Heterogeneous Causal Learning for Effectiveness Optimization in User Marketing

- **URL:** https://arxiv.org/abs/2004.09702
- **PDF:** https://arxiv.org/pdf/2004.09702.pdf
- **Source:** arXiv (Uber)
- **Topic:** uplift
- **Saved:** seed (originally from ppstacy/paper_reading)
- **Notes (PDF):** https://github.com/ppstacy/paper_reading/blob/master/causal_inference/Heterogeneous%20causal%20learning%20for%20effectiveness.pdf
- **Annotated paper (PDF):** https://github.com/ppstacy/paper_reading/blob/master/causal_inference/Studying%20Heterogeneous%20Causal%20Learning%20for%20Effectiveness%20Optimization%20in%20User%20Marketing%20(1)_withMarginNotes.pdf

## Summary

Industry paper on applying heterogeneous causal learning (uplift / CATE
estimation) to optimize the effectiveness of user-marketing interventions.
Combines treatment-effect estimators with a downstream targeting policy
under a budget constraint.

## Why relevant

Direct precedent for the conversion-lift / ad-attribution use case: the
goal is to identify users for whom a marketing treatment causally
increases the outcome and target spend at them. The paper's stack
(meta-learners → policy → constrained optimization) is the same shape as
the production work the reader cares about.

## Keywords

uplift modeling, heterogeneous treatment effects, user marketing,
incremental targeting, meta-learner, policy learning, treatment effect
estimation, conversion lift, budget-constrained allocation
