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

## 2026-11-09 — E2: what the metabolic correction of the ePMV is checked against (the 5.5–6.1 % of the brief)
- Context: the brief asks E2 to check "the metabolic correction with the tolerance of 5.5–6.1 %". The EMS sets the
  factor of each People object to 1 − 0.067·PMV with the PMV of the previous timestep (exact in EnergyPlus 25.1:
  differences of 1e-16 with the outputs at timestep frequency); the 5.5–6.1 % is the reduction of the activity level
  for a PMV of 1 *before* the correction, once the correction converges (section 4.8.1 of the detailed use), and the
  outputs of a simulation do not have that PMV (EnergyPlus calculates the PMV with the corrected activity level).
- Why it matters: a check of the reduction against the reported PMV of the same timestep would give about 6.7 %, not
  5.5–6.1 %, and one against the PMV before the correction needs the PMV calculated again (A6, `accim[comfort]`).
- Options considered: (a) the relation of the EMS, factor = 1 − 0.067·PMV of the previous timestep (0–3, cooling
  season), and corrected activity = activity·factor, with `calculation_tolerance` (0.001); (b) a band of 5.5–6.7 % on
  (1 − factor)/PMV of the same timestep, approximate and also with hourly outputs; (c) the PMV before the correction
  calculated with pythermalcomfort, and the band 5.5–6.1 %.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (it is exact and catches any other reduction; the
  5.5–6.1 % stays documented as the result of the correction).

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
