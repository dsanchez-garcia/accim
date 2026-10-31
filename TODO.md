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

- [ ] [P2][todo] Describe `keep_input` correctly in the parametric notebooks
  - Context: Nine parametric notebooks (00, 01, 02, 03, 05, 06, WF1, WF2, WF3) describe the argument `keep_input` of `run_parametric_simulation()` as "whether generated input files are preserved", but it keeps the input parameters (the columns of the plan) in the results table (see its docstring in `accim/parametric_and_optimisation/main.py`). Found by the review of the notebook texts of 2026-10-31.
  - Definition of done: the line corrected in the source notebooks and in their executed copies (the same edit), and the pages exported again with `docs/prepare_parametric_notebooks.py export` (no new run needed).
  - References: `docs/README.md` (§7.3), the key-argument lists of the cells that call `run_parametric_simulation()`.

- [ ] [P2][todo] `sampling_full_set()` drops ESP CTE (`ComfStand` 0) when the plan has `CAT` or `ComfMod`
  - Context: `drop_invalid_param_combinations()` takes `CAT` and `ComfMod` as 'n/a' for `ComfStand` 0 (its setpoints depend on neither), so with the predefined models a full set such as `{'ComfStand': [0, 1], 'CAT': [1, 2]}` simulates no row of `ComfStand` 0, without a warning; likewise, INT ISO7730 (22) is only kept with `ComfMod` 0. As in 0.8.2. Since 1.0.0, both work with any `CAT` and `ComfMod` in the simulation (see `DEVLOG.md`, 2026-10-31), so the rows are only repeated simulations.
  - Definition of done: the author decides whether to keep one row of these standards for each combination of the other parameters (the first value of `CAT` and `ComfMod`), to warn when they are dropped, or to keep the current behaviour (documented in the migration guide, 9.3); with a test.
  - References: `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py` (`valid_params`), `tests/parametric_and_optimisation/test_param_accis_filter.py`.

- [ ] [P1][blocked] Define backlog priority rules
  - Context: Standardize entry criteria for new tasks. Blocked on the approval of the author.
  - Proposal (2026-10-31): `P0`: it stops users or a release now (a crash or wrong results in a published version, lost data, a security problem); it goes before anything else. `P1`: needed for the next release, or wrong behaviour that has a workaround, failing tests, or documentation that misleads. `P2`: improvements, refactors, reviews and tasks without a date. When in doubt, the lower priority; raise it when a user is affected.
  - Definition of done: A short guideline with approved P0/P1/P2 criteria (once approved, in the Conventions of this file).
  - References: N/A

- [ ] [P2][blocked] Agree on issue and PR link format
  - Context: Avoid mixed linking styles in technical tracking files. Blocked on the approval of the author.
  - Proposal (2026-10-31): `#123` for the issues and pull requests of this repository and `owner/repo#123` for those of other repositories (for instance, `NREL/EnergyPlus#11409`), which GitHub links in both cases; full URLs only for other sites. `DEVLOG.md` already uses `#N` for this repository; applying it means changing "EnergyPlus pull request 11409" (and 11551) in `DEVLOG.md` and `TODO.md`.
  - Definition of done: One convention applied in `DEVLOG.md`, `TODO.md`, and `ROADMAP.md`.
  - References: N/A

- [ ] [P2][todo] Simulate accim with EnergyPlus 26.1
  - Context: accim accepts EnergyPlus 26.1 since 2026-10-18, but only 26.2 was installed: 26.1 was checked against its IDD and transition rules (from 25.2, only the PIU air terminals change), without simulations. The EMS change of 26.1 (EnergyPlus pull request 11409) is the one that made `InitASTvariables` necessary.
  - Definition of done: EnergyPlus 26.1 installed and the checks of the DEVLOG entry of 2026-10-18 repeated with it (or the version removed from the lists if something fails).
  - References: `DEVLOG.md` (2026-10-18, "EnergyPlus 26.1 and 26.2").

