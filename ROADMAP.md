# ROADMAP

Mid- and long-term technical plan.

## How to use this file

- Include large initiatives (not day-to-day small tasks).
- Each initiative must include objective, scope, and exit criteria.
- Move completed milestones to `DEVLOG.md` when finished.

## Initiative template

```md
### [R-XX] Initiative title
- Horizon: Qx YYYY / Long term
- Objective:
- Scope:
- Exit criteria:
- Dependencies:
```

## Initiatives

### [R-01] Technical documentation governance
- Horizon: Q3 2026
- Objective: Consolidate a stable structure for technical tracking and planning.
- Scope: Define rules across `DEVLOG.md`, `TODO.md`, `ROADMAP.md`, and `CHANGELOG.md`.
- Exit criteria: A short usage guide agreed and applied across all four files.
- Dependencies: none left (the priorities and the format of the references to issues and pull requests were agreed on 2026-11-09, in the conventions of `TODO.md`).

### [R-02] Historical archiving policy
- Horizon: Q4 2026
- Objective: Prevent tracking files from growing without control.
- Scope: Define archiving frequency (per release or quarter) and folder structure.
- Exit criteria: First archive cycle executed with a defined template.
- Dependencies: Finalized documentation workflow structure.

### [R-03] Remove the names of accim 0.x
- Horizon: Long term (accim 2.0)
- Objective: Remove the deprecated aliases that accim 1.0.0 kept for the scripts written for accim 0.x.
- Scope: `accim.sim.accis.addAccis`, `accim.sim.accis_single_idf`, `accim.sim.accis_single_idf_funcs`, `accim.sim.apmv_setpoints`, `runEp`, `removefiles`, `genCSVconcatenated`, `preview_Table_cols`, `accim.lists`, the old keyword arguments and the old keys of `AddAccis.arguments`.
- Exit criteria: no code, sample or notebook of accim uses the old names; the removal is announced in `CHANGELOG.md` at least one minor version before.
- Dependencies: TODO "Update the sample scripts and notebooks to the names of accim 1.0.0".

### [R-04] Refactoring of `Table`
- Horizon: Long term
- Objective: Split the constructor of `accim.data.postprocessing.main.Table` (about 1,400 lines) into steps (reading and concatenating the CSV files, aggregating, renaming, block and building levels), as `accim.sim` was split in 1.0.0, and its figure methods into a separate module.
- Scope: `accim/data/postprocessing/main.py`; the usage and the columns of `Table` do not change.
- Exit criteria: the tests of `Table` and the How-to notebooks give the same results.
- Dependencies: tests of `Table` that cover the frequencies, levels and units (see the regression tests in `TODO.md`).

### [R-05] Python API backend: complete coverage of the EMS
- Horizon: Long term
- Objective: Run any EMS model through the Python API of EnergyPlus, not only those of accim.
- Scope: `EnergyManagementSystem:TrendVariable`, `CurveOrTableIndexVariable` and `ConstructionIndexVariable`, the psychrometric and curve functions of Erl, the calling point `UserDefinedComponentModel`, integer actuators.
- Exit criteria: the 11 EMS example files of EnergyPlus give the same results with both backends.
- Dependencies: whether the API of EnergyPlus gives access to the data of these objects (curves, tables, constructions).

### [R-06] Parametric and optimisation module without besos
- Horizon: Long term (accim 2.0)
- Objective: Remove besos (and the pins pulp<4, datapackage and the patches of accim/_besos_compat.py) by replacing its Evaluator with an accim class that applies the Parameter objects with eppy, runs run_ep (EMS or API backend) in parallel with concurrent.futures and reads the results with the current readers; platypus directly for run_optimisation and SALib for run_sensitivity_analysis_by_epw.
- Scope: accim/parametric_and_optimisation/*, accim/_besos_compat.py, setup.py/pyproject.toml, tests/parametric_and_optimisation_full_workflow.
- Exit criteria: the full-workflow tests give the same results; pip install accim does not install besos; requirements-dev.txt has no inherited pins.
- Dependencies: E3 (pyproject with extras), regression tests of the full workflow.

### [R-07] The overheating criteria of CIBSE TM52 and TM59
- Horizon: Long term (after accim 1.2.0, when the documents are available)
- Objective: Give the overheating criteria of CIBSE TM52 (2013) and TM59 (2017) as indicators of the long-term discomfort and, if the author wants, as objectives of the optimisation.
- Scope: the criteria (TM52: the hours of exceedance, the weighted exceedance of a day and the upper limit; TM59: those of dwellings) as functions of `accim.data.postprocessing.long_term_discomfort`, with tests from the examples of the texts. Out of the scope of accim 1.2.0 since 2026-11-12 (`notes/decisions.md`; the recommendation of the review of Claude Science of 2026-11-11, `notes/TRASPASO_ClaudeScience_2026-11-11_v01.md` §4: CEN/TR 16798-2:2019, Annex D, already gives the long-term indicators): until then it was a blocked entry of `TODO.md` (C2 and D1 of `notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md`).
- Exit criteria: the functions give the results of the examples of both documents.
- Dependencies: the texts of CIBSE TM52 and TM59, which are not in the sources of the sessions of accim 1.2.0 (decision D12 of `notes/COPILOT_BRIEF_v1.2.0_v01.md`: no code about them without the texts).

