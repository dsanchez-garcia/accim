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

## 2026-10-31 — Where should the fixes of the branch reviews go: `v1.0.0` or `master`?
- Context: [[branch-reviews.md]] marks six small fixes of `refactor/sim-v1` as `port`. The five of PR 1 (the
  `parent_folder_path` of `morph_epws`, the empty baseline of `WorkspaceArtifactCleaner`, `set_problem()` without
  outputs, the error of `Table` without `idf_path`, the stale names of `using_Table.py`) were brought into the
  working tree of `v1.0.0` on 2026-10-31, with their tests, as the other fixes of the day.
- Why it matters: the other PRs of the note (objectives and `openpyxl`, the tests of sim-v1, the golden master in
  the repository) and the deletion of the refs depend on it.
- Options considered: (a) everything on `v1.0.0` before the release; (b) PR 1 on `v1.0.0`, the rest on `master`
  after the merge.
- Owner: author.
- Status: open.

## 2026-10-31 — Keep or drop the parametric integrity block of `review/refactor-sim-v1-20261024`?
- Context: That branch (local and on `origin`, not in `v1.0.0`) holds an earlier review of sim-v1, three of the
  fixes above and a block of checkpoints, owned folders and Pareto status with constraints for the parametric
  module ([[branch-reviews.md]], section 1.3). It rejects the checkpoints of the current version.
- Why it matters: the branch can only be deleted after this decision.
- Options considered: adapt the block to `v1.0.0` (with a migration of the old checkpoints), or drop it.
- Owner: author.
- Status: open.

## 2026-10-31 — Is a comfort objective independent of the control wanted in the optimisations?
- Context: The tag `archive/feat-comfort-metrics-experiment-api` adds comfort metrics computed with EMS variables,
  independent of the control. `compute_hourly_indicators` already gives the occupied hours and the same band of
  EN 16798-1 category II; only the PMV metric is missing ([[branch-reviews.md]], section 2.1).
- Why it matters: if not wanted, the whole module is dropped and the tag can be deleted after porting
  `checked_sum_results`.
- Options considered: drop the module; add the PMV indicators as an option of `compute_hourly_indicators`; port
  the EMS metrics as an objective.
- Owner: author.
- Status: open.

## 2026-10-31 — Are the setpoints of comfort standard 6 with `ComfMod` 2 right?
- Context: In `accim/sim/ems/setpoint_lines.py`, key `(6, 2)`, the heating and cooling setpoints use the same centre
  (`PMOT*0.30+25.9` with `CAT` 80, `+23.6` with 90), as in 0.x (question of the review of 2026-10-24,
  [[branch-reviews.md]], section 1.4).
- Why it matters: it may be a transcription error of the standard, which changes the results of that standard.
- Options considered: check against the source of the standard; keep as in 0.x.
- Owner: author.
- Status: open.

## 2026-10-31 — Should `add_vrf_objects` remove the ideal loads systems of the input model?
- Context: When accim adds its VRF system, `hvac/vrf.add_vrf_objects` replaces the equipment lists and connections
  but keeps the `ZoneHVAC:IdealLoadsAirSystem` objects of the model (and sets their availability on), so they are
  left unconnected and EnergyPlus reports one Severe error per run, as in 0.x ([[branch-reviews.md]], section 3).
- Why it matters: the error is harmless but confusing; removing them changes the output IDFs.
- Options considered: remove them; keep the behaviour of 0.x.
- Owner: author.
- Status: open.
