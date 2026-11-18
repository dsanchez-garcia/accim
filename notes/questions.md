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

## 2026-11-18 — Do the output IDFs of AddAccis keep all the digits of the curves of the VRF systems?
- Context: eppy writes the numbers wider than 18 characters with 7 significant digits when it writes a model that it
  has read. Since 2026-11-18, `run_ep` (both backends) and `run_simulation` keep the text of the numbers of the IDF in
  their copies (`accim.sim.accis.numbers_as_text`), which was the cause of the difference between the backends of
  2026-11-12 ([[decisions.md]], 2026-11-18). `AddAccis` writes each output IDF from the text of its model read again by
  eppy, so four coefficients of the curves of the indoor units of the VRF systems of accim (`VRFTUCoolCapFT` and
  `VRFTUHeatCapFT`) have 7 significant digits in its output IDFs (`-0.000010819418650677` is `-1.081942e-05`), and all
  their digits in the models of `add_accis_to_idf` and of the setpoints based on the PMV; the copies of the parametric
  module would have 7 too (not measured).
- Why it matters: the same VRF system of accim gives results that differ in their last digits by the function that
  made the model (up to 5e-10 K in the zone temperatures and 5e-3 J in the hourly energies, in two days of July of the
  sample model). Changing `AddAccis` changes its output IDFs (14 of the 21 compressed files of the golden master with
  those curves).
- Options considered: (a) leave it (the output IDFs and the golden master do not change; the difference is documented);
  (b) `AddAccis` reads the text of each model in `numbers_as_text()`, so its output IDFs have the curves with all
  their digits (the golden master written again on purpose), and the parametric module keeps them in its copies;
  (c) only one of the two.
- Owner: the author. Recommendation of Claude Code: (b), so that every model of accim has the curves of its VRF
  systems as accim defines them, and the results do not depend on the function that made the model. The P3 entry of
  [[../TODO.md]] waits for the answer.
- Status: open.

The question of 2026-11-17 on the range of the bisection of comfort standard 24 was answered on 2026-11-18, the
question of 2026-11-12 on the validation study of F3 and that of 2026-11-13 on checks 1 and 2 of the verification were
decided on 2026-11-13, and the six questions that were open after session 3 of the review of 1.2.0, on 2026-11-12 (see
"Answered" below).

## Answered

The question of 2026-11-17 on the range of the bisection of comfort standard 24 with the mean radiant temperature of
the zones (with `tr_mode='zone'`, the hooks of the SET looked for the air temperature within `temperature_range`, 10
to 40 °C, so where the mean radiant temperature of a zone was high, the air temperature of the heating setpoint
stopped at 10 °C and the heating setpoint was above that of the causal SET model) was answered by the author on
2026-11-18: option (c), the recommendation of Claude Code, `temperature_range` as the range of the setpoints given to
the thermostats with both values of `tr_mode` (the bisection of the air temperature from 2·low − MRT to 2·high −
MRT): see
[[decisions.md#2026-11-18 — The range of the setpoints of comfort standard 24 with the mean radiant temperature of the zones|the decision of 2026-11-18]].

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
