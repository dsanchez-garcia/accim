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

## 2026-11-09 — A3: with adaptive_coefficient_by='pmv_sign', which λ converts each setpoint into the PMV setpoint of the thermostat
- Context: the design of A3 gives the Erl of the option, "if PMV_{s} >= 0 set adap_coeff = λ_warm else λ_cool", with
  the PMV of the previous timestep, but not which λ converts the setpoints of the aPMV into the PMV setpoints of the
  thermostats (PMV = aPMV/(1 − λ·aPMV), v03 §11.1); with 'season' it is the λ of the season, as in accim 1.1.0.
- Why it matters: with the λ of the sign of the current PMV, the PMV setpoints of the thermostat would change each
  time the PMV changes sign (with λ 0.21/−0.49, the heating setpoint −0.5 would be the PMV −0.45 or −0.66).
- Options considered: (a) each setpoint with the λ of its side of the scale (the heating setpoint, negative where it
  is converted, with the λ of cool sensations; the cooling one with that of warm sensations), which is the inverse of
  aPMV(PMV) with λ by the sign; (b) both with the λ of the sign of the PMV of the previous timestep (the Erl of the
  design applied to the inverse too).
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (the monitor and the output `Adaptive
  Coefficient_<zone>` follow the design).

## 2026-11-09 — A3: does a key of the catalogue in one coefficient also set the other one
- Context: the design of A3 says that a key given in `adaptive_coefficient_cooling` "fills both coefficients at once
  unless the other is given explicitly"; its prompt only says that the arguments accept a key, and the defaults of the
  coefficients are numbers (0.293 and −0.293), so an explicit value equal to the default cannot be told apart.
- Why it matters: `adaptive_coefficient_cooling='yao2009_chongqing_classrooms'` alone gives λ 0.293 and −0.293 (the
  default) with (a), and 0.293 and −0.125 with (b).
- Options considered: (a) each argument takes the coefficient of its own side of the key (give the key to both to use
  the entry); (b) the defaults become None, which takes the other coefficient of a key, or 0.293/−0.293 otherwise (the
  signature changes, and the GUI and the documentation show other defaults); (c) a new argument with the key for both.
- Owner: the author.
- Status: open; option (a) decided provisionally, pending author (the conservative, backward-compatible one;
  documented in the docstring and in section 4.8).

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
