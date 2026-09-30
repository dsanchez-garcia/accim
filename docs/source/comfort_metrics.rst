.. _independent-comfort-metrics:

Independent comfort metrics and paper workflows
============================================================

Why reporting EMS is needed
---------------------------

Control setpoints and evaluation criteria serve different purposes. Measuring
custom-model discomfort against the very setpoints being optimised rewards wider
bands twice: energy and nominal discomfort can both fall without improving
comfort against a fixed reference. ACCIM therefore offers an explicit,
reporting-only metric layer. It does not add actuators, modify thermostats,
change schedules, or replace native aPMV counters.

Call ``SimulationBase.add_comfort_metrics`` after ACCIS/aPMV preparation and
parameter configuration, but before output discovery, reader selection and
problem creation. Both ``ParametricSimulation`` and ``OptimisationSimulation``
inherit it. The lower-level ``accim.sim.add_comfort_metrics`` works on a prepared
IDF without registering reporting requests or readers.

Availability and API contracts
------------------------------

These APIs are unreleased source additions on
``feat/comfort-metrics-experiment-api`` (introduced in commit ``a9b9ebd``).
Install the corresponding source revision as described in
:doc:`2_installation`; do not infer availability from the package version alone.

**Low-level model API** (signature, not an invocation):

.. code-block:: text

    accim.sim.add_comfort_metrics(
        building, *, metrics=('fixed_en',), name_prefix='ACCIM_CM', dry_run=False
    )

It returns a dictionary with ``targets``, ``outputs`` (a **list of dictionaries**),
``metrics``, ``name_prefix``, ``calling_point``, ``added``, ``reused``, ``would_add``
and ``dry_run``. ``dry_run=True`` checks prerequisites and collisions without
mutating the IDF. The function neither writes the IDF nor creates Output:Variable
requests, readers or a BESOS problem. It does not invalidate a separate session's
cached discovery; use the session wrapper when managing a live session.

**Session API**, inherited by both simulation classes (signature):

.. code-block:: text

    sim.add_comfort_metrics(
        *, metrics=('fixed_en',), name_prefix='ACCIM_CM',
        idf_scope='all', output_freqs=None
    )

It returns ``{'buildings': reports_by_idf, 'outputs': dataframe}``.
The output **DataFrame** contains one row per target, metric and frequency;
columns include ``idf``, ``metric``, ``variable_name``, ``key_value``, ``units``,
``aggregation``, ``ems_variable``, ``zone_name``, ``sensor_key``, ``ems_suffix``
and ``frequency``. ``idf_scope`` accepts the usual all/first/index/name/list
selectors; ``output_freqs=None`` inherits the session's frequencies.
This method has **no public dry_run argument**: it validates all selected
buildings before adding objects and appends requests with ``validate=False``.

Use :func:`accim.sim.comfort_metrics.add_comfort_metrics` for an independent
IDF operation or :meth:`accim.parametric_and_optimisation.main.SimulationBase.add_comfort_metrics`
for scoped session setup. Neither starts EnergyPlus. Output metadata describe
aggregation but do not automatically select a reader or reducer.

Definitions
-----------

``fixed_en``
    Occupied degree-hours against a fixed EN 16798-1 Cat II reference:
    R = clamp(RMOT, 10, 30), neutral = 0.33 R + 18.8,
    lower = neutral - 4, upper = neutral + 3 (degrees Celsius).
    At each zone timestep, the increment is
    occupied * max(To - upper, lower - To, 0) * ZoneTimeStep.
    Upper +3/lower -4 follow the ACCIM EN implementation. Clamping is an explicit
    horizontal boundary-extension policy, not a claim of unlimited standard
    applicability. No optimised custom coefficient enters this reference.

``fixed_pmv``
    Occupied integral of absolute Fanger PMV, and occupied hours with
    abs(PMV) > 0.5. Divide the integral by occupied hours to obtain the occupied
    mean absolute PMV; zero occupied hours means the mean is undefined.
    These can be diagnostic outputs without becoming optimisation objectives.

Both families also provide occupied hours. Occupied means instantaneous
``People Occupant Count > 0``, not a fixed office schedule and not person-hours.
With a nonzero population, an always-on People schedule can make this gate
active throughout the year.

