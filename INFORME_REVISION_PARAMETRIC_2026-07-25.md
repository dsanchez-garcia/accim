# Informe de revisión — `accim/parametric_and_optimisation`

**Fecha:** 2026-07-25
**Rama:** `refactor/outputs-api-consolidation` — revisión sobre `14c9570`, re-verificada contra `1907287` (los commits `1298e69` y `1907287` tocan `main.py`, `parameters.py` y `utils.py` pero no invalidan ningún hallazgo; ver notas en R3 y P13)
**Alcance:** los 10 módulos del paquete + subpaquete `funcs_for_besos` (~23.800 líneas en total).
**Relación con la revisión anterior:** el informe `INFORME_REVISION_2026-07-19.md` (rama `refactor/sim-v1`, tareas T00–T57) excluyó explícitamente este módulo. Este informe lo cubre; su plan asociado usa numeración **P00–P44** para no colisionar.

---

## 1. Resumen ejecutivo

El módulo es funcional y tiene una batería de tests amplia (28 ficheros de test unitarios + 5 de workflow completo), pero arrastra tres problemas de fondo:

1. **`main.py` es un god-module de 12.615 líneas** con una sola clase `SimulationBase` de ~150 métodos que mezcla 10 responsabilidades distintas (comparación de resultados, gestión de outputs, sampling, category mapping, summaries, checkpoints, ejecución paramétrica, ejecución de optimización, extracción de dataframes, ficheros). Es el mayor riesgo de mantenibilidad del paquete.
2. **Hay bugs de corrección reales**, dos de ellos potencialmente graves en resultados de simulación: los parámetros adicionales (`additional_params`) probablemente **no se aplican al IDF** en `run_parametric_simulation` (P01), y en sesiones multi-IDF con modelo custom el baseline EMS solo se aplica al **primer** edificio (P02).
3. **Ruido masivo de docstrings autogenerados** ("Argument used by X", "Usage: Use X within ACCIM workflows", `result = <module>()`), algunos incorrectos (documentan parámetros que no existen), que ocultan la documentación real y engordan los ficheros ~30–40 %.

Nada de lo encontrado exige reescritura: todo es corregible de forma incremental con tests de regresión.

---

## 2. Metodología

- Lectura completa de: `__init__.py`, `params_dicts.py`, `objectives.py`, `patches.py`, `file_cleanup.py`, `utils.py`, `parameters.py`, `funcs_for_besos/*`, `analysis.py`.
- Lectura dirigida de `plotting.py` (helpers comunes + 3 métodos representativos + índice de los 12 métodos de plot) y de `main.py` (worker, `SimulationBase.__init__`, `set_parameters`, `set_problem`, samplings, `set_evaluator`, blueprints de tareas, `run_parametric_simulation`, `run_optimisation`, subclases finales).
- Verificación de usos con grep (p. ej., la clase legacy `Parameter` no se usa en ningún sitio del repo).
- No se ha ejecutado ningún test ni modificado ningún fichero.

---

## 3. Hallazgos críticos (bugs de corrección)

### C1. `additional_params` probablemente no se aplican en el worker paramétrico — **el más grave** *(pendiente de confirmar con test)*
`main.py:293` (`_run_single_evaluation_worker`): el worker reconstruye el problema con `dummy_inputs = [Parameter(name=n) for n in problem_names_inputs]` — parámetros BESOS **sin selector** — y luego aplica manualmente solo los setters ACCIS/APMV (`params_dicts.all_params`, línea 287-291). Cualquier parámetro adicional del usuario (p. ej., un `FieldSelector` de espesor de aislamiento) queda registrado como columna de entrada en los resultados pero **nunca se escribe en el IDF**. Como `run_parametric_simulation` usa este worker incluso con `processes=1`, afectaría a todos los runs paramétricos con `additional_params`. Resultados silenciosamente incorrectos.

