# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Area Normalization and Floor Area Configuration**: Extended `set_building_floor_area` and related normalisation workflows for multi-IDF studies.
  - Added `mode='air-conditioned'` to calculate floor area from zones served or controlled by HVAC-related IDF objects such as `ZoneControl:*`, `ZoneHVAC:*`, `ZoneHVAC:EquipmentConnections`, `HVACTemplate:Zone:*`, and `AirTerminal:*`. The alias `mode='air-condicioned'` is also accepted.
  - `zones_list` can now be either a global list applied to every IDF or a dictionary mapping each IDF to its own list of zones.
  - `custom_area` can now be a global float/string value or a dictionary mapping each IDF to its own value.
  - Dictionary keys are normalized against IDF names and validated to prevent silent mismatches.
  - Multi-IDF area maps, `normalize_outputs()`, `normalize_per_m2` in dataframe extraction methods, and double-normalisation safeguards are supported consistently.
  - Added representative-IDF modes to reduce floor-area setup cost in large campaigns:
    - `representative_mode='all'` keeps legacy behavior.
    - `representative_mode='by_idf_mapping_category'` groups IDFs by a user-selected category (`representative_category`) and loads one deterministic representative IDF per category value.
    - `representative_mode='custom_map'` accepts explicit `representative_map={category_value: representative_idf}` with strict coverage and route validation.
  - Added validation and explicit errors for representative workflows:
    - Invalid `representative_category` now reports available categories from `idf_mapping_rules`.
    - Missing category columns in `outputs_param_simulation` now raise clear errors including available categories.
    - `custom_map` now validates missing/unknown category values and representative IDF membership per category group.
  - Added informative logs for floor-area representative workflows (total IDFs, representative IDFs loaded, and final mapping coverage).
- **Simulation Input Traceability (`in.idf`)**: Parametric and optimisation workflows now preserve the exact transient IDF executed by BESOS/EnergyPlus inside each simulation result directory.
- **Outputs Preflight Workflow (`parametric_and_optimisation`)**: Added `discover_available_outputs(...)`, `select_outputs(...)`, `clear_outputs(...)`, and `apply_outputs_preflight(...)` to discover, validate, clean, and apply output requests before running simulations.
- **Scoped Multi-IDF Output Preflight**: Added `idf_scope`/`validation_idf_scope` support across output discovery, selection, cleanup, application, and IDF output DataFrame helpers, plus `keep_only_outputs_in_idfs(...)` to prune existing `Output:Meter` and `Output:Variable` objects without adding missing outputs.
  - Multi-IDF output reads now include an `idf` column, cache entries are scoped to the validation target, temporary test-simulation IDFs use unique names per source IDF, and preflight verification reports include per-IDF details.
- **Plotting and Category Utilities**: Added categorical energy boxplots, highlight overlays, subplot sizing controls, keyword-based category mapping, category previews, and EPW suffix category persistence.
- **Advanced Parametric Visualisation Suite**: Added eight new plotting helpers in `PlottingMixin` for both `ParametricSimulation` and optimisation datasets (`df_source='parametric'|'optimisation'`).
  - New methods: `plot_parametric_scatter`, `plot_parametric_lines`, `plot_parametric_heatmap`, `plot_parametric_contour`, `plot_parametric_distributions`, `plot_parametric_ecdf`, `plot_parametric_density_2d`, and `plot_parametric_radar`.
  - Added shared plotting helpers for dataframe source resolution, filename-safe tokens, and normalization-aware axis-unit handling.
  - Added compatibility and resilience fallbacks (for example, seaborn `errorbar` vs legacy `ci`, and contour/KDE fallback to scatter when data is insufficient).
  - Added dedicated tests in `tests/parametric_and_optimisation/test_plotting_parametric_new_methods.py` covering all new visualisation methods.
