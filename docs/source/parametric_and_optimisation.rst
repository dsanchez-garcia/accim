Overview of parametric simulation and optimisation
==================================================

The module :mod:`accim.parametric_and_optimisation` simulates the same building many times with
different values of the parameters of its control, and analyses the results. It works with the
three kinds of control that accim adds to an EnergyPlus model: the adaptive setpoint temperatures
of the predefined comfort models, the adaptive setpoint temperatures of a custom comfort model,
and the aPMV setpoints. It answers two kinds of questions:

- **How do the results respond to the parameters?** A *parametric simulation*
  (:class:`~accim.parametric_and_optimisation.main.ParametricSimulation`) simulates a plan of
  parameter combinations chosen by you, and returns one row of results per simulation.
- **Which parameter values give the best trade-offs?** In an *optimisation*
  (:class:`~accim.parametric_and_optimisation.main.OptimisationSimulation`), a genetic algorithm
  (NSGA-II by default) chooses the combinations to minimise or maximise two or more objectives,
  for example the HVAC electricity and the indoor operative temperature. The result is the set of
  non-dominated solutions (the Pareto front), from which compromise solutions can be chosen.

Both classes are set up in the same way and share the methods that read, analyse and plot the
results. The simulations are run with `besos <https://besos.uvic.ca/>`_, which also provides the
sampling methods and, through Platypus, the optimisation algorithms. The sensitivity analysis uses
SALib.

This page explains the concepts and the steps of a study. The notebooks of
:doc:`jupyter_notebooks/parametric_and_optimisation_examples/index` apply them to the sample models
of accim, and the :doc:`API reference <api/accim.parametric_and_optimisation>` documents every
argument.

The steps of a study
--------------------

#. **Load and prepare the model**: read the IDF and, for exploratory runs, make the simulations
   lighter.
#. **Create the simulation object**: it adds the control of accim to the model.
#. **Choose the outputs**: what EnergyPlus writes, and how each simulation is summarised in the
   table of results.
#. **Define the parameters** and their values or ranges.
#. **Draw the plan** of a parametric simulation, or **set the objectives** of an optimisation.
#. **Run the simulations**.
#. **Analyse the results**: tables, plots, hourly indicators, sensitivity analysis and compromise
   solutions.

The sections below follow these steps with short code examples. The examples use the
custom adaptive model; the other kinds of parameters change only steps 1, 2 and 4.

1. Load and prepare the model
-----------------------------

The model is read with besos as an IDF object. accim and the parameters modify this object in
memory: the IDF file is never modified.

.. code-block:: python

    from besos import eppy_funcs as ef
    from accim.utils import reduce_runtime

    building = ef.get_building('my_model.idf')

    # Optional, for exploratory runs: 2 timesteps per hour and minimal shadowing, whole year
    reduce_runtime(
        idf_object=building,
        minimal_shadowing=True,
        timesteps=2,
        runperiod_begin_month=1,
        runperiod_begin_day_of_month=1,
        runperiod_end_month=12,
        runperiod_end_day_of_month=31,
    )
    # Keep the design days out of the annual results
    building.idfobjects['SimulationControl'][0].Run_Simulation_for_Sizing_Periods = 'No'

- :func:`~accim.utils.reduce_runtime` shortens each simulation. By default it also shortens the
  run period to 1 January, so give it the run period of the whole year if you want annual
  results. Fewer timesteps change the annual energy slightly: remove the call for final results.
- If the model simulates its design days (``Run Simulation for Sizing Periods = Yes``), they are
  simulated as additional environments, and the annual results read after each simulation include
  them (8,928 hours instead of 8,760 in the sample models). With ``'No'``, the design days are
  still used to size the HVAC system.
- The VRF systems that accim adds are autosized, so the model needs sizing periods (design days, or
  ``SizingPeriod:WeatherFileDays`` objects). accim enables the sizing calculations of the model, and
  warns if it has no sizing periods, since EnergyPlus would stop.

**aPMV setpoints.** For the aPMV setpoints, add an HVAC system with thermal comfort thermostats and
the aPMV control to the model before creating the simulation object, and check the inputs of the
People objects that the PMV depends on:

.. code-block:: python

    from accim.sim.apmv import (add_vrf_system, apply_apmv_setpoints,
                                set_pmv_input_parameters)

    add_vrf_system(building)
    apply_apmv_setpoints(
        building,
        output_frequencies=['hourly'],
        adaptive_coefficient_cooling=0.293,
        adaptive_coefficient_heating=-0.293,
        pmv_cooling_setpoint=0.5,
        pmv_heating_setpoint=-0.5,
        cooling_season_start='01/04',   # dd/mm, northern hemisphere
        cooling_season_end='01/10',
    )
    set_pmv_input_parameters(building, air_velocity=0.1, work_efficiency=0.0)

