---
title: Home
type: vault-index
tags: [vault, index, accim]
created: 2026-09-13
---

# accim — Vault Home

This is the entry point of the Obsidian vault for the **accim** repository
(Adaptive-Comfort-Control-Implemented Model). The vault root **is** the
repository root: no files were moved or duplicated to build it.

This note only links to existing documentation. Canonical technical content
still lives in the linked files themselves — read it there, not here.

## What is accim

ACCIM transforms fixed-setpoint EnergyPlus building energy models into
adaptive-setpoint models. See [[README.md#2. How to use|How to use accim]] in
the main README for the short version.

## Project documentation

- [[README.md|README]] — main project overview, citation list, usage and funding (English).
- [[README.rst|README.rst]] — short English abstract used for the PyPI project page.
- [[README.md#0. Development workflow files|Development workflow files]] — how `CHANGELOG.md`, `DEVLOG.md`, `TODO.md` and `ROADMAP.md` relate to each other.
- [[CHANGELOG.md|CHANGELOG]] — user-facing release notes (see the "Unreleased" section near the top).
- [[DEVLOG.md|DEVLOG]] — internal technical log ([[DEVLOG.md#Entries|entries]]).
- [[TODO.md|TODO]] — active short-term tasks ([[TODO.md#Backlog|backlog]]).
- [[ROADMAP.md|ROADMAP]] — medium/long-term initiatives ([[ROADMAP.md#Initiatives|initiatives]]).
- [[AGENTS_v2.md|AGENTS.md (v2)]] — guidelines for LLM-based agents working on this repo ([[AGENTS_v2.md#1. Objetivo|goals, in Spanish]]).
- [[tests/README.md|Tests README]] — how to run the test suite ([[tests/README.md#Running Tests|running tests]]).
- [[LICENSE|LICENSE]]

> No English/Spanish duplicate pair was found for README or TODO: `README.md`
> and `README.rst` are both English (the `.rst` file is a short abstract used
> for PyPI, not a translation). Notes in this vault link to both as-is.

## Published documentation (Sphinx / Read the Docs)

Full docs are published at https://accim.readthedocs.io/en/master/ and built
from `docs/source/`:

- [[docs/source/index.rst|Sphinx table of contents]]
- [[docs/source/1_requirements.md|1. Requirements]]
- [[docs/source/2_installation.md|2. Installation]]
- [[docs/source/3_quick tutorial.md|3. Quick tutorial]]
- [[docs/source/4_detailed use.md|4. Detailed use]]
- [[docs/source/5_troubleshooting.md|5. Troubleshooting]]
- [[docs/source/9_pickle_comparison_tutorial.md|9. Pickle comparison tutorial]]
- [[docs/source/6_citation.md|6. Citation]]
- [[docs/source/7_credits.md|7. Credits]]
- [[docs/source/8_pdfs_for_prev_versions.md|8. PDFs for previous versions]]

## Recent technical reports (existing, not modified)

These pre-existing reports remain in Spanish, at the repository root, as
canonical documents. They are linked here, not copied:

- [[INFORME_REVISION_PARAMETRIC_2026-07-25.md|Informe de revision — parametric_and_optimisation (2026-07-25)]]
- [[PLAN_IMPLEMENTACION_PARAMETRIC_2026-07-25.md|Plan de implementacion — parametric_and_optimisation (2026-07-25)]]
- [[informe_exp_4_3_parametric_apmv_w-figs.md|Informe de ejecucion — exp_4_3_parametric_apmv_w-figs.py]]

## Vault working notes (English, new for Obsidian)

- [[notes/README.md|notes/README]] — short guide to this vault.
- [[notes/obsidian-tutorial.md|Obsidian tutorial for this project]] — how to use this vault day to day.
- [[notes/work-log.md|Work log]] — reverse-chronological session log.
- [[notes/decisions.md|Decisions]] — durable architectural/process decisions.
- [[notes/questions.md|Open questions]] — pending questions and blockers.
- [[notes/references.md|References]] — sources, datasets and external resources.
- [[notes/templates/daily-note.md|Template: daily note]]
- [[notes/templates/decision-record.md|Template: decision record]]
- `notes/attachments/` — folder for pasted/dragged files (images, PDFs, etc.).

## How this vault is organized

See [[notes/obsidian-tutorial.md|the Obsidian tutorial]] for local Obsidian
configuration (attachments, new-note location, templates, wiki links) and for
day-to-day usage conventions.