### C2. Baseline EMS de modelo custom solo se aplica al primer edificio
`main.py:6117-6125` (`set_parameters`): con `parameters_type='accim custom model'` se aplica `modify_ComfStand(self.building, 99)`, `modify_ComfMod(..., 3)`, `modify_CAT(..., 80)` y los valores por defecto CustAST **solo a `self.building`** (el primero). En sesiones multi-IDF, los edificios 2..N conservan el ComfStand por defecto de `addAccis` → simulaciones con lógica de confort distinta por edificio sin aviso. Contraste: `AccimPredefModelsParamSim.__init__` (`main.py:12613-12614`) sí itera `for b in self.buildings`.

### C3. `Parameter.modify()` aplica los 25 modificadores a la vez
`parameters.py:319-347`: el método construye un dict cuyos *valores son el resultado de llamar* a los 25 `modify_*(idf, value)` — es decir, ejecuta todos los modificadores con el mismo valor sobre el IDF, y la línea final `parameters_accis[self.name]` no hace nada. Atenuante: **ni esta clase ni los 25 wrappers OO se usan en ningún punto del repo** (verificado por grep) — es código muerto peligroso. Además `Parameter.__init__` (líneas 260-286) omite `CustAST_ASTaul/ASTall/ASToffset` y todos los parámetros APMV, inconsistente con `params_dicts.all_params`.

### C4. `drop_invalid_param_combinations`: `continue` que salta validaciones
`param_accis.py:193-256`: cada chequeo está envuelto en `try/except KeyError: continue`. Si una columna no existe (p. ej. no se muestreó `CAT`), el `continue` **salta a la siguiente fila**, omitiendo todos los chequeos restantes de esa fila (VentCtrl×HVACmode, SetpointAcc, VOF, etc.). Deberían ser chequeos independientes condicionados a la presencia de la columna. Consecuencia: combinaciones inválidas pasan el filtro y se simulan.

### C5. `run_clustering` usa siempre `outputs_optimisation`
`analysis.py:2222`: la guarda permite ejecutar con `last_run_type == 'parametric'` (si `pareto_only=False`), pero `df = self.outputs_optimisation.copy()` está hardcodeado → `AttributeError` sobre `None` o, peor, clustering sobre resultados de una optimización anterior. También asume columna `'epw'` sin comprobarla y fija `random_state=42` sin parámetro.

### C6. `run_sensitivity_analysis_by_epw` corrompe estado si falla
`analysis.py:2098-2119`: intercambia temporalmente `self.outputs_param_simulation` por el subset del EPW y lo restaura **sin `try/finally`**. Si `run_sensitivity_analysis` lanza (p. ej. tamaño de muestra Sobol incompatible), la instancia queda con el subset filtrado como resultados "oficiales". Todas las operaciones posteriores del usuario operarían sobre datos truncados.

### C7. Normalización con área faltante: divide por 1 m² en silencio
`analysis.py:1663` (`normalize_outputs`), `analysis.py:2325` (`run_robustness_analysis`) y `plotting.py:522` (`_normalise_plot_columns`): cuando `building_floor_area` es un dict y un IDF no está en él, `fillna(1.0)` produce valores kWh/m² incorrectos sin ningún aviso. Debería lanzar error o, como mínimo, warning con los IDFs afectados.

### C8. Ambigüedad de nombres de backup por subcadena
`main.py:8340-8344` (`_iter_parametric_task_blueprints`): el matching del backup usa `f'_{idf_basename}_' in basename`. Si un IDF se llama `Model_A` y otro `Model_A_v2`, el patrón `_Model_A_` **también coincide** con `accim_idf_backup_Model_A_v2_...` → según el orden de la lista, un task puede simular el IDF equivocado. Mismo patrón de riesgo en `_normalise_floor_area_idf_name`.

### C9. Derivación de nombre EPW frágil
Patrón `epw.split('.epw')[0]` repetido (`main.py:8351`, `9787`, y otros): falla con extensión en mayúsculas (`.EPW`), y con rutas que contengan `.epw` en un directorio intermedio devuelve un prefijo de ruta. Debería ser `os.path.splitext(os.path.basename(epw))[0]` (con cuidado de compatibilidad: cambia el nombre de carpetas/keys en resultados existentes cuando el epw lleva ruta).

---

## 4. Hallazgos de robustez (importantes, no críticos)

