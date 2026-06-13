# %% [markdown]
# # 00 - Quickstart: environment and first run
#
# Goal: execute a minimal parametric simulation with `ParametricSimulation`.
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
# - `ParametricSimulation.sampling_lhs`
# - `ParametricSimulation.run_parametric_simulation`
#
# Workspace hygiene helpers used:
# - `WorkspaceArtifactCleaner.capture_initial_state`
# - `WorkspaceArtifactCleaner.print_generated_files`
# - `WorkspaceArtifactCleaner.delete_generated_files`
#
# This notebook focuses on a practical, low-friction setup designed to give you a
# complete end-to-end picture before scaling to larger studies:
# - Load one IDF and one EPW.
# - Select a couple of outputs.
# - Define custom-model parameter ranges.
# - Generate a small LHS sample.
# - Optionally run the simulation.
#
# By the end, you should understand not only which methods to call, but also why the
# sequence matters for building reliable parametric or optimization workflows.

# %% [markdown]
# ## Workflow map
#
# 1. Validate paths and load one model (`IDF`) plus one weather file (`EPW`).
# 2. Create a `ParametricSimulation` object with core context arguments.
# 3. Discover output candidates, select objective outputs, and apply preflight cleanup.
# 4. Define parameter bounds and generate a small sample (`LHS`).
# 5. Optionally execute the run and inspect the resulting DataFrame.
#
# Why this order is important:
# - Output selection should happen before problem definition, so objectives are explicit.
# - Problem definition should happen before sampling, so the sample matches parameter bounds.
# - Sampling should happen before run, so execution is reproducible and inspectable.
#
# The notebook keeps runtime low by default and uses an execution toggle, so you can
# validate setup first without launching simulations.

# %% [markdown]
# ## Step 1 - Import dependencies
#
# We import ACCIM/BESOS helpers and set a display option so result tables are easier to inspect.
#
# Why this step exists:
# - `Path` keeps file handling robust across environments.
# - `accim` and `ParametricSimulation` provide the parametric workflow APIs.
# - `besos.eppy_funcs` is used to load the IDF object required by ACCIM.
# - `pandas` display settings improve readability when reviewing sampled plans/results.

# %%
from pathlib import Path

import accim
import pandas as pd
from besos import eppy_funcs as ef
from accim.utils import WorkspaceArtifactCleaner
from accim.parametric_and_optimisation.main import ParametricSimulation

pd.set_option("display.max_columns", 120)

# %% [markdown]
# ## Step 2 - Define paths and validate inputs
#
# We resolve project-relative paths for the `IDF` and `EPW` files and print existence checks.
#
# Why this step exists:
# - Path validation fails fast before object creation and simulation setup.
# - It makes notebooks portable because paths are derived from `Path.cwd()`.
# - In batch studies, this same pattern avoids spending time debugging missing files later.

# %%
PROJECT_ROOT = Path.cwd()
NOTEBOOK_DIR = Path(__file__).resolve().parent


IDF_FILE = PROJECT_ROOT / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_high_performance.idf"
if not IDF_FILE.exists():
	IDF_FILE = NOTEBOOK_DIR / "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520_high_performance.idf"

EPW_FILE = PROJECT_ROOT / "Seville.epw"
if not EPW_FILE.exists():
	EPW_FILE = NOTEBOOK_DIR / "Seville.epw"

RESULTS_DIRNAME = "nb00_quickstart_results"

print("Project root:", PROJECT_ROOT)
print("IDF exists:", IDF_FILE.exists())
print("EPW exists:", EPW_FILE.exists())
print("Note: quickstart uses the high-performance envelope IDF only.")

# %% [markdown]
# ## Step 2.1 - Initialize artifact tracking for safe cleanup
#
# We create a `WorkspaceArtifactCleaner` and capture the initial file snapshot **before**
# running any operation that may generate outputs.
#
# Why this step exists:
# - It gives us a reliable baseline to detect only files created during this notebook run.
# - It enables a review-first cleanup flow (print list first, delete later).
# - It reduces the risk of deleting valuable files that existed before execution.

# %%
artifact_cleaner = WorkspaceArtifactCleaner(workspace_root=PROJECT_ROOT)
baseline_files = artifact_cleaner.capture_initial_state()
print("Baseline file count:", len(baseline_files))

