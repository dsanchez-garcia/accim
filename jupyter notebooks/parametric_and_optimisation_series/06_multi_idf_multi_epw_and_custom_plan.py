# %% [markdown]
# # 06 - Multi-IDF, multi-EPW, and custom plans
#
# Goal: run custom campaign plans with explicit `idf`/`epw` combinations and
# demonstrate compatibility with standard BESOS extensions.
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
# - `ParametricSimulation.sampling_custom`
# - `ParametricSimulation.run_parametric_simulation`
#
# Compatibility points demonstrated:
# - Non-ACCIM BESOS parameter via `additional_params` (`insulation_thickness_m`)
# - Callable reducer for output variables via `return_time_series`
#
# Workspace hygiene helpers used:
# - `WorkspaceArtifactCleaner.capture_initial_state`
# - `WorkspaceArtifactCleaner.print_generated_files`
# - `WorkspaceArtifactCleaner.delete_generated_files`

# %% [markdown]
# ## Workflow map
#
# 1. Import dependencies and configure display.
# 2. Define and validate multi-IDF/multi-EPW inputs.
# 3. Capture baseline files for safe cleanup.
# 4. Load a base IDF, reduce runtime, and initialize `ParametricSimulation`.
# 5. Select outputs and attach a callable reducer for a time-series output.
# 6. Define ACCIM parameters plus one BESOS non-ACCIM parameter.
# 7. Build an explicit custom plan with per-row `idf` and `epw`.
# 8. Estimate and execute the cross-scenario simulation campaign.
# 9. Review and optionally clean generated artifacts.

# %% [markdown]
# ## Step 1 - Import dependencies

# %%
from pathlib import Path

import accim
import pandas as pd
from besos import eppy_funcs as ef
from besos.parameters import FieldSelector, Parameter, RangeParameter
from accim.utils import WorkspaceArtifactCleaner
from accim.parametric_and_optimisation.main import ParametricSimulation
from tools.custom_output_funcs import return_time_series

pd.set_option("display.max_columns", 200)

# %% [markdown]
# ## Step 2 - Define paths and validate required files
#
# We use two envelope variants and two climates. The custom plan will map each row
# to a specific `idf`/`epw` combination.

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
RESULTS_DIRNAME = "nb06_multi_idf_multi_epw_custom_results"

print("IDF files found:", [idf.exists() for idf in IDF_FILES])
print("EPW files found:", [Path(epw).exists() for epw in EPWS])

# %% [markdown]
# ## Step 2.1 - Initialize artifact tracking for safe cleanup

# %%
artifact_cleaner = WorkspaceArtifactCleaner(workspace_root=PROJECT_ROOT)
baseline_files = artifact_cleaner.capture_initial_state()
print("Baseline file count:", len(baseline_files))

# %% [markdown]
# ## Step 3.1 - Load base IDF

# %%
building = ef.get_building(str(IDF_FILES[0]))

# %% [markdown]
# ## Step 3.2 - Apply quick-runtime settings (tutorial mode)
#
# This keeps the demonstration quick. Do not use these reduced settings for full-year
# detailed analyses.

# %%
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

# %% [markdown]
# ## Step 3.3 - Initialize `ParametricSimulation`

# %%
parametric = ParametricSimulation(
	building=building,
	parameters_type="accim custom model",
	epws=EPWS,
	output_freqs=["hourly"],
)

# %% [markdown]
# ## Step 4.1 - Discover available outputs

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
# ## Step 4.2 - Select outputs and attach callable reducer
#
# We optimize one meter objective and request one time-series variable reduced with
# `return_time_series`.

# %%
objective_meters = ["Heating:Electricity"]
selection = parametric.select_outputs(
	meters=objective_meters,
	match="case_insensitive",
	on_missing="raise",
	suggest=True,
)
df_meters_sel = selection["meters"]

mask_var = df_vars_available["variable_name"].str.contains(
	"Running Average Outdoor Air Temperature",
	case=False,
	na=False,
)
if mask_var.any():
	df_vars_sel = df_vars_available[mask_var].copy().head(1)
else:
	df_vars_sel = df_vars_available.head(1).copy()

df_vars_sel["name"] = df_vars_sel["variable_name"] + "_time series"
df_vars_sel["func"] = return_time_series

parametric.apply_outputs_preflight(
	df_meters_sel=df_meters_sel,
	df_vars_sel=df_vars_sel,
	clean_mode="all",
	validate_before_apply=False,
	validate_after_apply=True,
	on_missing="raise",
)
parametric.set_outputs_for_simulation(
	df_output_meter=df_meters_sel,
	df_output_variable=df_vars_sel,
)

