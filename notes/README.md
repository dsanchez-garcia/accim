---
title: notes/README
type: guide
tags: [vault, guide]
created: 2026-09-13
---

# Vault notes — short guide

This folder holds everything created **for the Obsidian vault itself**. It
does not duplicate technical documentation, tasks or code that already exist
elsewhere in the repository (see [[../Home.md|Home]] for links to those).

## Contents

- [[obsidian-tutorial.md]] — how to use Obsidian for this specific project.
- [[work-log.md]] — reverse-chronological log of work sessions (objective, files, finding/decision, validation, next step).
- [[decisions.md]] — durable architectural/process decisions (lightweight ADR log).
- [[questions.md]] — open questions and blockers that need a human answer.
- [[references.md]] — external sources, datasets and resources (no content duplication, links only).
- [[templates/daily-note.md]] — template used to start a new work-log entry.
- [[templates/decision-record.md]] — template used to record a new decision.
- `attachments/` — local folder for images, PDFs and other files dropped into notes.

## Conventions

- All content in this folder is written in **English**.
- File and folder names are **ASCII** and **kebab-case** (`Home.md` is the
  one intentional exception, as the vault's index note).
- Use wiki links (`[[...]]`) to cross-reference notes and existing repository
  files; do not copy their content here.
- Keep entries short. Link out to the canonical file (README, CHANGELOG,
  DEVLOG, TODO, ROADMAP, AGENTS_v2.md, `docs/source/`) instead of repeating it.

## Relationship with existing tracking files

This repository already tracks work through `CHANGELOG.md`, `DEVLOG.md`,
`TODO.md` and `ROADMAP.md` (see
[[../README.md#0. Development workflow files|Development workflow files]]).
`notes/work-log.md` does **not** replace them: it is a lighter, session-level
log meant to give an AI assistant (or a returning contributor) fast context
at the start of a session. Durable outcomes should still be promoted to the
existing tracking files as usual.
