# Brief para GitHub Copilot (Claude Opus 5.5, máximo esfuerzo) — accim v1.2.0

Fecha: 2026-11-09. Complementa `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md` (ciencia, fórmulas, EnergyPlus) con lo que ese documento no puede dar: el estado real del código tras A2/A1/A5, las decisiones del autor y las reglas de trabajo. Pégalo como primer mensaje de la sesión (bloque §1) y después un prompt de propuesta de la v03 (bloques "Prompt para Copilot").

> Antes de pegar §1, revisa §2 (decisiones): están rellenas con la recomendación de Claude Science; cambia las que no compartas. Lo que quede marcado `PENDIENTE` Copilot debe preguntarlo en `notes/questions.md`, no decidirlo.

---

## 1. Mensaje de arranque (pegar tal cual)

```
You are working on accim, branch v1.2.0 (D:\Python\accim). Read, in this order, before writing any code:
1. notes/COPILOT_BRIEF_v1.2.0_v01.md (this file) — rules and the author's decisions.
2. notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md — the proposals. Its sections 11 (formula sheet) and 12 (EnergyPlus 25.2 reference) are verified and are the only source of equations, coefficients, limits and EnergyPlus names: do not take them from memory. Its section 1 describes accim 1.1.0 and is OUTDATED: A2, A1 and A5 are already implemented on this branch (commits c0693c7f, 6d5fb2de, 6a6267dc). For the current API read the code, CHANGELOG.md [Unreleased], DEVLOG.md (entries of 2026-11-08/09) and CAMBIOS_CODIGO_v1.2.0.md.
3. AGENTS_v2.md, TODO.md (conventions and backlog), ROADMAP.md, notes/decisions.md, notes/questions.md, tests/README.md.

Known drift between the v03 proposals and the code (use the code): the registry is accim.sim.pmv_index.PMV_INDICES (not PMV_INDEXES) with the dataclasses PmvIndex and IndexParameter and the attribute add_objects; accim.sim.apmv has apply_apmv_setpoints, apply_epmv_setpoints and apply_pmv_setpoints; set_pmv_input_parameters(building, activity_level=, clothing_insulation=, air_velocity=, work_efficiency=, verbose=, *, cooling_season_start=121, cooling_season_end=274) — the arguments are NOT clo/met; clothing_insulation accepts a number, 'dynamic_ashrae55' or {'heating_season': x, 'cooling_season': y}; the constants are accim.constants.EPMV_EXPECTANCY_RANGES and EPMV_MET_REDUCTION_PER_PMV; accim.sim.people.set_clothing_method(building, method, schedule=None, calculation_method_schedule=None, verbose=True) and CLOTHING_METHODS exist; param_apmv._set_input_line finds Erl lines by variable name; the parametric type 'epmv setpoints' and get_available_params_epmv_setpoints() exist. The ePMV metabolic correction converges to 5.5-6.1 % per PMV unit instead of 6.7 % (documented deviation, CHANGELOG [Unreleased]); keep that documentation consistent if you touch it.

Verified facts about the two backends (read accim/sim/ems/erl.py and accim/sim/energyplus_api/controller.py to confirm before relying on them): the Erl interpreter supports the functions @Abs @ArcCos @ArcSin @Cos @DegToRad @Exp @Ln @Max @Min @Mod @RadToDeg @Round @Sin @WarnEP @SevereWarnEP @FatalHaltEP; the API controller provides the built-in variables HOUR, MINUTE, CURRENTTIME, DAYOFYEAR, DAYOFMONTH, DAYOFWEEK, MONTH, YEAR, CALENDARYEAR, HOLIDAY, DAYLIGHTSAVINGS, SUNISUP, ISRAINING, WARMUPFLAG, SYSTEMTIMESTEP, ZONETIMESTEP, TIMESTEPSPERHOUR, TIMESTEPNUM, CURRENTENVIRONMENT, ACTUALDATEANDTIME, ACTUALTIME, and the calling points BeginNewEnvironment, AfterNewEnvironmentWarmUpIsComplete, BeginZoneTimestepBeforeInitHeatBalance, BeginZoneTimestepAfterInitHeatBalance, BeginTimestepBeforePredictor, AfterPredictorBeforeHVACManagers, AfterPredictorAfterHVACManagers, InsideHVACSystemIterationLoop, EndOfZoneTimestepBeforeZoneReporting, EndOfZoneTimestepAfterZoneReporting, EndOfSystemTimestepBeforeHVACReporting, EndOfSystemTimestepAfterHVACReporting, EndOfZoneSizing, EndOfSystemSizing, AfterComponentInputReadIn, UnitarySystemSizing. EnergyManagementSystem:TrendVariable is NOT supported by the API backend: never generate it. ErlController exposes register, run_calling_point, get and set — read their docstrings; run_simulation hooks are hook(controller, calling_point).

Working rules (from the author):
- Never invent: an equation, coefficient, EnergyPlus field or variable name that is not in the v03 sections 11-12, in the code or in the IDD (C:\EnergyPlusV25-2-0\Energy+.idd) must not be written. If something is missing, write it in TODO.md as a blocked task and say so in the final message.
- Design decisions the documents leave open are the author's: if a decision below is marked PENDIENTE, or a new one appears, add it to notes/questions.md (template of that file) and stop that part; do not pick an option silently. Resolved ones go to notes/decisions.md.
- One proposal per commit, in the order given by the author for this session; before each commit: pytest (tests/core and the affected parametric tests), both run_ep backends identical on a sample IDF when EMS code changed, CHANGELOG.md [Unreleased] entry in the style of the existing ones, DEVLOG.md entry (Context / Changes / Files), TODO.md updated, docs (docs/source/4_detailed use.md and notebooks when the prompt asks), CAMBIOS_CODIGO_v1.2.0.md updated.
- Code: PEP 8, English names and reST docstrings with the citation of each equation (from v03 §9/§11); eppy for IDF I/O, never besos; Erl through accim.sim.ems; deprecations through accim._deprecation; tests with the sample IDFs of accim/sample_files and the EPWs of the repository root; golden-master tests must stay byte-identical unless the task says otherwise.
- At the end of each proposal, report: what was implemented, what deviates from the v03 prompt and why, what was left in TODO.md, and the open questions.

Session plan (the author's order): <E1 → D2 → E2 → B1 → B5 → C1 → D1, or the order he gives>. Start with the first item and stop when its commit is ready; wait for the author before the next one.
```