The cooling season is given by dates, so swap them for a location in the southern hemisphere.
:doc:`jupyter_notebooks/parametric_and_optimisation_examples/wf3_parametricsimulation_apmv_setpoints`
explains each of these settings.

2. Create the simulation object
-------------------------------

.. code-block:: python

    from accim.parametric_and_optimisation.main import ParametricSimulation

    sim = ParametricSimulation(
        buildings=[building],
        epws=['Seville.epw', 'Sydney.epw'],
        parameters_type='accim custom model',
        output_frequencies=['hourly'],
        script_type='vrf_ac',
    )

For an optimisation, use :class:`~accim.parametric_and_optimisation.main.OptimisationSimulation`
with the same arguments. ``parameters_type`` sets the kind of parameters of the study, and what
the object does to each model when it is created:

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - ``parameters_type``
     - When the object is created
     - Parameters that can be varied
   * - ``'accim predefined model'``
     - Adds accim to each model (:func:`~accim.sim.accis.add_accis_to_idf`)
     - ``comfort_standard``, ``category``, ``comfort_mode``, ``hvac_mode``, ``ventilation_control``,
       ``setpoint_tolerance`` and the other arguments of :func:`~accim.sim.accis.modify_accis`, with
       their names (see :doc:`4_detailed use`); since accim 1.2.0, also ``heating_setpoint_minimum`` and
       ``cooling_setpoint_maximum`` (the minimum heating setpoint and the maximum of the cooling
       setpoint of all the zones), and the limiter of the drift of the setpoints: ``drift_mode`` (the codes
       0, none; 1, ``'rate'``; 2, ``'window'``, as options), ``max_drift_rate``, ``alpha_indoor``,
       ``delta_cool``, ``delta_heat`` and ``initial_T_rm_in``
   * - ``'accim custom model'``
     - Adds accim to each model, with the custom adaptive model
     - ``custom_slope`` (slope of the comfort temperature), ``custom_intercept`` (intercept),
       ``custom_offset`` (offset of the setpoints from the comfort temperature) and
       ``custom_lower_limit``/``custom_upper_limit`` (applicability limits of the running mean
       outdoor temperature); the offsets and limits can also be set separately for cooling and
       heating (``custom_cooling_offset``, ``custom_heating_offset``, ``custom_cooling_lower_limit``...);
       since accim 1.2.0, also ``heating_setpoint_minimum`` and ``cooling_setpoint_maximum``, the parameters of
       the limiter of the drift of the setpoints (``drift_mode``...), and the outdoor
       metric of the custom model: ``custom_outdoor_metric`` (the codes of the metrics, 0 to 7, as options),
       ``custom_alpha`` and ``custom_days`` (rounded to whole days); and the coefficients of the regimes of the
       custom model, ``custom_regime_<regime>_<field>`` (such as ``custom_regime_1_slope``), once the model has
       them
   * - ``'apmv setpoints'``
     - Applies the aPMV setpoints with the default values of ``apply_apmv_setpoints``, unless
       ``bypass_add_accis=True``
     - ``adaptive_coefficient_cooling``, ``adaptive_coefficient_heating``,
       ``pmv_cooling_setpoint``, ``pmv_heating_setpoint``, and ``adaptive_coefficient`` and
       ``pmv_setpoint`` to vary both seasons, or both setpoints (-s and +s), together; since accim 1.2.0,
       also the inputs of the PMV of the occupants: ``clothing_insulation`` (clo), ``activity_level``
       (W/person) and ``air_velocity`` (m/s)
   * - ``'epmv setpoints'``
     - Applies the ePMV setpoints with the default values of ``apply_epmv_setpoints``, unless
       ``bypass_add_accis=True`` (since accim 1.2.0)
     - ``expectancy_factor`` (between 0.5 and 1), ``pmv_cooling_setpoint``, ``pmv_heating_setpoint`` and
       ``pmv_setpoint`` (both setpoints together), on the ePMV scale, and ``clothing_insulation``,
       ``activity_level`` and ``air_velocity``