- **Simulation Planning and Routing**: Added `sampling_custom()`, native multi-IDF/multi-EPW handling, IDF as an explicit input variable, per-row EPW routing, and a multi-IDF validation script.
- **Data Extraction and Persistence**: Added monthly aggregation methods, automatic hourly CSV fallback, optimisation hourly column discovery, hourly optimisation expansion controls, `.pkl`/`.json` session persistence, enhanced load methods, IDF backups, and session merging.
- **Optimisation and Analysis Tools**: Added optimisation run estimation, parallel optimisation evaluation via `processes`, Morris/Sobol sensitivity analysis integration, and MCDM compromise-solution helpers.
- **Model Utilities and Runtime Support**: Added `AccimSimulationVerifier`, `set_operative_temp_control`, `update_idf_version`, scheduled natural ventilation support, scheduled ventilation output variables, and automatic standard autosizing constraint initialization.
- **Consistent Output Management API (`parametric_and_optimisation`)**: Added `set_output_variables_to_idf(...)` and `set_output_meters_to_idf(...)` with aligned signatures and behavior.
  - Variables now accept both DataFrame (`df_output_variable`) and list (`output_variables`) inputs.
  - Meters now accept both list (`output_meters`) and DataFrame (`df_output_meter`) inputs, including per-row `frequency` overrides when present.
  - Added symmetric read aliases: `get_output_variables_df_from_idf(...)` and `get_output_meters_df_from_idf(...)`.
- **Importable Custom Output Reducers in Multiprocessing**: `set_outputs_for_simulation(...)` now accepts `func` values as callables or import-path strings (`"module.submodule:callable_name"`).
  - Reader reducer functions are serialized/resolved for worker processes so custom aggregation logic can be reused with `processes > 1` in parametric simulations.
  - Added user warnings when a reducer cannot be serialized as an importable path and may fail under Windows `spawn` multiprocessing.
- **XLSX Result Exports**: Parametric and optimisation result tables are now also saved as `.xlsx` files alongside existing `.csv`, `.pkl`, and `.json` exports.
- **Legacy Parametric Output Alias**: Added `outputs_param_sim` as a backward-compatible alias of `outputs_param_simulation`.
- **Workspace Artifact Cleanup Utility**: Added `WorkspaceArtifactCleaner` in `accim.utils` to snapshot workspace files, detect generated artifacts, preview deletion plans (`dry_run`), and safely remove selected outputs with allow/deny glob patterns.
- **Simulation Comparison Utilities**: Promoted simulation-result comparison helpers into the public `accim.parametric_and_optimisation` namespace.
  - Added/Exported `SimulationComparisonSession`, `compare_simulation_instances(...)`, `compare_latest_pickles_in_folders(...)`, and `compare_multiple_pickles_with_reference(...)` for strict/relaxed parity checks across DataFrames, simulation instances, and persisted files.
  - Added regression tests covering strict vs relaxed comparison modes, folder-latest pickle comparison, mixed source discovery, and session history/report persistence.
- **Pickle Comparison Tutorial Docs**: Added `docs/source/9_pickle_comparison_tutorial.md` and linked it in the docs index for end-to-end guidance on validating simulation output equivalence.
- **Project Tracking Workflow Files**: Added `DEVLOG.md`, `TODO.md`, and `ROADMAP.md` and documented the workflow in `README.md` to separate release notes, completed work logs, active tasks, and longer-term planning.
- **Operations Tooling for Notebooks and Campaign Runs**: Added helper scripts under `tools/` for custom output reducers, robust custom-plan parametric execution, batch notebook execution, and reruns of failed notebooks.
- **Regression Coverage for Optimisation Output Handling**: Added focused tests in `tests/parametric_and_optimisation/test_analysis_output_resolution.py` and `tests/parametric_and_optimisation/test_pareto_grouping.py`.
  - Covers robust objective-column resolution when optimisation outputs are normalized/renamed.
  - Covers configurable Pareto grouping by EPW and/or IDF and MCDM grouping behavior in plotting.
