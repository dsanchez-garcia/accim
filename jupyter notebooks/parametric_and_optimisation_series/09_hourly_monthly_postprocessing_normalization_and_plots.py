# %% [markdown]
# # 09 - Hourly/monthly post-processing, normalization, and plots
#
# Goal: load saved outputs and run analysis/post-processing helpers.
#
# ## Methods executed in this notebook
#
# Methods used when source files are available:
# - `ParametricSimulation.load_outputs_parametric`
# - `ParametricSimulation.normalize_outputs`
# - `ParametricSimulation.get_hourly_df`
# - `ParametricSimulation.get_monthly_df`
# - `ParametricSimulation.plot_categorical_boxplots`
# - `OptimisationSimulation.load_outputs_optimisation`
# - `OptimisationSimulation.get_hourly_df_optimisation`
# - `OptimisationSimulation.get_monthly_df_optimisation`
# - `OptimisationSimulation.plot_parallel_coordinates`
# - `OptimisationSimulation.plot_pairwise_scatter_matrix`

# %% [markdown]
# ## Step 1 - Import dependencies

# %%
from pathlib import Path

from accim.parametric_and_optimisation.main import ParametricSimulation, OptimisationSimulation

# %% [markdown]
# ## Step 2 - Locate latest saved output files

# %%
PROJECT_ROOT = Path.cwd()
PLOTS_OUT_DIR = PROJECT_ROOT / "nb09_postprocessing_plots"
PLOTS_OUT_DIR.mkdir(parents=True, exist_ok=True)

parametric_csv = max(
	PROJECT_ROOT.glob("**/outputs_param_simulation_*.csv"),
	key=lambda p: p.stat().st_mtime,
	default=None,
)
optim_csv = max(
	PROJECT_ROOT.glob("**/outputs_optimisation_*.csv"),
	key=lambda p: p.stat().st_mtime,
	default=None,
)

print("Latest parametric CSV:", parametric_csv)
print("Latest optimisation CSV:", optim_csv)

# %% [markdown]
# ## Step 3 - Parametric post-processing (if parametric outputs exist)

# %%
if parametric_csv is not None:
	parametric = ParametricSimulation.__new__(ParametricSimulation)
	parametric.last_run_type = None
	parametric.outputs_param_simulation = None
	parametric.outputs_param_simulation_hourly = None
	parametric.outputs_param_simulation_monthly = None
	parametric.outputs_param_simulation_filepath = None
	parametric.outputs_normalized = False
	parametric.epws = []
	parametric.buildings = []

	parametric.load_outputs_parametric(csv_path=str(parametric_csv))
	print("Loaded parametric rows:", len(parametric.outputs_param_simulation))

	try:
		parametric.normalize_outputs(df_types=["parametric"])
		print("Parametric normalization completed.")
	except Exception as exc:
		print("Parametric normalization skipped:", exc)

	try:
		parametric.get_hourly_df(start_date="2024-01-01 01", normalize_per_m2=False)
		print("Parametric hourly shape:", parametric.outputs_param_simulation_hourly.shape)
	except Exception as exc:
		print("Parametric hourly expansion skipped:", exc)

	try:
		parametric.get_monthly_df(start_date="2024-01-01 01", normalize_per_m2=False)
		print("Parametric monthly shape:", parametric.outputs_param_simulation_monthly.shape)
	except Exception as exc:
		print("Parametric monthly aggregation skipped:", exc)

	try:
		parametric.plot_categorical_boxplots(
			df_source="parametric",
			col="epw",
			out_dir=str(PLOTS_OUT_DIR),
			normalize_per_m2=False,
		)
		print("Parametric boxplots generated.")
	except Exception as exc:
		print("Parametric boxplots skipped:", exc)
else:
	print("No parametric outputs found. Run notebook 01/02/03/05/06 first.")

# %% [markdown]
# ## Step 4 - Optimisation post-processing (if optimisation outputs exist)

# %%
if optim_csv is not None:
	optim = OptimisationSimulation.__new__(OptimisationSimulation)
	optim.last_run_type = None
	optim.outputs_optimisation = None
	optim.outputs_optimisation_filepath = None
	optim.outputs_optimisation_hourly = None
	optim.outputs_optimisation_monthly = None
	optim.outputs_normalized = False
	optim.optimisation_csv_paths_non_dominated = []
	optim.optimisation_csv_paths_dominated = []
	optim.optimisation_csv_paths_non_dominated_by_epw = {}
	optim.optimisation_csv_paths_dominated_by_epw = {}
	optim.evaluators = {}
	optim.epws = []
	optim.buildings = []

	optim.load_outputs_optimisation(csv_path=str(optim_csv))
	print("Loaded optimisation rows:", len(optim.outputs_optimisation))

	try:
		optim.get_hourly_df_optimisation(
			only_pareto_optimal=True,
			skip_confirmation=True,
			start_date="2024-01-01 01",
			normalize_per_m2=False,
		)
		if optim.outputs_optimisation_hourly is not None:
			print("Optimisation hourly shape:", optim.outputs_optimisation_hourly.shape)
	except Exception as exc:
		print("Optimisation hourly expansion skipped:", exc)

	try:
		optim.get_monthly_df_optimisation(start_date="2024-01-01 01", normalize_per_m2=False)
		if optim.outputs_optimisation_monthly is not None:
			print("Optimisation monthly shape:", optim.outputs_optimisation_monthly.shape)
	except Exception as exc:
		print("Optimisation monthly aggregation skipped:", exc)

	try:
		optim.plot_parallel_coordinates(out_dir=str(PLOTS_OUT_DIR))
		print("Parallel coordinates plot generated.")
	except Exception as exc:
		print("Parallel coordinates skipped:", exc)

	try:
		optim.plot_pairwise_scatter_matrix(out_dir=str(PLOTS_OUT_DIR), normalize_per_m2=False)
		print("Pairwise scatter matrix generated.")
	except Exception as exc:
		print("Pairwise scatter matrix skipped:", exc)
else:
	print("No optimisation outputs found. Run notebook 07/08 first.")

