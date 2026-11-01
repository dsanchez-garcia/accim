---
title: Decisions
type: log
tags: [vault, decisions, adr]
created: 2026-09-13
---

# Decisions

Durable architectural/process decisions for this repository and its Obsidian
vault. Newest first. Use [[templates/decision-record.md|the decision-record
template]] to add a new entry.

## 2026-11-01 — Each zone has its arguments in `SetInputData_<zone>`, run by `RunACCIS_<zone>` with the shared programs

- **Status**: accepted (asked by the author on 2026-11-01, who chose the options of the API, the outputs and the
  models of earlier versions)
- **Context**: The author asked that the user can give the arguments of the ACCIS (comfort standard, category,
  comfort mode, HVAC mode...) for each zone or space, and that all the inputs be in one program (`SetInputData`)
  per zone. The ACCIS had one value of each argument for the whole model, in five programs (`SetInputData`,
  `SetVOFinputData`, `ApplyCAT`, `SetAppLimits`, `SetAST`), and all its programs calculated one set of setpoints
  with global variables; the subprograms of the setpoints have about 3000 lines.
- **Decision**: each occupied zone (each target of `resolve_targets`) has all its inputs in
  `SetInputData_<zone>` (`accim/sim/ems/inputs.py`, `INPUT_VARIABLES`, with the names of 0.x for the EMS
  variables until the review of the names), and a program `RunACCIS_<zone>`, the only one with a calling manager
  besides `SetGeoVar<zone>` and `InitASTvariables`, runs it and then the shared programs, in the order in which
  they ran for all the zones (so the subprograms are not repeated for each zone). The variables that the shared
  programs read before setting them in a timestep (`ACST`, `AHST`, `ACSTnoTol`, `AHSTnoTol`, `ComfTemp`,
  `CoolingSeason`) are restored and stored for each zone, and initialised at each new environment (the setpoints
  as Null, so that a zone without setpoints still stops EnergyPlus). The user gives `zone_arguments={zone:
  {argument: value}}` to `AddAccis` (the same in all the output IDFs, checked before writing them) and to
  `modify_accis` (`None` keeps the values of each zone); the zones by name, key of the aPMV setpoints or EMS name.
  The setpoints of each zone are new outputs, and those of the whole model keep their names (the values of the
  last zone). The models of earlier versions keep their programs, which `modify_accis` and the parametric module
  still set, without arguments per zone.
- **Consequences**: the EMS objects of the output IDFs change (the golden master was written again); with the
  same arguments in all the zones, the results do not change (simulations of up to four output IDFs of each
  configuration of the golden master, compared output by output, and the two backends); with different
  arguments, the setpoints of each zone equal those of a model whose zones all have its arguments. The EMS
  runs the shared programs once per zone. `get_accim_args` returns one dictionary per zone. Not done: per-zone
  parameters in `accim.parametric_and_optimisation` (its parameters set all the zones) and per-zone setpoints in
  `Table`. The program order of 0.x is kept, including its quirks (`CountHours_<zone>` reads the setpoints of the
  previous timestep; see [[../TODO.md]]).

## 2026-10-31 — Two parts of the integrity block of `review/refactor-sim-v1-20261024` are adapted, the rest dropped

- **Status**: accepted (the recommendation of [[questions.md]], chosen by the author on 2026-10-31)
- **Context**: That branch holds a block of versioned checkpoints with the identity of each evaluation, owned run
  folders and locks, the cleanup of owned paths only and a Pareto status with constraints, written against 0.8.2
  ([[branch-reviews.md]], section 1.3). Rebuilding it on the `main.py` of `v1.0.0` would rewrite a large part of
  it and reject the existing checkpoints. Two of its problems were real in `v1.0.0`: the Pareto status (and the
  cleanup of `keep_sim_files='non-dominated'`) ignored the constraints, and a resumed parametric run identified
  its simulations by the names of the IDF and the EPW and the parameters only.