print("Selected meters:", list(df_meters_sel["key_name"]))
print("Selected variable output names:", list(df_vars_sel["name"]))

# %% [markdown]
# ## Step 5 - Define ACCIM parameters + one BESOS non-ACCIM parameter
#
# This demonstrates interoperability: ACCIM parameters are combined with a standard
# BESOS `Parameter` that edits `Material` thickness.

# %%
accis_parameters = {
	"CustAST_m": (0.2, 0.8),
	"CustAST_n": (10, 20),
	"CustAST_ASToffset": (2.0, 4.0),
	"CustAST_ASTall": (9, 14),
	"CustAST_ASTaul": (30, 36),
}

insulation_thickness_param = Parameter(
	name="insulation_thickness_m",
	selector=FieldSelector(
		class_name="Material",
		object_name="Residential Roof Construction Material",
		field_name="Thickness",
	),
	value_descriptors=RangeParameter(min_val=0.02, max_val=0.20, name="insulation_thickness_m"),
)

parametric.set_parameters(
	accis_params_dict=accis_parameters,
	additional_params=[insulation_thickness_param],
)
parametric.set_problem()

print("Problem inputs:", parametric.problem.names("inputs"))
print("Problem outputs:", parametric.problem.names("outputs"))

# %% [markdown]
# ## Step 6 - Build explicit custom plan (row-by-row IDF/EPW mapping)

# %%
custom_plan = pd.DataFrame(
	[
		{
			"CustAST_m": 0.25,
			"CustAST_n": 12,
			"CustAST_ASToffset": 2.5,
			"CustAST_ASTall": 10,
			"CustAST_ASTaul": 32,
			"insulation_thickness_m": 0.04,
			"idf": str(IDF_FILES[0]),
			"epw": EPWS[0],
		},
		{
			"CustAST_m": 0.55,
			"CustAST_n": 17,
			"CustAST_ASToffset": 3.2,
			"CustAST_ASTall": 12,
			"CustAST_ASTaul": 34,
			"insulation_thickness_m": 0.10,
			"idf": str(IDF_FILES[0]),
			"epw": EPWS[1],
		},
		{
			"CustAST_m": 0.35,
			"CustAST_n": 14,
			"CustAST_ASToffset": 2.8,
			"CustAST_ASTall": 11,
			"CustAST_ASTaul": 33,
			"insulation_thickness_m": 0.08,
			"idf": str(IDF_FILES[1]),
			"epw": EPWS[0],
		},
		{
			"CustAST_m": 0.70,
			"CustAST_n": 19,
			"CustAST_ASToffset": 3.8,
			"CustAST_ASTall": 13,
			"CustAST_ASTaul": 35,
			"insulation_thickness_m": 0.16,
			"idf": str(IDF_FILES[1]),
			"epw": EPWS[1],
		},
	]
)

parametric.sampling_custom(custom_plan)
plan_df = parametric.parameters_values_df.copy()

print("Custom plan rows:", len(plan_df))
print(plan_df[["idf", "epw", "insulation_thickness_m"]].head())

# %% [markdown]
# ## Step 6.1 - Estimate final simulation count

# %%
epw_multiplier = 1 if "epw" in plan_df.columns else len(EPWS)
idf_multiplier = 1 if "idf" in plan_df.columns else len(IDF_FILES)
estimated_simulations = len(plan_df) * epw_multiplier * idf_multiplier

print("Plan rows:", len(plan_df))
print("EPW multiplier:", epw_multiplier)
print("IDF multiplier:", idf_multiplier)
print("Estimated simulation cases:", estimated_simulations)

# %% [markdown]
# ## Step 7 - Execute the custom plan simulation campaign
#
# We keep a small toggle for troubleshooting; the default is execution enabled.

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
# ## Step 7.1 - Check callable-derived output columns

# %%
if RUN_PARAMETRIC_SIMULATION:
	callable_cols = [c for c in outputs.columns if c.endswith("_time series")]
	print("Callable-derived columns:", callable_cols)
	if callable_cols:
		sample_col = callable_cols[0]
		sample_val = outputs[sample_col].iloc[0]
		print("Sample column:", sample_col)
		print("Sample value type:", type(sample_val))
else:
	print("No outputs to inspect because simulation was skipped.")

# %% [markdown]
# ## Step 8 - Review and optionally clean generated artifacts

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
