# 9. Migrating from accim 0.x to accim 1.0.0

accim 1.0.0 is a refactoring of the package: the code follows the conventions of Python (PEP 8), it is split
into smaller modules, it is faster, and it can run the simulations through the Python API of EnergyPlus
({ref}`python-api-backend`). The usage does not change, apart from the names of some classes, functions and
arguments, which did not follow the naming conventions of Python.

**The scripts written for accim 0.x still work**: the old names are kept as deprecated aliases, which show a
`DeprecationWarning` with the new name. Python hides these warnings by default, except in Jupyter notebooks and
in the code of the script that you run; to see all of them, run Python with `-W default::DeprecationWarning`.
The old names will be removed in a future version, so it is recommended to use the new ones.

The usage of `accim.parametric_and_optimisation` (`ParametricSimulation`, `OptimisationSimulation`, the
predefined models...) does not change at all. Its results only change for the models whose natural ventilation
is given by `ZoneVentilation` objects, which accim 0.x did not control in this module, for the optimisations
with OMOPSO, SMPSO, CMAES, GeneticAlgorithm and EvolutionaryStrategy (whose generations now have
`population_size` solutions), and in the post-processing (the daily and monthly tables, and the year of the
hourly tables without `start_date`), and the full-set plans of the predefined models no longer keep some
invalid combinations (see section 9.3). Some settings that always failed now run (`ComfStand` 0 and 22 with any
`ComfMod`, the baseline of `AccimPredefModelsParamSim`, PAES), and others stop with a clear error before the
optimisation starts, or instead of giving wrong values per m2 (see 9.3).

## 9.1 Classes, functions and modules

| accim 0.x | accim 1.0.0 |
| :--- | :--- |
| `accim.sim.accis.addAccis(...)` (class) | `accim.sim.accis.AddAccis(...)` |
| `accim.sim.accis_single_idf_funcs.addAccis(idf, ...)` | `accim.sim.accis.add_accis_to_idf(idf, ...)` |
| `accim.sim.accis_single_idf_funcs.modifyAccis(idf, ...)` | `accim.sim.accis.modify_accis(idf, ...)` |
| `accim.sim.accis_single_idf_funcs.gen_outputs_df(idf, ...)` | `accim.sim.accis.gen_outputs_df(idf, ...)` |
| `accim.sim.accis_single_idf.addAccis(idf, ...)` and its method `modifyAccis(...)` | `accim.sim.accis.add_accis_to_idf(idf, ...)` and `accim.sim.accis.modify_accis(idf, ...)` |
| `accim.sim.apmv_setpoints` | `accim.sim.apmv` (same functions) |
| `accim.run.run.runEp(...)` | `accim.run.run_ep(...)` |
| `accim.run.run.removefiles()` | `accim.run.remove_files()` |
| `accim.data.postprocessing.utils.genCSVconcatenated(...)` | `accim.data.postprocessing.utils.gen_csv_concatenated(...)` |
| `accim.data.postprocessing.utils.preview_Table_cols(...)` | `accim.data.postprocessing.utils.preview_table_cols(...)` |
| `accim.lists.fullEPversionsList`, `accim.lists.epvers_space_objs` | `accim.constants.SUPPORTED_ENERGYPLUS_VERSIONS`, `accim.constants.ENERGYPLUS_VERSIONS_WITH_SPACES` |

`accim.utils` is now a package with several modules (`people`, `editing`, `accim_args`, `versions`, `outputs`,
`verification` and `workspace`), but all its functions can still be imported from `accim.utils`, as before
(for instance, `from accim.utils import reduce_runtime`).

The classes `rename_epw_files` and `Table` keep their names: PEP 8 allows the names of functions for the classes
that are used mainly as functions, such as `rename_epw_files`.

The internal modules of `accim.sim` (`accim_Main`, `accim_Base`, `accim_Base_EMS`, `accim_VRFsystem`,
`accim_VRFsystem_EMS`, `accim_ExistingHVAC`, `accim_ExistingHVAC_EMS`, `accim_IDFgeneration`, `setAST_models`,
`dicts`, `lists` and `utils`) have been replaced by new modules (`arguments`, `model`, `build`, `generation`,
`outputs`, `people`, `targets`, `ems`, `hvac`...), which are not meant to be used directly.

## 9.2 Arguments

The arguments of `AddAccis`, `add_accis_to_idf` and `modify_accis`:

