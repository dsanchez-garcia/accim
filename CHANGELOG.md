# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Overview page of parametric simulation and optimisation** (`docs/source/parametric_and_optimisation.rst`): the documentation explains the module in prose before the notebooks: the questions each class answers, the steps of a study with short code examples (model, simulation object, outputs and readers, parameters, plan or objectives, run, analysis), the kinds of parameters, the sampling methods, where the results are saved, disk space, and where each topic is in the notebooks `00`-`10` and `wf1`-`wf5`. `hourly_plotting` and `filter_output_csvs` move to the same section.
- **Review of the documentation pages** against accim 0.7.8:
  - the landing page introduces accim and where to start;
  - Requirements: Python 3.9 or newer, and the version is shown (MyST did not replace `|version|`);
  - Quick tutorial: a runnable example instead of the outdated list of arguments;
  - Detailed use: current prompts, a table with every argument of `addAccis()` and its default, the zone resolver and `hvac_zone_map` of `ex_mm`, fixed links to the full list of setpoint temperatures, the current `runEp()`, and a new section on aPMV setpoints;
  - Troubleshooting: `geopy`, unsupported values of `EnergyPlus_version`, `update_idf_version()` and paths of 260 characters;
  - Citation: the aPMV article (2026) and the Zenodo DOI.
  - Sphinx: the API page of `accim.data.preprocessing` is generated again, table cells wrap, and the page titles include the version.
- **Documentation pages for the parametric and optimisation notebooks**: the documentation has a new section, "Parametric simulation and optimisation", with the workflows `wf1`-`wf5` and the tutorials `00`-`10` of `parametric_and_optimisation_examples`, as they ran with their default settings, with their tables and figures.
  - Read the Docs cannot run these notebooks (they need EnergyPlus). The new script `docs/prepare_parametric_notebooks.py` runs them in a working folder, and exports copies with their outputs to `docs/source/jupyter_notebooks/parametric_and_optimisation_examples`. On export it makes the paths relative, removes the progress bars, shortens long logs and scales the figures down.
  - `docs/source/conf.py` never runs notebooks (`nbsphinx_execute = 'never'`) and ignores `.ipynb_checkpoints` folders.
  - `docs/requirements.txt` adds IPython, which provides the syntax highlighting of the code cells.
  - Tutorials 05, 08 and 09 now show the figures they save.
- **Hourly analysis, comfort screening and hourly plots (`HourlyPlottingMixin`)**: `ParametricSimulation` and `OptimisationSimulation` inherit new methods that work on the hourly outputs already stored by the simulations, without simulating again (new module `accim.parametric_and_optimisation.hourly_plotting`, mixed into `PlottingMixin`).
  - `compute_hourly_indicators(...)` returns one row per evaluation, from the results table or the hourly dataframe: temperature statistics, hours above given temperatures, the share of hours and the degree-hours above, below and outside each category of an adaptive comfort model (`'EN16798-1'`, `'ASHRAE55'`, a dictionary or a function), energy totals, hourly peaks and the 99th percentile (in kWh, or kWh/m² with `normalize_per_m2=True`), heating/cooling/idle hours and a comfort outcome (`'meets'`, `'too warm'`, `'too cool'`). The running mean is taken from the outputs (`running_mean='auto'`), from another simulation with the same weather file, or calculated from the outdoor temperature or the EPW file. Results are stored in `self.hourly_indicators`.
  - Plotting methods: `plot_comfort_screening(...)` (energy against the share of hours outside a band, with tolerance line, lowest-energy evaluation within it, non-dominated evaluations and selected solutions), `plot_results_scatter_matrix(...)` (parameters, results and indicators with correlations, coloured scatter or density contours), `plot_hourly_heatmaps(...)`, `plot_hourly_period(...)` (periods chosen by date or automatically), `plot_hourly_binned_response(...)` (e.g. energy signatures), `plot_load_duration_curves(...)`, `plot_adaptive_comfort_chart(...)`, `plot_hourly_scatter_matrix(...)` and `plot_monthly_distributions(...)`. Variables are given by exact name or substring (several zones combined with `zone_aggregation`), groups by any column or combination of columns, with `*_labels`/`*_order`, `data_filter`, `out_dir`, `filename` and `filename_template`. Each method returns the figure with `saved_path` and a `summary` dataframe of the plotted numbers.
  - `get_hourly_series_by_epw(...)` and `attach_hourly_series_by_epw(...)` reuse weather-dependent hourly series (running mean, outdoor temperature) across simulations; module functions `adaptive_comfort_band`, `comfort_categories`, `read_epw_dry_bulb` and `running_mean_outdoor_temperature` (EN 16798-1 exponentially weighted mean or ASHRAE 55 simple mean) are exported by `accim.parametric_and_optimisation`.
  - Documentation in `docs/source/hourly_plotting.rst`; tests in `tests/parametric_and_optimisation/test_hourly_plotting_mixin.py`.
- **m-n filter for the custom adaptive model**: `set_mn_filter(...)` restricts `CustAST_m` and `CustAST_n` to the band of published linear adaptive comfort models. The slope m of the models is regressed on their intercept n, and two lines parallel to the regression line, through the models farthest above and below it, bound the band (a symmetric `offset`, e.g. 0.17, a `(lower, upper)` tuple or other `data` can be given). By default, the models are the 56 linear models collected by Yao et al. (2022), Building and Environment 217, 109020 (`accim.parametric_and_optimisation.mn_filter.review_models()`).
  - Parametric simulation: `sampling_lhs` draws `CustAST_m` and `CustAST_n` inside the band, uniformly over its area, so every sample is kept: the Latin hypercube is drawn on the unit square and mapped onto the band (`MNFilter.sample_inside`). With `mn_filter_mode='exclude'`, it draws them within their ranges and drops the pairs outside. `sampling_full_set`, `sampling_full_factorial` and `sampling_custom` drop the combinations outside the band (kept in `mn_filter_excluded_df`), and `run_parametric_simulation(...)` does not simulate them. Sobol and Morris samples are not filtered.
  - Optimisation: `run_optimisation(...)` maps the `CustAST_n` proposed by the algorithm onto the interval of n inside the band for the proposed `CustAST_m`, so every evaluated combination lies inside the band; the results show the simulated n. The filter is part of the resume signature.
  - The models of the review stay unchanged in `_REVIEW_MODELS`; `drop_models` leaves models out (row ids of `review_models()`, 0 to 55, or author labels such as `'Li et al. [61]'`) and `add_models` adds others (a DataFrame, dicts or `(m, n)` / `(author, year, mode, m, n)` tuples). The band, including the 'farthest' bounds, is fitted to the result. `MNFilter.models_table()` lists the models with their residual from the regression line.
  - `plot_mn_filter(...)` plots the models, the regression line, the inclusion interval and the included and excluded combinations; added models are purple diamonds and removed models grey crosses (`show_removed_models`). The confidence band of the regression uses a fixed bootstrap seed, so the figure is the same in every run.
  - Tests in `tests/parametric_and_optimisation/test_mn_filter.py`.