---

## 2. Decisiones del autor (rellenas con la recomendación; editar antes de pegar)

Copiar este bloque dentro del mensaje de arranque, detrás de "Working rules".

```
Author decisions (binding unless marked PENDIENTE):
D1. Numbering of new built-in comfort standards: ComfStand 23 for JPN Aqilah 2025 (free-running dwellings); numbers >= 100 are reserved for standards loaded from YAML (B3). ComfStand 3 (JPN Rijal) does not change.
D2. Static setpoints of JPN Aqilah 2025 outside its applicability (comfort mode 1): heating 20.0 / cooling 28.0 °C by default, configurable; documented as a user choice because the paper gives none. — PENDIENTE: confirm the values. User response: values are confirmed.
D3. Running-mean initialisation in Erl (B1): at BeginNewEnvironment initialise RMOTa and the Tday_i ring with the values that accim computes in Python from the EPW given to AddAccis (the same series as compute_setpoints, E1); if no EPW is given, initialise with the first value of the native PMOT sensor and warn. Monthly means always need the EPW (ValueError otherwise).
D4. Adaptive coefficient selection in aPMV (A3): keep 'season' (current behaviour) as default; add adaptive_coefficient_by='pmv_sign' using the PMV of the previous timestep. Catalogue entries of grade 'literature' (Zhang 2024 Köppen lambdas) are allowed with a warning; grade 'standard' (Yao 2009, GB/T 50785) without warning.
D5. heating_setpoint_floor / cooling_setpoint_ceiling (B5) apply to the operative-temperature setpoints of the ACCIS (all ComfStand and comfort modes). For the PMV-based setpoints (pmv_index) they are NOT applied (a PMV thermostat has no temperature setpoint); document it. — PENDIENTE: confirm. User response: confirmed.
D6. Regime priority in B2: the list order is the priority; the first regime whose condition holds wins; the last regime must be 'always' or accim appends one built from the scalar CustAST_* arguments.
D7. Outdoor metric range checks (B1): custom_alpha outside 0.6-0.9 and custom_days outside 7-30 raise a warning, not an error (ASHRAE 55-2020 §5.4.2.1 is the reference, EN 16798-1 recommends alpha 0.8).
D8. D1 tests: do not reproduce Table D.1 of CEN/TR 16798-2 (it needs a PMV calculation); test Method B weights (1, 2, 3 K) analytically and Method C with PPD values given as inputs; ppd_from_pmv tested against ISO 7730:2025 formula (5) at PMV 0 (5 %), ±0.5 (≈10.2 %), ±1 (≈26.1 %) — compute these with the formula, do not type them from memory.
D9. compute_setpoints (E1) reproduces the EnergyPlus running means (Engineering Reference §19.1: ASHRAE 55 = 30-day simple mean, CEN 15251 = 7-day exponential alpha 0.8, both from the EPW) and reads the Erl of get_setpoint_ems_code with accim.sim.ems.erl; the plotting function is optional (matplotlib already a dependency).
D10. Optional dependencies: pythermalcomfort only under an extra (accim[comfort]); never a hard dependency. pyproject.toml migration (E3) is not part of this session.
D11. B3 YAML files ship with the two examples of the v03 (JPN Aqilah 2025 FR; Qatar Indraganti & Boussaa 2018 HVAC) and the evidence block is mandatory in the schema.
D12. Anything about CIBSE TM52/TM59, the GB/T 50785 text or Boerstra 2015 is out of scope (documents not available): leave TODO entries, no code.
```

