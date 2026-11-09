# accim — Propuestas de mejora y nuevas funciones (tras la 1.1.0) — v02

- v02 (2026-11-08): coeficientes verificados en los PDF de la biblioteca local (`D:\Python\local-reference-manager`, inventario `exportacion_mendeley_20261101/inventario_para_api.json` → rutas en la carpeta Mendeley library). Cambios en A1, A3, A4, A5, B1, B3 y §9. La v01 queda como histórico.

- Fecha: 2026-11-08 (mismo día de la publicación de accim 1.1.0).
- Base verificada: `D:\Python\accim`, rama `master`, `accim.__version__ == '1.1.0'`, commit `6ca8c69d` ("docs: log the 1.1.0 release").
- Destinatario: el mantenedor, para implementar cada propuesta con GitHub Copilot en PyCharm.
- Idioma: prosa en español; identificadores, firmas, Erl y los bloques "Prompt para Copilot" en inglés, que es el idioma del código, de los docstrings y de `CHANGELOG.md`/`DEVLOG.md`/`TODO.md`/`ROADMAP.md`.

> Convención de este documento: lo marcado **[verificado]** se ha leído en el código de la 1.1.0; lo marcado **[verificar con texto completo]** procede de memoria/abstract y debe contrastarse con el artículo antes de codificar los coeficientes. Al final (§9) hay una lista de los artículos cuyos textos completos conviene tener.

---

## 0. Cómo usar este documento con Copilot en PyCharm

1. Abre el repositorio `D:\Python\accim` en PyCharm con el plugin de GitHub Copilot (Chat).
2. En Copilot Chat, añade este archivo como contexto (`#file:notes/PROPUESTAS_MEJORAS_post_1.1.0_v01.md`) y los archivos que cada propuesta enumera en "Archivos".
3. Pega el bloque "Prompt para Copilot" de la propuesta. Cada prompt pide: código + tests + entrada en `CHANGELOG.md` (sección `## [Unreleased]`) + nota en `DEVLOG.md`, que es la convención ya establecida en el repositorio (`ROADMAP.md` §"How to use this file", `TODO.md` §"Conventions").
4. Reglas de estilo que Copilot debe respetar (coherentes con la 1.1.0): PEP 8 y nombres en inglés; eppy para leer/escribir IDF (nunca besos); los programas Erl se generan con `accim.sim.ems` (`program_lines.py`, `setpoint_lines.py`, `objects.py`, `programs.py`); toda función nueva con docstring reST (`:param:`/`:return:`), `__all__` actualizado, deprecaciones con `accim._deprecation`; tests en `tests/core` (`pytest`), con IDFs de `accim/sample_files`.
5. Prioridades según la propuesta del `TODO.md` (2026-10-31): `P0` bloqueante, `P1` siguiente release, `P2` mejora. Esfuerzo: S (< 1 día), M (1–3 días), L (> 3 días).

---

## 1. Estado de partida (1.1.0) — lo que condiciona las propuestas **[verificado]**

| Aspecto | Estado en 1.1.0 | Implicación |
|---|---|---|
| Catálogo de modelos | `accim/sim/standards.py`: ComfStand 0–22 y 99 (CUSTOM). Sin mecanismo de registro externo. | Las propuestas B3 y B4 necesitan un registro extensible. |
| Temperatura exterior | `accim/sim/ems/objects.py::add_sensors` crea los sensores `RMOT` (variable de salida *CEN 15251 Adaptive Model Running Average Outdoor Air Temperature*, α fijo de EnergyPlus) y `PMOT` (*ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature*). `SET_COMF_TEMP` (ComfStand 99): `set ComfTemp = PMOT*m+n`. | El CUSTOM no permite elegir métrica exterior ni α (propuesta B1). |
| aPMV | `accim/sim/apmv.py::apply_apmv_setpoints`: argumentos por zona (`adaptive_coefficient_cooling/heating`, `pmv_*_setpoint`, tolerancias por estación, `cooling_season_start/end`). Erl: `PMV_sp = aPMV_sp/(1-λ·aPMV_sp)`; monitor `aPMV = PMV/(1+λ·PMV)`; horas de confort por zona; media ponderada de PMV cuando hay varios `People`. `set_pmv_input_parameters` fija clo, met y velocidad del aire. | El ePMV y otros índices PMV-derivados encajan en la misma infraestructura (A1, A2). |
| Backend API | `accim/sim/energyplus_api/runner.py::run_simulation(..., before_programs, after_programs)`; `ErlController` da acceso a las variables de los programas. `accim.sim.ems.erl` interpreta Erl en Python. No soporta `TrendVariable`. | Permite índices calculados en Python (ATHB, SET*) sin Erl (A4, A6), y una `compute_setpoints` sin EnergyPlus (E1). Las métricas exteriores nuevas deben evitar `TrendVariable` (B1). |
| Paramétrico | `accim/parametric_and_optimisation/parameters.py`: 29 clases `Parameter` (ComfStand, CustAST_*, CAT*, ComfMod, HVACmode, VentCtrl, VSToffset, MinOToffset, MaxWindSpeed, ASTtol, CoolSeason*, SetpointAcc, *VOF). `params_dicts.py` incluye `adaptive_coefficient*`, `pmv_*_setpoint`, pero no clo/met/velocidad del aire. | Faltan parámetros personales (C1). |
| Verificación | `accim/utils/verification.py::verify_accim_simulation` (67 kB) comprueba las salidas contra los argumentos del ACCIS. `accim.utils.print_setpoint_ems_code()` muestra el Erl. | E1/E2 amplían esto. |
| Dependencias | `setup.py` (`install_requires`: scikit-learn, eppy>=0.5.63, pycountry, geopy, matplotlib, numpy, pandas, openpyxl>=3.1.5, datapackage, unidecode, besos, pulp<4, SALib, seaborn). `accim/_besos_compat.py` parchea besos/dask/platypus. | Deuda técnica: besos (C3), migración a `pyproject.toml` (E3). |
| Roadmap existente | R-01 gobernanza de docs, R-02 archivado, R-03 quitar nombres 0.x (accim 2.0), R-04 refactor de `Table`, R-05 cobertura completa del EMS en el backend API. | Las propuestas de aquí se numeran R-06… para no colisionar. |

---

## 2. Mapa de propuestas

