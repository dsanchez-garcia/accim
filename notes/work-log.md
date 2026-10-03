---
title: Work log
type: log
tags: [vault, work-log]
created: 2026-09-13
---

# Work log

Reverse-chronological session log (most recent first). Each entry should be
short: objective, affected files, finding or decision, validation, next step.
Use [[templates/daily-note.md|the daily-note template]] to start a new entry.

This log is a lightweight, session-scoped complement to the repository's
existing tracking files — it does not replace them (see
[[decisions.md#2026-09-13 — `notes/work-log.md` complements, not replaces, existing tracking files|the related decision]]).

## 2026-10-03 — Exp 4.4 failure: EnergyPlus MAX_PATH

- **Objective**: Find out why exp 4.4 fails on this PC with no `eplusout.err` written.
- **Affected files**: `accim/parametric_and_optimisation/main.py` (`_warn_if_out_dir_too_long_for_energyplus`); new `tests/parametric_and_optimisation/test_energyplus_path_length_warning.py`; `llm_project_files/entrega_pc_lab_20261002/accim_source/examples/paper_experiments/exp_4_*.py`; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: `llm_project_files` is a junction to OneDrive. `Path.resolve()` expanded it to a run folder of 257 characters, and EnergyPlus 9.4 cannot write output paths of 260 or more characters. Reproduced manually. The "á" is not the cause. The scripts now use `os.path.abspath`, and accim warns early. Most `main.py` edits from the previous session had not been saved and were re-applied; edits to the same file must not be run in parallel.
- **Validation**: 9 tests passed. A real exp 4.4 test run is noted in [[../DEVLOG.md]].
- **Next step**: Regenerate the delivery zip if needed.

## 2026-10-03 — Progress reporting in run_optimisation

- **Objective**: Show simulation progress during `run_optimisation`, similar to `run_parametric_simulation`.
- **Affected files**: new `accim/parametric_and_optimisation/optimisation_progress.py`; `accim/parametric_and_optimisation/main.py` (`run_optimisation`, new `show_progress` argument); new `tests/parametric_and_optimisation/test_optimisation_progress.py`; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: The final number of simulations is only an estimate (`pop × ceil(evals/pop)` per case for generational algorithms), so it is shown with `~`. Progress is reported from the main process by wrapping the Platypus default evaluator, and each finished job is reported through `as_completed`.
- **Validation**: Toy NSGA-II tests (sequential and process pool) passed: 3/3. Checkpoint-resume tests passed: 3/3.
- **Next step**: Check the output in a real multi-process run.

## 2026-10-03 — Filtered copies of per-simulation output CSVs

- **Objective**: Reduce the size of already-run results by writing column-filtered copies of each `eplusout.csv`, for both parametric and optimisation sessions.
- **Affected files**: `accim/parametric_and_optimisation/main.py` (`SimulationBase.filter_simulation_output_csvs` + private helpers); new test module `tests/parametric_and_optimisation/test_filter_simulation_output_csvs.py`; [[../docs/source/filter_output_csvs.rst|how-to guide]]; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Values are copied as text, so they are never re-formatted. Originals and session paths are never modified. Plan A pickles store `output_dir` relative to the campaign root, so callers must `chdir` there, as with `get_hourly_df*`. Experiment 4.3 has no consolidated results or CSVs. No new durable decision was needed.
- **Validation**: 33 new tests and 17 related tests passed (Python 3.14, pandas 3.0.5). Real-data runs on 4.1/4.2 wrote to a temporary folder: 420/420 files written, about 52–57% smaller, and a sampled copy matched the original verbatim. Details are in [[../DEVLOG.md]].
- **Next step**: Run the tests under Python 3.9 on the simulation PC; build the docs.

## 2026-09-13 — Integrate Obsidian vault into the repository

- **Objective**: Set up the repository root as an Obsidian vault for
  persistent documentation and working context, without duplicating
  existing technical documentation, tasks or code.
- **Affected files**:
  - Created: `Home.md`, `notes/README.md`, `notes/obsidian-tutorial.md`,
    `notes/work-log.md`, `notes/decisions.md`, `notes/questions.md`,
    `notes/references.md`, `notes/templates/daily-note.md`,
    `notes/templates/decision-record.md`, `notes/attachments/.gitkeep`,
    `.obsidian/app.json`, `.obsidian/core-plugins.json`,
    `.obsidian/community-plugins.json`, `.obsidian/templates.json`,
    `.github/copilot-instructions.md`.
  - Modified: `.gitignore` (ignore `.obsidian/`),
    `sync_branch.bat` (exclude `Home.md` and `notes/` from `git clean -fd`).
  - Not modified: `README.md`, `README.rst`, `CHANGELOG.md`, `DEVLOG.md`,
    `TODO.md`, `ROADMAP.md`, `AGENTS_v2.md`, `docs/source/**`, and all root
    reports (linked from `Home.md`, not rewritten).
- **Finding or decision**: No literal `AGENTS.md` exists (only
  `AGENTS_v2.md`); no multilingual README/TODO pair exists to mirror in
  English. See [[decisions.md]] for the full list of decisions made in this
  session.
- **Validation**: All wiki links in `Home.md` and `notes/**` were checked
  against real file paths and exact heading text; JSON files in `.obsidian/`
  were parsed successfully; YAML frontmatter parsed successfully in every
  new note; `git diff --check` reported no whitespace errors; a search for
  the old `git clean -fd` (without exclusions) found no other destructive
  cleanup scripts in the repository.
- **Next step**: Open the vault in Obsidian once to confirm the local
  `.obsidian/` settings are picked up as expected (attachments, new-note
  folder, templates folder, relative wiki links, auto-update on rename, and
  the requested core plugins).
