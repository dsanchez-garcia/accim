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

### 2026-11-13 — Checks 1 and 2 of `verify_accim_simulation`, now that they find the zones and the windows with ':' in their names
- Context: until 2026-11-13, checks 1 and 2 skipped the zones and the windows whose names have ':' (those of the
  models of DesignBuilder, as the sample model), and `AccimSimulationVerifier` raised a `ValueError` with them. With
  the search of their outputs fixed (the P1 entry of `TODO.md` of 2026-11-09), they report what they skipped, measured
  with the sample model in Seville (EnergyPlus 25.1):
  1. Check 1 (`Check1_Cooling` and `Check1_Heating`: the system of a zone on, and the zone beyond its setpoint by more
     than `tolerance`, 0.1 °C) reports the hours in which the VRF system of the sample model does not hold the cooling
     setpoint. In the week of July of the try-runs of F3 (hourly outputs, 168 hours of each zone): 77 and 71 hours
     with the fixed setpoints of 20 and 26 °C, 6 and 17 with EN 16798-1, and 15 and 26 with ASHRAE 55; in the week of
     January, 18 and 21, 43 and 43, and 55 and 50. In those hours the cooling coils give 86 to 99 % of their largest
     output of the week (about 50 % in the other hours in which they are on) and the zones are 0.2 to 1.2 K above the
     setpoint on average (1.9 K at most): the system is at its limit, and the EMS is not wrong. In a mild week (29
     April to 5 May, mixed mode, timestep outputs) check 1 has no mismatch.
  2. Check 2 of `verify_accim_simulation` compares the conditions of the program `SetWindowOperation_<window>` with
     the outputs of the same timestep, and with a ventilation setpoint and a minimum outdoor temperature that are
     constants of the arguments of the model, 20 and 6 °C by default (the EMS of the models of accim calculates them
     in each timestep, and they have no such arguments). In that week of 29 April (`hvac_mode=[2]`,
     `ventilation_control=[0]`; 1008 timesteps, each window open in 107 or 108) it reports 213 mismatches of the six
     windows: 12 or 13 timesteps of each window open with the HVAC system on, 21 or 23 open with the zone at or below
     20 °C, and 1 open with the zone at or above the cooling setpoint. In the same simulation,
     `AccimSimulationVerifier` reports none in the 42 or 45 timesteps of each window that it checks: it reads the
     ventilation setpoint and the minimum outdoor temperature of each timestep from the outputs of the EMS, and
     leaves out the timesteps of the delay of the EMS (the last one before a window closes, and the first one of the
     HVAC system). An example of that delay: on 29 April a window opens at 6:40, since its zone was at 22.29 °C at
     6:30, above its ventilation setpoint (22.28 °C); in that timestep the zone falls to 18.62 °C and is heated, and
     the window closes at 6:50.
- Why it matters: `verify_accim_simulation` is the documented way to verify a simulation (section 4.6.1 of the
  detailed use). For the models of DesignBuilder, most of those of the users of accim, it gave warnings and now it
  gives mismatches: true ones of check 1 (a system that does not hold the setpoints, which is not an error of accim)
  and, in mixed mode, mismatches of check 2 that are not errors of the EMS. The function and the class have
  different checks 1 and 2 (the entry of `AccimSimulationVerifier` of `TODO.md`).
- Options considered. For check 1: (a) leave it as it is (implemented): its mismatches are the hours in which the
  system does not hold the setpoint, as its documentation says now, and the tests of accim that check other things do
  not look at them; (b) report them apart from the mismatches (a summary, and the rows on request), so that an empty
  result means that the EMS works; (c) an argument to skip it. For check 2: (a) leave it (implemented), with what it
  reports in its documentation, which points to the class; (b) give `verify_accim_simulation` the check 2 of the
  class for `HVACmode` 2 (the ventilation setpoint and the minimum outdoor temperature of each timestep, and the
  timesteps of the delay left out), and keep its own for 0 and 1; (c) write check 2 as checks 3 to 6 are written: the
  opening of each window in each timestep against the conditions of its program with the values that the EMS reads
  (the operative temperature of the previous timestep), exactly, with `calculation_tolerance`, for the three modes,
  and use it in the function and in the class.
- Recommendation of Claude Code: (b) for check 1; (c) for check 2, with (b) meanwhile if (c) has to wait; and one
  implementation of both checks for the function and the class.
- Owner: the author.
- Status: open. Implemented meanwhile: (a) for both.