| # | Localización | Problema |
|---|---|---|
| R1 | `utils.py:64-72` `descriptor_has_options` | `type(x) == int/float/np.float64` excluye `np.int64`/`np.int32`/`np.float32`. Una tupla `(np.int64(0), np.int64(2))` (salida típica de numpy/pandas) lanza `ValueError` incorrectamente. Usar `isinstance(x, numbers.Real)`. |
| R2 | `utils.py:186-222` `identify_hourly_columns` | Con df vacío o columnas todo-NaN, `.all()` sobre serie vacía devuelve `True` → todas las columnas se clasifican como horarias. El fallback duplica el mismo predicado vía `astype(str)`. |
| R3 | `utils.py` `expand_to_hourly_dataframe` | `start_date` por defecto `'2024-01-01 01'` (2024 es bisiesto: 8784 h vs 8760 h → desalineación silenciosa de fechas); `print` de depuración en producción; `except (ValueError, TypeError, SyntaxError, Exception)` — el `Exception` final hace redundante el resto. *Nota: el commit `1907287` añadió un fast-path vectorizado (rendimiento), pero estos tres puntos siguen presentes. El fast-path además fuerza `dtype=float` en las columnas horarias, dtype distinto al del fallback — verificar en P13.* |
| R4 | `analysis.py:1741-1793` `run_sensitivity_analysis` | Opera sobre `outputs_param_simulation` completo: con varios EPWs/IDFs mezcla filas de todos los climas → resultados SALib sin sentido o error críptico de tamaños. Debería detectar >1 EPW/IDF y exigir `run_sensitivity_analysis_by_epw` o filtro previo. |
| R5 | `main.py:6208, 6230` `set_parameters` | `input()` interactivo cuando `use_dflt_values=False` → bloquea ejecuciones headless/CI (stdin cerrado lanza EOFError). Debería fallar con mensaje claro o aceptar valores por argumento. |
| R6 | `main.py:9379-9390` | Exporta siempre CSV+**XLSX**+PKL+JSON. `to_excel` requiere `openpyxl` y falla con >1.048.576 filas (runs horarios grandes). Envolver en try/except o hacerlo opcional. |
| R7 | `patches.py` | Monkey-patching global de BESOS (`run_energyplus`, `to_platypus`). `to_platypus` se restaura en `finally` (bien, `main.py:9898`), pero el patch de `run_energyplus` es permanente. `GlobalAllCapsDict` solo redefine `__getitem__`: `.get()`, `in`, `.keys()` no son case-insensitive → fallos sutiles si BESOS usa esos accesos. |
| R8 | `patches.py:129-131, 216-217, 232-233, 246-247` y similares | `except Exception: pass` generalizado silencia errores reales de IO/permisos. Mínimo: log a stderr/warning. |
| R9 | `analysis.py:2312-2318` `run_robustness_analysis` | Borra **todos** los `BESOS_Output*` bajo `out_dir` tras cada EPW — si el usuario apunta `out_dir` a una carpeta compartida con otro run en curso, borra resultados ajenos. |
| R10 | `param_accis.py` / `param_apmv.py` | Escrituras EMS **posicionales** (`Program_Line_1 = 'set ComfStand = ...'`): si `addAccis` cambia el orden de líneas, se sobrescriben líneas equivocadas sin error. Un helper que localice la línea por contenido (`set <var> =`) sería robusto y centralizaría el patrón repetido 25 veces. |
| R11 | `param_accis.py:114-190` | El dict de combinaciones válidas está **duplicado** en `get_valid_param_combinations()` y `drop_invalid_param_combinations()`; ya divergirían silenciosamente si se actualiza uno. |
| R12 | `analysis.py` `set_building_floor_area` | Acepta el typo legacy `'air-condicioned'` (compat). Mantener pero documentar y emitir DeprecationWarning. |
| R13 | `main.py:9094` y `_get_salib_problem` | Accesos `self.problem` sin mensaje de error orientativo si no se llamó `set_problem()` antes (AttributeError crudo). |
| R14 | `plotting.py:1078-1081` | Uso de `g._legend` (API privada de seaborn) — frágil ante upgrades. |

---

## 5. Hallazgos de diseño y mantenibilidad

### M1. `main.py`: god-module (12.615 líneas)
`SimulationBase` concentra ~150 métodos. Bloques identificables y separables (con re-export para compatibilidad):

