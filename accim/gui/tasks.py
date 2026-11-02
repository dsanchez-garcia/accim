# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The tasks of the graphical user interface of accim: they run accim with the arguments of the forms
(:mod:`accim.gui.forms`), in the working folder (the current directory, which the window sets for each task).

This module does not use tkinter, and imports the modules of accim (and besos, pandas, matplotlib...) only when a task
runs, so that the window opens quickly.
"""

import os
from typing import Any, List, Mapping

__all__ = ['FIGURE_ANSWERS', 'RENAME_EPWS_ANSWERS', 'apply_apmv', 'make_figure', 'make_table', 'occupied_zones',
           'parametric_study', 'rename_epws']

#: The questions of rename_epw_files that the interface answers (the beginning of the question -> the answer): no
#: amendments of the names of the cities and no exclusions. The others (a city or country that OpenStreetMap does not
#: give, or a repeated name) need the cities and countries of the form.
RENAME_EPWS_ANSWERS = {
    'If any of the city or subcountry names needs some amendment': '',
    'If you want to exclude some EPWs from renaming': '',
}
#: The questions of the figures of Table that the interface answers: the rows and the columns of the subplots keep
#: their names.
FIGURE_ANSWERS = {
    'Do you want to rename the rows?': 'n',
    'Column names will be the subplot titles. Do you want to rename them?': 'n',
}


def occupied_zones(idf: str, energyplus_version: str = 'auto') -> List[str]:
    """The occupied zones of an IDF (those with People objects), in order: the names that ``zone_arguments`` takes.

    :param idf: The path of the IDF.
    :param energyplus_version: 'auto' or the EnergyPlus version of the IDF.
    """
    from accim.sim.accis import load_idf
    from accim.sim.targets import resolve_targets

    building = load_idf(idf, energyplus_version)
    return list(dict.fromkeys(target.zone_name for target in resolve_targets(building)))


def apply_apmv(arguments: Mapping[str, Any]) -> str:
    """Apply the aPMV setpoints to an IDF and save it with another name (the arguments of
    :func:`accim.gui.forms.apmv_arguments`).

    :return: The name of the IDF written.
    """
    from accim.sim import apmv
    from accim.sim.accis import load_idf

    building = load_idf(arguments['idf'], arguments['energyplus_version'])
    if arguments['always_occupied']:
        apmv.set_zones_always_occupied(building)
    if arguments['add_vrf_system']:
        apmv.add_vrf_system(building, supply_air_temp_input_method=arguments['supply_air_temp_input_method'])
    apmv.apply_apmv_setpoints(building, **arguments['apmv'])
    if arguments['pmv_inputs']:
        apmv.set_pmv_input_parameters(building, **arguments['pmv_inputs'])
    building.saveas(arguments['output_idf'])
    print(f'\nThe IDF with the aPMV setpoints has been saved as {arguments["output_idf"]}')
    return arguments['output_idf']


def rename_epws(arguments: Mapping[str, Any]) -> List[str]:
    """Rename the EPWs of the folder with :class:`accim.data.preprocessing.rename_epw_files` (the arguments of
    :func:`accim.gui.forms.rename_epws_arguments`); the window answers the questions of
    :data:`RENAME_EPWS_ANSWERS`.

    :return: The EPW files of the folder afterwards.
    """
    from accim.data.preprocessing import rename_epw_files

    rename_epw_files(**arguments)
    return sorted(name for name in os.listdir('.') if name.lower().endswith('.epw'))


def _non_interactive_figures() -> None:
    """Make matplotlib draw the figures in files, without windows (the tasks do not run in the thread of the window,
    and Table shows each figure after saving it)."""
    import matplotlib

    matplotlib.use('Agg')


def make_table(arguments: Mapping[str, Any]):
    """The :class:`accim.data.postprocessing.main.Table` of the CSV files of the folder (the arguments of
    :func:`accim.gui.forms.table_arguments`), with the columns of its type of table."""
    _non_interactive_figures()
    from accim.data.postprocessing.main import Table

    table = Table(**arguments['table'])
    table.format_table(type_of_table=arguments['type_of_table'])
    return table


def make_figure(table, arguments: Mapping[str, Any]) -> str:
    """Save a figure of a Table (the arguments of :func:`accim.gui.forms.figure_arguments`) in the folder; the window
    answers the questions of :data:`FIGURE_ANSWERS`.

    :return: The path of the PNG file.
    """
    import warnings

    _non_interactive_figures()
    with warnings.catch_warnings():
        # Table shows the figure after saving it, which does nothing without windows
        warnings.filterwarnings('ignore', message='.*non-interactive.*')
        if arguments['figure_type'] == 'scatter':
            table.scatter_plot(**arguments['kwargs'])
        else:
            table.time_plot(**arguments['kwargs'])
    import matplotlib.pyplot as plt

    plt.close('all')
    path = os.path.abspath(arguments['kwargs']['figname'] + '.png')
    print(f'\nThe figure has been saved as {path}')
    return path


def parametric_study(arguments: Mapping[str, Any]):
    """Run a basic parametric study with :class:`accim.parametric_and_optimisation.main.ParametricSimulation` (the
    arguments of :func:`accim.gui.forms.parametric_arguments`): the outputs are the meters of the form, the plan is
    the full set of the options or a Latin hypercube sample of the ranges, and the coefficients of the custom model
    that are not parameters take the default values.

    :return: The results (a pandas DataFrame, also saved in ``out_dir``).
    """
    from accim.parametric_and_optimisation.main import ParametricSimulation
    from accim.sim.accis import load_idf

    building = load_idf(arguments['idf'], 'auto')
    simulation = ParametricSimulation(buildings=[building], epws=list(arguments['epws']),
                                      parameters_type=arguments['parameters_type'],
                                      output_frequencies=['hourly'], script_type=arguments['script_type'])
    simulation.discover_available_outputs(reduce_sim_time=True, prefer='testsimeplus')
    selection = simulation.select_outputs(meters=list(arguments['meters']), match='case_insensitive',
                                          on_missing='raise', suggest=True)
    simulation.apply_outputs_preflight(df_meters_sel=selection['meters'], df_vars_sel=None, clean_mode='all',
                                       validate_before_apply=False, validate_after_apply=True, on_missing='raise')
    simulation.set_output_readers(df_output_meter=selection['meters'])
    simulation.set_parameters(accis_params_dict=dict(arguments['accis_params_dict']), use_default_values=True)
    simulation.set_problem()
    if arguments['sampling'] == 'full set':
        simulation.sampling_full_set()
    else:
        simulation.sampling_lhs(num_samples=arguments['samples'])
    print(f'\nThe plan has {len(simulation.parameters_values_df)} rows for each EPW.')
    return simulation.run_parametric_simulation(out_dir=arguments['out_dir'], df=simulation.parameters_values_df,
                                                processes=arguments['processes'], keep_input=True,
                                                keep_dirs=False)
