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

- [ ] [P2][todo] Add schema-heterogeneity tests for split-by grouped outputs
  - Context: Contract is to keep realistic per-group schemas when `drop_all_empty_output_columns=True`.
  - Definition of done: Tests assert different output-column sets across groups and downstream handling expectations.
  - References: `accim/parametric_and_optimisation/main.py`, `tests/parametric_and_optimisation/10_test_outputs_preflight.py`

- [ ] [P2][todo] Export again the documentation pages of `wf4` and `wf5`
  - Context: The executed copies in `docs/source/jupyter_notebooks/parametric_and_optimisation_examples/` ran before `ea4392d`, so on Read the Docs the MCDM figure and summary of `wf4` and `wf5` still label the temperature objective in kWh/m2 (e.g. `Annual mean operative temperature FLOOR_1_ZONE=23.1 kWh/m2`). Updating them means running both notebooks again with EnergyPlus: about 7 min for `wf4` and 3 min for `wf5` with their default settings. The other 13 pages that call `reduce_runtime` (all but tutorial 09) also print its old wording ("... days" for the timesteps per hour and the maximum figures in shadow overlap); refreshing them is optional and needs a run of all the notebooks (about 30 min).
  - Definition of done: `wf4` and `wf5` are run with `docs/prepare_parametric_notebooks.py run` on a commit that includes `ea4392d`, exported with `export` and merged into `master`; their MCDM figures and summaries show the temperature objective without kWh/m2.
  - References: [dsanchez-garcia/accim#2](https://github.com/dsanchez-garcia/accim/pull/2) (notes for reviewers), `docs/prepare_parametric_notebooks.py`, `DEVLOG.md` (2026-10-16).