### 2026-11-12 — The validation study of F3: the air speed of case (iv), and the limiter of the drift with setpoints that change within the day
- Context: the try-runs of `tools/indoor_adaptation_study.py` (8–14 January and 15–21 July of the sample model in
  Seville, 120 occupied hours each; the sample model is a test model, not a model of the study: `DEVLOG.md`) showed two
  things of the design of cases (iv) and (v) that the decisions of 2026-11-12 do not cover.
  1. The air speed of the fans is in both setpoints. The hook of comfort standard 24 converts both limits of the
     causal band of the SET into operative temperatures with the air speed of the People object of each timestep
     (decision 5 of the author of 2026-11-10: no air speed of its own), so the fans of case (iv) raise the heating
     setpoint as well as the cooling one: on 16 July, in Block1:Zone1 with 1.2 m/s, the heating setpoint goes from
     about 19.1 °C before the hours of the fans to 25.0–26.7 °C in them, and the cooling one from 28.0 to
     30.2–32.5 °C. The heating coils work in the first hours of the fans: 10.6 kWh in the week of July with 1.2 m/s
     and 1.4 kWh with 0.9 m/s (none with 0.6 nor with 0.1 m/s), beside 2044 and 2059 kWh of the cooling coils. The
     proposal of block F had an `air_speed_cooling`: an air speed of the cooling setpoint only.
  2. `drift_mode='rate'` limits every timestep. It keeps the setpoints of every timestep of the day, the unoccupied
     ones too, within `max_drift_rate` of the mean of those applied in the occupied timesteps of the day before
     (decision 13 of the review of session 3). The setpoints of a hook change within the day, and those of case (iv)
     by several kelvin between the hours of the fans (the occupied ones) and the rest, so the limiter keeps those of
     the hours of the fans all day: with 1.2 m/s and 0.25 K/day, about 25.4–25.9 and 31.0–31.6 °C on 16 July. In the
     week of July, against the same case without the limiter: with 1.2 m/s, the heating coils 343.6 kWh instead of 10.6
     (268.3 of them in the unoccupied hours) and the cooling coils 1549.6 kWh instead of 2043.7 (816 instead of 1351
     in the unoccupied hours, 733 instead of 692 in the occupied ones); with 0.6 m/s, 27.8 kWh instead of none and
     1700.7 instead of 2082.0 (891 instead of 1303, and 809 instead of 779). With 0.1 m/s (no fans) the limiter still
     changed a setpoint in 81.3, 70.2 and 25.2 of the 120 occupied hours with 0.25, 0.5 and 1.0 K/day (84.7, 73.3 and
     17.8 in the week of January), since the setpoints of the hook follow the mean radiant temperature, the humidity
     and the clothing of each timestep, with little energy (the cooling coils, 2375 kWh without it and 2371, 2369 and
     2375 with it in July; the heating coils, 51.2 kWh without it and 74.9, 50.8 and 55.0 with it in January). With
     the adaptive setpoints of case (ii), constant within the day, it acted with EN 16798-1 and 0.25 K/day only (72
     occupied hours of the week of July, 1786.5 instead of 1781.8 kWh of the cooling coils).
- Why it matters: the new result of the article is the sensitivity of the savings to the rate of the drift (case
  (v)). As the cases are, that of the causal SET model would measure mostly the setpoints of the unoccupied hours and
  the changes within the day, not the drift between days; and the heating in the hours of the fans is not what a
  building with fans under personal control does (their occupants would slow them down).
- Options considered: for 1: (a) leave it, the air speed of the People object in both setpoints, as decided; (b) an
  air speed of the cooling setpoint only in the hooks of the SET (the `air_speed_cooling` of the proposal; the heating
  setpoint and the SET of the hours below the cooling setpoint, with that of still air); (c) fans that run above an
  operative temperature only (25 °C, the condition of EN 16798-1, Table B.4: an EMS program for the air velocity
  schedule), which alone does not remove the heating with 0.9 and 1.2 m/s, whose heating setpoints of the occupied
  hours were 25.5 and 26.1 °C on average in that week (24.5 °C with 0.6 m/s).
  For 2: (a) leave the limiter, and case (v) of the causal SET model as it is, read with this in mind; (b) limit the
  occupied timesteps only, and give the unoccupied ones their targets; (c) limit the daily mean of the setpoints and
  keep their profile within the day; (d) leave the causal SET model out of case (v), or only its cases with fans.
- Owner: the author (1, with Ruiji Sun: the entry of the message in `TODO.md`; 2, a change of the limiter of F2).
- Status: open. Nothing changes in the meantime: the script has the cases as decided, and its docstring, the entry of
  the study in `TODO.md` and sections 4.2.7 and 4.7.6 of the detailed use say what happens.

The six questions that were open after session 3 of the review of 1.2.0 were decided on 2026-11-12 (see "Answered"
below).

## Answered

The questions on the scope and the technology of the GUI, on the names of the arguments of accim 1.0.0, on the EMS
code of the comfort standards of each output IDF of `AddAccis` (option 1, as implemented), on the design days of
`vrf_mm` (option (a): the same rule as `ex_mm`) and on the `schedule` of `set_clothing_method` of A5 (option (b): the
clothing insulation schedule, and another argument for `CalculationMethodSchedule`) were answered: see
[[decisions.md]]. The 36 provisional decisions of the proposals of 1.2.0 (2026-11-09 and 2026-11-10)
were answered on 2026-11-10 (`notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §5): see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]]. The 23 provisional decisions of the session of the review v04 (2026-11-10 and 2026-11-11) were answered on
2026-11-11 (the verdicts of the handoff of Claude Science, §3), but for two that stayed open until 2026-11-12, pending the author with Ruiji Sun (the SET of the indicators of F3 and the static reference of case (i) of its validation study): see
[[decisions.md#2026-11-11 — The verdicts on the 23 provisional decisions of the session of the review v04|the verdicts of 2026-11-11]]. The six questions left open after session 3 of the review of 1.2.0 (the eight findings of the self-audit of session 2 that needed a decision of the author, the details of tasks S4 and S1, comfort standards 9 and 10, and those two of F3) were decided on 2026-11-12 by Claude Code for the author, who delegated them: see [[decisions.md#2026-11-12 — The decisions on the six questions left open after session 3 of the review of 1.2.0|the decisions of 2026-11-12]].
