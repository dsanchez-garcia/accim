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

## 2026-11-10 — H6: the outdoor temperature of the functions of the clothing insulation, and their CSV files
- Context: the decision of A5 in v04 §6 is `clothing_insulation=callable`, written as a `Schedule:File` generated from
  the weather file with `accim.sim.preview.outdoor_metrics` (the TODO says `callable(rmot) -> clo`; v03 says "a
  callable that maps an outdoor-temperature pandas Series to clo values"). Neither says which temperature, with which
  alpha, how the function is called, nor where the file goes.
- Why it matters: the clothing insulation of the occupants of each hour, and the files that the models read.
- Options considered: (i) the function receives a pandas Series with the hourly values of a column of
  `outdoor_metrics(epw)` with its defaults (α = 0.8, 30 days), `clothing_outdoor_metric='RMOT'` by default (the
  running mean of EN 16798-1, B.1), and must return one value per hour (no element-wise fallback, so that a function
  of one value fails with a message instead of being called 8760 times); `epw` required; the values must be at least
  0 clo, with the warnings of the parametric parameter `clothing_insulation` (0–2 clo, ISO 7730; 1.5 clo, ASHRAE 55);
  the CSV file in the folder of the model, named `Sch_Clo_<people>_<weather file>_<8 characters of the SHA-1 of the
  values>.csv`, so that other values (or other models in the folder) do not replace the file that a model reads; the
  GUI takes numbers only (implemented); (ii) the whole DataFrame of `outdoor_metrics` as the argument; (iii) alpha and
  days of the metric as arguments.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`accim.sim.apmv.clothing_insulation_values`).

## 2026-11-10 — H5: the schema of the key regimes of the YAML files of the comfort standards
- Context: decision 4 of v04 §6 gives the key `regimes:` "with the same schema as CustomRegime of B2 (slope, intercept,
  offsets, limits, condition, outdoor_metric optional)", and says that a scalar `comfort_temperature` is a single regime
  'always'. It does not say whether the offsets are required, which conditions a comfort standard can have, or what
  applies when no condition holds.
- Why it matters: the custom model falls back on its scalar arguments when no regime holds; a comfort standard has no
  such arguments (its zones have those of the custom model, which are not its coefficients).
- Options considered: (i) the eight coefficients required, as in `CustomRegime` (no defaults); `condition`,
  `outdoor_metric`, `alpha` and `days` optional; the last regime must be 'always'; the conditions 'hvac_off' and
  'hvac_on' rejected (they read the HVAC system of the model in mixed mode, not the comfort model, and would make a
  comfort standard depend on the script type) (implemented); (ii) offsets 0 by default; (iii) allow every condition and
  check the mixed mode when the output IDFs are written.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`accim.sim.standards.definition_from_mapping` and
  `ComfortStandardDefinition`).

## 2026-11-10 — H5: the EMS code of a comfort standard with regimes
- Context: decision 4 of v04 §6 does not say how the EMS selects the regime of a comfort standard.
- Why it matters: the branches of a registered comfort standard had its numbers written in them; with regimes, they
  change in each timestep.
- Options considered: (i) the code of the custom model: the branches read its inputs (`Tout_metric*m+n`,
  `CustAST_ACSTaul`..., the offsets of each category plus `CustAST_ACSToffset` and `CustAST_AHSToffset`), the zones get
  the program `SelectCustomRegime_<zone>` with the regimes of the comfort standard, and the outdoor metric is always
  `Tout_metric`, so the model has the EMS code of the outdoor metric also with 'pmot' and 'rmot' (implemented; a
  comfort standard with one regime 'always' without its own metric keeps the code of before, numbers in the branches);
  (ii) a chain of branches per regime in each program of the ACCIS; (iii) native PMOT/RMOT in the conditions when no
  regime has its own metric. Also: the zones get the regimes of their comfort standard whatever `custom_regimes` (that
  of the custom model), and lose them when `modify_accis` or the parameter `comfort_standard` gives them another comfort
  standard (`accim.sim.ems.custom_regimes.set_standard_regimes`); `modify_custom_regime` of the parametric module
  changes those of the custom model only.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`accim.sim.ems.standard_lines.uses_regimes`).