``sim.get_available_parameters()`` lists the names. The parameters have the names of the arguments
of :mod:`accim.sim` since accim 1.0.0; their names of accim 0.x (``ComfStand``, ``CustAST_m``,
``'PMV setpoint'``...) still work, with a ``DeprecationWarning``, and the results of accim 0.x get
the new names when they are loaded (see :doc:`9_migration_guide`). The parameters of the accim models set the
arguments of all the occupied zones (each zone has them in its EMS program ``SetInputData_<zone>``).
``clothing_insulation``, ``activity_level`` and ``air_velocity`` set the schedules of all the People objects
with :func:`~accim.sim.apmv.set_pmv_input_parameters`, and warn outside the ranges in which ISO 7730:2025
(section 4) uses the PMV: 0 to 2 clo (and above 1.5 clo, with which ASHRAE 55-2020 does not use it), 0.8 to 4 met
(82.8 to 417.6 W/person, with a body surface area of 1.8 m², as in EnergyPlus) and 0 to 1 m/s
(:data:`accim.constants.PMV_INPUT_RANGES`). With the ePMV setpoints with ``metabolic_correction=True``,
``activity_level`` is not a parameter: the EMS programs of the correction read the activity level of the People
objects from their schedules and set it in each timestep, so
:func:`~accim.sim.apmv.set_pmv_input_parameters` raises a ``ValueError`` (set the activity level before applying
the setpoints, in the model of the study). The metrics of ``custom_outdoor_metric`` that the EMS calculates begin
with the running mean of ASHRAE 55 of EnergyPlus, unless the model was given the weather file with
``modify_accis(..., custom_outdoor_metric=..., epw=...)`` before the study (``'monthly_mean'`` needs it).
``accim.parametric_and_optimisation.parameters`` also has a class for each of them, which applies it to a model
(``Clo``, ``Met``, ``AirVelocity``, ``ExpectancyFactor``, ``AdaptiveCoefficientCooling``,
``AdaptiveCoefficientHeating``, ``CustAST_metric``, ``CustAST_alpha``, ``CustAST_days``, ``HeatingSetpointMinimum``
and ``CoolingSetpointMaximum``, besides those of the other parameters).
The regimes of the custom model (``custom_regimes``, section 4.2.4 of :doc:`4_detailed use`) depend on the model, so
their coefficients are parameters once the model has them: give them with
``modify_accis(sim.building, comfort_standard=99, comfort_mode=3, custom_regimes=[...])`` before
``set_parameters``, whose dictionary can then have ``custom_regime_<regime>_<field>``, where the field is
``slope``, ``intercept``, ``cooling_offset``, ``heating_offset``, ``cooling_lower_limit``, ``cooling_upper_limit``,
``heating_lower_limit`` or ``heating_upper_limit`` of :class:`~accim.sim.arguments.CustomRegime`; each one sets that
coefficient of the regime in all the zones, which keeps its condition. ``custom_regime_parameters(n)`` gives the
classes of the coefficients of the first ``n`` regimes (``CustAST_m_1``, ``CustAST_n_1``, ``CustAST_ACSToffset_1``,
``CustAST_AHSToffset_1``, ``CustAST_ACSTall_1``, ``CustAST_ACSTaul_1``, ``CustAST_AHSTall_1``, ``CustAST_AHSTaul_1``,
``CustAST_m_2``...).
The comfort standards defined by their data (section 4.2.5 of :doc:`4_detailed use`) are options of
``comfort_standard`` once they are registered (before sampling the plan): the plans keep their categories and comfort
modes only, the models get their EMS code, the zones get their outdoor metric (which the EMS begins with the running
mean of ASHRAE 55 of EnergyPlus, if it calculates it) and the parallel simulations, which run in other processes, get
the comfort standards of the registry.
For the aPMV and ePMV setpoints, apply them yourself
with explicit values, as in step 1 (for the ePMV, with ``apply_epmv_setpoints()``, section 4.8 of
:doc:`4_detailed use`), and pass ``bypass_add_accis=True``: the parameters of the study
then replace only the values they vary, and the object does not apply the setpoints again.

The other arguments are passed to :func:`~accim.sim.accis.add_accis_to_idf`, which has the same
names (those of accim 0.x, such as ``ScriptType`` or ``output_freqs``, still work, with a
``DeprecationWarning``). ``script_type`` is ``'vrf_ac'`` (VRF system, fully air-conditioned), ``'vrf_mm'`` (VRF
system with mixed-mode operation) or ``'ex_ac'`` (the existing HVAC system of the model, fully
air-conditioned). With ``'ex_ac'``, the arguments ``existing_hvac_operative_temperature_control``,
``existing_hvac_radiant_setpoints``, ``existing_hvac_availability_schedule``,
``existing_hvac_widen_outdoor_temperature_limits`` and ``existing_hvac_ideal_loads_backup`` adapt the existing HVAC
system so that it keeps the operative temperature between
the setpoints (section 4.1.1 of :doc:`4_detailed use`). Mixed-mode operation needs a model with natural ventilation: calculated
(AirflowNetwork), or given by ``ZoneVentilation:WindandStackOpenArea`` or
``ZoneVentilation:DesignFlowRate`` objects, whose opening accim controls; see :doc:`4_detailed use`.
With ``'vrf_ac'`` and ``'ex_ac'``, accim does not change the natural ventilation of the model, so
the windows that are open in it stay open: to simulate such a model fully air-conditioned with its
windows closed, use ``'vrf_mm'`` and ``hvac_mode`` 0 (as WF1 and WF4 do), or close them in the model
(as the aPMV examples do).

