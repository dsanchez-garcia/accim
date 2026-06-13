# %% [markdown]
# # 01 - Parametric ACCIM custom model
#
# Goal: run a complete parametric workflow for `parameters_type='accim custom model'`
# with richer output selection and multiple sampling strategies.

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
# - `ParametricSimulation.sampling_lhs`
# - `ParametricSimulation.sampling_full_factorial`
# - `ParametricSimulation.run_parametric_simulation`
#
# Pattern also included (commented template in Step 5.4):
# - `ParametricSimulation.sampling_custom`
#
# Workspace hygiene helpers used:
# - `WorkspaceArtifactCleaner.capture_initial_state`
# - `WorkspaceArtifactCleaner.print_generated_files`
# - `WorkspaceArtifactCleaner.delete_generated_files`

# %% [markdown]
# ## Workflow map
#
# 1. Import tools and configure display.
# 2. Define project paths and validate inputs.
# 3. Capture a baseline file snapshot for safe cleanup.
# 4. Load IDF, apply tutorial runtime settings, and initialize `ParametricSimulation`.
# 5. Discover outputs, select objective/auxiliary outputs, and apply preflight checks.
# 6. Define parameter ranges and generate sample plans.
# 7. Estimate simulation volume before running.
# 8. Execute simulations and inspect outputs.
# 9. Preview generated artifacts and optionally clean them.

# %% [markdown]
# ## Step 1 - Import dependencies
#
# We import ACCIM/BESOS components for model loading and parametric simulation, plus
# `WorkspaceArtifactCleaner` to keep the workspace clean and safe.

# %%
from pathlib import Path

import accim
import pandas as pd
from besos import eppy_funcs as ef
from accim.utils import WorkspaceArtifactCleaner
from accim.parametric_and_optimisation.main import ParametricSimulation

pd.set_option("display.max_columns", 160)

# %% [markdown]
# ## Step 2 - Define paths and validate required files
#
# We set two IDFs (high/low envelope performance) and two EPWs so this notebook
# demonstrates multi-model and multi-weather campaigns.

# %%
PROJECT_ROOT = Path.cwd()
NOTEBOOK_DIR = Path(__file__).resolve().parent


idf_high = PROJECT_ROOT / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_high_performance.idf"
if not idf_high.exists():
	idf_high = NOTEBOOK_DIR / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_high_performance.idf"

idf_low = PROJECT_ROOT / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_low_performance.idf"
if not idf_low.exists():
	idf_low = NOTEBOOK_DIR / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_low_performance.idf"

epw_seville = PROJECT_ROOT / "Seville.epw"
if not epw_seville.exists():
	epw_seville = NOTEBOOK_DIR / "Seville.epw"

epw_sydney = PROJECT_ROOT / "Sydney.epw"
if not epw_sydney.exists():
	epw_sydney = NOTEBOOK_DIR / "Sydney.epw"

IDF_FILES = [idf_high, idf_low]
EPWS = [str(epw_seville), str(epw_sydney)]
RESULTS_DIRNAME = "nb01_parametric_custom_results"

print("IDF files found:", [idf.exists() for idf in IDF_FILES])
print("EPW files found:", [Path(epw).exists() for epw in EPWS])

# %% [markdown]
# ## Step 2.1 - Initialize artifact tracking for safe cleanup
#
# We capture the initial file state before generating outputs. Later, we will diff against
# this baseline and preview any cleanup plan before deleting anything.

# %%
artifact_cleaner = WorkspaceArtifactCleaner(workspace_root=PROJECT_ROOT)
baseline_files = artifact_cleaner.capture_initial_state()
print("Baseline file count:", len(baseline_files))

# %% [markdown]
# ## Step 3.1 - Load the base IDF model
#
# We load the model once and keep the object as the source for all downstream workflow steps.

# %%
building = ef.get_building(str(IDF_FILES[0]))

# %% [markdown]
# ## Step 3.2 - Apply quick-runtime settings (tutorial mode)
#
# We use `reduce_runtime(...)` only to keep this tutorial fast.
#
# Important:
# - This helper simplifies the simulation setup (run period and computational settings).
# - It is appropriate for demonstration and workflow checks.
# - It should not be used in full annual studies or detailed hourly thermal analysis notebooks.

# %%
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

# %% [markdown]
# ## Step 3.3 - Initialize `ParametricSimulation`
#
# This object stores outputs, parameters, sampled plans, and execution results.

# %%
parametric = ParametricSimulation(
	building=building,
	parameters_type="accim custom model",
	epws=EPWS,
	output_freqs=["hourly"],
)

# %% [markdown]
# ## Step 4.1 - Discover available outputs
#
# We inspect model-available outputs first, so output selection is explicit and robust.

# %%
discovery = parametric.discover_available_outputs(
	reduce_sim_time=True,
	prefer="testsimeplus",
)
df_meters_available = discovery["meters"]
df_vars_available = discovery["variables"]
outputs_meta = discovery["meta"]

print("Discovery source:", outputs_meta.get("source"))
print("Meters available:", len(df_meters_available))
print("Variables available:", len(df_vars_available))

# %% [markdown]
# ## Step 4.2 - Select objective and auxiliary outputs
#
# We select electricity meters as objectives and a small set of thermal variables for context.

# %%
objective_meters = ["Heating:Electricity", "Cooling:Electricity"]
auxiliary_variables = [
	"Zone Operative Temperature",
	"Running Average Outdoor Air Temperature",
]

