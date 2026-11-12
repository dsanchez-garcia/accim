---
title: Work log
type: log
tags: [vault, work-log]
created: 2026-09-13
---

# Work log

Reverse-chronological session log (most recent first). Each entry should be
short: objective, affected files, finding or decision, validation, next step.
Use [[templates/daily-note.md|the daily-note template]] to start a new entry.

This log is a lightweight, session-scoped complement to the repository's
existing tracking files — it does not replace them (see
[[decisions.md#2026-09-13 — `notes/work-log.md` complements, not replaces, existing tracking files|the related decision]]).

## 2026-11-12 — The implementation of the decisions of 2026-11-12 (branch `v1.2.0`, on the server)

- **Objective**: the author asked Claude Code to implement, autonomously, the P1 and P2 tasks that the decisions of
  2026-11-12 left in [[../TODO.md]], one commit and one push for each task, with the rules of the review sessions
  (`COPILOT_SIGUIENTE_SESION.md` §2).
- **Affected files**: those of each task, in its entry of [[../DEVLOG.md]].
- **Finding or decision**: the choices that the decisions do not cover are in
  [[decisions.md#2026-11-12 — The implementation of the decisions of 2026-11-12: the choices that they do not cover|the entry of the implementation]].
  By task:
  - Comfort standards 9 and 10: 10 reads PMOT, and 9 the mean of the 7 previous days that the EMS calculates (the
    code of the outdoor metric of the custom model, `'ndrm'` with 7 days, in every model with a zone of 9); the heating
    setpoint of comfort mode 1 of 9 out of its limits takes the minus sign. A model without that code whose zone is
    edited by hand to comfort standard 9 stops EnergyPlus (documented); a zone that leaves 9 gets `'pmot'` again. With
    `Seville_Present.epw` and a year, their comfort temperatures change by up to 2.0 and 1.7 K (0.6 K on average).
  - A19 with S1: where the minimum or the maximum of the setpoints binds, the thermostat gets it with the tolerance
    (20.1 and 25.9 °C with limits of 20 and 26 °C), and the setpoints without the tolerance are the limits. A maximum
    less than twice the tolerance above the minimum is now a `ValueError` (the thermostats on both would cross), as
    the window of the limiter of the drift; the warning of S1 and check 5 compare the setpoints of the thermostats.
  - A24: every zone of a model with the code of JPN Aqilah 2025 has the inputs of its static setpoints (the defaults
    in the zones of the other comfort standards), so a zone edited by hand to comfort standard 23 runs in EnergyPlus;
    the golden master changes in `s01` to `s06` and `s09` only (two lines in each zone).
  - E-F1 measured again (A1 and A2): with 110.7, 115 and 126 W/person, the SET of pythermalcomfort is 0.05, 0.33 and
    0.94 to 0.97 K below the Pierce SET of EnergyPlus on average (standing, a year in Seville), and 0.05 to 0.06 K at
    the three activity levels without the term of the activity of the convective coefficient of its real environment,
    which the code of EnergyPlus has only in the standard environment (its Engineering Reference gives it for the
    model): both SET agree up to about 1.05 met only. The 1.8 m² of the hooks, instead of the 1.8258 m² of the Pierce
    model, change the SET by 0.01 to 0.02 K. The draft of the issue for EnergyPlus, which the author posts, is
    [[BORRADOR_issue_EnergyPlus_SET_Pierce_2026-11-12.md]].
  - A4: `run_ep` raises a `ValueError` with the EMS backend when a model of the folder is prepared for a hook (the
    programs `ApplyHookSetpoints_<zone>`), and the backend of the API warns (`MissingHookWarning`) when such a model
    gets no hook before its EMS programs; before, it ran with the setpoints of the comfort standard of its zones and
    the outputs of the hook at 0, in silence. A test of `Table` that ran such a model with the EMS backend now runs it
    with the API and the hook.
  - A25: `modify_accis` gives the warning of RMOT when a call without `epw` writes the programs of the outdoor metric
    again and the zones of JPN Aqilah 2025 of the model lose the running mean of the weather file, and the warning of
    the metrics that begin with PMOT no longer names theirs.
  - A8: `AddAccis` and `modify_accis` warn when a zone gets `drift_mode='window'`, an experimental mode; `'rate'` is
    the recommended one. Measured again (the sample model in Seville): with the window, the heating coils use 32 488
    kWh in April instead of 125.9 kWh, and the VRF system 21 715 kWh of electricity instead of 7817 kWh; the rate
    changes the setpoints on two Mondays of April only (152.9 kWh).
  - The reference SET: the documentation and the docstrings say that the SET of reference of the causal band is that
    of pythermalcomfort (that of the database of the model, calculated standing), no longer "provisional", and that
    the Pierce SET of EnergyPlus is the indicator that every model has, an approximation up to about 1.05 met.
- **Validation**: in the entry of each task of [[../DEVLOG.md]] (the tests of the task, EnergyPlus 25.1 with both
  backends where the EMS code changes, and the golden master, compared line by line before writing it again).
- **Next step**: the review of Claude Science of sessions 2 and 3, which also covers this session; the message of the
  author to Ruiji Sun, the jar of the Future Weather Generator and the issue for EnergyPlus.

## 2026-11-12 — The decisions on the six open questions, taken for the author (branch `v1.2.0`, on the server)

- **Objective**: the author delegated to Claude Code all the decisions that were open in [[questions.md]] after
  session 3, to be taken with the papers of his library where needed.
- **Affected files**: [[decisions.md]], [[questions.md]], [[../TODO.md]], [[../ROADMAP.md]], [[../DEVLOG.md]].
- **Finding or decision**: the thirteen verdicts are in
  [[decisions.md#2026-11-12 — The decisions on the six questions left open after session 3 of the review of 1.2.0|the decisions of 2026-11-12]].
  The two that waited for Ruiji Sun could be decided with sources: the paper builds its model with the SET of the
  ASHRAE Global Thermal Comfort Database II, version 2.1, whose script calculates it with `set_tmp` of pythermalcomfort
  (and the earlier paper of the same authors reads that column), so the reference SET of the causal band is that of
  pythermalcomfort; and EN 16798-1, Table B.5, has the seasonal limits that finding A15 missed. The code of EnergyPlus
  25.1 confirms findings A1 and A2 (1.8258 m², and no term of the activity in the convective coefficient of the real
  environment of its Pierce model).
- **Validation**: the sources of each verdict, read on the server (the entry in [[../DEVLOG.md]]); no code changed, no
  test run.
- **Next step**: the tasks of [[../TODO.md]] in the next implementation session; the review of Claude Science; the
  message of the author to Ruiji Sun, the jar of the Future Weather Generator and the issue for EnergyPlus.

## 2026-11-12 — The tests of pythermalcomfort with numba again (branch `v1.2.0`, on the server)

- **Objective**: run again the tests that Smart App Control kept from running (the report of session 3, section 5),
  once the author turned it off.
- **Affected files**: [[../TODO.md]], [[questions.md]], [[INFORME_SESION_v1.2.0_2026-11-11_3.md]] (an addendum),
  [[../DEVLOG.md]].
- **Finding or decision**: with numba 0.68.1, the five test files give 99 passed and `tests/core` 1542 passed and 2
  skipped: the 19 failures were the environment only. Smart App Control decides file by file with the reputation
  service of Microsoft, and its verdict changes (numba loaded on the day it was installed and was blocked from the
  next one).
- **Validation**: see the entry in [[../DEVLOG.md]].
- **Next step**: the review of Claude Science; the `TODO.md` entries of A1 and A2 and of the tests that skip without
  numba.

## 2026-11-12 — The final checks and the report of session 3 (branch `v1.2.0`, on the server)

- **Objective**: §8 of the instructions: the whole suites, the golden master, the documentation build, Python 3.9,
  and the report. Copilot stopped on 2026-11-11 (its monthly quota) with the tasks pushed and the report drafted;
  completed with Claude Code from the logs of its checks.
- **Affected files**: [[INFORME_SESION_v1.2.0_2026-11-11_3.md]], [[../DEVLOG.md]].
- **Finding or decision**: `tests/core`, 1511 passed, 19 failed and 14 skipped; the parametric suite, 520 passed; the
  golden master byte-identical; the documentation with the warnings of session 2. The 19 failures (and 12 of the
  skipped tests) are tests of session 2 that need pythermalcomfort, whose numba Windows Smart App Control blocks on
  the server since 2026-11-11; with a pure-Python stand-in of numba (the appendix of the report), the 99 tests of
  their five files pass.
- **Validation**: the report checked against `git log`, [[../TODO.md]], [[questions.md]] and the JSON file of the
  self-audit; the logs of the checks belong to `7cb4058`.
- **Next step**: the review of Claude Science of sessions 2 and 3; the answers of the author ([[questions.md]]); those
  tests again where numba loads.

## 2026-11-11 — The fixes of the self-audit of session 2 (branch `v1.2.0`, on the server)

- **Objective**: §7 of the instructions: fix the bugs and scientific findings (A1–A26) with a test that fails before,
  the small design, test, doc and minor ones in groups, and leave the others to the author.
- **Affected files**: `accim/sim/comfort_hooks.py` (A7, A3, A5), `accim/data/postprocessing/indoor_adaptation.py`
  (A12, A13, A14), `accim/sim/ems/drift_limiter.py` and `accim/sim/accis.py` (A9, A11), `param_accis.py` (A9, A23),
  `accim/sim/ems/outdoor_metric.py` (A21), the documentation (A16–A18, A20, A22, A24, A26), [[questions.md]],
  [[../TODO.md]], [[../DEVLOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§43).
- **Finding or decision**: the bugs A3, A7, A9 and A12 fixed; A24 (a bug) contradicts the decision of G4, so it is
  documented and left to the author with A1, A2, A4, A8, A15, A19 and A25 ([[questions.md]]); A10 was covered by S3.
- **Validation**: see the entries of each fix in [[../DEVLOG.md]].
- **Next step**: the final checks and the report of the session.

## 2026-11-11 — S5: the notes of the accepted decisions 1, 7, 16 and 22 (branch `v1.2.0`, on the server)

- **Objective**: the instructions of the verdicts of decisions 1 (an example of a clothing function of the
  temperature at 6:00), 7 (the absolute path of the CSV files of the `Schedule:File` objects), 16 (comfort modes 0 and
  3 of comfort standard 24) and 22 (the one-day delay of the running means of EnergyPlus in the first timestep).
- **Affected files**: [[../docs/source/4_detailed use.md]] (4.2, 4.2.2, 4.3.1, 4.8),
  `tests/core/test_pmv_input_parameters.py`, `tests/core/test_sun2026_set.py`, [[../TODO.md]], [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§42), [[../DEVLOG.md]].
- **Finding or decision**: EnergyPlus 25.1 stops before the simulation when the CSV file of a `Schedule:File` object
  is not found; the comfort temperature of INT EN16798 in the first timestep of each day is that of the day before (up
  to 0.44 K away in Seville).
- **Validation**: see the entry of S5 in [[../DEVLOG.md]].
- **Next step**: the fixes of the self-audit.

## 2026-11-11 — S4: the indicators of the causal band with the SET of pythermalcomfort (branch `v1.2.0`, on the server)

- **Objective**: decision 9 (provisional, pending Ruiji Sun): keep the Pierce SET in the indicators of F3 and add,
  off by default, the same indicators with the SET of pythermalcomfort (`set_of_results`).
- **Affected files**: `accim/data/postprocessing/indoor_adaptation.py`, `tests/core/test_indoor_adaptation.py`,
  [[../docs/source/4_detailed use.md]] (4.7.6), [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§41),
  [[questions.md]], [[../DEVLOG.md]].
- **Finding or decision**: `table_indicators(..., pythermalcomfort_set={'met': ..., 'clo': ..., 'air_speed': ...})`
  reads the conditions of the zones from the CSV file of each simulation; the inputs of the occupants are constant
  (E-F1 used the schedules of the People objects): the design choices are provisional in [[questions.md]].
- **Validation**: see the entry of S4 in [[../DEVLOG.md]].
- **Next step**: S5 (the notes of the accepted decisions #1, #7, #16 and #22).

## 2026-11-11 — S3: the reference of the rate of the limiter of the drift (branch `v1.2.0`, on the server)

- **Objective**: decision 13: the reference of the daily limit of `drift_mode='rate'` is the mean of the setpoints
  applied in the occupied timesteps of the previous day (not those of its last timestep).
- **Affected files**: `accim/sim/ems/drift_limiter.py`, `accim/sim/accis.py`, `tests/core/test_drift_limiter.py`,
  [[../docs/source/4_detailed use.md]] (4.2.7), [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§40),
  [[decisions.md]], [[../DEVLOG.md]].
- **Finding or decision**: as decided; the same results with the setpoints of the ACCIS (constant in the occupied
  timesteps of each day); after a day without occupants, the reference of the last occupied day (decision 14).
- **Validation**: see the entry of S3 in [[../DEVLOG.md]].
- **Next step**: S4 (the indicators of the causal band with the SET of pythermalcomfort).

## 2026-11-11 — S2: the static setpoints of Qatar, 20 and 26 °C (branch `v1.2.0`, on the server)

- **Objective**: decision 20: the static setpoints of the YAML file of Qatar are those of the offices of category II
  of EN 16798-1, Table B.2 (20 and 26 °C), not 25.5 °C (category I).
- **Affected files**: the two copies of `qat_indraganti2018_hvac.yaml`, the How-to notebook of the registry (source and
  exported), `tests/core/test_comfort_standard_registry.py`, [[../docs/source/4_detailed use.md]] (4.2.5),
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§39), [[decisions.md]], [[../DEVLOG.md]].
- **Finding or decision**: as decided; only comfort modes 0 and 1 of comfort standard 102 change.
- **Validation**: see the entry of S2 in [[../DEVLOG.md]].
- **Next step**: S3 (the reference of the rate of the limiter of the drift).

## 2026-11-11 — S1: the warning of the minimum and maximum with the setpoints of the comfort model (branch `v1.2.0`, on the server)

- **Objective**: decision 19: replace the comparison of the minimum and maximum of the setpoints with `ACSTaul`/
  `AHSTall` by the setpoints of the comfort model of each zone with the weather file (`compute_setpoints`).
- **Affected files**: `accim/sim/ems/setpoint_limits.py`, `accim/sim/accis.py`, `tests/core/test_setpoint_limits.py`,
  [[../docs/source/4_detailed use.md]] (4.2.3), [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§38),
  [[decisions.md]], [[questions.md]], [[../DEVLOG.md]].
- **Finding or decision**: one warning per zone with the limit, the extreme setpoint, the days and the first day; no
  warning without `epw`; the first timestep of a run period (running means of 0 in the EMS) can cross by itself. The
  details are provisional in [[questions.md]].
- **Validation**: see the entry of S1 in [[../DEVLOG.md]].
- **Next step**: S2 (the static setpoints of Qatar).

## 2026-11-11 — The self-audit of session 2 (branch `v1.2.0`, on the server)

- **Objective**: audit the 15 code tasks of session 2 with the checklist of the handoff of Claude Science (Appendix A),
  as an independent reviewer, without fixing anything.
- **Affected files**: [[attachments/autoauditoria_sesion2_v1.2.0.json]], [[../DEVLOG.md]].
- **Finding or decision**: three read-only reviewers on a worktree at `fe42957`; G1, G2 and H5 correct, the others
  correct with issues; 26 findings (5 bug, 3 scientific, 6 design, 3 test, 4 doc, 5 minor). numba is blocked by Smart
  App Control on this server, so what needs `pythermalcomfort.models` was not assessed.
- **Validation**: see the entry of the self-audit in [[../DEVLOG.md]].
- **Next step**: S1; the fixes of the audit after S5.

## 2026-11-11 — Step 0 of session 3: the verdicts on the 23 provisional decisions (branch `v1.2.0`, on the server)

- **Objective**: apply the verdicts of the handoff of Claude Science (§3) to the 23 provisional decisions of the
  session of the review v04, and record the pending items (comfort standards 9 and 10; the validation study of F3).
- **Affected files**: [[decisions.md]], [[questions.md]], [[../TODO.md]], [[../DEVLOG.md]].
- **Finding or decision**: 18 accepted (four with an instruction for S5), 3 changed (#13, #19, #20: tasks S3, S1,
  S2), 2 open with Ruiji Sun (#9, #12); comfort standards 9 and 10 stay as they are by the decision of the author,
  with the verified analysis in [[../TODO.md]] and a question in [[questions.md]]. Found while starting: Smart App
  Control (enforcement) blocks the DLLs of numba 0.68.1 on this server since 2026-11-11, so `pythermalcomfort.models`
  cannot be imported (the tests of the hooks of the SET and of the ATHB fail or skip).
- **Validation**: see the entry of Step 0 in [[../DEVLOG.md]].
- **Next step**: the self-audit of session 2 (`notes/attachments/autoauditoria_sesion2_v1.2.0.json`).

## 2026-11-11 — The report of the session of the review v04 (branch `v1.2.0`, on the server)

- **Objective**: the report that the task asks for once the list of v04 §7 is done: tasks and commits, deviations,
  TODO entries, provisional decisions, tests and backends, blocked items.
- **Affected files**: [[INFORME_SESION_v1.2.0_2026-11-10_2.md]], [[../DEVLOG.md]].
- **Finding or decision**: every task of v04 §7 (Step 0, G1–G5, H1, E-F1, F1–F3, H2–H6) is done and pushed; still
  blocked: CIBSE TM52/TM59, the jar of the Future Weather Generator and the validation study of F3; 23 provisional
  decisions wait for the author in [[questions.md]].
- **Validation**: the report checked against [[../DEVLOG.md]] and `git log`.
- **Next step**: the answers of the author ([[questions.md]], [[../TODO.md]]).

## 2026-11-10 — H6: the clothing insulation as a function of the outdoor temperature (branch `v1.2.0`, on the server)

- **Objective**: task H6 of v04 §7 (A5, decision of §6): `clothing_insulation=callable` of `set_pmv_input_parameters`,
  written as a `Schedule:File` from the weather file with `accim.sim.preview.outdoor_metrics`.
- **Affected files**: `accim/sim/apmv.py`, `accim/sim/preview.py`, `tests/core/test_pmv_input_parameters.py`,
  `tests/core/test_preview.py`, [[../docs/source/4_detailed use.md]] (4.8), [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§37), [[../DEVLOG.md]], [[../TODO.md]], [[questions.md]].
- **Finding or decision**: EnergyPlus 25.1 reads the Schedule:File hour by hour in standard time (also with the
  daylight saving time of the model), but reports *Zone Thermal Comfort Clothing Value* as 0 with the method
  `ClothingInsulationSchedule` (the PMV uses the schedule); `read_epw_dry_bulb` failed on the sample `Seville.epw`
  (a header in Latin-1), fixed. The choices of the function, its temperature and the CSV name are in [[questions.md]].
- **Validation**: see the entry of H6 in [[../DEVLOG.md]].
- **Next step**: the session report (`notes/INFORME_SESION_v1.2.0_2026-11-10_2.md`).

## 2026-11-10 — H5: the outdoor metric of each regime, and several regimes in the YAML files (branch `v1.2.0`, on the server)

- **Objective**: task H5 of v04 §7 (decisions 1 and 4 of §6, findings B2-1 and B2-2): an outdoor metric for each
  regime of the custom model; several regimes of a comfort standard defined by its data (key `regimes`); the
  documentation of the averaged `CustomRegime_<zone>` and of the alternation of `'hvac_off'`/`'hvac_on'`.
- **Affected files**: `accim/sim/arguments.py`, `accim/sim/standards.py`, `accim/sim/ems/custom_regimes.py`,
  `outdoor_metric.py` and `standard_lines.py`, `accim/sim/accis.py`, `accim/utils/ems_code.py` and `verification.py`,
  `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py`, `accim/gui/forms.py`,
  [[../docs/source/4_detailed use.md]] (4.2.4, 4.2.5), [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§36),
  [[../DEVLOG.md]], [[../TODO.md]], [[questions.md]].
- **Finding or decision**: a comfort standard with regimes reuses the program of the regimes of the custom model (its
  branches read the inputs of the custom model and its metric is always `Tout_metric`), so it gives exactly the
  setpoints of the custom model with the same regimes; the programs of the outdoor metric are kept while they calculate
  the metrics of the regimes (a plain `modify_accis` no longer loses the weather-file start). Provisional choices in
  [[questions.md]] (the schema of `regimes`, the EMS code, the names and the programs kept).
- **Validation**: see the entry of H5 in [[../DEVLOG.md]].
- **Next step**: H6 (`clothing_insulation=callable` as a Schedule:File).

## 2026-11-10 — H4: the saturation, frequencies and ranges of the hook of the ATHB (branch `v1.2.0`, on the server)

- **Objective**: task H4 of v04 §7 (findings A4-1 to A4-3, the test finding of §3.4): report the setpoints of the
  ATHB at the limits of their range, the frequencies of its outputs, the ranges of met and air speed, the documentation
  of W/person and the relative air speed, and a bounded scientific test.
- **Affected files**: `accim/sim/comfort_hooks.py`, `accim/sim/energyplus_api/runner.py`, `accim/constants.py`,
  `accim/data/postprocessing/optional_output_columns.py`, [[../docs/source/4_detailed use.md]] (4.7.5, 4.9.1),
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§35), [[../DEVLOG.md]], [[../TODO.md]].
- **Finding or decision**: in a July week of the sample model the ATHB_PMV stays within 0.25 of the cooling setpoint
  in every occupied timestep with cooling (at most 0.68); the reported ATHB_PMV differs from that of the averaged
  outputs of the previous timestep by up to 0.02 (the sensors read the last system timestep).
- **Validation**: see the entry of H4 in [[../DEVLOG.md]].
- **Next step**: H5 (the outdoor metric of each regime, and several regimes in the YAML files).

## 2026-11-10 — H3: the constant long-term range, Method C and Table by timestep (branch `v1.2.0`, on the server)

- **Objective**: task H3 of v04 §7 (findings C2-1 and D1-1, decision 5 of §6, verdict #20): `long_term_range` with the
  constant limits of EN 16798-1, Table B.2; Method C (the PPD-weighted hours) for the setpoints based on the PMV;
  `Table` with `source_frequency='timestep'`; the hourly indicators of `Table` against the timestep EMS counters.
- **Affected files**: `accim/sim/ems/long_term_discomfort.py`, `accim/sim/accis.py`, `accim/sim/pmv_index.py`,
  `accim/sim/apmv.py`, `accim/utils/verification.py`, `accim/parametric_and_optimisation/objectives.py` and `main.py`,
  `accim/data/postprocessing/main.py`, `long_term_discomfort.py` and `pmv_index_columns.py`, the GUI,
  [[../docs/source/4_detailed use.md]] (4.2.6, 4.7.3, 4.7.4, 4.8.2 new, 4.6.1, 4.10), [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§34), [[../DEVLOG.md]], [[../TODO.md]], [[questions.md]].
- **Finding or decision**: Method C compares the PMV of the previous timestep with the setpoints of the index converted
  to the scale of the PMV by the inverse of the index (as the thermostats); the building type is required for
  categories III and IV of Table B.2 (two provisional choices in [[questions.md]]).
- **Validation**: see the entry of H3 in [[../DEVLOG.md]] (EnergyPlus 25.1, both backends, checks 3 and 6).
- **Next step**: H4 (the saturation of the ATHB setpoints and the rest of A4).

## 2026-11-10 — H2: T0 of te_ref_nl from the weather file (branch `v1.2.0`, on the server)

- **Objective**: task H2 of v04 §7: T0 of `te_ref_nl` is the mean of the maximum and minimum of the whole day (verdict
  #8), from the weather file as a `Schedule:File`, or that of the previous day without it.
- **Affected files**: `accim/sim/schedule_files.py` (new), `accim/sim/ems/outdoor_metric.py`, `accim/utils/ems_code.py`,
  `accim/sim/preview.py`, [[../docs/source/4_detailed use.md]], [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]]
  (§33), [[../DEVLOG.md]], [[../TODO.md]], [[questions.md]].
- **Finding or decision**: EnergyPlus 25.1 gives the *Schedule Value* of the day from its first timestep at
  `BeginTimestepBeforePredictor`, so Te,ref is constant within each day and `compute_setpoints` reproduces it exactly;
  the CSV file goes to the folder of the model with its absolute path (two provisional choices in [[questions.md]]).
- **Validation**: `tests/core/test_outdoor_metric.py` 42 passed (EnergyPlus 25.1, both backends identical); `tests/core` 1386 passed, 2 skipped; parametric 511 passed; docs with the same 35 warnings.
- **Next step**: H3 (long-term range of EN 16798 and Method C).

## 2026-11-10 — F3: the indicators of the adaptation to the indoor climate (branch `v1.2.0`, on the server)

- **Objective**: task F3 of block F: the indicators of the causal band, the overcooling, T_rm_in and Tn_exp and the
  cooling effect for every simulation, and the design of the validation study.
- **Affected files**: `accim/data/postprocessing/indoor_adaptation.py` (new), `accim/data/postprocessing/main.py`,
  `accim/data/postprocessing/optional_output_columns.py`, `accim/sim/people.py`, the GUI,
  [[../docs/source/4_detailed use.md]], [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§32), [[../DEVLOG.md]],
  [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The indicators of the adaptation to the indoor climate measure every model with the SET of EnergyPlus (F3)|the decision]].
  The names of the proposal (`SET`, `PMV_SET`) would contain or be contained in others (`SET (°C)` of the hook,
  `<zone>_PMV`), so they are `SET_Pierce (°C)` and `SET_Pierce_PMV`; four provisional choices in [[questions.md]]; the
  simulations of the study wait for the author ([[../TODO.md]]).
- **Validation**: `tests/core/test_indoor_adaptation.py` 20 passed (also with EnergyPlus 25.1); `tests/core` 1377 passed, 2 skipped; docs with the same 35 warnings.
- **Next step**: H2 (T0 of `te_ref_nl` from the weather file).

## 2026-11-10 — F2: the limiter of the drift of the setpoints (branch `v1.2.0`, on the server)

- **Objective**: task F2 of block F: `drift_mode` 'rate' or 'window' (Parkinson, de Dear & Brager, 2020), an option of
  the ACCIS of each zone in Erl, for every comfort standard and the hooks.
- **Affected files**: `accim/sim/ems/drift_limiter.py` (new), `accim/sim/ems/inputs.py`, `accim/sim/generation.py`,
  `accim/sim/accis.py`, `accim/utils/ems_code.py`, `accim/sim/preview.py`, `accim/utils/verification.py`, the
  parametric module, the GUI, `Table`, [[../docs/source/4_detailed use.md]], [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§31), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The limiter of the drift of the setpoints is an option of the ACCIS of each zone, in Erl (F2)|the decision]].
  The window clips both setpoints, so its band is 2 K wide around T_rm_in by default; three provisional choices in
  [[questions.md]].
- **Validation**: `tests/core/test_drift_limiter.py` 11 passed (both backends identical with EnergyPlus 25.1, T_rm_in
  of pandas within 1e-4 K); `drift_mode=None` gives byte-identical output IDFs; `tests/core` 1356 passed, 2 skipped;
  `tests/parametric_and_optimisation` 511 passed; docs with the same 35 warnings.
- **Next step**: F3 (the indicators in `Table`).

## 2026-11-10 — F1: comfort standard 24, INT Sun2026 SET (branch `v1.2.0`, on the server)

- **Objective**: task F1 of block F: the causal SET model of Sun, Brager & Schiavon (2026) as comfort standard 24, a
  thin layer on the hook of the SET by bisection, with the inputs of the People objects and `tr_mode`.
- **Affected files**: `accim/sim/comfort_hooks.py`, `accim/sim/standards.py`, `accim/sim/generation.py`,
  `accim/sim/prompts.py`, `accim/utils/ems_code.py`, `accim/gui/forms.py`,
  `accim/data/postprocessing/optional_output_columns.py`, `tests/core/test_sun2026_set.py`,
  [[../docs/source/4_detailed use.md]], [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§30), [[../DEVLOG.md]],
  [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — Comfort standard 24, INT Sun2026 SET, is a thin layer on the hook of the SET by bisection (F1)|the decision]].
  The SET of the hook is 0.08 K (winter) and 0.155 K (summer) below the Pierce SET of EnergyPlus (at most 0.29 K,
  hourly); three provisional decisions in [[questions.md]].
- **Validation**: `tests/core/test_sun2026_set.py` 18 passed (two weeks with EnergyPlus 25.1; both backends identical
  without the hook).
- **Next step**: F2 (the limiter of the setpoint drift).

## 2026-11-10 — E-F1: the SET of EnergyPlus (Pierce) against pythermalcomfort (branch `v1.2.0`, on the server)

- **Objective**: task E-F1 of the review v04 and of block F: compare, hour by hour, the SET of EnergyPlus's Pierce
  model with `set_tmp` of pythermalcomfort from the same outputs, before F1.
- **Affected files**: `accim/sim/people.py` (`add_thermal_comfort_model`), `tests/core/test_pierce_set.py`,
  [[../docs/source/4_detailed use.md]], [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§29), [[../DEVLOG.md]],
  [[../TODO.md]], [[decisions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The SET of EnergyPlus (Pierce) against that of pythermalcomfort, measured (E-F1)|the decision]].
  pythermalcomfort is 0.045 K below EnergyPlus on average (at most 0.20 K) standing, 0.116 K (at most 0.34 K) sitting.
- **Validation**: the yearly EnergyPlus 25.1 run of the test reproduces the table within 0.001 K; 50 related tests
  passed.
- **Next step**: F1 (the causal SET of Sun et al. 2026 as comfort standard 24).

## 2026-11-10 — H1: the minimum and maximum of the setpoints (branch `v1.2.0`, on the server)

- **Objective**: task H1 of the review v04 (§4.5): rename `heating_setpoint_floor`/`cooling_setpoint_ceiling` to
  `heating_setpoint_minimum`/`cooling_setpoint_maximum` (EMS `AHSTmin`/`ACSTmax`, parameters
  `HeatingSetpointMinimum`/`CoolingSetpointMaximum`) with deprecated aliases.
- **Affected files**: `accim/_deprecation.py`, `accim/sim/arguments.py`, the modules of the ACCIS, the EMS code, the
  verification, the GUI and the parametric module, [[../docs/source/4_detailed use.md]], [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§28), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The minimum and maximum of the setpoints replace the floor and ceiling (H1)|the decision]].
  The warnings say "since accim 1.2.0" (`accim._deprecation` takes the version).
- **Validation**: `tests/core` 1323 passed, 2 skipped (golden master byte-identical); `tests/parametric_and_optimisation`
  509 passed; documentation build with the baseline warnings.
- **Next step**: E-F1 (EnergyPlus Pierce SET against pythermalcomfort).

## 2026-11-10 — G5: the housekeeping of the review of 1.2.0 (branch `v1.2.0`, on the server)

- **Objective**: task G5 of the review v04 (A3-1, A3-2, B5-1 to B5-3, B1-2, B3-1 to B3-3, E4-1 to E4-3, §3.4, §3.5).
- **Affected files**: `accim/sim/ems/setpoint_limits.py`, `erl.py` (`format_number`), `outdoor_metric.py`,
  `standard_lines.py`, `custom_regimes.py`, `accim/sim/standards.py`, `pmv_index.py`, `apmv.py`, `accis.py`,
  `preview.py`, `accim/utils/ems_code.py`, `verification.py`, `accim/run/run.py`, `energyplus_api/runner.py`,
  `accim/data/morphing.py`, the GUI label, the YAML of Qatar and the How-to notebook of the registry,
  [[../docs/source/4_detailed use.md]], [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§27), [[../DEVLOG.md]],
  [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The floor and ceiling bound the setpoints with and without the tolerance and are exact; the housekeeping of the review (G5)|the decision]].
  Provisional: verdict #13 read literally (ACSTaul/AHSTall are outdoor applicability limits), the static setpoints of
  Qatar (25.5 vs 26 °C of Table B.2) and the exact floor ([[questions.md]]).
- **Validation**: `tests/core` 1286 passed, 2 skipped; golden master 35 passed (byte-identical);
  `tests/parametric_and_optimisation` 507 passed; EnergyPlus 25.1: checks 4 and 5 with 0 mismatches, both backends
  identical; outdoor metrics of EnergyPlus against pandas within 1e-9 °C; documentation build with the baseline warnings.
- **Next step**: H1 (rename the floor and ceiling).

## 2026-11-10 — G4: JPN Aqilah 2025 with the weather file, and its static setpoints (branch `v1.2.0`, on the server)

- **Objective**: task G4 of the review v04 (findings B4-1, B4-2): comfort standard 23 with `rmot_alpha` from the weather
  file when it is given (RMOT and a warning otherwise), the test against 101, and `static_heating_setpoint` /
  `static_cooling_setpoint` (`StaticAHST`/`StaticACST`) in `AddAccis`, `modify_accis`, `zone_arguments`, the EMS code
  functions, the parametric module and the GUI.
- **Affected files**: `accim/sim/ems/static_setpoints.py` (new), `standard_lines.py`, `outdoor_metric.py`,
  `programs.py`, `objects.py`, `inputs.py`, `setpoint_lines.py`, `accim/sim/accis.py`, `generation.py`, `preview.py`,
  `standards.py`, `accim/utils/ems_code.py`, `verification.py`, the parametric module, the GUI, the golden files
  `s01`–`s06` and `s09`, [[../docs/source/4_detailed use.md]] (§4.1, §4.2, §4.2.5, §4.3, §4.3.1, §4.10),
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§26), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]],
  [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — JPN Aqilah 2025 reads the running mean of EN 16798-1 of the weather file when the model has its values, and its static setpoints are inputs of its zones (G4)|the decision]].
  Measured: the literal test criterion fails from 1 January (0.92 K on day 1, hours 2–24) and in some first hours of
  the year (0.1013 K, one timestep of reading lag); the test uses the starts of 1 April and 1 July and the hours 2–24
  (provisional, [[questions.md]]).
