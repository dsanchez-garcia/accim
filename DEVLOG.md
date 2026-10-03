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