meters_selection = parametric.select_outputs(
	meters=objective_meters,
	match="case_insensitive",
	on_missing="raise",
	suggest=True,
)
df_meters_sel = meters_selection["meters"]

vars_selection = parametric.select_outputs(
	variables=auxiliary_variables,
	match="contains",
	on_missing="warn",
	suggest=True,
)
df_vars_sel = vars_selection["variables"]
vars_report = vars_selection["report"]

if vars_report["missing"]["variables"]:
	print("Missing auxiliary variables:", vars_report["missing"]["variables"])

# %% [markdown]
# ## Step 4.3 - Apply output preflight and register final output set
#
# Preflight aligns selected output tables with the real IDF output objects.

# %%
parametric.apply_outputs_preflight(
	df_meters_sel=df_meters_sel,
	df_vars_sel=df_vars_sel,
	clean_mode="all",
	validate_before_apply=False,
	validate_after_apply=True,
	on_missing="raise",
)
parametric.set_outputs_for_simulation(df_output_meter=df_meters_sel, df_output_variable=df_vars_sel)

# %% [markdown]
# ## Step 5.1 - Define custom-model parameter ranges and build the problem
#
# These ranges define the exploration space for the ACCIM custom model controls.

# %%
accis_parameters = {
	"CustAST_m": (0.15, 0.95),
	"CustAST_n": (8, 23),
	"CustAST_ASToffset": (1.0, 6.0),
	"CustAST_ASTall": (8, 16),
	"CustAST_ASTaul": (28, 38),
}

parametric.set_parameters(accis_params_dict=accis_parameters)
parametric.set_problem()

# %% [markdown]
# ## Step 5.2 - Generate LHS sample plan
#
# LHS is used as default run plan because it provides a compact space-filling sample.

# %%
parametric.sampling_lhs(num_samples=6)
lhs_df = parametric.parameters_values_df.copy()
print("LHS rows:", len(lhs_df))
print(lhs_df.head())

# %% [markdown]
# ## Step 5.3 - Generate full-factorial sample plan
#
# Full factorial is included for comparison. It can grow quickly in larger problems.

# %%
parametric.sampling_full_factorial(level=2)
ff_df = parametric.parameters_values_df.copy()
print("Full factorial rows:", len(ff_df))
print(ff_df.head())

# %% [markdown]
# ## Step 5.4 - (Optional) custom simulation plan
#
# Use this pattern when you want explicit combinations (including explicit EPW mapping).

# %%
# custom_plan = pd.DataFrame(
#     [
#         {"CustAST_m": 0.30, "CustAST_n": 12, "CustAST_ASToffset": 2.5, "CustAST_ASTall": 10, "CustAST_ASTaul": 32, "epw": EPWS[0]},
#         {"CustAST_m": 0.60, "CustAST_n": 18, "CustAST_ASToffset": 4.0, "CustAST_ASTall": 12, "CustAST_ASTaul": 35, "epw": EPWS[1]},
#     ]
# )
# parametric.sampling_custom(custom_plan)
# plan_df = parametric.parameters_values_df.copy()

# Use LHS by default for the optional run.
plan_df = lhs_df.copy()
plan_df["idf"] = [str(IDF_FILES[i % len(IDF_FILES)]) for i in range(len(plan_df))]

# %% [markdown]
# ## Step 5.5 - Estimate the number of simulations to execute
#
# We estimate the final case count from the plan shape plus weather/model expansion rules.
#
# Estimation rule used here:
# - If `epw` is already a column in `plan_df`, each row already maps to one EPW.
# - If `epw` is missing, rows are expanded across the `EPWS` list.
# - If `idf` is already a column in `plan_df`, each row already maps to one IDF.
# - If `idf` is missing, rows are expanded across the `IDF_FILES` list.

# %%
epw_multiplier = 1 if "epw" in plan_df.columns else len(EPWS)
idf_multiplier = 1 if "idf" in plan_df.columns else len(IDF_FILES)
estimated_simulations = len(plan_df) * epw_multiplier * idf_multiplier

print("Plan rows:", len(plan_df))
print("EPW multiplier:", epw_multiplier)
print("IDF multiplier:", idf_multiplier)
print("Estimated simulation cases:", estimated_simulations)

# %% [markdown]
# ## Step 6 - Execute the parametric simulation
#
# This notebook is designed to execute a full parametric run.
#
# A small execution flag is kept only as a safety switch for quick troubleshooting.

# %%
RUN_PARAMETRIC_SIMULATION = True

if RUN_PARAMETRIC_SIMULATION:
	outputs = parametric.run_parametric_simulation(
		out_dir=str(PROJECT_ROOT / RESULTS_DIRNAME),
		df=plan_df,
		processes=1,
		keep_input=True,
		keep_dirs=False,
	)
	print("Rows:", len(outputs))
	print(outputs.head())
else:
	print("Simulation skipped. Set RUN_PARAMETRIC_SIMULATION = True to execute the run.")

# %% [markdown]
# ## Step 7 - Review and optionally clean generated artifacts
#
# We now inspect what files appeared after the baseline snapshot and optionally remove them.
#
# Safety approach used here:
# - Print generated files first.
# - Restrict deletion to a dedicated result folder.
# - Force-clean every generated file inside `nb01_parametric_custom_results/**` (via `RESULTS_DIRNAME`).
# - Use `dry_run=True` by default to preview the deletion plan.
# - When you are fully confident with the printed plan, set `dry_run=False`.

# %%
generated_files = artifact_cleaner.print_generated_files(max_items=200)

# %%
# Force-remove every generated artifact inside the dedicated result folder,
# including generated IDF files.
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

