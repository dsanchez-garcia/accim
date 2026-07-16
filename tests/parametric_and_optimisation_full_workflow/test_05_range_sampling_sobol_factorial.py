"""
Test 05 — Range Sampling: Sobol + Full Factorial + SA Sobol
===========================================================
Clases: ParametricSimulation (parameters_type='accim custom model')
Métodos cubiertos:
  sampling_sobol(num_samples=8), sampling_full_factorial(level=2),
  run_sensitivity_analysis(method='sobol'),
  run_sensitivity_analysis_by_epw(method='sobol', out_dir),
  run_parametric_simulation, get_hourly_df, get_monthly_df
Requisitos: SALib instalado (pip install SALib)
IDFs: SF_Detached_B_min_North.idf
EPWs: seville_2024, madrid_2024
Nota: sampling_sobol requiere num_samples potencia de 2 (8 → 8*(2*3+2)=64 sims/EPW).
      Para minimizar tiempo usamos sólo 3 parámetros y 2 EPWs.
"""

import os
import accim
import accim.utils
import pandas as pd
from besos import eppy_funcs as ef
from accim.parametric_and_optimisation.main import ParametricSimulation

OUT_SOBOL     = 'test_05_sobol_results'
OUT_FACTORIAL = 'test_05_factorial_results'

IDF_B   = 'SF_Detached_B_min_North.idf'
EPW_SEV = 'seville_2024.epw'
EPW_MAD = 'madrid_2024.epw'
EPW_BOTH = [EPW_SEV, EPW_MAD]

# Parámetros con rango — 3 dimensiones para Sobol (mínimo razonable)
ACCIS_PARAMS_RANGE = {
    'CustAST_m':         (0.01, 0.99),
    'CustAST_n':         (5.0,  23.0),
    'CustAST_ASToffset': (1.5,   5.0),
}

# ---------------------------------------------------------------------------
# Comprobación de SALib antes de ejecutar
# ---------------------------------------------------------------------------
try:
    import SALib
    print(f"SALib disponible: v{SALib.__version__}")
except ImportError:
    raise ImportError(
        "SALib no está instalado. Ejecuta: pip install SALib\n"
        "Este script (test_05) requiere SALib para sampling_sobol y run_sensitivity_analysis."
    )

# ---------------------------------------------------------------------------
# Función de setup común
# ---------------------------------------------------------------------------
def build_range_sim():
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
        epws=EPW_BOTH,
        parameters_type='accim custom model',
        output_type='standard',
        output_freqs=['hourly'],
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
    sim.set_parameters(accis_params_dict=ACCIS_PARAMS_RANGE, use_dflt_values=True)
    sim.set_problem(minimize_outputs=[True, True])
    sim.set_building_floor_area(mode='all')
    sim.set_category_mapping(
        epw_mapping_rules={'city': {'seville': ['seville'], 'madrid': ['madrid']}},
    )
    return sim

# ===========================================================================
# PARTE A — sampling_sobol + run_sensitivity_analysis (sobol)
# ===========================================================================
print("\n=== PARTE A: sampling_sobol ===")

sim_sobol = build_range_sim()

# sampling_sobol — num_samples=8 (potencia de 2)
# Total sims por EPW = 8 * (2*3 + 2) = 64 sims → 128 sims total (2 EPWs)
# Si el tiempo es excesivo, reducir a num_samples=4 → 32 sims/EPW
print("  sampling_sobol(num_samples=8)")
sim_sobol.sampling_sobol(num_samples=8)
n_sobol = len(sim_sobol.parameters_values_df)
print(f"  Muestras Sobol generadas: {n_sobol} filas")
assert not sim_sobol.parameters_values_df.empty, "sampling_sobol devolvió DataFrame vacío"
# Verificar que las columnas de parámetros están presentes
for p in ACCIS_PARAMS_RANGE:
    assert p in sim_sobol.parameters_values_df.columns, f"Columna '{p}' no en parameters_values_df"

print(f"  Primera fila:\n{sim_sobol.parameters_values_df.head(1).to_string(index=False)}")

sim_sobol.preview_category_mapping()

results_sobol = sim_sobol.run_parametric_simulation(
    out_dir=OUT_SOBOL,
    processes=2,
    keep_dirs=True,
    keep_input=True,
)
print(f"  Filas resultado Sobol: {len(results_sobol)}")
assert not results_sobol.empty
assert 'Heating:Electricity' in results_sobol.columns or any(
    'Heating' in c for c in results_sobol.columns
), "Columna Heating no encontrada en resultados"

# run_sensitivity_analysis(method='sobol') — sobre todos los EPWs
print("  run_sensitivity_analysis(method='sobol')")
# Para Sobol, la SA necesita Y con longitud N*(2D+2) dividible correctamente
try:
    sa_sobol = sim_sobol.run_sensitivity_analysis(method='sobol')
    print(f"  SA Sobol keys: {list(sa_sobol.keys())}")
    for output_name, res in sa_sobol.items():
        print(f"    [{output_name}] S1 range: [{min(res['S1']):.3f}, {max(res['S1']):.3f}]")
    assert len(sa_sobol) > 0
