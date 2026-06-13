# %% [markdown]
# # 10 - Decision support, robustness, and session merge
#
# Goal: compute compromise solutions, run robustness checks, and merge sessions.
#
# ## Methods executed in this notebook
#
# Methods used when required source files are available:
# - `OptimisationSimulation.load_outputs_optimisation`
# - `OptimisationSimulation.get_best_compromise_solution`
# - `OptimisationSimulation.plot_best_compromise_solutions`
# - `OptimisationSimulation.run_clustering`
# - `OptimisationSimulation.run_robustness_analysis`
# - `ParametricSimulation.load_outputs_parametric`
# - `OptimisationSimulation.merge`

# %% [markdown]
# ## Step 1 - Import dependencies

# %%
from pathlib import Path

import pandas as pd
from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation

# %% [markdown]
# ## Step 2 - Locate latest optimisation/parametric sessions

# %%
PROJECT_ROOT = Path.cwd()
OUT_DIR = PROJECT_ROOT / "nb10_decision_support_results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

optim_csv = max(
	PROJECT_ROOT.glob("**/outputs_optimisation_*.csv"),
	key=lambda p: p.stat().st_mtime,
	default=None,
)
param_csv = max(
	PROJECT_ROOT.glob("**/outputs_param_simulation_*.csv"),
	key=lambda p: p.stat().st_mtime,
	default=None,
)

print("Optimisation source:", optim_csv)
print("Parametric source:", param_csv)

# %% [markdown]
# ## Step 3 - Load optimisation outputs and compute compromise solutions

# %%
optim = None

if optim_csv is not None:
	optim = OptimisationSimulation.__new__(OptimisationSimulation)
	optim.last_run_type = None
	optim.outputs_optimisation = None
	optim.outputs_optimisation_filepath = None
	optim.outputs_optimisation_hourly = None
	optim.outputs_optimisation_monthly = None
	optim.optimisation_csv_paths_non_dominated = []
	optim.optimisation_csv_paths_dominated = []
	optim.optimisation_csv_paths_non_dominated_by_epw = {}
	optim.optimisation_csv_paths_dominated_by_epw = {}
	optim.evaluators = {}
	optim.epws = []
	optim.buildings = []

	optim.load_outputs_optimisation(csv_path=str(optim_csv))
	print("Optimisation rows loaded:", len(optim.outputs_optimisation))

	try:
		sol_knee = optim.get_best_compromise_solution(method="knee_point")
		print("Knee-point compromise rows:", len(sol_knee))
	except Exception as exc:
		sol_knee = pd.DataFrame()
		print("Knee-point compromise skipped:", exc)

	try:
		sol_topsis = optim.get_best_compromise_solution(method="topsis", weights=[0.7, 0.3])
		print("TOPSIS compromise rows:", len(sol_topsis))
	except Exception as exc:
		sol_topsis = pd.DataFrame()
		print("TOPSIS compromise skipped:", exc)

	try:
		mcdm_df = optim.plot_best_compromise_solutions(
			out_dir=str(OUT_DIR),
			mcdm_configs=[
				{"method": "knee_point"},
				{"method": "topsis"},
				{"method": "topsis", "weights": [0.7, 0.3], "label": "topsis_w70_30"},
			],
			normalize_per_m2=False,
		)
		print("Compromise summary rows:", len(mcdm_df))
	except Exception as exc:
		print("Compromise plotting skipped:", exc)
else:
	print("No optimisation outputs available. Run notebook 07 or 08 first.")

# %% [markdown]
# ## Step 4 - Cluster solution families and run robustness analysis

# %%
if optim is not None and getattr(optim, "outputs_optimisation", None) is not None:
	try:
		optim.run_clustering(
			n_clusters=2,
			cluster_by="parameters",
			pareto_only=True,
			out_dir=str(OUT_DIR),
		)
		print("Clustering completed.")
	except Exception as exc:
		print("Clustering skipped:", exc)

	try:
		if "epw" in optim.outputs_optimisation.columns:
			epw_values = [str(v) for v in optim.outputs_optimisation["epw"].dropna().unique().tolist()]
		else:
			epw_values = []

		robust_epws = epw_values[:2]
		if robust_epws:
			if "sol_topsis" in locals() and not sol_topsis.empty:
				optimal_df = sol_topsis
			elif "sol_knee" in locals() and not sol_knee.empty:
				optimal_df = sol_knee
			else:
				optimal_df = optim.outputs_optimisation.head(1)

			optim.run_robustness_analysis(
				optimal_solutions_df=optimal_df,
				epws_robustness=robust_epws,
				out_dir=str(OUT_DIR),
				normalize_per_m2=False,
			)
			print("Robustness analysis completed.")
		else:
			print("Robustness analysis skipped: no EPW labels found in optimisation outputs.")
	except Exception as exc:
		print("Robustness analysis skipped:", exc)

# %% [markdown]
# ## Step 5 - Demonstrate session merge with parametric outputs

# %%
if optim is not None and param_csv is not None:
	try:
		param_sim = ParametricSimulation.__new__(ParametricSimulation)
		param_sim.last_run_type = None
		param_sim.outputs_param_simulation = None
		param_sim.outputs_param_simulation_hourly = None
		param_sim.outputs_param_simulation_monthly = None
		param_sim.outputs_param_simulation_filepath = None
		param_sim.epws = []
		param_sim.buildings = []
		param_sim.load_outputs_parametric(csv_path=str(param_csv))
		print("Parametric rows loaded:", len(param_sim.outputs_param_simulation))

		merged_obj = optim.merge([param_sim], inplace=False)
		print("Merged object type:", type(merged_obj).__name__)
	except Exception as exc:
		print("Session merge skipped:", exc)
else:
	print("Session merge skipped: missing optimisation or parametric source.")

