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
