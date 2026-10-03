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


