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

## 2026-11-11 — Comfort standards 9 and 10 (IND IMAC R 7DRM and 30DRM): their running means, and the heating setpoint of 9 in comfort mode 1
- Context: the review of Claude Science of 2026-11-11 (`notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §2.1)
  checked the source of comfort standards 9 and 10, Rawal et al. (2022), Building and Environment 219, 109187
  (doi:10.1016/j.buildenv.2022.109187), Fig. 15: model A, Tneut = 0.39·Tout-7DRM + 18.42, with the simple mean of the 7
  previous days (the paper tells it apart from the weighted one, Tout-7DRM-W), and model B, Tneut = 0.42·Tout-30DRM +
  17.60. In accim the coefficients, the bands and the applicability limits are right, but the metrics are swapped: 9
  (7DRM) uses PMOT, the simple mean of 30 days of EnergyPlus, and 10 (30DRM) uses RMOT, the exponential running mean
  with α = 0.8 of EnergyPlus (`SetComfTemp` uses PMOT for both). In comfort mode 1 of 9, out of the applicability
  limits, the heating setpoint is `PMOT*0.078+23.25+2.72` (category 80) or `+1.5` (90), that of cooling, where comfort
  mode 0 of 9 and comfort mode 1 of 10 use the minus sign. The static equation 0.078·T + 23.25 could not be verified
  (it is not in Manu et al., 2016; probably the National Building Code of India 2016, not in the library). The
  analysis is in the entry of `TODO.md`.
- Why it matters: the setpoints of 9 and 10 follow other outdoor temperatures than those of their models, and the
  heating and cooling setpoints of 9 in comfort mode 1 are equal (but the tolerances) out of the limits; fixing them
  changes the results of 9 and 10 and their output IDFs.
- Options considered: (i) the recommendation of the review: 10 with PMOT (exactly the 30DRM); 9 with the arithmetic
  mean of the 7 previous days of the machinery of B1 (`'ndrm'`, 7 days, started from the weather file; without it, the
  start of B1); `SetComfTemp`, the setpoints and `CountHours` consistent; the minus sign in comfort mode 1 of 9; the
  golden master updated; `CHANGELOG.md` (Fixed) with a note of migration (the results published with accim 1.1.0 or
  earlier are reproduced with those versions); and, with the metrics corrected, the outdoor mean of the static line
  checked in its source (in 10 it reads RMOT today); (ii) keep them as they are, documented; (iii) fix the sign only.
- Owner: the author.
- Status: open; the author decided on 2026-11-11 not to change them in session 3 (`notes/COPILOT_SIGUIENTE_SESION.md`
  §2, rule 7): nothing was changed.

## 2026-11-10 — F3: the SET of the indicators of the causal band
- Context: the proposal of block F (§4 F3) asks for the hours within the causal band of every model; the SET can be
  that of the Pierce model of EnergyPlus (any model, with the outputs of `add_thermal_comfort_outputs`) or that of
  pythermalcomfort of the hook of comfort standard 24 (`SET_<zone>`, only in its simulations).
- Why it matters: the SET of the hook is 0.08–0.155 K below that of EnergyPlus on average (E-F1, F1), so the hours of
  the band of a simulation of comfort standard 24 differ slightly between both.
- Options considered: (i) the SET of EnergyPlus for every simulation (implemented: the same measure for every model;
  the hook still reports its own hours, `HoursInCausalBand_<zone>`); (ii) the SET of the hook where it exists.
- Review (2026-11-11, the handoff of Claude Science, `notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §2.3 and
  §3, #9): pending a question for Ruiji Sun: the text of Sun, Brager & Schiavon (2026) does not say which
  implementation of the SET they used. Until the answer, keep the Pierce SET of EnergyPlus as the SET of the
  indicators, and report also the indicators of the SET of pythermalcomfort (recalculated with `set_of_results`):
  E-F1 measured differences of −0.045 K on average and 0.18–0.20 K at most standing, and −0.12 K and 0.32–0.34 K
  sitting, of the order of what moves the hours near the limits of the band of 19–28 °C. Done provisionally in
  task S4 of the session of 2026-11-11.
- Owner: the author, with Ruiji Sun.
- Status: open; option (i) implemented provisionally, and the indicators of the SET of pythermalcomfort as an
  option (task S4 of the session of 2026-11-11).

## 2026-11-10 — F3: the static reference of case (i) of the validation study
- Context: the design of the study (§4 F3) has the case "(i) referencia estática PMV (24–26 / 20–22 °C)".
- Why it matters: accim has the PMV setpoints of `apply_pmv_setpoints` (category II: −0.5 and 0.5), the static
  setpoints of comfort mode 0 of the comfort standards (those of ISO 7730 of categories 80 and 90 are 25 and 27 °C or
  24 and 26 °C for cooling, and 19 and 22 °C or 20 and 23 °C for heating), and fixed thermostats.
- Options considered: one of them, or fixed setpoints of 24–26 °C and 20–22 °C (which accim would set with the static
  setpoints of a comfort standard defined by its data, section 4.2.5).
- Review (2026-11-11, the handoff of Claude Science, `notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §3, #12):
  a decision of the author with Ruiji Sun. Recommendation: (a) the PMV setpoints of `apply_pmv_setpoints`,
  category II (±0.5), as the reference of a "fixed PMV" (question 1 of `01_informe/propuesta_paper_RuijiSun_v02.md`
  of the folder *Indoor adaptive setpoints* of the author); (b) besides, fixed static setpoints of EN 16798-1:2019,
  Table B.2, category II (offices, 20 and 26 °C).
- Owner: the author, with Ruiji Sun.
- Status: open; section 4.7.6 of the detailed use lists the first two; no simulation run (`TODO.md`).

## Answered

The questions on the scope and the technology of the GUI, on the names of the arguments of accim 1.0.0, on the EMS
code of the comfort standards of each output IDF of `AddAccis` (option 1, as implemented), on the design days of
`vrf_mm` (option (a): the same rule as `ex_mm`) and on the `schedule` of `set_clothing_method` of A5 (option (b): the
clothing insulation schedule, and another argument for `CalculationMethodSchedule`) were answered: see
[[decisions.md]]. The 36 provisional decisions of the proposals of 1.2.0 (2026-11-09 and 2026-11-10)
were answered on 2026-11-10 (`notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md` §5): see [[decisions.md#2026-11-10 — The verdicts of the author on the 36 provisional decisions of the proposals of 1.2.0|the verdicts of 2026-11-10]]. The 23 provisional decisions of the session of the review v04 (2026-11-10 and 2026-11-11) were answered on
2026-11-11 (the verdicts of the handoff of Claude Science, §3), but for two that stay open above, pending the author
with Ruiji Sun (the SET of the indicators of F3 and the static reference of case (i) of its validation study): see
[[decisions.md#2026-11-11 — The verdicts on the 23 provisional decisions of the session of the review v04|the verdicts of 2026-11-11]].
