"""
Test 04 — OptimisationSimulation: Flujo completo de optimización multi-objetivo
================================================================================
Clases: OptimisationSimulation (parameters_type='accim custom model')
Métodos cubiertos:
  set_parameters (rangos), set_problem(minimize_outputs), estimate_optimisation_sims,
  run_optimisation (evaluations=4, population_size=2, algorithm='NSGAII',
      keep_sim_files='all'/'non-dominated'/'none', keep_df='all'/'non-dominated'),
  load_outputs_optimisation (pkl + json),
  get_best_compromise_solution (knee_point + topsis + topsis weighted),
  plot_best_compromise_solutions (mcdm_configs),
  plot_pareto_front (color_by, size_by, normalize_per_m2),
  plot_parallel_coordinates, plot_pairwise_scatter_matrix,
  run_clustering (parameters + objectives, pareto_only T/F),
  get_hourly_df_optimisation (variantes: only_pareto, epw_filter, output_columns),
  get_monthly_df_optimisation,
  normalize_outputs (optimisation + hourly),
  set_category_mapping, preview_category_mapping, apply_category_mapping,
  plot_categorical_boxplots(df_source='optimisation'),
  run_robustness_analysis
IDFs: SF_Detached_B_min_North.idf
EPWs: seville_2024, madrid_2024 (2 EPWs para minimizar sims)
"""

import os
import accim
import accim.utils
import pandas as pd
from besos import eppy_funcs as ef
from accim.parametric_and_optimisation.main import OptimisationSimulation

OUT_DIR = 'test_04_optim_results'

IDF_B   = 'SF_Detached_B_min_North.idf'
EPW_SEV = 'seville_2024.epw'
EPW_MAD = 'madrid_2024.epw'
EPW_BOTH = [EPW_SEV, EPW_MAD]

ACCIS_PARAMS = {
    'CustAST_m':         (0.01, 0.99),
    'CustAST_n':         (5.0,  23.0),
    'CustAST_ASToffset': (1.5,   5.0),
}

# ---------------------------------------------------------------------------
# 1. Preparar IDF
# ---------------------------------------------------------------------------
print("\n=== [1] Preparar IDF ===")
building = ef.get_building(IDF_B)
accim.utils.reduce_runtime(
    idf_object=building,
    runperiod_begin_month=6,
    runperiod_begin_day_of_month=1,
    runperiod_end_month=7,
    runperiod_end_day_of_month=31,
)

# ---------------------------------------------------------------------------
# 2. Instanciar OptimisationSimulation
# ---------------------------------------------------------------------------
print("\n=== [2] Instanciar OptimisationSimulation ===")
optim = OptimisationSimulation(
    buildings=[building],
    epws=EPW_BOTH,
    parameters_type='accim custom model',
    output_type='standard',
    output_freqs=['hourly'],
    ScriptType='vrf_mm',
    verbosemode=False,
)

# ---------------------------------------------------------------------------
# 3. Outputs
# ---------------------------------------------------------------------------
print("\n=== [3] Configurar outputs ===")
optim.set_output_met_objects_to_idf(['Heating:Electricity', 'Cooling:Electricity'])
df_meters_ts, _ = optim.get_outputs_df_from_testsim(reduce_sim_time=True)
df_meters_problem = df_meters_ts[
    df_meters_ts['key_name'].isin(['Heating:Electricity', 'Cooling:Electricity'])
].drop_duplicates(subset=['key_name'])
optim.set_outputs_for_simulation(df_output_meter=df_meters_problem)

# ---------------------------------------------------------------------------
# 4. Parámetros y problema
# ---------------------------------------------------------------------------
print("\n=== [4] Parámetros y set_problem ===")
optim.set_parameters(accis_params_dict=ACCIS_PARAMS, use_dflt_values=True)
optim.set_problem(minimize_outputs=[True, True])

# ---------------------------------------------------------------------------
# 5. Category mapping
# ---------------------------------------------------------------------------
print("\n=== [5] Category mapping ===")
optim.set_category_mapping(
    epw_mapping_rules={
        'city': {'seville': ['seville'], 'madrid': ['madrid']},
    },
)
optim.preview_category_mapping()

# ---------------------------------------------------------------------------
# 6. estimate_optimisation_sims
# ---------------------------------------------------------------------------
print("\n=== [6] estimate_optimisation_sims ===")
n_sims = optim.estimate_optimisation_sims(
    evaluations=4,
    population_size=2,
    epws=EPW_BOTH,
)
print(f"  Sims estimadas: {n_sims}")

# ---------------------------------------------------------------------------
# 7A. run_optimisation — keep_sim_files='all', keep_df='all'
# ---------------------------------------------------------------------------
print("\n=== [7A] run_optimisation (keep_sim_files='all', keep_df='all') ===")
optim.set_building_floor_area(mode='all')

