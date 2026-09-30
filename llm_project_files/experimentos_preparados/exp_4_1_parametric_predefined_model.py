"""Paper 4.1: predefined ACCIM models, static control and mixed-mode retrofit.

The manuscript FORECAST is 132 campaign runs. Static inspection of the current
catalogue instead gives 40 compatible combinations x 3 EPWs = 120; confirm the
generated plan on the simulation PC and acknowledge any difference explicitly.
ComfMod=0 is the static control; never restore ComfStand=0 / 'n/a' tokens.
CS14 has no compatible ComfMod=0: its savings cannot use an invented baseline.
No experiment/discovery runs on import or with no command-line action.
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
RESULT_FILE = None                     # One explicitly selected consolidated file
GEOMETRY_REVIEW_NOTE = ""             # Explain conditioned geometry vs 312 m2
SCHEDULE_REVIEW_NOTE = ""             # Verify occupancy/HVAC schedules on the other PC
ARGUMENTS = None  # CLI; in Spyder use ["load", "--result", "chosen.pkl"].

EXPERIMENT = {
    "number": "4.1", "kind": "parametric",
    "parameters_type": "accim predefined model", "ScriptType": "vrf_mm",
    "parameters": {
        "ComfStand": [1, 2, 3, 14, 16],
        "CAT": [1, 2, 3, 80, 90],
        "ComfMod": [0, 3],
        "HVACmode": [0, 2],
    },
    "epws": ["Seville_Present.epw", "Seville_ssp245_2050.epw", "Seville_ssp585_2080.epw"],
    "expected_runs": 132, "sampling": "full_set", "comfort": "fixed_en",
}


SETTINGS = {
    "script_directory": HERE,
    "idf": IDF_FILE, "epw_dir": EPW_DIRECTORY, "results_root": RESULTS_ROOT,
    "campaign": CAMPAIGN_NAME, "result": RESULT_FILE,
    "area_note": GEOMETRY_REVIEW_NOTE, "schedule_note": SCHEDULE_REVIEW_NOTE,
}


# %% All preparation/reporting/run/load logic is supplied by accim.
if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_paper_experiment(EXPERIMENT, SETTINGS, argv=ARGUMENTS)