# %% [markdown]
# ## Core setup arguments
#
# `ParametricSimulation(...)` arguments used here:
# - `building`: loaded IDF object to be modified and simulated.
# - `parameters_type="accim custom model"`: enables continuous custom-ACCIM parameters.
# - `epws=[...]`: default weather list used by downstream run calls.
# - `output_freqs=["hourly"]`: request hourly reporting frequency for selected outputs.
#
# Utilities used before simulation object creation:
# - `reduce_runtime(..., timesteps=2)`: tutorial-only speed-up utility.
#
# Why these choices are used here:
# - They keep the example deterministic and quick while still representing a real workflow.
# - They establish clean defaults that can later be extended to multi-EPW and optimization runs.
#
# Important scope note for `reduce_runtime(...)`:
# - It intentionally simplifies the simulation (e.g., shorter run period, simplified shadow
#   calculations, fewer timesteps), so it is useful for teaching and fast checks.
# - It should not be used in full studies where you need annual behavior fidelity.
# - In future notebooks focused on hourly operative-temperature analysis, we will not use it.

# %% [markdown]
# ## Step 3.1 - Load the base IDF model
#
# We load the IDF into a BESOS/Eppy building object.
#
# Why this step exists:
# - Everything downstream (output selection, parameter setup, simulation) depends on this object.
# - Keeping model loading isolated helps debugging path/model issues early.

# %%
building = ef.get_building(str(IDF_FILE))

# %% [markdown]
# ## Step 3.2 - Apply quick-runtime settings (tutorial mode)
#
# For this quickstart, we explicitly reduce simulation cost so the notebook stays responsive.
#
# What this function does in practice:
# - Restricts the simulation period (by default, this helper configures a short run window).
# - Simplifies selected simulation settings (such as shadow-calculation behavior).
# - Reduces computational burden through timestep and related simplifications.
#
# Why we do it here:
# - This notebook is for workflow learning, not for final calibrated annual results.
#
# When **not** to do it:
# - Full-year studies.
# - Any notebook where hourly operative temperature behavior is the analysis target.

# %%

# Keep quickstart fast. Increase timesteps for production studies.
accim.utils.reduce_runtime(idf_object=building, timesteps=2)

# %% [markdown]
# ## Step 3.3 - Initialize `ParametricSimulation`
#
# We now create the simulation manager object that will hold:
# - selected outputs,
# - parameter definitions,
# - sampled combinations,
# - and execution results.
#
# This object is the backbone of the rest of the notebook workflow.

# %%

parametric = ParametricSimulation(
	building=building,
	parameters_type="accim custom model",
	epws=[str(EPW_FILE)],
	output_freqs=["hourly"],
)

# %% [markdown]
# ## Step 4.1 - Discover which outputs the model can provide
#
# Before selecting objective metrics, we inspect the model's available outputs.
#
# Why this matters:
# - Output names vary across models and templates.
# - Discovering first helps avoid silent mismatches and broken objective definitions later.
# - In larger studies, this step gives you a reproducible inventory of what can be requested.
#
# In practice, this is your "schema discovery" stage for metrics.

# %%
discovery = parametric.discover_available_outputs(
	reduce_sim_time=True,  # lightweight discovery helper run
	prefer="testsimeplus",  # fallback policy when multiple discovery backends exist
)
df_meters_available = discovery["meters"]
df_vars_available = discovery["variables"]
outputs_meta = discovery["meta"]

print("Discovery source:", outputs_meta.get("source"))
print("Available meters:", len(df_meters_available))
print("Available variables:", len(df_vars_available))

# %% [markdown]
# ## Step 4.2 - Select objective outputs for this quickstart
#
# We now define which outputs represent our goals.
#
# For this tutorial we use two energy meters (`Heating:Electricity` and `Cooling:Electricity`)
# because they are simple, interpretable objectives and common in optimization workflows.
#
# Argument rationale:
# - `match="case_insensitive"`: reduces fragility to capitalization differences.
# - `on_missing="raise"`: fails early so we fix output names before expensive runs.
# - `suggest=True`: provides close-name suggestions to speed up debugging.
#
# This selection is not cosmetic: it directly shapes objective space and downstream analysis.

# %%
objective_meters = ["Heating:Electricity", "Cooling:Electricity"]
selection = parametric.select_outputs(
	meters=objective_meters,  # exact output goals for this quickstart
	match="case_insensitive",  # robust matching for common casing differences
	on_missing="raise",  # fail early if an objective output cannot be found
	suggest=True,  # print close matches when selection fails
)
df_meters_sel = selection["meters"]

