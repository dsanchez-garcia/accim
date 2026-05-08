# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.8] - 2026-04-18

### Changed
- **SetAST EMS Program Refactoring**: Extracted the monolithic 2200-line `SetAST` conditional block into a modular injection system. The internal `get_SetAST_lines` function now resolves model-specific comfort logic dynamically during IDF generation, achieving a ~98% reduction in the size of the generated EnergyPlus `SetAST` EMS program block (from ~2200 lines to ~38 lines per IDF), dramatically speeding up simulations and reducing file footprint.
- **Simulation Input Traceability (`in.idf`)**: Parametric and optimisation workflows now preserve the exact IDF that BESOS/EnergyPlus actually executes (the transient `in.idf` generated in BESOS temporary worker folders) inside each simulation result directory. This is implemented by an internal runtime patch of `besos.eplus_funcs.run_energyplus` that copies the incoming `building_path` to `<simulation_output_dir>/in.idf` before invoking EnergyPlus.
  - The patch is idempotent, so it is only applied once per process and remains safe under multiprocessing contexts.
  - Coverage now includes both execution paths: top-level parametric workers and optimisation evaluations routed through the Platypus bridge.
  - This improves reproducibility/auditability by allowing direct inspection of the exact EMS/program state tied to each simulation output folder.
- **Outputs Preflight Workflow (`parametric_and_optimisation`)**: Added a new pre-simulation workflow to discover real outputs, validate user selections, clean stale output objects, and apply verified output requests before running simulations.
  - Added `discover_available_outputs(...)` to discover outputs via lightweight test simulation (`get_outputs_df_from_testsim`) with optional fallback to `available_outputs/eplusout.rdd|mdd`.
  - Added `select_outputs(...)` to support both wishlist-first and dataframe-first selection, including strict validation, missing-output handling (`raise|warn|ignore`), and close-match suggestions.
  - Added `clear_outputs(...)` and `apply_outputs_preflight(...)` to provide explicit preflight cleaning and orchestration, with post-apply verification against current IDF output objects.
  - `clear_outputs(mode='all')` now preserves `OUTPUTCONTROL:FILES` by design and never removes it.

### Fixed
- **aPMV Parametric Setters in E+ 25.2 (`People` field compatibility)**: Fixed `BadEPFieldError: unable to find field Zone_or_ZoneList_Name` in `parametric_and_optimisation` setters by adding compatibility with both legacy and modern `People` schemas (`Zone_or_ZoneList_Name` and `Zone_or_ZoneList_or_Space_or_SpaceList_Name`).
- **aPMV Parametric Worker `IndexError` in OSM/Space-based models**: Fixed `IndexError: list index out of range` during multiprocessing parametric runs by replacing fragile `People`-derived name matching with robust discovery of real EMS targets from existing `set_zone_input_data_*` program names.
- **Thermal Comfort Thermostat Wiring for Existing OSM Controls**: Fixed a control-link bug where existing `ZoneControl:Thermostat:ThermalComfort` objects could keep pointing to pre-existing Fanger setpoint objects while `apply_apmv_setpoints` updated a different object. The routine now updates the actively referenced Fanger object and guarantees a valid thermal comfort control type schedule, restoring real HVAC energy sensitivity to aPMV parametric setpoint changes.
- **DualSetPointWithDeadBand Fatal Error**: Resolved a deep-seated initialization bug causing EnergyPlus to crash during warmup when processing certain IDFs. The bug was caused by a sequential misalignment of EMS Calling Managers where `SetAST` was evaluated before foundational variables (`ComfStand`, `ACSToffset`, `ACSTtol`) were initialized by `SetInputData` and `ApplyCAT`. We implemented a robust dependency-sorting system within `accim_Base_EMS.py` to correctly sequence the Calling Managers (`priority_programs`), ensuring all offsets and limits are populated successfully prior to setpoint prediction sequences.
- **Custom ACCIS Parameters Not Applied in Parametric Multiprocessing**: Fixed a regression in `run_parametric_simulation` where row-level sampled parameters (notably `CustAST_m`, `CustAST_n`, `CustAST_ASToffset`, `CustAST_ASTall`, `CustAST_ASTaul`) could be silently ignored in multiprocessing runs.
  - Root cause: worker processes rebuilt a lightweight evaluation problem with placeholder inputs that did not guarantee EMS setter side effects.
  - Resolution: each worker now applies the corresponding parameter setter functions directly to the worker-local IDF using the sampled row values before launching the EnergyPlus evaluation.
  - Result: sampled `set_parameters(...)` values are now effectively propagated into EMS programs for each simulated case.
