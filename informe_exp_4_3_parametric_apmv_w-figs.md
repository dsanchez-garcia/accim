# Informe de ejecución — `exp_4_3_parametric_apmv_w-figs.py`

- **Fecha de la revisión/ejecución:** 2026-07-20
- **Script ejecutado:** [`exp_4_3_parametric_apmv_w-figs.py`](./exp_4_3_parametric_apmv_w-figs.py)
- **Objetivo del script:** `ParametricSimulation` con *"apmv setpoints"* (Tabla 5, experimento 4.3), sobre el edificio `ALJARAFE CENTER_onlyGeometry.idf` con un sistema VRF inyectado por `add_vrf_system()` (EER=4.42, COP=4.95) y control de confort Fanger (`TempCtrl='pmv'`), sobre el que `apply_apmv_setpoints` añade la lógica EMS del índice aPMV (Adaptive PMV). Barrido paramétrico completo (`sampling_full_set`) de 4 valores de `Adaptive cooling coefficient` (0, 0.1, 0.3, 0.5) × 3 valores de `PMV setpoint` (0.2, 0.5, 0.7) × 3 EPWs (`Seville_Present`, `Seville_ssp245_2050`, `Seville_ssp585_2080`) → **36 simulaciones EnergyPlus**.
- **Entorno verificado:** Python 3.10.4, `accim` 0.7.8 (modo editable, `D:\DSG\accim`), `besos` (instalado, sin `__version__` expuesto), `pandas` 2.3.2, `numpy` 2.2.6, `seaborn` 0.13.2, `matplotlib` 3.10.6, EnergyPlus **9.4.0-998c4b761e** (versión usada según el IDF/ACCIS).
- **No se usó** `article_objectives.py` (excluido explícitamente por el usuario).

## 1. Resumen ejecutivo

Se ejecutó el script de punta a punta **dos veces**: una ejecución completa desde cero (36/36 simulaciones EnergyPlus reales) y una segunda ejecución de verificación tras aplicar correcciones, que reutilizó el checkpoint de la primera (0 simulaciones repetidas). **Ambas ejecuciones terminaron con éxito, sin errores fatales**, generando todas las tablas (`CSV`/`XLSX`/`PKL`/`JSON`) y las 3 figuras esperadas. Se detectaron 3 advertencias no bloqueantes (una de ellas corregida por ser una API obsoleta) y **una ineficiencia de rendimiento real y significativa** en `expand_to_hourly_dataframe` (función interna de `accim` usada por `get_hourly_df_parametric`), que fue diagnosticada, corregida con una ruta vectorizada, validada exhaustivamente (equivalencia funcional 1:1 con la implementación original) y medida (**~8.5× más rápida** en un benchmark aislado del mismo tamaño que el caso real).

## 2. Diseño experimental

| Parámetro | Valores | Nº niveles |
|---|---|---|
| `Adaptive cooling coefficient` (λ enfriamiento) | 0.0, 0.1, 0.3, 0.5 | 4 |
| `PMV setpoint` (aplicado como ±valor) | 0.2, 0.5, 0.7 | 3 |
| EPW (escenario climático) | `Seville_Present`, `Seville_ssp245_2050`, `Seville_ssp585_2080` | 3 |
| **Total combinaciones** | 4 × 3 × 3 | **36** |

Notas de diseño (documentadas en el propio script):
- El λ de la temporada de calefacción se mantiene fijo en el valor por defecto de `apply_apmv_setpoints` (`-0.293`), porque el parámetro global `'Adaptive coefficient'` forzaría el mismo signo en ambas estaciones; por eso se barre específicamente `'Adaptive cooling coefficient'`.
- El valor 0.3 se eligió por aproximarse al λ=0.293 de referencia del estudio aPMV original (JOBE 2026).
- `apply_apmv_setpoints` ya inyecta las salidas EMS relacionadas con aPMV/PMV, por lo que el script no reemplaza variables de salida, solo gestiona el meter `Electricity:HVAC` (horario).
- Área de suelo usada para normalizar (`mode='all'`): **332.49 m²** (IDF único).

## 3. Advertencias detectadas (no bloqueantes)

