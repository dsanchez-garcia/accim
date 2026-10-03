Filtered copies of simulation output CSVs
=========================================

``ParametricSimulation`` and ``OptimisationSimulation`` inherit
:meth:`~accim.parametric_and_optimisation.main.SimulationBase.filter_simulation_output_csvs`.
This method takes simulations that have already run and writes a copy of each
hourly EnergyPlus CSV (``eplusout.csv``) that contains only the selected
columns.

.. important::

   Creating filtered copies does **not** free disk space while the original
   files remain. The method never modifies or deletes the originals, and it
   does not change the paths stored in the session. Check the copies first.
   You can then archive or delete the originals yourself.

Signature
---------

.. code-block:: python

    report = sim.filter_simulation_output_csvs(
        keep_columns=None,      # str | sequence of str
        drop_columns=None,      # str | sequence of str
        csv_paths=None,         # None -> session results; or explicit paths
        output_dir=None,        # None -> next to each original
        suffix='_filtered',
        chunksize=None,         # rows per block; None -> whole file at once
        overwrite=False,
        encoding='utf-8',
        verbose=True,
    )  # -> pandas.DataFrame (one row per source file)

Behaviour
---------

- **Selection.** Pass exactly one of ``keep_columns`` or ``drop_columns``.
  Each item can be a full column name or a partial pattern. Matching follows
  ``get_hourly_df_parametric(output_columns=...)``. An exact name is tried
  first, then a case-insensitive exact name, then a case-insensitive substring.
  A substring can match several columns, for example the same variable in
  several zones. The ``Date/Time`` column is always kept, regardless of case
  or surrounding spaces.
- **Fidelity.** Rows and columns stay in their original order. Values are
  copied as text, so the method does not normalise or aggregate values or
  rebuild dates. The original line terminator is also preserved.
- **Sources.** By default, paths are resolved from the session results with the
  same logic as the hourly methods. Optimisation sessions include *all*
  evaluations, not only the Pareto front. Relative paths, including relative
  ``output_dir`` values saved in result pickles, are resolved against the
  current working directory. If you pass ``csv_paths``, no results need to be
  loaded. Each path is processed only once.
- **Memory.** CSVs are processed one at a time, and only the needed columns
  are read. With ``chunksize``, rows are also read and written in blocks.
  ``get_hourly_df*`` is not used.
- **Destinations.** By default, the copy is saved next to the original, for
  example as ``eplusout_filtered.csv``. With ``output_dir``, files are named
  ``<parent folder>_eplusout_filtered.csv``. If two names would still collide,
  a numeric suffix (``_2``, ``_3`` …) is added. Existing destinations are
  skipped unless ``overwrite=True``.
- **Safety.** Each copy is first written to a temporary file in the
  destination folder. It is published only after it is complete. If writing
  fails, the temporary file is removed. Invalid global arguments raise an
  error before any file is written. Per-file problems are recorded in the
  report, and processing continues.

Report columns
--------------

``source_path``, ``destination_path``, ``status``, ``rows``,
``original_columns``, ``kept_columns``, ``source_size_bytes``,
``destination_size_bytes``, ``reduction_pct``, ``unmatched_patterns``,
``detail``.

``status`` is one of the following:

- ``written``
- ``skipped_existing``: the destination already existed.
- ``missing``: the source file was not found.
- ``unresolved``: no CSV path could be resolved for a result row.
- ``no_outputs``: the selection would keep only ``Date/Time``, so no file is
  written.
- ``error``

Patterns without matches are listed per file and summarised in a
``UserWarning``.

Examples
--------

Parametric session loaded from disk, with copies next to the originals:

.. code-block:: python

    import os
    from accim.parametric_and_optimisation.main import ParametricSimulation

    os.chdir('Simulaciones_Plan_A')  # folder the stored output_dir paths are relative to
    sim = ParametricSimulation()
    sim.load_outputs_parametric(
        pickle_path='results_exp_4_2_parametric_custom/outputs_param_simulation_20260719_144253.pkl'
    )
    report = sim.filter_simulation_output_csvs(
        keep_columns=['Zone Operative Temperature',
                      'Adaptive Cooling Setpoint',
                      'Adaptive Heating Setpoint'],
        chunksize=2000,
    )
    print(report['status'].value_counts())
    print(report[['source_size_bytes', 'destination_size_bytes']].sum())

Optimisation session (all evaluations), with copies in a separate folder:

.. code-block:: python

    from accim.parametric_and_optimisation.main import OptimisationSimulation

    opt = OptimisationSimulation()
    opt.load_outputs_optimisation(pickle_path='optim_results/outputs_optimisation_20260720_101500.pkl')
    report = opt.filter_simulation_output_csvs(
        drop_columns=['Running Average Outdoor Air Temperature'],
        output_dir='optim_results/filtered_csvs',
    )

Explicit list of files, without loading any results:

.. code-block:: python

    import glob
    sim = ParametricSimulation()
    report = sim.filter_simulation_output_csvs(
        keep_columns='Zone Operative Temperature',
        csv_paths=glob.glob('results/BESOS_Output/*/eplusout.csv'),
        output_dir='results/filtered_csvs',
    )