| accim 0.x | accim 1.0.0 |
| :--- | :--- |
| `ScriptType` | `script_type` |
| `SupplyAirTempInputMethod` | `supply_air_temp_input_method` |
| `Output_type` | `output_type` |
| `Output_freqs` | `output_freqs` |
| `Output_keep_existing` | `output_keep_existing` |
| `Output_gen_dataframe` | `output_gen_dataframe` |
| `Output_take_dataframe` | `output_take_dataframe` |
| `EnergyPlus_version` | `energyplus_version` |
| `TempCtrl` | `temp_ctrl` |
| `VRFschedule` | `vrf_schedule` |
| `ComfStand` | `comf_stand` |
| `CAT` | `cat` |
| `CATcoolOffset`, `CATheatOffset` | `cat_cool_offset`, `cat_heat_offset` |
| `ComfMod` | `comf_mod` |
| `SetpointAcc` | `setpoint_acc` |
| `CustAST_ACSTaul`, `CustAST_ACSTall`, `CustAST_AHSTaul`, `CustAST_AHSTall` | `cust_ast_acst_aul`, `cust_ast_acst_all`, `cust_ast_ahst_aul`, `cust_ast_ahst_all` |
| `CustAST_m`, `CustAST_n` | `cust_ast_m`, `cust_ast_n` |
| `CustAST_ACSToffset`, `CustAST_AHSToffset` | `cust_ast_acst_offset`, `cust_ast_ahst_offset` |
| `CoolSeasonStart`, `CoolSeasonEnd` | `cool_season_start`, `cool_season_end` |
| `HVACmode` | `hvac_mode` |
| `VentCtrl` | `vent_ctrl` |
| `MaxTempDiffVOF`, `MinTempDiffVOF`, `MultiplierVOF` | `max_temp_diff_vof`, `min_temp_diff_vof`, `multiplier_vof` |
| `VSToffset` | `vst_offset` |
| `MinOToffset` | `min_ot_offset` |
| `MaxWindSpeed` | `max_wind_speed` |
| `ASTtol_start`, `ASTtol_end_input`, `ASTtol_steps` | `ast_tol_start`, `ast_tol_end_input`, `ast_tol_steps` |
| `ASTtol` (`modifyAccis`) | `ast_tol` |
| `NameSuffix` | `name_suffix` |
| `verboseMode` | `verbose_mode` |
| `confirmGen` | `confirm_gen` |

The keys of the attribute `arguments` of `AddAccis` have the new names (the old ones still work).

Other arguments:

| Function | accim 0.x | accim 1.0.0 |
| :--- | :--- | :--- |
| `run_ep` | `runOnlyAccim`, `confirmRun`, `num_CPUs`, `EnergyPlus_version` | `run_only_accim`, `confirm_run`, `num_cpus`, `energyplus_version` |
| `apply_apmv_setpoints` | `other_PMV_related_outputs` | `other_pmv_related_outputs` |
| `add_vrf_system` (aPMV) | `SupplyAirTempInputMethod`, `VRFschedule` | `supply_air_temp_input_method`, `vrf_schedule` |
| `Table` | `name_export_rows_with_NaN` | `name_export_rows_with_nan` |
| `get_idd_path_from_ep_version` | `EnergyPlus_version` | `energyplus_version` |

The prompts of `AddAccis` still show the old names (for instance, "Enter the ScriptType").

## 9.3 Changes in the output IDFs and in the behaviour

The output IDFs of accim 1.0.0 have the same objects as those of accim 0.x, except for the corrections below.
The new version was checked against accim 0.x with the output IDFs of 29 configurations (all script types,
temperature and PMV control, all the comfort standards, aPMV setpoints, `add_accis_to_idf` and `modify_accis`),
which are identical apart from these corrections, and with short parametric and optimisation studies (the IDFs
of each class of `accim.parametric_and_optimisation` and their results):

- The output IDFs are the same in every run: the zones, and the objects of each zone, are always in the same
  order. Before, the order of the zones could change from one run to another. Since EnergyPlus adds up some
  results (the meters, for instance) in the order of the objects, the results of a model whose objects are in a
  different order than with accim 0.x may differ in their last digits (rounding).
