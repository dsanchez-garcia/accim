---
title: Session report, accim v1.2.0, session 3 (2026-11-11)
type: report
tags: [vault, report, v1.2.0]
created: 2026-11-11
---

# Session report: session 3 of the review of accim 1.2.0 (2026-11-11)

Branch `v1.2.0` of `D:\DSG\accim`, from `b6b65dd` (the instructions [[COPILOT_SIGUIENTE_SESION.md]] and the updated
handoff [[TRASPASO_ClaudeScience_2026-11-11_v01.md]]). The task of the author: follow [[COPILOT_SIGUIENTE_SESION.md]]
autonomously: Step 0 (the verdicts of the handoff §3 on the 23 provisional decisions of session 2, and the pending
items), the self-audit of session 2, the tasks S1–S5, the fixes of the self-audit, the final checks and this report,
one commit and one push each. Each task has its entry in [[../DEVLOG.md]] (context, changes, files, verification), in
[[../CHANGELOG.md]] (Unreleased) where users see it, and a section of [[../CAMBIOS_CODIGO_v1.2.0.md]] (in Spanish,
§38–§43); this report summarises them and does not repeat their details. The previous report is
[[INFORME_SESION_v1.2.0_2026-11-10_2.md]].

**How the session ended.** The session of GitHub Copilot stopped on 2026-11-11 when its monthly quota ran out: every
task was committed and pushed (`7cb4058`), this report was drafted, and the last of the final checks (the suite of
`tests/core`) was still running; that run finished on its own. The report was completed on 2026-11-12 with Claude
Code, from the logs of those checks: they belong to `7cb4058` (launched 27 s after it; no tracked file has changed
since), and the golden master, the comparison of the warnings of the documentation build and the compilation with
Python 3.9 were repeated. What Claude Code added is in section 5 (the results of the whole suites, and a run of the
tests that need pythermalcomfort with a stand-in of numba); the sections 1–4 and 6–8 are the draft of Copilot,
checked against `git log`, `TODO.md`, [[questions.md]] and the JSON file of the self-audit, with two corrections (the
count of the tests that fail by numba, section 2, and the entry of comfort standards 9 and 10, which was completed,
not added, section 3).

## 1. Tasks and commits

Every commit was pushed to `origin/v1.2.0` right after it was made (no force-push, no history rewritten, no `wip(...)`
commit: no task ended blocked).