## 2026-11-10 — H5: the outdoor metric of a regime in the outputs, and the programs kept
- Context: decision 1 of v04 §6 (an outdoor metric per regime) proposes "a variable Tout_metric_<k> per metric" copied to
  `Tout_metric` by `SelectCustomRegime_<zone>`. `Tout_metric_<zone>` was already the EMS output of the outdoor metric of
  each zone (B1).
- Why it matters: the names, what `Tout_metric_<zone>` reports, and whether the programs of the outdoor metric, which
  begin with the values of the weather file, are written again when `modify_accis` changes other arguments.
- Options considered: (i) one variable per regime with its own metric, `ToutRegime_<regime>_<zone>` (and
  `RMOTr_<regime>_<zone>` for its own alpha), so that `Tout_metric_<zone>` keeps its name; after the chain of the
  regimes, `Tout_metric_<zone>` is the outdoor metric of the regime of the timestep; the programs are kept when they
  already calculate the outdoor metrics of the regimes of each zone, and written again otherwise (beginning with PMOT
  without `epw`, with a warning); a zone that leaves the custom model loses its regimes when one has its own outdoor
  metric (it would replace the `Tout_metric` that other comfort standards read), and keeps them otherwise, as before
  (implemented); (ii) one variable per distinct metric (`Tout_metric_<k>`), which would clash with the outputs of B1.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`accim.sim.ems.outdoor_metric.zone_program_lines`).

## 2026-11-10 — H3: the building type of long_term_range in categories III and IV
- Context: the decision of C2-1 (v04 §3.3, task H3) is `long_term_range=('en16798', category)`, with the constant
  limits of EN 16798-1:2019, Table B.2 (`accim.constants.EN16798_TABLE_B2`), whose minimum for heating differs between
  the residential and the office buildings in categories III (18.0 and 19.0 °C) and IV (16.0 and 18.0 °C).
- Why it matters: with `('en16798', 3)`, the lower limit is not defined by the category alone.
- Options considered: (i) `('en16798', category)` for categories I and II, whose limits are the same for both types,
  and `('en16798', category, building_type)` for any category, with a `ValueError` that lists both limits when the type
  is missing in categories III and IV (implemented: no limit is chosen for the user); (ii) the residential limits by
  default; (iii) the office limits by default.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`accim.sim.ems.long_term_discomfort.long_term_limits`).

## 2026-11-10 — H3: the range of Method C on the scale of the PMV, and its output
- Context: decision 5 of v04 §6 asks for Method C in the models of `pmv_index` "with the limits pmv_heating_setpoint/
  pmv_cooling_setpoint without the tolerance and the PMV of the zone that the EMS already measures", wf =
  PPD(PMV)/PPD(PMV_limit), and a counter `PpdWeightedHours_<zone>`. With the aPMV and the ePMV, those setpoints are on
  the scale of the index, not of the PMV.
- Why it matters: the PPD of formula (5) of ISO 7730:2025 is that of the PMV; comparing the PMV with setpoints of the
  aPMV (or the PPD of an aPMV) mixes scales.
- Options considered: (i) the limits converted to the scale of the PMV with the inverse of the index, as the thermostats
  get their PMV setpoints (aPMV/(1 − λ·aPMV) with the λ of the timestep, or of each side with
  `adaptive_coefficient_by='pmv_sign'`; ePMV/e on the side where e applies), so that the PMV is outside the range when
  the index is outside the setpoints (implemented; with the PMV setpoints, the setpoints themselves); (ii) the index of
  the zone against its setpoints, with the PPD of the index (not a PPD of ISO 7730). Also: one output per zone with both
  periods added up, `PPD Weighted Hours_<zone>` (the decision names one counter; `ppd_weighted_hours` of D1 gives each
  period after the simulations), without a total of the building (the outputs of the setpoints based on the PMV have
  none; the parametric module takes one objective per zone); the PMV of the previous timestep, as the hour counters of
  the index; and, in the parametric module, `report_long_term_discomfort=True` with 'apmv setpoints' and 'epmv
  setpoints' adds Method C (before, it did nothing with them) instead of a new argument of its classes.