Outputs use ``Summed`` / ``ZoneTimestep`` and are updated at
``EndOfZoneTimestepBeforeZoneReporting``. Increments reset every timestep and
exclude warmup. Sum hourly reports directly: do not multiply them by timestep
duration again. Units are ``C-hr`` for EN degree-hours and ``hr`` for time and
PMV-time integrals (PMV itself is dimensionless).

To uses the raw zone key; occupancy, RMOT and Fanger PMV use the resolved
People/Space key. The existing ACCIS/aPMV target resolver is reused. People must
already enable ``AdaptiveCEN15251`` for ``fixed_en``, ``Fanger`` for ``fixed_pmv``,
or both for a combined request. The metric API will not invent metabolic,
clothing or occupancy schedules.

.. list-table:: Returned metric roles (the ``metric`` field)
   :header-rows: 1
   :widths: 22 28 50

   * - Role
     - Included with
     - Value and units
   * - ``occupied``
     - Either family, once per target
     - Occupied duration, hr
   * - ``fixed_en``
     - ``fixed_en``
     - Fixed-reference occupied degree-hours, C-hr
   * - ``pmv_integral``
     - ``fixed_pmv``
     - Integral of occupied abs(Fanger PMV), hr times dimensionless PMV
   * - ``fixed_pmv_hours``
     - ``fixed_pmv``
     - Occupied duration with abs(Fanger PMV) > 0.5, hr

Selecting the ``fixed_pmv`` family does not create a row whose role is
``fixed_pmv``. Select the appropriate returned role, and use the returned
``variable_name`` rather than guessing an EMS output suffix.

Scope, collisions and aggregation
---------------------------------

* ``idf_scope`` selects buildings; ``output_freqs`` selects reporting frequencies.
  The method appends requests with ``validate=False`` and never discovers or
  simulates by itself. Existing readers and objectives are left unchanged.
* New definitions invalidate the output cache. The next explicit discovery also
  ignores stale on-disk RDD/MDD dictionaries. Discovery can simulate; this remains
  a separate, deliberate operation.
* A deterministic ``name_prefix`` keeps EMS names separate. Identical repeated
  calls reuse objects; incompatible definitions, duplicate targets, globals,
  scratch-variable collisions or additional calling managers raise before new
  objects are added. Unexpected object-creation failures roll back newly added
  objects for that building.
* Results are per resolved target, not automatically averaged over buildings.
  Summing multiple zones yields zone-hours or zone-degree-hours, not building
  hours. Multiple People in a legacy zone that resolve to the same suffix are
  rejected instead of silently double-counted. Expanded Space targets may share
  a zone temperature; choosing aggregation/weighting remains a study decision.
* Do not apply ACCIS/aPMV again after adding metrics: control preparation can
  replace globals or attach predictor-time managers to existing programs.

Example: select a single-target EN objective
--------------------------------------------------

The following assumes ``sim`` is an already prepared, single-building session
with its parameter domains configured. It deliberately registers exactly one
energy reader and one EN reader, in that order. The meter name must be checked
on the simulation PC before use; no availability validation or simulation is
implicit in these setup calls::

    import pandas as pd

    reducer = "accim.parametric_and_optimisation.objectives:checked_sum_results"
    energy_readers = pd.DataFrame([{
        "key_name": "Electricity:HVAC", "frequency": "Hourly",
        "name": "HVAC electricity [J]", "func": reducer,
    }])
    sim.set_output_meters_to_idf(
        df_output_meter=energy_readers, mode="append", validate=False,
    )

    report = sim.add_comfort_metrics(
        metrics=("fixed_en",), name_prefix="StudyComfort",
        idf_scope="first", output_freqs=["hourly"],
    )
    readers = report["outputs"].loc[
        report["outputs"]["metric"] == "fixed_en"
    ].copy()
    if len(readers) != 1:
        raise ValueError("Select a target or define multi-target aggregation explicitly")
    readers["name"] = "Fixed EN occupied discomfort [C-hr]"
    readers["func"] = reducer
    sim.set_output_readers(df_output_meter=energy_readers, df_output_variable=readers)
    sim.set_problem(minimize_outputs=[True, True])