| ID | Título | Prioridad | Esfuerzo | Módulos | Depende de |
|---|---|---|---|---|---|
| A1 | ePMV (Fanger & Toftum 2002) como consigna | P1 | M | `sim/apmv.py`, `sim/ems`, `parametric/funcs_for_besos/param_apmv.py`, GUI | A2 recomendable |
| A2 | Motor común de índices PMV-derivados (`apply_pmv_index_setpoints`) | P1 | M | `sim/apmv.py` → `sim/pmv_index.py` | — |
| A3 | λ del aPMV por clima (catálogo) | P2 | S | `constants.py`, `sim/apmv.py` | texto completo Zhang, Yao & Li 2024 |
| A4 | ATHB (Schweiker 2022) vía backend API + pythermalcomfort | P2 | L | `sim/energyplus_api`, nuevo `sim/comfort_hooks.py` | pythermalcomfort opcional |
| A5 | Vestimenta dinámica (ASHRAE 55 / Schiavon & Lee 2013) y clo por estación | P1 | S–M | `sim/apmv.py::set_pmv_input_parameters`, `sim/people.py` | — |
| A6 | Consignas por SET*/PPD | P2 | L | `sim/energyplus_api`, `sim/ems` | A4 |
| B1 | Métrica exterior configurable en CUSTOM (α, media mensual, Te,ref, 7DRM) | P1 | M | `sim/ems/program_lines.py`, `objects.py`, `sim/arguments.py`, `print_setpoint_ems_code` | — |
| B2 | CUSTOM con varios regímenes (NV/AC, umbral, estación, zona climática) | P1 | L | `sim/arguments.py`, `sim/ems/setpoint_lines.py`, paramétrico | B1 |
| B3 | Registro de modelos de confort externos (plugins YAML/Python) | P1 | L | `sim/standards.py`, `sim/ems/*`, GUI | — |
| B4 | Actualización JPN Rijal (categorías Aqilah et al. 2025) | P2 | S | `sim/standards.py`, `sim/ems/program_lines.py` | texto completo Aqilah 2025 |
| B5 | Suelo sanitario de calefacción (`heating_setpoint_floor`) | P1 | S | `sim/arguments.py`, `sim/ems/setpoint_lines.py` (ROUNDING) | — |
| C1 | Parámetros clo, met, v_air, e, λ por estación, floor | P1 | S | `parametric/parameters.py`, `params_dicts.py`, `param_apmv.py` | A1, A5, B5 |
| C2 | Objetivos de confort: EN 16798-2 Anexo F, TM52/TM59, PPD-ponderado | P2 | M | `parametric/objectives.py`, `data/postprocessing` | D1 |
| C3 | Desacoplar el paramétrico de besos | P2 (R-06) | L | `parametric/*`, `_besos_compat.py`, `setup.py` | — |
| D1 | Indicadores de disconfort de largo plazo en `Table` | P2 | M | `data/postprocessing/main.py`, nuevo `long_term_discomfort.py` | — |
| D2 | Columnas ePMV/aPMV/PPD y horas por índice en `Table` | P1 | S | `data/postprocessing` | A1 |
| E1 | `compute_setpoints()` sin EnergyPlus (intérprete Erl + EPW) | P1 | M | nuevo `sim/preview.py`, `sim/ems/erl.py` | — |
| E2 | `verify_accim_simulation` para los índices nuevos | P1 | S | `utils/verification.py` | A1, A2 |
| E3 | `pyproject.toml`, extras `accim[comfort]`, CI con EnergyPlus | P2 | M | raíz, `.github/workflows` | — |
| E4 | Integración con pyfwg y pyweatherfiles | P2 | S | `data/morphing.py` | — |

---

## 3. Bloque A — Índices de confort derivados del PMV

### A1. ePMV (PMV con factor de expectativa) como consigna

**Motivación.** Fanger & Toftum (2002) extendieron el PMV a edificios sin aire acondicionado en climas cálidos: `ePMV = e · PMV`, con el factor de expectativa `e` entre 0.5 y 1.0 (`e = 1` en edificios con aire acondicionado), y una reducción del metabolismo del 6.7 % por unidad de PMV por encima de neutro (un PMV de 1.5 equivale a una reducción del 10 %; `met_corr = met · (1 − 0.067 · PMV)` con el PMV sin corregir, y después se recalcula el PMV y se multiplica por `e`). **[verificado, Fanger & Toftum 2002, pp. 534–535, Tabla 1]**: expectativa alta, `e` = 0.9–1.0 (regiones donde el AC es habitual; calor breve en verano); moderada, 0.7–0.9 (algunos edificios con AC; verano); baja, 0.5–0.7 (pocos edificios con AC; calor todo el año). Valores por ciudad usados en la validación (Tabla 2): Bangkok 0.6, Singapur 0.7, Atenas 0.7, Brisbane 0.9. Tabla 3: el límite superior del PMV pasa a ser `0.5/e` (10 % PPD) o `0.85/e` (20 %), y "sólo el límite superior de la zona de confort se ve afectado por el factor de expectativa; no se espera ajuste del límite inferior" (cálculos con 1 met, 0.5 clo, 0.3 m/s, 70 % HR). Esto fija el diseño: `e` sólo actúa sobre la consigna de refrigeración, y `apply_to_heating=False` es la única opción fiel al artículo. pythermalcomfort lo implementa como `pmv_e(tdb, tr, vr, rh, met, clo, e_coefficient)`.

accim ya publica consignas aPMV (JBE 119, 115273, 2026); el ePMV es el índice hermano más citado y encaja en la misma mecánica de inversión.

**Diseño.**
- Nueva función `accim.sim.apmv.apply_epmv_setpoints(building, expectancy_factor=0.8, pmv_cooling_setpoint=0.5, pmv_heating_setpoint=-0.5, apply_to_heating=False, metabolic_correction=False, ...)` con la misma convención de argumentos por zona (`Union[float, dict]` + `default_*`) y la misma estación de refrigeración que `apply_apmv_setpoints`. Si se hace A2, es un caso del motor común.
- Erl, por zona (sufijo `{s}`):
  ```
  ! ePMV inverse: the Fanger thermostat controls PMV, so PMV_sp = ePMV_sp / e
  if CoolingSeason == 1
  set e_{s} = expectancy_{s}
  else
  set e_{s} = 1            ! Fanger & Toftum define ePMV only for warm conditions
  endif
  set PMV_C_SP_act_{s} = pmv_cooling_sp_{s} / e_{s}
  set PMV_H_SP_act_{s} = pmv_heating_sp_{s}          ! unchanged unless apply_to_heating
  set ePMV_{s} = e_{s} * PMV_{s}                      ! monitor
  ```
