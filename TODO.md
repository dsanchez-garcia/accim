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
  - Definition of done: the author confirms which running mean each one must use (EnergyPlus has no 7-day arithmetic mean: `RMOT` is exponential; B1, done on 2026-11-09, gives it to the custom model only, `custom_outdoor_metric='ndrm'` with `custom_days=7`); if they change, the setpoint lines, `SetComfTemp` and `CountHours` agree, the golden master is updated with `--update-golden`, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/sim/standards.py:114`, `accim/sim/ems/setpoint_lines.py:703` (9) and `:787` (10), `accim/sim/ems/program_lines.py` (`SET_COMF_TEMP`, `COUNT_HOURS`), `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md:350` and `:734`.

- [ ] [P1][todo] Comfort standard 9, comfort mode 1: the heating setpoint out of the applicability limits is that of cooling (pending the author)
  - Context: found with E1. Out of the applicability limits, comfort mode 1 of comfort standard 9 sets `AHST = PMOT*0.078+23.25+2.72+AHSTtol` (category 80) and `+1.5` (category 90), the values of the cooling setpoint, while comfort standards 0 and 10 and comfort mode 0 of 9 use `-2.72` and `-1.5` for the heating setpoint; so the heating and cooling setpoints are equal (but the tolerances) out of the limits. The output IDFs were not changed.
  - Definition of done: the author confirms the sign; if it is a bug, the lines are fixed, the golden master is updated with `--update-golden`, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/sim/ems/setpoint_lines.py:703` (comfort mode 1 of 9), `:687` (comfort mode 0 of 9), `:787` (comfort mode 1 of 10).

- [ ] [P2][todo] E1: the running mean of ASHRAE 55 with a .stat file, and leap years
  - Context: `accim.sim.preview` reproduces the running means of EnergyPlus from the EPW (Engineering Reference 25.2, 19.1). With a .stat file next to the EPW, EnergyPlus takes the running mean of ASHRAE 55 from the monthly means of the .stat file, which `compute_setpoints` does not reproduce (documented); and the running means of EnergyPlus need an EPW of 365 days (a ValueError otherwise; `outdoor_metrics` takes any number of whole days).
  - Definition of done: `energyplus_running_means` reads the .stat file as `ThermalComfort.cc` of EnergyPlus does, and handles EPWs of 366 days, with tests against EnergyPlus.
  - References: `accim/sim/preview.py` (`_energyplus_daily`), `docs/source/4_detailed use.md` §4.3.1.

- [ ] [P2][todo] D2: the columns `Tout_metric`, `HoursBelow_*_<zone>` and `ATHB_PMV_<zone>` in `Table`
  - Context: D2 is done (2026-11-09, `DEVLOG.md`): `Table` reads the CSV files of the IDFs with the setpoints based on the PMV and recognises their outputs (`aPMV_<zone>`, `ePMV_<zone>`, `Expectancy Factor_<zone>` (the `e_<zone>` of the proposal), `Corrected Activity Level_<people>` (the `Activity_corrected_<zone>` of v03), the setpoints and the hours), also in `wrangled_table`. The proposal also names `Tout_metric`, `HoursBelow_*` and, in v03, `ATHB_PMV_<zone>`: outputs of B1 (the configurable outdoor metric of the custom model), B5 (the floor of the heating setpoint) or D1 (`hours_below`) and A4 (ATHB). B1 and B5 are done (2026-11-09): `Tout_metric` and `Tout_metric_<zone>` exist, and `Table` averages them over time (`_AVERAGED_OUTPUTS`); `HoursBelow_<T>_<zone>` exist (EMS outputs summed, in hours, with `report_hours_below` of `AddAccis`); but their names and block and building values in `Table` are not done. `ATHB_PMV_<zone>` waits for A4.
  - Definition of done: `Table` recognises them as the outputs of D2 (names, aggregation over time, block and building values, figures), with tests.
  - References: `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` (D2, A4, B1, B5, D1), `CAMBIOS_CODIGO_v1.2.0.md` §7, §11 and §12.

