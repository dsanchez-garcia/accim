---
title: Open questions
type: log
tags: [vault, questions]
created: 2026-09-13
---

# Open questions

Pending questions or blockers that need a human decision. Newest first.
Move a question to [[decisions.md]] once it is resolved (and delete or mark
it here as answered).

## How to use this file

```md
## YYYY-MM-DD — Short question
- Context:
- Why it matters:
- Options considered:
- Owner:
- Status: open | answered (see [[decisions.md]])
```

## Open

## 2026-11-10 — C2: how the long-term comfort objectives reach the optimisation, and with which range
- Context: v03 (C2) asks for `hours_outside_range` (Method A), `degree_hours` (Method B) and `ppd_weighted_hours`
  (Method C) of CEN/TR 16798-2:2019, Annex D, in `objectives.py`, by zone and building and by warm and cold period,
  "with the categories of EN 16798-1 as ranges", and the deviations of Table E.1 as constraints; it has no prompt, and
  the brief no adjustment. The reducers of besos get one output (`EPResults`) each, so they cannot combine the
  operative temperature, the limits and the occupants that the functions of D1 need.
- Options considered: (a) the EMS counts the indicators in each timestep (summed EMS outputs of each zone and of the
  building), opt-in, and the reducers sum them; (b) only after the simulations (`Table(long_term_indicators=True)` of
  D1), which a parametric study can use but an optimisation cannot; (c) reducers of the operative temperature with fixed
  limits, which cannot leave out the hours without occupants. For the range: (i) the setpoints without the tolerance of
  the ACCIS (`AHSTnoTol`, `ACSTnoTol`), those of the hour counters of accim and of `Table(long_term_indicators=True)`,
  which are the limits of the categories of EN 16798-1 with INT EN16798 (1) within its applicability; (ii) fixed ranges
  of the categories (Table B.2 of EN 16798-1, for instance), independent of the comfort model of the control. For the
  building: (1) the sums of the zones, as D1; (2) their means, as `add_building_averages`.
- Owner: the author.
- Status: open; (a), (i) and (1) decided provisionally (`report_long_term_discomfort=False` by default, so the output
  IDFs do not change; the same limits as D1 and the other hour counters; the EnergyPlus comfort status of
  `hours_outside_comfort` stays the objective independent of the control), pending author. The constraint bound of
  `deviation_constraint_bound` is that of the simulated period (the yearly criterion); the weekly and monthly ones are
  checked after the simulations (`TODO.md`). The setpoints based on the PMV are left out (`ValueError`): their zones do
  not keep the setpoints of the ACCIS.

## 2026-11-10 — C2: Method C (the PPD-weighted hours) as an objective
- Context: Method C weighs each occupied hour outside the range with PPD(PMV)/PPD(PMVlimit) (ISO 7730:2025, formula
  (5)). The models with temperature setpoints do not calculate the PMV (the Fanger model of their People objects only
  with `setpoint_type='pmv'`), and the setpoints based on the PMV control an index (aPMV, ePMV or PMV) whose setpoints
  are not PMV limits but for the PMV index.
- Options considered: (a) not counted until the author chooses (blocked task in `TODO.md`); (b) the EMS of
  `accim.sim.pmv_index` counts it with the PMV of each zone and the PMV setpoints of its thermostats without the
  tolerance (the inverse of the setpoints of the index), only for the PMV index or for all; (c) the models with
  temperature setpoints get the Fanger model and fixed PMV limits of a category of EN 16798-1 (their output IDFs change,
  and their PMV depends on clothing, activity and air speed that they do not set).
- Owner: the author.
- Status: open; (a) decided provisionally (the most conservative: no output IDF changes and no choice of PMV or limits
  is made for the author), pending author.