- In mixed mode, `add_accis_to_idf`, and so `accim.parametric_and_optimisation`, controls the natural ventilation
  of the models without AirflowNetwork through their `ZoneVentilation:WindandStackOpenArea` and
  `ZoneVentilation:DesignFlowRate` objects, as `AddAccis` has done since accim 0.7.8: a schedule
  `Vent_Sch_<zone>`, actuated by the EMS programs of the windows, opens them. In accim 0.x, the in-memory
  functions left these objects with the schedules of the input model (always open in the sample models) and
  added no programs for them, so the ventilation controls and the arguments of the opening factor
  (`MaxTempDiffVOF`, `MinTempDiffVOF`, `MultiplierVOF`), `VSToffset`, `MinOToffset` and `MaxWindSpeed` had no
  effect on these models, and their parametric and optimisation studies give different results now.
- With the VRF systems (`script_type` 'vrf_ac' and 'vrf_mm'), `add_accis_to_idf`, and so
  `accim.parametric_and_optimisation`, enables the zone, system and plant sizing calculations of the model, as
  `AddAccis` does, and so does `accim.sim.apmv.add_vrf_system`. The VRF systems of accim are autosized, so
  EnergyPlus stopped with the models whose zone sizing calculation was off ("a zone sizing run must be done"); the
  models that already ran do not change their results. With the existing HVAC systems, the sizing calculations do
  not change. EnergyPlus also needs sizing periods: when a model has none, accim now warns (with `AddAccis` too)
  that EnergyPlus will stop, and recommends adding the design days of the location or
  `SizingPeriod:WeatherFileDays` objects.