- **EnergyPlus path-length pre-flight warning**: `run_optimisation(...)` and `run_parametric_simulation(...)` now warn on Windows if `out_dir` is too long. EnergyPlus output paths are `<out_dir>\BESOS_Output_<pid>\<run id>\eplusout.*`, and EnergyPlus fails when one reaches 260 characters (`MAX_PATH`). It then stops with "EnergyPlus Terminated--Error(s) Detected" and writes no `eplusout.err`.
- **Optimisation progress reporting**: `run_optimisation(...)` now prints progress while simulations run (new argument `show_progress=True`). It shows a run header with the estimated total number of simulations, the start and end of each IDF/EPW case, and the start of each generation. After every finished simulation it prints the generation progress, case and overall counts, elapsed time and an approximate ETA. Totals are estimates (per case, the count of NSGA-II given by `estimate_optimisation_sims`) and are prefixed with `~`. Works with `processes=1` and with `processes>1`.
- **Filtered copies of per-simulation output CSVs**: Added `SimulationBase.filter_simulation_output_csvs(...)` (inherited by `ParametricSimulation` and `OptimisationSimulation`). It writes a copy of each `eplusout.csv` that keeps or drops selected columns, using exact or partial names. `Date/Time`, row/column order and raw values are preserved. Files are processed one at a time with optional `chunksize`, through temporary files and without overwriting existing files. The method returns a per-file report. By default it covers all session results, including every optimisation evaluation, and it also accepts explicit paths. Originals and session paths are left untouched, so no disk space is freed until the originals are removed. See `docs/source/filter_output_csvs.rst`.
- **Template-based Plot Filenames with Category Placeholders**: Added `filename_template` support across plotting helpers in `PlottingMixin` (hourly, parametric, categorical, Pareto/MCDM, pairwise, and radar workflows).
  - Filenames can be customized via `str.format(...)` placeholders, including category labels sourced from `epw_mapping_rules` and `idf_mapping_rules` when those columns are present in the filtered plotting DataFrame.
  - Added method-specific placeholders (for example, `epw_tag`, `x`, `y`, `y_var`, `kind`, `df_source`) and automatic `.png` suffix completion when omitted.
  - Added collision protection for multi-file plotting methods (`plot_parametric_lines`, `plot_parametric_distributions`, EPW-loop methods) to raise a clear error when a template resolves to duplicate output paths.
  - Expanded plotting docstrings with `filename_template` usage guidance and examples.
  - Added regression tests in `tests/parametric_and_optimisation/test_plotting_parametric_new_methods.py` and `tests/parametric_and_optimisation/test_plotting_hourly_methods.py`.
- **Configurable Subplot Ordering Across Plotting/Analysis**: Added a shared subplot-ordering API to control panel/facet order in plotting methods that use `FacetGrid`, `catplot`/`relplot`/`displot`, `PairGrid`, and `matplotlib` subplot grids.
  - Added common arguments with backward-compatible defaults: `subplot_order_mode=('auto'|'alphabetical'|'ascending'|'descending'|'custom')`, `subplot_order_custom`, and `subplot_order_case_sensitive`.
  - Added reusable helpers in `accim.parametric_and_optimisation.utils`: `resolve_subplot_order(...)` and `resolve_subplot_orders(...)`.
  - Integrated ordering support in subplot-producing methods of `PlottingMixin` (including hourly, parametric, categorical, MCDM, heatmap/contour/density, and pairwise matrix visualisations) and in `run_sensitivity_analysis_by_epw(...)` for output-panel ordering.
  - Added consistent validations and explicit errors for unsupported dimension requests, missing `custom` configuration for active dimensions, and invalid custom labels with available-value hints.
  - Added dedicated tests in `tests/parametric_and_optimisation/test_subplot_ordering.py` (unit + integration + error cases).
- **Transversal Data Filtering for Tables and Visualisation**: Added a shared row-filter API to include/exclude/query simulation outputs before building tables or plots.
  - Added reusable helper `apply_data_filter(...)` in `accim.parametric_and_optimisation.utils` with support for `include`, `exclude`, and `query` filters, case-sensitivity control, strict/non-strict missing-column behavior, and configurable empty-result handling.
  - Added `get_filtered_results_table(...)` in `PlottingMixin` to produce filtered DataFrames for tabular review/export.
  - Integrated filtering arguments across plotting methods (hourly, parametric, categorical, optimisation visualisations, and radar) and in `run_sensitivity_analysis_by_epw(...)`.
  - Added tests in `tests/parametric_and_optimisation/test_data_filtering_api.py` for helper behavior, table filtering, plotting integration, and error paths.
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
- **Constructor-Level Output Object Safeguards (`parametric_and_optimisation`)**: Simulation constructors now enforce essential output objects in each loaded IDF.
  - `ParametricSimulation` and `OptimisationSimulation` now ensure `OutputControl:Files` exists and sets `Output_CSV`, `Output_MTR`, and `Output_ESO` to `Yes`.
  - Added constructor argument `remove_output_tables` (default `True`) to `SimulationBase`, `ParametricSimulation`, `OptimisationSimulation`, and `AccimPredefModelsParamSim`.
  - When enabled, initialization removes `Output:Table:Monthly` and `Output:Table:Annual` objects from each IDF.
  - Added regression coverage in `tests/parametric_and_optimisation/10_test_outputs_preflight.py` for constructor enforcement and optional table-retention mode.
