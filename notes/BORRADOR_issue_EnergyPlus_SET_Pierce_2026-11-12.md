---
title: Draft of an issue for EnergyPlus — the SET of the Pierce two-node model
type: draft
tags: [energyplus, set, pierce, e-f1]
created: 2026-11-12
---

# Draft of an issue for EnergyPlus: the SET of the Pierce two-node model

> **Para el autor.** Borrador del issue que pide la decisión del 12/11/2026 sobre los hallazgos A1 y A2 de la
> autoauditoría (`notes/decisions.md`): lo publica el autor, si lo ve oportuno, en el repositorio de EnergyPlus
> (NatLabRockies/EnergyPlus, antes NREL/EnergyPlus). El texto del issue está en inglés, listo para pegar, entre las
> dos líneas horizontales. Lo redactó Claude Code (Claude Fable 5.2) con la medición de E-F1 repetida el 12/11/2026
> (`tests/core/test_pierce_set.py`). Qué está comprobado y qué no:
>
> - **Comprobado en las fuentes** (etiqueta `v25.1.0` del repositorio de EnergyPlus, leídas el 12/11/2026): las líneas
>   de `src/EnergyPlus/ThermalComfort.cc` y `ThermalComfort.hh` que se citan, y el texto de
>   `doc/engineering-reference/src/simulation-models-encyclopedic-reference-005/occupant-thermal-comfort.tex`.
> - **Medido** con EnergyPlus 25.1 y pythermalcomfort 4.8.1 en el servidor: las tres tablas.
> - **No comprobado**: el listado del programa del SET del apéndice D de ASHRAE 55-2017 (el que cita el código de
>   EnergyPlus) ni el de ASHRAE 55-2020 (el que dice seguir pythermalcomfort): ninguna de las dos normas está en la
>   biblioteca. Por eso el issue pregunta cuál de los dos comportamientos es el deseado, sin afirmar cuál es el correcto.
>   Conviene revisar ese punto con la norma delante antes de publicarlo.
> - Antes de publicarlo, conviene buscar en el repositorio de EnergyPlus si ya hay un issue abierto sobre lo mismo.

---

**Title:** Pierce two-node model (SET): the code and the Engineering Reference differ in the convective coefficient of
the actual environment and in the body surface area

**EnergyPlus version:** 25.1.0 (build 1c11a3d85f), Windows 11. The lines quoted are those of the tag `v25.1.0`.

### Summary

The Engineering Reference says that the convective heat transfer coefficient of the Pierce two-node model is the
larger of a term of the air velocity and a term of the metabolic rate, and that all the thermal comfort models take a
body surface area of 1.8 m². In the code of the Pierce model, the convective coefficient of the actual environment has
no term of the metabolic rate (only that of the standard environment has it), and the activity level is divided by
1.8258 m². With activity levels above about 1.05 met, the output *Zone Thermal Comfort Pierce Model Standard Effective
Temperature* is then higher than the SET of other implementations of the two-node model that apply that term in the
actual environment: 0.33 K at 1.08 met and 0.97 K at 1.19 met in the case below, against pythermalcomfort 4.8.1.

We do not know which of the two is intended, so this is a question about the code and a note on the documentation,
rather than a bug report.

### What the Engineering Reference says

`doc/engineering-reference/src/simulation-models-encyclopedic-reference-005/occupant-thermal-comfort.tex`, Pierce
Two-Node Model:

- the convective heat transfer coefficient "varies with the air velocity around body and metabolic rate", and "the
  model uses the maximum value of" `h_c = 8.6 v^0.53` and `h_c = 5.66 (M/58.2 - 0.85)^0.39`; in the code form given
  there, `Hc = 8.6*AirVel**0.53` with the air velocity reset to 0.137 if it is lower, and
  `HcAct = 5.66*(ActMet - 0.85)**0.39` when `ActMet` is greater than 0.9;
- in its background section, the average person area of 1.8 m² "is used for the body surface area all thermal comfort
  models".

### What the code does

`src/EnergyPlus/ThermalComfort.cc`, `CalcStandardEffectiveTemp` (its header cites ANSI/ASHRAE Standard 55-2017,
Appendix D):

```cpp
if (AirVel < 0.1) AirVel = 0.1;
...
Real64 PInAtmospheres = state.dataEnvrn->OutBaroPress / 101325;
Real64 CorrectedHC = 3.0 * std::pow(PInAtmospheres, 0.53);
Real64 ForcedHC = 8.600001 * std::pow((AirVel * PInAtmospheres), 0.53);
state.dataThermalComforts->Hc = std::max(CorrectedHC, ForcedHC);
```

and the term of the metabolic rate only in the standard environment:

```cpp
if (ActMet <= 0.85) {
    StdHc = 3.0;
} else {
    StdHc = 5.66 * std::pow(ActMet - 0.85, 0.39);
}
if (StdHc <= 3.0) StdHc = 3.0;
```

`GetThermalComfortInputsASHRAE` divides the activity level by `BodySurfAreaPierce`, and `ThermalComfort.hh` has

