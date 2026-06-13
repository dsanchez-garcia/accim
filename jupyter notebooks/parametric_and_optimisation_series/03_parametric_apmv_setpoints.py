# %% [markdown]
# # 03 - Parametric APMV setpoints
#
# Goal: run a complete APMV parametric workflow with `parameters_type='apmv setpoints'`.
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
# - `ParametricSimulation.sampling_full_set`
# - `ParametricSimulation.run_parametric_simulation`
#
# Workspace hygiene helpers used:
# - `WorkspaceArtifactCleaner.capture_initial_state`
# - `WorkspaceArtifactCleaner.print_generated_files`
# - `WorkspaceArtifactCleaner.delete_generated_files`

# %% [markdown]
# ## Step 1 - Import dependencies

# %%
from pathlib import Path

import accim
import pandas as pd
from besos import eppy_funcs as ef
from accim.sim import apmv_setpoints
from accim.utils import WorkspaceArtifactCleaner
from accim.parametric_and_optimisation.main import ParametricSimulation

pd.set_option("display.max_columns", 160)

# %% [markdown]
# ## Step 2 - Define paths and validate files

# %%
PROJECT_ROOT = Path.cwd()
NOTEBOOK_DIR = Path(__file__).resolve().parent


IDF_FILE = PROJECT_ROOT / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_high_performance.idf"
if not IDF_FILE.exists():
	IDF_FILE = NOTEBOOK_DIR / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_high_performance.idf"

epw_seville = PROJECT_ROOT / "Seville.epw"
if not epw_seville.exists():
	epw_seville = NOTEBOOK_DIR / "Seville.epw"

EPWS = [str(epw_seville)]
RESULTS_DIRNAME = "nb03_parametric_apmv_results"

print("IDF exists:", IDF_FILE.exists())
print("EPWs exist:", [Path(epw).exists() for epw in EPWS])

# %% [markdown]
# ## Step 2.1 - Initialize artifact tracking

# %%
artifact_cleaner = WorkspaceArtifactCleaner(workspace_root=PROJECT_ROOT)
baseline_files = artifact_cleaner.capture_initial_state()
print("Baseline file count:", len(baseline_files))

# %% [markdown]
# ## Step 3 - Load IDF and initialize APMV simulation object

# %%
building = ef.get_building(str(IDF_FILE))
accim.utils.reduce_runtime(idf_object=building, timesteps=2)
# Ensure the model contains the HVAC structure expected by aPMV routines.
apmv_setpoints.add_vrf_system(building=building)

parametric = ParametricSimulation(
	building=building,
	parameters_type="apmv setpoints",
	epws=EPWS,
	output_freqs=["hourly"],
)

# %% [markdown]
# ## Step 4 - Discover outputs and configure objective outputs

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

selection = parametric.select_outputs(
	meters=["Heating:Electricity", "Cooling:Electricity"],
	variables=["aPMV"],
	match="contains",
	on_missing="warn",
	suggest=True,
)
df_meters_sel = selection["meters"]
df_vars_sel = selection["variables"]
report = selection["report"]
print("Missing outputs:", report.get("missing", {}))

parametric.apply_outputs_preflight(
	df_meters_sel=df_meters_sel,
	df_vars_sel=df_vars_sel,
	clean_mode="all",
	validate_before_apply=False,
	validate_after_apply=True,
	on_missing="warn",
)
parametric.set_outputs_for_simulation(df_output_meter=df_meters_sel)

# %% [markdown]
# ## Step 5 - Define APMV parameters and generate full-set plan

# %%
apmv_parameters = {
	"Adaptive coefficient": [0.0, 0.9],
	"PMV setpoint": [0.2, 0.8],
}
parametric.set_parameters(accis_params_dict=apmv_parameters)
parametric.set_problem()
parametric.sampling_full_set()

plan_df = parametric.parameters_values_df.copy()
print("Plan rows:", len(plan_df))
print(plan_df.head())

# %% [markdown]
# ## Step 5.1 - Estimate number of simulation cases

# %%
epw_multiplier = 1 if "epw" in plan_df.columns else len(EPWS)
estimated_simulations = len(plan_df) * epw_multiplier

print("EPW multiplier:", epw_multiplier)
print("Estimated simulation cases:", estimated_simulations)

# %% [markdown]
# ## Step 6 - Execute APMV parametric simulation

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

