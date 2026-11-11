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

## 2026-11-11 — The findings of the self-audit of session 2 that need a decision of the author
- Context: the self-audit of session 2 (`notes/attachments/autoauditoria_sesion2_v1.2.0.json`, findings A1–A26;
  §5 and §7 of `notes/COPILOT_SIGUIENTE_SESION.md`). The bugs and the small fixes are done in session 3 (see the entry
  of the report `notes/INFORME_SESION_v1.2.0_2026-11-11_3.md`); these need a choice of the author, so nothing was
  changed (the most conservative option), except the documentation where it says so.
- Why it matters: each one changes the results, the outputs or the model of some users.
- Options considered, by finding:
  - **A1 (scientific, E-F1 and F1)**: EnergyPlus converts the activity level of its Pierce model with a body surface
    area of 1.8258 m² (ThermalComfort.cc of EnergyPlus 25.1), and accim (the hooks of the SET and the comparison of
    E-F1) with 1.8 m² (`MET_ACTIVITY_LEVEL`, the convention of Fanger and ISO 7730): 1.43 % more met (1.057 against
    1.042 met for 110.7 W/person), so the differences of E-F1 and F1 (−0.045 K standing, −0.116 K sitting; −0.08 and
    −0.155 K) mix an input difference with the model difference. (i) Keep 1.8 m² and document the offset (about
    0.1 K, to be measured); (ii) convert with 1.8258 m² in the hooks, consistent with the Pierce SET that F1 and F3
    report beside them. The new measurement needs pythermalcomfort, blocked on this server (numba and Smart App
    Control; `TODO.md`).
  - **A2 (scientific, E-F1)**: in the real environment, EnergyPlus 25.1/25.2 computes the convective coefficient of
    the Pierce model without the term of the activity, 5.66·(met − 0.85)^0.39 (which it applies only to the standard
    environment), unlike its Engineering Reference and pythermalcomfort; above about 1.046 met that term is the larger
    one, so the agreement of E-F1 (the sample model is at 1.042 met in the Pierce model) holds near 1 met only. (i)
    Repeat E-F1 at 1.1 and 1.2 met and restrict the present statements to about 1 met (blocked here, as A1); (ii) the
    choice of the reference SET of F1 and F3 together with decision 9 (Ruiji Sun).
  - **A4 (design, F1)**: a model prepared by `apply_athb_setpoints`, `apply_set_setpoints` or
    `apply_sun2026_setpoints` simulated without its hook (the EMS backend, or the API without hooks) runs without an
    error or a warning, with the setpoints of the ACCIS and the outputs of the hook at 0. (i) As now, documented; (ii)
    `run_ep` and `run_simulation` raise (EMS backend) or warn (API backend without a hook) when the model has the
    programs `ApplyHookSetpoints_<zone>`.
  - **A8 (design, F2)**: `drift_mode='window'` clips both setpoints to T_rm_in ± delta, and T_rm_in is the running
    mean of the operative temperature of the zone itself, so the dead band collapses to `delta_heat + delta_cool` (2 K)
    around the recent temperature of the zone (or to a point, with crossed thermostats, when the band of the comfort
    model is all out of the window), with much more heating or cooling, and the exposure can drift by only about
    (1 − α)·delta per day: a stricter control than `'rate'`. It is decision 6 of the author, implemented as written.
    (i) Document the collapse and its energy effect, and warn with `'window'`; (ii) redefine `'window'` to limit only
    the changes that move a setpoint farther than delta from T_rm_in, or to shift the whole band keeping its width;
    (iii) keep `'rate'` as the recommended mode (case (v) of the validation study uses it). The narrow window of
    finding A9 raises a `ValueError` since session 3.
  - **A15 (design, H3)**: the range of `long_term_range` of the long-term discomfort uses the minimum for heating and
    the maximum for cooling of EN 16798-1, Table B.2 (20–26 °C for category II) in all the timesteps, while the table
    gives seasonal one-sided design values (about 1.0 clo in winter and 0.5 clo in summer), so summer overcooling between
    20 and 23 °C and winter overheating between 24 and 26 °C count as comfortable. (i) State the limitation in section
    4.2.6 (and pair it with the overcooling indicator of F3); (ii) a seasonal variant with the cooling season of the
    ACCIS, once the author chooses a source for the missing bounds.
  - **A19 (design, G5)**: where the minimum (maximum) of the setpoints binds, the thermostat setpoint and the limit of
    the comfort band are both the limit (AHST = AHSTnoTol = AHSTmin), so the tolerance vanishes there, unlike the
    setpoints of the hooks (decision 23 of G1: the thermostats get the band plus the tolerance). (i) As now, documented
    (the hour counters at the limit); (ii) AHST = max(AHST, AHSTmin + AHSTtol) and ACST = min(ACST, ACSTmax +
    ACSTtol), with AHSTnoTol and ACSTnoTol bounded by the limits (changes the output IDFs with limits).
  - **A24 (bug, G4)**: in the models of `add_accis_to_idf` (the code of all the comfort standards), a zone switched to
    comfort standard 23 by editing `set ComfStand = 23` in its program `SetInputData_<zone>` stops EnergyPlus during
    the warm-up ("Variable = 'STATICACST' used in expression has not been initialized"), since only the zones of 23
    have the inputs `StaticAHST` and `StaticACST` (decision of G4: the zones of the other comfort standards do not get
    them, and their output IDFs do not change). (i) As now, documented in section 4.2.1 (session 3); (ii) give every
    zone of the models with the code of 23 the two inputs (changes the output IDFs of `add_accis_to_idf`, golden
    master s01–s06 and s09); (iii) initialise both global variables in a program at the beginning of each environment
    (changes them too).
  - **A25 (design, G4)**: a `modify_accis` call that changes the outdoor metric of another zone without `epw`
    rewrites the programs of the outdoor metric beginning with PMOT, so the zones of JPN Aqilah 2025 move silently from
    the running mean of the weather file to the RMOT of EnergyPlus (about 21 % low on the first day, B4-1), without the
    warning of RMOT, and the warning that is given says that `rmot_alpha` begins with PMOT, which is wrong for those
    zones. (i) Give the warning of RMOT whenever the model has zones of 23 and its programs stop beginning with a
    weather file, and leave those zones out of the warning of PMOT; (ii) keep the start with the weather file (do not
    rewrite without `epw` when the programs can be kept, or ask for `epw`); document it in `modify_accis`.
