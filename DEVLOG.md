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

### 2026-09-30
#### [done] Align public documentation with the comfort and paper APIs
- Context: Document the APIs introduced in `a9b9ebd` without changing implementation or unpublished manuscript files.
- Changes: Expanded the guide's signatures, return shapes, metric roles, strict-reducer example, CLI options and resume/migration limits. Added matching README summaries and API navigation; documented source installation and paper-specific requirements. Corrected generic PMV default descriptions, single-IDF versus folder-based version detection, and the distinction between loading consolidated results and resuming checkpoints.
- Files: `README.md`, `README.rst`, `docs/source/comfort_metrics.rst`, requirements/installation pages, both relevant API indexes, `docs/modulo_parametric_and_optimisation_articulo.md`, the prepared handoff README, `CHANGELOG.md`, and `notes/work-log.md`.
- Verification: Documentation-only diff; 20 local links checked, two Python examples parsed with Python 3.9 grammar, and three public signatures compared with source ASTs. `git diff --check` passed. No example execution, tests, Sphinx/autodoc build, project imports, experiments or EnergyPlus runs; rendered documentation and numerical/runtime validation remain pending.
- Next step: Publish this documentation update on `feat/comfort-metrics-experiment-api`; review rendered docs and perform the separately documented checks on the simulation PC.

### 2026-09-30
#### [done] Integrate independent comfort reporting and paper orchestration into ACCIM
- Context: The paper entries must use ACCIM APIs, not local EMS or workflow helpers. Work isolated on `feat/comfort-metrics-experiment-api` at the user's request.
- Changes: Added reporting-only `accim.sim.add_comfort_metrics` and a scoped `SimulationBase` wrapper, strict scalar reducer and package-owned `run_paper_experiment`; all five entries now contain configuration and public package calls only. Added idempotence/collision checks, in-memory/on-disk discovery invalidation, exact LHS signature checks, legacy path-base mapping, finite-area validation and resolution-independent hourly dates. The native moving-reference objective in 4.5 is unchanged; fixed-Fanger outputs remain diagnostics.
- Files: `accim/sim/comfort_metrics.py`, relevant package exports, `accim/parametric_and_optimisation/{main,objectives,paper_experiments}.py`, `setup.py`, two new hermetic test modules, `docs/source/comfort_metrics.rst` and indexes, the six-file prepared handoff, `CHANGELOG.md`, and targeted vault logs.
- Verification: Source/API review and AST parse/compile (Python 3.9 grammar), including checks that entries contain no functions/classes/lambdas or sibling-experiment imports. `git diff --check`; dependency advisory lookup found no known CVEs for openpyxl 3.1.5. Tests were written but not run. No project imports, experiments, sampling, discovery, preflight or EnergyPlus execution. The local pandas-stubs environment warning remains unrelated.
- Next step: Run the hermetic tests in a configured environment and complete numerical/EMS validation on the simulation PC before campaigns; preserve legacy results and reconcile the manuscript count/area/schedule assumptions.

### 2026-09-30
#### [done] Prepare the five paper experiments without running simulations
- Context: Produce a portable handoff from the linked paper files, including the later archived 4.2 corrections, while preserving reference scripts, results and checkpoints.
- Changes: Added five uniquely named scripts and a README under `llm_project_files/experimentos_preparados/`. Experiment 4.4 contains its own occupied fixed-EN metric and import-safe shared utilities; execution, resume, discovery and load are explicit separate operations. Added content-aware checkpoint checks, saved LHS plans, selective energy normalization, per-climate compromise selection and exact hourly CSV/date handling.
- Files: `llm_project_files/experimentos_preparados/*.py`, `llm_project_files/experimentos_preparados/README.md`; session context in `notes/work-log.md` and pending author checks in `notes/questions.md`. Package source and reference artifacts were not changed.
- Verification: Read current API/source and relevant tests as text; parse/compile delivery ASTs without imports or execution; inspect EnergyPlus 9.4 IDD fields as text. Static catalogue intersection gives 40 combinations / 120 cases for 4.1, versus the requested forecast of 132. The archived 4.2 sidecar declares 300/300; the inspected hourly CSV header lacks PMOT/setpoints. No experiments, samplers, discovery, preflight or EnergyPlus simulations were executed. The IDE's unrelated pandas-stubs compatibility warning was left unchanged.
- Next step: Follow the handoff README on the simulation PC; resolve count/area/schedule differences and validate EMS numerics, worker transport, output contracts and resume before new campaigns. Update manuscript claims separately.

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