- **`set_parameters(use_dflt_values=True)` in Custom ACCIS Models**: Fixed a logic gap where fallback `CustAST` defaults were reported to the user but not physically injected into the IDF/EMS.
  - The default branch now performs the same concrete `modify_CustAST_*` writes as the interactive/manual branch.
  - This prevents zero-valued placeholder parameters from leaking into runtime when users intentionally rely on automatic defaults.
- **Categorical Energy Boxplots**: Introduced the `OptimParamSimulation.plot_categorical_boxplots()` method to effortlessly visualize simulation energy distributions (Heating and Cooling electricity) within FacetGrid boxplots. This method natively aggregates dual energy scales into a shared plot space using `pd.melt()`. It fully supports dimensional breakdowns across plot rows (`row`), columns (`col`), and colors (`hue`) based on robust category mapping rules. Includes native support to toggle Y-axis sharing (`sharey`) and underlying data point overlays (`show_points`).
- **Boxplot Highlight Overlays**: Integrated `highlight_dict` capabilities directly into `plot_categorical_boxplots()` allowing users to accurately overlay distinct, marker-styled simulations (like Specific historical `met` datasets or `tmy` weather models) directly on top of grouped Seaborn distributions without layout displacement.
- **Multi-IDF Parametric Validation Script**: Added `check_parametric_multiple_idfs.py` to exercise `OptimParamSimulation` with multiple IDFs and per-row EPW assignments without modifying the original IDF files.
- **`sampling_custom` Method**: Added `OptimParamSimulation.sampling_custom()` to define custom (non-cartesian) simulation plans intuitively. Accepts a list of dicts (e.g. `[{'idf': 'A', 'epw': 'seville.epw'}]`) or a dict mapping IDFs to one or more EPWs (e.g. `{'BuildingA': 'seville.epw', 'BuildingB': ['madrid_2024.epw', 'madrid_2025.epw']}`), or a pandas DataFrame directly.
- **`get_monthly_df` and `get_monthly_df_optimisation` Methods**: Added monthly aggregation methods for parametric and optimisation workflows respectively. Each method reads hourly data (automatically calling `get_hourly_df` / `get_hourly_df_optimisation` if needed) and aggregates to monthly periods. Default aggregation is `'sum'` for energy-type variables and `'mean'` for temperature, PMV, PPD, rate, and coefficient variables. Users can override any column's aggregation via the `agg_funcs` dict argument.
- **Automatic Hourly CSV Extraction in `get_hourly_df`**: When `outputs_param_simulation` does not already contain hourly list columns (i.e. outputs were configured as aggregate scalars), `get_hourly_df` now automatically falls back to reading the hourly data directly from the EnergyPlus CSV output files.
- **Automated Category Mapping**: Added `set_category_mapping`, `apply_category_mapping` and `preview_category_mapping` to support robust keyword-based mapping logic directly onto EPW and IDF names for advanced filtering and data aggregation workflows.
- **Parametric and Optimisation Area Normalization**: Upgraded energy normalisation capabilities to fully support multi-building (`idf`) simulations. 
  - `set_building_floor_area` now calculates and maps areas for multiple IDFs simultaneously.
  - Added the `normalize_outputs()` method to forcefully convert energy results across all base, hourly, and monthly DataFrames to $kWh/m^2$ in-place.
  - Added the `normalize_per_m2` argument natively to all dataframe extraction methods (`get_hourly_df`, `get_monthly_df`, `get_hourly_df_optimisation`, `get_monthly_df_optimisation`).
  - Integrated a double-normalisation safeguard (`self.outputs_normalized`) that automatically prevents unintended scaling across analytical plotting workflows.