- `metabolic_correction=True` (opcional, documentar la circularidad): actuador EMS sobre el `Schedule` de *Activity Level* del `People` de la zona, `met_corr = met0·(1 − 0.067·@Max PMV_prev 0)` usando el PMV del paso anterior (variable global `PMV_prev_{s}` escrita al final del programa). Requiere que `set_pmv_input_parameters` haya fijado un `Schedule:Compact` propio para la actividad (ya lo hace para clo/met/velocidad, comprobar).
- Salidas: `EnergyManagementSystem:OutputVariable` `ePMV_<zone>`, `e_<zone>`, contador de horas de confort en ePMV (clon de `count_aPMV_comfort_hours_*`).
- Límites: `0.5 <= e <= 1.0` con `ValueError`; `apply_to_heating=True` sólo con un `warnings.warn` explícito (Fanger & Toftum 2002, p. 535: el factor no modifica el límite inferior). Constantes en `accim/constants.py`: `EPMV_EXPECTANCY_RANGES = {'high': (0.9, 1.0), 'moderate': (0.7, 0.9), 'low': (0.5, 0.7)}` y `EPMV_MET_REDUCTION_PER_PMV = 0.067`.

**Archivos.** `accim/sim/apmv.py` (o `accim/sim/pmv_index.py` tras A2), `accim/sim/__init__.py`, `accim/parametric_and_optimisation/funcs_for_besos/param_apmv.py` (función equivalente para BESOS), `accim/parametric_and_optimisation/params_dicts.py`, `accim/gui/forms.py` (pestaña de consignas PMV), `docs/source/4_detailed use.md`, cuaderno `docs/source/jupyter_notebooks/.../using_epmv_setpoints.ipynb`.

**Tests.** (1) `e=1` ⇒ IDF idéntico en EMS a `apply_apmv_setpoints(λ=0)` salvo nombres; (2) inversión: para `e=0.7` y `ePMV_sp=0.5` la consigna PMV actuada es `0.7142…`; (3) simulación de `accim/sample_files` 1 semana: `ePMV_zone == e·PMV_zone` en cada paso (tolerancia 1e-6); (4) backend `api` y `ems` dan el mismo CSV.

