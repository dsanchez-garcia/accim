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

**aPMV setpoints.** For the aPMV setpoints, add an HVAC system with thermal comfort thermostats and
the aPMV control to the model before creating the simulation object, and check the inputs of the
People objects that the PMV depends on:

.. code-block:: python

    from accim.sim.apmv_setpoints import (add_vrf_system, apply_apmv_setpoints,
                                          set_pmv_input_parameters)

    add_vrf_system(building)
    apply_apmv_setpoints(
        building,
        outputs_freq=['hourly'],
        adap_coeff_cooling=0.293,
        adap_coeff_heating=-0.293,
        pmv_cooling_sp=0.5,
        pmv_heating_sp=-0.5,
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
        output_freqs=['hourly'],
        ScriptType='vrf_ac',
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
     - Adds accim to each model (``addAccis``)
     - ``ComfStand``, ``CAT``, ``ComfMod``, ``HVACmode``, ``VentCtrl``, ``ASTtol`` and the other
       arguments of ``addAccis`` (see :doc:`4_detailed use`)
   * - ``'accim custom model'``
     - Adds accim to each model, with the custom adaptive model
     - ``CustAST_m`` (slope of the comfort temperature), ``CustAST_n`` (intercept),
       ``CustAST_ASToffset`` (offset of the setpoints from the comfort temperature) and
       ``CustAST_ASTall``/``CustAST_ASTaul`` (applicability limits of the running mean outdoor
       temperature); the offsets and limits can also be set separately for cooling and heating
       (``CustAST_ACSToffset``, ``CustAST_AHSToffset``, ``CustAST_ACSTall``...)
   * - ``'apmv setpoints'``
     - Applies the aPMV setpoints with the default values of ``apply_apmv_setpoints``, unless
       ``bypass_addAccis=True``
     - ``'Adaptive cooling coefficient'``, ``'Adaptive heating coefficient'``,
       ``'PMV cooling setpoint'``, ``'PMV heating setpoint'``, and ``'Adaptive coefficient'`` and
       ``'PMV setpoint'`` to vary both seasons, or both setpoints (-s and +s), together

``sim.get_available_parameters()`` lists the names. For the aPMV setpoints, apply them yourself
with explicit values, as in step 1, and pass ``bypass_addAccis=True``: the parameters of the study
then replace only the values they vary, and the object does not apply the setpoints again.

The other arguments are passed to ``addAccis``. ``ScriptType`` is ``'vrf_ac'`` (VRF system, fully
air-conditioned), ``'vrf_mm'`` (VRF system with mixed-mode operation) or ``'ex_ac'`` (the existing
HVAC system of the model, fully air-conditioned). Mixed-mode operation needs a model with
calculated natural ventilation (AirflowNetwork); see :doc:`4_detailed use`.

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
  single value.
- Meters are read in J; step 7 converts them to kWh/m².
- To analyse hourly values afterwards (comfort screening, hourly plots), the variables must be
  written hourly (``output_freqs=['hourly']``) and the files of the simulations must be kept
  (step 6).

:doc:`jupyter_notebooks/parametric_and_optimisation_examples/04_outputs_preflight_and_output_control`
shows the other methods for output objects, for example to find and remove duplicates.

4. Define the parameters
------------------------

.. code-block:: python

    sim.set_parameters(
        accis_params_dict={
            'CustAST_m': (0.0, 0.7),          # tuple: range (min, max)
            'CustAST_n': (5.0, 22.5),
            'CustAST_ASToffset': (1.0, 5.0),
            'CustAST_ASTaul': (22.0, 40.0),
        },
        use_dflt_values=True,   # the parameters that are not varied take the defaults of accim
    )
    sim.set_problem()

- A **list** gives the options of a parameter (``'ComfStand': [1, 2]``), and a **tuple** gives its
  range (``'CustAST_m': (0.0, 0.7)``). Which one to use depends on the plan (step 5): options for
  all the combinations, ranges for sampling and optimisation.
- With ``use_dflt_values=True``, the parameters of the custom model that are not varied take the
  values of the ASHRAE 55 adaptive model with 80 % acceptability (m = 0.31, n = 17.8 °C, offsets
  of ±3.5 K, applicability limits of 10 and 33.5 °C), and accim prints them.
- ``additional_params`` adds besos parameters that change any other field of the model, for
  example the thickness of the insulation (see
  :doc:`jupyter_notebooks/parametric_and_optimisation_examples/06_multi_idf_multi_epw_and_custom_plan`).
- :meth:`~accim.parametric_and_optimisation.main.SimulationBase.set_problem` registers the
  parameters and the readers as the inputs and outputs of the problem. In an optimisation, it also
  sets the objectives (step 5).

**The m-n filter (custom model).** Independent ranges of the slope ``CustAST_m`` and the intercept
``CustAST_n`` include many pairs that no published adaptive model has, such as a high slope with a
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
     - all the combinations
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

``constraints`` and ``constraint_bounds`` are passed to the besos ``EPProblem``.

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
non-dominated solutions of each weather file. The notebooks call ``random.seed(...)`` before the
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
continue an interrupted run. ``preflight_report_parametric`` and ``preflight_report_optimisation``
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