- **Parametric Batch Execution with Checkpoint Resume**: `run_parametric_simulation(...)` now supports large campaigns using incremental batches and crash-safe resume.
  - Added `batch_size`, `checkpoint_every_batch`, and `resume_from_checkpoint` arguments for memory-aware execution and recovery after interruptions.
  - Added deterministic task signatures and a default checkpoint artifact (`outputs_param_simulation_checkpoint_latest.pkl` + metadata JSON) in the run output directory.
  - Added focused tests in `tests/parametric_and_optimisation/test_parametric_batch_checkpoint.py` covering batch checkpoints, resume behavior, validation, and explicit missing-checkpoint errors.
- **Interactive Parametric Preflight Diagnostics**: Added `preflight_report(...)` and `preflight_report_parametric(...)` to validate simulation plans before launching heavy runs.
  - Reports missing required input columns, null counts, unknown IDF/EPW labels, duplicate task signatures, and estimated total simulations.
  - Provides conservative recommendations for `processes` and `batch_size` using a lightweight system CPU/RAM snapshot.
  - Added tests in `tests/parametric_and_optimisation/test_parametric_preflight_report.py` for task estimation, validation checks, and wrapper behavior.
- **Optimisation Case Checkpoint Resume**: `run_optimisation(...)` now supports case-level recovery for long multi-IDF/multi-EPW campaigns.
  - Added `checkpoint_every_case` and `resume_from_checkpoint` arguments.
  - Added a default checkpoint artifact (`outputs_optimisation_checkpoint_latest.pkl` + metadata JSON) and automatic reuse of completed `IDF::EPW` cases.
  - Added a run-configuration compatibility signature in checkpoint metadata so incompatible checkpoints are skipped safely.
  - Added tests in `tests/parametric_and_optimisation/test_optimisation_checkpoint_resume.py` for checkpoint reuse and memory-mode behavior.
- **Interactive Optimisation Preflight Diagnostics**: Added `preflight_report_optimisation(...)` and expanded `preflight_report(...)` to support `mode='optimisation'` and auto-selection.
  - Reports case count, generations, estimated simulations, CPU/RAM snapshot, and conservative run kwargs including checkpoint-resume defaults.
  - Added tests in `tests/parametric_and_optimisation/test_optimisation_preflight_report.py` for estimation and wrapper mode routing.
- **Parametric Lazy Task Streaming and Atomic Checkpoints**: `run_parametric_simulation(...)` now iterates tasks lazily to reduce planning-memory pressure and writes checkpoints atomically (`.tmp` + replace).
  - Added a final checkpoint synchronization step when resuming, even if `checkpoint_every_batch=False`.
  - Extended tests in `tests/parametric_and_optimisation/test_parametric_batch_checkpoint.py` to verify refreshed checkpoints after resume.

### Changed
- **Breaking API Change in Output Discovery/Selection Returns**: `get_outputs_df_from_testsim(...)`, `discover_available_outputs(...)`, and `select_outputs(...)` now return a single dictionary instead of tuples.
  - New contracts are:
    - `get_outputs_df_from_testsim(...) -> {'meters': DataFrame, 'variables': DataFrame}`
    - `discover_available_outputs(...) -> {'meters': DataFrame, 'variables': DataFrame, 'meta': dict}`
    - `select_outputs(...) -> {'meters': DataFrame, 'variables': DataFrame, 'report': dict}`
  - Internal consumers, tests, and notebook workflows were updated to stop tuple unpacking and read values by explicit keys.
