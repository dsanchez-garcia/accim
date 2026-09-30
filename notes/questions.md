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

## 2026-09-30 — Reconcile paper assumptions before simulation campaigns

- **Context**: [[../llm_project_files/experimentos_preparados/README.md|The prepared handoff]] documents source-level differences affecting the experiment counts, conditioned-area denominator, occupancy schedules and legacy metric equivalence.
- **Why it matters**: The paper must describe the actual accepted input model and comfort reference, not inherit assumptions from older scripts or label static review as simulation validation.
- **Options considered**: Review and explicitly accept the current model/catalogue, or create a separate corrected-input campaign; never force invalid combinations or silently merge incompatible checkpoints.
- **Owner**: Paper author / simulation-PC operator.
- **Status**: open; complete the handoff's pending checks and update the manuscript before publication.