- **EMS Results Verification Utility**: Added `AccimSimulationVerifier` to `accim.utils`.
  - Replaces the former procedural function with a robust Object-Oriented class.
  - Reads an EnergyPlus simulation output (direct `.csv` parsing prioritize to bypass heavy `ReadVarsESO` operations) and verifies that the ACCIS EMS scripts injected by `AddAccis` operate correctly.
  - **Check 1 — HVAC Setpoint Adherence**: Verifies adaptive cooling (`ACST_Sch`) and heating (`AHST_Sch`) setpoint parameters natively. Features anti-bounce mask logic to mathematically pardon 1-timestep transient threshold shocks naturally occurring in simulations.
  - **Check 2 — Window Operation Logic**: Replicates the conditional logic of `SetWindowOperation_<windowname>`. Features dynamic parameter mapping directly from EMS evaluation series (`MinOutTemp` and `VST`) per-timestep instead of using static references.
  - **Intelligent Timestep Filtering**: Implements frequency-agnostic design-day stripping logic, automatically slicing simulation warmup buffers natively using `DatetimeIndex` logic.
  - **Leniency Models**: Integrates advanced 1-timestep window closing masks and mid-hour toggle aggregations (`open_transit`, `close_transit`) that mathematically excuse transition false positives inherently logged by EnergyPlus due to control lag or fractional overlapping in `Hourly` resolutions.
- **Operative Temperature Control Utility**: Added a new function `set_operative_temp_control` inside `accim.utils` that allows users to easily update IDFs to use operative temperature control by appending `ZoneControl:Thermostat:OperativeTemperature` configurations dynamically to all zone thermostats.
- **Global `update_idf_version` Utility**: Added an automated function inside `accim.utils.py` to seamlessly upgrade the defined EnergyPlus version of target IDF files.
- **Sizing Error Prevention**: Implemented automatic initialization of standard autosizing constraints within the `SimulationControl` object (via `setSimulationControlSizing` in `accim.sim.accim_Base`). This fully resolves strict EnergyPlus fatal sizing errors when modifying or autosizing components in exported skeleton environments.
- **Scheduled Natural Ventilation Support**: `accim` now supports mixed-mode simulations using `ZoneVentilation:WindandStackOpenArea` and `ZoneVentilation:DesignFlowRate` objects as an alternative to the Airflow Network (AFN). The ventilation type is automatically detected from the IDF:
  - If `AirflowNetwork:SimulationControl` is present, the existing AFN-based logic is used.
  - Otherwise, if `ZoneVentilation` objects are found for occupied zones, `Schedule:Constant` objects (named `Vent_Sch_{ZoneName}`) are automatically injected and linked to the ventilation objects.
  - EMS actuators target the `Schedule Value` of these schedules to modulate natural ventilation, preserving the full adaptive comfort control logic.
- **Ventilation Output Variables for Scheduled Mode**: When using scheduled natural ventilation, `Output:Variable` objects are automatically added for `Zone Ventilation Standard Density Air Change Rate` (ACH) and `Schedule Value` for each `Vent_Sch_` schedule, enabling direct verification of mixed-mode operation.
- **Optimisation Simulation Estimator**: Added `estimate_optimisation_sims()` method to `OptimParamSimulation` in `accim.parametric_and_optimisation.main`.
  - Calculates and prints the exact number of EnergyPlus simulations that `run_optimisation()` will execute before launching it, taking into account that NSGA-II (and other platypus algorithms) always complete a full generation before checking the `evaluations` stopping criterion.
  - Formula: `sims_per_epw = population_size × ⌈evaluations / population_size⌉`; `total = sims_per_epw × len(epws)`.
- **Parallel Evaluation in Optimisation**: Added `processes` parameter to `run_optimisation()` in `OptimParamSimulation`.
  - When `processes > 1`, uses `platypus.ProcessPoolEvaluator` to evaluate the individuals within each generation concurrently across the specified number of CPU cores.
  - The process pool is always safely closed via a `finally` block, even if an error occurs mid-run.
  - Default is `1` (sequential), preserving existing behaviour.