- **Floor Area Mode Semantics**: `mode='occupied'` remains strictly tied to `People` objects and their referenced `ZoneList`, `SpaceList`, or `Space` hierarchy. Use `mode='air-conditioned'` when normalisation should include all conditioned zones instead of only occupied zones.
- **SetAST EMS Program Refactoring**: Extracted the monolithic `SetAST` conditional block into a modular injection system. Generated EnergyPlus `SetAST` EMS program blocks are now much smaller and resolve model-specific comfort logic dynamically during IDF generation.
- **BESOS-style Parametric Flexibility**: `OptimParamSimulation` can now run without ACCIM-specific parameters, allowing generic BESOS parameters or zero internal parameters.
- **Top-Level Parametric Parallelization**: `run_parametric_simulation` now evaluates iterations across all EPW and IDF combinations via `concurrent.futures.ProcessPoolExecutor`.
- **Optimisation Storage Management**: Replaced the legacy `keep_dirs` argument with `keep_sim_files`, `keep_sim_files_batch_size`, and `keep_df`, enabling batch cleanup and memory-efficient final DataFrames.
- **Unified Object Identification**: Centralized hierarchy resolution for `People`, `Space`, `SpaceList`, and `ZoneList` objects through `accim.sim.utils.scan_zones`.
- **Optimisation Plotting and Clustering**: Improved Pareto-front plotting aesthetics and persisted `Cluster_ID` back into optimisation outputs for downstream plots.
- **File Naming and Timestamping**: Standardized output dataframe, JSON state, and IDF backup names with chronological `YYYYMMDD_HHMMSS` timestamps.
- **Explicit Parametric and Optimisation API Signatures**: Replaced public `*args`/`**kwargs` signatures in `parametric_and_optimisation` classes and methods with named arguments and expanded docstrings for clearer IDE hover help, while preserving the legacy `building` alias and routing algorithm-specific options through `algorithm_options`.
- **Output Workflow Defaults and Migration Path**:
  - `apply_outputs_preflight(...)` now defaults to `clean_mode='none'` to preserve user-defined `Output:*` objects unless cleanup is explicitly requested.
  - Legacy methods `set_output_var_df_to_idf(...)` and `set_output_met_objects_to_idf(...)` are preserved as wrappers and now emit `DeprecationWarning` messages that point to the new consistent methods.
  - Updated `tools/output_workflow_notebook_style.py` to use the new API and include the advanced meter DataFrame frequency path.
- **Notebook 14 Multi-IDF Workflow (without loop)**: Updated `14_main_optimisationsimulation_accim_custom_model_without_idf_loop.ipynb` to run a single `OptimisationSimulation` instance with `buildings=[...]` and explicit Pareto controls.
  - Step 2 now avoids per-IDF instantiation loops and prepares IDFs once before creating the optimisation object.
  - Step 3 now plots from one combined optimisation object and forwards the selected MCDM segmentation flags.

