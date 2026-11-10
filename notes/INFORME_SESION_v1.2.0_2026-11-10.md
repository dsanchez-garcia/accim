---
title: Session report, accim v1.2.0 (2026-11-09 and 2026-11-10)
type: report
tags: [vault, report, v1.2.0]
created: 2026-11-10
---

# Session report: the proposals of accim 1.2.0 (2026-11-09 and 2026-11-10)

Branch `v1.2.0` of `D:\DSG\accim` (the same repository as `D:\Python\accim` on the other computer). The task of the
author (2026-11-09): implement, end to end and in this order, every proposal of
[[PROPUESTAS_MEJORAS_post_1.1.0_v03.md]] that was not implemented yet, E1 → D2 → E2 → A3 → B1 → B5 → C1 → D1 → B2 → B3 →
B4 → C2 → E4 → A4 → A6, with the rules and the decisions D1–D12 of [[COPILOT_BRIEF_v1.2.0_v01.md]]; A2, A1 and A5 were
done before; E3 and C3 are out of scope (C3 only as the initiative R-06 of `ROADMAP.md`). Each proposal has its entry in
[[../DEVLOG.md]] (context, changes, files, verification), in [[../CHANGELOG.md]] (Unreleased) and a section of
[[../CAMBIOS_CODIGO_v1.2.0.md]] (in Spanish); this report summarises them and does not repeat their details.

## 1. Proposals implemented, and their commits

Every commit was pushed to `origin/v1.2.0` right after it was made (no force-push, no history rewritten).

| Order | Proposal | Commit | Status | CAMBIOS |
| :--- | :--- | :--- | :--- | :--- |
| 1 | E1: the setpoints of the ACCIS without EnergyPlus (`accim.sim.preview`) | `dcb5ddf` | done | §8 |
| 2 | D2: `Table` with the simulations of the setpoints based on the PMV | `aff9cfc` | done (first part) | §7 |
| 3 | E2: `verify_accim_simulation` checks what the EMS calculates | `622bc7d` | done | §9 |
| 4 | A3: the catalogue of adaptive coefficients of the aPMV, and the coefficient by the sign of the PMV | `9cfac72` | done | §10 |
| 5 | B1: the outdoor metric of the custom model | `aedfa3a` | done | §11 |
| 6 | B5: the floor and ceiling of the setpoints, and the occupied hours below some temperatures | `c2e0f44` | done | §12 |
| 7 | C1: the parameters of the occupants, of the new indices and of the custom model in the parametric module | `25152d4` | done | §13 |
| 8 | D1: the indicators of the long-term thermal discomfort (CEN/TR 16798-2) | `2f139de` | done | §14 |
| 9 | B2: several regimes of the custom model | `ab767df` | done; the outdoor metric of each regime blocked | §15 |
| 10 | B3: comfort standards defined by their data (YAML) | `975f796` | done; the data of Qatar and several regimes blocked | §16 |
| 11 | B4: JPN Aqilah 2025, the built-in comfort standard 23 | `2be69e2` | done; arguments of its static setpoints blocked | §17 |
| 12 | C2: long-term comfort objectives of the optimisation | `9f26f39` | done; Method C and CIBSE TM52/TM59 blocked | §18 |
| 13 | E4: future weather files with pyfwg | `c6ee7df` | done; the notebook blocked (no jar of the tool) | §19 |
| 14 | A4: the setpoints of the adaptive thermal heat balance (ATHB) with the API backend | `689362d` | done | §20 |
| 15 | A6: the setpoints of the standard effective temperature (SET) and of the PPD | `c8e127c` | done; the cooling effect and the Erl way blocked | §21 |
| — | C3: the initiative R-06 in `ROADMAP.md` (the text of v03, §5) | `9e7d54f` | done (roadmap only) | — |
| — | D2, completed: the optional outputs of the ACCIS and of the ATHB in `Table` | `eec5f8e` | done | §22 |

- D2 was done before E1, against the order: it was in progress when the plan of the author arrived. Its outputs of A4,
  B1 and B5 did not exist then, so they waited in `TODO.md`; once A4 was done, they were added at the end (with those of
  B2 and C2, of the same kind), so D2 is complete.
- Before this list, on the same branch: A2 and A1 (before 2026-11-09) and A5 (`6a6267d`, 2026-11-09).

## 2. Deviations from the v03 prompts, and why