- **Decision**: adapt those two parts, without changing how the module is used: a constraint-first dominance, as
  platypus (`accim/parametric_and_optimisation/_pareto.py`), in `_annotate_pareto_status` and in the cleanup of
  the workers; and the content of the IDF (its objects) and of the EPW, and the names of the outputs, in the
  signatures of the parametric tasks (`_content_digest`, `_build_parametric_task_signature`). Drop the rest
  (versioned checkpoint files, owned folders and locks, the patches, the benchmarks, the documentation page):
  `WorkspaceArtifactCleaner` already deletes only what appears after its snapshot.
- **Consequences**: the Pareto front of the optimisations with constraints changes (the evaluations that do not
  meet them no longer dominate those that do), and the evaluations without finite values are not pareto-optimal.
  A resumed run simulates again the tasks whose files or outputs changed, and those of the checkpoints written
  before (0.x included), without any migration. The branch was deleted on 2026-10-31, when the author confirmed.

## 2026-10-31 — The comfort objective independent of the control comes from the adaptive comfort status of EnergyPlus

- **Status**: accepted (the recommendation of [[questions.md]], chosen by the author on 2026-10-31)
- **Context**: The tag `archive/feat-comfort-metrics-experiment-api` computes comfort metrics with EMS programs,
  independent of the control ([[branch-reviews.md]], section 2). The comfort hours of accim follow the comfort
  model that accim controls, so an optimisation that changes it (the custom model of WF4, the aPMV setpoints of
  WF5) measures each evaluation against a different model; WF4 and WF5 minimise the mean operative temperature
  instead. EnergyPlus already computes, for each `People` object of the models of accim (which always get the
  adaptive models of ASHRAE 55 and CEN 15251), whether the zone is within their ranges: 1, 0, or -1 when it is
  empty or the running mean is out of range (`ThermalComfort.cc`).
- **Decision**: no EMS module. Two reducers in `objectives.py`: `hours_outside_comfort` (the occupied hours outside
  the range, from hourly values) and `fraction_outside_comfort` (their fraction of the occupied time, from hourly
  or timestep values), with an example in the overview page of the parametric module. The PMV indicators of
  `compute_hourly_indicators` wait for a study that needs them (they need the Fanger model in the `People`
  objects, which accim only adds with `temp_ctrl='pmv'`).
- **Consequences**: an optimisation can minimise the hours outside CEN 15251 or ASHRAE 55, a fixed reference,
  with no new EMS programs, outputs in the IDFs or work for the Python API backend. The objective is per zone
  (`People` object), and the hours of the design days count when the model simulates its sizing periods, as
  with the other readers. WF4 and WF5 keep their objectives. The tag was deleted on 2026-10-31, when the author
  confirmed (`checked_sum_results` and `openpyxl` are already in `v1.0.0`).

## 2026-10-31 — The fixes and tests of the branch reviews go to `v1.0.0`, before the release

- **Status**: accepted (option (a), chosen by the author on 2026-10-31)
- **Context**: [[branch-reviews.md]] marked as `port` or `adapt` six fixes and five groups of tests of
  `refactor/sim-v1`, and the strict reducer and the `openpyxl` dependency of the tag
  `archive/feat-comfort-metrics-experiment-api`, in four PRs; PR 1 (five small fixes) was already in the working
  tree of `v1.0.0`. The options were: (a) everything on `v1.0.0` before the release; (b) PR 1 on `v1.0.0`, the rest
  on `master` after the merge.
- **Decision**: (a). On 2026-10-31, `v1.0.0` got PR 2 (`objectives.checked_sum_results` and `openpyxl` in
  `install_requires`), PR 3 (the tests of sim-v1 adapted to `tests/core`, with the repair of
  `Table.wrangled_table(reshaping='pivot')`) and PR 4 (the golden master of the output IDFs in
  `tests/core/golden_master`, which also repeats the comparison with 0.8.2, and `tools/compare_backends.py`).
- **Consequences**: `v1.0.0` holds everything that the reviews proposed to keep from `refactor/sim-v1` and the
  comfort-metrics tag. After the decisions on the other two questions (above), the four refs of the reviews were
  deleted on 2026-10-31, when the author confirmed (see [[branch-reviews.md]]).

