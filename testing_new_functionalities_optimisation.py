"""
Testing new functionalities – Optimisation workflow
====================================================
This script demonstrates all post-processing capabilities of
OptimParamSimulation using a real NSGA-II optimisation run.

Workflow:
  1–9.  Setup: model, outputs, parameters, problem definition.
  10.   NSGA-II optimisation → outputs_optimisation (pareto-optimal column set).
  11.   MCDM – Best compromise solutions (Knee Point + TOPSIS) on Pareto front.
  12.   Data Visualization – Pareto front, parallel coordinates, pairwise scatter.
  13.   Clustering – K-Means grouping of Pareto-optimal solutions.
  14.   Robustness Analysis – Re-evaluate best designs under alternative EPWs.
  15.   Sensitivity Analysis (Morris, SEPARATE parametric run) – per EPW.

Note: SA (step 15) requires an independent parametric run with Morris sampling,
because NSGA-II does NOT sample the parameter space uniformly; using its
evaluations for SA would produce methodologically invalid indices.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['figure.dpi'] = 150
import matplotlib.pyplot as plt

import accim
from accim.parametric_and_optimisation.main import OptimParamSimulation
from besos import eppy_funcs as ef

#
OUT_DIR = 'testing_new_functionalities_optimisation'
EPW_LIST = ['Seville.epw', 'Sydney.epw']

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
# 5. Define the optimisation problem
# ---------------------------------------------------------------------------
parametric.set_problem(minimize_outputs=[True, True])

# ---------------------------------------------------------------------------
# 10. NSGA-II Optimisation
# ---------------------------------------------------------------------------
# After this call, parametric.outputs_optimisation will contain all evaluated
# solutions with the 'pareto-optimal' column correctly populated.
print("\n--- [10] NSGA-II Optimisation ---")
parametric.run_optimisation(
    algorithm='NSGAII',
    epws=EPW_LIST,
    out_dir=OUT_DIR,
    evaluations=20,
    population_size=10,
    processes=8,
    keep_df='all',
    keep_sim_files='all',
    keep_sim_files_batch_size=10,
)

##
import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['figure.dpi'] = 150
import matplotlib.pyplot as plt

import accim
from accim.parametric_and_optimisation.main import OptimParamSimulation
from besos import eppy_funcs as ef

#
OUT_DIR = 'testing_new_functionalities_optimisation'


parametric = OptimParamSimulation()
# instance.load_outputs_optimisation(pickle_path='testing_new_functionalities_optimisation/outputs_optimisation.pkl')
parametric.load_outputs_optimisation(pickle_path='testing_new_functionalities_optimisation/outputs_optimisation_20260427_134516.pkl')
# instance.load_outputs_optimisation(json_path='testing_new_functionalities_optimisation/outputs_optimisation_25400.json')



# parametric.get_hourly_df_optimisation()
#
# optim_pkl = f'{OUT_DIR}/outputs_optimisation.pkl'
# parametric.outputs_optimisation.to_pickle(optim_pkl)
# parametric.outputs_optimisation_hourly.to_pickle(f'{OUT_DIR}/outputs_optimisation_hourly.pkl')
# print(f"  Saved optimisation outputs to {optim_pkl}")

# ---------------------------------------------------------------------------
# 11. MCDM – Best compromise solutions, per EPW
# ---------------------------------------------------------------------------
# outputs_optimisation already has 'pareto-optimal' set correctly by
# run_optimisation – no mock or override needed.
print("\n--- [11] MCDM – Best Compromise Solution ---")
parametric.plot_best_compromise_solutions(
    out_dir=OUT_DIR,
    mcdm_configs=[
        {'method': 'knee_point'},
        {'method': 'topsis'},
        {'method': 'topsis', 'weights': [0.7, 0.3], 'label': 'topsis_w70_30'},
    ],
)

# ---------------------------------------------------------------------------
# 12. Data Visualization
# ---------------------------------------------------------------------------
print("\n--- [12] Data Visualization ---")
parametric.plot_pareto_front(
    out_dir=OUT_DIR,
    color_by='CustAST_ASToffset',
    size_by='CustAST_m',
)
parametric.plot_parallel_coordinates(out_dir=OUT_DIR)
parametric.plot_pairwise_scatter_matrix(out_dir=OUT_DIR)

# ---------------------------------------------------------------------------
# 13. Clustering of Optimal Solutions (K-Means)
# ---------------------------------------------------------------------------
print("\n--- [13] Clustering Optimal Solutions ---")
try:
    parametric.run_clustering(
        n_clusters=3,
        cluster_by='parameters',
        pareto_only=True,
        out_dir=OUT_DIR,
    )
    # Visualize clustered Pareto front (colored by cluster ID)
    parametric.plot_pareto_front(color_by='Cluster_ID', out_dir=OUT_DIR)
except Exception as e:
    print(f"Clustering error (likely too few Pareto-optimal points): {e}")

# ---------------------------------------------------------------------------
# 14. Robustness Analysis
# ---------------------------------------------------------------------------
# Use the MCDM results (best compromise solutions) as the candidate set.
# Re-simulate each candidate under additional/alternative EPW scenarios.
print("\n--- [14] Robustness Analysis ---")
try:
    mcdm_df = pd.read_csv(f'{OUT_DIR}/results_mcdm_best_solutions.csv')
    best_solutions = mcdm_df.head(2).copy()
    parametric.run_robustness_analysis(
        optimal_solutions_df=best_solutions,
        epws_robustness=parametric.epws,   # here you can pass future/extreme EPWs
        out_dir=f'{OUT_DIR}_robustness',
    )
except FileNotFoundError:
    print("MCDM results not found; skipping robustness analysis.")
except Exception as e:
    print(f"Robustness analysis error: {e}")

# ---------------------------------------------------------------------------
## 15. Sensitivity Analysis (Morris) – SEPARATE independent parametric run
# ---------------------------------------------------------------------------
# IMPORTANT: NSGA-II evaluations cannot be used for SA because the optimizer
# does NOT sample the parameter space uniformly/randomly. A dedicated
# Morris/Sobol-sampled parametric simulation is required.
print("\n--- [15] Sensitivity Analysis (Morris, independent parametric run) ---")

# 15a. Generate Morris samples (N*(k+1) = 3*(5+1) = 18 per EPW)
parametric.sampling_morris(num_samples=3, num_levels=4)

# 15b. Run parametric simulation with Morris samples
parametric.run_parametric_simulation(
    epws=EPW_LIST,
    out_dir=f'{OUT_DIR}_sa',
    df=parametric.parameters_values_df,
    processes=8,
    keep_dirs=False,
)

param_pkl = f'{OUT_DIR}_sa/outputs_parametric.pkl'
parametric.outputs_param_simulation.to_pickle(param_pkl)
print(f"  Saved parametric outputs to {param_pkl}")


# 15c. Compute Morris indices and generate plots per EPW
#      Saves: results_sa_morris_<EPW>.csv and plot_sa_morris_<EPW>.png
parametric.run_sensitivity_analysis_by_epw(
    method='morris',
    out_dir=f'{OUT_DIR}_sa',
)

# ---------------------------------------------------------------------------
## 16. Testing Load/Resume Functionalities
# ---------------------------------------------------------------------------
print("\n--- [16] Testing Load/Resume Functionalities ---")

import pandas as pd

# 16a. Save Parametric Outputs to Pickle
# param_pkl = f'{OUT_DIR}_sa/outputs_parametric.pkl'
# parametric.outputs_param_simulation.to_pickle(param_pkl)
# print(f"  Saved parametric outputs to {param_pkl}")

# 16b. Clear memory and Load Parametric Outputs
parametric.outputs_param_simulation = None
parametric.last_run_type = None

parametric.load_outputs_parametric(pickle_path=param_pkl)
print(f"  Loaded parametric outputs via load_outputs_parametric(). last_run_type: {parametric.last_run_type}")

# 16c. Save Optimisation Outputs to Pickle
# optim_pkl = f'{OUT_DIR}/outputs_optimisation.pkl'
# parametric.outputs_optimisation.to_pickle(optim_pkl)
# print(f"  Saved optimisation outputs to {optim_pkl}")

# 16d. Clear memory and Load Optimisation Outputs
parametric.outputs_optimisation = None
parametric.last_run_type = None

parametric.load_outputs_optimisation(pickle_path=optim_pkl)
print(f"  Loaded optimisation outputs via load_outputs_optimisation(). last_run_type: {parametric.last_run_type}")