# %% [markdown]
# ## Step 4.3 - Apply output preflight to clean and verify the IDF
#
# Selection happens in DataFrames, but simulations use output objects stored in the IDF.
# Preflight synchronizes both layers.
#
# Why this step is important:
# - Removes conflicting or legacy output requests from prior experiments.
# - Applies only the outputs needed for this notebook.
# - Verifies the final state so downstream `set_problem()` and run steps are reliable.
#
# Think of this as a consistency checkpoint between intent (selection tables) and execution
# state (the actual IDF objects used during simulation).

# %%
preflight = parametric.apply_outputs_preflight(
	df_meters_sel=df_meters_sel,
	df_vars_sel=None,
	clean_mode="all",  # remove legacy output objects and keep selected ones
	validate_before_apply=False,
	validate_after_apply=True,  # confirm selected outputs exist after apply
	on_missing="raise",
)

print("Missing meters after apply:", len(preflight["verification"]["meters"]["missing_in_idf"]))

# %% [markdown]
# ## Step 4.4 - Register outputs for simulation and problem definition
#
# This call stores the selected outputs inside the simulation object so they become
# part of the objective/response space used by `set_problem()` and later run methods.
#
# Without this registration step, sampling and execution may run with incomplete output intent.

# %%
parametric.set_outputs_for_simulation(df_output_meter=df_meters_sel)

# %% [markdown]
# ## Step 5 - Define parameters and generate samples
#
# We define a compact parameter range dictionary, create the `EPProblem`, and generate
# a small LHS sample plan for a quick demonstration.
#
# Why this step exists:
# - Parameter bounds encode the design space you want to explore.
# - `set_problem()` binds together outputs + parameters into a formal problem definition.
# - `sampling_lhs(...)` provides a space-filling sample that is efficient for small tutorials.

# %%
# Define a tiny parameter space and attach the EPProblem.
# Each tuple is interpreted as a numeric range: (min, max).
accis_parameters = {
	"CustAST_m": (0.2, 0.8),
	"CustAST_n": (10, 22),
	"CustAST_ASToffset": (2.0, 5.0),
}

parametric.set_parameters(accis_params_dict=accis_parameters)
parametric.set_problem()  # builds EPProblem from selected outputs + parameter definition
parametric.sampling_lhs(num_samples=4)  # small Latin Hypercube sample for demonstration

print("Sample size:", len(parametric.parameters_values_df))
parametric.parameters_values_df.head()

# %% [markdown]
# ## Step 6 - Optionally execute the parametric run
#
# We keep execution behind a toggle so you can review setup first; if enabled,
# the run executes the sampled plan and prints a preview of results.
#
# Why this pattern is useful:
# - You can debug setup quickly without paying simulation cost on every notebook execution.
# - Once validated, flipping one flag runs the exact sample already inspected above.

# %%
# `RUN_PARAMETRIC_SIMULATION` is defined right before first use to keep config local.
# Keep this False for a setup-only dry run.
RUN_PARAMETRIC_SIMULATION = True

if RUN_PARAMETRIC_SIMULATION:
	outputs = parametric.run_parametric_simulation(
		out_dir=str(PROJECT_ROOT / RESULTS_DIRNAME),  # output folder for batch artifacts and logs
		df=parametric.parameters_values_df,  # explicit sample plan to execute
		processes=1,  # increase with care; parallel overhead can dominate tiny runs
		keep_input=True,  # keep generated input models for auditability
		keep_dirs=False,  # remove per-run directories to reduce disk usage
	)
	print("Rows:", len(outputs))
	print(outputs.head())
else:
	print("Simulation skipped. Set RUN_PARAMETRIC_SIMULATION = True to execute the run.")

# %%
outputs

# %% [markdown]
# ## Step 7 - Review and optionally clean generated artifacts
#
# We now inspect what files appeared after the baseline snapshot and optionally remove them.
#
# Safety approach used here:
# - Print generated files first.
# - Restrict deletion to a dedicated result folder.
# - Force-clean every generated file inside `nb00_quickstart_results/**` (via `RESULTS_DIRNAME`).
# - Use `dry_run=True` by default to preview the deletion plan.
# - When you are fully confident with the printed plan, set `dry_run=False`.

# %%
generated_files = artifact_cleaner.print_generated_files(max_items=200)

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