## 2026-10-31 — accim removes the ideal loads systems of the input model when it adds its VRF systems

- **Status**: accepted (chosen by the author on 2026-10-31)
- **Context**: `hvac/vrf.add_vrf_objects` replaces the zone equipment lists and connections of the model with
  those of the VRF systems, but kept its `ZoneHVAC:IdealLoadsAirSystem` objects (with their availability set to
  'On' by `set_ideal_loads_availability_on`), so they were left unconnected and EnergyPlus reported one severe
  error for each of them in every run ("Orphaned ZoneHVAC object found"), as in 0.x ([[branch-reviews.md]],
  section 3). The options were: remove them; keep the behaviour of 0.x.
- **Decision**: remove them. `add_vrf_objects` removes all the `ZoneHVAC:IdealLoadsAirSystem` objects of the model,
  with `AddAccis`, `add_accis_to_idf` (and so `accim.parametric_and_optimisation`) and
  `accim.sim.apmv.add_vrf_system`; `set_ideal_loads_availability_on` (new in 1.0.0, with no alias) was removed. The
  existing HVAC systems (`ex_ac`, `ex_mm`) keep them.
- **Consequences**: the output IDFs with the VRF systems lose these objects (17 of the 29 configurations of the
  golden master; nothing else changes), and their results do not change: with the sample model, Seville and a whole
  year, the hourly CSV files of `AddAccis` (`vrf_ac`) and of the aPMV setpoints are identical, without the 2 severe
  errors.

## 2026-10-31 — The setpoints of comfort standard 6 with `ComfMod` 2 stay as in 0.x until they are checked

- **Status**: accepted (by the author on 2026-10-31, as a provisional decision; the check is a TODO item)
- **Context**: In `accim/sim/ems/setpoint_lines.py`, key `(6, 2)` (CHN Yang), the heating setpoint uses, within the
  applicability limits, the formula of the cooling setpoint (`PMOT*0.30+25.9` with `CAT` 80, `+23.6` with 90), as
  in 0.x (question of the review of 2026-10-24, [[branch-reviews.md]], section 1.4). With `ComfMod` 3, the heating
  setpoint is `PMOT*0.32+14.88` (`CAT` 80) or `PMOT*0.31+17.14` (`CAT` 90). The applicability limits of this
  standard are -7 to 30 °C and its category offsets are 0, so both setpoints are almost always equal: for
  instance, 30.4 °C for a PMOT of 15 °C with `CAT` 80, against a heating setpoint of 19.7 °C with `ComfMod` 3.
- **Decision**: keep them as they are for now, and check them later against the source of the standard.
- **Consequences**: the output IDFs and results of this combination do not change. If the check finds an error,
  its fix changes them (in the golden master, the configuration `b01`), with a CHANGELOG entry.

## 2026-10-31 — The air-conditioned parametric notebooks close the windows of the sample model

- **Status**: accepted (option (a), chosen by the author on 2026-10-31)
- **Context**: The sample model of the parametric notebooks (`OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520*.idf`)
  has two `ZoneVentilation:WindandStackOpenArea` objects (2 m2 per zone) with the schedule `Always On Discrete
  hvac_library`, without temperature limits. accim only controls them with the mixed-mode script types (`vrf_mm`,
  as `AddAccis` since 0.7.8). WF1 and WF4 used `ScriptType="vrf_ac"` with `HVACmode` 0, and 03, WF3 and WF5 apply
  aPMV setpoints, which only control the HVAC system, so these "fully air-conditioned" examples heated and cooled
  with the windows open all year (also with 0.8.2): heating 4-53 kWh/m2 (WF1), 2-51 (WF4), 52-71 (03), against
  0-1 in WF2 in air conditioning, with the windows closed. Found by the review of the texts of the notebooks run
  again with 1.0.0. The options were: (a) WF1 and WF4 with `ScriptType="vrf_mm"` and `HVACmode` 0, so that accim
  closes the windows, and the aPMV notebooks closing the ventilation objects; (b) a variant of the sample model
  without natural ventilation; (c) keep them and explain it in their texts.