### Fixed
- **Output Preflight Variable Verification in ACCIM Models**: `get_output_var_df_from_idf` now reads `Output:Variable` objects directly from the current IDF state (side-effect free), preventing false `missing_in_idf` reports after `apply_outputs_preflight(...)`.
- **`run_optimisation()` Return Value**: Restored the method return so it consistently returns the full optimisation `DataFrame` (`self.outputs_optimisation`) instead of `None`, fixing downstream errors like `TypeError: object of type 'NoneType' has no len()`.
- **Consistent Simulation Returns**: `run_parametric_simulation()` and `run_optimisation()` now consistently return their result DataFrames (`self.outputs_param_simulation` and `self.outputs_optimisation`) so downstream code can safely use `len(...)` and chaining without receiving `None`.
- **Temporary `available_outputs` Cleanup Control**: Output-discovery workflows now clean up the generated `available_outputs` folder by default, with a new opt-in flag (`keep_available_outputs=True`) to keep it when users need to inspect `rdd/mdd` artifacts.
- **Python 3.9 Type Union Syntax in `_run_single_evaluation_worker`**: Replaced `list | None` (Python 3.10+ syntax) with `Optional[list]` in `main.py` to restore Python 3.9 compatibility.
- **Matplotlib 3.9+ `cm.get_cmap()` Removal**: Replaced the removed `cm.get_cmap('coolwarm')` call in `plotting.py` with `plt.colormaps['coolwarm']` and a safe fallback for older Matplotlib versions.
- **`estimate_optimisation_sims()` Copy-Paste Bug**: The method erroneously accessed `self.outputs_param_simulation` (only set after a parametric run) and set `last_run_type` to `'parametric'`. Fixed to use the `epws` argument directly and set `last_run_type = 'optimisation'`.
- **Chained Comparison Logic Bug in `drop_invalid_param_combinations`**: The condition `MinTempDiffVOF >= MaxTempDiffVOF <= 0` in `param_accis.py` was always False (since `MaxTempDiffVOF` is validated to be positive), silently skipping invalid parameter combinations. Simplified to `MinTempDiffVOF >= MaxTempDiffVOF`.
- **`KeyError: 'reporting_frequency'` in `takeOutputDataFrame`**: The new `select_outputs()` / `apply_outputs_preflight()` workflow produces DataFrames with a `'frequency'` column, while `takeOutputDataFrame` in `accim_Base_EMS.py` expected `'reporting_frequency'`. Added an automatic column rename for backward compatibility.
- **aPMV Parametric Setters in E+ 25.2**: Added compatibility with modern `People` schemas that use `Zone_or_ZoneList_or_Space_or_SpaceList_Name`.
- **aPMV Parametric Worker `IndexError` in OSM/Space-based Models**: Replaced fragile `People`-derived name matching with robust discovery of real EMS targets.
- **Thermal Comfort Thermostat Wiring for Existing OSM Controls**: Existing thermal comfort thermostats now update the actively referenced Fanger setpoint object and guarantee a valid thermal comfort control type schedule.
- **DualSetPointWithDeadBand Fatal Error**: Corrected EMS Calling Manager sequencing so foundational variables are initialized before `SetAST` is evaluated.
- **Custom ACCIS Parameters in Parametric Multiprocessing**: Worker-local IDFs now receive sampled row-level parameter writes before EnergyPlus evaluation.
- **`set_parameters(use_dflt_values=True)` in Custom ACCIS Models**: Default `CustAST` values are now physically written into the IDF/EMS.
- **EPW/IDF Category Name Collision**: `apply_category_mapping` now detects conflicting EPW and IDF category names and renames conflicting EPW categories with an `epw_` prefix.
- **Boxplot Highlight Legend Placement**: Highlight handles now merge into the figure-level legend instead of overlapping the first subplot.
- **Multi-IDF Session Restore for `set_building_floor_area`**: `idf_backup_path` lists are now loaded correctly when restoring multi-IDF runs.
- **Normalization with Scalar Area**: `normalize_outputs` now handles scalar `building_floor_area` values from `mode='custom'`.
- **Category Mapping Persistence**: Mapping rules are now stored in dataframe metadata and restored when loading parametric or optimisation outputs.
- **Zero-input BESOS Compatibility**: Parametric runs now work when the BESOS problem has no native inputs and only external routing such as `idf`.
- **Python 3.9 Type Hint Compatibility**: Relaxed internal `IDF_class` annotations for environments where `besos.IDF_class` resolves as a module.
- **NSGA-II Pareto Status Annotation**: Pareto status is recomputed from the full evaluation history instead of matching only the final optimizer population.
- **Pandas Groupby Compatibility**: Avoided unstable `groupby().apply()` shapes when annotating Pareto status.
- **Legacy Object Conflicts**: Removed duplicate dummy `People` injection for `ZONELIST` configurations.
- **EMS Occupant Count Sensor Key**: EMS sensors now resolve the exact internal EnergyPlus occupant-count key.
- **EMS Coil Variable Initialization**: ExistingHVAC mixed-mode coil variables are initialized safely before timestep prediction logic.
- **Accis Simulation Spillage Error**: `genIDF` now skips stale or orphaned temporary `_pymod.idf` files.
- **Dangling Working Directories in Optimisations**: `keep_sim_files='none'` now removes remaining worker execution folders.
- **Problem Setup Overwrite Bug**: Loading outputs no longer overwrites pre-configured BESOS `EPProblem` instances with static mock stubs.
- **Session Context Persistence (`epws`)**: Original EPW lists are now persisted in JSON/Pickle metadata.
- **Normalization Plotting Artifacts**: Fixed divisor handling and `parameters_type` parsing errors in normalization-aware plotting.
- **Parametric Multiprocessing Output Readers**: Workers now preserve serialized meter/variable reader specifications, including frequency and aggregation behavior.
- **Output Deduplication Across IDF Key Casing**: Output scanning/insertion now resolves `Output:*` object keys robustly across casing variants (for example, `Output:Meter` vs `OUTPUT:METER`), preventing missed duplicate detection in mixed IDD environments.
- **aPMV Output Re-application Duplicates**: `_add_apmv_outputs(...)` now checks full `Output:Variable` keys (`Key_Value`, `Variable_Name`, `Reporting_Frequency`) before insertion, including `Schedule Value` rows.
- **Parametric `add_outputs` Visibility in Multiprocessing**: `run_parametric_simulation(...)` now reconstructs and evaluates BESOS `add_outputs` readers in worker processes, so callable-derived columns are persisted in `outputs_param_simulation`/`outputs_param_sim`.
- **Optimisation `add_outputs` Persistence in Worker Logs**: Patched BESOS evaluation records now include `add_outputs_values` in JSONL logs, improving reconstruction of full optimisation histories.
- **MCDM Output-Column Resolution in Optimisation Analysis**: `get_best_compromise_solution()` now resolves output columns against available dataframe names before indexing, avoiding `KeyError` when stored column labels differ from canonical output names.
- **EPW-Specific Sensitivity Output Paths**: `run_sensitivity_analysis_by_epw()` now sanitizes EPW labels (including full paths and `.epw` suffixes) before using them in directory/file names, preventing invalid path errors during result export.
- **Optimisation Execution per EPW in Multi-IDF Runs**: `run_optimisation()` now executes the selected algorithm inside the `EPW` loop for each `IDF × EPW` pair, fixing cases where only the last EPW was effectively optimized.
- **Configurable Pareto/MCDM Segmentation Across IDF and EPW**:
  - Added `pareto_separate_by_epw` and `pareto_separate_by_idf` to `run_optimisation(...)`, persisted in output `attrs`.
  - `_annotate_pareto_status(...)` now supports explicit grouping columns instead of hardcoding EPW-only behavior.
  - `plot_best_compromise_solutions(...)` now accepts `separate_by_epw` and `separate_by_idf` (defaulting from optimisation `attrs`) to avoid unintended cross-IDF or cross-EPW mixing.

