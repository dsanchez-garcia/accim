"""
Test 03 — ParametricSimulation: Custom Model + Sensitivity Analysis
====================================================================
Clases: ParametricSimulation (parameters_type='accim custom model')
Métodos cubiertos:
  set_parameters con rangos (tuple), sampling_morris, sampling_lhs,
  sampling_custom (list_of_dicts + DataFrame), run_parametric_simulation,
  run_sensitivity_analysis(method='morris'), run_sensitivity_analysis_by_epw,
  get_hourly_df(normalize_per_m2=True), get_monthly_df(agg_funcs, normalize_per_m2=True),
  normalize_outputs(df_types=[...]), load_outputs_parametric(csv_path),
  plot_categorical_boxplots(normalize_per_m2=True)
IDFs: SF_Detached_B_min_North.idf
EPWs: seville_2024, seville_2025, madrid_2024 (3 EPWs para SA por EPW)
"""

import os
import accim
import accim.utils
import pandas as pd
from besos import eppy_funcs as ef
from accim.parametric_and_optimisation.main import ParametricSimulation

OUT_MORRIS = 'test_03_morris_results'
OUT_LHS    = 'test_03_lhs_results'
OUT_CUSTOM = 'test_03_custom_results'

IDF_B  = 'SF_Detached_B_min_North.idf'
EPW_S24 = 'seville_2024.epw'
EPW_S25 = 'seville_2025.epw'
EPW_M24 = 'madrid_2024.epw'
EPW_ALL_3 = [EPW_S24, EPW_S25, EPW_M24]

# ---------------------------------------------------------------------------
# Bloque de setup común
# ---------------------------------------------------------------------------
def build_custom_sim(out_freqs=None):
    if out_freqs is None:
        out_freqs = ['hourly']
    building = ef.get_building(IDF_B)
    accim.utils.reduce_runtime(
        idf_object=building,
        runperiod_begin_month=6,
        runperiod_begin_day_of_month=1,
        runperiod_end_month=7,
        runperiod_end_day_of_month=31,
    )
    sim = ParametricSimulation(
        buildings=[building],
        epws=EPW_ALL_3,
        parameters_type='accim custom model',
        output_type='standard',
        output_freqs=out_freqs,
        ScriptType='vrf_mm',
        verbosemode=False,
    )
    sim.set_output_meters_to_idf(output_meters=['Heating:Electricity', 'Cooling:Electricity'])
    outputs_from_testsim = sim.discover_available_outputs(reduce_sim_time=True)
    df_meters_ts = outputs_from_testsim['meters']
    df_meters_problem = df_meters_ts[
        df_meters_ts['key_name'].isin(['Heating:Electricity', 'Cooling:Electricity'])
    ].drop_duplicates(subset=['key_name'])
    sim.set_output_readers(df_output_meter=df_meters_problem)
    sim.set_category_mapping(
        epw_mapping_rules={
            'city': {'seville': ['seville'], 'madrid': ['madrid']},
            'year': {'2024': ['2024'], '2025': ['2025']},
        },
    )
    return sim

# ---------------------------------------------------------------------------
# PARTE A — sampling_morris + run_sensitivity_analysis[_by_epw]
# ---------------------------------------------------------------------------
print("\n=== PARTE A: sampling_morris + Sensitivity Analysis ===")

sim_morris = build_custom_sim(out_freqs=['hourly'])

# Parámetros custom con rangos (tuple) — necesarios para Morris y LHS
sim_morris.set_parameters(
    accis_params_dict={
        'CustAST_m':         (0.01, 0.99),
        'CustAST_n':         (5.0,  23.0),
        'CustAST_ASToffset': (1.5,   5.0),
        'CustAST_ASTall':    (8.0,  16.0),
        'CustAST_ASTaul':    (28.0, 38.0),
    },
    use_dflt_values=True,
)

sim_morris.set_problem(minimize_outputs=[True, True])