``set_output_readers`` replaces the reader list; include additional readers and
matching objective directions explicitly if needed. Meters precede variables.
The metric method itself does not change readers or optimisation objectives.

The opt-in :func:`accim.parametric_and_optimisation.objectives.checked_sum_results`
requires a result with a nonempty, one-dimensional, numeric-convertible, finite
``data['Value']``. It returns one finite Python ``float``; missing data, NaN/Inf,
multidimensional values and overflow raise ``ValueError``. It performs no unit
conversion. It is importable by workers without local functions; the legacy
permissive ``sum_results`` behavior remains unchanged. To use the strict reducer,
set ``func`` explicitly: ``aggregation='sum'`` metadata alone does not enable it.

Paper convenience API
---------------------

``accim.parametric_and_optimisation.run_paper_experiment(spec, settings, argv=None)``
owns preparation, metrics, exact LHS-plan persistence, checkpoint checks,
load-only postprocessing, unit conversion, hourly CSV parsing and per-climate
plots/compromise selection for the five single-zone case-study workflows.
It is not a replacement for the general simulation classes, and returns the
session (simulation or postprocessing), or ``None`` for help, not a DataFrame.
See :func:`accim.parametric_and_optimisation.paper_experiments.run_paper_experiment`.

The five entry scripts under ``llm_project_files/experimentos_preparados`` contain
configuration and package calls only: no function/class definitions or imports
from another experiment. ``settings['script_directory']`` must be absolute;
relative CLI paths resolve there, not inside the installed package.

``spec`` supplies ``number`` (4.1--4.5), ``kind`` (parametric/optimisation),
``parameters_type``, ``ScriptType``, ``parameters``, ``epws``, ``expected_runs``,
``sampling`` (full_set/lhs/None) and ``comfort`` (fixed_en/apmv).
Preserve Python lists for categorical domains and tuples for continuous ranges;
round-tripping the executable specification through JSON changes tuples to lists.

``settings`` requires ``script_directory``, ``idf``, ``epw_dir`` and
``results_root``; optional ``campaign``, ``result``, ``area_note`` and
``schedule_note`` set CLI defaults. The wrapper specifically requires a pristine
single-zone model, one People object/target, and one annual Jan 1--Dec 31 RunPeriod.
Its 312 m2 reporting denominator, EER/COP 4.42/4.95, LHS 100 samples and NSGA-II
population 20/budget 200 per EPW are paper choices, **not general ACCIM defaults**.
The two aPMV workflows explicitly initialise PMV cooling/heating to +0.5/-0.5;
this overrides the current generic function's -0.5/+0.5 defaults.

.. list-table:: Operations are separate
   :header-rows: 1
   :widths: 20 45 35

   * - Action
     - Effect
     - EnergyPlus execution
   * - No arguments / ``help``
     - Prints help
     - No
   * - ``prepare``
     - Copies inputs, prepares IDF/report and samples a parametric preview plan
     - No; does not run discovery
   * - ``discover --simulate``
     - Isolated reduced run, inventory and actual CSV output-contract checks
     - Yes, explicit
   * - ``new --simulate``
     - New campaign in a directory that must not already exist
     - Yes, explicit
   * - ``resume --simulate``
     - Compatible, incomplete manifested campaign only
     - Yes, explicit
   * - ``load --result ...``
     - Tables/figures from one consolidated pickle/JSON/CSV; no input IDF needed
     - Never; ``--simulate`` is rejected

Campaign execution does not automatically postprocess. Use a later ``load``
operation and select the exact consolidated file; no timestamp or "latest file"
is selected implicitly. New/resume require review notes and a matching discovery
approval. Approval checks an output contract at one representative point using
the first EPW, not numerical validity across all parameters, climates or seasons.

