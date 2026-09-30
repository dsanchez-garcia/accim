Independent comfort metrics and paper workflows
==============================================

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
An always-on People schedule will therefore produce year-round occupancy.

Outputs use ``Summed`` / ``ZoneTimestep`` and are updated at
``EndOfZoneTimestepBeforeZoneReporting``. Increments reset every timestep and
exclude warmup. Sum hourly reports directly: do not multiply them by timestep
duration again. Units are ``C-hr`` for EN degree-hours and ``hr`` for time and
PMV-time integrals (PMV itself is dimensionless).

To uses the raw zone key; occupancy, RMOT and Fanger PMV use the resolved
People/Space key. The existing ACCIS/aPMV target resolver is reused. People must
already enable ``AdaptiveCEN15251`` or ``Fanger`` as applicable. The metric API
will not invent metabolic, clothing or occupancy schedules.

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
------------------------------------------

The following assumes ``sim`` is an already configured, single-building session;
no simulation is implicit in these setup calls::

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
    readers["func"] = (
        "accim.parametric_and_optimisation.objectives:checked_sum_results"
    )
    sim.set_output_readers(df_output_meter=energy_readers, df_output_variable=readers)
    sim.set_problem(minimize_outputs=[True, True])

The opt-in ``checked_sum_results`` reducer rejects empty, nonnumeric,
multidimensional, NaN/Inf and overflowing series. It is importable by workers;
the legacy permissive ``sum_results`` behavior remains unchanged.

Paper convenience API
---------------------

``accim.parametric_and_optimisation.run_paper_experiment(spec, settings, argv)``
owns preparation, metrics, exact LHS-plan persistence, checkpoint checks,
load-only postprocessing, unit conversion, hourly CSV parsing and per-climate
plots/compromise selection for the five single-zone case-study workflows.
It is not a replacement for the general simulation classes.

The five entry scripts under ``llm_project_files/experimentos_preparados`` contain
configuration and package calls only: no function/class definitions or imports
from another experiment. ``settings['script_directory']`` must be absolute;
relative CLI paths resolve there, not inside the installed package.

Actions are ``prepare``, ``discover``, ``new``, ``resume`` and ``load``. No arguments
prints help. ``load`` never loads an IDF or starts a campaign; ``prepare`` only
mutates copies. Discovery/new/resume require ``--simulate``. New/resume require
review notes and a matching discovery approval. All simulation work remains
explicit; old completed results and checkpoints must be preserved.

In notebooks, pass an explicit argument list to the package function; for
parallel campaigns, use a saved main-guarded entry script. Native optimisation
resume reuses completed IDF-by-EPW cases, not an interrupted population.

The paper's aPMV optimisation intentionally retains the native moving-reference,
all-time discomfort-hour objective. Fixed-PMV outputs are diagnostics, not a
silent replacement. Fixing the PMV setpoint or changing that objective defines
a different experiment. The handoff README records the 4.1 forecast/count
mismatch and the historical 4.2 missing-hourly-output limitation.

Validation status
-----------------

This change was checked by source/API/IDD inspection and syntax analysis only.
Hermetic regression tests are provided in ``test_comfort_metrics.py`` and
``test_paper_experiments_api.py`` but were not executed in this preparation.
EnergyPlus, discovery, preflight and experiment scripts were not run.

Before scientific use, validate keys, Erl compilation, calling-point timing,
occupancy, timestep integration and annual totals on the simulation PC. For
RMOT=20 C, limits are 21.4/28.4 C: an occupied 0.25-hour step at To=30 C gives
0.4 C-hr; at To=20 C it gives 0.35 C-hr; comfortable/unoccupied steps give zero.
Keep error and EMS trace files. Inspect warmup, applicability boundaries, Fanger
inputs, aPMV denominator singularities and Windows worker serialization.

