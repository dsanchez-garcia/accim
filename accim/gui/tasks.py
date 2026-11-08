# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The tasks of the graphical user interface of accim: they run accim with the arguments of the forms
(:mod:`accim.gui.forms`), in the working folder (the current directory, which the window sets for each task).

This module does not use tkinter, and imports the modules of accim (and besos, pandas, matplotlib...) only when a task
runs, so that the window opens quickly.
"""

import os
from typing import Any, Dict, List, Mapping, Tuple

__all__ = ['FIGURE_ANSWERS', 'RENAME_EPWS_ANSWERS', 'SESSION_FORMS', 'apmv_target_keys', 'apply_apmv', 'make_figure',
           'make_table', 'occupied_zones', 'open_session', 'open_table', 'parametric_study', 'rename_epws',
           'results_size', 'save_session', 'save_table', 'setpoint_ems_code', 'table_format']

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
#: The name of the values of the forms (the working folder and the fields of each tab) among the objects of the session
#: files of the interface; the others are the results of the tabs that have them: ``table`` (a Table),
#: ``hours_within_setpoints`` (the table of the hours, with the minimum and the zones) and ``parametric_results``.
SESSION_FORMS = 'gui_forms'


def occupied_zones(idf: str, energyplus_version: str = 'auto') -> List[str]:
    """The occupied zones of an IDF (those with People objects), in order: the names that ``zone_arguments`` takes.

    :param idf: The path of the IDF.
    :param energyplus_version: 'auto' or the EnergyPlus version of the IDF.
    """
    from accim.sim.accis import load_idf
    from accim.sim.targets import resolve_targets

    building = load_idf(idf, energyplus_version)
    return list(dict.fromkeys(target.zone_name for target in resolve_targets(building)))


def setpoint_ems_code(calls) -> str:
    """The EMS code of the setpoints of some comfort standards, categories and comfort modes
    (:func:`accim.utils.get_setpoint_ems_code`), one after the other under a title; a combination that gives no
    setpoints gets the reason instead.

    :param calls: The title and the keyword arguments of each call (:func:`accim.gui.forms.setpoint_ems_code_calls`).
    """
    from accim.utils.ems_code import get_setpoint_ems_code

    parts = []
    for title, kwargs in calls:
        try:
            code = get_setpoint_ems_code(**kwargs)
        except ValueError as error:
            code = f'! No EMS code: {error}'
        parts.append(f'! {"=" * 100}\n! {title}\n! {"=" * 100}\n{code}')
    return '\n\n'.join(parts) + '\n'


def results_size(arguments: Mapping[str, Any]) -> Tuple[Any, str]:
    """Estimate the size of the results of the simulations of the folder with
    :func:`accim.run.estimate_results_size` (the arguments of :func:`accim.gui.forms.results_size_arguments`).

    :return: Its table, and the size of all the results, in a sentence.
    """
    from accim.run import estimate_results_size
    from accim.sim.results_size import format_size

    table = estimate_results_size(**arguments)
    total, kept = (float(table[column].sum()) * 1e6 for column in ('total_mb', 'total_kept_mb'))
    epws = int(table['simulations'].max()) if len(table) else 0
    how = 'measured in a simulation' if arguments.get('simulate') else 'estimated from their outputs'
    return table, (f'The results of the {len(table)} IDFs with the {epws} EPWs of the folder ({how}): '
                   f'{format_size(total)}, {format_size(kept)} after "Remove the simulation files".')


def apmv_target_keys(building, values_by_name: Mapping[str, Mapping[str, Any]], idf: str = 'the IDF'):
    """The setpoints of some zones of :func:`accim.sim.apmv.apply_apmv_setpoints` by the keys of their zones in the
    model (that of the target of each occupied zone, :attr:`accim.sim.targets.Target.df_key`: the name of the zone,
    or '<space> <people>' in the models with spaces), from the names of the zones (or those keys), in any case.

    :param values_by_name: The values of each setpoint, ``{argument: {zone: value}}``.
    :raises ValueError: If a zone is not an occupied zone of the model.
    """
    from accim.sim.targets import resolve_targets

    targets = resolve_targets(building)
    keys = {}
    for target in targets:
        keys[target.zone_name.upper()] = target.df_key
        keys[target.df_key.upper()] = target.df_key
    result = {}
    for name, values in values_by_name.items():
        result[name] = {}
        for zone, value in values.items():
            key = keys.get(str(zone).strip().upper())
            if key is None:
                raise ValueError(f'{zone} is not an occupied zone of {idf}: they are '
                                 f'{", ".join(target.zone_name for target in targets)}.')
            result[name][key] = value
    return result


def apply_apmv(arguments: Mapping[str, Any]) -> str:
    """Apply the aPMV setpoints to an IDF and save it with another name (the arguments of
    :func:`accim.gui.forms.apmv_arguments`); the setpoints of some zones get the keys of these zones in the model
    (:func:`apmv_target_keys`).

    :return: The name of the IDF written.
    """
    from accim.sim import apmv
    from accim.sim.accis import load_idf

    building = load_idf(arguments['idf'], arguments['energyplus_version'])
    if arguments['always_occupied']:
        apmv.set_zones_always_occupied(building)
    if arguments['add_vrf_system']:
        apmv.add_vrf_system(building, supply_air_temp_input_method=arguments['supply_air_temp_input_method'])
    setpoints = dict(arguments['apmv'])
    by_zone = {name: value for name, value in setpoints.items() if isinstance(value, Mapping)}
    if by_zone:
        setpoints.update(apmv_target_keys(building, by_zone, arguments['idf']))
    apmv.apply_apmv_setpoints(building, **setpoints)
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


def table_format(table) -> Dict[str, Any]:
    """The arguments of :meth:`Table.format_table` that gave the columns of a table (those of its last call, or all the
    columns if it was not formatted), to make it again from the whole table: before each figure, whose data filter the
    rows of the table, and after opening a table saved in Python."""
    type_of_table = getattr(table, 'type_of_table', 'all')
    if type_of_table == 'custom':
        return dict(type_of_table='custom', custom_cols=list(getattr(table, 'custom_cols', None) or []))
    return dict(type_of_table=type_of_table)


def save_table(table, path: str) -> Tuple[str, str]:
    """Save a table with :meth:`Table.save`: a pickle file, which :func:`open_table` reads, and a JSON file to read it.

    :return: The paths of the two files.
    """
    return table.save(path)


def open_table(path: str):
    """A table saved with :meth:`Table.save` (in Python or by the interface), with the columns that it had."""
    from accim.data.postprocessing.main import Table

    table = Table.load(path)
    table.format_table(**table_format(table))
    return table


def save_session(path: str, objects: Mapping[str, Any]) -> Tuple[str, str]:
    """Save a session of the interface (the values of the forms, :data:`SESSION_FORMS`, and the results of the tabs)
    with :func:`accim.utils.save_session`: a pickle file, which :func:`open_session` reads, and a JSON file to read it.

    :return: The paths of the two files.
    """
    from accim.utils.session import save_session as save

    return save(path, **objects)


def open_session(path: str) -> Dict[str, Any]:
    """The objects of a session saved by the interface (:func:`save_session`).

    :raises ValueError: If the file is not a session of the interface.
    """
    from accim.utils.session import load_session

    session = load_session(path)
    if SESSION_FORMS not in session:
        raise ValueError(f'{path} is a session saved in Python, with {", ".join(session)}, not by the interface. The '
                         f'tables saved with Table.save open with "Open a table..." in the tab "6. Table and '
                         f'figures".')
    return session


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
                                      output_frequencies=['hourly'], script_type=arguments['script_type'],
                                      **dict(arguments.get('existing_hvac') or {}))
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