The adjustments of the brief (§3) and the decisions D1–D12 were applied as given; the deviations below are those
beyond them. The names of the code (the task: "The code is the truth for the current API") replace those of v03 in
every proposal (`clothing_insulation` and `activity_level`, not `clo` and `met`; `Expectancy Factor_<zone>`, not
`e_<zone>`...).

- **E1.** v03 says that the running means calculated from the weather file have no start-up transient, but EnergyPlus
  25.1 begins the running mean of CEN 15251 with its equation 19.82 not divided by 1 − α⁷ (5.92 °C instead of 8.34 °C on
  1 January in Seville), so `compute_setpoints` reproduces EnergyPlus (D9). A new public function,
  `accim.utils.get_setpoint_ems_programs`, since the text of `get_setpoint_ems_code` cuts the subprograms. Extra
  columns (`ACSTnoTol`, `AHSTnoTol`) and arguments (`timesteps_per_hour`, `start_date`, `frequency`). The running mean of
  ASHRAE 55 from a .stat file is not reproduced (`TODO.md`).
- **D2.** Besides the renaming of v03, four faults of `Table` found with these simulations were fixed: the CSV files
  `<IDF>[<EPW>.csv` stopped it; the indices, coefficients and setpoints were added up over time; the corrected activity
  level was taken for an energy; and the energy per m² of the block and building totals was infinite without the floor
  areas (now NaN). The outputs of the metabolic correction get the name of the zone only for the People objects of one
  zone; `PMV_<zone>` and `Occupied hours_<zone>` keep their EMS names (the same names as other columns). In the
  completion, the outdoor metric of each zone keeps its EMS name, so that no name contains another one, and the outputs
  of C2, which v03 does not list in D2, are included with the names of the indicators of D1.
- **E2.** The checks of `Tout_metric` (B1) and of the floor and ceiling (B5) were added when those outputs existed (in
  B1 and B5). Check 4 (the setpoints against `compute_setpoints`) covers every comfort standard, not only those of the
  registry of B3. Check 3 needs timestep outputs (hourly means break the formulas). The metabolic correction is checked
  with the exact relation of the EMS (factor = 1 − 0.067·PMV of the previous timestep), not with the 5.5–6.1 % band of
  the brief, which is its result.
- **A3.** A key of the catalogue fills only the argument it is given (the design text says both; the prompt does not,
  and the defaults are numbers); with `adaptive_coefficient_by='pmv_sign'`, each setpoint is converted into the PMV
  setpoint of the thermostat with the λ of its side (not in v03); the keys are resolved in the engine
  (`PmvIndex.resolve`) and in `generate_df_from_args`; the GUI fills the numbers of the catalogue instead of passing keys.
- **B1.** The EMS code of the metric is only in the output IDFs whose zones use a metric other than `'pmot'` (v03:
  always in comfort standard 99), so the output IDFs of 1.1.0 do not change. `SetAST_CS99_0` and `SetVST` use
  `Tout_metric` too, while `SetAppLimits` does not compare the metric in accim (v03 names SetComfTemp, SetAppLimits and
  COUNT_HOURS). The test of `rmot_alpha` (0.8) against the RMOT of EnergyPlus is after 21 days, not 14 (0.10 K on day 15,
  because of the start of EnergyPlus above). `Check4_Tout_metric` compares with `compute_setpoints`, not with
  `outdoor_metrics`. The end of each hour is `Minute > 59.5`, because the built-in variable `TimeStepsPerHour` is 0 at
  BeginTimestepBeforePredictor in EnergyPlus 25.1 (found while testing).
- **B5.** The floor and ceiling are a program of each zone, `ApplySetpointLimits_<zone>`, run right after SetAST, which
  bounds ACST and AHST and runs ROUNDING again, instead of lines at the end of the subprograms of SetAST: the same
  setpoints (checked with the Erl interpreter), the shared subprograms do not change, and no sentinel values are needed.
  The parametric classes keep the names of v03 (`HeatingSetpointFloor`, `CoolingSetpointCeiling`). The winter week of
  the tests begins on 1 January, not 8 January, because of a finding of E1 (`TODO.md`). D5: no floor or ceiling for the
  setpoints based on the PMV.