Several models can be simulated in the same study (``buildings=[building_a, building_b]``): each one
is identified by its file name, and the plan gets an ``idf`` column.

3. Choose the outputs
---------------------

Two different things are set here:

- **Output objects** (``Output:Variable`` and ``Output:Meter``) are what EnergyPlus writes. accim
  adds many of them; in a large study, keep only those you need, because hourly outputs make each
  simulation slower and its files larger.
- **Readers** turn the outputs of each simulation into the columns of the table of results, for
  example the annual sum of a meter or the annual mean of a temperature. In an optimisation, the
  readers are the objectives.

.. code-block:: python

    available = sim.discover_available_outputs()    # short test simulation; select_outputs runs it if needed
    selection = sim.select_outputs(
        meters=['Electricity:HVAC', 'Heating:Electricity', 'Cooling:Electricity'],
        variables=['Zone Operative Temperature'],
        on_missing='raise',
    )
    sim.apply_outputs_preflight(
        df_meters_sel=selection['meters'],
        df_vars_sel=selection['variables'],
        clean_mode='all',      # first remove the other output objects of the model
    )

    from accim.parametric_and_optimisation.objectives import sum_results, average_results

    readers_meters = selection['meters'].copy()
    readers_meters['func'] = [sum_results] * len(readers_meters)      # annual sum (J)
    readers_temp = selection['variables'].copy()
    readers_temp['func'] = [average_results] * len(readers_temp)      # annual mean (°C)
    readers_temp['name'] = 'Annual mean operative temperature ' + readers_temp['key_value']
    sim.set_output_readers(df_output_meter=readers_meters, df_output_variable=readers_temp)

- Without the ``func`` and ``name`` columns, the readers sum the hourly values and the columns take
  the names of the outputs. ``return_time_series`` keeps the whole series in each row instead of a
  single value. ``sum_results`` skips missing values; ``checked_sum_results`` stops with an error
  instead when a series is empty or has missing or infinite values, so that a failed simulation does
  not give a valid objective.
- Meters are read in J; step 7 converts them to kWh/m².
- To analyse hourly values afterwards (comfort screening, hourly plots), the variables must be
  written hourly (``output_frequencies=['hourly']``) and the files of the simulations must be kept
  (step 6).

**Hours within the setpoints.** The percentage of the occupied hours in which each zone is within
its setpoints (without tolerance) shows whether the HVAC system or the natural ventilation keeps the
setpoints of each simulation, so that the simulations in which it does not can be left out
(:ref:`hours-within-setpoints`). Read the sums of the two hour counters of the zones, named after the
outputs, and compute the percentages after the run with
:func:`~accim.data.postprocessing.setpoint_hours.hours_within_setpoints`:

.. code-block:: python

    import pandas as pd

    hours = sim.select_outputs(variables=['Occupied Hours_', 'Occupied Comfortable Hours_No Applicability_'],
                               match='contains', on_missing='raise')['variables']
    # with the other outputs: apply_outputs_preflight(..., df_vars_sel=pd.concat([selection['variables'], hours]))
    readers_hours = hours.copy()
    readers_hours['func'] = [sum_results] * len(readers_hours)
    readers_hours['name'] = readers_hours['variable_name']      # Occupied Hours_<zone>...
    sim.set_output_readers(df_output_meter=readers_meters,
                           df_output_variable=pd.concat([readers_temp, readers_hours], ignore_index=True))

    # after run_parametric_simulation (step 6)
    from accim.data.postprocessing.setpoint_hours import filter_by_hours_within_setpoints, hours_within_setpoints

    sim.outputs_param_simulation = hours_within_setpoints(sim.outputs_param_simulation)
    kept = filter_by_hours_within_setpoints(sim.outputs_param_simulation, min_percentage=90)

The table gets the columns ``Occupied Hours Within Setpoints_<zone> [%]`` and
``Occupied Hours Within Setpoints_Building [%]``, which the plots of step 7 can also filter, with
``data_filter={'include': {'Occupied Hours Within Setpoints_Building [%]': {'ge': 90}}}``. In an
optimisation, the sum of ``Occupied Discomfortable Hours_No Applicability_<zone>`` can be a
constraint: the occupied hours of a model and weather file are the same in every evaluation, so a
maximum of hours out of the setpoints is a minimum percentage within them.

**Comfort objectives independent of the control.** The comfort hours that accim counts
(``Comfortable Hours_*``, for instance) follow the comfort model that accim controls, so a study that
changes that model (the coefficients of the custom model, or the aPMV setpoints) measures each
evaluation against a different model. EnergyPlus also reports, for each ``People`` object of the
models of accim, whether its zone is within the adaptive comfort range of CEN 15251
(``Zone Thermal Comfort CEN 15251 Adaptive Model Category II Status``, or categories I and III) and of
ASHRAE 55 (``Zone Thermal Comfort ASHRAE 55 Adaptive Model 80% Acceptability Status``, or 90 %),
which do not depend on the control: 1 inside, 0 outside, and -1 when the zone is empty or the running
mean outdoor temperature is out of the range of the model. ``hours_outside_comfort`` turns its hourly
values into the occupied hours outside the range, and ``fraction_outside_comfort`` into their fraction
of the occupied time. The models do not request these variables, so add them before choosing the
outputs:

.. code-block:: python

    from accim.parametric_and_optimisation.objectives import hours_outside_comfort, sum_results

    status = 'Zone Thermal Comfort CEN 15251 Adaptive Model Category II Status'
    sim.set_output_variables_to_idf(output_variables=[status], validate=False)
    sim.discover_available_outputs(refresh=True)
    selection = sim.select_outputs(meters=['Electricity:HVAC'], variables=[status], on_missing='raise')
    sim.apply_outputs_preflight(df_meters_sel=selection['meters'], df_vars_sel=selection['variables'],
                                clean_mode='all')

    readers_meters = selection['meters'].copy()
    readers_meters['func'] = [sum_results] * len(readers_meters)
    readers_comfort = selection['variables'].copy()      # one row for each People object
    readers_comfort['func'] = [hours_outside_comfort] * len(readers_comfort)
    readers_comfort['name'] = 'Hours outside CEN 15251 II ' + readers_comfort['key_value']
    sim.set_output_readers(df_output_meter=readers_meters, df_output_variable=readers_comfort)

Each row is a zone (its ``People`` object), so an optimisation gets an objective for each one: keep the
rows of the zones that matter. As with the other readers, the hours of the design days count too when
the model simulates its sizing periods.

**Long-term comfort objectives (CEN/TR 16798-2).** With ``report_long_term_discomfort=True`` (accim
predefined and custom models), the models report the long-term discomfort of the occupied hours that
CEN/TR 16798-2:2019 (Annex D) defines, with the range of the comfort model of accim (between the
setpoints without the tolerance, see :ref:`long-term-discomfort-outputs`): Method A, the occupied hours
above the cooling setpoint and below the heating setpoint (``Hours Above Upper Limit_<zone>`` and
``Hours Below Lower Limit_<zone>``), and Method B, their degree hours (``Degree Hours Above Upper
Limit_<zone>`` and ``Degree Hours Below Lower Limit_<zone>``), with the sums of the zones as
``..._Building``. ``hours_outside_range`` and ``degree_hours`` sum them, and check that the output is
one of them:

.. code-block:: python

    from accim.parametric_and_optimisation.objectives import degree_hours, hours_outside_range, sum_results

    sim = ParametricSimulation(..., parameters_type='accim custom model', report_long_term_discomfort=True)
    selection = sim.select_outputs(meters=['Electricity:HVAC'],
                                   variables=['Hours Above Upper Limit_Building',
                                              'Degree Hours Above Upper Limit_Building'],
                                   on_missing='raise')
    sim.apply_outputs_preflight(df_meters_sel=selection['meters'], df_vars_sel=selection['variables'],
                                clean_mode='all')

    readers_meters = selection['meters'].copy()
    readers_meters['func'] = [sum_results] * len(readers_meters)
    readers_long_term = selection['variables'].copy()
    readers_long_term['func'] = [degree_hours if name.startswith('Degree') else hours_outside_range
                                 for name in readers_long_term['variable_name']]
    readers_long_term['name'] = readers_long_term['variable_name']
    sim.set_output_readers(df_output_meter=readers_meters, df_output_variable=readers_long_term)

Since these outputs follow the comfort model of accim, a study that changes it (the custom model, for
instance) measures each evaluation against its own range; the comfort status of EnergyPlus above does
not depend on it. Method C (the PPD-weighted hours) needs the PMV, which these models do not calculate.
The weekly and monthly deviations of Annex E, and the percentages of Method A, are calculated after the
simulations (:func:`~accim.data.postprocessing.long_term_discomfort.deviation_check`, and
``Table(long_term_indicators=True)``).

:doc:`jupyter_notebooks/parametric_and_optimisation_examples/04_outputs_preflight_and_output_control`
shows the other methods for output objects, for example to find and remove duplicates.

4. Define the parameters
------------------------

.. code-block:: python

    sim.set_parameters(
        accis_params_dict={
            'custom_slope': (0.0, 0.7),         # tuple: range (min, max)
            'custom_intercept': (5.0, 22.5),
            'custom_offset': (1.0, 5.0),
            'custom_upper_limit': (22.0, 40.0),
        },
        use_default_values=True,   # the parameters that are not varied take the defaults of accim
    )
    sim.set_problem()

- A **list** gives the options of a parameter (``'comfort_standard': [1, 2]``), and a **tuple** gives
  its range (``'custom_slope': (0.0, 0.7)``). Which one to use depends on the plan (step 5): options for
  all the combinations, ranges for sampling and optimisation.