- [ ] [P1][todo] `verify_accim_simulation`, check 1: the zones whose names have ':' are not checked (found with E2)
  - Context: `verify_accim_simulation` joins the key and the variable of each output as `<key>:<variable>`, and `find_col` splits them at the first ':', so the key of a zone such as `Block1:Zone1` (the sample model) is `BLOCK1`: its operative temperature is not found, and check 1 skips the zone with the warning "No 'Operative Temperature' column found" (seen in the tests of E2, 2026-11-09). `AccimSimulationVerifier._evaluate` splits the names of the columns of the CSV file in the same way. The checks of E2 look the outputs up by key and variable and are not affected. Not changed, since check 1 would then report the mismatches of models where it did nothing.
  - Definition of done: checks 1 and 2 find the outputs of the keys with ':' (from the key and the variable that `read_eso_using_readvarseso` gives), with a test with the sample model, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/utils/verification.py:191` (`find_col`) and `:198`, `tests/core/test_verification.py`.

- [ ] [P2][todo] `AccimSimulationVerifier` has checks 1 and 2 only
  - Context: the object-oriented verifier of `accim.utils.verification` evaluates checks 1 and 2 of `verify_accim_simulation`; checks 3 (the indices derived from the PMV, E2), 4 (the setpoints against `compute_setpoints`, E2 and B1) and 5 (the floor and ceiling of the setpoints, B5) are only in `verify_accim_simulation` (noted with E2 and B5, 2026-11-09).
  - Definition of done: the class runs the same checks as the function (or calls it), with tests, or its docstring points to the function for checks 3 to 5.
  - References: `accim/utils/verification.py` (`AccimSimulationVerifier`, `verify_accim_simulation`).

- [ ] [P1][todo] E1: the running mean of ASHRAE 55 of `energyplus_running_means` is 0.14 °C above that of EnergyPlus with a run period that begins on 8 January (found with B5)
  - Context: in the tests of B5 (2026-11-09), an output IDF of the sample model with the run period from 8 to 14 January, simulated with EnergyPlus 25.1 and `Seville_Present.epw` by timestep, gave 1008 mismatches of `Check4_PMOT` in `verify_accim_simulation`: the PMOT of EnergyPlus (*Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature*) is 10.574306 °C on 8 January and 9.678426 °C on 14 January, and that of `energyplus_running_means('Seville_Present.epw', 6, '08/01')` 10.716667 and 9.820787 °C: 0.142361 °C more (4.27 °C / 30) on every day of the week. With the run periods from 1 January (B1 and B5) and from 15 July (B5), there is no mismatch. The setpoints of the comfort standards that use PMOT (ASHRAE 55, the custom model...) of `compute_setpoints` differ in the same way (check 4); those of B5 use RMOT, which matched. The cause was not looked for, since it is not part of B5.
  - Definition of done: `energyplus_running_means` gives the PMOT of EnergyPlus for the run periods that begin on any day (as `ThermalComfort.cc` calculates it), with a test against EnergyPlus with a run period from 8 January, and `CHANGELOG.md` explains it if the documented behaviour changes.
  - References: `accim/sim/preview.py` (`_energyplus_daily`, `energyplus_running_means`), `accim/utils/verification.py` (`_setpoint_mismatches`), `tests/core/test_setpoint_limits.py` (the weeks of the EnergyPlus tests).

- [ ] [P2][todo] `read_eso_using_readvarseso` keeps only the last 8760 rows of long outputs at timestep frequency (found with B1)
  - Context: with `only_run_period=True` (the default, which `verify_accim_simulation` uses), if the CSV file of ReadVarsESO has no rows of design days (no jump back of the date) and more than 8800 rows, it keeps the last 8760 (`df_all.tail(8760)`), as for an hourly year: the outputs at timestep frequency of a run period of more than about 61 days lose their first days, and check 4 says "Not checked: the last environment of the outputs begins on 14/01, not on the first day of the RunPeriod (01/01)" (74 days, 10656 rows, 2026-11-09). ReadVarsESO itself writes all the rows (10656, with and without the argument `unlimited`). Not changed, since it is not part of B1.
  - Definition of done: the run period is taken without cutting the rows (for instance, from the environments of the ESO file), with a test, and `CHANGELOG.md` explains it as a fix.
  - References: `accim/utils/outputs.py:194` (`read_eso_using_readvarseso`, `only_run_period`), `accim/utils/verification.py` (`_setpoint_mismatches`).