- Owner: the author.
- Status: open; option (i), one output per zone without the building and the parametric argument implemented
  provisionally (`accim.sim.pmv_index.ppd_weighted_hours_lines`).

## 2026-11-10 — H2: where the CSV file of T0 of te_ref_nl is written
- Context: verdict #8 (task H2) asks for "the daily (Tmax+Tmin)/2 of the current day from the EPW as a Schedule:File
  read by a Schedule Value sensor"; the Schedule:File object needs a CSV file and its path.
- Why it matters: the output IDFs must find the file when they are simulated (by `run_ep`, by the parametric module
  in temporary folders, or after they are moved).
- Options considered: (i) the folder of the model (that of its file, or the current folder of AddAccis, where it
  writes the output IDFs), with the absolute path in the object (implemented: the Input Output Reference recommends a
  full path; EnergyPlus 25.1 read a path of 139 characters, although the reference says 100 at most); (ii) a relative
  name (EnergyPlus 25.1 found it next to the IDF), which breaks when the IDF is simulated elsewhere; (iii) the folder
  of the weather file, which can be a shared library or the repository.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`accim.sim.schedule_files`).

## 2026-11-10 — H2: which models get the Schedule:File of T0
- Context: the programs of the outdoor metric of a model have the branch of every metric, and the parametric module
  changes the metric of the zones without the weather file (`param_accis.modify_CustAST_metric`).
- Why it matters: a model made with another metric and `epw` has no schedule; if a sample gives its zones
  `te_ref_nl`, T0 cannot be that of the day.
- Options considered: (i) the schedule only when a zone has `te_ref_nl` and the weather file is given, and programs
  that begin with the values of a weather file but do not read the sensor are written again, beginning with PMOT, with
  the warnings (implemented: the output IDFs of the other metrics do not get a schedule and a CSV file); (ii) the
  schedule in every model with the outdoor metric and the weather file.
- Owner: the author.
- Status: open; option (i) implemented provisionally.

## 2026-11-10 — F3: the SET of the indicators of the causal band
- Context: the proposal of block F (§4 F3) asks for the hours within the causal band of every model; the SET can be
  that of the Pierce model of EnergyPlus (any model, with the outputs of `add_thermal_comfort_outputs`) or that of
  pythermalcomfort of the hook of comfort standard 24 (`SET_<zone>`, only in its simulations).
- Why it matters: the SET of the hook is 0.08–0.155 K below that of EnergyPlus on average (E-F1, F1), so the hours of
  the band of a simulation of comfort standard 24 differ slightly between both.
- Options considered: (i) the SET of EnergyPlus for every simulation (implemented: the same measure for every model;
  the hook still reports its own hours, `HoursInCausalBand_<zone>`); (ii) the SET of the hook where it exists.
- Owner: the author.
- Status: open; option (i) implemented provisionally.

## 2026-11-10 — F3: the definition of the overcooling
- Context: the proposal (§4 F3, a design decision) counts the "occupied hours with the operative temperature below the
  reference heating setpoint or, following Parkinson 2021, below 22 °C in the cooling season", without fixing the
  season of the first variant nor the reference setpoint.
- Why it matters: in the heating season, the hours below a heating setpoint are underheating, not overcooling.
- Options considered: (i) both variants in the cooling season of the ACCIS (from `cooling_season_start` to the day
  before `cooling_season_end`, 121 and 274 by default, by the date of each row), with one threshold: 22 °C by default,
  or the reference heating setpoint given as `overcooling_temperature` (implemented); (ii) the first variant in all
  the occupied hours; (iii) the hours of the cooling season defined by the operation of the cooling system.