- With ``use_default_values=True``, the parameters of the custom model that are not varied take the
  values of the ASHRAE 55 adaptive model with 80 % acceptability (m = 0.31, n = 17.8 °C, offsets
  of ±3.5 K, applicability limits of 10 and 33.5 °C), and accim prints them.
- ``additional_params`` adds besos parameters that change any other field of the model, for
  example the thickness of the insulation (see
  :doc:`jupyter_notebooks/parametric_and_optimisation_examples/06_multi_idf_multi_epw_and_custom_plan`).
- :meth:`~accim.parametric_and_optimisation.main.SimulationBase.set_problem` registers the
  parameters and the readers as the inputs and outputs of the problem. In an optimisation, it also
  sets the objectives (step 5).

**The m-n filter (custom model).** Independent ranges of the slope ``custom_slope`` and the
intercept ``custom_intercept`` include many pairs that no published adaptive model has, such as a high slope with a
high intercept.
:meth:`~accim.parametric_and_optimisation.main.SimulationBase.set_mn_filter` restricts them to the
band of the 56 linear adaptive models collected by Yao et al. (2022): the slope of the models is
regressed on their intercept, and two lines parallel to the regression line bound the band. With
the filter set, ``sampling_lhs`` draws the pairs inside the band; the other plans drop the pairs
outside it, and an optimisation moves the intercept proposed by the algorithm into the band. Sobol
and Morris samples are not filtered, because the sensitivity analysis needs independent inputs.
``sim.plot_mn_filter()`` draws the band and the pairs of the plan.

5. Draw the plan, or set the objectives
---------------------------------------

Parametric simulation: the plan
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The plan is a table with one column per parameter and one row per simulation, stored in
``sim.parameters_values_df``. The sampling methods repeat each sample for every weather file
(column ``epw``) and every model (column ``idf``, when there are several), so all of them are
compared with the same parameter values.

.. list-table::
   :header-rows: 1
   :widths: 30 14 26 30

   * - Method
     - Parameters
     - Rows per model and weather file
     - Use
   * - ``sampling_full_set()``
     - lists
     - all the combinations (those that are not valid are left out: with the accim models, the categories
       and comfort modes that a comfort standard does not have, and since accim 1.2.0 a minimum of the heating
       setpoint that is not lower than the maximum cooling setpoint)
     - compare discrete alternatives, such as comfort models and categories
   * - ``sampling_full_factorial(level)``
     - ranges
     - ``level`` values of each range, all combinations
     - regular grid of continuous parameters
   * - ``sampling_lhs(num_samples)``
     - ranges
     - ``num_samples``
     - explore a continuous space with few simulations (Latin hypercube)
   * - ``sampling_sobol(num_samples)``
     - ranges
     - ``num_samples`` x (2 x parameters + 2)
     - Sobol sensitivity indices
   * - ``sampling_morris(num_samples)``
     - ranges
     - ``num_samples`` x (parameters + 1)
     - Morris screening of the parameters
   * - ``sampling_custom(custom_plan)``
     - any
     - your own table
     - chosen combinations, or a different weather file for each model

.. code-block:: python

    sim.sampling_lhs(num_samples=20)
    plan = sim.parameters_values_df
    plan.to_csv('sampling_plan.csv', index=False)    # the Latin hypercube has no seed
    print('Simulations:', len(plan))

Each row of the plan is one EnergyPlus simulation. Estimate the time before running: rows x time
of one simulation / number of parallel processes.

Optimisation: the objectives
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In an optimisation, the parameters are usually ranges, and the readers of step 3 are the
objectives. :meth:`~accim.parametric_and_optimisation.main.SimulationBase.set_problem` says whether
each objective is minimised (``True``) or maximised (``False``), and which outputs are only
reported:

.. code-block:: python

    from besos.objectives import MeterReader

    reported = [MeterReader(key_name=name, frequency='Hourly', func=sum_results, name=name)
                for name in ['Heating:Electricity', 'Cooling:Electricity']]
    optim.set_problem(minimize_outputs=[True, True], add_outputs=reported)

``constraints`` and ``constraint_bounds`` are passed to the besos ``EPProblem``. An evaluation that
meets the constraints dominates any that does not (as the algorithms of platypus compare them), so
the ``pareto-optimal`` column of the results and ``keep_sim_files='non-dominated'`` only keep, among
the evaluations with the smallest violation, those that are not dominated in the objectives.

The acceptable deviations of CEN/TR 16798-2:2019 (Annex E, Table E.1) can be the bound of a constraint
on the occupied hours outside the range of the long-term discomfort (``report_long_term_discomfort=True``,
above): at most 3 % or 6 % of the occupied hours of a year (the levels ``'3%'`` and ``'6%'``), 12 % or
25 % of those of a month, and 20 % or 50 % of those of a week.
:func:`~accim.parametric_and_optimisation.objectives.deviation_constraint_bound` gives the bound from
the occupied hours of the simulated period, which do not change from one evaluation to another with the
same model and weather file (the sum of ``Occupied Hours_<zone>`` of the zones in a first simulation):

