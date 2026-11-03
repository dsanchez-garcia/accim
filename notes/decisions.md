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

## 2026-11-03 — The radiant systems, ventilated slabs and cooling panels follow the setpoints with `existing_hvac_radiant_setpoints`

- **Status**: accepted (the author answered the TODO item on 2026-11-03: "yes, but as one or several True/False
  arguments that apply the change or not, in line with the previous decisions", and chose `True` as the default)
- **Context**: with `ex_ac` and `ex_mm`, these objects heat or cool with setpoint schedules of their own, not with
  the thermostats, so their zones kept the setpoints of the model (65 to 82 % of the occupied hours of the example
  file `RadLoHydrHeatCoolAuto` of EnergyPlus within the setpoints, in a year in Seville). Since 2026-11-02 accim only
  warned about them.
- **Decision**: one argument, `existing_hvac_radiant_setpoints` (`True`), in `AddAccis`, `add_accis_to_idf`, the
  classes of the parametric module and the GUI. Those of the occupied zones get the setpoint schedules of their zones
  in the setpoint fields that they have (so they keep heating, cooling or both) and the operative temperature as their
  control temperature; the constant flow systems and ventilated slabs get the same schedule as high and low control
  temperature (on/off at the setpoint, which EnergyPlus accepts: checked in its sources); the `:Design` objects shared
  by several zones are copied per zone; the cooling panels of zones with a thermostat get `ZoneTotalLoad` instead,
  because their operative temperature control gave plant flow errors in `5ZoneCoolingPanelBaseboard`. `False` keeps
  them as in 0.x, with the warning.
- **Consequences**: the output IDFs of the models with these objects change by default (none of the golden master);
  `RadLoHydrHeatCoolAuto` reaches 99.5 to 100 % within the setpoints, and the hours that remain in other example files
  come from the models (radiant systems that only heat, slow slabs, capacity). The zones whose radiant systems follow
  the setpoints are not reported as zones without a thermostat. Section 4.1.1 of [[../docs/source/4_detailed use.md]].

## 2026-11-03 — The GUI shows the `existing_hvac_*` arguments with the existing HVAC systems

- **Status**: accepted (answer of the author to the TODO item on 2026-11-03)
- **Context**: the tab *Add the ACCIS* used the defaults of these arguments without showing them.
- **Decision**: a frame with the four booleans and the availability schedule (empty, `On 24/7` or any schedule
  typed), enabled with `ex_ac` and `ex_mm` (the two options of the setpoints only with temperature setpoints), in
  *Add the ACCIS* and in *Parametric study* (with `ex_ac`, its only existing HVAC script type). The other script types
  do not get these arguments.
- **Consequences**: `accim/gui/forms.py` (`EXISTING_HVAC_*`, `existing_hvac_arguments`), `app.py`, `tasks.py`;
  tests in `tests/core/test_gui.py`.

## 2026-11-03 — ESP CTE and INT ISO7730 keep one row per combination of the other parameters in the full sets

- **Status**: accepted (answer of the author to the TODO item on 2026-11-03)
- **Context**: `drop_invalid_param_combinations` dropped all the rows of ESP CTE (`comfort_standard` 0) when the
  plan had `category` or `comfort_mode`, and kept INT ISO7730 (22) only with `comfort_mode` 0, although their
  setpoints do not depend on these parameters (ESP CTE: neither; ISO7730: not on the comfort mode).
- **Decision**: their rows are kept only with the first value of these columns in the plan (`pd.unique(...)[0]`),
  so each one is simulated once for each combination of the other parameters.
- **Consequences**: plans with these columns can compare ESP CTE with the other standards; the results tables have
  one row of them per combination, with the first category and comfort mode of the plan. Migration guide, 9.3.

## 2026-11-03 — The heating setpoints of CHN Yang with `ComfMod` 2 are those of the source of the standard

- **Status**: accepted (the author checked the formulas of `(6, 2)` and `(6, 3)` against the source and corrected 2
  lines of `(6, 2)` on 2026-11-03); supersedes the decision of 2026-10-31 on comfort standard 6 below
- **Context**: within the applicability limits, the heating setpoint of `(6, 2)` used the formula of the cooling
  setpoint, as in 0.x.
- **Decision**: `PMOT*0.32+14.88` (category 80) and `PMOT*0.31+17.14` (category 90), as in `(6, 3)`.
- **Consequences**: the subprogram `SetAST_CS6_0` changes in every output IDF (every configuration of the golden
  master was written again, and only these 2 lines differ); the results change only with comfort standard 6 and
  comfort mode 2. Test in `tests/core/test_setast_chn_yang.py`.

## 2026-11-02 — The existing HVAC systems keep the operative temperature between the setpoints with arguments `existing_hvac_*`

- **Status**: accepted (asked by the author on 2026-11-02, who chose the default of the operative temperature control,
  the availability as an option with a warning, and the names; the rest was done while he asked to work
  autonomously, "if they are False, it is simulated as it is", so he may revise it)
- **Context**: With `ex_ac` and `ex_mm`, the operative temperature could be out of the adaptive setpoints in many
  hours (the author used the VRF systems of accim instead). The causes (simulations in
  [[../DEVLOG.md]], 2026-11-02): the existing thermostats controlled the air temperature, while the VRF systems of
  accim control the operative temperature; accim only gave the setpoints to the first control of each thermostat
  (the thermostats of the example files of EnergyPlus kept the setpoints of the model, and EnergyPlus stopped); the
  HVAC systems may be unavailable while the zones are occupied, may lock out their compressors or heaters with some
  outdoor temperatures, or may lack capacity, controls or equipment that heats or cools; and the radiant systems,
  ventilated slabs and cooling panels follow setpoint schedules of their own.
- **Decision**: four arguments of `AddAccis`, `add_accis_to_idf` and the classes of the parametric module, in
  `accim/sim/hvac/existing.py`: `existing_hvac_operative_temperature_control` (`True`: the thermostat of each
  occupied zone uses only a dual setpoint object of its own with the schedules of the zone, always, and controls the
  operative temperature as those of the VRF systems; `False`: the thermostats as in accim 0.x);
  `existing_hvac_availability_schedule` (`None`, with a warning; a schedule for the HVAC objects that heat or cool,
  the operation schemes with one scheme and the availability managers of the air and plant loops);
  `existing_hvac_widen_outdoor_temperature_limits` (`False`, with a warning; the limits of the VRF systems, -20 and
  80 °C, within the IDD); and `existing_hvac_ideal_loads_backup` (`False`; an ideal loads air system as the last
  equipment of each occupied zone, for the load that the existing system does not meet, whatever it is). Only
  warnings for the objects with setpoints of their own.
- **Consequences**: the output IDFs of the models without operative temperature thermostats change by default (the
  OSM office of the golden master: `b10`, `b11`, `s04`); those of DesignBuilder and of the VRF systems do not. The
  models with the thermostats of the example files of EnergyPlus simulate. With all the options, the sample models
  have 99.7 to 100 % of the occupied hours between the setpoints in a year in Seville; the energy of a backup is
  reported apart (district heating and cooling), as the loads that the existing system does not meet. Pending
    ([[../TODO.md]]): the radiant systems following the setpoints, and the arguments in the GUI (both done on
    2026-11-03, see the decisions above).

## 2026-11-02 — The arguments and parameters have descriptive names, the same in the whole package

- **Status**: accepted (the author's answer of 2026-11-02 to the open question of the names: option (a), and the
  parametric module too)
- **Context**: The names of 1.0.0 were a mechanical translation of those of 0.x to snake case
  ([[#2026-10-30 — PEP 8 names with deprecated aliases for accim 0.x|decision of 2026-10-30]]), with their
  abbreviations (`comf_mod`, `cat`, `vst_offset`...). The author asked for a review ("`ComfMod` no me gusta"), chose
  the suggested names, and asked that the arguments and parameters of `accim.parametric_and_optimisation` take the
  names of `accim.sim` ("el módulo debe ser consistente con el resto"), although the decision of 2026-10-30 had kept
  them.
- **Decision**: The arguments of `AddAccis`, `add_accis_to_idf`, `modify_accis` and `zone_arguments`, of
  `apply_apmv_setpoints` and the other functions of `accim.sim.apmv`, of `run_ep`, and the arguments, attributes and
  parameters of the parametric module have descriptive names, the same everywhere: `comfort_standard`, `category`,
  `comfort_mode`, `setpoint_type`, `output_frequencies`, `ventilation_control`, `min_opening_factor`,
  `setpoint_tolerance`, `custom_slope`..., `adaptive_coefficient_cooling`, `pmv_cooling_setpoint`,
  `only_accim_idfs`, `processes`, `use_default_values`... (the full list is in §9.2 of
  [[../docs/source/9_migration_guide.md]]). The names of 0.x stay as deprecated aliases with `DeprecationWarning`:
  arguments (`accepts_legacy_kwargs`), attributes of the parametric classes, names of parameters (`'ComfStand'`,
  `'CustAST_m'`... in `set_parameters`, `accis_parameter`, the samples and the plans) and columns of the results
  saved with 0.x, renamed when they are loaded. The snake-case names of the earlier commits of `v1.0.0` were never
  released, so they get no alias. The EMS variables (`ComfStand`, `CAT`...), the tags of the names of the output
  IDFs (`[CS_`, `[CA_`, `[CM_`...), the columns of `Table`, the texts of the prompts, the `modify_*` functions of
  `param_accis` and the class names of the wrappers of `parameters.py` keep their names: they are read by the EMS
  programs, by `Table` or by the results of earlier versions.
- **Consequences**: The output IDFs do not change (golden master). The scripts, notebooks and saved results of 0.x
  keep working with warnings; the documentation and the example notebooks use the new names. The aliases are removed
  with the others in a future major version ([[../ROADMAP.md]], R-03).

## 2026-11-02 — The GUI keeps tkinter and gets tabs for more steps

- **Status**: accepted (the author's answer of 2026-11-02 to the open question of the GUI: the first option)
- **Context**: [[#2026-11-01 — The first GUI uses tkinter and covers AddAccis, run_ep and the hours within the setpoints|The first GUI]]
  had three tabs; the open question offered more tabs with tkinter, a web interface as an optional extra, or leaving
  the rest in Python.
- **Decision**: tkinter, with seven tabs that share the working folder: *Add the ACCIS* (now with a table of the
  arguments of some zones, `zone_arguments`, and the occupied zones of the IDF), *aPMV setpoints*
  (`apply_apmv_setpoints`, the same setpoints in all the zones), *Rename the EPWs* (`rename_epw_files`), *Run the
  simulations*, *Hours within the setpoints*, *Table and figures* (`Table`, its scatter and time plots saved as PNG
  files) and *Parametric study* (a basic `ParametricSimulation`: full set or Latin hypercube, sums of meters). The
  forms stay in `forms.py` and the tasks that call accim are in `tasks.py`, both without tkinter, so they are tested
  without a display. A task can get fixed answers for the questions of the prompt that the GUI knows (those of
    `rename_epw_files` about amending or excluding EPWs, and those of the figures of `Table` about renaming the rows and
    columns of the subplots); any other question stops it with an error.
- **Consequences**: No new dependency. Still in Python only: the `custom` output type, different aPMV setpoints for
  each zone, the other figures and the reshaping of `Table`, and the outputs, objectives, optimisations and plots of
  the parametric module. eppy keeps one IDD per process, so IDFs of different EnergyPlus versions need a new session
  of the GUI.

## 2026-11-02 — The check of `claude/admiring-cori-fe6c57` is ported to `v1.0.0`, and the branch is deleted

- **Status**: accepted (the author asked on 2026-11-02 for the recommended option)
- **Context**: The local branch `claude/admiring-cori-fe6c57` (2 commits of 2026-10-19 on the old `master`, with a
  worktree in `.claude/worktrees/`) kept the `tests` package out of the wheel of accim, which `setup.py` of `v1.0.0`
  already does, and added a check to `packaging/release.py check` and the update of [[../packaging/README.md]]
  (its §7 still listed the problem as pending). Merging it conflicts in `CHANGELOG.md`, `notes/work-log.md` and
  `setup.py`.
- **Decision**: port only what `v1.0.0` lacked: the check of `release.py` (no top-level entry in the wheel of accim
  other than `accim` and its `.dist-info`), step 5 of §4.3 of the guide without its §7, and the CHANGELOG entry (the
  0.8.2 wheel installed `tests`). The branch was saved in a git bundle in the git-ignored
  `llm_project_files/branch_review_reports/`, and its worktree and the branch were removed (git refused to remove the
  worktree while its gitdir had an empty `modules` folder, which was deleted first).
- **Consequences**: checked with a wheel of `v1.0.0` built in a temporary folder (only `accim` and its
  `.dist-info`: no problem) and with a copy that adds `tests/__init__.py` (reported). `master` gets the change
  when it is fast-forwarded to `v1.0.0`.

## 2026-11-01 — The first GUI uses tkinter and covers AddAccis, run_ep and the hours within the setpoints

- **Status**: superseded in its scope by [[#2026-11-02 — The GUI keeps tkinter and gets tabs for more steps]]
  (accepted for the first version: priority task asked by the author on 2026-11-01; its item said that he would
  choose the scope and the technology, which he did on 2026-11-02)
- **Context**: A GUI in English, so that users without Python can add the ACCIS, run the simulations and look at the
  results. accim is used on Windows with EnergyPlus; its steps print a lot, ask in the prompt when an argument is
  missing, run long and use processes (`run_ep`).
- **Decision**: tkinter (with Python on Windows and macOS: no new dependency) in a package `accim.gui`, with the
  command `accim-gui` (`console_scripts`, so that EnergyPlus keeps a console) and `python -m accim.gui`. Three tabs
  with a common working folder: `AddAccis` (all the arguments of its prompts, except `custom` outputs and the
  arguments of each zone), `run_ep` (both backends) and the hours within the setpoints
  ([[../DEVLOG.md]], 2026-11-01). The logic of the forms (`forms.py`: choices, defaults, checks, the arguments of
  accim, the preview of the number of output IDFs) does not import tkinter, so it is tested without a display. Each
  task runs in a thread, in the folder, with its output in a log and `input()` raising an error (the GUI gives all
  the arguments, so a prompt is a bug).
- **Consequences**: no `Table`, figures, aPMV setpoints or parametric module in the GUI yet; Linux users may need
  `python3-tk`; the documentation mocks tkinter (`autodoc_mock_imports`). The tests of the window are skipped where
  tkinter cannot open one.

## 2026-11-01 — `ex_mm` reads whether the HVAC system is off from the load that the thermostat asks for

- **Status**: accepted (priority task asked by the author on 2026-11-01; the design was chosen while he could not
  answer, so he may revise it)
- **Context**: In mixed mode, the windows of a zone open only when its HVAC system is off. `ex_mm` found one heating
  and one cooling object of each zone and read their coils, which failed with several kinds of coils, with zones
  without cooling (or heating) equipment and with central systems, and needed `hvac_zone_map` when it could not find
  the zone of an object. The task asked to identify all the equipment of each zone (zone equipment, air loops, plant
  loops, baseboards, radiant systems...). The zone outputs of the air system (`Zone Air System Sensible
  Heating/Cooling Rate`) are not a state: a DOAS keeps them above 0, and they leave out the heat of the
  baseboards.
- **Decision**: read, for each zone (and the zone of each window), the load to the setpoints that its thermostat asks
  the HVAC system for (`Zone Predicted Sensible Load to Setpoint Heat Transfer Rate`, previous timestep): the HVAC
  system is off when it is 0, whatever the equipment. `vrf_mm` keeps its coils (its results do not change). No
  topology: the resolver of the zones of the HVAC objects is removed, and `hvac_zone_map` is deprecated without
  effect.
- **Consequences**: the four sample models simulate, the PTACs give the same results as with their coils, and the
  windows no longer stay open while the beams cool. Each occupied zone needs a thermostat (as with `ex_ac`). A zone
  whose thermostat has a cooling setpoint but no equipment that cools keeps its windows closed while the thermostat
  asks for cooling (HVAC mode 2 opens them only below the cooling setpoint anyway: no such timestep in the sample
  model with radiators). An HVAC system that is not available when the thermostat asks for a load counts as on.

## 2026-11-01 — The hour counters are corrected, and the percentage within the setpoints is computed from them in Python

- **Status**: accepted (priority task asked by the author on 2026-11-01; the design was chosen while he could not
  answer, so he may revise it)
- **Context**: The author asked that the hours within the setpoints (the EMS output of the comfortable hours, or
  similar) be easy to measure, to filter out the simulations below a percentage. The ACCIS had the counters
  (`Occupied Comfortable Hours_No Applicability_<zone>`, `Occupied Hours_<zone>`...), but they were wrong (see
  [[../DEVLOG.md]], 2026-11-01): the occupied comfortable hours kept their value out of the setpoints and could
  exceed the occupied hours, `CountHours_<zone>` set nothing below the heating setpoint and used the setpoints of
  the previous timestep. A percentage is a ratio of two sums, which one EnergyPlus output cannot give at every
  reporting frequency, and a reader of besos reads one output.
- **Decision**: correct the counters (all set in every timestep; `CountHours_<zone>` after `SetASTnoTol`, so
  `ACSTnoTol`/`AHSTnoTol` are results of each zone, not state) and compute the percentages in Python from the
  sums of the two existing counters, in `accim.data.postprocessing.setpoint_hours` (`hours_within_setpoints`,
  `filter_by_hours_within_setpoints`), for the CSV files of `run_ep` and for any table with one row per
  simulation (the results of the parametric module with readers of the counters, named after them). The building
  is the ratio of the sums over its zones. No new EMS output: a per-timestep status (1, 0, -1 as the comfort
  status of EnergyPlus) would work as one reader, but its hourly averages mix the occupied and unoccupied
  timesteps of an hour. For an optimisation, the sum of `Occupied Discomfortable Hours_No Applicability_<zone>`
  is the constraint (the occupied hours of a model and weather file do not change between evaluations).
- **Consequences**: the counters of the output IDFs change (the golden master was written again), not the setpoints
  or the other results; the models of earlier versions keep their counters. `make_averages` no longer stops
  EnergyPlus (`b02`, `b17`). The block and building totals of `Table` only add up the outputs of the zones. The
  aPMV setpoints (`accim.sim.apmv`) have their own counters, without occupied comfortable hours, which the module
  does not read.

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
  previous timestep; see [[../TODO.md]]); later the same day, the decision above moved `CountHours_<zone>` after
  `SetASTnoTol`, so `ACSTnoTol` and `AHSTnoTol` are no longer restored.

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

- **Status**: superseded on 2026-11-03 by "The heating setpoints of CHN Yang with `ComfMod` 2 are those of the source
  of the standard" (above): the author checked them and corrected them
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

- **Status**: accepted; the mechanical translation of the names and the parametric module keeping its names are
  superseded by [[#2026-11-02 — The arguments and parameters have descriptive names, the same in the whole package]]
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