## 2026-11-09 — B4: the running mean of JPN Aqilah 2025 (comfort standard 23)
- Context: the model of Aqilah et al. (2025, equation 8) uses `Trm = α·Trm−1 + (1 − α)·Tod−1` with α = 0.8 (McCartney
  & Nicol, equation 7), "started a week before the day of the survey" (v03, B4). EnergyPlus calculates the running mean
  of CEN 15251 with α = 0.8 (RMOT, Engineering Reference 19.1, equation 19.82: the same recursion, begun with a sum of 7
  days that is not divided by 1 − α⁷), which INT EN16798 (1) uses; B1 gives the EMS the exact recursion (`rmot_alpha`,
  begun with the weather file), which needs the EMS code of the outdoor metric in the output IDFs and `epw`.
- Options considered: (a) RMOT of EnergyPlus, as INT EN16798: the comfort standard has literal lines, no EMS code of the
  outdoor metric and no inputs of it in its zones; (b) `rmot_alpha` of B1, as the YAML file of the sample files (101).
  They differ by less than 0.05 °C after three weeks with `Seville_Present.epw` (section 4.2.2 of the detailed use).
- Owner: the author.
- Status: open; option (a) decided provisionally (as the other comfort standards with this running mean; (b) is
  available as a comfort standard defined by its data), pending author.

## 2026-11-09 — B4: how the static setpoints of JPN Aqilah 2025 are configurable (decision D2)
- Context: decision D2 says that the static setpoints of comfort mode 1 are 20.0 °C for heating and 28.0 °C for
  cooling "by default, configurable", documented as a choice of the user; it does not say how. The setpoints of the
  built-in comfort standards are literal lines of the EMS, and their arguments are those of `AddAccis`.
- Options considered: (a) 20 and 28 °C in the lines of comfort standard 23 (comfort modes 0 and 1), and other values
  through a comfort standard defined by its data with the same data and other `static_setpoints` (B3; the YAML file
  of the sample files is a copy to edit), without new arguments; (b) new arguments of `AddAccis`, `modify_accis` and
  `zone_arguments` (for instance `static_heating_setpoint` and `static_cooling_setpoint`), inputs of the zones of
  comfort standard 23 that its lines read, with the GUI and the parametric module; (c) inputs of the zones without
  arguments (edited in `SetInputData_<zone>`).
- Owner: the author.
- Status: open; option (a) decided provisionally (no new arguments, which are hard to take back; (b) can be added
  later without breaking anything), pending author. `TODO.md` has the task.

## 2026-11-09 — B3: the data of the comfort model of Qatar of the sample files
- Context: decision D11 asks that the YAML files of B3 ship with the two examples of v03, JPN Aqilah 2025 and Qatar
  (Indraganti & Boussaa 2018, offices with HVAC). For Qatar, v03 (B3 and §11.5) gives the comfort temperature
  (`Tc = 0.049·Tr + 22.5`), the citation and the statistics (N = 3742, R² = 0.015, SE = 0.007, p < 0.001; `Tr` with mean
  30.7 °C and SD 6.4; mean comfort temperature 24.0 °C), but writes "—" for its band, its applicability and its metric:
  `Tr` is "a running mean outdoor temperature", without α or days. The article is not one of the sources of this
  session, and the EMS cannot calculate setpoints without a metric, a band and limits.
- Options considered: (a) ship the file with the data of v03 and the missing keys empty (null), so
  `load_comfort_standards` rejects it with a message that names the keys, until the author adds them; (b) fill the
  missing keys with assumed values (a metric, the band of ASHRAE 55, limits from the range of `Tr`); (c) ship only the
  file of JPN Aqilah 2025.
- Owner: the author.
- Status: open; option (a) decided provisionally (nothing invented, D11 kept), pending author. `TODO.md` has the task.

## 2026-11-09 — B3: one regime for each comfort standard defined by its data
- Context: the design of B3 gives `ComfortStandardDefinition` `regimes: Tuple[CustomRegime, ...]  # B2; one regime for
  a single line`, but its YAML schema has one comfort temperature, one applicability and no conditions, and neither v03
  nor the brief say how comfort modes 0 to 3 apply with several regimes (which limits give the static or the extended
  setpoints), nor how a YAML file writes them.
- Options considered: (a) one regime with the condition 'always' (several, or another condition, raise a
  `ValueError`), whose offsets are added to those of the categories; the YAML files give it with
  `comfort_temperature` and `applicability`; (b) several regimes, written into the branches of SetComfTemp, SetAppLimits
  and ApplyCAT with the conditions of B2.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author. `TODO.md` has the task.

