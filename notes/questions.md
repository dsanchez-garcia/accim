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

None. The question of 2026-11-12 on the validation study of F3 and that of 2026-11-13 on checks 1 and 2 of the
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
