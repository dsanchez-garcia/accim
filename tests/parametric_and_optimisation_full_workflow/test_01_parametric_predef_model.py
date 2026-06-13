"""
Test 01 — ParametricSimulation: Accim Predefined Model (flujo completo)
========================================================================
Clases: ParametricSimulation (parameters_type='accim predefined model')
Métodos cubiertos:
  SimulationBase.__init__, get_output_var_df_from_idf, get_output_meter_df_from_idf,
  set_output_var_df_to_idf, set_output_met_objects_to_idf, get_outputs_df_from_testsim,
  set_outputs_for_simulation, get_available_parameters, set_parameters,
  sampling_full_set, set_category_mapping, preview_category_mapping,
  set_building_floor_area (mode='all' y 'occupied'), run_parametric_simulation,
  normalize_outputs, get_hourly_df, get_monthly_df, get_hourly_df_columns,
  load_outputs_parametric (pkl + json), plot_categorical_boxplots (variantes col/row/hue)
IDFs: SF_Detached_B_min_North.idf, SF_Detached_D_min_North.idf
EPWs: seville_2024, seville_2025, madrid_2024, madrid_2025
"""

import glob
import os
import accim
import accim.utils
import pandas as pd
from besos import eppy_funcs as ef
from accim.parametric_and_optimisation.main import ParametricSimulation

OUT_DIR = 'test_01_predef_results'

IDF_PATHS = [
    'SF_Detached_B_min_North.idf',
    'SF_Detached_D_min_North.idf',
]
EPW_ALL = [
    'seville_2024.epw',
    'seville_2025.epw',
    'madrid_2024.epw',
    'madrid_2025.epw',
]

# ---------------------------------------------------------------------------
# 1. Cargar IDFs y reducir runtime (junio–julio)
# ---------------------------------------------------------------------------
print("\n=== [1] Cargar IDFs y reducir runtime ===")
buildings = [ef.get_building(p) for p in IDF_PATHS]
for building in buildings:
    accim.utils.reduce_runtime(
        idf_object=building,
        runperiod_begin_month=6,
        runperiod_begin_day_of_month=1,
        runperiod_end_month=7,
        runperiod_end_day_of_month=31,
    )

# ---------------------------------------------------------------------------
# 2. Instanciar ParametricSimulation — predefined model, output_freqs hourly+monthly
# ---------------------------------------------------------------------------
print("\n=== [2] Instanciar ParametricSimulation (predefined model) ===")
parametric = ParametricSimulation(
    buildings=buildings,
    epws=EPW_ALL,
    parameters_type='accim predefined model',
    output_type='standard',
    output_keep_existing=False,
    output_freqs=['hourly', 'monthly'],
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    make_averages=False,
    verbosemode=False,
)

# ---------------------------------------------------------------------------
# 3. Inspeccionar outputs en el IDF
# ---------------------------------------------------------------------------
print("\n=== [3] Inspeccionar outputs del IDF ===")
df_vars = parametric.get_output_var_df_from_idf()
print(f"  Output variables en IDF: {len(df_vars)} filas")
assert not df_vars.empty, "get_output_var_df_from_idf devolvió DataFrame vacío"

df_meters = parametric.get_output_meter_df_from_idf()
print(f"  Output meters en IDF: {len(df_meters)} filas")

# Filtrar outputs a sólo los de temperatura operativa y setpoints
df_vars_filtered = df_vars[
    df_vars['variable_name'].str.contains(
        'Operative Temperature|Setpoint Temperature|Running Average Outdoor', na=False
    )
].copy()
print(f"  Variables filtradas: {len(df_vars_filtered)}")

# Aplicar el subset de variables al IDF
parametric.set_output_var_df_to_idf(outputs_df=df_vars_filtered)

# Añadir meters de energía
parametric.set_output_met_objects_to_idf(
    output_meters=['Heating:Electricity', 'Cooling:Electricity']
)