.. code-block:: python

    from besos.objectives import VariableReader
    from accim.parametric_and_optimisation.objectives import deviation_constraint_bound, hours_outside_range

    occupied_hours = 2100   # the occupied hours of the building in a year (all its zones)
    warm_hours = VariableReader(key_value='EMS', variable_name='Hours Above Upper Limit_Building',
                                frequency='Hourly', func=hours_outside_range,
                                name='Hours Above Upper Limit_Building')
    optim.set_problem(minimize_outputs=[True], constraints=[warm_hours],
                      constraint_bounds=[deviation_constraint_bound(occupied_hours, 'yearly', '6%')])  # '<=126.0'

6. Run the simulations
----------------------

.. code-block:: python

    results = sim.run_parametric_simulation(
        out_dir='param_results',
        df=sim.parameters_values_df,
        processes=4,                            # simulations in parallel
        keep_dirs=True,                         # keep the folder of each simulation
        sim_files_extensions=['.csv', '.err'],  # ... with only these files
        sim_files_policy='keep',
    )

.. code-block:: python

    optim.estimate_optimisation_sims(evaluations=60, population_size=20, epws=['Seville.epw'])
    results = optim.run_optimisation(
        out_dir='optim_results',
        algorithm='NSGAII',
        population_size=20,
        evaluations=60,               # budget of each weather file
        processes=4,                  # simulations of a generation in parallel
        keep_sim_files='non-dominated',
    )

**The table of results** has one row per simulation, with the parameters, ``idf``, ``epw``, the
columns of the readers and ``output_dir`` (the folder of the simulation). It is stored in
``sim.outputs_param_simulation`` or ``optim.outputs_optimisation``, and saved in ``out_dir`` as
``outputs_param_simulation_<date>_<time>`` or ``outputs_optimisation_<date>_<time>`` (CSV, pickle
and JSON). ``load_outputs_parametric`` and ``load_outputs_optimisation`` load it again in a new
session, so the results can be analysed without simulating again.

**Optimisation.** The algorithm runs separately for each weather file (and each model).
``evaluations`` stops it, but NSGA-II completes the current generation first, so it can simulate
more cases; ``estimate_optimisation_sims`` gives the number before running. The results include
all the evaluations (``keep_df='all'``), with a ``pareto-optimal`` column that marks the
non-dominated solutions of each weather file. WF4 and WF5 call ``random.seed(...)`` before the
run to repeat the same optimisation.

**Disk space.** Each simulation writes its own folder, and hourly CSV files are what make it heavy:

- ``keep_dirs=False`` (parametric) or ``keep_sim_files='none'`` (optimisation) keep only the table
  of results; ``keep_sim_files='non-dominated'`` keeps the folders of the non-dominated solutions;
- ``sim_files_extensions`` with ``sim_files_policy`` keeps (``'keep'``) or deletes (``'delete'``)
  the files with these extensions in each folder;
- :doc:`filter_output_csvs` writes copies of the CSV files with only some columns.

A light alternative, used in WF2 and WF4: run the study with annual results only, then simulate
again, with hourly outputs, only the cases you want to examine, by passing their rows as ``df`` to
``run_parametric_simulation`` (also available in ``OptimisationSimulation``).

**Long runs.** ``batch_size``, ``checkpoint_every_batch`` and ``resume_from_checkpoint`` (parametric)
or ``checkpoint_every_case`` and ``resume_from_checkpoint`` (optimisation) save the progress and
continue an interrupted run. A resumed parametric run reuses the simulations of the checkpoint
whose model (its objects, after the setup of accim), weather file, parameters and output names
are the same, and simulates the others again: changing the model or the outputs between the two
runs is safe. ``preflight_report_parametric`` and ``preflight_report_optimisation``
check the plan and estimate the number of simulations before running. On Windows, keep ``out_dir``
short: EnergyPlus fails when a path reaches 260 characters, and accim warns when ``out_dir`` is too
long.

7. Analyse the results
----------------------

Energy per floor area
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    sim.set_building_floor_area(mode='all')     # or 'occupied', 'air-conditioned', 'list', 'custom'
    sim.normalize_outputs(df_types=['parametric'])

:meth:`~accim.parametric_and_optimisation.analysis.AnalysisMixin.normalize_outputs` converts the
energy columns from J to kWh/m², in place. The plotting methods also accept
``normalize_per_m2=True``, which normalises only the plotted values: use one or the other.

