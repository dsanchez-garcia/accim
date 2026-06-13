"""
Tutorial: OptimisationSimulation with parameters_type='accim custom model' - Optimisation Part
=============================================================================================

This notebook covers the configuration and running of the optimization simulation.
The optimization results will be saved to disk so that they can be loaded and analyzed in a separate session.

Workflow:
  1. Load and prepare the IDF.
  2. Instantiate OptimisationSimulation.
  3. Discover, select and apply outputs.
  4. Define ACCIM custom-model parameters.
  5. Define and run the optimisation problem.
"""

# %% [markdown]
# # 0. Imports and user settings
# We start by importing the required packages and setting up the configurations.
# Since we are using standard optimization settings, we define the evaluations, population size, and CPU count.

# %%
import os
import multiprocessing as mp
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["figure.dpi"] = 150

import accim
from accim.parametric_and_optimisation.main import OptimisationSimulation
from tools.custom_output_funcs import return_time_series
from besos import eppy_funcs as ef

PROJECT_DIR = Path.cwd()
os.chdir(PROJECT_DIR)

IDF_FILE = "OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf"
EPW_LIST = ["Seville.epw", "Sydney.epw"]
OUT_DIR = "tutorial_optim_accim_custom_model"

EVALUATIONS = 10
POPULATION_SIZE = 5
PROCESSES = min(4, os.cpu_count() or 1)

# %% [markdown]
# # 1. Load and prepare the EnergyPlus model
# We load the building geometry from the IDF file using BESOS, and configure the occupancy.

# %%
def main() -> None:
    building = ef.get_building(IDF_FILE)

    accim.utils.set_occupancy_to_always(idf_object=building)

    # Keep the tutorial fast. Remove or relax this line for production runs.
    accim.utils.reduce_runtime(idf_object=building, timesteps=2)

# %% [markdown]
# # 2. Instantiate OptimisationSimulation
# We instantiate the `OptimisationSimulation` class using the custom adaptive comfort model parameters.

# %%
    parametric = OptimisationSimulation(
        building=building,
        parameters_type="accim custom model",
        epws=EPW_LIST,
    )

# %% [markdown]
# # 3. Discover available outputs
# Before selecting the optimization objectives, we discover what output variables and meters are present in the model.

# %%
    discovery = parametric.discover_available_outputs(
        reduce_sim_time=True,
        prefer="testsimeplus",
    )
    df_meters_available = discovery["meters"]
    df_vars_available = discovery["variables"]
    outputs_meta = discovery["meta"]

    print("Discovery source:", outputs_meta.get("source"))
    print("Available meters:", len(df_meters_available))
    print("Available variables:", len(df_vars_available))

    df_meters_available.head()

# %% [markdown]
# # 4. Select the outputs for this optimisation
# We select the Heating and Cooling electricity consumption as objectives, and define auxiliary variables to keep.