- **Decision**: (a). WF1 and WF4 add the VRF system with `ScriptType="vrf_mm"`, and `modify_HVACmode(building, 0)`
  keeps the windows closed (with `HVACmode` 0, `SetWindowOperation_<window>` sets their opening factor to 0). 03,
  WF3 and WF5 set the `Opening_Area_Fraction_Schedule_Name` of the `ZoneVentilation:WindandStackOpenArea` objects to
  the `Always Off Discrete` schedule of the model. accim itself does not change: with `vrf_ac` and `ex_ac` it
  leaves the natural ventilation of the model as it is, as `AddAccis` always has; Detailed use and the overview
  page of the parametric module now say so, with these two ways of closing the windows.
- **Consequences**: The five notebooks describe fully air-conditioned buildings with their windows closed, as their
  texts said. Their results change: for instance, the HVAC electricity of WF3 goes from 171-228 to 67-87 kWh/m2 and
  the heating of 03 from 52-71 to 3-13 kWh/m2, close to WF2 in air conditioning. They were run again and their
  texts checked against the new results (see [[../DEVLOG.md]]).

## 2026-10-31 — The hourly tables of the parametric module follow the calendar of EnergyPlus

- **Status**: accepted (to be confirmed by the author: it changes the daily and monthly tables, and the year of
  the hourly tables without `start_date`)
- **Context**: EnergyPlus labels each hourly or timestep value with the end of its interval (01:00 to 24:00) and
  writes no year. The hourly methods labelled the values from `'2024-01-01 01'` (the default `start_date`, and
  the year of the dates read from the CSV files), a leap year, and grouped them by the day of their label. So the
  value of 24:00 went to the next day and month (a 3-day run gave 4 daily rows), and a standard year of 8760
  hours got a 29 February, with every value from 1 March labelled one day early. Found by the regression tests
  of the post-processing (TODO P1). The options for the year were: keep 2024 and skip 29 February (labels
  that are not evenly spaced), a year chosen from the length of the series, or keep it and document it.
- **Decision**: Without `start_date` (or with the date read from the CSV files), the year is 2024 only for 8784
  hourly values, and 2023 otherwise; an explicit `start_date` keeps its year. The default of the argument is
  still `'2024-01-01 01'` (a `str` subclass, `_AutoYearStartDate`, marks it as automatic), so the signatures do
  not change. The daily and monthly aggregation moves the labels back one second before grouping when the step
  is one hour or less and the first label is not at midnight (labels at the start of each interval, and daily
  or monthly values, are grouped as they are).
- **Consequences**: Each day of the daily tables has its 24 values, and each month its hours. The hourly tables
  without `start_date` are labelled in 2023 for a standard year, so the scripts that select dates of 2024 in them
  must pass `start_date` (the tests and notebooks of the repository already do). Tests:
  `tests/parametric_and_optimisation/test_normalised_units_aggregation.py`.

## 2026-10-31 — `population_size` is the size of every generation, and the settings of the algorithms are checked first

- **Status**: accepted (to be confirmed by the author: it changes the results of 5 algorithms)
- **Context**: `run_optimisation()` documents `population_size` as the number of individuals (EnergyPlus
  simulations) of each generation, but platypus 1.4 takes the size of the generations of some algorithms from
  other options, 100 by default: `swarm_size` (OMOPSO, SMPSO) and `offspring_size` (CMAES, GeneticAlgorithm,
  EvolutionaryStrategy). It ignored `population_size` for the swarms and CMA-ES (its `Algorithm` swallows unknown
  keyword arguments) and took it only as the initial population of the other two, so these optimisations ran 100
  simulations per generation. Also, PAES (one solution, one parent) could not run, `ParticleSwarm` is abstract,
  and several algorithms need options or kinds of parameters that `run_optimisation()` did not check, so they
  failed with the errors of platypus after the first case had started (the 16-algorithm smoke test hid some
  failures: with `evaluations=2` most algorithms stopped after the initial population, so OMOPSO and
    EvolutionaryStrategy never reached their first iteration, which failed).
