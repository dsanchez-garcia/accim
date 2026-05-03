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
- **IDFs**: B · **EPWs**: seville_2024 + madrid_2024
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

### Ejecución directa (recomendada para desarrollo)
```powershell
cd d:\Python\accim\tests\parametric_and_optimisation_full_workflow
python test_01_parametric_predef_model.py
```

### Con pytest (desde la raíz del proyecto)
Los scripts **no** tienen funciones `test_*` (son scripts de flujo de trabajo completo),
por lo que se ejecutan como módulos, no como tests de pytest unitarios.
El `conftest.py` garantiza que el directorio de trabajo sea esta carpeta.

```powershell
cd d:\Python\accim
python -m pytest tests/parametric_and_optimisation_full_workflow/test_01_parametric_predef_model.py -s
```

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