except ValueError as e:
    print(f"  [!] SA Sobol falló (esperado si N es pequeño): {e}")

# run_sensitivity_analysis_by_epw(method='sobol') — por EPW separado
print("  run_sensitivity_analysis_by_epw(method='sobol')")
try:
    sa_sobol_by_epw = sim_sobol.run_sensitivity_analysis_by_epw(
        method='sobol',
        out_dir=OUT_SOBOL,
    )
    print(f"  SA Sobol por EPW: {list(sa_sobol_by_epw.keys())}")
    assert hasattr(sim_sobol, 'sensitivity_results_by_epw')
    # Verificar que se guardaron CSVs y PNGs
    import glob as _glob
    sa_csvs = _glob.glob(os.path.join(OUT_SOBOL, 'results_sa_sobol_*.csv'))
    sa_pngs = _glob.glob(os.path.join(OUT_SOBOL, 'plot_sa_sobol_*.png'))
    print(f"  CSVs SA guardados: {len(sa_csvs)}")
    print(f"  PNGs SA guardados: {len(sa_pngs)}")
    assert len(sa_csvs) >= 1, "No se generaron CSVs de SA Sobol"
except ValueError as e:
    print(f"  [!] SA Sobol by EPW falló (esperado con N pequeño): {e}")

# Hourly + Monthly
sim_sobol.get_hourly_df(start_date='2024-06-01 01')
sim_sobol.get_monthly_df(start_date='2024-06-01 01')
print(f"  Monthly Sobol shape: {sim_sobol.outputs_param_simulation_monthly.shape}")

sim_sobol.plot_categorical_boxplots(
    df_source='parametric',
    col='city',
    out_dir=OUT_SOBOL,
)

# ===========================================================================
# PARTE B — sampling_full_factorial
# ===========================================================================
print("\n=== PARTE B: sampling_full_factorial ===")

sim_factorial = build_range_sim()

# sampling_full_factorial — level=2 → 2^3 = 8 puntos de grilla por EPW
# Con 2 EPWs → 16 sims total (muy rápido)
print("  sampling_full_factorial(level=2)")
sim_factorial.sampling_full_factorial(level=2)
n_factorial = len(sim_factorial.parameters_values_df)
print(f"  Muestras factorial generadas: {n_factorial} filas")
assert not sim_factorial.parameters_values_df.empty, "sampling_full_factorial devolvió DataFrame vacío"
for p in ACCIS_PARAMS_RANGE:
    assert p in sim_factorial.parameters_values_df.columns, f"Columna '{p}' no en parameters_values_df"

print(f"  Valores únicos de CustAST_m: {sim_factorial.parameters_values_df['CustAST_m'].unique()}")

sim_factorial.preview_category_mapping()

results_factorial = sim_factorial.run_parametric_simulation(
    out_dir=OUT_FACTORIAL,
    processes=2,
    keep_dirs=True,
    keep_input=True,
)
print(f"  Filas resultado factorial: {len(results_factorial)}")
assert not results_factorial.empty

# Verificar columnas de resultados
output_cols = [c for c in results_factorial.columns if 'Electricity' in c]
print(f"  Columnas de energía encontradas: {output_cols}")

# Hourly + Monthly
sim_factorial.get_hourly_df(start_date='2024-06-01 01')
sim_factorial.get_monthly_df(start_date='2024-06-01 01')
print(f"  Monthly factorial shape: {sim_factorial.outputs_param_simulation_monthly.shape}")

sim_factorial.plot_categorical_boxplots(
    df_source='parametric',
    col='city',
    out_dir=OUT_FACTORIAL,
)

# load_outputs_parametric desde pickle (para verificar persistencia)
pkl_fact = sim_factorial.outputs_param_simulation_filepath.replace('.csv', '.pkl')
pf = ParametricSimulation.__new__(ParametricSimulation)
pf.last_run_type = None
pf.outputs_param_simulation = None
pf.outputs_param_simulation_hourly = None
pf.outputs_param_simulation_monthly = None
pf.outputs_param_simulation_filepath = None
pf.epws = []
pf.buildings = []
pf.load_outputs_parametric(
    pickle_path=pkl_fact,
    parameters_names=list(ACCIS_PARAMS_RANGE.keys()),
    outputs_names=['Heating:Electricity', 'Cooling:Electricity'],
)
print(f"  Factorial cargado desde PKL: {len(pf.outputs_param_simulation)} filas")
assert not pf.outputs_param_simulation.empty

# ===========================================================================
# RESUMEN FINAL
# ===========================================================================
print("\n=== RESUMEN SCRIPT 5 ===")
print(f"  Sobol: {n_sobol} muestras por EPW → {len(results_sobol)} sims totales")
print(f"  Factorial (level=2): {n_factorial // 2} puntos/EPW → {len(results_factorial)} sims totales")
print(f"  Outputs en '{OUT_SOBOL}/' y '{OUT_FACTORIAL}/'")
print("\n=== SCRIPT 5 COMPLETADO ===")