- The subprograms of ESP CTE and INT ISO7730 (`SetAST_CS0_0` and `SetAST_CS22_0`), whose setpoints do not depend
  on the comfort mode, set them whatever `ComfMod` is. In accim 0.x they only did so with `ComfMod` 0, which the
  output IDFs of `AddAccis` have, but not the models of `accim.parametric_and_optimisation`, whose baseline has
  `ComfMod` 3, so a plan with `ComfStand` 0 or 22 stopped EnergyPlus ("Variable = 'ACST' used in expression has
  not been initialized!") unless it also set `ComfMod` 0. The text of these two subprograms changes in all the
  output IDFs, not their results, and `modify_accis` updates them in the models of earlier versions of accim.
- The plans of `sampling_full_set` with the predefined models (`drop_invalid_param_combinations`) are checked rule
  by rule: before, a column missing from the plan (`CAT`, for instance) or a comfort standard without a table of
  valid categories and comfort modes (99) skipped all the remaining rules of the row, so these plans could keep
  invalid comfort modes, or `VentCtrl`, `VSToffset`, `MinOToffset` and `MaxWindSpeed` with `HVACmode` 0. As
  before, the rows of `ComfStand` 0 are dropped when the plan has `CAT` or `ComfMod`.
- The baseline of `AccimPredefModelsParamSim` (the custom comfort model: `ComfStand` 99, `CAT` 80, `ComfMod` 3)
  has the default coefficients that `ParametricSimulation(parameters_type='accim custom model')` applies (those
  of ASHRAE 55 with 80 % acceptability: `m` 0.31, `n` 17.8, offsets ±3.5, applicability limits 10 and 33.5). In
  accim 0.x it had no coefficients, so its heating setpoint was above the cooling one and EnergyPlus stopped in
  the test simulations of `discover_available_outputs()` and `set_output_*_to_idf(validate=True)`, and in the
  plans without `ComfStand`; the rows of the plans with another `ComfStand` do not change.
- `run_optimisation()` runs PAES, which evolves one solution, without `population_size` (platypus rejected it),
  and PAES and EvolutionaryStrategy, which evolve each solution from one parent, with a mutation as their variator
  (with the crossover that besos gives every algorithm, EvolutionaryStrategy stopped after the initial
  population). With OMOPSO, SMPSO, CMAES, GeneticAlgorithm and EvolutionaryStrategy,
  `population_size` is also the size of each generation (`swarm_size` or `offspring_size`, unless
  `algorithm_options` gives them): platypus ignored it for them, or took it only as the initial population, so
  they evaluated 100 solutions in each generation, and their results change. `run_optimisation()` checks the
  settings of the algorithm before it starts, and stops with a clear error with `'ParticleSwarm'` (the abstract
  base class of the particle swarms of platypus, which never ran: use `'OMOPSO'` or `'SMPSO'`), with the epsilon
  algorithms (`'EpsMOEA'`, `'OMOPSO'`, `'EpsNSGAII'`) without `algorithm_options={'epsilons': [...]}`, with
  `'NSGAIII'` without `divisions_outer` or with maximised objectives, with `'SPEA2'` and a `population_size`
  below 3, with `'OMOPSO'`, `'SMPSO'` and `'CMAES'` and categorical parameters, and with the single-objective
  algorithms and several objectives. Before, these settings failed once the first case had started.
- The post-processing of `accim.parametric_and_optimisation` follows the calendar of EnergyPlus, which labels
  each hourly or timestep value with the end of its interval: the daily and monthly tables add the value of
  24:00 to its own day and month (before, to the next ones, so a 3-day run gave 4 daily rows). Without
  `start_date`, the hourly tables are labelled in 2023, or in 2024 only when they have 8784 hourly values (before,
  always in 2024, so a standard year got a 29 February and every value from 1 March was labelled one day early);
  an explicit `start_date` keeps its year.
- The values per m2 (`normalize_outputs()`, `normalize_per_m2=True`, also in the plots) convert only the columns
  in J and the meters and objectives without unit (before, every column whose name contained Heating, Cooling,
  Energy..., such as the adaptive setpoint temperatures, in °C), are divided once (the daily, monthly and
  run-period tables of an hourly table already in kWh/m2 were divided again), and stop with a `ValueError` when
  an IDF of the results has no floor area or a table without `idf` column has several (before, their rows were
  divided by 1 m2 or by the area of the first IDF). The IDF files with an upper-case `.IDF` extension get their
  area. The hourly methods explain which simulation files are missing and which storage options removed them,
  and warn when they leave some simulations out. In the daily, monthly and run-period tables, the sums of the
  outputs that a simulation does not report (the zones or meters of another IDF) are empty instead of 0, and the
  simulations without category (with `apply_category_mapping()`) are kept; the groups of `split_by` are
  normalised with their table.
- The combinations of comfort standard and comfort mode that have no setpoints (comfort standards 4, 5 and 99
  with the comfort modes 0, 1 and 2; 6 with 0 and 1; 11 with 0) are skipped with a warning. Before, accim wrote
  output IDFs for them, which stopped EnergyPlus (a setpoint used before it is set).
- With natural ventilation only (`hvac_mode` 1), the ventilation controls 2 and 3, which only apply to mixed
  mode, are skipped.
- The tolerances from `ast_tol_start` to `ast_tol_end_input` do not depend on the rounding of the floats: before,
  0.1 to 0.3 in steps of 0.1 also gave 0.4.
- The output IDFs are written directly, without the intermediate files `*_pymod.idf`, and much faster.
- The People objects are changed in place: before, accim created them again, and their empty fields took the
  defaults of the IDD (the cold and heat stress temperature thresholds, 15.56 and 30 °C).
- With `ThermostatSetpoint:SingleCooling` objects (script types `ex_ac` and `ex_mm`), accim 0.x added the
  cooling setpoint schedule of a single zone, so EnergyPlus stopped; now it adds one for each zone.
- `make_averages=True` no longer adds the building averages of the AirflowNetwork outputs to models without
  AirflowNetwork (which stopped EnergyPlus), an empty average of the ventilation hours, or averages of the
  operative temperature that included the sensors of the windows; and it reuses the sensors of the zones whose
  names differ only in upper and lower case, which EnergyPlus took as duplicates.
- accim no longer adds program calling managers to the EMS programs that the input model already had.
- The repeated `Output:Variable` objects are removed.
- `modify_accis` keeps the current values of the arguments that are `None`, and works with the models without
  `SetVOFinputData` (fully air-conditioned).
- The prompts of the second stage keep `name_suffix`, `verbose_mode` and `confirm_gen` of the call.
- `output_idfs` maps the name of each output IDF to its own IDF object (read when it is used).
- `run_ep` names the output files after the whole name of the EPW: before, it cut the name at its first dot
  (`model[USA_CO_Golden-NREL` for `USA_CO_Golden-NREL.724666_TMY3.epw`), so the EPWs whose names differ after a
  dot overwrote each other's results.
- Importing accim no longer imports besos, dask and platypus or changes them; the patches that besos needs are
  applied by `accim.parametric_and_optimisation`. `accim.sim` does not import besos either, so it is imported
  much faster.