- **Validation**: `tests/core` 1269 passed, 2 skipped; golden master 35 passed (7 files written again, only the static
  lines of 23 and their declaration); `tests/parametric_and_optimisation` 507 passed; EnergyPlus 25.1: check 4 with 0
  mismatches (also `Tout_metric`), EMS and API backends identical with and without the weather file; documentation
  build with the warnings of the baseline.
- **Next step**: G5.

## 2026-11-10 — G3: the SET in the callbacks of EnergyPlus (branch `v1.2.0`, on the server)

- **Objective**: task G3 of the review v04 (findings A6-1 to A6-4): `SetSetpointHook(method='bisection')`, its
  outputs, `set_of_results`, the posture by default, and the documentation of `set_tmp`.
- **Affected files**: `accim/sim/comfort_hooks.py`, `accim/sim/energyplus_api/runner.py`,
  `accim/data/postprocessing/optional_output_columns.py`, `tests/core/test_comfort_hooks.py`,
  [[../docs/source/4_detailed use.md]] (§4.9, §4.9.2, §4.7.5), [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]]
  (§25), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The hook of the SET calculates by bisection in the callbacks on request, after calling pythermalcomfort before the API of EnergyPlus is loaded (G3)|the decision]].
  The access violation of `set_tmp` is its first call in a process that has loaded the library of the API of
  EnergyPlus (Python 3.14.3, numba 0.68.1), not the callback; `run_simulation` calls `prepare()` before loading it.
- **Validation**: 28 tests of the hooks (two days by bisection with EnergyPlus 25.1, exact to 1e-6), 58 with the API
  tests, 47 of Table; documentation build unchanged (59 warnings).
- **Next step**: G4.

## 2026-11-10 — G2: the running mean of ASHRAE 55 from the 2nd to the 30th of January (branch `v1.2.0`, on the server)

- **Objective**: task G2 of the review v04 (finding E1-1): `compute_setpoints` reproduces the PMOT of EnergyPlus with
  a run period that begins between the 2nd and the 30th of January.
- **Affected files**: `accim/sim/preview.py`, `accim/utils/verification.py`, `tests/core/test_preview.py`,
  `tests/core/test_verification.py`, [[../docs/source/4_detailed use.md]] (§4.3.1, §4.6.1), [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§24), [[../DEVLOG.md]], [[../TODO.md]].
- **Finding or decision**: EnergyPlus 25.1 writes the mean of 31 December over the day before such a run period for
  30 days; accim does the same now (10.574306 °C on 8 January, the value of EnergyPlus).
- **Validation**: 44 tests (one with EnergyPlus 25.1 from 8 January); the documentation build, the same 59 warnings
  as before the session (pandoc installed for it).
- **Next step**: G3.

## 2026-11-10 — G1: the hooks of the ATHB and of the SET and the counters of the ACCIS (branch `v1.2.0`, on the server)

- **Objective**: task G1 of the review v04 (finding A4/A6-1): the hour counters and outputs of the ACCIS follow the
  setpoints of the hooks.