# ---------------------------------------------------------------------------
# 4. Test simulation → obtener outputs disponibles
# ---------------------------------------------------------------------------
print("\n=== [4] Test simulation ===")
outputs_from_testsim = parametric.get_outputs_df_from_testsim(reduce_sim_time=True)
df_meters_ts = outputs_from_testsim['meters']
df_vars_ts = outputs_from_testsim['variables']
print(f"  Meters disponibles: {len(df_meters_ts)}")
print(f"  Variables disponibles: {len(df_vars_ts)}")

# Usar sólo Heating y Cooling electricity (frecuencia Monthly para besos)
df_meters_problem = df_meters_ts[
    df_meters_ts['key_name'].isin(['Heating:Electricity', 'Cooling:Electricity'])
].drop_duplicates(subset=['key_name']).head(2)
print(f"  Meters seleccionados para el problema: {df_meters_problem['key_name'].tolist()}")

parametric.set_outputs_for_simulation(df_output_meter=df_meters_problem)

# ---------------------------------------------------------------------------
# 5. Parámetros predefinidos — opciones (lista)
# ---------------------------------------------------------------------------
print("\n=== [5] Parámetros predefinidos ===")
available = parametric.get_available_parameters()
print(f"  Parámetros disponibles ({len(available)}): {available}")

parametric.set_parameters(
    accis_params_dict={
        'ComfStand': [0, 1],   # ESP CTE + EN16798
        'HVACmode': [0, 2],    # AC + mixed-mode
    }
)

# ---------------------------------------------------------------------------
# 6. Sampling — full set (combinaciones de opciones)
# ---------------------------------------------------------------------------
print("\n=== [6] sampling_full_set ===")
parametric.sampling_full_set()
print(f"  Filas en parameters_values_df: {len(parametric.parameters_values_df)}")
assert not parametric.parameters_values_df.empty

# ---------------------------------------------------------------------------
# 7. set_problem
# ---------------------------------------------------------------------------
print("\n=== [7] set_problem ===")
parametric.set_problem()

# ---------------------------------------------------------------------------
# 8. Category mapping
# ---------------------------------------------------------------------------
print("\n=== [8] Category mapping ===")
parametric.set_category_mapping(
    epw_mapping_rules={
        'city':     {'seville': ['seville'], 'madrid': ['madrid']},
        'year':     {'2024': ['2024'], '2025': ['2025']},
    },
    idf_mapping_rules={
        'typology': {'type_B': ['_B_'], 'type_D': ['_D_']},
    },
)
preview = parametric.preview_category_mapping()
print("  Preview EPW:\n", preview['epw'].to_string(index=False))
print("  Preview IDF:\n", preview['idf'].to_string(index=False))

# ---------------------------------------------------------------------------
# 9. Floor area — mode='all' y mode='occupied'
# ---------------------------------------------------------------------------
print("\n=== [9] set_building_floor_area ===")
area_all = parametric.set_building_floor_area(mode='all')
print(f"  Área total (all): {area_all}")

area_occ = parametric.set_building_floor_area(mode='occupied')
print(f"  Área ocupada (occupied): {area_occ}")

# Volvemos a mode='all' para la normalización principal
parametric.set_building_floor_area(mode='all')

# ---------------------------------------------------------------------------
# 10. run_parametric_simulation — 2 IDFs × 4 EPWs
# ---------------------------------------------------------------------------
print("\n=== [10] run_parametric_simulation ===")
results = parametric.run_parametric_simulation(
    out_dir=OUT_DIR,
    processes=2,
    keep_input=True,
    keep_dirs=True,
)
print(f"  Filas en outputs_param_simulation: {len(results)}")
assert not results.empty, "run_parametric_simulation devolvió DataFrame vacío"
assert 'epw' in results.columns
assert 'idf' in results.columns
# Las columnas de categorías deben estar presentes (se aplican automáticamente)
assert 'city' in results.columns, "Columna 'city' no generada por apply_category_mapping"
assert 'typology' in results.columns

