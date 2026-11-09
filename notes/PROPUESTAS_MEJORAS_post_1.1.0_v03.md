# accim — Propuestas de mejora y nuevas funciones (tras la 1.1.0) — v03

- v03 (2026-11-09): versión de máximo detalle para GitHub Copilot. Todas las ecuaciones, coeficientes, límites de aplicabilidad y nombres de objetos de EnergyPlus están **[verificado]** en la fuente que se cita (artículo, norma, IDD 25.2 o código de accim 1.1.0 / pythermalcomfort 4.8.1). No queda ninguna marca "verificar con texto completo". Documentos no disponibles: CIBSE TM52/TM59 y el texto de GB/T 50785-2012 (sus λ están tomados de Zhang, Yao & Li 2024, Tabla 1, que reproduce la norma); lo que dependía de ellos se marca **[no disponible]**.
- v02 (2026-11-08): coeficientes verificados en la biblioteca local. v01 (2026-11-08): propuesta inicial.
- Base de código: `D:\Python\accim`, rama `master`, `accim.__version__ == '1.1.0'`, commit `6ca8c69d`.
- Idioma: prosa en español; identificadores, firmas, Erl, pseudocódigo y los bloques "Prompt para Copilot" en inglés (idioma del código, de los docstrings y de `CHANGELOG.md`/`DEVLOG.md`/`TODO.md`/`ROADMAP.md`).

> Cómo leer las etiquetas: **[verificado: fuente, página/tabla/ecuación]** = leído en el documento o en el código; **[decisión de diseño]** = elección propuesta para accim, no un hecho de la literatura; **[no disponible]** = el documento no está en la biblioteca.

---

## 0. Cómo usar este documento con Copilot en PyCharm

1. Abre `D:\Python\accim` en PyCharm con GitHub Copilot Chat. Añade este archivo como contexto (`#file:notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`) y los archivos que cada propuesta enumera en "Archivos".
2. Pega primero la **cabecera común** (§10.3) y después el bloque "Prompt para Copilot" de la propuesta. Cada prompt pide código + tests + entrada en `CHANGELOG.md` (`## [Unreleased]`, estilo de la 1.1.0: `- **Nombre**: descripción en una o dos frases, con la sección de la documentación`) + nota en `DEVLOG.md`, que es la convención del repositorio (`ROADMAP.md` §"How to use this file", `TODO.md` §"Conventions").
3. Para las ecuaciones, remite a Copilot al **§11 (hoja de fórmulas)** y al **§12 (referencia de EnergyPlus)** de este documento: están pensados para copiarse en docstrings y en constantes.
4. Reglas que Copilot debe respetar (coherentes con la 1.1.0): PEP 8 y nombres en inglés; eppy para leer/escribir IDF (nunca besos); los programas Erl se generan con `accim.sim.ems` (`program_lines.py`, `setpoint_lines.py`, `objects.py`, `programs.py`, `inputs.py`, `erl.py`); ambos backends de `run_ep` (`'ems'` y `'api'`) deben dar CSV idénticos; toda función nueva con docstring reST (`:param:`/`:return:`), `__all__` actualizado, deprecaciones con `accim._deprecation`; tests con pytest en `tests/core` o `tests/parametric_and_optimisation`, con los IDF de `accim/sample_files`.
5. Prioridades según la propuesta del `TODO.md` (2026-10-31): `P0` bloqueante, `P1` siguiente release, `P2` mejora. Esfuerzo: S (< 1 día), M (1–3 días), L (> 3 días).

---

## 1. Estado de partida (1.1.0) **[verificado en el código]**

| Aspecto | Estado en 1.1.0 | Implicación |
|---|---|---|
| Catálogo de modelos | `accim/sim/standards.py`: dataclass `ComfortStandard(number, label, title, categories, comfort_modes)`; `COMFORT_STANDARDS` con ComfStand 0 (ESP CTE), 1 (INT EN16798), 2 (INT ASHRAE55), 3 (JPN Rijal), 4–5 (CHN GBT50785 Cold / HotMild), 6 (CHN Yang), 7–10 (IND IMAC C NV, C MM, R 7DRM, R 30DRM), 11 (IND Dhaka), 12 (ROM Udrea), 13–14 (AUS Williamson, DeDear), 15–16 (BRA Rupp NV, AC), 17–20 (MEX Oropeza Arid, DryTropic, Temperate, HumTropic), 21 (CHL Perez-Fargallo), 22 (INT ISO7730), 99 (CUSTOM). Sin registro externo. | B3 y B4 necesitan un registro extensible. |
| Temperatura exterior | `accim/sim/ems/objects.py::add_sensors` crea `RMOT` (*Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature*) y `PMOT` (*Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature*) sobre el primer `People` (`model.ems_keys[0]`). `program_lines.py::SET_COMF_TEMP`: `ComfStand 99 → set ComfTemp = PMOT*m+n`; `1 → RMOT*0.33+18.8`; `2 → PMOT*0.31+17.8`; `3 → PMOT*0.48+14.4`; `7 → PMOT*0.54+12.83`. | El CUSTOM no permite elegir métrica exterior ni α (B1). |
| aPMV | `accim/sim/apmv.py::apply_apmv_setpoints(building, output_frequencies, other_pmv_related_outputs, adaptive_coefficient_cooling=0.293, adaptive_coefficient_heating=-0.293, pmv_cooling_setpoint=0.5, pmv_heating_setpoint=-0.5, *_tolerance_*, cooling_season_start=121, cooling_season_end=274, default_*, verbose)`; argumentos `Union[float, dict]` por zona. Programas Erl por zona: `set_zone_input_data_<s>`, `apply_aPMV_<s>` (`PMV_sp = aPMV_sp/(1-λ·aPMV_sp)`, ±100 sin ocupación), `average_PMV_<s>` (media ponderada por ocupantes cuando hay varios `People`), `monitor_aPMV_<s>` (`aPMV = PMV/(1+λ·PMV)`), `count_aPMV_comfort_hours_<s>`. Funciones auxiliares públicas: `set_pmv_input_parameters` (clo, met, velocidad), `add_vrf_system`, `change_adaptive_coeff`, `set_zones_always_occupied`, `get_input_template_dictionary`, `generate_df_from_args`. | ePMV y los demás índices derivados del PMV encajan en esta infraestructura (A1, A2). |
| Backend API | `accim/sim/energyplus_api/runner.py::run_simulation(idf, epw, ..., before_programs: Sequence[Hook], after_programs: Sequence[Hook], ...)`, con `hook(controller, calling_point)` y `ErlController` para leer/escribir variables; `run_simulations()` en paralelo; `accim.sim.ems.erl` interpreta Erl con las reglas del EMS. No soporta `TrendVariable`, `CurveOrTableIndexVariable` ni `ConstructionIndexVariable` (R-05). | Índices calculados en Python (A4, A6), `compute_setpoints` sin EnergyPlus (E1); las métricas exteriores nuevas deben evitar `TrendVariable` (B1). |
| Paramétrico | `parameters.py`: 29 clases `Parameter` (ComfStand, CustAST_ACSTaul/ACSTall/AHSTaul/AHSTall/ASTaul/ASTall/m/n/ACSToffset/AHSToffset/ASToffset, CAT, CATcoolOffset, CATheatOffset, ComfMod, HVACmode, VentCtrl, VSToffset, MinOToffset, MaxWindSpeed, ASTtol, CoolSeasonStart, CoolSeasonEnd, SetpointAcc, MaxTempDiffVOF, MinTempDiffVOF, MultiplierVOF). `params_dicts.py` tiene `adaptive_coefficient(_cooling/_heating)`, `pmv_(cooling/heating_)setpoint`, pero ninguna clave para clo/met/velocidad. | C1. |
| Verificación y utilidades | `accim/utils/verification.py::verify_accim_simulation`; `accim.utils.print_setpoint_ems_code()`/`get_setpoint_ems_code()`; `accim.run.estimate_results_size()`. | E1, E2. |
| Dependencias | `setup.py` → `install_requires`: scikit-learn, eppy>=0.5.63, pycountry, geopy, matplotlib, numpy, pandas, openpyxl>=3.1.5, datapackage, unidecode, besos, pulp<4, SALib, seaborn. `accim/_besos_compat.py` parchea besos/dask/platypus. | C3, E3. |
| Tracking | `ROADMAP.md` R-01…R-05; `TODO.md` con P0–P2; `notes/` versionado; `llm_project_files/` ignorado por git. | Las iniciativas nuevas se numeran R-06… |

---

## 2. Mapa de propuestas

| ID | Título | Prioridad | Esfuerzo | Módulos | Depende de |
|---|---|---|---|---|---|
| A1 | ePMV (Fanger & Toftum 2002) como consigna | P1 | M | `sim/apmv.py`→`sim/pmv_index.py`, `sim/ems`, `parametric/funcs_for_besos/param_apmv.py`, GUI | A2 |
| A2 | Motor común de índices PMV-derivados | P1 | M | `sim/pmv_index.py` | — |
| A3 | Catálogo de λ del aPMV (Yao 2009, GB/T 50785, Zhang 2024) | P1 | S | `constants.py`, `sim/apmv.py`, GUI | — |
| A4 | ATHB (Schweiker 2022) vía backend API + pythermalcomfort | P2 | L | `sim/energyplus_api`, nuevo `sim/comfort_hooks.py` | pythermalcomfort opcional |
| A5 | Vestimenta dinámica (ASHRAE 55 / Schiavon & Lee 2013) y clo/met por estación | P1 | S–M | `sim/apmv.py::set_pmv_input_parameters`, `sim/people.py` | — |
| A6 | Consignas por SET* / PPD / cooling effect | P2 | L | `sim/energyplus_api`, `sim/ems` | A4 |
| B1 | Métrica exterior configurable en CUSTOM | P1 | M | `sim/ems/program_lines.py`, `objects.py`, `inputs.py`, `sim/arguments.py`, `utils` | — |
| B2 | CUSTOM con varios regímenes | P1 | L | `sim/arguments.py`, `sim/ems/setpoint_lines.py`, paramétrico | B1 |
| B3 | Registro de modelos de confort externos (YAML/Python) | P1 | L | `sim/standards.py`, `sim/ems/*`, GUI | B1, B2 |
| B4 | JPN Aqilah 2025 (viviendas, FR) como modelo nuevo | P2 | S | registro de B3 o `standards.py` + `program_lines.py` + `setpoint_lines.py` | — |
| B5 | Suelo sanitario de calefacción y techo de refrigeración | P1 | S | `sim/arguments.py`, `sim/ems/setpoint_lines.py` | — |
| C1 | Parámetros clo, met, v_air, e, λ, floor, métrica | P1 | S | `parametric/parameters.py`, `params_dicts.py`, `param_apmv.py` | A1, A5, B1, B5 |
| C2 | Objetivos de confort de largo plazo (EN 16798-2 Anexo D) | P2 | M | `parametric/objectives.py` | D1 |
| C3 | Desacoplar el paramétrico de besos (R-06) | P2 | L | `parametric/*`, `_besos_compat.py`, `setup.py` | E3 |
| D1 | Indicadores de disconfort de largo plazo en `Table` | P1 | M | `data/postprocessing/long_term_discomfort.py` | — |
| D2 | Columnas de los índices nuevos en `Table` | P1 | S | `data/postprocessing` | A1 |
| E1 | `compute_setpoints()` sin EnergyPlus | P1 | M | nuevo `sim/preview.py`, `sim/ems/erl.py` | — |
| E2 | `verify_accim_simulation` para los índices nuevos | P1 | S | `utils/verification.py` | A1, A2, B1 |
| E3 | `pyproject.toml`, extras, CI | P2 | M | raíz, `.github/workflows` | — |
| E4 | pyfwg / pyweatherfiles | P2 | S | `data/morphing.py` | — |

---
## 3. Bloque A — Índices de confort derivados del PMV

### A1. ePMV (PMV con factor de expectativa) como consigna

**Base científica [verificado: Fanger & Toftum 2002, *Energy and Buildings* 34(6) 533–536, pp. 534–535].**
- Definición: `ePMV = e · PMV`. El factor de expectativa `e` "se estima entre 1 y 0.5. Es 1 en edificios con aire acondicionado". Para edificios sin AC depende de la duración del periodo cálido y de cuántos edificios con AC hay en la región.
- Tabla 1 (rangos de `e`): expectativa **alta**, regiones donde los edificios con AC son comunes y el calor ocurre brevemente en verano, `e = 0.9–1.0`; **moderada**, algunos edificios con AC, calor en la estación de verano, `e = 0.7–0.9`; **baja**, pocos edificios con AC, calor en todas las estaciones, `e = 0.5–0.7`. Texto: "`e` puede ser 0.5 si el tiempo es cálido todo el año y hay pocos edificios con AC, y 0.7 si hay muchos; en regiones con calor sólo en verano y pocos edificios con AC, 0.7–0.8, y 0.8–0.9 si hay muchos; con periodos cálidos breves, 0.9–1".
- Corrección del metabolismo: "las tasas metabólicas registradas se redujeron un 6.7 % por cada unidad de la escala de PMV por encima de neutro, es decir, un PMV de 1.5 correspondió a una reducción del 10 %". Orden de cálculo (p. 535): (1) PMV con el met nominal; (2) `met_corr = met·(1 − 0.067·PMV)` si `PMV > 0`; (3) PMV recalculado con `met_corr`; (4) `ePMV = e · PMV_recalculado`. Así lo implementa `pythermalcomfort.models.pmv_e` **[verificado en el código 4.8.1]**: `met = where(pmv > 0, met·(1 + pmv·(−0.067)), met)`, PMV recalculado con ISO 7730:2025, `e_pmv = round(pmv·e, 2)`.
- Validación del artículo (Tabla 2): Bangkok `e = 0.6`, Singapur 0.7, Atenas 0.7, Brisbane 0.9; datos de la base de estudios de campo de de Dear (más de 3200 observaciones de edificios sin AC en verano, calidad ≥ II).
- Tabla 3 (límites de temperatura ajustados): con 1 met, 0.5 clo, 0.3 m/s y 70 % HR, el límite superior corresponde a `PMV_e = 0.5` (PPD 10 %) o `0.85` (PPD 20 %), es decir, a un PMV sin ajustar de `0.5/e` y `0.85/e`: `e = 1` → 27.9/28.7 °C; `e = 0.7` → 28.3/29.4 °C; `e = 0.5` → 29.0/30.5 °C. Texto literal: "It is only the upper temperature limit of the comfort zone that is affected by the expectancy factor, and no adjustment of the lower limit is expected."

