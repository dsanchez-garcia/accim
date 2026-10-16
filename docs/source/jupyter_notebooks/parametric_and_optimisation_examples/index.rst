Parametric simulation and optimisation examples
===============================================

These notebooks show how to run parametric studies and optimisations with the module
``accim.parametric_and_optimisation``, using the sample building models and weather files
distributed with accim. The pages show each notebook as it ran with its default settings: the
tables and figures are its results. :doc:`/parametric_and_optimisation` explains the concepts and
the steps of a study, and says in which notebooks each topic is.

Running the notebooks
---------------------

The notebooks, the sample models and the weather files are installed with the sample files of
accim::

    pip install "accim[samples]"

They are in the folder ``sample_files/jupyter_notebooks/parametric_and_optimisation_examples``
of the installed package (``accim/sample_files/...`` in the
`GitHub repository <https://github.com/dsanchez-garcia/accim/tree/master/accim/sample_files/jupyter_notebooks/parametric_and_optimisation_examples>`_).
To find it::

    import os
    import accim
    print(os.path.join(os.path.dirname(accim.__file__), 'sample_files', 'jupyter_notebooks',
                       'parametric_and_optimisation_examples'))

Copy the folder to a working directory and run the notebooks there: each one writes its results
in a subfolder of that directory. EnergyPlus must be installed; the sample models are in the
format of EnergyPlus 25.2, the version used for the results shown here.

- **Sample models**: ``OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520`` is a two-zone
  residential unit, with a high-performance and a low-performance envelope
  (``_high_performance`` and ``_low_performance``).
- **Weather files**: ``Seville.epw`` and ``Sydney.epw``, one city in each hemisphere.

The simulations are light: 2 timesteps per hour, minimal shadowing, the whole year without the
design days of the models, only the outputs that each notebook uses, and as many simulations in
parallel as half of the logical CPUs. With 12 logical CPUs, each tutorial runs in about 20 s to
2 min, and each complete workflow, which simulates more cases, in the time given below.

Complete workflows
------------------

Five complete studies, from the model to the decision: a parametric run and an optimisation of the
accim custom adaptive model, a parametric run of the accim predefined models, and a parametric run
and an optimisation of the aPMV setpoints. Each one runs on its own. Run times with 12 logical CPUs:

- WF1, parametric run of the custom model (40 annual simulations with hourly outputs): 4 min;
- WF2, parametric run of the predefined models (80 annual simulations, 8 of them again with
  hourly outputs): 6 min;
- WF3, parametric run of the aPMV setpoints (12 annual simulations): 1.5 min;
- WF4, optimisation of the custom model (NSGA-II, 60 evaluations per weather file, and the
  non-dominated solutions again with hourly outputs): 7 min;
- WF5, optimisation of the aPMV setpoints (NSGA-II, 60 evaluations): 3 min.

.. toctree::
   :maxdepth: 1

   wf1_parametricsimulation_accim_custom_model
   wf2_parametricsimulation_accim_predefined_model
   wf3_parametricsimulation_apmv_setpoints
   wf4_optimisationsimulation_accim_custom_model
   wf5_optimisationsimulation_apmv_setpoints

Topic tutorials
---------------

Shorter notebooks, one topic each: the first run, parametric runs of each kind of parameters,
outputs, sampling and sensitivity analysis, several models and weather files, optimisation,
post-processing and decision support. Run them in order: notebooks 09 and 10 reuse the results
of notebooks 02 and 07.

.. toctree::
   :maxdepth: 1

   00_quickstart_environment_and_first_run
   01_parametric_accim_custom_model
   02_parametric_accim_predefined_model
   03_parametric_apmv_setpoints
   04_outputs_preflight_and_output_control
   05_sampling_strategies_and_sensitivity_analysis
   06_multi_idf_multi_epw_and_custom_plan
   07_basic_multiobjective_optimization
   08_advanced_optimization_algorithms_and_constraints
   09_hourly_monthly_postprocessing_normalization_and_plots
   10_decision_support_robustness_and_session_merge

Updating these pages
--------------------

Read the Docs cannot run the notebooks, so these pages show copies that were run beforehand.
After changing a notebook, run it again and export it with ``docs/prepare_parametric_notebooks.py``
(see its docstring)::

    python docs/prepare_parametric_notebooks.py run --run-dir <working folder>
    python docs/prepare_parametric_notebooks.py export --executed-dir <working folder>