| Bloque | Líneas aprox. | Destino propuesto |
|---|---|---|
| Comparación de instancias/pickles (`compare_*`, `SimulationComparisonSession`) | 399–2864 (~2.500) | `comparison.py` |
| Gestión de outputs IDF (`scan_output_objects`, `set_output_*`, `discover/select/clear_outputs`, preflight) | 3304–6023 (~2.700) | `outputs_management.py` |
| Parámetros y sampling (`set_parameters`, `set_problem`, `sampling_*`) | 6024–6523 (~500) | `sampling.py` |
| Category mapping (`set/apply/preview_category_mapping`, sufijos EPW) | 6524–6955 (~430) | `category_mapping.py` |
| Summaries (`build/print/export_simulation_summary`) | 6956–7472 (~500) | `summary.py` |
| Serialización + checkpoints paramétrico/optimización | 7554–8438 (~880) | `checkpoints.py` |
| Ejecución (`run_parametric_simulation`, `run_optimisation`, workers, preflight) | 8439–10012 (~1.570) | `runners.py` (o quedarse en `main.py`) |
| Extracción de dataframes (`get_hourly_df*`, `get_output_df*`, agregaciones) | 10013–12051 (~2.000) | `results_extraction.py` |

### M2. `parameters.py`: ~1.450 líneas de código muerto duplicado
25 clases wrapper idénticas + clase legacy `Parameter` (con el bug C3). **Ningún uso en el repo** (código, tests, notebooks). Opciones: (a) eliminarlas en la próxima minor con nota en CHANGELOG; (b) mantener API generándolas programáticamente en ~15 líneas (`type()` en bucle sobre `params_dicts`). En `accis_parameter` (líneas 128-152): comas finales que crean tuplas accidentales (`parameter = Parameter(...),` + `return parameter[0]`), imports internos sin uso (`bf`, `np`), dict comentado de 38 líneas, y mensaje de error con typos ("Parameter do not exist… You need to chose…") que imprime `dict_keys(...)` crudo.

### M3. `plotting.py`: 12 métodos de plot con prólogo/epílogo clonados
Cada método público (~150–300 líneas) repite el mismo pipeline: `_get_plot_source_df` → `_filter_epw_rows` → `_apply_plot_data_filter` → chequeo de columnas → `_resolve_subplot_dimension_orders` → FacetGrid/figura → token EPW → `filename` vs `filename_template` (la validación de exclusividad está copiada 12 veces) → `savefig` + `print` + `close`. Extraer un helper de pipeline (preparación) y otro de guardado reduciría el fichero un ~40 % y garantizaría consistencia.

### M4. Docstrings autogenerados: ruido y errores
Patrón repetido en todo el paquete: parámetros documentados como "Argument used by X", ejemplos `result = <module>()` (literal, `plotting.py:13`), "Usage: Use X within ACCIM parametric and optimisation workflows" en cientos de métodos. Casos incorrectos: `set_parameters` documenta `:param HVACmode:` y `:param VentCtrl:` que **no existen** en la firma (`main.py:6054-6057`); `apply_data_filter` describe `strict` como "Boolean or mode flag controlling behaviour" (`utils.py:626`). Existe además un comentario-instrucción de generación olvidado en `parameters.py:350-355`.

### M5. `set_parameters`: triple bloque duplicado y lógica enrevesada
Los tres bloques de asignación de defaults (defaults automáticos / confirmación y / valores manuales, `main.py:6186-6247`) son idénticos salvo el dict de origen → un bucle sobre un mapping `{nombre: setter}` los colapsa. La validación options/ranges (6074-6108) no soporta mezclar listas y tuplas en `accis_params_dict` y no lo documenta (el error `TypeError('All Descriptors are not...')` es críptico).

### M6. `run_optimisation`: cadena de 16 `elif` por algoritmo
`main.py:9833-9866`: reemplazable por `getattr(optimizer, algorithm)` validado contra `available_algorithms`.

