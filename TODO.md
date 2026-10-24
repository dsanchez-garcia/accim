# TODO

Active short-term tasks.

## Conventions

- Use priorities: `P0` (critical), `P1` (high), `P2` (normal).
- Use status tags: `todo`, `in progress`, `blocked`.
- Reference issue/PR links when available.
- When a task is completed, move the outcome to `DEVLOG.md`.

## Task template

```md
- [ ] [P1][todo] Short title
  - Context:
  - Definition of done:
  - References:
```

## Backlog

- [ ] [P1][todo] Define backlog priority rules
  - Context: Standardize entry criteria for new tasks.
  - Definition of done: A short guideline with approved P0/P1/P2 criteria.
  - References: N/A

- [ ] [P2][todo] Agree on issue and PR link format
  - Context: Avoid mixed linking styles in technical tracking files.
  - Definition of done: One convention applied in `DEVLOG.md`, `TODO.md`, and `ROADMAP.md`.
  - References: N/A

- [ ] [P1][todo] Add regression tests for multi-IDF floor-area normalization mapping
  - Context: Validate `normalize_outputs(...)` with `building_floor_area` dictionaries across multiple IDFs in post-processing outputs.
  - Definition of done: Tests verify correct per-IDF divisors and fail on missing/incorrect IDF-area mapping assumptions.
  - References: `accim/parametric_and_optimisation/analysis.py`, `tests/parametric_and_optimisation/10_test_outputs_preflight.py`

- [ ] [P1][todo] Add regression tests for normalized-unit consistency across aggregation frequencies
  - Context: Ensure normalized outputs remain coherent when moving from hourly to daily/monthly/runperiod aggregations.
  - Definition of done: Tests validate expected normalized column naming and numeric consistency after aggregation.
  - References: `accim/parametric_and_optimisation/main.py`, `accim/parametric_and_optimisation/analysis.py`

- [ ] [P1][todo] Add resilience tests for missing CSV outputs after cleanup policies
  - Context: Post-processing should fail with clear diagnostics when required simulation CSV artifacts were removed by storage policies.
  - Definition of done: Tests cover missing file paths and assert actionable error messages in hourly/output retrieval methods.
  - References: `accim/parametric_and_optimisation/main.py`, `tests/parametric_and_optimisation/test_sim_file_cleanup.py`

- [ ] [P2][todo] Deterministic order of the occupied zones in `scan_zones`
  - Context: `scan_zones` builds `occupiedZones_orig` with `list(set(...))`, so the order of the zones, and of the objects that accim creates for each zone in the output IDFs (VRF systems, thermostats, outdoor air objects), changes from one Python process to another (string hashing). The results should not change, but two runs of `addAccis` on the same model give output IDFs that differ in the order of their objects, which makes comparisons harder (on 2026-10-18 they were compared with `PYTHONHASHSEED=0`).
  - Definition of done: the zones in the order of the targets (`list(dict.fromkeys(...))`), with a test; a check that the results do not change.
  - References: `accim/sim/utils.py` (`scan_zones`).

- [ ] [P2][todo] Simulate accim with EnergyPlus 26.1
  - Context: accim accepts EnergyPlus 26.1 since 2026-10-18, but only 26.2 was installed: 26.1 was checked against its IDD and transition rules (from 25.2, only the PIU air terminals change), without simulations. The EMS change of 26.1 (EnergyPlus pull request 11409) is the one that made `InitASTvariables` necessary.
  - Definition of done: EnergyPlus 26.1 installed and the checks of the DEVLOG entry of 2026-10-18 repeated with it (or the version removed from the lists if something fails).
  - References: `DEVLOG.md` (2026-10-18, "EnergyPlus 26.1 and 26.2").

- [ ] [P1][todo] Preserve per-IDF scope throughout output selection and application
  - Context: Selection collapses identical output requests from IDFs A/B into A alone, and meter application still uses a global request list. Checkpoint/cleanup integrity and constraint-aware Pareto were implemented separately on 2026-10-24 (see `DEVLOG.md`); they do not fix this scope loss.
  - Definition of done: Retain IDF scope through discovery/selection, deduplication, variable/meter setters and preflight verification; add regression tests without EnergyPlus and integration tests with two buildings.
  - References: [Review, section 4.3](docs/refactor-sim-v1-review.md); `tests/parametric_and_optimisation/10_test_outputs_preflight.py`.