- Owner: the author.
- Status: open; option (i) implemented provisionally.

## 2026-11-10 — F3: T_rm_in and the band of Tn_exp
- Context: Tn_exp = 1.06 + 0.951·T_rm_in (Parkinson et al., 2020, Fig. 6, with T_rm_in instead of the mean indoor
  temperature of the building, Tin), and the hours with abs(To − Tn_exp) > 2.5 K, a threshold that the proposal marks
  as inferred.
- Why it matters: the simulations with the limiter of the drift have their own T_rm_in (the EMS, with the operative
  temperature of the previous timestep); the 2.5 K are not of a published source.
- Options considered: T_rm_in (i) calculated from the rows of the table for every simulation, with the definition and
  the start of the limiter (implemented: the same measure for every model), or (ii) the output of the limiter where it
  exists; the band (i) 2.5 K by default, as the proposal (implemented, documented as inferred, an argument), or (ii)
  no default.
- Owner: the author.
- Status: open; options (i) implemented provisionally; the coefficients of the air-conditioned buildings (AC) by
  default, as the proposal.

## 2026-11-10 — F3: the static reference of case (i) of the validation study
- Context: the design of the study (§4 F3) has the case "(i) referencia estática PMV (24–26 / 20–22 °C)".
- Why it matters: accim has the PMV setpoints of `apply_pmv_setpoints` (category II: −0.5 and 0.5), the static
  setpoints of comfort mode 0 of the comfort standards (those of ISO 7730 of categories 80 and 90 are 25 and 27 °C or
  24 and 26 °C for cooling, and 19 and 22 °C or 20 and 23 °C for heating), and fixed thermostats.
- Options considered: one of them, or fixed setpoints of 24–26 °C and 20–22 °C (which accim would set with the static
  setpoints of a comfort standard defined by its data, section 4.2.5).
- Owner: the author.
- Status: open; section 4.7.6 of the detailed use lists the first two; no simulation run (`TODO.md`).

## 2026-11-10 — F2: the setpoint "applied the previous day" of the rate
- Context: decision 6 of block F: with `drift_mode='rate'`, |setpoint(d) − setpoint_applied(d − 1)| ≤ `max_drift_rate`
  and "the state is the applied setpoint of the previous day". The setpoints of the ACCIS change in each timestep (the
  first timestep of each day reads the running mean of the day before, and those of the hooks follow the humidity
  and the mean radiant temperature), so "the setpoint of the previous day" needs a definition.
- Why it matters: it sets the reference of the limit of each day.
- Options considered: (i) the setpoint applied by the limiter in the last timestep of the previous day (implemented;
  for the adaptive setpoints, that of the whole day); (ii) the mean of the setpoints applied in the occupied
  timesteps of the previous day; (iii) that of its last occupied timestep.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`DriftLastAHST_<zone>` → `DriftRefAHST_<zone>` at the change of
  DayOfYear), heating and cooling each one.

## 2026-11-10 — F2: the days without occupied hours in the running mean T_rm_in
- Context: T_rm_in(d) = (1 − alpha_indoor)·T_occ_mean(d − 1) + alpha_indoor·T_rm_in(d − 1), with T_occ_mean the mean
  operative temperature of the occupied hours; a day without occupants (a weekend) has no T_occ_mean.
- Why it matters: with offices, two days a week.
- Options considered: (i) T_rm_in does not change after a day without occupied hours (implemented: the occupants were
  not exposed); (ii) the mean of all the hours of that day; (iii) the decay of T_rm_in towards 0 (not meaningful).
- Owner: the author.
- Status: open; option (i) implemented provisionally.

## 2026-11-10 — F2: the parameter drift_mode of the parametric module and the limiter off
- Context: the parametric module takes numbers as options (as `custom_outdoor_metric`, which takes the codes of the
  metrics), and a plan may combine the limiter with its absence.