Plots of the table of results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Method
     - Shows
   * - ``plot_parametric_scatter``
     - an output against a parameter or another output, with trend lines
   * - ``plot_parametric_lines``
     - outputs against a swept parameter
   * - ``plot_parametric_heatmap``, ``plot_parametric_contour``
     - an output over the plane of two parameters
   * - ``plot_parametric_distributions``, ``plot_parametric_ecdf``, ``plot_categorical_boxplots``
     - distributions of outputs by group (violin, box, cumulative)
   * - ``plot_parametric_density_2d``
     - density of points (hexbin or KDE)
   * - ``plot_parametric_radar``
     - several metrics of a few groups
   * - ``plot_pareto_front``, ``plot_parallel_coordinates``, ``plot_pairwise_scatter_matrix``
     - optimisation results: Pareto front, parameters of the solutions
   * - ``plot_mn_filter``
     - the m-n band and the simulated pairs

The plotting methods share these arguments: ``df_source`` (``'parametric'``, ``'optimisation'``...),
groups (``hue``, ``col``, ``row``), ``data_filter`` (rows to include or exclude), ``out_dir`` and
``filename_template`` (where the PNG files are saved) and ``subplot_order_mode`` (order of the
panels). What each method returns (the figure, the paths of the files or a table) is given in the
API reference.

Compromise solutions
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    knee = optim.get_best_compromise_solution(method='knee_point')
    topsis = optim.get_best_compromise_solution(method='topsis', weights=[0.7, 0.3])
    optim.plot_best_compromise_solutions(out_dir='plots')

Each Pareto front (by default, one per weather file) gives one compromise solution: the knee point
is the solution closest to the utopia point after a min-max normalisation of the objectives, and
TOPSIS ranks the solutions with weights for the objectives.

Hourly results
^^^^^^^^^^^^^^

When the CSV files of the simulations were kept, ``get_hourly_df_parametric`` and
``get_hourly_df_optimisation`` read their hourly values into a long table (select the simulations
and columns to keep it small), and ``get_output_df`` aggregates them by day, month or run period.
:doc:`hourly_plotting` explains the hourly indicators of each evaluation (share of hours outside
an adaptive comfort band, peaks, operating hours), the comfort screening and the hourly plots.

Sensitivity analysis
^^^^^^^^^^^^^^^^^^^^

After a plan of ``sampling_sobol`` or ``sampling_morris`` has been simulated,
``run_sensitivity_analysis(method='sobol')`` (or ``'morris'``) computes the sensitivity indices of
each output with SALib, and ``run_sensitivity_analysis_by_epw`` does it separately for each weather
file. The method must match the plan.

Decision support and sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``run_clustering`` groups the solutions into families (KMeans) by parameters or by objectives.
- ``run_robustness_analysis`` simulates chosen solutions again with other weather files. It needs a
  session with the model, outputs and parameters of the study.
- ``merge`` and ``merge_all`` join the results of several sessions, and ``compare_with`` checks
  whether two runs give the same results.
- ``set_category_mapping`` adds columns derived from the names of the weather files and models (for
  example city and scenario) to group the results, and ``build_simulation_summary`` summarises what
  was simulated.

Practical advice
----------------

- Count the simulations before running, and start with a small plan or budget.
- Remember that ``reduce_runtime`` shortens the run period to 1 January unless you give the whole
  year, and that the design days enter the annual results unless
  ``Run_Simulation_for_Sizing_Periods`` is ``'No'``.
- Hourly analysis needs hourly outputs and the CSV files of the simulations: plan it before
  running, or simulate the chosen cases again.
- Save the plan of a Latin hypercube if you need to repeat it.
- Use the same weather files and models for all the cases you compare; the sampling methods do
  this for you.
- For aPMV setpoints, check the inputs of the People objects (activity, clothing, air velocity and
  work efficiency), and the dates of the cooling season for the hemisphere of the weather file.

Where each topic is in the notebooks
------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 60 40

   * - Topic
     - Notebooks
   * - First run and check of the environment
     - 00
   * - Custom adaptive model: ranges, Latin hypercube, full factorial and custom plans, m-n filter
     - 01, WF1
   * - Predefined comfort models: all the combinations
     - 02, WF2
   * - aPMV setpoints
     - 03, WF3, WF5
   * - Output objects: discovery, selection, duplicates and preflight
     - 04
   * - Sobol and Morris sensitivity analysis
     - 05
   * - Several models and weather files, custom plan, besos parameters, time series outputs
     - 06
   * - Optimisation with NSGA-II
     - 07, WF4, WF5
   * - Other algorithms, feasible solutions and Pareto plots
     - 08
   * - Hourly and monthly results, normalisation and plots of saved results
     - 09, WF2
   * - Compromise solutions, clustering, robustness and merging sessions
     - 10, WF4
   * - Comfort screening with hourly indicators
     - WF1, WF4

:doc:`jupyter_notebooks/parametric_and_optimisation_examples/index` explains how to run them.
