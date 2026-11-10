---
title: Decisions
type: log
tags: [vault, decisions, adr]
created: 2026-09-13
---

# Decisions

Durable architectural/process decisions for this repository and its Obsidian
vault. Newest first. Use [[templates/decision-record.md|the decision-record
template]] to add a new entry.

## 2026-11-09 — Comfort standards defined by their data are registered for the session, and their EMS code is added at the end of the chains of the built-in ones (B3)

- **Status**: accepted (proposal B3 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` with decisions D1 and D11 of the
  brief; four details decided provisionally, see questions.md)
- **Context**: adding a comfort model needed changes in the catalogue, the chains of the EMS programs, the setpoint
  lines and the GUI, and a release. The prompt asks for `ComfortStandardDefinition`, `register_comfort_standard()`,
  `load_comfort_standards()` with the YAML schema of v03, Erl built from the registry for the numbers 100 or more while
  the built-in comfort standards keep their literal lines (byte-identical output IDFs), the two YAML examples of v03,
  a How-to notebook, the GUI lists from the registry and `print_setpoint_ems_code` with the evidence.
- **Decision**: `accim.sim.standards` keeps the registry of the Python session (`register_comfort_standard`,
  `load_comfort_standards`, which registers by default); the new module `accim.sim.ems.standard_lines` writes the
  branches `elseif ComfStand == <n>` of a definition (SetComfTemp, SetAppLimits, ApplyCAT and, with a metric other
  than PMOT, CountHours and SetVST) and its setpoint lines, as those of the built-in comfort standards, and
  `accim.sim.ems.program_lines` adds them at the end of the literal chains, which do not change; the metrics that the
  EMS calculates use the EMS code of the outdoor metric of the custom model (B1), through the inputs of the zones of
  the comfort standard; a definition has one regime 'always'; comfort mode 2 uses the ISO 7730 values of the code
  (categories 80 and 90 only); a negative slope is written with the intercept first (Erl takes no minus sign after a
  multiplication sign); the processes of the parallel simulations of the parametric module receive the definitions.
- **Consequences**: the output IDFs of the built-in comfort standards do not change, with or without registered ones
  (golden master; each output IDF of `AddAccis` only has the code of its comfort standards), while the models of
  `add_accis_to_idf` have the code of those registered when they are made; the registry must be loaded again in each
  session; the Qatar example is incomplete and rejected until the author gives its metric, band and limits.

## 2026-11-09 — The custom model has several regimes, selected in each timestep by a program of each zone (B2)

- **Status**: accepted (proposal B2 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` with decision D6 of the brief;
  four details decided provisionally and one left open, see questions.md)
- **Context**: many comfort models have several equations or limits, each one under some conditions; the custom model
  (comfort standard 99) had one set of coefficients, the inputs `m`, `n`, `CustAST_*` of `SetInputData_<zone>`. The
  prompt asks for `CustomRegime`, `custom_regimes` in `AddAccis`, an Erl chain `if/elseif` in priority order that
  leaves `SetComfTemp`, `SetAppLimits`, `ApplyCAT` and the setpoint lines unchanged, the scalar arguments as a regime
  'always' (identical output IDFs without regimes), a `ValueError` for 'hvac_off'/'hvac_on' without mixed mode, and the
  factory `custom_regime_parameters(n)`.
- **Decision**: `accim.sim.arguments.CustomRegime` (frozen, checked) and `check_custom_regimes`; the module
  `accim.sim.ems.custom_regimes` writes `SelectCustomRegime_<zone>` in the zones of the custom model, run right before
  `SetAppLimits`, which sets the inputs of the custom model of the zone (so the category offsets still apply) and
  `CustomRegime_<zone>` (an EMS output, 0 when the scalar inputs apply, which are the appended regime of D6); the
  conditions reuse the lines of the cooling season of `SetAST_Master` and those of `NoH_NoC_reqs` of `ApplyAST_<zone>`;
  the outdoor metric of B1 rewrites them as the other programs of the custom model; `custom_regimes_of` reads the
  regimes back from the Erl (the comments of the programs are lost when eppy reads an IDF), for
  `verify_accim_simulation` and the parametric module (`custom_regime_<regime>_<field>`, `modify_custom_regime`,
  `custom_regime_parameters(n)`).
- **Consequences**: the output IDFs without regimes do not change (golden master), the regimes need comfort standard 99
  and `setpoint_type` 'temperature', and `compute_setpoints` cannot calculate the conditions of the HVAC system; the
  regimes use the outdoor metric of the zone (an outdoor metric for each regime is pending the author).

## 2026-11-09 — The indicators of the long-term discomfort are functions of a module of their own, and Table gives those of the temperature on request (D1)

- **Status**: accepted (proposal D1 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` with decision D8 of the brief;
  three details decided provisionally, see questions.md)
- **Context**: CEN/TR 16798-2:2019 (Annex D: Methods A, B and C; Annex E: Table E.1) is the reference of the long-term
  evaluation, since ISO 7730:2025 left it out (checked in the TR, pages 68–71, and in ISO 7730:2025, formula 5). The
  prompt asks for pure pandas functions, `Table(long_term_indicators=True)` with the setpoints without tolerance as
  limits, and tests of Table D.1, which D8 replaces with analytic tests (Method B), the PPD formula (Method C) and the
  PPD at 0, ±0.5 and ±1.
- **Decision**: `accim.data.postprocessing.long_term_discomfort` with `hours_outside_range`, `degree_hours`,
  `ppd_weighted_hours`, `ppd_from_pmv`, `deviation_check` (`DEVIATION_LIMITS`, levels '3%' and '6%') and
  `hours_below`, on Series of each row, with the occupancy and the hours of each row; `table_indicators` and
  `Table(long_term_indicators=True)` give Methods A and B of each simulation, zone and building, in the attribute
  `long_term_indicators`, separate from the constructor (R-04); the GUI shows them.
- **Consequences**: the tables without the option and their files do not change. With timestep tables, the indicators
  of Table are those of the CSV files (checked against a direct calculation with a simulation of B5); with hourly rows
  of timestep outputs, they use the means of each hour.

## 2026-11-09 — The parametric module varies the inputs of the PMV and the outdoor metric of the custom model (C1)

- **Status**: accepted (proposal C1 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`, with the adjustment of the brief:
  `clothing_insulation`/`activity_level` instead of `clo`/`met`; four details decided provisionally, see questions.md)
- **Context**: the parametric module had no parameters for the clothing insulation, the activity level or the air
  velocity, nor for the new arguments of B1 and B5; the prompt asks for the classes `Clo`, `Met`, `AirVelocity`,
  `ExpectancyFactor`, `HeatingSetpointFloor`, `CoolingSetpointCeiling`, `CustAST_metric`, `CustAST_alpha` and
  `CustAST_days`, with warnings outside the ranges of ISO 7730:2025 §4 and ASHRAE 55 (clo ≤ 1.5).
- **Decision**: the parameters `clothing_insulation`, `activity_level` (W/person) and `air_velocity` of the parameters
  types 'apmv setpoints' and 'epmv setpoints' call `set_pmv_input_parameters`, and warn outside
  `accim.constants.PMV_INPUT_RANGES` (ISO 7730:2025 §4, with A_Du = 1.8 m²) and above
  `ASHRAE55_MAX_CLOTHING_INSULATION`; `custom_outdoor_metric` (codes), `custom_alpha` and `custom_days` of the accim
  custom models set the inputs of B1 and its EMS code as `modify_accis` does, without removing the inputs given
  while the metric is 'pmot'; the wrapper classes have the names of v03 (with `AdaptiveCoefficientCooling` and
  `AdaptiveCoefficientHeating`); the full sets leave out a floor that is not lower than the ceiling. The factory of
  the regimes of B2 waits for B2.
- **Consequences**: the parameters of the PMV-based setpoints and of the accim custom models grow (the lists of
  `get_available_parameters()`, `test_epmv_parameters.py`, `test_legacy_names.py` and the GUI follow). A two-point
  design of `clothing_insulation` gives IDFs whose `Sch_Clo_<people>` schedules have each value (checked with
  `EvaluatorEP.generate_building` of besos, without simulating).

## 2026-11-09 — The setpoints of the ACCIS can have a floor and a ceiling, and the zones count the occupied hours below some temperatures (B5)

- **Status**: accepted (proposal B5 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` with decision D5 of
  `notes/COPILOT_BRIEF_v1.2.0_v01.md`; four details were decided provisionally, see questions.md)
- **Context**: EN 16798-1:2019 gives in Table B.2 the default design values of the indoor operative temperature
  (minimum for heating, maximum for cooling) of the buildings with mechanical cooling, and B.2.2 applies them in winter
  to those without it (checked in UNE-EN 16798-1:2020, pages 49 and 51). In accim, the applicability limits change the
  equation of the setpoints but do not bound them. B5 asks for `heating_setpoint_floor` (`AHSTfloor`) and
  `cooling_setpoint_ceiling` (`ACSTceil`), applied before ROUNDING in every comfort standard and comfort mode,
  `EN16798_TABLE_B2`, `report_hours_below` (`HoursBelow_<T>_<zone>`) and the parametric classes
  `HeatingSetpointFloor` and `CoolingSetpointCeiling`; D5: the setpoints based on the PMV have neither.
- **Decision**: `accim.sim.ems.setpoint_limits`: the zones with a floor or a ceiling get the optional inputs
  `AHSTfloor` and `ACSTceil` in `SetInputData_<zone>` and the program `ApplySetpointLimits_<zone>`, which
  `RunACCIS_<zone>` runs right after `SetAST`: it bounds AHST and ACST and runs the lines of ROUNDING again, so the
  setpoints are those of bounding before the rounding; the shared subprograms do not change. `report_hours_below`
  adds `CountHoursBelow_<zone>` after the other hour counters, with summed EMS outputs in hours. `AddAccis` rejects the
  floor and ceiling with `setpoint_type='pmv'`; `modify_accis` keeps them when its arguments are None; the parametric
  module sets them in all the zones. `get_setpoint_ems_code`, `compute_setpoints`, `verify_accim_simulation` (check 5)
  and the GUI (with the values of Table B.2) follow.
- **Consequences**: the output IDFs without a floor or a ceiling do not change (golden master). Since the cooling
  setpoint is rounded down strictly, a cooling setpoint bounded by the ceiling is one step of `setpoint_accuracy`
  below it (25.9999 °C with 26 °C and 10000), as with the lines of v03. With EnergyPlus 25.1, the setpoints of a winter
  and a summer week are within them and those of `compute_setpoints`, the counters are those of the occupants of the
  timestep and the operative temperature of the previous one, and both backends give identical results.

## 2026-11-09 — The custom model calculates its outdoor metric in Erl, only where a zone needs it (B1)

- **Status**: accepted (proposal B1 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` with decisions D3 and D7 of
  `notes/COPILOT_BRIEF_v1.2.0_v01.md`; four details were decided provisionally, see questions.md)
- **Context**: B1 asks for `custom_outdoor_metric` ('pmot' by default, 'rmot', 'rmot_alpha' with `custom_alpha`,
  'rmot_7day', 'daily_mean', 'ndrm' with `custom_days`, 'monthly_mean' and 'te_ref_nl') for the custom model, in a new
  Erl program SetOutdoorMetric without `EnergyManagementSystem:TrendVariable`, with `Tout_metric` as a global variable
  and an EMS output; D3: the running means begin with the values of the EPW given to AddAccis, or with PMOT and a
  warning, and 'monthly_mean' needs the EPW (ValueError); D7: alpha outside 0.6–0.9 and days outside 7–30 warn.
- **Decision**: `accim.sim.ems.outdoor_metric` writes three programs: `SetOutdoorMetric` (building, at
  BeginTimestepBeforePredictor before the zones: the hourly values of the end of each hour, `Minute > 59.5`, and at the
  first timestep of each day, `(Hour == 0) && (TimeStepNum == 1)`, the daily means `Tday_1...Tday_n` (n = max(30,
  `custom_days`)) and the means of the maximum and minimum `Tmid_1...Tmid_3`, without the warm-up days),
  `SetOutdoorMetric_<zone>` (run by `RunACCIS_<zone>` after its inputs `CustAST_metric`, `CustAST_alpha`,
  `CustAST_days`: the recursive running mean `RMOTa_<zone>` and `Tout_metric`) and `InitOutdoorMetric`
  (BeginNewEnvironment: the values are 0 until they begin). The EPW gives constants for the first day of the first
  RunPeriod (used if the environment begins that day; otherwise PMOT once it is not 0). `set_comfort_standard_code`
  writes these objects only if the model has the code of the custom model and a zone has a metric other than 'pmot';
  then `SetComfTemp`, `SetAST_CS99_0`, `CountHours_<zone>` and `SetVST` use `Tout_metric` instead of PMOT (constants
  `*_OUTDOOR_METRIC` of `program_lines`, `subprograms(outdoor_metric=True)`), and the outputs are `Tout_metric_<zone>`
  and `Tout_metric`. `modify_accis` keeps the metric when its arguments are None. `get_setpoint_ems_code`,
  `compute_setpoints` (`outdoor_metric_start`), `verify_accim_simulation` (`Check4_Tout_metric`), `Table` (averaged)
  and the GUI follow.
