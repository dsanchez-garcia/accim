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

- [ ] [P2][todo] A5: the clothing insulation as a function of the outdoor temperature
  - Context: A5 is done (2026-11-09, `DEVLOG.md`): the activity level and the clothing insulation by season and `'dynamic_ashrae55'` in `set_pmv_input_parameters`, as the prompt of the proposal asks, and `accim.sim.people.set_clothing_method`, with the `schedule` that the author chose (`notes/decisions.md`). The design of the proposal also has the clothing insulation as a function of the outdoor temperature (`callable(rmot) -> clo`), written as a `Schedule:File` from the EPW "vía E1" or as Erl by sections. It was blocked on E1, which is done (2026-11-09: `accim.sim.preview.outdoor_metrics` gives the running means of each hour of an EPW); the author's list of proposals for this session (2026-11-09) counts A5 as done, so it waits for the author.
  - Definition of done: as the author decides, with tests, documentation and `CHANGELOG.md`.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v02.md` (A5 and E1), `CAMBIOS_CODIGO_v1.2.0.md` §4 and §8.

- [ ] [P1][todo] Comfort standards 9 and 10 (IND IMAC R 7DRM and 30DRM): their running means look swapped (pending the author)
  - Context: found while checking `accim.sim.preview.compute_setpoints` (E1) against EnergyPlus. Comfort standard 9 is IMAC-R with the 7-day running mean (`9 = IND IMAC R 7DRM`) and 10 with the 30-day one, and v03 lists IMAC-R as `Tc = 0.39·T7DRM + 18.4` and `Tc = 0.42·T30DRM + 17.6` (Aqilah 2025, Table 1, citing Rawal et al.). But the setpoints of comfort standard 9 (`0.39·x + 18.42`) use `PMOT`, the 30-day mean of ASHRAE 55 in EnergyPlus, and those of 10 (`0.42·x + 17.6`) use `RMOT`, the running mean of CEN 15251 (α = 0.8, 7 days at the start); `SetComfTemp` uses `PMOT` for both, and `CountHours_<zone>` `PMOT` for 9 and `RMOT` for 10. The output IDFs were not changed (the session must not change them without the proposal or the author). The intercept is 18.42 in the code and 18.4 in v03.
  - Definition of done: the author confirms which running mean each one must use (EnergyPlus has no 7-day arithmetic mean: `RMOT` is exponential; a true 7DRM would need B1); if they change, the setpoint lines, `SetComfTemp` and `CountHours` agree, the golden master is updated with `--update-golden`, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/sim/standards.py:114`, `accim/sim/ems/setpoint_lines.py:703` (9) and `:787` (10), `accim/sim/ems/program_lines.py` (`SET_COMF_TEMP`, `COUNT_HOURS`), `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md:350` and `:734`.

- [ ] [P1][todo] Comfort standard 9, comfort mode 1: the heating setpoint out of the applicability limits is that of cooling (pending the author)
  - Context: found with E1. Out of the applicability limits, comfort mode 1 of comfort standard 9 sets `AHST = PMOT*0.078+23.25+2.72+AHSTtol` (category 80) and `+1.5` (category 90), the values of the cooling setpoint, while comfort standards 0 and 10 and comfort mode 0 of 9 use `-2.72` and `-1.5` for the heating setpoint; so the heating and cooling setpoints are equal (but the tolerances) out of the limits. The output IDFs were not changed.
  - Definition of done: the author confirms the sign; if it is a bug, the lines are fixed, the golden master is updated with `--update-golden`, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/sim/ems/setpoint_lines.py:703` (comfort mode 1 of 9), `:687` (comfort mode 0 of 9), `:787` (comfort mode 1 of 10).

- [ ] [P2][todo] E1: the running mean of ASHRAE 55 with a .stat file, and leap years
  - Context: `accim.sim.preview` reproduces the running means of EnergyPlus from the EPW (Engineering Reference 25.2, 19.1). With a .stat file next to the EPW, EnergyPlus takes the running mean of ASHRAE 55 from the monthly means of the .stat file, which `compute_setpoints` does not reproduce (documented); and the running means of EnergyPlus need an EPW of 365 days (a ValueError otherwise; `outdoor_metrics` takes any number of whole days).
  - Definition of done: `energyplus_running_means` reads the .stat file as `ThermalComfort.cc` of EnergyPlus does, and handles EPWs of 366 days, with tests against EnergyPlus.
  - References: `accim/sim/preview.py` (`_energyplus_daily`), `docs/source/4_detailed use.md` §4.3.1.

- [ ] [P2][blocked] D2: the columns `Tout_metric`, `HoursBelow_*_<zone>` and `ATHB_PMV_<zone>` in `Table`
  - Context: D2 is done (2026-11-09, `DEVLOG.md`): `Table` reads the CSV files of the IDFs with the setpoints based on the PMV and recognises their outputs (`aPMV_<zone>`, `ePMV_<zone>`, `Expectancy Factor_<zone>` (the `e_<zone>` of the proposal), `Corrected Activity Level_<people>` (the `Activity_corrected_<zone>` of v03), the setpoints and the hours), also in `wrangled_table`. The proposal also names `Tout_metric`, `HoursBelow_*` and, in v03, `ATHB_PMV_<zone>`: outputs of B1 (the configurable outdoor metric of the custom model), B5 (the floor of the heating setpoint) or D1 (`hours_below`) and A4 (ATHB), which accim does not have and which the author has not asked for in 1.2.0. Blocked on B1, B5, D1 and A4.
  - Definition of done: `Table` recognises them as the outputs of D2 (names, aggregation over time, block and building values, figures), with tests.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` (D2, A4, B1, B5, D1), `CAMBIOS_CODIGO_v1.2.0.md` §7.