- **Category-Split Hourly Outputs and Multi-Frequency Aggregation**: Added output post-processing controls for variable CSV output schemas across IDFs.
  - `get_hourly_df_parametric(...)` / `get_hourly_df(...)` now accept `split_by` to return a dictionary of DataFrames grouped by category (e.g. `building_type`), with optional `drop_all_empty_output_columns=True` to remove all-empty output columns per group.
  - `get_hourly_df_optimisation(...)` now supports the same `split_by` dictionary workflow.
  - Added generic aggregation methods `get_output_df(...)` and `get_output_df_optimisation(...)` with `frequency=('daily'|'monthly'|'runperiod')`.
  - `get_monthly_df(...)` and `get_monthly_df_optimisation(...)` are kept as monthly wrappers for backward compatibility.
  - `OptimisationSimulation` now exposes unified method names (`get_hourly_df`, `get_output_df`, `get_monthly_df`, `get_daily_df`, `get_runperiod_df`) so post-processing calls can match `ParametricSimulation` naming.
  - Added convenience wrappers: `get_daily_df(...)`, `get_runperiod_df(...)`, `get_daily_df_optimisation(...)`, and `get_runperiod_df_optimisation(...)`.
  - Added support in `normalize_outputs(...)` for new aggregated DataFrames: `parametric_daily`, `parametric_runperiod`, `optimisation_daily`, and `optimisation_runperiod`.
  - Added regression coverage in `tests/parametric_and_optimisation/10_test_outputs_preflight.py` for category-split hourly outputs and daily/monthly/runperiod aggregation.
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
  - `set_output_meters_to_idf(...)` now supports `mode=('append'|'replace')`, matching the variable API: `replace` removes existing `Output:Meter` objects in the selected IDF scope before adding the requested meters.
  - Legacy wrapper `set_output_met_objects_to_idf(...)` now forwards the new `mode` argument for backward-compatible migration.
  - Added regression coverage in `tests/parametric_and_optimisation/10_test_outputs_preflight.py` for meter replacement behavior.
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
- **Project Tracking Workflow Files**: Added `DEVLOG.md`, `TODO.md`, and `ROADMAP.md` and documented the workflow in `README.md` to separate release notes, completed work logs, active tasks, and longer-term planning.
- **Operations Tooling for Notebooks and Campaign Runs**: Added helper scripts under `tools/` for custom output reducers, robust custom-plan parametric execution, batch notebook execution, and reruns of failed notebooks.
- **Smoke/Resume Validation Tooling**: Added `tools/smoke_resume_runner.py` plus quick guides (`tools/README_smoke_resume_runner.md`, `tools/CHECKLIST_smoke_resume.md`) to validate checkpoint-resume behavior and `accim_results_root` routing with small test campaigns.
- **Regression Coverage for Optimisation Output Handling**: Added focused tests in `tests/parametric_and_optimisation/test_analysis_output_resolution.py` and `tests/parametric_and_optimisation/test_pareto_grouping.py`.
  - Covers robust objective-column resolution when optimisation outputs are normalized/renamed.
  - Covers configurable Pareto grouping by EPW and/or IDF and MCDM grouping behavior in plotting.
- **Parametric Batch Execution with Checkpoint Resume**: `run_parametric_simulation(...)` now supports large campaigns using incremental batches and crash-safe resume.
  - Added `batch_size`, `checkpoint_every_batch`, and `resume_from_checkpoint` arguments for memory-aware execution and recovery after interruptions.
  - Added deterministic task signatures and a default checkpoint artifact (`outputs_param_simulation_checkpoint_latest.pkl` + metadata JSON) in the run output directory.
  - Added focused tests in `tests/parametric_and_optimisation/test_parametric_batch_checkpoint.py` covering batch checkpoints, resume behavior, validation, and explicit missing-checkpoint errors.
- **Parametric Resume Now Survives Non-Deterministic Re-Sampling**: `run_parametric_simulation(...)` persists the exact sampling plan (`df`) inside the checkpoint and reconciles it automatically on resume.
  - Task signatures for resume are based on exact `(idf, epw, parameter values)`, so calling a non-deterministic sampler again (e.g. `sampling_lhs()`, which has no fixed random seed) in a new session used to produce a completely different plan and made `resume_from_checkpoint=True` silently re-run every task.
  - Added `resume_plan_source=('auto'|'checkpoint'|'provided')` (default `'auto'`): when the provided `df` does not match the plan stored in the checkpoint, accim now reuses the ORIGINAL checkpoint plan by default (with a `UserWarning`), so resume keeps skipping already-completed tasks without any extra action. `'provided'` restores the previous opt-in behavior of always using the newly supplied `df`.
  - Added internal helper `SimulationBase._parametric_plans_match(...)` for tolerant DataFrame comparison, and extended the checkpoint payload/loader (`_save_parametric_checkpoint`, `_load_parametric_checkpoint_state`) with an `input_plan` entry.
  - Fixed two pre-existing checkpoint tests that asserted a legacy plain-DataFrame checkpoint format no longer produced by `_save_parametric_checkpoint` (`state_v2` dict format), and added regression tests in `tests/parametric_and_optimisation/test_parametric_batch_checkpoint.py` covering plan reconciliation, the `resume_plan_source='provided'` opt-out, and the `_parametric_plans_match` helper.