**Consecuencias para el diseño [decisión de diseño].**
1. `e` sólo actúa sobre la consigna de refrigeración, y sólo cuando se espera calor (estación de refrigeración de accim). En la estación de calefacción `e = 1`.
2. La corrección metabólica es parte del índice: implementarla como opción (`metabolic_correction=True` por defecto para ser fiel al artículo), actuando sobre la schedule de actividad del `People`.
3. La inversión para el termostato de Fanger es lineal: `PMV_sp = ePMV_sp / e`.

**API.**
```python
def apply_epmv_setpoints(
        building: IDF,
        output_frequencies: Sequence[str] = ('hourly',),
        other_pmv_related_outputs: bool = True,
        expectancy_factor: Union[float, dict] = 0.8,          # Fanger & Toftum 2002, Table 1
        epmv_cooling_setpoint: Union[float, dict] = 0.5,       # target on the ePMV scale
        pmv_heating_setpoint: Union[float, dict] = -0.5,       # plain PMV; e does not apply (p. 535)
        metabolic_correction: Union[bool, dict] = True,        # 6.7 % per PMV unit above neutral
        cooling_setpoint_tolerance_cooling_season: Union[float, dict] = -0.1,
        cooling_setpoint_tolerance_heating_season: Union[float, dict] = -0.1,
        heating_setpoint_tolerance_cooling_season: Union[float, dict] = 0.1,
        heating_setpoint_tolerance_heating_season: Union[float, dict] = 0.1,
        cooling_season_start: Union[float, str] = 121,
        cooling_season_end: Union[float, str] = 274,
        default_expectancy_factor: float = 0.8,
        default_epmv_cooling_setpoint: float = 0.5,
        default_pmv_heating_setpoint: float = -0.5,
        verbose: bool = True,
) -> IDF: ...
```
Validación: `0.5 <= e <= 1.0` → `ValueError` fuera de rango (Fanger & Toftum 2002 no definen valores fuera de 0.5–1). Constantes en `accim/constants.py`:
```python
EPMV_EXPECTANCY_FACTORS = {  # Fanger & Toftum (2002), Table 1
    'high': (0.9, 1.0),      # AC buildings common; warm periods occurring briefly during the summer season
    'moderate': (0.7, 0.9),  # some AC buildings; warm summer season
    'low': (0.5, 0.7),       # few AC buildings; warm periods in all seasons
}
EPMV_CITY_EXAMPLES = {'Bangkok': 0.6, 'Singapore': 0.7, 'Athens': 0.7, 'Brisbane': 0.9}  # Table 2
EPMV_MET_REDUCTION_PER_PMV_UNIT = 0.067  # p. 534: 6.7 % per scale unit of PMV above neutral
```

**Erl por zona (sufijo `{s}`)** — reutiliza `COOLING_SEASON_LINES`, los sensores `PMV_{s}` y `People_Occupant_Count_{s}` y los actuadores `PMV_H_SP_act_{s}`/`PMV_C_SP_act_{s}` de `apply_apmv_setpoints`:
```
! set_zone_input_data_{s}
set expectancy_{s} = <e>
set epmv_cooling_sp_{s} = <ePMV_sp>
set pmv_heating_sp_{s} = <PMV_h_sp>
set met_nominal_{s} = <met from the Activity Level schedule, W/person>
set met_correction_{s} = <1 or 0>

! apply_ePMV_{s}
if CoolingSeason == 1
set e_{s} = expectancy_{s}
else
set e_{s} = 1
endif
set ePMV_C_SP_noTol_{s} = epmv_cooling_sp_{s}
set ePMV_C_SP_{s} = ePMV_C_SP_noTol_{s} + tolerance_cooling_sp_{s}
if People_Occupant_Count_{s} > 0
set PMV_C_SP_act_{s} = ePMV_C_SP_{s} / e_{s}           ! inverse of ePMV = e*PMV
set PMV_H_SP_act_{s} = pmv_heating_sp_{s} + tolerance_heating_sp_{s}
else
set PMV_H_SP_act_{s} = -100
set PMV_C_SP_act_{s} = 100
endif

! metabolic_correction_{s}  (only if met_correction_{s} == 1; actuator on the Activity Level schedule)
! PMV_prev_{s} is the PMV of the previous timestep (global variable written at the end of monitor_ePMV_{s});
! the article applies the correction to the PMV computed with the nominal met, so PMV_prev is computed
! with the nominal met by EnergyPlus only in the first timestep: document that the correction is applied with
! the PMV of the previous timestep (one-timestep lag) and that it reduces the met whose PMV is already corrected.
if (met_correction_{s} == 1) && (PMV_prev_{s} > 0)
set Activity_act_{s} = met_nominal_{s} * (1 - 0.067 * PMV_prev_{s})
else
set Activity_act_{s} = met_nominal_{s}
endif

! monitor_ePMV_{s}
set ePMV_{s} = e_{s} * PMV_{s}
set PMV_prev_{s} = PMV_{s}
```
Nota técnica sobre la corrección metabólica: el PMV que EnergyPlus calcula con el met reducido ya no es el PMV "nominal" del artículo, así que la secuencia (1)–(4) exacta sólo se reproduce con dos cálculos de PMV por paso. En Erl no hay función PMV; la alternativa exacta es el backend API (A4: calcular el PMV nominal con pythermalcomfort en el hook y derivar `met_corr`). Documentar ambas opciones: `metabolic_correction='lagged'` (Erl, aproximación de un paso) y `'exact'` (sólo con `backend='api'`).

**Salidas.** `EnergyManagementSystem:OutputVariable`: `ePMV_<zone>` (adimensional), `e_<zone>`, `Activity_corrected_<zone>` (W/persona); contadores `ePMV_comfort_hours_<zone>` (clon de `count_aPMV_comfort_hours`). Con `other_pmv_related_outputs=True`, las mismas salidas Fanger que en aPMV (*Zone Thermal Comfort Fanger Model PMV/PPD*, *Clothing Value*, *Control Fanger High/Low Setpoint PMV*; nombres en §12.2).

**Archivos.** `accim/sim/apmv.py` o `accim/sim/pmv_index.py` (A2); `accim/sim/__init__.py`; `accim/constants.py`; `accim/parametric_and_optimisation/funcs_for_besos/param_apmv.py` (función equivalente para BESOS); `params_dicts.py`; `accim/gui/forms.py` y `tasks.py`; `docs/source/4_detailed use.md` (sección nueva tras la de aPMV); cuaderno `docs/source/jupyter_notebooks/.../using_epmv_setpoints.ipynb`; `tests/core/test_epmv.py`.

**Tests.** (1) `e = 1`, sin corrección metabólica ⇒ consignas PMV idénticas a `apply_apmv_setpoints(λ = 0)`. (2) Inversión: `e = 0.7`, `ePMV_sp = 0.5` ⇒ `PMV_C_SP_act = 0.714285…`; `e = 0.5` ⇒ `1.0` (Tabla 3 del artículo). (3) Simulación de una semana de verano del IDF de ejemplo: `ePMV_zone == e·PMV_zone` en cada paso (|Δ| < 1e-6) y `PMV_zone <= ePMV_sp/e + tolerancia` en las horas ocupadas con refrigeración activa. (4) Con `metabolic_correction=True`, `Activity_corrected == met_nominal·(1 − 0.067·PMV_prev)` cuando `PMV_prev > 0`. (5) Backends `ems` y `api` dan el mismo CSV. (6) `ValueError` para `e = 0.4` y `e = 1.1`.

**Prompt para Copilot.**
```
Read accim/sim/apmv.py (apply_apmv_setpoints, _add_apmv_programs, _add_apmv_actuators, _add_apmv_outputs, set_pmv_input_parameters) and accim/sim/ems/erl.py. Implement apply_epmv_setpoints() following the ePMV index of Fanger & Toftum (2002): ePMV = e*PMV with 0.5 <= e <= 1.0, applied only to the cooling setpoint and only in the cooling season (e = 1 otherwise), because the article states that only the upper limit of the comfort zone is affected. Keep the per-zone argument convention (Union[float, dict] plus default_*), COOLING_SEASON_LINES, the Fanger dual-setpoint thermostat and the schedule actuators PMV_H_SP_<zone>/PMV_C_SP_<zone>. The Erl cooling setpoint is epmv_cooling_setpoint/e. Add the optional metabolic correction (met reduced by 6.7 % per PMV unit above neutral, using the PMV of the previous timestep) through an EMS actuator on the Activity Level schedule of each People object, and document the one-timestep lag. Add EMS output variables ePMV_<zone>, e_<zone>, Activity_corrected_<zone> and a comfort-hours counter. Put the constants EPMV_EXPECTANCY_FACTORS, EPMV_CITY_EXAMPLES and EPMV_MET_REDUCTION_PER_PMV_UNIT in accim/constants.py with the citation. Write tests/core/test_epmv.py (inverse formula, e=1 equals plain PMV control, metabolic correction values, API and EMS backends agree on a one-week summer run of a sample IDF, ValueError outside 0.5-1.0), export in accim/sim/__init__.py, document in docs/source/4_detailed use.md after apply_apmv_setpoints, and add CHANGELOG.md [Unreleased] and DEVLOG.md entries.
```

### A2. Motor común de índices PMV-derivados

**Motivación.** aPMV (existente), ePMV (A1) y el PMV puro con consignas por categoría (ISO 7730:2025 Tabla A.1 / EN 16798-1 Tabla B.1: I ±0.2, II ±0.5, III ±0.7, IV ±1.0 **[verificado]**) comparten toda la infraestructura (`_ensure_infrastructure`, `_create_tc_thermostat`, `_ensure_tc_control_schedule`, `_update_fanger_object`, sensores, actuadores, variables globales, `average_PMV`, contadores, salidas). Sólo cambian (a) las líneas Erl que convierten la consigna del índice en consigna PMV y (b) la línea del monitor.

**Diseño.**
```python
# accim/sim/pmv_index.py
@dataclass(frozen=True)
class PmvIndex:
    name: str                       # 'pmv', 'apmv', 'epmv'
    parameters: Tuple[str, ...]     # Erl input names, e.g. ('adap_coeff',) or ('expectancy',)
    def inverse_lines(self, sp_var: str, act_var: str, suffix: str, side: str) -> List[str]: ...
    def monitor_lines(self, suffix: str) -> List[str]: ...

PMV_INDEXES = {
    'pmv':  PmvIndex('pmv',  (), ...),                      # act = sp
    'apmv': PmvIndex('apmv', ('adap_coeff',), ...),         # act = sp/(1 - lambda*sp); monitor PMV/(1 + lambda*PMV)
    'epmv': PmvIndex('epmv', ('expectancy',), ...),         # cooling: act = sp/e; heating: act = sp; monitor e*PMV
}

def apply_pmv_index_setpoints(building, index: str, index_parameters: dict, **common_kwargs) -> IDF: ...
```
`apply_apmv_setpoints` y `apply_epmv_setpoints` pasan a ser envoltorios con la firma intacta; los nombres de los objetos EMS y el texto del IDF de salida de aPMV no cambian (test de regresión byte a byte con `accim/sample_files/sample IDFs/output_IDFs`). Añadir `CAMBIOS_CODIGO_v1.2.0.md` con el mismo formato que los de 1.0.0 y 1.1.0.