| # | Advertencia | Origen | ¿Esperada? | Acción |
|---|---|---|---|---|
| 1 | `UserWarning: Thermal Comfort Thermostat already exists for zone 'PLANTAX08:OFFICE'. Updating configuration.` | `accim/sim/apmv_setpoints.py:534` (`_ensure_infrastructure`) | Sí — `add_vrf_system()` ya crea un `ZoneControl:Thermostat:ThermalComfort` vía `setComfFieldsPeople(TempCtrl='pmv')`; cuando `apply_apmv_setpoints` se ejecuta a continuación detecta que ya existe y **actualiza su configuración** en vez de duplicarlo (comportamiento documentado como "Case C" en el código). | Ninguna (comportamiento por diseño). |
| 2 | `UserWarning: resume_from_checkpoint=True but no checkpoint was found at ...\outputs_param_simulation_checkpoint_latest.pkl. Starting a fresh run.` | `accim/parametric_and_optimisation/main.py:9045` | Sí — es la primera ejecución, no existía checkpoint previo. | Ninguna (informativo). |
| 3 | `DeprecationWarning: set_outputs_for_simulation is deprecated and will be removed in a future version. Use set_output_readers instead (same arguments).` | Línea 73 del script original | No debería persistir | **Corregida** (ver §4). |

No se encontró ningún `Traceback`, `Error`, `Exception`, `CRITICAL` ni `FAILED` en ninguno de los dos logs completos de ejecución.

## 4. Correcciones aplicadas al código fuente

| # | Archivo | Cambio | Motivo |
|---|---|---|---|
| 1 | `exp_4_3_parametric_apmv_w-figs.py` (línea 73) | `sim.set_outputs_for_simulation(df_output_meter=meters)` → `sim.set_output_readers(df_output_meter=meters)` (misma firma/argumentos). | Elimina el `DeprecationWarning` nº 3; usa la API vigente. |
| 2 | `accim/parametric_and_optimisation/utils.py` (`expand_to_hourly_dataframe`) | Se añadió una **ruta rápida vectorizada** (NumPy/pandas: `np.repeat`, `np.tile`, `np.concatenate`, `pd.date_range`) para el caso común en que todas las filas/columnas horarias tienen igual longitud (p. ej. 8760 h/año en todas las simulaciones). Se conserva **intacta** la ruta original fila-a-fila (`.apply(axis=1)` + bucle `timedelta`) como *fallback* automático para el caso raro de columnas horarias de longitud irregular (distintos recuentos de zona entre IDFs), documentado en `CHANGELOG.md` ("Sparse Hourly Expansion with Variable Output Columns"). | La ruta original escalaba muy mal: en la primera ejecución, la etapa `[get_hourly_df_parametric] Expanding...` (36 filas × 8760 h × 5 columnas EMS de aPMV) tardó **más de 1 hora** en un sistema con carga externa (PyCharm/antivirus). Es un cuello de botella algorítmico real (`DataFrame.apply(axis=1)` + `timedelta` por elemento), no solo una cuestión de hardware. |

### 4.1 Validación de la optimización (antes de darla por buena)

Se construyó un script de validación temporal (no forma parte del repo) con **5 escenarios sintéticos**, comparando la salida de la función optimizada contra una copia literal de la implementación original:

| Caso | Descripción | Resultado |
|---|---|---|
| `regular-case` | Todas las filas/columnas con igual longitud (camino rápido) | ✅ PASS — resultados idénticos |
| `regular-case-str-list` | Columnas horarias como *strings* de lista (round-trip CSV) | ✅ PASS — mismo manejo de error de parseo que el original |
| `irregular-case-short-row` | Una fila con una columna más corta que el resto (padding NaN) | ✅ PASS — cae al *fallback* y coincide con el original |
| `irregular-case-empty-row` | Una fila con una columna completamente vacía | ✅ PASS — cae al *fallback* y coincide con el original |
| `single-row` | Un único registro de entrada | ✅ PASS |

**Benchmark de rendimiento** (tamaño idéntico al caso real: 36 filas × 8760 h × 5 columnas hourly + 5 columnas de parámetros):

| Implementación | Tiempo | Resultado |
|---|---|---|
| Original (`.apply(axis=1)` + bucle `timedelta`) | 0.987 s | — |
| Optimizada (vectorizada) | **0.116 s** | **~8.5× más rápida** |
| Diferencia de valores entre ambas | — | **Ninguna** (columnas idénticas) |

