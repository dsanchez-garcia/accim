# %% [markdown]
# # 05 - Sampling strategies and sensitivity analysis
#
# Goal: connect Sobol/Morris sampling plans with sensitivity-analysis outputs.
#
# ## Methods executed in this notebook
#
# Core ACCIM/BESOS functions used in the runnable flow:
# - `accim.utils.reduce_runtime`
# - `ef.get_building`
# - `ParametricSimulation.discover_available_outputs`
# - `ParametricSimulation.select_outputs`
# - `ParametricSimulation.apply_outputs_preflight`
# - `ParametricSimulation.set_outputs_for_simulation`
# - `ParametricSimulation.set_parameters`
# - `ParametricSimulation.set_problem`
# - `ParametricSimulation.sampling_sobol`
# - `ParametricSimulation.sampling_morris`
# - `ParametricSimulation.run_parametric_simulation`
# - `ParametricSimulation.run_sensitivity_analysis`
# - `ParametricSimulation.run_sensitivity_analysis_by_epw`

# %% [markdown]
# ## Step 1 - Import dependencies

# %%
from pathlib import Path

import accim
import pandas as pd
from besos import eppy_funcs as ef
from accim.utils import WorkspaceArtifactCleaner
from accim.parametric_and_optimisation.main import ParametricSimulation

pd.set_option("display.max_columns", 160)

# %% [markdown]
# ## Step 2 - Resolve inputs and initialize simulation context

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
RESULTS_DIRNAME = "nb05_sampling_sensitivity_results"

artifact_cleaner = WorkspaceArtifactCleaner(workspace_root=PROJECT_ROOT)
baseline_files = artifact_cleaner.capture_initial_state()
print("Baseline file count:", len(baseline_files))

building = ef.get_building(str(IDF_FILE))
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

parametric = ParametricSimulation(
	building=building,
	parameters_type="accim custom model",
	epws=EPWS,
	output_freqs=["hourly"],
)

# %% [markdown]
# ## Step 3 - Configure outputs and parameter ranges

# %%
discovery = parametric.discover_available_outputs(
	reduce_sim_time=True,
	prefer="testsimeplus",
)
df_meters_available = discovery["meters"]
selection = parametric.select_outputs(
	meters=["Heating:Electricity", "Cooling:Electricity"],
	match="case_insensitive",
	on_missing="raise",
	suggest=True,
)
df_meters_sel = selection["meters"]

parametric.apply_outputs_preflight(
	df_meters_sel=df_meters_sel,
	df_vars_sel=None,
	clean_mode="all",
	validate_before_apply=False,
	validate_after_apply=True,
	on_missing="raise",
)
parametric.set_outputs_for_simulation(df_output_meter=df_meters_sel)

accis_parameters = {
	"CustAST_m": (0.15, 0.95),
	"CustAST_n": (8, 23),
	"CustAST_ASToffset": (1.0, 6.0),
}
parametric.set_parameters(accis_params_dict=accis_parameters)
parametric.set_problem(minimize_outputs=[True, True])

print("Configured parameters:", list(accis_parameters.keys()))
print("Outputs configured:", parametric.problem.names("outputs"))

# %% [markdown]
# ## Step 4 - Generate Morris and Sobol sampling plans

# %%
parametric.sampling_morris(num_samples=3, num_levels=4)
morris_df = parametric.parameters_values_df.copy()
print("Morris rows:", len(morris_df))

sobol_available = True
try:
	import SALib  # noqa: F401
except ImportError:
	sobol_available = False

if sobol_available:
	parametric.sampling_sobol(num_samples=8)
	sobol_df = parametric.parameters_values_df.copy()
	print("Sobol rows:", len(sobol_df))
else:
	sobol_df = pd.DataFrame()
	print("SALib not available. Sobol plan generation is skipped.")

# %% [markdown]
# ## Step 5 - Execute simulations (using Morris plan by default)

# %%
RUN_PARAMETRIC_SIMULATION = True
plan_df = morris_df

if RUN_PARAMETRIC_SIMULATION:
	outputs = parametric.run_parametric_simulation(
		out_dir=str(PROJECT_ROOT / RESULTS_DIRNAME),
		df=plan_df,
		processes=1,
		keep_input=True,
		keep_dirs=False,
	)
	print("Rows:", len(outputs))
else:
	print("Simulation skipped. Set RUN_PARAMETRIC_SIMULATION = True to execute the run.")

# %% [markdown]
# ## Step 6 - Run sensitivity analysis (global + by EPW)

# %%
if RUN_PARAMETRIC_SIMULATION:
	sa_morris = parametric.run_sensitivity_analysis(method="morris")
	print("Morris SA outputs:", list(sa_morris.keys()))

	sa_morris_by_epw = parametric.run_sensitivity_analysis_by_epw(
		method="morris",
		out_dir=str(PROJECT_ROOT / RESULTS_DIRNAME),
	)
	print("Morris SA by EPW:", list(sa_morris_by_epw.keys()))

	if sobol_available and not sobol_df.empty:
		# Optional second pass for Sobol if a Sobol-compatible run is desired.
		print("Sobol plan is available. Re-run with sobol_df before calling Sobol SA if needed.")
else:
	print("Sensitivity analysis skipped because simulation was not executed.")

# %% [markdown]
# ## Step 7 - Review and clean generated artifacts

# %%
generated_files = artifact_cleaner.print_generated_files(max_items=200)

# %%
artifact_cleaner.delete_generated_files(
	allow_patterns=[f"{RESULTS_DIRNAME}/**"],
	deny_patterns=[],
	dry_run=True,
	remove_empty_dirs=True,
)

# %%
artifact_cleaner.delete_generated_files(
	allow_patterns=[f"{RESULTS_DIRNAME}/**"],
	deny_patterns=[],
	dry_run=False,
	remove_empty_dirs=True,
)

