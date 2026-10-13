Hourly analysis, comfort screening and hourly plots
====================================================

``ParametricSimulation`` and ``OptimisationSimulation`` inherit a set of
methods (from
:class:`~accim.parametric_and_optimisation.hourly_plotting.HourlyPlottingMixin`)
to examine the hourly outputs that the simulations have already stored. Nothing
is simulated again: the methods read the simulation CSV files of the results
table, or the long hourly dataframe built with ``get_hourly_df_parametric()`` /
``get_hourly_df_optimisation()``.

Two kinds of analysis are covered:

- **Evaluation level.** :meth:`compute_hourly_indicators` calculates, for every
  evaluation of a study, indicators that need hourly values: temperature
  statistics, the share of hours and the degree-hours above and below each
  category of an adaptive comfort model, energy totals and hourly peaks,
  operating hours and a comfort outcome (``'meets'``, ``'too warm'`` or
  ``'too cool'``). The comfort criterion does not need to be part of the
  control or of the optimisation problem, so the evaluations can be screened
  after simulation. :meth:`plot_comfort_screening` and
  :meth:`plot_results_scatter_matrix` plot these indicators together with the
  parameters and annual results.
- **Hour level.** Heat maps, selected periods, binned responses (energy
  signatures), load-duration curves, adaptive comfort charts, scatter matrices
  and monthly distributions of hourly variables, for any group of simulations.

Variables, groups and filters
-----------------------------

- **Variables** are given by their exact column name or by a case-insensitive
  substring (``'Zone Operative Temperature'``, ``'Electricity:HVAC'``). When a
  substring matches several columns (the same variable in several zones),
  ``zone_aggregation`` (``'mean'``, ``'sum'``, ``'max'``...) combines them.
  Energy in J is shown in kWh per hour, or in kWh/m² with
  ``normalize_per_m2=True`` (``set_building_floor_area`` or ``floor_area``).
- **Groups** (``case``, ``hue``, ``panel``, ``row``, ``col``) are one column or a
  list of columns whose combinations define the groups. The ``*_labels``
  dictionaries map values, or tuples of values, to labels; string keys may be
  substrings, so ``{'Present': 'Present', 'ssp585_2080': 'SSP5-8.5 2080'}``
  labels full EPW paths. ``*_order`` lists the groups to draw and their order.
- **Filters**: every method accepts ``data_filter`` with the same rules as the
  rest of the plotting API (``include``, ``exclude``, ``query``).
- **Output**: each plotting method saves a PNG in ``out_dir`` (``filename`` or
  ``filename_template``) and returns the figure, with ``saved_path`` and
  ``summary`` (a dataframe with the numbers shown in the figure).

Adaptive comfort models
-----------------------

:func:`~accim.parametric_and_optimisation.adaptive_comfort_band` returns the
lower and upper limits for a running mean outdoor temperature:

- ``'EN16798-1'``: 0.33 T\ :sub:`rm` + 18.8 °C, categories I, II and III
  (+2/-3, +3/-4 and +4/-5 K), applicability 10-30 °C;
- ``'ASHRAE55'``: 0.31 T\ :sub:`rm` + 17.8 °C, 90 % and 80 % acceptability
  (±2.5 and ±3.5 K), applicability 10-33.5 °C;
- a dictionary (``slope``, ``intercept``, ``limits``, ``categories`` or
  ``upper_offset``/``lower_offset``) or a function ``f(rm) -> (lower, upper)``.

Outside the applicability limits, ``applicability='clip'`` keeps the limits of
the nearest applicable running mean (horizontal extension, as the adaptive
setpoints of accim), ``'exclude'`` leaves those hours out and ``'extend'``
applies the equation without limits.

The running mean is taken from the EnergyPlus outputs of the simulation
(``running_mean='auto'``). Simulations that did not report it (for example aPMV
controls) can reuse the series of another simulation with the same weather file
(:meth:`get_hourly_series_by_epw`), or calculate it from the outdoor
temperature or the EPW file with
:func:`~accim.parametric_and_optimisation.running_mean_outdoor_temperature`
(EN 16798-1 exponentially weighted mean or ASHRAE 55 simple mean).

Example
-------

.. code-block:: python

    from accim.parametric_and_optimisation import OptimisationSimulation

    sim = OptimisationSimulation()
    sim.load_outputs_optimisation(json_path='outputs_optimisation_20261010_130027.json')
    sim.set_building_floor_area(mode='custom', custom_area=312)

    # one row per evaluation, EN 16798-1 categories I-III
    ind = sim.compute_hourly_indicators(df_source='optimisation', comfort_standard='EN16798-1')

    # evaluations against 5 % of hours outside Category II, with the knee point marked
    knee = sim.get_best_compromise_solution(method='knee_point')
    sim.plot_comfort_screening(df=ind, x='E_HVAC', y='share_outside_II', col='epw',
                               selections={'Knee point': knee}, threshold=0.05)

    # parameters against the hourly outcome
    sim.plot_results_scatter_matrix(['CustAST_m', 'CustAST_n', 'CustAST_ASToffset', 'E_HVAC', 'share_outside_II'],
                                    df=ind, hue='comfort_outcome', upper='scatter', color_by='T_mean',
                                    diag='stacked', percent_columns=['share_outside_II'])

    # hourly outputs of the non-dominated solutions of one climate
    sim.get_hourly_df_optimisation(epw_filter='Present', output_columns=['Operative', 'Electricity:HVAC',
                                                                          'Running Average'])
    sim.plot_hourly_heatmaps(['Zone Operative Temperature', 'Electricity:HVAC'], df_source='optimisation_hourly',
                             case=['CustAST_m', 'CustAST_ASToffset'],
                             data_filter={'include': {'CustAST_ASToffset': {'gt': 4.5}}})

Methods
-------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Method
     - Purpose
   * - ``compute_hourly_indicators``
     - Hourly-based indicators of every evaluation (results table or hourly dataframe).
   * - ``get_hourly_series_by_epw`` / ``attach_hourly_series_by_epw``
     - Reuse weather-dependent hourly series (running mean, outdoor temperature) across simulations.
   * - ``plot_comfort_screening``
     - Energy against the share of hours outside a band, with a tolerance line, the lowest-energy
       evaluation within it, non-dominated evaluations and selected solutions.
   * - ``plot_results_scatter_matrix``
     - Scatter matrix of parameters, annual results and indicators, with correlations, coloured
       scatter or density contours in the upper panels.
   * - ``plot_hourly_heatmaps``
     - Day-by-hour maps of hourly variables, one row per case.
   * - ``plot_hourly_period``
     - Time series of a period chosen by date or automatically (largest value, largest difference
       between two cases), with an energy panel and shaded hours.
   * - ``plot_hourly_binned_response``
     - One variable binned against another (for example HVAC electricity against outdoor temperature),
       with the constant load of the hours without conditioning.
   * - ``plot_load_duration_curves``
     - Load-duration curves, optionally with a panel of annual energy against hourly peak.
   * - ``plot_adaptive_comfort_chart``
     - Hourly temperature against the running mean with the limits of an adaptive model and the
       share of hours outside them.
   * - ``plot_hourly_scatter_matrix``
     - Scatter matrix of hourly values (sampled points, density contours, distributions).
   * - ``plot_monthly_distributions``
     - Monthly distributions of an hourly variable for two scenarios, with the monthly comfort band.
