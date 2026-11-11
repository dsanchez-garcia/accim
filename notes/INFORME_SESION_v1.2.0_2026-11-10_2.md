---
title: Session report, accim v1.2.0, the review v04 (2026-11-10 and 2026-11-11)
type: report
tags: [vault, report, v1.2.0]
created: 2026-11-11
---

# Session report: the review v04 of accim 1.2.0 (2026-11-10 and 2026-11-11)

Branch `v1.2.0` of `D:\DSG\accim` (the same repository as `D:\Python\accim` on the other computer), from `d6dbae1`
and the commit of the author `0f8bb62` (block F and the review v04). The task of the author (2026-11-10): Step 0 of
[[PROPUESTAS_MEJORAS_post_1.1.0_v04.md]] (the 36 verdicts of its §5 to [[decisions.md]], `TODO.md` with its §6, the
P1 task of the renaming of B5, and the decision on `tr_mode`), then G1–G5, H1, E-F1, F1–F3 and H2–H6 as its §7 defines
them, one commit and one push each, with the rules of [[COPILOT_BRIEF_v1.2.0_v01.md]] (D1–D12), the equations and names
of [[PROPUESTAS_MEJORAS_post_1.1.0_v03.md]] §11–12, block F ([[PROPUESTA_ADAPTACION_INTERIOR_v03.md]] and
[[PROMPTS_COPILOT_bloque_F_v02.md]]) and the code as the truth for the current API. Each task has its entry in
[[../DEVLOG.md]] (context, changes, files, verification), in [[../CHANGELOG.md]] (Unreleased) and a section of
[[../CAMBIOS_CODIGO_v1.2.0.md]] (in Spanish); this report summarises them and does not repeat their details. The
previous report is [[INFORME_SESION_v1.2.0_2026-11-10.md]].

## 1. Tasks and commits

Every commit was pushed to `origin/v1.2.0` right after it was made (no force-push, no history rewritten). No task ended
blocked, so there is no `wip(...)` commit.

| Order | Task (v04 §7) | Findings and decisions | Commit | Status | CAMBIOS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | Step 0: the 36 verdicts to `notes/decisions.md`, `TODO.md` unblocked, the P1 renaming of B5, the decision on `tr_mode` | §4.4, §4.5, §5, §6 | `8c63702` | done | — |
| 1 | G1: the hooks of the ATHB and of the SET give their setpoints to the counters and outputs of the ACCIS (option (a)) | A4/A6-1 | `72ed578` | done | §23 |
| 2 | G2: `compute_setpoints`/`energyplus_running_means` reproduce the January branch of EnergyPlus (starts from 2 to 30 January) | E1-1, E2 doc | `33a5a58` | done | §24 |
| 3 | G3: the SET in the callbacks (`method='bisection'`), its outputs, `set_of_results`, the posture, the documentation of A6 | A6-1 to A6-4 | `e51e642` | done | §25 |
| 4 | G4: JPN Aqilah 2025 with `rmot_alpha` from the weather file; `static_heating_setpoint`/`static_cooling_setpoint` | B4-1, B4-2, §6.2 | `6109cc1` | done | §26 |
| 5 | G5: housekeeping (besos skips, `processes=0`, A3, B5 `noTol` and exact limits, SetVST, B1 formatter, Qatar, E4, docs) | A3-1/2, B5-1/3, B1-2, B3-1/3, E4-1/3, §3.4, §3.5 | `40eb001` | done | §27 |
| 6 | H1: `heating_setpoint_minimum`/`cooling_setpoint_maximum`, with deprecated aliases | §4.5 | `4e48ca4` | done | §28 |
| 7 | E-F1: the SET of the Pierce model of EnergyPlus against `set_tmp`, measured | block F §3 | `9a496ae` | done | §29 |
| 8 | F1: comfort standard 24, INT Sun2026 SET, on the hook of the SET by bisection | block F | `e376a1a` | done | §30 |
| 9 | F2: the limiter of the drift of the setpoints (`drift_mode`) | block F | `43de97a` | done | §31 |
| 10 | F3: the indicators of the adaptation to the indoor climate | block F | `590461b` | done; the simulations of its validation study blocked | §32 |
| 11 | H2: T0 of `te_ref_nl` of the whole day, from the weather file (`Schedule:File`) | B1-1 | `60d37a5` | done | §33 |
| 12 | H3: `long_term_range=('en16798', category)`, Method C for the PMV setpoints, `Table` by timestep | C2-1, D1-1, §6.5, #20 | `2b3c50f` | done | §34 |
| 13 | H4: the saturation of the ATHB, its frequencies, the ranges of met and air speed, a bounded scientific test | A4-1 to A4-3, §3.4 | `6f61692` | done | §35 |
| 14 | H5: an outdoor metric for each regime; several regimes in the YAML files; B2-1/B2-2 documented | B2-1, B2-2, §6.1, §6.4 | `90fdddc` | done | §36 |
| 15 | H6: `clothing_insulation=callable` as a `Schedule:File` from `outdoor_metrics` | §6 (A5) | `7ddd446` | done | §37 |