- **Affected files**: `accim/sim/ems/hook_setpoints.py` (new), `accim/sim/comfort_hooks.py`,
  `accim/sim/ems/setpoint_limits.py`, `accim/run/run.py`, `accim/utils/verification.py`,
  `tests/core/test_comfort_hooks.py`, [[../docs/source/4_detailed use.md]] (§4.9, §4.9.1, §4.9.2, §4.6.1),
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§23), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]],
  [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The hooks of the setpoints run before the EMS programs and give their setpoints to the ACCIS through a program of each zone (G1)|the decision]].
  Option (a) works by running the hooks before the programs and taking their setpoints right after SetAST; the
  thermostats get them with the tolerance (provisional, [[questions.md]]).
- **Validation**: 23 tests of the hooks (with EnergyPlus 25.1; both backends identical with and without the setpoints
  of a hook); 119 tests of the affected files; golden master unchanged.
- **Next step**: G2.

## 2026-11-10 — Step 0 of the review v04: the verdicts of the author and the unblocked tasks (branch `v1.2.0`, on the server)

- **Objective**: the step 0 of the task of the session: the 36 provisional decisions to [[decisions.md]] with the
  verdicts of v04 §5, `TODO.md` with v04 §6 and the renaming of B5, and the decision on `tr_mode` (v04 §4.4).
- **Affected files**: [[decisions.md]], [[questions.md]], [[../TODO.md]], [[../DEVLOG.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts]],
  [[decisions.md#2026-11-10 — The decisions of the author on the blocked tasks of 1.2.0 and the name of the setpoint limits of B5|the blocked tasks]]
  and [[decisions.md#2026-11-10 — With tr_mode='zone', the inverted SET setpoint of air temperature is written as an operative-temperature setpoint|tr_mode]].
- **Validation**: a script moved the entries and checked one verdict for each; no code changes.
- **Next step**: G1, then the list of v04 §7 in the order of the author.

## 2026-11-10 — The report of the session (branch `v1.2.0`, on the server)

- **Objective**: the report that the author asked for at the end of the list of proposals.
- **Affected files**: [[INFORME_SESION_v1.2.0_2026-11-10.md]], [[../DEVLOG.md]].
- **Finding or decision**: all the proposals of the list are done; the parts that wait for the author or for missing
  documents and tools are blocked tasks in [[../TODO.md]], and 36 decisions taken provisionally are in [[questions.md]].
- **Validation**: the figures of the report checked against [[../DEVLOG.md]] and `git log`.
- **Next step**: the answers of the author.

## 2026-11-10 — D2, completed: the optional outputs of the ACCIS and of the ATHB in Table (branch `v1.2.0`, on the server)

- **Objective**: the task of D2 left in `TODO.md` (its outputs of A4, B1 and B5, and B2), unblocked once A4 was done.
- **Affected files**: `accim/data/postprocessing/optional_output_columns.py` (new), `accim/data/postprocessing/main.py`,
  `tests/core/test_table_optional_outputs.py` (new), [[../docs/source/4_detailed use.md]] (§4.7.5),
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§22), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]],
  [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The optional outputs of the ACCIS and of the ATHB in Table (D2, completed)|the decision]].
  Table dropped these outputs with `standard_outputs=True` and added up the ATHB_PMV over time; the outdoor metric of
  each zone keeps its EMS name, so that `Tout_metric (°C)` is not part of other names.
- **Validation**: 18 new tests (one with EnergyPlus 25.1); the tests of Table; the whole suite (1783 passed, 2
  skipped); the documentation build (59 warning lines, as before).
- **Next step**: the report of the session.

## 2026-11-10 — A6: the setpoints of the SET and the PPD (branch `v1.2.0`, on the server)

- **Objective**: A6, the last proposal of the list of the author.
- **Affected files**: `accim/sim/comfort_hooks.py`, `tests/core/test_comfort_hooks.py`, `setup.py`, `accim/run/run.py`,
  [[../docs/source/4_detailed use.md]] (§4.8, §4.9.2), [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§21),
  [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The setpoints of the SET are a hook of the API backend with a table by relative humidity (A6)|the decision]].
  `pythermalcomfort.models.set_tmp` stops EnergyPlus with an access violation at its first call in a callback (not the
  stack, not the compilation), so the hook tabulates its setpoints by humidity before the simulation.
- **Validation**: 6 new tests (one with EnergyPlus 25.1 through `run_ep(backend='api', hooks=[hook])`); the whole suite
  (1765 passed, 2 skipped); the documentation build (59 warning lines, as before).
- **Next step**: R-06 in `ROADMAP.md`, and the report of the session.

## 2026-11-10 — A4: the setpoints of the ATHB with the Python API (branch `v1.2.0`, on the server)

- **Objective**: A4, after E4, in the order of the author (with D10 and the adjustment of the brief: `help(ErlController)`
  read first).
- **Affected files**: `accim/sim/comfort_hooks.py` (new), `accim/run/run.py`, `setup.py`,
  `tests/core/test_comfort_hooks.py` (new), [[../docs/source/4_detailed use.md]] (§4.9.1),
  `docs/source/2_installation.md`, `docs/source/api/accim.sim.rst`, [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§20), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The setpoints of the ATHB are a hook of the backend of the Python API on the setpoints of the ACCIS (A4)|the decision]].
  The equations of v03 are those of the installed pythermalcomfort 4.8.1 (read in its source), which needs Python 3.11
  or later. The sensors of the zones read the last values of the previous timestep, while the outputs are the means of
  each timestep, so the ATHB_PMV of the outputs cannot be recalculated exactly from them; the setpoints can.
- **Validation**: 12 new tests (a fake controller, and EnergyPlus 25.1 with `run_ep(backend='api', hooks=[hook])` and
  both backends without the hook); the whole suite; the documentation build.
- **Next step**: A6.

## 2026-11-10 — E4: the future weather files with pyfwg (branch `v1.2.0`, on the server)

- **Objective**: E4, after C2, in the order of the author.
- **Affected files**: `accim/data/morphing.py`, `setup.py`, `tests/core/test_morphing.py`, `tests/README.md`,
  [[../docs/source/4_detailed use.md]] (§4.5.1), `docs/source/2_installation.md`, [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§19), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — morph_epws delegates in pyfwg on request, for the global tool, and pyfwg and pyweatherfiles are the extra accim[weather] (E4)|the decision]].
  The API of pyfwg was read in its installed source (0.4.0, from PyPI); its command for the version 3 of the tool has
  more arguments than that of `engine='java'` ([[../TODO.md]]). The jar of the tool is not on the server, so the
  notebook waits.
- **Validation**: 10 new tests (pyfwg mocked, and the arguments and constants against the installed pyfwg; one with
  the tool, skipped without its jar); the tests of `tests/core`; the documentation build.
- **Next step**: A4.

## 2026-11-10 — C2: the long-term comfort objectives (branch `v1.2.0`, on the server)

- **Objective**: C2, after B4, in the order of the author.
- **Affected files**: `accim/sim/ems/long_term_discomfort.py` (new), `accim/sim/accis.py`,
  `accim/parametric_and_optimisation/objectives.py`, `accim/parametric_and_optimisation/main.py`,
  `accim/data/postprocessing/long_term_discomfort.py`, `accim/utils/verification.py`, `accim/gui/app.py`,
  `accim/gui/forms.py`, `tests/core/test_long_term_discomfort_counters.py` (new) and three test files,
  [[../docs/source/4_detailed use.md]], `docs/source/parametric_and_optimisation.rst`, [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§18), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-10 — The long-term comfort objectives are EMS counters of the ACCIS with the range of its setpoints, opt-in (C2)|the decision]].
  The reducers of besos get one output each, so the indicators are counted by the EMS; EnergyPlus writes the units of
  the EMS output variables in capitals (`Kh` is reported as `[KH]`). Method C and the weekly and monthly constraints
  wait ([[questions.md]], [[../TODO.md]]).
- **Validation**: 22 new tests of the counters, 6 of the reducers and the parametric module, and 1 new (and 1 extended)
  of the GUI; EnergyPlus 25.1: a winter and a
  summer week (check 6, 0 mismatches; the totals of the functions of D1), the other outputs unchanged, three models
  with the EMS and API backends (identical), and a parametric study of two simulations with the new reducers; the golden
  master (unchanged); the whole suite; the documentation build.
- **Next step**: E4.

## 2026-11-09 — B4: JPN Aqilah 2025, comfort standard 23 (branch `v1.2.0`, on the server)

- **Objective**: B4, after B3, in the order of the author (with decisions D1 and D2).
- **Affected files**: `accim/sim/standards.py`, `accim/sim/ems/program_lines.py`, `accim/sim/ems/setpoint_lines.py`,
  `accim/sim/ems/setast.py`, `accim/sim/generation.py`, `accim/sim/accis.py`, `accim/utils/ems_code.py`,
  `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py`, `README.md`, `tests/core/test_jpn_aqilah2025.py`
  (new) and four updated tests, the golden master (7 files and its README), [[../docs/source/4_detailed use.md]],
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§17), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]],
  [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — JPN Aqilah 2025 is the built-in comfort standard 23, defined by its data, with the running mean of EnergyPlus (B4)|the decision]].
  Changing the literal `SET_VST` would have changed every output IDF in mixed mode, so the branches of 23 go at the end
  of the chains, as those of B3. The running mean and the way to configure the static setpoints wait for the author
  ([[questions.md]], [[../TODO.md]]).
- **Validation**: 13 new tests; EnergyPlus 25.1: a week of January (check 4, 0 mismatches; the static setpoint at the
  first timestep), and three models with the EMS and API backends (identical); the golden master (only additions in
  the 7 in-memory configurations); the whole suite; the documentation build.
- **Next step**: C2.

## 2026-11-09 — B3: comfort standards defined by their data (branch `v1.2.0`, on the server)

- **Objective**: B3, after B2, in the order of the author (with decisions D1 and D11).
- **Affected files**: `accim/sim/standards.py`, `accim/sim/ems/standard_lines.py` (new),
  `accim/sim/ems/program_lines.py`, `accim/sim/ems/programs.py`, `accim/sim/ems/outdoor_metric.py`,
  `accim/sim/ems/inputs.py`, `accim/sim/accis.py`, `accim/sim/generation.py`, `accim/sim/__init__.py`,
  `accim/sim/preview.py`, `accim/utils/ems_code.py`, `accim/utils/verification.py`,
  `accim/parametric_and_optimisation/` (`main.py`, `patches.py`, `funcs_for_besos/param_accis.py`), `accim/gui/`
  (`app.py`, `forms.py`, `tasks.py`), `setup.py`, `accim/sample_files/comfort_standards/` (new),
  `accim/sample_files/jupyter_notebooks/comfort_standards_registry/` (new), `docs/prepare_howto_notebooks.py`, the
  docs (4.2.5 and its references, the How-to page, `index.rst`, `api/accim.sim.ems.rst`), the tests,
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§16), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]],
  [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — Comfort standards defined by their data are registered for the session, and their EMS code is added at the end of the chains of the built-in ones (B3)|the decision]].
  The Erl interpreter of accim rejected `PMOT*(-0.2)` ("Minus sign used on the right side of multiplication sign", as
  EnergyPlus), so negative slopes are written with the intercept first. The workers of the parallel simulations are
  new processes without the registry, so they receive the definitions. The Qatar example waits for its data
  ([[questions.md]], [[../TODO.md]]).
- **Validation**: the new tests (core, parametric and GUI); EnergyPlus 25.1: a week of April (check 4, 0 mismatches,
  also `Tout_metric`), a year in the How-to notebook (0 mismatches in 8760 hours), and three models with the EMS and
  API backends (identical); the whole suite; the documentation build.
- **Next step**: B4.

## 2026-11-09 — B2: several regimes of the custom model (branch `v1.2.0`, on the server)

- **Objective**: B2, after D1, in the order of the author (with decision D6).
- **Affected files**: `accim/sim/arguments.py`, `accim/sim/ems/custom_regimes.py` (new),
  `accim/sim/ems/program_lines.py`, `accim/sim/ems/outdoor_metric.py`, `accim/sim/accis.py`, `accim/sim/__init__.py`,
  `accim/sim/preview.py`, `accim/utils/ems_code.py`, `accim/utils/verification.py`,
  `accim/data/postprocessing/main.py`, `accim/parametric_and_optimisation/` (`params_dicts.py`, `parameters.py`,
  `main.py`, `funcs_for_besos/param_accis.py`), `accim/gui/forms.py`, `accim/gui/app.py`,
  `tests/core/test_custom_regimes.py` (new), `tests/parametric_and_optimisation/test_custom_regime_parameters.py`
  (new), `tests/core/test_gui.py`, [[../docs/source/4_detailed use.md]] (4.2.4 and its references),
  `docs/source/parametric_and_optimisation.rst`, `docs/source/api/accim.sim.ems.rst`, [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]] (§15), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The custom model has several regimes, selected in each timestep by a program of each zone (B2)|the decision]].
  The program writes the inputs of the custom model, not ACSTall/ACSToffset (SetAppLimits and ApplyCAT would overwrite
  them); eppy drops the comment lines of the EMS programs when it reads an IDF, so the regimes are read back from the
  Erl lines. The outdoor metric of each regime waits for the author ([[questions.md]], [[../TODO.md]]).
- **Validation**: 20 + 4 new tests and 2 of the GUI; EnergyPlus 25.1: a week of April with three regimes (check 4 of
  `verify_accim_simulation`, 0 mismatches), a week of June with 'hvac_off' in mixed mode (the regime follows the coils
  of the previous timestep, and the setpoints those of the regime), and the EMS and API backends identical; the whole
  suite; the documentation build.
- **Next step**: B3.

## 2026-11-09 — D1: the indicators of the long-term thermal discomfort (branch `v1.2.0`, on the server)

- **Objective**: D1, after C1, in the order of the author (with decision D8).
- **Affected files**: `accim/data/postprocessing/long_term_discomfort.py` (new), `accim/data/postprocessing/main.py`,
  `accim/gui/forms.py`, `accim/gui/app.py`, `tests/core/test_long_term_discomfort.py` (new), `tests/core/test_gui.py`,
  [[../docs/source/4_detailed use.md]] (4.7.4, 4.10), `docs/source/api/accim.data.postprocessing.rst`,
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§14), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]],
  [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The indicators of the long-term discomfort are functions of a module of their own, and Table gives those of the temperature on request (D1)|the decision]].
  Annex D and Table E.1 of CEN/TR 16798-2 and formula (5) of ISO 7730:2025 checked in the documents. `Table` with
  timestep CSV files and `standard_outputs=True` drops all the outputs (in [[../TODO.md]]). Three details decided
  provisionally in [[questions.md]].
- **Validation**: 9 new tests and 2 of the GUI; the indicators of a timestep table equal to a direct calculation from
  the CSV file of a simulation of B5; the whole suite; the documentation build.
- **Next step**: B2.

## 2026-11-09 — C1: the parameters of the occupants, the new indices and the custom model (branch `v1.2.0`, on the server)

- **Objective**: C1, after B5, in the order of the author (with the adjustment of the brief: `clothing_insulation` and
  `activity_level` instead of `clo` and `met`).
- **Affected files**: `accim/constants.py`, `accim/parametric_and_optimisation/funcs_for_besos/param_apmv.py`,
  `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py`,
  `accim/parametric_and_optimisation/params_dicts.py`, `accim/parametric_and_optimisation/parameters.py`,
  `accim/parametric_and_optimisation/main.py`, `accim/gui/forms.py`,
  `tests/parametric_and_optimisation/test_pmv_and_metric_parameters.py` (new),
  `tests/parametric_and_optimisation/test_epmv_parameters.py`, `tests/parametric_and_optimisation/test_legacy_names.py`,
  `docs/source/parametric_and_optimisation.rst`, [[../docs/source/4_detailed use.md]] (4.2.2, 4.8),
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§13), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]],
  [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The parametric module varies the inputs of the PMV and the outdoor metric of the custom model (C1)|the decision]].
  The ranges of ISO 7730:2025 §4 and the body surface area of 1.8 m² checked in the standard and in the Engineering
  Reference of EnergyPlus 25.2 (§19.1). Applying `custom_alpha` before `custom_outdoor_metric` in a sample lost the
  alpha (the inputs were removed while the metric was 'pmot'): the modifiers keep them. The factory of the regimes of
  B2 waits for B2 (in [[../TODO.md]]). Four details decided provisionally in [[questions.md]].
- **Validation**: 8 new tests (a two-point design of `clothing_insulation` with besos, without simulating); the
  whole suite; the documentation build.
- **Next step**: D1.

## 2026-11-09 — B5: the floor and ceiling of the setpoints, and the hours below some temperatures (branch `v1.2.0`, on the server)

- **Objective**: B5, after B1, in the order of the author (with decision D5).
- **Affected files**: `accim/sim/ems/setpoint_limits.py` (new), `accim/constants.py`, `accim/sim/ems/inputs.py`,
  `accim/sim/ems/programs.py`, `accim/sim/generation.py`, `accim/sim/accis.py`, `accim/sim/preview.py`,
  `accim/utils/ems_code.py`, `accim/utils/verification.py`,
  `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py`, `accim/parametric_and_optimisation/parameters.py`,
  `accim/parametric_and_optimisation/params_dicts.py`, `accim/gui/forms.py`, `accim/gui/app.py`,
  `tests/core/test_setpoint_limits.py` (new), `tests/core/test_gui.py`,
  `tests/parametric_and_optimisation/test_setpoint_limit_parameters.py` (new),
  `tests/parametric_and_optimisation/test_legacy_names.py`, [[../docs/source/4_detailed use.md]] (4.2, 4.2.1, 4.2.3,
  4.3, 4.6.1, 4.10), `docs/source/api/accim.sim.ems.rst`, `docs/source/parametric_and_optimisation.rst`,
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§12), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]],
  [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The setpoints of the ACCIS can have a floor and a ceiling, and the zones count the occupied hours below some temperatures (B5)|the decision]].
  Table B.2 and clause B.2.2 checked in UNE-EN 16798-1:2020. A program of each zone after SetAST that bounds the
  setpoints and rounds them again gives the setpoints of the lines of v03 (checked with the interpreter). The
  counters read the occupants of the timestep and the operative temperature of the previous one (checked with
  EnergyPlus 25.1). With a run period from 8 January, the PMOT of `energyplus_running_means` (E1) is 0.142361 °C above
  that of EnergyPlus (in [[../TODO.md]]). Four details decided provisionally in [[questions.md]].
- **Validation**: 20 new tests (three with EnergyPlus 25.1), 2 of the parametric module and 2 of the GUI; two weeks of
  EnergyPlus 25.1 at timestep frequency without mismatches in checks 4 and 5; `run_ep` with both backends, identical;
  a screenshot of the frame; the whole suite; the documentation build.
- **Next step**: C1.

## 2026-11-09 — B1: the outdoor metric of the custom model (branch `v1.2.0`, on the server)

