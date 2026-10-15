# DEVLOG

Internal development log for the repository.

> This file complements `CHANGELOG.md`:
> - `CHANGELOG.md`: user-facing changes per release.
> - `DEVLOG.md`: day-to-day technical notes (tests, decisions, blockers).

## Conventions

- Add one entry per work block or PR.
- Use status: `done`, `in progress`, or `blocked`.
- Reference touched file paths and issue/PR links when available.
- Include a minimal verification step (tests, script, or manual check).
- Keep entries in reverse chronological order (most recent first).

## Entry template

```md
### YYYY-MM-DD
#### [status] Short title
- Context:
- Changes:
- Files:
- Verification:
- Next step:
```

## Entries

### 2026-10-15
#### [done] Fix the evaluation worker of `run_parametric_simulation`
- Context: While rewriting the notebooks wf2 and wf4, parametric runs failed or lost data in `_run_single_evaluation_worker`, which runs every evaluation, with one process or several: with `keep_dirs=False`, every simulation used the same `<out_dir>/BESOS_Output` folder, so parallel simulations collided and EnergyPlus failed; with several processes, two workers could try to create `BESOS_Output` at the same time (`FileExistsError`, intermittent); and the reported outputs (`add_outputs`) were looked for in the tuple returned by BESOS, which only holds the objectives and the simulation folder, so they were empty, or the first one got the folder path and `output_dir` was missing.
- Changes: the BESOS evaluator gets `out_dir=None` when `keep_dirs=False` (BESOS then runs each simulation in a temporary folder); with `keep_dirs=True`, `<out_dir>/BESOS_Output` is created with `exist_ok=True` before the evaluator; when there are reported outputs, `problem.pre_optimisation()` makes BESOS record them and the worker reads them from the last row of `problem.add_outputs_list`; `output_dir` is the last element of the BESOS result whenever `keep_dirs=True`.
- Files: `accim/parametric_and_optimisation/main.py`, `tests/parametric_and_optimisation/test_parametric_worker.py`, `CHANGELOG.md`.
- Verification: the new tests call the real worker with a fake BESOS evaluator (no EnergyPlus run); 4 of the 6 fail on the previous code and all pass with the fix. `pytest tests/parametric_and_optimisation`: 160 passed, 1 failed (`test_subplot_ordering.py::test_resolve_subplot_orders_custom_missing_dimension_raises`, which already failed before the change). Notebooks wf1, wf2 and wf4 executed with reduced runs and several processes, without the notebook workarounds (see the next entry).
- Next step: none.

#### [done] Rewrite the notebooks wf1, wf2 and wf4 of `parametric_and_optimisation_examples`
- Context: Handoff from the paper chat (`llm_project_files/HANDOFF_notebooks_claude_code.md`): distributable notebooks that reproduce experiments similar to Examples 1, 2 and 4 of the paper with the sample IDF and EPW files. The author asked for simulations as light as possible with annual results, and for full hourly results only in wf1.
- Changes: all three use `reduce_runtime(timesteps=2)` with the full-year run period, `Run_Simulation_for_Sizing_Periods = "No"` (the sample IDFs simulate 7 design days, which the annual readers added to the results: 8,928 h, +3.3 % HVAC electricity), only the outputs that are used, and parallel processes. wf1: LHS of the custom model inside the m-n band, ASHRAE 55 screening (`compute_hourly_indicators`, `plot_results_scatter_matrix`, `plot_comfort_screening`, `plot_adaptive_comfort_chart`). wf2: the 40 predefined configurations of the paper in annual mode (`keep_dirs=False`), then the 4 EN 16798-1 Cat. III configurations simulated again with hourly outputs for the hourly views. wf4: NSGA-II (population 20, 60 evaluations per EPW, fixed seed) with annual results, knee point and TOPSIS, then the non-dominated solutions simulated again with hourly outputs for the screening and the hourly views of the compromise solutions.
- Files: `accim/sample_files/jupyter_notebooks/parametric_and_optimisation_examples/wf1_parametricsimulation_accim_custom_model.ipynb`, `wf2_parametricsimulation_accim_predefined_model.ipynb`, `wf4_optimisationsimulation_accim_custom_model.ipynb`.
- Verification: executed with nbconvert in a copy of the folder, with reduced runs (wf1: 3 LHS samples; wf2: 4 configurations; wf4: population 4 and 8 evaluations per EPW). The hourly re-simulations reproduce the annual HVAC electricity of the main runs exactly.
- Next step: decide whether to set `Run Simulation for Sizing Periods` to `No` in the sample IDFs; mixed mode needs AirflowNetwork openings, which the sample model lacks; wf3, wf5 and tutorials 00-10.

