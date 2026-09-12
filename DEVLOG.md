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