### M7. Imports pesados y duplicados
`analysis.py` y `plotting.py` importan `matplotlib.pyplot` y `seaborn` a nivel de módulo (y los **re-importan** dentro de métodos). `__init__.py` importa `main` eagerly → `import accim.parametric_and_optimisation` arrastra besos + matplotlib + seaborn (+ sklearn/SALib lazy). Para uso en clusters/headless conviene laziness o al menos `matplotlib.use('Agg')` documentado.

### M8. `param_apmv.py`: doble recorrido redundante
Cada función llama a `_get_apmv_program_targets` **y** `_get_apmv_input_programs_by_target` cuando la primera es exactamente `keys()` de la segunda; el bucle con `.get(zonename)` nunca puede dar `None`. Además ~40 líneas de código comentado repetido en 6 funciones.

### M9. Miscelánea
- Anotaciones erróneas: `value: any` (`param_accis.py:727, 752`), `idf: besos.IDF_class` usa un **módulo** como tipo.
- Mezcla `normalise`/`normalize` en nombres internos.
- `print()` como mecanismo de logging en todo el paquete (sin niveles ni supresión).
- `run_parametric_simulation` itera el generador de blueprints 3 veces (conteo, pendientes, ejecución) — correcto pero triplica el coste de iterar el plan.
- `patches.py`: pruning de Pareto O(n²) por lote (aceptable para tamaños típicos).
- `objectives.py`: correcto, sin problemas.
- `file_cleanup.py`: correcto y bien testeado; sin problemas relevantes.

---

## 6. Estado de tests

Cobertura existente razonable: `tests/parametric_and_optimisation/` (28 ficheros: base, sampling, runs, optimización, análisis, carga, plotting, cleanup, checkpoints, preflight, pareto, comparaciones, filtros, ordering) y `tests/parametric_and_optimisation_full_workflow/` (5 workflows E2E con IDFs y EPWs reales).

**Huecos detectados** (ningún test cubre): aplicación real de `additional_params` en el worker (C1), multi-IDF custom model (C2), `drop_invalid_param_combinations` con columnas ausentes (C4), `run_clustering` tras run paramétrico (C5), restauración de estado en `run_sensitivity_analysis_by_epw` con fallo (C6), área faltante en normalización (C7), colisión de nombres de backup (C8), EPW con `.EPW`/ruta (C9), numpy ints en descriptores (R1).

---

## 7. Decisiones que debe tomar el usuario

| ID | Decisión | Opciones |
|---|---|---|
| DP1 | Clases legacy de `parameters.py` (muertas + bug C3) | (a) eliminar en próxima minor · (b) generarlas programáticamente y deprecar · (c) solo arreglar el bug |
| DP2 | Cambio de derivación de nombre EPW (C9) | (a) corregir ya asumiendo que cambian keys/carpetas con EPWs con ruta · (b) corregir solo el caso `.EPW` mayúsculas y documentar |
| DP3 | División de `main.py` (M1) | (a) split completo en 8 módulos con re-exports · (b) split parcial (comparison + results_extraction, ~4.500 líneas) · (c) posponer |
| DP4 | `input()` interactivo en `set_parameters` (R5) | (a) eliminar y lanzar error claro · (b) mantener con detección de TTY |
| DP5 | Export XLSX automático (R6) | (a) hacerlo opt-in (`export_excel=False`) · (b) mantener envuelto en try/except |
| DP6 | Docstrings autogenerados (M4) | (a) limpieza completa (mucho diff) · (b) solo corregir los incorrectos |
| DP7 | Formato EMS posicional (R10) | (a) helper por contenido ahora · (b) posponer y añadir solo asserts de sanidad |

---

## 8. Priorización recomendada

1. **Fase 1 — Bugs de corrección** (C1, C2, C4–C7): riesgo real de resultados incorrectos en investigación publicable. C1 y C2 primero (afectan a resultados de simulación, no solo a post-proceso).
2. **Fase 2 — Robustez** (C3 vía DP1, C8, C9, R1–R9): errores de borde y estado.
3. **Fase 3 — Refactor estructural** (M1–M3, M5, M6, M8): sin cambio de comportamiento, con tests como red.
4. **Fase 4 — Calidad** (M4, M7, M9): docstrings, typing, logging, imports.

El detalle tarea a tarea está en `PLAN_IMPLEMENTACION_PARAMETRIC_2026-07-25.md`.