- **Objective**: B1, after A3, in the order of the author (with decisions D3 and D7).
- **Affected files**: `accim/sim/ems/outdoor_metric.py` (new), `accim/sim/ems/program_lines.py`,
  `accim/sim/ems/setast.py`, `accim/sim/ems/programs.py`, `accim/sim/ems/inputs.py`, `accim/sim/generation.py`,
  `accim/sim/accis.py`, `accim/sim/preview.py`, `accim/utils/ems_code.py`, `accim/utils/verification.py`,
  `accim/data/postprocessing/main.py`, `accim/gui/forms.py`, `accim/gui/app.py`,
  `tests/core/test_outdoor_metric.py` (new), `tests/core/test_gui.py`, [[../docs/source/4_detailed use.md]] (4.2.2,
  4.3.1, 4.6.1, 4.10), `docs/source/api/accim.sim.ems.rst`, [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]]
  (§11), [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The custom model calculates its outdoor metric in Erl, only where a zone needs it (B1)|the decision]].
  The first simulations found that the built-in variable `TimeStepsPerHour` reads 0 at BeginTimestepBeforePredictor
  in EnergyPlus 25.1 (the hourly values were never added; the interpreter of `compute_setpoints` had hidden it, since
  it set the value), and that the running means are not initialised without the EPW (EnergyPlus stopped: a variable
  used before it was set); the end of the hour is `Minute > 59.5`, and `InitOutdoorMetric` sets them to 0.
  `read_eso_using_readvarseso` keeps the last 8760 rows of long outputs (in [[../TODO.md]]). Five details decided
  provisionally in [[questions.md]].
- **Validation**: 34 new tests (two with EnergyPlus 25.1) and 2 of the GUI; five simulations of EnergyPlus 25.1 at
  timestep frequency (every metric, with and without the EPW, mixed mode) without mismatches in check 4; `run_ep` with
  both backends, identical; a screenshot of the frame; the whole suite; the documentation build.
- **Next step**: B5.

## 2026-11-09 — A3: the catalogue of adaptive coefficients of the aPMV and pmv_sign (branch `v1.2.0`, on the server)

- **Objective**: A3, after E2, in the order of the author (with decision D4).
- **Affected files**: `accim/constants.py`, `accim/sim/pmv_index.py`, `accim/sim/apmv.py`, `accim/gui/forms.py`,
  `accim/gui/app.py`, `tests/core/test_apmv_coefficients.py` (new), `tests/core/test_gui.py`,
  [[../docs/source/4_detailed use.md]] (4.8), [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§10),
  [[../DEVLOG.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The aPMV takes the adaptive coefficients of a catalogue, and with pmv_sign the coefficient of the side of the PMV (A3)|the decision]].
  With 'pmv_sign', the λ of the sign of the current PMV would make the PMV setpoints of the thermostats jump when the
  PMV changes sign, so each setpoint is converted with the λ of its side; that, and the keys that fill one
  coefficient only, are decided provisionally in [[questions.md]].
- **Validation**: 6 new tests (one with both backends of EnergyPlus 25.1) and those of the GUI; `run_ep` with both
  backends, identical; a screenshot of the tab; the whole suite; the documentation build.
- **Next step**: B1.

## 2026-11-09 — E2: `verify_accim_simulation` checks what the EMS calculates (branch `v1.2.0`, on the server)

- **Objective**: E2, after E1, in the order of the author.
- **Affected files**: `accim/utils/verification.py`, `accim/sim/preview.py`, `tests/core/test_verification.py` (new),
  [[../docs/source/4_detailed use.md]] (4.6.1), [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§9),
  [[../TODO.md]], [[../DEVLOG.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — verify_accim_simulation checks the indices of the PMV with the outputs at timestep frequency, and every comfort standard against compute_setpoints (E2)|the decision]].
  The EMS reads the PMV of the previous timestep and the occupants of the current one; the outputs follow the
  formulas within 1e-16 at timestep frequency, not hourly. The 5.5–6.1 % of the brief is decided provisionally in
  [[questions.md]]. Check 1 skips the zones whose names have ':' (pre-existing, in [[../TODO.md]]).
- **Validation**: 12 new tests, two with simulations of EnergyPlus 25.1; the whole suite; the documentation build.
- **Next step**: A3.

## 2026-11-09 — E1: the setpoints of the ACCIS without EnergyPlus (branch `v1.2.0`, on the server)

- **Objective**: E1, the first proposal of the list of the author for this session (the brief
  `notes/COPILOT_BRIEF_v1.2.0_v01.md`, decisions D1-D12), after D2.
- **Affected files**: `accim/sim/preview.py` (new), `accim/utils/ems_code.py`, `accim/utils/__init__.py`,
  `accim/sim/__init__.py`, `tests/core/test_preview.py` (new), [[../docs/source/4_detailed use.md]] (4.3.1),
  `docs/source/api/accim.sim.rst`, [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§8), [[../TODO.md]],
  [[../DEVLOG.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — compute_setpoints runs the setpoint programs of the output IDFs with the running means of EnergyPlus, start-up transient included (E1)|the decision]].
  EnergyPlus starts the running mean of CEN 15251 without normalising equation 19.82 (v03 says there is no start-up
  transient), takes the daily means of the simulated days from the first timestep of each hour, and its EMS reads the
  running means of the previous day at the first timestep of each day; `compute_setpoints` reproduces it to machine
  precision. Two possible errors of comfort standards 9 and 10, left in [[../TODO.md]] for the author; the first days
  of `outdoor_metrics`, decided provisionally in [[questions.md]].
- **Validation**: 30 new tests, two of them with simulations of EnergyPlus 25.1; the whole suite; the documentation
  build.
- **Next step**: E2.

## 2026-11-09 — D2: `Table` with the simulations of the setpoints based on the PMV (branch `v1.2.0`, on the server)

- **Objective**: D2 of the proposals (v02 and v03), included in 1.2.0 by the author; then the session plan of the
  author (brief `notes/COPILOT_BRIEF_v1.2.0_v01.md`, decisions D1-D12), in which D2 comes after E1: D2 was finished
  first because it was in progress.
- **Affected files**: `accim/data/postprocessing/main.py`, `accim/data/postprocessing/pmv_index_columns.py` (new),
  `accim/sim/pmv_index.py`, `tests/core/test_table_pmv_index.py` (new), [[../docs/source/4_detailed use.md]] (4.7.3),
  [[../CHANGELOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (§7), [[../TODO.md]], [[../DEVLOG.md]], [[decisions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — Table reads the CSV files of the simulations of any IDF and names the outputs of the setpoints based on the PMV after their zones, with names that do not contain each other (D2)|the decision]].
  `Table` could not read the CSV files of these simulations, added up their indices and setpoints over time and gave
  infinite totals per m2; v03 of the proposals was written on the code of 1.1.0, so its names of the outputs of A1
  differ from those of the code, which are used.
- **Validation**: 29 new tests; two simulations of 3 days with EnergyPlus 25.1; 1490 passed and 1 skipped; the
  documentation build with the same warnings.
- **Next step**: E1, and the rest of the session plan.

## 2026-11-09 — The answers of the author: A5 committed, the conventions of TODO.md, and D2, E2 and E1 for 1.2.0

- **Objective**: The author answered the five questions: commit and push the work to `v1.2.0`, apply the two
  proposals of [[../TODO.md]] (priorities and format of the references), do E1 and then the last part of A5, and
  include D2 and E2 in 1.2.0; he installed EnergyPlus 26.2 (`C:\EnergyPlusV26-2-0`).
- **Affected files**: [[../TODO.md]], [[../DEVLOG.md]], [[../ROADMAP.md]], [[decisions.md]], `tests/README.md`.
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The priorities of TODO.md and the format of the references to issues and pull requests|the decision]].
  GitHub names the repository of EnergyPlus `NatLabRockies/EnergyPlus` (`NREL/EnergyPlus` redirects to it); the pull
  requests 11409 ("Catch EMS variables initialized after reference") and 11551 (its follow-up) were read there.
- **Validation**: with the installed EnergyPlus 26.2, the golden master and `tests/core/test_energyplus_versions.py`:
  86 passed and 1 skipped (EnergyPlus 26.1, not installed); A5 committed (`6a6267d`) and pushed.
- **Next step**: D2, E2, E1 and the clothing insulation as a function of the outdoor temperature (A5).

## 2026-11-09 — `set_clothing_method` (A5) with the option of the author; the sources of the dynamic clothing model

- **Objective**: The answer of the author to the open question ("Opción (b)"), and the articles that the proposals
  lacked, in `D:\DSG\Otros articulos pendientes` and `D:\DSG\Mendeley library` (on the server).
- **Affected files**: `accim/sim/people.py`, `tests/core/test_pmv_input_parameters.py`,
  `tests/core/test_people_instance.py`, [[../docs/source/4_detailed use.md]] (4.8), [[../CHANGELOG.md]],
  [[../CAMBIOS_CODIGO_v1.2.0.md]], [[../TODO.md]], [[../DEVLOG.md]], [[decisions.md]], [[questions.md]],
  [[PROPUESTAS_MEJORAS_post_1.1.0_v02.md]] (§9.2).
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The schedule of set_clothing_method is the clothing insulation schedule, and CalculationMethodSchedule has its own argument|the decision]].
  The equations of the dynamic model are those of Schiavon and Lee (2013, equation 10) and ASHRAE 55-2020
  (Figure 5-1), which accepts the model in mechanically conditioned buildings.
- **Validation**: 1451 passed and 11 skipped (EnergyPlus 26.x); the documentation build with the same 59 lines of
  warnings.
- **Next step**: the tasks of [[../TODO.md]] that need the author.

## 2026-11-09 — The open points of `CAMBIOS_CODIGO_v1.2.0.md` (branch `v1.2.0`, on the server)

- **Objective**: The request of the author: "continúa con lo que puedas hacer del documento
  CAMBIOS_CODIGO_v1.2.0.md": the tests with EnergyPlus 26.x, the calling point of the metabolic correction "sin
  probarlo" and the cause of the differences between the backends, not looked for.
- **Affected files**: `tests/core/test_energyplus_versions.py`, [[../CAMBIOS_CODIGO_v1.2.0.md]] (§1, §2, §3, §5),
  [[../TODO.md]], [[../DEVLOG.md]], [[questions.md]].
- **Finding or decision**: EnergyPlus 26.1 and 26.2 can be tested without installing them: the zip files of NREL,
  linked with directory junctions at the default folders (`ACCIM_ENERGYPLUS_DIR` is not enough for besos and four
  tests). The correction before the internal gains makes them follow it in the same timestep, but delays the season
  one timestep, with negligible differences in a year: it stays. The backends start to differ in the HVAC or zone air
  solution of the warm-up, not in the EMS, the PMV or the comfort thermostat. Details in [[../DEVLOG.md]]; the
  question of `set_clothing_method`, in [[questions.md]].
- **Validation**: `tests/core` and `tests/parametric_and_optimisation` with EnergyPlus 26.x linked: 1448 passed, no
  skips (the junctions and the copies removed afterwards).
- **Next step**: the answers of the author ([[questions.md]], [[../TODO.md]]).

## 2026-11-09 — The pending tasks of `TODO.md` and A5 (branch `v1.2.0`, on the server); the standards checked

- **Objective**: The requests of the author: "quiero que actualices accim a la rama v1.2.0" (the server, `D:\DSG\accim`,
  had a shallow clone of July at 0.7.8), "vamos a trabajar en las tareas pendientes; mira las del TODO.md; cuando
  termines, vamos a continuar con las tareas de los cambios de la v1.2.0 ... no quiero que te inventes nada", and the
  standards that the proposals lacked, in `D:\DSG\Normativas` (EN 16798-1, CEN/TR 16798-2 and ISO 7730:2025).
- **Affected files**: `accim/sim/apmv.py`, `tests/core/test_pmv_input_parameters.py` (new),
  `tests/core/test_people_instance.py`, the ePMV notebook and its page (new), `docs/source/index.rst`,
  `2_installation.md`, `3_quick tutorial.md`, [[../docs/source/4_detailed use.md]] (4.8, 4.8.1), [[../docs/README.md]]
  (§2, §7), [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]], [[../TODO.md]], [[decisions.md]],
  [[PROPUESTAS_MEJORAS_post_1.1.0_v02.md]] (§9.2).
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The activity level and the clothing insulation take values by season in set_pmv_input_parameters, with the cooling season of the setpoints, and 'dynamic_ashrae55' sets the dynamic clothing model of EnergyPlus|the decision]].
  Read the Docs already had `v1.1.0` active. ISO 7730:2025 names I to IV the categories (A to C in 2005), and the
  approximation of the metabolic correction holds with the PMV program of its Annex D (details in [[../DEVLOG.md]]).
  On the server, `py` is Python 3.14 (accim in editable mode) and `python` is Python 3.10 (accim 0.7.8); EnergyPlus 9.4,
  9.6, 25.1 and 25.2 are installed (not 26.x), and pandoc is not (the documentation build used a portable copy).
- **Validation**: `tests/core` and `tests/parametric_and_optimisation`: 1437 passed, 10 skipped (EnergyPlus 26.x);
  the notebook run twice (the same results); the documentation build, with the same 59 lines of warnings as `HEAD`.
- **Next step**: the tests with EnergyPlus 26.x and the two parts of A5 not done ([[../TODO.md]]).

## 2026-11-09 — A1: the ePMV setpoints (branch `v1.2.0`)

- **Objective**: The request of the author: go on with the work of the previous session, "termines el A1 y el A5 lo
  dejes pendiente"; the How-to notebook of the ePMV "no lo ejecutes; déjalo como tarea pendiente".
- **Affected files**: `accim/sim/pmv_index.py`, `accim/sim/apmv.py`, `accim/constants.py`, the parametric module
  (`param_apmv.py`, `params_dicts.py`, `parameters.py`, `main.py`), the GUI (`forms.py`, `tasks.py`, `app.py`), the new
  folder `accim/sample_files/jupyter_notebooks/example_epmv_setpoints`, `docs/prepare_howto_notebooks.py`,
  `tests/core/test_epmv.py` (new), `tests/core/test_gui.py`, [[../docs/source/4_detailed use.md]] (4.8.1),
  `docs/source/parametric_and_optimisation.rst`, `docs/source/2_installation.md`, [[../README.md]],
  [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]], [[../TODO.md]], [[decisions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-09 — The ePMV applies the expectancy factor in the cooling season to the warm side only, and its metabolic correction uses the PMV of the previous timestep|the decision]].
  The heat gains of the occupants follow the corrected activity level one timestep later, and the correction converges
  to a slightly smaller reduction than that of Fanger and Toftum; both documented. The author's file of proposals has a
  v02 with the coefficients checked.
- **Validation**: 17 new tests of the ePMV (one with both backends), 6 of the GUI and 2 of the parametric module;
  simulations of the residential model; `tests/core` and `tests/parametric_and_optimisation`: 1421 passed and one test
  of the legacy names fixed (`expectancy_factor` has no name of accim 0.x); the documentation build (the same 59
  lines of warnings).
- **Next step**: run and export the notebook ([[../TODO.md]]); A5, pending.

## 2026-11-08 — A2: one engine for the setpoints based on indices derived from the PMV (branch `v1.2.0`)

- **Objective**: The request of the author: "vamos a añadir una serie de nuevas funcionalidades a accim; quiero que lo
  hagas en una nueva rama v1.2.0" (he first wrote v1.3.0, then "me refería a la v1.2.0"), those of his file
  `notes/PROPUESTAS_MEJORAS_post_1.1.0_v01.md` (not in git), "empezamos con el bloque A". He chose the P1 proposals
  (A2, A1 and A5, in this order), one commit for each pushed to GitHub, the ePMV of the proposal (the expectancy
  factor only in the cooling season and on the cooling setpoint) and its optional metabolic correction.
- **Affected files**: `accim/sim/pmv_index.py` (new), `accim/sim/apmv.py`, `accim/sim/__init__.py`,
  `accim/parametric_and_optimisation/funcs_for_besos/param_apmv.py`, `tests/core/test_pmv_index.py` (new),
  [[../docs/source/4_detailed use.md]] (4.8, 4.9), `docs/source/api/accim.sim.rst`, [[../CHANGELOG.md]],
  [[../DEVLOG.md]], [[../CAMBIOS_CODIGO_v1.2.0.md]] (new), [[decisions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-08 — The setpoints based on indices derived from the PMV share one engine, with the Erl of each index in a registry|the decision]].
  The index of each zone is calculated from the PMV of the previous timestep. With the thermal comfort thermostats,
  the two backends give the same setpoints but results of EnergyPlus that differ by rounding (about 1e-10 °C), already
  with 1.1.0.
- **Validation**: the golden master (the aPMV unchanged); 8 new tests; `tests/core` and
  `tests/parametric_and_optimisation`: 1395 passed (one fixed: 'λ' in a printed text); the documentation build.
- **Next step**: A1, the ePMV setpoints.

## 2026-11-08 — Release 1.1.0 (PyPI, GitHub, Read the Docs)

- **Objective**: The request of the author: "quiero publicar en github, pypi, y actualizar readthedocs con la v1.1.0".
- **Affected files**: [[../CHANGELOG.md]] (the release commit `33f2cae8`), [[../TODO.md]], [[../DEVLOG.md]]; the branch
  `v1.1.0` deleted (local and GitHub), the tag `v1.1.0`, the GitHub release, PyPI and TestPyPI.
- **Finding or decision**: As §4 of [[../packaging/README.md]]. Deleting the branch `v1.1.0` before pushing the tag
  let Read the Docs give the tag the slug `v1.1.0`. The new version of Read the Docs is inactive, and only the author
  can activate it (his session): the one step left, in [[../TODO.md]]. The local `PYTHONPATH` has an empty entry (the
  current folder), so the tests of the installed wheels ran with `PYTHONPATH` empty.
- **Validation**: 1386 tests; the local wheels, TestPyPI and PyPI in new venvs (`pip check`, 133 sample files, and with
  the local wheels and PyPI a smoke test of the functions of 1.1.0 and one day of simulation with both backends:
  identical CSV files); the builds of `latest` and `master` passed, with the same 30 warnings, and `/en/latest/`
  shows 1.1.0 and the new tutorials. Details in [[../DEVLOG.md]].
- **Next step**: the author activates `v1.1.0` in Read the Docs ([[../TODO.md]]).

## 2026-11-08 — The tutorials show the functions of 1.1.0; the How-to pages generated again

- **Objective**: The request of the author: "quiero que los tutoriales (al menos, uno de ellos) muestren las nuevas
  funcionalidades que hemos implementado", before publishing 1.1.0 (the release has its own entry).
