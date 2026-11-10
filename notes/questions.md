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
