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
  - Context: Branch `v1.0.0` (refactoring to PEP 8, Python API backend), merged into the local `master` by fast-forward on 2026-11-01 (to `a4a3e164`). `master` is not pushed yet: `packaging/README.md` (§4.8) pushes it after PyPI, because Read the Docs then builds `latest` from it. Later on 2026-11-01, `v1.0.0` got the arguments of each zone (`zone_arguments`), the corrected hour counters with the percentage of the occupied hours within the setpoints (`accim.data.postprocessing.setpoint_hours`), `ex_mm` for any existing HVAC system and a GUI in English (`accim-gui`); on 2026-11-02, after the answers of the author, the descriptive names of the arguments, attributes and parameters in the whole package, including the parametric module (the names of 0.x stay as deprecated aliases), and seven tabs in the GUI, and then the fixes of the findings of the branch reviews (`notes/branch-reviews.md`, 1.4) and of the two P2 items of `Table` and the parametric notebooks. So `master` must be fast-forwarded again.
  - Definition of done: the author reviews the branch and merges it; `CHANGELOG.md` gets the date; accim and accim-samples 1.0.0 are published as in `packaging/README.md`.
  - References: `CHANGELOG.md` (Unreleased), `DEVLOG.md` (2026-10-30, 2026-11-01, 2026-11-02).

- [ ] [P2][todo] `sampling_full_set()` drops ESP CTE (`comfort_standard` 0) when the plan has `category` or `comfort_mode`
  - Context: `drop_invalid_param_combinations()` takes `category` and `comfort_mode` as 'n/a' for `comfort_standard` 0 (its setpoints depend on neither), so with the predefined models a full set such as `{'comfort_standard': [0, 1], 'category': [1, 2]}` simulates no row of `comfort_standard` 0, without a warning; likewise, INT ISO7730 (22) is only kept with `comfort_mode` 0. As in 0.8.2 (with the parameters `ComfStand`, `CAT` and `ComfMod`). Since 1.0.0, both work with any category and comfort mode in the simulation (see `DEVLOG.md`, 2026-10-31), so the rows are only repeated simulations.
  - Definition of done: the author decides whether to keep one row of these standards for each combination of the other parameters (the first value of `category` and `comfort_mode`), to warn when they are dropped, or to keep the current behaviour (documented in the migration guide, 9.3); with a test.
  - References: `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py` (`valid_params`), `tests/parametric_and_optimisation/test_param_accis_filter.py`.

- [ ] [P2][todo] Check the setpoints of comfort standard 6 (CHN Yang) with comfort mode 2 against the source of the standard
  - Context: In `accim/sim/ems/setpoint_lines.py`, key `(6, 2)`, the heating setpoint uses, within the applicability limits (-7 to 30 °C), the formula of the cooling setpoint (`PMOT*0.30+25.9` with category 80, `PMOT*0.30+23.6` with 90), as in 0.x. With comfort mode 3, the heating setpoint is `PMOT*0.32+14.88` (category 80) or `PMOT*0.31+17.14` (90), and with comfort mode 2 outside the limits it is static and lower than the cooling one (19 and 22 °C against 25 and 27 °C with category 80). The category offsets of this standard are 0, so within the limits both setpoints are equal: 30.4 °C for a PMOT of 15 °C with category 80, against a heating setpoint of 19.7 °C with comfort mode 3. The author decided on 2026-10-31 to keep them until they are checked (`notes/decisions.md`).
  - Definition of done: the formulas of `(6, 2)` and `(6, 3)` checked against the source of the model of Yang; if they are wrong, fixed with a test, the golden master written again (configuration `b01`, `--update-golden`) and a CHANGELOG entry; if they are right, the reason added to the decision.
  - References: `accim/sim/ems/setpoint_lines.py` (`(6, 2)`, `(6, 3)`), `accim/sim/ems/program_lines.py` (`SetAppLimits`, `ApplyCAT`), `accim/sim/standards.py`, `notes/branch-reviews.md` (section 1.4).

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

- [ ] [P2][todo] Simulate accim with EnergyPlus 26.1
  - Context: accim accepts EnergyPlus 26.1 since 2026-10-18, but only 26.2 was installed: 26.1 was checked against its IDD and transition rules (from 25.2, only the PIU air terminals change), without simulations. The EMS change of 26.1 (EnergyPlus pull request 11409) is the one that made `InitASTvariables` necessary.
  - Definition of done: EnergyPlus 26.1 installed and the checks of the DEVLOG entry of 2026-10-18 repeated with it (or the version removed from the lists if something fails).
  - References: `DEVLOG.md` (2026-10-18, "EnergyPlus 26.1 and 26.2").