- **Consequences**: the output IDFs of the other comfort standards and of 'pmot' do not change (golden master). The
  built-in variable `TimeStepsPerHour` of the EMS Application Guide reads 0 at BeginTimestepBeforePredictor in
  EnergyPlus 25.1 (found with an EMS output of a copy of it, 2026-11-09), so the end of the hour is `Minute > 59.5`
  (the guide: Minute, 1.0–60.0, the end of the timestep). With EnergyPlus 25.1, every metric gives the values of
  `compute_setpoints` in every timestep, and both backends give identical results. The test of v03 (rmot_alpha(0.8)
  against the native RMOT, |Δ| < 0.05 K after 14 days) is made after 21 days: EnergyPlus begins its running mean of
  CEN 15251 with equation 19.82 not divided by 1 − α⁷ and uses the daily means of the first timestep of each hour,
  which gives 0.10 K on day 15 with `Seville_Present.epw` from 1 January, and less than 0.045 K from day 22.

## 2026-11-09 — The aPMV takes the adaptive coefficients of a catalogue, and with pmv_sign the coefficient of the side of the PMV (A3)

- **Status**: accepted (proposal A3 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` with decision D4 of
  `notes/COPILOT_BRIEF_v1.2.0_v01.md`; the details below were not in the proposal: for the review of the author)
- **Context**: A3 asks for `APMV_ADAPTIVE_COEFFICIENTS` (Yao 2009, GB/T 50785-2012, the λN of Zhang 2024 as
  'literature'), keys in `adaptive_coefficient_cooling/heating` resolved in `generate_df_from_args`, a warning for
  the 'literature' entries, `get_adaptive_coefficients(key)` and `adaptive_coefficient_by='season'|'pmv_sign'`; D4
  keeps 'season' as the default. In the code, `apply_apmv_setpoints` goes through `accim.sim.pmv_index`, whose EMS
  programs choose the coefficient in `apply_aPMV_<zone>` (by season) and calculate the aPMV in `monitor_aPMV_<zone>`.
- **Decision**: the catalogue is in `accim.constants`, with the values of v03 §11.2 and A3. The keys are resolved by
  the engine (a new hook `PmvIndex.resolve`, also used by `generate_df_from_args`), so `apply_pmv_index_setpoints`
  takes them too; each argument takes the coefficient of its own side (questions.md). With 'pmv_sign', the program
  of the setpoints does not choose the coefficient (the new hook `PmvIndex.seasonal_coefficient`), the monitor chooses
  it by the sign of the PMV of the zone (after `average_PMV_<zone>`, so with the PMV of the previous timestep also in
  zones with several People objects), and each setpoint is converted with the λ of its side (questions.md). The
  `get_adaptive_coefficients` of `accim.sim.apmv` is that of `accim.sim.pmv_index`. The GUI keeps numbers in its
  fields: the list of the catalogue fills them and shows the grade, source and notes.
- **Consequences**: the output IDFs of 'season' do not change (golden master); 'pmv_sign' gives the same results with
  both backends and passes check 3 of `verify_accim_simulation`. Section 4.8 of
  [[../docs/source/4_detailed use.md]] and section 10 of [[../CAMBIOS_CODIGO_v1.2.0.md]].

## 2026-11-09 — verify_accim_simulation checks the indices of the PMV with the outputs at timestep frequency, and every comfort standard against compute_setpoints (E2)

- **Status**: accepted (proposal E2 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` and its adjustment in
  `notes/COPILOT_BRIEF_v1.2.0_v01.md`; the details below were not in the proposal: for the review of the author)
- **Context**: E2 asks `verify_accim_simulation` to check ePMV = e·PMV (with PMV > 0, as implemented), aPMV =
  PMV/(1 + λ·PMV), the corrected activity level, `Tout_metric` (B1), the floor and ceiling of B5 and, for B3, the
  setpoints of the registered models against `compute_setpoints`. The EMS calculates the index at the beginning of
  each timestep from the PMV of the previous timestep and the occupants of the current one (checked with simulations
  of EnergyPlus 25.1: differences of 1e-16 with the outputs at timestep frequency); hourly outputs average both, so
  the relations do not hold in them.
- **Decision**: check 3 compares the index of each zone, the metabolic factor and the corrected activity level with
  their formulas applied to the PMV of the previous timestep, only with the outputs at timestep frequency (with hourly
  ones it warns that it needs them); the first timestep of each environment is not checked, and the expected values
  are independent of the Erl of the model, except the cooling season, which the programs of the model give. Check 4,
  only with the new argument `epw`, compares the setpoints of every zone of an output IDF of `AddAccis` with
  `compute_setpoints` (with the arguments of its program `SetInputData_<zone>`) and the running means of EnergyPlus
  with `energyplus_running_means`, in the run period, so the comfort standards of B3 will go through it. The checks of
  before do not change; the new ones have their own tolerance, `calculation_tolerance` (0.001).
- **Consequences**: the outputs of the indices, the metabolic correction and the setpoints of the ACCIS can be checked
  after a simulation; the checks of B1 and B5 wait for their outputs ([[../TODO.md]]). A wrong weather file makes check
  4 fail in every adaptive setpoint (not in the static ones). Section 4.6.1 of
  [[../docs/source/4_detailed use.md]] and section 9 of [[../CAMBIOS_CODIGO_v1.2.0.md]]; the 5.5–6.1 % of the brief
  is in [[questions.md]].

## 2026-11-09 — compute_setpoints runs the setpoint programs of the output IDFs with the running means of EnergyPlus, start-up transient included (E1)

- **Status**: accepted (proposal E1 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` and decision D9 of
  `notes/COPILOT_BRIEF_v1.2.0_v01.md`; the details below were not in the proposal: for the review of the author)
- **Context**: E1 asks for `compute_setpoints`, which evaluates the Erl programs of `get_setpoint_ems_code` hour by hour
  with the running means as EnergyPlus calculates them ("both computed from the weather file, so no start-up
  transient"), tested against the hourly CSV of EnergyPlus within the rounding of `SetpointAcc`. But
  `get_setpoint_ems_code` gives text whose subprograms are cut to the lines of the comfort mode, which `SetAST_Master`
  cannot run. And EnergyPlus 25.1 (simulations of the sample model, and its `ThermalComfort.cc`) starts the running
  mean of CEN 15251 with equation 19.82 not divided by 1 − α⁷, takes the daily means of the simulated days from the
  first timestep of each hour, and its EMS reads the running means of the previous day at the first timestep of each
  day.
- **Decision**: a new function, `accim.utils.get_setpoint_ems_programs`, gives the programs by name with the whole
  subprograms (the text of `get_setpoint_ems_code` does not change). `compute_setpoints` runs them in each timestep, as
  `RunACCIS_<zone>` does, with the running means as EnergyPlus calculates them, including the start-up transient of
  CEN 15251 that v03 says does not exist (D9: reproduce the running means of EnergyPlus). The hourly values are the
  means of the timesteps, as the hourly EMS outputs of EnergyPlus; `applicable` and `cooling_season` are those of the
  last timestep of the hour. `outdoor_metrics` gives the metrics as the standards define them, apart from those of
  EnergyPlus (`energyplus_running_means`). The `.stat` file that EnergyPlus reads for ASHRAE 55 is not reproduced.
- **Consequences**: the values of `compute_setpoints` are those of the EMS outputs of EnergyPlus 25.1 to machine
  precision (the tests allow 0.0001 °C); a run period from 1 January has the low running mean of CEN 15251 of
  EnergyPlus in its first days. B1 can initialise its running means in Erl from `outdoor_metrics` (D3). Section 4.3.1
  of [[../docs/source/4_detailed use.md]] and section 8 of [[../CAMBIOS_CODIGO_v1.2.0.md]]; the `.stat` file, the leap
  years and two possible errors of comfort standards 9 and 10 found on the way are in [[../TODO.md]].

## 2026-11-09 — Table reads the CSV files of the simulations of any IDF and names the outputs of the setpoints based on the PMV after their zones, with names that do not contain each other (D2)

- **Status**: accepted (proposal D2 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v02.md` and `_v03.md`, which the author
  included in 1.2.0 on 2026-11-09; the details below were not in the proposal: for the review of the author)
- **Context**: D2 asks `Table` to recognise `ePMV_<zone>`, `e_<zone>` (`Expectancy Factor_<zone>`) and `aPMV_<zone>` in
  `rename_cols` and in `time_plot`. A simulation of the ePMV setpoints showed that `Table` could not read their CSV
  files at all: `run_ep` names them `<IDF>[<EPW>.csv`, and `Table` split every name into the twelve parts of the names
  of the output IDFs of `AddAccis`. It also added up their index and setpoints over time and took the corrected activity
  level for an energy. The figures of `Table` take the columns whose names contain the names they are given.
- **Decision**: the names with two parts give `Model` (the IDF) and `EPW`, and the other columns `CS_X`... `NS_X`, as
  the arguments of `AddAccis` that do not apply; other names stop `Table` with a clear `ValueError`. The outputs of the
  zones are named `<zone>_<name>`: the index and its coefficient with their names, the setpoints with the index in
  parentheses after them (`Heating Setpoint (aPMV)`, `Cooling Setpoint_No Tolerance (aPMV)`), so that no name contains
  another one (`<zone>_aPMV` would be part of `<zone>_aPMV Heating Setpoint`), the hour counters with `(h)`, the
  schedules of the thermostats `Thermostat Heating Setpoint (PMV)` and `Thermostat Cooling Setpoint (PMV)`. They keep
  their EMS names: `PMV_<zone>` of the PMV setpoints (`<zone>_PMV` is the PMV of EnergyPlus), `Occupied hours_<zone>`
  (the same column as `Occupied Hours_<zone>` of the ACCIS, which `Table` does not rename) and the outputs of the
  metabolic correction of the People objects of several zones; those of a People object of one zone get the name of
  the zone, `<zone>_Metabolic Correction Factor` and `<zone>_Corrected Activity Level (W/person)` (the
  `Activity_corrected_<zone>` of v03 of the proposals), with the mean of the People objects of a zone that has several.
  All but the hour counters are averaged over time; the index,
  the coefficient, the setpoints and the counters get block and building values. The names of the outputs come from
  `accim.sim.pmv_index` (`zone_outputs`), and what `Table` does with them is in the module
  `accim.data.postprocessing.pmv_index_columns`, not in the constructor of `Table` (R-04).
- **Consequences**: the GUI and `Table` make the tables and figures of these simulations, also together with those of
  the ACCIS (they are told apart by `Model`; `ComfStand` with one standard and `CS_X` is not a variable of the table, as
  the other `_X` values). The tables of the ACCIS do not change, unless they have `Zone Mean Air Temperature`. Section
  4.7.3 of [[../docs/source/4_detailed use.md]] and section 7 of [[../CAMBIOS_CODIGO_v1.2.0.md]]; the parts of D2 for B1
  and B5 are in [[../TODO.md]].

## 2026-11-09 — The priorities of TODO.md and the format of the references to issues and pull requests

