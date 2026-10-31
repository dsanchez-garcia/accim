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

## 2026-10-31 — Keep or drop the parametric integrity block of `review/refactor-sim-v1-20261024`?
- Context: That branch (local and on `origin`, not in `v1.0.0`) holds an earlier review of sim-v1, three of the
  fixes of PR 1 (already in `v1.0.0`) and a block of checkpoints, owned folders and Pareto status with constraints
  for the parametric module ([[branch-reviews.md]], section 1.3). It rejects the checkpoints of the current version.
- Why it matters: the branch can only be deleted after this decision.
- Options considered: adapt the block to `v1.0.0` (with a migration of the old checkpoints), or drop it.
- Recommendation (2026-10-31, asked by the author): adapt only two parts, which fix real problems without changing
  how the module is used, and drop the rest. (1) The Pareto status with constraints: `_annotate_pareto_status`
  only compares the objectives, so with constraints an evaluation that does not meet them can be marked
  `pareto-optimal` (no example uses constraints); the branch has a constraint-first dominance, as Platypus
  (`_pareto.py`, 67 lines, with `test_constraint_pareto.py`). (2) The identity of the parametric checkpoints: a
  resumed run skips the tasks whose signature (IDF name, EPW and parameters) is in the checkpoint, so after
  changing the model, the EPW or the outputs under the same names it reuses the old rows; with a hash of the
  contents of the IDF and the EPW, and the names of the outputs, in the signature, those rows are simulated again
  (the rows of old checkpoints too, so nothing needs a migration). Drop the versioned checkpoint files, the owned
  run folders and locks, the cleanup of owned paths (`v1.0.0` already deletes only what appeared after the
  snapshot of `WorkspaceArtifactCleaner`), the patches, the benchmarks and the documentation page, which would
  rewrite a large part of `main.py`. Then delete the branch, locally and on `origin` (after keeping
  `docs/refactor-sim-v1-review.md` outside the repository, if wanted).
- Owner: author.
- Status: open (recommendation given; waiting for the author).

## 2026-10-31 — Is a comfort objective independent of the control wanted in the optimisations?
- Context: The tag `archive/feat-comfort-metrics-experiment-api` adds comfort metrics computed with EMS variables,
  independent of the control. `compute_hourly_indicators` already gives the occupied hours and the same band of
  EN 16798-1 category II; only the PMV metric is missing ([[branch-reviews.md]], section 2.1).
- Why it matters: if not wanted, the whole module is dropped and the tag can be deleted after porting
  `checked_sum_results`.
- Options considered: drop the module; add the PMV indicators as an option of `compute_hourly_indicators`; port
  the EMS metrics as an objective.
- Recommendation (2026-10-31, asked by the author): a comfort objective independent of the control is worth having,
  but not with the EMS module of the tag. When an optimisation changes the comfort model (the coefficients of the
  custom model, or of the aPMV setpoints), the comfort hours of accim follow that same model, and WF4 and WF5
  minimise the mean operative temperature instead, so their solutions can save energy by being uncomfortable (the
  solutions that TOPSIS picks in WF4 have about 30 °C on average). EnergyPlus already computes, in every model of
  accim, the adaptive comfort of ASHRAE 55 (80 and 90 % acceptability) and of CEN 15251 (categories I to III) for
  each `People` object, since accim always adds these comfort models to them: `Zone Thermal Comfort CEN 15251
  Adaptive Model Category II Status` is 1 inside the category, 0 outside and -1 when the zone is empty or the
  running mean is out of range (`ThermalComfort.cc`), so
  it measures comfort against a fixed model. A small reducer in `objectives.py` (occupied hours outside the
  category, from those variables at timestep frequency) and an example would give that objective, without new EMS
  programs, outputs in the IDFs or work for the API backend. Leave the PMV indicators of
  `compute_hourly_indicators` for when a study needs them (they need the Fanger model, which accim only adds with
  `temp_ctrl='pmv'`). Then delete the tag, locally and on GitHub (`checked_sum_results` and `openpyxl` are already
  in `v1.0.0`).
- Owner: author.
- Status: open (recommendation given; waiting for the author).