- **Affected files**: the source notebooks `using_addAccis`, `using_runEp` and `full_example_IBPSA` (in
  `accim/sample_files/jupyter_notebooks/`), their pages and that of `research_paper_case_study`,
  [[../docs/source/3_quick tutorial.md]] (3.1.3), [[../docs/source/4_detailed use.md]] (two labels),
  [[../README.md]], `docs/prepare_howto_notebooks.py`, `tests/core/test_docs_notebook_pages.py`, [[../docs/README.md]],
  [[../CHANGELOG.md]], [[../DEVLOG.md]].
- **Finding or decision**: *Using AddAccis()* shows `results_size`, the EMS code of the comfort standard of an output
  IDF only, `print_setpoint_ems_code()`/`get_setpoint_ems_code()` (new 2.3) and `modify_accis()` (new 2.4); *Using
  run_ep()* shows `estimate_results_size()` without and with simulation (23.3 and 21.9 MB; the files, 21.9 MB). The
  export of the How-to pages shortened a joined output of exactly 100 line breaks (an off-by-one between
  `_merge_streams` and `_clean_stream`), which hid the size and the confirmation of `AddAccis()`: fixed, with a test.
  The research paper case study changes slightly with 1.1.0 (Shimla, `Ind_Adap_MM`: 89.67 to 89.59 kWh/m2).
- **Validation**: the four notebooks ran without problems; the pages compared cell by cell with the previous ones;
  `test_docs_notebook_pages.py` (25 passed; the new test fails before the fix); the documentation build (the same 59
  lines of warnings); `tests/core` and `tests/parametric_and_optimisation`: 1386 passed.
- **Next step**: the release of 1.1.0 ([[../packaging/README.md]]).

## 2026-11-08 — The GUI reviewed against 1.1.0: the arguments of each zone, the EMS code, the size of the results

