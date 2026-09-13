---
title: Decisions
type: log
tags: [vault, decisions, adr]
created: 2026-09-13
---

# Decisions

Durable architectural/process decisions for this repository and its Obsidian
vault. Newest first. Use [[templates/decision-record.md|the decision-record
template]] to add a new entry.

## 2026-09-13 — Treat `AGENTS_v2.md` as the current `AGENTS.md`

- **Status**: accepted
- **Context**: The repository does not have a literal `AGENTS.md` file, but
  has [[../AGENTS_v2.md|AGENTS_v2.md]] ("AGENTS.md (v2)"), which defines
  agent design/operation guidelines for this project.
- **Decision**: [[../.github/copilot-instructions.md|Copilot instructions]]
  point to `AGENTS_v2.md` as the file to consult when instructions say
  "`AGENTS.md`, if it exists".
- **Consequences**: If a literal `AGENTS.md` is added later, update the
  Copilot instructions to prefer it (or merge both) instead of
  `AGENTS_v2.md`.

## 2026-09-13 — `notes/work-log.md` complements, not replaces, existing tracking files

- **Status**: accepted
- **Context**: The repository already separates work tracking across
  `CHANGELOG.md`, `DEVLOG.md`, `TODO.md` and `ROADMAP.md` (see
  [[../README.md#0. Development workflow files|Development workflow files]]).
- **Decision**: `notes/work-log.md` is a lightweight, session-scoped log for
  fast context recovery (by humans or an AI assistant). It must not duplicate
  or replace the existing four tracking files; durable outcomes are still
  promoted to them as before.
- **Consequences**: Two logs exist with different scopes. Copilot
  instructions clarify which one to read for which purpose.

## 2026-09-13 — No documentation is duplicated or rewritten for the vault

- **Status**: accepted
- **Context**: The repository already has substantial documentation
  (`README.md`, `CHANGELOG.md`, `DEVLOG.md`, `TODO.md`, `ROADMAP.md`,
  `AGENTS_v2.md`, `docs/source/`, root-level reports).
- **Decision**: [[../Home.md|Home.md]] and vault notes only link to existing
  documentation with wiki links; they never copy or restate its content.
- **Consequences**: Home.md must be revisited if canonical files are renamed
  or restructured (see [[obsidian-tutorial.md#4. What NOT to do|What NOT to
  do]]).

## 2026-09-13 — Vault content stays in English, ASCII, kebab-case

- **Status**: accepted
- **Context**: The rest of the repository's process documentation
  (`CHANGELOG.md`, `DEVLOG.md`, `TODO.md`, `ROADMAP.md`) was already
  translated to English (see `DEVLOG.md`, entry *2026-06-11*). No
  multilingual pair of README/TODO exists to mirror.
- **Decision**: All new vault notes are written in English, with ASCII,
  kebab-case file and folder names under `notes/`. `Home.md` is the single
  intentional exception (Obsidian's conventional vault-index filename).
- **Consequences**: Any future vault note should follow the same convention
  for consistency and predictable linking.

## 2026-09-13 — Use the repository root as the Obsidian vault; ignore `.obsidian/` in git

- **Status**: accepted
- **Context**: The goal is persistent documentation and working context for
  this repository, browsable with Obsidian, without introducing a separate
  vault folder that would fragment the existing file layout.
- **Decision**: The repository root is the Obsidian vault. `.obsidian/` is
  added to `.gitignore` (local UI/workspace/preferences); `Home.md` and
  `notes/` are the versionable vault content.
- **Consequences**: `sync_branch.bat`'s `git clean -fd` was updated to
  exclude `Home.md` and `notes/`, since they are not committed by default and
  would otherwise be deleted as untracked files.