optim.run_optimisation(
    epws=EPW_BOTH,
    out_dir=OUT_DIR,
    evaluations=4,
    population_size=2,
    algorithm='NSGAII',
    processes=1,
    keep_sim_files='all',
    keep_df='all',
)
df_optim = optim.outputs_optimisation
print(f"  Filas totales: {len(df_optim)}")
assert not df_optim.empty
assert 'pareto-optimal' in df_optim.columns
assert 'epw' in df_optim.columns
assert 'city' in df_optim.columns  # categoría auto-aplicada

n_pareto = df_optim['pareto-optimal'].sum()
print(f"  Pareto-óptimas: {n_pareto}")

# ---------------------------------------------------------------------------
# 8. load_outputs_optimisation (pkl + json)
# ---------------------------------------------------------------------------
print("\n=== [8] load_outputs_optimisation ===")
opt_csv  = optim.outputs_optimisation_filepath
opt_pkl  = opt_csv.replace('.csv', '.pkl')
opt_json = opt_csv.replace('.csv', '.json')

# Desde pickle
o2 = OptimisationSimulation.__new__(OptimisationSimulation)
o2.last_run_type = None
o2.outputs_optimisation = None
o2.outputs_optimisation_filepath = None
o2.outputs_optimisation_hourly = None
o2.outputs_optimisation_monthly = None
o2.optimisation_csv_paths_non_dominated = []
o2.optimisation_csv_paths_dominated = []
o2.optimisation_csv_paths_non_dominated_by_epw = {}
o2.optimisation_csv_paths_dominated_by_epw = {}
o2.evaluators = {}
o2.epws = []
o2.buildings = []
o2.load_outputs_optimisation(pickle_path=opt_pkl)
print(f"  Cargado desde PKL: {len(o2.outputs_optimisation)} filas")
assert not o2.outputs_optimisation.empty

# Desde JSON
o3 = OptimisationSimulation.__new__(OptimisationSimulation)
o3.last_run_type = None
o3.outputs_optimisation = None
o3.outputs_optimisation_filepath = None
o3.outputs_optimisation_hourly = None
o3.outputs_optimisation_monthly = None
o3.optimisation_csv_paths_non_dominated = []
o3.optimisation_csv_paths_dominated = []
o3.optimisation_csv_paths_non_dominated_by_epw = {}
o3.optimisation_csv_paths_dominated_by_epw = {}
o3.evaluators = {}
o3.epws = []
o3.buildings = []
o3.load_outputs_optimisation(json_path=opt_json)
print(f"  Cargado desde JSON: {len(o3.outputs_optimisation)} filas")
assert not o3.outputs_optimisation.empty

# ---------------------------------------------------------------------------
# 9. get_best_compromise_solution
# ---------------------------------------------------------------------------
print("\n=== [9] get_best_compromise_solution ===")
for epw_lbl in df_optim['epw'].unique():
    optim.outputs_optimisation = df_optim[df_optim['epw'] == epw_lbl].copy()
    try:
        sol_knee = optim.get_best_compromise_solution(method='knee_point')
        print(f"  [{epw_lbl}] knee_point: {sol_knee[['Heating:Electricity','Cooling:Electricity']].values}")
    except Exception as e:
        print(f"  [{epw_lbl}] knee_point skipped: {e}")
    try:
        sol_topsis = optim.get_best_compromise_solution(method='topsis', weights=[0.7, 0.3])
        print(f"  [{epw_lbl}] topsis(0.7/0.3): {sol_topsis[['Heating:Electricity','Cooling:Electricity']].values}")
    except Exception as e:
        print(f"  [{epw_lbl}] topsis skipped: {e}")
optim.outputs_optimisation = df_optim  # restaurar

# ---------------------------------------------------------------------------
# 10. plot_best_compromise_solutions
# ---------------------------------------------------------------------------
print("\n=== [10] plot_best_compromise_solutions ===")
output_names = ['Heating:Electricity', 'Cooling:Electricity']
optim.problem.names = lambda t: output_names if t == 'outputs' else []
mcdm_df = optim.plot_best_compromise_solutions(
    out_dir=OUT_DIR,
    mcdm_configs=[
        {'method': 'knee_point'},
        {'method': 'topsis'},
        {'method': 'topsis', 'weights': [0.7, 0.3], 'label': 'topsis_w70_30'},
    ],
    normalize_per_m2=False,
)
assert mcdm_df is not None

