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

### 2026-11-17 — The range of the bisection of comfort standard 24 with the mean radiant temperature of the zones
- Context: the hooks of the SET find their setpoints by bisection within `temperature_range`, 10 to 40 °C by default
  (the limits of the inputs of the SET of pythermalcomfort; "Bisección en [10, 40] °C" in the design of F1 that the
  author decided on 2026-11-10). With `tr_mode='zone'`, the default of comfort standard 24, the unknown of the
  bisection is the air temperature, with the mean radiant temperature of the zone, and the hook gives the thermostat
  (air + MRT)/2. The outputs of task A6 (2026-11-17, `SETsaturated_<zone>`) showed that, in the weeks of the
  EnergyPlus tests of the sample model in Seville (8–14 January and 15–21 July, EnergyPlus 25.1; the inputs of the
  People objects: 1.06 met, 1.0 clo in winter and 0.5 clo in summer, 0.137 m/s), the air temperature whose SET is the
  heating setpoint of the SET (19.09 °C) is below 10 °C in all the timesteps of January and in 62–64 % of those of
  July (79–86 % of the occupied ones): the mean radiant temperature of the zones is high (25 °C in January and 29 °C
  in July, 1.2 and 3.6 K above the air temperature). The bisection then gives 10 °C, and the heating setpoint of the
  thermostat is (10 + MRT)/2 instead of (air + MRT)/2 with the air temperature of the model, which goes down to
  −1.7 °C in January. Measured against a range of −20 to 40 °C, in which no setpoint is at a limit, the heating
  setpoints of the hook are higher than those of the model by 2.4 K on average in January (3.5 K in the occupied
  hours, 5.9 K at most) and by 1.0 K in July (1.6 and 1.8 K in the occupied hours of the two zones, 3.5 K at most).
  The cooling setpoint never reaches 40 °C.
- Why it matters: the heating setpoints of comfort standard 24 with `tr_mode='zone'` are not those of the causal SET
  model wherever the mean radiant temperature of a zone is high. In the occupied hours of that week of January they
  are 18.3 °C on average instead of 14.8 °C, above the minimum heating setpoint of 18 °C of the validation study of F3
  (with which they would be 18 °C). Since task A6, the hook warns of it at the end of every such simulation.
- Options considered: (a) keep 10 to 40 °C for the air temperature, documented and reported (as now); (b) a wider
  default range of the air temperature with `tr_mode='zone'` (for instance −20 to 40 °C: the SET of pythermalcomfort is
  calculated without the limits of its inputs, `limit_inputs=False`); (c) `temperature_range` as the range of the
  setpoints given to the thermostats, the operative temperatures: with `tr_mode='zone'`, the bisection of the air
  temperature within 2·10 − MRT to 2·40 − MRT, so that (air + MRT)/2 is within 10 to 40 °C.
- Recommendation of Claude Code: (c). The range of the bisection is a bracket of the numerical method, and the design
  asks for the air temperature whose SET is the setpoint with the mean radiant temperature of the zone; (c) keeps the
  meaning of `temperature_range` as the range of the setpoints, the same with both values of `tr_mode`. The results
  of comfort standard 24 with `tr_mode='zone'` change (lower heating setpoints where the zones are warm), so the
  simulations of the validation study of F3 are to be run after the decision.
- Owner: the author (the range was decided with F1 on 2026-11-10).
- Status: open. Implemented meanwhile: (a), with the outputs and the warning of task A6.

The question of 2026-11-12 on the validation study of F3 and that of 2026-11-13 on checks 1 and 2 of the
verification were decided on 2026-11-13, and the six questions that were open after session 3 of the review of
1.2.0, on 2026-11-12 (see "Answered" below).

## Answered

The questions on the scope and the technology of the GUI, on the names of the arguments of accim 1.0.0, on the EMS
code of the comfort standards of each output IDF of `AddAccis` (option 1, as implemented), on the design days of
`vrf_mm` (option (a): the same rule as `ex_mm`) and on the `schedule` of `set_clothing_method` of A5 (option (b): the
clothing insulation schedule, and another argument for `CalculationMethodSchedule`) were answered: see
[[decisions.md]]. The 36 provisional decisions of the proposals of 1.2.0 (2026-11-09 and 2026-11-10)
were answered on 2026-11-10 (`notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §5): see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]]. The 23 provisional decisions of the session of the review v04 (2026-11-10 and 2026-11-11) were answered on
2026-11-11 (the verdicts of the handoff of Claude Science, §3), but for two that stayed open until 2026-11-12, pending the author with Ruiji Sun (the SET of the indicators of F3 and the static reference of case (i) of its validation study): see
[[decisions.md#2026-11-11 — The verdicts on the 23 provisional decisions of the session of the review v04|the verdicts of 2026-11-11]]. The six questions left open after session 3 of the review of 1.2.0 (the eight findings of the self-audit of session 2 that needed a decision of the author, the details of tasks S4 and S1, comfort standards 9 and 10, and those two of F3) were decided on 2026-11-12 by Claude Code for the author, who delegated them: see [[decisions.md#2026-11-12 — The decisions on the six questions left open after session 3 of the review of 1.2.0|the decisions of 2026-11-12]].

The question of 2026-11-13 on what checks 1 and 2 of `verify_accim_simulation` report, now that they find the zones
and the windows with ':' in their names, was answered by the author that day ("Haz los checks 1 y 2", the
recommendation: check 1 apart from the mismatches, an exact check 2, and one implementation for the function and the
class): see
[[decisions.md#2026-11-13 — Checks 1 and 2 of the verification: check 1 apart, an exact check 2, and one implementation|the decision of 2026-11-13]].

The question of 2026-11-12 on the validation study of F3 (the air speed of the fans of case (iv) in the heating
setpoint of the causal SET model, and the limiter of the drift with setpoints that change within the day) was
decided on 2026-11-13 by Claude Code for the author, who asked for it: the fans are those that the occupants
control (the heating setpoint of still air, `air_speed_heating`), their air speed is that of all the hours of the
cooling season, and the limiter stays as it is; provisional, to be agreed with the authors of the models: see
[[decisions.md#2026-11-13 — The validation study of F3: the fans that the occupants control, and the limiter of the drift with the setpoints of a hook|the decisions of 2026-11-13]].