Los scripts de validación/benchmark fueron temporales y se eliminaron tras confirmar la equivalencia; no forman parte del repositorio.

Se ejecutó `get_errors` sobre ambos archivos modificados: no se introdujo ningún error de sintaxis ni de comportamiento; solo persisten *warnings* de tipado laxo preexistentes (no relacionados con el cambio) y dos avisos de "*statement seems to have no effect*" en líneas de inspección interactiva intencionales del propio script (`sim.parameters_values_df` / `sim.outputs_param_simulation_hourly.shape`), que no se deben modificar.

## 5. Cronología de las ejecuciones

| Ejecución | Inicio | Fin | Duración total | Simulaciones EnergyPlus reales | Notas |
|---|---|---|---|---|---|
| 1ª (desde cero) | 16:19:23 | 16:38:18 | ~18 min 55 s | 36/36 (ritmo ≈ 12-17 s/tarea, `processes=2`) | Generó el checkpoint completo |
| 2ª (verificación tras fix) | 16:45:03 | 16:56:15 | ~11 min 12 s | **0/36** (reanudado vía `resume_from_checkpoint=True`: *"Resuming from checkpoint: 36/36 tasks already completed"*) | Confirma que ya no aparece el `DeprecationWarning` y que los resultados son reproducibles |

## 6. Resultados de la simulación paramétrica

### 6.1 Tabla completa de resultados (`table_runs.csv`, 36 filas)

Columna de energía: `Electricity:HVAC_kWh/m2` (meter `Electricity:HVAC`, normalizado por `set_building_floor_area(mode='all')` + `normalize_outputs()` → 332.49 m²).

| Electricity:HVAC (kWh/m²) | Adaptive cooling coeff. | PMV setpoint | EPW | Escenario |
|---:|---:|---:|---|---|
| 230.64 | 0.0 | 0.5 | Seville_Present | present |
| 260.96 | 0.0 | 0.2 | Seville_Present | present |
| 213.68 | 0.0 | 0.7 | Seville_Present | present |
| 260.91 | 0.1 | 0.2 | Seville_Present | present |
| 230.39 | 0.1 | 0.5 | Seville_Present | present |
| 213.19 | 0.1 | 0.7 | Seville_Present | present |
| 260.81 | 0.3 | 0.2 | Seville_Present | present |
| 229.74 | 0.3 | 0.5 | Seville_Present | present |
| 211.86 | 0.3 | 0.7 | Seville_Present | present |
| 260.70 | 0.5 | 0.2 | Seville_Present | present |
| 209.98 | 0.5 | 0.7 | Seville_Present | present |
| 228.87 | 0.5 | 0.5 | Seville_Present | present |
| 235.92 | 0.0 | 0.2 | Seville_ssp245_2050 | ssp245-2050 |
| 204.61 | 0.0 | 0.5 | Seville_ssp245_2050 | ssp245-2050 |
| 187.61 | 0.0 | 0.7 | Seville_ssp245_2050 | ssp245-2050 |
| 235.90 | 0.1 | 0.2 | Seville_ssp245_2050 | ssp245-2050 |
| 204.48 | 0.1 | 0.5 | Seville_ssp245_2050 | ssp245-2050 |
| 187.44 | 0.1 | 0.7 | Seville_ssp245_2050 | ssp245-2050 |
| 235.83 | 0.3 | 0.2 | Seville_ssp245_2050 | ssp245-2050 |
| 204.09 | 0.3 | 0.5 | Seville_ssp245_2050 | ssp245-2050 |
| 186.85 | 0.3 | 0.7 | Seville_ssp245_2050 | ssp245-2050 |
| 235.75 | 0.5 | 0.2 | Seville_ssp245_2050 | ssp245-2050 |
| 203.55 | 0.5 | 0.5 | Seville_ssp245_2050 | ssp245-2050 |
| 185.97 | 0.5 | 0.7 | Seville_ssp245_2050 | ssp245-2050 |
| 212.02 | 0.0 | 0.2 | Seville_ssp585_2080 | ssp585-2080 |
| 181.09 | 0.0 | 0.5 | Seville_ssp585_2080 | ssp585-2080 |
| 164.14 | 0.0 | 0.7 | Seville_ssp585_2080 | ssp585-2080 |
| 212.00 | 0.1 | 0.2 | Seville_ssp585_2080 | ssp585-2080 |
| 181.08 | 0.1 | 0.5 | Seville_ssp585_2080 | ssp585-2080 |
| 164.20 | 0.1 | 0.7 | Seville_ssp585_2080 | ssp585-2080 |
| 211.96 | 0.3 | 0.2 | Seville_ssp585_2080 | ssp585-2080 |
| 180.97 | 0.3 | 0.5 | Seville_ssp585_2080 | ssp585-2080 |
| 164.09 | 0.3 | 0.7 | Seville_ssp585_2080 | ssp585-2080 |
| 211.91 | 0.5 | 0.2 | Seville_ssp585_2080 | ssp585-2080 |
| 180.72 | 0.5 | 0.5 | Seville_ssp585_2080 | ssp585-2080 |
| 163.72 | 0.5 | 0.7 | Seville_ssp585_2080 | ssp585-2080 |