- **Parametric Plotting Methods Resolve Columns Renamed by `normalize_outputs()`**: `plot_parametric_scatter(...)`, `plot_parametric_ecdf(...)`, and `plot_parametric_distributions(...)` no longer raise a `KeyError` for energy columns renamed by `normalize_outputs()` (for example `'Electricity:HVAC'` -> `'Electricity:HVAC_kWh/m2'`).
  - Added shared helper `PlottingMixin._resolve_plot_axis_column(...)`, reusing the existing energy-aware fuzzy matcher `_resolve_output_columns(...)` (previously only wired into optimisation/Pareto plotting) for `x`/`y`/`y_vars` axis arguments before the "missing column" validation.
  - When a requested axis name is resolved to a different (renamed) column, an informational message is printed so the substitution is not silent.
  - Note: this only covers accim plotting methods; plain pandas calls on `outputs_param_simulation` (e.g. `df.groupby('epw')['Electricity:HVAC']...`) still need the post-normalization column name, since they do not go through accim's column resolution.
  - Added regression test `test_plot_methods_resolve_column_renamed_by_normalize_outputs` in `tests/parametric_and_optimisation/test_plotting_parametric_new_methods.py`.
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
- **Global Simulation Summary API (`parametric_and_optimisation`)**: Added structured summary inspection for parametric/optimisation outputs.
  - Added persistent attribute `simulation_summary` plus public methods `build_simulation_summary(...)` and `print_simulation_summary(...)` in `SimulationBase`.
  - Summary includes dynamic category detection (rule-driven via `epw_mapping_rules`/`idf_mapping_rules` when available, otherwise inferred), key uniques (`idf`, `epw`, `output_dir`), numeric/energy column detection, and per-category counts.
  - Added strict validation for explicit `category_columns` with detailed invalid/available/auto-detected diagnostics.
  - Added optional JSON export API `export_simulation_summary_json(...)` for reproducibility/audit workflows.
  - Added automatic summary refresh after `run_parametric_simulation(...)`, `load_outputs_parametric(...)`, `run_optimisation(...)`, and `load_outputs_optimisation(...)`.
  - Added optional run flags `export_summary_json` and `summary_json_path` to auto-export summary JSON at the end of parametric and optimisation runs.
  - Added focused tests in `tests/parametric_and_optimisation/test_simulation_summary.py` covering rules/inference/validation, run/load auto-refresh, and manual/automatic JSON export.
- **Per-Extension Simulation File Cleanup (`parametric_and_optimisation`)**: Added file-level cleanup controls for retained simulation folders.
  - Added `sim_files_extensions` and `sim_files_policy=('keep'|'delete')` to `run_parametric_simulation(...)` and `run_optimisation(...)`.
  - Extension selectors accept tokens like `csv`, `.csv`, and `*.csv` (case-insensitive) and are applied within each simulation subdirectory under `BESOS_Output*`.
  - Added warnings when a selected policy can remove `.csv` outputs used by hourly/monthly post-processing.
  - Clarified in API docstrings that this cleanup does **not** delete run-level backups such as `accim_idf_backup_*`.
  - Added focused tests in `tests/parametric_and_optimisation/test_sim_file_cleanup.py`.

### Changed
- **Example notebooks of `parametric_and_optimisation`** (`accim/sample_files/jupyter_notebooks/parametric_and_optimisation_examples/`): the complete workflows `wf1`-`wf5` (parametric runs and optimisations with the custom model, the predefined models and aPMV setpoints) have been rewritten, and the tutorials `00`-`10` have been brought up to date with the current API. They run with the sample IDF and EPW files after `pip install "accim[samples]"`.
  - Light simulations: 2 timesteps per hour, minimal shadowing, the full year without design days, only the outputs that are used, and parallel processes. Full hourly results are kept only in `wf1`; `wf2` and `wf4` simulate the chosen configurations and solutions again with hourly outputs.
  - `wf1`: custom model sampled inside the m-n band and ASHRAE 55 screening. `wf2`: the 40 predefined configurations, with the cooling season of each hemisphere. `wf3` and `wf5`: aPMV setpoints, with realistic PMV inputs of the occupants (the sample model has a work efficiency, clothing and air velocity of 1). `wf4`: NSGA-II, knee point and TOPSIS, and the screening of the non-dominated solutions.
  - Tutorials: notebooks 09 and 10 reuse the results of 02 and 07, so the deletion of results at the end of each notebook is now optional (`DELETE_RESULTS = False`); notebook 10 configures the session of 07 again, chooses the compromise solutions per EPW and checks the robustness of one of them with both EPWs. Notebook 06 simulates both sample models with both EPWs and two thicknesses of the roof material (a BESOS parameter added to the accim ones), and notebook 05 runs the Morris analysis in parallel.
- **Sample files moved to a separate, optional distribution (`accim-samples`)**: `pip install accim` now installs only the library (the wheel goes from about 36 MB to about 0.5 MB). The sample files (`accim/sample_files`: Jupyter notebooks, IDFs, EPWs, CSVs, figures and scripts) are published as the new distribution `accim-samples`, with the same version as accim, and are installed with `pip install "accim[samples]"` into the same `site-packages/accim/sample_files` folder. They can be added later with the same command and removed with `pip uninstall accim-samples` without affecting accim. `.ipynb_checkpoints` and `__pycache__` folders are no longer distributed.
  - Build: `dist_build_package.bat` builds both distributions into `dist/`; `accim-samples` is built by the new `packaging/build_samples_dist.py` from the template in `packaging/accim-samples/`. The script checks that the wheel only contains `accim/sample_files/**` and warns if a file exceeds the default PyPI upload limit (100 MB). `dist_upload_test.bat` and `dist_upload.bat` use the new `packaging/release.py`: they only upload the files of the current version, check both wheels and run `twine check`, skip what is already published, ask to type the version to confirm and upload `accim-samples` before `accim`.
  - Documentation: installation options in `README.md` and `docs/source/2_installation.md`; `README.md` (section 2.1.1) and `docs/source/2_installation.md` explain how to run the example notebooks.