## 2026-11-09 — B3: comfort mode 2 and the outdoor metric of the comfort standards defined by their data
- Context: the comfort modes of the built-in comfort standards are 0 (static setpoints), 1 (adaptive when applicable,
  otherwise static), 2 (otherwise the static setpoints of ISO 7730) and 3 (otherwise horizontally extended); v03 lists
  `comfort_modes: [0, 1, 2, 3]` for JPN Aqilah 2025 but defines only `static_setpoints` (modes 0 and 1). The code has
  ISO 7730 static setpoints for comfort mode 2 only for the categories 80 and 90 (25/27 °C cooling and 19/22 °C heating
  with 80; 24/26 and 20/23 °C with 90, below/above the limits, the same in comfort standards 2, 3, 6, 9–12, 15, 16 and
  21). The metrics of B1 other than PMOT and RMOT are calculated by the EMS code of the custom model with the inputs
  `CustAST_metric`, `CustAST_alpha` and `CustAST_days` of the zone.
- Options considered: comfort mode 2 (a) only with the categories 80 and 90, with those values (`ValueError`
  otherwise), or (b) a key with the static setpoints of comfort mode 2; the metric (a) through the inputs of the zone
  (the zones of a registered comfort standard get those of its metric; a zone keeps them when `modify_accis` gives it
  another comfort standard), or (b) an EMS variable of its own for each registered comfort standard.
- Owner: the author.
- Status: open; options (a) and (a) decided provisionally (the code's ISO 7730 values; one EMS code of the outdoor
  metric for all), pending author.

## 2026-11-09 — B3: what `load_comfort_standards` does by default
- Context: the prompt asks for `load_comfort_standards(yaml_path)` returning the definitions, and
  `register_comfort_standard(definition)`; it does not say whether loading registers them.
- Options considered: (a) `register=True` by default (loading a file makes its comfort standards usable, as the GUI
  needs), `register=False` to only read them, `replace=False` (a number already registered raises a `ValueError`);
  (b) only read, and register with `register_comfort_standard`.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author.

## 2026-11-09 — B2: an outdoor metric for each regime of the custom model
- Context: the design of B2 in v03 gives `CustomRegime` the field `outdoor_metric: Optional[str] = None  # overrides
  custom_outdoor_metric for this regime (B1)`, and its prompt only says "optional outdoor_metric". Neither says which
  metric the conditions `metric_below/above/between` compare when the regimes have different metrics (that of the zone,
  or that of each regime), nor how the running means of the metrics that the zone does not use begin and are kept
  (B1 keeps one running mean `RMOTa_<zone>` with the alpha of the zone, and its daily means only if a zone has a
  metric other than 'pmot').
- Why it matters: with a metric for each regime, the comfort temperature, the setpoints and the applicability of the
  custom model would change of variable from one timestep to the next, and the EMS would have to keep the running
  means of several metrics in each zone.
- Options considered: (a) not available yet: `outdoor_metric` must be None, and all the regimes use the metric of the
  zone (`custom_outdoor_metric`); (b) the conditions compare the metric of the zone, and the regime selected sets
  `Tout_metric` to its own metric (EMS code of B1 for every metric used by a regime, with the alpha and days of the
  zone); (c) as (b), with the alpha and days of each regime.
- Owner: the author.
- Status: open; option (a) decided provisionally (a `ValueError` explains it), pending author. `TODO.md` has the task.

## 2026-11-09 — B2: how the program of the regimes sets the custom model
- Context: the prompt of B2 says that `SelectCustomRegime` "assigns m, n, ACSToffset, AHSToffset, ACSTall, ACSTaul,
  AHSTall and AHSTaul ... so that SetComfTemp, SetAppLimits, ApplyCAT and the ComfStand 99 setpoint lines do not
  change"; but SetAppLimits sets ACSTall... from the inputs `CustAST_ACSTall`... of the zone, and ApplyCAT sets
  ACSToffset to `CustAST_ACSToffset + CATcoolOffset`, so values written in ACSTall or ACSToffset before them are
  overwritten. Decision D6 says that, if the last regime is not 'always', "accim appends one built from the scalar
  CustAST_* arguments".
