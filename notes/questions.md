---
title: Open questions
type: log
tags: [vault, questions]
created: 2026-09-13
---

# Open questions

Pending questions or blockers that need a human decision. Newest first.
Move a question to [[decisions.md]] once it is resolved (and delete or mark
it here as answered).

## How to use this file

```md
## YYYY-MM-DD — Short question
- Context:
- Why it matters:
- Options considered:
- Owner:
- Status: open | answered (see [[decisions.md]])
```

## Open

## 2026-10-24 — Confirm the CS6 heating relation and supported comfort modes

- **Context**: The sim-v1 review found advertised CS6 modes without setpoint assignments and a heating/cooling inversion in the generated CM2 formulas. Evidence and exact source references are in [[../docs/refactor-sim-v1-review.md]]; follow-up implementation is tracked in [[../TODO.md]].
- **Why it matters**: Choosing coefficients changes scientific results. Golden comparisons against the same generator cannot establish which relation is correct.
- **Options considered**: Verify the published model and implement its supported modes with independent numerical tests; explicitly reject unsupported combinations until validated. Do not infer the correct formula solely from a neighbouring code branch.
- **Owner**: Maintainer/domain expert.
- **Status**: open; no comfort formula was changed in this review.