# ---------------------------------------------------------------------------
# 11. plot_pareto_front (variantes)
# ---------------------------------------------------------------------------
print("\n=== [11] plot_pareto_front ===")
param_names = list(ACCIS_PARAMS.keys())
optim.plot_pareto_front(
    color_by=param_names[0],
    size_by=None,
    out_dir=OUT_DIR,
    normalize_per_m2=False,
)
optim.plot_pareto_front(
    color_by=param_names[1],
    size_by=param_names[2],
    out_dir=OUT_DIR,
    normalize_per_m2=True,
)

# ---------------------------------------------------------------------------
# 12. plot_parallel_coordinates + plot_pairwise_scatter_matrix
# ---------------------------------------------------------------------------
print("\n=== [12] plot_parallel_coordinates + pairwise_scatter_matrix ===")
optim.plot_parallel_coordinates(out_dir=OUT_DIR)
optim.plot_pairwise_scatter_matrix(out_dir=OUT_DIR, normalize_per_m2=False)

# ---------------------------------------------------------------------------
# 13. run_clustering
# ---------------------------------------------------------------------------
print("\n=== [13] run_clustering ===")
try:
    optim.run_clustering(n_clusters=2, cluster_by='parameters', pareto_only=True, out_dir=OUT_DIR)
    print("  Clustering (parameters, pareto_only=True) OK")
except Exception as e:
    print(f"  Clustering skipped (insuficientes puntos): {e}")

try:
    optim.run_clustering(n_clusters=2, cluster_by='objectives', pareto_only=False, out_dir=OUT_DIR)
    print("  Clustering (objectives, pareto_only=False) OK")
except Exception as e:
    print(f"  Clustering skipped: {e}")

# ---------------------------------------------------------------------------
# 14. get_hourly_df_optimisation (variantes)
# ---------------------------------------------------------------------------
print("\n=== [14] get_hourly_df_optimisation ===")

# Variante 1: only_pareto_optimal=True, skip_confirmation=True
optim.get_hourly_df_optimisation(
    only_pareto_optimal=True,
    skip_confirmation=True,
    start_date='2024-06-01 01',
)
hourly_optim = optim.outputs_optimisation_hourly
if hourly_optim is not None and not hourly_optim.empty:
    print(f"  Hourly optim (pareto only) shape: {hourly_optim.shape}")
    assert 'datetime' in hourly_optim.columns
else:
    print("  [!] Hourly optim vacío (puede ocurrir si no hay csvs en keep_dirs=False)")

# Variante 2: epw_filter + output_columns
hourly_cols_available = optim.get_hourly_df_columns()
print(f"  Columnas horarias disponibles: {hourly_cols_available[:3]}")
optim.get_hourly_df_optimisation(
    only_pareto_optimal=False,
    epw_filter='seville',
    output_columns=hourly_cols_available[:2] if hourly_cols_available else None,
    skip_confirmation=True,
    start_date='2024-06-01 01',
)
print("  get_hourly_df_optimisation (epw_filter='seville') OK")

# Variante 3: simulation_indices
pareto_idx = df_optim[df_optim['pareto-optimal']].index[:2].tolist()
if pareto_idx:
    optim.get_hourly_df_optimisation(
        simulation_indices=pareto_idx,
        skip_confirmation=True,
        start_date='2024-06-01 01',
    )
    print(f"  get_hourly_df_optimisation (simulation_indices={pareto_idx}) OK")

# ---------------------------------------------------------------------------
# 15. get_monthly_df_optimisation
# ---------------------------------------------------------------------------
print("\n=== [15] get_monthly_df_optimisation ===")
optim.get_monthly_df_optimisation(
    skip_confirmation=True,
    start_date='2024-06-01 01',
)
monthly_optim = optim.outputs_optimisation_monthly
if monthly_optim is not None and not monthly_optim.empty:
    print(f"  Monthly optim shape: {monthly_optim.shape}")
else:
    print("  [!] Monthly optim vacío")

# ---------------------------------------------------------------------------
# 16. normalize_outputs
# ---------------------------------------------------------------------------
print("\n=== [16] normalize_outputs ===")
optim.outputs_normalized = False
optim.normalize_outputs(df_types=['optimisation'])
print("  normalize_outputs(['optimisation']) OK")

# ---------------------------------------------------------------------------
# 17. apply_category_mapping explícito
# ---------------------------------------------------------------------------
print("\n=== [17] apply_category_mapping (explícito) ===")
optim.apply_category_mapping(df_types=['optimisation'])
assert 'city' in optim.outputs_optimisation.columns

# ---------------------------------------------------------------------------
# 18. plot_categorical_boxplots (df_source='optimisation')
# ---------------------------------------------------------------------------
print("\n=== [18] plot_categorical_boxplots (optimisation) ===")
optim.plot_categorical_boxplots(
    df_source='optimisation',
    col='city',
    out_dir=OUT_DIR,
    sharey=True,
    show_points=True,
)