- Options considered: (a) one program `SelectCustomRegime_<zone>` for each zone of the custom model (the conditions
  of the HVAC system read the sensors of the zone), run by `RunACCIS_<zone>` right before `SetAppLimits`, that writes
  the inputs `m`, `n`, `CustAST_ACSToffset`, `CustAST_AHSToffset`, `CustAST_ACSTall`, `CustAST_ACSTaul`,
  `CustAST_AHSTall` and `CustAST_AHSTaul`, so the programs of the custom model do not change and the offsets of the
  category still apply; without a last regime 'always', the program has no `else`, so the inputs of
  `SetInputData_<zone>` (the scalar arguments, which `modify_accis` and the parametric module can still change) are the
  appended regime; a regime 'always' before the last one raises a `ValueError` (the regimes after it would never
  apply); the new EMS global and output variable `CustomRegime_<zone>` is the number of the regime (0 for the scalar
  arguments), which `verify_accim_simulation` checks; (b) one program for all the zones that writes ACSTall... after
  SetAppLimits and ApplyCAT (they would need changes, and the HVAC conditions are of each zone).
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author.

## 2026-11-09 — B2: the meaning of the conditions of the regimes
- Context: the prompt lists the conditions without saying what each one compares, nor whether the limits of the
  conditions of the outdoor metric are included.
- Options considered: 'cooling_season' and 'heating_season' are CoolingSeason 1 or 0, calculated with the lines of
  SetAST_Master and the cooling season of the zone; 'hvac_off' and 'hvac_on' are NoH_NoC_reqs 1 or 0, calculated with
  the lines with which ApplyAST_<zone> of mixed mode calculates it (the coils of the VRF systems of accim, or the load
  to the setpoints of the existing HVAC systems, of the previous timestep), so they need 'vrf_mm' or 'ex_mm'
  (`ValueError` otherwise, as v03 says) and `compute_setpoints` cannot calculate them (`ValueError`);
  ('metric_below', x) is metric < x, ('metric_above', x) is metric > x, and ('metric_between', (x1, x2)) is
  x1 <= metric <= x2, as the applicability limits of the ACCIS (`>=` and `<=` within, `<` and `>` outside).
- Owner: the author.
- Status: open; decided provisionally, pending author.

## 2026-11-09 — B2: the regimes in the zones and in the parametric module
- Context: v03 does not say whether the regimes can differ between zones, nor which coefficients the factory
  `custom_regime_parameters(n)` makes parameters ("CustAST_m_1, CustAST_n_1, ...").
- Options considered: the same regimes in all the zones whose comfort standard is 99 (`zone_arguments` cannot give
  them); in the parametric module, the eight coefficients of each regime (not the values of its condition), as the
  parameters `custom_regime_<regime>_<field>` of the accim custom models (accepted by `set_parameters` and
  `accis_parameter`, applied by BESOS through `param_accis.modify_custom_regime`) and the classes `CustAST_m_1`,
  `CustAST_n_1`, `CustAST_ACSToffset_1`, `CustAST_AHSToffset_1`, `CustAST_ACSTall_1`, `CustAST_ACSTaul_1`,
  `CustAST_AHSTall_1` and `CustAST_AHSTaul_1` of the factory.
- Owner: the author.
- Status: open; decided provisionally, pending author.

## 2026-11-09 — D1: what are the warm and cold periods of the indicators of Table
- Context: the prompt of D1 asks Table for the indicators "per zone and building for the warm and cold periods, using
  the ACSTnoTol/AHSTnoTol columns as limits by default"; CEN/TR 16798-2 (Annex D, Methods B and C) calls "warm period"
  the sum of the time above the upper limit and "cold period" that below the lower limit, while the design of v03
  also says "por estación cálida/fría definida con cooling_season_start/end".
- Options considered: (a) the warm and cold periods of the TR (above and below the range), with the setpoints of each
  hour as the limits (which already follow the cooling season); (b) also split by the cooling and heating seasons.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author.

