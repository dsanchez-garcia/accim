---
title: Session report, accim v1.2.0, session 4 (2026-11-12)
type: report
tags: [vault, report, v1.2.0]
created: 2026-11-12
---

# Session report: session 4 of accim 1.2.0, the implementation of the decisions of 2026-11-12

Branch `v1.2.0` of `D:\DSG\accim`, from `f3f9eb5` (the decisions on the six questions that session 3 left open, taken
for the author on the same day: [[decisions.md]]). The task of the author: "Quiero que continúes con las
implementaciones P1 y P2, si hace falta, en otro chat; trabaja de forma autónoma", that is, the P1 and P2 tasks that
those decisions left in [[../TODO.md]], autonomously, with the rules of the review sessions
([[COPILOT_SIGUIENTE_SESION.md]] §2): one commit and one push for each task, the definition of done, and no invented
formula. A session of Claude Code on the server. Each task has its entry in [[../DEVLOG.md]] (context, changes, files,
verification), in [[../CHANGELOG.md]] (Unreleased) where users see it, and a section of
[[../CAMBIOS_CODIGO_v1.2.0.md]] (in Spanish, §44–§55); this report summarises them and does not repeat their details.
The previous report is [[INFORME_SESION_v1.2.0_2026-11-11_3.md]].

**What to read first.** Three things came out of the session that are not in its tasks:

1. An open question of the validation study of F3 ([[questions.md]]): the air speed of the fans of case (iv) raises
   the heating setpoint of the causal SET model too, and the limiter of the drift acts on the setpoints of a hook
   within the day and in the unoccupied hours more than on the drift between days (section 4).
2. A finding of the final checks: with the models of `add_accis_to_idf`, the EMS and API backends give identical
   setpoints and EMS outputs, but the other outputs differ in their last digits. It is older than this session
   (section 5).
3. What only the author can do (section 6): the message to Ruiji Sun, the weather file of the humid climate and a
   model for the study, the jar of the Future Weather Generator, and the issue for EnergyPlus.

## 1. Tasks and commits

Every commit was pushed to `origin/v1.2.0` right after it was made (no force-push, no history rewritten).

