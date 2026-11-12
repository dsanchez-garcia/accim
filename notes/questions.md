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