- **Sensitivity Analysis Integration**: Added internal support for Morris and Sobol sensitivity analysis natively using `SALib` via `sampling_sobol` and `sampling_morris`. To quickly deploy robust SA workflows per-EPW climate, the high-level method `run_sensitivity_analysis_by_epw` natively outputs bar-charts (`mu*` vs `sigma`, `S1` vs `ST`) and summaries inside a target directory automatically.
- **Multi-Criteria Decision Making (MCDM)**: Included automated detection of compromise optimal solutions (e.g., knee point and TOPSIS methods) from `outputs_optimisation`. The new `plot_best_compromise_solutions` enables users to instantly isolate and map ideal solutions atop per-EPW clustered Pareto-front scatter distributions using tailored weight combinations.
- **Session Resumption & State Persistence**: The `OptimParamSimulation` class now automatically generates `.pkl` and `.json` files alongside the standard `.csv` outputs at the end of both `run_optimisation` and `run_parametric_simulation` executions. This preserves simulation configuration metadata (e.g., parameters, outputs) directly inside the dataframe attributes.
- **Enhanced Load Methods**: `load_outputs_optimisation` and `load_outputs_parametric` have been upgraded to support `.pkl` and `.json` paths natively. Loading from these formats automatically reconstructs the internal problem object state, enabling instant post-processing analysis without requiring heavy `addAccis` reinjections.
- **IDF Backup Management**: Implemented automated backup routines that save the structural state of the IDF model (`accim_idf_backup_...`) within the simulation output directory. The exact backup path is serialized into the metadata of the output files and auto-loaded gracefully during downstream methods (e.g. `set_building_floor_area`) to prevent missing building references when resuming analytical sessions.
- **Energy Normalization**: Added `set_building_floor_area` to intelligently calculate or assign total building area (by all zones, occupied zones, custom list, or static value). Downstream analytical visualizations (`plot_pareto_front`, `run_robustness_analysis`, etc.) now feature `normalize_per_m2` arguments to auto-scale results into specific kWh/m2 metrics dynamically.
- **Optimisation Workflow Hourly Support**: The `get_hourly_df_columns` utility now natively supports optimisation contexts by scanning the first available EnergyPlus `.csv` simulation output directly.
- **Hourly Data Expansion API Overhaul**: Completely redesigned `get_hourly_df_optimisation` to provide intuitive, granular control over hourly data extraction. It replaces manual dataframe manipulation with high-level parameters (`only_pareto_optimal`, `epw_filter`, `simulation_indices`, `output_columns`). It also features automatic `start_date` extraction from EnergyPlus CSVs and an interactive `dry_run` size-estimation prompt to prevent memory saturation on massive expansion tasks.
- **Simulation Workflow Safeguards**: Added robust contextual tracking (`last_run_type`) to `OptimParamSimulation` to natively enforce correct analytical sequencing. All post-simulation analysis methods (such as `plot_best_compromise_solutions`, `run_sensitivity_analysis`) now validate the executed simulation context, raising `ValueError` exceptions immediately if applied to incompatible data types (e.g. attempting to run sensitivity analysis over NSGA-II populations).