## 2026-11-09 — D1: what Table(long_term_indicators=True) gives
- Context: the prompt asks Table for "these indicators per zone and building"; the indicators are sums of each
  simulation, while the rows of `Table.df` are timesteps or hours (the indicators need them).
- Options considered: Methods A and B with the temperature (the operative temperature and the setpoints without the
  tolerance of each zone), the occupied hours of each row (the EMS output `Occupied Hours_<zone>`) as the time, in a
  new attribute `long_term_indicators` (a row per simulation, columns `<zone>_...` and `Building_...`, the building
  adding up its zones), only for the tables that ask for it (so the files of the other tables do not change); Method C
  (which needs the PMV and its limits), the deviations of Table E.1 and the hours below some temperatures with the
  functions of the module.
- Owner: the author.
- Status: open; decided provisionally, pending author.

## 2026-11-09 — D1: the gaps of CEN/TR 16798-2 in Method C and Table E.1
- Context: Method C gives wf = 0 for PMVlimit,lower ≤ PMV < PMVlimit,upper and the weight for PMV < PMVlimit,lower or
  PMVlimit,upper < PMV, so a PMV equal to the upper limit is in neither; Table E.1 gives 44 h for 25 % of 175 h
  (43.75 h), and 58 h of 166 h for 50 % of the weekly total time.
- Options considered: a PMV equal to the upper limit is within the range (as in Method B); `deviation_check` uses the
  percentages of Table E.1 (43.75 h), not its rounded hours.
- Owner: the author.
- Status: open; decided provisionally, pending author.

## 2026-11-09 — C1: with which parameters types are the inputs of the PMV parameters
- Context: the prompt of C1 asks to register `Clo`, `Met` and `AirVelocity` "in get_available_params_apmv_setpoints()",
  and the brief points to `get_available_params_epmv_setpoints()` as the recent pattern; with the accim models
  (temperature setpoints), they would only change the outputs of the PMV.
- Options considered: (a) the parameters types 'apmv setpoints' and 'epmv setpoints' only; (b) also the accim models.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author.

## 2026-11-09 — C1: the units and range of activity_level
- Context: the brief replaces `met` with `activity_level`, the argument of `set_pmv_input_parameters`, in W/person (as
  the People objects of EnergyPlus); the prompt warns outside 0.8–4 met (ISO 7730:2025 §4: 46–232 W/m²).
- Options considered: (a) the parameter in W/person, warning outside 82.8–417.6 W/person (46–232 W/m² times the body
  surface area of 1.8 m² of ISO 7730:2025 §4 and of EnergyPlus, Engineering Reference 19.1); (b) a parameter in met,
  converted to W/person.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (the name and units of the argument of accim).

## 2026-11-09 — C1: the outdoor metric of the custom model as a parameter
- Context: the parametric module turns the options into floats, and samples ranges with floats; the modifiers get the
  model and the value only (not the weather file of the simulation); its parameters are applied one after the other.
- Options considered: `custom_outdoor_metric` takes the codes of the metrics (0–7) as options (a code that is not
  whole raises a ValueError); `custom_days` is rounded to the nearest whole day; the metrics begin with PMOT, unless
  the model was given the weather file with `modify_accis(..., epw=...)` before the study, whose programs are kept
  ('monthly_mean' needs them); while the metric is 'pmot' and the model has no code of the outdoor metric, the inputs
  given stay in `SetInputData_<zone>` as local Erl variables, so that `custom_alpha` or `custom_days` given before
  `custom_outdoor_metric` are kept.
- Owner: the author.
- Status: open; these options decided provisionally, pending author.

## 2026-11-09 — C1: the plans with a floor of the heating setpoint not lower than the ceiling
- Context: the prompt asks to update "the plans of `sampling_full_set()`"; the modifiers of B5 reject a floor that is
  not lower than the ceiling, which stops that simulation.
- Options considered: `drop_invalid_param_combinations` leaves those rows out, and `sampling_full_set()` also applies it
  to the accim custom models (before, only to the predefined models; its other rules need columns that the custom
  models do not have).