The order of v04 §7.1 was kept; E-F1 ran right before F1, as block F asks.

## 2. Deviations from v04, and why

The decisions of v04 §5–§6, D1–D12 and the `tr_mode` decision of the task were applied as given. The deviations below
are those beyond them; the design questions that these sources did not answer are in section 4 (provisional, in
[[questions.md]]).

- **Step 0.** The new task of the ATHB in mixed mode (verdict #34) was added to `TODO.md` with the others; the
  radiative fraction of the operative-temperature thermostats (0.5, which `tr_mode='zone'` needs) was checked in the
  code before recording the decision.
- **G1.** Option (a) was viable: the hooks write the variables of the new programs `ApplyHookSetpoints_<zone>`, which
  run right after `SetAST` and before the minimum and maximum of B5, so the counters, outputs and limits follow them.
  The setpoints of the hooks are the limits of the comfort band (the setpoints without the tolerance), and the
  thermostats get them with the tolerance of the zone (provisional, [[questions.md]]).
- **G2.** None. The documentation build needed pandoc on this server (`pip install pypandoc_binary`).
- **G3.** The access violation of `set_tmp` was traced (DEVLOG, 5 experiments, Python 3.14.3, numba 0.68.1,
  pythermalcomfort 4.8.1): it is the first call of `set_tmp` in a process that has loaded the library of the API of
  EnergyPlus, not the callback itself; `NUMBA_DISABLE_JIT=1` is not an option (pythermalcomfort uses `.py_func`). The
  warm-up therefore runs before `load_energyplus_api` (`prepare_hooks`); after it, the bisection runs in the callbacks.
  The table stays the default, as v04 §3.1 says.
- **G4.** The criterion of the test of 23 against its YAML twin 101 (|ΔComfTemp| < 0.1 K from day 21, > 1 K on day 1)
  holds for the starts of 1 April and 1 July and for the hours 2 to 24, not from 1 January (0.92 K on day 1) nor in the
  first timestep of each day (23 reads the RMOT of the previous day): the test checks it that way and records the
  values (provisional). The models of `add_accis_to_idf` gained the static setpoints of 23: 7 golden files written again
  on purpose (additions only; CHANGELOG and DEVLOG say so).
- **G5.** The minimum is also exact after the rounding (the finding only asked it for the maximum); verdict #13 was
  implemented literally (with `ACSTaul`/`AHSTall`, applicability limits of the outdoor metric); the static setpoints of
  Qatar are those of v04 §6.3 (20/25.5 °C) although Table B.2 gives 20/26 °C (the three provisional). The commit message
  of G5 begins with a byte-order mark (written with the default encoding of PowerShell); the later ones were written
  without it.
- **H1.** None (the old names keep working with a `DeprecationWarning`; the models with the old EMS inputs, from
  development builds only, must be made again).
- **E-F1.** None. The result (pythermalcomfort − EnergyPlus: −0.045 K mean and 0.18–0.20 K at most standing; −0.12 K
  and 0.32–0.34 K sitting) is in [[decisions.md]] and section 4.9.2 of the detailed use.
- **F1.** The comfort modes of 24 are 1 and 2 (0 keeps its meaning of static setpoints); the "CustAST_ACSTaul/all and
  AHSTaul/all limits" of the prompt are applicability limits of the outdoor metric, so the setpoints of the SET are
  bounded by the range of the bisection and the minimum and maximum of B5 only; the clothing of the dynamic model is
  read from its output; the backend without the API (v03 A6a) is a P2 task (all provisional).
- **F2.** The setpoint "applied the previous day" is that of its last timestep; the days without occupied hours do not
  change T_rm_in; the parameter `drift_mode` takes the codes 0, 1 and 2, 0 turning the limiter off (provisional).
- **F3.** The names in `Table` are `<zone>_SET_Pierce (°C)`, `<zone>_SET_Pierce_PMV`, `<zone>_CoolingEffect...`, not
  `SET` and `PMV_SET` of the proposal (`SET (°C)` is the SET of the hook, and `<zone>_PMV` would be part of
  `<zone>_PMV_SET`); the simulations of the validation study need choices that the proposal does not make (section 6).
- **H2.** The CSV file goes to the folder of the model with its absolute path; the schedule is written only for the
  models with a zone with `te_ref_nl`, and programs that begin with a weather file but do not read the schedule are
  written again (beginning with PMOT, with a warning) (provisional).
- **H3.** The building type is required in categories III and IV (`ValueError` listing both limits); Method C is on the
  scale of the PMV through the inverse of the index, with one output per zone and no building total, and in the
  parametric module `report_long_term_discomfort=True` adds it to the PMV setpoints (provisional).
- **H4.** The saturation is a summed output and a warning at the end of the simulation (`finish()`), not a counter of
  the ACCIS; the scientific test bounds the ATHB_PMV within 0.25 of the setpoint in at least 95 % of the occupied
  cooling timesteps (all of them in the week simulated; at most 0.68 with a setpoint of 0.5).
- **H5.** v04 §6.1 proposes a variable `Tout_metric_<k>` per metric; that name was already the output of the metric of
  each zone (B1), so the regimes use `ToutRegime_<regime>_<zone>` (and `RMOTr_<regime>_<zone>` for an own alpha), and
  `Tout_metric_<zone>` reports the metric of the regime of the timestep. In the YAML files the eight coefficients are
  required (as in `CustomRegime`), the last regime must be 'always' and the conditions 'hvac_off'/'hvac_on' are
  rejected; a comfort standard with regimes reuses the program of the regimes of the custom model (its branches read the
  inputs of the custom model and its metric is always `Tout_metric`). Two refinements of B2 came with it: the programs
  of the outdoor metric are kept while they calculate the metrics of the regimes (a plain `modify_accis` no longer loses
  the start with the weather file), and a zone that leaves the custom model loses its regimes when one has its own
  metric (it would replace the `Tout_metric` that other comfort standards read). All provisional.
- **H6.** The function receives a pandas Series of a column of `outdoor_metrics(epw)` (`'RMOT'` by default, α = 0.8)
  and must return one value per hour; the CSV file is named after the schedule, the weather file and the SHA-1 of the
  values; the GUI takes numbers only (provisional). Found while testing it: `read_epw_dry_bulb` (E1) failed with a
  `UnicodeDecodeError` on the sample `Seville.epw` (a header in Latin-1), so the weather files are now read as Latin-1
  (a regression test added). EnergyPlus 25.1 reports *Zone Thermal Comfort Clothing Value* as 0 with the method
  `ClothingInsulationSchedule` (as E-F1 had seen), so the test with EnergyPlus checks the *Schedule Value* hour by hour
  and the clothing that EnergyPlus reports with `CalculationMethodSchedule`; the documentation says it.

## 3. Entries of TODO.md

Added in the session (6, all P2):

- [P2][todo] The tests of `tests/core` that need besos without skipping (G5: four were made to skip; the others
  remain).
- [P2][blocked] Block F: the simulations of the validation study of F3 (section 6).
- [P2][todo] Comfort standard 24 without the API: the fallback of the EMS (v03 A6a) (F1).
- [P2][todo] A4: the metabolic rate of the People objects in the hook of the ATHB (`met='people'`) (H4).
- [P2][todo] A6: the setpoints of the SET at the limits of their range (H4: the saturation of the SET, as that of the
  ATHB).
- [P2][todo] A4: the setpoints of the ATHB in mixed mode (Step 0, verdict #34).

Done and removed (10): `Table` with `source_frequency='timestep'` (P1, H3); E1, the 0.14 °C of PMOT from 8 January
(P1, G2); B2, the outdoor metric of each regime (H5); B4, the arguments of the static setpoints of 23 (G4); B3, the data
of Qatar (G5) and several regimes (H5); C2, Method C (H3); A6, the SET of pythermalcomfort in the callbacks (G3); A6, the
cooling effect and the Erl way (Step 0: the Erl way discarded, the cooling effect an indicator of F3); A5, the clothing
as a function of the outdoor temperature (H6). The P1 renaming of B5 and the tasks G1, G5, H2, H4 and E-F1/F1/F2/F3
that Step 0 added were done within the session.

Still blocked: CIBSE TM52/TM59 (C2 and D1) and the notebook and test of the Future Weather Generator (E4), as the task
says, and the validation study of F3. Still open and pending the author from before: comfort standards 9 and 10 (their
running means look swapped) and comfort standard 9 in comfort mode 1 (P1).

## 4. Provisional decisions in notes/questions.md

23 entries, each with the most conservative, backward-compatible option implemented provisionally (the options and
reasons are in [[questions.md]]):

- G1 — the tolerance of the setpoints of the ACCIS with the setpoints of the hooks: the hooks give the limits of the
  comfort band, and the thermostats get them with the tolerance of the zone.
- G4 — the criterion of the test of 23 against 101: as measured (section 2).
- G5 — verdict #13 with `ACSTaul`/`AHSTall`; the static setpoints of Qatar 20/25.5 °C; the minimum exact after the
  rounding, as the maximum.
- F1 — the comfort modes 1 and 2 of 24; the limits of the prompt as applicability limits; the clothing of the dynamic
  model read from its output.
- F2 — the setpoint applied the previous day; the days without occupied hours; `drift_mode` 0 turns the limiter off.
- F3 — the SET of the indicators (the Pierce model of EnergyPlus); the overcooling (both variants in the cooling season,
  one threshold); T_rm_in and the band of Tn_exp (2.5 K, the AC coefficients by default); the static reference of case
  (i) of the validation study (open).
- H2 — the folder of the CSV file of T0; which models get the schedule.
- H3 — the building type in categories III and IV; Method C on the scale of the PMV and its output.
- H5 — the schema of `regimes` in the YAML files; the EMS code of a comfort standard with regimes; the names of the
  metrics of the regimes and the programs kept.
- H6 — the outdoor temperature of the functions of the clothing insulation, how they are called, and the names of their
  CSV files.

## 5. Tests and backend comparisons

The whole suites after the last commit of code (H6): `py -m pytest tests/core -q -p no:cacheprovider`:
**1520 passed, 2 skipped** (24 min 35 s; the golden master byte-identical); `py -m pytest
tests/parametric_and_optimisation -q -p no:cacheprovider`: **518 passed** (2 min) (Python 3.14.3).
The two skipped tests need what this machine does not have: the jar of the Future Weather Generator (`ACCIM_FWG_JAR`)
and EnergyPlus 26.1.

| Task | New or changed tests (main files) | `tests/core` after it | Parametric | Golden master |
| :--- | :--- | :--- | :--- | :--- |
| Step 0 | none (no code) | — | — | — |
| G1 | `test_comfort_hooks.py` 23 (5 new, 6 changed) | 119 passed in the related files | — | unchanged |
| G2 | `test_preview.py` 2 new, `test_verification.py` | 44 passed in both files | — | unchanged (no IDF changes) |
| G3 | `test_comfort_hooks.py` 28 (5 new, 3 changed) | 58 + 47 passed in the related files | — | unchanged |
| G4 | `test_jpn_aqilah2025.py` 28 (13 new or changed) | 1269 passed, 2 skipped | 507 passed | 7 files written again on purpose (the static setpoints of 23 in the models of `add_accis_to_idf`) |
| G5 | limits, hooks, A3 (17), `processes=0`, metrics, Qatar, E4 | 1286 passed, 2 skipped | 507 passed | unchanged (35 passed) |
| H1 | the old names, the parametric names, the GUI sessions | 1323 passed, 2 skipped | 509 passed | unchanged |
| E-F1 | `test_pierce_set.py` 2 (1 with a yearly EnergyPlus run) | 50 passed in the related files | — | unchanged |
| F1 | `test_sun2026_set.py` 18 | 1329 passed, 2 skipped (and `test_zone_arguments.py` 32 after its fix) | 509 passed | unchanged |
| F2 | `test_drift_limiter.py` 11, `test_drift_parameters.py` 2 | 1356 passed, 2 skipped | 511 passed | unchanged |
| F3 | `test_indoor_adaptation.py` 20 | 1377 passed, 2 skipped | — | unchanged |
| H2 | `test_outdoor_metric.py` 42, `test_schedule_files.py` 4 | 1386 passed, 2 skipped | 511 passed | unchanged |
| H3 | `test_long_term_discomfort_counters.py` 52, `test_ppd_weighted_hours.py` 49 | 1469 passed, 2 skipped | 517 passed | unchanged |
| H4 | `test_comfort_hooks.py`, `test_table_optional_outputs.py` 49 | 1472 passed, 2 skipped | — | unchanged |
| H5 | `test_regime_metrics.py` 14, `test_standard_regimes.py` 22 | 1508 passed, 2 skipped | 518 passed | unchanged |
| H6 | `test_pmv_input_parameters.py` 11 new, `test_preview.py` 1 new | 1520 passed, 2 skipped (the first run: 3 failed, fake models without `Schedule:File`, fixed) | 518 passed | unchanged |

The documentation build (`py -m sphinx -E -b html docs/source docs/_build/html -w docs/_build/sphinx_warnings.txt`,
with pandoc from `pypandoc_binary`) kept the warnings of the baseline in every task: 59 warning lines before the
session and after G1–G3 (G4 fixed two references of MyST to a label without a title); from G5 on they were counted as
unique lines, 35 in the baseline and in every build. The changed modules compile with Python 3.9.

EMS code and hooks that changed were simulated with both backends (EnergyPlus 25.1, the sample model in Seville,
`check_exact=True` unless said otherwise); every comparison gave identical results:

| Task | Simulations | Result |
| :--- | :--- | :--- |
| G1 | 15–21 July, API backend with the hooks; the model with the objects of the hooks without a hook (EMS vs API); constant setpoints 21.5/26.5 °C given by a hook (API) and by the same lines in `RunACCIS_<zone>` (EMS): schedules, setpoints without the tolerance and comfortable hours | identical; the setpoints and counters of the hooks within 1e-4 of those of the bisection and the table |
| G3 | two days by bisection with `run_ep(backend='api')` in a new process | setpoints and `SET_<zone>` within 1e-6 of the values that the sensors read |
| G4 | 23 from 8 January with the weather file, static 21/26 °C | identical; check 4 without mismatches in 2016 timesteps |
| G5 | a winter and a summer week with the minimum and maximum; `processes=0` | identical; checks 4 and 5 without mismatches |
| H1 | the B5 simulations with the new names | identical |
| F1 | two weeks without the hook (EMS vs API) | identical (the outputs of the hook 0) |
| F2 | 1–30 April, window and rate | identical |
| H2 | `te_ref_nl` with the `Schedule:File` | identical; check 4 without mismatches |
| H3 | a summer week with `long_term_range=('en16798', 2)`; the PPD-weighted hours with the aPMV and the PMV | identical; the outputs calculated from the PMV within 1e-9 |
| H4 | without the hook, and with constant setpoints by a hook and by the programs | identical |
| H5 | 1–7 April: the custom model with two regimes with their own metrics; a comfort standard with two regimes | identical; check 4 without mismatches (`custom_regime`, `Tout_metric`, ACST, AHST, ComfTemp) in the 1008 timesteps of each zone |

No EMS code changed in G2, G3 (the hook only adds sensors and outputs), E-F1, F3 and H6.

## 6. Blocked items, and the exact information that is missing

- **C2 and D1, CIBSE TM52 and TM59.** The texts of CIBSE TM52 (2013) and TM59 (2017): the hours of exceedance, the
  weighted exceedance of a day and the upper limit of TM52, and the criteria for dwellings of TM59 (out of scope, D12).
- **E4, the How-to notebook and the test with the tool.** The jar of the global Future Weather Generator on the machine,
  in the environment variable `ACCIM_FWG_JAR`, and the version of Java it needs (Java 1.8.0_481 is installed); then the
  command line of the Java engine of accim (8 arguments) checked against that of pyfwg for version 3 (12 arguments),
  which v04 §6.7 takes as the reference.
- **Block F, the simulations of the validation study of F3.** The climates ("the cities of the articles on heat of the
  group" and "a humid one", not named in the proposal); the static reference of case (i) (the PMV setpoints of
  `apply_pmv_setpoints`, the static setpoints of a comfort mode 0, or fixed temperatures; open in [[questions.md]]);
  the seasonal clothing insulation schedule of case (iii); the air velocity schedules of case (iv) (0.1, 0.6 and
  1.0 m/s in the cooling season: when and where); and the future weather files of 2050 and 2080, which need the jar of
  the Future Weather Generator.
- Pending the author from before the session (not tasks of v04): which running mean comfort standards 9 and 10
  (IND IMAC R 7DRM and 30DRM) must use, and the heating setpoint of comfort standard 9 in comfort mode 1 out of the
  applicability limits.

## 7. Environment

- Python 3.14.3 (`py`), with numba 0.68.1, pythermalcomfort 4.8.1, besos and eppy; Python 3.9 for the compatibility
  checks. EnergyPlus 9.4, 9.6, 25.1 (with its Python API), 25.2 and 26.2; EnergyPlus 26.1 is not installed.
- Installed during the session: `pypandoc_binary` (pandoc for the documentation build).
- No jar of the Future Weather Generator on the machine (Java 1.8.0_481 is installed).
