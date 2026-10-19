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

## 2026-10-19 — Release 0.8.2

- **Objective**: Publish accim 0.8.2 (with `accim-samples`): EnergyPlus 26.1 and 26.2, the `People:Definition` and `People:Instance` objects of 26.2, and the fixes of `TempCtrl='pmv'`, `ComfStand=[0]` and `Table`.
- **Affected files**: `accim/__init__.py`, [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: The author kept 0.8.2 although the release adds features (Semantic Versioning would make it 0.9.0). From TestPyPI only `accim` and `accim-samples` were installed (`--no-deps`), with the dependencies from PyPI. The clean environments get newer libraries than the development one (eppy 0.6.7, pandas 3.0.6), and accim works with them.
- **Validation**: tests; three clean venvs (local wheels, TestPyPI, PyPI) with imports and a 1-day simulation with EnergyPlus 26.2; GitHub release. Details in [[../DEVLOG.md]].
- **Next step**: none; `v0.8.2` is active in Read the Docs.

## 2026-10-17 — Release 0.8.1 (`pulp<4`)

- **Objective**: Fix the import of `accim.parametric_and_optimisation` in new installations: PuLP 4 renamed the `pulp.apis.*_api` modules that `pyehub` (a dependency of besos) imports.
- **Affected files**: `setup.py`, `accim/__init__.py`, [[../CHANGELOG.md]], `docs/source/5_troubleshooting.md`, [[../TODO.md]]; [[../DEVLOG.md]].
- **Finding or decision**: `'pulp<4'` in `install_requires` is enough. A shim for the renamed modules was not needed. The test of a clean installation with all the dependencies has to be done before the upload, from the local wheels (`pip install --find-links dist`).
- **Validation**: tests; clean venv with the local wheels before the upload; clean install from PyPI after it; GitHub release. Details in [[../DEVLOG.md]].
- **Next step**: activate `v0.8.0` and `v0.8.1` in Read the Docs.

## 2026-10-17 — Release 0.8.0

- **Objective**: Publish accim 0.8.0 on PyPI (with `accim-samples`), show 0.8.0 on Read the Docs and make the GitHub release.
- **Affected files**: `accim/__init__.py`, [[../CHANGELOG.md]], `README.md`, two pages of `docs/source`, a docstring and a stale test; [[../DEVLOG.md]].
- **Finding or decision**: 0.7.8 was never published, so the version goes from 0.7.7 to 0.8.0 and the texts that said 0.7.8 now say 0.8.0. A test that contradicted `f1e6bdc` (partial custom subplot orders) was removed. Only the tag `v0.8.0` was pushed. Right after an upload, the CDN can serve the old index page for a few minutes.
- **Validation**: tests; dry run from TestPyPI; clean install from PyPI; GitHub release with the three files of `dist/`. Details in [[../DEVLOG.md]].
- **Next step**: activate `v0.8.0` in Read the Docs.

## 2026-10-16 — How-to notebooks: one source, run with accim 0.7.8

- **Objective**: Make the sample files the only source of the How-to notebooks, correct them for accim 0.7.8 and EnergyPlus 25.1, run them and export them to the documentation.
- **Affected files**: the seven How-to notebooks and their IDFs in `accim/sample_files/jupyter_notebooks/`; new `docs/prepare_howto_notebooks.py`; `docs/source/jupyter_notebooks/` (exported notebooks; data copies removed); [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Three notebooks needed fixes of accim code, found here and made in PR #6: `Table.time_plot` with pandas 3, the `'nan'` checks of `rename_epw_files`, and the `SetAST` program of `addAccis` with several output IDFs (stale lines since `95b695b`). The executed copies were run against PR #6. Details in [[../DEVLOG.md]].
- **Validation**: the seven notebooks run without errors with PR #6, EnergyPlus 25.1 and pandas 3; local html build without warnings from these pages; `accim-samples` wheel 25.3 MB.
- **Next step**: merge after PR #6.

## 2026-10-16 — Sample notebook `full_example` removed

- **Objective**: Decide what to do with the older full example of the sample files (`jupyter_notebooks/full_example`, EPW files of Japan), which failed after `pip install "accim[samples]"` and was left out of the update of the How-to notebooks.
- **Affected files**: `accim/sample_files/jupyter_notebooks/full_example/` (removed); [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: The author chose to remove it rather than update it: it repeated `full_example_IBPSA`, which is in the documentation. Nothing in the repository links to the folder; the link that `addAccis()` prints to its old documentation page (404) changes in PR #6.
- **Validation**: `accim-samples` wheel 27.6 MB (29.8 MB before). Details in [[../DEVLOG.md]].
- **Next step**: optional page redirect in Read the Docs for the link printed by accim 0.7.8 and earlier.


## 2026-10-16 — Release scripts, README and docs for `accim-samples`

- **Objective**: Publish accim on PyPI and build the documentation by running the `dist_*.bat` scripts; explain in the README and the documentation how to run the example notebooks with `accim[samples]`, and remove section 0 of the README.
- **Affected files**: new `packaging/release.py`; `dist_build_package.bat`, `dist_upload.bat`, `dist_upload_test.bat`, `dist_build_docs.bat`; `docs/source/api/accim.parametric_and_optimisation.rst`; `accim/parametric_and_optimisation/main.py` (docstring); [[../README.md]]; `docs/source/{1_requirements,2_installation,4_detailed use}.md`; [[../DEVLOG.md]]; [[../Home.md]]; [[README.md|notes/README]]; [[decisions.md]]; `.github/copilot-instructions.md`; [[../CHANGELOG.md]].
- **Finding or decision**: The upload scripts uploaded all of `dist/`, which held an old 0.7.8.1 build; now only the current version goes, `accim-samples` before `accim`, after confirmation. The README section 0 was used by agents: its content moved to [[../DEVLOG.md#Tracking files|Tracking files]].
- **Validation**: both distributions built and checked; dry runs and cancelled uploads (nothing uploaded); docs built with the script. Details in [[../DEVLOG.md]].
- **Next step**: First upload of `accim-samples` (token for the entire account).


## 2026-10-16 — Agent-generated files removed

- **Objective**: Remove the files written by AI agents that do not belong in the repository, and the Spanish page on comparing pickles from Read the Docs, as the author asked.
- **Affected files**: `docs/source/index.rst`, `CHANGELOG.md`, `.gitignore`, [[../Home.md]], [[references.md]]; removed reports in `docs/` and at the root, run logs `exp_4_*_run.log` and tracked `.ipynb_checkpoints` folders. Full list in [[../DEVLOG.md]].
- **Finding or decision**: The author keeps this vault, `AGENTS_v2.md`, `.github/copilot-instructions.md`, `DEVLOG.md`, `TODO.md` and `ROADMAP.md`. The review and plan of 2026-07-25 left the repository and stay in the author's project files.
- **Validation**: no tracked file refers to the removed files; local html build with notebooks never executed.
- **Next step**: none.


## 2026-10-16 — The parametric notebooks in the documentation

- **Objective**: Show the workflows and tutorials of `parametric_and_optimisation_examples` on Read the Docs, as the author asked.
- **Affected files**: new `docs/prepare_parametric_notebooks.py` and `docs/source/jupyter_notebooks/parametric_and_optimisation_examples/` (index and 16 executed notebooks); `docs/source/conf.py`, `docs/source/index.rst`, `docs/requirements.txt`; tutorials 05, 08 and 09; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Read the Docs cannot run these notebooks (EnergyPlus), so the documentation shows copies run beforehand, as for the other notebook pages, and `conf.py` never runs notebooks. The copies are exported with relative paths, without progress bars, with shortened logs and smaller figures; a 256-colour palette shrinks most figures but bands heatmaps, so each figure keeps its colours when the palette would change it visibly. The runs used a copy of the committed accim (`git archive`, first in `PYTHONPATH`) because another session was editing the working copy.
- **Validation**: the 16 notebooks ran without errors; local html, latex and epub builds without errors or warnings from the new pages; pages checked in the browser. Details in [[../DEVLOG.md]].
- **Next step**: Merge into `master` so that Read the Docs builds the section; export wf4 and wf5 again after the minor fixes are committed.


## 2026-10-15 — Parametric plan, extra parameters, custom baseline and MCDM per front

- **Objective**: Fix the accim bugs that made tutorial 06 simulate the wrong model and ignore its roof insulation, and that forced workarounds in tutorial 05; choose compromise solutions per front. Requested by the author, with tests.
- **Affected files**: `accim/parametric_and_optimisation/main.py`, `analysis.py`, `plotting.py`; new `tests/parametric_and_optimisation/test_parametric_plan.py`, plus `test_parametric_worker.py` and `test_analysis_output_resolution.py`; tutorials 05, 06 and 10; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Parametric results now follow the task order (by IDF, EPW and plan row), with one row per plan row even when rows repeat, so parallel runs give the same table as sequential ones. The worker gets the non-accim BESOS parameters as a keyword argument, so the existing fake workers of the tests keep working. `get_best_compromise_solution` uses the same grouping as `plot_best_compromise_solutions`.
- **Validation**: 14 new tests, 11 failing on the previous code; parametric suite 174 passed, 1 old failure. Tutorials 05, 06 and 10 executed and checked (plan order, model of each row, effect of the roof thickness, ComfStand 99 in both IDFs). Details in [[../DEVLOG.md]].
- **Next step**: Commit, after the author's approval.


## 2026-10-15 — Notebooks wf3, wf5 and tutorials 00-10

- **Objective**: Finish the notebooks of `parametric_and_optimisation_examples`: wf3 and wf5 (aPMV setpoints, Examples 3 and 5 of the paper) and the tutorials 00-10, all runnable with the sample IDF and EPW files.
- **Affected files**: `wf2`, `wf3`, `wf5` and `00`-`10` in `accim/sample_files/jupyter_notebooks/parametric_and_optimisation_examples/`; [[../DEVLOG.md]].
- **Finding or decision**: The sample model has a work efficiency, clothing and air velocity of 1 in its People object, which overheats the zones under aPMV setpoints; wf3, wf5 and tutorial 03 set realistic PMV inputs. The aPMV cooling season is given by dates, so wf3 and wf5 use Seville only, and wf2 gives Sydney the cooling season of the southern hemisphere. Several tutorials ran without errors but gave wrong results; the causes in accim are listed in [[../DEVLOG.md]] (dropped `idf` column with one building, `additional_params` ignored by the parametric worker, custom-model baseline only on the first building, row order and duplicates in Morris/Sobol runs, MCDM over the fronts of all EPWs). None of them affects the campaign of the paper, which uses one building, accim parameters only and no Sobol/Morris.
- **Validation**: wf3 in full and wf5 reduced, without errors; tutorials 00-10 executed in order without errors. Details in [[../DEVLOG.md]].
- **Next step**: The author decides whether to fix those issues in accim and whether to commit the notebooks.


## 2026-10-15 — Notebooks wf1, wf2, wf4 and the parametric evaluation worker

- **Objective**: Rewrite the notebooks wf1, wf2 and wf4 of `parametric_and_optimisation_examples` after the handoff from the paper chat, with light simulations, and fix the bugs they exposed.
- **Affected files**: the three notebooks; `accim/parametric_and_optimisation/main.py` (`_run_single_evaluation_worker`); new `tests/parametric_and_optimisation/test_parametric_worker.py`; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Full hourly results only in wf1; wf2 and wf4 run in annual mode and simulate the chosen configurations or solutions again with hourly outputs (see [[decisions.md#2026-10-15 — Hourly results of the parametric notebooks only where they are analysed|the decision]]). The sample IDFs simulate 7 design days, which the annual readers added to the results (+3.3 % HVAC electricity); the notebooks set `Run_Simulation_for_Sizing_Periods = "No"`. The evaluation worker shared one folder with `keep_dirs=False`, could create `BESOS_Output` twice at once and lost the `add_outputs`; fixed. Mixed mode needs AirflowNetwork openings, which the sample model lacks.
- **Validation**: 6 new worker tests (4 fail on the previous code); parametric unit tests 160 passed, 1 failure that predates the change; the three notebooks executed with reduced runs. Details in [[../DEVLOG.md]].
- **Next step**: Design days in the sample IDFs; wf3, wf5 and tutorials 00-10.


## 2026-10-15 — Optional sample files: `accim` and `accim[samples]`

- **Objective**: Allow installing accim from pip with or without `accim/sample_files`, since more (heavy) notebooks will be added.
- **Affected files**: `setup.py`, `MANIFEST.in`, new `packaging/accim-samples/` and `packaging/build_samples_dist.py`, `dist_build_package.bat`, `dist_upload*.bat`, `.gitignore`, [[../README.md]], `docs/source/{1_requirements,2_installation,4_detailed use}.md`, [[../CHANGELOG.md]], [[../DEVLOG.md]].
- **Finding or decision**: pip extras only add dependencies, so the sample files are a second distribution, `accim-samples`, pulled in by the `samples` extra and installed into the same `accim/sample_files` folder (see [[decisions.md#2026-10-15 — Ship sample files as the separate distribution `accim-samples`|the decision]]). No runtime code uses `sample_files`. Parallel edits to the same file lost changes again (`setup.py`, `dist_build_package.bat`); they were re-applied one at a time.
- **Validation**: Core wheel 0.51 MB without sample files; samples wheel 29.1 MB with 129/129 files and no `accim/__init__.py`; install/uninstall of each distribution in a temporary venv left the other intact. Details in [[../DEVLOG.md]].
- **Next step**: First upload of `accim-samples` to TestPyPI/PyPI and test `pip install "accim[samples]"`.


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
