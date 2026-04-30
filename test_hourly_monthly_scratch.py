import os
import pandas as pd
import accim.utils
from accim.parametric_and_optimisation.main import OptimParamSimulation
from besos import eppy_funcs as ef

BASE_DIR = os.path.abspath(os.path.dirname(__name__))
EP_PATH = r"C:\EnergyPlusV9-6-0"

IDF_BASENAMES = ["SF_Detached_B_min_North", "SF_Detached_D_min_North"]
IDF_PATHS = [os.path.join(BASE_DIR, f"{name}.idf") for name in IDF_BASENAMES]

EPW_BASENAMES = ["seville_2024", "seville_2025", "madrid_2024", "madrid_2025"]
EPW_PATHS = [os.path.join(BASE_DIR, f"{name}.epw") for name in EPW_BASENAMES]

OUT_DIR = os.path.join(BASE_DIR, "tmy_parametric_analysis_outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# 1) Build the EnergyPlus models (read as-is)


for idf in IDF_PATHS:
    accim.utils.remove_accents_in_idf(idf_path=idf)
buildings = [ef.get_building(path, ep_path=EP_PATH) for path in IDF_PATHS]

for building in buildings:
    accim.utils.reduce_runtime(
        idf_object=building,
        runperiod_end_month=3,
        runperiod_end_day_of_month=31
    )


# 2) Instantiate OptimParamSimulation
parametric = OptimParamSimulation(
    buildings=buildings,
    epws=EPW_PATHS,
    parameters_type=None,
    bypass_addAccis=True,
    output_freqs=["hourly"],
)

parametric.set_output_met_objects_to_idf(
    output_meters=["DistrictHeating:Facility", "DistrictCooling:Facility"],
)

df_meters_ts, _ = parametric.get_outputs_df_from_testsim()
df_meters_ts = df_meters_ts[df_meters_ts["key_name"].isin(["DistrictHeating:Facility", "DistrictCooling:Facility"])]
parametric.set_outputs_for_simulation(df_output_meter=df_meters_ts)

parametric.set_parameters()
parametric.set_problem()

# Use the new sampling_custom method with a dict mapping
parametric.sampling_custom({
    IDF_BASENAMES[0]: EPW_PATHS[0:2],  # B with seville 2024, 2025
    IDF_BASENAMES[1]: EPW_PATHS[2:4]   # D with madrid 2024, 2025
})

print(f"Generated Custom Plan ({len(parametric.parameters_values_df)} rows):")
print(parametric.parameters_values_df)

print("\nRunning parametric simulation...")
parametric.run_parametric_simulation(
    out_dir=OUT_DIR,
    processes=1,
    keep_input=True,
    keep_dirs=True,
)

print("outputs_param_simulation columns:")
print(parametric.outputs_param_simulation.columns.tolist())

from accim.parametric_and_optimisation.utils import identify_hourly_columns

try:
    print("\nRunning get_hourly_df()...")
    parametric.get_hourly_df()
    hourly_df = parametric.outputs_param_simulation_hourly
    print(f"Hourly DF Shape: {hourly_df.shape}")
    print(hourly_df.head())
except Exception as e:
    print(f"Error in get_hourly_df: {e}")

try:
    print("\nRunning get_monthly_df()...")
    parametric.get_monthly_df()
    monthly_df = parametric.outputs_param_simulation_monthly
    print(f"Monthly DF Shape: {monthly_df.shape}")
    print(monthly_df.head())
    print("Test completed successfully!")
except Exception as e:
    print(f"Error in get_monthly_df: {e}")