- **C1.** The parameters are named as the arguments of accim (the brief); `activity_level` is in W/person (82.8–417.6,
  with the body surface area of 1.8 m²); the inputs of the PMV are not parameters of the accim models, which have
  temperature setpoints; `AdaptiveCoefficientCooling/Heating` were added (missing); `custom_regime_parameters(n)` was done
  with B2. A fault found while testing was fixed: `custom_alpha` before `custom_outdoor_metric` in a sample lost its
  value.
- **D1.** The tests follow D8 instead of Table D.1. `Table` gives Methods A and B (Method C needs the PMV and its limits)
  in a new attribute, `long_term_indicators`, with a row for each simulation, not as columns of `Table.df`; the warm and
  cold periods are those of the range (above and below it), not seasons. `deviation_check` uses the percentages of
  Table E.1 (43.75 h a month), since its hours ("33 / 58 of 166 h") do not match 20 % and 50 %.
- **B2.** One program for each zone, `SelectCustomRegime_<zone>` (the conditions of the HVAC system read the sensors of
  the zone), not one `SelectCustomRegime`; it writes the inputs `m`, `n` and `CustAST_*`, not `ACSToffset` or `ACSTall`,
  which ApplyCAT and SetAppLimits overwrite. D6: the appended regime is that of the scalar inputs of `SetInputData_<zone>`
  (no `else`), not a frozen copy. A new output, `CustomRegime_<zone>` (not in v03). The outdoor metric of each regime is
  not implemented (`ValueError` unless None; blocked). The same regimes in every zone of comfort standard 99; the factory
  of the parametric module covers the eight coefficients, not the thresholds of the conditions.
- **B3.** One regime 'always' for each definition (several: blocked); comfort mode 2 only with the categories 80 and 90
  (the ISO 7730 values of the code); the metrics that the EMS calculates go through the inputs of the zone
  (`CustAST_metric`, `CustAST_alpha`, `CustAST_days`, shared with the custom model), with the new fields `alpha` and
  `days`; `load_comfort_standards` registers by default; the YAML file of Qatar is shipped incomplete and rejected (v03
  gives neither its metric, nor its band, nor its limits; blocked). A negative slope is written intercept first (Erl
  rejects a minus sign after a multiplication sign). Beyond the prompt: the branches of SetVST, the parametric module and
  its parallel processes (the registry is passed to them), the GUI and its session files, `epw` for the registered
  comfort standards whose metric the EMS calculates.
- **B4.** v03 has no prompt for B4 (the design comes from its scientific basis and D1/D2). The running mean is the RMOT
  of EnergyPlus (as comfort standard 1), not the `rmot_alpha` of the YAML file of B3; the static setpoints 20/28 °C are
  literal, configurable through a comfort standard defined by its data with the same data (no new arguments; blocked if
  the author wants them); its code is at the end of the chains (`BUILT_IN_BRANCHES`), so the other output IDFs do not
  change (7 in-memory golden files gained its code, additions only); models of earlier versions with 23 raise a
  `ValueError`; no notebook (v03 asks for none).
- **C2.** No prompt. The EMS counts the indicators (`report_long_term_discomfort`, False by default), since the reducers
  of besos receive one output each; the range is that of the setpoints of the ACCIS without the tolerance, not fixed
  ranges of EN 16798-1; the building is the sum of its zones; Method C is not counted (blocked); the weekly and monthly
  deviations of Table E.1 are not constraints (they are checked after the simulations; `TODO.md`); the setpoints based on
  the PMV raise a `ValueError`.
- **E4.** No prompt. `morph_epws(engine='java' | 'pyfwg')`, Java by default, instead of delegating to pyfwg whenever it
  is installed (the default behaviour does not change); only the global tool; the typical meteorological years of
  pyweatherfiles are taken as EPW paths (no conversion); no notebook (no jar of the Future Weather Generator on this
  machine; blocked). Found: the Java engine gives the tool 8 positional arguments, while pyfwg gives 12 to its version 3
  (`TODO.md`).
- **A4.** Full air-conditioning only; the setpoints in every timestep; a range of 10–30 °C; the ATHB_PMV of each zone from
  its air and mean radiant temperatures; no cache (about 1 ms for each zone and timestep). Test (3) of v03 (the ATHB_PMV
  within the setpoints with the HVAC on) does not hold strictly (the VRF of the sample model exceeds the cooling setpoint
  by up to 1 K while it cools), so the tests check instead that the setpoints are those of the bisection with the sensors
  of the zone. `verify_accim_simulation` and the GUI do not handle these setpoints (`TODO.md`).
