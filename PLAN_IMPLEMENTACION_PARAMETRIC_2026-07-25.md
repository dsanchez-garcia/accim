# Plan de implementación — `accim/parametric_and_optimisation`

**Fecha:** 2026-07-25 · **Base:** `refactor/outputs-api-consolidation` (`1907287`; hallazgos verificados también contra los commits `1298e69` y `1907287`)
**Nota de desfase de líneas:** las referencias de línea del informe corresponden a `14c9570`. Tras la actualización, en `main.py` el bloque del batch-runner paramétrico (~9186 en adelante) se desplaza ~+36 líneas, y en `utils.py` todo lo posterior a `expand_to_hourly_dataframe` (~línea 150) se desplaza ~+45 líneas. El resto de referencias no varía.
**Informe asociado:** `INFORME_REVISION_PARAMETRIC_2026-07-25.md`
**Numeración:** P00–P44 (las tareas T00–T57 del plan de 2026-07-19 corresponden al resto del paquete y no colisionan).

Convenciones por tarea: **[archivo]** afectado · **[test]** de regresión a añadir · **[riesgo]** de romper compatibilidad (bajo/medio/alto) · **[dep]** dependencias · **[DP#]** decisión previa requerida (ver sección 7 del informe).

---

## Fase 0 — Salvaguardas (ejecutar antes de tocar nada)

### P00. Baseline de tests y rama de trabajo
- Crear rama `fix/parametric-review` desde la rama actual.
- Ejecutar la suite completa dos veces y guardar el log como baseline:
  - `pytest tests/parametric_and_optimisation -x -q` (rápidos)
  - `pytest tests/parametric_and_optimisation_full_workflow -q` (lentos, requieren EnergyPlus; anotar cuáles pasan hoy)
- Cualquier test que ya falle en baseline se anota y queda fuera del criterio de aceptación de este plan.
- **[riesgo]** n/a · **[dep]** ninguna

---

## Fase 1 — Bugs de corrección de resultados (prioridad máxima)

### P01. Verificar y corregir la no-aplicación de `additional_params` en el worker paramétrico (C1)
- **[archivo]** `main.py` (`_run_single_evaluation_worker`, ~línea 287-293)
- Paso 1 (verificación): test que cree un `additional_params` con `FieldSelector` (p. ej. `Lights.Watts_per_Zone_Floor_Area` o un campo trivial), ejecute `run_parametric_simulation` con 2 valores y `processes=1`, y compruebe en el `in.idf` copiado de cada carpeta de resultados que el campo cambió. Si BESOS aplica el valor (porque `Parameter(name=...)` conserva algún selector), documentar y cerrar.
- Paso 2 (corrección, si se confirma): serializar los selectors de `additional_params` igual que ya se hace con los readers de outputs (`_serialize_problem_outputs` es el patrón a imitar): módulo+qualname para funciones importables, o spec declarativa para `FieldSelector` (class_name, object_name, field_name). En el worker, reconstruir y aplicar antes de crear el evaluator. Si un selector no es serializable, **fallar en `run_parametric_simulation` con error claro**, nunca en silencio.
- **[test]** nuevo `test_additional_params_applied_in_worker.py` (con `bypass_addAccis=True` y IDF mínimo para no requerir EnergyPlus: basta inspeccionar el IDF que construye el worker; extraer la parte de preparación del worker a una función testeable si hace falta)
- **[riesgo]** medio · **[dep]** P00

### P02. Aplicar baseline EMS de modelo custom a todos los edificios (C2)
- **[archivo]** `main.py:6117-6125` y bloque de defaults 6186-6247 (`set_parameters`)
- Cambiar cada `bf_accim.modify_X(self.building, v)` por un bucle `for b in self.buildings:` (mismo patrón que `AccimPredefModelsParamSim.__init__`, `main.py:12613`). Incluye la aplicación de defaults y de valores de usuario.
- La lectura de `get_accim_args(self.building)` para decidir qué falta puede seguir usando el primero (los edificios pasan por el mismo `addAccis`), pero documentarlo.
- **[test]** sesión con 2 IDFs y `parameters_type='accim custom model'`; tras `set_parameters`, comprobar en ambos IDFs que `SetInputData.Program_Line_1 == 'set ComfStand = 99'` y los defaults CustAST aplicados.
- **[riesgo]** bajo · **[dep]** P00

### P03. Reescribir `drop_invalid_param_combinations` (C4)
- **[archivo]** `funcs_for_besos/param_accis.py:142-261`
- Sustituir la cadena de `try/except KeyError: continue` por chequeos vectorizados condicionados a la presencia de columna:
  ```python
  has = lambda c: c in df.columns
  valid = pd.Series(True, index=df.index)
  if has('ComfStand') and has('CAT'):
      valid &= df.apply(lambda r: r['CAT'] in VALID_COMBINATIONS.get(r['ComfStand'], ([], []))[0], axis=1)
  # ... resto de reglas, cada una independiente
  ```
- Unificar el dict duplicado: `drop_invalid_param_combinations` debe consumir `get_valid_param_combinations()` (una sola fuente, R11).
- No mutar el df de entrada (trabajar sobre copia, sin columna `valid` residual).
- **[test]** casos: (a) df sin columna `CAT` → las reglas VentCtrl/HVACmode siguen aplicándose; (b) combinación inválida CS=4/CAT=80 se elimina; (c) df de entrada no se modifica.
- **[riesgo]** bajo · **[dep]** P00

### P04. `run_clustering`: seleccionar el dataframe según `last_run_type` (C5)
- **[archivo]** `analysis.py:2184-2255`
- Si `last_run_type == 'parametric'` → `outputs_param_simulation` (y `pareto_only` debe ser False, ya validado); si `'optimisation'` → `outputs_optimisation`. Guardar el resultado en el atributo del que provino (no siempre en `outputs_optimisation`).
- Añadir: chequeo de columna `'epw'` (si no existe, clusterizar sin agrupar por EPW), parámetro `random_state: int = 42`.
- **[test]** clustering tras run paramétrico simulado (df inyectado a mano + `last_run_type='parametric'`, `pareto_only=False`).
- **[riesgo]** bajo (corrige un crash) · **[dep]** P00

### P05. `run_sensitivity_analysis_by_epw`: no corromper estado en fallo (C6)
- **[archivo]** `analysis.py:2098-2119`
- Opción preferida: refactorizar `run_sensitivity_analysis` para aceptar `df: Optional[pd.DataFrame] = None` (default: `self.outputs_param_simulation`) y eliminar el swap. Alternativa mínima: envolver el swap en `try/finally`.
- **[test]** provocar fallo en el análisis (p. ej. método sobol sobre muestras morris) y verificar que `self.outputs_param_simulation` conserva el df completo original.
- **[riesgo]** bajo · **[dep]** P00

### P06. Área de suelo faltante: error en vez de `fillna(1.0)` (C7)
- **[archivo]** `analysis.py:1660-1667` (`normalize_outputs`), `analysis.py:2323-2329` (`run_robustness_analysis`), `plotting.py:520-525` (`_normalise_plot_columns`)
- Extraer helper único `_resolve_area_divisors(df, area_attr, context) -> pd.Series` que: mapee áreas por IDF, y si hay IDFs sin área **lance `ValueError`** listándolos (o warning + exclusión de filas si se prefiere no romper — decidir en revisión de PR; recomendación: error, porque el dato resultante es incorrecto).
- **[test]** dict de áreas incompleto → error con el nombre del IDF ausente en el mensaje.
- **[riesgo]** medio (código que hoy "funciona" con valores erróneos pasará a fallar — es lo deseable) · **[dep]** P00

### P07. Matching exacto de backups de IDF (C8)
- **[archivo]** `main.py:8334-8347` (`_iter_parametric_task_blueprints`) y `_save_idf_backup` (3293-3299)
- En vez de matching por subcadena sobre el filename, construir el mapping determinista en `_save_idf_backup` (`self._idf_backup_by_name: dict[str, str]` con clave = idf_basename exacto) y consumirlo en el blueprint. Mantener el fallback actual solo para checkpoints antiguos.
- **[test]** dos IDFs `Model_A` y `Model_A_v2` → cada task recibe su backup correcto.
- **[riesgo]** bajo · **[dep]** P00

### P08. Derivación robusta de nombre EPW (C9) **[DP2]**
- **[archivo]** `main.py` (todas las ocurrencias de `.split('.epw')`: ~8351, 9787, y las que aparezcan con grep), `analysis.py:2305`
- Helper único `_epw_label(epw) -> str` = `os.path.splitext(os.path.basename(str(epw)))[0]` con lowercase de la extensión.
- Nota de compatibilidad: para EPWs pasados con ruta, cambian las keys de `evaluators` y etiquetas `epw` en resultados nuevos (los antiguos no se ven afectados). Documentar en CHANGELOG.
- **[test]** `'Seville.EPW'`, `'data/epws/seville.epw'`, `'C:\\x.epw\\seville.epw'`.
- **[riesgo]** medio (nombres de salida) · **[dep]** DP2

---

## Fase 2 — Robustez

### P09. `parameters.py`: resolver clases legacy (C3) **[DP1]**
- **[archivo]** `parameters.py:221-1812`
- Según DP1: (a) eliminar `Parameter` + 25 wrappers y el dict comentado 77-115 (recomendado: no hay ningún uso en repo, tests ni notebooks); anotar en CHANGELOG; o (b) generarlas programáticamente:
  ```python
  def _make_wrapper(name, func):
      return type(name, (), {'__init__': lambda self: setattr(self, 'name', name),
                             'modify': lambda self, idf, value: func(idf, value)})
  for _n, _f in params_dicts.all_params.items(): ...
  ```
- En cualquier caso, si se conserva `Parameter`, arreglar `modify` (dispatch por nombre, sin ejecutar los 25) y completar el dict de `__init__` desde `params_dicts.all_params`.
- **[test]** si se conservan: `Parameter('ComfStand').modify(idf, 1)` modifica solo `Program_Line_1` de `SetInputData` y ninguna otra línea.
- **[riesgo]** bajo · **[dep]** DP1

### P10. Limpiar `accis_parameter`
- **[archivo]** `parameters.py:42-152`
- Quitar comas finales/tuplas accidentales, imports internos sin uso, dict comentado; validar tupla de rango (`min < max`); mensaje de error corregido ("Parameter '<x>' does not exist. Valid parameters: [...]" con `sorted(list)`), matching case-insensitive conservado.
- **[test]** rango invertido `(2, 0)` → ValueError; mensaje contiene lista legible.
- **[riesgo]** bajo

### P11. `descriptor_has_options`: aceptar tipos numpy (R1)
- **[archivo]** `utils.py:38-72`
- `isinstance(v, numbers.Real)` (excluyendo `bool` explícitamente) para elementos de lista y tupla.
- **[test]** `(np.int64(0), np.int64(2))` → rango; `[np.float32(1.5)]` → options; `[True, False]` → ValueError.
- **[riesgo]** bajo

### P12. `identify_hourly_columns`: guardas de vacío y dedup del fallback (R2)
- **[archivo]** `utils.py:186-222`
- Si `len(df) == 0` → devolver `[]`. Columnas todo-NaN → no horarias. Eliminar el fallback duplicado (mismo predicado).
- **[test]** df vacío, df con columna NaN, df mixto.
- **[riesgo]** bajo

### P13. `expand_to_hourly_dataframe`: fechas y ruido (R3)
- **[archivo]** `utils.py` (la vectorización de rendimiento ya la aportó el commit `1907287`; esta tarea queda reducida a corrección/robustez)
- Documentar el significado de `start_date` y validar coherencia longitud-de-serie vs año elegido (warning si 8760 vs bisiesto). Sustituir `print` por `warnings.warn`/logging. Simplificar el except a `Exception` única con mensaje.
- Verificar la consistencia de dtypes entre el fast-path nuevo (fuerza `dtype=float` en columnas horarias) y el fallback fila-a-fila (preserva objetos): decidir un dtype canónico y testearlo en ambas rutas.
- **[test]** serie de 8760 h con default bisiesto → warning; mismo df por fast-path y fallback → mismos dtypes.
- **[riesgo]** bajo

### P14. Guarda multi-EPW/IDF en `run_sensitivity_analysis` (R4)
- **[archivo]** `analysis.py:1700-1793`
- Si `outputs_param_simulation` contiene >1 valor en `epw` o `idf` → `ValueError` indicando usar `run_sensitivity_analysis_by_epw` o `data_filter`. (Tras P05, si se añadió el parámetro `df`, la guarda aplica al df efectivo.)
- **[test]** df con 2 EPWs → error orientativo.
- **[riesgo]** bajo (convierte resultados basura en error) · **[dep]** P05

### P15. `set_parameters` headless (R5) **[DP4]**
- **[archivo]** `main.py:6204-6247`
- Según DP4: (a) eliminar la rama interactiva: `use_dflt_values=False` + parámetros sin definir → `ValueError` listándolos y explicando cómo definirlos; o (b) mantener `input()` solo si `sys.stdin.isatty()`.
- **[test]** `use_dflt_values=False` con faltantes en entorno no interactivo → error claro, no EOFError.
- **[riesgo]** bajo · **[dep]** DP4, coordinar con P22 (dedup del bloque)

### P16. Export XLSX tolerante (R6) **[DP5]**
- **[archivo]** `main.py:9379-9390` (`run_parametric_simulation`) y equivalente en `_save_outputs_optimisation_full`
- Según DP5: argumento `export_excel: bool = True` + try/except con warning (ImportError de openpyxl, límite de filas). CSV/PKL/JSON siguen siendo incondicionales.
- **[test]** monkeypatch de `to_excel` para lanzar → el run termina y emite warning.
- **[riesgo]** bajo

### P17. `GlobalAllCapsDict` completo y patches documentados (R7, R8)
- **[archivo]** `patches.py`
- Implementar `get`, `__contains__`, `setdefault` case-insensitive (o sustituir por normalización de claves al construir). Añadir docstring de módulo explicando qué se parchea de BESOS y cuándo se restaura. Sustituir los `except Exception: pass` por `except Exception as e: warnings.warn(...)` en operaciones de copia/borrado.
- **[test]** `'csv' in GlobalAllCapsDict({'CSV': 1})` → True; `.get('csv')` → 1.
- **[riesgo]** bajo

### P18. `run_robustness_analysis`: borrado acotado (R9)
- **[archivo]** `analysis.py:2300-2319`
- No borrar `BESOS_Output*` globalmente: usar un subdirectorio propio por llamada (`out_dir/robustness_<timestamp>/`) y limpiar solo ese, o registrar los dirs creados por el evaluator y borrar solo esos.
- **[test]** carpeta `BESOS_Output_ajena` preexistente sobrevive al análisis.
- **[riesgo]** bajo

### P19. Escrituras EMS por contenido (R10) **[DP7]**
- **[archivo]** `funcs_for_besos/param_accis.py`, `param_apmv.py`
- Helper `set_ems_program_line(program, var_name, value)` que localice la línea `set <var> =` por contenido entre los campos `Program_Line_*` y la reemplace; error claro si no existe. Reescribir los 25 `modify_*` sobre el helper (colapsa ~600 líneas repetidas). Si DP7=(b), añadir solo un assert de que la línea actual empieza por `set <var>` antes de sobrescribir.
- **[test]** IDF con líneas EMS en orden alterado → el valor va a la línea correcta / error claro (según opción).
- **[riesgo]** medio (toca el corazón de la escritura de parámetros; los goldens del workflow completo son la red)

### P20. `param_apmv.py`: eliminar doble recorrido y código comentado (M8)
- **[archivo]** `funcs_for_besos/param_apmv.py`
- Iterar directamente `_get_apmv_input_programs_by_target(idf).items()`; borrar `_get_apmv_program_targets` o dejarla como `keys()`. Eliminar los bloques comentados repetidos.
- **[test]** los existentes de APMV siguen pasando.
- **[riesgo]** bajo · **[dep]** P19 si se hace junto

### P21. Mensajes de error accionables para prerequisitos (R13)
- **[archivo]** `main.py` (`set_problem`, `sampling_*`, `run_*`, `_get_salib_problem`)
- Acceso a `self.problem`/`self.parameters_list`/`self.sim_outputs` inexistentes → error tipo "Llama antes a set_parameters()/set_outputs_for_simulation()/set_problem()". Un pequeño helper `_require_attr(name, hint)`.
- **[test]** llamar `set_problem()` sin `set_parameters()` → mensaje orientativo.
- **[riesgo]** bajo

---

## Fase 3 — Refactor estructural (sin cambio de comportamiento)

### P22. Deduplicar bloque de defaults en `set_parameters` (M5)
- **[archivo]** `main.py:6186-6247`
- Mapping `{'m': modify_CustAST_m, ...}` + un solo bucle parametrizado por el dict de valores (defaults o usuario). Documentar la restricción "todo listas o todo tuplas" y mejorar el `TypeError`.
- **[test]** los existentes (02, 03 custom model) + caso mezcla lista/tupla → error documentado.
- **[riesgo]** bajo · **[dep]** P02, P15

### P23. Despacho de algoritmos por nombre en `run_optimisation` (M6)
- **[archivo]** `main.py:9833-9866`
- `optimizer_cls = getattr(optimizer, algorithm, None)`; si `None` o no está en `available_algorithms` → KeyError actual. 34 líneas → 5.
- **[test]** el de optimización existente + algoritmo inválido.
- **[riesgo]** bajo

### P24. Pipeline común de plotting (M3)
- **[archivo]** `plotting.py`
- Extraer: (1) `_prepare_plot_df(df_source, df_long, epw_filter, data_filter*, context)`; (2) `_resolve_and_save_figure(fig, out_dir, default_filename, filename, filename_template, template_df, extra_context, context)` que centralice la exclusividad filename/template, token EPW, makedirs, savefig, print y close. Migrar los 12 métodos.
- **[test]** los de plotting existentes (07, hourly, parametric_new, subplot_ordering) sin cambios; comparar rutas de salida generadas antes/después para 2-3 métodos.
- **[riesgo]** medio (superficie amplia, pero mecánico) · **[dep]** P00

### P25. División de `main.py` — parte 1: comparación (M1) **[DP3]**
- **[archivo]** `main.py:399-2864` → nuevo `comparison.py`
- Mover `compare_simulation_instances`, `_collect_pickle_files`, `_order_pickle_files`, `_resolve_reference_pickle`, `compare_latest_pickles_in_folders`, `compare_multiple_pickles_with_reference`, `preflight_report`, `SimulationComparisonSession`. Re-export desde `main.py` y `__init__.py` (imports idénticos siguen funcionando).
- **[test]** `11_test_compare_simulation_instances.py` sin cambios; test de humo de imports antiguos.
- **[riesgo]** medio · **[dep]** DP3

### P26. División de `main.py` — parte 2: extracción de resultados (M1) **[DP3]**
- **[archivo]** `main.py:10013-12051` → nuevo `results_extraction.py` como mixin (`ResultsExtractionMixin`) del que herede `SimulationBase`.
- **[test]** `test_hourly_parametric_public_api.py` y afines sin cambios.
- **[riesgo]** medio · **[dep]** P25

### P27. División de `main.py` — parte 3: sampling + category mapping + summary + checkpoints (M1) **[DP3]**
- Igual que P26, en tres mixins (`sampling.py`, `category_mapping.py`, `summary_and_checkpoints.py` o separados). `main.py` queda con `SimulationBase.__init__`, runners y subclases (~4.000 líneas).
- **[test]** suite completa; smoke de imports.
- **[riesgo]** medio · **[dep]** P26

### P28. Única iteración del plan de tareas en `run_parametric_simulation`
- **[archivo]** `main.py:9112-9235`
- Materializar las signatures una vez (`list(...)`) y derivar total/pendientes de esa lista en vez de iterar el generador 3 veces. Mantener el streaming solo para la ejecución si el plan es muy grande (o aceptar materializar: cada task ya contiene `row_dict`, el plan completo cabe en memoria en la práctica).
- **[test]** `test_parametric_batch_checkpoint.py` sin cambios.
- **[riesgo]** bajo

### P29. Deduplicar la construcción de readers en el worker
- **[archivo]** `main.py:294-355` (`_run_single_evaluation_worker`)
- Los dos bloques (outputs y add_outputs) son idénticos → helper `_build_reader_from_spec(spec)`.
- **[riesgo]** bajo · **[dep]** P01

---

## Fase 4 — Calidad: docstrings, typing, logging, imports

### P30. Purga de docstrings autogenerados (M4) **[DP6]**
- **[archivo]** todos los del paquete
- Según DP6: (a) eliminar los bloques "Usage: Use X within ACCIM..." y parámetros "Argument used by X" sin contenido, dejando docstrings reales; o (b) solo corregir los incorrectos. En ambos casos, obligatorio: quitar `:param HVACmode:/:param VentCtrl:` fantasma de `set_parameters` (`main.py:6054-6057`), el `<module>` literal en `plotting.py:9-13` y `param_accis.py:25-30`, y el comentario-instrucción olvidado en `parameters.py:350-355`.
- **[riesgo]** nulo funcional; diff grande — hacerlo en commit propio sin mezclar con lógica.

### P31. Corrección de type hints
- **[archivo]** `param_accis.py` (`value: any` → `Any`; `idf: besos.IDF_class` — anotar como `Any` o `'IDF'` con TYPE_CHECKING), `param_apmv.py` ídem, revisar `Optional` faltantes en firmas con default `None` en `plotting.py`/`main.py`.
- **[riesgo]** bajo

### P32. Logging en lugar de `print`
- **[archivo]** todo el paquete
- `logger = logging.getLogger('accim.parametric')`; mapear `print('[info] ...')` → `logger.info`, `print('[!] ...')` → `logger.warning`; conservar `tqdm` para progreso. Mantener `verbosemode` conectando un handler por defecto para no cambiar la experiencia actual.
- **[riesgo]** medio (usuarios que capturan stdout) — documentar en CHANGELOG.

### P33. Higiene de imports (M7)
- **[archivo]** `analysis.py`, `plotting.py`, `main.py`
- Eliminar re-imports internos duplicados (`import os/pandas/matplotlib` dentro de métodos cuando ya están a nivel de módulo); mover seaborn/matplotlib de `analysis.py` a imports perezosos dentro de los métodos que los usan (solo 2 métodos los necesitan); documentar backend headless.
- **[riesgo]** bajo

### P34. Unificar utilidades duplicadas
- Token sanitizado de EPW/ficheros: usar `PlottingMixin._safe_plot_token` (o moverlo a `utils.py`) también en `analysis.py:2100-2103`.
- `_normalise_floor_area_idf_name` y la normalización de basenames de `_save_idf_backup`/`_get_idf_identifier`: una sola función en `utils.py`.
- **[riesgo]** bajo

### P35. DeprecationWarning para compat legacy
- `mode='air-condicioned'` (typo aceptado, `analysis.py:1406`), alias `building=` en constructores, `outputs_param_sim` property: emitir `DeprecationWarning` con fecha objetivo de retirada.
- **[riesgo]** bajo

---

## Fase 5 — Opcionales / rendimiento (solo si sobra presupuesto)

### P36. Vectorizar `drop_invalid_param_combinations` por completo (si P03 se hizo con `apply`)
### P37. Cache de lookups en `analysis.py` (`_get_zone_lookup` y familia se reconstruyen por llamada; memoizar por id(idf))
### P38. `_iter_list_object_values`: sustituir el sondeo `range(1, 500)` por inspección de `fieldnames` únicamente
### P39. Pruning Pareto de `patches.py` a O(n log n) o al menos short-circuit (solo si hay quejas de rendimiento con >5.000 evaluaciones)
### P40. `seaborn._legend` → API pública (`get_legend()`/`legendHandles` según versión) (R14)
### P41. Revisar `keep_sim_files='non-dominated'`: el batch-cleanup usa registros en memoria por worker (`_store_optimisation_records_in_memory`) — documentar que con `processes>1` el pruning por lotes es aproximado (cada worker ve solo sus registros)
### P42. `run_parametric_simulation`: opción `save_outputs=False` para benchmarks
### P43. Type-checking estático del paquete (mypy laxo o pyright basic) en CI
### P44. Documentar en `docs/` la arquitectura post-split (M1) y el flujo worker/checkpoint

---

## Orden de ejecución sugerido por sesiones

| Sesión | Tareas | Nota |
|---|---|---|
| **SP1** | P00, P01, P02 | Los dos bugs de resultados. P01 empieza por el test de verificación. |
| **SP2** | P03–P08 | Resto de Fase 1. P08 requiere DP2 decidido. |
| **SP3** | P09–P16 | Robustez. Requiere DP1, DP4, DP5. |
| **SP4** | P17–P21 | Robustez II. P19 requiere DP7 y correr los workflows E2E después. |
| **SP5** | P22–P24, P28, P29 | Refactors acotados sin split. |
| **SP6** | P25–P27 | Split de `main.py` (solo si DP3=a/b). Un commit por módulo extraído. |
| **SP7** | P30–P35 | Calidad. P30 en commit aislado. |
| **SP8** | P36–P44 | Opcionales, según presupuesto. |

**Protocolo por sesión:** (1) suite rápida antes; (2) implementar con un commit por tarea (`fix(parametric): ...` / `refactor(parametric): ...`); (3) suite rápida después de cada tarea y workflows E2E al cierre de SP1, SP4 y SP6; (4) actualizar CHANGELOG en las tareas con nota de compatibilidad (P06, P08, P09, P32, P35).

## Decisiones pendientes antes de empezar

- **DP1** (P09), **DP2** (P08), **DP3** (P25–P27), **DP4** (P15), **DP5** (P16), **DP6** (P30), **DP7** (P19) — descritas en la sección 7 del informe. SP1 y SP2 (salvo P08) pueden ejecutarse sin ninguna decisión tomada.