.. list-table:: Key CLI options
   :header-rows: 1
   :widths: 40 60

   * - Options
     - Meaning / defaults
   * - ``--idf``, ``--epw-dir``, ``--results-root``, ``--campaign``
     - Override settings; campaign defaults to paper-v1. Relative paths use script_directory.
   * - ``--simulate``
     - Required only for discovery/new/resume; absent by default.
   * - ``--approval``, ``--area-note``, ``--schedule-note``, ``--ems-note``
     - Matching approval file and explicit human review notes required for new/resume.
   * - ``--count-note``
     - Acknowledge a plan count different from the manuscript forecast (notably 4.1).
   * - ``--workers``, ``--batch-size``
     - Defaults 2 and 10; batch size is used by parametric campaigns.
   * - ``--result``, ``--legacy-area``, ``--legacy-metric-note``
     - Choose a consolidated file; declare a known old normalization area or review a legacy optimisation metric where metadata are absent.
   * - ``--legacy-path-base``, ``--old-root``, ``--new-root``
     - Explicit base for historical relative paths, followed by prefix mapping. Old/new roots must be supplied together; no basename guessing.
   * - ``--hourly``, ``--hourly-all``, ``--hourly-indices``
     - Default: no hourly reads. Select three rows (non-dominated for optimisation), all rows, or comma-separated result-row labels of the chosen climate; process one CSV at a time.
   * - ``--climate``, ``--calendar-year``
     - Climate defaults to Present. Optional display year must match the CSV's leap status; it does not identify a TMY's source year.

Load trusted files only: pickle deserialization can execute arbitrary code.
Missing/ambiguous series, unknown paths and invalid units are errors, not reasons
to relaunch a simulation. Normalized legacy data require their original area or
the raw consolidated file; comfort units are not converted to energy units.

In notebooks, pass an explicit argument list to the package function; for
parallel campaigns, use a saved main-guarded entry script. Native optimisation
resume reuses completed IDF-by-EPW cases, not an interrupted population.

Preserve the whole campaign directory, not just a checkpoint. Parametric resume
uses the exact persisted plan (no new LHS draw), completed signatures and all
result chunks. The wrapper supplements the native compatibility signatures with
input/source/configuration fingerprints; the generic run methods do not supply
these paper-specific approval gates. Loading a historical campaign means loading
its consolidated results: ``load`` rejects checkpoint files themselves. A
completed checkpoint must not be used as a shortcut to postprocessing.

The package integration uses manifest schema ``paper-prepared-v2``. Keep v1
results for load; do not bypass fingerprint mismatches to resume them under the
new implementation. When transferring a compatible v2 campaign, preserve plan,
manifest, batches, recovery files and simulation directories, including PID-suffixed
directories. Migration rewrites paths in copies, not in the archived checkpoint.

The paper's aPMV optimisation intentionally retains the native moving-reference,
all-time discomfort-hour objective. Fixed-PMV outputs are diagnostics, not a
silent replacement. Fixing the PMV setpoint or changing that objective defines
a different experiment. The handoff README records the 4.1 forecast/count
mismatch and the historical 4.2 missing-hourly-output limitation.

The handoff forecasts 132/300/36/400/400 campaign evaluations (1,268 total),
pending execution checks. The current compatibility catalogue instead implies
40 combinations / 120 cases for 4.1 because CS14 excludes ComfMod=0. Do not add
invalid combinations to meet a forecast. The archived 4.2 sidecar declares
300/300, but the inspected hourly CSV lacks PMOT and setpoints: fixing paths
does not make those regression series available.

Validation status
-----------------

As of 2026-09-30, this change was checked by source/API/IDD inspection and syntax
analysis only. Documentation examples are setup/usage illustrations, not run logs.
Hermetic regression tests are provided in ``test_comfort_metrics.py`` and
``test_paper_experiments_api.py`` but were not executed in this preparation.
EnergyPlus, discovery, preflight and experiment scripts were not run. This
documentation update does not claim a successful Sphinx/autodoc build or a
successful numerical regression suite.

Before scientific use, validate keys, Erl compilation, calling-point timing,
occupancy, timestep integration and annual totals on the simulation PC. For
RMOT=20 C, limits are 21.4/28.4 C: an occupied 0.25-hour step at To=30 C gives
0.4 C-hr; at To=20 C it gives 0.35 C-hr; comfortable/unoccupied steps give zero.
Keep error and EMS trace files. Inspect warmup, applicability boundaries, Fanger
inputs, aPMV denominator singularities and Windows worker serialization.

