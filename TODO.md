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

- [ ] [P1][todo] Fix `addAccis(TempCtrl='pmv')`
  - Context: Found on 2026-10-18 while checking EnergyPlus 26.2, and the same with 25.2: `genIDF` stops with `UnboundLocalError: cannot access local variable 'ComfStand_value'`, because its PMV branch calls `replace_SetAST_dynamic_lines(SetAST[0], ComfStand_value, ComfMod_value)` and these variables only exist in the loops of the temperature branch. Before `dd116ea` (2026-10-16) the branch called `get_SetAST_lines(ComfStand_value, ComfMod_value)`, with the same problem. accim 0.8.0 and 0.8.1 have it, so no output IDF can be generated with PMV control.
  - Definition of done: decide what SetAST must contain in the PMV output IDFs (probably only its base lines); a test that runs `addAccis` with `TempCtrl='pmv'`; an output IDF simulated without errors.
  - References: `accim/sim/accim_IDFgeneration.py` (`genIDF`, branch `elif TempCtrl.lower() == 'pmv'`), `tests/core/test_addaccis_setast.py`.

- [ ] [P2][todo] Check `Table` with models whose zones have several spaces
  - Context: Since 2026-10-18, accim simulates models with `Space` objects where a zone has several occupant instances (a zone of several spaces, a SpaceList that covers several spaces of a zone, a remainder space): the EMS objects of such a zone are named after the zone (`<suffix>` = zone name), while the zones with one instance keep `<Space>_<People>`. Before, these models stopped in EnergyPlus, so `Table` never read their results. `Table` finds the occupied zones of models with SpaceLists through OpenStudio conventions (spaces whose Space Type is the name of the SpaceList) and renames zone columns after spaces, which assumes one space per zone.
  - Definition of done: `Table` (and the parametric readers of hourly outputs) checked with the outputs of a model with a zone of two spaces and with a SpaceList of several spaces per zone; fixed if the zones are not found or are mixed up.
  - References: `accim/data/postprocessing/main.py` (occupied zones, around the `SPACELIST` branch), `accim/sim/apmv_setpoints.py` (`_resolve_targets`), `DEVLOG.md` (2026-10-18, "Names of the occupant instances in models with Space objects").

- [ ] [P2][todo] Deterministic order of the occupied zones in `scan_zones`
  - Context: `scan_zones` builds `occupiedZones_orig` with `list(set(...))`, so the order of the zones, and of the objects that accim creates for each zone in the output IDFs (VRF systems, thermostats, outdoor air objects), changes from one Python process to another (string hashing). The results should not change, but two runs of `addAccis` on the same model give output IDFs that differ in the order of their objects, which makes comparisons harder (on 2026-10-18 they were compared with `PYTHONHASHSEED=0`).
  - Definition of done: the zones in the order of the targets (`list(dict.fromkeys(...))`), with a test; a check that the results do not change.
  - References: `accim/sim/utils.py` (`scan_zones`).

- [ ] [P2][todo] Simulate accim with EnergyPlus 26.1
  - Context: accim accepts EnergyPlus 26.1 since 2026-10-18, but only 26.2 was installed: 26.1 was checked against its IDD and transition rules (from 25.2, only the PIU air terminals change), without simulations. The EMS change of 26.1 (EnergyPlus pull request 11409) is the one that made `InitASTvariables` necessary.
  - Definition of done: EnergyPlus 26.1 installed and the checks of the DEVLOG entry of 2026-10-18 repeated with it (or the version removed from the lists if something fails).
  - References: `DEVLOG.md` (2026-10-18, "EnergyPlus 26.1 and 26.2").

- [ ] [P2][todo] Review the branch `refactor/sim-v1` and decide what to bring to `master`
  - Context: `refactor/sim-v1` holds the old refactoring towards accim 1.0 (the "1.0.0 clean-break release": new API, modernised docstrings, documentation and notebooks, more tests, and the code review of 2026-07-19), with 36 commits from 2026-05-27 to 2026-07-19 and about 118 files changed. Development went on with 0.7.x in `master` instead (69 commits since the two split at `c03250f`), so the branch was never merged. It was kept on purpose on 2026-10-17, when the other branches were merged into `master` and deleted.
  - Definition of done: each change of the branch checked against the current `master` and marked as port, adapt or drop; the useful parts brought in small PRs with their tests; then the branch deleted.
  - References: `origin/refactor/sim-v1`; `git log c03250f..origin/refactor/sim-v1`; the CHANGELOG of that branch (1.0.0 entry).

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