- [ ] [P1][todo] Validate single/batch EMS behavior and comfort-model invariants
  - Context: Current single paths differ in existing-HVAC resolution and Scheduled ventilation, AC-only modification assumes a mixed-mode program, and advertised CS6 modes have no setpoint assignments. Other comfort-counter and setpoint-order findings need independent numerical oracles.
  - Definition of done: Cover AC/MM, existing HVAC, schedules and occupant mappings through both entry points; validate every advertised model/mode and comfort-hour partition; resolve the CS6 formula against its scientific source before changing it.
  - References: [Review, sections 4.2 and 4.3](docs/refactor-sim-v1-review.md); `notes/questions.md`; `accim/sim/setAST_models.py`.

- [ ] [P1][todo] Replace executable IDF argument parsing without breaking generated offsets
  - Context: `get_accim_args` still evaluates IDF text with `eval`. A direct `literal_eval` substitution changes generated constant sums such as `3.5 + 1` from numbers into strings, so the historical proposal needs adaptation.
  - Definition of done: A bounded numeric-expression parser preserving required constant arithmetic and inert Erl-text fallback; reject executable calls/attributes and test that payloads are never executed; retain ACCIS/aPMV round trips and verifier numeric contracts.
  - References: [Review, section 4.2](docs/refactor-sim-v1-review.md); `accim/utils.py` (`get_accim_args`).

- [ ] [P2][todo] Adapt the remaining useful sim-v1 refactor incrementally from current code
  - Context: Review completed on 2026-10-24 against `master` at `1a2f5947` and `refactor/sim-v1` at `ef1ec593` (117/36 exclusive commits, common ancestor `c03250f`). All 36 historical commits have a port/adapt/drop disposition; three small fixes were ported on the review branch. A wholesale merge would regress current features.
  - Definition of done: Small tested changes sharing current setup/injection and combination generation behind compatible public APIs; harden/adapt goldens and repair numbered-test collection; preserve EnergyPlus 26.x, current parametric contracts and packaging. Keep CLI default until an optional API backend has end-to-end parity evidence. Do not delete the historical branch as part of the review.
  - References: [Review, sections 6-10](docs/refactor-sim-v1-review.md); `DEVLOG.md` (2026-10-24); `benchmarks/energyplus_api.py`.

- [ ] [P2][todo] Review the archived branch `feat/comfort-metrics-experiment-api` (tag `archive/feat-comfort-metrics-experiment-api`)
  - Context: Work of 2026-09-30 that was never merged: comfort metric APIs independent of the control (`accim/sim/comfort_metrics.py`, with tests), the workflows of the paper experiments inside the package (`accim/parametric_and_optimisation/paper_experiments.py` and the prepared experiment scripts) and their documentation (`docs/source/comfort_metrics.rst`, README). The branch was deleted on 2026-10-17 and kept as a tag, also on GitHub. It split from `master` at `853e9b4`, 26 commits before the `master` of that day, and part of it may overlap with the hourly indicators added later (`compute_hourly_indicators`). It also brings back the Spanish description of the module for the paper, removed from the repository on 2026-10-16: do not bring that back.
  - Definition of done: each part marked as port or drop (for example, the comfort metrics that `compute_hourly_indicators` does not cover); the useful parts brought in a PR with their tests; then the tag deleted.
  - References: `git show archive/feat-comfort-metrics-experiment-api`; `git diff --stat 853e9b4 archive/feat-comfort-metrics-experiment-api`.

- [ ] [P2][todo] Review the archived local branch `codex/paper-simple-energy` (local tag `archive/codex-paper-simple-energy`)
  - Context: Work of 2026-10-02/03, made with Codex and never published: simple energy experiments and tutorials for the paper (`examples/paper_experiments/`, with scripts, inputs and documentation pages), and agent validation reports in Spanish (`VALIDACION_*.md`, `REVISION_LAB.md`, `INSTRUCCIONES_TRASLADO.md`). The branch and its Codex worktree were deleted on 2026-10-17. The tag only exists in the local repository of the author: do not push it (avoid `git push --tags`).
  - Definition of done: decide whether any part belongs in the repository (not the agent reports) or with the files of the paper, move it there, and delete the tag.
  - References: `git show archive/codex-paper-simple-energy`; `git diff --stat 853e9b4 archive/codex-paper-simple-energy`.

- [ ] [P2][todo] Add schema-heterogeneity tests for split-by grouped outputs
  - Context: Contract is to keep realistic per-group schemas when `drop_all_empty_output_columns=True`.
  - Definition of done: Tests assert different output-column sets across groups and downstream handling expectations.
  - References: `accim/parametric_and_optimisation/main.py`, `tests/parametric_and_optimisation/10_test_outputs_preflight.py`
