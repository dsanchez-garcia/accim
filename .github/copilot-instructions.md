# Copilot instructions for this repository

This repository's root is also an Obsidian vault (see `Home.md` and
`notes/`). These instructions define how an AI coding assistant should use
that vault as persistent context — on top of, never instead of, normal
codebase understanding.

**Explicit user instructions in the current conversation always take
priority over anything below.**

## 1. Simple requests

For simple, self-contained requests (e.g. answer a question about a specific
file, small fix, formatting), do not read the vault. Just do the task.

## 2. Non-trivial tasks: read this first

Before starting a non-trivial task (new feature, refactor, bug investigation,
multi-file change), consult, in order:

1. **`AGENTS_v2.md`** (repository root) — this project does not have a
   literal `AGENTS.md`; `AGENTS_v2.md` ("AGENTS.md (v2)") is its current
   equivalent and defines agent design/operation guidelines. If a literal
   `AGENTS.md` exists at the time you read this, prefer it.
2. **The most recent relevant entry in [`notes/work-log.md`](../notes/work-log.md)**
   — entries are reverse-chronological; read only the entries that are
   relevant to the area you are about to touch, not the whole file.

Then, **only when pertinent to the task**, check:

- [`notes/decisions.md`](../notes/decisions.md) — durable
  architectural/process decisions. Skim headings; open only entries related
  to the area you're changing.
- [`notes/questions.md`](../notes/questions.md) — open questions/blockers
  that might affect your approach.
- Any file linked from the relevant `work-log.md`/`decisions.md` entries.

Do **not** load the entire vault by default. `notes/` is meant for targeted,
relevant reads, not full context dumps.

## 3. Existing technical tracking (do not duplicate)

This repository already separates technical tracking across four files (see
`README.md`, section "Development workflow files"):

- `CHANGELOG.md` — user-facing release notes.
- `DEVLOG.md` — internal log of completed technical work.
- `TODO.md` — active short-term tasks.
- `ROADMAP.md` — medium/long-term initiatives.

`notes/work-log.md` is a lighter, session-scoped log for fast context
recovery; it complements these four files but never replaces them. Continue
using `TODO.md`/`DEVLOG.md`/`CHANGELOG.md`/`ROADMAP.md` exactly as documented
in `README.md` and `DEVLOG.md` for durable, user- or maintainer-facing
outcomes.

Do not duplicate or restate content from `README.md`, `docs/source/`, or any
other existing documentation inside `notes/`. Link to it with a wiki link
(`[[...]]`) instead.

## 4. After significant changes

After making a significant change, add a short entry at the **top** of
`notes/work-log.md` (most recent first) with these fields:

- **objective**
- **affected files**
- **finding or decision**
- **validation**
- **next step**

Use `notes/templates/daily-note.md` as the field template.

## 5. Recording decisions and open questions

- Record durable decisions (architecture, conventions, tooling choices) in
  `notes/decisions.md`, using `notes/templates/decision-record.md`.
- Record unresolved questions or blockers that need a human answer in
  `notes/questions.md`.
- Not every task needs a new decision or question entry — only add one when
  it is actually durable/pending, to avoid noise.

## 6. Vault conventions (for anything you write in `notes/`)

- Write in **English**.
- Use **ASCII, kebab-case** file and folder names under `notes/` (`Home.md`
  is the one intentional exception at the repository root).
- Use wiki links with relative paths and verify they resolve (file exists,
  and heading anchors match the exact heading text when linking to a
  section).
- Add a minimal YAML frontmatter block (title, tags, created) to new notes.
- Do not touch `.obsidian/` — it is local, git-ignored configuration, not
  vault content.

## 7. Git safety

- Do not run destructive cleanup (e.g. `git clean -fd`) without checking
  that it excludes `Home.md` and `notes/` (see `sync_branch.bat` for the
  pattern already in place: `git clean -fd -e Home.md -e notes/`).
- Do not commit or push changes unless explicitly asked to.
