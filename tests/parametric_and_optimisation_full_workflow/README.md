# parametric_and_optimisation_full_workflow

Scripts de testeo **total** del módulo `accim/parametric_and_optimisation`.
Cubren todas las clases, métodos y variantes de argumentos en el contexto de un
flujo de trabajo completo (no tests unitarios parciales).

## Archivos incluidos

| Archivo | Tipo | Descripción |
|---|---|---|
| `SF_Detached_B_min_North.idf` | IDF | Edificio residencial unifamiliar tipo B |
| `SF_Detached_D_min_North.idf` | IDF | Edificio residencial unifamiliar tipo D |
| `seville_2024.epw` | EPW | Clima Sevilla 2024 |
| `seville_2025.epw` | EPW | Clima Sevilla 2025 |
| `madrid_2024.epw` | EPW | Clima Madrid 2024 |
| `madrid_2025.epw` | EPW | Clima Madrid 2025 |

## Scripts de test

### `test_01_parametric_predef_model.py`
- **Clase**: `ParametricSimulation(parameters_type='accim predefined model')`
- **IDFs**: B + D · **EPWs**: los 4
- **Cubre**: `sampling_full_set`, `get/set_output_*`, `get_hourly/monthly_df`,
  `load_outputs_parametric` (pkl + json), `plot_categorical_boxplots` (col + row + hue),
  `set_building_floor_area` (all + occupied), `normalize_outputs`

### `test_02_parametric_wrapper_and_bypass.py`
- **Clases**: `AccimPredefModelsParamSim` · `ParametricSimulation(bypass_addAccis=True)` · `parameters_type=None`
- **IDFs**: B (wrapper y `parameters_type=None`) + D (bypass) · **EPWs**: seville_2024 + madrid_2024
- **Cubre**: `sampling_custom` (dict / list / DataFrame), `set_building_floor_area`
  (custom + list), `plot_categorical_boxplots(sharey=False, show_points=False)`

### `test_03_parametric_custom_model_and_sensitivity.py`
- **Clase**: `ParametricSimulation(parameters_type='accim custom model')`
- **IDF**: B · **EPWs**: seville_2024 + seville_2025 + madrid_2024
- **Cubre**: `sampling_morris`, `sampling_lhs`, `sampling_custom` (list/DataFrame),
  `run_sensitivity_analysis(morris)`, `run_sensitivity_analysis_by_epw`,
  `normalize_per_m2=True`, `load_outputs_parametric(csv_path)`

### `test_04_optimisation.py`
- **Clase**: `OptimisationSimulation(parameters_type='accim custom model')`
- **IDF**: B · **EPWs**: seville_2024 + madrid_2024
- **Cubre**: `run_optimisation` (keep_sim_files=all/non-dominated/none),
  `load_outputs_optimisation` (pkl + json), `get_best_compromise_solution` (knee_point + topsis),
  `plot_best_compromise_solutions`, `plot_pareto_front`, `plot_parallel_coordinates`,
  `plot_pairwise_scatter_matrix`, `run_clustering`, `get_hourly/monthly_df_optimisation`,
  `run_robustness_analysis`, `plot_categorical_boxplots(df_source='optimisation')`

### `test_05_range_sampling_sobol_factorial.py`
- **Clase**: `ParametricSimulation(parameters_type='accim custom model')`
- **IDF**: B · **EPWs**: seville_2024 + madrid_2024
- **Requisito**: `pip install SALib`
- **Cubre**: `sampling_sobol`, `sampling_full_factorial`, `run_sensitivity_analysis(sobol)`,
  `run_sensitivity_analysis_by_epw(sobol)`

## Cómo ejecutar

Desde esta carpeta (los scripts usan los IDFs y EPWs de la carpeta y escriben en ella sus resultados), con
pytest:

```powershell
cd d:\Python\accim\tests\parametric_and_optimisation_full_workflow
python -m pytest test_01_parametric_predef_model.py -s -p no:cacheprovider
```

Los scripts **no** tienen funciones `test_*` (son scripts de flujo de trabajo completo): se ejecutan cuando
pytest los importa, así que pytest termina con «no tests ran» (código 5) si el script llega al final, y con
un error de colección si falla. El `conftest.py` solo cambia el directorio de trabajo para las funciones de
test, no al importar los scripts, de ahí que haya que ejecutarlos desde esta carpeta.

No los ejecutes directamente (`python test_01_parametric_predef_model.py`) en Windows: con `processes=2`,
los procesos de las simulaciones vuelven a importar el script, que no tiene `if __name__ == '__main__':`, y
repiten todo el flujo, con lo que el pool de procesos se rompe (`BrokenProcessPool`). Con pytest, esos
procesos importan el `__main__` de pytest, que no se vuelve a ejecutar.

## Preparación de los modelos

Los IDFs `SF_Detached_*` no tienen periodos de dimensionado y tienen desactivado el dimensionado de zonas.
accim activa el dimensionado de los sistemas VRF (autosize) que añade, pero EnergyPlus también necesita
periodos de dimensionado. Los scripts llaman a `enable_sizing()` de `tests/test_setup.py`, que activa el
dimensionado y añade unos días del EPW como periodos de dimensionado (que no se simulan). eppy lee todos los
modelos de un proceso con el IDD del primero, así que todos los modelos de un script deben ser de la misma
versión de EnergyPlus (9.6).

## Periodo de simulación

Todos los scripts reducen el periodo a **junio–julio** (2 meses) mediante
`accim.utils.reduce_runtime(runperiod_begin_month=6, runperiod_end_month=7)`,
lo que permite probar frecuencias horaria y mensual sin tiempos de ejecución excesivos.

## Estructura de outputs

Cada script genera su propia carpeta de resultados dentro de este directorio:

```
parametric_and_optimisation_full_workflow/
├── test_01_predef_results/
├── test_02_wrapper_results/
├── test_02_bypass_results/
├── test_02_none_results/
├── test_03_morris_results/
├── test_03_lhs_results/
├── test_03_custom_results/
├── test_04_optim_results/
├── test_05_sobol_results/
└── test_05_factorial_results/
```