- **Objective**: The request of the author: review whether the GUI is up to date with the code ("no he visto ninguna
  opción para especificar la configuración de accis (comfort standard, etc) por zona"), working autonomously.
- **Affected files**: `accim/gui/forms.py`, `tasks.py` and `app.py`, `tests/core/test_gui.py`,
  [[../docs/source/4_detailed use.md]] (4.10), [[../README.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]],
  [[decisions.md]].
- **Finding or decision**: See
  [[decisions.md#2026-11-08 — The GUI gives fields for the arguments of each zone and asks for the confirmation of AddAccis after the estimated size|the decision]].
  The table of the zones existed, but at the end of the tab 1, out of view; the functions of 1.1.0 and some
  arguments were missing (the list is in [[../DEVLOG.md]]). Scripts that drive the window and run `run_ep` on Windows
  need `if __name__ == '__main__':`, since its processes re-run the main module (`accim-gui` and `python -m accim.gui`
  have it). ImageGrab only captures the desktop from the process of the agent: `PrintWindow` of the Win32 API renders
  the window.
- **Validation**: 109 tests of the GUI (24 new); screenshots of the tabs; a run through the window with EnergyPlus
  25.1 (zones, `AddAccis` with the confirmation after the estimate, the EMS code, the size of the results, `run_ep`,
  the hours, a parametric study with the eppy building), with no error; the documentation build.
- **Next step**: the review of the author (committed and pushed to `master` at his request).

## 2026-11-08 — `__version__` is 1.1.0 on `master` (in development); the stale editable installs of accim

- **Objective**: The requests of the author: open the GUI (the command `accim-gui` needed `pip install -e .`), then
  "hay que actualizar la versión a 1.1.0", only the number: `## [Unreleased]` of [[../CHANGELOG.md]] stays until the
  release, since the work on the GUI goes on.
- **Affected files**: `accim/__init__.py`, `tests/core/test_deprecation.py` (`test_version`),
  [[../docs/source/4_detailed use.md]] (the two headers of the transcriptions, §5 of [[../docs/README.md]]),
  [[../packaging/README.md]] (§4.2 names `test_version`), [[../DEVLOG.md]]; outside the repository, the editable
  install of accim in the local Python 3.14.
- **Finding or decision**: The other mentions of 1.0.0 are historical and stay. The local Python had three editable
  installs (0.7.6, 0.7.8 and, after `pip install -e .`, 1.0.0; pip reported `Successfully installed accim-0.7.6`)
  because the local `PYTHONPATH` ends with `;`: Python takes the empty entry as the current folder, which pip keeps in
  `sys.path` (it only removes `sys.path[0]`), so `pip install -e .` from the root of the repository took the
  `accim.egg-info` of the repository for the installed accim, and left the previous install in site-packages. The old
  ones were uninstalled, with the consent of the author, and accim was reinstalled from another folder
  (`pip install -e D:\Python\accim`), which replaced 1.0.0 with 1.1.0.
- **Validation**: `test_deprecation.py`, `test_addaccis_banner.py` and `test_session.py`: 36 passed;
  `importlib.metadata.version('accim')` and `accim.__version__`: 1.1.0; `accim-gui.exe` in the Scripts folder.
- **Next step**: the work on the GUI; at the release, only the CHANGELOG and the commit `Release v1.1.0` remain of
  §4.2 of [[../packaging/README.md]].

## 2026-11-08 — `v1.1.0` merged into `master` and pushed; the work goes on in `master`

- **Objective**: The requests of the author: move the changes of `v1.1.0` to `master` and push them; then commit this
  entry, push it and go on working in `master`.
- **Affected files**: none in the tree: `master`, local and on GitHub, moved from `73f958b5` (the log of the 1.0.0
  release) to `bb98ede5`, the commit of `v1.1.0`.
- **Finding or decision**: `master` was an ancestor of `v1.1.0` (12 commits behind), so it was fast-forwarded
  (`git fetch . v1.1.0:master`), with no merge commit, as `v1.0.0` on 2026-11-01. Unlike §4.8 of
  [[../packaging/README.md]], `master` was pushed before the release, because the author asked for it: `latest` (the
  default version of Read the Docs) and `master` now show the changes of 1.1.0, which is not on PyPI yet, under the
  title of 1.0.0 (`__version__`). Before the push, the Python files of `accim` were checked statically against Python
  3.9, that of Read the Docs (the local Python is 3.14, so the local build of the documentation cannot see it): syntax,
  `X | Y` evaluated at run time, f-strings of 3.12 and imports of 3.10+; nothing found.
- **Validation**: `git ls-remote origin`: `master` and `v1.1.0` at `bb98ede5`; the builds 35730336 (`latest`) and
  35730337 (`master`) of Read the Docs passed, with the same number of Sphinx warnings (30) as the previous builds and
  no failed import; the API reference of `latest` shows `estimate_results_size` and `print_setpoint_ems_code`.
- **Next step**: the work goes on in `master`, at the request of the author (`v1.1.0` stays, equal to `master` with
  this entry); at the release, delete the branch `v1.1.0` (local and on GitHub) before pushing the tag `v1.1.0` (§4.5
  of [[../packaging/README.md]]).

## 2026-11-08 — The size of the results of the simulations, before running them (branch `v1.1.0`)

- **Objective**: The request of the author: estimate the weight of the results of the simulations of `run_ep`, like
  the estimate of the parametric module, without simulation or, more exactly, with simulation, as the user chooses;
  and know it when the output IDFs are generated, to choose their outputs.
- **Affected files**: `accim/sim/results_size.py` (new), `accim/run/results_size.py` (new), `accim/run/__init__.py`,
  `accim/run/run.py`, `accim/sim/accis.py`; `tests/core/test_results_size.py` (new); [[../CHANGELOG.md]],
  [[../DEVLOG.md]], [[../docs/source/4_detailed use.md]] (4.1, 4.4, 4.6), [[../docs/source/9_migration_guide.md]],
  `docs/source/api/accim.run.rst` and `accim.sim.rst`, [[../CAMBIOS_CODIGO_v1.1.0.md]] (section 9), [[decisions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-08 — The size of the results is estimated from the outputs of the models, and AddAccis prints it before writing the output IDFs|the decision]].
  The ESO and CSV files are 90 to 95 % of the results, and their size is that of their values: about 30 MB for each
  simulation of a standard hourly output IDF of the sample model (25 GB for 140 output IDFs and 6 EPWs). The estimate
  without simulation counts the values that the outputs report, with the bytes measured in the files of EnergyPlus 25.1;
  `estimate_results_size(simulate=True)` simulates one IDF of each group with the same outputs, as `run_ep`.
- **Validation**: 16 simulations (9 of calibration, 7 of example files of EnergyPlus): within 10 % for the results of
  more than 5 MB; 10 new tests, one of them against a simulation; `tests/core` and `tests/parametric_and_optimisation`:
  1362 passed; the documentation build (the same warnings).
- **Next step**: committed and pushed to `v1.1.0` at the request of the author; his review.

## 2026-11-07 — The EMS code of the setpoints before adding the ACCIS, the How-to pages, and the indentation (branch `v1.1.0`)

- **Objective**: The requests of the author: a helper to read the EMS code of the setpoints before using accim
  (which setpoints apply, and what happens out of the applicability limits); the pending task of [[../TODO.md]] (the
  How-to pages that show EMS programs); and an example of the indentation of the EMS code of a generated IDF.
- **Affected files**: `accim/utils/ems_code.py` (new), `accim/utils/__init__.py`, `accim/sim/ems/setast.py`;
  `tests/core/test_ems_code.py` (new); the pages `full_example_IBPSA` and `using_apmv_setpoints` of
  `docs/source/jupyter_notebooks/`; [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../docs/source/4_detailed use.md]] (4.3),
  `docs/source/api/accim.utils.rst`, [[../CAMBIOS_CODIGO_v1.1.0.md]], [[../TODO.md]].
- **Finding or decision**: `accim.utils.print_setpoint_ems_code(comfort_standard, category, comfort_mode, ...)`
  prints the code of the output IDFs, built with the functions that write them, in the order in which it runs. The
  results of the full example of the How-to pages change slightly, only because of the design days of `vrf_mm`: run
  with the code of `a235b1c9`, they are those of the pages of 1.0.0. In an output IDF of `AddAccis`, the 34 programs
  are indented, and the same IDF without indentation only differs in spaces.
- **Validation**: 33 new tests; the pages compared with those of 1.0.0 (section 7.4 of [[../docs/README.md]]) and
  with a run of `a235b1c9`; the documentation build (the same warnings); `tests/core` and
  `tests/parametric_and_optimisation`: 1352 passed.
- **Next step**: committed and pushed to `v1.1.0` at the request of the author; his review.

## 2026-11-07 — The answers of the author: `vrf_mm` on the design days, and the EMS code of the comfort standards (branch `v1.1.0`)

- **Objective**: The answers of the author to the two open questions of [[questions.md]]: option (a) for the design
  days of `vrf_mm` (the rule of `ex_mm`) and option 1 for the EMS code of the comfort standards of each output IDF
  (implemented on 2026-11-06).
- **Affected files**: `accim/sim/ems/program_lines.py`, `accim/sim/ems/objects.py`, `accim/sim/build.py`,
  `accim/sim/hvac/existing.py`, `accim/sim/hvac/schedules.py`; `tests/core/test_existing_hvac_mixed_mode.py`,
  `tests/core/test_hour_counters.py`, the 12 golden files of `vrf_mm`; [[../CHANGELOG.md]], [[../DEVLOG.md]],
  [[../docs/source/4_detailed use.md]], [[../docs/source/9_migration_guide.md]], [[../CAMBIOS_CODIGO_v1.1.0.md]],
  [[decisions.md]], [[questions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-07 — Mixed mode air-conditions the zones on the design days with `vrf_mm` too|the decision]];
  that of 2026-11-06 on the EMS code is accepted, with no change. With the sample model (no occupants on its winter
  design day), `vrf_mm` sized the VRF systems for heating design loads of 0 (EnergyPlus warned); now 1.9 and 2.2 kW,
  and the cooling design loads, and so the VRF systems, are about 6 % lower (no pull-down after the hours without
  occupants).
- **Validation**: the Erl test of the design days and a new test of the sensor and the lines, with `ex_mm` and
  `vrf_mm` (both fail with `vrf_mm` without the change); golden master: only the 12 configurations of `vrf_mm` change,
  only with added lines; the sizing periods of the sample model with EnergyPlus 25.1, before and after;
  `tests/core` and `tests/parametric_and_optimisation`: 1317 passed.
- **Next step**: committed and pushed to `v1.1.0` at the request of the author; before the release, the How-to pages
  of [[../TODO.md]].

## 2026-11-07 — `ex_ac` and `ex_mm` with the example files of EnergyPlus (branch `v1.1.0`)

- **Objective**: The request of the author: test `ex_mm` and `ex_ac` with many IDFs with different HVAC systems, so
  that they work with any model whose original simulates, with scheduled or AirflowNetwork natural ventilation in
  `ex_mm`, and windows that open and close when needed in mixed mode; later, to reduce the number or the length of the
  simulations (the first campaign took hours).
- **Affected files**: `accim/sim/windows.py` (new), `accim/sim/model.py`, `accim/sim/hvac/existing.py`,
  `accim/sim/hvac/schedules.py`, `accim/sim/ems/objects.py`, `accim/sim/ems/program_lines.py`, `accim/sim/build.py`,
  `accim/sim/accis.py`, `accim/energyplus.py`; `tests/core/test_mixed_mode_windows.py` (new), `test_existing_hvac.py`,
  `test_existing_hvac_mixed_mode.py`, golden files (`ex_mm`, `b13`, `b15`, `b22`); [[../CHANGELOG.md]],
  [[../DEVLOG.md]], [[../docs/source/4_detailed use.md]], [[../docs/source/9_migration_guide.md]],
  `docs/source/api/accim.sim.rst`, [[../CAMBIOS_CODIGO_v1.1.0.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-07 — In mixed mode accim takes the whole control of the windows it opens, and `ex_mm` air-conditions the zones on the design days|the decision]].
  Besides the windows and the design days: accim replaced the EMS global and internal variables of the models (33
  example files stopped), the backup broke NodeLists and AirflowNetwork distribution models, `ZoneVentilation:DesignFlowRate`
  gave a `BadEPFieldError`, the VRF systems failed with the availability schedule, and `HVACTemplate` models kept their
  setpoints (now expanded by `AddAccis`). EnergyPlus 25.1 crashes with the Kiva examples with operative temperature
  control (not accim).
- **Validation**: baseline with the code before (618 example files, 4 variants); after the fixes, 170 selected models
  with 5-day periods (see [[../DEVLOG.md]]); new tests; the golden master changes only where expected (checked line by
  line); `python -m pytest tests/core tests/parametric_and_optimisation -q -p no:cacheprovider`: 1314 passed.
- **Next step**: the review of the author; the open question on `vrf_mm` and the design days.

## 2026-11-06 — EMS programs: only the code of the comfort standards of each output IDF, and indented lines (branch `v1.1.0`)

- **Objective**: The questions of the author: could the EMS code of the generated IDFs be indented, to see where each block `if`-`elseif`-`else`-`endif` begins and ends, and what about adding only the EMS code of the comfort standards chosen instead of that of all of them. He was not available to choose, so the recommended option was implemented for his review ([[questions.md#2026-11-06 — Keep only the EMS code of the comfort standards of each output IDF of `AddAccis`?|the open question]]).
- **Affected files**: `accim/sim/ems/` (`programs.py`, `program_lines.py`, `setast.py`, `inputs.py`), `accim/sim/accis.py`, `accim/parametric_and_optimisation/funcs_for_besos/param_accis.py`, `tests/core/test_comfort_standard_code.py` (new) and three other tests, the 22 golden files of `AddAccis`, [[../CHANGELOG.md]], [[../docs/source/9_migration_guide.md]], [[../docs/source/4_detailed use.md]], [[../CAMBIOS_CODIGO_v1.1.0.md]], [[../DEVLOG.md]], [[../TODO.md]], the source notebook `full_example_IBPSA`.
- **Finding or decision**: See [[decisions.md#2026-11-06 — Each output IDF of `AddAccis` only has the EMS code of the comfort standards of its zones, and the EMS programs are indented|the decision]]. eppy removes the spaces at the beginning of the fields when it reads an IDF, so `AddAccis` and `modify_accis` indent the programs again; EnergyPlus ignores them. An output IDF of the sample model goes from 78 programs with 6851 lines (645 KB) to 34 with 1393 lines (357 KB); the comfort standard of an output IDF is then changed with `modify_accis` (or `modify_ComfStand`), which add its code.
- **Validation**: the Erl compiler gives the same variables with the code of each comfort standard as with that of all of them (every category and comfort mode); 424 output IDFs of the golden master checked object by object; identical EnergyPlus results for 19 pairs of output IDFs (9.4, 9.6, 25.1, 26.2); the test suites and the documentation build (see [[../DEVLOG.md]]).
- **Next step**: the review of the author; regenerate the How-to pages `full_example_IBPSA` and `using_apmv_setpoints` before the release ([[../TODO.md]]).

## 2026-11-06 — `accim.sim` restructured around eppy (branch `v1.1.0`)

- **Objective**: The request of the author: another restructuring of accim using eppy whenever possible, mainly in `accim.sim`, in a new branch `v1.1.0`, as easy and simple to understand as possible; then, understandable even if a bit slower, and eppy rather than besos whenever possible.
- **Affected files**: `accim/sim/` (`accis.py`, `generation.py`, `model.py`, `people.py`, `outputs.py`, `apmv.py`, `chile_funcs.py`, `ems/`, `hvac/`, `energyplus_api/idf.py` and `runner.py`; `idf_tools.py` removed), `accim/utils/` (`people.py`, `editing.py`, `verification.py`, `accim_args.py`), `accim/data/postprocessing/main.py`, `tools/compare_backends.py`, 20 test files (new `test_chile_funcs.py`) and 19 golden files; [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../CAMBIOS_CODIGO_v1.1.0.md]] (new), [[../docs/source/9_migration_guide.md]] (9.4), [[../docs/source/4_detailed use.md]], [[../docs/source/5_troubleshooting.md]], [[decisions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-06 — `accim.sim` reads, changes and writes the models with eppy, even where code of its own was faster|the decision]]. eppy reads the numeric fields as numbers (besos kept text): the output IDFs write some numbers in another way (same values, identical EnergyPlus results), and `str(value or '')` took a limit of 0 °C as an empty field (fixed). Saving each output IDF with eppy is about 18 times slower than the writer of 1.0.0 (`EpBunch.__repr__`): `AddAccis` with 140 output IDFs, about 6 s → 17 s.
- **Validation**: 1277 tests of `tests/core` and `tests/parametric_and_optimisation` and the 87 numbered tests of the parametric module passed; golden master: only number formatting changed in 19 configurations (2926 fields), checked field by field and with simulations; both backends of the API give identical CSV files; details in [[../DEVLOG.md]].
- **Next step**: the review of the author (committed and pushed to `v1.1.0` at his request); the release.

## 2026-11-03 — Release 1.0.0 (PyPI, GitHub, Read the Docs)

- **Objective**: The request of the author: publish 1.0.0 on PyPI, make the GitHub release, move the changes to `master` and push them, and make sure that the notebook pages of Read the Docs show the results of every cell.
- **Affected files**: `docs/prepare_parametric_notebooks.py`, the page of the parametric tutorial 10, `tests/core/test_docs_notebook_pages.py` (new), `docs/source/conf.py`, [[../CHANGELOG.md]], [[../docs/README.md]], [[../packaging/README.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]].
- **Finding or decision**: The published page of tutorial 10 had two empty outputs (tqdm widgets, whose state the export drops): the export now leaves them out. The PDF of Read the Docs stopped at the value of `SETPOINT_LINES` (more than 200,000 characters in one line), and then Read the Docs published nothing: `conf.py` cuts long values, and, with the approval of the author, the tag `v1.0.0` was moved to that fix of the documentation (the package is unchanged). The branch `v1.0.0` was deleted before pushing the tag (same name: git and the slug of Read the Docs).
- **Validation**: 1273 tests; three clean installs (local wheels, TestPyPI, PyPI), two of them with simulations of the installed accim; the 23 notebook pages of `latest`, `master` and `v1.0.0` compared cell by cell with their notebooks; details in [[../DEVLOG.md]].
- **Next step**: none for the release.

## 2026-11-03 — Sessions saved in a pickle file and a readable JSON file

- **Objective**: The request of the author: save a pickle file that resumes the session of the classic workflow (as in the notebook of the research paper case study), as the parametric module does, also in the GUI, and a JSON file that people can read; he chose `Table.save`/`Table.load` and `save_session`/`load_session`, and in the GUI the whole session plus opening tables saved in Python.
- **Affected files**: `accim/utils/session.py` (new), `accim/utils/__init__.py`, `accim/data/postprocessing/main.py` (`Table`), `accim/gui/` (`app.py`, `tasks.py`, `__init__.py`), `tests/core/test_session.py` (new), `tests/core/test_gui.py`, the notebook of the research paper case study and its page; [[../docs/source/4_detailed use.md]] (4.7.2, 4.10), [[../README.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[decisions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-03 — Tables and sessions are saved in a pickle file, to resume them, and a JSON file, to read them|the decision]]: the pickle file resumes the session and is written first; the JSON file is only for reading, and shows at most 1000 rows of each table (`json_max_rows`), since the review found that the JSON of whole hourly tables cost seconds to minutes and hundreds of MB. The review also found that `format_table` recorded its arguments before its checks, and that the GUI resolved relative paths twice: both fixed.
- **Validation**: 14 new tests of the sessions and 9 of the GUI; a GUI session reopened in a new window; the notebook ran end to end (2007 s) and its page was regenerated, with only the expected differences; 1249 tests of `tests/core` and `tests/parametric_and_optimisation` passed, and the documentation builds without new warnings; details in [[../DEVLOG.md]].
- **Next step**: the review of the author; the release ([[../TODO.md]]).

## 2026-11-03 — The answers to the P2 items, EnergyPlus 26.1, and the EMS of 0.8.2 against 1.0.0

- **Objective**: Apply the answers of the author to the five P2 items of [[../TODO.md]] (radiant systems with a True/False argument, the `existing_hvac_*` arguments in the GUI, ESP CTE in the full sets, his correction of CHN Yang, EnergyPlus 26.1), and show him an output IDF to see whether the EMS code changed since 0.x.
- **Affected files**: `accim/sim/hvac/existing.py`, `model.py`, `build.py`, `accis.py`, `ems/setpoint_lines.py` (the author), `accim/parametric_and_optimisation/main.py`, `funcs_for_besos/param_accis.py`, `accim/gui/` (`forms.py`, `app.py`, `tasks.py`); tests (`test_existing_hvac.py`, `test_setast_chn_yang.py` (new), `test_gui.py`, `test_energyplus_versions.py`, `_golden.py`, `test_golden_master.py`, all the golden files, `test_param_accis_filter.py`); [[../docs/source/4_detailed use.md]], [[../docs/source/9_migration_guide.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[decisions.md]].
- **Finding or decision**: Four decisions of 2026-11-03 in [[decisions.md]] (radiant setpoints, the GUI, ESP CTE rows, CHN Yang). The cooling panels follow the thermostat (`ZoneTotalLoad`), since their operative temperature control gave plant flow errors. The stop of the custom model without `InitASTvariables` comes with EnergyPlus 26.2, not 26.1 (contrary to the notes of 0.8.2). The EMS of 1.0.0 is restructured (per-zone `RunACCIS_<zone>` and `SetInputData_<zone>`, 5 calling managers instead of 29) with the same results as 0.8.2 except the corrected hour counters.
- **Validation**: year simulations of six radiant example files; the 26.1 campaign (14 simulations per version: identical sums to 25.2, both backends identical, a parametric study); the 0.8.2 comparison (86/96 and 90/100 identical columns); the test suites; details in [[../DEVLOG.md]].
- **Next step**: the review of the author (committed and pushed to `v1.0.0` at his request); the release ([[../TODO.md]]).

## 2026-11-02 — The existing HVAC systems keep the operative temperature between the setpoints

- **Objective**: The question of the author: with existing HVAC systems the operative temperature exceeded the setpoints in some models (he used the VRF systems instead); can the existing equipment keep it between them (`ex_mm`)? Then: investigate the HVAC systems themselves (capacity, outdoor temperature limits), for any IDF, with arguments that simulate the model as it is when they are off.
- **Affected files**: `accim/sim/hvac/existing.py`, `accim/sim/hvac/schedules.py` (new), `vrf.py`, `build.py`, `accis.py`, `outputs.py`, `model.py`, `accim/parametric_and_optimisation/main.py`; `tests/core/test_existing_hvac.py` (new), the golden master (`b10`, `b11`, `s04`, new `b21`, `b22`); [[../docs/source/4_detailed use.md]] (4.1.1), [[../docs/source/9_migration_guide.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[decisions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-02 — The existing HVAC systems keep the operative temperature between the setpoints with arguments `existing_hvac_*`|the decision]]: the main cause was air temperature control (the VRF systems control the operative temperature); also the thermostats with several controls (EnergyPlus examples: setpoints not applied, EnergyPlus stopped), the availability, the outdoor temperature limits and the HVAC system itself (capacity, controls, no cooling equipment), which only a backup ideal loads system covers for any system.
- **Validation**: year simulations in Seville of the four sample models and `5ZoneAirCooled` (OSM office: 53–77 % → 86–93 % → 100 %); 21 new tests; all the tests of `tests/core` and `tests/parametric_and_optimisation` passed; golden master: only the OSM office changes, `b21` (`False`) equals the former `b11`; details in [[../DEVLOG.md]].
- **Next step**: the review of the author; the radiant systems and the GUI ([[../TODO.md]]).

## 2026-11-02 — The findings of the branch reviews, fixed

- **Objective**: Continue, without answers of the author, with the P2 items of [[../TODO.md]] that need no decision: the findings of the branch reviews ([[branch-reviews.md]], 1.4), the block means of `Table` and `keep_input` in the parametric notebooks.
- **Affected files**: `accim/data/` (`postprocessing/main.py`, `postprocessing/utils.py`, `preprocessing.py`, `morphing.py`), `accim/run/run.py`, `accim/utils/` (`editing.py`, `workspace.py`, `accim_args.py`, `verification.py`), `accim/sim/` (`prompts.py`, `accis.py`, `apmv.py`), `accim/parametric_and_optimisation/main.py`, ten notebooks and their pages, 17 test files (four new); [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[branch-reviews.md]].
- **Finding or decision**: Two of them lost data (`rename_epw_files` deleted the EPWs excluded from the renaming; `WorkspaceArtifactCleaner` removed the empty folders of the user), one ran code of the IDF (`eval` in `get_accim_args`) and one read models with the IDD of another version (`load_idf('auto')`). The relative comparisons of `wrangled_table` stay fractions (their columns are named after the formula): the documentation was corrected instead. Found on the way: messages that cp1252 cannot write stopped the scripts with their output redirected to a file.
- **Validation**: every new test fails with the code before; 1160 tests passed; the golden master is unchanged; the GUI workflow with real simulations again; details in [[../DEVLOG.md]].
- **Next step**: the release of 1.0.0 ([[../TODO.md]]).

## 2026-11-02 — Seven tabs in the GUI

- **Objective**: The answer of the author on the GUI: keep tkinter and add tabs for more steps.
- **Affected files**: `accim/gui/` (`forms.py`, `tasks.py` (new), `app.py`, `__init__.py`), `accim/data/postprocessing/main.py` (`Table.generate_fig_data`), `tests/core/test_gui.py`, `tests/core/test_table_figures.py` (new); [[../docs/source/4_detailed use.md]] (4.10), [[../README.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[decisions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-02 — The GUI keeps tkinter and gets tabs for more steps|the decision]]: the arguments of some zones, the aPMV setpoints, the renaming of the EPWs, `Table` and its figures, and a basic parametric study. Running the tabs with real simulations found that the figures of `Table` failed with run period tables (fixed in `Table`), needed colours and asked whether to rename the rows and columns (the GUI answers no); the test with a fake `Table` had missed them.
- **Validation**: 72 GUI tests and 5 figure tests with real `Table`s; the whole workflow through the window with real simulations (all seven tabs, no error); details in [[../DEVLOG.md]].
- **Next step**: the release of 1.0.0 ([[../TODO.md]]).

## 2026-11-02 — Descriptive names of the arguments in the whole package

- **Objective**: The answer of the author on the review of the names: the suggested names (option a), also for the arguments and parameters of the parametric module.
- **Affected files**: `accim/sim/`, `accim/run/run.py`, `accim/parametric_and_optimisation/`, `accim/_deprecation.py`, the sample scripts and notebooks, the tests (new `tests/parametric_and_optimisation/test_legacy_names.py`); [[../docs/source/9_migration_guide.md]], [[../docs/source/4_detailed use.md]], [[../docs/source/parametric_and_optimisation.rst]], the executed notebooks, [[../README.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-02 — The arguments and parameters have descriptive names, the same in the whole package|the decision]]: only the names of 0.x stay as deprecated aliases (arguments, attributes, parameters and saved results); the EMS variables, the tags of the output IDFs and the columns of `Table` keep their names.
- **Validation**: 1115 tests passed; the golden master is unchanged; 21 example notebooks run again without errors or deprecation warnings of accim.
- **Next step**: the GUI tabs (entry above).

## 2026-11-02 — The branch `claude/admiring-cori-fe6c57`: its check ported, the branch deleted

- **Objective**: The open question on that branch, for which the author asked for the recommended option.
- **Affected files**: `packaging/release.py`, [[../packaging/README.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-02 — The check of `claude/admiring-cori-fe6c57` is ported to `v1.0.0`, and the branch is deleted|the decision]]: only the check of `release.py`, the guide and the CHANGELOG entry were missing in `v1.0.0`; the branch is kept in a git bundle and was deleted with its worktree.
- **Validation**: a wheel of `v1.0.0` passes the check, and a copy with a `tests` package fails it.
- **Next step**: the other two answers of the author (the names of the arguments, the scope of the GUI).

## 2026-11-01 — A GUI in English (`accim-gui`)

- **Objective**: The third priority task of [[../TODO.md]]: a graphical user interface in English.
- **Affected files**: `accim/gui/` (new), `accim/__init__.py`, `setup.py`, `tests/core/test_gui.py` (new); [[../docs/source/4_detailed use.md]] (4.10), [[../docs/source/index.rst]], [[../README.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-01 — The first GUI uses tkinter and covers AddAccis, run_ep and the hours within the setpoints|the decision]]: tkinter, three tabs (add the ACCIS, run the simulations, hours within the setpoints), forms checked without tkinter, tasks in a thread with a log and no prompts. The scope was the author's to choose: open question in [[questions.md]].
- **Validation**: 25 tests; the whole workflow through the window with its threads (AddAccis, `run_ep` with processes, the hours table); `python -m accim.gui` opens; screenshots reviewed.
- **Next step**: the answers of the author (names of the arguments, scope of the GUI); then the release.

## 2026-11-01 — `ex_mm` for any existing HVAC system

- **Objective**: The second priority task of [[../TODO.md]]: develop `ex_mm`, which was "UNDER DEVELOPMENT" (it had to identify all the HVAC equipment of each zone to open the windows when the air conditioning is off).
- **Affected files**: `accim/sim/ems/program_lines.py`, `programs.py`, `accim/sim/hvac/existing.py` (rewritten), `hvac/resolver.py` (removed), `accim/sim/model.py`, `build.py`, `accis.py`, `tests/core/test_existing_hvac_mixed_mode.py` (new), the golden master; [[../docs/source/4_detailed use.md]] (4.1), [[../docs/source/9_migration_guide.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[decisions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-01 — `ex_mm` reads whether the HVAC system is off from the load that the thermostat asks for|the decision]]: instead of finding the equipment, the load that the thermostat of each zone asks for (0 when the HVAC system is off), for any equipment; `hvac_zone_map` is deprecated. The baseline showed two of the four sample models failing and, with the beams, windows open while cooling.
- **Validation**: the four sample models and the `ex_mm` configurations of the golden master simulate; PTACs identical to before; windows open with a load only in the first timestep of the load; both backends identical; details in [[../DEVLOG.md]].
- **Next step**: the GUI in English.

## 2026-11-01 — The hours within the setpoints, easy to measure and to filter by

- **Objective**: The first priority task of [[../TODO.md]] asked by the author: the hours within the setpoints easy to measure, to filter out the simulations below a percentage (working autonomously: the author could not answer).
- **Affected files**: `accim/sim/ems/program_lines.py`, `accim/sim/ems/programs.py`, `accim/data/postprocessing/setpoint_hours.py` (new), `accim/data/postprocessing/main.py` (`Table`), `tests/core/test_hour_counters.py` and `test_setpoint_hours.py` (new), the golden master; [[../docs/source/4_detailed use.md]] (4.7.1), [[../docs/source/parametric_and_optimisation.rst]], [[../docs/source/9_migration_guide.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[decisions.md]].
- **Finding or decision**: The counters were wrong, so the percentage could not be measured: the occupied comfortable hours kept their value out of the setpoints (up to 107 % of the occupied hours), and `CountHours_<zone>` never counted the cold hours and used the setpoints of the previous timestep. All corrected, which also fixed the P2 task of `make_averages`. See [[decisions.md#2026-11-01 — The hour counters are corrected, and the percentage within the setpoints is computed from them in Python|the decision]]: percentages in Python from the two counters, for CSV files and for tables of results. Found, not changed (P2 in [[../TODO.md]]): the block means of `Table` include the excluded zones.
- **Validation**: simulations of the sample model before and after (only the counters change; the occupied counters now add up); `b02` and `b17` with `make_averages` simulate; the example of the parametric documentation run end to end; 1012 tests passed; details in [[../DEVLOG.md]].
- **Next step**: the priority task of `ex_mm`, then the GUI in English.

## 2026-11-01 — The arguments of each zone, in one EMS program per zone

- **Objective**: The three changes asked by the author on `v1.0.0`: the arguments of the ACCIS for each zone or space, all the inputs of the EMS in one program per zone, and a review of the names of the arguments with suggestions; later, three tasks for the TODO (hours within the setpoints as a filter, `ex_mm`, a GUI in English) and a commit and push when finished.
- **Affected files**: `accim/sim/ems/inputs.py` (new), `programs.py`, `program_lines.py`, `objects.py`, `accim/sim/generation.py`, `accis.py`, `accis_single_idf.py`, `accim/utils/accim_args.py`, `verification.py`, `param_accis.py`, `main.py` of the parametric module; their tests and the golden master; [[../docs/source/4_detailed use.md]], [[../docs/source/9_migration_guide.md]], [[../CAMBIOS_CODIGO_v1.0.0.md]], [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See [[decisions.md#2026-11-01 — Each zone has its arguments in `SetInputData_<zone>`, run by `RunACCIS_<zone>` with the shared programs|the decision]]: `SetInputData_<zone>` with all the inputs, and `RunACCIS_<zone>`, which runs it and the shared programs and keeps for each zone the variables they read before setting them (without that, a zone took the setpoints of the zone that ran before it, as at the end of the day with ESP CTE). The names of the EMS variables do not change until the author answers the review of the names (open question in [[questions.md]], with a suggestion for each argument). Found, not changed (in [[../TODO.md]]): `CountHours_<zone>` reads the setpoints of the previous timestep and never counts the cold discomfort, and `make_averages` stops EnergyPlus in two cases; both as before.
- **Validation**: simulations of up to four output IDFs of each configuration of the golden master with the commit before and after: all their common outputs identical; with different arguments per zone, the setpoints of each zone equal those of a model whose zones all have its arguments, and both backends give identical files; 987 tests and the 87 numbered tests of the parametric module passed; details in [[../DEVLOG.md]].
- **Next step**: the answer of the author on the names; then the release (`master` must be fast-forwarded again to `v1.0.0`).

## 2026-11-01 — `v1.0.0` merged into `master`

- **Objective**: Move the changes of `v1.0.0` to `master`, as the author asked: the first step of the 1.0.0 release ([[../packaging/README.md]], §4.1).
- **Affected files**: none in the tree: the local `master` moved from `1a2f5947` to `a4a3e164`, the commit of `v1.0.0`; [[../TODO.md]] (the release item), [[questions.md]].
- **Finding or decision**: `master` was an ancestor of `v1.0.0` (29 commits behind), so it was fast-forwarded, as the branches merged into `master` on 2026-10-19 whenever possible; no merge commit. `master` is not pushed: §4.8 of the release guide pushes it after PyPI, because Read the Docs then builds `latest` from it. The local branch `claude/admiring-cori-fe6c57` (2 commits on the old `master`) is not in `v1.0.0`; what to do with it is a new question in [[questions.md]].
- **Validation**: `master` and `v1.0.0` point to `a4a3e164` and `git diff v1.0.0 master` is empty; `master` is 29 commits ahead of `origin/master`; `python -m pytest tests/core tests/parametric_and_optimisation -q -p no:cacheprovider` on `master`: 953 passed in 8 min 45 s, with no file left in the working tree.
- **Next step**: the question on `claude/admiring-cori-fe6c57`; then the release steps of [[../packaging/README.md]] (§4.1 to §4.11), with the push of `master` and of the tag at §4.8.

## 2026-10-31 — The refs of the branch reviews deleted

- **Objective**: Delete the refs reviewed in [[branch-reviews.md]], as the author confirmed.
- **Affected files**: [[../TODO.md]] (the three review items removed), [[../DEVLOG.md]], [[branch-reviews.md]], [[decisions.md]].
- **Finding or decision**: `refactor/sim-v1`, `review/refactor-sim-v1-20261024` and the tag `archive/feat-comfort-metrics-experiment-api` deleted locally and on `origin`, and the local tag `archive/codex-paper-simple-energy` deleted; a git bundle with their commits and the agent reports stay in the git-ignored `llm_project_files/branch_review_reports/`.
- **Validation**: `git ls-remote origin` lists only `master` and `v1.0.0`; no local ref of the four is left.
- **Next step**: none for the reviews; the open items are in [[../TODO.md]].

## 2026-10-31 — The last two recommendations: Pareto with constraints, checkpoints, comfort objectives

- **Objective**: Apply the recommendations that the author chose for the last two questions of [[questions.md]].
- **Affected files**: `accim/parametric_and_optimisation/_pareto.py` (new), `main.py`, `patches.py`, `objectives.py`; their tests; `docs/source/parametric_and_optimisation.rst`, `docs/source/9_migration_guide.md`; [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]], [[branch-reviews.md]].
- **Finding or decision**: Two decision records (see [[decisions.md]]). The Pareto status and the cleanup of the workers compare the evaluations as platypus does, with the constraints; the parametric checkpoints identify each simulation by the content of its IDF and EPW and its output names too; and two reducers turn the adaptive comfort status of EnergyPlus into a comfort objective with a fixed reference. `select_outputs` only finds the variables that the model already requests, so the status variable must be added first (the overview page shows how).
- **Validation**: the reducers agree with the timestep counts of a real simulation; 457 tests of the parametric module and the numbered tests 03 and 04 pass; details in [[../DEVLOG.md]].
- **Next step**: the author confirms the deletion of the refs reviewed in [[branch-reviews.md]].

## 2026-10-31 — Answers of the author on the branch reviews

- **Objective**: Apply the answers of the author to the questions of [[questions.md]]: everything to `v1.0.0` (1), the setpoints of CS6 with `ComfMod` 2 kept until checked (4), the orphan ideal loads systems removed (5); recommend for (2) and (3).
- **Affected files**: `accim/sim/hvac/vrf.py`, `accim/parametric_and_optimisation/objectives.py`, `accim/data/postprocessing/`, `accim/utils/`, `setup.py`; `tests/core/golden_master/`, `tests/core/test_golden_master.py` and the tests of PR 3; `tools/`; the How-to page of `Table`; [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]], [[branch-reviews.md]].
- **Finding or decision**: Three decision records (see [[decisions.md]]). PRs 2 to 4 of [[branch-reviews.md]] are in `v1.0.0`; the tests of PR 3 found 11 bugs, all fixed. The golden master runs each configuration in its own process: eppy keeps the IDD of the first model of a Python session (with `'auto'`, besos only warns), a finding added to [[../TODO.md]]. The heating setpoint of CS6 with `ComfMod` 2 equals the cooling one within its limits, which the TODO item records for the check.
- **Validation**: identical results without the ideal loads systems (whole year, both the ACCIS and the aPMV setpoints); the goldens equal the outputs checked against 0.8.2 except those objects, and `--legacy` repeats the comparison with 0.8.2; 87 numbered tests passed; details in [[../DEVLOG.md]].
- **Next step**: the author confirms the deletion of `refactor/sim-v1` and answers (2) and (3) of [[questions.md]].

## 2026-10-31 — The air-conditioned parametric notebooks close the windows of the sample model

- **Objective**: Apply the answer of the author (option (a)) to the open windows of the "fully air-conditioned" parametric notebooks.
- **Affected files**: the notebooks `03`, `wf1`, `wf3`, `wf4`, `wf5` and their pages; `docs/source/4_detailed use.md`, `docs/source/parametric_and_optimisation.rst`, `docs/README.md`; [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See [[decisions.md#2026-10-31 — The air-conditioned parametric notebooks close the windows of the sample model|the decision]]: WF1 and WF4 use `vrf_mm` with `HVACmode` 0, and the aPMV notebooks set the `ZoneVentilation` objects to `Always Off Discrete`; accim does not change, and its docs now warn that `vrf_ac` and `ex_ac` keep the natural ventilation of the model. The working folder of the first run kept the results of the morning, which inflated the folder sizes printed by WF1 and WF4: the notebooks were run again in a new folder, and `docs/README.md` now asks for one.
- **Validation**: the five notebooks run without errors and were exported; the HVAC electricity of WF3 drops from 171-228 to 67-87 kWh/m2; a subagent checked the texts against the new outputs and two claims by simulation. Details in [[../DEVLOG.md]].
- **Next step**: the other open questions of [[questions.md]].

## 2026-10-31 — Texts of the parametric notebooks checked against their results with 1.0.0

- **Objective**: Make the markdown of the 16 parametric notebooks, re-run with 1.0.0, agree with their new results.
- **Affected files**: markdown cells of `09`, `wf2` (cells 5, 15, 33), `wf3`, `wf4` and `wf5` in `accim/sample_files/jupyter_notebooks/parametric_and_optimisation_examples/` (and their executed copies), their pages in `docs/source/jupyter_notebooks/parametric_and_optimisation_examples/` (re-exported), `docs/source/parametric_and_optimisation.rst`.
- **Finding or decision**: WF2 no longer says that mixed mode needs AirflowNetwork: accim controls the `ZoneVentilation` objects of the sample model, and mixed mode uses about 3 % (Seville) and 4 % (Sydney) less HVAC electricity than air conditioning; the design days would add about 2 %, not 3 % (16 + 16 check simulations). Older statements contradicted by the outputs also fixed (WF3 hours within the aPMV setpoints, MCDM axis label in WF4/WF5, per-table normalisation of the plots in 09, seeds in the overview page). Found, not changed: with `ScriptType="vrf_ac"` (WF1, WF4) and with the aPMV setpoints (03, WF3, WF5), the always-open `ZoneVentilation` objects of the sample model stay open all year, so these "fully air-conditioned" runs heat and cool with open windows.
- **Validation**: `git diff` of the sources shows only the edited lines; the export of `09 wf2 wf3 wf4 wf5` wrote the 5 pages, which differ from the previous export only in those cells.
- **Next step**: the author decides how WF1, WF4, 03, WF3 and WF5 should close the windows of the sample model (notebook code or accim), and runs them again.

## 2026-10-31 — Pending tasks of TODO.md: ComfStand 0 and 22, plan filter, wrapper baseline, algorithms, post-processing, branch reviews

- **Objective**: Work through the pending tasks of [[../TODO.md]] after the sizing option (b) and the guide to the code changes.
- **Affected files**: `accim/sim/ems/setast.py`, `accim/sim/accis.py`, `accim/parametric_and_optimisation/main.py`, `analysis.py`, `utils.py`, `plotting.py`, `hourly_plotting.py`, `funcs_for_besos/param_accis.py`; new tests `tests/core/test_setast_static_standards.py`, and in `tests/parametric_and_optimisation`: `test_param_accis_filter.py`, `test_predef_wrapper_baseline.py`, `test_optimisation_algorithms.py`, `test_normalisation_multi_idf.py`, `test_normalised_units_aggregation.py`, `test_missing_csv_diagnostics.py`, `test_plot_floor_areas.py`; numbered tests 04 and 08 and the full-workflow scripts 01 and 02; [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], `docs/source/9_migration_guide.md`, [[../CAMBIOS_CODIGO_v1.0.0.md]].
- **Finding or decision**: The subprograms of ESP CTE and INT ISO7730 now set their setpoints whatever `ComfMod` is ([[decisions.md#2026-10-31 — The subprograms of ESP CTE and INT ISO7730 set their setpoints whatever `ComfMod` is|decision]]); the plan filter checks each rule; the wrapper baseline has the default coefficients of the custom model. Checking the algorithms one step at a time showed that platypus ignored `population_size` for 5 of them (100 simulations per generation), that EvolutionaryStrategy and OMOPSO (categorical) failed at their first iteration, and that the smoke test hid it with `evaluations=2` ([[decisions.md#2026-10-31 — `population_size` is the size of every generation, and the settings of the algorithms are checked first|decision]]). The regression tests of the post-processing found 11 problems (floor areas, units, double normalisation, calendar, diagnostics), fixed with the same pattern in the plots ([[decisions.md#2026-10-31 — The hourly tables of the parametric module follow the calendar of EnergyPlus|decision on the calendar]]); the tests of the groups of `split_by` found 3 more (zero-filled sums, uncategorised simulations dropped, groups left in J). The reviews of `refactor/sim-v1` and of the archived tags are in [[branch-reviews.md]]; the five small fixes of its PR 1 are in `v1.0.0`, and its other steps wait for the author ([[questions.md]]). The process items (priority rules, link format) have proposals and wait for the author.
- **Validation**: Erl interpreter tests that reproduce the errors of EnergyPlus without the fixes; numbered tests (87 passed) and the 5 full-workflow scripts with EnergyPlus 9.6, run again after the last fixes of the aggregation; golden master (only the two subprograms change); default suites, 762 passed. Details in [[../DEVLOG.md]].
- **Next step**: the decisions of the author ([[questions.md]]: the windows of the air-conditioned notebooks, the target branch of the PRs of the reviews, and the other open questions; the decisions of the day "to be confirmed" in [[decisions.md]]).

## 2026-10-31 — Sizing calculations of the VRF systems (option b)

- **Objective**: Implement the option chosen by the author for the open question on sizing: `add_accis_to_idf` enables the sizing calculations with the VRF script types, as `AddAccis` does.
- **Affected files**: `accim/sim/accis.py`, `accim/sim/apmv.py`, `accim/sim/outputs.py`, `tests/core/test_sizing.py`, docs (`4_detailed use.md`, `9_migration_guide.md`, `parametric_and_optimisation.rst`); [[../CHANGELOG.md]], [[../DEVLOG.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: See [[decisions.md#2026-10-31 — `add_accis_to_idf` and `add_vrf_system` enable the sizing calculations of the VRF systems|the decision]]. Also `apmv.add_vrf_system`, which adds the same autosized VRF systems. EnergyPlus also needs sizing periods (it stops only when the model has sizing objects and no `SizingPeriod` objects, checked in its source), so accim now warns in that case. The parametric overview page still used names of 0.x and said that mixed mode needs AirflowNetwork; fixed.
- **Validation**: EnergyPlus 9.6 end to end (runs with a sizing period; warns and stops as expected without); `test_sizing.py` 8 passed (6 fail without the change); golden master: only `SimulationControl` changes, in the 7 in-memory VRF/aPMV configurations; 518 passed. Details in [[../DEVLOG.md]].
- **Next step**: the guide to the code changes of 1.0.0, then the pending tasks of [[../TODO.md]].

## 2026-10-30 — accim 1.0.0: parametric tests that run, and integer actuators of the API backend

- **Objective**: Make the numbered tests and the full-workflow scripts of the parametric module run (they never had: 28 of 84 tests failed, also on `master`, and the 5 scripts stopped early), and set the integer actuators of the API backend as the EMS does.
- **Affected files**: `tests/test_setup.py`, `tests/parametric_and_optimisation/*`, `tests/parametric_and_optimisation_full_workflow/*`, `accim/parametric_and_optimisation/main.py` and `analysis.py` (two internal fixes), `accim/sim/energyplus_api/controller.py`, `accim/sim/ems/erl.py`; [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[questions.md]].
- **Finding or decision**: The tests were written for an older API and with test models that cannot size the VRF systems; fixed in the tests only, with a shared `enable_sizing()`. Running them found two crashes of the parametric module, fixed without changing its usage (an evaluation log named after the path of the EPW, and the Sobol analysis by EPW), and three problems left for the author in [[../TODO.md]]: ComfStand 0 (and 22) with the baseline ComfMod, the plan filter that stops its checks at a missing column, and the invalid baseline of `AccimPredefModelsParamSim`. The API backend now finds the type of each actuator and sets integer and logical actuators as the EMS (the API alone rounds them, which even crashed EnergyPlus in a test), and supports `@WarnEP`, `@SevereWarnEP` and `@FatalHaltEP`.
- **Validation**: numbered tests 84 passed; the 5 full-workflow scripts run to the end; `tests/core` and `tests/parametric_and_optimisation` 510 passed; both backends give identical CSV files for an EnergyPlus example with an integer actuator set to 6.6. Details in [[../DEVLOG.md]].
- **Next step**: the decisions of the author ([[questions.md]], [[decisions.md]], [[../TODO.md]]); run the parametric notebooks again; release.

## 2026-10-30 — accim 1.0.0: samples, notebooks and a check of the parametric module

- **Objective**: After the push of `v1.0.0`, update the sample scripts, notebooks and transcripts to the names of 1.0.0, and deal with the stale tests of the parametric module.
- **Affected files**: `accim/sample_files/script_usage/*.py`, the notebooks of `accim/sample_files/jupyter_notebooks` and their pages in `docs/source/jupyter_notebooks`, `docs/source/4_detailed use.md`, `docs/source/9_migration_guide.md`, `docs/README.md`, `accim/__init__.py` (lazy subpackages), `tests/core/*.py`; [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[decisions.md]], [[questions.md]].
- **Finding or decision**: A comparison of the parametric classes with 0.8.2 showed that `add_accis_to_idf` now applies the scheduled natural ventilation (mixed mode through `ZoneVentilation` objects), which in 0.8.2 only `addAccis` applied; kept and documented as a fix, since the results of the parametric module change for these models (see [[decisions.md#2026-10-30 — `add_accis_to_idf` builds the same model as `AddAccis`, including the scheduled natural ventilation|the decision]]). `add_accis_to_idf` still does not enable the sizing calculations, as in 0.8.2, which is why the full-workflow scripts of the parametric tests fail (open question in [[questions.md]]). All 28 failures of the numbered parametric tests are the same on `master`.
- **Validation**: the 7 How-to notebooks run without errors and their figures do not change; `tests/core` and `tests/parametric_and_optimisation`: 490 passed, plus a new test of the hash seed. Details in [[../DEVLOG.md]].
- **Next step**: the author confirms the decision and answers the question; run the parametric notebooks again with 1.0.0 (see [[../TODO.md]]).

## 2026-10-30 — accim 1.0.0: refactoring and Python API backend

- **Objective**: Refactor accim to the conventions of Python (PEP 8), faster and split into modules, and run its models through the Python API of EnergyPlus in parallel to eppy and the EMS, keeping the usage (and, at the author's request, the usage of `parametric_and_optimisation`); branch `v1.0.0`.
- **Affected files**: `accim/sim/**` (rebuilt: `accis`, `model`, `build`, `generation`, `ems/`, `hvac/`, `energyplus_api/`...), `accim/utils/**` (package, lazy), `accim/run/run.py`, `accim/_deprecation.py`, `accim/_besos_compat.py`, `accim/energyplus.py`, `accim/constants.py`, `accim/data/postprocessing/*.py`, internal calls of `accim/parametric_and_optimisation/main.py`, `tests/core/**`, `docs/source/**`, `README.md`, `setup.py`; [[../CHANGELOG.md]], [[../DEVLOG.md]], [[../TODO.md]], [[../ROADMAP.md]].
- **Finding or decision**: New names with deprecated aliases for those of 0.x (see [[decisions.md#2026-10-30 — PEP 8 names with deprecated aliases for accim 0.x|the decision]]); the API backend runs the EMS programs of the IDF in Python with the exact rules of the EMS, EnergyPlus 24.2 or later (see [[decisions.md#2026-10-30 — The Python API backend runs the EMS programs of the IDF in Python|the decision]]). The comparison with 0.8.2 found several bugs, fixed and listed in the CHANGELOG (combinations without setpoints, `SingleCooling`, `make_averages`, extra calling managers, tolerances...). A code review then found 6 more problems (Erl operators with Null, output variables in the scope of a program, long sums, `pow` of C, EPW names with dots, positional arguments of the deprecated class), checked against the source of EnergyPlus and fixed.
- **Validation**: output IDFs byte-identical to 0.8.2 in 29 configurations (with the corrections); identical CSV files with both backends for the 10 model types of accim and 9 of the 11 EMS examples of EnergyPlus; `tests/core` 279 passed, `tests/parametric_and_optimisation` 209 passed; `AddAccis` about 3 times faster. Details in [[../DEVLOG.md]].
- **Next step**: update the sample scripts and notebooks to the new names, then review, commit and release 1.0.0 (see [[../TODO.md]]).

## 2026-10-19 — Release guide

- **Objective**: Write a guide, like the one of the documentation, for building the distributions of accim and uploading them to PyPI.
- **Affected files**: `packaging/README.md`, `docs/README.md` (link to it); [[../DEVLOG.md]].
- **Finding or decision**: Written in Spanish, for the author, in `packaging`, which no distribution includes. Found while writing it: the wheel of accim installs a top-level `tests` package in site-packages, and the editable install of the author's Python keeps the metadata of 0.7.6.
- **Validation**: the checks of `release.py` that upload nothing (`tools`, `check`, `upload --dry-run`) and the commands of the smoke test ran. Details in [[../DEVLOG.md]].
- **Next step**: exclude `tests` from the packages of `setup.py` in the next release.

## 2026-10-19 — Maintenance guide of the documentation

- **Objective**: Write a guide in `docs` with everything needed to maintain the documentation, to reread it when in doubt.
- **Affected files**: `docs/README.md`; [[../DEVLOG.md]].
- **Finding or decision**: Written in Spanish, for the author, outside `docs/source`, so that Sphinx does not publish it. Found while checking it: the ComfMod figure of `4_detailed use.md` is linked from MDPI, which answers 403 to Read the Docs, so it is missing from the PDF and the EPUB; `docs/Makefile` points to `.` instead of `source`.
- **Validation**: the two scripts of the guide were run; its links and paths exist; markdown-it renders it. Details in [[../DEVLOG.md]].
- **Next step**: none.

## 2026-10-19 — Documentation after 0.8.2

- **Objective**: Check whether the documentation needed updates after 0.8.2, and update what was left.
- **Affected files**: `docs/source/4_detailed use.md`, `docs/source/8_pdfs_for_prev_versions.md`, the pages of `using_addAccis`, `full_example_IBPSA` and `research_paper_case_study`; [[../DEVLOG.md]].
- **Finding or decision**: The pages already described 0.8.2, and `using_Table` run again gives the same page. Only the version banners (v0.7.8 in the executed pages, v0.8.0 in the transcripts of `Detailed use`) and the page of previous versions were left. The author chose to run again only the three How-to notebooks that print the banner, not the parametric ones.
- **Validation**: same figures and results in the three pages; the differences are the banner, `InitASTvariables`, the order of the zones and the shortened logs. Details in [[../DEVLOG.md]].
- **Next step**: the parametric pages still print v0.7.8.

## 2026-10-19 — Release 0.8.2

- **Objective**: Publish accim 0.8.2 (with `accim-samples`): EnergyPlus 26.1 and 26.2, the `People:Definition` and `People:Instance` objects of 26.2, and the fixes of `TempCtrl='pmv'`, `ComfStand=[0]` and `Table`.
- **Affected files**: `accim/__init__.py`, [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: The author kept 0.8.2 although the release adds features (Semantic Versioning would make it 0.9.0). From TestPyPI only `accim` and `accim-samples` were installed (`--no-deps`), with the dependencies from PyPI. The clean environments get newer libraries than the development one (eppy 0.6.7, pandas 3.0.6), and accim works with them.
- **Validation**: tests; three clean venvs (local wheels, TestPyPI, PyPI) with imports and a 1-day simulation with EnergyPlus 26.2; GitHub release. Details in [[../DEVLOG.md]].
- **Next step**: none; `v0.8.2` is active in Read the Docs.

## 2026-10-17 — Release 0.8.1 (`pulp<4`)

- **Objective**: Fix the import of `accim.parametric_and_optimisation` in new installations: PuLP 4 renamed the `pulp.apis.*_api` modules that `pyehub` (a dependency of besos) imports.
- **Affected files**: `setup.py`, `accim/__init__.py`, [[../CHANGELOG.md]], `docs/source/5_troubleshooting.md`, [[../TODO.md]]; [[../DEVLOG.md]].
- **Finding or decision**: `'pulp<4'` in `install_requires` is enough. A shim for the renamed modules was not needed. The test of a clean installation with all the dependencies has to be done before the upload, from the local wheels (`pip install --find-links dist`).
- **Validation**: tests; clean venv with the local wheels before the upload; clean install from PyPI after it; GitHub release. Details in [[../DEVLOG.md]].
- **Next step**: activate `v0.8.0` and `v0.8.1` in Read the Docs.

## 2026-10-17 — Release 0.8.0

- **Objective**: Publish accim 0.8.0 on PyPI (with `accim-samples`), show 0.8.0 on Read the Docs and make the GitHub release.
- **Affected files**: `accim/__init__.py`, [[../CHANGELOG.md]], `README.md`, two pages of `docs/source`, a docstring and a stale test; [[../DEVLOG.md]].
- **Finding or decision**: 0.7.8 was never published, so the version goes from 0.7.7 to 0.8.0 and the texts that said 0.7.8 now say 0.8.0. A test that contradicted `f1e6bdc` (partial custom subplot orders) was removed. Only the tag `v0.8.0` was pushed. Right after an upload, the CDN can serve the old index page for a few minutes.
- **Validation**: tests; dry run from TestPyPI; clean install from PyPI; GitHub release with the three files of `dist/`. Details in [[../DEVLOG.md]].
- **Next step**: activate `v0.8.0` in Read the Docs.

## 2026-10-16 — How-to notebooks: one source, run with accim 0.7.8

- **Objective**: Make the sample files the only source of the How-to notebooks, correct them for accim 0.7.8 and EnergyPlus 25.1, run them and export them to the documentation.
- **Affected files**: the seven How-to notebooks and their IDFs in `accim/sample_files/jupyter_notebooks/`; new `docs/prepare_howto_notebooks.py`; `docs/source/jupyter_notebooks/` (exported notebooks; data copies removed); [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Three notebooks needed fixes of accim code, found here and made in PR #6: `Table.time_plot` with pandas 3, the `'nan'` checks of `rename_epw_files`, and the `SetAST` program of `addAccis` with several output IDFs (stale lines since `95b695b`). The executed copies were run against PR #6. Details in [[../DEVLOG.md]].
- **Validation**: the seven notebooks run without errors with PR #6, EnergyPlus 25.1 and pandas 3; local html build without warnings from these pages; `accim-samples` wheel 25.3 MB.
- **Next step**: merge after PR #6.

## 2026-10-16 — Sample notebook `full_example` removed

- **Objective**: Decide what to do with the older full example of the sample files (`jupyter_notebooks/full_example`, EPW files of Japan), which failed after `pip install "accim[samples]"` and was left out of the update of the How-to notebooks.
- **Affected files**: `accim/sample_files/jupyter_notebooks/full_example/` (removed); [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: The author chose to remove it rather than update it: it repeated `full_example_IBPSA`, which is in the documentation. Nothing in the repository links to the folder; the link that `addAccis()` prints to its old documentation page (404) changes in PR #6.
- **Validation**: `accim-samples` wheel 27.6 MB (29.8 MB before). Details in [[../DEVLOG.md]].
- **Next step**: optional page redirect in Read the Docs for the link printed by accim 0.7.8 and earlier.


## 2026-10-16 — Release scripts, README and docs for `accim-samples`

- **Objective**: Publish accim on PyPI and build the documentation by running the `dist_*.bat` scripts; explain in the README and the documentation how to run the example notebooks with `accim[samples]`, and remove section 0 of the README.
- **Affected files**: new `packaging/release.py`; `dist_build_package.bat`, `dist_upload.bat`, `dist_upload_test.bat`, `dist_build_docs.bat`; `docs/source/api/accim.parametric_and_optimisation.rst`; `accim/parametric_and_optimisation/main.py` (docstring); [[../README.md]]; `docs/source/{1_requirements,2_installation,4_detailed use}.md`; [[../DEVLOG.md]]; [[../Home.md]]; [[README.md|notes/README]]; [[decisions.md]]; `.github/copilot-instructions.md`; [[../CHANGELOG.md]].
- **Finding or decision**: The upload scripts uploaded all of `dist/`, which held an old 0.7.8.1 build; now only the current version goes, `accim-samples` before `accim`, after confirmation. The README section 0 was used by agents: its content moved to [[../DEVLOG.md#Tracking files|Tracking files]].
- **Validation**: both distributions built and checked; dry runs and cancelled uploads (nothing uploaded); docs built with the script. Details in [[../DEVLOG.md]].
- **Next step**: First upload of `accim-samples` (token for the entire account).


## 2026-10-16 — Agent-generated files removed

- **Objective**: Remove the files written by AI agents that do not belong in the repository, and the Spanish page on comparing pickles from Read the Docs, as the author asked.
- **Affected files**: `docs/source/index.rst`, `CHANGELOG.md`, `.gitignore`, [[../Home.md]], [[references.md]]; removed reports in `docs/` and at the root, run logs `exp_4_*_run.log` and tracked `.ipynb_checkpoints` folders. Full list in [[../DEVLOG.md]].
- **Finding or decision**: The author keeps this vault, `AGENTS_v2.md`, `.github/copilot-instructions.md`, `DEVLOG.md`, `TODO.md` and `ROADMAP.md`. The review and plan of 2026-07-25 left the repository and stay in the author's project files.
- **Validation**: no tracked file refers to the removed files; local html build with notebooks never executed.
- **Next step**: none.


## 2026-10-16 — The parametric notebooks in the documentation

- **Objective**: Show the workflows and tutorials of `parametric_and_optimisation_examples` on Read the Docs, as the author asked.
- **Affected files**: new `docs/prepare_parametric_notebooks.py` and `docs/source/jupyter_notebooks/parametric_and_optimisation_examples/` (index and 16 executed notebooks); `docs/source/conf.py`, `docs/source/index.rst`, `docs/requirements.txt`; tutorials 05, 08 and 09; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Read the Docs cannot run these notebooks (EnergyPlus), so the documentation shows copies run beforehand, as for the other notebook pages, and `conf.py` never runs notebooks. The copies are exported with relative paths, without progress bars, with shortened logs and smaller figures; a 256-colour palette shrinks most figures but bands heatmaps, so each figure keeps its colours when the palette would change it visibly. The runs used a copy of the committed accim (`git archive`, first in `PYTHONPATH`) because another session was editing the working copy.
- **Validation**: the 16 notebooks ran without errors; local html, latex and epub builds without errors or warnings from the new pages; pages checked in the browser. Details in [[../DEVLOG.md]].
- **Next step**: Merge into `master` so that Read the Docs builds the section; export wf4 and wf5 again after the minor fixes are committed.


## 2026-10-15 — Parametric plan, extra parameters, custom baseline and MCDM per front

- **Objective**: Fix the accim bugs that made tutorial 06 simulate the wrong model and ignore its roof insulation, and that forced workarounds in tutorial 05; choose compromise solutions per front. Requested by the author, with tests.
- **Affected files**: `accim/parametric_and_optimisation/main.py`, `analysis.py`, `plotting.py`; new `tests/parametric_and_optimisation/test_parametric_plan.py`, plus `test_parametric_worker.py` and `test_analysis_output_resolution.py`; tutorials 05, 06 and 10; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Parametric results now follow the task order (by IDF, EPW and plan row), with one row per plan row even when rows repeat, so parallel runs give the same table as sequential ones. The worker gets the non-accim BESOS parameters as a keyword argument, so the existing fake workers of the tests keep working. `get_best_compromise_solution` uses the same grouping as `plot_best_compromise_solutions`.
- **Validation**: 14 new tests, 11 failing on the previous code; parametric suite 174 passed, 1 old failure. Tutorials 05, 06 and 10 executed and checked (plan order, model of each row, effect of the roof thickness, ComfStand 99 in both IDFs). Details in [[../DEVLOG.md]].
- **Next step**: Commit, after the author's approval.


## 2026-10-15 — Notebooks wf3, wf5 and tutorials 00-10

- **Objective**: Finish the notebooks of `parametric_and_optimisation_examples`: wf3 and wf5 (aPMV setpoints, Examples 3 and 5 of the paper) and the tutorials 00-10, all runnable with the sample IDF and EPW files.
- **Affected files**: `wf2`, `wf3`, `wf5` and `00`-`10` in `accim/sample_files/jupyter_notebooks/parametric_and_optimisation_examples/`; [[../DEVLOG.md]].
- **Finding or decision**: The sample model has a work efficiency, clothing and air velocity of 1 in its People object, which overheats the zones under aPMV setpoints; wf3, wf5 and tutorial 03 set realistic PMV inputs. The aPMV cooling season is given by dates, so wf3 and wf5 use Seville only, and wf2 gives Sydney the cooling season of the southern hemisphere. Several tutorials ran without errors but gave wrong results; the causes in accim are listed in [[../DEVLOG.md]] (dropped `idf` column with one building, `additional_params` ignored by the parametric worker, custom-model baseline only on the first building, row order and duplicates in Morris/Sobol runs, MCDM over the fronts of all EPWs). None of them affects the campaign of the paper, which uses one building, accim parameters only and no Sobol/Morris.
- **Validation**: wf3 in full and wf5 reduced, without errors; tutorials 00-10 executed in order without errors. Details in [[../DEVLOG.md]].
- **Next step**: The author decides whether to fix those issues in accim and whether to commit the notebooks.


## 2026-10-15 — Notebooks wf1, wf2, wf4 and the parametric evaluation worker

- **Objective**: Rewrite the notebooks wf1, wf2 and wf4 of `parametric_and_optimisation_examples` after the handoff from the paper chat, with light simulations, and fix the bugs they exposed.
- **Affected files**: the three notebooks; `accim/parametric_and_optimisation/main.py` (`_run_single_evaluation_worker`); new `tests/parametric_and_optimisation/test_parametric_worker.py`; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Full hourly results only in wf1; wf2 and wf4 run in annual mode and simulate the chosen configurations or solutions again with hourly outputs (see [[decisions.md#2026-10-15 — Hourly results of the parametric notebooks only where they are analysed|the decision]]). The sample IDFs simulate 7 design days, which the annual readers added to the results (+3.3 % HVAC electricity); the notebooks set `Run_Simulation_for_Sizing_Periods = "No"`. The evaluation worker shared one folder with `keep_dirs=False`, could create `BESOS_Output` twice at once and lost the `add_outputs`; fixed. Mixed mode needs AirflowNetwork openings, which the sample model lacks.
- **Validation**: 6 new worker tests (4 fail on the previous code); parametric unit tests 160 passed, 1 failure that predates the change; the three notebooks executed with reduced runs. Details in [[../DEVLOG.md]].
- **Next step**: Design days in the sample IDFs; wf3, wf5 and tutorials 00-10.


## 2026-10-15 — Optional sample files: `accim` and `accim[samples]`

- **Objective**: Allow installing accim from pip with or without `accim/sample_files`, since more (heavy) notebooks will be added.
- **Affected files**: `setup.py`, `MANIFEST.in`, new `packaging/accim-samples/` and `packaging/build_samples_dist.py`, `dist_build_package.bat`, `dist_upload*.bat`, `.gitignore`, [[../README.md]], `docs/source/{1_requirements,2_installation,4_detailed use}.md`, [[../CHANGELOG.md]], [[../DEVLOG.md]].
- **Finding or decision**: pip extras only add dependencies, so the sample files are a second distribution, `accim-samples`, pulled in by the `samples` extra and installed into the same `accim/sample_files` folder (see [[decisions.md#2026-10-15 — Ship sample files as the separate distribution `accim-samples`|the decision]]). No runtime code uses `sample_files`. Parallel edits to the same file lost changes again (`setup.py`, `dist_build_package.bat`); they were re-applied one at a time.
- **Validation**: Core wheel 0.51 MB without sample files; samples wheel 29.1 MB with 129/129 files and no `accim/__init__.py`; install/uninstall of each distribution in a temporary venv left the other intact. Details in [[../DEVLOG.md]].
- **Next step**: First upload of `accim-samples` to TestPyPI/PyPI and test `pip install "accim[samples]"`.


## 2026-10-03 — Exp 4.4 failure: EnergyPlus MAX_PATH

- **Objective**: Find out why exp 4.4 fails on this PC with no `eplusout.err` written.
- **Affected files**: `accim/parametric_and_optimisation/main.py` (`_warn_if_out_dir_too_long_for_energyplus`); new `tests/parametric_and_optimisation/test_energyplus_path_length_warning.py`; `llm_project_files/entrega_pc_lab_20261002/accim_source/examples/paper_experiments/exp_4_*.py`; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: `llm_project_files` is a junction to OneDrive. `Path.resolve()` expanded it to a run folder of 257 characters, and EnergyPlus 9.4 cannot write output paths of 260 or more characters. Reproduced manually. The "á" is not the cause. The scripts now use `os.path.abspath`, and accim warns early. Most `main.py` edits from the previous session had not been saved and were re-applied; edits to the same file must not be run in parallel.
- **Validation**: 9 tests passed. A real exp 4.4 test run is noted in [[../DEVLOG.md]].
- **Next step**: Regenerate the delivery zip if needed.

## 2026-10-03 — Progress reporting in run_optimisation

- **Objective**: Show simulation progress during `run_optimisation`, similar to `run_parametric_simulation`.
- **Affected files**: new `accim/parametric_and_optimisation/optimisation_progress.py`; `accim/parametric_and_optimisation/main.py` (`run_optimisation`, new `show_progress` argument); new `tests/parametric_and_optimisation/test_optimisation_progress.py`; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: The final number of simulations is only an estimate (`pop × ceil(evals/pop)` per case for generational algorithms), so it is shown with `~`. Progress is reported from the main process by wrapping the Platypus default evaluator, and each finished job is reported through `as_completed`.
- **Validation**: Toy NSGA-II tests (sequential and process pool) passed: 3/3. Checkpoint-resume tests passed: 3/3.
- **Next step**: Check the output in a real multi-process run.

## 2026-10-03 — Filtered copies of per-simulation output CSVs

- **Objective**: Reduce the size of already-run results by writing column-filtered copies of each `eplusout.csv`, for both parametric and optimisation sessions.
- **Affected files**: `accim/parametric_and_optimisation/main.py` (`SimulationBase.filter_simulation_output_csvs` + private helpers); new test module `tests/parametric_and_optimisation/test_filter_simulation_output_csvs.py`; [[../docs/source/filter_output_csvs.rst|how-to guide]]; [[../CHANGELOG.md]]; [[../DEVLOG.md]].
- **Finding or decision**: Values are copied as text, so they are never re-formatted. Originals and session paths are never modified. Plan A pickles store `output_dir` relative to the campaign root, so callers must `chdir` there, as with `get_hourly_df*`. Experiment 4.3 has no consolidated results or CSVs. No new durable decision was needed.
- **Validation**: 33 new tests and 17 related tests passed (Python 3.14, pandas 3.0.5). Real-data runs on 4.1/4.2 wrote to a temporary folder: 420/420 files written, about 52–57% smaller, and a sampled copy matched the original verbatim. Details are in [[../DEVLOG.md]].
- **Next step**: Run the tests under Python 3.9 on the simulation PC; build the docs.

## 2026-09-13 — Integrate Obsidian vault into the repository

- **Objective**: Set up the repository root as an Obsidian vault for
  persistent documentation and working context, without duplicating
  existing technical documentation, tasks or code.
- **Affected files**:
  - Created: `Home.md`, `notes/README.md`, `notes/obsidian-tutorial.md`,
    `notes/work-log.md`, `notes/decisions.md`, `notes/questions.md`,
    `notes/references.md`, `notes/templates/daily-note.md`,
    `notes/templates/decision-record.md`, `notes/attachments/.gitkeep`,
    `.obsidian/app.json`, `.obsidian/core-plugins.json`,
    `.obsidian/community-plugins.json`, `.obsidian/templates.json`,
    `.github/copilot-instructions.md`.
  - Modified: `.gitignore` (ignore `.obsidian/`),
    `sync_branch.bat` (exclude `Home.md` and `notes/` from `git clean -fd`).
  - Not modified: `README.md`, `README.rst`, `CHANGELOG.md`, `DEVLOG.md`,
    `TODO.md`, `ROADMAP.md`, `AGENTS_v2.md`, `docs/source/**`, and all root
    reports (linked from `Home.md`, not rewritten).
- **Finding or decision**: No literal `AGENTS.md` exists (only
  `AGENTS_v2.md`); no multilingual README/TODO pair exists to mirror in
  English. See [[decisions.md]] for the full list of decisions made in this
  session.
- **Validation**: All wiki links in `Home.md` and `notes/**` were checked
  against real file paths and exact heading text; JSON files in `.obsidian/`
  were parsed successfully; YAML frontmatter parsed successfully in every
  new note; `git diff --check` reported no whitespace errors; a search for
  the old `git clean -fd` (without exclusions) found no other destructive
  cleanup scripts in the repository.
- **Next step**: Open the vault in Obsidian once to confirm the local
  `.obsidian/` settings are picked up as expected (attachments, new-note
  folder, templates folder, relative wiki links, auto-update on rename, and
  the requested core plugins).