- **A6.** No prompt. Only the way (b) of v03 (a hook of the API backend), with the setpoints tabulated by relative
  humidity (0–100 %, every 1 %) when the hook is made and interpolated in the callbacks, because `set_tmp` of
  pythermalcomfort 4.8.1 stops EnergyPlus 25.1 with an access violation inside the callbacks of the API (also with a
  warm-up and with a stack of 64 MB; `pmv_athb` works there); hence no output of the SET of the zones. No defaults for the
  SET setpoints, the metabolic rate, the clothing and the air speed (v03 gives none). The setpoints of the PPD are those
  of the PMV of `apply_pmv_setpoints` (documented, also category IV). The Erl way (a) and the cooling effect: blocked.
- **C3.** The text of R-06 is that of v03 (§5), unchanged.

## 3. Entries added to TODO.md

22 new tasks are open, and one changed. Three other tasks of the session were done within it and removed: the checks
of E2 that waited for B1 and B5 (done with them), `custom_regime_parameters(n)` of C1 (done with B2) and the rest of D2
(`eec5f8e`).

Blocked (see section 6):

- [P2] B2: an outdoor metric for each regime of the custom model (pending the author).
- [P2] B4: arguments for the static setpoints of JPN Aqilah 2025 (pending the author).
- [P2] B3: the data of the comfort model of Qatar of the sample files (pending the author).
- [P2] B3: several regimes of a comfort standard defined by its data (pending the author).
- [P2] C2: Method C (the PPD-weighted hours) as an objective of the optimisation (pending the author).
- [P2] C2 and D1: the overheating criteria of CIBSE TM52 and TM59 (documents not available).
- [P2] E4: the How-to notebook of the future weather files, and the test with the tool (pending the jar of the Future
  Weather Generator).
- [P2] A6: the setpoints of the cooling effect of the elevated air speed, and the proportional control in Erl (pending
  the author).

To do (found during the session, or the parts of a proposal that can be done later):

- [P1] `Table` with `source_frequency='timestep'` and `standard_outputs=True` drops all the outputs (found with D1).
- [P1] Comfort standards 9 and 10 (IND IMAC R 7DRM and 30DRM): their running means look swapped (pending the author).
- [P1] Comfort standard 9, comfort mode 1: the heating setpoint out of the applicability limits is that of cooling
  (pending the author).
- [P1] `verify_accim_simulation`, check 1: the zones whose names have ':' are not checked (found with E2).
- [P1] E1: the running mean of ASHRAE 55 of `energyplus_running_means` is 0.14 °C above that of EnergyPlus with a run
  period that begins on 8 January (found with B5).
- [P2] B2: check 4 of `verify_accim_simulation` with the conditions `'hvac_off'` and `'hvac_on'`.
- [P2] The full table of the setpoints lacks JPN Aqilah 2025 (23).
- [P2] C2: the weekly and monthly deviations of Table E.1 as constraints of the optimisation.
- [P2] E4: the command line of `morph_epws(engine='java')` may not be that of the current versions of the Future Weather
  Generator (to check with the jar).
- [P2] A4 and A6: the setpoints of the ATHB and of the SET in the model, for `verify_accim_simulation`, the GUI and to make
  the hooks again.
- [P2] A6: the SET of pythermalcomfort in the callbacks of EnergyPlus (the cause of the access violation).
- [P2] E1: the running mean of ASHRAE 55 with a .stat file, and leap years.
- [P2] `AccimSimulationVerifier` has checks 1 and 2 only.
- [P2] `read_eso_using_readvarseso` keeps only the last 8760 rows of long outputs at timestep frequency (found with B1).

Changed: [P2] A5, the clothing insulation as a function of the outdoor temperature, from blocked to to do: it waited for
E1, which is done; the list of the author counts A5 as done, so it waits for the author.

## 4. Provisional decisions in notes/questions.md

36 entries, each "decided provisionally, pending author", with the most conservative option that keeps the behaviour
and the output IDFs of before (the options and reasons are in [[questions.md]]):

- E1 — the running means of the first days of the weather file in `outdoor_metrics`: a year that repeats (the first days
  take the last days of the file, as EnergyPlus does for ASHRAE 55).