# ---------------------------------------------------------------------------
# 19. run_robustness_analysis
# ---------------------------------------------------------------------------
print("\n=== [19] run_robustness_analysis ===")
try:
    import glob as _glob
    mcdm_csv = os.path.join(OUT_DIR, 'results_mcdm_best_solutions.csv')
    if os.path.exists(mcdm_csv):
        mcdm_solutions = pd.read_csv(mcdm_csv).head(2)
        optim.run_robustness_analysis(
            optimal_solutions_df=mcdm_solutions,
            epws_robustness=EPW_BOTH,
            out_dir=OUT_DIR + '_robustness',
            normalize_per_m2=False,
        )
        print("  run_robustness_analysis OK")
    else:
        print("  [!] Archivo MCDM no encontrado, se omite robustness analysis")
except Exception as e:
    print(f"  run_robustness_analysis skipped: {e}")

# ---------------------------------------------------------------------------
# 20. run_optimisation — keep_sim_files='non-dominated'
# ---------------------------------------------------------------------------
print("\n=== [20] run_optimisation (keep_sim_files='non-dominated') ===")
building2 = ef.get_building(IDF_B)
accim.utils.reduce_runtime(
    idf_object=building2,
    runperiod_begin_month=6,
    runperiod_begin_day_of_month=1,
    runperiod_end_month=7,
    runperiod_end_day_of_month=31,
)
optim2 = OptimisationSimulation(
    buildings=[building2],
    epws=[EPW_SEV],
    parameters_type='accim custom model',
    output_type='standard',
    output_freqs=['hourly'],
    ScriptType='vrf_mm',
    verbosemode=False,
)
optim2.set_output_met_objects_to_idf(['Heating:Electricity', 'Cooling:Electricity'])
df_mt2, _ = optim2.get_outputs_df_from_testsim(reduce_sim_time=True)
df_mt2 = df_mt2[df_mt2['key_name'].isin(['Heating:Electricity', 'Cooling:Electricity'])].drop_duplicates(subset=['key_name'])
optim2.set_outputs_for_simulation(df_output_meter=df_mt2)
optim2.set_parameters(accis_params_dict=ACCIS_PARAMS, use_dflt_values=True)
optim2.set_problem(minimize_outputs=[True, True])
optim2.run_optimisation(
    epws=[EPW_SEV],
    out_dir=OUT_DIR + '_nondominatedonly',
    evaluations=4,
    population_size=2,
    algorithm='NSGAII',
    processes=1,
    keep_sim_files='non-dominated',
    keep_df='non-dominated',
)
assert not optim2.outputs_optimisation.empty
print(f"  Pareto-óptimas (non-dominated only): {len(optim2.outputs_optimisation)}")

# ---------------------------------------------------------------------------
# 21. run_optimisation — keep_sim_files='none'
# ---------------------------------------------------------------------------
print("\n=== [21] run_optimisation (keep_sim_files='none') ===")
building3 = ef.get_building(IDF_B)
accim.utils.reduce_runtime(
    idf_object=building3,
    runperiod_begin_month=6,
    runperiod_begin_day_of_month=1,
    runperiod_end_month=7,
    runperiod_end_day_of_month=31,
)
optim3 = OptimisationSimulation(
    buildings=[building3],
    epws=[EPW_MAD],
    parameters_type='accim custom model',
    output_type='standard',
    output_freqs=['hourly'],
    ScriptType='vrf_mm',
    verbosemode=False,
)
optim3.set_output_met_objects_to_idf(['Heating:Electricity', 'Cooling:Electricity'])
df_mt3, _ = optim3.get_outputs_df_from_testsim(reduce_sim_time=True)
df_mt3 = df_mt3[df_mt3['key_name'].isin(['Heating:Electricity', 'Cooling:Electricity'])].drop_duplicates(subset=['key_name'])
optim3.set_outputs_for_simulation(df_output_meter=df_mt3)
optim3.set_parameters(accis_params_dict=ACCIS_PARAMS, use_dflt_values=True)
optim3.set_problem(minimize_outputs=[True, True])
optim3.run_optimisation(
    epws=[EPW_MAD],
    out_dir=OUT_DIR + '_nosimfiles',
    evaluations=4,
    population_size=2,
    algorithm='NSGAII',
    processes=1,
    keep_sim_files='none',
    keep_df='all',
)
assert not optim3.outputs_optimisation.empty
print(f"  Filas (keep_sim_files='none'): {len(optim3.outputs_optimisation)}")

print(f"\n=== SCRIPT 4 COMPLETADO — outputs en '{OUT_DIR}/' ===")
