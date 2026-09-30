"""Paper 4.3: aPMV cooling coefficient x symmetric PMV setpoint.

4 x 3 x 3 climates = 36 FORECAST campaign runs. Heating lambda stays at the
reviewed default -0.293; lambda_c=0 is NOT pure PMV in the heating season.
VRF/Fanger are prepared once on a copy, followed by one aPMV injection.
Reports native discomfort hours separately from occupied fixed-Fanger metrics.
"""

import multiprocessing
from pathlib import Path

from accim.parametric_and_optimisation import run_paper_experiment


# %% EDIT THESE PATHS, or use the corresponding command-line options.
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
    "number": "4.3", "kind": "parametric",
    "parameters_type": "apmv setpoints", "ScriptType": None,
    "parameters": {
        "Adaptive cooling coefficient": [0.0, 0.1, 0.3, 0.5],
        "PMV setpoint": [0.2, 0.5, 0.7],
    },
    "epws": ["Seville_Present.epw", "Seville_ssp245_2050.epw", "Seville_ssp585_2080.epw"],
    "expected_runs": 36, "sampling": "full_set", "comfort": "apmv",
}


# %% Existing aPMV requests are preserved with append, not replaced.
SETTINGS = {
    "script_directory": HERE,
    "idf": IDF_FILE, "epw_dir": EPW_DIRECTORY, "results_root": RESULTS_ROOT,
    "campaign": CAMPAIGN_NAME, "result": RESULT_FILE,
    "area_note": GEOMETRY_REVIEW_NOTE, "schedule_note": SCHEDULE_REVIEW_NOTE,
}


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_paper_experiment(EXPERIMENT, SETTINGS, argv=ARGUMENTS)