**Prompt para Copilot.**
```
Refactor accim/sim/apmv.py into a generic engine accim/sim/pmv_index.py: a frozen dataclass PmvIndex (name, Erl parameter names, inverse_lines(), monitor_lines()) and a registry PMV_INDEXES with 'pmv', 'apmv' (act = sp/(1 - lambda*sp), monitor PMV/(1 + lambda*PMV)) and 'epmv' (cooling act = sp/e in the cooling season, heating unchanged, monitor e*PMV). apply_pmv_index_setpoints(building, index, index_parameters, ...) shares _ensure_infrastructure, _create_tc_thermostat, sensors, actuators, PMV averaging and comfort-hour counters. Keep apply_apmv_setpoints() as a thin wrapper with the exact same signature, defaults, EMS object names and output IDF text, and add a regression test comparing the IDF produced before and after the refactor for every sample IDF. Add apply_epmv_setpoints() as a second wrapper. Write CAMBIOS_CODIGO_v1.2.0.md (Spanish, same structure as CAMBIOS_CODIGO_v1.1.0.md), update accim/sim/__init__.py, docs, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### A3. Catálogo de coeficientes adaptativos λ del aPMV

**Base científica.**
- Yao, Li & Liu (2009), *Building and Environment* 44, 2089–2096 **[verificado: §4 y Conclusiones]**: `aPMV = PMV/(1 + λ·PMV)`; en aulas en free-running de Chongqing, `λ = 0.293` en condiciones cálidas y `λ = −0.125` en frías; el ajuste es "muy bueno" en `−3 ≤ PMV ≤ 3`.
- GB/T 50785-2012 **[verificado vía Zhang, Yao & Li 2024, Tabla 1, "Values of λ for the five climate zones in different building types in Chinese National Standard GB/T 50785-2012"]**:

| Zona climática | Edificio | λ (PMV ≥ 0) | λ (PMV < 0) |
|---|---|---|---|
| Severe cold (SC) y Cold | Residencial, comercios, hoteles y oficinas | 0.24 | −0.50 |
| Severe cold (SC) y Cold | Educativos | 0.21 | −0.29 |
| Hot summer–cold winter (HSCW), hot summer–warm winter (HSWW) y Mild | Residencial, comercios, hoteles y oficinas | 0.21 | −0.49 |
| HSCW, HSWW y Mild | Educativos | 0.17 | −0.28 |

  Grados de la norma para edificios en free-running (Tabla 2 de Zhang 2024): I `−0.5 ≤ aPMV ≤ 0.5`; II `−1 ≤ aPMV < −0.5` o `0.5 < aPMV ≤ 1`; III `aPMV < −1` o `aPMV > 1`.
- Zhang, Yao & Li (2024), *Building and Environment* 256, 111481 **[verificado: §3, Tablas 4–7]**: 22 785 registros de edificios NV de la ASHRAE Global Thermal Comfort Database II en 14 zonas Köppen, con filtrado de atípicos por regla de caja; λ ajustado con su algoritmo (λN) y con el de Zhang et al. 2019 (λP). Tabla 6 (λN; λP), formato `PMV<0 / PMV>0`:

| Köppen | λN | λP |
|---|---|---|
| Af | 0.66 / 0.66 | 0.66 / 0.11 |
| Am | −0.66 / 0.46 | −0.66 / 0.15 |
| Aw | – / 0.36 | – / 0.21 |
| BSh | −0.56 / 0.66 | 0.15 / 0.51 |
| BSk | −0.66 / 0.09 | −0.66 / −0.32 |
| BWh | −0.66 / 0.34 | −0.54 / 0.21 |
| Cfa | 0.1 / 0.41 | 0.19 / 0.38 |
| Cfb | −0.41 / −0.23 | 0.22 / −0.46 |
| Csa | −0.66 / 0.29 | −0.53 / −0.4 |
| Csb | −0.25 / 0.55 | −0.26 / −0.66 |
| Csc | −0.66 / −0.66 | −0.66 / −0.66 |
| Cwb | −0.66 / 0.55 | −0.31 / 0.33 |
| Dfb | −0.66 / −0.66 | −0.66 / −0.66 |
| Dwa | −0.66 / −0.07 | −0.66 / −0.28 |
| Media de valores absolutos | 0.57 / 0.44 | 0.49 / 0.38 |

  Mejora de λN frente a λP (Tabla 7, edificios NV): MAE medio 0.55 → 0.36 (34.5 %), RMSE medio 0.69 → 0.43 (37.7 %). Código: `github.com/SuDBE/aPMV-calculation`. **Advertencia [decisión de diseño]:** muchos λN saturan en el límite ±0.66 del ajuste y varios signos contradicen el mecanismo adaptativo (λ < 0 con PMV > 0 en Cfb, Csc, Dfb, Dwa; λ > 0 con PMV < 0 en Af, Cfa). Incluirlos en el catálogo como `'literature'` con `warnings.warn` al usarlos; sólo Yao 2009 y GB/T 50785 como `'standard'`.
- Contexto adicional en la biblioteca (no leídos en detalle): Zhang, Cheng & Fang 2019 (*B&E* 163, 106318, algoritmo λP) y Zhang & Lin 2020 (*Indoor Air*, λ variable).

**Diseño.**
```python
# accim/constants.py
APMV_ADAPTIVE_COEFFICIENTS = {
    'yao2009_chongqing_classrooms': {'cooling': 0.293, 'heating': -0.125, 'grade': 'standard',
        'source': '10.1016/j.buildenv.2009.02.014', 'notes': 'Free-running classrooms, Chongqing'},
    'gbt50785_cold_general':        {'cooling': 0.24, 'heating': -0.50, 'grade': 'standard', 'source': 'GB/T 50785-2012 via 10.1016/j.buildenv.2024.111481 Table 1'},
    'gbt50785_cold_education':      {'cooling': 0.21, 'heating': -0.29, ...},
    'gbt50785_hscw_hsww_mild_general':   {'cooling': 0.21, 'heating': -0.49, ...},
    'gbt50785_hscw_hsww_mild_education': {'cooling': 0.17, 'heating': -0.28, ...},
    'zhang2024_Af': {'cooling': 0.66, 'heating': 0.66, 'grade': 'literature', 'source': '10.1016/j.buildenv.2024.111481 Table 6 (lambda_N)'},
    # ... one entry per Köppen row of Table 6; Aw has no PMV<0 value (None)
}
```
`apply_apmv_setpoints(adaptive_coefficient_cooling='gbt50785_cold_general')` acepta una clave además de un número (resolución en `generate_df_from_args`/`_resolve_targets`); cuando se da una clave, rellena los dos coeficientes a la vez salvo que el otro se dé explícitamente. Nueva función `accim.sim.apmv.get_adaptive_coefficients(key) -> dict` y, en la GUI, un desplegable con la fuente. Nota en la documentación: accim usa `adaptive_coefficient_cooling` en la estación de refrigeración y `_heating` en la de calefacción (por calendario), mientras que la norma china y Yao los definen por el signo del PMV; documentar la diferencia y ofrecer `adaptive_coefficient_by='season' | 'pmv_sign'` (la segunda opción: `if PMV_{s} >= 0 set adap_coeff = λ_warm else λ_cool`, seleccionando con el PMV del paso anterior para evitar circularidad).

**Prompt para Copilot.**
```
Add APMV_ADAPTIVE_COEFFICIENTS to accim/constants.py with the entries listed in the proposal (Yao 2009; GB/T 50785-2012 by climate zone and building type; Zhang, Yao & Li 2024 Table 6 lambda_N per Köppen zone, grade 'literature'), each with 'cooling', 'heating', 'grade', 'source' and 'notes'. Let apply_apmv_setpoints accept a key of that dict (str) in adaptive_coefficient_cooling/heating and resolve it in generate_df_from_args; warn when a 'literature' entry is used. Add get_adaptive_coefficients(key). Add the option adaptive_coefficient_by='season'|'pmv_sign' (the latter selects lambda by the sign of the PMV of the previous timestep in Erl). Update the GUI dropdown, docs, tests (resolution of keys, warning, pmv_sign Erl lines) and CHANGELOG.md [Unreleased]/DEVLOG.md.
```

### A4. ATHB (Adaptive Thermal Heat Balance) con el backend API

**Base científica.**
- Schweiker & Wagner (2015), *Building and Environment* 94, 252–262 **[verificado: ecs. 1–5, §4.1, Tablas 2–3]**. Marco: `CLO_behavioural = a + b·Trm` (ec. 1); `MET_physiological = (Trm − c)·d` (ec. 2); `MET_variable_psychological = (X − e)·f` (ec. 3); `MET_constant_psychological = g` (ec. 4); `MET_adapted = MET0 + Σ` (ec. 5). Coeficientes de laboratorio (LOBSTER, 2511 votos, 105 sujetos, Trm 14.1–26.4 °C): `a = 1.25`, `b = −0.030` (R² modelo completo 0.65); `d = −0.0178` met/K (pendiente de frecuencia cardiaca 0.193 × HRtoMET 0.092), `c = 18 °C` (inicio del verano en Karlsruhe; la reducción sólo se aplica en condiciones cálidas); psicológica −0.049 met por punto de control percibido. Entradas de referencia (Tabla 3): `MET0 = 1.1`, `CLO0 = 0.5`, HR 50 %, 0.15 m/s.
- Schweiker (2022), *Indoor Air* 32, e13018, "Combining adaptive and heat balance models for thermal sensation prediction: a new approach towards a theory and data-driven adaptive thermal heat balance (ATHB) approach" **[verificado: §3–4, Tablas 1–3 y tablas de validación]**. Datos: ASHRAE Global Thermal Comfort Database II, 57 084 registros tras limpieza; entrenamiento N = 34 250, test N = 11 417. Adaptación fisiológica (Tabla 1): `MET [W/m²] = 48.5 − 0.23·Trm` (R²adj 0.39; β = −0.63 ± 0.19 para BMR). Adaptación conductual: regresión de `log10(CLO)` (Tabla 2, modelo 3 `Trm * METad`, R²adj 0.134; modelos con tipo de edificio, estrategia de refrigeración y estación llegan a 0.43). Adaptación psicológica: nueva función de transferencia entre carga térmica `Lad` (calculada con el met ajustado) y TSV (Tabla 3, modelo 4 `Lad * Trm * METad`, R²adj 0.097). Validación en el test set: PMV sesgo 0.038, MAE 1.01, RMSE 1.30; ATHB_PMV sesgo −0.054, MAE 0.85, RMSE 1.14, TPR 0.43 frente a 0.33.
- Implementación de referencia **[verificado: código fuente de `pythermalcomfort.models.pmv_athb`, 4.8.1]**. Por su estructura, estos coeficientes corresponden a los modelos "Trm * METad" (clo, Tabla 2 n.º 3) y "Lad * Trm * METad" (TSV, Tabla 3 n.º 4) de Schweiker 2022 **[inferido: el PDF no imprime los coeficientes, que están en el material suplementario]**:
```python
met_adapted = met - (0.234 * t_running_mean) / 58.2                     # met units; 0.234 W/m2 per K
clo_adapted = 10 ** (-0.17168 - 0.000485 * t_running_mean
                     + 0.08176 * met_adapted - 0.00527 * t_running_mean * met_adapted)
pmv = pmv_ppd_optimized(tdb, tr, vr, rh, met_adapted, clo_adapted, wme=0)
ts = 0.303 * exp(-0.036 * met_adapted * 58.15) + 0.028                  # Fanger's transfer coefficient
l_adapted = pmv / ts                                                    # thermal load, W/m2
athb_pmv = (1.484 + 0.0276 * l_adapted - 0.9602 * met_adapted - 0.0342 * t_running_mean
            + 0.0002264 * l_adapted * t_running_mean + 0.018696 * met_adapted * t_running_mean
            - 0.0002909 * l_adapted * met_adapted * t_running_mean)
```
  `t_running_mean` es la media móvil exterior de EN 16798-1 (α = 0.8; §11.4). La firma es `pmv_athb(tdb, tr, vr, rh, met, t_running_mean, clo=False)`; con `clo` numérico se omite la adaptación conductual.

**Por qué no en Erl.** El ATHB necesita el PMV completo (iteración de `tcl`) con clo y met modificados cada paso; EnergyPlus sólo expone el PMV de los parámetros del `People`. El backend API de accim 1.0.0 (`run_simulation(after_programs=[hook])`) permite calcularlo en Python.

**Diseño.**
```python
# accim/sim/comfort_hooks.py  (requires accim[comfort] -> pythermalcomfort)
class AthbSetpointHook:
    """after_programs hook: computes the ATHB-PMV of each target with pythermalcomfort and actuates the
    operative-temperature setpoint schedules so that athb_pmv stays within [athb_heating_sp, athb_cooling_sp]."""
    def __init__(self, targets, athb_cooling_setpoint=0.5, athb_heating_setpoint=-0.5, met=1.1, air_speed=0.1,
                 clo='adaptive', running_mean_alpha=0.8, tolerance_k=0.1, max_iterations=20): ...
    def __call__(self, controller, calling_point): ...
```
Pasos por paso de tiempo y zona: leer `Zone Mean Air Temperature`, `Zone Mean Radiant Temperature`, `Zone Air Relative Humidity` (sensores que `apply_athb_setpoints` añade al IDF) y `RMOT`; resolver por bisección la temperatura operativa `Top*` tal que `pmv_athb(Top*, Top*, v, RH, met, RMOT) = athb_sp` (refrigeración y calefacción); escribir `ACST`/`AHST` en los actuadores de las schedules de consigna (los mismos que usa el ACCIS). `apply_athb_setpoints(building, ...)` prepara el IDF (termostato dual de temperatura operativa, schedules actuables, sensores, salidas `ATHB_PMV_<zone>`, `ATHB_clo_<zone>`, `ATHB_met_<zone>`) y devuelve el hook; `run_ep(backend='api', hooks=[hook])` lo conecta (añadir el argumento `hooks` a `run_ep`). Con `backend='ems'`: `NotImplementedError('ATHB setpoints need run_ep(backend="api")')`.

**Rendimiento.** ~10 evaluaciones de PMV por zona y paso (bisección a 0.1 K). Medir con el IDF de ejemplo; si hace falta, caché por `(round(Top, 1), round(RH), round(RMOT, 1))` o, mejor, tabla precalculada `Top*(RMOT, RH)` al inicio de cada día (RMOT constante dentro del día).

**Tests.** (1) `pmv_athb` de pythermalcomfort reproduce los valores del docstring del paquete. (2) Con `t_running_mean = 18`, `met = 1.1`: `clo_adapted` y `met_adapted` iguales a las fórmulas de arriba. (3) Simulación de una semana: `ATHB_PMV_zone` dentro de `[sp_h − tol, sp_c + tol]` en horas ocupadas con HVAC activo. (4) `backend='ems'` lanza `NotImplementedError`.

**Prompt para Copilot.**
```
Create accim/sim/comfort_hooks.py with AthbSetpointHook, an after_programs hook for accim.sim.energyplus_api.run_simulation that computes the ATHB-PMV of each target zone with pythermalcomfort.models.pmv_athb (lazy import; pythermalcomfort is the optional extra accim[comfort]) from the zone mean air temperature, mean radiant temperature, relative humidity, a given air speed and met, and the running mean outdoor temperature RMOT, and finds by bisection (0.1 K) the operative temperatures at which athb_pmv equals the heating and cooling ATHB setpoints, writing them to the setpoint schedule actuators used by the ACCIS. Add apply_athb_setpoints(building, ...) that prepares the IDF (operative temperature dual thermostat, actuated setpoint schedules, EMS sensors, output variables ATHB_PMV_<zone>, ATHB_clo_<zone>, ATHB_met_<zone>) and returns the hook; add a hooks argument to accim.run.run_ep that is only valid with backend='api' (NotImplementedError otherwise). Read help(ErlController) first and never guess its method names. Tests: formulas of met_adapted/clo_adapted, one-week run keeps ATHB_PMV within the setpoints, EMS backend raises. Document the ATHB equations (Schweiker 2022 as implemented in pythermalcomfort) in the docstring, update docs, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### A5. Vestimenta dinámica y clo/met por estación