- **Consolidated Output-Objects API (`parametric_and_optimisation`)**: reduced the Output:Variable/Output:Meter method surface to a canonical set (read: `get_output_variables_df_from_idf`/`get_output_meters_df_from_idf`/`scan_output_objects`; discover: `discover_available_outputs`; write: `set_output_variables_to_idf`/`set_output_meters_to_idf`; prune: `keep_only_outputs_in_idfs`/`clear_outputs`/`autocorrect_output_duplicates`; orchestrate: `select_outputs`/`apply_outputs_preflight`/`set_output_readers`).
  - `set_output_variables_to_idf(...)` and `set_output_meters_to_idf(...)` now share the same argument order and defaults, including `validate=True` (behaviour change for variables, which previously defaulted to `False`); the deprecated `set_output_var_df_to_idf(...)` wrapper pins `validate=False` to preserve legacy behaviour.
  - Both setters share unified semantics: rows with empty `frequency` are expanded using `self.output_freqs`; `mode='replace'` always removes existing objects of the type in every scoped IDF (with a warning when nothing remains to add); object access is case-tolerant.
  - Both setters now return a report dict with per-IDF counts (`added`, `skipped_existing`, `removed_replace`, `missing`, `filtered_missing`) and aggregated totals.
  - Meter validation no longer re-implements discovery inline: both setters delegate to a shared helper that reuses any cached discovery matching the validation scope (including `prefer='rdd_mdd'` caches) and otherwise runs `discover_available_outputs(prefer='testsimeplus')`. This also gives meter validation the VRF-autosizing `SizingPeriod:WeatherFileDays` safeguard, and makes the number of test simulations independent of call order.
  - `clear_outputs(mode='meters_vars')` is now implemented on top of `keep_only_outputs_in_idfs(...)` so a single removal engine exists; unreachable dead code in the `'all'` filter was removed and invalid `mode` values now raise `ValueError`.
  - `apply_outputs_preflight(...)` now reports the actually-applied counts from the setter reports (exposed under `setter_reports`), applies meters from the selection DataFrame (preserving per-row frequencies), and its verification step no longer flags auto-filtered outputs as missing.
  - Tests and sample notebooks were migrated to the canonical API.
- **Output Variable API Symmetry with Meters**:
  - `set_output_variables_to_idf(...)` now exposes validation controls aligned with `set_output_meters_to_idf(...)`: `validate`, `on_missing`, `auto_filter`, `reduce_sim_time`, `validation_idf_scope`, and `keep_available_outputs`.
  - Variable application can now pre-validate availability via `discover_available_outputs(...)`, with consistent missing-output handling (`warn`/`raise`/`ignore`) and optional auto-filtering.
  - Removed the keyword-only separator in `set_output_variables_to_idf(...)` so all arguments are directly visible in IDE call hints when opening the method parenthesis.
  - `apply_outputs_preflight(...)` now forwards the same validation-policy inputs when applying selected variables.
  - Added regression coverage in `tests/parametric_and_optimisation/10_test_outputs_preflight.py`.
- **Explicit `addAccis` Constructor Passthrough (`parametric_and_optimisation`)**:
  - `SimulationBase.__init__` now exposes and forwards explicit `addAccis` passthrough arguments (`Output_take_dataframe`, `EnergyPlus_version`, `VRFschedule`, `eer`, `cop`, `hvac_zone_map`) with defaults aligned to `accis.addAccis`.
  - `ParametricSimulation`, `OptimisationSimulation`, and `AccimPredefModelsParamSim` constructors were updated to expose and forward the same explicit arguments.
- **`discover_available_outputs(prefer='rdd_mdd')` Self-Sufficient Path**:
  - The `rdd_mdd` path now generates `available_outputs/eplusout.rdd` and `available_outputs/eplusout.mdd` with a reduced test simulation when files are missing (or `refresh=True`), then parses those files directly.
  - Removed silent fallback to `testsimeplus` for this path; failures now raise clear exceptions.
  - Shared reduced test-simulation preparation was extracted to a private helper and reused by both discovery flows.
- **Custom-Model CustAST Defaulting Symmetry and Visibility**:
  - `set_parameters(...)` for `parameters_type='accim custom model'` now applies a symmetric default-resolution flow for `ASTaul` and `ASTall` (both initialized to `0` and then resolved through `dflt_values` when omitted).
  - Default values remain `ASTaul=33.5` and `ASTall=10` when those parameters are not explicitly provided.
  - When defaults are applied, the user now receives a yellow console warning summarizing `parameter=value` pairs (for example `ASTaul=33.5, ASTall=10`).
- **Output Retrieval API Explicitness and Constructor Defaults**:
  - `ParametricSimulation` wrappers (`get_hourly_df`, `get_output_df`, `get_monthly_df`, `get_daily_df`, `get_runperiod_df`) now expose advanced extraction arguments explicitly (for example `epw_filter`, `simulation_indices`, `output_columns`, `file_source`, `skip_confirmation`) without `**kwargs`, improving IDE discoverability.
  - Constructor default `output_keep_existing` is now aligned to `True` across `SimulationBase`, `ParametricSimulation`, `OptimisationSimulation`, and `AccimPredefModelsParamSim`.
- **Custom Subplot Ordering Semantics (`subplot_order_mode='custom'`)**: Active subplot dimensions no longer require exhaustive `subplot_order_custom` entries.
  - Unspecified active dimensions now preserve their current data order (equivalent to `auto`) instead of raising an error.
  - Validation for unsupported/custom dimensions remains strict and unchanged.
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
- **Configurable Results Root Routing**: Added optional `accim_results_root` support in simulation constructors and run methods to resolve relative `out_dir` paths without relying on global environment variables.
  - Supported in `SimulationBase`, `ParametricSimulation`, `OptimisationSimulation`, and `AccimPredefModelsParamSim` constructors.
  - Supported as a per-run override in `run_parametric_simulation(...)` and `run_optimisation(...)`.
  - Resolution precedence is now: absolute `out_dir` > method `accim_results_root` > instance `accim_results_root` > `ACCIM_RESULTS_ROOT` environment variable > legacy relative behavior.
- **Parametric Checkpoint Internals for Long Runs**: `run_parametric_simulation(...)` now persists batch chunks to disk and merges them at the end instead of keeping the full run payload in memory.
  - Added batch artifact directory `outputs_param_simulation_batches`.
  - Added stateful checkpoint payload support (`completed_signatures`, `batch_pickles`) while keeping backward compatibility with legacy DataFrame checkpoints.
