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

## 2026-11-09 — E1: the running means of the first days of the weather file in outdoor_metrics
- Context: `accim.sim.preview.outdoor_metrics` (E1) calculates the running means of the standards (EN 16798-1 B.1 and
  B.2, the mean of the n previous days of ASHRAE 55, the reference temperature of the ATG) from the daily means of the
  previous days, and the first days of the weather file have no previous days in it. v03 and D1-D12 do not say what
  they get.
- Why it matters: the values of the first days of January, and the initial values of the running means of B1 (D3).
- Options considered: (a) a year that repeats: the first days take the last days of the file, as EnergyPlus does for
  ASHRAE 55 at the beginning of a run period, and B.1 is its infinite sum (a closed form); (b) NaN for the days without
  enough previous days (B.1 would never be complete); (c) the sums truncated at the first day of the file.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (it is what accim does; `energyplus_running_means`
  gives the values of EnergyPlus, whatever the answer).

## Answered

The questions on the scope and the technology of the GUI, on the names of the arguments of accim 1.0.0, on the EMS
code of the comfort standards of each output IDF of `AddAccis` (option 1, as implemented), on the design days of
`vrf_mm` (option (a): the same rule as `ex_mm`) and on the `schedule` of `set_clothing_method` of A5 (option (b): the
clothing insulation schedule, and another argument for `CalculationMethodSchedule`) were answered: see
[[decisions.md]].
