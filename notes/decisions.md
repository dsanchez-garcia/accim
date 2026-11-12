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

## 2026-11-12 — The implementation of the decisions of 2026-11-12: the choices that they do not cover

- **Status**: accepted provisionally (taken on 2026-11-12 by Claude Code, the model Claude Fable 5.2, while it
  implemented the decisions of that day for the author, who asked it to work autonomously; the author can change any of
  them, and the review of Claude Science of sessions 2 and 3 can contrast them)
- **Context**: on 2026-11-12 the author asked for the implementation of the P1 and P2 tasks of
  [[decisions.md#2026-11-12 — The decisions on the six questions left open after session 3 of the review of 1.2.0|the decisions of that day]]
  (the entry below). The decisions say what to do; these are the choices of how, with the most conservative option
  where there was one, as the rules of the review sessions ask (`notes/COPILOT_SIGUIENTE_SESION.md` §2, rule 3). Each
  task is one commit, and `DEVLOG.md` has its verification.
- **Decision** (by task, in the order in which they were done):
  1. Comfort standards 9 and 10 (decision 11).
     - The code of 9 reads `Tout_metric` in every model, with no fallback to `PMOT`: in a model without the EMS code of
       the outdoor metric (those of `add_accis_to_idf`, or the output IDFs of other comfort standards), a zone whose
       program is edited to `set ComfStand = 9` stops EnergyPlus (the variable is not initialised). The alternatives
       were to write the lines of 9 with `PMOT` in the models without that code, as the custom model does (a silent
       running mean that is not that of the model, the error that the decision corrects), or to give that code to every
       model with the code of 9 (all the models of `add_accis_to_idf`, which would get the programs of the outdoor
       metric and the outputs `Tout_metric_<zone>` without using them). `AddAccis`, `modify_accis` and the parameter
       `comfort_standard` of the parametric module add the code.
     - A zone that leaves 9 gets the outdoor metric `'pmot'` again, unless the call gives it one, and the model loses
       the code of the outdoor metric when no zone needs it: otherwise the custom model would inherit the mean of 7
       days without being asked. The zones that leave a comfort standard of the registry keep theirs, as before.
     - The arguments `custom_outdoor_metric`, `custom_alpha` and `custom_days` do not change the metric of 9.
     - The static line 0.078·T + 23.25 keeps `PMOT` in 9 and takes it in 10, as decided; it is still not verified in
       the National Building Code of India 2016.
     - The models of earlier versions of accim (one program `SetInputData`) keep their code of 9 and 10; those of
       accim before 0.8, which get the subprograms of this version, get those of 9 with `PMOT`.
     - `Table.format_table(type_of_table='temperature')` takes `Tout_metric (°C)` for 9 in comfort modes 1 to 3.
     - The golden master changes in the output IDFs of 9 and 10, in one line of `SetVST` of every model in mixed mode
       (its branch of INT EN16798 named comfort standard 10) and in the models with the code of all the comfort
       standards; checked line by line before writing the golden files again.
  2. The minimum and maximum of the setpoints with the tolerance (decision 6, finding A19; and decision 10, task S1).
     - A maximum less than twice the tolerance of the setpoints above the minimum of the same zone is a `ValueError`
       (`check_setpoint_limits(..., setpoint_tolerance=...)`), as a window of the limiter of the drift narrower than
       twice the tolerance (finding A9): the setpoints of the thermostats on both limits would cross. The decision does
       not mention it; without it, limits less than 0.2 K apart (valid until now) would give EnergyPlus a heating
       setpoint above the cooling setpoint. `AddAccis` checks it with the largest tolerance of its output IDFs, and
       `modify_accis` in every call, also for the limits that the zones keep (the tolerance of the setpoints is an
       argument of every call).
     - The warning of S1 compares the setpoints of the thermostats on the limits, and its message gives both values
       when the tolerance is not 0 ("24.5 °C, 24.6 °C in its thermostat with the tolerance").
     - Check 5 of `verify_accim_simulation` compares the setpoints of the thermostats with the limits with the
       tolerance, and those without the tolerance with the limits themselves.
     - The models written with the limits before this change keep their program until their limits are written again
       (`modify_accis` with a limit); the limits are new in 1.2.0, so no released model has them.
     - The measurement of F1 of the winter week of comfort standard 24 (8–14 January, the sample model with a minimum
       of 18 °C in one zone) was made again, since that thermostat now heats to 18.1 °C: the largest hourly difference
       between the SET of the hook and that of EnergyPlus in that zone is 0.187 K (it was 0.191 K), and the other zone
       is within the causal band in 58.2 of its 60 occupied hours (56.3 before); checked against the commit before the
       change in a temporary worktree. The summer week does not change.
  3. The static setpoints of JPN Aqilah 2025 in every zone (decision 7, finding A24).
     - The inputs are added where the EMS global variables of the static setpoints are declared
       (`set_static_setpoint_variables`, which `add_accis_to_idf` and `set_comfort_standard_code` already call), so
       every function that writes the code of 23 gives them to all the zones, in the place of the inputs of the zones.
     - The zones of the other comfort standards get the defaults (20 and 28 °C), as the decision says, also when
       `AddAccis` or `modify_accis` are given other static setpoints for the zones of 23.
     - A model that loses the code of 23 (`set_comfort_standard_code` without it) loses these inputs in the zones of
       the other comfort standards, so that the output IDFs of `AddAccis` without that code do not change.
  4. E-F1 measured again (decisions 1 and 2, findings A1 and A2); the measurement is in the entry below.
     - The activity levels are 110.7 (that of the sample model), 115 and 126 W/person (the examples of the decision:
       1.1 and 1.2 met with the 1.8 m² of the hooks), constant all the year, each one in a simulation of a year; the
       clothing insulation is that of the sample model (1.0 and 0.5 clo by season), and its two levels are reported
       apart.
     - That the term of the activity of the convective coefficient is the difference is checked with a copy of the
       source of the two-node model of pythermalcomfort 4.8.1 in which the condition of that term is disabled in the
       real environment only (the test builds it from the installed source, and is skipped with another version):
       its argument `calculate_ce` removes the term from both environments, so it does not reproduce EnergyPlus.
     - The draft of the issue asks which behaviour is intended and does not say which one is right: the program of
       the SET of ASHRAE 55-2017, Appendix D, which the code of EnergyPlus cites, is not in the library.
     - The comments of `PMV_BODY_SURFACE_AREA` and `MET_ACTIVITY_LEVEL` said that EnergyPlus takes 1.8 m² in all its
       thermal comfort models; they now say which ones do.
  5. A model prepared for a hook that is simulated without it (decision 3, finding A4).
     - A model is "prepared for a hook" if its IDF file has a program `ApplyHookSetpoints_<zone>`, read from the text
       of the file (`hook_zones_of_file`), so that `run_ep` checks the models of the folder without loading them
       with eppy, whatever their EnergyPlus version is.
     - The backend of the API warns when a model prepared for a hook gets no hook before its EMS programs
       (`before_programs`; `hooks` with `runs_before_programs` in `run_ep`), whatever hook it is: the model does not
       keep which function prepared it (an entry of `TODO.md`), so a hook of another kind is not detected.
       `run_simulations` warns once for all its models (`MissingHookWarning`, a `UserWarning` that can be filtered).
     - `run_ep` raises before it prints the simulations and before any of them runs, also for a folder with other
       models that could run: the user takes the models of the hooks out of the folder, or runs it with the backend
       of the API.
     - `tests/core/test_table_optional_outputs.py` simulated a model with the objects of the ATHB with the EMS
       backend, and checked that the outputs of the ATHB were 0: it now runs it with the backend of the API and the
       hook (and checks the error of the EMS backend), so `Table` is tested with the outputs of the hook.
  6. The warning of RMOT of `modify_accis` (decision 8, finding A25).
     - The warning is that of JPN Aqilah 2025 without the weather file, with the reason before its text ("whose
       programs of the outdoor metric this call has written again without the weather file of the simulation"), once
       in the call. A model that already read RMOT is not warned again by the calls that do not give comfort standard
       23, as before.
     - The warning of the outdoor metrics that begin with PMOT leaves out the metric of the zones of JPN Aqilah 2025
       whenever the programs are written without a weather file (it already did in the models that did not begin with
       one; the fix is in `set_outdoor_metric_code`, so the parametric module follows), and is not given if no other
       metric begins with PMOT.
     - The input of the outdoor metric of those zones (`CustAST_metric = 2`) stays, unused, as before: a later call
       with `epw` gives them the running mean of the weather file again.
  7. The warning of `drift_mode='window'` (decision 4, finding A8).
     - The warning is given when a call gives the window to a zone (in its arguments or in `zone_arguments`), once in
       the call, after the checks of the arguments; not for the zones that keep it in a call that does not give it,
       and not by the parameter `drift_mode` of the parametric module, which would warn in every simulation (its
       documentation says that the window is experimental).
     - The measurements of the finding were made again before documenting them (the sample model in Seville, January,
       April and July, without the limiter, with the window and with the rate): those of the window are the same; the
       rate no longer gives exactly the results of no limiter, as the finding said, since it changed the setpoints by
       about 0.2 K on two Mondays of April and one of July (probably since task S3, which came after the self-audit:
       not checked with the earlier code). The documentation gives what was measured on 2026-11-12, and
       `tests/core/test_drift_limiter.py` reproduces April (three simulations of a month).
     - The documentation also gives the electricity of the VRF system (from 7817 to 21 715 kWh in April), which the
       finding did not have, since the energy of the coils alone hides that the cooling energy falls.
- **Consequences**: the tasks done leave `TODO.md` for `DEVLOG.md`; the documentation says what each choice means
  for the users (section 4.2 of the detailed use, and `CHANGELOG.md`).

## 2026-11-12 — E-F1 measured again: the SET of EnergyPlus (Pierce) against that of pythermalcomfort, by activity level

- **Status**: accepted (a measurement; task of `TODO.md` from findings A1 and A2 of the self-audit of 2026-11-11,
  decided on 2026-11-12: decisions 1 and 2 of the entry of the decisions below). It completes the measurement of
  2026-11-10 ([[decisions.md#2026-11-10 — The SET of EnergyPlus (Pierce) against that of pythermalcomfort, measured (E-F1)|E-F1]]),
  which holds near 1 met only.
- **Context**: the self-audit found that the Pierce model of EnergyPlus converts the activity level with 1.8258 m²
  (accim, with 1.8 m²: finding A1) and has no term of the activity in the convective coefficient of the real
  environment (finding A2), so E-F1, measured at the 110.7 W/person of the sample model, mixed an input difference with
  the model difference and could not be extended to other activity levels. Both were checked in the sources on
  2026-11-12 (the tag `v25.1.0` of the repository of EnergyPlus): in `ThermalComfort.cc`, `CalcStandardEffectiveTemp`
  takes an air velocity of at least 0.1 m/s and the convective coefficient of the real environment max(3.0·P^0.53,
  8.600001·(v·P)^0.53), with 5.66·(met − 0.85)^0.39 only in that of the standard environment, and its header cites
  ASHRAE 55-2017, Appendix D; `ThermalComfort.hh` has `BodySurfArea = 1.8` (Dubois) and `BodySurfAreaPierce = 1.8258`;
  and the Engineering Reference (`occupant-thermal-comfort.tex`) says that the convective coefficient of the Pierce
  model is the larger of 8.6·v^0.53 and 5.66·(M/58.2 − 0.85)^0.39, with the air velocity reset to 0.137 m/s, and that
  all the thermal comfort models take 1.8 m². pythermalcomfort 4.8.1 (`two_nodes_gagge.py`) has that term in both
  environments, unless `calculate_ce`. The listings of the SET of ASHRAE 55-2017 and 55-2020 are not in the library
  **[not verified]**.
- **Measurement** (2026-11-12, `tests/core/test_pierce_set.py`): the model of E-F1 (the sample model with the ACCIS,
  `vrf_ac`, INT EN16798, category II, comfort mode 3, and Pierce in its People objects; a year in Seville, EnergyPlus
  25.1, 6 timesteps per hour; air velocity 0.137 m/s; clothing insulation 1.0 clo until 1 April and from 1 October, 0.5
  clo between them), with the activity level schedules of its People objects at 110.7 (the sample model), 115 and 126
  W/person. Differences of the hourly means (`set_tmp` of pythermalcomfort 4.8.1 minus the Pierce SET of EnergyPlus),
  all the hours of the year, Block1:Zone1 / Block1:Zone2: mean, mean absolute and maximum absolute (K).

  With the metabolic rate of the hooks of accim, activity/(58.2·1.8):

  | Activity (met) | Posture | Mean | Mean absolute | Maximum absolute |
  |---|---|---|---|---|
  | 110.7 W (1.057) | standing | −0.045 / −0.045 | 0.057 / 0.056 | 0.181 / 0.196 |
  | 110.7 W (1.057) | sitting | −0.116 / −0.116 | 0.118 / 0.117 | 0.324 / 0.344 |
  | 115 W (1.098) | standing | −0.325 / −0.325 | 0.325 / 0.325 | 0.578 / 0.603 |
  | 115 W (1.098) | sitting | −0.398 / −0.397 | 0.398 / 0.397 | 0.711 / 0.746 |
  | 126 W (1.203) | standing | −0.943 / −0.943 | 0.943 / 0.943 | 1.411 / 1.441 |
  | 126 W (1.203) | sitting | −1.021 / −1.020 | 1.021 / 1.020 | 1.537 / 1.580 |

  With the metabolic rate of the Pierce model of EnergyPlus, activity/(58.2·1.8258) (the same inputs for both models):

  | Activity (met) | Posture | Mean | Mean absolute | Maximum absolute |
  |---|---|---|---|---|
  | 110.7 W (1.042) | standing | −0.058 / −0.058 | 0.058 / 0.058 | 0.132 / 0.144 |
  | 110.7 W (1.042) | sitting | −0.128 / −0.128 | 0.128 / 0.128 | 0.273 / 0.290 |
  | 115 W (1.082) | standing | −0.331 / −0.331 | 0.331 / 0.331 | 0.516 / 0.535 |
  | 115 W (1.082) | sitting | −0.403 / −0.403 | 0.403 / 0.403 | 0.649 / 0.677 |
  | 126 W (1.186) | standing | −0.966 / −0.966 | 0.966 / 0.966 | 1.387 / 1.411 |
  | 126 W (1.186) | sitting | −1.043 / −1.043 | 1.043 / 1.043 | 1.512 / 1.546 |

  By clothing insulation (the metabolic rate of the Pierce model, standing, Block1:Zone1; mean): −0.065 K (0.5 clo) and
  −0.051 K (1.0 clo) at 110.7 W/person; −0.373 and −0.290 K at 115 W/person; −1.090 and −0.843 K at 126 W/person.

  The body surface area of the conversion alone (`set_tmp` with 1.8 m² minus `set_tmp` with 1.8258 m², standing): +0.013
  K on average in the year at 110.7 W/person (+0.037 K with 1.0 clo and −0.012 K with 0.5 clo; at most 0.071 K), +0.006
  K at 115 W/person and +0.023 K at 126 W/person (at most 0.078 K).

  Without the term of the activity in the convective coefficient of the real environment of pythermalcomfort (its
  two-node model run from a copy of its source with that one condition disabled; the metabolic rate of the Pierce model,
  standing), as in the code of EnergyPlus:

  | Activity (met) | Mean | Mean absolute | Maximum absolute |
  |---|---|---|---|
  | 110.7 W (1.042) | −0.058 / −0.058 | 0.058 / 0.058 | 0.132 / 0.144 |
  | 115 W (1.082) | −0.056 / −0.056 | 0.056 / 0.056 | 0.130 / 0.141 |
  | 126 W (1.186) | −0.051 / −0.051 | 0.051 / 0.051 | 0.125 / 0.134 |

- **Decision**: (1) the statements of E-F1 and F1 on the agreement of both SET (0.05 to 0.2 K) hold near 1 met only
  (up to about 1.05 met, where the term of the activity is not the larger one at 0.137 m/s); at 1.1 met the SET of
  pythermalcomfort is 0.33 K below that of EnergyPlus on average, and at 1.2 met, 0.94 to 0.97 K (standing; 0.07 K more
  sitting). (2) That term of the convective coefficient of the real environment accounts for all the dependence on the
  activity level: without it, the difference is 0.05 to 0.06 K at the three activity levels, of the order of the other
  differences of both codes (the radiative fraction of the body, 0.72 in EnergyPlus and 0.73 standing or 0.70 sitting
  in pythermalcomfort). (3) The body surface area of the conversion (1.8 m² in the hooks of accim, kept by decision 1 of
  2026-11-12) changes the SET by 0.01 to 0.02 K on average (at most 0.08 K), so it is not what makes both SET differ.
  (4) The reference SET of F1 and F3 is that of pythermalcomfort (decision 12 of 2026-11-12), so these differences are
  the error of the Pierce SET of EnergyPlus as an approximation of it: the indicators of the causal band with the
  Pierce SET are comparable with those of the reference SET only for activity levels of about 1 met.
- **Consequences**: `tests/core/test_pierce_set.py` reproduces the three tables (the activity level is its parameter;
  the three simulations run at the same time), and sections 4.9.2, 4.9.3 and 4.7.6 of the detailed use give the
  differences by activity level. The draft of an issue for the repository of EnergyPlus
  ([[BORRADOR_issue_EnergyPlus_SET_Pierce_2026-11-12.md]]) has the measurement and the two differences between its
  code and its Engineering Reference; the author posts it, if he sees fit, once he has checked the program of the SET
  of ASHRAE 55 that the code cites.

## 2026-11-12 — The decisions on the six questions left open after session 3 of the review of 1.2.0

- **Status**: accepted (decided on 2026-11-12 by Claude Code, the model Claude Fable 5.2, for the author, who delegated
  to it all the decisions that were open in [[questions.md]]; the author can change any of them, and the review of
  Claude Science of sessions 2 and 3 can contrast them)
- **Context**: after session 3 ([[INFORME_SESION_v1.2.0_2026-11-11_3.md]]), [[questions.md]] had six open entries: the
  eight findings of the self-audit of session 2 that needed a decision of the author (A1, A2, A4, A8, A15, A19, A24 and
  A25), the details of tasks S4 and S1 (implemented provisionally), comfort standards 9 and 10, and the two questions of
  F3 that waited for the author with Ruiji Sun (#9, the SET of the indicators of the causal band, and #12, the static
  reference of case (i) of the validation study). Their sources were read again on the server before deciding; nothing
  of the code was changed.
- **What was checked** (on 2026-11-12; **[verified]** in the source, **[inferred]**, or as said):
  - The SET of the causal model **[verified]**: Sun, Brager & Schiavon (2026), Energy and Buildings 370, 118097 (the PDF
    is now with the other pending articles of the server, those of Appendix B of the handoff of Claude Science), builds
    its model with the ASHRAE Global Thermal Comfort Database II, version 2.1 (809 buildings and more than 100 000
    records, §3.1), with the SET as the metric of the indoor thermal environment, which takes in the metabolic rate and
    the clothing insulation (§3.2 and §4.1), and it describes no calculation of the SET of its own (its data are
    available on request). §4.3 gives TSV = 0.11·SET − 2.6 and the band of 19 to 28 °C of SET, 7 °C wider than that of
    the PMV model (24 to 26 °C), and proposes the limits of the band as the heating and cooling setpoints of the
    thermostats, and the band to assess the thermal comfort of building energy simulations. The script that makes that
    version of the database (`v2.1.0/main.py` of the repository `CenterForTheBuiltEnvironment/ashrae-db-II` of GitHub,
    which holds the code that maintains the database from version 2.1) drops the columns `pmv`, `ppd` and `set` of the
    earlier version and calculates `set` with `set_tmp(tdb=ta, tr=tr, v=vel, rh=rh, met=met, clo=clo)` of
    pythermalcomfort and no other argument: the air speed and the clothing insulation as recorded, and the defaults of
    the function (the posture, standing). And the code of the earlier paper of the same authors with the same database
    and metric (Sun et al., 2024, Building and Environment, 111530, doi:10.1016/j.buildenv.2024.111530; its notebook
    `neutral_temperature.ipynb`, in the repository `ruijis/paper-causal-thinking` of GitHub) reads the file of the
    measurements of version 2.1 from that repository and regresses the votes on its column `set`, without calculating
    the SET.
  - The Pierce model of EnergyPlus **[verified]**: in `src/EnergyPlus/ThermalComfort.cc` of EnergyPlus 25.1 (the tag
    `v25.1.0` of its repository), the Pierce model divides the activity level by `BodySurfAreaPierce` and the Fanger
    model by `BodySurfArea`; the convective coefficient of the real environment is the larger of 3.0·P^0.53 and
    8.600001·(v·P)^0.53, with an air velocity of at least 0.1 m/s, and 5.66·(met − 0.85)^0.39 is only in that of the
    standard environment; the function cites ASHRAE 55-2017, Appendix D. In pythermalcomfort 4.8.1
    (`two_nodes_gagge.py`) the real environment has that term too (unless `calculate_ce`). With `set_tmp` (standing, the
    air and mean radiant temperatures equal, 0.137 m/s, 50 %), that term lowers the SET by 0.16 K at 1.1 met and by 0.40
    K at 1.2 met with 0.5 clo and 26 °C, by 0.06 and 0.16 K with 1.0 clo and 21 °C, and by nothing at 1.042 met;
    standing is 0.03 to 0.04 K above sitting; and 110.7 W/person converted with 1.8 m² instead of 1.8258 m² give 0.01 K
    (0.5 clo) to 0.07 K (1.0 clo) more. These are two conditions, not the measurement of E-F1 (the self-audit estimated
    −0.39 K at 1.1 met and −0.97 K at 1.2 met with the conditions of the year of E-F1 and the algorithm of EnergyPlus).
  - Comfort standards 9 and 10 **[verified]**: Rawal et al. (2022), Building and Environment 219, 109187: its
    nomenclature tells the 7-day and 30-day running means of the outdoor temperature (Tout-7DRM and Tout-30DRM) apart
    from their weighted versions (Tout-7DRM-W and Tout-30DRM-W); §4.4 and Fig. 15 give model A with Tout-7DRM and model
    B with Tout-30DRM, both from 5.5 to 33 °C, for dwellings in natural ventilation or mixed mode; §5.1 weights them
    exponentially (α = 0.8) only to compare the model with others (Fig. 17); §3.2 says that both were calculated with
    functions written in R from hourly weather data, without a formula. In accim (`accim/sim/ems/setpoint_lines.py` and
    `program_lines.py`), 9 reads `PMOT`, 10 reads `RMOT`, and comfort mode 1 of 9 adds 2.72 and 1.5 to the heating
    setpoint out of the limits. The line 0.078·T + 23.25 (±1.5 °C for 90 %) is the model of the air-conditioned
    buildings of the National Building Code of India 2016 and of the Energy Conservation Building Code 2017, with the
    30-day outdoor running mean air temperature, according to two secondary sources found on the web (a course handout
    that reproduces the code of 2017, and a report of TERI); neither code is in the library **[not verified in the
    codes]**.
  - EN 16798-1 **[verified]**: UNE-EN 16798-1:2020, Table B.5 (B.2.4, p. 54), the temperature ranges for the hourly
    calculation of the heating and cooling energy, has the two limits of each season (with about 1.0 clo in the heating
    season and 0.5 clo in the cooling season): in category II, 20.0–24.0 and 23.0–26.0 °C in the offices, and 20.0–25.0
    and 23.0–26.0 °C in the living spaces of the dwellings; its note lets the limits within the winter and summer values
    be used between the seasons, with θrm between 10 and 15 °C. CEN/TR 16798-2:2019 has the same ranges in its Table B.4
    (p. 34; it differs in the heating range of the offices of category IV), repeats that note (7.2.2) and applies the
    criteria of the heating season below a running mean of 10 °C (its remarks on Figure B.1). Table B.4 of EN 16798-1
    (B.2.3, p. 54) gives the corrections for air speeds of 0.6, 0.9 and 1.2 m/s under personal control, with operative
    temperatures above 25 °C.
- **Decision** (the six entries of [[questions.md]] are below, moved as they were, each with its verdict):
  1. A1: the hooks keep the conversion of the activity level with 1.8 m² (option (i)); E-F1 is measured again with the
    1.8258 m² of the Pierce model too.
  2. A2: E-F1 is measured at 1.1 and 1.2 met, and its statements hold near 1 met until then (option (i)); the reference
    SET of F1 and F3 is that of pythermalcomfort (option (ii), with #9).
  3. A4: `run_ep` raises with the EMS backend, and the API backend warns, when a model prepared for a hook is simulated
    without it (option (ii)).
  4. A8: `'window'` stays as it is, documented with its energy cost and with a warning, and `'rate'` is the recommended
    mode (options (i) and (iii)); it is not redefined in 1.2.0.
  5. A15: the limitation of the constant range is documented (option (i)), and a seasonal range with the limits of EN
    16798-1, Table B.5, is a P2 task (option (ii)).
  6. A19: where the minimum or the maximum binds, the thermostats get it with the tolerance (option (ii)).
  7. A24: every zone of the models with the code of comfort standard 23 gets the inputs of its static setpoints (option
    (ii)).
  8. A25: `modify_accis` gives the warning of RMOT when the zones of 23 lose the start with the weather file (option
    (i)).
  9. S4: `pythermalcomfort_set` of `table_indicators` is final (option (i)), and it also takes the inputs of the
    occupants from the People objects (option (ii)).
  10. S1: the comparison stays as implemented (option (i)), with the thermostat setpoints of the verdict of A19.
  11. Comfort standards 9 and 10 are corrected in 1.2.0 as the review of Claude Science recommends (option (i)).
  12. #9: the reference SET of the causal band is that of pythermalcomfort, with which the SET of the database of the
    model was calculated; the Pierce SET of EnergyPlus stays as the indicator that every model has.
  13. #12: the validation study has both static references, the PMV setpoints of category II and the fixed 20 and 26 °C
    of EN 16798-1; its climates, clothing insulation and air speeds are chosen too.
- **Consequences**: [[questions.md]] has no open question. None of the decisions is implemented yet: `TODO.md` has their
  tasks (P1: comfort standards 9 and 10, A19 with S1, A24, A4, A8, A25, E-F1 measured again with the corrections of its
  documentation, and the documentation of the reference SET; P2: the inputs of the People objects in
  `pythermalcomfort_set`, the seasonal range of A15 and the simulations of the validation study). The overheating
  criteria of CIBSE TM52 and TM59 leave the scope of 1.2.0 for `ROADMAP.md` (the recommendation of the handoff of Claude
  Science, §4). Three things are left to the author, who is the one who can do them: the message to Ruiji Sun (to
  confirm the SET of the paper and to agree the choices of the study), the jar of the Future Weather Generator, and the
  issue for EnergyPlus on the convective coefficient of its Pierce model, once E-F1 is measured again.

### 2026-11-11 — The findings of the self-audit of session 2 that need a decision of the author
- Context: the self-audit of session 2 (`notes/attachments/autoauditoria_sesion2_v1.2.0.json`, findings A1–A26;
  §5 and §7 of `notes/COPILOT_SIGUIENTE_SESION.md`). The bugs and the small fixes are done in session 3 (see the entry
  of the report `notes/INFORME_SESION_v1.2.0_2026-11-11_3.md`); these need a choice of the author, so nothing was
  changed (the most conservative option), except the documentation where it says so.
- Why it matters: each one changes the results, the outputs or the model of some users.
- Options considered, by finding:
  - **A1 (scientific, E-F1 and F1)**: EnergyPlus converts the activity level of its Pierce model with a body surface
    area of 1.8258 m² (ThermalComfort.cc of EnergyPlus 25.1), and accim (the hooks of the SET and the comparison of
    E-F1) with 1.8 m² (`MET_ACTIVITY_LEVEL`, the convention of Fanger and ISO 7730): 1.43 % more met (1.057 against
    1.042 met for 110.7 W/person), so the differences of E-F1 and F1 (−0.045 K standing, −0.116 K sitting; −0.08 and
    −0.155 K) mix an input difference with the model difference. (i) Keep 1.8 m² and document the offset (about
    0.1 K, to be measured); (ii) convert with 1.8258 m² in the hooks, consistent with the Pierce SET that F1 and F3
    report beside them. The new measurement needs pythermalcomfort, which was blocked on this server on 2026-11-11
    (numba and Smart App Control) and is imported again since the author turned Smart App Control off on 2026-11-12
    (`TODO.md`).
  - **A2 (scientific, E-F1)**: in the real environment, EnergyPlus 25.1/25.2 computes the convective coefficient of
    the Pierce model without the term of the activity, 5.66·(met − 0.85)^0.39 (which it applies only to the standard
    environment), unlike its Engineering Reference and pythermalcomfort; above about 1.046 met that term is the larger
    one, so the agreement of E-F1 (the sample model is at 1.042 met in the Pierce model) holds near 1 met only. (i)
    Repeat E-F1 at 1.1 and 1.2 met and restrict the present statements to about 1 met (not blocked here any more, as
    A1); (ii) the choice of the reference SET of F1 and F3 together with decision 9 (Ruiji Sun).
  - **A4 (design, F1)**: a model prepared by `apply_athb_setpoints`, `apply_set_setpoints` or
    `apply_sun2026_setpoints` simulated without its hook (the EMS backend, or the API without hooks) runs without an
    error or a warning, with the setpoints of the ACCIS and the outputs of the hook at 0. (i) As now, documented; (ii)
    `run_ep` and `run_simulation` raise (EMS backend) or warn (API backend without a hook) when the model has the
    programs `ApplyHookSetpoints_<zone>`.
  - **A8 (design, F2)**: `drift_mode='window'` clips both setpoints to T_rm_in ± delta, and T_rm_in is the running
    mean of the operative temperature of the zone itself, so the dead band collapses to `delta_heat + delta_cool` (2 K)
    around the recent temperature of the zone (or to a point, with crossed thermostats, when the band of the comfort
    model is all out of the window), with much more heating or cooling, and the exposure can drift by only about
    (1 − α)·delta per day: a stricter control than `'rate'`. It is decision 6 of the author, implemented as written.
    (i) Document the collapse and its energy effect, and warn with `'window'`; (ii) redefine `'window'` to limit only
    the changes that move a setpoint farther than delta from T_rm_in, or to shift the whole band keeping its width;
    (iii) keep `'rate'` as the recommended mode (case (v) of the validation study uses it). The narrow window of
    finding A9 raises a `ValueError` since session 3.
  - **A15 (design, H3)**: the range of `long_term_range` of the long-term discomfort uses the minimum for heating and
    the maximum for cooling of EN 16798-1, Table B.2 (20–26 °C for category II) in all the timesteps, while the table
    gives seasonal one-sided design values (about 1.0 clo in winter and 0.5 clo in summer), so summer overcooling between
    20 and 23 °C and winter overheating between 24 and 26 °C count as comfortable. (i) State the limitation in section
    4.2.6 (and pair it with the overcooling indicator of F3); (ii) a seasonal variant with the cooling season of the
    ACCIS, once the author chooses a source for the missing bounds.
  - **A19 (design, G5)**: where the minimum (maximum) of the setpoints binds, the thermostat setpoint and the limit of
    the comfort band are both the limit (AHST = AHSTnoTol = AHSTmin), so the tolerance vanishes there, unlike the
    setpoints of the hooks (decision 23 of G1: the thermostats get the band plus the tolerance). (i) As now, documented
    (the hour counters at the limit); (ii) AHST = max(AHST, AHSTmin + AHSTtol) and ACST = min(ACST, ACSTmax +
    ACSTtol), with AHSTnoTol and ACSTnoTol bounded by the limits (changes the output IDFs with limits).
  - **A24 (bug, G4)**: in the models of `add_accis_to_idf` (the code of all the comfort standards), a zone switched to
    comfort standard 23 by editing `set ComfStand = 23` in its program `SetInputData_<zone>` stops EnergyPlus during
    the warm-up ("Variable = 'STATICACST' used in expression has not been initialized"), since only the zones of 23
    have the inputs `StaticAHST` and `StaticACST` (decision of G4: the zones of the other comfort standards do not get
    them, and their output IDFs do not change). (i) As now, documented in section 4.2.1 (session 3); (ii) give every
    zone of the models with the code of 23 the two inputs (changes the output IDFs of `add_accis_to_idf`, golden
    master s01–s06 and s09); (iii) initialise both global variables in a program at the beginning of each environment
    (changes them too).
  - **A25 (design, G4)**: a `modify_accis` call that changes the outdoor metric of another zone without `epw`
    rewrites the programs of the outdoor metric beginning with PMOT, so the zones of JPN Aqilah 2025 move silently from
    the running mean of the weather file to the RMOT of EnergyPlus (about 21 % low on the first day, B4-1), without the
    warning of RMOT, and the warning that is given says that `rmot_alpha` begins with PMOT, which is wrong for those
    zones. (i) Give the warning of RMOT whenever the model has zones of 23 and its programs stop beginning with a
    weather file, and leave those zones out of the warning of PMOT; (ii) keep the start with the weather file (do not
    rewrite without `epw` when the programs can be kept, or ask for `epw`); document it in `modify_accis`.
- Owner: the author (A1 and A2 with Ruiji Sun, as decision 9).
- Provisional decision (pending author until 2026-11-12): nothing changed but the documentation of A24 (section 4.2.1).
- Status: answered on 2026-11-12 (A1 (i); A2 (i) and (ii); A4 (ii); A8 (i) and (iii); A15 (i) and (ii); A19 (ii); A24
  (ii); A25 (i); decided by Claude Code for the author).
- Verdict (2026-11-12), by finding:
  - **A1**: option (i). The hooks keep the conversion with 1.8 m² (`MET_ACTIVITY_LEVEL`). The activity level of a People
    object is the heat of an activity that the user knows in met, which the documentation of EnergyPlus relates with
    58.2 W/m² and 1.8 m² (Input Output Reference 25.2, 1.14.2.1.10, as the decision of F1 records), the convention of
    ISO 7730 and ASHRAE 55 and of the other hooks of accim; `set_tmp` takes the metabolic rate in met (its own body
    surface area changes nothing at 0.001 K, E-F1), and the SET of the database of the causal model was calculated with
    the metabolic rate of its records (the verdict on the SET of the indicators, below). So the metabolic rate of the
    hook must be that of the activity, and the 1.8258 m² are a detail of the Pierce model of EnergyPlus, which reads
    1.43 % less met from the same schedule. To do (the entry of E-F1 of `TODO.md`): E-F1 also with met =
    activity/(58.2·1.8258), which compares both models with the same inputs, and the effect of the convention of accim
    reported apart; the sentence of section 4.9.2 on "the body surface area of 1.8 m² with which EnergyPlus gives the
    activity per person" corrected (true of its Fanger and KSU models, not of its Pierce model); the entries of E-F1 and
    F1 of this file, sections 4.9.2 and 4.9.3, `CHANGELOG.md` and the values of `tests/core/test_pierce_set.py` updated.
    Done on 2026-11-12 (the entry "E-F1 measured again" above: the conversion changes the SET by 0.01 to 0.02 K on
    average).
  - **A2**: options (i) and (ii). (i) E-F1 is repeated at 1.1 and 1.2 met (for instance, 115 and 126 W/person) with both
    clothing levels, and `tests/core/test_pierce_set.py` takes the activity level as a parameter; until then, the
    statements of E-F1 and F1 ("within 0.2 K standing and 0.35 K sitting", −0.08 and −0.155 K) hold near 1 met only, and
    the documentation says so, and that the code of EnergyPlus 25.1 and 25.2 follows the program of ASHRAE 55-2017,
    Appendix D, whose real environment has no term of the activity in the convective coefficient, unlike its Engineering
    Reference (19.1.4, equations 19.27 and 19.28) and unlike pythermalcomfort. (ii) The reference SET of F1 and F3 is
    that of pythermalcomfort (the verdict on the SET of the indicators, below). The difference between the code of
    EnergyPlus and its Engineering Reference is worth an issue in the repository of EnergyPlus
    (NatLabRockies/EnergyPlus) once it is measured: its draft, with the measurement, is part of the task, and the author
    posts it. Measured on 2026-11-12 (the entry "E-F1 measured again" above): standing, the SET of pythermalcomfort is
    0.33 K below that of EnergyPlus at 1.1 met and 0.94 to 0.97 K at 1.2 met, and 0.05 to 0.06 K at the three activity
    levels without that term; the draft of the issue is `notes/BORRADOR_issue_EnergyPlus_SET_Pierce_2026-11-12.md`.
  - **A4**: option (ii). A model with the programs `ApplyHookSetpoints_<zone>` was prepared for a hook, and without it
    its results are those of the comfort standard of its zones, with the outputs of the hook at 0: `run_ep` raises a
    `ValueError` with the EMS backend (its default), which cannot run a hook, naming the models and
    `run_ep(backend='api', hooks=[...])`; with the API backend (`run_ep`, `run_simulation` and `run_simulations`), a
    warning when no hook that runs before the programs (`runs_before_programs`) is given. It completes the clear error
    that the prompt of F1 asked for comfort standard 24 without the API backend. The test of both backends without the
    hook (`test_without_the_hook_both_backends_give_the_same_results_with_comfort_standard_24`) checks the error and the
    warning instead. The EMS output of the timesteps without the setpoints of the hook, which the finding gives as
    optional, is not added: the models simulated out of accim stay documented (sections 4.9.1 and 4.9.3). Implemented
    on 2026-11-12 (`DEVLOG.md`; section 48 of `CAMBIOS_CODIGO_v1.2.0.md`), with the choices of the entry "The
    implementation of the decisions of 2026-11-12" at the top of this file.
  - **A8**: options (i) and (iii); option (ii) is not done in accim 1.2.0. `'window'` stays as decision 6 defines it (it
    is implemented and tested), as an experimental mode: section 4.2.7 and the docstring of
    `accim.sim.ems.drift_limiter` say that both setpoints follow the recent temperature of the zone itself, that the
    dead band is `delta_heat` + `delta_cool` at most (2 K by default), what that costs (the measurements of the finding:
    the heating energy of April of the sample model in Seville, from 125.9 to 32 488 kWh) and that the exposure can then
    drift by about (1 − `alpha_indoor`)·delta per day; `AddAccis` and `modify_accis` warn when a zone gets
    `drift_mode='window'`; and `'rate'` is the recommended mode (in the documentation, and in case (v) of the validation
    study). The reason: the source of F2 supports the rate (the changes of the setpoints spread over a couple of weeks:
    Parkinson et al., 2020, section 4.3.2), while the window and its 1.0 K have no source (they are values that the
    proposal of block F chose for the author to correct, §6.6), and no paper read gives another rule either, so a new
    definition would be an invented one. If the validation study needs a window, it is designed then with its authors.
    Implemented on 2026-11-12 (`DEVLOG.md`; section 50 of `CAMBIOS_CODIGO_v1.2.0.md`), with the measurements made
    again that day.
  - **A15**: options (i) and (ii). (i) Section 4.2.6 and the docstring of `accim.sim.ems.long_term_discomfort` say that
    `('en16798', category)` takes the two design values of Table B.2 (the minimum of the heating season, with about 1.0
    clo, and the maximum of the cooling season, with about 0.5 clo) as a constant range of all the timesteps, so the
    summer hours that are too cold and the winter hours that are too warm within it count as comfortable, and point to
    the overcooling indicator of F3. (ii) The source of the missing limits is the standard itself: EN 16798-1:2019,
    Table B.5 (see "What was checked" above). A seasonal range is another value of `long_term_range` (the constant one
    does not change), with the limits of that table and the season of each day from the running mean of the outdoor
    temperature of the standard, θrm: the heating season below 10 °C, the cooling season above 15 °C, and between them
    the lower limit of the heating season and the upper limit of the cooling season, as the note of the table allows
    (**[inferred]** from that note and from CEN/TR 16798-2:2019, 7.2.2 and the remarks on Figure B.1), in the EMS
    counters and in the functions of the postprocessing. A P2 task, not needed to release 1.2.0.
  - **A19**: option (ii). The minimum and the maximum are limits of the comfort band (finding B5-1: the minimum is a
    limit of the setpoint without the tolerance), so the thermostats get them with the tolerance, as every other
    setpoint of the ACCIS and as those of the hooks (decision 23 of G1): AHSTnoTol = max(AHSTnoTol, AHSTmin) and
    ACSTnoTol = min(ACSTnoTol, ACSTmax), as now, and AHST = max(AHST, AHSTmin + AHSTtol) and ACST = min(ACST, ACSTmax +
    ACSTtol), exact after the rounding (decision 21: the rounded setpoints are AHSTmin + AHSTtol and ACSTmax + ACSTtol
    where they bind). With the thermostat on the limit itself, the operative temperature settles on the limit of the
    band, and the hour counters, the long-term discomfort and the hours below the temperature of the minimum
    (`report_hours_below`, the use for which B5 was proposed) count the decimals of the control as discomfort, which is
    what the tolerance is for. The thermostats still respect the limits (0.1 K within them with the default tolerance),
    and nothing changes with `setpoint_tolerance=0`. The limits are new in 1.2.0, so no released output changes. The
    comparison of S1 follows it (its verdict below), and so do the documentation (section 4.2 and the module
    `accim.sim.ems.setpoint_limits`), check 5 of `verify_accim_simulation` and `tests/core/test_setpoint_limits.py`.
    Implemented on 2026-11-12 (`DEVLOG.md`; section 45 of `CAMBIOS_CODIGO_v1.2.0.md`), with the choices of the entry
    "The implementation of the decisions of 2026-11-12" at the top of this file.
  - **A24**: option (ii). Every zone of a model with the code of JPN Aqilah 2025 (its subprograms `SetAST_CS23_<chunk>`)
    gets the inputs `StaticAHST` and `StaticACST` in its program `SetInputData_<zone>`, with the defaults (20 and 28 °C)
    in the zones of the other comfort standards, which do not read them. The zones share those global variables, so a
    program that initialised them (option (iii)) would leave a zone switched by hand with the values of the zone that
    ran before it; and the documentation says that the models of `add_accis_to_idf` have the code of all the comfort
    standards, so they must work with any of them in any zone. The output IDFs of `add_accis_to_idf` change by two lines
    in each zone (the golden master s01–s06 and s09 updated, only additions; G4 already changed them, and comfort
    standard 23 is new in 1.2.0, so nothing released changes); the models of `AddAccis` with other comfort standards
    have not that code and do not change. It replaces the part of the decision of G4 that left the zones of the other
    comfort standards without the inputs, and the warning that session 3 wrote in section 4.2.1. Implemented on
    2026-11-12 (`DEVLOG.md`; section 46 of `CAMBIOS_CODIGO_v1.2.0.md`).
  - **A25**: option (i). When a call of `modify_accis` without `epw` writes again the programs of the outdoor metric of
    a model that began with the values of a weather file, and the model has zones of JPN Aqilah 2025, it gives the
    warning of RMOT (their code reads the RMOT of EnergyPlus again, about 21 % low on the first day), and those zones
    are left out of the warning of the metrics that begin with PMOT; documented in `modify_accis`. It is what accim does
    with the custom model in the same case (decision D3: without the weather file, the fallback, with a warning) and
    what G4 decided for 23 (RMOT without the weather file, with a warning): the fault is the missing warning and the
    wrong one. An error, or keeping programs that the call must write again (option (ii)), would treat these zones
    unlike those of the custom model. Implemented on 2026-11-12 (`DEVLOG.md`; section 49 of
    `CAMBIOS_CODIGO_v1.2.0.md`).

### 2026-11-11 — S4: how the indicators of the causal band are given with the SET of pythermalcomfort
- Context: decision 9 (provisional, the entry "F3: the SET of the indicators of the causal band" below; task S4 of
  `notes/COPILOT_SIGUIENTE_SESION.md`): keep the Pierce SET of EnergyPlus and add, behind an optional argument off by
  default, the same indicators with the SET of pythermalcomfort, through `set_of_results` (G3) and the inputs that
  E-F1 compared. It does not say where the argument goes, how the inputs of the occupants are given, where the
  conditions of the zones come from, nor how the rows of the CSV files are matched with those of the table.
- Why it matters: `set_of_results` takes constant inputs of the occupants (those of a hook), while E-F1 took the
  values of the schedules of the People objects in each timestep, as EnergyPlus does; and `Table` drops the mean
  radiant temperature and the relative humidity with `standard_outputs=True` (and adds them up over the timesteps of
  each hour with `frequency_agg_func='sum'`).
- Options considered: (i) the argument `pythermalcomfort_set` of
  `accim.data.postprocessing.indoor_adaptation.table_indicators` only (not of `Table` nor of the GUI): a dict with
  `met`, `clo`, `air_speed` and, optionally, `position` (the posture of the hooks by default), or a hook of the SET
  with them; the SET of `set_of_results` of the outputs *Zone Mean Air Temperature*, *Zone Mean Radiant Temperature*
  and *Zone Air Relative Humidity* of each zone, keyed by its name in the table, in each row of the CSV file of each
  simulation (the column `Source` with `.csv`, in the current folder), averaged over the rows of the CSV file of each
  row of the table (as `Table` averages the Pierce SET; the hour of each row as `Table` gives it); the columns
  `<zone>_Mean SET_pythermalcomfort (°C)`, `<zone>_Mean TSV_causal_pythermalcomfort` and `<zone>_Hours In / Above /
  Below Causal Band_pythermalcomfort (h)` and `(%)` after those of each zone and of the building; NaN, with a
  warning, for the zones without those outputs (such as those that `Table` names after their spaces); a `ValueError`
  if a CSV file is not found (implemented); (ii) the inputs of the occupants of each row from the schedules of the
  People objects (their outputs *Schedule Value*, as E-F1), which cases (iii) and (iv) of the validation study need
  (a seasonal clothing insulation, the dynamic clothing model): it needs those outputs requested and the People
  objects of each zone; (iii) an argument of `Table` too (and its box in the GUI); (iv) the conditions of the zones
  from the columns of the table.
- Owner: the author (with the answer of Ruiji Sun on decision 9).
- Provisional decision (pending author until 2026-11-12): option (i) implemented provisionally: off by default, the
  other indicators and the outputs do not change.
- Status: answered on 2026-11-12 (accepted as implemented, and option (ii) added; decided by Claude Code for the
  author).
- Verdict (2026-11-12): option (i), accepted as implemented and no longer provisional, with option (ii) as another value
  of the same argument; options (iii) and (iv) are not done. With the verdict on the SET of the indicators (the entry of
  F3 below), the indicators of `pythermalcomfort_set` are those of reference of the causal band, so they must be able to
  take the inputs of the occupants that the hook of comfort standard 24 takes: besides constant inputs (a dict, or a
  hook), the values of the People objects of each zone in each row of the CSV file (their activity level, clothing
  insulation and air velocity, as E-F1 read them and as the hook reads them with `met`, `clo` and `air_speed` None),
  which cases (iii) and (iv) of the validation study need; the outputs that it needs are requested with those of
  `add_thermal_comfort_outputs`. The argument stays in `table_indicators`: `Table(indoor_adaptation_indicators=True)`
  keeps giving the indicators that need nothing but EnergyPlus, and neither `Table` nor the GUI get the argument (option
  (iii)) until someone needs it; and the conditions of the zones are not taken from the columns of the table (option
  (iv)), which drop the mean radiant temperature and the relative humidity and add up the timesteps of each hour.

### 2026-11-11 — S1: the details of the comparison of the minimum and maximum with the setpoints of the comfort model
- Context: decision 19 (the verdicts of 2026-11-11 in [[decisions.md]]; task S1 of `notes/COPILOT_SIGUIENTE_SESION.md`)
  replaces the comparison with `ACSTaul`/`AHSTall` by option (ii): with the weather file, the setpoints of the comfort
  model of each zone with `accim.sim.preview.compute_setpoints`, and a warning for each zone whose minimum is at or
  above the lowest cooling setpoint, or whose maximum is at or below the highest heating setpoint, with the value, the
  first date and the number of days; the zones that `compute_setpoints` does not cover are left out with a debug
  message. It does not say which setpoints, which days, nor when `modify_accis` compares them.
- Why it matters: what the warning reports, and when it is given.
- Options considered: (i) the setpoints of the thermostats (`ACST`/`AHST`, with the tolerance, rounded: where they
  cross, the heating setpoint of the thermostats is at or above the cooling one), by timestep, with the timesteps per
  hour of the model, from the first day of its first `RunPeriod` to its last day (to the end of the year if the run
  period goes on in the next one), including the first timestep of the run period, whose running means are 0 in the
  EMS as in EnergyPlus; `modify_accis` compares whenever the model has a minimum or a maximum (given in the call or
  before) and `epw` is given; the zones left out: those whose setpoints a hook gives and those with the limiter of the
  drift of the setpoints (their setpoints are not those of `compute_setpoints`), and those whose arguments it rejects
  (with the debug message of the logger `accim.sim.ems.setpoint_limits`, the first use of `logging` in accim)
  (implemented); (ii) the setpoints without the tolerance (`ACSTnoTol`/`AHSTnoTol`, the comfort band), which cross
  later; (iii) the whole year of the weather file, whatever the run period; (iv) leave out the first timestep of the
  run period.
- Owner: the author.
- Provisional decision (pending author until 2026-11-12): option (i) implemented provisionally
  (`accim.sim.ems.setpoint_limits.warn_crossed_setpoint_limits`): it only adds warnings.
- Status: answered on 2026-11-12 (accepted as implemented, with the change of the verdict of finding A19; decided by
  Claude Code for the author).
- Verdict (2026-11-12): option (i), accepted as implemented, with the change that the verdict of finding A19 brings. The
  thermostats are what EnergyPlus gets, so the setpoints compared are theirs (with the tolerance, rounded), not the
  limits of the comfort band (option (ii)); the days are those of the run period of the model, which is what is
  simulated (option (iii) would warn of days that the model does not simulate); and the first timestep stays (option
  (iv) would hide a crossing that the EMS of the simulation gives too, with the same running means of 0). With the
  verdict of A19 (the entry of the self-audit above), the heating setpoint of the thermostat on the minimum is AHSTmin +
  AHSTtol and the cooling one on the maximum is ACSTmax + ACSTtol, so the warning compares these values with the cooling
  and heating setpoints of the comfort model.

### 2026-11-11 — Comfort standards 9 and 10 (IND IMAC R 7DRM and 30DRM): their running means, and the heating setpoint of 9 in comfort mode 1
- Context: the review of Claude Science of 2026-11-11 (`notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §2.1)
  checked the source of comfort standards 9 and 10, Rawal et al. (2022), Building and Environment 219, 109187
  (doi:10.1016/j.buildenv.2022.109187), Fig. 15: model A, Tneut = 0.39·Tout-7DRM + 18.42, with the simple mean of the 7
  previous days (the paper tells it apart from the weighted one, Tout-7DRM-W), and model B, Tneut = 0.42·Tout-30DRM +
  17.60. In accim the coefficients, the bands and the applicability limits are right, but the metrics are swapped: 9
  (7DRM) uses PMOT, the simple mean of 30 days of EnergyPlus, and 10 (30DRM) uses RMOT, the exponential running mean
  with α = 0.8 of EnergyPlus (`SetComfTemp` uses PMOT for both). In comfort mode 1 of 9, out of the applicability
  limits, the heating setpoint is `PMOT*0.078+23.25+2.72` (category 80) or `+1.5` (90), that of cooling, where comfort
  mode 0 of 9 and comfort mode 1 of 10 use the minus sign. The static equation 0.078·T + 23.25 could not be verified
  (it is not in Manu et al., 2016; probably the National Building Code of India 2016, not in the library). The
  analysis is in the entry of `TODO.md`.
- Why it matters: the setpoints of 9 and 10 follow other outdoor temperatures than those of their models, and the
  heating and cooling setpoints of 9 in comfort mode 1 are equal (but the tolerances) out of the limits; fixing them
  changes the results of 9 and 10 and their output IDFs.
- Options considered: (i) the recommendation of the review: 10 with PMOT (exactly the 30DRM); 9 with the arithmetic
  mean of the 7 previous days of the machinery of B1 (`'ndrm'`, 7 days, started from the weather file; without it, the
  start of B1); `SetComfTemp`, the setpoints and `CountHours` consistent; the minus sign in comfort mode 1 of 9; the
  golden master updated; `CHANGELOG.md` (Fixed) with a note of migration (the results published with accim 1.1.0 or
  earlier are reproduced with those versions); and, with the metrics corrected, the outdoor mean of the static line
  checked in its source (in 10 it reads RMOT today); (ii) keep them as they are, documented; (iii) fix the sign only.
- Owner: the author.
- Provisional decision (pending author until 2026-11-12): the author decided on 2026-11-11 not to change them in session
  3 (`notes/COPILOT_SIGUIENTE_SESION.md` §2, rule 7): nothing was changed.
- Status: answered on 2026-11-12 (option (i); decided by Claude Code for the author).
- Verdict (2026-11-12): option (i), the whole recommendation of the review, in accim 1.2.0. Checked again in Rawal et
  al. (2022) (see "What was checked" above): model A (0.39·T + 18.42) is defined with the 7-day running mean of the
  outdoor temperature and model B (0.42·T + 17.60) with the 30-day one, neither of them weighted, so comfort standard 10
  reads `PMOT` (the 30-day mean of EnergyPlus) and 9 the arithmetic mean of the 7 previous days of the machinery of B1
  (`'ndrm'` with 7 days, beginning with the values of the weather file; without it, the start of B1, with its warning);
  `SetComfTemp`, the setpoints and `CountHours` agree; the heating setpoint of comfort mode 1 of 9 out of the limits
  takes the minus sign; and the line 0.078·T + 23.25 reads `PMOT` in 10 too, as in 7, 8 and 9 (the 30-day running mean
  of the model of the air-conditioned buildings of the National Building Code of India 2016, according to secondary
  sources: to be checked in the code if the author gets it). Keeping them (option (ii)) would leave two comfort
  standards that do not follow the models of their names, and the sign alone (option (iii)) would leave the metrics. The
  golden master is updated, and `CHANGELOG.md` (Fixed) has the note of migration: the results of comfort standards 9 and
  10 change, and those published with accim 1.1.0 or earlier are reproduced with those versions. Rule 7 of the
  instructions of session 3, with which the author kept them unchanged, was for that session only.
- Implemented on 2026-11-12 (`DEVLOG.md`; `CHANGELOG.md`, Fixed; section 44 of `CAMBIOS_CODIGO_v1.2.0.md`;
  `tests/core/test_imac_r.py`), with the choices of the entry "The implementation of the decisions of 2026-11-12" at
  the top of this file.

### 2026-11-10 — F3: the SET of the indicators of the causal band
- Context: the proposal of block F (§4 F3) asks for the hours within the causal band of every model; the SET can be
  that of the Pierce model of EnergyPlus (any model, with the outputs of `add_thermal_comfort_outputs`) or that of
  pythermalcomfort of the hook of comfort standard 24 (`SET_<zone>`, only in its simulations).
- Why it matters: the SET of the hook is 0.08–0.155 K below that of EnergyPlus on average (E-F1, F1), so the hours of
  the band of a simulation of comfort standard 24 differ slightly between both.
- Options considered: (i) the SET of EnergyPlus for every simulation (implemented: the same measure for every model;
  the hook still reports its own hours, `HoursInCausalBand_<zone>`); (ii) the SET of the hook where it exists.
- Review (2026-11-11, the handoff of Claude Science, `notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §2.3 and
  §3, #9): pending a question for Ruiji Sun: the text of Sun, Brager & Schiavon (2026) does not say which
  implementation of the SET they used. Until the answer, keep the Pierce SET of EnergyPlus as the SET of the
  indicators, and report also the indicators of the SET of pythermalcomfort (recalculated with `set_of_results`):
  E-F1 measured differences of −0.045 K on average and 0.18–0.20 K at most standing, and −0.12 K and 0.32–0.34 K
  sitting, of the order of what moves the hours near the limits of the band of 19–28 °C. Done provisionally in
  task S4 of the session of 2026-11-11.
- Owner: the author, with Ruiji Sun.
- Provisional decision (pending author until 2026-11-12): option (i) implemented provisionally, and the indicators of
  the SET of pythermalcomfort as an option (task S4 of the session of 2026-11-11).
- Status: answered on 2026-11-12 (changed: the SET of pythermalcomfort is the reference; decided by Claude Code for the
  author).
- Verdict (2026-11-12): the reference SET of the causal band is that of pythermalcomfort (`set_tmp`) in every
  simulation, and the Pierce SET of EnergyPlus stays as the indicator that every model has without pythermalcomfort. The
  paper builds its model with the SET of the ASHRAE Global Thermal Comfort Database II, version 2.1, and describes no
  calculation of its own, and the script that makes that version of the database calculates its column `set` with
  `set_tmp` of pythermalcomfort, from the air and mean radiant temperatures, the air speed, the relative humidity, the
  metabolic rate and the clothing insulation of each record, with the defaults of the function, and the earlier paper of
  the same authors took that column as its SET (see "What was checked" above): so that is the SET of the paper
  (**[inferred]**: its authors are of the Center for the Built Environment, which maintains both the database and
  pythermalcomfort). Hence: comfort standard 24 is right as it is (its hook inverts the SET of pythermalcomfort); the
  indicators of reference of the causal band are those of the SET of pythermalcomfort (the outputs of the hook in the
  simulations of comfort standard 24, and `table_indicators(..., pythermalcomfort_set=...)` in any simulation: the
  verdict of S4 above), and the validation study reports them, with those of the Pierce SET beside them; the Pierce SET
  approximates it near 1 met (E-F1: within 0.2 K standing) and is higher above about 1.05 met, where the code of
  EnergyPlus has not the term of the activity of the convective coefficient (finding A2: tenths of a kelvin at 1.1 and
  1.2 met, to be measured; measured on 2026-11-12, 0.33 K at 1.1 met and 0.94 to 0.97 K at 1.2 met, standing: the entry
  "E-F1 measured again" above; the causal TSV changes by 0.11 per kelvin). No output or column changes its name, and
  `Table(indoor_adaptation_indicators=True)` does not change; the documentation (sections 4.7.6, 4.9.2 and 4.9.3) and
  the docstrings stop calling the indicators of pythermalcomfort provisional, and say which SET is the reference. The
  database calculated its SET with the default posture of `set_tmp` (standing), and the hooks of accim sit the occupants
  with 1.2 met or less (the decision of G3, not reopened), 0.03 to 0.07 K lower: it is documented, and
  `position='standing'` gives that of the database. The confirmation of Ruiji Sun is still worth asking (that the SET of
  the paper is the column `set` of the database), but nothing waits for it: with another answer, this verdict is
  reviewed.

### 2026-11-10 — F3: the static reference of case (i) of the validation study
- Context: the design of the study (§4 F3) has the case "(i) referencia estática PMV (24–26 / 20–22 °C)".
- Why it matters: accim has the PMV setpoints of `apply_pmv_setpoints` (category II: −0.5 and 0.5), the static
  setpoints of comfort mode 0 of the comfort standards (those of ISO 7730 of categories 80 and 90 are 25 and 27 °C or
  24 and 26 °C for cooling, and 19 and 22 °C or 20 and 23 °C for heating), and fixed thermostats.
- Options considered: one of them, or fixed setpoints of 24–26 °C and 20–22 °C (which accim would set with the static
  setpoints of a comfort standard defined by its data, section 4.2.5).
- Review (2026-11-11, the handoff of Claude Science, `notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §3, #12):
  a decision of the author with Ruiji Sun. Recommendation: (a) the PMV setpoints of `apply_pmv_setpoints`,
  category II (±0.5), as the reference of a "fixed PMV" (question 1 of `01_informe/propuesta_paper_RuijiSun_v02.md`
  of the folder *Indoor adaptive setpoints* of the author); (b) besides, fixed static setpoints of EN 16798-1:2019,
  Table B.2, category II (offices, 20 and 26 °C).
- Owner: the author, with Ruiji Sun.
- Provisional decision (pending author until 2026-11-12): section 4.7.6 of the detailed use lists the first two; no
  simulation run (`TODO.md`).
- Status: answered on 2026-11-12 (both references of the recommendation of the review; decided by Claude Code for the
  author).
- Verdict (2026-11-12): both references of the recommendation of the review, as the position of the author for the study
  (to be agreed with Ruiji Sun before its simulations; nothing of accim 1.2.0 depends on it): (a) the PMV setpoints of
  `apply_pmv_setpoints`, category II (PMV ±0.5), the "fixed PMV" reference, which is the comparison of the paper itself
  (it measures its band against that of the PMV model, 24 to 26 °C, §4.3); and (b) fixed setpoints of 20 and 26 °C (EN
  16798-1:2019, Table B.2, category II: the minimum of the heating season and the maximum of the cooling season,
  which are also the lower limit of the heating range and the upper limit of the cooling range of its Table B.5 for the
  energy calculations), the usual static baseline, which accim sets as the static setpoints of a comfort standard
  defined by its data (section 4.2.5) in comfort mode 0. The static setpoints of comfort mode 0 of the built-in comfort
  standards are not a reference of the study. The other choices of the study that the review proposed are taken with it
  (the entry of the study in `TODO.md`): the climates, Seville and a hot and humid one, Singapore, unless Ruiji Sun
  prefers a humid one with a heating season (Shanghai or Ningbo); the clothing insulation by season of case (iii), 1.0
  and 0.5 clo with the cooling season from day 121 to 274, and the dynamic clothing model as a sensitivity; and the air
  speeds of case (iv), 0.6, 0.9 and 1.2 m/s (those of Table B.4 of EN 16798-1) in the occupied hours of the cooling
  season, besides 0.1 m/s.

## 2026-11-11 — The verdicts on the 23 provisional decisions of the session of the review v04

- **Status**: accepted (the verdicts of the review of Claude Science of 2026-11-11,
  `notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §3, made binding by the task of the author of 2026-11-11,
  `notes/COPILOT_SIGUIENTE_SESION.md` §1 and §4)
- **Context**: the session of the review v04 (2026-11-10 and 2026-11-11,
  [[INFORME_SESION_v1.2.0_2026-11-10_2.md]]) left 23 decisions taken provisionally in [[questions.md]], each with the
  most conservative, backward-compatible option. The review of Claude Science of 2026-11-11 gave a verdict on each
  one (handoff §3): accept as implemented (some with an instruction), change, or wait for the author with Ruiji Sun.
- **Decision**: 18 are accepted as implemented, four of them with an instruction done in task S5 of the session of
  2026-11-11: #1 (H6, an example of a clothing function of the column `'Tout'`), #7 (H2, the absolute path of the CSV
  file of T0, and a relative mode as a P2 entry of `TODO.md`), #16 (F1, a clear error for comfort modes 0 and 3 of
  comfort standard 24) and #22 (G4, the one-day delay of the native RMOT in the first timestep of each day); 3 are
  changed: #13 (F2, the reference of the rate: task S3), #19 (G5, the warning of verdict 13: task S1) and #20 (G5, the
  static setpoints of Qatar: task S2); #9 (F3, the SET of the indicators) and #12 (F3, the static reference of case (i)
  of the validation study) stay open in [[questions.md]], pending the author with Ruiji Sun (#9 done provisionally in
  task S4; both decided on 2026-11-12: the decisions of 2026-11-12 above). The 21 entries of [[questions.md]] are below,
  moved as they were, with their verdicts (numbered as in the handoff §3, in the order of [[questions.md]], newest
  first).
- **Consequences**: the decisions of 2026-11-10 that said "provisional" are final, but for the changed details (tasks
  S1 to S3, and the instructions of S5) and the two open questions; the tasks are those of
  `notes/COPILOT_SIGUIENTE_SESION.md` §6.

### 2026-11-10 — H6: the outdoor temperature of the functions of the clothing insulation, and their CSV files
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
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`accim.sim.apmv.clothing_insulation_values`).
- Status: answered on 2026-11-11 (accepted with an instruction; handoff §3, #1).
- Verdict (handoff §3, #1): Accepted, with an instruction: add to the documentation an example of a clothing function that uses the column `'Tout'`, for the models of the outdoor air temperature at 6 a.m. (Schiavon & Lee 2013, equation 4; ASHRAE 55-2020, Figure 5-1); done in task S5 of the session of 2026-11-11.

### 2026-11-10 — H5: the schema of the key regimes of the YAML files of the comfort standards
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
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`accim.sim.standards.definition_from_mapping` and
  `ComfortStandardDefinition`).
- Status: answered on 2026-11-11 (accepted; handoff §3, #2).
- Verdict (handoff §3, #2): Accepted: a comfort standard must not depend on the script type (the HVAC system of the model).

### 2026-11-10 — H5: the EMS code of a comfort standard with regimes
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
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`accim.sim.ems.standard_lines.uses_regimes`).
- Status: answered on 2026-11-11 (accepted; handoff §3, #3).
- Verdict (handoff §3, #3): Accepted as implemented.

### 2026-11-10 — H5: the outdoor metric of a regime in the outputs, and the programs kept
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
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`accim.sim.ems.outdoor_metric.zone_program_lines`).
- Status: answered on 2026-11-11 (accepted; handoff §3, #4).
- Verdict (handoff §3, #4): Accepted as implemented.

### 2026-11-10 — H3: the building type of long_term_range in categories III and IV
- Context: the decision of C2-1 (v04 §3.3, task H3) is `long_term_range=('en16798', category)`, with the constant
  limits of EN 16798-1:2019, Table B.2 (`accim.constants.EN16798_TABLE_B2`), whose minimum for heating differs between
  the residential and the office buildings in categories III (18.0 and 19.0 °C) and IV (16.0 and 18.0 °C).
- Why it matters: with `('en16798', 3)`, the lower limit is not defined by the category alone.
- Options considered: (i) `('en16798', category)` for categories I and II, whose limits are the same for both types,
  and `('en16798', category, building_type)` for any category, with a `ValueError` that lists both limits when the type
  is missing in categories III and IV (implemented: no limit is chosen for the user); (ii) the residential limits by
  default; (iii) the office limits by default.
- Owner: the author.
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`accim.sim.ems.long_term_discomfort.long_term_limits`).
- Status: answered on 2026-11-11 (accepted; handoff §3, #5).
- Verdict (handoff §3, #5): Accepted: no limit is chosen for the user.

### 2026-11-10 — H3: the range of Method C on the scale of the PMV, and its output
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
- Provisional decision (pending author until 2026-11-11): option (i), one output per zone without the building and the parametric argument implemented
  provisionally (`accim.sim.pmv_index.ppd_weighted_hours_lines`).
- Status: answered on 2026-11-11 (accepted; handoff §3, #6).
- Verdict (handoff §3, #6): Accepted: consistent with how the thermostats get their PMV setpoints.

### 2026-11-10 — H2: where the CSV file of T0 of te_ref_nl is written
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
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`accim.sim.schedule_files`).
- Status: answered on 2026-11-11 (accepted with a note; handoff §3, #7).
- Verdict (handoff §3, #7): Accepted, with a note: document that the absolute path breaks when the IDF is simulated on another computer, and an optional relative mode in the future (a P2 entry of `TODO.md`); done in task S5 of the session of 2026-11-11.

### 2026-11-10 — H2: which models get the Schedule:File of T0
- Context: the programs of the outdoor metric of a model have the branch of every metric, and the parametric module
  changes the metric of the zones without the weather file (`param_accis.modify_CustAST_metric`).
- Why it matters: a model made with another metric and `epw` has no schedule; if a sample gives its zones
  `te_ref_nl`, T0 cannot be that of the day.
- Options considered: (i) the schedule only when a zone has `te_ref_nl` and the weather file is given, and programs
  that begin with the values of a weather file but do not read the sensor are written again, beginning with PMOT, with
  the warnings (implemented: the output IDFs of the other metrics do not get a schedule and a CSV file); (ii) the
  schedule in every model with the outdoor metric and the weather file.
- Owner: the author.
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally.
- Status: answered on 2026-11-11 (accepted; handoff §3, #8).
- Verdict (handoff §3, #8): Accepted as implemented.

### 2026-11-10 — F3: the definition of the overcooling
- Context: the proposal (§4 F3, a design decision) counts the "occupied hours with the operative temperature below the
  reference heating setpoint or, following Parkinson 2021, below 22 °C in the cooling season", without fixing the
  season of the first variant nor the reference setpoint.
- Why it matters: in the heating season, the hours below a heating setpoint are underheating, not overcooling.
- Options considered: (i) both variants in the cooling season of the ACCIS (from `cooling_season_start` to the day
  before `cooling_season_end`, 121 and 274 by default, by the date of each row), with one threshold: 22 °C by default,
  or the reference heating setpoint given as `overcooling_temperature` (implemented); (ii) the first variant in all
  the occupied hours; (iii) the hours of the cooling season defined by the operation of the cooling system.
- Owner: the author.
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally.
- Status: answered on 2026-11-11 (accepted; handoff §3, #10).
- Verdict (handoff §3, #10): Accepted as implemented.
- Note (finding A13 of the self-audit of 2026-11-11): the source of the 22 °C is Parkinson, de Dear & Brager (2020),
  Energy and Buildings 206, 109559, section 4.3.2 (the typical summer setpoint of the air-conditioned offices,
  "current summertime practices (~22 °C)"); Parkinson, Schiavon, de Dear & Brager (2021), Scientific Reports 11, the
  "Parkinson 2021" of the proposal, studies the overcooling but gives no temperature threshold. The value stays a
  design decision; the docstrings and section 4.7.6 cite the 2020 paper since then.

### 2026-11-10 — F3: T_rm_in and the band of Tn_exp
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
- Provisional decision (pending author until 2026-11-11): options (i) implemented provisionally; the coefficients of the air-conditioned buildings (AC) by
  default, as the proposal.
- Status: answered on 2026-11-11 (accepted; handoff §3, #11).
- Verdict (handoff §3, #11): Accepted: keep the mark of "inferred" of the band of 2.5 K.

### 2026-11-10 — F2: the setpoint "applied the previous day" of the rate
- Context: decision 6 of block F: with `drift_mode='rate'`, |setpoint(d) − setpoint_applied(d − 1)| ≤ `max_drift_rate`
  and "the state is the applied setpoint of the previous day". The setpoints of the ACCIS change in each timestep (the
  first timestep of each day reads the running mean of the day before, and those of the hooks follow the humidity
  and the mean radiant temperature), so "the setpoint of the previous day" needs a definition.
- Why it matters: it sets the reference of the limit of each day.
- Options considered: (i) the setpoint applied by the limiter in the last timestep of the previous day (implemented;
  for the adaptive setpoints, that of the whole day); (ii) the mean of the setpoints applied in the occupied
  timesteps of the previous day; (iii) that of its last occupied timestep.
- Owner: the author.
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`DriftLastAHST_<zone>` → `DriftRefAHST_<zone>` at the change of
  DayOfYear), heating and cooling each one.
- Status: answered on 2026-11-11 (changed; handoff §3, #13).
- Verdict (handoff §3, #13): Changed: the reference of the daily limit of the rate is the mean of the setpoints applied in the occupied timesteps of the previous day (option (ii)), for each limited setpoint as before: the same for setpoints constant within the day (the ACCIS without hooks), and more representative for those of the hooks, which vary within the day; the days without occupied timesteps keep the reference of the last occupied day (#14); done in task S3 of the session of 2026-11-11.
- Implementation (task S3, 2026-11-11): `DriftSumAHST_<zone>` and `DriftSumACST_<zone>` add the setpoints applied
  in the occupied timesteps (counted by `n_occ_<zone>`, as T_rm_in); at the change of DayOfYear, if the day had
  occupied timesteps, `DriftRefAHST_<zone>`/`DriftRefACST_<zone>` are their means; `DriftLast*` removed (see the
  entry of S3 in [[../DEVLOG.md]]).

### 2026-11-10 — F2: the days without occupied hours in the running mean T_rm_in
- Context: T_rm_in(d) = (1 − alpha_indoor)·T_occ_mean(d − 1) + alpha_indoor·T_rm_in(d − 1), with T_occ_mean the mean
  operative temperature of the occupied hours; a day without occupants (a weekend) has no T_occ_mean.
- Why it matters: with offices, two days a week.
- Options considered: (i) T_rm_in does not change after a day without occupied hours (implemented: the occupants were
  not exposed); (ii) the mean of all the hours of that day; (iii) the decay of T_rm_in towards 0 (not meaningful).
- Owner: the author.
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally.
- Status: answered on 2026-11-11 (accepted; handoff §3, #14).
- Verdict (handoff §3, #14): Accepted: without exposure, no change.

### 2026-11-10 — F2: the parameter drift_mode of the parametric module and the limiter off
- Context: the parametric module takes numbers as options (as `custom_outdoor_metric`, which takes the codes of the
  metrics), and a plan may combine the limiter with its absence.
- Why it matters: `modify_accis` cannot remove the limiter (`None` keeps the arguments, as the minimum and maximum of
  B5), so a sample without it must turn it off in a model that has it.
- Options considered: (i) the codes 0 (none), 1 ('rate') and 2 ('window'), also their names; 0 sets `DriftMode = 0`
  in the zones that have the limiter (whose program then changes nothing) and does nothing in a model without it
  (implemented); (ii) the names only, without an option of none.
- Owner: the author.
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`param_accis.modify_DriftMode`).
- Status: answered on 2026-11-11 (accepted; handoff §3, #15).
- Verdict (handoff §3, #15): Accepted as implemented.

### 2026-11-10 — F1: the numbers of the comfort modes of comfort standard 24
- Context: the decision of the author names the comfort modes of comfort standard 24 'SET band' and 'SET neutral
  +/- offset' without numbers; the catalogue of accim (`accim.sim.standards.ComfortStandard.comfort_modes`) numbers
  them, and 0 means static setpoints in the other comfort standards.
- Why it matters: the number is part of the names of the output IDFs of the other comfort standards (`CM_`), and
  the parametric module numbers the comfort modes.
- Options considered: (i) 1 = 'SET band', 2 = 'SET neutral +/- offset' (implemented); (ii) 0 and 1; (iii) the names
  only.
- Owner: the author.
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`SUN2026_COMFORT_MODES`; the functions take the number or the
  name): 0 keeps its meaning of static setpoints.
- Status: answered on 2026-11-11 (accepted with an instruction; handoff §3, #16).
- Verdict (handoff §3, #16): Accepted, with an instruction: check that comfort modes 0 and 3 of comfort standard 24 give a clear error (and make them do so if they do not); done in task S5 of the session of 2026-11-11.

### 2026-11-10 — F1: the "CustAST_ACSTaul/all and AHSTaul/all limits" of the prompt of F1
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
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (it changes nothing in the ACCIS).
- Status: answered on 2026-11-11 (accepted; handoff §3, #17).
- Verdict (handoff §3, #17): Accepted: the model of Sun, Brager & Schiavon (2026) has no applicability limits of the outdoor temperature.

### 2026-11-10 — F1: the clothing insulation of the dynamic clothing model in the hook
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
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (it reads what EnergyPlus calculates).
- Status: answered on 2026-11-11 (accepted; handoff §3, #18).
- Verdict (handoff §3, #18): Accepted as implemented.

### 2026-11-10 — G5: the warning of verdict 13 compares the floor and ceiling with ACSTaul and AHSTall
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
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally
  (`accim.sim.ems.setpoint_limits.warn_crossed_setpoint_limits`, called by `AddAccis` and `modify_accis`): it is the
  text of the verdict and only adds a warning.
- Status: answered on 2026-11-11 (changed; handoff §3, #19).
- Verdict (handoff §3, #19): Changed: an error of v04 (handoff §2.2): `ACSTaul` and `AHSTall` are applicability limits of the outdoor metric, not setpoints, so comparing a limit of an indoor setpoint with them has no meaning. The literal comparison (option (i)) is removed and replaced by option (ii): with the weather file, the setpoints of the comfort model of each zone from `accim.sim.preview.compute_setpoints`, and a warning for each zone whose minimum heating setpoint is at or above its lowest cooling setpoint, or whose maximum cooling setpoint is at or below its highest heating setpoint; done in task S1 of the session of 2026-11-11.

### 2026-11-10 — G5: the static setpoints of the YAML file of Qatar (20 and 25.5 °C)
- Context: v04 §6.3 gives `static_setpoints: {heating: 20.0, cooling: 25.5}` for
  `qat_indraganti2018_hvac.yaml`, "EN 16798-1 Table B.2, offices, category II". In `accim.constants.EN16798_TABLE_B2`
  (UNE-EN 16798-1:2020, page 49, checked by `tests/core/test_setpoint_limits.py`), the offices of category II have 20
  and 26 °C; 25.5 °C is the cooling value of category I (21 and 25.5 °C).
- Why it matters: the value and its source disagree; comfort modes 0 and 1 of 102 use them.
- Options considered: (i) the numbers of v04 §6.3, 20 and 25.5 °C (implemented); (ii) category II of the table, 20 and
  26 °C; (iii) category I, 21 and 25.5 °C.
- Owner: the author.
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (the numbers of the decision; the YAML file notes the disagreement
  in a comment and its evidence says that they are a choice).
- Status: answered on 2026-11-11 (changed; handoff §3, #20).
- Verdict (handoff §3, #20): Changed to 20.0 and 26.0 °C (option (ii)): an error of v04 (handoff §2.2): EN 16798-1:2019, Table B.2 gives 20.0 and 26.0 °C for the offices of category II, and 25.5 °C is the cooling value of category I; done in task S2 of the session of 2026-11-11.

### 2026-11-10 — G5: the floor exact after the rounding, as the ceiling (B5-2)
- Context: finding B5-2 of v04 §3.3 asks to set `roundedACST = ACSTceil` where the ceiling bounds the cooling setpoint,
  since the strict rounding downwards gives one step of `SetpointAcc` below it, and says that the floor is exact. The
  floor is exact when its product by `SetpointAcc` is exact in binary (20 °C, or 25.5 °C with 10000); otherwise the
  strict rounding upwards gives one step above it (19.1 × 100 = 1910.0000000000002, so a floor of 19.1 °C gave 19.11 °C
  with an accuracy of 100).
- Why it matters: the heating setpoint bounded by the floor would be above the floor for some floors and accuracies.
- Options considered: (i) set `roundedAHST = AHSTfloor` where the floor bounds the heating setpoint too (implemented);
  (ii) only the ceiling, as written in the finding.
- Owner: the author.
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally: the program of the limits is new in 1.2.0, so no released output
  changes, and with the floors of Table B.2 and the default accuracy the result is that of option (ii).
- Status: answered on 2026-11-11 (accepted; handoff §3, #21).
- Verdict (handoff §3, #21): Accepted: symmetry with the maximum.

### 2026-11-10 — G4: the criterion of the test of JPN Aqilah 2025 against its YAML twin 101
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
- Provisional decision (pending author until 2026-11-11): option (i) implemented provisionally (`tests/core/test_jpn_aqilah2025.py`, thresholds unchanged), with the
  measured values in the test, `DEVLOG.md` and `notes/decisions.md`; with the weather file, 23 and 101 are identical in
  every timestep, which another test checks.
- Status: answered on 2026-11-11 (accepted with an instruction; handoff §3, #22).
- Verdict (handoff §3, #22): Accepted, with an instruction: document the one-day delay of the native RMOT in the first timestep of each day (it also affects comfort standard 1) where the test of 23 against 101 and comfort standards 1 and 23 are documented; done in task S5 of the session of 2026-11-11.

### 2026-11-10 — G1: the tolerance of the setpoints of the ACCIS with the setpoints of the hooks
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
- Provisional decision (pending author until 2026-11-11): option (i) decided provisionally: it is the only one in which the counters, the outputs and the floor
  and ceiling of B5 (D5) follow the hook in the same programs as the adaptive setpoints, and `setpoint_tolerance` keeps
  its meaning; `setpoint_tolerance=0` gives the thermostats the setpoints of the hook as they are (as before G1). It
  changes the thermostat setpoints of A4 and A6 (not released yet) by the tolerance (0.1 K by default), pending author.
- Status: answered on 2026-11-11 (accepted; handoff §3, #23).
- Verdict (handoff §3, #23): Accepted: the setpoints of a hook have the meaning of the adaptive setpoints (the setpoints without the tolerance are the limits of the comfort band).

## 2026-11-10 — The indicators of the adaptation to the indoor climate measure every model with the SET of EnergyPlus (F3)

- **Status**: accepted (task F3 of block F, `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §4 F3; the cooling effect of A6
  as an indicator, v04 §5 #35 and §6.8); the choices that the proposal does not fix were provisional in
  `notes/questions.md`: accepted on 2026-11-11 (the verdicts of 2026-11-11 above), but for the SET of the
  indicators and the static reference of case (i) of the study, decided on 2026-11-12 (the decisions of 2026-11-12
  above): the reference SET of the causal band is that of pythermalcomfort, and the Pierce SET of EnergyPlus of this
  decision stays as the indicator that every model has.
- **Context**: the article of validation of block F compares the setpoints of the comfort standards, of the causal SET
  model of comfort standard 24 and of the limiter of the drift in the same terms: the hours within the causal band, the
  overcooling, the neutrality by exposure and the cooling effect.
- **Decision**: a module of indicators, `accim.data.postprocessing.indoor_adaptation`, with functions of the rows of
  each timestep or hour (as those of the long-term discomfort, D1) and `Table(indoor_adaptation_indicators=True)`, an
  attribute with a row for each simulation; the SET of the indicators is that of the Pierce model of EnergyPlus, which
  any model reports with `accim.sim.people.add_thermal_comfort_outputs` (the models Fanger, Pierce and
  CoolingEffectASH55 of the People objects, and their outputs for each occupant instance); the cooling effect is the
  output of EnergyPlus (Engineering Reference 25.2, 19.1.9), not a setpoint; Tn_exp (Parkinson et al., 2020, Fig. 6)
  is only a diagnostic; the outputs of EnergyPlus get names in `Table` that no other name contains
  (`SET_Pierce (°C)`, `SET_Pierce_PMV`, `CoolingEffect (°C)`, `CoolingEffect_PMV`, `CoolingEffect_PPD`).
- **Consequences**: the indicators of the SET need the outputs of `add_thermal_comfort_outputs` before the simulations
  (without them, NaN and a warning); the indicators are those of the rows of the table (hourly means with hourly rows),
  and T_rm_in is calculated from them for every simulation; the study itself is a design (section 4.7.6 of the
  detailed use), whose simulations wait for choices of the author (`TODO.md`).

## 2026-11-10 — The limiter of the drift of the setpoints is an option of the ACCIS of each zone, in Erl (F2)

- **Status**: accepted (task F2 of block F; decisions 6 and 7 of the author of 2026-11-10,
  `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §6, copied here as the prompt of F2 asks, not reopened; since
  2026-11-12, `'window'` is an experimental mode, with a warning, and `'rate'` the recommended one: finding A8 in the
  decisions of 2026-11-12 above)
- **Context**: Parkinson, de Dear & Brager (2020), Energy and Buildings 206, 109559: the occupants adapt to the mean
  indoor temperature they are exposed to (Fig. 6), and the changes of the setpoints should be spread over days to
  weeks (section 4.3.2).
- **Decisions of the author (copied)**: (6) `drift_mode` None by default (the IDF and the results of every comfort
  standard unchanged); `'rate'`: |setpoint(d) − setpoint_applied(d − 1)| ≤ `max_drift_rate`, 0.5 K/day by default, the
  first occupied day without limit, and then the state is the setpoint applied the previous day; `'window'`: the
  target clipped to [T_rm_in − `delta_heat`, T_rm_in + `delta_cool`], 1.0 K each by default, T_rm_in(d) = (1 −
  `alpha_indoor`)·T_occ_mean(d − 1) + `alpha_indoor`·T_rm_in(d − 1) of the operative temperature of the zone in its
  occupied hours, `alpha_indoor` 0.8, inactive until one full occupied day, whose mean starts T_rm_in,
  `initial_T_rm_in` (None) overriding the start; the limiter applies to the heating and the cooling setpoints of any
  comfort standard (adaptive, PMV-derived temperatures and the SET of comfort standard 24); (7) only on request.
- **Implementation**: `accim.sim.ems.drift_limiter`: the inputs `DriftMode` (1 rate, 2 window, 0 none),
  `MaxDriftRate`, `AlphaIndoor`, `DeltaCool`, `DeltaHeat` and `InitTrmIn` of the zones with the limiter only
  (`accim.sim.ems.inputs`, optional); the program `ApplyDriftLimiter_<zone>`, run by `RunACCIS_<zone>` after `SetAST`
  and the program of a hook and before `SetASTnoTol` (so before the minimum and maximum of B5, "before the existing
  clipping" of the prompt), with the Erl accumulators `sum_T_occ_<zone>` and `n_occ_<zone>` (the operative
  temperature `<zone>_OpT` of the timesteps with `Occ_count_<zone>` > 0) flushed at the change of `DayOfYear`, out of
  the warm-up days (`WarmupFlag`, so the warm-up does not count, as decision 6 wants), without `TrendVariable`; the
  targets are the setpoints without the tolerance, and where the limiter changes them `AHST`/`ACST` get its setpoints
  plus the tolerance, rounded again; `InitDriftLimiter` at `BeginNewEnvironment`; the outputs `T_rm_in_<zone>`,
  `DriftTargetAHST_<zone>`, `DriftTargetACST_<zone>`, `DriftAppliedAHST_<zone>`, `DriftAppliedACST_<zone>`
  (averaged) and `DriftLimitedHours_<zone>` (summed). The setpoints of the PMV (`setpoint_type='pmv'`,
  `accim.sim.pmv_index`) have none (decision D5: they are not temperatures). Three choices that the decisions do
  not fix were provisional in `notes/questions.md` (the verdicts of 2026-11-11 above: two accepted, and the
  reference of the rate changed to the mean of the occupied timesteps of the previous day, task S3).
- **Consequences**: with `'window'`, both setpoints are clipped to the window, so the band is at most 2 K wide around
  T_rm_in: in the first 12 days of a run period from 1 April in Seville (the sample model, INT EN16798, category II,
  comfort mode 3, EnergyPlus 25.1), T_rm_in was 25.6–26.3 °C and the heating setpoint 24.6–25.3 °C instead of
  19–20.8 °C. `compute_setpoints` cannot calculate the limiter; `verify_accim_simulation` checks its targets.

## 2026-11-10 — Comfort standard 24, INT Sun2026 SET, is a thin layer on the hook of the SET by bisection (F1)

- **Status**: accepted (task F1 of block F; decisions 1 to 5 and 8 of the author of 2026-11-10,
  `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §6, copied here as the prompt of F1 asks, not reopened; the conversion
  of `tr_mode='zone'` is the decision of 2026-11-10 below; the plan of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md`
  §4.6: the hook of the SET generalised, and comfort standard 24 a thin layer on it)
- **Context**: the causal SET model of Sun, Brager & Schiavon (2026), Energy and Buildings 370, 118097, Fig. 7a:
  TSV = 0.11·SET − 2.6 (the band of TSV ±0.5 is 19.09 to 28.18 °C of SET, 19 and 28 °C in the paper; the neutral SET
  23.6 °C). EnergyPlus has no thermostat of the SET.
- **Decisions of the author (copied)**: (1) comfort standard 24, label `INT Sun2026 SET`, title `24 = INT Sun, Brager
  & Schiavon 2026 (causal SET band)`, with the comfort modes 'SET band' and 'SET neutral +/- offset'; (2) `tsv_limit`
  0.5 by default, 0.7 and 1.0 accepted with a warning (a linear extrapolation, SET = (±tsv_limit + 2.6)/0.11), and the
  categories 80 and 90 both give 0.5; (3) no own minimum: the common minimum of B5 (`heating_setpoint_minimum`, H1)
  after the inversion, None by default, with a warning when the inverted heating setpoint falls below 18 °C without
  it; (4) `tr_mode` 'zone' (default) or 'equal_air'; (5) the air speed, clothing insulation and metabolic rate of the
  schedules of the People object, no own air speed; (8) the names of H1.
- **Implementation**: `accim.sim.comfort_hooks`: `SetSetpointHook` takes `met`, `clo` and `air_speed` None (read from
  the People object of each zone in each timestep with the sensors `SET_Act_<zone>`, `SET_Clo_<zone>` or
  `SET_CloValue_<zone>` and `SET_CloMethod_<zone>`, and `SET_Vel_<zone>`; the activity level divided by 58.2 W/m²
  (Engineering Reference 25.2, equation 19.28) and 1.8 m² (Input Output Reference 25.2, 1.14.2.1.10)) and `tr_mode`;
  `Sun2026SetpointHook` (method 'bisection', 10–40 °C, 0.05 K) with the outputs `TSV_causal_<zone>` and
  `HoursInCausalBand_<zone>`; `apply_sun2026_setpoints` (also the Pierce model and its output);
  `accim.sim.standards.COMFORT_STANDARDS[24]` with `HOOK_COMFORT_STANDARDS`: no EMS code, so `AddAccis`,
  `modify_accis`, the EMS code and `compute_setpoints` reject it with a `ValueError` (the fallback of the EMS, v03
  A6a, is a P2 entry of `TODO.md`). The comfort modes are numbered 1 and 2, the "applicability limits" of the prompt
  are not applied to the setpoints of the SET, and the dynamic clothing model is read from its output: provisional
  decisions in `notes/questions.md`, accepted on 2026-11-11 (the verdicts of 2026-11-11 above).
- **Measurement (scope 6 of the prompt)**: the sample model with the ACCIS (INT EN16798, category II, comfort mode 3,
  `vrf_ac`, a minimum heating setpoint of 18 °C in Block1:Zone1), Seville, EnergyPlus 25.1, 6 timesteps per hour,
  the inputs of the People objects (1.06 met; 1.0 clo in winter, 0.5 clo in summer; 0.137 m/s), sitting (the posture
  of the hook with 1.2 met or less), `tr_mode='zone'`. Differences of the hourly means of `SET_<zone>` (the SET of
  the hook, with the values that its sensors read at the beginning of each timestep) minus the Pierce SET of
  EnergyPlus (K):

  | Week | Zone | Mean | Mean absolute | Maximum absolute |
  |---|---|---|---|---|
  | 8–14 January | Block1:Zone1 | −0.080 | 0.081 | 0.191 |
  | 8–14 January | Block1:Zone2 | −0.082 | 0.083 | 0.204 |
  | 15–21 July | Block1:Zone1 | −0.156 | 0.156 | 0.262 |
  | 15–21 July | Block1:Zone2 | −0.154 | 0.154 | 0.291 |

  Diagnostics: per timestep, the SET of the hook against the Pierce SET of the previous timestep (whose conditions its
  sensors read) differs by −0.080/−0.082 K (winter) and −0.156/−0.154 K (summer) on average, at most 0.27–0.40 K;
  computed standing (the posture of EnergyPlus), by −0.009/−0.010 K (winter) and −0.079/−0.078 K (summer), at most
  0.17–0.28 K, so the posture accounts for about 0.07 K, as in E-F1. Occupied hours within the band: 60 and 56.3 of 60
  in winter (the zone with the minimum of 18 °C, all), 27.8 and 34.3 of 60 in summer, when the VRF system of the sample
  model kept the operative temperature a median 0.45 and 0.71 K above the cooling setpoint in those hours (mean radiant
  temperature 5.8 and 4.7 K above the air temperature). The heating setpoints of the zone without minimum went down to
  16.0 °C in winter (the hook warns). `tests/core/test_sun2026_set.py` reproduces the table within 0.001 K.
- **Consequences**: the SET of the hook is lower than that of EnergyPlus by 0.08–0.16 K on average in these weeks
  (at most 0.29 K hourly), so the band of accim is reached at slightly warmer conditions than with the Pierce model;
  a paper with F1 should report the SET of both (the outputs of the hook and of the Pierce model are in every
  simulation of comfort standard 24).

## 2026-11-10 — The SET of EnergyPlus (Pierce) against that of pythermalcomfort, measured (E-F1)

- **Status**: accepted (task E-F1 of `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §3 and §5, and of the session of
  2026-11-10; a measurement, not a tolerance decided beforehand). Findings A1 and A2 of the self-audit of 2026-11-11
  (the decisions of 2026-11-12 above): this measurement holds near 1 met only (the code of EnergyPlus has not the term
  of the activity of the convective coefficient that the context below gives to its Pierce model, and that
  pythermalcomfort has), and its metabolic rate, converted with 1.8 m², is 1.43 % above that of the Pierce model
  (1.8258 m²); measured again on 2026-11-12, with 110.7, 115 and 126 W/person and both conversions (the entry "E-F1
  measured again" of that day, above), which keeps the values of this table for 110.7 W/person
- **Context**: F1 inverts the SET of pythermalcomfort (`set_tmp`, the code of ASHRAE 55) in the hook of the SET, while
  EnergyPlus reports the SET of its Pierce two-node model (Engineering Reference 25.2, 19.1.4: hc = max(8.6·v^0.53,
  5.66·(met − 0.85)^0.39) with v ≥ 0.137 m/s, radiative area 0.72 of the body, 1.8 m²). Block F asked to compare them,
  hour by hour, from the same outputs, before using F1 in a paper.
- **Measurement**: the sample model (`TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf`) with the ACCIS
  (`vrf_ac`, INT EN16798, category II, comfort mode 3) and Pierce in its People objects
  (`accim.sim.people.add_thermal_comfort_model`), a year in Seville (`Seville_Present.epw`), EnergyPlus 25.1, 6
  timesteps per hour; in each timestep, `set_tmp(tdb=Zone Mean Air Temperature, tr=Zone Mean Radiant Temperature,
  v=the air velocity schedule (0.137 m/s), rh=Zone Air Relative Humidity, met=activity schedule/(58.2·1.8) (110.7
  W/person, 1.057 met), clo=the clothing schedule (0.5 and 1.0), limit_inputs=False, round_output=False)` against
  `Zone Thermal Comfort Pierce Model Standard Effective Temperature` (the mean radiant temperature of the People objects,
  `EnclosureAveraged`, is that of the zone; the work efficiency schedule is 0; the output `Zone Thermal Comfort Clothing
  Value` was 0 in this run, so the schedule values were used). Differences of the hourly means (pythermalcomfort minus
  EnergyPlus), all the hours of the year (52 560 timesteps per zone):

  | Zone | Posture | Mean (K) | Mean absolute (K) | Maximum absolute (K) |
  |---|---|---|---|---|
  | Block1:Zone1 | standing | −0.045 | 0.056 | 0.180 |
  | Block1:Zone2 | standing | −0.045 | 0.056 | 0.196 |
  | Block1:Zone1 | sitting | −0.116 | 0.118 | 0.324 |
  | Block1:Zone2 | sitting | −0.116 | 0.117 | 0.344 |

  The differences of the timesteps are those of the hours to 0.001 K (standing: maximum 0.181 and 0.197 K, 95th
  percentile 0.144 and 0.149 K); in the occupied hours, the mean absolute differences are 0.076 and 0.073
  K (standing) and 0.160 and 0.154 K (sitting). The body surface area (1.8 or 1.8258 m²) and the barometric pressure of
  the site (99 900 to 103 200 Pa, or 101 325 Pa) do not change them at 0.001 K. Standing, the mean difference of the
  timesteps grows with the SET of EnergyPlus (Block1:Zone1 / Block1:Zone2): −0.007 / −0.008 K (22–24 °C), −0.014 /
  −0.012 K (24–26 °C), −0.045 / −0.043 K (26–28 °C), −0.094 / −0.096 K (28–30 °C) and −0.137 / −0.144 K (above 30 °C,
  maximum 0.181 / 0.197 K); −0.077 / −0.076 K with 0.5 clo and −0.014 K with 1.0 clo. The largest differences were in warm afternoons
  with the mean radiant temperature 7 K above the air temperature (Block1:Zone2, 29 July 17:20: SET 33.03 °C in
  EnergyPlus and 32.83 °C in pythermalcomfort).
- **Consequences**: the SET of accim (pythermalcomfort) is that of EnergyPlus within 0.2 K standing and 0.35 K sitting
  in this case, and slightly lower (so the setpoints of the SET of accim are slightly warmer than those that would give
  the same SET in EnergyPlus); F1 keeps the posture of the hook (sitting with 1.2 met or less, G3) and reports both
  SET; `tests/core/test_pierce_set.py` reproduces the table (within 0.001 K) and fails if EnergyPlus, pythermalcomfort
  or the model change it.

## 2026-11-10 — The minimum and maximum of the setpoints replace the floor and ceiling (H1)

- **Status**: accepted (task H1 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §7, §4.5; decision 8 of block F,
  `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §6)
- **Context**: `heating_setpoint_floor` could be read as a physical floor (a radiant floor); the names are public API
  of 1.2.0, so they change before the release.
- **Decision**: `heating_setpoint_minimum`/`cooling_setpoint_maximum` (EMS inputs `AHSTmin`/`ACSTmax`, parameter classes
  `HeatingSetpointMinimum`/`CoolingSetpointMaximum`, modifiers `modify_AHSTmin`/`modify_ACSTmax`, checks
  `Check5_AHSTmin`/`Check5_ACSTmax`); the old names of the arguments (also in `zone_arguments` and GUI sessions), of the
  parameters, classes and modifiers are deprecated aliases (`accim.sim.arguments.DEPRECATED_ARGUMENT_NAMES`, version
  1.2.0 in the warnings); the old EMS inputs are not read (only development builds had them). The prose of the code and
  the docs says "the minimum heating setpoint" and "the maximum cooling setpoint"; the program keeps its name
  `ApplySetpointLimits_<zone>`.
- **Consequences**: block F (F1, F2) uses the new names; models made with development builds of 1.2.0 that have
  `AHSTfloor`/`ACSTceil` must be made again.

## 2026-11-10 — The floor and ceiling bound the setpoints with and without the tolerance and are exact; the housekeeping of the review (G5)

- **Status**: accepted (task G5 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §7, findings A3-1, A3-2, B5-1 to B5-3,
  B1-2, B3-1 to B3-3, E4-1 to E4-3 and §3.4–§3.5, verdicts #3, #13, #26 and #28); three points were provisional
  (`notes/questions.md`: the literal reading of verdict #13 and the static setpoints of Qatar, changed by tasks S1
  and S2 of 2026-11-11; the exact floor, accepted: the verdicts of 2026-11-11 above). Changed in part on 2026-11-12
  (finding A19 in the decisions of 2026-11-12 above): where the minimum or the maximum binds, the thermostats get it
  with the tolerance, and the setpoints without the tolerance are the limit
- **Context**: the floor bounded only the setpoints with the tolerance (the comfort band of the counters was 0.1 K
  below it) and the strict rounding put the cooling setpoint one step below the ceiling; a key of the catalogue of the
  aPMV filled one side only; the YAML file of Qatar was incomplete; the outdoor metric could write `nan`; pyfwg added the
  urban heat island that Java does not.
- **Decision**: `ApplySetpointLimits_<zone>` runs right after `SetASTnoTol`, bounds `AHST`/`ACST`, rounds again, sets
  the rounded setpoints to the floor/ceiling where they bound them, and bounds `AHSTnoTol`/`ACSTnoTol` too; the line
  moves in the models of earlier builds of 1.2.0; `warn_crossed_setpoint_limits` warns if the floor is above `ACSTaul`
  or the ceiling below `AHSTall` (literal; replaced on 2026-11-11 by the comparison with the setpoints of the comfort
  model of each zone with the weather file, decision 19 of the verdicts of 2026-11-11 above, task S1).
  `adaptive_coefficients=<key>` gives both sides (`ValueError` with explicit
  values on a side); a key with the numeric default on the other side warns; with `'pmv_sign'` the setpoints must have
  their signs. One formatter of the numbers of the programs (`erl.format_number`), and a `ValueError` for a weather
  file without the 12 months. Qatar with the data of v04 §6.3 (its static setpoints 20 and 26 °C since decision 20 of
  2026-11-11, task S2); the categories in numeric order; a warning for the signs
  of the offsets. `fwg_add_uhi=False` unless given, a warning with `fwg_options_ensemble=0`, the cleanup after a
  `ValueError` of pyfwg. `processes=0` runs in the current process.
- **Consequences**: the hour counters, the long-term discomfort and the hours below some temperatures of the zones with
  a floor or a ceiling use the bounded band; check 5 of `verify_accim_simulation` checks the setpoints without the
  tolerance too; the output IDFs without a floor or a ceiling do not change (golden master byte-identical); the YAML
  101 gives the ApplyCAT lines of 23; the How-to notebook of the registry reads Qatar.

## 2026-11-10 — JPN Aqilah 2025 reads the running mean of EN 16798-1 of the weather file when the model has its values, and its static setpoints are inputs of its zones (G4)

- **Status**: accepted (task G4 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §7, findings B4-1 and B4-2, verdicts
  #29 and #30, decision §6.2); the criterion of its test was provisional (`notes/questions.md`;
  accepted on 2026-11-11, with the documentation of task S5: the verdicts of 2026-11-11 above). Changed in part on
  2026-11-12 (findings A24 and A25 in the decisions of 2026-11-12 above): every zone of the models with the code of 23
  gets the inputs of the static setpoints, and `modify_accis` warns when its zones go back to RMOT
- **Context**: comfort standard 23 read the RMOT of EnergyPlus, whose first value in a run period is not divided by
  1 − α⁷, and its static setpoints were literals. The author decided `rmot_alpha` from the weather file when `AddAccis`
  gets one (RMOT otherwise, with a warning) and the arguments `static_heating_setpoint`/`static_cooling_setpoint`
  (`StaticAHST`/`StaticACST`, 20.0/28.0). The EMS code of 23 is shared by all its zones (one branch of `SetComfTemp`),
  so the metric has to be a property of the model.
- **Decision**: the code of 23 reads `Tout_metric` exactly when the programs of the outdoor metric of the model begin
  with the values of a weather file (`epw` of `AddAccis` or `modify_accis`, or programs already written with it), and
  then its zones get the inputs of `rmot_alpha` with α 0.8 (`standard_lines.WEATHER_FILE_METRICS`,
  `outdoor_metric.outdoor_metric_needed`, `set_weather_file_lines`); otherwise RMOT, and the inputs of the outdoor metric
  of its zones are not used. The static setpoints are inputs of the zones of 23 only (other comfort standards ignore
  them), read in comfort modes 0 and 1 (D2: the static setpoints of the definition, those of both modes), declared as
  global variables in the models with the code of 23; in the parametric module they are written to all the zones, so
  that the order of the parameters of a sample does not matter.
- **Consequences**: with the weather file, 23 gives the setpoints of the YAML twin 101 from the first day; the models
  with the code of all the comfort standards (golden `s01`–`s06`, `s09`) changed by the static lines of 23 and their
  declaration; `compute_setpoints(outdoor_metric_start='epw')` (the default) gives the setpoints of 23 with the weather
  file. Measured: without it, 23 is 0.92/1.47/1.93 K lower on the first day (hours 2–24; starts 1 January, 1 April,
  1 July, Seville) and at most 0.028 K from day 21; the first hour of each day differs by up to 0.10 K for the timing of
  the readings (one timestep), not the transient.

## 2026-11-10 — The hook of the SET calculates by bisection in the callbacks on request, after calling pythermalcomfort before the API of EnergyPlus is loaded (G3)

- **Status**: accepted (task G3 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §7, findings A6-1 to A6-4, verdict #35;
  the rule of the session on `set_tmp` in the callbacks)
- **Context**: A6 tabulated the setpoints by humidity because `set_tmp` stopped EnergyPlus in the callbacks; the review
  ran it there with Python 3.12, and block F (F1) needs a SET whose inputs change in time. In this environment (Python
  3.14.3, numba 0.68.1), the first call of `set_tmp` in a process stops it with an access violation whenever the
  library of the API of EnergyPlus has been loaded before (inside a callback or not), and works when it is made before
  loading it; `NUMBA_DISABLE_JIT=1` makes pythermalcomfort 4.8.1 fail (`'function' object has no attribute 'py_func'`).
- **Decision**: `SetSetpointHook(method='table' | 'bisection')`, `'table'` by default; with `'bisection'`, the
  setpoints in each timestep and the output `SET_<zone>`; `prepare()` (one call with numbers, one with an array of two
  values), which `run_simulation` calls (`prepare_hooks`) before `load_energyplus_api`; `apply_set_setpoints` adds the
  sensors and the outputs of the mean air and radiant temperatures and the humidity, at the frequencies of the outputs
  of the ACCIS of the model by default; `set_of_results`; `position=None`: sitting with 1.2 met or less.
- **Consequences**: F1 builds on the bisection; the hooks with `prepare()` must run through `run_simulation` (or
  `run_ep`, whose processes are new); a process that has loaded the API of EnergyPlus before calling pythermalcomfort
  cannot calculate the SET in this environment.

## 2026-11-10 — The hooks of the setpoints run before the EMS programs and give their setpoints to the ACCIS through a program of each zone (G1)

- **Status**: accepted (task G1 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §7, option (a) of finding A4/A6-1; the
  tolerance decided provisionally, accepted on 2026-11-11: the verdicts of 2026-11-11 above); supersedes the way the hooks of A4 and A6 set the setpoints
  (the decisions of A4 and A6 of 2026-11-10 below)
- **Context**: the hooks of the ATHB and of the SET wrote the actuators of the setpoint schedules after the programs of
  the ACCIS, so its hour counters, the long-term discomfort of C2 and the outputs of the setpoints of the zones were
  those of the adaptive setpoints that the thermostats no longer followed. The counters run inside `RunACCIS_<zone>`,
  with the variables of the zone, after SetAST.
- **Decision**: option (a): the hooks run before the EMS programs (`runs_before_programs`, which `run_ep` routes to
  `before_programs`; as `after_programs` they stop the simulation) and set `HookAHST_<zone>`, `HookACST_<zone>` and
  `HookSetpoints_<zone>`; the program `ApplyHookSetpoints_<zone>` (`accim.sim.ems.hook_setpoints`), run by
  `RunACCIS_<zone>` right after SetAST (and before the floor and ceiling of B5), sets `AHST`/`ACST` to them plus the
  tolerance and rounds them, so SetASTnoTol, the counters, ApplyAST and the outputs follow the hook; `InitHookSetpoints`
  sets the flags to 0 at each new environment. Option (b) (counters of their own) was not needed.
- **Consequences**: the comfortable hours, the long-term discomfort and the outputs of the setpoints of the zones are
  those of the ATHB or the SET; the floor and ceiling of B5 bound them (D5); the thermostats get the setpoints of the
  hook with the tolerance of the setpoints of the zone; check 4 of `verify_accim_simulation` skips these zones; the
  comfort temperature and the applicability limits stay those of the comfort standard of the zone.

## 2026-11-10 — With tr_mode='zone', the inverted SET setpoint of air temperature is written as an operative-temperature setpoint

- **Status**: accepted (the author, in the task of the session of 2026-11-10, answering the open question of
  `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §4.4)
- **Context**: the SET setpoints of A6 are operative temperatures with the air and mean radiant temperatures equal
  (tr = ta = Top), written to the dual setpoint thermostats of the ACCIS, which control the operative temperature with
  the radiative fraction 0.5 (`TypOperativeTempControlSch`, 0 on the design days). F1 (decision 4 of block F,
  `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §6) solves the air temperature whose SET is the target with the mean
  radiant temperature of the zone (`tr_mode='zone'`, the default) or with tr = ta (`tr_mode='equal_air'`); v04 §4.4
  asked which thermostat receives the air-temperature setpoint.
- **Decision**: with `tr_mode='zone'`, the inverted air-temperature setpoint ta_sp is converted to an
  operative-temperature setpoint, Top_sp = (ta_sp + tr_zone)/2, with the mean radiant temperature of the zone of the
  previous timestep (that of the sensors of the hooks), and written to the operative-temperature thermostat that the
  ACCIS already actuates (`AHST_Act_<zone>`, `ACST_Act_<zone>`); with `tr_mode='equal_air'`, the solution of the
  bisection (ta = tr = Top) is written as it is (the behaviour of A6).
- **Consequences**: no new thermostat, actuator or HVAC change; the conversion uses the same weighting as the
  thermostats (0.5), and lags the mean radiant temperature by one timestep, as every input of the hooks.

## 2026-11-10 — The decisions of the author on the blocked tasks of 1.2.0 and the name of the setpoint limits of B5

- **Status**: accepted (the author, `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §4.5 and §6, made binding by the task of
  the session of 2026-11-10; §4.5 is decision 8 of block F, `notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md` §6)
- **Context**: the session of the proposals of 1.2.0 left eight tasks of `TODO.md` blocked on the author, and A5 (the
  clothing as a function of the outdoor temperature) waiting for him; block F asked to rename the floor and ceiling
  of B5.
- **Decision**:
  - B2, an outdoor metric for each regime (§6.1): the conditions of all the regimes are evaluated with the metric of
    the zone (`CustAST_metric`), and the selected regime can set its own metric (`outdoor_metric`, `alpha`, `days`; the
    zone's when None) to calculate `ComfTemp`: `SetOutdoorMetric` calculates every distinct metric of the regimes of
    the zone (a variable `Tout_metric_<k>` for each one), and `SelectCustomRegime_<zone>` copies that of the selected
    regime into `Tout_metric`. P2.
  - B4, the static setpoints of JPN Aqilah 2025 (§6.2): new arguments `static_heating_setpoint` and
    `static_cooling_setpoint` (20.0 and 28.0 by default; EMS keys `StaticAHST`/`StaticACST`) of `AddAccis`,
    `modify_accis` and `zone_arguments`, for every comfort standard with comfort mode 1 whose standard does not fix
    static setpoints of its own (now only 23; the others ignore them, documented); parameters `StaticHeatingSetpoint`
    and `StaticCoolingSetpoint` of the parametric module.
  - B3, the data of Qatar (§6.3): `outdoor_metric: rmot_alpha`, `alpha: 0.8` (the article uses a running mean
    without α: that of EN 16798-1, noted in `evidence`); `comfort_temperature: {slope: 0.049, intercept: 22.5}`;
    `applicability: {metric_min: 10.0, metric_max: 40.0}` (the range of Tr of the study, mean 30.7 °C, SD 6.4 → about
    21–40 °C, opened to 10 °C to cover the winter of offices with HVAC, noted as a choice); `categories: {90: ±2.5, 80:
    ±3.5}` (the bands of ASHRAE 55, as the article compares, noted as "not own"); `comfort_modes: [0, 1, 2, 3]`;
    `static_setpoints: {heating: 20.0, cooling: 25.5}` (EN 16798-1, Table B.2, offices, category II; changed to 20.0
    and 26.0 °C, the values of that category, by decision 20 of 2026-11-11 above, task S2); `evidence: {N:
    3742, R2: 0.015, SE: 0.007, p: '<0.001', Tr_mean: 30.7, Tr_sd: 6.4, mode: HVAC, bands: 'ASHRAE 55, not own'}`.
    The file must load and be the second example.
  - B3, several regimes in a YAML file (§6.4): a key `regimes:` (a list) with the schema of `CustomRegime` of B2
    (`slope`, `intercept`, offsets, limits, `condition`, optional `outdoor_metric`); a scalar `comfort_temperature` is
    one regime `'always'`. It depends on the metric of each regime. P2.
  - C2, Method C (§6.5): only for the models with setpoints based on the PMV (`pmv_index`), with the limits
    `pmv_heating_setpoint`/`pmv_cooling_setpoint` without the tolerance and the PMV of the zone that the EMS already
    measures; wf = PPD(PMV)/PPD(PMV_limit) with formula (5) of ISO 7730:2025 in Erl (`@Exp`); counter
    `PpdWeightedHours_<zone>`. For the temperature models of the ACCIS, Method C does not apply (no PMV): a documented
    `ValueError`. P2.
  - C2 and D1, CIBSE TM52/TM59 (§6.6): still without the texts, blocked.
  - E4, the notebook and the test with the jar of the Future Weather Generator (§6.7): pending the jar
    (`ACCIM_FWG_JAR`) and the Java version it needs; the command line of pyfwg (12 arguments for version 3) is the
    reference for the 8 arguments of the Java engine of accim, to resolve with the jar.
  - A6, the cooling effect and the Erl way (§6.8): the Erl way is discarded; the cooling effect is postponed to F3
    (an indicator, not a setpoint); the convergence plan A6 → F1 of v04 §4.6 replaces the task.
  - A5, the clothing as a function of the outdoor temperature (§6): `clothing_insulation=callable`, written as a
    `Schedule:File` generated from the weather file with `accim.sim.preview.outdoor_metrics`; no Erl version by
    sections. P2.
  - B5, the names of the setpoint limits (§4.5): `heating_setpoint_floor`/`cooling_setpoint_ceiling` become
    `heating_setpoint_minimum`/`cooling_setpoint_maximum` (EMS keys `AHSTmin`/`ACSTmax`; parameters
    `HeatingSetpointMinimum`/`CoolingSetpointMaximum`), with deprecated aliases through `accim._deprecation`, before
    1.2.0 (P1): "floor" can be read as a physical floor (a radiant floor).
- **Consequences**: the tasks are in [[../TODO.md]] (unblocked), and their order in v04 §7 (G4, G5, H1, H3, H5, H6);
  CIBSE TM52/TM59 and the notebook of the Future Weather Generator stay blocked.

## 2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0

- **Status**: accepted (the author, `notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §5, made binding by the task of the session of 2026-11-10)
- **Context**: the session of the proposals of 1.2.0 (2026-11-09 and 2026-11-10,
  [[INFORME_SESION_v1.2.0_2026-11-10.md]]) left 36 decisions taken provisionally in [[questions.md]], each with the most
  conservative option. The independent review v04 gave the verdict of the author on each one (§5): accept as is, or
  with a change that becomes a task of v04 §7.
- **Decision**: 29 are accepted (some with a note to document) and 7 are changed, completely or in part: #3 (A3, a key
  of the catalogue: task G5), #8 (B1, T0 of `te_ref_nl`: task H2), #13 (B5, crossed setpoints: task G5), #20 (D1,
  Method C at the upper limit: task H3), #28 (B3, the data of Qatar: task G5), #29 (B4, the static setpoints: task
  G4) and #35 (A6: the convergence plan A6 → F1, tasks G3, E-F1 and F1–F3); #30 (B4, the running mean of 23) is
  accepted without a weather file and changed with one by finding B4-1 (task G4). The 36 entries of
  [[questions.md]] are below, moved as they were, with their verdicts (numbered as in v04 §5, oldest first).
- **Consequences**: the decisions of 2026-11-09 and 2026-11-10 that said "decided provisionally" are final, but for
  the changed details; the tasks of the changes are in [[../TODO.md]] and in v04 §7.

### 2026-11-09 — E1: the running means of the first days of the weather file in outdoor_metrics

- Context: `accim.sim.preview.outdoor_metrics` (E1) calculates the running means of the standards (EN 16798-1 B.1 and
  B.2, the mean of the n previous days of ASHRAE 55, the reference temperature of the ATG) from the daily means of the
  previous days, and the first days of the weather file have no previous days in it. v03 and D1-D12 do not say what
  they get.
- Why it matters: the values of the first days of January, and the initial values of the running means of B1 (D3).
- Options considered: (a) a year that repeats: the first days take the last days of the file, as EnergyPlus does for
  ASHRAE 55 at the beginning of a run period, and B.1 is its infinite sum (a closed form); (b) NaN for the days without
  enough previous days (B.1 would never be complete); (c) the sums truncated at the first day of the file.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author (it is what accim does; `energyplus_running_means`
  gives the values of EnergyPlus, whatever the answer).
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #1).
- Verdict (v04 §5, #1): Accepted: consistent with the Engineering Reference §19.1 (the running means are "calculated directly from the weather file"); the documentation says that EnergyPlus 25.1 begins the running mean of CEN 15251 without dividing it by 1 − α⁷ and that `compute_setpoints` reproduces it (finding E1-1 adds the start between 2 and 30 January, task G2).

### 2026-11-09 — E2: what the metabolic correction of the ePMV is checked against (the 5.5–6.1 % of the brief)

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
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author (it is exact and catches any other reduction; the
  5.5–6.1 % stays documented as the result of the correction).
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #2).
- Verdict (v04 §5, #2): Accepted: the band of 5.5–6.1 % is the result of the correction, not the rule.

### 2026-11-09 — A3: does a key of the catalogue in one coefficient also set the other one

- Context: the design of A3 says that a key given in `adaptive_coefficient_cooling` "fills both coefficients at once
  unless the other is given explicitly"; its prompt only says that the arguments accept a key, and the defaults of the
  coefficients are numbers (0.293 and −0.293), so an explicit value equal to the default cannot be told apart.
- Why it matters: `adaptive_coefficient_cooling='yao2009_chongqing_classrooms'` alone gives λ 0.293 and −0.293 (the
  default) with (a), and 0.293 and −0.125 with (b).
- Options considered: (a) each argument takes the coefficient of its own side of the key (give the key to both to use
  the entry); (b) the defaults become None, which takes the other coefficient of a key, or 0.293/−0.293 otherwise (the
  signature changes, and the GUI and the documentation show other defaults); (c) a new argument with the key for both.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author (the conservative, backward-compatible one;
  documented in the docstring and in section 4.8).
- Status: answered by the author on 2026-11-10 (changed; v04 §5, #3).
- Verdict (v04 §5, #3): Changed (finding A3-1, task G5): the catalogue is made of pairs, so a key given on one side only must not pair a sourced λ with the default −0.293/0.293, which has no source: a new argument `adaptive_coefficients=<key>` sets both sides (a `ValueError` if it is combined with explicit numbers), the keys of each side are kept (an explicit number on the other side wins), and a warning is given when one side is a key and the other is left at the numeric default.

### 2026-11-09 — A3: with adaptive_coefficient_by='pmv_sign', which λ converts each setpoint into the PMV setpoint of the thermostat

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
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author (the monitor and the output `Adaptive
  Coefficient_<zone>` follow the design).
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #4).
- Verdict (v04 §5, #4): Accepted: the cooling setpoint is an aPMV > 0 (λ of warm sensations) and the heating setpoint an aPMV < 0 (λ of cool sensations); the signs of the setpoints are validated with `pmv_sign` (finding A3-2, task G5).

### 2026-11-09 — B1: does every model of the custom model have the EMS code of the outdoor metric, or only those that need it

- Context: the prompt of B1 says that SetComfTemp, SetAppLimits and COUNT_HOURS of the custom model use `Tout_metric`,
  a new global variable and EMS output; with the default `'pmot'`, the behaviour must not change.
- Why it matters: with the code in every model of the custom model (and in the models of `add_accis_to_idf`, which
  have the code of all the comfort standards), the output IDFs of 1.1.0 with comfort standard 99 would get new
  programs, global variables and outputs (new columns in the CSV files), although their setpoints would not change.
- Options considered: (a) always; (b) only if a zone has a metric other than `'pmot'` (`CustAST_metric` ≠ 0) and the
  model has the code of the custom model; otherwise the custom model uses PMOT, as in 1.1.0.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (b) decided provisionally, pending author (the golden master does not change; the parametric
  parameters of C1 will add the code when they set a metric).
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #5).
- Verdict (v04 §5, #5): Accepted: the output IDFs of 1.1.0 do not change.

### 2026-11-09 — B1: which programs of the custom model use Tout_metric

- Context: the prompt names SetComfTemp, SetAppLimits and COUNT_HOURS. In accim, SetAppLimits only sets the limits of
  the custom model from its inputs; the outdoor temperature is compared with them in the subprogram of its setpoints
  (`SetAST_CS99_0`), in `CountHours_<zone>` and, in mixed mode, in `SetVST` (the ventilation setpoint).
- Why it matters: with PMOT in some of them, the custom model would mix two outdoor temperatures.
- Options considered: (a) only the programs of the prompt (SetAppLimits unchanged); (b) every program where the
  custom model uses its outdoor temperature: SetComfTemp, `SetAST_CS99_0`, `CountHours_<zone>` and `SetVST`.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (b) decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #6).
- Verdict (v04 §5, #6): Accepted: more complete than v03, which forgot SetVST.

### 2026-11-09 — B1: on which day do the programs of the outdoor metric begin with the values of the weather file

- Context: decision D3 says to initialise the running means with the values that accim calculates from the EPW given
  to AddAccis, but not for which day; the programs keep constants, not the whole year.
- Why it matters: if the model is simulated from another day (another RunPeriod, or the design days), the constants
  of the first day would be wrong.
- Options considered: (a) the constants of the first day of the first RunPeriod of the input IDF, used only if the
  environment begins on that day (otherwise, the PMOT of EnergyPlus, as without the EPW); (b) the constants of the
  365 days (more than 10 000 program lines).
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #7).
- Verdict (v04 §5, #7): Accepted: as decision D3.

### 2026-11-09 — B1: T0 of te_ref_nl before the first hour of the day has ended

- Context: v03 gives Te,ref = (T0 + 0.8·T−1 + 0.4·T−2 + 0.2·T−3)/2.4 with T0 "the running (max+min)/2 of today"; at
  the first timesteps of a day, no hourly value of the day has ended.
- Options considered: (a) the outdoor temperature of the timestep; (b) the mean of the maximum and minimum of the
  previous day.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (changed; v04 §5, #8).
- Verdict (v04 §5, #8): Changed (task H2): van der Linden et al. (2006) define Ti as the mean of the maximum and the minimum of the whole day, and the partial value makes Te,ref drift within the day. With the weather file, T0 is the daily value of the weather file, written as a `Schedule:File` read by a sensor `Schedule Value`; without it, the (max+min)/2 of the previous day, with a warning. Until H2, the drift is documented.

### 2026-11-09 — B1: the arguments of the outdoor metric in modify_accis

- Context: the other arguments of the custom model of `modify_accis` (`custom_slope`...) default to 0 and are always
  written.
- Options considered: (a) `custom_outdoor_metric='pmot'`, `custom_alpha=0.8`, `custom_days=30` written by every call
  (a call without them would remove the metric of the zones); (b) `None` by default, keeping the values of each zone,
  as `comfort_standard` and the other arguments that are None.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (b) decided provisionally, pending author (the most conservative: a call without them changes
  nothing of the outdoor metric).
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #9).
- Verdict (v04 §5, #9): Accepted as is.

### 2026-11-09 — B5: where the floor and ceiling bound the setpoints

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
- Provisional decision (pending author until 2026-11-10): option (b) decided provisionally, pending author (checked with the Erl interpreter: the setpoints are
  those of bounding before the rounding; with EnergyPlus 25.1, no mismatch with `compute_setpoints`).
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #10).
- Verdict (v04 §5, #10): Accepted: better than lines in the shared subprograms.

### 2026-11-09 — B5: the floor and ceiling in modify_accis

- Context: `modify_accis` writes the inputs of its arguments that are not None; several of them have numbers as
  defaults, which every call writes.
- Options considered: (a) numbers as defaults; (b) `None` by default, keeping the floor and ceiling of each zone, as
  the arguments of the outdoor metric of B1; there is no way to remove them with `modify_accis` (a model without them
  is made again with `AddAccis` or `add_accis_to_idf`, or the lines are removed from `SetInputData_<zone>` and
  `accim.sim.ems.setpoint_limits.set_setpoint_limits_code` is called).
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (b) decided provisionally, pending author (the most conservative: a call without them changes
  nothing of the floor and ceiling).
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #11).
- Verdict (v04 §5, #11): Accepted as is.

### 2026-11-09 — B5: the outputs of report_hours_below and the setpoint types

- Context: the prompt asks for the counters `HoursBelow_<T>_<zone>`, but not with which outputs and setpoint types.
- Options considered: the outputs of every `output_type` but 'custom' (the standard and detailed outputs take all the
  EMS outputs; with 'simplified', their `Output:Variable` objects are added; with 'custom', the user keeps those
  chosen); the counters also with `setpoint_type='pmv'`, since they only need the occupants and the operative
  temperature (only the floor and ceiling are rejected there, D5); the temperatures with decimals named with `p`
  (`HoursBelow_17p5_<zone>`: the names of the EMS cannot have dots) and `m` for the minus sign.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): these options decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #12).
- Verdict (v04 §5, #12): Accepted as is.

### 2026-11-09 — B5: a floor above the cooling setpoint, or a ceiling below the heating setpoint

- Context: the floor only bounds the heating setpoint and the ceiling the cooling setpoint; accim checks that the floor
  is lower than the ceiling, but a floor above the cooling setpoint of the comfort model (or a ceiling below its heating
  setpoint) gives a heating setpoint above the cooling setpoint in those timesteps. v03 does not say what to do.
- Options considered: (a) as v03 writes the lines, documented; (b) also raise the cooling setpoint to the floor and
  lower the heating setpoint to the ceiling (not in v03).
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author (documented in section 4.2.3 of the detailed use).
- Status: answered by the author on 2026-11-10 (changed; v04 §5, #13).
- Verdict (v04 §5, #13): Changed: a `ValueError` when the model is built if the floor is not lower than the ceiling (as the code already does), and a warning in the log if the floor is above `ACSTaul` or the ceiling below `AHSTall` (crossed setpoints make EnergyPlus warn and give meaningless results; task G5).

### 2026-11-09 — C1: with which parameters types are the inputs of the PMV parameters

- Context: the prompt of C1 asks to register `Clo`, `Met` and `AirVelocity` "in get_available_params_apmv_setpoints()",
  and the brief points to `get_available_params_epmv_setpoints()` as the recent pattern; with the accim models
  (temperature setpoints), they would only change the outputs of the PMV.
- Options considered: (a) the parameters types 'apmv setpoints' and 'epmv setpoints' only; (b) also the accim models.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #14).
- Verdict (v04 §5, #14): Accepted: the models of the ACCIS control temperatures; clo and met are not their parameters.

### 2026-11-09 — C1: the units and range of activity_level

- Context: the brief replaces `met` with `activity_level`, the argument of `set_pmv_input_parameters`, in W/person (as
  the People objects of EnergyPlus); the prompt warns outside 0.8–4 met (ISO 7730:2025 §4: 46–232 W/m²).
- Options considered: (a) the parameter in W/person, warning outside 82.8–417.6 W/person (46–232 W/m² times the body
  surface area of 1.8 m² of ISO 7730:2025 §4 and of EnergyPlus, Engineering Reference 19.1); (b) a parameter in met,
  converted to W/person.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author (the name and units of the argument of accim).
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #15).
- Verdict (v04 §5, #15): Accepted: 82.8 W/person (46 W/m² of ISO 7730:2025 §4 times 1.8 m²) stays the documented bound; 0.8 met × 58.2 W/m² × 1.8 m² = 83.8 W/person would be the bound written in met.

### 2026-11-09 — C1: the outdoor metric of the custom model as a parameter

- Context: the parametric module turns the options into floats, and samples ranges with floats; the modifiers get the
  model and the value only (not the weather file of the simulation); its parameters are applied one after the other.
- Options considered: `custom_outdoor_metric` takes the codes of the metrics (0–7) as options (a code that is not
  whole raises a ValueError); `custom_days` is rounded to the nearest whole day; the metrics begin with PMOT, unless
  the model was given the weather file with `modify_accis(..., epw=...)` before the study, whose programs are kept
  ('monthly_mean' needs them); while the metric is 'pmot' and the model has no code of the outdoor metric, the inputs
  given stay in `SetInputData_<zone>` as local Erl variables, so that `custom_alpha` or `custom_days` given before
  `custom_outdoor_metric` are kept.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): these options decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #16).
- Verdict (v04 §5, #16): Accepted as is.

### 2026-11-09 — C1: the plans with a floor of the heating setpoint not lower than the ceiling

- Context: the prompt asks to update "the plans of `sampling_full_set()`"; the modifiers of B5 reject a floor that is
  not lower than the ceiling, which stops that simulation.
- Options considered: `drop_invalid_param_combinations` leaves those rows out, and `sampling_full_set()` also applies it
  to the accim custom models (before, only to the predefined models; its other rules need columns that the custom
  models do not have).
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #17).
- Verdict (v04 §5, #17): Accepted: consistent with the verdict on the floor above the cooling setpoint (#13).

### 2026-11-09 — D1: what are the warm and cold periods of the indicators of Table

- Context: the prompt of D1 asks Table for the indicators "per zone and building for the warm and cold periods, using
  the ACSTnoTol/AHSTnoTol columns as limits by default"; CEN/TR 16798-2 (Annex D, Methods B and C) calls "warm period"
  the sum of the time above the upper limit and "cold period" that below the lower limit, while the design of v03
  also says "por estación cálida/fría definida con cooling_season_start/end".
- Options considered: (a) the warm and cold periods of the TR (above and below the range), with the setpoints of each
  hour as the limits (which already follow the cooling season); (b) also split by the cooling and heating seasons.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #18).
- Verdict (v04 §5, #18): Accepted: it is the literal definition of Annex D (the sums above the upper limit and below the lower limit).

### 2026-11-09 — D1: what Table(long_term_indicators=True) gives

- Context: the prompt asks Table for "these indicators per zone and building"; the indicators are sums of each
  simulation, while the rows of `Table.df` are timesteps or hours (the indicators need them).
- Options considered: Methods A and B with the temperature (the operative temperature and the setpoints without the
  tolerance of each zone), the occupied hours of each row (the EMS output `Occupied Hours_<zone>`) as the time, in a
  new attribute `long_term_indicators` (a row per simulation, columns `<zone>_...` and `Building_...`, the building
  adding up its zones), only for the tables that ask for it (so the files of the other tables do not change); Method C
  (which needs the PMV and its limits), the deviations of Table E.1 and the hours below some temperatures with the
  functions of the module.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #19).
- Verdict (v04 §5, #19): Accepted as is.

### 2026-11-09 — D1: the gaps of CEN/TR 16798-2 in Method C and Table E.1

- Context: Method C gives wf = 0 for PMVlimit,lower ≤ PMV < PMVlimit,upper and the weight for PMV < PMVlimit,lower or
  PMVlimit,upper < PMV, so a PMV equal to the upper limit is in neither; Table E.1 gives 44 h for 25 % of 175 h
  (43.75 h), and 58 h of 166 h for 50 % of the weekly total time.
- Options considered: a PMV equal to the upper limit is within the range (as in Method B); `deviation_check` uses the
  percentages of Table E.1 (43.75 h), not its rounded hours.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted in part, changed in part; v04 §5, #20).
- Verdict (v04 §5, #20): Accepted for the percentages of Table E.1 (its hours do not match, as found). Changed for Method C: the range of wf = 0 follows the literal text of the TR, PMVlimit,lower ≤ PMV < PMVlimit,upper, so a PMV equal to the upper limit is outside the range (task H3).

### 2026-11-09 — B2: an outdoor metric for each regime of the custom model

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
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally (a `ValueError` explains it), pending author. `TODO.md` has the task.
- Status: answered by the author on 2026-11-10 (accepted for now; v04 §5, #21).
- Verdict (v04 §5, #21): Accepted for now; the decision of v04 §6.1 unblocks it (task H5).

### 2026-11-09 — B2: how the program of the regimes sets the custom model

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
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #22).
- Verdict (v04 §5, #22): Accepted as is.

### 2026-11-09 — B2: the meaning of the conditions of the regimes

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
- Provisional decision (pending author until 2026-11-10): decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #23).
- Verdict (v04 §5, #23): Accepted as is.

### 2026-11-09 — B2: the regimes in the zones and in the parametric module

- Context: v03 does not say whether the regimes can differ between zones, nor which coefficients the factory
  `custom_regime_parameters(n)` makes parameters ("CustAST_m_1, CustAST_n_1, ...").
- Options considered: the same regimes in all the zones whose comfort standard is 99 (`zone_arguments` cannot give
  them); in the parametric module, the eight coefficients of each regime (not the values of its condition), as the
  parameters `custom_regime_<regime>_<field>` of the accim custom models (accepted by `set_parameters` and
  `accis_parameter`, applied by BESOS through `param_accis.modify_custom_regime`) and the classes `CustAST_m_1`,
  `CustAST_n_1`, `CustAST_ACSToffset_1`, `CustAST_AHSToffset_1`, `CustAST_ACSTall_1`, `CustAST_ACSTaul_1`,
  `CustAST_AHSTall_1` and `CustAST_AHSTaul_1` of the factory.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #24).
- Verdict (v04 §5, #24): Accepted; regimes by zone would be a future P2 task, if they are needed.

### 2026-11-09 — B3: what `load_comfort_standards` does by default

- Context: the prompt asks for `load_comfort_standards(yaml_path)` returning the definitions, and
  `register_comfort_standard(definition)`; it does not say whether loading registers them.
- Options considered: (a) `register=True` by default (loading a file makes its comfort standards usable, as the GUI
  needs), `register=False` to only read them, `replace=False` (a number already registered raises a `ValueError`);
  (b) only read, and register with `register_comfort_standard`.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #25).
- Verdict (v04 §5, #25): Accepted as is.

### 2026-11-09 — B3: comfort mode 2 and the outdoor metric of the comfort standards defined by their data

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
- Provisional decision (pending author until 2026-11-10): options (a) and (a) decided provisionally (the code's ISO 7730 values; one EMS code of the outdoor
  metric for all), pending author.
- Status: answered by the author on 2026-11-10 (accepted with a note; v04 §5, #26).
- Verdict (v04 §5, #26): Accepted with a note: document that comfort mode 2 (the static setpoints of ISO 7730 out of the applicability) is not defined for the categories I–IV of a YAML file (task G5).

### 2026-11-09 — B3: one regime for each comfort standard defined by its data

- Context: the design of B3 gives `ComfortStandardDefinition` `regimes: Tuple[CustomRegime, ...]  # B2; one regime for
  a single line`, but its YAML schema has one comfort temperature, one applicability and no conditions, and neither v03
  nor the brief say how comfort modes 0 to 3 apply with several regimes (which limits give the static or the extended
  setpoints), nor how a YAML file writes them.
- Options considered: (a) one regime with the condition 'always' (several, or another condition, raise a
  `ValueError`), whose offsets are added to those of the categories; the YAML files give it with
  `comfort_temperature` and `applicability`; (b) several regimes, written into the branches of SetComfTemp, SetAppLimits
  and ApplyCAT with the conditions of B2.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally, pending author. `TODO.md` has the task.
- Status: answered by the author on 2026-11-10 (accepted for now; v04 §5, #27).
- Verdict (v04 §5, #27): Accepted for now; several regimes in a YAML file follow the decision of v04 §6.4 (task H5).

### 2026-11-09 — B3: the data of the comfort model of Qatar of the sample files

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
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally (nothing invented, D11 kept), pending author. `TODO.md` has the task.
- Status: answered by the author on 2026-11-10 (changed; v04 §5, #28).
- Verdict (v04 §5, #28): Changed: the YAML file is completed with the data of v04 §6.3, so that it loads (task G5).

### 2026-11-09 — B4: how the static setpoints of JPN Aqilah 2025 are configurable (decision D2)

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
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally (no new arguments, which are hard to take back; (b) can be added
  later without breaking anything), pending author. `TODO.md` has the task.
- Status: answered by the author on 2026-11-10 (changed; v04 §5, #29).
- Verdict (v04 §5, #29): Changed: new arguments `static_heating_setpoint` and `static_cooling_setpoint` (v04 §6.2; task G4).

### 2026-11-09 — B4: the running mean of JPN Aqilah 2025 (comfort standard 23)

- Context: the model of Aqilah et al. (2025, equation 8) uses `Trm = α·Trm−1 + (1 − α)·Tod−1` with α = 0.8 (McCartney
  & Nicol, equation 7), "started a week before the day of the survey" (v03, B4). EnergyPlus calculates the running mean
  of CEN 15251 with α = 0.8 (RMOT, Engineering Reference 19.1, equation 19.82: the same recursion, begun with a sum of 7
  days that is not divided by 1 − α⁷), which INT EN16798 (1) uses; B1 gives the EMS the exact recursion (`rmot_alpha`,
  begun with the weather file), which needs the EMS code of the outdoor metric in the output IDFs and `epw`.
- Options considered: (a) RMOT of EnergyPlus, as INT EN16798: the comfort standard has literal lines, no EMS code of the
  outdoor metric and no inputs of it in its zones; (b) `rmot_alpha` of B1, as the YAML file of the sample files (101).
  They differ by less than 0.05 °C after three weeks with `Seville_Present.epw` (section 4.2.2 of the detailed use).
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): option (a) decided provisionally (as the other comfort standards with this running mean; (b) is
  available as a comfort standard defined by its data), pending author.
- Status: answered by the author on 2026-11-10 (accepted without a weather file; changed with one; v04 §5, #30).
- Verdict (v04 §5, #30): Accepted for the models without a weather file: Aqilah et al. (2025) use α = 0.8 begun a week before (equation 7), and the RMOT of EnergyPlus is α = 0.8 truncated at 7 days (Engineering Reference 19.82), the same definition in practice, to be documented in the docstring of comfort standard 23. With a weather file given to `AddAccis`, finding B4-1 of v04 §3.1 applies (the RMOT of EnergyPlus begins about 21 % below the running mean, and the deficit decays as 0.8^n): comfort standard 23 uses `rmot_alpha` begun with the weather file, and the RMOT of EnergyPlus otherwise, with a warning (task G4).

### 2026-11-10 — C2: Method C (the PPD-weighted hours) as an objective

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
- Provisional decision (pending author until 2026-11-10): (a) decided provisionally (the most conservative: no output IDF changes and no choice of PMV or limits
  is made for the author), pending author.
- Status: answered by the author on 2026-11-10 (accepted for now; v04 §5, #31).
- Verdict (v04 §5, #31): Accepted for now; the decision of v04 §6.5 unblocks Method C for the setpoints based on the PMV only (task H3).

### 2026-11-10 — C2: how the long-term comfort objectives reach the optimisation, and with which range

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
- Provisional decision (pending author until 2026-11-10): (a), (i) and (1) decided provisionally (`report_long_term_discomfort=False` by default, so the output
  IDFs do not change; the same limits as D1 and the other hour counters; the EnergyPlus comfort status of
  `hours_outside_comfort` stays the objective independent of the control), pending author. The constraint bound of
  `deviation_constraint_bound` is that of the simulated period (the yearly criterion); the weekly and monthly ones are
  checked after the simulations (`TODO.md`). The setpoints based on the PMV are left out (`ValueError`): their zones do
  not keep the setpoints of the ACCIS.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #32).
- Verdict (v04 §5, #32): Accepted as is.

### 2026-11-10 — E4: how morph_epws delegates in pyfwg, and what "accepts TMY of pyweatherfiles" means

- Context: v03 (E4): "`morph_epws()` delega opcionalmente en `pyfwg` (Future Weather Generator) y acepta TMY de
  `pyweatherfiles`; sólo si están instalados (`accim[weather]`)", with a notebook; no prompt, and the brief no
  adjustment. pyfwg 0.4.0 (PyPI) runs the global, Europe and CORDEX distributions of the tool
  (`morph_epw_global`, `morph_epw_europe`, `morph_epw_cordex`), checks the parameters and supports the versions 3, 4
  and 5 of the global tool; pyweatherfiles generates typical meteorological years (`TMYGenerator`, exported to CSV,
  TMY or XLSX) and writes EPW files from hourly data (`HourlyEPWConverter`).
- Options considered: for the delegation, (a) a new argument `engine` ('java' by default, as before; 'pyfwg'), (b)
  pyfwg whenever it is installed (the default behaviour of `morph_epws` would change with the packages of the
  environment); for the distributions, (i) the global one only (that of the command of `engine='java'`, with its
  options), (ii) all those of pyfwg (their options differ); for pyweatherfiles, (1) `morph_epws(engine='pyfwg')` takes
  paths of EPW files of any folder, such as those that pyweatherfiles writes, and the docs say how to get them, (2)
  `morph_epws` takes the objects or TMY files of pyweatherfiles and converts them (a base EPW and the columns would be
  new arguments).
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): (a), (i) and (1) decided provisionally (the default behaviour does not change; `pyfwg_arguments` gives
  the other arguments of `pyfwg.morph_epw_global`), pending author. The notebook waits for the jar of the tool
  (`TODO.md`).
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #33).
- Verdict (v04 §5, #33): Accepted as is.

### 2026-11-10 — A4: the models, hours and range of the setpoints of the ATHB

- Context: the prompt of A4 asks for the hook of the backend of the Python API that sets the operative temperatures of
  the ATHB setpoints "to the setpoint schedule actuators used by the ACCIS", and `apply_athb_setpoints` that prepares
  the IDF; it does not say which models (mixed mode, whose windows follow the setpoints of the ACCIS), whether the
  setpoints apply without occupants, nor the range of the bisection.
- Options considered: models: (a) full air-conditioning only (`ValueError` in mixed mode), (b) also mixed mode (the
  windows would follow the adaptive setpoints and the HVAC the ATHB ones); hours: (i) every timestep, as the ACCIS in
  full air-conditioning, (ii) only with occupants (the PMV-based setpoints of accim set back the thermostats without
  occupants); range: 10–30 °C (the air temperatures with which ISO 7730:2025 uses the PMV, v03 C1), with its limits as
  the setpoints out of it, or a wider one.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): (a), (i) and 10–30 °C (an argument, `temperature_range`) decided provisionally (the most conservative:
  the ACCIS keeps controlling everything but the setpoints of the HVAC, and the PMV is used within its range), pending
  author. Also provisional: the ATHB_PMV of each zone is reported from its air and mean radiant temperatures (the
  setpoints, for both equal to the operative temperature); at the first timestep of each environment the running mean
  is 0, as for the ACCIS; the cache or table of v03 (performance) is not needed (about 1 ms per zone and timestep).
- Status: answered by the author on 2026-11-10 (accepted with a note; v04 §5, #34).
- Verdict (v04 §5, #34): Accepted with a note: the range of 10–30 °C is that of the validity of the PMV (ISO 7730:2025 §4: ta 10–30 °C); the ATHB setpoints in mixed mode stay a P2 task (`TODO.md`).

### 2026-11-10 — A6: which setpoints of SET, PPD or cooling effect

- Context: v03 (A6, no prompt) gives two ways for the setpoints of the SET, (a) a proportional control in Erl of the
  setpoint from the SET of the previous timestep (k ≈ 0.8, with saturation; "sencillo pero con retardo y posible
  oscilación") and (b) a hook of the API backend with `pythermalcomfort.models.set_tmp` and bisection ("exacto"); the
  PPD through A2 (the PMV setpoints of the categories of ISO 7730:2025, Table A.1); and names the cooling effect
  without a design; it gives no defaults for the SET setpoints, the metabolic rate, the clothing or the air speed.
- Options considered: (b) only, as A4, with required arguments (chosen); (a) also; the cooling effect with some index
  and setpoints (not designed in v03). The SET of pythermalcomfort crashes in the callbacks of EnergyPlus, so (b) became
  a table of the setpoints by relative humidity (every 1 %, interpolated), without an output of the SET.
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): (b) with the table decided provisionally; (a) and the cooling effect wait for the author (blocked task
  in `TODO.md`).
- Status: answered by the author on 2026-11-10 (changed; v04 §5, #35).
- Verdict (v04 §5, #35): Changed: the table by relative humidity is replaced by the convergence plan A6 → F1 of v04 §4.6 (the table stays the default method of `SetSetpointHook`, and a method by bisection in the callbacks is added, task G3); the Erl way (a) is discarded, since the author chose the API backend in block F; the cooling effect is postponed to F3 (an indicator, not a setpoint).

### 2026-11-10 — D2 (completed): the names in Table of the optional outputs of the ACCIS and of the ATHB

- Context: v03 (D2) asks Table to recognise `ATHB_PMV_<zone>`, `Tout_metric` and `HoursBelow_*_<zone>` in the renaming
  and in the figures and `wrangled_table`; it does not give their names in Table, nor those of `Tout_metric_<zone>`,
  `CustomRegime_<zone>` (B2, added to the task in `TODO.md`) or the outputs of C2, nor their block and building values.
- Options considered: the outdoor metric of each zone: (a) it keeps its EMS name, as the comfort temperature and the
  setpoints of each zone of the ACCIS (chosen), or (b) `<zone>_Tout_metric (°C)`, which contains `Tout_metric (°C)`, the
  name of that of the model, so the figures would take the zones with it; the outputs of C2: (i) the same names as the
  indicators of `Table(long_term_indicators=True)`, `<zone>_Hours Above Upper Limit (h)`... and `Building_...` for the
  EMS sums of the building (chosen), or (ii) not renamed (v03 does not list them); block and building values for the
  hours, the degree hours and the ATHB (as for the index of the PMV-based setpoints), not for the regime and the outdoor
  metric of the zones (as for the schedules of the thermostats).
- Owner: the author.
- Provisional decision (pending author until 2026-11-10): (a), (i) and the levels above decided provisionally (no name contains another one, and the names follow
  those that Table already gives), pending author.
- Status: answered by the author on 2026-11-10 (accepted; v04 §5, #36).
- Verdict (v04 §5, #36): Accepted as is.

## 2026-11-10 — The optional outputs of the ACCIS and of the ATHB in Table (D2, completed)

- **Status**: accepted (proposal D2 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`, the outputs of A4, B1 and B5 that it
  lists, with those of B2 and C2; the names decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
- **Context**: D2 was done on 2026-11-09 for the PMV-based setpoints, before the outputs of the other proposals existed;
  Table dropped the optional outputs with `standard_outputs=True`, kept their EMS names in capitals without block and
  building values, and added up the outputs of the ATHB over time.
- **Decision**: a module `accim.data.postprocessing.optional_output_columns`, as `pmv_index_columns`, with the names of
  Table (`<zone>_HoursBelow_<T> (h)`, `<zone>_Hours Above Upper Limit (h)`, `Building_...`, `<zone>_ATHB_PMV`,
  `<zone>_CustomRegime`, `Tout_metric (°C)`), what is averaged and what has block and building values; the outdoor metric
  of each zone keeps its EMS name, so that no name contains another one.
- **Consequences**: Table keeps and names every optional output of 1.2.0; a test checks the names against the modules of
  `accim.sim` that create the outputs, so a new optional output needs its name in Table.

## 2026-11-10 — The setpoints of the SET are a hook of the API backend with a table by relative humidity (A6)

- **Status**: accepted (proposal A6 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`, way (b); decided provisionally,
  answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]]);
  partly superseded: the way the hook gives its setpoints, by
  [[decisions.md#2026-11-10 — The hooks of the setpoints run before the EMS programs and give their setpoints to the ACCIS through a program of each zone (G1)|G1]],
  and the rest by the convergence plan A6 → F1 (verdict #35)
- **Context**: v03 gives the SET setpoints by Erl (approximate) or by a hook with pythermalcomfort (exact), and the PPD
  through the PMV setpoints; the SET of pythermalcomfort stops EnergyPlus when it is calculated in its callbacks
  (corrected by G3: only at its first call in a process that has loaded the library of the API of EnergyPlus,
  in Python 3.14.3 with numba 0.68.1).
- **Decision**: `apply_set_setpoints` and `SetSetpointHook` in `accim.sim.comfort_hooks`, as the ATHB, with the setpoints
  calculated by bisection for each relative humidity (0–100 %, every 1 %) when the hook is made and interpolated in the
  callbacks; no output of the SET; the PPD documented as the PMV setpoints of `apply_pmv_setpoints`.
- **Consequences**: the hook takes about 1.5 s to be made, and nothing of pythermalcomfort runs in the callbacks; the
  SET of the zones is calculated after the simulations; the Erl way and the cooling effect wait for the author.

## 2026-11-10 — The setpoints of the ATHB are a hook of the backend of the Python API on the setpoints of the ACCIS (A4)

- **Status**: accepted (proposal A4 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`, its prompt, the adjustment of the
  brief and D10; details decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]]);
  partly superseded: the way the hook gives its setpoints, by
  [[decisions.md#2026-11-10 — The hooks of the setpoints run before the EMS programs and give their setpoints to the ACCIS through a program of each zone (G1)|G1]]
- **Context**: the ATHB (Schweiker, 2022) needs the whole PMV with the adapted clothing and metabolic rate in each
  timestep, which the EMS cannot calculate; the backend of the Python API of accim 1.0.0 runs Python hooks after the
  EMS programs.
- **Decision**: `accim.sim.comfort_hooks.apply_athb_setpoints` adds to a model with the ACCIS (full air-conditioning)
  the sensors and outputs of the ATHB and returns `AthbSetpointHook`, which sets the actuators of the setpoint
  schedules of the ACCIS to the operative temperatures of the ATHB setpoints, found by bisection with
  `pythermalcomfort.models.pmv_athb` (imported only then, the extra `accim[comfort]`); `run_ep` gets `hooks` (API
  backend only).
- **Consequences**: the ACCIS keeps its programs, thermostats and outputs, and the hook replaces its setpoints; the
  model needs the API backend and the hook (the EMS gives the ACCIS setpoints); pythermalcomfort needs Python 3.11 or
  later, so the setpoints of the ATHB too; the arguments of the hook are not in the model (`TODO.md`).

## 2026-11-10 — morph_epws delegates in pyfwg on request, for the global tool, and pyfwg and pyweatherfiles are the extra accim[weather] (E4)

- **Status**: accepted (proposal E4 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`, which has no prompt; the design
  decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
- **Context**: `morph_epws` ran the Future Weather Generator with Java from the command line, with the arguments of an
  earlier version of the tool; v03 asks for an optional delegation in pyfwg and the TMY of pyweatherfiles, only if they
  are installed (`accim[weather]`, the extra of v03, E3).
- **Decision**: `engine='pyfwg'` (`'java'` by default) runs the global tool through `pyfwg.morph_epw_global`, with the
  options of `morph_epws` and `pyfwg_arguments` for the others, and renames and moves the future EPWs as the Java
  engine does; pyfwg is imported only then. `setup.py` gets the extra `weather` (`pyfwg>=0.4.0`, `pyweatherfiles`);
  accim does not import pyweatherfiles: its EPWs are morphed by path.
- **Consequences**: the default behaviour of `morph_epws` does not change; with pyfwg, the versions 3, 4 and 5 of the
  global tool and EPWs of any folder can be used; the other distributions are run with pyfwg directly; the notebook and
  the test with the tool wait for its jar.

## 2026-11-10 — The long-term comfort objectives are EMS counters of the ACCIS with the range of its setpoints, opt-in (C2)

- **Status**: accepted (proposal C2 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`, which has no prompt; the design
  decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
- **Context**: v03 asks for the indicators of CEN/TR 16798-2:2019 (Annex D: Methods A, B and C) as objectives of the
  parametric and optimisation module, reusing D1, and the deviations of Table E.1 as constraints. The reducers of besos
  get one output each, while the indicators need the operative temperature, the limits and the occupants together.
- **Decision**: with `report_long_term_discomfort=True` (False by default), the EMS of each zone counts Methods A and B
  in each timestep with the setpoints without the tolerance as the limits, as the hour counters of the ACCIS and
  `Table(long_term_indicators=True)` of D1 (`accim.sim.ems.long_term_discomfort`), with the sums of the zones for the
  building; `hours_outside_range` and `degree_hours` sum these outputs, and `deviation_constraint_bound` gives the
  bound of a constraint with Table E.1 (`deviation_limit` of D1). Method C is not counted (it needs a PMV and limits
  that the author has to choose).
- **Consequences**: the output IDFs do not change unless it is asked; the objectives follow the comfort model of the
  control (the comfort status of EnergyPlus stays the objective independent of it); the setpoints based on the PMV
  cannot have them; the weekly and monthly deviations of Table E.1 are checked after the simulations.

## 2026-11-09 — JPN Aqilah 2025 is the built-in comfort standard 23, defined by its data, with the running mean of EnergyPlus (B4)

- **Status**: accepted (proposal B4 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` with decisions D1 and D2 of the
  brief; two details decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
- **Context**: v03 asks for the adaptive model of Japanese dwellings in free-running mode of Aqilah et al. (2025) as a
  new comfort standard, without changing JPN Rijal (3); D1 gives it the number 23 and D2 the static setpoints of 20 and
  28 °C, configurable. A new built-in comfort standard changes the chains of `SetComfTemp`, `SetAppLimits`, `ApplyCAT`,
  `CountHours_<zone>` and `SetVST`, which the output IDFs of the other comfort standards also have (`SetVST` whole).
- **Decision**: its EMS code is written as that of the comfort standards defined by their data (B3): literal branches
  (`program_lines.BUILT_IN_BRANCHES`) added at the end of the literal chains of accim 1.1.0, and its setpoint lines,
  equal to those that `standard_lines` writes from its definition (`standards.built_in_definitions()`), which also
  gives its source and evidence to `print_setpoint_ems_code`; its running mean is RMOT of EnergyPlus, as for INT
  EN16798; its static setpoints are literal (20/28 °C), and other values are given with a comfort standard defined by
  its data with the same data.
- **Consequences**: the output IDFs of `AddAccis` of the other comfort standards do not change; the models with the
  code of all the comfort standards (`add_accis_to_idf`) gain that of 23 (7 golden files written again, only
  additions); the models of earlier versions cannot be given 23 (`ValueError`); arguments for its static setpoints
  wait for the author.

## 2026-11-09 — Comfort standards defined by their data are registered for the session, and their EMS code is added at the end of the chains of the built-in ones (B3)

- **Status**: accepted (proposal B3 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` with decisions D1 and D11 of the
  brief; four details decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
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
  four details decided provisionally and one left open, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
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
  three details decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
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
  `clothing_insulation`/`activity_level` instead of `clo`/`met`; four details decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
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
  `notes/COPILOT_BRIEF_v1.2.0_v01.md`; four details were decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
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
  `notes/COPILOT_BRIEF_v1.2.0_v01.md`; four details were decided provisionally, answered on 2026-11-10, see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]])
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
  takes them too; each argument takes the coefficient of its own side (changed on 2026-11-10: see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]]). With 'pmv_sign', the program
  of the setpoints does not choose the coefficient (the new hook `PmvIndex.seasonal_coefficient`), the monitor chooses
  it by the sign of the PMV of the zone (after `average_PMV_<zone>`, so with the PMV of the previous timestep also in
  zones with several People objects), and each setpoint is converted with the λ of its side ([[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]]). The
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