- **Decision**: `population_size` is also passed as `swarm_size` or `offspring_size` (`algorithm_options` can
  still give them); PAES gets no `population_size`, and PAES and EvolutionaryStrategy (one parent for each
  solution) get a mutation as their variator, instead of the crossover that besos gives every algorithm (with it,
  EvolutionaryStrategy stopped after the initial population); `_check_optimisation_algorithm()`
  raises clear errors before anything is written (`ParticleSwarm`; `epsilons` and `divisions_outer`; SPEA2 with
  fewer than k + 2 solutions; categorical parameters with OMOPSO, SMPSO and CMAES; NSGAIII with maximised
  objectives; single-objective algorithms with several objectives). The list of accepted names keeps all the
  algorithms that can run; `ParticleSwarm` gets its own error instead of disappearing silently.
- **Consequences**: The optimisations with OMOPSO, SMPSO, CMAES, GeneticAlgorithm and EvolutionaryStrategy run the
  planned number of simulations, and their results change (CHANGELOG, migration guide 9.3). The requirements are
  in the docstring of `run_optimisation()`. Tests: `test_optimisation_algorithms.py` (fast) and
  `04_test_optimization.py` (each algorithm iterates at least once with EnergyPlus).

## 2026-10-31 — The subprograms of ESP CTE and INT ISO7730 set their setpoints whatever `ComfMod` is

- **Status**: accepted (to be confirmed by the author, who was given the two options in `TODO.md`)
- **Context**: The setpoints of ESP CTE (`ComfStand` 0) and INT ISO7730 (22) do not depend on the comfort mode,
  but their subprograms (`SetAST_CS0_0`, `SetAST_CS22_0`) only set them in the branch `ComfMod == 0`. The
  output IDFs of `AddAccis` set `ComfMod` 0 for them, but the models of `accim.parametric_and_optimisation`
  keep the `ComfMod` of their baseline (3), so their plans with `ComfStand` 0 or 22 stopped EnergyPlus
  ("Variable = 'ACST' used in expression has not been initialized!" in `SetASTnoTol`), also in 0.8.2. The
  options were: (1) these subprograms set the setpoints whatever `ComfMod` is; (2) the setter of `ComfStand`
  of the parametric module sets `ComfMod` 0 for them.
- **Decision**: (1). `ems/setast.py` writes the lines of the comfort standards whose only key in
  `SETPOINT_LINES` is `(ComfStand, None)` (`depends_on_comfort_mode()`) without the branches of `ComfMod`
  (13 and 14 also have that key, as a fallback, so they keep them). The fix lives in the EMS programs, where the
  bug is: it works with any `ComfMod` of `SetInputData`, with the plans of every sampling method, with
  `modify_accis` and with the edits by hand, while (2) only covered the parametric setter. `modify_accis`
  rewrites these two subprograms in the models of earlier versions (those of `bypass_addAccis=True`), as it
  already adds `SetAST_Master` to the models of accim before 0.8.
- **Consequences**: The text of the two subprograms changes in every output IDF, not the results (golden
  master: the 426 output IDFs with ACCIS differ only in these two programs). The parametric plans with
  `ComfStand` 0 or 22 run. The plan filter of the predefined models still drops `ComfStand` 0 when the plan
  has `CAT` or `ComfMod` (see `TODO.md`). Tests: `tests/core/test_setast_static_standards.py`,
  `tests/core/test_modifyaccis_setast.py`, `08_test_accim_predef_model.py`.

## 2026-10-31 — `add_accis_to_idf` and `add_vrf_system` enable the sizing calculations of the VRF systems