---

## 3. Qué pedirle propuesta a propuesta (ajustes a los prompts de la v03)

| Propuesta | Usar el prompt de la v03 con este ajuste |
|---|---|
| E1 `compute_setpoints` | Añadir: "Return also the outdoor-metric series needed by B1 (`outdoor_metrics`) so that AddAccis can initialise the Erl running means (decision D3)". |
| D2 columnas en `Table` | Los nombres reales de las salidas ya implementadas están en el CHANGELOG [Unreleased]: `ePMV_<zone>`, `Expectancy Factor_<zone>`, `Metabolic Correction Factor_<people>`, `Corrected Activity Level_<people>`, `PMV Heating/Cooling Setpoint_<zone>`; úsalos, no los de la v03. |
| E2 verificación | Idem: comprobar `ePMV = e·PMV` sólo con PMV > 0 (así está implementado), y la corrección metabólica con la tolerancia del 5.5–6.1 %. |
| B1 métrica exterior | Añadir D3 y D7; recordar que `Hour`/`Minute`/`DayOfYear` existen en ambos backends (verificado) y que `TrendVariable` está prohibido. |
| B5 suelo/techo | Añadir D5. |
| C1 parámetros | Sustituir en el prompt `clo`/`met` por `clothing_insulation`/`activity_level` y apoyarse en `get_available_params_epmv_setpoints()` como patrón reciente. |
| D1 largo plazo | Añadir D8. |
| A3 catálogo λ | Añadir D4. |
| B2 regímenes | Añadir D6. |
| B3 registro | Añadir D1 y D11; el número 23 queda reservado a B4. |
| B4 Aqilah | Añadir D1 y D2. |
| A4 ATHB, A6 | Sólo tras E1; requiere `accim[comfort]` (D10) y leer `help(ErlController)`. |

---

## 4. Lo que Copilot debe devolver al autor tras cada propuesta

1. Resumen de lo implementado y de las desviaciones respecto al prompt de la v03 (con motivo).
2. Lista de entradas nuevas en `TODO.md` y en `notes/questions.md`.
3. Resultado de `pytest` y de la comparación de backends (nombres de los tests, tiempo de simulación).
4. El commit propuesto (mensaje en el estilo `feat(sim): ... (B1)`), sin hacer push hasta que el autor lo apruebe.
