ACCIM stands for Adaptive Comfort Control Implemented Model.

In research terms, this is a proposal for a paradigm shift, from using fixed PMV-based to adaptive setpoint temperatures, based on adaptive thermal comfort algorithms and it has been widely studied and published on scientific research journals (for more information, refer to https://orcid.org/0000-0002-3080-0821).

In terms of code, this is a python package that transforms fixed setpoint temperature building energy models into adaptive setpoint temperature energy models by adding the Adaptive Comfort Control Implementation Script (ACCIS). This package has been developed to be used in EnergyPlus building energy performance simulations.

Development workflow files
--------------------------

``CHANGELOG.md`` contains user-facing release notes; ``DEVLOG.md`` records
completed technical work; ``TODO.md`` tracks active tasks; and ``ROADMAP.md``
contains medium/long-term initiatives. See `README.md <README.md>`_ for the
complete project overview and legacy usage examples.

Independent comfort reporting and paper workflows (unreleased)
-------------------------------------------------------------

The source branch ``feat/comfort-metrics-experiment-api`` adds reporting metrics
independent of optimised control setpoints, without changing thermostats,
schedules or native aPMV counters:

* ``accim.sim.add_comfort_metrics(...)`` operates on a prepared IDF, offers a
  non-mutating ``dry_run``, and returns per-target output metadata.
* ``SimulationBase.add_comfort_metrics(...)`` is inherited by both simulation
  classes. It appends scoped reporting requests without discovery; readers and
  objectives are still selected explicitly.
* ``objectives.checked_sum_results(...)`` is an opt-in worker-importable reducer
  that rejects missing/non-finite series and performs no unit conversion.

``fixed_en`` provides occupied Cat II degree-hours with clamped RMOT and fixed
+3/-4 K limits; ``fixed_pmv`` provides occupied absolute-Fanger-PMV integrals and
fixed-threshold hours. Add metrics after control preparation and before
discovery/readers/problem creation. Multizone aggregation requires an explicit
study definition; zone-hours must not be presented automatically as building hours.

The separate ``accim.parametric_and_optimisation.run_paper_experiment(...)`` API
manages the five single-zone paper workflows. Their entries contain configuration
and package calls only. ``load`` consumes an explicitly chosen consolidated
result, not a checkpoint, and never simulates. Discovery/new/resume require
explicit opt-in. Optimisation resume reuses completed IDF-by-EPW cases, not
interrupted populations. The wrapper's 312 m2 denominator, budgets and approval
gates are not defaults of the general simulation classes.

The generic aPMV function currently defaults to cooling -0.5 / heating +0.5;
the paper workflow explicitly overrides these to +0.5 / -0.5. Dictionary-entry
fallback arguments are separate from these top-level defaults.

See the `API and usage guide <docs/source/comfort_metrics.rst>`_,
`source installation instructions <docs/source/2_installation.md>`_ and
`experiment handoff <llm_project_files/experimentos_preparados/README.md>`_.
Install the corresponding source revision: a published version number alone
does not guarantee these APIs. Static review is complete; numerical/EMS and
runtime validation remain pending.