- **Status**: accepted (option (b), chosen by the author)
- **Context**: The VRF systems that accim adds are autosized, and EnergyPlus cannot run them without a zone
  sizing run ("For autosizing of ZoneHVAC:TerminalUnit:VariableRefrigerantFlow ..., a zone sizing run must be
  done"). `AddAccis` (IDF files) enabled the zone, system and plant sizing calculations for every script type
  (since 0.7.8), but `add_accis_to_idf` (IDF objects, used by `accim.parametric_and_optimisation`) and
  `apmv.add_vrf_system` did not, also in 0.8.2, so the parametric module could not run the models whose zone
  sizing was off. Checked with EnergyPlus 9.6 (`SF_Detached_B`, `vrf_mm`): with the zone sizing on and a sizing
  period, the model runs; without sizing periods, EnergyPlus stops ("Sizing for Zones has been requested but
  there are no design environments specified", `CheckEnvironmentSpecifications`, only when the model has
  `Sizing:Zone`, `Sizing:System` or `Sizing:Plant` objects); the system and plant sizing only add a warning when
  there are no plant loops. The options were: (a) keep 0.8.2; (b) enable them in `add_accis_to_idf` only with
  the VRF script types; (c) enable them with every script type, as `AddAccis`.
- **Decision**: (b). `add_accis_to_idf` (with `vrf_ac` and `vrf_mm`) and `apmv.add_vrf_system` call the same
  `enable_sizing_calculations()` as `AddAccis`, so both paths build the same VRF models. With `ex_ac` and
  `ex_mm`, `add_accis_to_idf` keeps the user's sizing settings: accim adds no autosized equipment to them, and
  enabling the sizing of a model with sizing objects but no sizing periods would stop EnergyPlus. Accim does not
  add sizing periods (design conditions are a modelling choice, and weather-file days would size the systems
  differently for each EPW of a study); `enable_sizing_calculations()` warns when a model has sizing objects
  but no sizing periods.
- **Consequences**: The VRF models whose zone sizing was off now run if they have sizing periods; the models
  that already ran keep their results (golden master: only `SimulationControl` changes in the 7 in-memory VRF
  and aPMV configurations; the 20 `AddAccis` configurations and the 2 `ex_*` ones are identical). `AddAccis`
  still enables the sizing of the `ex_*` models, which may stop those without sizing periods (now with the
  warning); revisit if it is reported. Tests: `tests/core/test_sizing.py`.

## 2026-10-30 — `add_accis_to_idf` builds the same model as `AddAccis`, including the scheduled natural ventilation

- **Status**: accepted (to be confirmed by the author, since it changes results of the parametric module)
- **Context**: In accim 0.8.2, `addAccis` (files) and `accis_single_idf_funcs.addAccis` (IDF objects, used by
  `accim.parametric_and_optimisation`) were separate code paths. The scheduled natural ventilation of 0.7.8
  (mixed mode through `ZoneVentilation` objects in models without AirflowNetwork) was only implemented in the
  first one, so in the parametric module the ventilation of these models was not controlled, and its
  ventilation parameters (`VentCtrl`, `MaxTempDiffVOF`, `VSToffset`...) had no effect. accim 1.0.0 builds both
  from the same model and sequence (`AccimModel` in `accim/sim/model.py`, which finds the windows and the
  scheduled ventilation, and `accim/sim/build.py`). A comparison of the parametric classes against 0.8.2
  (session script, model of the parametric notebooks) found the difference: the IDFs of `vrf_ac` and the aPMV
  setpoints are identical, and those of `vrf_mm` differ only in the objects of the scheduled ventilation.
- **Decision**: Keep one sequence: `add_accis_to_idf` applies the scheduled natural ventilation, as `AddAccis`
  does, and the change is documented as a fix (`CHANGELOG.md`, migration guide 9.3). The sizing calculations
  were decided later ([[#2026-10-31 — `add_accis_to_idf` and `add_vrf_system` enable the sizing calculations of the VRF systems|the decision of 2026-10-31]]).
- **Consequences**: The parametric and optimisation studies of mixed-mode models with `ZoneVentilation`
  objects give different results than with 0.8.2, including those of the parametric example notebooks, whose
  published pages were computed with 0.8.2 ([[../TODO.md]]). Reverting would need an option of `AccimModel`
  that skips the scheduled ventilation for IDF objects.

## 2026-10-30 — PEP 8 names with deprecated aliases for accim 0.x

- **Status**: accepted
- **Context**: The author asked to refactor accim to the conventions of Python, keeping the usage similar, and
  allowed renaming the classes and arguments that break the rules; later, the usage of
  `accim.parametric_and_optimisation` had to stay the same. Many scripts, notebooks and papers use the names
  of 0.x (`addAccis`, `ScriptType`, `ComfStand`, `runEp`...).
- **Decision**: In accim 1.0.0 the public names follow PEP 8 with a mechanical translation (`addAccis` ->
  `AddAccis`, `ScriptType` -> `script_type`, `runEp` -> `run_ep`, `apmv_setpoints` -> `apmv`...), and every
  old name stays as a deprecated alias (`accim/_deprecation.py`, `LEGACY_ARGUMENT_NAMES`) that warns with
  `DeprecationWarning`. The classes used as functions (`rename_epw_files`, `Table`) keep their names, as PEP 8
  allows. The parametric module keeps its API and only changes its internal calls. The prompts keep their
  texts.
- **Consequences**: The scripts of 0.x run unchanged (with warnings); the migration guide
  (`docs/source/9_migration_guide.md`) lists the names; the aliases are removed in a future major version
  ([[../ROADMAP.md]], R-03).

## 2026-10-30 — The Python API backend runs the EMS programs of the IDF in Python

- **Status**: accepted
- **Context**: The author wanted to use accim through the Python API of EnergyPlus in parallel to eppy and the
  EMS. The control logic of accim lives in the EMS programs that it writes in the output IDFs (SetAST,
  ApplyAST, SetWindowOperation...). Writing that logic again in Python would give two implementations to keep
  in sync, with results that could differ.
- **Decision**: The backend reads the EMS objects of the IDF, runs EnergyPlus through `pyenergyplus` without
  the programs, calling managers and actuators, and runs the programs in the callbacks of the API with an Erl
  interpreter (`accim/sim/ems/erl.py`) that follows `RuntimeLanguageProcessor.cc` and `EMSManager.cc`
  (operator grouping, Null and uninitialised values, errors while sizing, resets at each new environment,
  actuators released when Null). Sensors and internal variables are read from the Erl variables of
  EnergyPlus, so it requires EnergyPlus 24.2 or later (`getEMSGlobalVariableHandle`). `run_ep(backend='ems')`
  stays the default.
- **Consequences**: One source of truth (the IDF), identical results (checked against the EMS backend in the
  tests), and Python hooks that can read and change the variables of the programs. The interpreter must follow
  the changes of the EMS in new EnergyPlus versions (the tests compare both backends). Some EMS features are not
  supported and raise an error ([[../ROADMAP.md]], R-05).

## 2026-10-15 — Hourly results of the parametric notebooks only where they are analysed

- **Status**: accepted
- **Context**: The notebooks of `parametric_and_optimisation_examples` are
  run by users on their own computers, and hourly outputs are what makes each
  simulation heavy (about 1 MB of `eplusout.csv` per annual simulation with
  the minimal outputs). The author asked for simulations as light as
  possible, with annual results.
- **Decision**: wf1 is the only workflow that keeps the hourly results of
  every evaluation (the ASHRAE 55 screening needs them). wf2 and wf4 run in
  annual mode, without simulation folders, and then simulate again, with
  hourly outputs, only the configurations or solutions analysed hourly (wf2:
  the 4 EN 16798-1 Cat. III configurations; wf4: the non-dominated
  solutions). All of them use 2 timesteps per hour, the full-year run
  period, no design-day environments and only the outputs they read.
- **Consequences**: The screening of wf4 covers the non-dominated solutions,
  not every evaluation as in the paper. The re-simulations reproduce the
  annual results exactly, and each one is checked in the notebook. Annual
  results differ slightly from runs with the 6 timesteps of the model.


## 2026-10-15 — Ship sample files as the separate distribution `accim-samples`

- **Status**: accepted
- **Context**: `accim/sample_files` (notebooks, IDFs, EPWs, CSVs) made the
  accim wheel about 36 MB and will grow as more notebooks are added. pip
  extras cannot add files to a distribution, only extra dependencies. No
  runtime code of accim reads `sample_files`.
- **Decision**: The core `accim` distribution excludes `accim/sample_files`
  (`setup.py` + `prune` in `MANIFEST.in`). The files are published as
  `accim-samples` (built by `packaging/build_samples_dist.py`), which only
  contains `accim/sample_files/**` and installs into the same folder. The
  extra `accim[samples]` requires `accim-samples==<accim version>`, and
  `accim-samples` requires `accim==<same version>`. Only the wheel is built
  by default to reduce the size uploaded to PyPI.
- **Consequences**: Every accim release must upload both distributions with
  the same version (`dist_build_package.bat` builds both into `dist/`).
  `accim-samples` must never contain `accim/__init__.py`. PyPI's default
  per-file limit is 100 MB (the build script warns); a larger limit must be
  requested if the samples wheel grows beyond it. Installs from git only get
  the library. See [[../README.md]] and
  [[../docs/source/2_installation.md]] for user instructions.


## 2026-09-13 — Treat `AGENTS_v2.md` as the current `AGENTS.md`

- **Status**: accepted
- **Context**: The repository does not have a literal `AGENTS.md` file, but
  has [[../AGENTS_v2.md|AGENTS_v2.md]] ("AGENTS.md (v2)"), which defines
  agent design/operation guidelines for this project.
- **Decision**: [[../.github/copilot-instructions.md|Copilot instructions]]
  point to `AGENTS_v2.md` as the file to consult when instructions say
  "`AGENTS.md`, if it exists".
- **Consequences**: If a literal `AGENTS.md` is added later, update the
  Copilot instructions to prefer it (or merge both) instead of
  `AGENTS_v2.md`.

## 2026-09-13 — `notes/work-log.md` complements, not replaces, existing tracking files

- **Status**: accepted
- **Context**: The repository already separates work tracking across
  `CHANGELOG.md`, `DEVLOG.md`, `TODO.md` and `ROADMAP.md` (see
  [[../DEVLOG.md#Tracking files|Tracking files]]).
- **Decision**: `notes/work-log.md` is a lightweight, session-scoped log for
  fast context recovery (by humans or an AI assistant). It must not duplicate
  or replace the existing four tracking files; durable outcomes are still
  promoted to them as before.
- **Consequences**: Two logs exist with different scopes. Copilot
  instructions clarify which one to read for which purpose.

## 2026-09-13 — No documentation is duplicated or rewritten for the vault

- **Status**: accepted
- **Context**: The repository already has substantial documentation
  (`README.md`, `CHANGELOG.md`, `DEVLOG.md`, `TODO.md`, `ROADMAP.md`,
  `AGENTS_v2.md`, `docs/source/`, root-level reports).
- **Decision**: [[../Home.md|Home.md]] and vault notes only link to existing
  documentation with wiki links; they never copy or restate its content.
- **Consequences**: Home.md must be revisited if canonical files are renamed
  or restructured (see [[obsidian-tutorial.md#4. What NOT to do|What NOT to
  do]]).

## 2026-09-13 — Vault content stays in English, ASCII, kebab-case

- **Status**: accepted
- **Context**: The rest of the repository's process documentation
  (`CHANGELOG.md`, `DEVLOG.md`, `TODO.md`, `ROADMAP.md`) was already
  translated to English (see `DEVLOG.md`, entry *2026-06-11*). No
  multilingual pair of README/TODO exists to mirror.
- **Decision**: All new vault notes are written in English, with ASCII,
  kebab-case file and folder names under `notes/`. `Home.md` is the single
  intentional exception (Obsidian's conventional vault-index filename).
- **Consequences**: Any future vault note should follow the same convention
  for consistency and predictable linking.

## 2026-09-13 — Use the repository root as the Obsidian vault; ignore `.obsidian/` in git

- **Status**: accepted
- **Context**: The goal is persistent documentation and working context for
  this repository, browsable with Obsidian, without introducing a separate
  vault folder that would fragment the existing file layout.
- **Decision**: The repository root is the Obsidian vault. `.obsidian/` is
  added to `.gitignore` (local UI/workspace/preferences); `Home.md` and
  `notes/` are the versionable vault content.
- **Consequences**: `sync_branch.bat`'s `git clean -fd` was updated to
  exclude `Home.md` and `notes/`, since they are not committed by default and
  would otherwise be deleted as untracked files.