**Base científica.**
- Schiavon & Lee (2013), *Building and Environment* 59, 250–260 **[verificado: resumen, §3.4, ecs. 4–7]**: 6333 observaciones seleccionadas de las 23 475 de ASHRAE RP-884 y RP-921; mediana de clo 0.59 (0.50 en verano, n = 3384; 0.69 en invierno, n = 2949); correlación del clo con la temperatura exterior (r = 0.45), la operativa interior (r = 0.3) y la HR (r = 0.26). Modelos mixtos (sin silla; añadir la silla si existe):
  - ec. (4) SI: `log10(clo) = −0.1635 − 0.0066·day06_ta` (R²adj 0.19 en la base);
  - ec. (5) SI: `log10(clo) = 0.2134 − 0.0165·top − 0.0063·day06_ta` (R²adj 0.22);
  - ecs. (6)–(7) IP: `log10(clo) = −0.0460 − 0.00367·day06_ta`; `log10(clo) = 0.6189 − 0.00916·top − 0.0035·day06_ta`.
  - Validez: `day06_ta` entre −27.2 y 26 °C; `top` entre 16.6 y 31.7 °C. `day06_ta` es la temperatura exterior medida a las 6:00.
- ASHRAE 55-2020 **[verificado: §5.2.2.2(g), Figura 5-1 y apéndice informativo p. 47]**: modelo por tramos de la Figura 5-1,

| `ta(out,6)` | `Icl` |
|---|---|
| < −5 °C | 1.00 clo |
| −5 ≤ ta(out,6) < 5 °C | `0.818 − 0.0364·ta(out,6)` |
| 5 ≤ ta(out,6) < 26 °C | `10^(−0.1635 − 0.0066·ta(out,6))` |
| ≥ 26 °C | 0.46 clo |

  "The model represented in Figure 5-1 is suited to be implemented in building performance simulation software or building control systems"; "based on field study and may not be appropriate for all cultures and occupancy types"; la norma no se aplica a ocupantes con más de 1.5 clo (§5.2.2.3). Ocupantes en movimiento (§5.2.2.2 e): `Icl,active = Icl·(0.6 + 0.4/M)` para 1.2 < M < 2.0 met.
- EnergyPlus 25.2 **[verificado: `Energy+.idd`, objeto `People`; Input Output Reference §1.14.2.1.16]**: campo *Clothing Insulation Calculation Method* con claves `ClothingInsulationSchedule` (por defecto), `DynamicClothingModelASHRAE55` ("the dynamic predictive clothing insulation model developed by Schiavon and Lee (2013) ... as a function of outdoor air temperature measured at 6am") y `CalculationMethodSchedule` (schedule con valor 1 = schedule, 2 = dinámico); campo siguiente *Clothing Insulation Calculation Method Schedule Name*; después *Clothing Insulation Schedule Name*. Salida *Zone Thermal Comfort Clothing Value*.
- EN 16798-1:2019 Tabla B.2 **[verificado]**: valores de diseño con ~1.0 clo en invierno y ~0.5 clo en verano, ~1.2 met sedentario; Tabla B.5 (cálculo de energía): HR ~40 % en calefacción y 60 % en refrigeración, v < 0.1 m/s.

**Diseño.**
```python
def set_pmv_input_parameters(building, clo=0.5, met=..., air_velocity=...):
    # clo accepts:
    #   float                      -> constant Schedule:Compact (current behaviour)
    #   'dynamic_ashrae55'         -> People.Clothing_Insulation_Calculation_Method = 'DynamicClothingModelASHRAE55'
    #   {'heating_season': 1.0, 'cooling_season': 0.5}  -> Schedule:Compact aligned with cooling_season_start/end
    #   callable(outdoor_metric: pd.Series) -> pd.Series   -> Schedule:File built from the EPW (needs E1), e.g. Schiavon eq. (4)
    # met accepts float or the season dict; air_velocity float or season dict.
```
Además `accim.sim.people.set_clothing_method(building, method, schedule_name=None)` y `accim.sim.people.dynamic_clothing_ashrae55(ta_out_6: ArrayLike) -> np.ndarray` (pura, para tests y para `compute_setpoints`). Nota de documentación: el modelo dinámico nativo de EnergyPlus usa la temperatura exterior a las 6:00 del archivo climático, no la media móvil; para clo en función de `RMOT` (ATHB, A4) usar el `callable`.

**Tests.** `dynamic_clothing_ashrae55([-10, 0, 10, 20, 30]) == [1.00, 0.818, 10**(-0.1635-0.066), 10**(-0.1635-0.132), 0.46]`; el `People` del IDF de ejemplo tiene el campo correcto; la schedule por estación vale 1.0 los días 120 y 275 y 0.5 los días 121 y 274 (con `cooling_season_start=121`, `cooling_season_end=274`).

**Prompt para Copilot.**
```
Extend accim.sim.apmv.set_pmv_input_parameters so that clo accepts a float, the string 'dynamic_ashrae55' (set the People field 'Clothing Insulation Calculation Method' to 'DynamicClothingModelASHRAE55' with eppy; verify the field name with building.idfobjects['People'][0].fieldnames), a dict {'heating_season': x, 'cooling_season': y} written as a Schedule:Compact aligned with cooling_season_start/end, or a callable that maps an outdoor-temperature pandas Series to clo values and is written as a Schedule:File from the EPW. Accept the season dict for met and air_velocity too. Add accim/sim/people.py functions set_clothing_method() and dynamic_clothing_ashrae55(ta_out_6) implementing the ASHRAE 55-2020 piecewise model (1.00 below -5 °C; 0.818 - 0.0364*t for -5..5; 10**(-0.1635 - 0.0066*t) for 5..26; 0.46 above 26). Tests for the pure function, the People fields and the schedule values on days 120, 121, 274 and 275. Document in docs/source/4_detailed use.md with the citations (Schiavon & Lee 2013 eq. 4; ASHRAE 55-2020 Figure 5-1), add CHANGELOG.md [Unreleased] and DEVLOG.md entries.
```

### A6. Consignas por SET*, PPD o cooling effect (P2)

**Base [verificado: Input Output Reference 25.2, variables de salida; ASHRAE 55-2020 definición de SET].** EnergyPlus publica *Zone Thermal Comfort Pierce Model Standard Effective Temperature*, *Pierce Model Effective Temperature PMV*, *Pierce Model Standard Effective Temperature PMV*, *Pierce Model Discomfort Index*, *Pierce Model Thermal Sensation Index*, *KSU Model Thermal Sensation Vote*, *Fanger Model PPD*, *ASHRAE 55 Elevated Air Speed Cooling Effect*, *... Cooling Effect Adjusted PMV/PPD* (modelo `CoolingEffectASH55` del `People`). SET: "temperatura de un ambiente imaginario a 50 % HR, < 0.1 m/s y tr = ta en el que la pérdida total de calor por la piel de un ocupante imaginario con 1.0 met y 0.6 clo es la misma que en el ambiente real".

**Diseño.** Dos vías. (a) Erl con control proporcional sobre la consigna de temperatura a partir del índice del paso anterior: `T_sp = T_sp_prev + k·(SET_target − SET_prev)` con saturación `[T_min, T_max]` y `k ≈ 0.8`; sencillo pero con retardo y posible oscilación (documentar). (b) Hook del backend API (como A4) con `pythermalcomfort.models.set_tmp` y bisección sobre la temperatura operativa: exacto. Categorías PPD de ISO 7730:2025 Tabla A.1 (I < 6 %, II < 10 %, III < 15 %, IV < 25 %) como consignas PPD → equivalentes a PMV ±0.2/0.5/0.7/1.0, por lo que la vía "PPD" se resuelve con A2 (`index='pmv'`, `category`). Prioridad baja hasta tener A4.

---

## 4. Bloque B — Modelo CUSTOM y modelos regionales

### B1. Métrica exterior configurable en el modelo CUSTOM

**Base científica.**
- EN 16798-1:2019 Anexo B **[verificado: B.2.2, fórmulas B.1–B.3, p. 47–49]**: `Θrm = (1 − α)·{Θed−1 + α·Θed−2 + α²·Θed−3 + …}` (B.1), con `Θed−i` la media diaria exterior del día `i` anterior y `α` "constante entre 0 y 1 (valor recomendado 0.8)". Fórmula aproximada cuando no hay registros (B.2): `Θrm = (Θed−1 + 0.8·Θed−2 + 0.6·Θed−3 + 0.5·Θed−4 + 0.4·Θed−5 + 0.3·Θed−6 + 0.2·Θed−7)/3.8`. Temperatura de confort (B.3): `Θc = 0.33·Θrm + 18.8`. Límites: I `+2/−3`, II `+3/−4`, III `+4/−5` K (asimétricos: el inferior es 1 K más ancho). "The limits only apply when 10 < Θrm < 30 °C". Aplicabilidad (B.2.2): oficinas y edificios similares (p. ej. residenciales) con ocupación sedentaria, acceso fácil a ventanas practicables y libertad de vestimenta; en verano y entretiempo se aplican los límites adaptativos; **en invierno se aplican los límites de la Tabla B.2** (edificios con refrigeración mecánica). Corrección por velocidad de aire bajo control personal (Tabla B.4, Θo > 25 °C): +1.2 K a 0.6 m/s, +1.8 K a 0.9 m/s, +2.2 K a 1.2 m/s.
- ASHRAE 55-2020 **[verificado: §5.4.1, §5.4.2.1 y definiciones]**: la *prevailing mean outdoor air temperature* se basa en no menos de 7 y no más de 30 días secuenciales anteriores, media aritmética simple de las medias diarias; excepción: ponderación decreciente en la que el peso de un día está entre 0.6 y 0.9 del peso del día siguiente, sin límite superior de días. Aplicabilidad del modelo adaptativo (§5.4.1): sin refrigeración ni calefacción mecánica en funcionamiento, 1.0–1.5 met, libertad de vestimenta al menos 0.5–1.0 clo, prevailing mean > 10 °C y < 33.5 °C.
- ATG neerlandesa **[verificado: van der Linden et al. 2006, *E&B* 38, 8–17, §3]**: `Te,ref = (1·T_hoy + 0.8·T_ayer + 0.4·T_−2 + 0.2·T_−3)/2.4`, donde cada `T` es **la media de la máxima y la mínima del día** ("calculated from the averages of the maximum and minimum outdoor (air) temperature of the day under study and the three preceding days"). Alpha adopta los límites de Beta por debajo de `Te,ref` 10–12 °C (calefacción en marcha).
- IMAC-R (Aqilah 2025, Tabla 1, citando a Rawal et al.) **[verificado]**: `Tc = 0.39·Tout-7DRM + 18.4` (90 % ±2.15, 80 % ±3.60) y `Tc = 0.42·Tout-30DRM + 17.6`; accim ya tiene ComfStand 9 y 10 con 7DRM/30DRM.
- Aqilah 2025 (Tabla 6) **[verificado]**: la correlación de Tc con Trm apenas cambia con α entre 0.33 y 0.94 (R² 0.63–0.67) y cae a 0.16 con α = 0.99; usan α = 0.8 con la media móvil iniciada una semana antes.
- EnergyPlus **[verificado: `objects.py`]**: `RMOT` y `PMOT` son sensores de las variables de salida del modelo adaptativo CEN 15251 y ASHRAE 55, con la media que EnergyPlus calcula internamente (sin control de α ni de días por parte de accim).

**Diseño.**
- Argumento `custom_outdoor_metric` (clave `CustAST_metric` en `AddAccis.arguments`, por defecto `'pmot'` = comportamiento actual) con valores:

| Valor | Definición | Implementación |
|---|---|---|
| `'pmot'` | sensor ASHRAE 55 nativo | actual |
| `'rmot'` | sensor CEN 15251 nativo (α de EnergyPlus) | actual |
| `'rmot_alpha'` + `custom_alpha` (0.6–0.9; aviso fuera) | EN 16798-1 B.1 con α libre | Erl recursivo diario |
| `'rmot_7day'` | EN 16798-1 B.2 (pesos 1, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2 / 3.8) | Erl con 7 medias diarias |
| `'daily_mean'` | media de las 24 h del día anterior | Erl |
| `'ndrm'` + `custom_days` (7–30) | media aritmética de los `n` días anteriores (ASHRAE 55 §5.4.2.1) | Erl con anillo de `n` valores |
| `'monthly_mean'` | media mensual del EPW | 12 constantes calculadas en Python al generar el IDF |
| `'te_ref_nl'` | ATG con medias de máx./mín. diarias | Erl con `@Max`/`@Min` diarios |

- Erl sin `TrendVariable` (compatible con el backend API). Programa `SetOutdoorMetric` con calling point `BeginTimestepBeforePredictor` y variables globales persistentes; sensor `Tout` = *Site Outdoor Air Drybulb Temperature*:
```
! accumulate the day
if (Hour == 0) && (Minute == ZoneTimeStep*60)       ! first timestep of the day: close yesterday
set Tday_7 = Tday_6
set Tday_6 = Tday_5
...
set Tday_2 = Tday_1
set Tday_1 = Tsum / Hsum                            ! daily mean of yesterday
set Tmid_1 = (Tmax_day + Tmin_day) / 2             ! for te_ref_nl
set RMOTa = (1 - alpha) * Tday_1 + alpha * RMOTa     ! EN 16798-1 (B.1) in recursive form
set Tsum = 0
set Hsum = 0
set Tmax_day = -100
set Tmin_day = 100
endif
set Tsum = Tsum + Tout * ZoneTimeStep
set Hsum = Hsum + ZoneTimeStep
set Tmax_day = @Max Tmax_day Tout
set Tmin_day = @Min Tmin_day Tout
! select the metric
if CustAST_metric == 2          ! rmot_alpha
set Tout_metric = RMOTa
elseif CustAST_metric == 3      ! rmot_7day, EN 16798-1 (B.2)
set Tout_metric = (Tday_1 + 0.8*Tday_2 + 0.6*Tday_3 + 0.5*Tday_4 + 0.4*Tday_5 + 0.3*Tday_6 + 0.2*Tday_7) / 3.8
elseif CustAST_metric == 7      ! te_ref_nl (van der Linden 2006)
set Tout_metric = (1*Tmid_0 + 0.8*Tmid_1 + 0.4*Tmid_2 + 0.2*Tmid_3) / 2.4   ! Tmid_0 = running (max+min)/2 of today
...
endif
```
  Arranque: en `BeginNewEnvironment` inicializar `RMOTa` y `Tday_i` con el valor de `PMOT` del primer paso (o con las medias calculadas en Python desde el EPW y escritas en `SetInputData`, que es lo que hace `compute_setpoints`, E1, y evita el transitorio). Documentar que las medias mensuales atan el IDF al EPW.