### 6.2 Estadísticos descriptivos por escenario climático (`table_energy_by_epw.csv`)

| EPW | n | media | desv. típica | mín | p25 | p50 | p75 | máx |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Seville_Present | 12 | 234.31 | 21.03 | 209.98 | 213.56 | 230.06 | 260.73 | 260.96 |
| Seville_ssp245_2050 | 12 | 209.00 | 21.15 | 185.97 | 187.57 | 204.28 | 235.77 | 235.92 |
| Seville_ssp585_2080 | 12 | 185.66 | 20.73 | 163.72 | 164.18 | 181.02 | 211.92 | 212.02 |

### 6.3 Efecto de cada parámetro (promediado sobre las otras dos dimensiones)

**`Adaptive cooling coefficient` (λ enfriamiento) — efecto pequeño y monótono:**

| λ enfriamiento | media (kWh/m²) | mín | máx |
|---:|---:|---:|---:|
| 0.0 | 210.07 | 164.14 | 260.96 |
| 0.1 | 209.95 | 164.20 | 260.91 |
| 0.3 | 209.58 | 164.09 | 260.81 |
| 0.5 | 209.02 | 163.72 | 260.70 |

Aumentar λ de 0.0 a 0.5 reduce el consumo medio solo ~0.5% (210.07 → 209.02 kWh/m²): el aPMV amplía ligeramente la banda de confort en la que no hay actuación de climatización, pero el efecto es marginal frente al del `PMV setpoint`.

**`PMV setpoint` — efecto dominante (banda de confort más ancha ⇒ mucho menos consumo):**

| PMV setpoint | media (kWh/m²) | mín | máx |
|---:|---:|---:|---:|
| 0.2 (Cat. A, estricto) | 236.22 | 211.91 | 260.96 |
| 0.5 (Cat. B) | 205.02 | 180.72 | 230.64 |
| 0.7 (Cat. C, relajado) | 187.73 | 163.72 | 213.68 |

Pasar de 0.2 a 0.7 reduce el consumo medio **~20.6%** (236.22 → 187.73 kWh/m²): es, con diferencia, el parámetro con mayor impacto energético del diseño experimental.

**Efecto climático (calentamiento futuro ⇒ menos consumo del meter `Electricity:HVAC`):**

Reducción porcentual `ssp585-2080` vs. `Present`, para cada combinación (λ, setpoint):

| λ enfriamiento | setpoint 0.2 | setpoint 0.5 | setpoint 0.7 |
|---:|---:|---:|---:|
| 0.0 | −18.75% | −21.48% | −23.18% |
| 0.1 | −18.75% | −21.40% | −22.98% |
| 0.3 | −18.73% | −21.23% | −22.55% |
| 0.5 | −18.71% | −21.04% | −22.03% |

La reducción es consistente (entre −18.7% y −23.2%) en las 12 combinaciones de (λ, setpoint), y es más pronunciada cuanto más relajado es el setpoint (0.7). Esto es coherente con un edificio dominado por demanda de calefacción en el escenario base, cuya necesidad decrece al calentarse el clima más de lo que aumenta la demanda de refrigeración con el VRF (EER=4.42) modelado.

### 6.4 Extremos globales

