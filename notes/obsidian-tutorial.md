---
title: Obsidian tutorial for accim
type: tutorial
tags: [vault, guide, obsidian]
created: 2026-09-13
---

# Obsidian tutorial for this project

This note explains how Obsidian is set up for the **accim** repository and
how to use it day to day. It assumes no prior Obsidian experience.

## 1. Opening the vault

The repository root (`D:\Python\accim`) **is** the Obsidian vault. In
Obsidian, choose *Open folder as vault* and select the repository root
(not a subfolder). Obsidian will create a local `.obsidian/` config folder
at the root the first time you open it; this folder is git-ignored (see
[[decisions.md|decisions]]) and never versioned.

## 2. Local configuration already applied

The following settings are pre-configured in `.obsidian/` so a fresh clone
behaves consistently for every contributor who opens it:

- **Attachments**: new attachments (images, PDFs, pasted files) are stored in
  `notes/attachments/`.
- **New notes**: created in `notes/` by default.
- **Templates folder**: `notes/templates/`.
- **Links**: wiki links (`[[...]]`), written as **relative** paths, and
  automatically rewritten across the vault when a file is renamed or moved.
- **Core plugins enabled**: file explorer, search, graph view, backlinks,
  outgoing links, templates, command palette, properties and canvas.

If any of these plugins are missing in your Obsidian version, enable them
manually under *Settings → Core plugins*.

## 3. Everyday usage

### Navigating

- Start from [[../Home.md|Home]] — it links to every existing piece of
  documentation (README, CHANGELOG, DEVLOG, TODO, ROADMAP, published docs,
  reports) and to all vault notes.
- Use **Backlinks** and **Outgoing links** (bottom of the right sidebar, or
  the panes for a given note) to see what links to/from the note you have
  open.
- Use **Graph view** (`Ctrl/Cmd+G` or the graph icon) to visualize how notes
  and documents connect.
- Use the **Command palette** (`Ctrl/Cmd+P`) for any Obsidian action, and the
  **Quick switcher** (`Ctrl/Cmd+O`) to jump to a note by name.

### Writing notes

- Prefer **wiki links** over plain text: `[[TODO.md#Backlog]]` instead of
  writing out a path in prose.
- Link to a heading with `#`: `[[TODO.md#Backlog]]` links straight to the
  *Backlog* section (Obsidian resolves the anchor by the exact heading text,
  not a slugified version, so match the heading verbatim). Avoid anchoring
  to headings that themselves contain square brackets (e.g. CHANGELOG's
  `[Unreleased]`) — nested brackets are unreliable inside `[[...]]` syntax;
  link to the file itself instead.
- Add a short YAML frontmatter block (**Properties**) at the top of new
  notes, for example:

  ```yaml
  ---
  title: My note
  tags: [example]
  created: 2026-09-13
  ---
  ```

  Properties are editable from the small table Obsidian renders at the top
  of the note, or directly as YAML in source mode.

### Using templates

1. Open the **Command palette** (`Ctrl/Cmd+P`).
2. Run *Templates: Insert template*.
3. Pick [[templates/daily-note.md|daily-note]] to start a new work session
   entry, or [[templates/decision-record.md|decision-record]] to log a new
   decision.
4. `{{date}}` / `{{time}}` placeholders are filled in automatically by the
   Templates plugin using the date/time format configured in
   `.obsidian/templates.json`.

### Canvas

Use *New canvas* (command palette) for freeform diagrams (e.g. sketching the
`parametric_and_optimisation` data flow). Save canvases under `notes/` and
attach exported images to `notes/attachments/` if needed.

## 4. What NOT to do

- Do not copy README/CHANGELOG/DEVLOG/TODO/ROADMAP/AGENTS_v2.md content into
  new notes — link to it instead.
- Do not rename existing canonical documentation files from inside Obsidian
  unless that is the explicit goal of your task; renaming updates links
  automatically, but the repository's own tooling (Sphinx `docs/source/`,
  `setup.py`, badges in `README.md`) may reference paths independently of
  Obsidian.
- Do not commit `.obsidian/` — it is git-ignored on purpose (local UI state,
  workspace layout, device-specific paths).

## 5. Keeping context for future sessions

See [[work-log.md]] for the expected entry format, and
[[../.github/copilot-instructions.md|Copilot instructions]] for how an AI
assistant is expected to use this vault automatically.