# ---------------------------------------------------------------------------
# 11. normalize_outputs
# ---------------------------------------------------------------------------
print("\n=== [11] normalize_outputs ===")
parametric.normalize_outputs()
print("  Normalización aplicada.")
assert parametric.outputs_normalized is True

# ---------------------------------------------------------------------------
# 12. get_hourly_df y get_monthly_df
# ---------------------------------------------------------------------------
print("\n=== [12] get_hourly_df ===")
parametric.get_hourly_df(start_date='2024-06-01 01', normalize_per_m2=False)
hourly = parametric.outputs_param_simulation_hourly
print(f"  Hourly shape: {hourly.shape}")
assert hourly is not None and not hourly.empty
assert 'datetime' in hourly.columns

print("\n=== [12b] get_monthly_df ===")
parametric.get_monthly_df(start_date='2024-06-01 01')
monthly = parametric.outputs_param_simulation_monthly
print(f"  Monthly shape: {monthly.shape}")
assert monthly is not None and not monthly.empty
assert 'month' in monthly.columns

# ---------------------------------------------------------------------------
# 13. get_hourly_df_columns
# ---------------------------------------------------------------------------
print("\n=== [13] get_hourly_df_columns ===")
hourly_cols = parametric.get_hourly_df_columns()
print(f"  Columnas horarias detectadas: {len(hourly_cols)}")

# ---------------------------------------------------------------------------
# 14. load_outputs_parametric desde pickle y JSON
# ---------------------------------------------------------------------------
print("\n=== [14] load_outputs_parametric (pkl + json) ===")
csv_path = parametric.outputs_param_simulation_filepath
pkl_path = csv_path.replace('.csv', '.pkl')
json_path = csv_path.replace('.csv', '.json')

# Desde pickle
p2 = ParametricSimulation.__new__(ParametricSimulation)
p2.last_run_type = None
p2.outputs_param_simulation = None
p2.outputs_param_simulation_hourly = None
p2.outputs_param_simulation_monthly = None
p2.outputs_param_simulation_filepath = None
p2.epws = []
p2.buildings = []
p2.load_outputs_parametric(pickle_path=pkl_path)
print(f"  Cargado desde PKL: {len(p2.outputs_param_simulation)} filas")
assert not p2.outputs_param_simulation.empty

# Desde JSON
p3 = ParametricSimulation.__new__(ParametricSimulation)
p3.last_run_type = None
p3.outputs_param_simulation = None
p3.outputs_param_simulation_hourly = None
p3.outputs_param_simulation_monthly = None
p3.outputs_param_simulation_filepath = None
p3.epws = []
p3.buildings = []
p3.load_outputs_parametric(json_path=json_path)
print(f"  Cargado desde JSON: {len(p3.outputs_param_simulation)} filas")
assert not p3.outputs_param_simulation.empty

# ---------------------------------------------------------------------------
# 15. plot_categorical_boxplots — variantes
# ---------------------------------------------------------------------------
print("\n=== [15] plot_categorical_boxplots ===")

# Variante 1: col=city, hue=year, sharey=True, show_points=True (por defecto)
parametric.plot_categorical_boxplots(
    df_source='parametric',
    col='city',
    hue='year',
    out_dir=OUT_DIR,
    sharey=True,
    show_points=True,
)

# Variante 2: row=typology, col=city
parametric.plot_categorical_boxplots(
    df_source='parametric',
    col='city',
    row='typology',
    out_dir=OUT_DIR,
    sharey=False,
)

# Variante 3: hue=typology sólo
parametric.plot_categorical_boxplots(
    df_source='parametric',
    hue='typology',
    out_dir=OUT_DIR,
    show_points=False,
)

# Verificar que se generaron plots
plots = glob.glob(os.path.join(OUT_DIR, 'plot_categorical_boxplots_*.png'))
assert len(plots) >= 3, f"Se esperaban >=3 plots, se encontraron {len(plots)}"

print(f"\n=== SCRIPT 1 COMPLETADO — outputs en '{OUT_DIR}/' ===")