- Why it matters: `modify_accis` cannot remove the limiter (`None` keeps the arguments, as the minimum and maximum of
  B5), so a sample without it must turn it off in a model that has it.
- Options considered: (i) the codes 0 (none), 1 ('rate') and 2 ('window'), also their names; 0 sets `DriftMode = 0`
  in the zones that have the limiter (whose program then changes nothing) and does nothing in a model without it
  (implemented); (ii) the names only, without an option of none.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`param_accis.modify_DriftMode`).

## 2026-11-10 — F1: the numbers of the comfort modes of comfort standard 24
- Context: the decision of the author names the comfort modes of comfort standard 24 'SET band' and 'SET neutral
  +/- offset' without numbers; the catalogue of accim (`accim.sim.standards.ComfortStandard.comfort_modes`) numbers
  them, and 0 means static setpoints in the other comfort standards.
- Why it matters: the number is part of the names of the output IDFs of the other comfort standards (`CM_`), and
  the parametric module numbers the comfort modes.
- Options considered: (i) 1 = 'SET band', 2 = 'SET neutral +/- offset' (implemented); (ii) 0 and 1; (iii) the names
  only.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`SUN2026_COMFORT_MODES`; the functions take the number or the
  name): 0 keeps its meaning of static setpoints.

## 2026-11-10 — F1: the "CustAST_ACSTaul/all and AHSTaul/all limits" of the prompt of F1
- Context: scope 2 of the prompt of F1 asks to apply "the existing CustAST_ACSTaul/all and AHSTaul/all limits and the
  B5 minimum/maximum" to the inverted setpoints. In the ACCIS, `ACSTaul`, `ACSTall`, `AHSTaul` and `AHSTall` (and the
  `CustAST_*` inputs of the custom model) are the applicability limits of the outdoor metric (RMOT, PMOT or
  `Tout_metric`), not limits of the setpoints (the same reading as the question of verdict 13 above).
- Why it matters: applied to the setpoints of the SET, they would bound an indoor temperature with limits of the
  outdoor temperature (10 and 30 °C for INT EN16798).
- Options considered: (i) the setpoints of the SET are bounded by the range of the bisection (10–40 °C) and by the
  minimum and maximum of B5 in the EMS after the hook, and the applicability limits of the comfort standard of the
  zone keep their role in the hour counters of the ACCIS (implemented); (ii) bound them with ACSTaul/ACSTall/AHSTaul/
  AHSTall as temperatures.
- Owner: the author.
- Status: open; option (i) implemented provisionally (it changes nothing in the ACCIS).

## 2026-11-10 — F1: the clothing insulation of the dynamic clothing model in the hook
- Context: the hook of comfort standard 24 reads the clothing insulation of the People objects (decision 5 of block
  F, "clothing via set_clothing_method of A5"). With the method DynamicClothingModelASHRAE55, EnergyPlus calculates
  it; the documentation of EnergyPlus lists the output *Zone Thermal Comfort Clothing Value* [clo] of the People
  objects without saying when it is calculated. Measured with EnergyPlus 25.1 and the Pierce model: with the dynamic
  model it was 0.75 until 6:00 of 1 January and then 0.534, 0.639...; with the clothing insulation schedule, 0.
- Why it matters: the hook needs the clothing insulation of each timestep.
- Options considered: (i) the output of the People object (that of the previous timestep, as the other sensors of
  the zone; the hook gives no setpoints while it is 0) with the dynamic model, the schedule with
  ClothingInsulationSchedule, and one of them by the calculation method schedule with CalculationMethodSchedule
  (implemented); (ii) the equations of the dynamic model of the Engineering Reference (19.1.7) in Python.
- Owner: the author.
- Status: open; option (i) implemented provisionally (it reads what EnergyPlus calculates).

