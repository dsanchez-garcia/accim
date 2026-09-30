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

## 2026-09-30 — Promote paper helpers into ACCIM APIs

- **Objective**: Make all five paper entries configuration-only and integrate their independent comfort/reporting capabilities into ACCIM on a new branch.
- **Affected files**: Package metric/workflow APIs and tests; [[../docs/source/comfort_metrics.rst|API guide]]; [[../llm_project_files/experimentos_preparados/README.md|handoff]]; [[../CHANGELOG.md]], [[../DEVLOG.md]] and [[decisions.md]].
- **Finding or decision**: Reporting metrics are opt-in and separate from controllers; 4.5 retains its original objective. Entry scripts no longer contain helpers or import each other. See the API guide and development log for implementation details.
- **Validation**: Source review, AST syntax/contracts, whitespace/link checks and dependency advisory lookup only; no tests or simulations executed. Prepared hermetic tests for subsequent use. Branch: `feat/comfort-metrics-experiment-api`.
- **Next step**: Publish the requested branch, install it on the simulation PC and complete the handoff's pending numerical/EMS checks before execution.

## 2026-09-30 — Prepare the paper experiment handoff without simulation

- **Objective**: Prepare five portable paper experiments while preserving all reference scripts and existing campaign artifacts.
- **Affected files**: [[../llm_project_files/experimentos_preparados/README.md|Handoff README]] and its five linked scripts; [[../DEVLOG.md]]; [[questions.md]].
- **Finding or decision**: Execution/resume and result-only loading are separate; 4.4 owns its fixed occupied EN metric and shared helpers. Source inspection exposes a 4.1 count mismatch and missing hourly regression variables in the inspected archived 4.2 CSV; details are in the handoff, not duplicated here.
- **Validation**: AST parsing/compilation and API/IDD text inspection only. No experiment, sampling, discovery, preflight or EnergyPlus execution. References and checkpoints were not modified.
- **Next step**: Perform the handoff's numerical/EMS and portability checks on the simulation PC, then reconcile manuscript counts, schedules and metric definitions.

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