| Order | Task | Decisions and findings | Commit | Status | CAMBIOS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | Step 0: 21 of the 23 provisional decisions to [[decisions.md]] with the verdicts of the handoff §3 (#9 and #12 open, with the review of the handoff); comfort standards 9 and 10 recorded (question and `TODO.md`); the proposal of the handoff §4 in the blocked entry of the validation study of F3 | handoff §3, §4 | `fe42957` | done | — |
| 1 | The self-audit of session 2 (`0f8bb628..47d0b486`, three reviewers in parallel, read-only, in a worktree): [[attachments/autoauditoria_sesion2_v1.2.0.json]], findings A1–A26 | §5 of the instructions | `c8473e8` | done | — |
| 2 | S1: the warning of the minimum and maximum of the setpoints compares them with the setpoints of the comfort model (`compute_setpoints`, with `epw`) | decision 19 | `63b76db` | done | §38 |
| 3 | S2: the static setpoints of the YAML file of Qatar, 20 and 26 °C (EN 16798-1, Table B.2, offices, category II) | decision 20 | `7486aef` | done | §39 |
| 4 | S3: the reference of `drift_mode='rate'`, the mean of the setpoints applied in the occupied timesteps of the previous day | decisions 13 and 14; A10 | `218d949` | done | §40 |
| 5 | S4: the indicators of the causal band with the SET of pythermalcomfort, as an option of `table_indicators` (`pythermalcomfort_set`) | decision 9 (provisional) | `fd21246` | done | §41 |
| 6 | S5: the notes of the accepted decisions: an example of a clothing function of the temperature at 6:00; the absolute path of the CSV files of the `Schedule:File` objects (and a P2 entry for a relative mode); a test of comfort modes 0 and 3 of comfort standard 24; the one-day delay of the running means of EnergyPlus in the first timestep of each day | decisions 1, 7, 16, 22 | `f472c8a` | done | §42 |
| 7 | A7: the saturated hours of the hook of the ATHB are those of the run period (the API of EnergyPlus) | A7 (bug) | `8faf7bb` | done | §43 |
| 8 | A3: the hook of the SET with the dynamic clothing model adds the Pierce model (EnergyPlus stopped before) | A3 (bug) | `d29ed58` | done | §43 |
| 9 | A12: the cooling season of the indicators of F3 that goes on in the next year | A12 (bug) | `e52763d` | done | §43 |
| 10 | A13: the source of the 22 °C of the overcooling, Parkinson, de Dear & Brager (2020), §4.3.2 | A13 (scientific) | `fb6bd3c` | done | §43 |
| 11 | A9: the window of the limiter of the drift cannot be narrower than twice the tolerance (`ValueError`, and the plans drop those rows) | A9 (bug) | `384961b` | done | §43 |
| 12 | The documentation findings | A14, A16, A17, A18, A20, A22, A24 (documentation), A26 | `13e1c0e` | done | §43 |
| 13 | AddAccis warns of the arguments of the limiter without `drift_mode`; the old names of the minimum and maximum in the plans | A11, A23 | `2add889`, `69646e3` | done | §43 |
| 14 | No hours in the causal band in a timestep without the SET; a test that `prepare()` runs before the API is loaded | A5, A6 | `5418b71` | done | §43 |
| 15 | The name of the CSV file of T0 of `te_ref_nl` with a hash of its values | A21 | `bf77332` | done | §43 |
| 16 | The findings left to the author ([[questions.md]]) and the pending tasks (`TODO.md`) | A1, A2, A4, A8, A15, A19, A24, A25; A22, A26 | `7cb4058` | done | — |
| 17 | This report | §8 | (the last commit) | done | — |

`69646e3` holds the notes of `2add889` (`CAMBIOS_CODIGO_v1.2.0.md`, a sentence of `CHANGELOG.md` and the entry of
`DEVLOG.md`), which its `git add` did not take because it ran at the same time as their edits, and two lines of its
tests shortened to 120 characters; nothing was rewritten.

## 2. Deviations from the instructions, and why

- **The environment blocks numba.** Windows Smart App Control (enforcement mode) blocks the DLLs of numba 0.68.1, so
  `pythermalcomfort.models` cannot be imported with the only Python that has it (3.14.3): `set_tmp` and `pmv_athb` do
  not run on this server. They did in session 2: the first blocked load in the Code Integrity log of Windows is of
  2026-11-11 at 17:23, the first import of this session. It was not disabled (a security setting of the machine). The
  tests that need them fail with an `ImportError` instead of skipping (rule 1 asks to skip): 19 in the whole suite, 14
  of `tests/core/test_comfort_hooks.py`, 4 of `tests/core/test_sun2026_set.py` and 1 of
  `tests/core/test_drift_limiter.py`, all of them tests of session 2 that passed then (section 5); a `TODO.md` entry
  asks them to skip with `pytest.importorskip('pythermalcomfort.models')`. The new tests of S4, A3, A5 and A7 use a SET
  of the test, or an EnergyPlus run without the hooks, so they run here; those that need pythermalcomfort itself are
  skipped (`importorskip`). The yearly comparisons with pythermalcomfort (E-F1, F1) could not be repeated (A1, A2);
  section 5 has a run of all those tests with a stand-in of numba, made when the report was completed.
- **S3.** The unit test of the day without occupants expects now the reference of the last occupied day (decision 14),
  not that of the last timestep of the previous day: the expectation changes with the decision, the test is not looser.
- **S4.** The instruction did not fix the form of the inputs of the occupants: `set_of_results` takes the constant
  inputs of a hook, while E-F1 used the values of the schedules of the People objects in each timestep. The option takes
  constant inputs (a dict or a hook) and reads the conditions of the zones from the CSV file of each simulation; the
  choices, and the alternative of the inputs of each row, are provisional in [[questions.md]], and the limitation (a
  seasonal or dynamic clothing insulation gives the two SET different inputs) is documented.
- **A13.** A correction of a citation: no test can fail before it (§7 asks for one).
- **A24 (a bug).** Its fix in the code contradicts the decision of G4 (only the zones of comfort standard 23 have
  `StaticAHST` and `StaticACST`, and the output IDFs of the other zones do not change; the golden master of the models
  of `add_accis_to_idf` would change), so it is documented (section 4.2.1) and left to the author with its options.
- **A6 and A10** were findings of missing tests: A6 got its test (the code already did it), and A10 was covered by the
  new EnergyPlus test of S3.
- **The baseline of the documentation build.** The instructions give 35 unique warning lines; the warnings file of the
  last build of session 2 has 55 lines, 47 of them distinct, and 35 distinct once their line numbers (which move when
  the pages change) are left out: the build of this session is compared with it in that way (section 5).

## 3. Entries of TODO.md

Added in this session:

- [P2][todo] A relative path for the CSV files of the `Schedule:File` objects of accim (H2 and H6; decision 7, S5).
- [P2][todo] The `Schedule:File` objects of accim with EnergyPlus 9.4 and 9.6 and daylight saving time (A22, A26: a
  warning, or the CSV files shifted by one hour).
- [P2][blocked] E-F1 measured again with the body surface area of the Pierce model (1.8258 m²) and at 1.1 and 1.2 met
  (A1, A2; blocked here by numba).
- [P2][todo] The tests that need `pythermalcomfort.models` skip instead of failing when numba cannot be loaded.

Changed (Step 0):

- [P1][todo] Comfort standards 9 and 10 (IND IMAC R 7DRM and 30DRM): their running means are swapped (it said "look
  swapped"), and the next entry, the sign of the heating setpoint of 9 in comfort mode 1: completed with the analysis
  verified by the review of Claude Science (Rawal et al. 2022, doi:10.1016/j.buildenv.2022.109187) and the status
  "the author decided on 2026-11-11 not to change them in session 3" (rule 7).
- The blocked entry of the simulations of the validation study of F3 has the proposal of the handoff §4 (the climates,
  case (i), the clothing of case (iii) and the air speeds of case (iv) of EN 16798-1, Table B.4), still blocked until
  the author decides with Ruiji Sun.

## 4. Provisional decisions in notes/questions.md

- **S1: the details of the comparison of the minimum and maximum with the setpoints of the comfort model** (the
  setpoints of the thermostats, by timestep, the first run period, the zones left out with a debug message): option
  (i) implemented; it only adds warnings.
- **S4: how the indicators of the causal band are given with the SET of pythermalcomfort** (an argument of
  `table_indicators` only, constant inputs of the occupants, the conditions of the zones from the CSV files, the rows
  matched by their hour): option (i) implemented, off by default.
- **The findings of the self-audit of session 2 that need a decision of the author**: A1, A2 (the SET of the Pierce
  model: its body surface area and its convective coefficient), A4, A8, A15, A19, A24 and A25, with their options;
  nothing changed but the documentation of A24.
- Kept open from session 2, with the review of the handoff: **F3: the SET of the indicators of the causal band**
  (decision 9, pending Ruiji Sun; done provisionally in S4) and **F3: the static reference of case (i)** (decision 12).
- Recorded in Step 0, not changed (rule 7): **comfort standards 9 and 10**, their running means and the heating
  setpoint of 9 in comfort mode 1.

## 5. Tests and backend comparisons

The final checks of §8, on `7cb4058` (the last commit of the tasks), launched right after it on 2026-11-11:

| Check | Result |
| :--- | :--- |
| `py -m pytest tests/core -q -p no:cacheprovider` | **1511 passed, 19 failed, 14 skipped** of 1544 tests (22 min 43 s) |
| `py -m pytest tests/parametric_and_optimisation -q -p no:cacheprovider` | **520 passed** (2 min 10 s) |
| The golden master (`tests/core/test_golden_master.py`, within the first suite; run again on its own on 2026-11-12) | 35 passed: byte-identical |
| The documentation build | succeeded, with the warnings of session 2 (below) |
| The 9 modules of accim changed in the session, with Python 3.9 (`py -3.9 -m py_compile`; again on 2026-11-12) | they compile |

The 19 failures have one cause, the numba of section 2: `ImportError: DLL load failed while importing _nrt_python`,
which accim raises again as "The setpoints of the SET [of the ATHB] need pythermalcomfort" (in 5 of them, inside an
EnergyPlus run). They are 14 tests of `tests/core/test_comfort_hooks.py`, 4 of `tests/core/test_sun2026_set.py` and
`test_addaccis_and_modify_accis_add_the_limiter` of `tests/core/test_drift_limiter.py`: tests of session 2, not
changed in this one, that passed then (1520 passed and 2 skipped in `tests/core`, with numba). Of the 14 skipped
tests, 12 are skipped for the same reason (`importorskip('pythermalcomfort.models')`: 8 of `test_sun2026_set.py`, 2 of
`test_comfort_hooks.py`, 1 of `test_pierce_set.py`, and the new test of S4 with pythermalcomfort itself in
`test_indoor_adaptation.py`); the other two are those of session 2 (EnergyPlus 26.1; the jar of the Future Weather
Generator). Leaving those 31 tests out, the other 1513 tests of `tests/core` give 1511 passed and the 2 skipped ones
of session 2. No test of this session fails; but the tests that run the hooks of the ATHB and of the SET with
pythermalcomfort did not run after S3, A3, A5 and A7, which change `accim/sim/comfort_hooks.py` and the limiter.

**Those tests, run with a stand-in of numba (2026-11-12, Claude Code).** To know whether those changes broke the
hooks, the five test files that hold the 31 tests were run with a pure-Python stand-in of numba on the `PYTHONPATH` of
the test processes only: a module `numba` whose `jit`, `njit` and `vectorize` give back the Python functions of
pythermalcomfort 4.8.1 without compiling them (the same source, slower). It is not installed and it is not in the
repository, and Smart App Control was not touched.

| Test file | With the stand-in | In the suite above (numba blocked) |
| :--- | :--- | :--- |
| `tests/core/test_comfort_hooks.py` | 34 passed | 18 passed, 14 failed, 2 skipped |
| `tests/core/test_sun2026_set.py` | 22 passed | 10 passed, 4 failed, 8 skipped |
| `tests/core/test_drift_limiter.py` | 15 passed | 14 passed, 1 failed |
| `tests/core/test_indoor_adaptation.py` | 26 passed | 25 passed, 1 skipped |
| `tests/core/test_pierce_set.py` | 2 passed | 1 passed, 1 skipped |

The 99 tests pass and none is skipped: among them, the EnergyPlus 25.1 runs with the hooks through the API (the ATHB
and its saturated hours, A7; the SET by its table and by bisection; comfort standard 24 for a week of January and one
of July, A5), the hook of the SET before the limiter (S3), the yearly comparison of E-F1 (`test_pierce_set.py`) and
the test of S4 with pythermalcomfort itself. This run checks the code of accim with the formulas of pythermalcomfort;
it does not check numba: neither its compiled code (whose results can differ from those of the stand-in in the last
digits) nor its behaviour in the callbacks of EnergyPlus (the rule of v04 §7.1 on `set_tmp`, and `prepare()`). So
the result of this server is still that of the first table, and those tests are to be run again where numba loads.
The new measurements that A1 and A2 ask for (`TODO.md`) were not made.

| Task | New or changed tests | Result after it |
| :--- | :--- | :--- |
| Step 0, audit | none (documents) | — |
| S1 | `test_setpoint_limits.py` (4 new instead of the literal warning) | 30 passed |
| S2 | `test_comfort_standard_registry.py` (Qatar against Table B.2) | 44 passed |
| S3 | `test_drift_limiter.py` (the mean with the Erl interpreter; a hook whose setpoints change within the day with EnergyPlus; the reference in the test of both backends) | 12 passed, 1 failed (numba) |
| S4 | `test_indoor_adaptation.py` (5 new; the EnergyPlus test of the indicators with the real CSV file) | 25 passed, 1 skipped |
| S5 | `test_pmv_input_parameters.py` (the clothing function of the documentation), `test_sun2026_set.py` (comfort modes 0 and 3) | 74 passed with `test_jpn_aqilah2025.py` |
| A7 | `test_comfort_hooks.py` (a fake API; an EnergyPlus run with the real controller) | the new ones pass; 14 failed as before (numba) |
| A3 | `test_sun2026_set.py` (the Pierce model; the prepared model in EnergyPlus) | both failed before (EnergyPlus fatal) and pass |
| A12, A13, A14 | `test_indoor_adaptation.py` | 25 passed, 1 skipped |
| A9 | `test_drift_limiter.py`, `test_drift_parameters.py` | 94 passed in five related files, 1 failed (numba) |
| A11, A23 | `test_drift_limiter.py`, `test_setpoint_limit_parameters.py` | the new ones failed before and pass |
| A5, A6 | `test_sun2026_set.py`, `test_comfort_hooks.py` | 28 passed, 10 skipped, 18 failed as before (numba) |
| A21 | `test_outdoor_metric.py` | 43 passed |

Every new test of a bug was run without the fix first (the module stashed) and failed, except where the finding was a
missing test (A6) or a citation (A13).

Backend comparisons and EnergyPlus runs (EnergyPlus 25.1, the sample model in Seville):

| Task | Simulations | Result |
| :--- | :--- | :--- |
| S3 | 1–9 April: setpoints that rise 0.25 K an hour, by a Python hook (API backend) and by the same lines in `RunACCIS_<zone>` (EMS backend), with `drift_mode='rate'`; and the existing comparison of both backends with the ACCIS | identical (`check_exact`); the reference is the mean of the occupied timesteps day by day (also the weekend without occupants), and with the ACCIS it equals the setpoint of the last timestep |
| S4 | the four days of the EnergyPlus test of the indicators, with the outputs of the conditions of the zones | the indicators of the SET of the test from the hourly rows of the real CSV file |
| S5 | a one-day run with a `Schedule:File` whose CSV file is missing | EnergyPlus stops before the simulation (severe error "File Name ... not found") |
| A7 | 15–16 July with the real controller of the API and a probe hook | 288 counted timesteps (`kind_of_sim` 3, out of the warm-up); the design days and the warm-up days left out |
| A3 | 15 July, the model of `apply_set_setpoints` with the dynamic clothing model, EMS backend without the hook | runs (before the fix: "FATAL: Errors found in processing Energy Management System input") |
| A20 | a one-day run with `set TestExpA = 5e-05*100000` | EnergyPlus reads the exponents (5, and 24 for `-1E-05*100000+2.5e+1`) |

The documentation build after the last change of the documentation (`py -m sphinx -E -b html docs/source
docs/_build/html -w docs/_build/sphinx_warnings.txt`, with the pandoc of `pypandoc_binary` on the `PATH`): build
succeeded with 47 warnings (55 lines in the file, 35 distinct without their line numbers), the same as the baseline of
session 2 (no new warning, none gone: the two files are byte-identical, since all the warnings are in docstrings of
modules that this session did not change). The How-to notebook of the registry was run and exported again with
`docs/prepare_howto_notebooks.py` (A18: 63 s, 0 problems). The 9 modules changed in the session compile with Python
3.9.

## 6. Blocked items, and the exact information that is missing

- **The SET of the indicators of F3 and of comfort standard 24 (decision 9, A1, A2).** Which implementation of the SET
  Sun, Brager & Schiavon (2026) used (a question for Ruiji Sun); and, to measure the effect of the body surface area of
  the Pierce model (1.8258 m²) and of other activity levels, a computer where numba loads (pythermalcomfort).
- **The static reference of case (i) of the validation study (decision 12)** and the simulations of the study: the
  decisions of the author with Ruiji Sun on the proposal of the handoff §4 (the climates, the reference, the clothing of
  case (iii), the air speeds of case (iv)), and the future weather files of 2050 and 2080 (the jar of the Future Weather
  Generator).
- **Comfort standards 9 and 10**: the decision of the author on the analysis of the review (the running means and the
  sign of comfort mode 1 of 9), postponed by rule 7.
- **CIBSE TM52 and TM59, and the jar of the Future Weather Generator**: as in session 2 (the texts of TM52 and TM59;
  the jar in `ACCIM_FWG_JAR` and its Java).

## 7. Environment

- Python 3.14.3 (`py`), with numba 0.68.1, pythermalcomfort 4.8.1, pytest 9.0.3, besos and eppy 0.5.69; Python 3.9
  for the compatibility checks (the 9 modules changed in the session compile). EnergyPlus 9.4, 9.6, 25.1 (with its
  Python API), 25.2 and 26.2.
- **Windows Smart App Control is on (enforcement)** and blocks the DLLs of numba (`_dynfunc`, `_devicearray`,
  `_nrt_python`): `import pythermalcomfort.models` raises an `ImportError`. Not changed.
- The documentation build needs pandoc: that of `pypandoc_binary` (installed in session 2) is not on the `PATH`, so its
  folder was added to the `PATH` of the build process.
- `inventario_para_api.json` was added to `.git/info/exclude` (it is never committed).
- The self-audit ran in a git worktree of the commit of Step 0 in the temporary folder, removed at the end, with its
  scratch folders.
- The logs of the final checks of Copilot are in `%TEMP%\accim_s3` (with the folders of its test runs, 1.1 GB, not
  removed). The stand-in of numba of section 5 is a file of the scratch folder of the Claude Code session, used
  through `PYTHONPATH`: nothing was installed, and no setting of the machine was changed.

## 8. The self-audit of session 2

The audit of the commits `0f8bb628..47d0b486` (session 2) found 26 findings
([[attachments/autoauditoria_sesion2_v1.2.0.json]]), by three reviewers: hooks and the SET (G1, G3, E-F1, F1: A1–A7),
the limiter of the drift and the indicators (F2, F3, H3, H4: A8–A17), and the preview and the custom models (G2, G4,
G5, H1, H2, H5, H6: A18–A26).

| Severity | Findings | Fixed (commit) | Left open (where) |
| :--- | :--- | :--- | :--- |
| bug (5) | A3, A7, A9, A12, A24 | A3 `d29ed58`, A7 `8faf7bb`, A9 `384961b`, A12 `e52763d`; A24 documented `13e1c0e` | A24, the code ([[questions.md]]: it contradicts the decision of G4) |
| scientific (3) | A1, A2, A13 | A13 `fb6bd3c` | A1, A2 ([[questions.md]]; their measurement in `TODO.md`, blocked by numba) |
| design (6) | A4, A8, A15, A19, A21, A25 | A21 `bf77332` | A4, A8, A15, A19, A25 ([[questions.md]]) |
| test (3) | A6, A10, A16 | A6 `5418b71`, A10 `218d949` (S3), A16 `13e1c0e` | — |
| doc (4) | A14, A17, A18, A26 | `13e1c0e` (A18 with the How-to notebook run and exported again) | A26: the warning or shifted CSV files in `TODO.md` |
| minor (5) | A5, A11, A20, A22, A23 | A5 `5418b71`, A11 and A23 `2add889` (`69646e3`), A20 and A22 `13e1c0e` | A22: as A26, in `TODO.md` |

The main ones: A7, the saturated hours of the hook of the ATHB counted the warm-up days and the design days (the
controller of the API updates `WarmupFlag` only for the programs that read it); A3, `apply_set_setpoints` with the
dynamic clothing model made EnergyPlus stop before the simulation; A9, a window of the limiter narrower than twice the
tolerance crossed the setpoints of the thermostats; A12, a cooling season in two years gave no overcooled hours; A13,
the 22 °C of the overcooling is of Parkinson et al. (2020), not (2021); A18, the α = 0.8 of Qatar is that of its
article; A21, two weather files of the same name replaced each other's T0; A24, a zone switched to comfort standard 23
by hand stops EnergyPlus.

## Appendix: the stand-in of numba of section 5

A file `numba/__init__.py` in a folder out of the repository, put first on the `PYTHONPATH` of the test processes
(`$env:PYTHONPATH = '<folder>'`, then `py -m pytest tests/core/test_comfort_hooks.py tests/core/test_sun2026_set.py
tests/core/test_drift_limiter.py tests/core/test_indoor_adaptation.py tests/core/test_pierce_set.py -q -p
no:cacheprovider`; run here as four processes in parallel, 19 minutes of test time in all, since the hooks run without
compiling). It has only what pythermalcomfort 4.8.1 imports from numba; with it, `set_tmp(tdb=25, tr=25, v=0.1,
rh=50, met=1.2, clo=0.5)` gives the 24.3 °C of the documentation of pythermalcomfort.

```python
import functools

import numpy as np

__version__ = '0.0.0+pure.python.stand.in'


class _Type:
    """A numba type (``float64``): calling it gives a signature, which the stand-in ignores."""

    def __call__(self, *args, **kwargs):
        return self

    def __getitem__(self, item):
        return self


float64 = float32 = int64 = int32 = boolean = _Type()
prange = range


def _not_compiled(function):
    """The function itself, with the attribute ``py_func`` of the dispatchers of numba (the Python function)."""
    function.py_func = function
    return function


def jit(*args, **kwargs):
    """``@jit``, ``@jit(nopython=True, cache=True)``: the function itself, not compiled."""
    if len(args) == 1 and callable(args[0]) and not isinstance(args[0], _Type) and not kwargs:
        return _not_compiled(args[0])
    return _not_compiled


njit = jit


def vectorize(*args, **kwargs):
    """``@vectorize([float64(float64, ...)], cache=True)``: ``numpy.vectorize`` of the function, with float64 output
    and, as a universal function of numba, a scalar for scalar inputs."""

    def wrap(function):
        vectorized = np.vectorize(function, otypes=[np.float64])

        @functools.wraps(function)
        def universal_function(*values, **named):
            result = vectorized(*values, **named)
            return result[()] if isinstance(result, np.ndarray) and result.ndim == 0 else result

        return universal_function

    if len(args) == 1 and callable(args[0]) and not isinstance(args[0], (list, tuple, _Type)) and not kwargs:
        return wrap(args[0])
    return wrap
```