# sampling_morris — 3 trayectorias × (5 params + 1) = 18 sims/EPW → 54 sims total
print("  sampling_morris(num_samples=3, num_levels=4)")
sim_morris.sampling_morris(num_samples=3, num_levels=4)
print(f"  parameters_values_df shape: {sim_morris.parameters_values_df.shape}")
assert not sim_morris.parameters_values_df.empty

sim_morris.preview_category_mapping()
sim_morris.set_building_floor_area(mode='all')

results_morris = sim_morris.run_parametric_simulation(
    out_dir=OUT_MORRIS,
    processes=2,
    keep_dirs=True,
    keep_input=True,
)
print(f"  Filas resultado Morris: {len(results_morris)}")
assert not results_morris.empty

# run_sensitivity_analysis(method='morris') — sobre todos los EPWs juntos
print("  run_sensitivity_analysis(method='morris')")
sa_results = sim_morris.run_sensitivity_analysis(method='morris')
assert len(sa_results) > 0, "run_sensitivity_analysis no devolvió resultados"
print(f"  SA keys: {list(sa_results.keys())}")

# run_sensitivity_analysis_by_epw — por EPW separado
print("  run_sensitivity_analysis_by_epw(method='morris')")
sa_by_epw = sim_morris.run_sensitivity_analysis_by_epw(
    method='morris',
    out_dir=OUT_MORRIS,
)
assert len(sa_by_epw) == len(EPW_ALL_3), (
    f"Se esperaban {len(EPW_ALL_3)} EPWs en SA, se obtuvo {len(sa_by_epw)}"
)
assert hasattr(sim_morris, 'sensitivity_results_by_epw')

# get_hourly_df con normalize_per_m2=True
print("  get_hourly_df(normalize_per_m2=True)")
sim_morris.get_hourly_df(start_date='2024-06-01 01', normalize_per_m2=True)
hourly = sim_morris.outputs_param_simulation_hourly
assert hourly is not None and not hourly.empty
print(f"  Hourly shape: {hourly.shape}")

# get_monthly_df con agg_funcs personalizados
print("  get_monthly_df(agg_funcs=..., normalize_per_m2=True)")
# Detectar columna de energía de calefacción para especificar agg_func
energy_cols = [c for c in hourly.columns if 'Heating' in c or 'Cooling' in c]
agg_custom = {col: 'sum' for col in energy_cols}
sim_morris.get_monthly_df(
    agg_funcs=agg_custom,
    start_date='2024-06-01 01',
    normalize_per_m2=True,
)
monthly = sim_morris.outputs_param_simulation_monthly
assert monthly is not None and not monthly.empty
print(f"  Monthly shape: {monthly.shape}")

# normalize_outputs explícito sobre df_types
print("  normalize_outputs(df_types=['parametric_hourly', 'parametric_monthly'])")
# Reset para probar la llamada explícita (los anteriores normalize_per_m2 ya revirtieron flag)
sim_morris.outputs_normalized = False
sim_morris.normalize_outputs(df_types=['parametric_hourly', 'parametric_monthly'])

# plot_categorical_boxplots con normalize_per_m2=True
sim_morris.plot_categorical_boxplots(
    df_source='parametric',
    col='city',
    hue='year',
    out_dir=OUT_MORRIS,
    normalize_per_m2=True,
    show_points=True,
)

# load_outputs_parametric desde CSV
csv_path = sim_morris.outputs_param_simulation_filepath
print(f"  load_outputs_parametric(csv_path={os.path.basename(csv_path)})")
p_loaded = ParametricSimulation.__new__(ParametricSimulation)
p_loaded.last_run_type = None
p_loaded.outputs_param_simulation = None
p_loaded.outputs_param_simulation_hourly = None
p_loaded.outputs_param_simulation_monthly = None
p_loaded.outputs_param_simulation_filepath = None
p_loaded.epws = []
p_loaded.buildings = []
p_loaded.load_outputs_parametric(
    csv_path=csv_path,
    parameters_names=['CustAST_m', 'CustAST_n', 'CustAST_ASToffset', 'CustAST_ASTall', 'CustAST_ASTaul'],
    outputs_names=['Heating:Electricity', 'Cooling:Electricity'],
)
print(f"  Cargado desde CSV: {len(p_loaded.outputs_param_simulation)} filas")
assert not p_loaded.outputs_param_simulation.empty

