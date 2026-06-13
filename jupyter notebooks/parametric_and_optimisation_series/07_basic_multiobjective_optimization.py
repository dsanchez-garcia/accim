# %% [markdown]
# # 07 - Basic multi-objective optimization
#
# Goal: run a compact multi-objective optimization and inspect early Pareto-front results.

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
# - `OptimisationSimulation.estimate_optimisation_sims`
# - `OptimisationSimulation.run_optimisation`
#
# Workspace hygiene helpers used:
# - `WorkspaceArtifactCleaner.capture_initial_state`
# - `WorkspaceArtifactCleaner.print_generated_files`
# - `WorkspaceArtifactCleaner.delete_generated_files`

# %% [markdown]
# ## Workflow map
#
# 1. Import dependencies and configure display.
# 2. Define paths and validate IDF/EPW files.
# 3. Capture baseline files for safe cleanup.
# 4. Load IDF, apply tutorial runtime settings, and initialize `OptimisationSimulation`.
# 5. Discover/select outputs and register them for optimization.
# 6. Define parameter bounds and objective direction.
# 7. Estimate run size and optionally execute NSGA-II.
# 8. Preview generated artifacts and optionally clean them.

# %% [markdown]
# ## Step 1 - Import dependencies
#
# We import optimization workflow components and a workspace cleaner for safe artifact handling.

# %%
from pathlib import Path

import accim
import pandas as pd
from besos import eppy_funcs as ef
from accim.utils import WorkspaceArtifactCleaner
from accim.parametric_and_optimisation.main import OptimisationSimulation

pd.set_option("display.max_columns", 160)

# %% [markdown]
# ## Step 2 - Define paths and validate input files
#
# We declare both envelope-performance IDFs plus two EPWs.
# This notebook initializes from the high-performance IDF as a baseline case.

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
RESULTS_DIRNAME = "nb07_basic_optimization_results"

print("IDF files found:", [idf.exists() for idf in IDF_FILES])
print("EPW files found:", [Path(epw).exists() for epw in EPWS])

# %% [markdown]
# ## Step 2.1 - Initialize artifact tracking for safe cleanup
#
# We store the initial workspace file list so cleanup can target only newly generated files.

# %%
artifact_cleaner = WorkspaceArtifactCleaner(workspace_root=PROJECT_ROOT)
baseline_files = artifact_cleaner.capture_initial_state()
print("Baseline file count:", len(baseline_files))

# %% [markdown]
# ## Step 3.1 - Load the base IDF model
#
# We load the model once; downstream optimization setup reuses this object.

# %%
building = ef.get_building(str(IDF_FILES[0]))

# %% [markdown]
# ## Step 3.2 - Apply quick-runtime settings (tutorial mode)
#
# This quickstart optimization intentionally uses reduced runtime settings for fast iteration.
#
# Important:
# - `reduce_runtime(...)` simplifies simulation behavior and timing configuration.
# - It is appropriate for notebook demonstrations and debugging.
# - It should not be used in full annual analyses or high-fidelity comfort studies.

# %%
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

# %% [markdown]
# ## Step 3.3 - Initialize `OptimisationSimulation`
#
# This object manages output objectives, parameter definitions, algorithm settings, and results.

# %%
optim = OptimisationSimulation(
	building=building,
	parameters_type="accim custom model",
	epws=EPWS,
	output_freqs=["hourly"],
)

# %% [markdown]
# ## Step 4.1 - Discover available outputs
#
# We inspect available output candidates before selecting optimization objectives.

# %%
discovery_ok = True
try:
	discovery = optim.discover_available_outputs(
		reduce_sim_time=True,
		prefer="testsimeplus",
	)
	df_meters_available = discovery["meters"]
	df_vars_available = discovery["variables"]
	outputs_meta = discovery["meta"]
	print("Discovery source:", outputs_meta.get("source"))
	print("Meters available:", len(df_meters_available))
	print("Variables available:", len(df_vars_available))
except Exception as exc:
	discovery_ok = False
	print("Output discovery failed; continuing with explicit meters.")
	print(f"Discovery error: {exc}")

# %% [markdown]
# ## Step 4.2 - Select objective outputs and register them
#
# We optimize for heating and cooling electricity, then synchronize output objects in the IDF.

# %%
objective_meters = ["Heating:Electricity", "Cooling:Electricity"]
if discovery_ok:
	selection = optim.select_outputs(
		meters=objective_meters,
		match="case_insensitive",
		on_missing="raise",
		suggest=True,
	)
	df_meters_sel = selection["meters"]
else:
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

# %% [markdown]
# ## Step 5 - Define parameters and objective direction
#
# We set custom-model parameter bounds and define a two-objective minimization problem.

# %%
accis_parameters = {
	"CustAST_m": (0.15, 0.95),
	"CustAST_n": (8, 23),
	"CustAST_ASToffset": (1.0, 6.0),
	"CustAST_ASTall": (8, 16),
	"CustAST_ASTaul": (28, 38),
}

optim.set_parameters(accis_params_dict=accis_parameters)
optim.set_problem(minimize_outputs=[True, True])

# %% [markdown]
# ## Step 6.1 - Estimate optimization campaign size
#
# We estimate simulation demand to validate that tutorial settings stay lightweight.

# %%
EVALUATIONS = 6
POPULATION_SIZE = 3

estimated = optim.estimate_optimisation_sims(
	evaluations=EVALUATIONS,
	population_size=POPULATION_SIZE,
	epws=EPWS,
)
print("Estimated simulations:", estimated)

# %% [markdown]
# ## Step 6.2 - Optionally run NSGA-II optimization
#
# We keep execution behind a toggle so setup can be reviewed before launching simulations.

# %%
RUN_OPTIMIZATION = True

if RUN_OPTIMIZATION:
	outputs_optim = optim.run_optimisation(
		epws=EPWS,
		out_dir=str(PROJECT_ROOT / RESULTS_DIRNAME),
		evaluations=EVALUATIONS,
		population_size=POPULATION_SIZE,
		algorithm="NSGAII",
		processes=1,
		keep_df="all",
		keep_sim_files="non-dominated",
		keep_sim_files_batch_size=POPULATION_SIZE,
	)
	print("Rows:", len(outputs_optim))
	if "pareto-optimal" in outputs_optim.columns:
		print(outputs_optim["pareto-optimal"].value_counts(dropna=False))
	print(outputs_optim.head())
else:
	print("Optimization skipped. Set RUN_OPTIMIZATION = True to execute the run.")

# %% [markdown]
# ## Step 7 - Review and optionally clean generated artifacts
#
# We now inspect what files appeared after the baseline snapshot and optionally remove them.
#
# Safety approach used here:
# - Print generated files first.
# - Restrict deletion to a dedicated result folder.
# - Force-clean every generated file inside `nb07_basic_optimization_results/**` (via `RESULTS_DIRNAME`).
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