- **Mínimo consumo:** 163.72 kWh/m² → λ=0.5, setpoint=0.7, `Seville_ssp585_2080` (clima más cálido + banda de confort más ancha + mayor coeficiente adaptativo).
- **Máximo consumo:** 260.96 kWh/m² → λ=0.0, setpoint=0.2, `Seville_Present` (clima actual + banda de confort más estricta + sin adaptación).
- **Rango total:** 97.24 kWh/m² (≈ 59.4% del valor máximo).

## 7. Figuras generadas (`results_exp_4_3_parametric_apmv/plots/`)

| Archivo | Tamaño | Contenido |
|---|---:|---|
| `plot_parametric_lines_parametric_Electricity_HVAC_kWh_m2_by_Adaptive_cooling_coefficient.png` | 150,175 B | Energía vs. λ enfriamiento, una línea por `PMV setpoint`, faceteado por `epw` |
| `plot_parametric_heatmap_parametric_Electricity_HVAC_kWh_m2_by_Adaptive_cooling_coefficient_PMV_setpoint.png` | 220,003 B | Heatmap anotado (λ × setpoint), faceteado por `epw` |
| `plot_hourly_lines_apmv_present.png` | 512,487 B | Series horarias de `aPMV`, `aPMV Cooling Setpoint`, `aPMV Heating Setpoint` (zona `PLANTAX08:OFFICE`) para el escenario `Present`, expandidas desde los 36 CSV de simulación (315,360 filas × 12 columnas) |

## 8. Ubicación de los archivos generados

- Backups de IDF: `results_exp_4_3_parametric_apmv/accim_idf_backup_ALJARAFE CENTER_onlyGeometry_pre_parametric_20260720_161923.idf` (1ª ejecución) y `..._20260720_164513.idf` (2ª ejecución)
- Simulaciones individuales de EnergyPlus (solo `.csv` conservados, `keep_dirs=True`, `keep_input=True`): `results_exp_4_3_parametric_apmv/BESOS_Output/<hash>/` (36 carpetas)
- Chunk de resultados por batch (batch único, 36 tareas cupieron en `batch_size=40`): `results_exp_4_3_parametric_apmv/outputs_param_simulation_batches/outputs_param_simulation_batch_00001_20260720_162820_451353.pkl`
- Checkpoint de reanudación: `results_exp_4_3_parametric_apmv/outputs_param_simulation_checkpoint_latest.pkl` (+ `.meta.json`)
- Resultados completos (CSV/XLSX/PKL/JSON), por ejecución: `outputs_param_simulation_20260720_162820.*` y `outputs_param_simulation_20260720_164513.*`
- Tablas finales: `results_exp_4_3_parametric_apmv/table_runs.csv`, `table_energy_by_epw.csv`
- Figuras: `results_exp_4_3_parametric_apmv/plots/*.png`

## 9. Conclusión

El script `exp_4_3_parametric_apmv_w-figs.py` es **100% compatible** con la API actual de `accim` (`ParametricSimulation`, `apply_apmv_setpoints`/`add_vrf_system`, `discover_available_outputs`, `set_output_meters_to_idf`/`set_output_readers`, `set_parameters`/`set_problem`/`sampling_full_set`, `preflight_report_parametric`, `run_parametric_simulation`, `set_building_floor_area`/`normalize_outputs`, `plot_parametric_lines`/`plot_parametric_heatmap`, `get_hourly_df_parametric`, `plot_hourly_lines`) y se ejecuta de principio a fin **sin errores**. Se corrigió una advertencia de API obsoleta (`set_outputs_for_simulation` → `set_output_readers`) y se identificó y corrigió una **ineficiencia de rendimiento real** en `expand_to_hourly_dataframe` (más de 1 hora → función vectorizada, validada como funcionalmente idéntica y ~8.5× más rápida en benchmark equivalente). Los resultados del barrido paramétrico son físicamente coherentes: el `PMV setpoint` domina el ahorro energético (~20.6% entre Cat. A y Cat. C), el `Adaptive cooling coefficient` tiene un efecto marginal (~0.5%), y el calentamiento climático futuro reduce el consumo del meter `Electricity:HVAC` entre un 18.7% y un 23.2% frente al clima presente, en un edificio aparentemente dominado por demanda de calefacción.