- `SET_COMF_TEMP` para ComfStand 99: `set ComfTemp = Tout_metric*m+n`; `SetAppLimits` y `COUNT_HOURS` comparan con `Tout_metric` en lugar de `PMOT` cuando `ComfStand == 99`.
- Salida `Output:Variable` EMS `Tout_metric` (°C) para verificarla en `Table`; `print_setpoint_ems_code`/`get_setpoint_ems_code` muestran el programa `SetOutdoorMetric`; GUI con desplegable; `verify_accim_simulation` recalcula la métrica desde el CSV de `Tout` (E2).

**Tests.** `rmot_alpha` con α = 0.8 frente al sensor `RMOT` nativo: |Δ| < 0.05 K tras 14 días; `rmot_7day` y `ndrm(7)` frente a pandas sobre el EPW (`rolling(7).mean()` desplazado un día); `te_ref_nl` frente a cálculo con `resample('D').agg(['max','min'])`; backends `ems` y `api` idénticos; `custom_alpha = 0.95` emite aviso.

**Prompt para Copilot.**
```
In accim/sim (arguments.py, ems/program_lines.py, ems/objects.py, ems/inputs.py, accis.py) add the argument custom_outdoor_metric (key 'CustAST_metric', default 'pmot' = current behaviour) for ComfStand 99, with 'pmot', 'rmot', 'rmot_alpha' (+ custom_alpha, warn outside 0.6-0.9 per ASHRAE 55-2020 §5.4.2.1), 'rmot_7day' (EN 16798-1 formula B.2, weights 1, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2 divided by 3.8), 'daily_mean', 'ndrm' (+ custom_days 7-30, arithmetic mean), 'monthly_mean' (12 constants computed from the EPW given to AddAccis) and 'te_ref_nl' ((T0 + 0.8*T-1 + 0.4*T-2 + 0.2*T-3)/2.4 with T = mean of the daily maximum and minimum, van der Linden 2006). Implement the running means in a new Erl program SetOutdoorMetric without EnergyManagementSystem:TrendVariable (the API backend does not support it): accumulate the daily mean, max and min of the Site Outdoor Air Drybulb Temperature sensor and update the metric at the first timestep of each day; initialise at BeginNewEnvironment. SetComfTemp, SetAppLimits and COUNT_HOURS for ComfStand 99 must use the new global variable Tout_metric, which is also an EMS output variable. Update print_setpoint_ems_code/get_setpoint_ems_code, the GUI form, verify_accim_simulation, docs/source/4_detailed use.md, and add tests comparing rmot_alpha(0.8) with the native RMOT sensor after 14 days, rmot_7day/ndrm with pandas on the EPW, te_ref_nl with daily max/min means, and EMS vs API backends. Add CHANGELOG.md [Unreleased] and DEVLOG.md entries.
```

### B2. CUSTOM con varios regímenes (ecuaciones condicionadas)

**Motivación [verificado en la literatura leída].** Muchos modelos no son una sola recta: EN 16798-1 cambia a límites fijos en invierno (B.2.2) y sus bandas son asimétricas; la ATG usa los límites Beta bajo `Te,ref` 10–12 °C; GB/T 50785 tiene coeficientes por zona climática; IMAC-C distingue NV y MM (ComfStand 7 y 8); Aqilah 2025 define el modelo sólo en FR; Indraganti & Boussaa 2018 (Tabla 10) listan modelos HVAC, MM y FR con pendientes distintas. En 1.1.0 el CUSTOM tiene una recta (`CustAST_m`, `CustAST_n`), dos offsets (`CustAST_ACSToffset`, `CustAST_AHSToffset`) y cuatro límites (`CustAST_ACSTall/aul`, `CustAST_AHSTall/aul`).

**Diseño.**
```python
# accim/sim/arguments.py
@dataclass(frozen=True)
class CustomRegime:
    slope: float
    intercept: float
    cooling_offset: float
    heating_offset: float
    cooling_lower_limit: float
    cooling_upper_limit: float
    heating_lower_limit: float
    heating_upper_limit: float
    condition: Union[str, Tuple[str, float]] = 'always'
    # 'always' | 'cooling_season' | 'heating_season' | 'hvac_off' | 'hvac_on'
    # | ('metric_below', x) | ('metric_above', x) | ('metric_between', (x1, x2))
    outdoor_metric: Optional[str] = None     # overrides custom_outdoor_metric for this regime (B1)
```
`AddAccis(custom_regimes=[CustomRegime(...), ...])`; en Erl, una cadena `if/elseif` en un programa nuevo `SelectCustomRegime` escribe `m`, `n`, `ACSToffset`, `AHSToffset`, `ACSTall`, `ACSTaul`, `AHSTall`, `AHSTaul` en las variables que ya existen, de modo que `SetComfTemp`, `SetAppLimits`, `ApplyCAT` y `SetAST_CS99_*` no cambian. El orden de la lista es la prioridad (el primer régimen cuya condición se cumple gana); el último debe ser `'always'` o accim añade uno con los `CustAST_*` escalares. `hvac_off`/`hvac_on` se evalúan con el sensor del modo mixto ya existente (`vrf_mm`/`ex_mm`); en modelos sin modo mixto, `ValueError`. Compatibilidad total: los argumentos escalares siguen funcionando (un régimen `'always'`). Paramétrico: fábrica `custom_regime_parameters(n_regimes)` que genera clases `CustAST_m_1`, `CustAST_n_1`, … (C1).

**Prompt para Copilot.**
```
Add a frozen dataclass CustomRegime to accim/sim/arguments.py (slope, intercept, cooling/heating offsets, four applicability limits, condition in {'always','cooling_season','heating_season','hvac_off','hvac_on',('metric_below',x),('metric_above',x),('metric_between',(x1,x2))}, optional outdoor_metric) and the AddAccis argument custom_regimes (list). Generate an Erl program SelectCustomRegime that assigns m, n, ACSToffset, AHSToffset, ACSTall, ACSTaul, AHSTall and AHSTaul from the first regime whose condition holds (if/elseif chain, last regime 'always'), so that SetComfTemp, SetAppLimits, ApplyCAT and the ComfStand 99 setpoint lines do not change. Keep the scalar CustAST_* arguments working as a single 'always' regime (regression test: identical output IDF). Raise ValueError for hvac_on/hvac_off in models that are not mixed mode. Add a factory custom_regime_parameters(n) in accim/parametric_and_optimisation/parameters.py. Tests with two regimes (metric_below 10 vs always) checking the Erl text and a one-week simulation. Update print_setpoint_ems_code, docs, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### B3. Registro de modelos de confort externos (plugins YAML/Python)

**Motivación.** Añadir un modelo nacional hoy exige tocar `standards.py`, `program_lines.py` (`SET_COMF_TEMP`, límites, `COUNT_HOURS`), `setpoint_lines.py`, la GUI y publicar una versión. El proyecto de modelos regionales necesita distribuir modelos como archivos y que `print_setpoint_ems_code` y `compute_setpoints` (E1) los entiendan.

**Diseño.**
```python
# accim/sim/standards.py
@dataclass(frozen=True)
class ComfortStandardDefinition:
    standard: ComfortStandard                     # number >= 100, label, title, categories, comfort_modes
    outdoor_metric: str                           # B1 values
    regimes: Tuple[CustomRegime, ...]             # B2; one regime for a single line
    category_offsets: Dict[Number, Tuple[float, float]]   # CAT -> (cooling_offset, heating_offset); asymmetric allowed
    static_setpoints: Optional[Tuple[float, float]] = None # (heating, cooling) used by comfort modes 0 and 1
    evidence: Dict[str, Any] = field(default_factory=dict) # N, R2, SE, metric range, building type, mode
    citation: str = ''

def register_comfort_standard(definition: ComfortStandardDefinition) -> None: ...
def load_comfort_standards(path: PathLike) -> List[ComfortStandardDefinition]: ...   # YAML, one or many files
```
Esquema YAML (ejemplo real, datos **[verificado: Aqilah et al. 2025, ec. 8, §3.4.2, Conclusiones 5–6]**; ver B4):
```yaml
number: 101
label: JPN Aqilah2025 FR
title: 101 = JPN Aqilah 2025 (dwellings, free-running)
citation: "Aqilah, Rijal, Yoshida & Nicol (2025) Energy & Buildings 335, 115469, doi:10.1016/j.enbuild.2025.115469"
outdoor_metric: rmot_alpha
alpha: 0.8
comfort_temperature: {slope: 0.38, intercept: 16.9}
applicability: {metric_min: 5.0, metric_max: 30.0}
categories:
  90: {cooling_offset: 1.5, heating_offset: -1.5, description: "90 % comfort band"}
  80: {cooling_offset: 2.0, heating_offset: -2.0, description: "80 % comfort band"}
comfort_modes: [0, 1, 2, 3]
static_setpoints: {heating: 20.0, cooling: 28.0}   # user choice; the paper gives no static values
evidence: {N: 11566, R2: 0.67, SE: 0.003, p: "<0.001", houses: 64, votes_total: 32988, mode: FR,
           within_band: {90: 0.66, 80: 0.79}, comfort_temperature_range: [14.5, 30.0]}
```
Los generadores Erl recorren el registro para `number >= 100`; los 24 modelos actuales siguen definidos en código (regresión byte a byte). `print_setpoint_ems_code` imprime también el bloque `evidence`. GUI: lista desde el registro. Segundo ejemplo real para `accim/sample_files/comfort_standards/`: Qatar **[verificado: Indraganti & Boussaa 2018, *E&B*, ec. 5 y Tabla 10]**, oficinas con HVAC, `Tc = 0.049·Tr + 22.5` (N = 3742, R² = 0.015, p < 0.001, SE = 0.007; `Tr` media móvil exterior con media 30.7 °C, SD 6.4; temperatura de confort media 24.0 °C) — su R² casi nulo es precisamente el caso de uso del campo `evidence`. La misma Tabla 10: Rijal et al. (Japón, calefacción y refrigeración) `Tc = 0.065·Tr + 23.9`; Manu et al. (India, MM) `Tn = 0.28·Tr + 17.87`; Indraganti et al. (India) `Tc = 0.15·Tr + 22.1`.

**Prompt para Copilot.**
```
Design a plugin registry for comfort standards in accim/sim/standards.py: ComfortStandardDefinition (standard, outdoor_metric, regimes, category_offsets with asymmetric offsets, static_setpoints, evidence, citation), register_comfort_standard() and load_comfort_standards(yaml_path) with the YAML schema given in the proposal (validate with a clear error message). Make accim/sim/ems/program_lines.py (SET_COMF_TEMP, SET_APP_LIMITS, APPLY_CAT, COUNT_HOURS) and setpoint_lines.py build their Erl from the registry for numbers >= 100 while the built-in standards 0-22 and 99 keep their literal lines (regression test: byte-identical output IDFs for the sample models). Ship accim/sample_files/comfort_standards/jpn_aqilah2025_fr.yaml and qat_indraganti2018_hvac.yaml with the data of the proposal, a how-to notebook, GUI lists read from the registry, print_setpoint_ems_code printing the evidence block, docs, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### B4. Modelo JPN Aqilah 2025 (viviendas, free-running)

**Base científica [verificado: Aqilah, Rijal, Yoshida & Nicol 2025, *Energy & Buildings* 335, 115469, CC BY-NC].**
- Campo: 64 viviendas, 2 años, 32 988 votos; método de Griffiths para `Tc`; `Tc` media mensual de 19 °C (enero) a 27 °C (septiembre); sensación media 4.0 (FR), 3.7 (HT), 4.2 (CL) en escala 1–7.
- Modelo adaptativo (modo FR, ec. 8): `Tc = 0.38·Trm + 16.9` (N = 11 566, R² = 0.67, SE = 0.003, p < 0.001). `Trm` según McCartney & Nicol (ec. 7): `Trm = α·Trm−1 + (1 − α)·Tod−1` con α = 0.8, media móvil iniciada una semana antes del día de encuesta (texto de la ec. 7 tal como está impreso: `Trm = Trm−1 + (1 − α)Tod−1`, es la forma recursiva estándar). Aplicable a `Trm` de ~5 a 30 °C; `Tc` resultante 14.5–30 °C.
- Banda de confort (Conclusiones 5–6): **±1.5 K (90 %) y ±2.0 K (80 %)**, obtenida con regresión cuadrática y probit sobre `ΔT = Tin − Tc` (ec. 5: `Pcomf = −0.05·ΔT² + 0.003·ΔT − 1.0`, N = 21 502, R² = 0.8); 79 % de los puntos dentro de ±2.0 K y 66 % dentro de ±1.5 K.
- Comparación de pendientes (texto): 0.38 frente a ASHRAE 0.31, EN 15251 0.33, Williamson & Daniel 0.26, Indraganti 0.26; Rijal et al. 2019 (misma base, otro periodo) 0.48; IMAC-R 0.42. La Tabla 1 del artículo recoge el modelo japonés anterior (Rijal et al.; ComfStand 3 de accim): `Tc = 0.48·Tpma + 14.4` con bandas 90 % ±2.5 y 80 % ±3.5 "−ASHRAE" (es decir, tomadas de ASHRAE 55, no propias).

