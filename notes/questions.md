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

## 2026-11-18 — The windows of the model on the design days in full air-conditioning ('vrf_ac')
- Context: the VRF heating with warm zones noted on 2026-11-18, investigated the same day (`DEVLOG.md`). In 'vrf_ac' the
  AirflowNetwork windows of the model keep its own control (section 4.1 of the detailed use), and those of the sample
  model open on its winter design day: its venting setpoint schedule (`20001`) is 0 °C on the winter design days and
  24 °C on the other days. So the sizing of the winter design day has the windows open at −4 °C: design heating loads of
  303 and 357 kW, VRF indoor units of 62 and 73 m³/s, coils and outdoor units of 1.0 and 1.2 MW and constant fans of
  8.9 and 10.5 kW, whose heat keeps the zones at 22.6 to 26.6 °C in a week of January with the cooling coils on in 1007
  of its 1008 timesteps (1401 and 1666 kWh, and 1495 and 1763 kWh of the fans); the heating with warm zones is that of
  the timesteps in which the windows open (24 °C of air). With the schedule at 24 °C on the winter design days: 1.5 and
  1.7 kW, 0.61 and 0.79 m³/s, fans of 87 and 113 W, and in that week 45 and 69 kWh of cooling, 15 and 19 kWh of the
  fans and 6.8 and 7.4 kWh of heating. In mixed mode ('vrf_mm') the EMS closes the windows on the design days, and the
  sizing is that of the setpoints (1.5 and 1.7 kW, 0.63 and 0.81 m³/s, a year of 2026-11-18).
- Why it matters: every simulation of the sample model with 'vrf_ac' (tests, docs, the measurements of comfort
  standard 24 and of its fallback, the try-runs of the validation study of F3, whose VRF system "does not hold 26 °C")
  has VRF systems about 100 times larger than its loads, with fans whose heat dominates the energy and the
  temperatures; the comparisons between cases of the same model hold, their absolute values do not. Any input model
  whose natural ventilation opens its windows on a design day gets the same sizing with 'vrf_ac' (and its autosized
  systems with 'ex_ac').
- Options considered: (a) 'vrf_ac' (and 'ex_ac') close the windows of the AirflowNetwork on the design days, as mixed
  mode does, and keep the natural ventilation of the model on the other days (the output IDFs of 'vrf_ac' with an
  AirflowNetwork change: golden master); (b) 'vrf_ac' closes them always, a full air-conditioning without natural
  ventilation (the documented behaviour changes); (c) a warning of AddAccis when the windows of the model can open on
  the design days, and the sample model fixed (its schedule `20001` at 24 °C on the winter design days: a sample file,
  and the results of the tests and docs that use it, change); (d) the sample model fixed only.
  Recommendation of Claude Code: (a), the sizing for the setpoints with the windows closed, as in mixed mode, with a
  note in section 4.1; then the measurements with 'vrf_ac' and the sample model whose absolute values matter (the
  validation study) are taken again.
- Owner: the author.
- Status: open.

## 2026-11-18 — Check 2 with the HVAC system on in a part of the previous timestep: keep it exact, or accept both states?
- Context: the entry of `TODO.md` (found with B2): the EMS sensors of the coils read their last system timestep, and
  check 2 takes the HVAC system of the previous timestep as on where the outputs of that timestep (its means) are not
  0, so a window that the EMS opened after a timestep in which a coil worked in a part of it would be a false
  mismatch. The definition of done of the entry accepts both states there, with an EnergyPlus case. Searched again on
  2026-11-18: a year of the sample model in mixed mode ('vrf_mm', HVACmode 2, VentCtrl 0) gives no mismatch of check
  2, and no window opens in a timestep after one with the coils of its zone on (12902 and 11643 such timesteps in the
  two zones; the windows opened 1841 and 2138 times), as in four weeks before.
- Why it matters: accepting both states wherever the coils of the previous timestep worked would make check 2 accept
  a window open after a timestep with the coils on all of it, which it reports now (the decision of 2026-11-13 of an
  exact check 2; the timestep 41 of `test_check_2_compares_the_opening_factor_of_each_window_with_that_of_its_programs`
  would change); keeping it, the false mismatch would be reported if it ever happens.
- Options considered: (a) keep check 2 as it is and close the entry, with a note in the docs of check 2 (possible, not
  seen in a year of the sample model); (b) accept both states there (the definition of done); (c) report those
  timesteps apart, as possible false mismatches (as check 1 does); (d) read the outputs at the frequency of the system
  timesteps when the model reports them (they tell the state exactly; ReadVarsESO and the reader of its CSV file do
  not take them yet). Recommendation of Claude Code: (a).
- Owner: the author.
- Status: open.

