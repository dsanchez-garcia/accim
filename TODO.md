# TODO

Active short-term tasks.

## Conventions

- Use priorities: `P0` (critical), `P1` (high), `P2` (normal).
- Use status tags: `todo`, `in progress`, `blocked`.
- Reference issue/PR links when available.
- When a task is completed, move the outcome to `DEVLOG.md`.

## Task template

```md
- [ ] [P1][todo] Short title
  - Context:
  - Definition of done:
  - References:
```

## Backlog

- [ ] [P1][blocked] Activate the version `v1.1.0` in Read the Docs
  - Context: 1.1.0 is published on PyPI and GitHub (2026-11-08), and `latest` and `master` show 1.1.0. Read the Docs created the version `v1.1.0` of the tag (slug `v1.1.0`, commit `33f2cae8`), but it is inactive (`/en/v1.1.0/` gives 404), and activating it needs the session of the author: Versions, `v1.1.0`, Edit, Active, Update version (`docs/README.md` §2). Blocked on the author.
  - Definition of done: `https://accim.readthedocs.io/en/v1.1.0/` says "accim 1.1.0 documentation", with its PDF and EPUB; `docs/README.md` §2 lists the active tags up to `v1.1.0`.
  - References: `packaging/README.md` §4.10, `docs/README.md` §2.

- [ ] [P1][blocked] Define backlog priority rules
  - Context: Standardize entry criteria for new tasks. Blocked on the approval of the author.
  - Proposal (2026-10-31): `P0`: it stops users or a release now (a crash or wrong results in a published version, lost data, a security problem); it goes before anything else. `P1`: needed for the next release, or wrong behaviour that has a workaround, failing tests, or documentation that misleads. `P2`: improvements, refactors, reviews and tasks without a date. When in doubt, the lower priority; raise it when a user is affected.
  - Definition of done: A short guideline with approved P0/P1/P2 criteria (once approved, in the Conventions of this file).
  - References: N/A

- [ ] [P2][blocked] Agree on issue and PR link format
  - Context: Avoid mixed linking styles in technical tracking files. Blocked on the approval of the author.
  - Proposal (2026-10-31): `#123` for the issues and pull requests of this repository and `owner/repo#123` for those of other repositories (for instance, `NREL/EnergyPlus#11409`), which GitHub links in both cases; full URLs only for other sites. `DEVLOG.md` already uses `#N` for this repository; applying it means changing "EnergyPlus pull request 11409" (and 11551) in `DEVLOG.md` and `TODO.md`.
  - Definition of done: One convention applied in `DEVLOG.md`, `TODO.md`, and `ROADMAP.md`.
  - References: N/A