**Decisión de diseño.** No cambiar ComfStand 3 (resultados publicados). Añadir el modelo nuevo como ComfStand 23 (`JPN Aqilah2025`) o, con B3, como YAML `jpn_aqilah2025_fr.yaml` (ver B3). Diferencias respecto a ComfStand 3 que deben quedar en la documentación: métrica `Trm` (α = 0.8) en lugar de `PMOT`; pendiente 0.38/16.9 en lugar de 0.48/14.4; bandas ±1.5/±2.0 propias en lugar de ±2.5/±3.5 de ASHRAE; aplicabilidad 5–30 °C; modo FR (viviendas). Consignas estáticas fuera de aplicabilidad (ComfMod 1): el artículo no las da; proponer 20/28 °C como valores de usuario y dejarlos configurables.

### B5. Suelo sanitario de calefacción y techo de refrigeración

**Motivación.** EN 16798-1 Tabla B.2 **[verificado]** fija mínimos de calefacción por categoría (viviendas: I 21.0, II 20.0, III 18.0, IV 16.0 °C; oficinas: I 21.0, II 20.0, III 19.0, IV 18.0 °C) y máximos de refrigeración (25.5/26.0/27.0/28.0 °C), y B.2.2 obliga a usar esos límites en invierno aunque el edificio sea adaptativo. En accim el único freno inferior es `AHSTall` (límite de aplicabilidad), que cambia de ecuación (ComfMod 1/2/3) en vez de acotar la consigna.

**Diseño.** Argumentos `heating_setpoint_floor` (clave `AHSTfloor`) y `cooling_setpoint_ceiling` (`ACSTceil`), por defecto `None`, aplicados al final de `SetAST` antes de `ROUNDING`: `if AHST < AHSTfloor; set AHST = AHSTfloor; endif` y `if ACST > ACSTceil; set ACST = ACSTceil; endif`; válidos para todos los ComfStand y modos. Constantes de ayuda `EN16798_TABLE_B2 = {('residential', 1): (21.0, 25.5), ('residential', 2): (20.0, 26.0), ('residential', 3): (18.0, 27.0), ('residential', 4): (16.0, 28.0), ('office', 1): (21.0, 25.5), ('office', 2): (20.0, 26.0), ('office', 3): (19.0, 27.0), ('office', 4): (18.0, 28.0)}`. Contadores opcionales `report_hours_below=[18, 17, 16]` → variables `HoursBelow_18_<zone>` etc. en `COUNT_HOURS` (o en `Table`, D1). Parámetro del paramétrico (C1).

**Prompt para Copilot.**
```
Add the AddAccis arguments heating_setpoint_floor (key 'AHSTfloor') and cooling_setpoint_ceiling (key 'ACSTceil'), default None, applied for every comfort standard and comfort mode as the last lines of SetAST before ROUNDING (if AHST < AHSTfloor set AHST = AHSTfloor; if ACST > ACSTceil set ACST = ACSTceil). Add EN16798_TABLE_B2 to accim/constants.py with the heating minimum and cooling maximum per building type and category (residential I-IV: 21.0/25.5, 20.0/26.0, 18.0/27.0, 16.0/28.0; office I-IV: 21.0/25.5, 20.0/26.0, 19.0/27.0, 18.0/28.0; EN 16798-1:2019 Table B.2) and the optional report_hours_below list that adds HoursBelow_<T>_<zone> counters. Parametric Parameter classes HeatingSetpointFloor and CoolingSetpointCeiling. Tests: setpoints never below/above the floor/ceiling in a winter and a summer week, counters sum to the occupied hours below each threshold. Update print_setpoint_ems_code, GUI, docs, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

---

## 5. Bloque C — Paramétrico y optimización

### C1. Parámetros personales y de los índices nuevos

**Estado [verificado]:** 29 clases `Parameter` en `parameters.py`; `params_dicts.py` ya tiene las claves `adaptive_coefficient(_cooling/_heating)`, `pmv_(cooling/heating_)setpoint`, `setpoint_tolerance`, `cooling_season_start/end`, pero ninguna para clo, met o velocidad del aire; `funcs_for_besos/param_apmv.py` replica `apply_apmv_setpoints` para BESOS.

**Diseño.** Nuevas clases (mismo patrón que las existentes, `modify()` sobre el modelo eppy):

| Clase | Acción | Rango sugerido |
|---|---|---|
| `Clo` | `set_pmv_input_parameters(clo=x)` | 0.3–1.5 (ASHRAE 55 no se aplica > 1.5 clo) |
| `Met` | `set_pmv_input_parameters(met=x)` | 0.8–4 met (ISO 7730:2025 §4: 46–232 W/m²) |
| `AirVelocity` | `set_pmv_input_parameters(air_velocity=x)` | 0–1 m/s (ISO 7730:2025 §4) |
| `ExpectancyFactor` | A1 | 0.5–1.0 |
| `AdaptiveCoefficientCooling/Heating` | aPMV (comprobar si ya existe clase; las claves existen en `params_dicts`) | −0.7–0.7 |
| `HeatingSetpointFloor`, `CoolingSetpointCeiling` | B5 | 16–21 / 25.5–28 °C |
| `CustAST_metric`, `CustAST_alpha`, `CustAST_days` | B1 | categórico; 0.6–0.9; 7–30 |
| `custom_regime_parameters(n)` | B2 | fábrica |

Actualizar `get_available_params_apmv_setpoints()` y `get_available_params_accim_custom_models()`, los planes de `sampling_full_set()` y la documentación `parametric_and_optimisation.rst`. Rangos de validez del PMV para avisos: ISO 7730:2025 §4 **[verificado]**: PMV sólo entre −2 y +2; M 46–232 W/m² (0.8–4 met); Icl 0–0.310 m²·K/W (0–2 clo); ta 10–30 °C; tr 10–40 °C; var 0–1 m/s; pa 0–2700 Pa.

**Prompt para Copilot.**
```
In accim/parametric_and_optimisation/parameters.py add Parameter subclasses Clo, Met, AirVelocity (they call accim.sim.apmv.set_pmv_input_parameters on the model), ExpectancyFactor (apply_epmv_setpoints), HeatingSetpointFloor, CoolingSetpointCeiling, CustAST_metric, CustAST_alpha and CustAST_days, following the pattern of the existing classes and of funcs_for_besos/param_apmv.py; validate ranges with warnings (ISO 7730:2025 §4: 0.8-4 met, 0-2 clo, 0-1 m/s; ASHRAE 55: clo <= 1.5). Register them in params_dicts.py and in get_available_params_apmv_setpoints()/get_available_params_accim_custom_models(). Tests in tests/parametric_and_optimisation build a two-point design for Clo and check the clo schedule value in the generated IDFs. Update parametric_and_optimisation.rst, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### C2. Objetivos de confort de largo plazo

Reutiliza D1. En `objectives.py`, junto a las horas de confort actuales y `checked_sum_results()`: `hours_outside_range` (Método A), `degree_hours` (Método B), `ppd_weighted_hours` (Método C), por zona/edificio y por periodo cálido/frío, con las categorías de EN 16798-1 como rangos. Los criterios de desviación admisible (CEN/TR 16798-2 Anexo E, Tabla E.1 **[verificado]**: 3 %/6 % anual, 12 %/25 % mensual, 20 %/50 % semanal de las horas ocupadas; con 2100 h de trabajo al año: 63/126 h anuales, 21/44 h mensuales, 8/20 h semanales) sirven como restricciones de la optimización (`constraints=` ya existe en `run_optimisation`). **[no disponible]** CIBSE TM52/TM59: no incluir sus umbrales hasta tener el texto.

### C3. Desacoplar el paramétrico de besos — iniciativa R-06 para `ROADMAP.md`

```md
### [R-06] Parametric and optimisation module without besos
- Horizon: Long term (accim 2.0)
- Objective: Remove besos (and the pins pulp<4, datapackage and the patches of accim/_besos_compat.py) by replacing its Evaluator with an accim class that applies the Parameter objects with eppy, runs run_ep (EMS or API backend) in parallel with concurrent.futures and reads the results with the current readers; platypus directly for run_optimisation and SALib for run_sensitivity_analysis_by_epw.
- Scope: accim/parametric_and_optimisation/*, accim/_besos_compat.py, setup.py/pyproject.toml, tests/parametric_and_optimisation_full_workflow.
- Exit criteria: the full-workflow tests give the same results; pip install accim does not install besos; requirements-dev.txt has no inherited pins.
- Dependencies: E3 (pyproject with extras), regression tests of the full workflow.
```

---

## 6. Bloque D — Postproceso (`Table`)

### D1. Indicadores de disconfort de largo plazo

**Base [verificado: CEN/TR 16798-2:2019, Anexo D, pp. 68–70, y Anexo E].** Métodos definidos para horas ocupadas:
- **Método A – Porcentaje fuera de rango:** número o % de horas ocupadas con PMV o temperatura operativa fuera del rango especificado.
- **Método B – Grados-hora:** `wf = 0` si `Θo,limit,lower ≤ Θo ≤ Θo,limit,upper`; si no, `wf = |Θo − Θo,limit|` (ejemplo: 23.0 < Θo ≤ 26.0 °C ≡ −0.5 < PMV < 0.5, oficina individual, categoría II, verano); indicador `Σ wf·time`, por separado para el periodo cálido (`Θo > upper`) y el frío (`Θo < lower`); unidad: horas (grados-hora).
- **Método C – Ponderado por PPD:** `wf = 0` dentro de `[PMV_limit,lower, PMV_limit,upper)`; fuera, `wf = PPD(PMV_actual) / PPD(PMV_limit)`; indicador `Σ wf·time` por periodo cálido y frío.
- Tabla D.1 (ejemplo, 1.2 met, 0.5 clo, rango 23–26 °C): `wf(°C)` 3/2/1 a 20/21/22 °C y 1/2/3 a 27/28/29 °C; `wf(PPD)` 4.7/3.1/1.9 y 1.9/3.1/4.7 respectivamente; 0 entre 23 y 26 °C.
- Anexo E (desviaciones admisibles, Tabla E.1): sobre horas ocupadas, anual 3 % / 6 %, mensual 12 % / 25 %, semanal 20 % / 50 %; "por ejemplo, con el nivel del 6 % se admiten temperaturas por encima del criterio 126 h al año pero no más de 20 h en una semana laboral ni 44 h en un mes laboral". Criterios semanales estrictos impiden semanas enteras de sobrecalentamiento.
- Relación PMV→PPD **[verificado: ISO 7730:2025, Cláusula 5, fórmula (5)]**: `PPD = 100 − 95·exp(−0.03353·PMV⁴ − 0.2179·PMV²)`; "dissatisfied" son los votos hot, warm, cool y cold de la escala de siete puntos.
- Nota: ISO 7730:2025 **[verificado: prólogo]** ha eliminado de la norma las secciones de evaluación a largo plazo, adaptación y diversidad (y ha corregido el programa de cálculo y suprimido las tablas de PMV); la referencia normativa para los indicadores de largo plazo es, por tanto, CEN/TR 16798-2 (y EN 15251 Anexo F histórico). Li, Parkinson, Schiavon et al. 2020 (*B&E*, "Improved long-term thermal comfort indices for continuous monitoring", en la biblioteca) es la referencia académica para variantes.
- **[no disponible]** CIBSE TM52 (2013) y TM59 (2017).

**Diseño.** Módulo `accim/data/postprocessing/long_term_discomfort.py` con funciones puras sobre `pandas`:
```python
def hours_outside_range(top: pd.Series, lower: pd.Series, upper: pd.Series, occupied: pd.Series, timestep_h: float) -> dict  # Method A: {'hot_h','cold_h','hot_pct','cold_pct'}
def degree_hours(top, lower, upper, occupied, timestep_h) -> dict                                                            # Method B: {'hot_Kh','cold_Kh'}
def ppd_weighted_hours(pmv: pd.Series, pmv_lower: float, pmv_upper: float, occupied, timestep_h) -> dict                     # Method C
def ppd_from_pmv(pmv) -> np.ndarray
def deviation_check(hours_outside: float, occupied_hours: float, period='yearly', level='6%') -> bool                        # Annex E Table E.1
def hours_below(temp: pd.Series, thresholds=(18, 17, 16), occupied=None, timestep_h=1.0) -> dict
```
`Table(long_term_indicators=True)` las expone como columnas agregadas (por zona y edificio, por estación cálida/fría definida con `cooling_season_start/end`), usando como límites las consignas sin tolerancia (`ACSTnoTol`/`AHSTnoTol`) que accim ya exporta o los rangos de categoría de EN 16798-1. Mantener el módulo separado del constructor de `Table` (R-04).

**Prompt para Copilot.**
```
Create accim/data/postprocessing/long_term_discomfort.py with pure pandas functions implementing CEN/TR 16798-2:2019 Annex D: hours_outside_range (Method A: hours and % of occupied hours above the upper and below the lower limit), degree_hours (Method B: sum over occupied hours of |Top - limit| * timestep, separately for the warm and the cold side), ppd_weighted_hours (Method C: weight PPD(PMV)/PPD(PMV_limit) outside the PMV range), ppd_from_pmv (ISO 7730: 100 - 95*exp(-0.03353*PMV**4 - 0.2179*PMV**2)), deviation_check against Annex E Table E.1 (yearly 3 %/6 %, monthly 12 %/25 %, weekly 20 %/50 % of occupied hours) and hours_below(thresholds). Add the option long_term_indicators=True to accim.data.postprocessing.main.Table that adds these indicators per zone and building for the warm and cold periods, using the ACSTnoTol/AHSTnoTol columns as limits by default. Unit tests reproduce Table D.1 of the TR (weights 1, 2, 3 K and 1.9, 3.1, 4.7 for 27, 28, 29 °C with a 23-26 °C range at 1.2 met and 0.5 clo). Document in the Table section of the docs, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### D2. Columnas de los índices nuevos en `Table`

Reconocer `ePMV_<zone>`, `e_<zone>`, `Activity_corrected_<zone>`, `aPMV_<zone>`, `ATHB_PMV_<zone>`, `Tout_metric`, `HoursBelow_*_<zone>` en las tablas de renombrado (`rename_cols`) y en `time_plot`/`wrangled_table`; unidades: adimensional, W/persona, °C, h.

---

## 7. Bloque E — Verificación, herramientas y empaquetado

### E1. `compute_setpoints()`: consignas sin EnergyPlus

**Motivación.** `print_setpoint_ems_code` muestra el Erl de cada combinación; `accim.sim.ems.erl` lo interpreta en Python **[verificado: CHANGELOG 1.0.0, backend API]**. Con la serie exterior de un EPW se pueden calcular `RMOT` (EN 16798-1 B.1, α = 0.8, media diaria exterior) y `PMOT` tal como los calcula EnergyPlus **[verificado: Engineering Reference 25.2, cap. 19.1, ecs. 19.70–19.72 y 19.82–19.84]**: ASHRAE 55 → media aritmética simple de las 30 medias diarias anteriores, calculada directamente del EPW (`To = (Tod−1 + … + Tod−30)/30`, forma recursiva con α = 29/30; exige un EPW de año completo); CEN 15251 → media ponderada exponencial de las 7 medias diarias anteriores con α = 0.8 (`To = (1−α)·{Tod−1 + α·Tod−2 + … + α⁶·Tod−7}`, o recursiva `To = (1−α)·Tod−1 + α·To−1`). Como se calculan del EPW, no hay transitorio de arranque y evaluar `SetAppLimits`, `ApplyCAT`, `SetComfTemp`, `SetAST_Master` y `SetAST_CS*` hora a hora.

**Diseño.**
```python
# accim/sim/preview.py
def outdoor_metrics(epw: PathLike, alpha: float = 0.8, days: int = 30) -> pd.DataFrame
    # columns: Tout, daily_mean, RMOT (B.1), RMOT_7day (B.2), PMOT_n (n-day arithmetic), Te_ref_nl, monthly_mean