# ---------------------------------------------------------------------------
# PARTE B — sampling_lhs
# ---------------------------------------------------------------------------
print("\n=== PARTE B: sampling_lhs ===")

sim_lhs = build_custom_sim()
sim_lhs.set_parameters(
    accis_params_dict={
        'CustAST_m':         (0.01, 0.99),
        'CustAST_n':         (5.0,  23.0),
        'CustAST_ASToffset': (1.5,   5.0),
        'CustAST_ASTall':    (8.0,  16.0),
        'CustAST_ASTaul':    (28.0, 38.0),
    },
    use_dflt_values=True,
)
sim_lhs.set_problem(minimize_outputs=[True, True])
sim_lhs.set_building_floor_area(mode='all')

print("  sampling_lhs(num_samples=4)")
sim_lhs.sampling_lhs(num_samples=4)
print(f"  LHS samples shape: {sim_lhs.parameters_values_df.shape}")
assert not sim_lhs.parameters_values_df.empty

results_lhs = sim_lhs.run_parametric_simulation(
    out_dir=OUT_LHS,
    processes=2,
    keep_dirs=True,
    keep_input=True,
)
print(f"  Filas resultado LHS: {len(results_lhs)}")
assert not results_lhs.empty

sim_lhs.get_hourly_df(start_date='2024-06-01 01')
sim_lhs.get_monthly_df(start_date='2024-06-01 01')
sim_lhs.plot_categorical_boxplots(
    df_source='parametric',
    col='city',
    out_dir=OUT_LHS,
)

# ---------------------------------------------------------------------------
# PARTE C — sampling_custom: list_of_dicts y DataFrame
# ---------------------------------------------------------------------------
print("\n=== PARTE C: sampling_custom (list y DataFrame) ===")

sim_custom = build_custom_sim()
# Sin parámetros de rango — parameters_type='accim custom model' sin vary params
# Usamos sampling_custom para especificar sólo EPWs (sin parámetros variables)
sim_custom.set_parameters(use_dflt_values=True)   # sin accis_params_dict → lista vacía
sim_custom.set_problem()
sim_custom.set_building_floor_area(mode='all')

# sampling_custom — list of dicts (con sólo 'epw')
print("  sampling_custom(list of dicts)")
plan_list = [{'epw': EPW_S24}, {'epw': EPW_M24}]
sim_custom.sampling_custom(custom_plan=plan_list)
print(f"  parameters_values_df:\n{sim_custom.parameters_values_df}")

# sampling_custom — DataFrame
print("  sampling_custom(DataFrame)")
plan_df = pd.DataFrame({'epw': [EPW_S24, EPW_S25, EPW_M24]})
sim_custom.sampling_custom(custom_plan=plan_df)
print(f"  parameters_values_df:\n{sim_custom.parameters_values_df}")

results_custom = sim_custom.run_parametric_simulation(
    out_dir=OUT_CUSTOM,
    processes=1,
    keep_dirs=True,
    keep_input=True,
)
print(f"  Filas resultado custom sampling: {len(results_custom)}")
assert not results_custom.empty

sim_custom.get_hourly_df(start_date='2024-06-01 01')
sim_custom.get_monthly_df(start_date='2024-06-01 01')

print(f"\n=== SCRIPT 3 COMPLETADO — outputs en '{OUT_MORRIS}/', '{OUT_LHS}/', '{OUT_CUSTOM}/' ===")
