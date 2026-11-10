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