def compute_setpoints(epw, comfort_standard, category=None, comfort_mode=None, **custom_arguments) -> pd.DataFrame
    # columns: datetime, Tout, RMOT, PMOT, Tout_metric, ComfTemp, ACST, AHST, applicable, cooling_season
def plot_setpoints(df: pd.DataFrame, ax=None) -> matplotlib.axes.Axes
```
Usos: previsualización para usuarios y documentación; tests de regresión del Erl de cada ComfStand frente a los CSV de EnergyPlus de `accim/sample_files` (tolerancia = redondeo `SetpointAcc`); generación de `Schedule:File` para A5 y de constantes iniciales para B1; base de `verify_accim_simulation` (E2).

**Prompt para Copilot.**
```
Create accim/sim/preview.py with outdoor_metrics(epw, alpha=0.8, days=30) (daily mean, EN 16798-1 running mean B.1 with alpha, 7-day approximate formula B.2, n-day arithmetic mean, van der Linden Te_ref with daily max/min means, monthly mean) and compute_setpoints(epw, comfort_standard, category=None, comfort_mode=None, **custom_arguments) that evaluates the ACCIS Erl programs returned by accim.utils.get_setpoint_ems_code with the Erl interpreter of accim.sim.ems.erl hour by hour, returning a DataFrame (datetime, Tout, RMOT, PMOT, Tout_metric, ComfTemp, ACST, AHST, applicable, cooling_season). Reproduce the EnergyPlus conventions (Engineering Reference 25.2 §19.1): PMOT = simple arithmetic mean of the previous 30 daily means taken from the EPW; RMOT = exponentially weighted mean of the previous 7 daily means with alpha 0.8 (eq. 19.82); both computed from the weather file, so no start-up transient. Add plot_setpoints(df). Tests compare the DataFrame with the hourly CSV of an EnergyPlus simulation of the sample IDF (tolerance = the SetpointAcc rounding) for ComfStand 1, 2 and 99. Document in docs/source/4_detailed use.md after print_setpoint_ems_code, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### E2. `verify_accim_simulation` para los índices nuevos

Comprobaciones adicionales: `ePMV = e·PMV` (A1), `aPMV = PMV/(1 + λ·PMV)`, `Activity_corrected = met·(1 − 0.067·PMV_prev)` cuando `PMV_prev > 0`, `Tout_metric` frente a `outdoor_metrics()` (E1), `AHST ≥ AHSTfloor`, `ACST ≤ ACSTceil`, y para B3 que las consignas de los modelos registrados coinciden con `compute_setpoints`.

### E3. Empaquetado y CI

- Migrar `setup.py` a `pyproject.toml` (PEP 621) con `[project.optional-dependencies]`: `comfort = ["pythermalcomfort>=4.8"]`, `gui`, `optimisation = ["platypus-opt", "SALib"]`, `weather = ["pyfwg", "pyweatherfiles"]`, `dev`. Mantener un `setup.py` mínimo si los `.bat` de `packaging/` lo requieren.
- GitHub Actions: lint + tests unitarios sin EnergyPlus en cada push; job semanal con EnergyPlus instalado que ejecute la simulación de humo de un IDF de ejemplo con ambos backends y `verify_accim_simulation`.
- `requires-python` explícito y matriz 3.10–3.13.

### E4. Integración con pyfwg y pyweatherfiles

`accim.data.morphing.morph_epws()` delega opcionalmente en `pyfwg` (Future Weather Generator) y acepta TMY de `pyweatherfiles`; sólo si están instalados (`accim[weather]`). Cuaderno: EPW presente → EPW futuros → `run_ep` → `Table` con los indicadores de D1.

---

## 8. Orden de implementación sugerido

1. **Sprint 1 (P1, bajo riesgo):** A2 → A1 → A3 → D2 → E2. Resultado: 1.2.0 con ePMV y catálogo de λ.
2. **Sprint 2 (CUSTOM y verificación):** E1 (`outdoor_metrics`, `compute_setpoints`) → B1 → B5 → C1 → D1.
3. **Sprint 3 (regionales):** B2 → B3 → B4 (primer YAML real) → A5.
4. **Sprint 4 (P2):** C2, E4, A6.
5. **Largo plazo:** A4 (ATHB vía API), C3 (R-06), E3.

Cada sprint cierra con: entrada en `CHANGELOG.md [Unreleased]`, nota en `DEVLOG.md`, cuadernos regenerados, `verify_accim_simulation` en verde con los IDF de ejemplo y ambos backends idénticos.

---

## 9. Fuentes: disponibles (leídas) y no disponibles

Bibliotecas consultadas: `D:\Python\local-reference-manager` (inventario `data\exportacion_mendeley_20261101\inventario_para_api.json` con las rutas de la carpeta *Mendeley library*; los archivos `referencias.xlsx`, `articulos.csv`, `archivos.csv` y `.lrm\*` no son legibles desde el sandbox por permisos), `...\Investigacion\Mendeley pendiente 3` y `...\Investigacion\Normativas`.

### 9.1 Leídas y usadas en este documento

| Uso | Referencia | Archivo | Datos tomados |
|---|---|---|---|
| A1 | Fanger, P.O., Toftum, J. (2002). Extension of the PMV model to non-air-conditioned buildings in warm climates. *Energy and Buildings* 34(6), 533–536. | Mendeley library: `Ole Fanger, Toftum_2002_Extension of the PMV model...pdf` (texto no extraíble; leído como imagen) | Tabla 1 (`e`), 6.7 %/unidad PMV, Tabla 2 (ciudades), Tabla 3 (`0.5/e`), sólo límite superior |
| A3 | Yao, R., Li, B., Liu, J. (2009). A theoretical adaptive model of thermal comfort – Adaptive Predicted Mean Vote (aPMV). *Building and Environment* 44, 2089–2096. | Mendeley library | λ 0.293 / −0.125 |
| A3 | Zhang, S., Yao, R., Li, B. (2024). An improved approach for solving the adaptive coefficient in the aPMV index. *Building and Environment* 256, 111481. | Mendeley library | Tabla 1 (GB/T 50785), Tabla 2 (grados), Tablas 4–7 (λN/λP por Köppen, MAE/RMSE) |
| A3 | Zhang, Cheng & Fang (2019) *B&E* 163, 106318; Zhang & Lin (2020) *Indoor Air* 30 | Mendeley library | Contexto (algoritmo λP, λ variable); no leídos en detalle |
| A4 | Schweiker, M., Wagner, A. (2015). A framework for an adaptive thermal heat balance model (ATHB). *Building and Environment* 94, 252–262. | Mendeley library | ecs. 1–5; a = 1.25, b = −0.030, c = 18 °C, d = −0.0178; −0.049 met/punto de control; Tablas 2–3 |
| A4 | Schweiker, M. (2022). Combining adaptive and heat balance models for thermal sensation prediction... *Indoor Air* 32, e13018, doi:10.1111/ina.13018. | Mendeley pendiente 3: `Indoor Air - 2022 - Schweiker - Combining adaptive and heat balance models for thermal sensation.pdf` | Datos (ASHRAE DB II, 57 084 / 34 250 / 11 417), Tabla 1 (MET = 48.5 − 0.23·Trm), Tablas 2–3 (estructura de modelos y R²adj), validación (MAE 1.01 → 0.85). Coeficientes finales tomados de `pythermalcomfort.models.pmv_athb` 4.8.1 |
| A5 | Schiavon, S., Lee, K.H. (2013). Dynamic predictive clothing insulation models based on outdoor air and indoor operative temperatures. *Building and Environment* 59, 250–260. | Mendeley pendiente 3: `1-s2.0-S0360132312002260-main.pdf` | ecs. 4–7, validez (−27.2…26 °C; 16.6…31.7 °C), medianas de clo, R²adj 0.19/0.22 |
| A5, A6, B1, B5 | ANSI/ASHRAE Standard 55-2020 (y 55-2013) | Mendeley library: `Arens et al._2021_Thermal Environmental Conditions for Human Occupancy.pdf`; `ANSIASHRAE_2013_...pdf` | §5.2.2.2(e,g), §5.2.2.3, Figura 5-1 y ecuaciones (p. 47), §5.4.1, §5.4.2.1, definición de SET |
| B1, B5, D1 | EN 16798-1:2019 (UNE-EN 16798-1:2020, versión inglesa) | Normativas: `EN_16798-1_2020_English.pdf` (y `UNE-EN_16798-1=2020.pdf`) | Anexo B: B.1–B.3, Tablas B.1–B.5, B.2.2 (aplicabilidad e invierno), B.2.3 (Tabla B.4) |
| D1, C2 | CEN/TR 16798-2:2019 (UNE-CEN/TR 16798-2:2019, inglés) | Normativas: `UNE-CEN(TR 16798-2=2019.pdf` | §8.3, Anexo D (Métodos A, B, C; Tabla D.1), Anexo E (Tabla E.1) |
| A2, C1, D1 | ISO 7730:2025 (UNE-EN ISO 7730:2025, inglés; 4ª edición) | Normativas: `UNE-EN_ISO_7730=2025.pdf` | Prólogo (cambios), §4 (rangos), fórmula (5) PPD, Tabla A.1 (categorías I–IV) |
| B1 | van der Linden, A.C. et al. (2006). Adaptive temperature limits: A new guideline in the Netherlands. *Energy and Buildings* 38, 8–17. | Mendeley library | `Te,ref` con medias de máx./mín.; Alpha→Beta bajo 10–12 °C |
| B3 | Indraganti, M., Boussaa, D. (2018). An adaptive relationship of thermal comfort for the Gulf Cooperation Council (GCC) Countries: The case of offices in Qatar. *Energy and Buildings*. | Mendeley library | ec. 5, Tabla 10 |
| B3, B4 | Aqilah, N., Rijal, H.B., Yoshida, K., Nicol, F. (2025). Developing new comfort band for adaptive model in Japanese residential building. *Energy & Buildings* 335, 115469. | Mendeley pendiente 3: `1-s2.0-S0378778825001999-main.pdf` | ecs. 5, 7, 8; Tablas 1 y 6; Conclusiones; Fig. 13 |
| A1, A3, A4 | pythermalcomfort 4.8.1 (`models.pmv_e`, `pmv_a`, `pmv_athb`) | instalado en el entorno de trabajo | implementación de referencia (usa el modelo PMV de ISO 7730:2025) |
| A5, A6, §12 | EnergyPlus 25.2: `Energy+.idd`, Input Output Reference §1.14.2.1.16, Engineering Reference §19.1 | `C:\EnergyPlusV25-2-0` | campos de `People`, variables de salida de confort, medias exteriores |
| D1 | Li, P., Parkinson, T., Schiavon, S. et al. (2020). Improved long-term thermal comfort indices for continuous monitoring. *B&E*. | Mendeley library | No leído; referencia académica para variantes de D1 |

### 9.2 No disponibles

| Documento | Afecta a | Qué se haría con él |
|---|---|---|
| CIBSE TM52 (2013) *The limits of thermal comfort: avoiding overheating in European buildings* | C2, D1 | Criterios 1–3 de sobrecalentamiento adaptativo (horas de exceso, exceso diario ponderado, límite superior) |
| CIBSE TM59 (2017) *Design methodology for the assessment of overheating risk in homes* | C2, D1 | Criterios para viviendas |
| GB/T 50785-2012 (texto de la norma) | A3 | Confirmar la Tabla 1 tomada de Zhang 2024 y leer los límites de aplicabilidad del método gráfico |
| Boerstra et al. (2015), nueva guía híbrida neerlandesa (ISSO 74 rev.) | B1 | Versión revisada de `Te,ref` y de los límites Alpha/Beta |

---

## 10. Plantillas

### 10.1 Entrada de `CHANGELOG.md [Unreleased]` (estilo 1.1.0)
```md
### Added
- **`accim.sim.pmv_index.apply_epmv_setpoints()`**: setpoints based on the ePMV index of Fanger and Toftum (2002), `ePMV = e·PMV`, with the expectancy factor `e` (0.5–1.0) of each zone applied to the cooling setpoint in the cooling season; the Fanger thermostat receives `PMV = ePMV_sp/e`, and the metabolic rate is reduced by 6.7 % per PMV unit above neutral. Outputs `ePMV_<zone>`, `e_<zone>` and `Activity_corrected_<zone>`, and the comfort hours in ePMV. Section 4.x of the detailed use.
```

