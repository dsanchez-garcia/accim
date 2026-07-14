# %% [markdown]
# # Optimisation example with custom output reducers and `processes > 1`
#
# This script is notebook-style (`# %%`) and shows two supported ways to pass custom
# reducer functions into `set_outputs_for_simulation(...)`:
#
# 1) callable object imported from a top-level module
# 2) import path string: "module.submodule:callable_name"
#
# By default, `RUN_FULL` is False so the file is safe to execute as a smoke check.
# Set `RUN_FULL = True` to run the actual EnergyPlus optimisation.

# %%
from pathlib import Path

import pandas as pd
from besos import eppy_funcs as ef

from accim.parametric_and_optimisation.main import OptimisationSimulation

# Top-level importable callables (safe pattern for multiprocessing on Windows)
from tools.custom_output_funcs import return_time_series, q95

# %%
RUN_FULL = False

idf_path = Path("tests/test_data/SF_Detached_B_min_North.idf")
epw_path = Path("tests/test_data/seville_2024.epw")
out_dir = Path("tools/tmp_optim_callable_example")

print(f"IDF exists: {idf_path.exists()} -> {idf_path}")
print(f"EPW exists: {epw_path.exists()} -> {epw_path}")
print(f"RUN_FULL={RUN_FULL}")

# %% [markdown]
# Instantiate simulation class and inject ACCIM custom model.

# %%
building = ef.get_building(str(idf_path))

optim = OptimisationSimulation(
    building=building,
    parameters_type="accim custom model",
)

# %% [markdown]
# Define outputs for BESOS readers.
#
# - `func` as callable (`return_time_series`)
# - `func` as import path string (`tools.custom_output_funcs:q95`)

# %%
df_output_variable = pd.DataFrame(
    [
        {
            "key_value": "*",
            "variable_name": "Zone Operative Temperature",
            "frequency": "hourly",
            "name": "Zone Operative Temperature (time series)",
            "func": return_time_series,
        },
        {
            "key_value": "*",
            "variable_name": "Zone Operative Temperature",
            "frequency": "hourly",
            "name": "Zone Operative Temperature (q95)",
            "func": "tools.custom_output_funcs:q95",
        },
    ]
)

df_output_meter = pd.DataFrame(
    [
        {
            "key_name": "Electricity:HVAC",
            "frequency": "hourly",
            "name": "Electricity:HVAC q95",
            "func": "tools.custom_output_funcs:q95",
        }
    ]
)

optim.set_outputs_for_simulation(
    df_output_variable=df_output_variable,
    df_output_meter=df_output_meter,
)

print("Configured output readers:")
for r in optim.sim_outputs:
    print("-", getattr(r, "name", type(r).__name__))

# %% [markdown]
# Define ACCIM parameters and optimisation problem.

# %%
accis_parameters = {
    "CustAST_m": (0.2, 0.8),
    "CustAST_n": (10, 23),
    "CustAST_ASToffset": (2, 4),
    "CustAST_ASTall": (10, 15),
    "CustAST_ASTaul": (30, 35),
}
optim.set_parameters(accis_params_dict=accis_parameters)
optim.set_problem(minimize_outputs=[True, True, True])

# %% [markdown]
# Run optimisation with multiprocessing.
#
# This is intentionally behind `RUN_FULL` to keep this script lightweight by default.

# %%
if RUN_FULL:
    results = optim.run_optimisation(
        epws=[str(epw_path)],
        out_dir=str(out_dir),
        evaluations=4,
        population_size=2,
        algorithm="NSGAII",
        processes=4,
        keep_sim_files="none",
        keep_df="all",
    )
    print(results.head())
else:
    print("Dry run only. Set RUN_FULL=True to execute optimisation with processes > 1.")