- Owner: the author.
- Status: open; decided provisionally, pending author.

## 2026-11-09 — B5: where the floor and ceiling bound the setpoints
- Context: the prompt of B5 puts the lines `if AHST < AHSTfloor ...` and `if ACST > ACSTceil ...` at the end of
  SetAST, before ROUNDING, for every comfort standard and comfort mode. In accim, SetAST runs SetAST_Master and the
  subprograms `SetAST_CS<n>_<k>`, shared by all the zones, whose branches of each comfort mode end with ROUNDING;
  ROUNDING reads ACST and AHST (unrounded) and writes `roundedACST` and `roundedAHST`.
- Why it matters: lines in the subprograms would change the output IDFs without a floor or a ceiling (they would need
  a sentinel value for the zones without them, and a Null variable stops EnergyPlus), and they would be repeated in
  every branch of every comfort mode.
- Options considered: (a) the lines in every branch of the subprograms, with sentinel values; (b) a program of each
  zone with a floor or a ceiling, `ApplySetpointLimits_<zone>`, run by `RunACCIS_<zone>` right after `run SetAST`,
  which bounds ACST and AHST and runs the lines of ROUNDING again: the same setpoints as (a), and the output IDFs
  without them do not change.
- Owner: the author.
- Status: open; option (b) decided provisionally, pending author (checked with the Erl interpreter: the setpoints are
  those of bounding before the rounding; with EnergyPlus 25.1, no mismatch with `compute_setpoints`).

## 2026-11-09 — B5: the floor and ceiling in modify_accis
- Context: `modify_accis` writes the inputs of its arguments that are not None; several of them have numbers as
  defaults, which every call writes.
- Options considered: (a) numbers as defaults; (b) `None` by default, keeping the floor and ceiling of each zone, as
  the arguments of the outdoor metric of B1; there is no way to remove them with `modify_accis` (a model without them
  is made again with `AddAccis` or `add_accis_to_idf`, or the lines are removed from `SetInputData_<zone>` and
  `accim.sim.ems.setpoint_limits.set_setpoint_limits_code` is called).
- Owner: the author.
- Status: open; option (b) decided provisionally, pending author (the most conservative: a call without them changes
  nothing of the floor and ceiling).

## 2026-11-09 — B5: the outputs of report_hours_below and the setpoint types
- Context: the prompt asks for the counters `HoursBelow_<T>_<zone>`, but not with which outputs and setpoint types.
- Options considered: the outputs of every `output_type` but 'custom' (the standard and detailed outputs take all the
  EMS outputs; with 'simplified', their `Output:Variable` objects are added; with 'custom', the user keeps those
  chosen); the counters also with `setpoint_type='pmv'`, since they only need the occupants and the operative
  temperature (only the floor and ceiling are rejected there, D5); the temperatures with decimals named with `p`
  (`HoursBelow_17p5_<zone>`: the names of the EMS cannot have dots) and `m` for the minus sign.
- Owner: the author.
- Status: open; these options decided provisionally, pending author.

## 2026-11-09 — B5: a floor above the cooling setpoint, or a ceiling below the heating setpoint
- Context: the floor only bounds the heating setpoint and the ceiling the cooling setpoint; accim checks that the floor
  is lower than the ceiling, but a floor above the cooling setpoint of the comfort model (or a ceiling below its heating
  setpoint) gives a heating setpoint above the cooling setpoint in those timesteps. v03 does not say what to do.
- Options considered: (a) as v03 writes the lines, documented; (b) also raise the cooling setpoint to the floor and
  lower the heating setpoint to the ceiling (not in v03).
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (documented in section 4.2.3 of the detailed use).

## 2026-11-09 — B1: does every model of the custom model have the EMS code of the outdoor metric, or only those that need it
- Context: the prompt of B1 says that SetComfTemp, SetAppLimits and COUNT_HOURS of the custom model use `Tout_metric`,
  a new global variable and EMS output; with the default `'pmot'`, the behaviour must not change.