### 10.2 Test de regresión de IDF (patrón)
```python
def test_output_idf_unchanged(reference_output_idf, sample_idf):
    before = normalise(reference_output_idf.read_text(encoding='utf-8'))
    after = normalise(AddAccis(...).output_idfs[0].idfstr())
    assert before == after
```

### 10.3 Cabecera común para Copilot
```
You are working on accim 1.1.0 (D:\Python\accim). Rules: PEP 8, English names and reST docstrings; eppy for IDF I/O (never besos); Erl generated through accim.sim.ems; both run_ep backends ('ems' and 'api') must give identical CSVs; pytest tests in tests/; every change logged in CHANGELOG.md [Unreleased] and DEVLOG.md; deprecations through accim._deprecation; never guess an EnergyPlus field or output-variable name — use the ones listed in section 12 of notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md or check Energy+.idd; equations and coefficients come from section 11 of that file, with their citation in the docstring. Task: <paste the proposal prompt>.
```

---

## 11. Hoja de fórmulas (todas **[verificado]**; copiar en docstrings con su cita)

### 11.1 Índices derivados del PMV
| Índice | Fórmula | Inversa para el termostato de Fanger | Fuente |
|---|---|---|---|
| PMV / PPD | `PPD = 100 − 95·exp(−0.03353·PMV⁴ − 0.2179·PMV²)` | — | ISO 7730:2025 (5) |
| aPMV | `aPMV = PMV / (1 + λ·PMV)` | `PMV = aPMV / (1 − λ·aPMV)` | Yao et al. 2009; accim `apmv.py` |
| ePMV | `ePMV = e · PMV_corr`, `PMV_corr` calculado con `met·(1 − 0.067·PMV)` si `PMV > 0` | `PMV = ePMV / e` (sólo límite superior) | Fanger & Toftum 2002 |
| ATHB (2022) | `met_ad = met − 0.234·Trm/58.2`; `clo_ad = 10^(−0.17168 − 0.000485·Trm + 0.08176·met_ad − 0.00527·Trm·met_ad)`; `PMV* = PMV(tdb, tr, vr, rh, met_ad, clo_ad)`; `ts = 0.303·exp(−0.036·met_ad·58.15) + 0.028`; `L_ad = PMV*/ts`; `ATHB_PMV = 1.484 + 0.0276·L_ad − 0.9602·met_ad − 0.0342·Trm + 0.0002264·L_ad·Trm + 0.018696·met_ad·Trm − 0.0002909·L_ad·met_ad·Trm` | numérica (bisección sobre Top) | Schweiker 2022 vía pythermalcomfort 4.8.1 |
| ATHB (2015, laboratorio) | `CLO = 1.25 − 0.030·Trm`; `MET_phys = (Trm − 18)·(−0.0178)` (sólo Trm > 18); `MET_psy,var = −0.049`/punto de control percibido; `MET_ad = MET0 + Σ` | — | Schweiker & Wagner 2015 |

### 11.2 Factores y catálogos
- `e` (Fanger & Toftum 2002, Tabla 1): alta 0.9–1.0; moderada 0.7–0.9; baja 0.5–0.7; `e = 1` con AC. Ciudades (Tabla 2): Bangkok 0.6, Singapur 0.7, Atenas 0.7, Brisbane 0.9.
- λ (Yao 2009): 0.293 cálido, −0.125 frío. λ (GB/T 50785-2012): SC/Cold general 0.24/−0.50, educativo 0.21/−0.29; HSCW/HSWW/Mild general 0.21/−0.49, educativo 0.17/−0.28 (PMV ≥ 0 / PMV < 0). λN por Köppen (Zhang 2024, Tabla 6): ver A3.
- Categorías PMV/PPD (ISO 7730:2025 Tabla A.1 = EN 16798-1 Tabla B.1): I PPD < 6 %, |PMV| < 0.2; II < 10 %, < 0.5; III < 15 %, < 0.7; IV < 25 %, < 1.0. Local (ISO Tabla A.1): DR < 10/20/30 %; PD vertical < 3/5/10 %; suelo < 10/10/15 %; asimetría < 5/5/10 %.
- Rangos de validez del PMV (ISO 7730:2025 §4): PMV −2…+2; M 46–232 W/m² (0.8–4 met); Icl 0–0.310 m²·K/W (0–2 clo); ta 10–30 °C; tr 10–40 °C; var 0–1 m/s; pa 0–2700 Pa; 1 met = 58.2 W/m²; 1 clo = 0.155 m²·°C/W.
- ISO 7730:2025 (4ª ed.) frente a 2005: suprime las secciones de evaluación a largo plazo, adaptación y diversidad; corrige el programa de cálculo; suprime las tablas de PMV; categorías renombradas I–IV (antes A/B/C) con la IV nueva.

### 11.3 Vestimenta
- ASHRAE 55-2020 Figura 5-1: `Icl = 1.00` si `ta6 < −5`; `0.818 − 0.0364·ta6` si `−5 ≤ ta6 < 5`; `10^(−0.1635 − 0.0066·ta6)` si `5 ≤ ta6 < 26`; `0.46` si `ta6 ≥ 26` (°C). Ocupantes en movimiento: `Icl,active = Icl·(0.6 + 0.4/M)`, 1.2 < M < 2.0 met. No aplicable > 1.5 clo.
- Schiavon & Lee 2013: (4) `log10(clo) = −0.1635 − 0.0066·day06_ta`; (5) `log10(clo) = 0.2134 − 0.0165·top − 0.0063·day06_ta`; validez `day06_ta ∈ [−27.2, 26] °C`, `top ∈ [16.6, 31.7] °C`; sin silla.
- EN 16798-1 Tablas B.2/B.5: ~1.0 clo invierno, ~0.5 clo verano, ~1.2 met sedentario (1.5 met de pie), HR 50 % (B.2) o 40 %/60 % (B.5), v < 0.1 m/s.

### 11.4 Temperatura exterior de referencia
- EN 16798-1 (B.1): `Θrm = (1 − α)·{Θed−1 + α·Θed−2 + α²·Θed−3 + …}`, α recomendado 0.8; forma recursiva `Θrm = (1 − α)·Θed−1 + α·Θrm−1`. (B.2) aproximada: `(Θed−1 + 0.8·Θed−2 + 0.6·Θed−3 + 0.5·Θed−4 + 0.4·Θed−5 + 0.3·Θed−6 + 0.2·Θed−7)/3.8`.
- EnergyPlus (Eng. Ref. 19.1): CEN 15251 = (B.1) truncada a 7 días con α = 0.8 (ec. 19.82); ASHRAE 55 = media simple de 30 días (ec. 19.70); ambas del EPW (año completo).
- ASHRAE 55-2020 §5.4.2.1: 7–30 días secuenciales, media simple de medias diarias; o ponderación decreciente con razón 0.6–0.9 entre días consecutivos, sin límite de días.
- ATG (van der Linden 2006): `Te,ref = (1·T0 + 0.8·T−1 + 0.4·T−2 + 0.2·T−3)/2.4`, `Ti = (Tmax,i + Tmin,i)/2`.
- McCartney & Nicol (citado en Aqilah 2025, ec. 7): `Trm = α·Trm−1 + (1 − α)·Tod−1`.

### 11.5 Modelos adaptativos citados en este documento
| Modelo | Ecuación | Banda | Métrica | Aplicabilidad | Fuente |
|---|---|---|---|---|---|
| EN 16798-1 | `Θc = 0.33·Θrm + 18.8` | I +2/−3; II +3/−4; III +4/−5 K | Θrm (α 0.8) | 10 < Θrm < 30 °C; invierno → Tabla B.2 | EN 16798-1 B.2.2 |
| ASHRAE 55 | `Tot = 0.31·Tpma + 17.8` | 90 % ±2.5; 80 % ±3.5 K | prevailing mean (7–30 d) | 10 < Tpma < 33.5 °C; sin HVAC en marcha; 1.0–1.5 met; 0.5–1.0 clo | ASHRAE 55-2020 §5.4; Eng. Ref. 19.73–74 |
| Japón viviendas FR (Aqilah 2025) | `Tc = 0.38·Trm + 16.9` | 90 % ±1.5; 80 % ±2.0 K | Trm (α 0.8) | Trm ≈ 5–30 °C | Aqilah et al. 2025 ec. 8 |
| Japón viviendas MM (Rijal et al.; accim ComfStand 3) | `Tc = 0.48·Tpma + 14.4` | 90 % ±2.5; 80 % ±3.5 (de ASHRAE) | Tpma | — | Aqilah 2025 Tabla 1 |
| Japón oficinas (Rijal et al., HVAC) | `Tc = 0.065·Tr + 23.9` | — | Tr | — | Indraganti & Boussaa 2018 Tabla 10 |
| Qatar oficinas HVAC | `Tc = 0.049·Tr + 22.5` (R² 0.015, N 3742) | — | Tr | — | Indraganti & Boussaa 2018 ec. 5 |
| India IMAC-R | `Tc = 0.39·T7DRM + 18.4`; `Tc = 0.42·T30DRM + 17.6` | 90 % ±2.15; 80 % ±3.60 | 7DRM / 30DRM | — | Aqilah 2025 Tabla 1 (Rawal et al.) |
| India (Manu et al., MM) | `Tn = 0.28·Tr + 17.87` | — | Tr | — | Indraganti & Boussaa 2018 Tabla 10 |
| Australia viviendas MM (Williamson & Daniel) | `Tc = 0.26·Tpma + 15.9` | 90 % ±3.5; 80 % ±4.5 | Tpma | — | Aqilah 2025 Tabla 1 |
| Malasia viviendas CL | `Tc = 0.56·Trm + 8.9` | ±2 | Trm | — | Aqilah 2025 Tabla 1 |
| México educativo NV | `Tc = 0.32·Trm + 18.4` | 90 % ±2.5; 80 % ±3.5 | Trm | — | Aqilah 2025 Tabla 1 |

### 11.6 Indicadores de largo plazo (CEN/TR 16798-2 Anexo D)
- A: `% horas ocupadas fuera de rango`. B: `Σ |Θo − Θo,limit|·Δt` fuera de rango (grados-hora), por lado. C: `Σ [PPD(PMV)/PPD(PMV_limit)]·Δt` fuera de rango. Desviaciones admisibles (Anexo E, Tabla E.1): anual 3 %/6 %, mensual 12 %/25 %, semanal 20 %/50 % de las horas ocupadas.

---

## 12. Referencia de EnergyPlus 25.2 **[verificado en `Energy+.idd` e Input Output Reference]**

### 12.1 Objeto `People` (campos relevantes)
- *Thermal Comfort Model 1…5 Type*: `Fanger`, `Pierce`, `KSU`, `AdaptiveASH55`, `AdaptiveCEN15251`, `CoolingEffectASH55`, `AnkleDraftASH55`.
- *Mean Radiant Temperature Calculation Type*: `EnclosureAveraged` (defecto), `SurfaceWeighted`, `AngleFactor`.
- *Clothing Insulation Calculation Method*: `ClothingInsulationSchedule` (defecto), `DynamicClothingModelASHRAE55`, `CalculationMethodSchedule`; *Clothing Insulation Calculation Method Schedule Name* (valor 1 = schedule, 2 = modelo dinámico); *Clothing Insulation Schedule Name*; *Air Velocity Schedule Name*; *Activity Level Schedule Name* (W/persona).

### 12.2 Variables de salida de confort (`Zone Thermal Comfort …`)
`Fanger Model PMV`; `Fanger Model PPD`; `Clothing Value`; `Clothing Surface Temperature`; `Mean Radiant Temperature`; `Operative Temperature`; `Effective Air Temperature`; `Control Type`; `Control Fanger Low Setpoint PMV`; `Control Fanger High Setpoint PMV`; `Pierce Model Effective Temperature PMV`; `Pierce Model Standard Effective Temperature PMV`; `Pierce Model Standard Effective Temperature`; `Pierce Model Discomfort Index`; `Pierce Model Thermal Sensation Index`; `KSU Model Thermal Sensation Vote`; `KSU Model Thermal Sensation Index`; `ASHRAE 55 Adaptive Model 80% Acceptability Status`; `ASHRAE 55 Adaptive Model 90% Acceptability Status`; `ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature`; `ASHRAE 55 Adaptive Model Temperature`; `CEN 15251 Adaptive Model Category I/II/III Status`; `CEN 15251 Adaptive Model Running Average Outdoor Air Temperature`; `CEN 15251 Adaptive Model Temperature`; `ASHRAE 55 Elevated Air Speed Cooling Effect`; `ASHRAE 55 Elevated Air Speed Cooling Effect Adjusted PMV`; `ASHRAE 55 Elevated Air Speed Cooling Effect Adjusted PPD`; `ASHRAE 55 Ankle Draft PPD`; `ASHRAE 55 Simple Model Summer/Winter/Summer or Winter Clothes Not Comfortable Time`.
(Los nombres completos llevan el prefijo `Zone Thermal Comfort `; p. ej. `Zone Thermal Comfort Fanger Model PMV`. accim ya usa los dos *Running Average Outdoor Air Temperature* como sensores `RMOT` y `PMOT`.)

### 12.3 Otros sensores usados en las propuestas
`Site Outdoor Air Drybulb Temperature` (B1); `Zone Mean Air Temperature`, `Zone Mean Radiant Temperature`, `Zone Air Relative Humidity`, `Zone Operative Temperature` (A4, A6; accim ya usa `Zone Operative Temperature` como `<zone>_OpT`); `People Occupant Count` (ya usado); variables Erl integradas `Hour`, `Minute`, `ZoneTimeStep`, `CurrentTime`, `DayOfYear` y funciones `@Max`, `@Min` (B1) — del *EMS Application Guide*; `CurrentTime` y `ZoneTimeStep` ya se usan en `setpoint_lines.py`.

### 12.4 Termostatos
`ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint` (usado por aPMV; consignas PMV en schedules actuadas por EMS `PMV_H_SP_<zone>`/`PMV_C_SP_<zone>`); `ThermostatSetpoint:DualSetpoint` con control de temperatura operativa (ACCIS); EnergyPlus no tiene termostato por SET ni por PPD (A6 necesita Erl o el backend API).