- E2 — what the metabolic correction of the ePMV is checked against: the exact relation of the EMS (factor = 1 −
  0.067·PMV of the previous timestep), with `calculation_tolerance`.
- A3 — whether a key of the catalogue in one coefficient also sets the other: no, each argument takes the coefficient of
  its own side.
- A3 — with `'pmv_sign'`, which λ converts each setpoint: each setpoint with the λ of its side (the inverse of the aPMV
  with λ by the sign).
- B1 — whether every model of the custom model has the EMS code of the outdoor metric: only those whose zones use a
  metric other than `'pmot'`.
- B1 — which programs use `Tout_metric`: every program where the custom model uses its outdoor temperature (SetComfTemp,
  `SetAST_CS99_0`, `CountHours_<zone>`, `SetVST`).
- B1 — on which day the programs begin with the values of the weather file: the first day of the first RunPeriod (the
  PMOT of EnergyPlus otherwise).
- B1 — T0 of `te_ref_nl` before the first hour of the day has ended: the outdoor temperature of the timestep.
- B1 — the arguments of the outdoor metric in `modify_accis`: None by default, keeping the values of each zone.
- B5 — where the floor and ceiling bound the setpoints: a program of each zone after SetAST that rounds again.
- B5 — the floor and ceiling in `modify_accis`: None by default, keeping those of each zone.
- B5 — the outputs of `report_hours_below`: with every `output_type` but `'custom'`, also with the setpoints based on
  the PMV, `p` and `m` in the names of the temperatures.
- B5 — a floor above the cooling setpoint, or a ceiling below the heating setpoint: as v03 writes the lines, documented.
- C1 — the parameters types of the inputs of the PMV: `'apmv setpoints'` and `'epmv setpoints'` only.
- C1 — the units and range of `activity_level`: W/person, with a warning out of 82.8–417.6 W/person.
- C1 — the outdoor metric of the custom model as a parameter: the codes of the metrics, the days rounded, the weather
  file of `modify_accis` kept, and the inputs kept while the metric is `'pmot'`.
- C1 — the plans with a floor not lower than the ceiling: left out (also in the full sets of the custom models).
- D1 — the warm and cold periods of the indicators of `Table`: above and below the range, not by season.
- D1 — what `Table(long_term_indicators=True)` gives: Methods A and B in a new attribute, one row for each simulation.
- D1 — the gaps of CEN/TR 16798-2: a PMV equal to the upper limit is within the range; `deviation_check` uses the
  percentages of Table E.1.
- B2 — an outdoor metric for each regime: not available yet (`ValueError`); the regimes use the metric of the zone.
- B2 — how the program of the regimes sets the custom model: one program of each zone that writes the inputs of the
  custom model before SetAppLimits, without `else`.
- B2 — the meaning of the conditions: the cooling season of SetAST_Master, the HVAC of ApplyAST_<zone> (mixed mode
  only), and the metric conditions as the applicability limits of the ACCIS (`<`, `>`, and `<=` within).
- B2 — the regimes in the zones and in the parametric module: the same regimes in all the zones of comfort standard 99;
  the eight coefficients of each regime as parameters.
- B3 — what `load_comfort_standards` does by default: it registers (`register=True`).
- B3 — comfort mode 2 and the outdoor metric: comfort mode 2 only with the categories 80 and 90; the metric through the
  inputs of the zone.
- B3 — one regime for each comfort standard defined by its data: one regime 'always'.
- B3 — the data of Qatar of the sample files: the data of v03 with the missing keys empty, so that the file is rejected
  with the names of the keys (nothing invented).
- B4 — how the static setpoints of JPN Aqilah 2025 are configurable (D2): literal 20 and 28 °C, and other values
  through a comfort standard defined by its data; no new arguments.
- B4 — the running mean of JPN Aqilah 2025: the RMOT of EnergyPlus, as INT EN16798.
- C2 — Method C as an objective: not counted (no choice of PMV or limits is made for the author).
- C2 — how the objectives reach the optimisation, and with which range: EMS counters on request (False by default), the
  limits of D1 and of the other hour counters, the constraint bound of the simulated period.
- E4 — how `morph_epws` delegates to pyfwg, and what "accepts TMY of pyweatherfiles" means: on request (`engine`), the
  global tool only, and the TMY as EPW files given by path.
