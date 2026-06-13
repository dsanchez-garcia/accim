# %% [markdown]
# # 04 - Outputs preflight and output control
#
# Goal: discover, validate, and safely apply output objects to the IDF.
#
# ## Methods executed in this notebook
#
# Core ACCIM/BESOS functions used in the runnable flow:
# - `accim.utils.reduce_runtime`
# - `ef.get_building`
# - `ParametricSimulation.scan_output_objects`
# - `ParametricSimulation.autocorrect_output_duplicates`
# - `ParametricSimulation.discover_available_outputs`
# - `ParametricSimulation.select_outputs`
# - `ParametricSimulation.apply_outputs_preflight`
# - `ParametricSimulation.set_outputs_for_simulation`
# - `ParametricSimulation.get_output_meter_df_from_idf`
# - `ParametricSimulation.get_output_var_df_from_idf`
#
# Optional reset helper shown at the end:
# - `ParametricSimulation.clear_outputs`

# %% [markdown]
# ## Step 1 - Import dependencies

# %%
from pathlib import Path

import accim
from besos import eppy_funcs as ef
from accim.parametric_and_optimisation.main import ParametricSimulation

# %% [markdown]
# ## Step 2 - Resolve inputs and initialize simulation object

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

building = ef.get_building(str(IDF_FILE))
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

parametric = ParametricSimulation(
	building=building,
	parameters_type="accim custom model",
	epws=EPWS,
	output_freqs=["hourly"],
)

# %% [markdown]
# ## Step 3 - Scan current output objects and attempt duplicate autocorrection

# %%
scan_before = parametric.scan_output_objects()
print("Current output meters in IDF:", len(scan_before.get("meters", [])))
print("Current output vars in IDF:", len(scan_before.get("variables", [])))

autocorrect_report = parametric.autocorrect_output_duplicates(warn=True)
print("Autocorrect report keys:", list(autocorrect_report.keys()))

# %% [markdown]
# ## Step 4 - Discover available outputs from a short test simulation

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
# ## Step 5 - Select a validated output subset

# %%
selection = parametric.select_outputs(
	meters=["Heating:Electricity", "Cooling:Electricity"],
	variables=["Zone Operative Temperature", "Running Average Outdoor Air Temperature"],
	match="contains",
	on_missing="warn",
	suggest=True,
)
df_meters_sel = selection["meters"]
df_vars_sel = selection["variables"]
report = selection["report"]

print("Selected meters:", len(df_meters_sel))
print("Selected variables:", len(df_vars_sel))
print("Missing:", report.get("missing", {}))

# %% [markdown]
# ## Step 6 - Apply preflight checks and register outputs for simulation

# %%
preflight_report = parametric.apply_outputs_preflight(
	df_meters_sel=df_meters_sel,
	df_vars_sel=df_vars_sel,
	clean_mode="all",
	validate_before_apply=False,
	validate_after_apply=True,
	on_missing="warn",
)

parametric.set_outputs_for_simulation(
	df_output_meter=df_meters_sel,
	df_output_variable=df_vars_sel,
)

print("Preflight verification keys:", list(preflight_report.get("verification", {}).keys()))
print("Simulation output readers configured:", len(parametric.sim_outputs))

# %% [markdown]
# ## Step 7 - Inspect output objects now present in the IDF

# %%
df_meters_in_idf = parametric.get_output_meter_df_from_idf()
df_vars_in_idf = parametric.get_output_var_df_from_idf()

print("Output meters in IDF after apply:", len(df_meters_in_idf))
print("Output variables in IDF after apply:", len(df_vars_in_idf))
print(df_meters_in_idf.head())

# %% [markdown]
# ## Step 8 - Optional reset (uncomment to clear all output objects)

# %%
# parametric.clear_outputs()
# print("All output objects cleared from IDF.")