- [ ] [P2][blocked] Review the branch `refactor/sim-v1` and decide what to bring to `master`
  - Context: `refactor/sim-v1` holds the old refactoring towards accim 1.0 (the "1.0.0 clean-break release": new API, modernised docstrings, documentation and notebooks, more tests, and the code review of 2026-07-19), with 36 commits from 2026-05-27 to 2026-07-19 and about 118 files changed. Development went on with 0.7.x in `master` instead (69 commits since the two split at `c03250f`), so the branch was never merged. It was kept on purpose on 2026-10-17, when the other branches were merged into `master` and deleted.
  - Progress (2026-10-31): reviewed against `v1.0.0` in `notes/branch-reviews.md` (20 items: 6 port, 5 adapt, 9 drop; do not merge, v1.0.0 supersedes the refactoring). The five fixes of its PR 1 (`morph_epws`, `WorkspaceArtifactCleaner`, `set_problem()` without outputs, `Table` without `idf_path`, `using_Table.py`) are in the working tree of `v1.0.0`, with tests. Blocked on the author: the target branch of the other PRs (the tests of sim-v1, the golden master in the repository) and the integrity block of `review/refactor-sim-v1-20261024` (`notes/questions.md`).
  - Definition of done: each change of the branch checked against the current `master` and marked as port, adapt or drop; the useful parts brought in small PRs with their tests; then the branch deleted.
  - References: `origin/refactor/sim-v1`; `git log c03250f..origin/refactor/sim-v1`; the CHANGELOG of that branch (1.0.0 entry); `notes/branch-reviews.md`.

- [ ] [P2][blocked] Review the archived branch `feat/comfort-metrics-experiment-api` (tag `archive/feat-comfort-metrics-experiment-api`)
  - Context: Work of 2026-09-30 that was never merged: comfort metric APIs independent of the control (`accim/sim/comfort_metrics.py`, with tests), the workflows of the paper experiments inside the package (`accim/parametric_and_optimisation/paper_experiments.py` and the prepared experiment scripts) and their documentation (`docs/source/comfort_metrics.rst`, README). The branch was deleted on 2026-10-17 and kept as a tag, also on GitHub. It split from `master` at `853e9b4`, 26 commits before the `master` of that day, and part of it may overlap with the hourly indicators added later (`compute_hourly_indicators`). It also brings back the Spanish description of the module for the paper, removed from the repository on 2026-10-16: do not bring that back.
  - Progress (2026-10-31): reviewed in `notes/branch-reviews.md` (9 items: 2 port, 1 adapt, 6 drop): `compute_hourly_indicators` covers the metrics except PMV; port `checked_sum_results` and add `openpyxl` to `install_requires`. Blocked on the author: whether a comfort objective independent of the control, or the PMV indicators, are wanted (`notes/questions.md`).
  - Definition of done: each part marked as port or drop (for example, the comfort metrics that `compute_hourly_indicators` does not cover); the useful parts brought in a PR with their tests; then the tag deleted.
  - References: `git show archive/feat-comfort-metrics-experiment-api`; `git diff --stat 853e9b4 archive/feat-comfort-metrics-experiment-api`; `notes/branch-reviews.md`.

- [ ] [P2][blocked] Review the archived local branch `codex/paper-simple-energy` (local tag `archive/codex-paper-simple-energy`)
  - Context: Work of 2026-10-02/03, made with Codex and never published: simple energy experiments and tutorials for the paper (`examples/paper_experiments/`, with scripts, inputs and documentation pages), and agent validation reports in Spanish (`VALIDACION_*.md`, `REVISION_LAB.md`, `INSTRUCCIONES_TRASLADO.md`). The branch and its Codex worktree were deleted on 2026-10-17. The tag only exists in the local repository of the author: do not push it (avoid `git push --tags`).
  - Progress (2026-10-31): reviewed in `notes/branch-reviews.md` (9 items: 4 paper, 5 drop): nothing belongs in the repository, and what is worth keeping is already with the files of the paper (`llm_project_files/entrega_pc_lab_20261002/`). Blocked on the author: accept that copy and delete the local tag (`git tag -d archive/codex-paper-simple-energy`).
  - Definition of done: decide whether any part belongs in the repository (not the agent reports) or with the files of the paper, move it there, and delete the tag.
  - References: `git show archive/codex-paper-simple-energy`; `git diff --stat 853e9b4 archive/codex-paper-simple-energy`; `notes/branch-reviews.md`.

- [ ] [P2][todo] Findings of the branch reviews still open in `v1.0.0`
  - Context: The reviews of 2026-10-24 and 2026-10-31 (`notes/branch-reviews.md`, section 1.4) list problems inherited from 0.x: `get_accim_args` evaluates IDF text with `eval`; `rename_epw_files` deletes the original EPWs that the user excluded from the renaming; `give_address` calls Nominatim without a timeout and `morph_epws` does not check the exit code of Java; `apply_apmv_setpoints` adds calling managers to the user's EMS programs; the windows of the existing HVAC systems are matched to their zones by substring (`ZONE1` takes those of `ZONE10`); `select_outputs` drops duplicate requests of different IDFs; `Table.wrangled_table(reshaping='pivot')` does not work. The setpoints of comfort standard 6 with `ComfMod` 2 and the orphan ideal loads systems with VRF are questions for the author (`notes/questions.md`).
  - Definition of done: each finding fixed with a test, or documented as intended.
  - References: `notes/branch-reviews.md` (sections 1.1 and 1.4).