# %%
    objective_meters = [
        "Heating:Electricity",
        "Cooling:Electricity",
    ]

    auxiliary_variables = [
        "Setpoint Temperature_No Tolerance",
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
    meters_report = meters_selection["report"]

    variables_selection = parametric.select_outputs(
        variables=auxiliary_variables,
        match="contains",
        on_missing="warn",
        suggest=True,
    )
    df_vars_sel = variables_selection["variables"]
    variables_report = variables_selection["report"]

    print("Selected objective meters:", len(df_meters_sel))
    print("Selected auxiliary variables:", len(df_vars_sel))

    if variables_report["missing"]["variables"]:
        print("Missing auxiliary variables:", variables_report["missing"]["variables"])
        print("Suggestions:", variables_report["suggestions"]["variables"])

# %% [markdown]
# # 5. Apply the selected outputs to the IDF
# Clear stale output objects, apply the selected ones, and set the simulation outputs.

# %%
    preflight_report = parametric.apply_outputs_preflight(
        df_meters_sel=df_meters_sel,
        df_vars_sel=df_vars_sel,
        clean_mode="all",
        validate_before_apply=False,
        validate_after_apply=True,
        on_missing="raise",
    )

    print("Meters missing in IDF:", len(preflight_report["verification"]["meters"]["missing_in_idf"]))
    print("Variables missing in IDF:", len(preflight_report["verification"]["vars"]["missing_in_idf"]))

    # Attach an importable callable reducer to the running-average outdoor temperature output.
    # String format is robust with processes > 1 on Windows.
    df_vars_callable = df_vars_sel[
        df_vars_sel["variable_name"].str.contains("Running Average Outdoor Air Temperature", case=False, na=False)
    ].copy()
    df_vars_callable["func"] = return_time_series
    # Alternative robust format for multiprocessing on Windows:
    # df_vars_callable["func"] = "tools.custom_output_funcs:return_time_series"
    df_vars_callable["name"] = df_vars_callable["variable_name"] + "_time series"

    # Build non-optimized callable readers first (they will be passed via add_outputs).
    parametric.set_outputs_for_simulation(df_output_variable=df_vars_callable)
    add_output_readers = list(parametric.sim_outputs)

    # Set objective readers (meters) for optimisation.
    parametric.set_outputs_for_simulation(
        df_output_meter=df_meters_sel,
    )

# %% [markdown]
# # 6. Define ACCIM custom-model parameters
# Define range descriptors for the NSGA-II algorithm parameters.

# %%
    parametric.get_available_parameters()

    accis_parameters = {
        "CustAST_m": (0.01, 0.99),
        "CustAST_n": (5, 23),
        "CustAST_ASToffset": (1.5, 5),
        "CustAST_ASTall": (8, 16),
        "CustAST_ASTaul": (28, 38),
    }

    parametric.set_parameters(accis_params_dict=accis_parameters)

# %% [markdown]
# # 7. Define the optimisation problem
# In this example, only meter outputs are optimized. Callable variable outputs are
# reported as add_outputs (non-optimized) for inspection.

# %%
    minimize_flags = [True] * len(df_meters_sel)
    parametric.set_problem(minimize_outputs=minimize_flags, add_outputs=add_output_readers)

# %% [markdown]
# # 8. Estimate the number of simulations
# Estimate how many runs will be executed based on evaluations and population size.

# %%
    parametric.estimate_optimisation_sims(
        evaluations=EVALUATIONS,
        population_size=POPULATION_SIZE,
        epws=EPW_LIST,
    )

# %% [markdown]
# # 9. Run NSGA-II optimisation
# Run the optimization. The results will be automatically saved as a CSV and a pickle file in `OUT_DIR`.

# %%
    outputs_optimisation = parametric.run_optimisation(
        epws=EPW_LIST,
        out_dir=OUT_DIR,
        algorithm="NSGAII",
        evaluations=EVALUATIONS,
        population_size=POPULATION_SIZE,
        processes=PROCESSES,
        keep_df="all",
        keep_sim_files="non-dominated",
        keep_sim_files_batch_size=POPULATION_SIZE,
    )

    print("Optimisation rows:", len(outputs_optimisation))
    print("Optimisation CSV:", parametric.outputs_optimisation_filepath)

    outputs_optimisation.head()

# %% [markdown]
# # 10. Verify callable-derived columns in optimisation outputs
# Inspect columns generated from callable add_outputs and preview a sample value.

# %%
    callable_cols = [c for c in outputs_optimisation.columns if c.endswith("_time series")]
    print("Callable-derived columns found:", callable_cols)

    if callable_cols:
        first_col = callable_cols[0]
        first_val = outputs_optimisation[first_col].iloc[0]
        print("Sample column:", first_col)
        print("Sample value type:", type(first_val))
        # Print a short preview when possible
        try:
            print("Sample length:", len(first_val))
            print("Sample head:", first_val[:5])
        except Exception:
            print("Sample value:", first_val)
    else:
        print("No callable-derived columns were found. Re-run optimisation after applying the latest module patch.")


if __name__ == "__main__":
    mp.freeze_support()
    main()