## 2026-11-18 — IND IMAC: the band of 85 % of the static setpoints, and the running means below 15 °C
- Context: checked on 2026-11-18 (`notes/decisions.md`): the line 0.078·Tout + 23.25 of the static setpoints of
  comfort standards 7 to 10 (and of comfort mode 1 of 11, IND Dhaka, out of its applicability limits), with the
  30-day outdoor running mean and ±1.5 K for 90 % of acceptability, is that of the air-conditioned buildings of the
  National Building Code of India 2016 (Volume 2, Part 8, Section 3, 6.2 c)); it is equation 3 of Dhaka & Mathur
  (2017), whose text gives 1.47 K (90 %) and 2.72 K (80 %) as half-widths, although its Table 7 gives bands of those
  widths (±0.73 and ±1.36 K): the paper contradicts itself, and the code and accim follow its text. The ±2.11 K of
  category 85 (comfort standards 7 and 8) is the mean of 1.5 and 2.72 K, which neither source gives. The code says
  that its equations are not applicable with outdoor running means below 15 °C (Dhaka & Mathur fitted it with
  outdoor temperatures of 25 to 44 °C); accim applies the line with any running mean (comfort mode 0, and comfort
  mode 1 out of the applicability limits of the adaptive models, also below them, and so in comfort standard 11).
- Options considered: (a) keep the setpoints, documented (done on 2026-11-18); (b) category 85 of comfort modes 0
  and 1 documented as an interpolation (done) or removed; (c) the line limited to running means of 15 °C or more
  (below, its value at 15 °C), in comfort standards 7 to 11, which changes the setpoints below 15 °C; (d) the bands of
  Table 7 of the paper (±0.73 and ±1.36 K) for categories 90 and 80, which would leave the code. Recommendation of
  Claude Code: (a).
- Owner: the author.
- Status: open.

## 2026-11-18 — Should `AddAccis` write comfort standard 24, with the fallback of the EMS?
- Context: since 2026-11-18 (the provisional decision of that day in [[decisions.md]]), `apply_sun2026_setpoints(model,
  ems_fallback=True)` gives a model of comfort standard 24 a feedback of its setpoints on the SET of the Pierce model
  of EnergyPlus, with which it runs with the EMS backend (`run_ep()`); the model is generated with another comfort
  standard, whose comfort temperature and applicability limits its zones keep, and `AddAccis` raises a `ValueError`
  with comfort standard 24 (its message points to `ems_fallback`). The entry of `TODO.md` of the fallback (v03 A6a)
  had "the `ValueError` of `AddAccis` replaced by it" in its definition of done.
- Why it matters: with comfort standard 24 in `AddAccis`, its output IDFs (`CS_INT Sun2026 SET`) would run with the
  EMS backend like the others, also in the parametric module; but it changes the arguments and the output IDFs of
  `AddAccis`, and the zones need a comfort temperature and applicability limits of their own (comfort standard 24 has
  none: its setpoints are those of the SET).
- Options considered: (a) leave it as it is: `AddAccis` with another comfort standard, then `apply_sun2026_setpoints(...,
  ems_fallback=True)` (two steps, documented in section 4.9.3); (b) `AddAccis` with comfort standard 24 writes the
  ACCIS of another comfort standard for the comfort temperature and the limits (an argument, or a default such as that
  of ASHRAE 55), and then the objects of the hook and the fallback (with the arguments `tsv_limit`, `set_offset`,
  `ems_relaxation` and `ems_slope`, and People objects with the schedules of the Pierce model), the output IDFs being
  run with the EMS backend or with the hook; (c) as (b), with the comfort temperature and the limits of the causal SET
  model itself (the neutral SET and the band, converted to operative temperatures by the fallback), a new design.
  Recommendation of Claude Code: (a) until the validation study of F3 needs comfort standard 24 in parametric studies,
  then (b).
- Owner: the author.
- Status: open.

The other questions are answered: the question of 2026-11-18 on the digits of the curves of the VRF systems in the
output IDFs of AddAccis and the question of 2026-11-17 on the range of the bisection of comfort standard 24 were
answered on 2026-11-18, the question of 2026-11-12 on the validation study of F3 and that of 2026-11-13 on checks 1
and 2 of the verification were decided on 2026-11-13, and the six questions that were open after session 3 of the
review of 1.2.0, on 2026-11-12 (see "Answered" below).

## Answered

The question of 2026-11-18 on whether the output IDFs of `AddAccis` keep all the digits of the curves of the VRF
systems (eppy wrote four coefficients of the curves of the indoor units with 7 significant digits in them, and the
models of `add_accis_to_idf` had all of them, so the results differed in their last digits by the function that made
the model) was answered by the author on 2026-11-18 ("Sí, hazlo"): option (b), the recommendation of Claude Code,
`AddAccis` and the parametric module keep all the digits; extended to the numbers of the input models and to the other
files of models that accim writes: see
[[decisions.md#2026-11-18 — accim keeps all the digits of the numbers of the models that it writes|the decision of 2026-11-18]].

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