### Changed
- **BESOS-style Parametric Flexibility**: `OptimParamSimulation` can now be configured without ACCIM-specific parameters, allowing workflows that bypass `addAccis`/`apply_apmv_setpoints` and rely on generic BESOS parameters or even zero internal parameters.
- **IDF as Explicit Input Variable**: Multi-building simulations now expose `idf` as an input-like variable in `outputs_param_simulation` and `outputs_optimisation`, preserving the selected model in the result tables and metadata.
- **Per-row EPW Routing for Multi-IDF Runs**: `run_parametric_simulation` now accepts an `epw` column in the input dataframe so users can define exact IDF/EPW combinations instead of always evaluating the full Cartesian product.
- **Top-Level Parametric Parallelization**: Refactored `run_parametric_simulation` to evaluate iterations via `concurrent.futures.ProcessPoolExecutor` across all EPW and IDF combos globally. Ensures multi-core `processes` execution speeds up non-cartesian parametric plans and 1-to-1 building-to-weather matrixes instead of bottlenecking inside `besos.evaluator.df_apply`.
- **Native Multiple IDFs & EPWs Integration**: The `OptimParamSimulation` class now natively accepts `buildings` (list of IDFs) and `epws` (list of climate files) in its constructor. All parameter sampling methods (like `sampling_full_set`, `sampling_lhs`, etc.) automatically compute and include the full combinations of IDFs and EPWs into the simulation plan without requiring manual DataFrame construction.
- **Optimisation Memory and Disk Usage Management**: Completely overhauled how the `OptimParamSimulation.run_optimisation` method manages raw simulation outputs. The legacy `keep_dirs` argument was removed in favor of `keep_sim_files`, `keep_sim_files_batch_size`, and `keep_df`. This enables "on-the-fly" batch cleanups of dominated simulation results during the optimization loop (reducing peak disk storage required for massive optimizations) and allows memory-efficient final DataFrames by selectively discarding dominated solutions. Furthermore, `get_hourly_df_optimisation` now gracefully ignores missing/deleted simulation directories natively instead of failing.
- **Unified Object Identification**: Globalized the robust hierarchy resolution logic from `apmv_setpoints._resolve_targets` into the central pipeline (`accim.sim.utils.scan_zones`). The overarching dataset map is meticulously managed across all hierarchical relationships for `People`, `Space`, `SpaceList`, and `ZoneList` objects universally without duplicate clashes.
- **Optimisation Plot Aesthetics & Clustering Integrity**: Upgraded the `plot_pareto_front` method to output publication-ready visualizations supporting `RdYlGn` colormaps (via `color_by`), dynamic scatter sizes (via `size_by`), and representative legend handles, additionally auto-encoding configurations into filenames to prevent overwriting. Furthermore, `run_clustering` now natively persists its generated `Cluster_ID` column directly back to the `outputs_optimisation` object so subsequent analytical plots can seamlessly access it without requiring manual DataFrame merges.
- **File Naming & Timestamping**: Hardened all internal naming conventions for output dataframes, json state files, and idf backups to use universally chronological timestamp suffixes (`YYYYMMDD_HHMMSS`) instead of transient system Process IDs, preventing file collisions in highly parallelized environments and improving readability.