- Why it matters: with the code in every model of the custom model (and in the models of `add_accis_to_idf`, which
  have the code of all the comfort standards), the output IDFs of 1.1.0 with comfort standard 99 would get new
  programs, global variables and outputs (new columns in the CSV files), although their setpoints would not change.
- Options considered: (a) always; (b) only if a zone has a metric other than `'pmot'` (`CustAST_metric` ≠ 0) and the
  model has the code of the custom model; otherwise the custom model uses PMOT, as in 1.1.0.
- Owner: the author.
- Status: open; option (b) decided provisionally, pending author (the golden master does not change; the parametric
  parameters of C1 will add the code when they set a metric).

## 2026-11-09 — B1: which programs of the custom model use Tout_metric
- Context: the prompt names SetComfTemp, SetAppLimits and COUNT_HOURS. In accim, SetAppLimits only sets the limits of
  the custom model from its inputs; the outdoor temperature is compared with them in the subprogram of its setpoints
  (`SetAST_CS99_0`), in `CountHours_<zone>` and, in mixed mode, in `SetVST` (the ventilation setpoint).
- Why it matters: with PMOT in some of them, the custom model would mix two outdoor temperatures.
- Options considered: (a) only the programs of the prompt (SetAppLimits unchanged); (b) every program where the
  custom model uses its outdoor temperature: SetComfTemp, `SetAST_CS99_0`, `CountHours_<zone>` and `SetVST`.
- Owner: the author.
- Status: open; option (b) decided provisionally, pending author.

## 2026-11-09 — B1: on which day do the programs of the outdoor metric begin with the values of the weather file
- Context: decision D3 says to initialise the running means with the values that accim calculates from the EPW given
  to AddAccis, but not for which day; the programs keep constants, not the whole year.
- Why it matters: if the model is simulated from another day (another RunPeriod, or the design days), the constants
  of the first day would be wrong.
- Options considered: (a) the constants of the first day of the first RunPeriod of the input IDF, used only if the
  environment begins on that day (otherwise, the PMOT of EnergyPlus, as without the EPW); (b) the constants of the
  365 days (more than 10 000 program lines).
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author.

## 2026-11-09 — B1: T0 of te_ref_nl before the first hour of the day has ended
- Context: v03 gives Te,ref = (T0 + 0.8·T−1 + 0.4·T−2 + 0.2·T−3)/2.4 with T0 "the running (max+min)/2 of today"; at
  the first timesteps of a day, no hourly value of the day has ended.
- Options considered: (a) the outdoor temperature of the timestep; (b) the mean of the maximum and minimum of the
  previous day.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author.

## 2026-11-09 — B1: the arguments of the outdoor metric in modify_accis
- Context: the other arguments of the custom model of `modify_accis` (`custom_slope`...) default to 0 and are always
  written.
- Options considered: (a) `custom_outdoor_metric='pmot'`, `custom_alpha=0.8`, `custom_days=30` written by every call
  (a call without them would remove the metric of the zones); (b) `None` by default, keeping the values of each zone,
  as `comfort_standard` and the other arguments that are None.
- Owner: the author.
- Status: open; option (b) decided provisionally, pending author (the most conservative: a call without them changes
  nothing of the outdoor metric).
## 2026-11-09 — A3: with adaptive_coefficient_by='pmv_sign', which λ converts each setpoint into the PMV setpoint of the thermostat
- Context: the design of A3 gives the Erl of the option, "if PMV_{s} >= 0 set adap_coeff = λ_warm else λ_cool", with
  the PMV of the previous timestep, but not which λ converts the setpoints of the aPMV into the PMV setpoints of the
  thermostats (PMV = aPMV/(1 − λ·aPMV), v03 §11.1); with 'season' it is the λ of the season, as in accim 1.1.0.
- Why it matters: with the λ of the sign of the current PMV, the PMV setpoints of the thermostat would change each
  time the PMV changes sign (with λ 0.21/−0.49, the heating setpoint −0.5 would be the PMV −0.45 or −0.66).