| Order | Task | Decisions and findings | Commit | Status | CAMBIOS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Comfort standards 9 and 10 (IND IMAC R 7DRM and 30DRM) read the running means of their models: 10 reads PMOT, and 9 the mean of the 7 previous days that the EMS calculates (`'ndrm'`); the heating setpoint of comfort mode 1 of 9 out of its limits takes the minus sign | decision 11 | `e650068` | done | §44 |
| 2 | The thermostats get the minimum and the maximum of the setpoints with the tolerance; a maximum less than twice the tolerance above the minimum is a `ValueError`; the warning of S1 and check 5 follow | decisions 6 and 10 (A19, S1) | `c92afd2` | done | §45 |
| 3 | Every zone of a model with the code of JPN Aqilah 2025 has the inputs of its static setpoints, so a zone edited by hand to comfort standard 23 runs | decision 7 (A24) | `f1ebe0c` | done | §46 |
| 4 | E-F1 measured again, by activity level (110.7, 115 and 126 W/person), with both body surface areas and both postures; its documentation; the draft of the issue for EnergyPlus | decisions 1 and 2 (A1, A2) | `ca36b88` | done | §47 |
| 5 | A model prepared for a hook is not simulated without it in silence: `run_ep` raises with the EMS backend, and the backend of the API warns (`MissingHookWarning`) | decision 3 (A4) | `fdea779` | done | §48 |
| 6 | `modify_accis` warns when the zones of JPN Aqilah 2025 lose the start with the weather file | decision 8 (A25) | `7dc94b6` | done | §49 |
| 7 | `drift_mode='window'` is an experimental mode, with a warning; `'rate'` is the recommended one; the cost of the window, measured again | decision 4 (A8) | `84abcfd` | done | §50 |
| 8 | The SET of pythermalcomfort is the reference SET of the causal band: the documentation and the docstrings | decision 12 (#9 of the review) | `eaf7aa3` | done | §51 |
| 9 | `pythermalcomfort_set='people'`: the indicators of the causal band with the inputs of the occupants of the People objects in each row | decision 9 (S4, option (ii)) | `bb1e5bf` | done | §52 |
| 10 | The limitation of the constant range of `long_term_range` in the documentation, and the seasonal range of EN 16798-1, Table B.5 (`'en16798_seasonal'`) | decision 5 (A15) | `b5fad7d` | done | §53 |
| 11 | The validation study of F3: the script of its simulations, `tools/indoor_adaptation_study.py` (26 cases), tried with a winter and a summer week | decision 13 | `f808f24` | the script is done; the study is not run (the entry of `TODO.md` stays) | §54 |
| 12 | Final checks: the test of A24 runs both backends; the finding of the models of `add_accis_to_idf` | section 5 | `aa4931c` | done | §55 |
| 13 | This report | — | (the last commit) | done | — |

## 2. Deviations from the instructions, and why

- **The scope.** "The P1 and P2 implementations" were read as the eight P1 and the three P2 tasks that the decisions
  of 2026-11-12 left in `TODO.md` (the list of the consequences of those decisions in [[decisions.md]]). The other
  entries of `TODO.md` were not touched. One of them is a P1 of 2026-11-09 (check 1 of `verify_accim_simulation` skips
  the zones whose names have ':', as those of the sample model): it was left because, as its entry says, check 1
  would then report the mismatches of the models where it did nothing so far (in the try-run of F3 with fixed
  setpoints, the zones of the sample model are above 26 °C with the cooling on in 91 of their 120 occupied hours of
  the week of July), so it needs a decision on what check 1 compares, not only the fix of `find_col`.
- **F3: the script, not the study.** A year of a case of the causal SET model takes hours (its hook inverts the SET by
  bisection in each timestep), the choices are to be agreed with Ruiji Sun first, and the humid climate and the years
  2050 and 2080 need files that the author gets. The script has all the cases but the static reference (a), the PMV
  setpoints of `apply_pmv_setpoints`, whose models have no outputs of the ACCIS for the indicators of `Table`. Its
  try-runs are with the sample model, which is a test model: their numbers are not results of the study.
- **The verification of the first tasks ran with later tasks in progress.** The whole suite of `tests/core` ran twice
  during the tasks, with the working tree of the moment: after task 1 (3 failures, which pass when run again: two
  tests of old chains corrected within the task, and one whose EnergyPlus run shared the working folder with three
  simulations of the measurement of E-F1) and after task 3, when the tree already had the changes of tasks 4 and 5
  (3 failures, all of them from those changes and corrected in their tasks: a helper of the test of E-F1 that another
  test calls, a wrong expectation of a new test of A4, and the test of the next point). The edits of the
  documentation of task 5 were taken out before the commit of task 4 and applied again after it. While the tests of
  task 6 ran in the working tree, four hunks of task 7 (the warning of the window) were written in
  `accim/sim/accis.py`; the commit of task 6 has the file without them. From task 8 on, the tests and the
  documentation build of each task ran in a temporary git worktree with a copy of the working tree (`HEAD`, its
  uncommitted changes and its untracked files), so that the next task could be edited meanwhile; one commit for each
  task was kept by saving the files that several tasks share (the notes and the documentation) as they were at the
  end of each task (`git hash-object -w`) and staging those blobs (`git update-index --cacheinfo`). The final checks
  of section 5 ran on the final tree, with all the tasks together.
- **A4: a test changed with the decision.** `test_the_optional_outputs_of_a_simulation` simulated a model prepared for
  the hook of the ATHB with the EMS backend. A4 forbids it, so the test now checks the `ValueError` and simulates
  with the backend of the API and the hook, and asserts that the output of the hook is not 0 (with the EMS backend
  it was 0, which the test did not look at): it is stricter, not looser.
- **A8: `'rate'` is not the same as no limiter.** The finding said that `'rate'` gave the results of no limiter in
  that model. Measured again: with 0.5 K/day it changed the setpoints by about 0.2 K on two Mondays of April and one
  of July, whose targets were more than 0.5 K from the setpoints of the last occupied day (the Friday), with 27 kWh
  more of the heating coils in April. The documentation has what was measured.
- **S4 (ii): a correction found on the way.** The sensor of the mean radiant temperature of the hooks of the SET reads
  that of the timestep itself, not that of the previous one, as the documentation said (measured: with the values
  that the sensors read, the SET of the results is that of the hook within 0.001 K). Only the documentation and the
  docstrings changed.
- **A15.** Between the seasons (a running mean of 10 to 15 °C) the standard only says that the limits are between
  those of both seasons: the counters take the lower limit of the heating season and the upper limit of the cooling
  season there (a choice, recorded). The list of the graphical user interface keeps the constant ranges only.
- **E-F1.** No code of accim changes: the hooks keep 1.8 m² (decision 1, option (i)); the measurement is a test.
- **The golden master changed on purpose in two tasks**, compared line by line before `--update-golden`: task 1 (21 of
  its 31 configurations: the output IDFs of 9 and 10, a line of `SetVST` in the models in mixed mode, and the chains
  of 9 and 10 in the models with all the comfort standards) and task 3 (`s01` to `s06` and `s09`: two lines in each
  program `SetInputData_<zone>`).
- **Task 12 was not in the list.** The final checks found that the EnergyPlus test of A24 ran with the EMS backend
  only; adding the other backend showed the finding of section 5, which got its own commit.
- **The baseline of the documentation build** is that of session 3: 55 lines in the file of warnings, 33 distinct
  warnings without their line numbers and the folder of the repository.

## 3. Entries of TODO.md

Removed, done in this session (11): comfort standards 9 and 10 (two entries: the running means, and the sign of
comfort mode 1 of 9); A19 with S1; A24; A4; A8; A25; the documentation of the reference SET; E-F1 measured again;
`pythermalcomfort_set` with the inputs of the People objects; `long_term_range` (A15).

Added (2):

- [P2][todo] The static setpoints of IND IMAC (comfort standards 7 to 10): check the line 0.078·T + 23.25 in the
  National Building Code of India 2016 (from task 1: the paper of the adaptive models does not have it).
- [P2][todo] The EMS and API backends differ in their last digits with the models of `add_accis_to_idf` (section 5).

Changed (2):

- [P2][todo] Block F, the simulations of the validation study of F3: its status (the script, and what is left: the
  simulations, the humid climate, the static reference (a), the future weather files, the two open points of the
  design, and a model of the study) and its definition of done.
- [P2][todo] The message of the author to Ruiji Sun: one more point to ask (the air speed of the heating setpoint of
  case (iv)).

`TODO.md` has 22 entries now: one P1 (check 1 of `verify_accim_simulation`, section 2), 20 P2 to do and one P2
blocked (E4: the jar of the Future Weather Generator).

## 4. Decisions of the session, and the open question

The choices that the decisions of 2026-11-12 do not cover are in [[decisions.md]] ("The implementation of the
decisions of 2026-11-12: the choices that they do not cover", items 1 to 11, one for each task), and the measurement
of E-F1 has its own entry there. The main ones:

- **Comfort standard 9**: its 7-day mean is that of the EMS code of the outdoor metric of the custom models (`'ndrm'`
  with 7 days), which begins with the weather file (`epw`) or, without it, with PMOT and a warning; the models of
  earlier versions keep their code.
- **A19**: a maximum less than twice the tolerance above the minimum is a `ValueError` (the thermostats would cross),
  as the window of the limiter.
- **A4**: an error with the EMS backend of `run_ep` (which cannot run a hook) and a warning with the backend of the
  API (the model still runs); the models simulated out of accim are not covered, and no EMS output was added.
- **S4 (ii)**: the value `'people'`, with the schedules read from the model of each simulation (found by the name of
  its CSV file, or given with the key `'idf'`).
- **A15**: `long_term_range=('en16798_seasonal', category, building_type)`, with the seasons by the running mean of
  each timestep (below 10 °C and above 15 °C), in the EMS counters, in check 6 and in the postprocessing.
- **F3**: the choices of the script that decision 13 does not make (the base model of the cases of the causal SET
  model, their minimum heating setpoint of 18 °C, the hours of the fans, the cases of the limiter, the seasonal range
  of the offices of category II for every case).

**Open, in [[questions.md]]: the validation study of F3.** The try-runs of the script (8–14 January and 15–21 July of
the sample model in Seville) showed two things that the decisions do not cover:

1. *The air speed of the fans is in both setpoints.* The hook of comfort standard 24 converts both limits of the
   causal band with the air speed of the People object (decision 5 of the author of 2026-11-10), so with 1.2 m/s the
   heating setpoint goes from about 19 °C to 25.0–26.7 °C in the hours of the fans, and the heating coils work in the
   first of them in July (10.6 kWh in the week; 1.4 kWh with 0.9 m/s). The proposal of block F had an
   `air_speed_cooling`, for the cooling setpoint only.
2. *`drift_mode='rate'` limits every timestep*, the unoccupied ones too, to the mean of the setpoints of the occupied
   timesteps of the day before ± its rate (decision 13 of session 3). With the setpoints of a hook, which change
   within the day, and much more with the fans, it keeps the setpoints of the occupied hours at night: with 1.2 m/s
   and 0.25 K/day, 343.6 kWh of the heating coils in the week of July instead of 10.6, and 1549.6 kWh of the cooling
   coils instead of 2043.7, most of the difference in the unoccupied hours. Without fans, the limiter still changed a
   setpoint in 81, 70 and 25 of the 120 occupied hours (0.25, 0.5 and 1.0 K/day), with little energy. So case (v) of
   the causal SET model would measure mostly that, and not the sensitivity of the savings to the rate of the drift.

Nothing was changed for them: the script has the cases as decided, and its docstring, `TODO.md` and sections 4.2.7
and 4.7.6 of the detailed use say what happens. The question has the numbers and the options (an air speed of the
cooling setpoint only; fans above a temperature; limiting the occupied timesteps only, or the daily mean; leaving the
causal SET model out of case (v)).

## 5. Tests and backend comparisons

The final checks, in a temporary worktree. The whole suites ran on the code of `f808f24`; task 12 changed one test
afterwards, which was run with its file (the fourth row):

| Check | Result |
| :--- | :--- |
| `py -m pytest tests/core -q -p no:cacheprovider` | **1615 passed and 2 skipped**, no failure (34 min 29 s); the skipped ones need EnergyPlus 26.1 and the jar of the Future Weather Generator |
| `py -m pytest tests/parametric_and_optimisation -q -p no:cacheprovider` | **520 passed** (2 min 16 s) |
| The golden master (`tests/core/test_golden_master.py`, within the first suite) | 35 passed: byte-identical (also on its own on `aa4931c`) |
| `tests/core/test_jpn_aqilah2025.py`, with the test of A24 of task 12 (on `aa4931c`) | 31 passed (2 min 12 s) |
| The documentation build, after the last change of the documentation | succeeded, with the warnings of the baseline (no new one, none gone) |
| The 45 Python files changed since `f3f9eb5`, with Python 3.9 (`py -3.9 -m py_compile`) | they compile |

**The finding of task 12: the backends with the models of `add_accis_to_idf`.** With the output IDFs of `AddAccis`
(the EMS code of one comfort standard), both backends give identical CSV files: all the comparisons of both backends
of `tests/core` are with such IDFs. With a model of `add_accis_to_idf` (the code of all the comfort standards) they
do not: the EMS outputs and the setpoints of the thermostats (the schedule values that the four actuators of the model
set, the only inputs of accim to EnergyPlus) are identical in every timestep, also in the warm-up days and the design
days, but the other outputs differ in their last digits from the first timestep of the first design day: in 1 and 2
July of the sample model, up to 5e-10 K in the zone temperatures, 2e-6 W in the rates of the coils and 5e-3 J in the
hourly energies (1.5e-7 of the value at most). It is not of this session: the model that is not edited gives the same
numbers with the code of `f3f9eb5`. It has no practical effect, but the rule of the project is that both backends give
identical results, and section 4.9 of the detailed use said so without this exception (it has it now, beside that of
the thermostats of the PMV). The cause was not found. It is born before the first reported timestep, so probably while
EnergyPlus sizes; three things were checked and discarded (the errors of the first run of the programs, which the EDD
file of EnergyPlus shows to be the same with both kinds of models; the state that such a run leaves: running the
programs once more at the first call of the controller changes no digit of the results; and the first calls: the
first 400 values that the controller gives to the actuators in the design days of the sizing are those of the trace
of the EMS). It is a P2 entry of `TODO.md`, with what was measured. The test of A24 compares the EMS outputs and the
schedule values exactly, and the other outputs within 1e-6.

The tests of each task (the results after it; the details are in `DEVLOG.md`):

| Task | New or changed tests | Result after it |
| :--- | :--- | :--- |
| 1, comfort standards 9 and 10 | `test_imac_r.py` (new, 32 tests), `test_comfort_standard_code.py`, `test_comfort_standard_registry.py`, `test_table_columns.py`; the golden master | `tests/core` without the golden master: 1536 passed, 2 skipped, 3 failed that pass when run again (section 2); the golden master, 35 passed after its update; `tests/parametric_and_optimisation`, 520 passed |
| 2, A19 with S1 | `test_setpoint_limits.py` (32 tests), `test_comfort_hooks.py`, `test_sun2026_set.py` (a measurement of the winter week made again) | 390 passed in the related files; the golden master, 35 passed without changes |
| 3, A24 | `test_jpn_aqilah2025.py`, `test_zone_arguments.py`, `test_modifyaccis_setast.py`; the golden master | 71 passed; `tests/core`: 1585 passed, 2 skipped, 3 failed from the changes in progress of tasks 4 and 5 (section 2); `tests/parametric_and_optimisation`, 520 passed |
| 4, E-F1 | `test_pierce_set.py` (written again: three simulations of a year), `test_indoor_adaptation.py` | 6 passed and 26 passed |
| 5, A4 | `test_missing_hook.py` (new, 5 tests), `test_sun2026_set.py`, `test_table_optional_outputs.py` | 45 passed |
| 6, A25 | `test_jpn_aqilah2025.py` | 802 passed with the related files, the golden master and `tests/parametric_and_optimisation` |
| 7, A8 | `test_drift_limiter.py` (17 tests) | 229 passed with the related files |
| 8, the reference SET | none (texts) | `test_indoor_adaptation.py`, 26 passed |
| 9, S4 (ii) | `test_people_set_inputs.py` (new, 7 tests) | 268 passed with the related files |
| 10, A15 | `test_long_term_discomfort_counters.py`, `test_long_term_discomfort.py` | 779 passed with the related files, the golden master and `tests/parametric_and_optimisation` |
| 11, F3 | none (a tool) | the script run for two weeks |
| 12 | `test_jpn_aqilah2025.py` (the test of A24, with both backends) | 31 passed |

The EnergyPlus test of A24 fails with the commit before it (the error of EnergyPlus), and the measurement of the
winter week of comfort standard 24 that A19 changes gives the old values with the commit before it, both in a
temporary worktree; the tests of A4 and A25 assert the error and the warnings that did not exist before.

Backend comparisons and EnergyPlus runs (EnergyPlus 25.1, the sample model in Seville):

| Task | Simulations | Result |
| :--- | :--- | :--- |
| 1 | comfort standard 9 with and without the weather file, and 10, with both backends; check 4 of `verify_accim_simulation` | identical results (`check_exact`); check 4 without mismatches |
| 2 | a winter and a summer week with limits of 20 and 26 °C, both backends | identical; the thermostats exactly at 20.1 and 25.9 °C where the limits bind; checks 4 and 5 without mismatches |
| 3 | two days of July with a zone switched by hand to comfort standard 23 (EMS backend; both backends in task 12) | runs, with setpoints of 20 and 28 °C; the EMS outputs and the setpoints identical in both backends, the other outputs within rounding (the finding above) |
| 4 | three simulations of a year (110.7, 115 and 126 W/person) | standing, with the conversion of the Pierce model, the SET of pythermalcomfort is 0.058, 0.331 and 0.966 K below that of EnergyPlus on average; 0.05 to 0.06 K at the three levels without the term of the activity of the convective coefficient |
| 5 | comfort standard 24 with the EMS backend of `run_ep`, and with the backend of the API without the hook | a `ValueError` before anything runs; a warning, and both backends still equal without the hook |
| 7 | April without the limiter, with the window and with the rate (a test); January and July (a script) | with the window, the heating coils use 42 814, 32 488 and 4464 kWh in January, April and July instead of 19.7, 125.9 and 10.4 kWh |
| 9 | a week of July with comfort standard 24 (the backend of the API) | with the values that the sensors of the hook read, the SET of the results is that of the hook within 0.001 K; the hours within the causal band with `'people'` are those of the hook (27.8 and 34.3 of 60), 24.7 and 31.2 with the Pierce SET |
| 10 | 15–28 January and 12–25 March with the seasonal range, both backends | identical; check 6 without mismatches; in January, 69.7 and 70.3 of the 120 occupied hours of each zone above the upper limit, against 4.8 and 19.3 with the constant range |
| 11 | the cases of the script for 8–14 January and 15–21 July (the backend of the API) | no failed simulation; the open question of section 4 |
| 12 | 1 and 2 July, both backends: models of `add_accis_to_idf` (six cases) and output IDFs of `AddAccis` (two) | the finding above; identical files with the output IDFs of `AddAccis` |

## 6. Left to the author, and the exact information that is missing

- **The open question of the validation study** (section 4): the air speed of the heating setpoint of case (iv), with
  Ruiji Sun, and what the limiter of the drift limits when the setpoints change within the day (a change of F2, or of
  case (v)).
- **The message to Ruiji Sun** (an entry of `TODO.md`): whether the SET of the paper is the column `set` of the ASHRAE
  Global Thermal Comfort Database II, version 2.1 (`set_tmp` of pythermalcomfort, standing), and the choices of the
  study (the static references, the climates, the clothing insulation, the air speeds, and the point above).
- **The simulations of the study**: the weather file of the hot and humid climate (Singapore, unless Ruiji Sun
  prefers Shanghai or Ningbo), a model of the study (the sample model is a test model), and, for 2050 and 2080, the
  jar of the Future Weather Generator (`ACCIM_FWG_JAR` and its Java).
- **The issue for EnergyPlus** (the SET of its Pierce model has no term of the activity in the convective coefficient
  of the real environment, unlike its Engineering Reference): the draft is
  [[BORRADOR_issue_EnergyPlus_SET_Pierce_2026-11-12.md]]; the author posts it. It asks which behaviour is intended,
  since the program of the SET of ASHRAE 55-2017 that the code cites is not in the library: to be checked first, if
  the author has the standard.
- **The National Building Code of India 2016** (or the Energy Conservation Building Code 2017): the line
  0.078·T + 23.25 of the static setpoints of IND IMAC.
- **The review of Claude Science** of sessions 2 and 3 (the v05), which can also cover this session and contrast the
  decisions of 2026-11-12.
- **The P1 entry of `TODO.md`** (check 1 of `verify_accim_simulation`, section 2): what check 1 should compare.

## 7. Environment

- Python 3.14.3 (`py`), with numba 0.68.1, pythermalcomfort 4.8.1, pytest 9.0.3, besos and eppy 0.5.69; Python 3.9 for
  the compatibility checks. EnergyPlus 25.1 with its Python API. Windows Smart App Control is off since 2026-11-12
  (the author), so numba loads; no setting of the machine was changed in the session, and nothing was installed.
- The documentation build needs pandoc: the folder of that of `pypandoc_binary` was added to the `PATH` of the build
  process.
- The temporary git worktrees of the checks (`%TEMP%\accim_wt_verify`, `accim_wt_final` and `accim_wt_start`, the
  last one with `f3f9eb5`) were removed at the end. The scripts and the results of the measurements (E-F1, A8, S4,
  A15, the try-runs of F3 and the comparisons of the backends) are in the scratch folder of the Claude Code session,
  out of the repository; what they measured is in `DEVLOG.md`, [[decisions.md]] and [[questions.md]].
- The connector of GitHub of Claude Code did not connect; git was used from the shell.