**Prompt para Copilot.**
```
Read accim/sim/apmv.py (apply_apmv_setpoints and its helpers) and accim/sim/ems/erl.py. Add apply_epmv_setpoints() to accim/sim/apmv.py implementing the ePMV index of Fanger & Toftum (2002): ePMV = e*PMV. Keep the per-zone argument convention (Union[float, dict] plus default_*), the cooling season logic (COOLING_SEASON_LINES), the Fanger dual-setpoint thermostat and the schedule actuators PMV_H_SP_<zone>/PMV_C_SP_<zone>. In the Erl program, the cooling PMV setpoint is pmv_cooling_setpoint/e in the cooling season and unchanged otherwise; the heating setpoint is unchanged unless apply_to_heating=True. Add EMS output variables ePMV_<zone> and e_<zone> and a comfort-hours counter like count_aPMV_comfort_hours. Validate 0.5 <= e <= 1.0. Add tests in tests/core/test_epmv.py (inverse formula, e=1 equals plain PMV control, API and EMS backends agree on a one-week run of a sample IDF), export it in accim/sim/__init__.py, document it in docs/source/4_detailed use.md next to apply_apmv_setpoints, and add entries to CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### A2. Motor común de índices PMV-derivados

**Motivación.** aPMV (ya), ePMV (A1) y el PMV puro con consignas ±0.2/0.5/0.7 (categorías ISO 7730/EN 16798-1) comparten el 90 % de la infraestructura (`_ensure_infrastructure`, `_create_tc_thermostat`, sensores, actuadores, media ponderada, contadores). Duplicar `apply_*_setpoints` por índice multiplicará el mantenimiento.

**Diseño.**
- Nuevo módulo `accim/sim/pmv_index.py` con `apply_pmv_index_setpoints(building, index='apmv'|'epmv'|'pmv', index_parameters: dict, ...)`. La transformación índice→PMV se encapsula en un registro `PMV_INDEX_INVERSES = {'apmv': lambda sp, p: f'{sp}/(1-{p["lambda"]}*{sp})', 'epmv': ..., 'pmv': ...}` que devuelve líneas Erl, más la línea del monitor.
- `apply_apmv_setpoints` y `apply_epmv_setpoints` pasan a ser envoltorios finos (firma intacta, misma salida; tests de regresión con los IDF de `accim/sample_files/sample IDFs/output_IDFs`).
- Documentar en `CAMBIOS_CODIGO_v1.2.0.md` (mismo formato que los de 1.0.0 y 1.1.0).

**Prompt para Copilot.**
```
Refactor accim/sim/apmv.py into a generic engine accim/sim/pmv_index.py: apply_pmv_index_setpoints(building, index, index_parameters, ...) shares _ensure_infrastructure, _create_tc_thermostat, sensors, actuators, PMV averaging and comfort-hour counters; only the Erl lines that convert the index setpoint into a PMV setpoint (and the monitor line) depend on the index, taken from a dict PMV_INDEX_INVERSES. Keep apply_apmv_setpoints() as a thin wrapper with the exact same signature, defaults, EMS object names and output IDF text (add a regression test that compares the IDF produced before and after the refactor for the sample IDFs). Add apply_epmv_setpoints() as a second wrapper. Update accim/sim/__init__.py, docs and CHANGELOG.md [Unreleased].
```

### A3. Catálogo de λ del aPMV por clima

**Motivación.** El λ de Yao et al. (2009) para las aulas de Chongqing es 0.293 (condiciones cálidas) y −0.125 (frías) **[verificado, Yao, Li & Liu 2009, §4 y Conclusiones]**. GB/T 50785-2012 adopta el aPMV para edificios en free-running con λ por zona climática y tipo de edificio **[verificado vía Zhang, Yao & Li 2024, Tabla 1, que reproduce la norma]**:

| Zona climática (GB/T 50785-2012) | Edificio | λ (PMV ≥ 0) | λ (PMV < 0) |
|---|---|---|---|
| Severe cold y Cold | Residencial, comercio, hoteles, oficinas | 0.24 | −0.50 |
| Severe cold y Cold | Educativos | 0.21 | −0.29 |
| HSCW, HSWW y Mild | Residencial, comercio, hoteles, oficinas | 0.21 | −0.49 |
| HSCW, HSWW y Mild | Educativos | 0.17 | −0.28 |

Grados de la norma (Tabla 2 de Zhang 2024): I `−0.5 ≤ aPMV ≤ 0.5`; II `0.5 < |aPMV| ≤ 1`; III `|aPMV| > 1`.

Zhang, Yao & Li (2024, *Build. Environ.* 256, 111481) **[verificado, Tabla 6]** ajustan λ (su algoritmo λN y el λP de Zhang 2019) en 14 zonas Köppen con 22 785 registros de edificios NV de la ASHRAE Global Thermal Comfort Database II. λN (PMV<0 / PMV>0): Af 0.66/0.66; Am −0.66/0.46; Aw –/0.36; BSh −0.56/0.66; BSk −0.66/0.09; BWh −0.66/0.34; Cfa 0.1/0.41; Cfb −0.41/−0.23; Csa −0.66/0.29; Csb −0.25/0.55; Csc −0.66/−0.66; Cwb −0.66/0.55; Dfb −0.66/−0.66; Dwa −0.66/−0.07. **Advertencia para el catálogo:** muchos valores saturan en el límite ±0.66 del ajuste y varios signos contradicen la lógica de adaptación (λ negativo con PMV>0, p. ej. Cfb, Csc, Dfb), así que estos λ se incluirían como "literatura, con aviso", no como valores por defecto; los de GB/T 50785 y Yao 2009 sí pueden ser predefinidos. El código de Zhang 2024 está en `github.com/SuDBE/aPMV-calculation`.

**Diseño.** `accim/constants.py::APMV_ADAPTIVE_COEFFICIENTS: dict[str, dict]` con claves `'yao2009_chongqing'`, `'gbt50785_cold_general'`, `'gbt50785_cold_education'`, `'gbt50785_hscw_hsww_mild_general'`, `'gbt50785_hscw_hsww_mild_education'`, `'zhang2024_<koppen>'` → `{'cooling': λc, 'heating': λh, 'source': DOI, 'notes': ...}`. `apply_apmv_setpoints(adaptive_coefficient_cooling='gbt50785_cold_general')` acepta la clave además del número (resuelta en `_resolve_targets`/`generate_df_from_args`). GUI: desplegable con la fuente. Los valores de la tabla anterior pueden codificarse ya.

### A4. ATHB (Adaptive Thermal Heat Balance) con el backend API

**Motivación.** El ATHB de Schweiker & Wagner (2015) ajusta las entradas del balance térmico según la media móvil exterior `Trm` (EN 15251) y calcula un PMV adaptado **[verificado, Schweiker & Wagner 2015, ecs. 1–5 y §4.1]**: adaptación conductual `CLO = a + b·Trm` con `a = 1.25`, `b = −0.030`; fisiológica `MET_phys = (Trm − c)·d` con `c = 18 °C` (inicio del verano en Karlsruhe; sólo actúa con `Trm > c`) y `d = −0.0178` met/K (pendiente de la frecuencia cardiaca 0.193 × HRtoMET 0.092); psicológica variable `−0.049` met por punto de control percibido (ec. 3) y una constante `g` por condición experimental (ec. 4); `MET_adapted = MET0 + MET_phys + MET_psych,var + MET_psych,const` (ec. 5), con `MET0 = 1.1`, `CLO0 = 0.5` en sus cálculos. Datos: 2511 votos, 105 sujetos (LOBSTER), `Trm` 14–26 °C. La versión que implementa pythermalcomfort (`pmv_athb(tdb, tr, vr, rh, met, t_running_mean)`) cita Schweiker 2022, cuyos coeficientes **no están verificados** (PDF no disponible, ver §9): antes de codificar, contrastar los coeficientes de `pythermalcomfort.models.pmv_athb` con ese artículo. No es expresable en Erl sin reimplementar el PMV (iteración de la temperatura de la ropa), pero el backend API de la 1.0.0 ya ejecuta los programas en Python.

**Diseño.**
- Nuevo módulo `accim/sim/comfort_hooks.py` con hooks `after_programs` para `run_simulation`: en cada `calling_point` de control, leen `Zone Mean Air Temperature`, `Zone Mean Radiant Temperature`, `Zone Air Relative Humidity`, velocidad del aire y RMOT del `ErlController`, calculan el índice con pythermalcomfort y escriben la consigna de temperatura (bisección sobre la temperatura operativa objetivo, 0.1 K) en los actuadores de las schedules de consigna.
- `apply_athb_setpoints(building, ...)` prepara el IDF (thermostat dual de temperatura operativa, schedules actuables, salidas) y `run_ep(backend='api', comfort_hooks=[...])` los conecta. Con `backend='ems'` lanza `NotImplementedError` con el mensaje de por qué.
- `pythermalcomfort` como dependencia opcional (`extras_require['comfort']`), importada perezosamente.

**Riesgo.** Rendimiento (una bisección con ~10 evaluaciones de PMV por zona y paso); medir en el IDF de ejemplo y, si hace falta, cachear por (Top, RH, RMOT) redondeados.

### A5. Vestimenta dinámica y clo por estación

**Motivación.** Línea directa con el artículo de adaptación al frío (clo como variable paramétrica). ASHRAE 55-2020 §5.2.2.2(g) y Figura 5-1 permiten determinar el clo representativo del día a partir de la temperatura exterior a las 06:00, `ta(out,6)`, con el modelo de Schiavon & Lee (2013) **[verificado, ASHRAE 55-2020, p. 11 y apéndice informativo p. 47]**:

| `ta(out,6)` | `Icl` (clo) |
|---|---|
| < −5 °C | 1.00 |
| −5 ≤ `ta(out,6)` < 5 °C | `0.818 − 0.0364·ta(out,6)` |
| 5 ≤ `ta(out,6)` < 26 °C | `10^(−0.1635 − 0.0066·ta(out,6))` |
| ≥ 26 °C | 0.46 |

La norma añade que el modelo "está pensado para implementarse en software de simulación o sistemas de control", que se basa en estudios de campo "y puede no ser apropiado para todas las culturas y tipos de ocupación", y que no se aplica a ocupantes con más de 1.5 clo (§5.2.2.3). Para ocupantes en movimiento, `Icl,active = Icl·(0.6 + 0.4/M)` con 1.2 < M < 2.0 met (§5.2.2.2 e). EnergyPlus tiene en `People` el campo *Clothing Insulation Calculation Method* con la opción `DynamicClothingModelASHRAE55` **[verificar el nombre exacto del campo y de la opción en el IDD de 25.2 antes de codificar; las ecuaciones de arriba sirven para el test]**. `set_pmv_input_parameters` hoy fija un clo constante.

**Diseño.**
- `set_pmv_input_parameters(building, clo=0.5 | 'dynamic_ashrae55' | {'heating_season': 1.0, 'cooling_season': 0.5} | callable)`; para el diccionario, una `Schedule:Compact` con los periodos de `cooling_season_start/end`; para `callable(rmot) -> clo`, generar un `Schedule:File` anual desde el EPW (vía E1) o Erl por tramos.
- Lo mismo para `met` (p. ej. 1.0 noche / 1.2 día) reutilizando la lógica de schedules.
- Exponer en `accim.sim.people` una función `set_clothing_method(building, method, schedule=None)`.

**Prompt para Copilot.**
```
Extend accim.sim.apmv.set_pmv_input_parameters so that clo accepts a float, the string 'dynamic_ashrae55' (sets the People field Clothing Insulation Calculation Method to DynamicClothingModelASHRAE55 — check the field name in the IDD with eppy's idfobjects fieldnames), or a dict {'heating_season': x, 'cooling_season': y} that writes a Schedule:Compact aligned with cooling_season_start/end. Accept the same dict form for met. Add tests with the sample IDF that check the People object fields and the schedule values on day 120, 121, 274 and 275, document in docs/source/4_detailed use.md and add CHANGELOG.md [Unreleased] and DEVLOG.md entries.
```

### A6. Consignas basadas en SET* o PPD (P2)

EnergyPlus publica *Zone Thermal Comfort Pierce Model Standard Effective Temperature* y *Fanger Model PPD* **[verificar nombres exactos de las variables de salida]**. Dos vías: (a) Erl con corrección proporcional de la consigna de temperatura a partir del SET del paso anterior (`T_sp += k·(SET_target − SET_prev)`, con saturación); (b) hook del backend API con pythermalcomfort (`set_tmp`) y bisección como en A4. Útil para la zona de confort SET de ASHRAE 55 con velocidad de aire elevada (modo mixto con ventiladores). Depende de A4.

---

## 4. Bloque B — Modelo CUSTOM y modelos regionales

### B1. Métrica exterior configurable en el modelo CUSTOM

**Motivación.** Los modelos regionales que se quieren reproducir (proyecto "New regional model paper") usan métricas exteriores distintas: media móvil exponencial con α ≠ 0.8, media mensual, media diaria, media de 7 días (IMAC), y la `Te,ref` neerlandesa de la ATG, `Te,ref = (1·T_hoy + 0.8·T_ayer + 0.4·T_−2 + 0.2·T_−3)/2.4`, donde cada `T` es la **media de la máxima y la mínima diarias**, no la media de las 24 h **[verificado, van der Linden et al. 2006, §3]**. ASHRAE 55-2020 §5.4.2.1 **[verificado]** admite para la prevailing mean una media aritmética simple de 7 a 30 días consecutivos anteriores, o una ponderación decreciente en la que el peso de cada día es entre 0.6 y 0.9 del peso del día siguiente (sin límite superior de días en ese caso); la media diaria es la media de todas las observaciones del día. En 1.1.0 el CUSTOM sólo usa `PMOT` **[verificado: `set ComfTemp = PMOT*m+n`]**.

**Diseño.**
- Nuevo argumento `custom_outdoor_metric` (clave `CustAST_metric` en `AddAccis.arguments`): `'pmot'` (actual, por defecto), `'rmot'` (sensor CEN), `'rmot_alpha'` + `custom_alpha` (validar 0.6–0.9 según ASHRAE 55-2020 §5.4.2.1, con aviso fuera de ese rango), `'daily_mean'`, `'7drm'`, `'30drm'` (o `'ndrm'` + `custom_days` entre 7 y 30), `'monthly_mean'`, `'te_ref_nl'` (con medias de máxima y mínima diarias: acumular `Tmax`/`Tmin` del día en Erl con `@Max`/`@Min`).
- Implementación sin `EnergyManagementSystem:TrendVariable` (no soportado por el backend API, R-05): acumular en Erl la media diaria (`set Tsum = Tsum + Tout*ZoneTimeStep; set Hsum = Hsum + ZoneTimeStep` y, cuando `Hour == 0 && Minute == ZoneTimeStep*60`, cerrar el día: `set Tday_1 = Tsum/Hsum`, desplazar `Tday_2..7`, `set RMOTa = (1-alpha)*Tday_1 + alpha*RMOTa`). Arranque: inicializar `RMOTa` con la media del primer día (o con `PMOT`) en el calling point `BeginNewEnvironment`. Las medias mensuales se precalculan en Python desde el EPW al generar el IDF (12 constantes en `SetInputData`) — documentar que entonces el IDF está ligado al EPW.
- `set ComfTemp = Tout_metric*m+n` donde `Tout_metric` es una variable global que el programa `SetOutdoorMetric` rellena según `CustAST_metric`.
- Actualizar `print_setpoint_ems_code` / `get_setpoint_ems_code`, `verify_accim_simulation` (E2) y la GUI.
- Añadir la métrica como salida (`Output:Variable` EMS `Tout_metric`) para comprobarla en `Table`.

**Tests.** Comparar `RMOTa` con α=0.8 frente al sensor `RMOT` nativo (diferencias sólo en el arranque); `7drm` frente a cálculo en pandas desde el EPW; backend EMS vs API.

**Prompt para Copilot.**
```
In accim/sim (arguments.py, ems/program_lines.py, ems/objects.py, ems/inputs.py, accis.py) add the argument custom_outdoor_metric (key 'CustAST_metric') for the CUSTOM comfort standard (ComfStand 99), with values 'pmot' (default, current behaviour), 'rmot', 'rmot_alpha' (with custom_alpha), 'daily_mean', '7drm', '30drm', 'monthly_mean' and 'te_ref_nl'. Implement the running means in Erl without EnergyManagementSystem:TrendVariable (the API backend does not support it): accumulate the daily mean of the outdoor dry-bulb sensor and update the running mean at the end of each day; for 'monthly_mean' precompute the 12 values from the EPW given to AddAccis. SetComfTemp for ComfStand 99 must use the new global variable Tout_metric. Update print_setpoint_ems_code/get_setpoint_ems_code, the GUI form, docs/source/4_detailed use.md and add tests comparing the Erl running mean (alpha=0.8) with the native RMOT sensor and the 7-day mean with a pandas computation from the EPW. Add CHANGELOG.md [Unreleased] and DEVLOG.md entries.
```

### B2. CUSTOM con varios regímenes (ecuaciones condicionadas)

**Motivación.** Muchos modelos regionales no son una sola recta: cambian de ecuación según el modo (NV frente a AC en modo mixto, como IMAC-C NV/MM), según un umbral de temperatura exterior (p. ej. el modelo bilineal), por estación (calefacción/refrigeración) o por zona climática (GB/T 50785 frío / cálido-templado). Hoy el CUSTOM tiene una recta, dos offsets y cuatro límites **[verificado: `CustAST_m/n`, `CustAST_ACSToffset/AHSToffset`, `CustAST_ACSTall/aul`, `CustAST_AHSTall/aul`]**.

**Diseño.**
- Dataclass `accim.sim.arguments.CustomRegime(slope, intercept, cooling_offset, heating_offset, cooling_lower_limit, cooling_upper_limit, heating_lower_limit, heating_upper_limit, condition)` con `condition` ∈ `{'always', 'cooling_season', 'heating_season', 'hvac_off', 'hvac_on', ('metric_below', x), ('metric_above', x)}`.
- `AddAccis(custom_regimes=[CustomRegime(...), ...])`; el régimen actual se resuelve en Erl con una cadena `if/elseif` que escribe `m`, `n` y los límites en las variables ya existentes, de modo que `SetComfTemp`, `SetAppLimits` y `ApplyCAT` no cambian.
- Compatibilidad: los argumentos `CustAST_*` escalares siguen funcionando (un solo régimen `'always'`).
- Paramétrico: `CustAST_m_1`, `CustAST_n_1`, … generados dinámicamente (ver C1).

### B3. Registro de modelos de confort externos (plugins)

**Motivación.** Añadir un modelo nacional hoy exige tocar `standards.py`, `program_lines.py` (`SET_COMF_TEMP`, límites, `COUNT_HOURS`), `setpoint_lines.py`, la GUI y publicar una versión. El proyecto de modelos regionales (Qatar, Indraganti & Boussaa 2018; Japón, Aqilah 2025; etc.) necesita poder distribuir modelos como archivos.

**Diseño.**
- `accim.sim.standards.register_comfort_standard(standard: ComfortStandard, definition: ComfortStandardDefinition)` donde `ComfortStandardDefinition` contiene: métrica exterior (B1), `comfort_temperature` (pendiente/ordenada o regímenes de B2), límites de aplicabilidad, categorías con offsets (simétricos o asimétricos), modos de confort admitidos (0–3), cita.
- Carga desde YAML: `accim.sim.standards.load_comfort_standards('path/*.yaml')`; esquema documentado con un ejemplo (`accim/sample_files/comfort_standards/example_regional_model.yaml`). Números de ComfStand reservados ≥ 100 para externos. Primer ejemplo real para el YAML **[verificado, Indraganti & Boussaa 2018, ec. 5 y Tabla 10]**: Qatar (oficinas con HVAC), `Tc = 0.049·Tr + 22.5` con `Tr` la media móvil exterior (N = 3742, R² = 0.015, p < 0.001, SE = 0.007; temperatura de confort media 24.0 °C), con `Tr` medio 30.7 °C. La misma Tabla 10 recoge Rijal et al. (Japón, calefacción y refrigeración) `Tc = 0.065·Tr + 23.9`, Manu et al. (India, modo mixto) `Tn = 0.28·Tr + 17.87` e Indraganti et al. (India) `Tc = 0.15·Tr + 22.1`. El R² de Qatar (0.015) y la pendiente casi nula aconsejan que el YAML lleve un campo `evidence` (N, R², rango de `Tr`) que `print_setpoint_ems_code` muestre.
- Los generadores Erl recorren el registro en lugar de los diccionarios literales; los 24 modelos actuales se siguen definiendo en código (sin cambio de salida: test de regresión sobre los IDF de salida de ejemplo).
- GUI y `print_setpoint_ems_code` leen el registro.

**Prompt para Copilot.**
```
Design a plugin registry for comfort standards in accim/sim/standards.py: ComfortStandardDefinition (outdoor metric, comfort temperature slope/intercept or regimes, applicability limits, categories with symmetric or asymmetric offsets, allowed comfort modes, citation), register_comfort_standard() and load_comfort_standards(yaml_path). Make accim/sim/ems/program_lines.py (SET_COMF_TEMP, SET_APP_LIMITS, APPLY_CAT, COUNT_HOURS) and setpoint_lines.py build their Erl from the registry for numbers >= 100, while the built-in standards 0-22 and 99 keep their literal lines; add a regression test that the output IDFs of the sample models are byte-identical. Provide accim/sample_files/comfort_standards/example_regional_model.yaml and a how-to notebook. Update GUI lists, print_setpoint_ems_code, docs, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### B4. Actualización del modelo JPN Rijal (ComfStand 3)

**[verificar con texto completo]** ComfStand 3 usa offsets de ±2.5 K (90 %) y ±3.5 K (80 %); Aqilah, Rijal, Yoshida & Nicol (2025, *Energy & Buildings*, 10.1016/j.enbuild.2025.115469) propondrían ±1.5 K (90 %) y ±2.0 K (80 %) para viviendas japonesas. Para no romper resultados publicados: añadir categorías nuevas (p. ej. `CAT 90.2025`/`80.2025` o un ComfStand 23 "JPN Aqilah 2025") en lugar de cambiar las existentes. Con B3 sería un YAML.

### B5. Suelo sanitario de calefacción

**Motivación.** El artículo de adaptación al frío fija un suelo de 18 °C (OMS) en el conjunto admisible y reporta horas por debajo de 18/17/16 °C y 20–21 °C para grupos vulnerables. Hoy el único freno inferior es `AHSTall` (límite de aplicabilidad), que cambia de ecuación en vez de acotar la consigna.

**Diseño.** Argumento `heating_setpoint_floor` (clave `AHSTfloor`, por defecto `None`) aplicado en `ROUNDING`/final de `SetAST`: `if AHST < AHSTfloor; set AHST = AHSTfloor; endif` (y análogo `cooling_setpoint_ceiling`, `ACSTceil`). Válido para todos los ComfStand, para aPMV/ePMV (sobre la consigna de temperatura resultante no procede; documentar que ahí se aplica al PMV) y como parámetro del paramétrico. Contadores `HoursBelow_<T>` configurables (`report_hours_below=[18, 17, 16]`) en `COUNT_HOURS` o en `Table` (D1).

---

## 5. Bloque C — Paramétrico y optimización

### C1. Parámetros personales y de los índices nuevos

Añadir en `accim/parametric_and_optimisation/parameters.py` clases `Parameter` para: `Clo`, `Met`, `AirVelocity` (envuelven `set_pmv_input_parameters`), `ExpectancyFactor` (A1), `AdaptiveCoefficientCooling/Heating` ya existen en `params_dicts` → comprobar que tienen clase; `HeatingSetpointFloor` (B5); `CustAST_metric`/`CustAST_alpha` (B1); regímenes de B2 generados con una fábrica `custom_regime_parameters(n_regimes)`. Actualizar `get_available_params_apmv_setpoints()` y `get_available_params_accim_custom_models()`, y los planes de `sampling_full_set()`.

**Prompt para Copilot.**
```
In accim/parametric_and_optimisation/parameters.py add Parameter subclasses Clo, Met, AirVelocity (they call accim.sim.apmv.set_pmv_input_parameters on the model), ExpectancyFactor (apply_epmv_setpoints), HeatingSetpointFloor and CustAST_metric/CustAST_alpha, following the pattern of the existing classes and of funcs_for_besos/param_apmv.py; register them in params_dicts.py and in get_available_params_apmv_setpoints()/get_available_params_accim_custom_models(). Add tests in tests/parametric_and_optimisation that build a two-point design for Clo and check the clo schedule value in the generated IDFs. Update parametric_and_optimisation.rst, CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### C2. Objetivos de confort de largo plazo

En `objectives.py`, junto a las horas de confort actuales: horas fuera de rango y grados-hora ponderados de EN 16798-2 Anexo F (criterios por categoría), PPD-ponderado (Anexo F, método del PPD), criterios CIBSE TM52 (1: horas con ΔT ≥ 1 K > 3 % de las ocupadas; 2: exceso diario ponderado ≤ 6; 3: ΔT ≤ 4 K) y TM59 para viviendas, aplicables a las zonas en free-running del modo mixto. Reutilizan D1. **[verificar umbrales en EN 16798-2 y TM52 con los documentos]**

### C3. Desacoplar el paramétrico de besos (propuesta de iniciativa R-06 para `ROADMAP.md`)

- Objetivo: eliminar `besos` (y `pulp<4`, `datapackage`, parches de `_besos_compat.py`) sustituyendo `Evaluator` por una clase propia que (a) aplique los `Parameter` con eppy, (b) ejecute `run_ep` (EMS o API) en paralelo con `concurrent.futures`, (c) lea resultados con `Table`/lectores actuales; platypus directo para `run_optimisation` y SALib para la sensibilidad (ambos ya son dependencias).
- Exit criteria: `tests/parametric_and_optimisation_full_workflow` idéntico; `pip install accim` sin besos; `requirements-dev.txt` sin pins heredados.
- Dependencias: E3 (pyproject con extras), tests de regresión del flujo completo.

---

## 6. Bloque D — Postproceso (`Table`)

### D1. Indicadores de disconfort de largo plazo

Nuevo módulo `accim/data/postprocessing/long_term_discomfort.py` con funciones puras sobre DataFrames horarios: `hours_outside_range`, `degree_hours` (EN 16798-2 Anexo F, con pesos por categoría), `ppd_weighted_hours`, `tm52_criteria`, `tm59`, `hours_below(thresholds)`; `Table` las expone como columnas agregadas opcionales (`long_term_indicators=True`). Mantener la separación que pide R-04 (no engordar el constructor de `Table`; módulo aparte).

### D2. Columnas de los índices nuevos en `Table`

Reconocer `ePMV_<zone>`, `e_<zone>`, `aPMV_<zone>`, `Tout_metric`, `HoursBelow_*` en las tablas de renombrado (`rename_cols`) y en las figuras de `time_plot`.

---

## 7. Bloque E — Verificación, herramientas y empaquetado

### E1. `compute_setpoints()`: consignas sin EnergyPlus

**Motivación.** `print_setpoint_ems_code` muestra el Erl; el paso siguiente es ejecutarlo. `accim.sim.ems.erl` ya interpreta Erl con las reglas del EMS **[verificado en el CHANGELOG 1.0.0]**. Con la serie exterior de un EPW se pueden calcular `RMOT`/`PMOT` (fórmulas de EN 16798-1 α=0.8 y de ASHRAE 55) y evaluar `SetAppLimits`, `ApplyCAT`, `SetComfTemp`, `SetAST_Master` y `SetAST_CS*` hora a hora.

**Diseño.** `accim.sim.preview.compute_setpoints(epw, comfort_standard, category, comfort_mode, **custom_args) -> pandas.DataFrame` con columnas `datetime, Tout, RMOT, PMOT, ComfTemp, ACST, AHST, applicable, cooling_season`; `plot_setpoints(df)` con matplotlib. Usos: previsualización para usuarios y docs, tests de regresión del Erl de cada ComfStand (se comparan con los CSV de EnergyPlus de `accim/sample_files` con tolerancia de redondeo), y generación de `Schedule:File` para A5/B1.

**Prompt para Copilot.**
```
Create accim/sim/preview.py with compute_setpoints(epw, comfort_standard, category=None, comfort_mode=None, **custom_arguments) that reads the EPW dry-bulb series with pandas, computes RMOT (EN 16798-1 exponential running mean, alpha 0.8, the EnergyPlus start-up convention) and PMOT (ASHRAE 55 prevailing mean as EnergyPlus computes it), and evaluates the ACCIS Erl programs returned by accim.utils.get_setpoint_ems_code with the Erl interpreter of accim.sim.ems.erl, hour by hour, returning a DataFrame (datetime, Tout, RMOT, PMOT, ComfTemp, ACST, AHST, applicable, cooling_season). Add plot_setpoints(df). Write tests that compare the DataFrame with the hourly CSV of an EnergyPlus simulation of the sample IDF (tolerance = the SetpointAcc rounding). Document in docs/source/4_detailed use.md (section after print_setpoint_ems_code), CHANGELOG.md [Unreleased] and DEVLOG.md.
```

### E2. `verify_accim_simulation` para los índices nuevos

Extender las comprobaciones a `ePMV = e·PMV`, `aPMV = PMV/(1+λ·PMV)`, `Tout_metric` frente a cálculo en pandas, y `AHST >= AHSTfloor`.

### E3. Empaquetado y CI

- Migrar `setup.py` a `pyproject.toml` (PEP 621) con `extras_require`: `comfort` (pythermalcomfort), `gui`, `optimisation` (platypus, SALib), `dev`. Mantener `setup.py` mínimo si los `.bat` de `packaging/` lo requieren.
- GitHub Actions: lint + tests unitarios sin EnergyPlus en cada push; un job semanal que instale EnergyPlus (instalador silencioso de Windows o imagen Linux) y ejecute el test de humo de un IDF de ejemplo con ambos backends.
- `python_requires` explícito y matriz 3.10–3.13.

### E4. Integración con pyfwg y pyweatherfiles

`accim.data.morphing.morph_epws()` → delegar opcionalmente en `pyfwg` (Future Weather Generator) y aceptar TMY de `pyweatherfiles`; sólo si están instalados (`extras_require['weather']`). Documentar el flujo EPW presente → EPW futuros → `run_ep` → `Table` en un cuaderno.

---

## 8. Orden de implementación sugerido

1. **Sprint 1 (fundamentos, P1, bajo riesgo):** A2 (motor común) → A1 (ePMV) → D2 → E2. Resultado: 1.2.0 con ePMV.
2. **Sprint 2 (CUSTOM y regionales):** B1 (métrica exterior) → B5 (suelo) → C1 (parámetros) → E1 (`compute_setpoints`, que además sirve de test de B1).
3. **Sprint 3:** B2 (regímenes) → B3 (registro/plugins) → B4 (JPN 2025 como primer plugin externo) → A5 (clo dinámico).
4. **Sprint 4 (P2):** A3, D1, C2, E4.
5. **Largo plazo:** A4/A6 (índices vía backend API), C3 (sin besos, R-06), E3.

Cada sprint cierra con: entrada en `CHANGELOG.md [Unreleased]`, nota en `DEVLOG.md`, notebooks regenerados (como se hizo en 1.1.0), `verify_accim_simulation` en verde con los IDF de ejemplo.

---

## 9. Textos completos: disponibles en la biblioteca y pendientes de descargar

Biblioteca consultada: `D:\Python\local-reference-manager` (1776 documentos en `vigilancia_20261105/after.json`, 1221 con PDF; rutas locales en `exportacion_mendeley_20261101/inventario_para_api.json`; los archivos `referencias.xlsx`, `articulos.csv`, `archivos.csv` y `.lrm/*` no son legibles desde el sandbox por permisos, pero el JSON del inventario contiene lo mismo).

### 9.1 Disponibles y ya leídos (lo extraído está incorporado arriba)

| Propuesta | Referencia | Archivo en Mendeley library | Qué se ha tomado |
|---|---|---|---|
| A1 | Fanger & Toftum 2002, *E&B* 34, 533–536 | `Ole Fanger, Toftum_2002_Extension of the PMV model...pdf` (texto no extraíble; leído como imagen) | Tabla 1 (`e`), 6.7 %/unidad PMV, Tabla 3 (`0.5/e`), sólo límite superior |
| A3 | Yao, Li & Liu 2009, *B&E* 44 | `Yao, Li, Liu_2009_A theoretical adaptive model...pdf` | λ 0.293 / −0.125 |
| A3 | Zhang, Yao & Li 2024, *B&E* 256, 111481 | `Zhang, Yao, Li_2024_An improved approach...pdf` | Tabla 1 (GB/T 50785), Tabla 2 (grados), Tabla 6 (λN/λP por Köppen) |
| A3 | Zhang, Cheng & Fang 2019, *B&E* 163, 106318 (algoritmo λP); Zhang & Lin 2020, *Indoor Air* (λ variable) | en la biblioteca | No leídos aún; útiles para la nota metodológica del catálogo |
| A4 | Schweiker & Wagner 2015, *B&E* 94, 252–262 | `Schweiker, Wagner_2015_A framework for an adaptive thermal heat balance model (ATHB).pdf` | ecs. 1–5, a = 1.25, b = −0.030, c = 18 °C, d = −0.0178, −0.049/punto de control |
| A5, B1 | ANSI/ASHRAE 55-2020 (y 55-2013) | `Arens et al._2021_Thermal Environmental Conditions for Human Occupancy.pdf`; `ANSIASHRAE_2013_...pdf` | §5.2.2.2(g) y p. 47 (clo dinámico), §5.4.2.1 (prevailing mean), §5.4.1 (aplicabilidad) |
| B1 | van der Linden et al. 2006, *E&B* 38, 8–17 (ATG) | `van der Linden...2006...pdf` | Fórmula de `Te,ref` con medias de máx./mín. diarias; Alpha usa límites Beta bajo `Te,ref` 10–12 °C |
| B3 | Indraganti & Boussaa 2018, *E&B* | `Indraganti, Boussaa_2018_An adaptive relationship...GCC...pdf` | ec. 5 y Tabla 10 |
| D1 | Li, Parkinson, Schiavon et al. 2020, *B&E* (índices de confort a largo plazo para monitorización continua) | en la biblioteca | No leído aún; candidato a base de `long_term_discomfort.py` |
| — | Humphreys & Nicol 2002 (validez del ISO-PMV); Nicol & Humphreys 2010 (derivación EN 15251); de Dear & Brager 2002 (ASHRAE 55) | en la biblioteca | Contexto; ya usados en el proyecto de adaptación al frío |

### 9.2 Pendientes de descargar (en orden de necesidad)

1. **Schweiker, M. (2022)** — la actualización del ATHB que implementa `pythermalcomfort.models.pmv_athb` (citada allí como `[Schweiker2022]`; comprobar el DOI en el docstring de pythermalcomfort). Sin ella no se pueden validar los coeficientes de A4.
2. **Aqilah, N., Rijal, H.B., Yoshida, K., Nicol, F. (2025)**, *Energy and Buildings*, 10.1016/j.enbuild.2025.115469 — para B4 (offsets ±1.5/±2.0 K, métrica exterior y límites). En la biblioteca sólo está la revisión de Aqilah et al. 2022 (*Energies* 15, 9012).
3. **EN 16798-1:2019** y **EN 16798-2:2019** (CEN/TR) — en la biblioteca figuran sin PDF. Necesarias para la definición de α (B1, Anexo B de la parte 1) y para los indicadores de largo plazo del Anexo F de la parte 2 (C2, D1).
4. **CIBSE TM52 (2013)** y **TM59 (2017)** — no están en la biblioteca; criterios de sobrecalentamiento para C2/D1.
5. **GB/T 50785-2012** (texto de la norma) — sin PDF; la Tabla 1 de λ ya está tomada de Zhang 2024, pero conviene el original para A3 y para los límites de aplicabilidad del método gráfico.
6. **ISO 7730:2005** — sin PDF; sólo para citar las categorías A/B/C (±0.2/0.5/0.7) en A2.
7. **Schiavon & Lee 2013**, *B&E* 59, 250–260 — no está en la biblioteca (el inventario no tiene el DOI 10.1016/j.buildenv.2012.08.024), pero las ecuaciones ya están verificadas en ASHRAE 55-2020, p. 47; descargar sólo si se quiere citar el original en la documentación de A5.
8. **Boerstra et al. 2015** (nueva guía híbrida neerlandesa, ISSO 74 rev.) — sin PDF; sólo si B1 incluye la versión revisada de `Te,ref`.

Cuando estén descargados, el siguiente paso es una `_v03` de este documento con los coeficientes de A4 y B4 y los criterios de C2/D1 verificados.

---

## 10. Plantillas

**Entrada de `CHANGELOG.md [Unreleased]` (estilo 1.1.0):**
```md
### Added
- **`accim.sim.apmv.apply_epmv_setpoints()`**: setpoints based on the ePMV index of Fanger and Toftum (2002), `ePMV = e·PMV`, with the expectancy factor `e` of each zone (0.5–1.0) applied in the cooling season; the Fanger thermostat receives `PMV = ePMV_sp/e`. Outputs `ePMV_<zone>` and `e_<zone>`, and the comfort hours in ePMV. Section 4.x of the detailed use.
```

**Test de regresión de IDF (patrón):**
```python
def test_output_idf_unchanged(tmp_path, sample_idf):
    before = read_text(reference_output_idf)
    after = AddAccis(...).output_idfs[0].idfstr()
    assert normalise(before) == normalise(after)
```

**Prompt genérico para Copilot (cabecera común):**
```
You are working on accim 1.1.0 (D:\Python\accim). Rules: PEP 8, English names and docstrings (reST), eppy for IDF I/O (never besos), Erl generated through accim.sim.ems, both run_ep backends ('ems' and 'api') must give identical CSVs, tests with pytest in tests/, every change logged in CHANGELOG.md [Unreleased] and DEVLOG.md, deprecations through accim._deprecation. Task: <paste the proposal prompt>.
```