### Fixed
- **Multi-IDF Session Restore – `set_building_floor_area(mode='occupied')`**: Fixed a `TypeError` thrown when `idf_backup_path` is a `list` (multi-IDF runs). The method now iterates over all valid backup paths and loads each IDF using `accim.utils.get_building`, correctly populating `self.buildings`.
- **Normalization with Scalar Area – `normalize_outputs`**: Fixed a `TypeError: 'float' object is not iterable` raised when `building_floor_area` is a single float (e.g., from `mode='custom'`). When `divisors` is a scalar, the division is applied element-wise via vectorized pandas operations instead of `zip`.
- **Category Mapping Persistence**: `apply_category_mapping` now embeds `epw_mapping_rules` and `idf_mapping_rules` inside `DataFrame.attrs` and silently overwrites the last `.pkl` on disk. `load_outputs_parametric` (and `load_outputs_optimisation`) automatically restore these rules when loading a pickle, so `set_category_mapping` does not need to be re-called after loading a session.
- **Zero-input BESOS Compatibility**: Added an internal fallback path so parametric runs still work when the BESOS problem has no native input parameters and only external routing such as `idf` is used.
- **Python 3.9 Type Hint Compatibility**: Relaxed internal `IDF_class` type annotations in `OptimParamSimulation` to avoid import-time failures in environments where `besos.IDF_class` resolves as a module rather than a concrete type.
- **NSGA-II Pareto Status Annotation**: Fixed a bug in `OptimParamSimulation` where non-dominated points from earlier generations were incorrectly marked as dominated (`False`) due to strict matching against only the final optimizer population. The logic has been rewritten to deterministically recompute the Pareto front from scratch using the objective values across the full evaluation history, grouped by EPW.
- **Pandas Groupby Compatibility**: Resolved a `ValueError` (`Cannot set a DataFrame with multiple columns to the single column pareto-optimal`) triggered in Pandas 2.2+ by refactoring the `_annotate_pareto_status` method to use an explicit iterative grouping approach, completely bypassing unstable `groupby().apply()` DataFrame return shape variations.
- **Legacy Object Conflicts**: Eliminated an unstable hack inside `accim.sim.accim_Base` where duplicate dummy `People` objects were injected whenever it encountered `ZONELIST` configurations, thereby securing EnergyPlus engine safety.
- **EMS Occupant Count Sensor Key**: Fixed a bug in `addEMSSensorsBase` where the `People Occupant Count` sensor was built with a hardcoded `'People ' + zonename` key. The sensor now correctly resolves the exact internal EnergyPlus key from the model hierarchy (e.g. `SpaceName PeopleName`), preventing fatal EMS sensor errors during simulation.
- **EMS Coil Variable Initialization**: Resolved fatal EnergyPlus initialization array crashes (`Variable ... used in expression has not been initialized!`) in mixed-mode ExistingHVAC (`ex_mm`) simulations. Realigned EMS code injection to map coil variables to `ems_objs_name` and safely spawn a `BeginNewEnvironment` initialization program (`InitExisHVACCoils`) to explicitly pre-initialize actuator nodes to `0` prior to any timestep prediction executions.
- **Accis Simulation Spillage Error**: Resolved an `IndexError` raised during the batch-creation of IDFs under the internal `genIDF` utility in `accim.sim.accis`. The model-loop has been robustified so it actively maps newly generated instance IDFs natively to memory, safely skipping stale or orphaned temporary `_pymod.idf` files left over physically on the drive by previous crashes.
- **Dangling Working Directories in Optimisations**: Fixed a file spillage bug inside `run_optimisation` where using `keep_sim_files='none'` correctly stripped EnergyPlus results from DataFrames but left the base worker execution folders (`out_dir_{pid}`) physically present on the disk containing the last evaluated step. These are now forcefully purged as intended.
- **Problem Setup Overwrite Bug**: Resolved a severe flaw where `load_outputs_optimisation` and `load_outputs_parametric` forcefully overwrote pre-configured, valid `besos.problem.EPProblem` instances with static `MockProblem` stubs. Users can now securely load legacy results into pre-defined simulation architectures to launch new executions (e.g. `run_robustness_analysis` or Morris sensitivity analysis).
- **Session Context Persistence (`epws`)**: Fixed an omission where the original climate files list (`epws`) was not passed down into the dataframe serialization properties. Metadata payloads (JSON/Pickle) now safely persist this array, preventing `NameError` exceptions downstream when post-processing scripts attempt to re-access the initial EPW context list organically.
- **Normalization Plotting Artifacts**: Fixed an `UnboundLocalError` linked to the variable `divisor` during normalization conversions and a `NoneType` attribute error when parsing `parameters_type` inside `plot_pareto_front` visualization executions.
- **Parametric Multiprocessing Output Readers (time-series support)**: Fixed a bug in `run_parametric_simulation` where worker processes reconstructed the `EPProblem` using only output names (strings), losing the original `MeterReader`/`VariableReader` configuration.
  - Workers now receive a serialized specification of the original readers, preserving their type (`meter` vs `variable`), frequency, and aggregation function (`func` / `_process`).
  - This ensures that advanced reducers like `return_time_series` continue to return full time-series in multiprocessing mode instead of silently collapsing to scalar aggregates.

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
[Unreleased]: https://github.com/dsanchez-garcia/accim/compare/v0.7.8...HEAD
[0.7.8]: https://github.com/dsanchez-garcia/accim/compare/v0.7.7...v0.7.8
[0.7.7]: https://github.com/dsanchez-garcia/accim/compare/v0.7.6...v0.7.7
[0.7.6]: https://github.com/dsanchez-garcia/accim/compare/v0.7.5...v0.7.6
[0.7.5]: https://github.com/dsanchez-garcia/accim/releases/tag/v0.7.5