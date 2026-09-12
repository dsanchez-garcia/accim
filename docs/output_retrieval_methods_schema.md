# Esquema de metodos para obtencion de outputs de simulacion

Fecha de actualizacion: 2026-07-02

## Objetivo

Documento de referencia para localizar rapidamente los metodos de:

- resultados base,
- expansion horaria,
- agregacion por frecuencia,
- normalizacion por area,
- delegacion entre wrappers y metodos internos.

## Flujo general

1. Ejecutar/cargar resultados base.
2. Expandir a horario (embedded, CSV o ESO).
3. Agregar a `daily`, `monthly` o `runperiod`.
4. Normalizar a `kWh/m2` (opcional).
5. Dividir por categoria (`split_by`) si aplica.

## Metodos publicos principales

### 1) Resultados base

- `ParametricSimulation.run_parametric_simulation(...)` -> `accim/parametric_and_optimisation/main.py:8185`
- `ParametricSimulation.load_outputs_parametric(...)` -> `accim/parametric_and_optimisation/main.py:8672`
- `OptimisationSimulation.run_optimisation(...)` -> `accim/parametric_and_optimisation/main.py:8811`
- `OptimisationSimulation.load_outputs_optimisation(...)` -> `accim/parametric_and_optimisation/main.py:9563`

### 2) Expansion horaria

- Parametrico
  - `get_hourly_df_parametric(...)` -> `main.py:10190`
  - `get_hourly_df(...)` (wrapper explicito) -> `main.py:10391`
- Optimizacion
  - `get_hourly_df_optimisation(...)` -> `main.py:10862`
  - `OptimisationSimulation.get_hourly_df(...)` (alias unificado) -> `main.py:11561`

Atributos de salida horarios:

- Parametrico: `outputs_param_simulation_hourly`, `outputs_param_simulation_hourly_by_category`
- Optimizacion: `outputs_optimisation_hourly`, `outputs_optimisation_hourly_by_category`

### 3) Agregacion por frecuencia

- Parametrico
  - `get_output_df(...)` -> `main.py:10444`
  - `get_monthly_df(...)` -> `main.py:10543`
  - `get_daily_df(...)` -> `main.py:10580`
  - `get_runperiod_df(...)` -> `main.py:10614`
- Optimizacion
  - `get_output_df_optimisation(...)` -> `main.py:11041`
  - `get_monthly_df_optimisation(...)` -> `main.py:11143`
  - `get_daily_df_optimisation(...)` -> `main.py:11182`
  - `get_runperiod_df_optimisation(...)` -> `main.py:11218`
- Alias unificados en `OptimisationSimulation`
  - `get_output_df(...)` -> `main.py:11597`
  - `get_monthly_df(...)` -> `main.py:11637`
  - `get_daily_df(...)` -> `main.py:11672`
  - `get_runperiod_df(...)` -> `main.py:11707`

Atributos agregados:

- Parametrico: `outputs_param_simulation_daily`, `outputs_param_simulation_monthly`, `outputs_param_simulation_runperiod`, `outputs_param_simulation_aggregated_by_category`
- Optimizacion: `outputs_optimisation_daily`, `outputs_optimisation_monthly`, `outputs_optimisation_runperiod`, `outputs_optimisation_aggregated_by_category`

## Delegacion de wrappers

- Parametrico
  - `get_hourly_df(...)` -> `get_hourly_df_parametric(...)`
  - `get_monthly_df(...)` -> `get_output_df(frequency='monthly', ...)`
  - `get_daily_df(...)` -> `get_output_df(frequency='daily', ...)`
  - `get_runperiod_df(...)` -> `get_output_df(frequency='runperiod', ...)`

- Optimizacion
  - `OptimisationSimulation.get_hourly_df(...)` -> `get_hourly_df_optimisation(...)`
  - `OptimisationSimulation.get_output_df(...)` -> `get_output_df_optimisation(...)`
  - `OptimisationSimulation.get_monthly_df(...)` -> `get_monthly_df_optimisation(...)`
  - `OptimisationSimulation.get_daily_df(...)` -> `get_daily_df_optimisation(...)`
  - `OptimisationSimulation.get_runperiod_df(...)` -> `get_runperiod_df_optimisation(...)`

## Helpers privados criticos

### Categoria y agregacion

- `_ensure_grouping_category_column(...)` -> `main.py:9964`
- `_get_identifier_columns_for_aggregation(...)` -> `main.py:10015`
- `_split_dataframe_by_category(...)` -> `main.py:10054`
- `_build_default_aggregation_map(...)` -> `main.py:10081`
- `_normalize_aggregation_frequency(...)` -> `main.py:10131`
- `_aggregate_hourly_dataframe(...)` -> `main.py:10154`

### Lectura y expansion desde ficheros

- `_resolve_simulation_file_path(...)` -> `main.py:10649`
- `_extract_hourly_outputs_from_file(...)` -> `main.py:10725`
- `_attach_hourly_outputs_from_simulation_files(...)` -> `main.py:10816`
- `expand_to_hourly_dataframe(...)` -> `accim/parametric_and_optimisation/utils.py:80`
- `identify_hourly_columns(...)` -> `accim/parametric_and_optimisation/utils.py:186`

## Normalizacion de outputs

Metodos en `accim/parametric_and_optimisation/analysis.py`:

- `_normalizable_output_df_mapping(...)` -> `analysis.py:1548`
- `_get_normalized_output_df_types(...)` -> `analysis.py:1563`
- `_is_df_type_normalized(...)` -> `analysis.py:1571`
- `_invalidate_normalized_df_types(...)` -> `analysis.py:1575`
- `_refresh_outputs_normalized_flag(...)` -> `analysis.py:1585`
- `normalize_outputs(...)` -> `analysis.py:1598`

## Nota de contrato actual

- `split_by` puede devolver grupos con diferentes columnas de output cuando `drop_all_empty_output_columns=True`.
- Los wrappers parametricos exponen argumentos de forma explicita (sin `**kwargs`) para mejorar autocompletado en IDE.