#### [done] Split sample files into the optional distribution `accim-samples`
- Context: More notebooks are going to be added to `accim/sample_files` (already about 125 MB uncompressed, 36 MB wheel). The user wants to install accim with or without them from pip.
- Changes: pip extras cannot add files to a distribution, only dependencies, so the sample files go into a second distribution. Root `setup.py` now excludes `accim.sample_files*` from `find_packages`, adds `exclude_package_data` as a safety net and declares `extras_require={'samples': ['accim-samples==<accim version>']}`. Root `MANIFEST.in` now uses `prune accim/sample_files`. New `packaging/accim-samples/` (setup.py, MANIFEST.in, README.md for PyPI) and `packaging/build_samples_dist.py`, which stages a copy of `accim/sample_files` (without `__pycache__`, `*.pyc`, `.ipynb_checkpoints`) in `build/samples_stage`, builds a wheel by default (`--sdist` optional) and checks its content. The samples wheel never contains `accim/__init__.py`, so both distributions install into `site-packages/accim` and uninstall independently. `accim-samples` requires `accim==<same version>`. `dist_build_package.bat` builds both; upload scripts upload both from `dist/`. `/build/` added to `.gitignore`.
- Files: `setup.py`, `MANIFEST.in`, `packaging/accim-samples/*`, `packaging/build_samples_dist.py`, `dist_build_package.bat`, `dist_upload.bat`, `dist_upload_test.bat`, `.gitignore`, `README.md`, `docs/source/1_requirements.md`, `docs/source/2_installation.md`, `docs/source/4_detailed use.md`, `CHANGELOG.md`, `notes/work-log.md`, `notes/decisions.md`.
- Verification: Built with Python 3.14, setuptools 82.0.1, build 1.5.0. Core wheel, built from the source tree and through the sdist: 0.51 MB, no `sample_files` entries, metadata `Provides-Extra: samples` and `Requires-Dist: accim-samples==0.7.8; extra == "samples"`. Samples wheel: 29.1 MB, 129/129 source files (same set as the filtered source tree), no `accim/__init__.py`, `Requires-Dist: accim==0.7.8`; `--sdist` also works (29.4 MB). In a temporary venv (`--no-deps`): both installed together, `import accim.sample_files` resolved to site-packages; uninstalling `accim-samples` kept accim intact, and uninstalling `accim` kept `sample_files`. Resolution of `accim[samples]` against a real index was not tested (`accim-samples` is not on PyPI yet; the name was free on 2026-10-15). The existing `dist/` (0.7.8.1) was not touched.
- Next step: First upload of `accim-samples` (needs an account-scoped PyPI token, or a token for the new project); test `pip install "accim[samples]"` from TestPyPI.


### 2026-10-03
#### [done] Diagnose exp 4.4 failure: EnergyPlus output path exceeds MAX_PATH
- Context: Exp 4.4 test run failed on this PC: every simulation ended with "EnergyPlus Terminated--Error(s) Detected" and no `eplusout.err` was written. The same script works on another PC.
- Root cause: `llm_project_files` is a junction to `D:\OneDrive - Universidad de Cádiz (uca.es)\...`. The script's `Path(__file__).resolve()` expanded it, so the BESOS run folder was 257 characters long. EnergyPlus 9.4 cannot open its output files at 260 or more characters (`MAX_PATH`), even with `LongPathsEnabled=1`. Reproduced: the same `in.idf` succeeds in a short path, also with "á" in it, and fails with `**FATAL:OpenOutputFiles: Could not open file ... for output` in a 262-character ASCII path.
- Changes: Added `SimulationBase._warn_if_out_dir_too_long_for_energyplus`, called from `run_optimisation` and `run_parametric_simulation`. In the 5 delivery scripts (`entrega_pc_lab_20261002/.../exp_4_*.py`), `HERE` now uses `os.path.abspath` instead of `.resolve()`. Re-applied the `run_optimisation` progress edits: most of them had not been saved to `main.py` in the previous session.
- Files: `accim/parametric_and_optimisation/main.py`, `tests/parametric_and_optimisation/test_energyplus_path_length_warning.py`, delivery scripts, `CHANGELOG.md`, `notes/work-log.md`.
- Verification: path warning + progress + checkpoint tests: 9 passed (Python 3.14).
- Next step: Regenerate the delivery zip if the patched scripts must be shipped.