## [0.7.7] - 2026-04-11


### Fixed
- **Numpy 2.0+ Compatibility Bug**: Fixed an issue where building names and EnergyPlus EMS program line overrides were unintentionally injected with the numeric wrapper string `np.float64(...)` by safely replacing `repr()` instances with `str()` in parameter representations.
- **Python 3.14 SyntaxWarnings**: Resolved invalid escape sequence warnings (`\E`) inside `accim/utils.py` by sanitizing internal paths to adopt forward slashes syntax.

### Changed
- **Dependencies Relaxation**: Lifted the ceiling on `numpy` (`<2.0.0`) and `matplotlib` (`<=3.7`) dependencies inside `setup.py` to fully support and adapt to the latest environment setups. 
- **Python Version Definition**: Lifted maximum python support limitations (updated `python_requires` to `>=3.9` from `<3.10`). `accim` now officially scales alongside newer releases of Python and core packages like `eppy`.


## [0.7.6] - 2025-12-16

### Added
- **Robust ESO Results Parsing**: Added `read_eso_using_readvarseso` to `accim.utils`.
  - Uses the native EnergyPlus `ReadVarsESO` utility for 100% format compatibility.
  - Automatically separates data by reporting frequency (Hourly, Monthly, Timestep).
  - Generates metadata tables (Report Type, Area, Units) replicating DesignBuilder/ResultsViewer structure.
  - Intelligently filters out Design Days and Sizing Periods to return only the RunPeriod data.
- **Variable Key Pattern Identification**: Added `identify_variable_key_pattern` to `accim.utils`.
  - Automatically detects the naming convention (Key Index) used by EnergyPlus for specific report variables (e.g., returns placeholders like `[Zone Name]`, `[Space Name] [People Name]`, or `[Schedule Name]`).
  - Executes a rapid micro-simulation (1 day, minimal shadowing) to generate actual output keys.
  - Implements a robust two-level search strategy:
    1. **Direct Object Match**: Scans raw IDF fields to match keys against any object name (VRF, Schedules, Coils), ignoring specific IDD field names.
    2. **Hierarchy Match**: Analyzes Zone/Space/People relationships, supporting both modern (E+ 9.6+) and legacy hierarchies.
  - Handles variables with multiple keys and prioritizes specific object matches over global environment variables.
