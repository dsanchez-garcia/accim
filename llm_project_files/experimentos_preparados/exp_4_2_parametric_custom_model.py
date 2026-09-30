"""Paper 4.2: custom adaptive models, LHS 100 x 3 climates (300 forecast runs).

Combines the reference v3 with the later simulation-folder fixes: explicit
consolidated load, original checkpoint plan, actual normalized column names,
no-tolerance setpoints and PMOT (NOT RMOT) for custom-model regression figures.
The required vrf_ac is retained; the later copy's vrf_mm is NOT adopted.
The existing 300/300 campaign is preserved and is load-only in this delivery.
"""

import multiprocessing
from pathlib import Path

from accim.parametric_and_optimisation import run_paper_experiment


# %% EDIT THESE PATHS, or use command-line overrides (no dated result path).
HERE = Path(__file__).resolve().parent
IDF_FILE = HERE / "inputs" / "ALJARAFE CENTER_onlyGeometry.idf"
EPW_DIRECTORY = HERE / "inputs"
RESULTS_ROOT = HERE / "results"
CAMPAIGN_NAME = "paper-v1"
RESULT_FILE = None                     # Select the RAW consolidated .pkl explicitly
GEOMETRY_REVIEW_NOTE = ""
SCHEDULE_REVIEW_NOTE = ""
ARGUMENTS = None  # CLI; in Spyder use ["load", "--result", "chosen.pkl"].

EXPERIMENT = {
    "number": "4.2", "kind": "parametric",
    "parameters_type": "accim custom model", "ScriptType": "vrf_ac",
    "parameters": {
        "CustAST_m": (0.0, 0.7),
        "CustAST_n": (5.0, 22.5),
        "CustAST_ASToffset": (1.0, 5.0),
        "CustAST_ASTaul": (22.0, 40.0),
    },
    "epws": ["Seville_Present.epw", "Seville_ssp245_2050.epw", "Seville_ssp585_2080.epw"],
    "expected_runs": 300, "sampling": "lhs", "comfort": "fixed_en",
}


# %% new persists plan.pkl/plan.csv; resume NEVER calls sampling_lhs again.
# load needs neither the input IDF nor EPWs and cannot launch simulations.
SETTINGS = {
    "script_directory": HERE,
    "idf": IDF_FILE, "epw_dir": EPW_DIRECTORY, "results_root": RESULTS_ROOT,
    "campaign": CAMPAIGN_NAME, "result": RESULT_FILE,
    "area_note": GEOMETRY_REVIEW_NOTE, "schedule_note": SCHEDULE_REVIEW_NOTE,
}


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_paper_experiment(EXPERIMENT, SETTINGS, argv=ARGUMENTS)
