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

- [ ] [P1][in progress] Release accim 1.0.0
  - Context: Branch `v1.0.0` (refactoring to PEP 8, Python API backend), merged into the local `master` by fast-forward on 2026-11-01 (to `a4a3e164`). `master` is not pushed yet: `packaging/README.md` (§4.8) pushes it after PyPI, because Read the Docs then builds `latest` from it. Later on 2026-11-01, `v1.0.0` got the arguments of each zone (`zone_arguments`), the corrected hour counters with the percentage of the occupied hours within the setpoints (`accim.data.postprocessing.setpoint_hours`), `ex_mm` for any existing HVAC system and a GUI in English (`accim-gui`); on 2026-11-02, after the answers of the author, the descriptive names of the arguments, attributes and parameters in the whole package, including the parametric module (the names of 0.x stay as deprecated aliases), and seven tabs in the GUI,   and then the fixes of the findings of the branch reviews (`notes/branch-reviews.md`, 1.4) and of the two P2 items of `Table` and the parametric notebooks;   and later on 2026-11-02, the existing HVAC systems that keep the operative temperature between the setpoints (the arguments `existing_hvac_*`, decided with the author); on 2026-11-03, after the answers of the author to the P2 items, the radiant systems that follow the setpoints (`existing_hvac_radiant_setpoints`), the `existing_hvac_*` arguments in the GUI, the rows of ESP CTE and INT ISO7730 in the full sets, the heating setpoints of CHN Yang with comfort mode 2 (corrected by the author) and the simulations with EnergyPlus 26.1; and, later on 2026-11-03, the sessions saved in a pickle file and a readable JSON file (`Table.save`/`Table.load`, `accim.utils.save_session`/`load_session`, and the menu *Session* of the GUI). So `master` must be fast-forwarded again.
    - Definition of done: the author reviews the branch and merges it; `CHANGELOG.md` gets the date; accim and accim-samples 1.0.0 are published as in `packaging/README.md`.
    - References: `CHANGELOG.md` (Unreleased), `DEVLOG.md` (2026-10-30, 2026-11-01, 2026-11-02, 2026-11-03).

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
