"""
Testing new functionalities – Sensitivity Analysis (Morris) + MCDM
===================================================================
This script demonstrates two new analytical capabilities added to
the OptimParamSimulation class in branch feature/analysis_methods:

  10. Sensitivity Analysis (Morris method, per EPW)
      Identifies which parameters most influence Heating and Cooling
      electricity demand. Uses Morris sampling: N*(k+1) EnergyPlus
      simulations, with N=5 trajectories and k=5 parameters → 30 runs/EPW.
      Outputs:
        · results_sa_morris_<EPW>.csv  – mu, mu*, sigma per parameter
        · plot_sa_morris_<EPW>.png     – bar chart mu* vs sigma

  11. MCDM – Best compromise solution (per EPW)
      Selects the best single design from the full set of simulations
      using two multi-criteria decision-making methods:
        · Knee Point: minimises normalised Euclidean distance to Utopia point
        · TOPSIS (equal weights): standard TOPSIS with equal weighting
        · TOPSIS (weighted 70/30): prioritises heating over cooling
      Outputs:
        · results_mcdm_best_solutions.csv
        · plot_mcdm_best_solutions.png  – all solutions + best highlighted

Note: For publication quality, increase num_samples in sampling_morris
to at least 50 (300 runs/EPW).
"""

from __future__ import annotations

import os

import pandas as pd

import accim.utils
from accim.parametric_and_optimisation.main import OptimParamSimulation
from besos import eppy_funcs as ef

# This script intentionally runs in top-level (no main()).
# Option A:
#   - No `addAccis` (no parameterisation of ACCIM)
#   - You may add Output:Meter objects for Heating/Cooling
#   - Total simulations = 4 (2 IDFs x 4 EPWs plan → 4 pairs)

BASE_DIR = os.path.abspath(os.path.dirname(__name__))
EP_PATH = r"C:\EnergyPlusV9-6-0"

IDF_BASENAMES = ["SF_Detached_B_min_North", "SF_Detached_D_min_North"]
IDF_PATHS = [os.path.join(BASE_DIR, f"{name}.idf") for name in IDF_BASENAMES]

EPW_BASENAMES = ["seville_2024", "seville_2025", "madrid_2024", "madrid_2025"]
EPW_PATHS = [os.path.join(BASE_DIR, f"{name}.epw") for name in EPW_BASENAMES]

# 4 pairs total (as in check_parametric_multiple_idfs.py):
#   B + seville_2024
#   B + seville_2025
#   D + madrid_2024
#   D + madrid_2025
OUT_DIR = os.path.join(BASE_DIR, "tmy_parametric_analysis_outputs")
ANALYSIS_DIR = os.path.join(OUT_DIR, "analysis")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1) Build the EnergyPlus models (read as-is)
# ---------------------------------------------------------------------------
for idf in IDF_PATHS:
    accim.utils.remove_accents_in_idf(idf_path=idf)

buildings = [ef.get_building(path, ep_path=EP_PATH) for path in IDF_PATHS]
for building in buildings:
    accim.utils.reduce_runtime(idf_object=building)
# ---------------------------------------------------------------------------
# 2) Instantiate OptimParamSimulation without addAccis
#    and add ONLY the heating/cooling Output:Meters
# ---------------------------------------------------------------------------
parametric = OptimParamSimulation(
    building=buildings,
    parameters_type=None,
    bypass_addAccis=True,
    output_freqs=["hourly"],
)

buildings[0].idfobjects['output:meter']

parametric.set_output_met_objects_to_idf(
    output_meters=["DistrictHeating:Facility", "DistrictCooling:Facility"],
)

df_meters_ts, _ = parametric.get_outputs_df_from_testsim()
df_meters_ts = df_meters_ts[df_meters_ts["key_name"].isin(["DistrictHeating:Facility", "DistrictCooling:Facility"])]
parametric.set_outputs_for_simulation(df_output_meter=df_meters_ts)

# No parameters => inputs empty; parametric simulation becomes just evaluating the 4 (idf, epw) pairs.
parametric.set_parameters()
parametric.set_problem()

simulation_plan = pd.DataFrame(
    {
        "idf": [
            IDF_BASENAMES[0],
            IDF_BASENAMES[0],
            IDF_BASENAMES[1],
            IDF_BASENAMES[1],
        ],
        "epw": [
            os.path.join(BASE_DIR, "seville_2024.epw"),
            os.path.join(BASE_DIR, "seville_2025.epw"),
            os.path.join(BASE_DIR, "madrid_2024.epw"),
            os.path.join(BASE_DIR, "madrid_2025.epw"),
        ],
    },
)

print("\n[1/4] Run 4 parametric simulations (Heating + Cooling only)...")
parametric.run_parametric_simulation(
    epws=EPW_PATHS,
    out_dir=OUT_DIR,
    df=simulation_plan,
    processes=1,
    keep_input=True,
    keep_dirs=True,
)

##
print("\n[2/4] MCDM best compromise (knee_point + topsis + topsis w70/30)...")
parametric.outputs_optimisation = parametric.outputs_param_simulation.copy()
parametric.outputs_optimisation["pareto-optimal"] = True
parametric.last_run_type = "optimisation"
parametric.plot_best_compromise_solutions(
    out_dir=ANALYSIS_DIR,
    mcdm_configs=[
        {"method": "knee_point"},
        {"method": "topsis"},
        {"method": "topsis", "weights": [0.7, 0.3], "label": "topsis_w70_30"},
    ],
)

# ---------------------------------------------------------------------------
# 3) Sensitivity analysis (best-effort)
#    Without addAccis there are no model inputs => Morris/Sobol may fail.
# ---------------------------------------------------------------------------
print("\n[3/4] Sensitivity Analysis (Morris) per EPW - best-effort...")
try:
    parametric.last_run_type = "parametric"
    parametric.run_sensitivity_analysis_by_epw(
        method="morris",
        out_dir=ANALYSIS_DIR,
        num_levels=4,
    )
except Exception as e:  # noqa: BLE001
    print(f"  [skip] Sensitivity Analysis failed (expected without parameters): {e}")

# ---------------------------------------------------------------------------
# 4) Extra plots/clustering (best-effort)
# ---------------------------------------------------------------------------
print("\n[4/4] Extra analysis plots/clustering (best-effort)...")
try:
    parametric.last_run_type = "optimisation"
    parametric.plot_pareto_front(out_dir=ANALYSIS_DIR)
except Exception as e:  # noqa: BLE001
    print(f"  [skip] plot_pareto_front failed: {e}")

try:
    parametric.plot_parallel_coordinates(out_dir=ANALYSIS_DIR)
except Exception as e:  # noqa: BLE001
    print(f"  [skip] plot_parallel_coordinates failed: {e}")

try:
    # With no inputs, cluster by objectives (outputs).
    parametric.run_clustering(n_clusters=2, cluster_by="objectives", pareto_only=True, out_dir=ANALYSIS_DIR)
except Exception as e:  # noqa: BLE001
    print(f"  [skip] run_clustering failed: {e}")

print("\n[done] Finished. Results saved under:")
print(f"  OUT_DIR     = {OUT_DIR}")
print(f"  ANALYSIS_DIR= {ANALYSIS_DIR}")