- **Notebook 14 Multi-IDF Workflow (without loop)**: Updated `14_main_optimisationsimulation_accim_custom_model_without_idf_loop.ipynb` to run a single `OptimisationSimulation` instance with `buildings=[...]` and explicit Pareto controls.
  - Step 2 now avoids per-IDF instantiation loops and prepares IDFs once before creating the optimisation object.
  - Step 3 now plots from one combined optimisation object and forwards the selected MCDM segmentation flags.

### Deprecated
- **Output-Objects API legacy names (`parametric_and_optimisation`)**: the following methods now emit `DeprecationWarning` and delegate to their canonical replacements; they will be removed in a future version.
  - `get_output_var_df_from_idf(...)` → `get_output_variables_df_from_idf(...)`
  - `get_output_meter_df_from_idf(...)` → `get_output_meters_df_from_idf(...)`
  - `get_outputs_df_from_testsim(...)` → `discover_available_outputs(...)` (the test-simulation implementation is now the internal helper `_get_outputs_df_from_testsim`)
  - `set_outputs_for_simulation(...)` → `set_output_readers(...)` (renamed because it registers besos readers and does not modify the IDFs)
  - `set_output_var_df_to_idf(...)` and `set_output_met_objects_to_idf(...)` remain deprecated wrappers of `set_output_variables_to_idf(...)` / `set_output_meters_to_idf(...)`.

### Fixed
- **EnergyPlus 25.2 in `addAccis`, `runEp` and the IDD lookup**: `addAccis(EnergyPlus_version='25.2')` and its prompt accept EnergyPlus 25.2 (`accim.lists`, `accim.utils.get_idd_path_from_ep_version`), and `read_eso_using_readvarseso` also looks for ReadVarsESO in `C:\EnergyPlusV25-2-0`. Before, the lists stopped at 25.1, so `addAccis` only worked with `'auto'` for IDFs of 25.2.
  - `runEp` accepts `EnergyPlus_version='auto'`, which reads the version of the IDFs (new function `get_iddfile_from_idfs` of `accim.run.run`; IDFs of different versions raise an error, because eppy uses one IDD in each Python session), and it uses the version entered in the prompt after a wrong one. Before, both cases ended in `IDF.setiddname('not-supported')`.
  - `accim.sim.accis_single_idf` and `accis_single_idf_funcs` take `'auto'` as the version of the IDF, like `None`. Before, `accis_single_idf_funcs.addAccis` rejected `'auto'`.
  - Tests in `tests/core/test_energyplus_versions.py`.
