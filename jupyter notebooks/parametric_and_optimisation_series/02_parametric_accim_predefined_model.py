# %% [markdown]
# # 02 - Parametric ACCIM predefined model
#
# Goal: run option-based campaigns with `AccimPredefModelsParamSim`.
#
# ## Methods executed in this notebook
#
# Core ACCIM/BESOS functions used in the runnable flow:
# - `accim.utils.reduce_runtime`
# - `ef.get_building`
# - `AccimPredefModelsParamSim.set_outputs_for_simulation`
# - `AccimPredefModelsParamSim.get_available_parameters`
# - `AccimPredefModelsParamSim.set_parameters`
# - `AccimPredefModelsParamSim.sampling_full_set`
# - `AccimPredefModelsParamSim.set_problem`
# - `AccimPredefModelsParamSim.run_parametric_simulation`
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
from accim.utils import WorkspaceArtifactCleaner
from accim.parametric_and_optimisation.main import AccimPredefModelsParamSim

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

epw_sydney = PROJECT_ROOT / "Sydney.epw"
if not epw_sydney.exists():
	epw_sydney = NOTEBOOK_DIR / "Sydney.epw"

EPWS = [
	str(epw_seville),
	str(epw_sydney),
]
RESULTS_DIRNAME = "nb02_parametric_predefined_results"

print("IDF exists:", IDF_FILE.exists())
print("EPWs exist:", [Path(epw).exists() for epw in EPWS])

# %% [markdown]
# ## Step 2.1 - Initialize artifact tracking

# %%
artifact_cleaner = WorkspaceArtifactCleaner(workspace_root=PROJECT_ROOT)
baseline_files = artifact_cleaner.capture_initial_state()
print("Baseline file count:", len(baseline_files))

# %% [markdown]
# ## Step 3 - Load IDF and initialize predefined-model simulation

# %%
building = ef.get_building(str(IDF_FILE))
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

parametric = AccimPredefModelsParamSim(
	building=building,
	epws=EPWS,
	output_freqs=["hourly"],
)

# %% [markdown]
# ## Step 4 - Define objective meters explicitly

# %%
df_meters_sel = pd.DataFrame(
	{
		"key_name": ["Heating:Electricity", "Cooling:Electricity"],
		"frequency": ["hourly", "hourly"],
	}
)
parametric.set_outputs_for_simulation(df_output_meter=df_meters_sel)
print("Objective meters configured:", list(df_meters_sel["key_name"]))

# %% [markdown]
# ## Step 5 - Define predefined-model options and sample full set

# %%
available_parameters = parametric.get_available_parameters()
print("Available predefined parameters:", available_parameters)

predef_parameters = {
	"ComfStand": [1],
	"HVACmode": [2],
	"CAT": [1],
	"CATcoolOffset": [0],
	"CATheatOffset": [0],
}
parametric.set_parameters(accis_params_dict=predef_parameters)
parametric.sampling_full_set()
parametric.set_problem()

plan_df = parametric.parameters_values_df.copy()
print("Plan rows:", len(plan_df))
print(plan_df.head())

# %% [markdown]
# ## Step 5.1 - Estimate number of simulation cases

# %%
epw_multiplier = 1 if "epw" in plan_df.columns else len(EPWS)
idf_multiplier = 1 if "idf" in plan_df.columns else 1
estimated_simulations = len(plan_df) * epw_multiplier * idf_multiplier

print("EPW multiplier:", epw_multiplier)
print("IDF multiplier:", idf_multiplier)
print("Estimated simulation cases:", estimated_simulations)

# %% [markdown]
# ## Step 6 - Execute predefined-model parametric simulation

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

