"""Paper 4.5: NSGA-II, population 20, budget 200 per EPW (400 forecast).

Minimise HVAC electricity and the ONE native Discomfortable Total Hours_*
counter. It sums ZoneTimeStep increments, is not occupancy-filtered in the
reviewed accim source, and moves with the optimised PMV setpoint.
Fixed occupied Fanger diagnostics are retained in CSVs, NOT substituted into
the optimisation. Fixing PMV setpoint or changing the objective is a DIFFERENT
experimental configuration and needs a new campaign and manuscript definition.
"""

import multiprocessing
from pathlib import Path

from accim.parametric_and_optimisation import run_paper_experiment


# %% EDIT THESE PATHS, or use command-line options; no machine-specific paths.
HERE = Path(__file__).resolve().parent
IDF_FILE = HERE / "inputs" / "ALJARAFE CENTER_onlyGeometry.idf"
EPW_DIRECTORY = HERE / "inputs"
RESULTS_ROOT = HERE / "results"
CAMPAIGN_NAME = "paper-v1"
RESULT_FILE = None
GEOMETRY_REVIEW_NOTE = ""
SCHEDULE_REVIEW_NOTE = ""
ARGUMENTS = None  # CLI; in Spyder use ["load", "--result", "chosen.pkl"].

EXPERIMENT = {
    "number": "4.5", "kind": "optimisation",
    "parameters_type": "apmv setpoints", "ScriptType": None,
    "parameters": {
        "Adaptive cooling coefficient": (0.0, 1.0),
        "Adaptive heating coefficient": (-1.0, 0.0),
        "PMV setpoint": (0.2, 0.9),
    },
    "epws": ["Seville_Present.epw", "Seville_ssp585_2080.epw"],
    "expected_runs": 400, "sampling": None, "comfort": "apmv",
}


# %% Resume reuses completed EPW cases; it does not resume a Platypus population.
# Pareto flags and TOPSIS/knee selections are always scoped to the same climate.
SETTINGS = {
    "script_directory": HERE,
    "idf": IDF_FILE, "epw_dir": EPW_DIRECTORY, "results_root": RESULTS_ROOT,
    "campaign": CAMPAIGN_NAME, "result": RESULT_FILE,
    "area_note": GEOMETRY_REVIEW_NOTE, "schedule_note": SCHEDULE_REVIEW_NOTE,
}


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_paper_experiment(EXPERIMENT, SETTINGS, argv=ARGUMENTS)