## 2026-11-10 — G5: the warning of verdict 13 compares the floor and ceiling with ACSTaul and AHSTall
- Context: verdict 13 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§5) asks for a `ValueError` if the floor of the
  heating setpoint is not lower than the ceiling of the cooling setpoint (there since B5) and a warning in the log if
  the floor exceeds `ACSTaul` or the ceiling falls below `AHSTall`, because crossed setpoints give warnings and
  meaningless results in EnergyPlus. In the ACCIS, `ACSTaul` and `AHSTall` (program `SetAppLimits`) are the upper
  applicability limit of the cooling setpoint and the lower one of the heating setpoint, limits of the outdoor metric
  (RMOT, PMOT or `Tout_metric`: 30 and 10 °C for INT EN16798), not setpoints.
- Why it matters: compared literally, an indoor setpoint limit is compared with a limit of the outdoor temperature, so
  the warning only fires with extreme values (a floor above 30 °C, a ceiling below 10 °C with INT EN16798), while the
  setpoints can cross with ordinary values (a floor of 24 °C above a cooling setpoint of 23.5 °C in winter).
- Options considered: (i) literal (implemented); (ii) compare with the extreme setpoints of the comfort model of the
  zone (the lowest cooling setpoint and the highest heating setpoint over the range of its outdoor metric, with the Erl
  interpreter of accim, which needs the comfort mode and, for some comfort standards, the weather file); (iii) a
  warning in the error file of EnergyPlus in the timesteps in which the heating setpoint is above the cooling one
  (`@WarnEP` in `ApplySetpointLimits_<zone>`, which changes the output IDFs).
- Owner: the author.
- Status: open; option (i) implemented provisionally
  (`accim.sim.ems.setpoint_limits.warn_crossed_setpoint_limits`, called by `AddAccis` and `modify_accis`): it is the
  text of the verdict and only adds a warning.

## 2026-11-10 — G5: the static setpoints of the YAML file of Qatar (20 and 25.5 °C)
- Context: v04 §6.3 gives `static_setpoints: {heating: 20.0, cooling: 25.5}` for
  `qat_indraganti2018_hvac.yaml`, "EN 16798-1 Table B.2, offices, category II". In `accim.constants.EN16798_TABLE_B2`
  (UNE-EN 16798-1:2020, page 49, checked by `tests/core/test_setpoint_limits.py`), the offices of category II have 20
  and 26 °C; 25.5 °C is the cooling value of category I (21 and 25.5 °C).
- Why it matters: the value and its source disagree; comfort modes 0 and 1 of 102 use them.
- Options considered: (i) the numbers of v04 §6.3, 20 and 25.5 °C (implemented); (ii) category II of the table, 20 and
  26 °C; (iii) category I, 21 and 25.5 °C.
- Owner: the author.
- Status: open; option (i) implemented provisionally (the numbers of the decision; the YAML file notes the disagreement
  in a comment and its evidence says that they are a choice).

## 2026-11-10 — G5: the floor exact after the rounding, as the ceiling (B5-2)
- Context: finding B5-2 of v04 §3.3 asks to set `roundedACST = ACSTceil` where the ceiling bounds the cooling setpoint,
  since the strict rounding downwards gives one step of `SetpointAcc` below it, and says that the floor is exact. The
  floor is exact when its product by `SetpointAcc` is exact in binary (20 °C, or 25.5 °C with 10000); otherwise the
  strict rounding upwards gives one step above it (19.1 × 100 = 1910.0000000000002, so a floor of 19.1 °C gave 19.11 °C
  with an accuracy of 100).
- Why it matters: the heating setpoint bounded by the floor would be above the floor for some floors and accuracies.
- Options considered: (i) set `roundedAHST = AHSTfloor` where the floor bounds the heating setpoint too (implemented);
  (ii) only the ceiling, as written in the finding.
- Owner: the author.
- Status: open; option (i) implemented provisionally: the program of the limits is new in 1.2.0, so no released output
  changes, and with the floors of Table B.2 and the default accuracy the result is that of option (ii).