- **Status**: accepted (the author approved both proposals of [[../TODO.md]] of 2026-10-31, 2026-11-09: "¿Apruebas las
  dos propuestas del TODO.md (prioridades y formato de enlaces)? Sí")
- **Context**: the conventions of [[../TODO.md]] named the priorities `P0`, `P1` and `P2` without criteria, and the
  tracking files referred to issues and pull requests in several ways ("PR #6", "EnergyPlus pull request 11409").
- **Decision**: `P0`, it stops users or a release now; `P1`, needed for the next release, or wrong behaviour that has
  a workaround, failing tests, or documentation that misleads; `P2`, improvements, refactors, reviews and tasks without
  a date; when in doubt, the lower priority, raised when a user is affected. References: `#123` for this repository and
  `owner/repo#123` for other repositories, which GitHub links (not inside code spans); full URLs only for other sites.
  The repository of EnergyPlus is now `NatLabRockies/EnergyPlus` on GitHub (`NREL/EnergyPlus` redirects to it), so the
  references use that name.
- **Consequences**: the conventions of [[../TODO.md]] have the criteria and the format, and those of
  [[../DEVLOG.md]] refer to them; the two references of [[../DEVLOG.md]] to the pull requests of EnergyPlus follow the
  format, and the dependency of R-01 in [[../ROADMAP.md]] is solved. The numbered "PR 1" to "PR 4" of the entries of the
  branch reviews are the steps of `notes/branch-reviews.md`, not pull requests of GitHub, and are kept.

## 2026-11-09 — The schedule of set_clothing_method is the clothing insulation schedule, and CalculationMethodSchedule has its own argument

- **Status**: accepted (the author answered the open question of `notes/questions.md`, 2026-11-09: "Opción (b)")
- **Context**: the design of A5 proposes `accim.sim.people.set_clothing_method(building, method, schedule=None)`
  without defining `schedule`. The field *Clothing Insulation Calculation Method* has three methods:
  `ClothingInsulationSchedule` reads the clothing insulation schedule, `DynamicClothingModelASHRAE55` no schedule, and
  `CalculationMethodSchedule` a schedule that chooses the method (1, the clothing insulation schedule; 2, the dynamic
  model) and, for the periods with 1, the clothing insulation schedule.
- **Decision**: `schedule` is the clothing insulation schedule (with `ClothingInsulationSchedule`, and for the periods
  of the method 1 of `CalculationMethodSchedule`; an error with `DynamicClothingModelASHRAE55`), and
  `calculation_method_schedule`, named as its field in the IDD, is the schedule that chooses the method, required with
  `CalculationMethodSchedule` and an error with the other methods. Without `schedule`, the People objects keep theirs.
  The function sets all the People objects (and the People:Instance objects of EnergyPlus 26.2), and checks the method,
  the schedules and the values of the calculation method schedule (1 and 2) before changing anything.
- **Consequences**: with `set_pmv_input_parameters` (`'dynamic_ashrae55'` and the values by season), accim sets the
  three methods of EnergyPlus; the clothing insulation as a function of the outdoor temperature, which needs E1, is
  the part of A5 that is left ([[../TODO.md]]). Section 4.8 of [[../docs/source/4_detailed use.md]] and section 4 of
  [[../CAMBIOS_CODIGO_v1.2.0.md]].

## 2026-11-09 — The activity level and the clothing insulation take values by season in set_pmv_input_parameters, with the cooling season of the setpoints, and 'dynamic_ashrae55' sets the dynamic clothing model of EnergyPlus

- **Status**: accepted (proposal A5 of the author's file of proposals after 1.1.0,
  `notes/PROPUESTAS_MEJORAS_post_1.1.0_v02.md`, done as its prompt asks; the author asked to work on the pending tasks
  of `TODO.md` and then on those of the changes of 1.2.0, "pero no quiero que te inventes nada")
- **Context**: `set_pmv_input_parameters` wrote a constant `Schedule:Compact` for each parameter of each People object,
  with one value for the model or a dictionary with a value for each target, and reused an existing schedule with its
  old value. A5 asks for `clothing_insulation` as a number, `'dynamic_ashrae55'` (the method
  `DynamicClothingModelASHRAE55` of the field *Clothing Insulation Calculation Method*, in the People objects of the
  IDDs of 9.4 to 25.2 and in the People:Instance objects of 26.2) or a dictionary by season "aligned with
  cooling_season_start/end", and the same dictionary for `activity_level`. The function had no cooling season, and its
  dictionaries already meant "by target".
- **Decision**: a dictionary whose keys are among `'heating_season'` and `'cooling_season'` is by season (with both
  keys and numbers, or a `ValueError`); any other one is by target, as before, and its values can also be dictionaries
  by season or `'dynamic_ashrae55'` (only for the clothing insulation). The keyword-only arguments
  `cooling_season_start` and `cooling_season_end` (after `verbose`, so that positional calls keep their meaning) have
  the defaults and the meaning of those of the setpoints (from the first day to the day before the second one, also
  across the new year), and give the `Through:` dates of the schedule, those of a year that is not a leap year, as
  `transform_ddmm_to_int`. `'dynamic_ashrae55'` only sets the method and keeps the clothing insulation schedule, which
  EnergyPlus does not read with it; a number or a dictionary by season sets `ClothingInsulationSchedule` back when the
  field has another method, and does not touch an empty field, so earlier models do not change. Each call replaces the
  schedules of the parameters that it receives, which fixes the reuse of the old value.
- **Consequences**: the user gives the same cooling season to the setpoints and to `set_pmv_input_parameters`. With the
  daylight saving time of a model, EnergyPlus changes the schedule one hour before the EMS programs change the season
  (at 0:00 of the local time instead of the standard time), on the same day; documented in
  [[../CAMBIOS_CODIGO_v1.2.0.md]] §4. The clothing insulation as a function of the outdoor temperature (which needs E1)
  and `set_clothing_method` of the proposal are pending in [[../TODO.md]]. Section 4.8 of
  [[../docs/source/4_detailed use.md]].

## 2026-11-09 — The ePMV applies the expectancy factor in the cooling season to the warm side only, and its metabolic correction uses the PMV of the previous timestep

- **Status**: accepted (the author chose, for A1: "e solo en la estación de refrigeración y en la consigna de
  refrigeración; apply_to_heating=True lo aplica también a la de calefacción, con aviso", with the ePMV of each zone
  coherent with it, and the metabolic correction "opcional (metabolic_correction=False por defecto), documentando la
  aproximación y el efecto en las ganancias internas"; the How-to notebook written but not run, "déjalo como tarea
  pendiente")
- **Context**: Fanger and Toftum (2002) define ePMV = e·PMV for buildings without air-conditioning in warm climates,
  and only the upper limit of the comfort zone depends on e (their Table 3). They also reduce the metabolic rate by
  6.7 % for each unit of PMV, calculated with the uncorrected rate, and calculate the PMV again. EnergyPlus calculates
  the PMV once per timestep, at its end, with the activity level of the People objects, which also gives their heat
  gains; an activity level schedule may be shared by several People objects, and a People object may apply to several
  zones (OpenStudio models: one People object for a SpaceList).
- **Decision**: the index `'epmv'` of [[decisions.md#2026-11-08 — The setpoints based on indices derived from the PMV share one engine, with the Erl of each index in a registry|the engine]]:
  e (0.5 to 1, `ValueError` otherwise) in the cooling season and 1 in the heating season; the PMV setpoint of the
  cooling thermostat is the setpoint divided by e, the heating setpoint is a PMV setpoint unless `apply_to_heating`
  (warning); the ePMV of each zone is e·PMV for positive PMV and the PMV otherwise (always e·PMV with
  `apply_to_heating`), so that the hours within the setpoints are counted with the index that the thermostat keeps. The
  metabolic correction (EMS programs run after those of the zones, at `BeginTimestepBeforePredictor`) multiplies the
  activity level of each People object by 1 - 0.067·PMV, with the PMV of the previous timestep, between 0 and 3, in the
  cooling season; each People object gets its own activity level schedule, a copy of its own that the EMS sets, and an
  EMS sensor reads the original one; a People object of several zones is corrected with the mean PMV of its occupants
  in them (warning). `set_pmv_input_parameters` refuses to set the activity level of a corrected People object. The
  engine gets `PmvIndex.add_objects` for these objects.
- **Consequences**: the correction converges to the activity level whose PMV gives it, slightly less than Fanger and
  Toftum (5.5 to 6.1 % instead of 6.7 % for a PMV of 1 with 1 to 1.2 met; PMV 0.01 to 0.04 higher), and the heat gains
  of the occupants follow it one timestep later (EnergyPlus calculates the internal gains before the calling point),
  both documented in section 4.8.1 of [[../docs/source/4_detailed use.md]]. The ePMV is also a parameters type of the
  parametric module and an index of the tab *2. PMV-based setpoints* of the GUI. Section 3 of
  [[../CAMBIOS_CODIGO_v1.2.0.md]]; the notebook to run is in [[../TODO.md]].

## 2026-11-08 — The setpoints based on indices derived from the PMV share one engine, with the Erl of each index in a registry

- **Status**: accepted (proposal A2 of the author's file of proposals after 1.1.0,
  `notes/PROPUESTAS_MEJORAS_post_1.1.0_v01.md`; the author chose the P1 proposals of its block A for the branch
  `v1.2.0`: A2, A1 and A5)
- **Context**: the aPMV setpoints (`apply_apmv_setpoints`), the ePMV setpoints of A1 and setpoints of the PMV itself
  need the same thermostats (Fanger, dual setpoint), sensors, actuators, averaged PMV of the zones with several
  occupant instances and hour counters; a function per index would copy about 600 lines of `accim/sim/apmv.py` for
  each one.
- **Decision**: `accim/sim/pmv_index.py` has the engine, `apply_pmv_index_setpoints(building, index,
  index_parameters, ...)`, moved from `apmv.py` with the same code, and a registry `PMV_INDICES` of `PmvIndex`
  objects with what depends on the index: its name in the EMS objects (`apply_<name>_<zone>`, `<name>_<zone>`...),
  its parameters by zone (lines of `set_zone_input_data_<zone>`), the coefficient of each season, the inverse (the
  PMV setpoint of the thermostat from the setpoint of the index) and the monitor (the index of the zone; none for the
  PMV, whose index is the sensor `PMV_<zone>`). `apply_apmv_setpoints` and the new `apply_pmv_setpoints` are thin
  wrappers in `accim.sim.apmv`, the module that users import; the output IDFs of the aPMV do not change (golden
  master). A model has the setpoints of one index only (`ValueError`), and the modifiers of the parametric module
  (`param_apmv`) find the lines by the names of their variables, since their positions depend on the index.
- **Consequences**: a new index is an entry of `PMV_INDICES` (a few Erl lines) and a wrapper with its arguments.
  The EMS variables of the aPMV keep the names of accim 0.x (`adap_coeff_cooling_<zone>`...). Section 2 of
  [[../CAMBIOS_CODIGO_v1.2.0.md]], section 4.8 of [[../docs/source/4_detailed use.md]].

## 2026-11-08 — The GUI gives fields for the arguments of each zone and asks for the confirmation of AddAccis after the estimated size

- **Status**: accepted (the author asked to review whether the GUI was up to date with the code, "no he visto ninguna
  opción para especificar la configuración de accis (comfort standard, etc) por zona", and then to work
  autonomously)
- **Context**: the table of `zone_arguments` existed since 2026-11-02, but at the end of the tab *Add the ACCIS*
  (y = 1122 of 1497 px, with 600 px visible), below the existing HVAC systems and the tolerances, and with a single
  free-text field of pairs `name=value`; the author did not find it. The functions of 1.1.0 (the EMS code of the
  setpoints, the size of the results, which `AddAccis` prints before writing the output IDFs so that other outputs can
  be chosen) and some arguments (`vrf_*`, the offsets of the category, `setpoint_accuracy`, `debug_ems`, the
  dictionaries of `apply_apmv_setpoints`, the zones of `filter_by_hours_within_setpoints`) were not in the GUI, which
  asked for the confirmation before running `AddAccis` with `confirm=True`.
- **Decision**: a table of the zones shared by *Add the ACCIS* and *aPMV setpoints* (`_ZoneTable` in
  `accim/gui/app.py`): the zone (from *Find the occupied zones*, or typed), a field for each main argument (comfort
  standard, category, comfort mode, HVAC mode and ventilation control; the adaptive coefficients and aPMV setpoints)
  and the others as pairs `name=value`; the rows keep the text of the arguments, so the session files do not change.
  The table of `zone_arguments` goes right below the comfort models, and the buttons of the two tabs stay at the
  bottom. The forms check each zone with every output IDF (`forms.zone_arguments_problems`, with the functions of
  `accim.sim.generation` that `AddAccis` uses). The window runs `AddAccis` with `confirm=None` and answers its
  question with a dialog that shows what it printed (the number of output IDFs and the estimated size of their
  results): a task can now ask the user through `AccimApp.ask_from_task`, and the answers of `_no_prompts` can be
  functions of the question and of what the task printed. The zones of the aPMV setpoints are given by their names
  and get the keys of their targets in the task (`tasks.apmv_target_keys`); an unknown zone stops it, since
  `apply_apmv_setpoints` only warns.
- **Consequences**: `accim/gui/forms.py`, `tasks.py` and `app.py`; tests in `tests/core/test_gui.py`; section 4.10 of
  [[../docs/source/4_detailed use.md]]. Still in Python only: the `custom` output type, `modify_accis()`, the other
  figures and the reshaping of `Table`, and the aPMV setpoints, outputs, objectives, optimisations and plots of the
  parametric module.

## 2026-11-08 — The size of the results is estimated from the outputs of the models, and AddAccis prints it before writing the output IDFs

- **Status**: proposed (implemented in the branch `v1.1.0` at the request of the author, "añadir función o método
  para estimar el peso de los resultados de simulación, de forma similar al existente en parametric_and_optimisation,
  pero que funcione con el módulo run; me gustaría que se pudiera estimar sin simulación, o de forma más exacta, con
  simulación, y que el usuario lo pueda elegir", and "también estaría bien conocer el peso estimado cuando se genera
  el idf, para poder decidir sobre los outputs"; the details are for his review)
- **Context**: `run_ep` writes about 30 MB in each simulation of a standard hourly output IDF of the sample model, so
  140 output IDFs with 6 EPWs take about 25 GB. The estimate of the parametric module is the memory of the hourly
  tables (`get_hourly_df_parametric`), not the size of the files. Reading an output IDF with eppy takes about 0.7 s.
- **Decision**: the size is the disk space of the files of the simulations (the memory to read the values of the CSV
  files, at 8 bytes each as in the parametric module, is also given). Without simulation
  (`accim.sim.results_size.estimate_simulation_size`), it counts the values that the outputs of the model report and
  the times they are reported, with the bytes of each value measured in the files of EnergyPlus 25.1; with
  simulation (`accim.run.estimate_results_size(simulate=True)`), it runs one simulation of each group of IDFs with the
  same outputs, as `run_ep` runs it, in a temporary folder, and measures its files. The groups are made from the text
  of the IDFs (their output objects and the number of objects of each type), not with eppy, only to compare them
  (an exception to [[#2026-11-06 — `accim.sim` reads, changes and writes the models with eppy, even where code of its own was faster|reading the models with eppy]]:
  eppy would take more than a minute for 140 output IDFs); the representative of each group is read with eppy.
  `AddAccis` prints the estimate of each model before asking whether to write the output IDFs, and keeps it in
  `results_size`; `add_accis_to_idf` does not print it (the parametric module calls it for each sample).
- **Consequences**: the estimate is approximate: within 10 % of the files for results of more than 5 MB in 16
  simulations (9 of calibration, 7 of validation with example files of EnergyPlus), within 45 % for smaller ones,
  and short for the variables whose keys it does not know (counted as one, and named in its notes) or reported at each
  HVAC timestep. The bytes per value were measured with EnergyPlus 25.1 on Windows (line ends of two bytes); other
  versions write the same formats. Sections 4.1, 4.4 and 4.6 of [[../docs/source/4_detailed use.md]], section 9 of
  [[../CAMBIOS_CODIGO_v1.1.0.md]].

## 2026-11-07 — Mixed mode air-conditions the zones on the design days with `vrf_mm` too

- **Status**: accepted (option (a) of the question of [[questions.md]], chosen by the author on 2026-11-07)
- **Context**: since the decision below (of the same day), `ex_mm` air-conditions the zones on the design days with the
  windows closed, occupied or not: its HVAC systems were off on the design days without occupants, and EnergyPlus
  sized them for no load. `vrf_mm` had the same rule (the HVAC systems off without occupants and while the windows are
  open) and autosized VRF systems, but it was left as it was, as an open question, since the request was about `ex_ac`
  and `ex_mm`.
- **Decision**: the same rule for `vrf_mm`: its programs `ApplyAST_<zone>` and `SetWindowOperation_<window>` end with
  the lines of the design days, and the sensor `DesignDay` is added in mixed mode (`ems.objects.add_design_day_sensor`,
  moved from `hvac/existing.py`).
- **Consequences**: the output IDFs of `vrf_mm` change (the 12 configurations of `vrf_mm` of the golden master, only
  with added lines), and so the sizes of its VRF systems: with the sample model, whose winter design day has no
  occupants, the heating design loads of its two zones go from 0 (EnergyPlus warned that they were zero) to 1.9 and
  2.2 kW, and the cooling design loads, and so the VRF systems, are about 6 % lower, since the peak no longer includes
  the pull-down after the hours without occupants. Section 4.1 of [[../docs/source/4_detailed use.md]], section 9.4 of
  [[../docs/source/9_migration_guide.md]] and section 8 of [[../CAMBIOS_CODIGO_v1.1.0.md]].

## 2026-11-07 — In mixed mode accim takes the whole control of the windows it opens, and `ex_mm` air-conditions the zones on the design days

- **Status**: proposed (done in the branch `v1.1.0` while the author asked to work autonomously: "quiero que pruebes
  distintos idfs [...] con distintos HVAC system para comprobar que funciona en cualquiera", "en el ex_mm puede haber
  ventilación scheduled o con airflow network" and "las ventanas se deben poder abrir y cerrar cuando sea necesario
  para trabajar en modo mixto"; he may revise it)
- **Context**: `ex_ac` and `ex_mm` were run with 618 example files of EnergyPlus 25.1 (see [[../DEVLOG.md]],
  2026-11-07). In mixed mode, accim only found the AirflowNetwork windows named as in DesignBuilder; it took the fans of
  the `ZoneVentilation:DesignFlowRate` objects as windows; it kept the limits of the `ZoneVentilation` objects, which
  kept closed the windows that the EMS opened (the first window of the OSM residential model of the golden master never
  ventilated: its maximum indoor temperature was a schedule of 1 °C); and the occupant ventilation controls and hybrid
  ventilation managers of the models overrode the EMS. With `ex_mm`, the HVAC systems were off on the design days
  without occupants, so EnergyPlus sized them for no load (it stopped with the furnaces of `House-2FurnaceAC-*`).
  Thermostats of ZoneLists stopped accim, and thermal comfort (PMV) and staged thermostats kept the zones away from
  the setpoints.
- **Decision**: the windows of mixed mode are found by what EnergyPlus simulates (`accim.sim.windows`): the exterior
  windows, doors and glass doors with AirflowNetwork openings when the AirflowNetwork simulates the multizone
  airflows, otherwise the natural ventilation `ZoneVentilation` objects (also of spaces and lists, split for each
  zone). accim takes their whole control: their own limits are removed, and the occupant ventilation controls of these
  windows (also that of their zones, which is given to the other openings of the zones) and, when accim controls
  windows, the hybrid ventilation managers (which act on all the ventilation objects of the zones of their air loops)
  are removed with a warning, except the hybrid ventilation managers of an AirflowNetwork that simulates the air
  distribution system together with the windows (`MultizoneWithDistribution`), which stay so that the air loops are off
  while the windows are open (EnergyPlus stopped without them). With `ex_mm`,
  the design days (day types `SummerDesignDay` and `WinterDesignDay`, sensor `DesignDay`) are air-conditioned with the
  windows closed, occupied or not. The thermostats of ZoneLists are split per zone; with
  `existing_hvac_operative_temperature_control=True`, the PMV thermostats of the occupied zones are removed and the
  staged thermostats get the setpoint schedules of their zones (with `False`, warnings).
- **Consequences**: the output IDFs of `ex_mm` change (design days), and those of `vrf_mm` and `ex_mm` with
  `ZoneVentilation` objects with limits or fans (golden master `b13` and `b15`). The rule of the design days was not
  applied to `vrf_mm`; the author chose to apply it too (see
  [[#2026-11-07 — Mixed mode air-conditions the zones on the design days with `vrf_mm` too|the decision above]]). The
  sizing periods of the type `SizingPeriod:WeatherFileDays` are not detected as design days. Sections 4.1, 4.1.1 and
  4.1.2 of [[../docs/source/4_detailed use.md]], section 9.4 of [[../docs/source/9_migration_guide.md]], section 8 of
  [[../CAMBIOS_CODIGO_v1.1.0.md]].

## 2026-11-06 — Each output IDF of `AddAccis` only has the EMS code of the comfort standards of its zones, and the EMS programs are indented

- **Status**: accepted (option 1, the recommendation, chosen by the author on 2026-11-07 for the question of
  [[questions.md]]; implemented before in the branch `v1.1.0` for his review: he had asked whether the EMS
  code could be indented, "de forma que se pueda ver claramente dónde empiezan y terminan los bloques
  if-elif-else-endif", and what I thought of "añadir únicamente el EMS program para las consignas especificadas, en
  lugar de añadir todas las líneas de todos los posibles comfort_standard"; he was not available to choose among the
  options below, so the recommended one was implemented)
- **Context**: the models had the code of the 24 comfort standards in `SetComfTemp`, `SetAppLimits`, `ApplyCAT`,
  `CountHours_<zone>`, `SetAST_Master` and the subprograms `SetAST_CS<n>_<chunk>`, so that the comfort standard of a
  zone could be changed in its program `SetInputData_<zone>`: the parametric module does it in each sample, and
  `AddAccis` writes all its output IDFs from one model. An output IDF of the sample model with two zones had 78
  programs with 6851 lines (645 KB), 5166 of them in the subprograms. The lines had no indentation, and eppy removes
  the spaces at the beginning of the fields when it reads an IDF.
- **Decision**: of the options (1) the code of the comfort standards of each output IDF in all the programs that
  depend on the comfort standard, (2) only in the subprograms and `SetAST_Master` (less code, but `SetComfTemp`,
  `SetAppLimits` and `ApplyCAT` would still have every comfort standard) and (3) the code of all of them, as before,
  option 1. `AddAccis` writes in each output IDF the code of the comfort standards of its zones
  (`ems.programs.set_comfort_standard_code`, with the chains cut by `ems.program_lines.for_comfort_standards`);
  `add_accis_to_idf` keeps the code of all of them (the parametric module needs it); `modify_accis`, and
  `modify_ComfStand` of the parametric module, add the code that a model lacks and remove none. A program without code
  for the comfort standards of the model only returns
  (EnergyPlus needs a line). The lines are indented with 4 spaces for each block `IF` or `WHILE`: `add_program` and
  `set_program_lines` indent what they write, and `AddAccis` and `modify_accis` indent all the programs and subroutines
  of the model (`indent_programs`).
- **Consequences**: the comfort standard of an output IDF can only be changed with `modify_accis` (by hand,
  EnergyPlus stops); the category, the comfort mode and the other inputs can still be changed by hand. The output
  IDFs are about half as large (357 KB, 34 programs with 1393 lines) and give the same results (the Erl compiler of
  accim with every comfort standard, category and comfort mode; 19 pairs of output IDFs in EnergyPlus 9.4, 9.6, 25.1
  and 26.2), and `AddAccis` takes about the same time. The golden files of the 22 configurations of `AddAccis` were
  written again. Details in section 7 of [[../CAMBIOS_CODIGO_v1.1.0.md]], in [[../CHANGELOG.md]] and in section 9.4
  of [[../docs/source/9_migration_guide.md]].

## 2026-11-06 — `accim.sim` reads, changes and writes the models with eppy, even where code of its own was faster

- **Status**: accepted (the author asked for another restructuring of accim "using, when possible, eppy", mainly in
  `accim.sim`, in a new branch `v1.1.0`, "as easy and simple to understand as possible"; then, that he prefers it
  "more understandable even if a bit slower", and that eppy is better than besos whenever possible)
- **Context**: the restructuring of 1.0.0 kept code of its own where eppy has methods: helpers
  (`accim.sim.idf_tools`: `try_objects`, `remove_objects`, `copy_idf`, `idf_text`, the lines of the EMS programs
  through `.obj`), lookups by name with lists, raw `.obj` slices, an `IdfWriter` that wrote the output IDFs from text
  rendered once, and a parser of IDF text in the Python API backend; and `load_idf('auto')` read the models with
  besos. eppy is slower where 1.0.0 had optimised: `EpBunch.__repr__` formats the comments of all the fields of the
  IDD of each object, so saving each output IDF with eppy took 126 ms instead of 7 ms with the sample model.
- **Decision**: eppy wherever it has the method, and besos only where its features are needed (the parametric
  module; running EnergyPlus and reading the ESO in `accim.utils.outputs`). `load_idf` reads every model with eppy
  (the version of its `Version` object, the IDD where accim finds it); `AddAccis` reads each file twice
  (`input_idfs`, and the model that gets the ACCIS), keeps the text of each model (`IDF.idfstr`, since an eppy model
  takes about 140 times the memory of its text) and saves each output IDF with `IDF.savecopy`, after
  `generation.set_combination`; existence checks with `IDF.getobject` (case-insensitive, as EnergyPlus);
  `removeallidfobjects`; `fieldvalues`/`key` instead of `.obj`; the API backend reads and changes the model with eppy
  (`read_ems`, `prepare_for_api`) and saves it. Small helpers only where eppy has none: `ems.programs.add_program`
  and `set_program_lines`, `ems.objects.add_sensor`, `hvac.schedules.add_compact_schedule`. `Table`, `chile_funcs`
  and the functions of `accim.utils` that only read an IDF use `load_idf`.
- **Consequences**: `AddAccis` is slower with many output IDFs (`AddAccis` with the 140 of the sample model: 17 s instead of about 6 s).
  One EnergyPlus version per Python session for every reading of accim, also with `'auto'`, in `Table` and in
  `run_simulation` (a clear `ValueError`; before, besos only warned). The output IDFs write some numbers as eppy does
  (same values and results; the golden files of 19 configurations were written again), and `input_idfs` and
  `output_idfs` are eppy objects, without the methods of besos. The internal helpers removed are listed in
  [[../CHANGELOG.md]] and in section 9.4 of [[../docs/source/9_migration_guide.md]]; the guide for the maintainer is
  [[../CAMBIOS_CODIGO_v1.1.0.md]]. Code that reads numeric fields must not use `value or ''`: eppy gives 0 as a
  number (the bug of the outdoor temperature limits of 0 °C, fixed).

## 2026-11-03 — Tables and sessions are saved in a pickle file, to resume them, and a JSON file, to read them

- **Status**: accepted (the author asked to save a pickle file that resumes the session of the classic workflow, as
  in the research paper notebook, "as the parametric module already does", also in the GUI, with a readable JSON
  file; he chose both `Table.save`/`Table.load` and `save_session`/`load_session`, and in the GUI the whole session
  plus opening tables saved in Python)
- **Context**: the results of `run_ep` stay in the CSV files, but the tables of `Table` were lost with the session,
  and making them again reads every CSV file (an hourly table of only 4 sample CSV files takes about 9 s; one of the
  20 of the case study, much longer). The GUI forgot its forms and results when closed.
- **Decision**: two files with the same name: a pickle file (`pd.to_pickle`, as the parametric module), which
  resumes the session, written first, and a JSON file only for reading (metadata first, strict JSON: NaN as `null`,
  infinity as `"Infinity"`, `ensure_ascii=False`), never read back, in which each DataFrame shows its number of rows
  and its first 1000 rows (`json_max_rows`; `None` for all): the whole JSON of the hourly table of the 4 sample CSV
  files took 5.4 s and 70 MB (its pickle, 0.06 s), and the review of the change found 21.5 s, 292 MB and 0.5 GB of
  memory for 24 simulations; with the limit, 0.11 s and 2.3 MB. `Table.save`/`Table.load` pickle the `Table` itself
  (all its attributes, so that its methods work as before), with `Table._JSON_ATTRIBUTES` in the JSON (`df` as
  `format_table` left it, not `df_backup`); `accim.utils.save_session(filename, /, *, json_max_rows=1000, **objects)`
  pickles a dictionary with `accim_session` (format 1), the version, the date, the working folder and the objects,
  and `load_session` returns the objects by name. Each file is written through a temporary one; an object that
  pickle cannot save is named in the error. `Table` keeps `arguments` and the `type_of_table`/`custom_cols` of the
  last successful `format_table` (`'all'` after one that fails), so that the GUI can make a table again from
  `df_backup` before each figure. The GUI session (menu *Session*) is a `save_session` file with `gui_forms` (the
  folder and the `state()` of each tab) and the results of the tabs 5, 6 and 7; opening it replaces the forms and
  the results, and lists the files that are no longer in the folder.
- **Consequences**: pickle files can run code when they are read, and need a pandas that reads those of the version
  that saved them (documented); the pickle files of hourly tables of many simulations are large, as their CSV files.
  A table saved in Python
  opens in the tab *Table and figures*, and a session of the GUI loads in Python with `load_session`. Section 4.7.2
  of [[../docs/source/4_detailed use.md]]; tests in `tests/core/test_session.py` and `tests/core/test_gui.py`.

## 2026-11-03 — The radiant systems, ventilated slabs and cooling panels follow the setpoints with `existing_hvac_radiant_setpoints`

- **Status**: accepted (the author answered the TODO item on 2026-11-03: "yes, but as one or several True/False
  arguments that apply the change or not, in line with the previous decisions", and chose `True` as the default)
- **Context**: with `ex_ac` and `ex_mm`, these objects heat or cool with setpoint schedules of their own, not with
  the thermostats, so their zones kept the setpoints of the model (65 to 82 % of the occupied hours of the example
  file `RadLoHydrHeatCoolAuto` of EnergyPlus within the setpoints, in a year in Seville). Since 2026-11-02 accim only
  warned about them.
- **Decision**: one argument, `existing_hvac_radiant_setpoints` (`True`), in `AddAccis`, `add_accis_to_idf`, the
  classes of the parametric module and the GUI. Those of the occupied zones get the setpoint schedules of their zones
  in the setpoint fields that they have (so they keep heating, cooling or both) and the operative temperature as their
  control temperature; the constant flow systems and ventilated slabs get the same schedule as high and low control
  temperature (on/off at the setpoint, which EnergyPlus accepts: checked in its sources); the `:Design` objects shared
  by several zones are copied per zone; the cooling panels of zones with a thermostat get `ZoneTotalLoad` instead,
  because their operative temperature control gave plant flow errors in `5ZoneCoolingPanelBaseboard`. `False` keeps
  them as in 0.x, with the warning.
- **Consequences**: the output IDFs of the models with these objects change by default (none of the golden master);
  `RadLoHydrHeatCoolAuto` reaches 99.5 to 100 % within the setpoints, and the hours that remain in other example files
  come from the models (radiant systems that only heat, slow slabs, capacity). The zones whose radiant systems follow
  the setpoints are not reported as zones without a thermostat. Section 4.1.1 of [[../docs/source/4_detailed use.md]].

## 2026-11-03 — The GUI shows the `existing_hvac_*` arguments with the existing HVAC systems

- **Status**: accepted (answer of the author to the TODO item on 2026-11-03)
- **Context**: the tab *Add the ACCIS* used the defaults of these arguments without showing them.
- **Decision**: a frame with the four booleans and the availability schedule (empty, `On 24/7` or any schedule
  typed), enabled with `ex_ac` and `ex_mm` (the two options of the setpoints only with temperature setpoints), in
  *Add the ACCIS* and in *Parametric study* (with `ex_ac`, its only existing HVAC script type). The other script types
  do not get these arguments.
- **Consequences**: `accim/gui/forms.py` (`EXISTING_HVAC_*`, `existing_hvac_arguments`), `app.py`, `tasks.py`;
  tests in `tests/core/test_gui.py`.

## 2026-11-03 — ESP CTE and INT ISO7730 keep one row per combination of the other parameters in the full sets

- **Status**: accepted (answer of the author to the TODO item on 2026-11-03)
- **Context**: `drop_invalid_param_combinations` dropped all the rows of ESP CTE (`comfort_standard` 0) when the
  plan had `category` or `comfort_mode`, and kept INT ISO7730 (22) only with `comfort_mode` 0, although their
  setpoints do not depend on these parameters (ESP CTE: neither; ISO7730: not on the comfort mode).
- **Decision**: their rows are kept only with the first value of these columns in the plan (`pd.unique(...)[0]`),
  so each one is simulated once for each combination of the other parameters.
- **Consequences**: plans with these columns can compare ESP CTE with the other standards; the results tables have
  one row of them per combination, with the first category and comfort mode of the plan. Migration guide, 9.3.

## 2026-11-03 — The heating setpoints of CHN Yang with `ComfMod` 2 are those of the source of the standard

- **Status**: accepted (the author checked the formulas of `(6, 2)` and `(6, 3)` against the source and corrected 2
  lines of `(6, 2)` on 2026-11-03); supersedes the decision of 2026-10-31 on comfort standard 6 below
- **Context**: within the applicability limits, the heating setpoint of `(6, 2)` used the formula of the cooling
  setpoint, as in 0.x.
- **Decision**: `PMOT*0.32+14.88` (category 80) and `PMOT*0.31+17.14` (category 90), as in `(6, 3)`.
- **Consequences**: the subprogram `SetAST_CS6_0` changes in every output IDF (every configuration of the golden
  master was written again, and only these 2 lines differ); the results change only with comfort standard 6 and
  comfort mode 2. Test in `tests/core/test_setast_chn_yang.py`.

## 2026-11-02 — The existing HVAC systems keep the operative temperature between the setpoints with arguments `existing_hvac_*`

- **Status**: accepted (asked by the author on 2026-11-02, who chose the default of the operative temperature control,
  the availability as an option with a warning, and the names; the rest was done while he asked to work
  autonomously, "if they are False, it is simulated as it is", so he may revise it)
- **Context**: With `ex_ac` and `ex_mm`, the operative temperature could be out of the adaptive setpoints in many
  hours (the author used the VRF systems of accim instead). The causes (simulations in
  [[../DEVLOG.md]], 2026-11-02): the existing thermostats controlled the air temperature, while the VRF systems of
  accim control the operative temperature; accim only gave the setpoints to the first control of each thermostat
  (the thermostats of the example files of EnergyPlus kept the setpoints of the model, and EnergyPlus stopped); the
  HVAC systems may be unavailable while the zones are occupied, may lock out their compressors or heaters with some
  outdoor temperatures, or may lack capacity, controls or equipment that heats or cools; and the radiant systems,
  ventilated slabs and cooling panels follow setpoint schedules of their own.
- **Decision**: four arguments of `AddAccis`, `add_accis_to_idf` and the classes of the parametric module, in
  `accim/sim/hvac/existing.py`: `existing_hvac_operative_temperature_control` (`True`: the thermostat of each
  occupied zone uses only a dual setpoint object of its own with the schedules of the zone, always, and controls the
  operative temperature as those of the VRF systems; `False`: the thermostats as in accim 0.x);
  `existing_hvac_availability_schedule` (`None`, with a warning; a schedule for the HVAC objects that heat or cool,
  the operation schemes with one scheme and the availability managers of the air and plant loops);
  `existing_hvac_widen_outdoor_temperature_limits` (`False`, with a warning; the limits of the VRF systems, -20 and
  80 °C, within the IDD); and `existing_hvac_ideal_loads_backup` (`False`; an ideal loads air system as the last
  equipment of each occupied zone, for the load that the existing system does not meet, whatever it is). Only
  warnings for the objects with setpoints of their own.
- **Consequences**: the output IDFs of the models without operative temperature thermostats change by default (the
  OSM office of the golden master: `b10`, `b11`, `s04`); those of DesignBuilder and of the VRF systems do not. The
  models with the thermostats of the example files of EnergyPlus simulate. With all the options, the sample models
  have 99.7 to 100 % of the occupied hours between the setpoints in a year in Seville; the energy of a backup is
  reported apart (district heating and cooling), as the loads that the existing system does not meet. Pending
    ([[../TODO.md]]): the radiant systems following the setpoints, and the arguments in the GUI (both done on
    2026-11-03, see the decisions above).

## 2026-11-02 — The arguments and parameters have descriptive names, the same in the whole package

- **Status**: accepted (the author's answer of 2026-11-02 to the open question of the names: option (a), and the
  parametric module too)
- **Context**: The names of 1.0.0 were a mechanical translation of those of 0.x to snake case
  ([[#2026-10-30 — PEP 8 names with deprecated aliases for accim 0.x|decision of 2026-10-30]]), with their
  abbreviations (`comf_mod`, `cat`, `vst_offset`...). The author asked for a review ("`ComfMod` no me gusta"), chose
  the suggested names, and asked that the arguments and parameters of `accim.parametric_and_optimisation` take the
  names of `accim.sim` ("el módulo debe ser consistente con el resto"), although the decision of 2026-10-30 had kept
  them.
- **Decision**: The arguments of `AddAccis`, `add_accis_to_idf`, `modify_accis` and `zone_arguments`, of
  `apply_apmv_setpoints` and the other functions of `accim.sim.apmv`, of `run_ep`, and the arguments, attributes and
  parameters of the parametric module have descriptive names, the same everywhere: `comfort_standard`, `category`,
  `comfort_mode`, `setpoint_type`, `output_frequencies`, `ventilation_control`, `min_opening_factor`,
  `setpoint_tolerance`, `custom_slope`..., `adaptive_coefficient_cooling`, `pmv_cooling_setpoint`,
  `only_accim_idfs`, `processes`, `use_default_values`... (the full list is in §9.2 of
  [[../docs/source/9_migration_guide.md]]). The names of 0.x stay as deprecated aliases with `DeprecationWarning`:
  arguments (`accepts_legacy_kwargs`), attributes of the parametric classes, names of parameters (`'ComfStand'`,
  `'CustAST_m'`... in `set_parameters`, `accis_parameter`, the samples and the plans) and columns of the results
  saved with 0.x, renamed when they are loaded. The snake-case names of the earlier commits of `v1.0.0` were never
  released, so they get no alias. The EMS variables (`ComfStand`, `CAT`...), the tags of the names of the output
  IDFs (`[CS_`, `[CA_`, `[CM_`...), the columns of `Table`, the texts of the prompts, the `modify_*` functions of
  `param_accis` and the class names of the wrappers of `parameters.py` keep their names: they are read by the EMS
  programs, by `Table` or by the results of earlier versions.
- **Consequences**: The output IDFs do not change (golden master). The scripts, notebooks and saved results of 0.x
  keep working with warnings; the documentation and the example notebooks use the new names. The aliases are removed
  with the others in a future major version ([[../ROADMAP.md]], R-03).

## 2026-11-02 — The GUI keeps tkinter and gets tabs for more steps

- **Status**: accepted (the author's answer of 2026-11-02 to the open question of the GUI: the first option)
- **Context**: [[#2026-11-01 — The first GUI uses tkinter and covers AddAccis, run_ep and the hours within the setpoints|The first GUI]]
  had three tabs; the open question offered more tabs with tkinter, a web interface as an optional extra, or leaving
  the rest in Python.
- **Decision**: tkinter, with seven tabs that share the working folder: *Add the ACCIS* (now with a table of the
  arguments of some zones, `zone_arguments`, and the occupied zones of the IDF), *aPMV setpoints*
  (`apply_apmv_setpoints`, the same setpoints in all the zones), *Rename the EPWs* (`rename_epw_files`), *Run the
  simulations*, *Hours within the setpoints*, *Table and figures* (`Table`, its scatter and time plots saved as PNG
  files) and *Parametric study* (a basic `ParametricSimulation`: full set or Latin hypercube, sums of meters). The
  forms stay in `forms.py` and the tasks that call accim are in `tasks.py`, both without tkinter, so they are tested
  without a display. A task can get fixed answers for the questions of the prompt that the GUI knows (those of
    `rename_epw_files` about amending or excluding EPWs, and those of the figures of `Table` about renaming the rows and
    columns of the subplots); any other question stops it with an error.
- **Consequences**: No new dependency. Still in Python only: the `custom` output type, different aPMV setpoints for
  each zone (in the GUI since
  [[#2026-11-08 — The GUI gives fields for the arguments of each zone and asks for the confirmation of AddAccis after the estimated size|2026-11-08]]),
  the other figures and the reshaping of `Table`, and the outputs, objectives, optimisations and plots of
  the parametric module. eppy keeps one IDD per process, so IDFs of different EnergyPlus versions need a new session
  of the GUI.

## 2026-11-02 — The check of `claude/admiring-cori-fe6c57` is ported to `v1.0.0`, and the branch is deleted

- **Status**: accepted (the author asked on 2026-11-02 for the recommended option)
- **Context**: The local branch `claude/admiring-cori-fe6c57` (2 commits of 2026-10-19 on the old `master`, with a
  worktree in `.claude/worktrees/`) kept the `tests` package out of the wheel of accim, which `setup.py` of `v1.0.0`
  already does, and added a check to `packaging/release.py check` and the update of [[../packaging/README.md]]
  (its §7 still listed the problem as pending). Merging it conflicts in `CHANGELOG.md`, `notes/work-log.md` and
  `setup.py`.
- **Decision**: port only what `v1.0.0` lacked: the check of `release.py` (no top-level entry in the wheel of accim
  other than `accim` and its `.dist-info`), step 5 of §4.3 of the guide without its §7, and the CHANGELOG entry (the
  0.8.2 wheel installed `tests`). The branch was saved in a git bundle in the git-ignored
  `llm_project_files/branch_review_reports/`, and its worktree and the branch were removed (git refused to remove the
  worktree while its gitdir had an empty `modules` folder, which was deleted first).
- **Consequences**: checked with a wheel of `v1.0.0` built in a temporary folder (only `accim` and its
  `.dist-info`: no problem) and with a copy that adds `tests/__init__.py` (reported). `master` gets the change
  when it is fast-forwarded to `v1.0.0`.

## 2026-11-01 — The first GUI uses tkinter and covers AddAccis, run_ep and the hours within the setpoints

- **Status**: superseded in its scope by [[#2026-11-02 — The GUI keeps tkinter and gets tabs for more steps]]
  (accepted for the first version: priority task asked by the author on 2026-11-01; its item said that he would
  choose the scope and the technology, which he did on 2026-11-02)
- **Context**: A GUI in English, so that users without Python can add the ACCIS, run the simulations and look at the
  results. accim is used on Windows with EnergyPlus; its steps print a lot, ask in the prompt when an argument is
  missing, run long and use processes (`run_ep`).
- **Decision**: tkinter (with Python on Windows and macOS: no new dependency) in a package `accim.gui`, with the
  command `accim-gui` (`console_scripts`, so that EnergyPlus keeps a console) and `python -m accim.gui`. Three tabs
  with a common working folder: `AddAccis` (all the arguments of its prompts, except `custom` outputs and the
  arguments of each zone), `run_ep` (both backends) and the hours within the setpoints
  ([[../DEVLOG.md]], 2026-11-01). The logic of the forms (`forms.py`: choices, defaults, checks, the arguments of
  accim, the preview of the number of output IDFs) does not import tkinter, so it is tested without a display. Each
  task runs in a thread, in the folder, with its output in a log and `input()` raising an error (the GUI gives all
  the arguments, so a prompt is a bug).
- **Consequences**: no `Table`, figures, aPMV setpoints or parametric module in the GUI yet; Linux users may need
  `python3-tk`; the documentation mocks tkinter (`autodoc_mock_imports`). The tests of the window are skipped where
  tkinter cannot open one.

## 2026-11-01 — `ex_mm` reads whether the HVAC system is off from the load that the thermostat asks for

- **Status**: accepted (priority task asked by the author on 2026-11-01; the design was chosen while he could not
  answer, so he may revise it)
- **Context**: In mixed mode, the windows of a zone open only when its HVAC system is off. `ex_mm` found one heating
  and one cooling object of each zone and read their coils, which failed with several kinds of coils, with zones
  without cooling (or heating) equipment and with central systems, and needed `hvac_zone_map` when it could not find
  the zone of an object. The task asked to identify all the equipment of each zone (zone equipment, air loops, plant
  loops, baseboards, radiant systems...). The zone outputs of the air system (`Zone Air System Sensible
  Heating/Cooling Rate`) are not a state: a DOAS keeps them above 0, and they leave out the heat of the
  baseboards.
- **Decision**: read, for each zone (and the zone of each window), the load to the setpoints that its thermostat asks
  the HVAC system for (`Zone Predicted Sensible Load to Setpoint Heat Transfer Rate`, previous timestep): the HVAC
  system is off when it is 0, whatever the equipment. `vrf_mm` keeps its coils (its results do not change). No
  topology: the resolver of the zones of the HVAC objects is removed, and `hvac_zone_map` is deprecated without
  effect.
- **Consequences**: the four sample models simulate, the PTACs give the same results as with their coils, and the
  windows no longer stay open while the beams cool. Each occupied zone needs a thermostat (as with `ex_ac`). A zone
  whose thermostat has a cooling setpoint but no equipment that cools keeps its windows closed while the thermostat
  asks for cooling (HVAC mode 2 opens them only below the cooling setpoint anyway: no such timestep in the sample
  model with radiators). An HVAC system that is not available when the thermostat asks for a load counts as on.

## 2026-11-01 — The hour counters are corrected, and the percentage within the setpoints is computed from them in Python

- **Status**: accepted (priority task asked by the author on 2026-11-01; the design was chosen while he could not
  answer, so he may revise it)
- **Context**: The author asked that the hours within the setpoints (the EMS output of the comfortable hours, or
  similar) be easy to measure, to filter out the simulations below a percentage. The ACCIS had the counters
  (`Occupied Comfortable Hours_No Applicability_<zone>`, `Occupied Hours_<zone>`...), but they were wrong (see
  [[../DEVLOG.md]], 2026-11-01): the occupied comfortable hours kept their value out of the setpoints and could
  exceed the occupied hours, `CountHours_<zone>` set nothing below the heating setpoint and used the setpoints of
  the previous timestep. A percentage is a ratio of two sums, which one EnergyPlus output cannot give at every
  reporting frequency, and a reader of besos reads one output.
- **Decision**: correct the counters (all set in every timestep; `CountHours_<zone>` after `SetASTnoTol`, so
  `ACSTnoTol`/`AHSTnoTol` are results of each zone, not state) and compute the percentages in Python from the
  sums of the two existing counters, in `accim.data.postprocessing.setpoint_hours` (`hours_within_setpoints`,
  `filter_by_hours_within_setpoints`), for the CSV files of `run_ep` and for any table with one row per
  simulation (the results of the parametric module with readers of the counters, named after them). The building
  is the ratio of the sums over its zones. No new EMS output: a per-timestep status (1, 0, -1 as the comfort
  status of EnergyPlus) would work as one reader, but its hourly averages mix the occupied and unoccupied
  timesteps of an hour. For an optimisation, the sum of `Occupied Discomfortable Hours_No Applicability_<zone>`
  is the constraint (the occupied hours of a model and weather file do not change between evaluations).
- **Consequences**: the counters of the output IDFs change (the golden master was written again), not the setpoints
  or the other results; the models of earlier versions keep their counters. `make_averages` no longer stops
  EnergyPlus (`b02`, `b17`). The block and building totals of `Table` only add up the outputs of the zones. The
  aPMV setpoints (`accim.sim.apmv`) have their own counters, without occupied comfortable hours, which the module
  does not read.

## 2026-11-01 — Each zone has its arguments in `SetInputData_<zone>`, run by `RunACCIS_<zone>` with the shared programs

- **Status**: accepted (asked by the author on 2026-11-01, who chose the options of the API, the outputs and the
  models of earlier versions)
- **Context**: The author asked that the user can give the arguments of the ACCIS (comfort standard, category,
  comfort mode, HVAC mode...) for each zone or space, and that all the inputs be in one program (`SetInputData`)
  per zone. The ACCIS had one value of each argument for the whole model, in five programs (`SetInputData`,
  `SetVOFinputData`, `ApplyCAT`, `SetAppLimits`, `SetAST`), and all its programs calculated one set of setpoints
  with global variables; the subprograms of the setpoints have about 3000 lines.
- **Decision**: each occupied zone (each target of `resolve_targets`) has all its inputs in
  `SetInputData_<zone>` (`accim/sim/ems/inputs.py`, `INPUT_VARIABLES`, with the names of 0.x for the EMS
  variables until the review of the names), and a program `RunACCIS_<zone>`, the only one with a calling manager
  besides `SetGeoVar<zone>` and `InitASTvariables`, runs it and then the shared programs, in the order in which
  they ran for all the zones (so the subprograms are not repeated for each zone). The variables that the shared
  programs read before setting them in a timestep (`ACST`, `AHST`, `ACSTnoTol`, `AHSTnoTol`, `ComfTemp`,
  `CoolingSeason`) are restored and stored for each zone, and initialised at each new environment (the setpoints
  as Null, so that a zone without setpoints still stops EnergyPlus). The user gives `zone_arguments={zone:
  {argument: value}}` to `AddAccis` (the same in all the output IDFs, checked before writing them) and to
  `modify_accis` (`None` keeps the values of each zone); the zones by name, key of the aPMV setpoints or EMS name.
  The setpoints of each zone are new outputs, and those of the whole model keep their names (the values of the
  last zone). The models of earlier versions keep their programs, which `modify_accis` and the parametric module
  still set, without arguments per zone.
- **Consequences**: the EMS objects of the output IDFs change (the golden master was written again); with the
  same arguments in all the zones, the results do not change (simulations of up to four output IDFs of each
  configuration of the golden master, compared output by output, and the two backends); with different
  arguments, the setpoints of each zone equal those of a model whose zones all have its arguments. The EMS
  runs the shared programs once per zone. `get_accim_args` returns one dictionary per zone. Not done: per-zone
  parameters in `accim.parametric_and_optimisation` (its parameters set all the zones) and per-zone setpoints in
  `Table`. The program order of 0.x is kept, including its quirks (`CountHours_<zone>` reads the setpoints of the
  previous timestep; see [[../TODO.md]]); later the same day, the decision above moved `CountHours_<zone>` after
  `SetASTnoTol`, so `ACSTnoTol` and `AHSTnoTol` are no longer restored.

## 2026-10-31 — Two parts of the integrity block of `review/refactor-sim-v1-20261024` are adapted, the rest dropped

- **Status**: accepted (the recommendation of [[questions.md]], chosen by the author on 2026-10-31)
- **Context**: That branch holds a block of versioned checkpoints with the identity of each evaluation, owned run
  folders and locks, the cleanup of owned paths only and a Pareto status with constraints, written against 0.8.2
  ([[branch-reviews.md]], section 1.3). Rebuilding it on the `main.py` of `v1.0.0` would rewrite a large part of
  it and reject the existing checkpoints. Two of its problems were real in `v1.0.0`: the Pareto status (and the
  cleanup of `keep_sim_files='non-dominated'`) ignored the constraints, and a resumed parametric run identified
  its simulations by the names of the IDF and the EPW and the parameters only.
- **Decision**: adapt those two parts, without changing how the module is used: a constraint-first dominance, as
  platypus (`accim/parametric_and_optimisation/_pareto.py`), in `_annotate_pareto_status` and in the cleanup of
  the workers; and the content of the IDF (its objects) and of the EPW, and the names of the outputs, in the
  signatures of the parametric tasks (`_content_digest`, `_build_parametric_task_signature`). Drop the rest
  (versioned checkpoint files, owned folders and locks, the patches, the benchmarks, the documentation page):
  `WorkspaceArtifactCleaner` already deletes only what appears after its snapshot.
- **Consequences**: the Pareto front of the optimisations with constraints changes (the evaluations that do not
  meet them no longer dominate those that do), and the evaluations without finite values are not pareto-optimal.
  A resumed run simulates again the tasks whose files or outputs changed, and those of the checkpoints written
  before (0.x included), without any migration. The branch was deleted on 2026-10-31, when the author confirmed.

## 2026-10-31 — The comfort objective independent of the control comes from the adaptive comfort status of EnergyPlus

- **Status**: accepted (the recommendation of [[questions.md]], chosen by the author on 2026-10-31)
- **Context**: The tag `archive/feat-comfort-metrics-experiment-api` computes comfort metrics with EMS programs,
  independent of the control ([[branch-reviews.md]], section 2). The comfort hours of accim follow the comfort
  model that accim controls, so an optimisation that changes it (the custom model of WF4, the aPMV setpoints of
  WF5) measures each evaluation against a different model; WF4 and WF5 minimise the mean operative temperature
  instead. EnergyPlus already computes, for each `People` object of the models of accim (which always get the
  adaptive models of ASHRAE 55 and CEN 15251), whether the zone is within their ranges: 1, 0, or -1 when it is
  empty or the running mean is out of range (`ThermalComfort.cc`).
- **Decision**: no EMS module. Two reducers in `objectives.py`: `hours_outside_comfort` (the occupied hours outside
  the range, from hourly values) and `fraction_outside_comfort` (their fraction of the occupied time, from hourly
  or timestep values), with an example in the overview page of the parametric module. The PMV indicators of
  `compute_hourly_indicators` wait for a study that needs them (they need the Fanger model in the `People`
  objects, which accim only adds with `temp_ctrl='pmv'`).
- **Consequences**: an optimisation can minimise the hours outside CEN 15251 or ASHRAE 55, a fixed reference,
  with no new EMS programs, outputs in the IDFs or work for the Python API backend. The objective is per zone
  (`People` object), and the hours of the design days count when the model simulates its sizing periods, as
  with the other readers. WF4 and WF5 keep their objectives. The tag was deleted on 2026-10-31, when the author
  confirmed (`checked_sum_results` and `openpyxl` are already in `v1.0.0`).

## 2026-10-31 — The fixes and tests of the branch reviews go to `v1.0.0`, before the release

- **Status**: accepted (option (a), chosen by the author on 2026-10-31)
- **Context**: [[branch-reviews.md]] marked as `port` or `adapt` six fixes and five groups of tests of
  `refactor/sim-v1`, and the strict reducer and the `openpyxl` dependency of the tag
  `archive/feat-comfort-metrics-experiment-api`, in four PRs; PR 1 (five small fixes) was already in the working
  tree of `v1.0.0`. The options were: (a) everything on `v1.0.0` before the release; (b) PR 1 on `v1.0.0`, the rest
  on `master` after the merge.
- **Decision**: (a). On 2026-10-31, `v1.0.0` got PR 2 (`objectives.checked_sum_results` and `openpyxl` in
  `install_requires`), PR 3 (the tests of sim-v1 adapted to `tests/core`, with the repair of
  `Table.wrangled_table(reshaping='pivot')`) and PR 4 (the golden master of the output IDFs in
  `tests/core/golden_master`, which also repeats the comparison with 0.8.2, and `tools/compare_backends.py`).
- **Consequences**: `v1.0.0` holds everything that the reviews proposed to keep from `refactor/sim-v1` and the
  comfort-metrics tag. After the decisions on the other two questions (above), the four refs of the reviews were
  deleted on 2026-10-31, when the author confirmed (see [[branch-reviews.md]]).

## 2026-10-31 — accim removes the ideal loads systems of the input model when it adds its VRF systems

- **Status**: accepted (chosen by the author on 2026-10-31)
- **Context**: `hvac/vrf.add_vrf_objects` replaces the zone equipment lists and connections of the model with
  those of the VRF systems, but kept its `ZoneHVAC:IdealLoadsAirSystem` objects (with their availability set to
  'On' by `set_ideal_loads_availability_on`), so they were left unconnected and EnergyPlus reported one severe
  error for each of them in every run ("Orphaned ZoneHVAC object found"), as in 0.x ([[branch-reviews.md]],
  section 3). The options were: remove them; keep the behaviour of 0.x.
- **Decision**: remove them. `add_vrf_objects` removes all the `ZoneHVAC:IdealLoadsAirSystem` objects of the model,
  with `AddAccis`, `add_accis_to_idf` (and so `accim.parametric_and_optimisation`) and
  `accim.sim.apmv.add_vrf_system`; `set_ideal_loads_availability_on` (new in 1.0.0, with no alias) was removed. The
  existing HVAC systems (`ex_ac`, `ex_mm`) keep them.
- **Consequences**: the output IDFs with the VRF systems lose these objects (17 of the 29 configurations of the
  golden master; nothing else changes), and their results do not change: with the sample model, Seville and a whole
  year, the hourly CSV files of `AddAccis` (`vrf_ac`) and of the aPMV setpoints are identical, without the 2 severe
  errors.

## 2026-10-31 — The setpoints of comfort standard 6 with `ComfMod` 2 stay as in 0.x until they are checked

- **Status**: superseded on 2026-11-03 by "The heating setpoints of CHN Yang with `ComfMod` 2 are those of the source
  of the standard" (above): the author checked them and corrected them
- **Context**: In `accim/sim/ems/setpoint_lines.py`, key `(6, 2)` (CHN Yang), the heating setpoint uses, within the
  applicability limits, the formula of the cooling setpoint (`PMOT*0.30+25.9` with `CAT` 80, `+23.6` with 90), as
  in 0.x (question of the review of 2026-10-24, [[branch-reviews.md]], section 1.4). With `ComfMod` 3, the heating
  setpoint is `PMOT*0.32+14.88` (`CAT` 80) or `PMOT*0.31+17.14` (`CAT` 90). The applicability limits of this
  standard are -7 to 30 °C and its category offsets are 0, so both setpoints are almost always equal: for
  instance, 30.4 °C for a PMOT of 15 °C with `CAT` 80, against a heating setpoint of 19.7 °C with `ComfMod` 3.
- **Decision**: keep them as they are for now, and check them later against the source of the standard.
- **Consequences**: the output IDFs and results of this combination do not change. If the check finds an error,
  its fix changes them (in the golden master, the configuration `b01`), with a CHANGELOG entry.

## 2026-10-31 — The air-conditioned parametric notebooks close the windows of the sample model

- **Status**: accepted (option (a), chosen by the author on 2026-10-31)
- **Context**: The sample model of the parametric notebooks (`OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520*.idf`)
  has two `ZoneVentilation:WindandStackOpenArea` objects (2 m2 per zone) with the schedule `Always On Discrete
  hvac_library`, without temperature limits. accim only controls them with the mixed-mode script types (`vrf_mm`,
  as `AddAccis` since 0.7.8). WF1 and WF4 used `ScriptType="vrf_ac"` with `HVACmode` 0, and 03, WF3 and WF5 apply
  aPMV setpoints, which only control the HVAC system, so these "fully air-conditioned" examples heated and cooled
  with the windows open all year (also with 0.8.2): heating 4-53 kWh/m2 (WF1), 2-51 (WF4), 52-71 (03), against
  0-1 in WF2 in air conditioning, with the windows closed. Found by the review of the texts of the notebooks run
  again with 1.0.0. The options were: (a) WF1 and WF4 with `ScriptType="vrf_mm"` and `HVACmode` 0, so that accim
  closes the windows, and the aPMV notebooks closing the ventilation objects; (b) a variant of the sample model
  without natural ventilation; (c) keep them and explain it in their texts.
- **Decision**: (a). WF1 and WF4 add the VRF system with `ScriptType="vrf_mm"`, and `modify_HVACmode(building, 0)`
  keeps the windows closed (with `HVACmode` 0, `SetWindowOperation_<window>` sets their opening factor to 0). 03,
  WF3 and WF5 set the `Opening_Area_Fraction_Schedule_Name` of the `ZoneVentilation:WindandStackOpenArea` objects to
  the `Always Off Discrete` schedule of the model. accim itself does not change: with `vrf_ac` and `ex_ac` it
  leaves the natural ventilation of the model as it is, as `AddAccis` always has; Detailed use and the overview
  page of the parametric module now say so, with these two ways of closing the windows.
- **Consequences**: The five notebooks describe fully air-conditioned buildings with their windows closed, as their
  texts said. Their results change: for instance, the HVAC electricity of WF3 goes from 171-228 to 67-87 kWh/m2 and
  the heating of 03 from 52-71 to 3-13 kWh/m2, close to WF2 in air conditioning. They were run again and their
  texts checked against the new results (see [[../DEVLOG.md]]).

## 2026-10-31 — The hourly tables of the parametric module follow the calendar of EnergyPlus

- **Status**: accepted (to be confirmed by the author: it changes the daily and monthly tables, and the year of
  the hourly tables without `start_date`)
- **Context**: EnergyPlus labels each hourly or timestep value with the end of its interval (01:00 to 24:00) and
  writes no year. The hourly methods labelled the values from `'2024-01-01 01'` (the default `start_date`, and
  the year of the dates read from the CSV files), a leap year, and grouped them by the day of their label. So the
  value of 24:00 went to the next day and month (a 3-day run gave 4 daily rows), and a standard year of 8760
  hours got a 29 February, with every value from 1 March labelled one day early. Found by the regression tests
  of the post-processing (TODO P1). The options for the year were: keep 2024 and skip 29 February (labels
  that are not evenly spaced), a year chosen from the length of the series, or keep it and document it.
- **Decision**: Without `start_date` (or with the date read from the CSV files), the year is 2024 only for 8784
  hourly values, and 2023 otherwise; an explicit `start_date` keeps its year. The default of the argument is
  still `'2024-01-01 01'` (a `str` subclass, `_AutoYearStartDate`, marks it as automatic), so the signatures do
  not change. The daily and monthly aggregation moves the labels back one second before grouping when the step
  is one hour or less and the first label is not at midnight (labels at the start of each interval, and daily
  or monthly values, are grouped as they are).
- **Consequences**: Each day of the daily tables has its 24 values, and each month its hours. The hourly tables
  without `start_date` are labelled in 2023 for a standard year, so the scripts that select dates of 2024 in them
  must pass `start_date` (the tests and notebooks of the repository already do). Tests:
  `tests/parametric_and_optimisation/test_normalised_units_aggregation.py`.

## 2026-10-31 — `population_size` is the size of every generation, and the settings of the algorithms are checked first

- **Status**: accepted (to be confirmed by the author: it changes the results of 5 algorithms)
- **Context**: `run_optimisation()` documents `population_size` as the number of individuals (EnergyPlus
  simulations) of each generation, but platypus 1.4 takes the size of the generations of some algorithms from
  other options, 100 by default: `swarm_size` (OMOPSO, SMPSO) and `offspring_size` (CMAES, GeneticAlgorithm,
  EvolutionaryStrategy). It ignored `population_size` for the swarms and CMA-ES (its `Algorithm` swallows unknown
  keyword arguments) and took it only as the initial population of the other two, so these optimisations ran 100
  simulations per generation. Also, PAES (one solution, one parent) could not run, `ParticleSwarm` is abstract,
  and several algorithms need options or kinds of parameters that `run_optimisation()` did not check, so they
  failed with the errors of platypus after the first case had started (the 16-algorithm smoke test hid some
  failures: with `evaluations=2` most algorithms stopped after the initial population, so OMOPSO and
    EvolutionaryStrategy never reached their first iteration, which failed).
- **Decision**: `population_size` is also passed as `swarm_size` or `offspring_size` (`algorithm_options` can
  still give them); PAES gets no `population_size`, and PAES and EvolutionaryStrategy (one parent for each
  solution) get a mutation as their variator, instead of the crossover that besos gives every algorithm (with it,
  EvolutionaryStrategy stopped after the initial population); `_check_optimisation_algorithm()`
  raises clear errors before anything is written (`ParticleSwarm`; `epsilons` and `divisions_outer`; SPEA2 with
  fewer than k + 2 solutions; categorical parameters with OMOPSO, SMPSO and CMAES; NSGAIII with maximised
  objectives; single-objective algorithms with several objectives). The list of accepted names keeps all the
  algorithms that can run; `ParticleSwarm` gets its own error instead of disappearing silently.
- **Consequences**: The optimisations with OMOPSO, SMPSO, CMAES, GeneticAlgorithm and EvolutionaryStrategy run the
  planned number of simulations, and their results change (CHANGELOG, migration guide 9.3). The requirements are
  in the docstring of `run_optimisation()`. Tests: `test_optimisation_algorithms.py` (fast) and
  `04_test_optimization.py` (each algorithm iterates at least once with EnergyPlus).

## 2026-10-31 — The subprograms of ESP CTE and INT ISO7730 set their setpoints whatever `ComfMod` is

- **Status**: accepted (to be confirmed by the author, who was given the two options in `TODO.md`)
- **Context**: The setpoints of ESP CTE (`ComfStand` 0) and INT ISO7730 (22) do not depend on the comfort mode,
  but their subprograms (`SetAST_CS0_0`, `SetAST_CS22_0`) only set them in the branch `ComfMod == 0`. The
  output IDFs of `AddAccis` set `ComfMod` 0 for them, but the models of `accim.parametric_and_optimisation`
  keep the `ComfMod` of their baseline (3), so their plans with `ComfStand` 0 or 22 stopped EnergyPlus
  ("Variable = 'ACST' used in expression has not been initialized!" in `SetASTnoTol`), also in 0.8.2. The
  options were: (1) these subprograms set the setpoints whatever `ComfMod` is; (2) the setter of `ComfStand`
  of the parametric module sets `ComfMod` 0 for them.
- **Decision**: (1). `ems/setast.py` writes the lines of the comfort standards whose only key in
  `SETPOINT_LINES` is `(ComfStand, None)` (`depends_on_comfort_mode()`) without the branches of `ComfMod`
  (13 and 14 also have that key, as a fallback, so they keep them). The fix lives in the EMS programs, where the
  bug is: it works with any `ComfMod` of `SetInputData`, with the plans of every sampling method, with
  `modify_accis` and with the edits by hand, while (2) only covered the parametric setter. `modify_accis`
  rewrites these two subprograms in the models of earlier versions (those of `bypass_addAccis=True`), as it
  already adds `SetAST_Master` to the models of accim before 0.8.
- **Consequences**: The text of the two subprograms changes in every output IDF, not the results (golden
  master: the 426 output IDFs with ACCIS differ only in these two programs). The parametric plans with
  `ComfStand` 0 or 22 run. The plan filter of the predefined models still drops `ComfStand` 0 when the plan
  has `CAT` or `ComfMod` (see `TODO.md`). Tests: `tests/core/test_setast_static_standards.py`,
  `tests/core/test_modifyaccis_setast.py`, `08_test_accim_predef_model.py`.

## 2026-10-31 — `add_accis_to_idf` and `add_vrf_system` enable the sizing calculations of the VRF systems

- **Status**: accepted (option (b), chosen by the author)
- **Context**: The VRF systems that accim adds are autosized, and EnergyPlus cannot run them without a zone
  sizing run ("For autosizing of ZoneHVAC:TerminalUnit:VariableRefrigerantFlow ..., a zone sizing run must be
  done"). `AddAccis` (IDF files) enabled the zone, system and plant sizing calculations for every script type
  (since 0.7.8), but `add_accis_to_idf` (IDF objects, used by `accim.parametric_and_optimisation`) and
  `apmv.add_vrf_system` did not, also in 0.8.2, so the parametric module could not run the models whose zone
  sizing was off. Checked with EnergyPlus 9.6 (`SF_Detached_B`, `vrf_mm`): with the zone sizing on and a sizing
  period, the model runs; without sizing periods, EnergyPlus stops ("Sizing for Zones has been requested but
  there are no design environments specified", `CheckEnvironmentSpecifications`, only when the model has
  `Sizing:Zone`, `Sizing:System` or `Sizing:Plant` objects); the system and plant sizing only add a warning when
  there are no plant loops. The options were: (a) keep 0.8.2; (b) enable them in `add_accis_to_idf` only with
  the VRF script types; (c) enable them with every script type, as `AddAccis`.
- **Decision**: (b). `add_accis_to_idf` (with `vrf_ac` and `vrf_mm`) and `apmv.add_vrf_system` call the same
  `enable_sizing_calculations()` as `AddAccis`, so both paths build the same VRF models. With `ex_ac` and
  `ex_mm`, `add_accis_to_idf` keeps the user's sizing settings: accim adds no autosized equipment to them, and
  enabling the sizing of a model with sizing objects but no sizing periods would stop EnergyPlus. Accim does not
  add sizing periods (design conditions are a modelling choice, and weather-file days would size the systems
  differently for each EPW of a study); `enable_sizing_calculations()` warns when a model has sizing objects
  but no sizing periods.
- **Consequences**: The VRF models whose zone sizing was off now run if they have sizing periods; the models
  that already ran keep their results (golden master: only `SimulationControl` changes in the 7 in-memory VRF
  and aPMV configurations; the 20 `AddAccis` configurations and the 2 `ex_*` ones are identical). `AddAccis`
  still enables the sizing of the `ex_*` models, which may stop those without sizing periods (now with the
  warning); revisit if it is reported. Tests: `tests/core/test_sizing.py`.

## 2026-10-30 — `add_accis_to_idf` builds the same model as `AddAccis`, including the scheduled natural ventilation

- **Status**: accepted (to be confirmed by the author, since it changes results of the parametric module)
- **Context**: In accim 0.8.2, `addAccis` (files) and `accis_single_idf_funcs.addAccis` (IDF objects, used by
  `accim.parametric_and_optimisation`) were separate code paths. The scheduled natural ventilation of 0.7.8
  (mixed mode through `ZoneVentilation` objects in models without AirflowNetwork) was only implemented in the
  first one, so in the parametric module the ventilation of these models was not controlled, and its
  ventilation parameters (`VentCtrl`, `MaxTempDiffVOF`, `VSToffset`...) had no effect. accim 1.0.0 builds both
  from the same model and sequence (`AccimModel` in `accim/sim/model.py`, which finds the windows and the
  scheduled ventilation, and `accim/sim/build.py`). A comparison of the parametric classes against 0.8.2
  (session script, model of the parametric notebooks) found the difference: the IDFs of `vrf_ac` and the aPMV
  setpoints are identical, and those of `vrf_mm` differ only in the objects of the scheduled ventilation.
- **Decision**: Keep one sequence: `add_accis_to_idf` applies the scheduled natural ventilation, as `AddAccis`
  does, and the change is documented as a fix (`CHANGELOG.md`, migration guide 9.3). The sizing calculations
  were decided later ([[#2026-10-31 — `add_accis_to_idf` and `add_vrf_system` enable the sizing calculations of the VRF systems|the decision of 2026-10-31]]).
- **Consequences**: The parametric and optimisation studies of mixed-mode models with `ZoneVentilation`
  objects give different results than with 0.8.2, including those of the parametric example notebooks, whose
  published pages were computed with 0.8.2 ([[../TODO.md]]). Reverting would need an option of `AccimModel`
  that skips the scheduled ventilation for IDF objects.

## 2026-10-30 — PEP 8 names with deprecated aliases for accim 0.x

- **Status**: accepted; the mechanical translation of the names and the parametric module keeping its names are
  superseded by [[#2026-11-02 — The arguments and parameters have descriptive names, the same in the whole package]]
- **Context**: The author asked to refactor accim to the conventions of Python, keeping the usage similar, and
  allowed renaming the classes and arguments that break the rules; later, the usage of
  `accim.parametric_and_optimisation` had to stay the same. Many scripts, notebooks and papers use the names
  of 0.x (`addAccis`, `ScriptType`, `ComfStand`, `runEp`...).
- **Decision**: In accim 1.0.0 the public names follow PEP 8 with a mechanical translation (`addAccis` ->
  `AddAccis`, `ScriptType` -> `script_type`, `runEp` -> `run_ep`, `apmv_setpoints` -> `apmv`...), and every
  old name stays as a deprecated alias (`accim/_deprecation.py`, `LEGACY_ARGUMENT_NAMES`) that warns with
  `DeprecationWarning`. The classes used as functions (`rename_epw_files`, `Table`) keep their names, as PEP 8
  allows. The parametric module keeps its API and only changes its internal calls. The prompts keep their
  texts.
- **Consequences**: The scripts of 0.x run unchanged (with warnings); the migration guide
  (`docs/source/9_migration_guide.md`) lists the names; the aliases are removed in a future major version
  ([[../ROADMAP.md]], R-03).

## 2026-10-30 — The Python API backend runs the EMS programs of the IDF in Python

- **Status**: accepted
- **Context**: The author wanted to use accim through the Python API of EnergyPlus in parallel to eppy and the
  EMS. The control logic of accim lives in the EMS programs that it writes in the output IDFs (SetAST,
  ApplyAST, SetWindowOperation...). Writing that logic again in Python would give two implementations to keep
  in sync, with results that could differ.
- **Decision**: The backend reads the EMS objects of the IDF, runs EnergyPlus through `pyenergyplus` without
  the programs, calling managers and actuators, and runs the programs in the callbacks of the API with an Erl
  interpreter (`accim/sim/ems/erl.py`) that follows `RuntimeLanguageProcessor.cc` and `EMSManager.cc`
  (operator grouping, Null and uninitialised values, errors while sizing, resets at each new environment,
  actuators released when Null). Sensors and internal variables are read from the Erl variables of
  EnergyPlus, so it requires EnergyPlus 24.2 or later (`getEMSGlobalVariableHandle`). `run_ep(backend='ems')`
  stays the default.
- **Consequences**: One source of truth (the IDF), identical results (checked against the EMS backend in the
  tests), and Python hooks that can read and change the variables of the programs. The interpreter must follow
  the changes of the EMS in new EnergyPlus versions (the tests compare both backends). Some EMS features are not
  supported and raise an error ([[../ROADMAP.md]], R-05).

## 2026-10-15 — Hourly results of the parametric notebooks only where they are analysed

- **Status**: accepted
- **Context**: The notebooks of `parametric_and_optimisation_examples` are
  run by users on their own computers, and hourly outputs are what makes each
  simulation heavy (about 1 MB of `eplusout.csv` per annual simulation with
  the minimal outputs). The author asked for simulations as light as
  possible, with annual results.
- **Decision**: wf1 is the only workflow that keeps the hourly results of
  every evaluation (the ASHRAE 55 screening needs them). wf2 and wf4 run in
  annual mode, without simulation folders, and then simulate again, with
  hourly outputs, only the configurations or solutions analysed hourly (wf2:
  the 4 EN 16798-1 Cat. III configurations; wf4: the non-dominated
  solutions). All of them use 2 timesteps per hour, the full-year run
  period, no design-day environments and only the outputs they read.
- **Consequences**: The screening of wf4 covers the non-dominated solutions,
  not every evaluation as in the paper. The re-simulations reproduce the
  annual results exactly, and each one is checked in the notebook. Annual
  results differ slightly from runs with the 6 timesteps of the model.


## 2026-10-15 — Ship sample files as the separate distribution `accim-samples`

- **Status**: accepted
- **Context**: `accim/sample_files` (notebooks, IDFs, EPWs, CSVs) made the
  accim wheel about 36 MB and will grow as more notebooks are added. pip
  extras cannot add files to a distribution, only extra dependencies. No
  runtime code of accim reads `sample_files`.
- **Decision**: The core `accim` distribution excludes `accim/sample_files`
  (`setup.py` + `prune` in `MANIFEST.in`). The files are published as
  `accim-samples` (built by `packaging/build_samples_dist.py`), which only
  contains `accim/sample_files/**` and installs into the same folder. The
  extra `accim[samples]` requires `accim-samples==<accim version>`, and
  `accim-samples` requires `accim==<same version>`. Only the wheel is built
  by default to reduce the size uploaded to PyPI.
- **Consequences**: Every accim release must upload both distributions with
  the same version (`dist_build_package.bat` builds both into `dist/`).
  `accim-samples` must never contain `accim/__init__.py`. PyPI's default
  per-file limit is 100 MB (the build script warns); a larger limit must be
  requested if the samples wheel grows beyond it. Installs from git only get
  the library. See [[../README.md]] and
  [[../docs/source/2_installation.md]] for user instructions.


## 2026-09-13 — Treat `AGENTS_v2.md` as the current `AGENTS.md`

- **Status**: accepted
- **Context**: The repository does not have a literal `AGENTS.md` file, but
  has [[../AGENTS_v2.md|AGENTS_v2.md]] ("AGENTS.md (v2)"), which defines
  agent design/operation guidelines for this project.
- **Decision**: [[../.github/copilot-instructions.md|Copilot instructions]]
  point to `AGENTS_v2.md` as the file to consult when instructions say
  "`AGENTS.md`, if it exists".
- **Consequences**: If a literal `AGENTS.md` is added later, update the
  Copilot instructions to prefer it (or merge both) instead of
  `AGENTS_v2.md`.

## 2026-09-13 — `notes/work-log.md` complements, not replaces, existing tracking files

- **Status**: accepted
- **Context**: The repository already separates work tracking across
  `CHANGELOG.md`, `DEVLOG.md`, `TODO.md` and `ROADMAP.md` (see
  [[../DEVLOG.md#Tracking files|Tracking files]]).
- **Decision**: `notes/work-log.md` is a lightweight, session-scoped log for
  fast context recovery (by humans or an AI assistant). It must not duplicate
  or replace the existing four tracking files; durable outcomes are still
  promoted to them as before.
- **Consequences**: Two logs exist with different scopes. Copilot
  instructions clarify which one to read for which purpose.

## 2026-09-13 — No documentation is duplicated or rewritten for the vault

- **Status**: accepted
- **Context**: The repository already has substantial documentation
  (`README.md`, `CHANGELOG.md`, `DEVLOG.md`, `TODO.md`, `ROADMAP.md`,
  `AGENTS_v2.md`, `docs/source/`, root-level reports).
- **Decision**: [[../Home.md|Home.md]] and vault notes only link to existing
  documentation with wiki links; they never copy or restate its content.
- **Consequences**: Home.md must be revisited if canonical files are renamed
  or restructured (see [[obsidian-tutorial.md#4. What NOT to do|What NOT to
  do]]).

## 2026-09-13 — Vault content stays in English, ASCII, kebab-case

- **Status**: accepted
- **Context**: The rest of the repository's process documentation
  (`CHANGELOG.md`, `DEVLOG.md`, `TODO.md`, `ROADMAP.md`) was already
  translated to English (see `DEVLOG.md`, entry *2026-06-11*). No
  multilingual pair of README/TODO exists to mirror.
- **Decision**: All new vault notes are written in English, with ASCII,
  kebab-case file and folder names under `notes/`. `Home.md` is the single
  intentional exception (Obsidian's conventional vault-index filename).
- **Consequences**: Any future vault note should follow the same convention
  for consistency and predictable linking.

## 2026-09-13 — Use the repository root as the Obsidian vault; ignore `.obsidian/` in git

- **Status**: accepted
- **Context**: The goal is persistent documentation and working context for
  this repository, browsable with Obsidian, without introducing a separate
  vault folder that would fragment the existing file layout.
- **Decision**: The repository root is the Obsidian vault. `.obsidian/` is
  added to `.gitignore` (local UI/workspace/preferences); `Home.md` and
  `notes/` are the versionable vault content.
- **Consequences**: `sync_branch.bat`'s `git clean -fd` was updated to
  exclude `Home.md` and `notes/`, since they are not committed by default and
  would otherwise be deleted as untracked files.
