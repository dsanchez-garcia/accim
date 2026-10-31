---
title: Reviews of refactor/sim-v1 and of the archived tags
tags: [vault, review, branches]
created: 2026-10-31
---

# Reviews of `refactor/sim-v1` and of the archived tags

Review part of three P2 items of [[../TODO.md#Backlog|the backlog]]: the branch `refactor/sim-v1`, the tag
`archive/feat-comfort-metrics-experiment-api` and the local tag `archive/codex-paper-simple-energy`.

- **Compared against**: the working tree of `v1.0.0` on 2026-10-31 (`1ba4e34c` plus the uncommitted changes of
  that day), not the old `master` (`1a2f5947`, 0.8.2). What 1.0.0 contains: [[../CAMBIOS_CODIGO_v1.0.0.md]],
  [[../CHANGELOG.md]] (Unreleased) and [[../docs/source/9_migration_guide.md]].
- **Method**: read-only git (`log`, `show`, `diff`, `ls-tree`) and searches of the working tree. No test was run;
  nothing was ported, merged or deleted. The marks are proposals for the author.
- **State in v1.0.0**: covered / partly covered / missing / not applicable.
- **Mark**: `port` (bring the change as it is, with its test), `adapt` (keep the intent, rewrite it for the
  modules and names of 1.0.0), `drop` (superseded, paper-specific or not wanted). For the Codex tag, `paper` means
  keep it with the paper files (`llm_project_files/`, git-ignored), outside the repository.
- Paths without a ref are in the `v1.0.0` working tree (line numbers of 2026-10-31); the files of a reviewed ref
  can be read with `git --no-pager show <ref>:<path>`.
- **How to use**: read the summary line of each section; the last section orders the PRs and the deletion of the
  refs, and lists the decisions that need the author.

**State (2026-10-31, after the answers of the author)**: the author chose to bring everything to `v1.0.0` before the
release ([[decisions.md]]), and PRs 1 to 4 below were done that day: the five fixes of PR 1; `checked_sum_results`
and `openpyxl` (PR 2); the tests of sim-v1 adapted to `tests/core`, with the repair of
`Table.wrangled_table(reshaping='pivot')` (PR 3); and the golden master of the output IDFs in
`tests/core/golden_master`, with `tools/compare_backends.py` (PR 4). The orphan ideal loads systems with VRF are
removed (section 3), and the setpoints of CS6 with `ComfMod` 2 stay as in 0.x until a later check (a TODO item).
The author then chose the two recommendations of [[questions.md]]: of the integrity block of
`review/refactor-sim-v1-20261024` (section 1.3), only the Pareto status with constraints and the identity of the
parametric checkpoints were adapted; and the comfort objective independent of the control comes from the adaptive
comfort status of EnergyPlus (two reducers of `objectives.py`), not from the EMS module of the comfort-metrics tag
(section 2). No ref has been deleted yet: `refactor/sim-v1`, `review/refactor-sim-v1-20261024` and the two tags
wait for the confirmation of the author.

## 1. Branch `refactor/sim-v1`

`refactor/sim-v1` = `origin/refactor/sim-v1` = `ef1ec593`: 36 commits since `c03250f`, 118 files (+8419/-5960).
**Recommendation: do not merge.** v1.0.0 re-did the same refactoring with other module and argument names, and with
deprecated aliases instead of a clean break, so the production code is superseded except for six small fixes.
Port those, adapt five groups of tests, drop the rest, then delete the branch. **20 items: 6 port, 5 adapt, 9 drop.**

### 1.1 Changes

| Item | Area / files | State in v1.0.0 | Mark | Reason |
| --- | --- | --- | --- | --- |
| `35a272e2`, `8c3b52d1`, `6c1cb805`, `48f7e9e3` Golden-file characterization of `accim.sim` | `tests/sim/_golden.py`, `test_characterization_batch.py`, `test_characterization_single.py`, 14 gzip goldens, `tests/conftest.py` (`--update-golden`) | partly covered | adapt | v1.0.0 checked 29 configurations against 0.8.2 with a golden master kept outside the repository (CAMBIOS, section 11). Reuse only the harness (`--update-golden`, `gzip(mtime=0)`) to bring it in: goldens regenerated with v1.0.0, exact comparison (outputs are deterministic now and the order of the calling managers matters), failure when a golden is missing |
| `35a272e2`, `ff94c014` Known bugs as `xfail` | `tests/sim/test_known_bugs.py`: PMV in `AddAccis`, single path with `ex_*` | covered | drop | Both work in v1.0.0: `test_generation.py::test_pmv_control_has_one_output_idf_and_the_name_suffix`, `test_addaccis_setast.py::test_pmv_output_idf_has_only_the_base_lines_of_setast`; `add_accis_to_idf` builds an `AccimModel` for every script type |
| `ff94c014`, `07da26c8`, `76b62e77`, `50db30f3` One engine for files and IDF objects | `engine.py`, `batch.py`, `single.py` (`AccimJob.apply_accis`), dead code, mutable default arguments | covered | drop | `model.AccimModel` with `build.add_accis_objects` and `build.add_outputs` serve both `AddAccis` and `add_accis_to_idf`; `accim_Main_single_idf.py` is gone; no mutable defaults left in `accim/sim` |
| `4b7b6fd1`, `ab1faff4`, `6dea3cc4` Module split and PEP 8 internals | `engine`, `batch`, `single`, `idf_generation`, `ems/`, `hvac/`; re-exports in `accim/sim/__init__.py`; committed `__pycache__/*.pyc` | covered | drop | Other module map in v1.0.0 (`accis`, `model`, `build`, `generation`, `ems/`, `hvac/`...); `accim/sim/__init__.py` exports `AddAccis`, `add_accis_to_idf`, `modify_accis`, `gen_outputs_df` lazily (`apply_apmv_setpoints` stays in `accim.sim.apmv`); the `.pyc` files are noise |
| `539d7ae8`, `9acc2589` Clean-break public names | arguments `comfort_standard`, `category`, `comfort_mode`, `vent_control`, `temp_control`, `verbose`, `confirm_generation`; class `AddAccisToIdf`, function `add_accis`; no aliases | covered (other names) | drop | v1.0.0 uses `comf_stand`, `cat`, `comf_mod`, `vent_ctrl`, `temp_ctrl`, `verbose_mode`, `confirm_gen` and `add_accis_to_idf`, and keeps the 0.x names as deprecated aliases (`arguments.LEGACY_ARGUMENT_NAMES`, `accim/_deprecation.py`); a third set of names would confuse users |
| `5a84769b` Prompts isolated in `accim.sim.prompts` | `prompts.py`, `idf_generation.py`; `tests/sim/test_prompts.py` (scripted answers, retry after an invalid answer) | partly covered | adapt | Code covered by `prompts.ask_model_arguments` and `ask_generation_arguments` (with an injectable `ask`); `test_addaccis_arguments.py` only checks the supply air method, the empty accuracy and the name suffix. Port the scripted-answer and retry tests to the v1.0.0 functions |
| `b172cdce`, `0848b189`, `c68eb1c9` Release of the clean-break 1.0.0 | `accim/__init__.py` version, `MIGRATION.md`, README, CHANGELOG 1.0.0 entry | covered | drop | `__version__ = '1.0.0'`, `docs/source/9_migration_guide.md`, README and CHANGELOG (Unreleased) describe the 1.0.0 that will be released |
| `e53d246e`, `d9144407`, `b43b2fa3`, `efc91e23` Samples, notebooks, docstrings and docs to the 1.0 API | `script_usage/*.py`, How-to notebooks (docs and `sample_files`), docstrings, `docs/source/api/accim.sim.rst`, quick tutorial, detailed use, troubleshooting | covered | drop | Redone in v1.0.0 (`7e9dfc1b`, `ae581501`, `0c59b2db`) with its own names; the sim-v1 texts use names that v1.0.0 does not have |
| `c43d1294` (sample) Stale names in the `Table` sample script | `accim/sample_files/script_usage/using_Table.py`: `scatter_plot_adap_vs_stat`, column `Category` | missing | port | Still stale in v1.0.0 (lines 207, 280, 287, 299, 355, 403, 422): the method is `Table.scatter_plot_with_baseline` and the column is `CAT` |
| `2ff043c2` (1/2) Clear error when `Table` has no `idf_path` | `accim/data/postprocessing/main.py`, `tests/data/test_table_fixes.py` | missing | port | `Table.__init__` still calls `get_building(idf_path)` with `None` (`main.py:871`) and fails with an unclear `AttributeError` |
| `2ff043c2` (2/2) `Table.wrangled_table(reshaping='pivot')` | `index=self.indexcols.remove('col_to_pivot')` passes `None` to `pivot_table` | missing | adapt | Bug still at `main.py:2021`. The sim-v1 one-line fix does not make the pivot path work (it leaves `col_to_pivot` in `indexcols`, and the later comparisons expect other column names; see section 4.1 of the 2026-10-24 review, section 1.3 below): repair the whole path, with a test |
| `24def6c7` (code) matplotlib 3.6+ in the `Table` plots | `get_shared_y_axes().join`, `legendHandles` | covered | drop | v1.0.0 has `_share_y_axis` and `_legend_handles` (`accim/data/postprocessing/main.py:22-35`) |
| `83652a5a`, `3213b98a`, `e0c034a1`, `24def6c7`, `4d46f1f4`, `5b0029a9`, `c43d1294`, `48f7e9e3` (tests) Tests of `Table` and `postprocessing.utils` | `tests/data/test_table_characterization.py`, `test_table_fixes.py`, `test_table_methods.py`, `test_table_plotting.py`, `test_postprocessing_utils.py`, 3 CSV goldens | partly covered | adapt | v1.0.0 tests the zone and block columns, the spaces and `time_plot` (`tests/core/test_table_*.py`), not `format_table` presets, the concatenated-CSV round trip, `gather_vars_query`, `custom_order`, `generate_fig_data`, `scatter_plot`, `scatter_plot_with_baseline`, `preview_table_cols` or `gen_csv_concatenated`. Port them with the new names, regenerate the goldens with v1.0.0 (`Table` changed after `c03250f`) and check more than "a PNG exists" |
| `4a1d3a32` NameError in `morph_epws`, dead code | `accim/data/morphing.py` (`parent_folder_path` only defined when a scenario EPW is found), commented blocks of `morphing.py` and `preprocessing.py` | missing | port | Still in v1.0.0: defined at `morphing.py:122` inside the scenario loop, used at `:130`. The dead comments (`morphing.py:87-88`, `preprocessing.py:321,484,520`) are optional |
| `3213b98a` (part) Tests of morphing and preprocessing | `tests/data/test_morphing.py` (Java mocked), `tests/data/test_preprocessing.py` (`capitalize_words`, `give_address*` with `requests` mocked) | missing | port | v1.0.0 has no test of `morph_epws`, `capitalize_words` or `give_address*` (only `test_preprocessing_geopy.py` and `test_rename_epw_files.py`) |
| `2e628af2` `run.py` cleanup | dead code, IDD not resolved again after asking again for the version, `run_ep` names; `tests/run/test_run.py` | covered | drop | v1.0.0 asks until the version is valid (`run._ask_version`) and then resolves the IDD (`accim.energyplus.idd_path`), tested by `test_energyplus_versions.py::test_run_ep_uses_the_version_corrected_in_the_prompt`. The sim-v1 test of `removefiles` expects the 0.x deletion of every non-simulation file, which v1.0.0 stopped on purpose (`test_run_removefiles.py`). Only the padding of `make_eplaunch_options` ('23.1' to '23-1-0') is untested (optional) |
| `11b7b29c` (fix) `WorkspaceArtifactCleaner` with an empty workspace | `accim/utils.py` | missing | port | v1.0.0 still sets `_baseline_files = set()` and checks `if not self._baseline_files` (`accim/utils/workspace.py:37,64`), so an empty initial workspace raises "Initial state not captured" |
| `11b7b29c`, `b7c8a260`, `c0c20acf` Tests of `accim.utils` | `tests/utils/test_utils_pure.py`, `test_utils_idf.py`, `test_workspace_cleaner.py`: `transform_ddmm_to_int`, `remove_accents`, `amend_idf_version_from_dsb`, `remove_accents_in_idf`, `get_available_fields`, `get_idf_hierarchy`, `reduce_runtime`, the cleaner, `get_accim_args` round trip | partly covered | adapt | v1.0.0 tests the imports, the IDD paths, the people hierarchies, `set_occupancy_to_always` with `People:Instance` and the messages of `reduce_runtime` and `modify_timesteps`. Port the rest against `accim.utils.editing`, `people`, `accim_args` and `workspace`, with the v1.0.0 argument names in the round trip |
| `50366d53` `set_problem()` without `set_outputs_for_simulation()` | `accim/parametric_and_optimisation/main.py` (`self.sim_outputs = None`), `test_set_problem_no_outputs.py` | missing | port | `SimulationBase.set_problem` (`main.py:6733`) still reads `self.sim_outputs`, which only `set_outputs_for_simulation` creates (`main.py:6202`): `AttributeError` for a sweep without outputs |
| `ef1ec593` Code review of 2026-07-19 | `INFORME_REVISION_2026-07-19.md`, `PLAN_IMPLEMENTACION_2026-07-19.md` (agent reports, Spanish) | not applicable | drop | Documents, not code. Most findings are fixed in v1.0.0 (duplicated outputs, `SingleCooling`, PMV generation, `_pymod` deletion, `output_idfs`, empty `pd.concat`, models without `People`, EPW names with dots, `removefiles`, IDD paths, patches in `accim/__init__.py`, version lists); the open ones are in section 1.4 |

### 1.2 Tests and docs worth porting

- **Tests: yes**, adapted (rows marked port or adapt above): morphing and preprocessing with mocks, `accim.utils`,
  `Table` methods and plots, prompts with scripted answers, and the regression tests of the fixes. Move them to
  `tests/core` (v1.0.0 has no `tests/sim`, `tests/data`, `tests/run`, `tests/utils` or top-level
  `tests/conftest.py`), use the v1.0.0 names (`gen_csv_concatenated`, `preview_table_cols`,
  `prompts.ask_model_arguments`, the `accim.utils` submodules) and regenerate every golden with v1.0.0.
- **Docs and notebooks: no.** v1.0.0 rewrote the samples, notebooks, docstrings, API reference and tutorials; the
  sim-v1 versions document names that v1.0.0 does not have (`AddAccisToIdf`, `add_accis`, `comfort_standard`,
  `verbose`...).

### 1.3 Related ref: `review/refactor-sim-v1-20261024` (`6e090d59`)

Found during this review: one commit (35 files, +3167/-488) on top of `master` 0.8.2, local and on `origin`, not in
`v1.0.0` and not mentioned in its TODO or DEVLOG. It holds a first review of sim-v1 against 0.8.2
(`docs/refactor-sim-v1-review.md`, Spanish), three of the fixes above and a parametric integrity block.
**5 items: 1 port, 1 adapt, 3 drop.**

| Item | Area / files | State in v1.0.0 | Mark | Reason |
| --- | --- | --- | --- | --- |
| Three small fixes, with 13 regression cases | cleaner, `morph_epws`, `sim_outputs`; `tests/core/test_workspace_artifact_cleaner.py`, `test_morphing_no_scenarios.py`, `tests/parametric_and_optimisation/test_set_problem_no_outputs.py` | missing | port | Same fixes as section 1.1, written against 0.8.2 (closer to v1.0.0 than sim-v1): use these versions, with the cleaner fix in `accim/utils/workspace.py` |
| Parametric integrity block | `_checkpoint.py` (versioned, hashed checkpoints with the identity of each evaluation), `_execution.py` (owned run folders, locks, cleanup of owned paths only), `_pareto.py` (feasibility first), `file_cleanup.py`, `patches.py`, `main.py`, owned discovery folder of `print_available_outputs_mod`, `docs/source/checkpoint_integrity.rst`, 4 new and 3 adapted tests, `benchmarks/checkpoint_integrity_smoke.py` | missing | adapt | v1.0.0 still has the problems: `_annotate_pareto_status` ignores the constraints (`main.py:10738`) and a checkpoint task is identified by IDF label, EPW and parameters only (`_build_parametric_task_signature`, `main.py:8213`). Rebuild it on the v1.0.0 `main.py` (changed since 0.8.2: algorithms, normalisation, calendar); old checkpoints would be rejected, so it needs the author's decision and a CHANGELOG entry |
| Ownership of the `*_pymod.idf` files | `accim/sim/_workspace.py`, changes to `accis.py`, `accim_Main.py`, `accim_IDFgeneration.py`, `tests/core/test_batch_workspace.py` | not applicable | drop | v1.0.0 writes no `*_pymod.idf` files and does not rewrite the input IDFs |
| CLI versus Runtime API benchmark | `benchmarks/energyplus_api.py`, `benchmarks/results/*.json`, `tests/core/test_energyplus_api_benchmark.py` | covered | drop | Superseded by the API backend of v1.0.0 (`run_ep(backend='api')`, `accim.sim.energyplus_api`), checked against the EMS in `tests/core/test_energyplus_api.py` |
| Review report and tracking | `docs/refactor-sim-v1-review.md`, `TODO.md`, `DEVLOG.md`, `notes/` | not applicable | drop | Agent report (Spanish): keep it outside the repository if wanted. Its four TODO items, against v1.0.0: per-IDF output scope (open, section 1.4), single/batch EMS behaviour (fixed by v1.0.0 except the CS6 question), safe parsing in `get_accim_args` (open), incremental refactor (done by v1.0.0) |

### 1.4 Findings of the reviews still open in v1.0.0

Not code to port: candidates for new TODO items.

- `get_accim_args` evaluates IDF text with `eval` (`accim/utils/accim_args.py:67`); a plain `ast.literal_eval`
  would turn generated sums such as `3.5 + 1` into text (2026-10-24 review).
- `rename_epw_files` deletes the original EPWs that the user excluded from the renaming
  (`accim/data/preprocessing.py`, from line 644).
- `give_address` calls Nominatim without a timeout (`preprocessing.py:160`); `morph_epws` runs Java without
  checking its exit code (`morphing.py:89`).
- `apply_apmv_setpoints` adds a calling manager to every EMS program that has none of the same name, the user's
  included (`accim/sim/apmv.py:700-717`).
- Existing HVAC systems: windows are matched to zones by substring (`accim/sim/hvac/existing.py:98,180`), so
  `ZONE1` also takes the windows of `ZONE10`.
- Parametric module: `select_outputs` drops duplicates without the `idf` column (`main.py:5835`), so identical
  requests of two IDFs keep the first one only; Pareto status and checkpoints as in section 1.3.
- CS6, `ComfMod` 2: the heating and cooling setpoints use the same centre (`PMOT*0.30+25.9` with `CAT` 80,
  `+23.6` with 90; `accim/sim/ems/setpoint_lines.py`, key `(6, 2)`): needs a check against the source of the
  standard (question of the 2026-10-24 review).
- Not done: CI, `pyproject.toml`; the legacy scripts of `accim/misc/` (not packaged) are still there.

## 2. Tag `archive/feat-comfort-metrics-experiment-api`

`32c8942a`, also on GitHub: 3 commits since `853e9b4` (`a9b9ebd7` code, `25b5a0a6` docs, `32c8942a` RST headings),
29 files (+3283/-12). **Recommendation: drop the metrics module and the paper workflow.** The paper (manuscript v19,
in `llm_project_files/`) uses the hourly indicators of the module, and `compute_hourly_indicators` already gives
the occupied hours and the EN 16798-1 metric. Port the strict reducer and the `openpyxl` dependency; the PMV
metric is missing and could become an option of `compute_hourly_indicators`. Then delete the tag.
**9 items: 2 port, 1 adapt, 6 drop.**

### 2.1 `comfort_metrics.py` versus `compute_hourly_indicators`, metric by metric

`add_comfort_metrics` adds EMS programs that report, for each `People` target and zone timestep, occupied-only
increments (warm-up excluded, at `EndOfZoneTimestepBeforeZoneReporting`). `compute_hourly_indicators`
(`accim/parametric_and_optimisation/hourly_plotting.py:817`) computes indicators after the simulation from the
hourly CSV of each evaluation.

| Metric of the tag | Definition in the tag | Equivalent in v1.0.0 | State | Mark |
| --- | --- | --- | --- | --- |
| Occupied hours (`Occupied Hours`, h) | Zone timesteps with `People Occupant Count` > 0 | `n_hours` with `occupied='People Occupant Count'` (hours with a value > 0; zones combined with `max`) | covered (hourly, whole building) | drop |
| `fixed_en`: EN 16798-1 category II occupied degree-hours (C-h) | Operative temperature against 0.33 RMOT + 18.8, upper +3 K, lower -4 K, RMOT clamped to 10-30 C | `Kh_outside_II`, `Kh_above_II`, `Kh_below_II` (and `share_*_II`) with `comfort_standard='EN16798-1'`, `applicability='clip'`: same band (`ADAPTIVE_COMFORT_MODELS`, category II +3/-4) | covered (hourly means instead of timesteps; zones combined with `zone_aggregation` unless one is selected) | drop |
| `fixed_pmv`: occupied integral of abs(PMV) and hours with abs(PMV) > 0.5 (h) | Fanger PMV of the `People` objects (needs the `Fanger` model) | none: only temperature-based indicators | missing | adapt (optional): a PMV option of `compute_hourly_indicators` (column `Zone Thermal Comfort Fanger Model PMV`: mean abs(PMV), hours above 0.5), not an EMS module |
| Use as an objective during an optimisation | EMS output variables (key `EMS`, `Summed`) that BESOS reads in each run | none: the indicators come after the simulation, and the in-run comfort counters of v1.0.0 (ACCIS `CountHours_*`, aPMV) follow the controlled comfort model | missing | drop, unless a comfort objective independent of the control is wanted (see the decisions) |

### 2.2 Parts

| Item | Area / files | State in v1.0.0 | Mark | Reason |
| --- | --- | --- | --- | --- |
| `a9b9ebd7` Metrics module and session wrapper | `accim/sim/comfort_metrics.py`, `SimulationBase.add_comfort_metrics`, forced rediscovery (`_output_definitions_changed`), eager import in `accim/sim/__init__.py`, `test_comfort_metrics.py` | partly covered | drop | Occupied hours and `fixed_en` covered (section 2.1). It imports `accim.sim.apmv_setpoints._resolve_targets` (a deprecated module in v1.0.0; now `accim.sim.targets.resolve_targets`), and the eager import would undo the lazy `accim.sim` |
| `a9b9ebd7` `fixed_pmv` metric | part of `comfort_metrics.py` | missing | adapt | Optional; see section 2.1 |
| `a9b9ebd7` Strict reducer `checked_sum_results` | `accim/parametric_and_optimisation/objectives.py`; `test_strict_reducer_*` in `test_paper_experiments_api.py` | missing | port | v1.0.0 has `average_results`, `sum_results` and `return_time_series`; `sum_results` skips NaN silently. Small, independent, importable by the workers |
| `a9b9ebd7` Paper workflow inside the package | `paper_experiments.py` (`run_paper_experiment`, 1192 lines: 312 m2, EER/COP 4.42/4.95, budgets, approval notes), its export in `parametric_and_optimisation/__init__.py`, the rest of `test_paper_experiments_api.py` | not applicable | drop | Paper-specific, not a general API. Its generic helpers exist in v1.0.0: the EnergyPlus calendar of the hourly tables (decision of 2026-10-31), `_find_columns` and `path_replacements` (`hourly_plotting.py`) |
| `a9b9ebd7`, `25b5a0a6` Prepared experiment scripts | `llm_project_files/experimentos_preparados/` (5 scripts and a README, Spanish) | not applicable | drop | `llm_project_files/` is git-ignored now. A later revision is with the paper files (`llm_project_files/SS_261003/experimentos_preparados/`), and the current campaign (`llm_project_files/campaign_v03/`) does not use `run_paper_experiment` |
| `a9b9ebd7` `openpyxl>=3.1.5` | `setup.py` | partly covered | port | v1.0.0 writes XLSX files (`main.py:9936`, `:10916`), but `openpyxl` only arrives through besos (pyehub): declare it in `install_requires` |
| `25b5a0a6`, `32c8942a` Documentation | `docs/source/comfort_metrics.rst`, README.md and README.rst (section 2.2.9), `1_requirements.md` and `2_installation.md` (installing the branch), API pages, `index.rst` | partly covered | drop | Documents the dropped APIs. Its general corrections are already in v1.0.0: Python 3.9 or newer and the `jupyter_notebooks` path in `1_requirements.md`, and the aPMV default signs (`apmv.apply_apmv_setpoints`: cooling +0.5, heating -0.5) |
| `25b5a0a6` Spanish description of the module | `docs/modulo_parametric_and_optimisation_articulo.md` | not applicable | drop | Removed on 2026-10-16; not to be brought back |
| `a9b9ebd7`, `25b5a0a6` Tracking entries | CHANGELOG, DEVLOG, `notes/decisions.md` (2026-09-30, comfort metrics as an opt-in API), `notes/questions.md`, `notes/work-log.md` | not applicable | drop | They describe the unmerged work; the decision of 2026-09-30 was never adopted in `master` or `v1.0.0`, and this review proposes not to adopt it |

## 3. Local tag `archive/codex-paper-simple-energy`

`aa1ce90b`, local only (never pushed): 2 commits since `853e9b4` (`b409daed` experiments and tutorials, `aa1ce90b`
PuLP pin and lab environment), 37 files (+15390/-1). **Recommendation: nothing goes to the repository.** What is
worth keeping is already with the paper files, in `llm_project_files/entrega_pc_lab_20261002/` (same blobs, except
a later one-line path fix in the five scripts), so the tag can be deleted locally. **9 items: 0 port, 4 paper,
5 drop.**

| Item | Files | State in v1.0.0 | Mark | Reason |
| --- | --- | --- | --- | --- |
| `b409daed` Five experiment scripts | `examples/paper_experiments/exp_4_1_*.py` to `exp_4_5_*.py` (private model `ALJARAFE CENTER`, 312 m2, heating and cooling electricity, `TEST_RUN`) | not applicable | paper | Already in `llm_project_files/entrega_pc_lab_20261002/accim_source/examples/paper_experiments/`, in a newer version (`os.path.abspath` for paths of 260 characters or more); the later campaign is `llm_project_files/campaign_v03/` |
| `b409daed`, `aa1ce90b` Run instructions | `README.md`, `README_exp_4_1.md` to `README_exp_4_5.md` (Spanish) | not applicable | paper | Identical copies in the delivery folder |
| `b409daed`, `aa1ce90b` Lab environment | `environment_reference.json`, `requirements_reference.txt` | partly covered | paper | Identical copies in the delivery folder; the PuLP pin is in the v1.0.0 `setup.py` (`pulp<4`) |
| `b409daed` Link from the paper | `PAPER_TUTORIAL_LINK.md` (Methods section 2.7 linked to `parametric_and_optimisation_tutorials/index.html`) | not applicable | paper | Identical copy in the delivery folder. Manuscripts v15 to v19 link to `jupyter_notebooks/parametric_and_optimisation_examples/index.html` instead, which v1.0.0 builds |
| `b409daed`, `aa1ce90b` Agent reports | `VALIDACION_exp_4_1.md` to `VALIDACION_exp_4_5.md`, `VALIDACION_TUTORIALES.md`, `REVISION_LAB.md`, `INSTRUCCIONES_TRASLADO.md` (Spanish) | not applicable | drop | Agent reports (copies stay in the delivery folder). Their findings on accim: EPW paths in the name of the optimisation log and the import of geopy, both fixed in v1.0.0; an orphan `ZoneHVAC:IdealLoadsAirSystem` after adding the VRF system (one Severe error per run), still in v1.0.0: `hvac/vrf.add_vrf_objects` replaces the equipment lists and connections but keeps the ideal loads systems (`set_ideal_loads_availability_on`) |
| `b409daed` Public tutorial inputs | `tutorial_inputs/` (`TestModel_V940_ac.idf`, `TestModel_V940_mm.idf`, `Seville_Present.epw`, `provenance.json`) | not applicable | drop | Derived from `TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf` (`accim/sample_files/sample IDFs/input_IDFs/`) and the Seville EPW of the aPMV notebook, already distributed |
| `b409daed` Tutorial pages | `docs/source/parametric_and_optimisation_tutorials/` (index, getting started, public example, `exp_4_1` to `exp_4_5` with `literalinclude` of the scripts), toctree in `index.rst` | covered | drop | Same five workflows as the wf1 to wf5 notebooks of v1.0.0 (`docs/source/jupyter_notebooks/parametric_and_optimisation_examples/`), which the manuscript links; the pages would publish the scripts of the private model |
| `b409daed` `nbsphinx_execute = 'never'` | `docs/source/conf.py` | covered | drop | Already in v1.0.0 (`conf.py:44`) |
| `b409daed` `.gitignore` of the examples | `examples/paper_experiments/.gitignore` | not applicable | drop | v1.0.0 has no `examples/` folder |

## Proposed next steps for the author

1. **PR 1, small fixes** (on `v1.0.0` before the release, or on `master` after the merge): `parent_folder_path`
   of `morph_epws`, empty baseline of `WorkspaceArtifactCleaner`, `sim_outputs = None`, clear error of `Table`
   without `idf_path`, stale names of `using_Table.py`. Tests: those of `review/refactor-sim-v1-20261024` for the
   first three (section 1.3) and `test_idf_path_none_raises_clear_error` of sim-v1; entries in Fixed of
   [[../CHANGELOG.md]].
2. **PR 2, objectives and dependencies**: `checked_sum_results` with its two tests, and `openpyxl` in
   `install_requires`.
3. **PR 3, tests from sim-v1** adapted to v1.0.0 in `tests/core` (section 1.2).
4. **PR 4, golden master in the repository**: the golden master and the comparison of the two backends used for
   1.0.0 (section 11 of [[../CAMBIOS_CODIGO_v1.0.0.md]]), reusing the harness of sim-v1.
5. **Optional PRs after a decision**: the parametric integrity block of `review/refactor-sim-v1-20261024`
   (section 1.3), the PMV indicators of `compute_hourly_indicators` (section 2.1), the repair of
   `wrangled_table(reshaping='pivot')`.
6. **New items in [[../TODO.md]]** for the findings of section 1.4 and the orphan ideal loads systems of section 3,
   and the three review items closed; plus an entry in [[work-log.md]]. This note did not change them.
7. **Delete the refs** (never with `git push --tags`, which would publish the local tag):
   - now: the local tag `archive/codex-paper-simple-energy` (`git tag -d`), once the delivery folder is accepted as
     the copy kept with the paper files;
   - after PR 2 and the PMV decision: the tag `archive/feat-comfort-metrics-experiment-api`, locally and on GitHub;
   - after PRs 1, 3 and 4: the branch `refactor/sim-v1`, locally and on `origin`;
   - after PR 1 and the decision on its integrity block: `review/refactor-sim-v1-20261024`, locally and on `origin`
     (keep `docs/refactor-sim-v1-review.md` and the July reports outside the repository first, if wanted).

**Decisions that need the author**

- `review/refactor-sim-v1-20261024`: adapt its integrity block to v1.0.0 (checkpoints, owned folders, Pareto
  with constraints; it rejects old checkpoints) or drop it.
- Whether a comfort objective independent of the control is wanted during optimisations (the only use of the EMS
  metrics that v1.0.0 lacks), and whether the PMV indicators are worth adding.
- CS6 with `ComfMod` 2 (section 1.4): check the formulas against the source of the standard.
- Orphan ideal loads systems with VRF: remove them in `add_vrf_objects` (the output IDFs change) or keep the
  behaviour of 0.x.
- Target of the PRs: `v1.0.0` before the release, or `master` after the merge.