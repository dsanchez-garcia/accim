# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.8] - 2026-04-18

### Added
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
- **Simulation Workflow Safeguards**: Added robust contextual tracking (`last_run_type`) to `OptimParamSimulation` to natively enforce correct analytical sequencing. All post-simulation analysis methods (such as `plot_best_compromise_solutions`, `run_sensitivity_analysis`) now validate the executed simulation context, raising `ValueError` exceptions immediately if applied to incompatible data types (e.g. attempting to run sensitivity analysis over NSGA-II populations).

### Changed
- **Optimisation Memory and Disk Usage Management**: Completely overhauled how the `OptimParamSimulation.run_optimisation` method manages raw simulation outputs. The legacy `keep_dirs` argument was removed in favor of `keep_sim_files`, `keep_sim_files_batch_size`, and `keep_df`. This enables "on-the-fly" batch cleanups of dominated simulation results during the optimization loop (reducing peak disk storage required for massive optimizations) and allows memory-efficient final DataFrames by selectively discarding dominated solutions. Furthermore, `get_hourly_df_optimisation` now gracefully ignores missing/deleted simulation directories natively instead of failing.
- **Unified Object Identification**: Globalized the robust hierarchy resolution logic from `apmv_setpoints._resolve_targets` into the central pipeline (`accim.sim.utils.scan_zones`). The overarching dataset map is meticulously managed across all hierarchical relationships for `People`, `Space`, `SpaceList`, and `ZoneList` objects universally without duplicate clashes.
- **Optimisation Plot Aesthetics & Clustering Integrity**: Upgraded the `plot_pareto_front` method to output publication-ready visualizations supporting `RdYlGn` colormaps (via `color_by`), dynamic scatter sizes (via `size_by`), and representative legend handles, additionally auto-encoding configurations into filenames to prevent overwriting. Furthermore, `run_clustering` now natively persists its generated `Cluster_ID` column directly back to the `outputs_optimisation` object so subsequent analytical plots can seamlessly access it without requiring manual DataFrame merges.

### Fixed
- **NSGA-II Pareto Status Annotation**: Fixed a bug in `OptimParamSimulation` where non-dominated points from earlier generations were incorrectly marked as dominated (`False`) due to strict matching against only the final optimizer population. The logic has been rewritten to deterministically recompute the Pareto front from scratch using the objective values across the full evaluation history, grouped by EPW.
- **Pandas Groupby Compatibility**: Resolved a `ValueError` (`Cannot set a DataFrame with multiple columns to the single column pareto-optimal`) triggered in Pandas 2.2+ by refactoring the `_annotate_pareto_status` method to use an explicit iterative grouping approach, completely bypassing unstable `groupby().apply()` DataFrame return shape variations.
- **Legacy Object Conflicts**: Eliminated an unstable hack inside `accim.sim.accim_Base` where duplicate dummy `People` objects were injected whenever it encountered `ZONELIST` configurations, thereby securing EnergyPlus engine safety.
- **EMS Occupant Count Sensor Key**: Fixed a bug in `addEMSSensorsBase` where the `People Occupant Count` sensor was built with a hardcoded `'People ' + zonename` key. The sensor now correctly resolves the exact internal EnergyPlus key from the model hierarchy (e.g. `SpaceName PeopleName`), preventing fatal EMS sensor errors during simulation.
- **EMS Coil Variable Initialization**: Resolved fatal EnergyPlus initialization array crashes (`Variable ... used in expression has not been initialized!`) in mixed-mode ExistingHVAC (`ex_mm`) simulations. Realigned EMS code injection to map coil variables to `ems_objs_name` and safely spawn a `BeginNewEnvironment` initialization program (`InitExisHVACCoils`) to explicitly pre-initialize actuator nodes to `0` prior to any timestep prediction executions.
- **Accis Simulation Spillage Error**: Resolved an `IndexError` raised during the batch-creation of IDFs under the internal `genIDF` utility in `accim.sim.accis`. The model-loop has been robustified so it actively maps newly generated instance IDFs natively to memory, safely skipping stale or orphaned temporary `_pymod.idf` files left over physically on the drive by previous crashes.
- **Dangling Working Directories in Optimisations**: Fixed a file spillage bug inside `run_optimisation` where using `keep_sim_files='none'` correctly stripped EnergyPlus results from DataFrames but left the base worker execution folders (`out_dir_{pid}`) physically present on the disk containing the last evaluated step. These are now forcefully purged as intended.

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