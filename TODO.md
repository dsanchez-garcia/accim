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

- [ ] [P1][todo] Release accim 1.0.0
  - Context: Branch `v1.0.0` (refactoring to PEP 8, Python API backend), pushed to `origin/v1.0.0`, not merged.
  - Definition of done: the author reviews the branch and merges it; `CHANGELOG.md` gets the date; accim and accim-samples 1.0.0 are published as in `packaging/README.md`.
  - References: `CHANGELOG.md` (Unreleased), `DEVLOG.md` (2026-10-30).

- [ ] [P1][todo] Run the parametric example notebooks again with accim 1.0.0
  - Context: Their pages were computed with 0.8.2. In 1.0.0, `add_accis_to_idf` controls the natural ventilation of the mixed-mode models with `ZoneVentilation` objects, as `AddAccis` does (see `notes/decisions.md`), and the notebooks use such a model (`OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520*.idf`), so their results change (in the one-week tests of the session, cooling 17% to 35% lower). Only their imports were updated for 1.0.0.
  - Definition of done: the notebooks of `parametric_and_optimisation_examples` are run with 1.0.0 and exported with `docs/prepare_parametric_notebooks.py` (see `docs/README.md` §7.3), and their texts agree with the new results.
  - References: `docs/source/9_migration_guide.md` (9.3), `CHANGELOG.md` (Fixed).

- [ ] [P1][todo] ComfStand 0 and 22 in the parametric module stop EnergyPlus
  - Context: The setpoints of ComfStand 0 (ESP CTE) and 22 (INT ISO7730) are only in the branch `ComfMod == 0` of their subprograms (`SetAST_CS0_0`, `SetAST_CS22_0`), and the baseline of the models of the parametric module has `ComfMod` 2 (the default of `SetInputData`), so a plan such as `{'ComfStand': [0, 1]}` stops EnergyPlus ("Variable = 'ACST' used in expression has not been initialized!" in `SetASTnoTol`); they only work if the plan also sets `ComfMod` 0. `drop_invalid_param_combinations()` does not help: it takes `CAT` and `ComfMod` as 'n/a' for ComfStand 0, so it drops ComfStand 0 when the plan has `CAT`, and when a column is missing it skips all the remaining checks of the row (`except KeyError: continue`), so without `CAT` it keeps rows such as ComfStand 0 with `ComfMod` 3, and does not check `VentCtrl` and `HVACmode`. The same in 0.8.2 (found while fixing the numbered tests, which used `ComfStand` 0).
  - Definition of done: ComfStand 0 (and 22) work in the parametric module, and the filter checks each rule whose columns are in the plan, with tests. Options for the author: the subprograms of the comfort standards with one comfort mode set their setpoints whatever `ComfMod` is (it changes the EMS programs of all the output IDFs, not their results), or the setter of `ComfStand` sets `ComfMod` 0 for them.
  - References: `accim/sim/ems/setast.py` (`MODULAR_COMFORT_MODES`), `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py`.

- [ ] [P2][todo] The baseline of `AccimPredefModelsParamSim` is not a valid comfort model
  - Context: The wrapper sets the custom model (`ComfStand` 99, `CAT` 80, `ComfMod` 3) without its coefficients, so the heating setpoint is above the cooling one and EnergyPlus stops in any simulation of the baseline: the test simulations of `discover_available_outputs()` and of `set_output_*_to_idf(validate=True)`, and the plans without `ComfStand`, `CAT` and `ComfMod`. The same in 0.8.2.
  - Definition of done: the baseline of the wrapper simulates (for instance, with the default coefficients of the custom model, as `ParametricSimulation(parameters_type='accim custom model')` applies), with a test; or documented.
  - References: `accim/parametric_and_optimisation/main.py` (`AccimPredefModelsParamSim.__init__`), `tests/parametric_and_optimisation_full_workflow/test_02_parametric_wrapper_and_bypass.py`.

- [ ] [P2][todo] Optimisation algorithms that fail with the defaults of `run_optimisation()`
  - Context: The smoke test of the 16 algorithms (`04_test_optimization.py::test_optimization_all_algorithms`, which only logs) passes with GeneticAlgorithm, EvolutionaryStrategy, NSGAII, GDE3, MOEAD, IBEA and PESA2. The others fail: EpsMOEA, OMOPSO and EpsNSGAII need `epsilons`, and NSGAIII `divisions_outer` (options of the algorithm); SMPSO and CMAES do not work with categorical parameters (`'_Category' object has no attribute 'max_value'`); PAES gives `got multiple values for argument 'population_size'`, ParticleSwarm `'NoneType' object is not callable` and SPEA2 `list index out of range` (population of 2). The last three may be problems of the module.
  - Definition of done: the errors of PAES, ParticleSwarm and SPEA2 explained or fixed; the requirements of the others documented in `run_optimisation()`.
  - References: `accim/parametric_and_optimisation/main.py` (`run_optimisation`).

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