- Owner: the author (A1 and A2 with Ruiji Sun, as decision 9).
- Status: open; nothing changed but the documentation of A24 (section 4.2.1).

## 2026-11-11 — S4: how the indicators of the causal band are given with the SET of pythermalcomfort
- Context: decision 9 (provisional, the entry "F3: the SET of the indicators of the causal band" below; task S4 of
  `notes/COPILOT_SIGUIENTE_SESION.md`): keep the Pierce SET of EnergyPlus and add, behind an optional argument off by
  default, the same indicators with the SET of pythermalcomfort, through `set_of_results` (G3) and the inputs that
  E-F1 compared. It does not say where the argument goes, how the inputs of the occupants are given, where the
  conditions of the zones come from, nor how the rows of the CSV files are matched with those of the table.
- Why it matters: `set_of_results` takes constant inputs of the occupants (those of a hook), while E-F1 took the
  values of the schedules of the People objects in each timestep, as EnergyPlus does; and `Table` drops the mean
  radiant temperature and the relative humidity with `standard_outputs=True` (and adds them up over the timesteps of
  each hour with `frequency_agg_func='sum'`).
- Options considered: (i) the argument `pythermalcomfort_set` of
  `accim.data.postprocessing.indoor_adaptation.table_indicators` only (not of `Table` nor of the GUI): a dict with
  `met`, `clo`, `air_speed` and, optionally, `position` (the posture of the hooks by default), or a hook of the SET
  with them; the SET of `set_of_results` of the outputs *Zone Mean Air Temperature*, *Zone Mean Radiant Temperature*
  and *Zone Air Relative Humidity* of each zone, keyed by its name in the table, in each row of the CSV file of each
  simulation (the column `Source` with `.csv`, in the current folder), averaged over the rows of the CSV file of each
  row of the table (as `Table` averages the Pierce SET; the hour of each row as `Table` gives it); the columns
  `<zone>_Mean SET_pythermalcomfort (°C)`, `<zone>_Mean TSV_causal_pythermalcomfort` and `<zone>_Hours In / Above /
  Below Causal Band_pythermalcomfort (h)` and `(%)` after those of each zone and of the building; NaN, with a
  warning, for the zones without those outputs (such as those that `Table` names after their spaces); a `ValueError`
  if a CSV file is not found (implemented); (ii) the inputs of the occupants of each row from the schedules of the
  People objects (their outputs *Schedule Value*, as E-F1), which cases (iii) and (iv) of the validation study need
  (a seasonal clothing insulation, the dynamic clothing model): it needs those outputs requested and the People
  objects of each zone; (iii) an argument of `Table` too (and its box in the GUI); (iv) the conditions of the zones
  from the columns of the table.
- Owner: the author (with the answer of Ruiji Sun on decision 9).
- Status: open; option (i) implemented provisionally: off by default, the other indicators and the outputs do not
  change.

## 2026-11-11 — S1: the details of the comparison of the minimum and maximum with the setpoints of the comfort model
- Context: decision 19 (the verdicts of 2026-11-11 in [[decisions.md]]; task S1 of `notes/COPILOT_SIGUIENTE_SESION.md`)
  replaces the comparison with `ACSTaul`/`AHSTall` by option (ii): with the weather file, the setpoints of the comfort
  model of each zone with `accim.sim.preview.compute_setpoints`, and a warning for each zone whose minimum is at or
  above the lowest cooling setpoint, or whose maximum is at or below the highest heating setpoint, with the value, the
  first date and the number of days; the zones that `compute_setpoints` does not cover are left out with a debug
  message. It does not say which setpoints, which days, nor when `modify_accis` compares them.
- Why it matters: what the warning reports, and when it is given.
- Options considered: (i) the setpoints of the thermostats (`ACST`/`AHST`, with the tolerance, rounded: where they
  cross, the heating setpoint of the thermostats is at or above the cooling one), by timestep, with the timesteps per
  hour of the model, from the first day of its first `RunPeriod` to its last day (to the end of the year if the run
  period goes on in the next one), including the first timestep of the run period, whose running means are 0 in the
  EMS as in EnergyPlus; `modify_accis` compares whenever the model has a minimum or a maximum (given in the call or
  before) and `epw` is given; the zones left out: those whose setpoints a hook gives and those with the limiter of the
  drift of the setpoints (their setpoints are not those of `compute_setpoints`), and those whose arguments it rejects
  (with the debug message of the logger `accim.sim.ems.setpoint_limits`, the first use of `logging` in accim)
  (implemented); (ii) the setpoints without the tolerance (`ACSTnoTol`/`AHSTnoTol`, the comfort band), which cross
  later; (iii) the whole year of the weather file, whatever the run period; (iv) leave out the first timestep of the
  run period.
- Owner: the author.
- Status: open; option (i) implemented provisionally (`accim.sim.ems.setpoint_limits.warn_crossed_setpoint_limits`):
  it only adds warnings.

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
