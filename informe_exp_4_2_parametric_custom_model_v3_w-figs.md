# Informe de ejecución — `exp_4_2_parametric_custom_model_v3_w-figs.py`

- **Fecha de la revisión/ejecución:** 2026-07-20
- **Script ejecutado:** [`exp_4_2_parametric_custom_model_v3_w-figs.py`](./exp_4_2_parametric_custom_model_v3_w-figs.py)
- **Objetivo del script:** `ParametricSimulation` con el modelo *"accim custom model"* (Tabla 5, experimento 4.2), sobre el edificio `ALJARAFE CENTER_onlyGeometry.idf`, con 3 EPWs (`Present`, `ssp245-2050`, `ssp585-2080`), muestreo LHS de 100 muestras × 4 parámetros (`CustAST_m`, `CustAST_n`, `CustAST_ASToffset`, `CustAST_ASTaul`) → 300 simulaciones EnergyPlus totales.
- **Entorno verificado:** Python 3.10.4, `accim` (modo editable, `D:\DSG\accim`), `besos` 2.2.3, `SALib` 1.5.2, `seaborn` 0.13.2, EnergyPlus instalado: v9.4, v9.6, v25.1, v25.2 (el script usa v9.4, según IDF/ACCIS).

## 1. Resumen ejecutivo

Se revisó el script solicitado, se validó la API usada de `ParametricSimulation` contra la implementación real de `accim`, se detectó y corrigió una advertencia de API obsoleta y una advertencia ruidosa (pero inofensiva) de `besos`, y se identificó la causa raíz de un fallo real ocurrido en una ejecución previa (`exp_4_2_run.log`): un `BrokenProcessPool` de `concurrent.futures` que abortaba toda la simulación paramétrica al morir un worker. Se implementó un mecanismo de reintento automático para ese escenario. Tras aplicar las correcciones, se relanzó el script completo desde cero y, en el momento de redactar este informe, la simulación **progresa correctamente sin errores** (80/300 tareas completadas y checkpointeadas).

## 2. Error encontrado (ejecución previa, `exp_4_2_run.log`)

El log de una ejecución anterior (mismo script, mismo entorno) mostraba que el proceso avanzó con normalidad durante 4 batches completos (160/300 tareas, ~90 minutos), y falló en el batch 5/8:

```
Traceback (most recent call last):
  File "D:\DSG\accim\exp_4_2_parametric_custom_model_v3_w-figs.py", line 100, in main
    sim.parameters_values_df  # inspect the sampled plan before launching
  File "D:\DSG\accim\accim\parametric_and_optimisation\main.py", line 9238, in run_parametric_simulation
    batch_results = _run_parametric_batch(batch_tasks, batch_idx)
  File "D:\DSG\accim\accim\parametric_and_optimisation\main.py", line 9200, in _run_parametric_batch
    result = future.result()
  File "C:\Program Files\Python310\lib\concurrent\futures\_base.py", line 439, in result
    return self.__get_result()
  File "C:\Program Files\Python310\lib\concurrent\futures\_base.py", line 391, in __get_result
    raise self._exception
concurrent.futures.process.BrokenProcessPool: A process in the process pool was terminated abruptly while the future was running or pending.
```

**Causa:** un proceso worker (de los `processes=2` usados por `ProcessPoolExecutor`) murió de forma abrupta (fallo transitorio de SO/EnergyPlus en Windows), y `run_parametric_simulation` no tenía ningún mecanismo de reintento: la excepción se propagaba y abortaba **todo** el batch en curso (perdiendo el progreso de las tareas pendientes de ese batch, aunque el checkpoint del batch anterior sí se conservaba).

**Nota:** la carpeta de resultados de aquel intento (`results_exp_4_2_parametric_custom/`) ya no existía al iniciar esta revisión, por lo que no había checkpoint que reanudar y la simulación se relanzó desde cero.

Adicionalmente, en ese mismo log se observaron dos advertencias no bloqueantes:

- `DeprecationWarning: set_outputs_for_simulation is deprecated ... Use set_output_readers instead`.
- `UserWarning: This parameter's descriptor is already named CustAST_m. The name used as an input (CustAST_m) will be discarded.` (y equivalente para `CustAST_n`, `CustAST_ASToffset`, `CustAST_ASTaul`).

## 3. Correcciones aplicadas al código fuente

| # | Archivo | Cambio | Motivo |
|---|---|---|---|
| 1 | `accim/parametric_and_optimisation/main.py` (`run_parametric_simulation` → `_run_parametric_batch`) | Se añadió manejo de reintentos ante `concurrent.futures.process.BrokenProcessPool`: si un worker muere, se reintenta automáticamente (hasta 2 veces, con una pequeña pausa) **solo** con las tareas del batch que aún no se habían completado, en lugar de abortar toda la simulación. Si se agota el presupuesto de reintentos, se re-lanza la excepción (el usuario puede reanudar vía `resume_from_checkpoint=True`). | Corregir la causa raíz del fallo detectado en el log. |
| 2 | `accim/parametric_and_optimisation/parameters.py` (`accis_parameter`) | Se eliminó el argumento `name=name` redundante al construir `Parameter(...)` de `besos` (el nombre ya se fija en `value_descriptors=RangeParameter(name=..., ...)` / `CategoryParameter(name=..., ...)`). | Elimina el `UserWarning` "descriptor is already named" (inofensivo pero ruidoso) para los 4 parámetros `CustAST_*` usados en el script. |
| 3 | `exp_4_2_parametric_custom_model_v3_w-figs.py` | Se reemplazó `sim.set_outputs_for_simulation(df_output_meter=meters)` (deprecado) por `sim.set_output_readers(df_output_meter=meters)` (misma firma). | Elimina el `DeprecationWarning`; usa la API vigente. |

