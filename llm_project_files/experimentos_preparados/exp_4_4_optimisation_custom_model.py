"""Paper 4.4: custom-model NSGA-II using only accim's public workflow API.

Minimise HVAC electricity and occupied degree-hours against fixed EN Cat II.
The reporting EMS is provided by accim, not defined in this experiment.
Population 20, budget 200 per climate: 400 FORECAST campaign evaluations.
No simulation on import or without an explicit action and --simulate.
"""

import multiprocessing
from pathlib import Path

from accim.parametric_and_optimisation import run_paper_experiment


# %% Editable configuration; relative paths are based on this file.
HERE = Path(__file__).resolve().parent
IDF_FILE = HERE / "inputs" / "ALJARAFE CENTER_onlyGeometry.idf"
EPW_DIRECTORY = HERE / "inputs"
RESULTS_ROOT = HERE / "results"
CAMPAIGN_NAME = "paper-v1"
RESULT_FILE = None
GEOMETRY_REVIEW_NOTE = ""
SCHEDULE_REVIEW_NOTE = ""
ARGUMENTS = None  # CLI; in Spyder use e.g. ["load", "--result", "chosen.pkl"].

EXPERIMENT = {
    "number": "4.4", "kind": "optimisation",
    "parameters_type": "accim custom model", "ScriptType": "vrf_ac",
    "parameters": {
        "CustAST_m": (0.0, 0.7),
        "CustAST_n": (5.0, 22.5),
        "CustAST_ASToffset": (1.0, 5.0),
        "CustAST_ASTaul": (22.0, 40.0),
    },
    "epws": ["Seville_Present.epw", "Seville_ssp585_2080.epw"],
    "expected_runs": 400, "sampling": None, "comfort": "fixed_en",
}
SETTINGS = {
    "script_directory": HERE,
    "idf": IDF_FILE, "epw_dir": EPW_DIRECTORY, "results_root": RESULTS_ROOT,
    "campaign": CAMPAIGN_NAME, "result": RESULT_FILE,
    "area_note": GEOMETRY_REVIEW_NOTE, "schedule_note": SCHEDULE_REVIEW_NOTE,
}


# %% No local helpers: preparation, metrics, run/resume/load and figures are in accim.
if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_paper_experiment(EXPERIMENT, SETTINGS, argv=ARGUMENTS)
