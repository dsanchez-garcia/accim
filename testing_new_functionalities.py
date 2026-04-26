"""
Testing new functionalities – Sensitivity Analysis (Morris) + MCDM
===================================================================
This script demonstrates two new analytical capabilities added to
the OptimParamSimulation class in branch feature/analysis_methods:

  10. Sensitivity Analysis (Morris method, per EPW)
      Identifies which parameters most influence Heating and Cooling
      electricity demand. Uses Morris sampling: N*(k+1) EnergyPlus
      simulations, with N=5 trajectories and k=5 parameters → 30 runs/EPW.
      Outputs:
        · results_sa_morris_<EPW>.csv  – mu, mu*, sigma per parameter
        · plot_sa_morris_<EPW>.png     – bar chart mu* vs sigma

  11. MCDM – Best compromise solution (per EPW)
      Selects the best single design from the full set of simulations
      using two multi-criteria decision-making methods:
        · Knee Point: minimises normalised Euclidean distance to Utopia point
        · TOPSIS (equal weights): standard TOPSIS with equal weighting
        · TOPSIS (weighted 70/30): prioritises heating over cooling
      Outputs:
        · results_mcdm_best_solutions.csv
        · plot_mcdm_best_solutions.png  – all solutions + best highlighted

Note: For publication quality, increase num_samples in sampling_morris
to at least 50 (300 runs/EPW).
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['figure.dpi'] = 150
import matplotlib.pyplot as plt

import accim
from accim.parametric_and_optimisation.main import OptimParamSimulation
from besos import eppy_funcs as ef


# def main():
# ---------------------------------------------------------------------------
# 1. Build the EnergyPlus model
# ---------------------------------------------------------------------------
building = ef.get_building('OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
accim.utils.set_occupancy_to_always(idf_object=building)
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

# ---------------------------------------------------------------------------
# 2. Instantiate OptimParamSimulation
# ---------------------------------------------------------------------------
parametric = OptimParamSimulation(
    building=building,
    parameters_type='accim custom model',
)

# ---------------------------------------------------------------------------
# 3. Select IDF outputs
# ---------------------------------------------------------------------------
df_vars = parametric.get_output_var_df_from_idf()
df_vars = df_vars[
    (df_vars['variable_name'].str.contains('Setpoint Temperature_No Tolerance')) |
    (df_vars['variable_name'].str.contains('Zone Operative Temperature')) |
    (df_vars['variable_name'].str.contains('Running Average Outdoor Air Temperature'))
]
parametric.set_output_var_df_to_idf(outputs_df=df_vars)
parametric.set_output_met_objects_to_idf(
    output_meters=['Heating:Electricity', 'Cooling:Electricity']
)

df_meters_ts, _ = parametric.get_outputs_df_from_testsim()
parametric.set_outputs_for_simulation(df_output_meter=df_meters_ts)

# ---------------------------------------------------------------------------
# 4. Define optimisation parameters (5-D search space)
# ---------------------------------------------------------------------------
accis_parameters = {
    'CustAST_m': (0.01, 0.99),
    'CustAST_n': (5, 23),
    'CustAST_ASToffset': (1.5, 5),
    'CustAST_ASTall': (8, 16),
    'CustAST_ASTaul': (28, 38),
}
parametric.set_parameters(accis_params_dict=accis_parameters)

# ---------------------------------------------------------------------------
# 5. Define the besos problem (needed for SA and MCDM)
# ---------------------------------------------------------------------------
parametric.set_problem(minimize_outputs=[True, True])

param_cols = ['CustAST_m', 'CustAST_n', 'CustAST_ASToffset', 'CustAST_ASTall', 'CustAST_ASTaul']
generated_files = []



# ---------------------------------------------------------------------------
# 10. Sensitivity Analysis (Morris) – separate results per EPW
# ---------------------------------------------------------------------------
# Morris method: N*(k+1) total runs, with k=5 parameters and N=5 trajectories
# → 5*(5+1) = 30 EnergyPlus runs per EPW (60 total for 2 EPWs).
# For publication quality, increase N to at least 50 (300 runs/EPW).

print("\n--- [10] Sensitivity Analysis (Morris) ---")

parametric.sampling_morris(num_samples=3, num_levels=4)  # 5*(5+1)=30 sims/EPW
parametric.run_parametric_simulation(
    epws=['Seville.epw', 'Sydney.epw'],
    out_dir='testing_new_functionalities',
    df=parametric.parameters_values_df,
    processes=6,
    keep_dirs=False,
)

# run_sensitivity_analysis_by_epw handles per-EPW SA internally:
# saves results_sa_morris_<EPW>.csv and plot_sa_morris_<EPW>.png
parametric.run_sensitivity_analysis_by_epw(
    method='morris',
    out_dir='testing_new_functionalities',
)

# ---------------------------------------------------------------------------
# 11. MCDM – Best compromise solution, per EPW
# ---------------------------------------------------------------------------
# For this test, MCDM is applied to the parametric simulation results
# (treating all rows as Pareto-optimal, since no real optimisation was run).
# In a real workflow, call plot_best_compromise_solutions() directly after
# run_optimisation() – no extra setup needed.
print("\n--- [11] MCDM – Best Compromise Solution ---")

# Build a minimal outputs_optimisation from the parametric SA results.
# We mark all rows as 'pareto-optimal' for demonstration purposes.
param_sim_df = parametric.outputs_param_simulation.copy()
param_sim_df['pareto-optimal'] = True
parametric.outputs_optimisation = param_sim_df

# plot_best_compromise_solutions handles per-EPW MCDM internally:
# saves results_mcdm_best_solutions.csv and plot_mcdm_best_solutions.png
parametric.plot_best_compromise_solutions(
    out_dir='testing_new_functionalities',
    mcdm_configs=[
        {'method': 'knee_point'},
        {'method': 'topsis'},
        {'method': 'topsis', 'weights': [0.7, 0.3], 'label': 'topsis_w70_30'},
    ],
)

# if __name__ == '__main__':
#     from multiprocessing import freeze_support
#     freeze_support()
#     main()


# if __name__ == '__main__':
#     from multiprocessing import freeze_support
#     freeze_support()
#     main()