- A4 — the models, hours and range of the setpoints of the ATHB: full air-conditioning, every timestep, 10–30 °C (an
  argument).
- A6 — which setpoints of SET, PPD or cooling effect: the way (b) with the table; the way (a) and the cooling effect
  wait for the author.
- D2, completed — the names in `Table` of the optional outputs: the outdoor metric of each zone keeps its EMS name; the
  outputs of C2 with the names of the indicators of D1; no block and building values for the regime and the metric of
  the zones.

## 5. Tests and backend comparisons

The whole suite, `py -m pytest tests/core tests/parametric_and_optimisation -q -p no:cacheprovider` (Python 3.14, about
17 minutes), after the last commit of code (`eec5f8e`): **1783 passed, 2 skipped**. The two skipped tests need what this
machine does not have: the jar of the Future Weather Generator (`ACCIM_FWG_JAR`, E4) and EnergyPlus 26.1.

| Proposal | New tests | Whole suite after it | Golden master |
| :--- | :--- | :--- | :--- |
| D2 | 29 | 1490 passed, 1 skipped | unchanged |
| E1 | 30 (2 against EnergyPlus 25.1) | 1521 passed, 1 skipped | unchanged |
| E2 | 12 (2 against EnergyPlus 25.1) | 1533 passed, 1 skipped | unchanged |
| A3 | 6, and the GUI | 1539 passed, 1 skipped, 1 failed (a '≥' in a label of the GUI, which cp1252 cannot print, replaced by '>='; then that test and those of the GUI passed) | unchanged |
| B1 | 34, and 2 of the GUI | 1573 passed, 1 skipped, 1 failed (a test that called `_generation_arguments` without the new arguments, which got defaults); then 1576 passed, 1 skipped | unchanged |
| B5 | 20 (3 with EnergyPlus), 2 parametric, 2 of the GUI | 1600 passed, 1 skipped | unchanged |
| C1 | 8 | 1608 passed, 1 skipped | unchanged |
| D1 | 9, and 2 of the GUI | 1618 passed, 1 skipped | unchanged |
| B2 | 20, 4 parametric, 2 of the GUI | 1644 passed, 1 skipped | unchanged |
| B3 | 43, 5 parametric, 2 of the GUI | 1695 passed, 1 skipped | unchanged |
| B4 | 13 | 1707 passed, 1 skipped, 2 failed (two tests that took 23 for a comfort standard that does not exist, and literal chains), fixed: their files 65 passed; the next run of the suite (C2) passed | 7 in-memory golden files gained the code of 23 (additions only); the 22 configurations of `AddAccis` unchanged |
| C2 | 22 counters, 6 objectives, the GUI | 1738 passed, 1 skipped | unchanged |
| E4 | 10 (1 skipped without the jar) | `tests/core`: 1240 passed, 2 skipped | unchanged |
| A4 | 12 (2 with EnergyPlus 25.1) | 1759 passed, 2 skipped | unchanged |
| A6 | 6 (1 with EnergyPlus 25.1) | 1765 passed, 2 skipped | unchanged |
| D2, completed | 18 (1 with EnergyPlus 25.1) | 1783 passed, 2 skipped | unchanged |

The documentation build (`py -m sphinx -E -b html docs/source docs/_build/html -w docs/_build/sphinx_warnings.txt`) had
the same warnings as the build before it in every proposal (59 lines; the entry of D2 reports 55 lines for its build);
from E1 on, the modules changed by each proposal compile with Python 3.9 (besos is not installed there, so the
parametric package is only compiled). Until C2, the one skipped test was that of EnergyPlus 26.1; from E4 on, the test
with the jar of the Future Weather Generator is the second one.

The proposals that changed EMS code were simulated with `run_ep(backend='ems')` and `run_ep(backend='api')` (EnergyPlus
25.1, `Seville_Present.epw`, the sample model): the results were identical in every case (largest difference 0.0 in
every column, or `check_exact=True` in the tests).