- **PMV Parameter Management**: Added `set_pmv_input_parameters` to `apmv_setpoints`.
  - Allows bulk modification of `People` objects (Activity Level, Clothing Insulation, Air Velocity, Work Efficiency).
  - Automatically creates and assigns the necessary `Schedule:Compact` objects.
  - Supports global values (float) or zone-specific values (dictionary).
- **Model Introspection Tools** in `accim.utils`:
  - `get_idf_hierarchy`: Extracts the relationship between Zones, Spaces, ZoneLists, and SpaceLists.
  - `get_people_hierarchy`: Resolves exactly which spaces are affected by specific `People` objects.
  - `get_available_target_names` and `get_input_template_dictionary`: Helpers to assist users in configuring simulation dictionaries with valid keys.
- **EMS Debugging**: Added `add_ems_debug_output` helper to easily enable Verbose EMS reporting in the `.edd` file.
- **Automatic Metering**: `apply_apmv_setpoints` now automatically adds `Output:Meter` objects for `EnergyTransfer:HVAC` and `Electricity:HVAC`.

### Changed
- **Major Refactor of `apply_apmv_setpoints`**:
  - **Unified Version Support**: Removed separate logic paths for legacy (< v23.1) and modern EnergyPlus versions. The code now dynamically detects the model structure.
  - **Hierarchy Resolution**: Implemented a strict 3-level priority logic (`Space/SpaceList` > `ZoneList` > `Zone`) to correctly identify EMS control targets.
  - **Dictionary Inputs**: Arguments like `adap_coeff_cooling` or `pmv_cooling_sp` now accept dictionaries, allowing different values for specific zones or spaces.
- **Infrastructure Generation**: The creation of Schedules and Thermostats is now smarter. It checks for existing objects and updates or replaces them (e.g., converting a standard DualSetpoint thermostat to a ThermalComfort one) without creating duplicates.
- **User Feedback**: Standardized `verbose_mode` across functions. Success messages are optional, but warnings for conflicts (e.g., duplicate objects) are now always displayed.

### Fixed
- **EMS Naming Issues**: Fixed `Invalid variable name` errors in EnergyPlus. A new sanitization function replaces invalid characters (hyphens, dots, spaces, parentheses) with underscores in EMS variable names.
- **EMS Sensor Mapping**: Fixed a critical bug where EMS Sensors pointed to the original `People` object name instead of the internal instance name generated by EnergyPlus when using `ZoneList` or `SpaceList`.
- **BESOS Compatibility**: Fixed runtime crashes when reading `.eso` files containing empty units `[]`, duplicate keys, or trailing schedule names. This is handled via a robust "Monkey Patch" applied automatically to `besos.objectives.read_eso`.

## [0.7.5] - 2024-05-22

### Added
- **New Parametric Simulation and Optimization module (`parametric_and_optimisation`)**. This is the main feature of this release, adding powerful new capabilities to the package.
  - Allows running parametric simulations by varying a wide range of `accim` inputs.
  - Includes the ability to define optimization problems to find optimal parameters based on user-defined objectives.
  - Integrates with the `besos` library for executing optimization algorithms.
  - New classes and functions have been added to manage parameters, objectives, and simulation runs.

### Changed
- The internal project structure has been updated to accommodate the new module.

## [0.7.4] and earlier

A detailed changelog for versions prior to 0.7.5 was not formally maintained in this file.

---
[Unreleased]: https://github.com/dsanchez-garcia/accim/compare/v0.7.7...HEAD
[0.7.7]: https://github.com/dsanchez-garcia/accim/compare/v0.7.6...v0.7.7
[0.7.6]: https://github.com/dsanchez-garcia/accim/compare/v0.7.5...v0.7.6
[0.7.5]: https://github.com/dsanchez-garcia/accim/releases/tag/v0.7.5
