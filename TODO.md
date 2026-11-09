# TODO

Active short-term tasks.

## Conventions

- Use priorities:
  - `P0` (critical): it stops users or a release now (a crash or wrong results in a published version, lost data, a security problem); it goes before anything else.
  - `P1` (high): needed for the next release, or wrong behaviour that has a workaround, failing tests, or documentation that misleads.
  - `P2` (normal): improvements, refactors, reviews and tasks without a date.
  - When in doubt, the lower priority; raise it when a user is affected.
- Use status tags: `todo`, `in progress`, `blocked`.
- Reference issues and pull requests when available: `#123` for those of this repository and `owner/repo#123` for those of other repositories (for instance, `NatLabRockies/EnergyPlus#11409`, the repository of EnergyPlus, formerly `NREL/EnergyPlus`), which GitHub links in both cases (as plain text: not inside code spans); full URLs only for other sites.
- When a task is completed, move the outcome to `DEVLOG.md`.

## Task template

```md
- [ ] [P1][todo] Short title
  - Context:
  - Definition of done:
  - References:
```

## Backlog

- [ ] [P2][blocked] A5: the clothing insulation as a function of the outdoor temperature
  - Context: A5 is done (2026-11-09, `DEVLOG.md`): the activity level and the clothing insulation by season and `'dynamic_ashrae55'` in `set_pmv_input_parameters`, as the prompt of the proposal asks, and `accim.sim.people.set_clothing_method`, with the `schedule` that the author chose (`notes/decisions.md`). The design of the proposal also has the clothing insulation as a function of the outdoor temperature (`callable(rmot) -> clo`), written as a `Schedule:File` from the EPW "vía E1" (`compute_setpoints`, not implemented) or as Erl by sections. Blocked on E1, which the author asked for on 2026-11-09 for 1.2.0 (with D2 and E2).
  - Definition of done: as the author decides, with tests, documentation and `CHANGELOG.md`.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v02.md` (A5 and E1), `CAMBIOS_CODIGO_v1.2.0.md` §4.

- [ ] [P2][blocked] D2: the columns `Tout_metric`, `HoursBelow_*_<zone>` and `ATHB_PMV_<zone>` in `Table`
  - Context: D2 is done (2026-11-09, `DEVLOG.md`): `Table` reads the CSV files of the IDFs with the setpoints based on the PMV and recognises their outputs (`aPMV_<zone>`, `ePMV_<zone>`, `Expectancy Factor_<zone>` (the `e_<zone>` of the proposal), `Corrected Activity Level_<people>` (the `Activity_corrected_<zone>` of v03), the setpoints and the hours), also in `wrangled_table`. The proposal also names `Tout_metric`, `HoursBelow_*` and, in v03, `ATHB_PMV_<zone>`: outputs of B1 (the configurable outdoor metric of the custom model), B5 (the floor of the heating setpoint) or D1 (`hours_below`) and A4 (ATHB), which accim does not have and which the author has not asked for in 1.2.0. Blocked on B1, B5, D1 and A4.
  - Definition of done: `Table` recognises them as the outputs of D2 (names, aggregation over time, block and building values, figures), with tests.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` (D2, A4, B1, B5, D1), `CAMBIOS_CODIGO_v1.2.0.md` §7.