```cpp
Real64 constexpr BodySurfArea = 1.8;          // Dubois body surface area of the human body (m2)
Real64 constexpr BodySurfAreaPierce = 1.8258; // Pierce two node body surface area of the human body (m2)
```

So three things differ from the Engineering Reference: the convective coefficient of the actual environment has no
term of the metabolic rate; the lowest air velocity is 0.1 m/s, not 0.137 m/s (which the KSU model takes); and the
Pierce model takes 1.8258 m², not 1.8 m².

### How much it changes the SET

A two-zone model with a VRF system (the weather file of Seville, a year, 6 timesteps per hour), with the Pierce model
in its People objects, a constant air velocity schedule of 0.137 m/s, no work efficiency, a clothing insulation
schedule of 1.0 clo (winter) and 0.5 clo (summer), and a constant activity level schedule of 110.7, 115 or 126
W/person. For each timestep, the SET was also calculated with `pythermalcomfort.models.set_tmp` (pythermalcomfort
4.8.1) from the outputs *Zone Mean Air Temperature*, *Zone Mean Radiant Temperature* (the People objects have
`EnclosureAveraged`) and *Zone Air Relative Humidity* of the zone and the schedule values of the People object, with
the metabolic rate as the activity level divided by 58.2 W/m² and 1.8258 m², standing. Hourly means of the SET of
pythermalcomfort minus that of EnergyPlus, all the hours of the year, one zone (the other one is the same within
0.001 K in the means):

| Activity level | Metabolic rate | Mean (K) | Mean absolute (K) | Maximum absolute (K) |
| --- | --- | --- | --- | --- |
| 110.7 W/person | 1.04 met | −0.058 | 0.058 | 0.13 |
| 115 W/person | 1.08 met | −0.331 | 0.331 | 0.52 |
| 126 W/person | 1.19 met | −0.966 | 0.966 | 1.39 |

pythermalcomfort 4.8.1 applies `5.66*(met - 0.85)**0.39` in the convective coefficient of both environments. With that
term taken out of its actual environment only (a copy of its source with that one condition disabled), as in the code
of EnergyPlus:

| Activity level | Metabolic rate | Mean (K) | Mean absolute (K) | Maximum absolute (K) |
| --- | --- | --- | --- | --- |
| 110.7 W/person | 1.04 met | −0.058 | 0.058 | 0.13 |
| 115 W/person | 1.08 met | −0.056 | 0.056 | 0.13 |
| 126 W/person | 1.19 met | −0.051 | 0.051 | 0.13 |

So that term accounts for all the dependence on the activity level; the remaining 0.05 K is of the order of the other
differences between both codes (EnergyPlus takes 0.72 as the fraction of the body surface that radiates;
pythermalcomfort, 0.73 standing and 0.70 sitting). The term is the larger one from about 1.05 met at 0.137 m/s.

The body surface area is a smaller effect: with 110.7 W/person converted with 1.8 m² instead of 1.8258 m² (1.057 met
instead of 1.042 met), the SET of pythermalcomfort is 0.013 K higher on average over the year (0.037 K higher with 1.0
clo, 0.012 K lower with 0.5 clo).

### Questions

1. Is the convective coefficient of the actual environment without the term of the metabolic rate the intended
   behaviour (the program of ASHRAE 55-2017, Appendix D, which the code cites)? If it is, could the Engineering
   Reference say that the term `5.66 (M/58.2 - 0.85)^0.39` applies to the standard environment only, that the lowest
   air velocity is 0.1 m/s, and that the Pierce model takes a body surface area of 1.8258 m²? If it is not, the SET of
   the Pierce model is about 0.3 K too high at 1.1 met and 1 K too high at 1.2 met.
2. Later editions of ASHRAE 55 and other implementations (pythermalcomfort, which says it follows ASHRAE 55-2020)
   apply that term in the actual environment too. Would EnergyPlus follow them?

### How to reproduce

Any model with a People object whose *Thermal Comfort Model Type* fields include `Pierce`, an activity level schedule
above about 110 W/person and the output *Zone Thermal Comfort Pierce Model Standard Effective Temperature*, compared
with `set_tmp(tdb, tr, v, rh, met, clo)` of pythermalcomfort from the outputs and schedule values above. The script of
the measurement is the test `tests/core/test_pierce_set.py` of accim (https://github.com/dsanchez-garcia/accim, branch
`v1.2.0`), which builds the model from a sample file of that repository.

---

## Notes for the author (not part of the issue)

- The numbers are those of `tests/core/test_pierce_set.py` (measured on 2026-11-12; `notes/decisions.md`, E-F1).
- The second table needs a modified copy of the two-node model of pythermalcomfort 4.8.1 (the test builds it from the
  installed source, and is skipped with another version of pythermalcomfort).
- accim keeps the conversion of the activity level with 1.8 m² in its hooks (decision of 2026-11-12, finding A1), so
  its SET differs from the Pierce SET of EnergyPlus by those 0.013 K too.