- **`geopy`**: `geopy` is now in `install_requires`, and `accim.data.preprocessing` imports it only when `rename_epw_files` geolocates an EPW file, with a message on how to install it if it is missing. Before, the module imported it when it was loaded, but it was not a dependency, so `from accim.data.preprocessing import rename_epw_files` failed on a clean install. The documentation no longer mocks it. Tests in `tests/core/test_preprocessing_geopy.py`.
- **`rename_epw_files` with EPW files that name no scenario or year**: they get the Present scenario again. Before, the checks compared the cells with the string `'nan'`, but they are NaN (or the column does not exist when no EPW names a scenario or a year), so `rename_epw_files` failed with `TypeError` or `KeyError`, with pandas 2 and 3. Tests in `tests/core/test_rename_epw_files.py`.
- **Default values of `apply_apmv_setpoints`**: `pmv_cooling_sp=0.5` and `pmv_heating_sp=-0.5`, as in the docstring and in the defaults for missing dictionary keys, and a cooling season from day 121 (1 May) to day 274 (1 October, not included), as `CoolSeasonStart` and `CoolSeasonEnd` of `addAccis`. Before, the defaults were `pmv_cooling_sp=-0.5` and `pmv_heating_sp=0.5`, so both PMV setpoints of the thermostat were 0, and the cooling season went from day 120 to day 210 (29 July). `ParametricSimulation(parameters_type='apmv setpoints')` uses these defaults unless `bypass_addAccis=True`. Behaviour change: simulations that rely on these defaults give different results, for example tutorial 03 of `parametric_and_optimisation_examples` (cooling season). Tests in `tests/core/test_apmv_setpoints_defaults.py`.
- **EMS program `SetAST` when `addAccis` generates several IDFs**: each output IDF has the 4 base lines of `SetAST` (SetpointAcc, m, n and `run SetAST_Master`) followed by the lines of its comfort model (new function `replace_SetAST_dynamic_lines` of `accim.sim.accim_IDFgeneration`). All output IDFs are saved from the same IDF object. Before, the branches that append the lines of the comfort model trimmed `SetAST` to 16 lines, so the second and later IDFs of a call kept 12 lines of the previous one. When the cut fell inside an if block, EnergyPlus stopped ("Missing an ENDIF"), for example with `ComfMod=[0, 3]` and `HVACmode=[0]`; the other branches left lines 5 to 16 blank. The method `modifyAccis` of `accim.sim.accis_single_idf.addAccis` had the same problem from its second call. Tests in `tests/core/test_addaccis_setast.py` and `tests/core/test_modifyaccis_setast.py`.
- **`modifyAccis` of `accim.sim.accis_single_idf_funcs`** (used by `AccimPredefModelsParamSim`): it keeps the lines `set m` and `set n` of `SetAST`. Before, it trimmed `SetAST` to its first line and added `run SetAST_Master` as the second, where the setters of `CustAST_m` and `CustAST_n` then wrote. Test in `tests/core/test_modifyaccis_setast.py`.
- **`removefiles` (`accim.run.run`)**: it deletes only the simulation files of `runEp`, whose names contain `[`, except the `.py`, `.idf`, `.epw`, `.csv` and `.eso` files, and their `Table.csv`, `Meter.csv` and `Zsz.csv` files. Before, it deleted every other file of the working folder (for instance, Jupyter notebooks) and every CSV ending with `Table.csv`, `Meter.csv` or `Zsz.csv`, and it failed when the folder had subfolders. Behaviour change. Test in `tests/core/test_run_removefiles.py`.
- **`Table.time_plot` with pandas 3**: it reads the first date by position (`.iloc[0]`) and builds the dates with offset objects (`pd.offsets.Hour`, `Day` and `MonthEnd`), which work with pandas 2 and 3; the year of the dates (1900, as before) is given to `strptime`, which Python 3.14 warns about otherwise. Before, `Series[0]` raised `KeyError: 0` and pandas 3 rejects the aliases `'H'` and `'M'`. Test in `tests/core/test_table_time_plot.py`.
- **Link to the full example printed by `addAccis`**: it points to `jupyter_notebooks/full_example_IBPSA/full_example_IBPSA.html`. Before, it pointed to `full_example/full_example.html`, which does not exist. Tests in `tests/core/test_addaccis_banner.py`.
- **Prompts of `addAccis` and messages of `runEp`**: with `ScriptType` `'ex_ac'` or `'ex_mm'`, `SupplyAirTempInputMethod`, which only the VRF systems use, is no longer needed to skip the prompts; before, without it, `addAccis` asked for all the arguments of the first stage and used the answers instead of those of the call. When the setpoint accuracy is left empty in the prompts, `SetpointAcc` is 10000, as in the function call (it was 100). `runEp` prints "EPWs" instead of "sample_EPWs", and so do some docstrings. Tests in `tests/core/test_addaccis_arguments.py` and `tests/core/test_energyplus_versions.py`.
- **Normalised tables in plots**: the plotting methods (`plot_categorical_boxplots`, `plot_best_compromise_solutions`, `plot_pareto_front`, `plot_pairwise_scatter_matrix` and the `plot_parametric_*` methods) now check whether the table they plot was normalised by `normalize_outputs`. Before, they checked the global flag `outputs_normalized`, which is False while any other loaded table is not normalised, so a table already in kWh/m2 was divided by 3.6e6 again and labelled kWh (for example, `normalize_outputs(df_types=['parametric'])`, then `get_hourly_df(...)` and `plot_categorical_boxplots(df_source='parametric')`). Tests in `tests/parametric_and_optimisation/test_normalization_state.py`.
- **Normalisation state after a new simulation**: `run_parametric_simulation`, `run_optimisation`, `load_outputs_parametric` and `load_outputs_optimisation` reset the normalisation state of the tables they replace, so `normalize_outputs` converts the new results. Before, after `normalize_outputs`, a new simulation on the same object kept its table marked as normalised: `normalize_outputs` skipped the new results, which stayed in J, and the plots took them as kWh/m2. The tables that are not replaced (for example an hourly table built before) keep their state. Tests in `tests/parametric_and_optimisation/test_normalization_state.py`.
- **Estimated number of optimisation simulations**: `estimate_optimisation_sims`, `preflight_report_optimisation` and the progress of `run_optimisation` now count the offspring of NSGA-II in pairs: after the initial population, each generation evaluates `population_size` rounded up to an even number. Before, they assumed `population_size` evaluations per generation, so with an odd population the estimate fell short (population 3 and 6 evaluations: 6 instead of 7 simulations per EPW) and the progress went past 100 %. The new function `estimate_case_simulations` of `accim.parametric_and_optimisation.optimisation_progress` gives the count of one IDF/EPW case. Tests in `tests/parametric_and_optimisation/test_optimisation_progress.py` and `test_optimisation_preflight_report.py`.
- **Messages of `reduce_runtime` and `modify_timesteps`** (`accim.utils`): the number of timesteps per hour and the maximum figures in shadow overlap calculations are printed without a unit. Before, both messages said "days". Tests in `tests/parametric_and_optimisation/test_reduce_runtime_messages.py`.
- **Facets of `plot_hourly_scatter` and `plot_hourly_lines`**: the `row`, `col` and `hue` columns are kept when the hourly results are stacked (new argument `extra_id_vars` of `prepare_hourly_long_df`), so the results of the predefined models can be split by `ComfMod`, `HVACmode` or other parameters without passing `id_vars`. A facet column that is not in the plotted data is reported. Before, the default `id_vars` only kept the parameters of the custom model (`CustAST_m`, `CustAST_n`), and the other facets were ignored without a message. Tests in `tests/parametric_and_optimisation/test_plotting_hourly_methods.py`.
- **Units of the objectives in `plot_best_compromise_solutions`**: only energy objectives are converted to kWh (or kWh/m2) and labelled with that unit; the others, such as the annual mean operative temperature of wf4, keep their values and their name. Before, the second objective was labelled kWh/m2 even when it was a temperature, and it was divided by 3.6e6 when the results were not normalised. Tests in `tests/parametric_and_optimisation/test_mcdm_plot_objective_units.py`.
- **seaborn warning in `plot_categorical_boxplots`**: without `hue`, the boxes are coloured by energy type through `hue`, with no legend, instead of passing `palette` alone, which seaborn 0.13 deprecates (FutureWarning; it stops working in 0.14). The figure does not change. Test in `tests/parametric_and_optimisation/test_plotting_parametric_new_methods.py`.
- **Simulation plan of `run_parametric_simulation`**:
  - The results have one row per row of the plan (per row and EPW when the plan has no `epw` column), in the order of the plan, also with `processes > 1`. Before, parallel results came in the order in which the simulations finished, which broke the analyses that pair the results with the sample by position (Morris and Sobol).
  - Repeated rows of a plan (same IDF, EPW and parameter values) are simulated once and keep one row each. Before, they were all simulated and only the last one was kept, so a Morris plan with repeated points lost rows.
  - The `idf` column of a plan may name each IDF by its identifier, file name or path. With one IDF loaded, a value that names another IDF raises an error. Before, the column was dropped without a warning, and every row was simulated with the loaded IDF.
  - Tests in `tests/parametric_and_optimisation/test_parametric_plan.py`.