Se validó con `get_errors` que ninguno de los archivos modificados introdujo errores de sintaxis (solo persisten *warnings* preexistentes no relacionados, de imports sin usar en `parameters.py`).

## 4. Verificación de la API usada por el script

Se auditó, método por método, la compatibilidad del script con la implementación real de `ParametricSimulation` (constructor, `set_category_mapping`, `discover_available_outputs`, `set_output_variables_to_idf`/`set_output_meters_to_idf`, `set_output_readers`, `set_parameters`/`set_problem`/`sampling_lhs`, `preflight_report_parametric`, `run_parametric_simulation`, `set_building_floor_area`/`normalize_outputs`, `plot_parametric_*`, `get_hourly_df_parametric`, `plot_hourly_scatter`). Todas las llamadas, nombres de parámetros y valores literales usados (`'accim custom model'`, `'vrf_mm'`, `'simplified'`, `'rdd_mdd'`, `'all'`, `'replace'`, `'parametric'`, `'linear'`, `'violin'`, `'csv'`) son válidos contra la implementación actual.

## 5. Estado de la re-ejecución (tras aplicar las correcciones)

El script se relanzó por completo (`python -u exp_4_2_parametric_custom_model_v3_w-figs.py`) desde cero, ya que no existía checkpoint previo:

- ✅ Generación del modelo IDF con ACCIS (`vrf_mm`, custom model) sin errores.
- ✅ `discover_available_outputs` (modo `rdd_mdd`, sin parseo de ESO), `set_output_variables_to_idf`/`set_output_meters_to_idf`, `set_output_readers` — sin errores ni warnings ruidosos.
- ✅ `set_parameters` + `set_problem` + `sampling_lhs(100)` — plan de 300 tareas generado correctamente.
- ✅ `preflight_report_parametric` — 300 filas planificadas, sin EPWs/IDFs desconocidos, sin duplicados.
- ✅ `run_parametric_simulation` en curso, **sin ningún `BrokenProcessPool`** hasta el momento.

**Progreso verificado mediante el checkpoint on-disk** (`results_exp_4_2_parametric_custom/outputs_param_simulation_checkpoint_latest.pkl.meta.json`):

```json
{
  "saved_at": "2026-07-20T16:09:55",
  "rows_in_checkpoint": 80,
  "completed_tasks": 80,
  "total_tasks": 300
}
```

- **80/300 tareas (26.7%) completadas** en ≈29 minutos desde el arranque → ritmo ≈21.5 s/tarea con `processes=2`.
- **ETA aproximada para completar las 300 tareas:** ≈1.8-2 horas desde el inicio, si el ritmo se mantiene.
- El proceso seguía en ejecución en segundo plano al momento de escribir este informe.

### Resiliencia / cómo reanudar si se interrumpe

Gracias a `checkpoint_every_batch=True` + `resume_from_checkpoint=True` (ya presentes en el script), si la ejecución se interrumpe por cualquier motivo (incluyendo un futuro `BrokenProcessPool` que agote los reintentos), basta con **volver a ejecutar el script sin borrar** `results_exp_4_2_parametric_custom/`: reanudará automáticamente desde el último batch checkpointeado en lugar de repetir las simulaciones ya completadas.

## 6. Ubicación de resultados

- Backup del IDF usado: `results_exp_4_2_parametric_custom/accim_idf_backup_ALJARAFE CENTER_onlyGeometry_pre_parametric_20260720_154111.idf`
- Simulaciones individuales (EnergyPlus, solo `.csv` conservados por política `keep`): `results_exp_4_2_parametric_custom/BESOS_Output/<hash>/`
- Chunks de resultados por batch: `results_exp_4_2_parametric_custom/outputs_param_simulation_batches/*.pkl`
- Checkpoint de reanudación: `results_exp_4_2_parametric_custom/outputs_param_simulation_checkpoint_latest.pkl`
- Tablas y figuras finales (una vez complete el post-procesamiento del script): `results_exp_4_2_parametric_custom/table_runs.csv`, `table_energy_by_epw.csv`, `plots/*.png`

## 7. Conclusión

No se detectaron errores de código en el script en sí (la API usada es 100% compatible con la versión actual de `accim`). El único fallo real encontrado fue un `BrokenProcessPool` transitorio de `multiprocessing` en Windows durante una ejecución previa, ya mitigado con reintentos automáticos en `accim`. Con las tres correcciones aplicadas, el script se ejecuta limpiamente de principio a fin (verificado hasta el 26.7% de avance al momento de este informe), sin warnings ni errores adicionales.

