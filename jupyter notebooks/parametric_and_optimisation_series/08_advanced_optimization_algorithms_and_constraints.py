# %% [markdown]
# # 08 - Advanced optimization: algorithms and constraints
#
# Goal: compare optimization algorithms and demonstrate simple feasibility filtering.
#
# ## Methods executed in this notebook
#
# Core ACCIM/BESOS functions used in the runnable flow:
# - `accim.utils.reduce_runtime`
# - `ef.get_building`
# - `OptimisationSimulation.discover_available_outputs`
# - `OptimisationSimulation.select_outputs`
# - `OptimisationSimulation.apply_outputs_preflight`
# - `OptimisationSimulation.set_outputs_for_simulation`
# - `OptimisationSimulation.set_parameters`
# - `OptimisationSimulation.set_problem`
# - `OptimisationSimulation.set_evaluator`
# - `OptimisationSimulation.estimate_optimisation_sims`
# - `OptimisationSimulation.run_optimisation`
# - `OptimisationSimulation.plot_pareto_front`

# %% [markdown]
# ## Step 1 - Import dependencies

# %%
from pathlib import Path

import accim
import pandas as pd
from besos import eppy_funcs as ef
from accim.parametric_and_optimisation.main import OptimisationSimulation

pd.set_option("display.max_columns", 200)

# %% [markdown]
# ## Step 2 - Resolve inputs and initialize optimisation object

# %%
PROJECT_ROOT = Path.cwd()
NOTEBOOK_DIR = Path(__file__).resolve().parent


IDF_FILE = PROJECT_ROOT / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_high_performance.idf"
if not IDF_FILE.exists():
	IDF_FILE = NOTEBOOK_DIR / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_high_performance.idf"

epw_seville = PROJECT_ROOT / "Seville.epw"
if not epw_seville.exists():
	epw_seville = NOTEBOOK_DIR / "Seville.epw"

epw_sydney = PROJECT_ROOT / "Sydney.epw"
if not epw_sydney.exists():
	epw_sydney = NOTEBOOK_DIR / "Sydney.epw"

EPWS = [
	str(epw_seville),
	str(epw_sydney),
]
RESULTS_DIRNAME = "nb08_advanced_optimization_results"

building = ef.get_building(str(IDF_FILE))
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

optim = OptimisationSimulation(
	building=building,
	parameters_type="accim custom model",
	epws=EPWS,
	output_freqs=["hourly"],
)

# %% [markdown]
# ## Step 3 - Configure outputs and problem definition

# %%
objective_meters = ["Heating:Electricity", "Cooling:Electricity"]
try:
	discovery = optim.discover_available_outputs(
		reduce_sim_time=True,
		prefer="testsimeplus",
	)
	df_meters_available = discovery["meters"]
	selection = optim.select_outputs(
		meters=objective_meters,
		match="case_insensitive",
		on_missing="raise",
		suggest=True,
	)
	df_meters_sel = selection["meters"]
except Exception as exc:
	print("Output discovery failed; continuing with explicit meters.")
	print(f"Discovery error: {exc}")
	df_meters_sel = pd.DataFrame(
		{"key_name": objective_meters, "frequency": ["hourly", "hourly"]}
	)

try:
	optim.apply_outputs_preflight(
		df_meters_sel=df_meters_sel,
		df_vars_sel=None,
		clean_mode="all",
		validate_before_apply=False,
		validate_after_apply=True,
		on_missing="raise",
	)
except Exception as exc:
	print("Outputs preflight failed; applying selected meters directly.")
	print(f"Preflight error: {exc}")
optim.set_outputs_for_simulation(df_output_meter=df_meters_sel)

accis_parameters = {
	"CustAST_m": (0.15, 0.95),
	"CustAST_n": (8, 23),
	"CustAST_ASToffset": (1.0, 6.0),
}
optim.set_parameters(accis_params_dict=accis_parameters)
optim.set_problem(minimize_outputs=[True, True])

# %% [markdown]
# ## Step 4 - Build evaluator explicitly and estimate campaign size

# %%
EVALUATIONS = 8
POPULATION_SIZE = 4

evaluator = optim.set_evaluator(
	epw=EPWS[0],
	out_dir=str(PROJECT_ROOT / RESULTS_DIRNAME / "evaluator_probe"),
)
print("Evaluator built:", type(evaluator).__name__)

estimated = optim.estimate_optimisation_sims(
	evaluations=EVALUATIONS,
	population_size=POPULATION_SIZE,
	epws=EPWS,
)
print("Estimated simulations:", estimated)

# %% [markdown]
# ## Step 5 - Run and compare algorithms
#
# Two algorithms are shown: `NSGAII` and `SPEA2`.

# %%
RUN_OPTIMIZATION = True
ALGORITHMS_TO_RUN = ["NSGAII"]

results_by_algorithm = {}

if RUN_OPTIMIZATION:
	for algorithm_name in ALGORITHMS_TO_RUN:
		outputs_optim = optim.run_optimisation(
			epws=EPWS,
			out_dir=str(PROJECT_ROOT / RESULTS_DIRNAME / algorithm_name.lower()),
			evaluations=EVALUATIONS,
			population_size=POPULATION_SIZE,
			algorithm=algorithm_name,
			processes=1,
			keep_df="all",
			keep_sim_files="non-dominated",
			keep_sim_files_batch_size=POPULATION_SIZE,
		)

		# Simple feasibility filter example: keep solutions below a total-energy cap.
		outputs_optim = outputs_optim.copy()
		outputs_optim["total_energy"] = (
			outputs_optim["Heating:Electricity"] + outputs_optim["Cooling:Electricity"]
		)
		feasible = outputs_optim[outputs_optim["total_energy"] <= outputs_optim["total_energy"].quantile(0.8)]
		results_by_algorithm[algorithm_name] = {
			"all": outputs_optim,
			"feasible": feasible,
		}
		print(f"{algorithm_name}: total={len(outputs_optim)} | feasible={len(feasible)}")
else:
	print("Optimization skipped. Set RUN_OPTIMIZATION = True to execute algorithm comparison.")

# %% [markdown]
# ## Step 6 - Plot Pareto front for the last run (if available)

# %%
if RUN_OPTIMIZATION and getattr(optim, "outputs_optimisation", None) is not None:
	optim.plot_pareto_front(
		color_by="CustAST_m",
		size_by="CustAST_n",
		out_dir=str(PROJECT_ROOT / RESULTS_DIRNAME),
		normalize_per_m2=False,
	)
	print("Pareto front plot generated.")
else:
	print("Pareto plotting skipped because optimization was not executed.")