## 2026-11-10 — G4: the criterion of the test of JPN Aqilah 2025 against its YAML twin 101
- Context: task G4 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§3.1 B4-1) asks for a test of 23 (with the RMOT of
  EnergyPlus) against 101 (`rmot_alpha` from the weather file) with |ΔComfTemp| < 0.1 K from day 21 and > 1 K on day 1;
  the review suggested the start of 1 January. Measured with `compute_setpoints` (Seville, category 90, comfort mode 3):
  from 1 January, the difference of the first day is 0.92 K in hours 2 to 24 (1.30 K in the hourly maximum, which is
  that of the first hour, whose first timestep reads RMOT 0), and from day 21 the first hour of some days differs by up
  to 0.10 K (0.1013 K on 2 May): in the first timestep of each day 23 still reads the RMOT of the previous day while 101
  has already updated its running mean (0.52 K in that timestep), a difference that is not the transient of B4-1 and
  lasts all the year. In hours 2 to 24 the difference from day 21 is at most 0.024–0.028 K.
- Why it matters: the literal criterion fails with the start of 1 January (by 0.08 K on day 1, and by 0.0013 K on 2 May),
  and a test must not be loosened to pass.
- Options considered: (i) the starts of 1 April and 1 July of the review (the transient of the first day 1.47 and 1.93 K),
  hours 2 to 24 of each day, and all the hours of days 21 to 30; (ii) the start of 1 January with the hourly maximum of
  day 1 and the whole year from day 21 (fails); (iii) daily means of the comfort temperature.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`tests/core/test_jpn_aqilah2025.py`, thresholds unchanged), with the
  measured values in the test, `DEVLOG.md` and `notes/decisions.md`; with the weather file, 23 and 101 are identical in
  every timestep, which another test checks.

## 2026-11-10 — G1: the tolerance of the setpoints of the ACCIS with the setpoints of the hooks
- Context: task G1 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` (§3.1, finding A4/A6-1, option (a)): the hooks of
  the ATHB and of the SET update `ACST`, `AHST`, `ACSTnoTol`, `AHSTnoTol` and the rounded setpoints of the ACCIS
  before its hour counters run. In the ACCIS, the setpoints without the tolerance (`ACSTnoTol`, `AHSTnoTol`) are the
  limits of the comfort band, which the counters use, and the thermostats get the setpoints with the tolerance
  (`ACST = ACSTnoTol + ACSTtol`, `ACSTtol = −setpoint_tolerance`); v04 does not say which of them the setpoints of a
  hook are.
- Why it matters: the comfortable hours must be those of the band of the ATHB or of the SET, and the thermostats of A4
  and A6 got the setpoints of the hooks as they were (without a tolerance).
- Options considered: (i) the setpoints of a hook are the limits of the comfort band (without the tolerance), and the
  thermostats get them with the tolerance, as the adaptive setpoints; (ii) the thermostats get them as they are (as
  before G1), and the counters use a band wider by the tolerance; (iii) the thermostats get them as they are and the
  counters use their band (no tolerance anywhere: a second program after SetASTnoTol).
- Owner: the author.
- Status: open; option (i) decided provisionally: it is the only one in which the counters, the outputs and the floor
  and ceiling of B5 (D5) follow the hook in the same programs as the adaptive setpoints, and `setpoint_tolerance` keeps
  its meaning; `setpoint_tolerance=0` gives the thermostats the setpoints of the hook as they are (as before G1). It
  changes the thermostat setpoints of A4 and A6 (not released yet) by the tolerance (0.1 K by default), pending author.

## Answered

The questions on the scope and the technology of the GUI, on the names of the arguments of accim 1.0.0, on the EMS
code of the comfort standards of each output IDF of `AddAccis` (option 1, as implemented), on the design days of
`vrf_mm` (option (a): the same rule as `ex_mm`) and on the `schedule` of `set_clothing_method` of A5 (option (b): the
clothing insulation schedule, and another argument for `CalculationMethodSchedule`) were answered: see
[[decisions.md]]. The 36 provisional decisions of the proposals of 1.2.0 (2026-11-09 and 2026-11-10)
were answered on 2026-11-10 (`notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §5): see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]].