- **Additional parameters in parametric runs**: the BESOS parameters given in `additional_params` of `set_parameters` (for example a `FieldSelector` on a material) are now applied in each simulation of `run_parametric_simulation`, as in `run_optimisation`. Before, the evaluation worker only applied accim parameters and ignored the others without a warning. With `processes > 1` they must be picklable, otherwise an error explains it. Tests in `tests/parametric_and_optimisation/test_parametric_worker.py`.
- **Custom-model baseline in every IDF**: with `parameters_type='accim custom model'`, `set_parameters` writes the baseline of the custom model (ComfStand 99, ComfMod 3, CAT 80, and the default limits and offsets not among the parameters) in every loaded IDF. Before, it only wrote it in the first one, so the other IDFs kept the comfort model set by `addAccis` and the custom parameters had no effect on them. Test in `tests/parametric_and_optimisation/test_parametric_plan.py`.
- **`get_best_compromise_solution` per front**: the method is now applied to the non-dominated solutions of each EPW (and of each IDF when the fronts are separated by IDF), as in `plot_best_compromise_solutions`, and returns one row per front. Before, it normalised and compared the solutions of all the fronts together. New arguments `separate_by_epw` and `separate_by_idf`, taken by default from the attributes of the results, as in the plot. Tests in `tests/parametric_and_optimisation/test_analysis_output_resolution.py`.
- **Evaluations of `run_parametric_simulation`**: three fixes in the function that runs each evaluation, with one process or several:
  - With `keep_dirs=False`, each simulation now runs in a temporary folder created by BESOS. Before, every simulation used the same `<out_dir>/BESOS_Output` folder, so simulations running in parallel overwrote each other's files and EnergyPlus failed (`CalledProcessError`).
  - With `keep_dirs=True`, `<out_dir>/BESOS_Output` is created before the BESOS evaluator, tolerating a folder created by another process. Before, processes starting at the same time could try to create it together, and one of them failed with `FileExistsError`.
  - The reported outputs (`add_outputs` of `set_problem`) are now read from the record that BESOS keeps for each evaluation. Before, they were looked for among the objectives returned by BESOS, so they were empty without `keep_dirs` and, with `keep_dirs=True`, the first one received the path of the simulation folder and `output_dir` was missing, so the methods that read the hourly CSV files could not find them.
  - Tests in `tests/parametric_and_optimisation/test_parametric_worker.py`.
- **`Date/Time` of simulation CSVs read with `skip_blank_lines=False`**: `Table` (`accim.data.postprocessing`) and `filter_simulation_output_csvs(...)` now read `eplusout.csv` files with `skip_blank_lines=False`. With the pandas default, a line that starts exactly at the end of one of the 256 KiB read blocks lost its leading space (`' 07/23  15:00:00'` was read as `'07/23  15:00:00'`), so that `Date/Time` value differed from all the others.
- **`Table` plots with recent matplotlib versions**: the plotting methods of `Table` no longer call `GrouperView.join` (removed in matplotlib 3.8) to share the secondary y-axes, or `Legend.legendHandles` (removed in matplotlib 3.9); the helpers `_share_y_axis` and `_legend_handles` work with old and new versions.
- **aPMV setpoints applied on the aPMV scale (`apply_apmv_setpoints`)**: the EMS program `apply_aPMV_<target>` passed `s/(1 + lambda*s)` to the Fanger thermal comfort thermostat, where `s` is `pmv_heating_sp` or `pmv_cooling_sp` and `lambda` is the adaptive coefficient of the current season. That is the aPMV of a PMV equal to `s`, not the PMV whose aPMV equals `s`, so the zone aPMV settled around `s/(1 + 2*lambda*s)` and the effect of `lambda` was inverted.
  - `pmv_heating_sp` and `pmv_cooling_sp` are now targets on the aPMV scale, and the setpoint tolerances are applied on that scale.
  - The thermostat receives the PMV given by the inverse aPMV formula, `PMV = aPMV/(1 - lambda*aPMV)`.
  - `count_aPMV_comfort_hours_<target>` now compares the zone aPMV with these aPMV setpoints, so `Comfortable Hours_<target>` counts the hours within the setpoints that are actually applied.
  - Behaviour change: simulations with a non-zero adaptive coefficient give different results from earlier versions.
- **Output-Objects API fixes (`parametric_and_optimisation`)**:
  - `select_outputs(match='exact')` now matches correctly for variables (the needle was previously compared against an upper-cased series, so mixed-case requests never matched); for meters, `'exact'` is now truly exact instead of behaving case-insensitively. `'contains'` no longer interprets the needle as a regex, and missing/suggestion reports preserve the original casing of requested and available names.
  - `set_output_readers(...)` (formerly `set_outputs_for_simulation`) no longer mutates the caller's DataFrames when adding the internal `output_name` column.
  - `discover_available_outputs(...)` now raises an early `ValueError` for invalid `prefer` values instead of failing later with `NameError`.
  - Output setters now emit an explicit warning when validation is requested but discovery yields no available outputs, instead of silently adding everything.
  - `SimulationBase.__init__` no longer shares the mutable default `output_freqs` list across instances.
- **`set_parameters(...)` Robustness for Custom Models Without Parsed `CustAST` Args**:
  - Added a safe fallback path when `get_accim_args(...)` does not expose a `CustAST` dictionary, avoiding `KeyError: 'CustAST'` during custom-model parameter setup.
- **Per-DataFrame Normalization State Tracking in Output Post-Processing**:
  - Replaced fragile global-only normalization gating with per-dataset tracking (`parametric_hourly`, `parametric_monthly`, `optimisation_daily`, etc.) to avoid false skips or side effects when normalizing selected outputs.
  - Hourly/aggregated output builders now invalidate normalization state only for the datasets they overwrite, preventing stale normalization markers.
- **Default Aggregation Heuristic Diagnostics**:
  - `get_output_df(...)` / `get_output_df_optimisation(...)` now emit a warning when numeric output columns do not match known `mean`/`sum` keyword heuristics and therefore default to `sum`, making aggregation assumptions explicit.
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
- **Case-Robust Filtering in `keep_only_outputs_in_idfs(...)`**: Output pruning now reads `Output:Meter` and `Output:Variable` objects with casing-tolerant key access, so objects created as `OUTPUT:*` are correctly matched and removed when not selected.
- **Sparse Hourly Expansion with Variable Output Columns**: `expand_to_hourly_dataframe(...)` now handles rows where some hourly outputs are missing (e.g. different zone counts by IDF) by using the first non-empty series length and padding missing columns with `NaN` instead of silently dropping rows.
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