### 2026-10-03
#### [done] Add progress reporting to run_optimisation
- Context: `run_optimisation` only showed the EnergyPlus "Running…/Completed" lines from the workers. `run_parametric_simulation` already reports batch progress through tqdm.
- Changes: Added the new module `accim/parametric_and_optimisation/optimisation_progress.py`, with `OptimisationProgressReporter` and `ProgressReportingEvaluator`. The evaluator wraps `PlatypusConfig.default_evaluator`, which is `MapEvaluator` or `ProcessPoolEvaluator`. It re-implements `evaluate_all` with `submit_func` + `as_completed`, or with sequential `job.run()`, so it can report each finished job while keeping the result order. For unknown evaluators it delegates the whole batch. `run_optimisation` gained `show_progress=True` and case start/skip/end hooks. The `finally` block now always restores the original default evaluator.
- Files: `accim/parametric_and_optimisation/optimisation_progress.py`, `accim/parametric_and_optimisation/main.py`, `tests/parametric_and_optimisation/test_optimisation_progress.py`, `CHANGELOG.md`, `notes/work-log.md`.
- Verification: New tests run Platypus NSGA-II on a toy problem with `MapEvaluator` and with `ProcessPoolEvaluator(2)`: 3 passed. `test_optimisation_checkpoint_resume.py`: 3 passed. Both runs used Python 3.14 and platypus 1.4.1. No real EnergyPlus run.
- Next step: Check the output in a real run with `processes>1` on the simulation PC (Python 3.9).


### 2026-10-03
#### [done] Add filtered copies of per-simulation output CSVs
- Context: Large campaigns need to keep only a few hourly outputs of already-run simulations. The existing `get_hourly_df*` methods build one joint DataFrame and read full CSVs, and `keep_only_outputs_in_idfs` only affects future runs.
- Changes: Added public `SimulationBase.filter_simulation_output_csvs` and private helpers. The method validates all arguments before writing. It resolves session paths with `_resolve_simulation_file_path`, including all optimisation evaluations, or accepts explicit paths, and removes duplicate paths. Columns are matched exactly, then case-insensitively, then by substring, with `Date/Time` always kept. Reads use positional `usecols`, `dtype=str` and an optional `chunksize`. Output is written through `csv.writer` with the source line terminator, so it does not depend on pandas `to_csv` keyword versions. Each file is published from a temporary file, and destinations avoid collisions. The method returns a per-file report. No existing method changed.
- Files: `accim/parametric_and_optimisation/main.py`, `tests/parametric_and_optimisation/test_filter_simulation_output_csvs.py`, `docs/source/filter_output_csvs.rst`, `docs/source/index.rst`, `docs/source/api/accim.parametric_and_optimisation.rst`, `CHANGELOG.md`, `notes/work-log.md`.
- Verification: New tests: 33 passed. Related existing suites (`test_hourly_parametric_public_api`, `test_sim_file_cleanup`, `test_data_filtering_api`, `test_analysis_output_resolution`): 17 passed. Both runs used Python 3.14 and pandas 3.0.5. Real-data check on the Plan A results loaded from pickles, with output written to a temporary folder outside OneDrive: 4.1 wrote 120/120 files, 145.1 → 63.2 MB, and 4.2 wrote 300/300 files, 399.2 → 193.9 MB. In both runs, 4 of 9 columns were kept and a sampled copy matched the original subset verbatim. Experiment 4.3 has no consolidated results and no CSVs; it raised the expected pre-write `ValueError`. Sphinx build not run.
- Next step: Optionally run on the simulation PC with Python 3.9 / older pandas, and build the docs.

### 2026-06-11
#### [done] Align README.rst with development workflow documentation
- Context: The workflow section had been added in `README.md` but not mirrored in `README.rst`.
- Changes: Added a matching "Development workflow files" section to `README.rst`.
- Files: `README.rst`.
- Verification: Manual review of reStructuredText formatting and wording consistency.
- Next step: Keep both README files aligned when workflow documentation changes.

### 2026-06-11
#### [done] Translate tracking docs to English and add README workflow section
- Context: The tracking files and process docs needed to be fully in English.
- Changes: Translated `DEVLOG.md`, `TODO.md`, and `ROADMAP.md`, and added a workflow section in `README.md`.
- Files: `DEVLOG.md`, `TODO.md`, `ROADMAP.md`, `README.md`.
- Verification: Manual review of Markdown structure and wording.
- Next step: Keep all new tracking entries and updates in English.

### 2026-06-11
#### [done] Split tracking into DEVLOG, TODO, and ROADMAP
- Context: The team decided to separate done work, active tasks, and long-term initiatives.
- Changes: Created `TODO.md` and `ROADMAP.md`; kept `DEVLOG.md` focused on completed technical work.
- Files: `DEVLOG.md`, `TODO.md`, `ROADMAP.md`.
- Verification: Manual review of links and Markdown structure.
- Next step: Track new tasks in `TODO.md` and move completed outcomes to `DEVLOG.md`.

### 2026-06-11
#### [done] Create initial DEVLOG structure
- Context: The repository needed a continuous technical change record.
- Changes: Created `DEVLOG.md` with conventions, template, and tracking pointers.
- Files: `DEVLOG.md`.
- Verification: Manual Markdown format review.
- Next step: Start logging all technical changes from now on.

## Tracking

- Active tasks: `TODO.md`
- Future implementations: `ROADMAP.md`