- Options considered: (a) each setpoint with the λ of its side of the scale (the heating setpoint, negative where it
  is converted, with the λ of cool sensations; the cooling one with that of warm sensations), which is the inverse of
  aPMV(PMV) with λ by the sign; (b) both with the λ of the sign of the PMV of the previous timestep (the Erl of the
  design applied to the inverse too).
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (the monitor and the output `Adaptive
  Coefficient_<zone>` follow the design).

## 2026-11-09 — A3: does a key of the catalogue in one coefficient also set the other one
- Context: the design of A3 says that a key given in `adaptive_coefficient_cooling` "fills both coefficients at once
  unless the other is given explicitly"; its prompt only says that the arguments accept a key, and the defaults of the
  coefficients are numbers (0.293 and −0.293), so an explicit value equal to the default cannot be told apart.
- Why it matters: `adaptive_coefficient_cooling='yao2009_chongqing_classrooms'` alone gives λ 0.293 and −0.293 (the
  default) with (a), and 0.293 and −0.125 with (b).
- Options considered: (a) each argument takes the coefficient of its own side of the key (give the key to both to use
  the entry); (b) the defaults become None, which takes the other coefficient of a key, or 0.293/−0.293 otherwise (the
  signature changes, and the GUI and the documentation show other defaults); (c) a new argument with the key for both.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (the conservative, backward-compatible one;
  documented in the docstring and in section 4.8).

## 2026-11-09 — E2: what the metabolic correction of the ePMV is checked against (the 5.5–6.1 % of the brief)
- Context: the brief asks E2 to check "the metabolic correction with the tolerance of 5.5–6.1 %". The EMS sets the
  factor of each People object to 1 − 0.067·PMV with the PMV of the previous timestep (exact in EnergyPlus 25.1:
  differences of 1e-16 with the outputs at timestep frequency); the 5.5–6.1 % is the reduction of the activity level
  for a PMV of 1 *before* the correction, once the correction converges (section 4.8.1 of the detailed use), and the
  outputs of a simulation do not have that PMV (EnergyPlus calculates the PMV with the corrected activity level).
- Why it matters: a check of the reduction against the reported PMV of the same timestep would give about 6.7 %, not
  5.5–6.1 %, and one against the PMV before the correction needs the PMV calculated again (A6, `accim[comfort]`).
- Options considered: (a) the relation of the EMS, factor = 1 − 0.067·PMV of the previous timestep (0–3, cooling
  season), and corrected activity = activity·factor, with `calculation_tolerance` (0.001); (b) a band of 5.5–6.7 % on
  (1 − factor)/PMV of the same timestep, approximate and also with hourly outputs; (c) the PMV before the correction
  calculated with pythermalcomfort, and the band 5.5–6.1 %.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (it is exact and catches any other reduction; the
  5.5–6.1 % stays documented as the result of the correction).

## 2026-11-09 — E1: the running means of the first days of the weather file in outdoor_metrics
- Context: `accim.sim.preview.outdoor_metrics` (E1) calculates the running means of the standards (EN 16798-1 B.1 and
  B.2, the mean of the n previous days of ASHRAE 55, the reference temperature of the ATG) from the daily means of the
  previous days, and the first days of the weather file have no previous days in it. v03 and D1-D12 do not say what
  they get.
- Why it matters: the values of the first days of January, and the initial values of the running means of B1 (D3).
- Options considered: (a) a year that repeats: the first days take the last days of the file, as EnergyPlus does for
  ASHRAE 55 at the beginning of a run period, and B.1 is its infinite sum (a closed form); (b) NaN for the days without
  enough previous days (B.1 would never be complete); (c) the sums truncated at the first day of the file.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (it is what accim does; `energyplus_running_means`
  gives the values of EnergyPlus, whatever the answer).

## Answered

The questions on the scope and the technology of the GUI, on the names of the arguments of accim 1.0.0, on the EMS
code of the comfort standards of each output IDF of `AddAccis` (option 1, as implemented), on the design days of
`vrf_mm` (option (a): the same rule as `ex_mm`) and on the `schedule` of `set_clothing_method` of A5 (option (b): the
clothing insulation schedule, and another argument for `CalculationMethodSchedule`) were answered: see
[[decisions.md]].