| Proposal | Simulations (rows × columns) | Largest difference | Time, ems / api |
| :--- | :--- | :--- | :--- |
| A3 | `pmv_sign` with `gbt50785_cold_general`, 24 April – 7 May, timestep and hourly: 2016 × 81 | 0.0 | 5.0 / 7.4 s |
| B1 | three of five simulations by timestep: `rmot_alpha` and `te_ref_nl` (8496 rows), `rmot_alpha` (0.7) and `rmot` without the EPW (8496 rows), `rmot_alpha` and `pmot` in mixed mode (5904 rows) | 0.0 | 13.5 / 16.2, 12.8 / 16.2, 9.5 / 13.1 s |
| B5 | a winter and a summer week, timestep, floor, ceiling and counters: 1008 × 108 each | 0.0 | 5.7 / 7.0, 4.1 / 6.5 s |
| B2 | April `vrf_ac` (1008 × 102), June `vrf_mm` with `'hvac_off'` (1008 × 113); and a test, 10 days hourly, `check_exact=True` | 0.0 | 4.7 / 6.3, 4.3 / 6.9 s |
| B3 | JPN Aqilah 2025 (101) April `vrf_ac` (1008 × 103), June `vrf_mm` (1008 × 114), a comfort standard 102 in January (1008 × 100) | 0.0 | 5.4 / 7.7, 4.5 / 8.1, 4.1 / 6.6 s |
| B4 | comfort standard 23: January `vrf_ac` (1008 × 100), April `vrf_mm` (1008 × 111), June `vrf_mm` (1008 × 111) | 0.0 | 5.4 / 7.0, 4.4 / 7.4, 4.3 / 7.0 s |
| C2 | January `vrf_ac` (1008 × 112), April `vrf_mm` (1008 × 123), July `vrf_mm` (1008 × 123) | 0.0 | 6.2 / 8.1, 4.8 / 7.4, 4.4 / 7.1 s |
| A4 | the model prepared for the ATHB, without the hook, a week by timestep (a test, `check_exact=True`) | identical | — |

No EMS code changed in D2, E1, E2, C1, D1, E4, A6 and the completion of D2 (A6 only adds sensors when the setpoints are
applied; the comparison of A4 still passes).

## 6. Blocked items, and the exact information that is missing

- **B2, an outdoor metric for each regime.** The author has to choose its meaning: whether the conditions compare the
  metric of the zone and the selected regime then sets `Tout_metric` to its own metric, and with which `alpha` and
  `days` (those of the zone or of each regime).
- **B3, the comfort model of Qatar (Indraganti 2018) of the sample files.** Its outdoor metric (one of
  `OUTDOOR_METRICS`, with α or days), its applicability limits, its categories with their offsets, and its comfort modes
  with the static setpoints of comfort modes 0 and 1: v03 gives none of them.
- **B3, several regimes of a comfort standard defined by its data.** The schema of the YAML files and the meaning of
  the regimes (with the conditions of B2).
- **B4, arguments for the static setpoints of JPN Aqilah 2025.** Whether the author wants new arguments (for instance
  `static_heating_setpoint` and `static_cooling_setpoint` of `AddAccis`, `modify_accis` and `zone_arguments`), inputs
  of the zones, or the current comfort standard defined by its data.
- **C2, Method C as an objective.** The PMV and its limits (and the models) with which the EMS would count the
  PPD-weighted hours.
- **C2 and D1, CIBSE TM52 and TM59.** The texts of the documents (out of the scope of the session, D12).
- **E4, the How-to notebook and the test with the tool.** The jar of the global Future Weather Generator (and the
  Java version it needs) on the machine, in `ACCIM_FWG_JAR`.
- **A6, the cooling effect and the Erl way.** The design of the setpoints by cooling effect (which index is kept within
  which setpoints, and whether the air speed or the temperature is controlled), and whether the proportional control in
  Erl of v03 (with its delay and oscillation) is wanted.
- **A5, the clothing insulation as a function of the outdoor temperature** (not in this list of the author): its form,
  `callable(rmot) -> clo` written as a `Schedule:File` from the weather file through E1, or as Erl by sections.

## 7. Environment

- Python 3.14 (`py`), and Python 3.9 for the compatibility checks. EnergyPlus 9.4, 9.6, 25.1 (with its Python API), 25.2
  and 26.2; EnergyPlus 26.1 is not installed.
- Installed from PyPI during the session, for the extras of the proposals: pyfwg 0.4.0 (E4, `accim[weather]`) and
  pythermalcomfort 4.8.1 (A4 and A6, `accim[comfort]`, Python 3.11 or later; it adds numba and llvmlite). pyweatherfiles
  0.0.0 was already installed.
- No jar of the Future Weather Generator on the machine (Java 1.8.0_481 is installed).
