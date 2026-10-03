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
