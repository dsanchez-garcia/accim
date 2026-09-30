# 1. Requirements

Please, note this documentation is for version |version|.

To use accim, the following must be installed:

*   Python **3.9 or newer**, in an environment compatible with the installed BESOS and scientific dependencies.
    *   On Windows, add the chosen Python interpreter to PATH (or invoke its full path).
    *   Disable path length limit.
*   EnergyPlus (any version between 9.1 and 25.1, inclusive) in the default path (e.g., `C:\EnergyPlusV25-1-0`).
    *   The EnergyPlus executable, IDD and IDF version must agree; configure BESOS accordingly.

Jupyter Notebook is also recommended to run the example notebooks located in `accim/sample_files/jupyter_notebooks`.

## Independent metrics and prepared paper workflows

The unreleased APIs `add_comfort_metrics`, `checked_sum_results` and
`run_paper_experiment` require the corresponding source revision from
`feat/comfort-metrics-experiment-api`; a version number alone is not a capability
check. See [installation](2_installation.md) and the
[metric/workflow guide](comfort_metrics.rst).

Install the package dependencies in the same environment: BESOS/eppy,
Platypus, NumPy/pandas/SciPy, matplotlib/seaborn and the other requirements
declared by accim. `openpyxl>=3.1.5` is now declared for the automatic XLSX
campaign exports. Do not mix interpreters between the editor, terminal and workers.

Metric preparation requires a prepared IDF with `AdaptiveCEN15251` enabled on
People for `fixed_en`, `Fanger` for `fixed_pmv`, or both. It does not invent
comfort-input or occupancy schedules. The paper wrapper additionally requires
one zone, one resolved People target and a complete annual weather RunPeriod.
Those restrictions and its 312 m² denominator are paper-specific.

Result-only `load` needs the Python dependencies and a trusted consolidated
file; it does not load an input IDF or launch EnergyPlus. Hourly figures also
require the retained simulation CSVs. Preparation/discovery/campaigns need the
input IDF and EPWs; only discovery/new/resume may simulate, by explicit opt-in.
