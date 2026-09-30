# 2. Installation

First of all, you need to install the package. To install the latest
version, execute:

    pip install accim

To install some specific version, execute the same code followed by
"==version number". For instance, to install version 0.6.11:

    pip install accim==0.6.11

## Install the source APIs used by the prepared experiments

The independent comfort-metric APIs and `run_paper_experiment` were introduced
on `feat/comfort-metrics-experiment-api` in source commit `a9b9ebd`. They are
listed as **unreleased**; installing a similarly numbered PyPI distribution
does not guarantee that it contains these methods.

For a local clone on the simulation PC, install its checked-out source from the
chosen environment. The following PowerShell commands are instructions for that
PC, **not commands run during documentation preparation**:

```powershell
git fetch origin
git switch feat/comfort-metrics-experiment-api
python -m pip install -e .
```

Run these from the clone root. Preserve local changes before switching branches;
do not use destructive reset/cleanup to follow this example. If the branch is
already checked out, fetch and fast-forward it only when appropriate. For a
reproducible study, record the full commit being installed rather than relying
on the moving branch name. Editable installation reflects later source edits,
so do not change that checkout midway through a campaign.

The updated package declares `openpyxl>=3.1.5` for XLSX output. Save the installed
environment and package versions with the campaign. Updating accim during an
interrupted campaign may invalidate its source/configuration fingerprint:
retain the previous environment for resume or create a separate new campaign.

Copy the five configuration-only entries and their README from
`llm_project_files/experimentos_preparados`. They import accim directly and do
not depend on another experiment or `article_objectives.py`. Supply the private
IDF and weather files separately; they are not provided by installing the API.

Start with `help` and the documented non-simulating `prepare` operation on the
destination PC. Discovery and campaigns require explicit `--simulate` and the
review steps in the [metric/workflow guide](comfort_metrics.rst). Installing the
package or compiling script syntax does **not** validate EMS numerics,
EnergyPlus compatibility or multiprocessing behavior.
