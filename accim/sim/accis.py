# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Add the Adaptive-Comfort-Control Implementation Script (ACCIS) to EnergyPlus models.

The ACCIS is an EnergyManagementSystem script that applies adaptive setpoint temperatures.

- :class:`AddAccis` adds it to the IDF files of the working folder (or those given) and writes an output
  IDF for each combination of the arguments (comfort standard, category, comfort mode, HVAC mode...).
- :func:`add_accis_to_idf` adds it to an IDF object of eppy or besos, and :func:`modify_accis` sets the
  arguments of that model.
"""

import os
import tempfile
import warnings
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd

from accim import __version__
from accim._deprecation import accepts_legacy_kwargs, rename_legacy_kwargs, warn_deprecated
from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS
from accim.energyplus import (
    expand_objects,
    find_energyplus,
    idd_path,
    read_idf_version,
    unsupported_version_message,
)
from accim.sim import prompts
from accim.sim.arguments import (
    DEPRECATED_ARGUMENT_NAMES,
    LEGACY_ARGUMENT_NAMES,
    OUTPUT_FREQUENCIES,
    OUTPUT_TYPES,
    SCRIPT_TYPES,
    SUPPLY_AIR_TEMP_INPUT_METHODS,
    CustomRegime,
    as_list,
    check_choice,
    check_custom_regimes,
    is_mixed_mode,
    normalise_energyplus_version,
    normalise_setpoint_type,
    to_bool,
    to_day_of_year,
)
from accim.sim.build import add_accis_objects, add_outputs
from accim.sim.ems.custom_regimes import set_custom_regimes, set_standard_regimes, uses_hvac_conditions
from accim.sim.ems.drift_limiter import ARGUMENTS as DRIFT_ARGUMENTS
from accim.sim.ems.drift_limiter import DEFAULTS as DRIFT_DEFAULTS
from accim.sim.ems.drift_limiter import INPUTS as DRIFT_INPUTS
from accim.sim.ems.drift_limiter import DRIFT_MODES
from accim.sim.ems.drift_limiter import check_drift_arguments, check_window_width, drift_inputs, set_drift_limiter_code
from accim.sim.ems.inputs import (
    check_zone_arguments,
    input_programs,
    input_values,
    read_inputs,
    resolve_zone_arguments,
    set_inputs,
    zone_comfort_standards,
    zone_names,
)
from accim.sim.ems.long_term_discomfort import set_long_term_discomfort_code
from accim.sim.ems.outdoor_metric import (
    INPUTS as OUTDOOR_METRIC_INPUTS,
    OUTDOOR_METRICS,
    begins_with_weather_file,
    check_outdoor_metric_arguments,
    metric_code,
    outdoor_metric_needed,
    set_outdoor_metric_code,
    weather_file_zones,
)
from accim.sim.ems.programs import (
    add_comfort_standard_code,
    add_program,
    code_comfort_standards,
    indent_programs,
    set_comfort_standard_code,
    set_program_lines,
)
from accim.sim.ems.setast import (
    CUSTOM_COMFORT_STANDARD,
    MODULAR_COMFORT_MODES,
    depends_on_comfort_mode,
    master_program_lines,
    subprograms,
)
from accim.sim.ems.setpoint_limits import (
    HOURS_BELOW_PREFIX,
    INPUTS as SETPOINT_LIMIT_INPUTS,
    check_hours_below,
    check_setpoint_limits,
    has_setpoint_limits,
    set_hours_below_code,
    set_setpoint_limits_code,
    warn_crossed_setpoint_limits,
)
from accim.sim.ems.standard_lines import WEATHER_FILE_METRICS, outdoor_metric_standards, standard_inputs
from accim.sim.ems.static_setpoints import (
    ARGUMENTS as STATIC_SETPOINT_ARGUMENTS,
    DEFAULTS as STATIC_SETPOINT_DEFAULTS,
    INPUTS as STATIC_SETPOINT_INPUTS,
    check_static_setpoints,
    has_static_setpoints,
)
from accim.sim.generation import (
    GenerationArguments,
    OutputIdfs,
    combinations,
    output_name,
    set_combination,
    zone_arguments_errors,
    zone_input_arguments,
)
from accim.sim.model import AccimModel, hvac_template_types
from accim.sim.outputs import OUTPUT_DATAFRAME_COLUMNS, enable_sizing_calculations, output_variables_dataframe
from accim.sim.results_size import SIZE_COLUMNS, SimulationSize, estimate_simulation_size, format_size
from accim.sim.standards import comfort_standard_definition, definition_of
from accim.sim.targets import resolve_targets

__all__ = ['AddAccis', 'add_accis_to_idf', 'addAccis', 'gen_outputs_df', 'load_idf', 'modify_accis']

Number = Union[int, float]

BANNER = (
    '\n--------------------------------------------------------'
    f'\nAdaptive-Comfort-Control-Implemented Model (ACCIM) v{__version__}'
    '\n--------------------------------------------------------'
    '\n\nThis tool allows to apply adaptive setpoint temperatures. '
    '\nFor further information, please read the documentation: '
    '\nhttps://accim.readthedocs.io/en/master/'
    '\nFor a visual understanding of the tool, please visit the following jupyter notebooks:'
    '\n-    Using AddAccis() to apply adaptive setpoint temperatures'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/addAccis/using_addAccis.html'
    '\n-    Using rename_epw_files() to rename the EPWs for proper data analysis after simulation'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/rename_epw_files/using_rename_epw_files.html'
    '\n-    Using run_ep() to directly run simulations with EnergyPlus'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/runEp/using_runEp.html'
    '\n-    Using the class Table() for data analysis'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/Table/using_Table.html'
    '\n-    Full example'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/full_example_IBPSA/full_example_IBPSA.html'
    '\n'
    '\nStarting with the process.'
)
_START_MODEL = '\n=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================\n'
_END_MODEL = '\n=======================END OF GENERIC IDF FILE GENERATION PROCESS=======================\n'
_START_OUTPUTS = '\n=======================START OF OUTPUT IDF FILES GENERATION PROCESS=======================\n'
_END_OUTPUTS = '\n=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================\n'


class _Arguments(dict):
    """The arguments of an ACCIS run. The names of accim 0.x also work, with a DeprecationWarning."""

    def _new_name(self, key) -> Optional[str]:
        new = LEGACY_ARGUMENT_NAMES.get(key)
        return new if new is not None and dict.__contains__(self, new) else None

    def __missing__(self, key):
        new = self._new_name(key)
        if new is None:
            raise KeyError(key)
        warn_deprecated(f'arguments[{key!r}]', f'arguments[{new!r}]')
        return dict.__getitem__(self, new)

    def __contains__(self, key) -> bool:
        return dict.__contains__(self, key) or self._new_name(key) is not None

    def get(self, key, default=None):
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        new = self._new_name(key)
        if new is None:
            return default
        warn_deprecated(f'arguments[{key!r}]', f'arguments[{new!r}]')
        return dict.__getitem__(self, new)


# ----------------------------------------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------------------------------------

def _amend_designbuilder_version(path: Union[str, os.PathLike]) -> None:
    """Replace the version of the IDF files of DesignBuilder 7 ('9.4.0.002') with '9.4'."""
    with open(path, 'rb') as file:
        data = file.read()
    if b'Version, 9.4.0.002' in data:
        with open(path, 'wb') as file:
            file.write(data.replace(b'Version, 9.4.0.002', b'Version, 9.4'))


def load_idf(path: Union[str, os.PathLike], energyplus_version: str = 'auto'):
    """Read an IDF file with eppy, with the IDD of its EnergyPlus version.

    eppy reads all the models of a Python session with the IDD of the first one, so the models of other EnergyPlus
    versions need a new Python session.

    :param path: The path of the IDF file.
    :param energyplus_version: 'auto' to take the version of the Version object of the file, or an EnergyPlus version,
        such as '25.1'.
    :return: The IDF object of eppy.
    :raises ValueError: If eppy already reads the models of another EnergyPlus version in this Python session.
    :raises FileNotFoundError: If that EnergyPlus version is not installed (its IDD is needed).
    """
    from eppy.modeleditor import IDF

    _amend_designbuilder_version(path)
    version = normalise_energyplus_version(energyplus_version)
    if version == 'auto':
        version = read_idf_version(path)
    idd = idd_path(version)
    if IDF.getiddname() is None:
        find_energyplus(version)  # FileNotFoundError, with the folders where accim looks for it, if not installed
        IDF.setiddname(idd)
    elif Path(IDF.getiddname()).resolve() != Path(idd).resolve():
        raise ValueError(
            f'eppy is already using the IDD {IDF.getiddname()} in this Python session, and it cannot read '
            f'{os.path.basename(os.fspath(path))}, a model of EnergyPlus {version} (whose IDD is {idd}). Use a new '
            f'Python session for the models of other EnergyPlus versions.'
        )
    return IDF(str(path))


def _idf_version(idf) -> str:
    return '.'.join(str(i) for i in idf.idd_version[:2])


def _input_files(idfs: Optional[Iterable[Union[str, os.PathLike]]]) -> List[str]:
    """The input IDF files: those given, or those in the working folder, without the output IDFs."""
    if idfs is None:
        candidates = sorted(os.listdir())
    else:
        candidates = [os.fspath(f) for f in ([idfs] if isinstance(idfs, (str, os.PathLike)) else idfs)]
    files = [f for f in candidates
             if f.endswith('.idf') and '[' not in os.path.basename(f) and '_pymod' not in os.path.basename(f)]
    if not files:
        raise FileNotFoundError('No idf files were found. There must be at least 1 idf file located at the path '
                                'where this script is being run.')
    return files


# ----------------------------------------------------------------------------------------------------------
# Arguments
# ----------------------------------------------------------------------------------------------------------

def _check_model_arguments(script_type, supply_air_temp_input_method, output_type, output_frequencies,
                           setpoint_type) -> Tuple:
    """Check the arguments of the models; return output_type, output_frequencies and setpoint_type normalised."""
    check_choice('script_type', script_type, SCRIPT_TYPES)
    if script_type.startswith('vrf'):
        check_choice('supply_air_temp_input_method', supply_air_temp_input_method, SUPPLY_AIR_TEMP_INPUT_METHODS)
    check_choice('output_type', output_type.lower() if isinstance(output_type, str) else output_type, OUTPUT_TYPES)
    if output_frequencies is None:
        raise ValueError(f'output_frequencies is required: a list such as {list(OUTPUT_FREQUENCIES[:2])}.')
    output_frequencies = as_list(output_frequencies)
    invalid = [f for f in output_frequencies if not isinstance(f, str) or f.lower() not in OUTPUT_FREQUENCIES]
    if invalid:
        raise ValueError(f'{invalid} are not valid output_frequencies. Valid values: {list(OUTPUT_FREQUENCIES)}.')
    return output_type.lower(), output_frequencies, normalise_setpoint_type(setpoint_type)


def _print_model_arguments(script_type, supply_air_temp_input_method, output_type, output_frequencies,
                           energyplus_version, setpoint_type) -> None:
    print('Basic input data:')
    print(f'Script type is: {script_type}')
    if script_type.startswith('vrf'):
        print(f'Supply Air Temperature Input Method is: {supply_air_temp_input_method}')
    print(f'Output type is: {output_type}')
    print('Output frequencies are: ')
    print(output_frequencies)
    if energyplus_version != 'auto':
        print(f'EnergyPlus version is: {energyplus_version}')
    print(f'Temperature Control method is: {setpoint_type}')


def _check_version(version: str) -> None:
    if version not in SUPPORTED_ENERGYPLUS_VERSIONS:
        raise ValueError(unsupported_version_message(version))


def _to_confirmation(value: Any) -> bool:
    if value is None:
        return input('Do you still want to run ACCIS? [y/n]: ') == 'y'
    if isinstance(value, str):
        return value.lower() in ('y', 'yes', 'true')
    return bool(value)


#: The columns of ``AddAccis.results_size``: a row for each input IDF.
_RESULTS_SIZE_COLUMNS = ['idf', 'output_idfs'] + SIZE_COLUMNS + ['total_mb', 'total_kept_mb']


def _plural(number: int, noun: str) -> str:
    return f'{number} {noun}{"" if number == 1 else "s"}'


def _estimate_results_size(idf, stem: str) -> Optional[SimulationSize]:
    """The estimated size of the results of a simulation of an output IDF of a model, or None (with a warning) if it
    cannot be estimated, which does not stop AddAccis."""
    try:
        return estimate_simulation_size(idf)
    except Exception as error:  # noqa: BLE001 (an estimate must not stop the generation of the output IDFs)
        warnings.warn(f'The size of the results of the output IDFs of {stem} could not be estimated: '
                      f'{type(error).__name__}: {error}', stacklevel=3)
        return None


def _results_size_table(sizes: Dict[str, Optional[SimulationSize]], output_idfs: int) -> pd.DataFrame:
    """A row for each input IDF: the estimated size of the results of a simulation of one of its output IDFs, and
    of all of them with one EPW."""
    rows = []
    for stem, size in sizes.items():
        if size is None:
            continue
        megabytes = size.megabytes()
        rows.append({'idf': stem, 'output_idfs': output_idfs, **megabytes,
                     'total_mb': megabytes['simulation_mb'] * output_idfs,
                     'total_kept_mb': megabytes['kept_mb'] * output_idfs})
    return pd.DataFrame(rows, columns=_RESULTS_SIZE_COLUMNS)


def _results_size_message(sizes: Dict[str, Optional[SimulationSize]], output_idfs: int) -> str:
    """The estimated size of the results of the output IDFs, to choose the outputs before writing them."""
    lines = ['The estimated size of the results of each simulation of the output IDFs, from their outputs (without '
             'simulating them):']
    total = kept = 0.0
    notes = []
    for stem, size in sizes.items():
        if size is None:
            continue
        series = size.describe_series()
        lines.append(f'    {stem} ({_plural(output_idfs, "output IDF")}): {size.describe()}'
                     f'{f"; {series}" if series else ""}')
        notes += [f'{stem}: {note}' for note in size.notes]
        total += size.total * output_idfs
        kept += size.kept * output_idfs
    count = output_idfs * sum(size is not None for size in sizes.values())
    lines.append(f'With each EPW, {"the " if count > 1 else ""}{_plural(count, "output IDF")}: {format_size(total)} '
                 f'({format_size(kept)} after accim.run.remove_files(), which keeps the ESO and CSV files).')
    lines += [f'Note, {note}.' for note in notes]
    lines.append('The outputs decide it (output_type, output_frequencies, outputs_dataframe); '
                 'accim.run.estimate_results_size(simulate=True) measures it in a simulation of an output IDF.')
    return '\n'.join(lines)


def _check_existing_hvac_arguments(operative_temperature_control: Any, availability_schedule: Any,
                                   widen_outdoor_temperature_limits: Any, ideal_loads_backup: Any,
                                   radiant_setpoints: Any) -> Tuple[bool, ...]:
    """Check the arguments of the existing HVAC systems; return existing_hvac_operative_temperature_control,
    existing_hvac_widen_outdoor_temperature_limits, existing_hvac_ideal_loads_backup and
    existing_hvac_radiant_setpoints as booleans."""
    if availability_schedule is not None and (not isinstance(availability_schedule, str)
                                              or not availability_schedule.strip()):
        raise ValueError(f"existing_hvac_availability_schedule must be None or the name of a schedule (such as "
                         f"'On 24/7'), not {availability_schedule!r}.")
    return (to_bool(operative_temperature_control, 'existing_hvac_operative_temperature_control'),
            to_bool(widen_outdoor_temperature_limits, 'existing_hvac_widen_outdoor_temperature_limits'),
            to_bool(ideal_loads_backup, 'existing_hvac_ideal_loads_backup'),
            to_bool(radiant_setpoints, 'existing_hvac_radiant_setpoints'))


def _warn_hvac_zone_map(hvac_zone_map: Optional[Dict[str, str]]) -> None:
    """hvac_zone_map is no longer used: 'ex_mm' does not look for the HVAC equipment of each zone."""
    if hvac_zone_map is not None:
        warnings.warn(
            "hvac_zone_map is deprecated since accim 1.0.0 and has no effect: in mixed mode with the existing HVAC "
            "systems (script type 'ex_mm'), accim reads whether the HVAC system of each zone is on from the load "
            'that its thermostat asks for, whatever its equipment, so it no longer needs the zone of each HVAC '
            'object.',
            DeprecationWarning,
            stacklevel=3,
        )


#: The arguments of the outdoor metric of the custom model (accim.sim.ems.outdoor_metric)
_OUTDOOR_METRIC_ARGUMENTS = ('custom_outdoor_metric', 'custom_alpha', 'custom_days')
#: The arguments of the minimum and maximum of the setpoints (accim.sim.ems.setpoint_limits)
_SETPOINT_LIMIT_ARGUMENTS = ('heating_setpoint_minimum', 'cooling_setpoint_maximum')
#: The arguments of the output IDFs that the prompts do not ask, and their defaults
_NOT_ASKED_ARGUMENTS = (('custom_outdoor_metric', 'pmot'), ('custom_alpha', 0.8), ('custom_days', 30),
                        ('heating_setpoint_minimum', None), ('cooling_setpoint_maximum', None),
                        *zip(STATIC_SETPOINT_ARGUMENTS, STATIC_SETPOINT_DEFAULTS), *DRIFT_DEFAULTS.items())


def _warn_rmot_start(where: str) -> None:
    """Warn that JPN Aqilah 2025 reads the RMOT of EnergyPlus, without the weather file of the simulation (finding B4-1
    of the review of accim 1.2.0)."""
    warnings.warn(f'JPN Aqilah 2025 (comfort standard 23){where} reads the running mean outdoor temperature of CEN '
                  f'15251 that EnergyPlus calculates (RMOT), whose first value in a run period is the sum of the 7 '
                  f'previous days of equation 19.82 of the Engineering Reference, not divided by 1 - 0.8**7 (about '
                  f'21 % below the running mean of EN 16798-1), a difference that decays by 0.8 each day: give the '
                  f'weather file of the simulation (argument epw) so that the EMS calculates the running mean of EN '
                  f'16798-1 with alpha 0.8 from its values.', stacklevel=3)


def _check_static_setpoint_arguments(heating: Any, cooling: Any, zone_arguments: Dict[Any, Dict[str, Any]]) -> None:
    """Check the static setpoints of JPN Aqilah 2025 (:mod:`accim.sim.ems.static_setpoints`), of all the zones and of
    those of ``zone_arguments``.

    :raises ValueError: If they are not valid.
    """
    check_static_setpoints(heating, cooling)
    for zone, arguments in zone_arguments.items():
        if any(name in arguments for name in STATIC_SETPOINT_ARGUMENTS):
            check_static_setpoints(arguments.get(STATIC_SETPOINT_ARGUMENTS[0], heating),
                                   arguments.get(STATIC_SETPOINT_ARGUMENTS[1], cooling), where=str(zone))


def _ems_output_frequencies(idf) -> List[str]:
    """The reporting frequencies of the Output:Variable objects of the EMS output variables of a model (those of the
    ACCIS), in their order (none if it has none)."""
    ems_outputs = {str(o.Name).strip().upper() for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    frequencies: List[str] = []
    for output in idf.idfobjects['Output:Variable']:
        if str(output.Variable_Name).strip().upper() in ems_outputs:
            frequency = str(output.Reporting_Frequency).strip().capitalize()
            if frequency and frequency not in frequencies:
                frequencies.append(frequency)
    return frequencies


def _check_drift_arguments(arguments: Dict[str, Any], zone_arguments: Dict[Any, Dict[str, Any]]) -> bool:
    """Check the arguments of the limiter of the drift of the setpoints (:mod:`accim.sim.ems.drift_limiter`), of all
    the zones and of those of ``zone_arguments``; return True if a zone has ``drift_mode``.

    :param arguments: The arguments of the call (``drift_mode``, ``max_drift_rate``...; None is not given).
    :raises ValueError: If they are not valid.
    """
    check_drift_arguments(**arguments)
    found = arguments.get('drift_mode') is not None
    for zone, own in zone_arguments.items():
        given = {name: own[name] for name in DRIFT_ARGUMENTS if name in own}
        if given:
            check_drift_arguments(**given, where=str(zone))
            found = found or given.get('drift_mode') is not None
    return found


def _check_window_widths(arguments: Dict[str, Any], zone_arguments: Dict[Any, Dict[str, Any]],
                         tolerance: Any) -> None:
    """Check the width of the window of the limiter of the drift of the setpoints
    (:func:`accim.sim.ems.drift_limiter.check_window_width`) of all the zones and of those of ``zone_arguments``, with
    their tolerance of the setpoints (that of the zone, or ``tolerance``).

    :raises ValueError: If a window is narrower than twice the tolerance.
    """
    def check(own: Dict[str, Any], where: str = '') -> None:
        values = {**arguments, **{name: own[name] for name in DRIFT_ARGUMENTS if own.get(name) is not None}}
        if values.get('drift_mode') == 'window':
            check_window_width(values.get('delta_heat', DRIFT_DEFAULTS['delta_heat']),
                               values.get('delta_cool', DRIFT_DEFAULTS['delta_cool']),
                               own.get('setpoint_tolerance', tolerance), where=where)

    check({})
    for zone, own in zone_arguments.items():
        check(own, str(zone))


def _check_setpoint_limits(minimum: Any, maximum: Any, zone_arguments: Dict[Any, Dict[str, Any]]) -> bool:
    """Check the minimum heating setpoint and the maximum cooling setpoint, of all the zones and of those
    of ``zone_arguments``; return True if a zone has one of them.

    :raises ValueError: If they are not valid.
    """
    check_setpoint_limits(minimum, maximum)
    found = minimum is not None or maximum is not None
    for zone, arguments in zone_arguments.items():
        if any(name in arguments for name in _SETPOINT_LIMIT_ARGUMENTS):
            check_setpoint_limits(arguments.get('heating_setpoint_minimum', minimum),
                                  arguments.get('cooling_setpoint_maximum', maximum), where=str(zone))
            found = True
    return found


def _add_hours_below_outputs(idf, frequencies: Iterable[str]) -> None:
    """The Output:Variable objects of the hours below some temperatures (report_hours_below), at the output
    frequencies, for the outputs that do not have them (output_type 'simplified')."""
    names = [o.Name for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']
             if str(o.Name).startswith(HOURS_BELOW_PREFIX)]
    _request_outputs(idf, names, frequencies)


def _request_outputs(idf, names: Iterable[str], frequencies: Iterable[str]) -> None:
    """Add the Output:Variable objects of some outputs at some frequencies that the model does not have."""
    names = list(names)
    requested = {(str(o.Variable_Name).upper(), str(o.Reporting_Frequency).upper())
                 for o in idf.idfobjects['Output:Variable']}
    for frequency in frequencies:
        for name in names:
            if (name.upper(), frequency.upper()) not in requested:
                idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name,
                                 Reporting_Frequency=frequency.capitalize(), Schedule_Name='')


def _check_long_term_discomfort(report_long_term_discomfort: Any, setpoint_type: str) -> bool:
    """Check ``report_long_term_discomfort``: a boolean, and only with ``setpoint_type`` 'temperature'.

    :raises ValueError: If it is not valid.
    """
    if not isinstance(report_long_term_discomfort, bool):
        raise ValueError(f'report_long_term_discomfort must be True or False, not {report_long_term_discomfort!r}.')
    if report_long_term_discomfort and setpoint_type == 'pmv':
        raise ValueError("report_long_term_discomfort needs setpoint_type 'temperature': with 'pmv', the Fanger "
                         "thermostats control the zones, and the range of the long-term discomfort (the setpoints of "
                         "the ACCIS) is not that of the control.")
    return report_long_term_discomfort


def _check_long_term_range(long_term_range: Any, report_long_term_discomfort: bool) -> Any:
    """Check ``long_term_range`` (:func:`accim.sim.ems.long_term_discomfort.long_term_limits`), which needs
    ``report_long_term_discomfort``.

    :raises ValueError: If it is not valid, or it is given without ``report_long_term_discomfort``.
    """
    from accim.sim.ems.long_term_discomfort import long_term_limits

    long_term_limits(long_term_range)
    if long_term_range is not None and not report_long_term_discomfort:
        raise ValueError('long_term_range is the range of the long-term discomfort: it needs '
                         'report_long_term_discomfort=True.')
    return None if long_term_range is None else tuple(long_term_range)


def _check_outdoor_metric(metric: Any, alpha: Any, days: Any, zone_arguments: Dict[Any, Dict[str, Any]],
                          epw: Optional[Union[str, os.PathLike]]) -> Optional[str]:
    """Check the arguments of the outdoor metric of the custom model, of all the zones and of those of
    ``zone_arguments`` (with the warnings of decision D7), and the weather file; return its path.

    :raises ValueError: If an argument is not valid, ``epw`` is not a file, or 'monthly_mean' has no weather file
        (decision D3).
    """
    codes = {check_outdoor_metric_arguments(metric, alpha, days)}
    for zone, arguments in zone_arguments.items():
        if any(name in arguments for name in _OUTDOOR_METRIC_ARGUMENTS):
            codes.add(check_outdoor_metric_arguments(arguments.get('custom_outdoor_metric', metric),
                                                     arguments.get('custom_alpha', alpha),
                                                     arguments.get('custom_days', days), where=str(zone)))
    if epw is not None:
        if not os.path.isfile(epw):
            raise ValueError(f'epw must be the path of a weather file (EPW), not {epw!r}.')
        epw = os.path.abspath(epw)
    elif OUTDOOR_METRICS['monthly_mean'] in codes:
        raise ValueError("custom_outdoor_metric 'monthly_mean' needs the weather file of the simulations (argument "
                         "epw), whose monthly means the EMS programs keep.")
    return epw


# ----------------------------------------------------------------------------------------------------------
# AddAccis: files
# ----------------------------------------------------------------------------------------------------------

class AddAccis:
    """Add the ACCIS to IDF files and write an output IDF for each combination of the arguments.

    The input IDFs are those given in ``idfs`` or, by default, all the IDF files in the working folder
    (except the output IDFs, whose names contain '['). The output IDFs are written next to them, with
    names that give their arguments, such as ``Model[CS_INT EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf``.

    Each output IDF only has the EMS code of the comfort standards of its zones (its comfort standard, and those of
    ``zone_arguments``), so its comfort standard can only be changed with :func:`modify_accis`, which adds the code of
    the new one. The lines of the EMS programs are indented inside the blocks IF and WHILE.

    The missing arguments are asked: those of the models if ``script_type``, ``output_type``,
    ``output_frequencies``, ``keep_existing_outputs``, ``setpoint_type`` or (with VRF systems)
    ``supply_air_temp_input_method`` is None, and those of the output IDFs if ``comfort_standard``, ``category``,
    ``comfort_mode`` or (in mixed mode) ``hvac_mode`` or ``ventilation_control`` is None.

    :param idfs: The IDF files. By default, those in the working folder.
    :param script_type: 'vrf_ac' (a new VRF system in each occupied zone, full air-conditioning), 'vrf_mm' (VRF
        system, mixed mode), 'ex_ac' (the existing HVAC systems, full air-conditioning) or 'ex_mm' (existing HVAC
        systems, mixed mode).
    :param supply_air_temp_input_method: 'supply air temperature' or 'temperature difference' (VRF systems only).
    :param output_type: 'standard', 'simplified', 'detailed' or 'custom' (which asks which outputs to keep).
    :param output_frequencies: The reporting frequencies of the outputs: a list of 'timestep', 'hourly', 'daily',
        'monthly' and 'runperiod'.
    :param keep_existing_outputs: True to keep the Output:Variable objects of the models.
    :param make_outputs_dataframe: True to keep a DataFrame with the Output:Variable objects in ``df_outputs``.
    :param outputs_dataframe: A DataFrame like ``df_outputs``, filtered to keep the outputs wanted, which
        replace those of the models.
    :param energyplus_version: '9.1' to '26.2', or 'auto' to read it from the models.
    :param setpoint_type: 'temperature' (or 'temp') for adaptive setpoint temperatures, or 'pmv' for setpoints based
        on the PMV of Fanger.
    :param vrf_availability_schedule: The availability schedule of the VRF systems.
    :param comfort_standard: The comfort standards (a list): 0 = ESP CTE; 1 = INT EN16798-1; 2 = INT ASHRAE55;
        3 = JPN Rijal; 4 = CHN GBT50785 Cold; 5 = CHN GBT50785 HotMild; 6 = CHN Yang; 7 = IND IMAC C NV;
        8 = IND IMAC C MM; 9 = IND IMAC R 7DRM; 10 = IND IMAC R 30DRM; 11 = IND Dhaka; 12 = ROM Udrea;
        13 = AUS Williamson; 14 = AUS DeDear; 15 = BRA Rupp NV; 16 = BRA Rupp AC; 17 = MEX Oropeza Arid;
        18 = MEX Oropeza DryTropic; 19 = MEX Oropeza Temperate; 20 = MEX Oropeza HumTropic;
        21 = CHL Perez-Fargallo; 22 = INT ISO7730; 23 = JPN Aqilah2025; 99 = CUSTOM; and those of the comfort standards
        defined by their data of the registry (100 or more, :mod:`accim.sim.standards`).
    :param category: The categories (a list): 1, 2 or 3 (CAT I, II, III), or 80, 85 or 90 (% of acceptability).
    :param category_cooling_offset: An offset summed to the cooling setpoint offset of the category.
    :param category_heating_offset: An offset summed to the heating setpoint offset of the category.
    :param comfort_mode: The comfort modes (a list): 0 or 0.X = static; 1 or 1.X = adaptive when applicable,
        otherwise the local static model; 2 = adaptive when applicable, otherwise the international static
        model; 3 = adaptive when applicable, otherwise the adaptive setpoints extended horizontally.
    :param setpoint_accuracy: The accuracy of the setpoints: 2 rounds them to every half degree, 10 to the first
        decimal...
    :param custom_cooling_upper_limit: Custom model (comfort_standard 99): upper applicability limit of the cooling
        setpoint (of the running mean outdoor temperature).
    :param custom_cooling_lower_limit: Custom model: lower applicability limit of the cooling setpoint.
    :param custom_heating_upper_limit: Custom model: upper applicability limit of the heating setpoint.
    :param custom_heating_lower_limit: Custom model: lower applicability limit of the heating setpoint.
    :param custom_slope: Custom model: slope m of the comfort temperature (m * running mean outdoor temperature + n).
    :param custom_intercept: Custom model: intercept n of the comfort temperature.
    :param custom_cooling_offset: Custom model: offset of the cooling setpoint from the comfort temperature (positive).
    :param custom_heating_offset: Custom model: offset of the heating setpoint from the comfort temperature (negative).
    :param cooling_season_start: The start of the cooling season (a date 'dd/mm' or a day of the year), used by
        some static models.
    :param cooling_season_end: The end of the cooling season.
    :param hvac_mode: The HVAC modes (a list): 0 = fully air-conditioned; 1 = naturally ventilated; 2 = mixed mode.
    :param ventilation_control: The ventilation controls (a list). With HVAC mode 1: 0 = ventilates above the comfort
        temperature; 1 = above the upper comfort limit. With HVAC mode 2: 0 = above the comfort temperature,
        opening the windows fully; 1 = above the lower comfort limit, opening them fully; 2 and 3 = like 0 and 1,
        with the customised venting opening factor.
    :param opening_factor_max_temp_diff: The maximum temperature difference (indoor minus outdoor) of the venting
        opening factor (greater than 0).
    :param opening_factor_min_temp_diff: The minimum temperature difference of the venting opening factor.
    :param min_opening_factor: The venting opening factor from the maximum temperature difference up (between 0 and
        1): with the ventilation controls 2 and 3, the opening factor goes from 1, below the minimum temperature
        difference, to this value, above the maximum one.
    :param ventilation_setpoint_offset: The offsets of the ventilation setpoint temperature (a list).
    :param min_outdoor_temp_offset: The offsets of the minimum outdoor temperature for ventilation (a list).
    :param max_wind_speed: The maximum wind speeds for ventilation (a list).
    :param setpoint_tolerance_start: The first tolerance of the setpoints.
    :param setpoint_tolerance_end: The last tolerance of the setpoints.
    :param setpoint_tolerance_step: The step between tolerances.
    :param name_suffix: A suffix for the names of the output IDFs.
    :param verbose: True to print the process.
    :param confirm: True to write the output IDFs without asking; None to ask.
    :param vrf_eer: The energy efficiency ratio of the VRF systems.
    :param vrf_cop: The coefficient of performance of the VRF systems.
    :param add_building_averages: True to add the building averages of the hours of each zone and of some outputs.
    :param debug_ems: True to make EnergyPlus write the EDD file of the EMS.
    :param hvac_zone_map: Deprecated since accim 1.0.0, without effect: 'ex_mm' reads whether the HVAC system of
        each zone is on from the load that its thermostat asks for, so it no longer needs the zone of each existing
        HVAC object.
    :param zone_arguments: The arguments of some zones, which are the same in all the output IDFs:
        ``{zone: {argument: value}}``, for instance ``{'Block1:Zone1': {'comfort_standard': 2, 'category': 80,
        'comfort_mode': 3}}``. The zones are the occupied zones, given by their names (or '<space> <people>', as in
        the dictionaries of :func:`accim.sim.apmv.apply_apmv_setpoints`); the arguments are those of
        :func:`modify_accis`, with one value each (the tolerance of the setpoints is ``setpoint_tolerance``). The other
        arguments of these zones, and the arguments of the other zones, are those of each output IDF, whose name
        does not change. Each zone needs a valid combination of comfort standard, category and comfort mode, and
        the HVAC mode and ventilation control of mixed mode only with 'vrf_mm' and 'ex_mm'. Only with temperature
        control (``setpoint_type`` 'temperature').
    :param existing_hvac_operative_temperature_control: With the existing HVAC systems ('ex_ac' and 'ex_mm') and
        ``setpoint_type`` 'temperature': True (the default) to make the thermostat of each occupied zone control the
        operative temperature of the zone between its setpoints at all times, as the thermostats of the VRF systems: it
        gets a ThermostatSetpoint:DualSetpoint object of its own with the setpoint schedules of the zone, a control
        type schedule that always selects it, and a ZoneControl:Thermostat:OperativeTemperature object (radiative
        fraction 0.5, and 0 on the design days, so that the sizing does not change) if it has none. False keeps the
        thermostats of the model, which control the air temperature, and gives the setpoints only to the setpoint
        object of the first control of each thermostat, as accim 0.x did.
    :param existing_hvac_availability_schedule: With the existing HVAC systems, the name of a schedule of the model,
        or 'On 24/7' (always 1, added if the model does not have it), that becomes the availability schedule of the
        HVAC objects that heat or cool the zones (zone equipment, air terminals, unitary systems, fans, coils...) and
        replaces the availability managers of their air and plant loops, so that, with 'On 24/7', they are always
        available. None (the default) keeps their availability, and warns if it can switch them off, since they
        cannot keep the zones between the setpoints while they are off.
    :param existing_hvac_widen_outdoor_temperature_limits: With the existing HVAC systems, True to widen the outdoor
        temperature limits of their HVAC objects (the outdoor temperatures outside which the compressors of their DX
        coils and VRF systems, or their supplemental heaters, do not work: the VRF systems do not cool above 43 °C
        and do not heat above 16 °C by default in EnergyPlus, for instance) to those of the VRF systems of accim, -20
        and 80 °C (or the bounds of the IDD, if they are narrower). False (the default) keeps them, and warns if they
        are narrower.
    :param existing_hvac_ideal_loads_backup: With the existing HVAC systems, True to add to each occupied zone a
        backup ideal loads air system ('<zone> ACCIS Backup Ideal Loads'), the last equipment of the zone, which
        supplies the load to the setpoints that the existing HVAC system does not meet, whatever its type and the
        reason (capacity, controls, operating limits, availability, no equipment that cools or heats...), so that the
        operative temperature stays between the setpoints. Its energy is reported apart, as district heating and
        cooling and in the outputs 'Zone Ideal Loads Zone Sensible Heating Rate' and 'Zone Ideal Loads Zone Sensible
        Cooling Rate'. False (the default) adds nothing.
    :param existing_hvac_radiant_setpoints: With the existing HVAC systems and ``setpoint_type`` 'temperature': True
        (the default) to make their radiant systems (``ZoneHVAC:LowTemperatureRadiant:*``,
        ``ZoneHVAC:HighTemperatureRadiant``),
        ventilated slabs and cooling panels, which heat or cool with setpoint schedules of their own, not with the
        thermostats, follow the setpoints of their zones: they get the setpoint schedules of their zones in their
        heating and cooling setpoint fields (both the high and the low control temperatures of the constant flow
        radiant systems and the ventilated slabs, which then work at full output beyond the setpoints) and the
        operative temperature as their control temperature (the cooling panels in zones with a thermostat get the
        control type ZoneTotalLoad, so that they follow the thermostat); a design object that several zones share is
        copied for each zone. False keeps them as in the model, with a warning.
    :param custom_outdoor_metric: Custom model: the outdoor temperature of reference of its comfort temperature
        (m * metric + n), setpoints and applicability (:data:`accim.sim.ems.outdoor_metric.OUTDOOR_METRICS`): 'pmot'
        (the default, as before accim 1.2.0), the running mean of ASHRAE 55 that EnergyPlus calculates; 'rmot', that
        of CEN 15251 of EnergyPlus; 'rmot_alpha', the running mean of EN 16798-1:2019, formula (B.1), with
        ``custom_alpha``; 'rmot_7day', its approximate formula (B.2); 'daily_mean', the daily mean of the previous day;
        'ndrm', the arithmetic mean of the daily means of the ``custom_days`` previous days (ASHRAE 55-2020,
        5.4.2.1); 'monthly_mean', the monthly mean of the weather file ``epw``; 'te_ref_nl', the reference
        temperature of the Dutch ATG (van der Linden et al., 2006), whose T0, the mean of the maximum and minimum of
        the day itself, is that of the weather file ``epw`` (a Schedule:File object whose CSV file is written in the
        folder of the output IDFs), or that of the previous day without it. The EMS calculates them from the outdoor
        dry-bulb temperature (:mod:`accim.sim.ems.outdoor_metric`); with a metric other than 'pmot', the output IDFs
        of the custom model have these EMS programs, and the outputs ``Tout_metric`` and ``Tout_metric_<zone>``.
    :param custom_alpha: Custom model, 'rmot_alpha': the alpha of the running mean, between 0 and 1 (EN 16798-1
        recommends 0.8); outside 0.6 to 0.9 (ASHRAE 55-2020, 5.4.2.1) it warns.
    :param custom_days: Custom model, 'ndrm': the number of previous days (30 by default); outside 7 to 30 (ASHRAE
        55-2020, 5.4.2.1) it warns.
    :param epw: The weather file (EPW) of the simulations, with which the outdoor metrics of the custom model that the
        EMS calculates begin on the first day of the RunPeriod of the model (the running means of the previous days,
        as :func:`accim.sim.preview.outdoor_metrics` calculates them), and whose monthly means 'monthly_mean' needs.
        Without it, they begin with the running mean of ASHRAE 55 of EnergyPlus, with a warning. With it, JPN Aqilah
        2025 (comfort standard 23) uses the running mean of EN 16798-1:2019 (B.1) with α = 0.8 that the EMS calculates
        from it ('rmot_alpha', as the comfort standard of the sample file
        ``accim/sample_files/comfort_standards/jpn_aqilah2025_fr.yaml``) instead of the RMOT of EnergyPlus, whose
        first value in a run period is lower (equation 19.82 of the Engineering Reference is not divided by 1 − α⁷,
        about 21 % below the running mean, a difference that decays by α each day); without it, JPN Aqilah 2025 reads
        the RMOT of EnergyPlus, with a warning (finding B4-1 of the review of accim 1.2.0).
    :param heating_setpoint_minimum: The minimum heating setpoint (°C), or None (the default) for none: in every
        comfort standard and comfort mode, the heating setpoint is not lower (the input ``AHSTmin`` of each zone,
        see :mod:`accim.sim.ems.setpoint_limits`); EN 16798-1:2019 (B.2.2) applies in winter the minimums of its Table
        B.2 (:data:`accim.constants.EN16798_TABLE_B2`). Also for each zone in ``zone_arguments``. Only with
        ``setpoint_type`` 'temperature' (the setpoints based on the PMV have none). The setpoints are bounded before
        their rounding, and the setpoints without the tolerance (the limits of the comfort band of the hour counters)
        are bounded too (finding B5-1 of the review of accim 1.2.0).
    :param cooling_setpoint_maximum: The maximum cooling setpoint (°C), or None (the default) for none: the
        cooling setpoint is not higher (the input ``ACSTmax``), as the maximums of Table B.2 of EN 16798-1. A cooling
        setpoint bounded by the maximum is the maximum, and a heating setpoint bounded by the minimum the minimum (not
        one step of ``setpoint_accuracy`` beyond them, as the strict rounding would give: finding B5-2). It must be
        higher than the minimum. With the weather file of the simulations (``epw``), a warning tells of the zones whose
        minimum is at or above the cooling setpoint of their comfort model, or whose maximum is at or below its heating
        setpoint, in some timestep of the run period of the model, since the heating setpoint is then at or above the
        cooling setpoint (:func:`accim.sim.ems.setpoint_limits.warn_crossed_setpoint_limits`, with the setpoints of
        :func:`accim.sim.preview.compute_setpoints`); without it, no warning.
    :param report_hours_below: A list of temperatures (°C), such as ``[18, 17, 16]``, or None (or an empty list) for
        none: the output IDFs report the occupied hours of each zone with the operative temperature below each of
        them, ``HoursBelow_<T>_<zone>`` (``HoursBelow_18_<zone>``, and ``HoursBelow_17p5_<zone>`` for 17.5), with
        every ``output_type`` but 'custom', which keeps the outputs chosen.
    :param custom_regimes: Custom model: a list of regimes (:class:`accim.sim.arguments.CustomRegime`), each one with
        the coefficients of the custom model (slope, intercept, offsets and applicability limits) and the condition
        under which they apply: 'always' (only the last regime), 'cooling_season', 'heating_season', 'hvac_off' and
        'hvac_on' (these two, in mixed mode only), ``('metric_below', x)``, ``('metric_above', x)`` or
        ``('metric_between', (x1, x2))`` (the outdoor metric of the custom model). In each timestep, the first regime
        whose condition holds applies (the order of the list is the priority); if none holds, the scalar arguments
        (``custom_slope``...) apply. None (the default) for none: the custom model has the scalar arguments only, as
        before accim 1.2.0. The zones of the custom model get the program SelectCustomRegime_<zone> and the output
        ``CustomRegime_<zone>``, the number of the regime of each timestep (0 for the scalar arguments); see
        :mod:`accim.sim.ems.custom_regimes`. It needs ``comfort_standard`` 99 (in the output IDFs or in
        ``zone_arguments``) and ``setpoint_type`` 'temperature'. The zones of the comfort standards of the registry
        with regimes (the key ``regimes`` of their YAML files, :mod:`accim.sim.standards`) get those of their comfort
        standard, with the same program, whatever this argument.
    :param report_long_term_discomfort: True to report the long-term thermal discomfort of the occupied hours of each
        zone and of the building, Methods A and B of CEN/TR 16798-2:2019, Annex D, with the range between the setpoints
        without the tolerance of the ACCIS (:mod:`accim.sim.ems.long_term_discomfort`): the outputs ``Hours Above Upper
        Limit_<zone>``, ``Hours Below Lower Limit_<zone>`` (in hours), ``Degree Hours Above Upper Limit_<zone>`` and
        ``Degree Hours Below Lower Limit_<zone>`` (in degree hours, Kh), and their sums ``..._Building``, with every
        ``output_type`` but 'custom', which keeps the outputs chosen. The parametric and optimisation module reads them
        as objectives and constraints (:mod:`accim.parametric_and_optimisation.objectives`). False (the default) for
        none, as before accim 1.2.0. It needs ``setpoint_type`` 'temperature'.
    :param long_term_range: With ``report_long_term_discomfort``, the range of the long-term discomfort: None (the
        default) for the setpoints without the tolerance of the ACCIS (how well the control keeps its own band), or
        ``('en16798', category)`` (1 to 4) or ``('en16798', category, building_type)`` ('residential' or 'office',
        needed in categories III and IV) for the constant limits of EN 16798-1:2019, Table B.2, the minimum for heating
        and the maximum for cooling of the category (20.0 and 26.0 °C in category II), so that models with different
        comfort standards are compared with the same range (finding C2-1 of the review of accim 1.2.0;
        :func:`accim.sim.ems.long_term_discomfort.long_term_limits`).
    :param static_heating_setpoint: The static heating setpoint (°C) of the comfort standards whose standard does not
        give it, in comfort mode 0 and out of the applicability limits in comfort mode 1: only JPN Aqilah 2025
        (comfort standard 23), whose paper gives no static setpoints (decision D2 of the brief of 1.2.0); 20.0 by
        default. The other comfort standards ignore it (they have the static setpoints of their standards). Its zones
        have it as the input ``StaticAHST`` (:mod:`accim.sim.ems.static_setpoints`). Also for each zone in
        ``zone_arguments``.
    :param static_cooling_setpoint: The static cooling setpoint (°C) of the same comfort standards (the input
        ``StaticACST``); 28.0 by default. It must be higher than ``static_heating_setpoint``.
    :param drift_mode: The limiter of the drift of the setpoints by the indoor thermal history (task F2 of block F,
        after Parkinson, de Dear & Brager, 2020; see :mod:`accim.sim.ems.drift_limiter`): None (the default) for none,
        and the output IDFs are those without it; 'rate', the setpoints of each day within ``max_drift_rate`` of the
        mean of those applied in the occupied timesteps of the last day with occupants (the first occupied day without
        limit); 'window', the setpoints within
        [T_rm_in − ``delta_heat``, T_rm_in + ``delta_cool``], with T_rm_in the exponentially weighted daily running
        mean of the operative temperature of the zone in its occupied hours (``alpha_indoor``), inactive until one
        full occupied day unless ``initial_T_rm_in`` is given. It limits the setpoints of any comfort standard (and
        those of a hook of the API backend), before the minimum and maximum of the setpoints; the zones get the
        program ApplyDriftLimiter_<zone> and the outputs ``T_rm_in_<zone>``, ``DriftTargetAHST_<zone>``,
        ``DriftTargetACST_<zone>``, ``DriftAppliedAHST_<zone>``, ``DriftAppliedACST_<zone>`` and
        ``DriftLimitedHours_<zone>``. Also for each zone in ``zone_arguments``. Only with ``setpoint_type``
        'temperature'.
    :param max_drift_rate: 'rate': the largest change of the setpoints from one day to the next (K/day), greater than
        0; 0.5 by default.
    :param alpha_indoor: 'window': the weight of the running mean of the day before, from 0 to 1 (1 excluded); 0.8 by
        default, as the running mean of EN 16798-1.
    :param delta_cool: 'window': the largest distance of the setpoints above T_rm_in (K); 1.0 by default.
    :param delta_heat: 'window': the largest distance of the setpoints below T_rm_in (K); 1.0 by default.
    :param initial_T_rm_in: 'window': the first T_rm_in (°C), with which the limiter is active from the first day;
        None (the default) to start it with the mean of the first occupied day.
    :ivar arguments: The arguments, after asking the missing ones.
    :ivar input_idfs: The input IDFs, {'input IDF name': IDF object}.
    :ivar occupied_zones: The occupied zones of each input IDF, as in the EMS objects.
    :ivar occupied_zones_original_name: The occupied zones of each input IDF.
    :ivar windows_and_doors: The windows and doors that open in each input IDF, as in the EMS objects (mixed mode).
    :ivar windows_and_doors_original_name: The windows and doors that open in each input IDF (mixed mode).
    :ivar zone_arguments: The arguments of the zones of ``zone_arguments`` in each input IDF, by the names of the
        zones in the EMS objects: ``{input IDF name: {zone: {argument: value}}}``.
    :ivar output_idfs: The output IDFs, {'output IDF file name': IDF object} (each one is read when it is used;
        ``output_idfs.paths`` has their paths).
    :ivar df_outputs: The DataFrame of Output:Variable objects (argument ``make_outputs_dataframe``).
    :ivar results_size: The size of the results of the simulations of the output IDFs, estimated from their outputs
        without simulating them (:func:`accim.sim.results_size.estimate_simulation_size`), which AddAccis prints
        before writing the output IDFs, so that other outputs can be chosen: a row for each input IDF, with the size of
        each file of a simulation of one of its output IDFs in MB ('eso_mb', 'csv_mb', 'mtr_mb', 'meter_csv_mb',
        'sql_mb', 'other_mb'), that of the whole simulation ('simulation_mb'), that of the files that
        :func:`accim.run.remove_files` keeps ('kept_mb'), the memory to read the values of its CSV file
        ('csv_memory_mb') and the size of the simulations of all its output IDFs with one EPW ('total_mb',
        'total_kept_mb'). :func:`accim.run.estimate_results_size` estimates or measures the size of the results of the
        output IDFs and EPWs of a folder.
    """

    # heating_setpoint_floor and cooling_setpoint_ceiling, the names of the development of 1.2.0
    @accepts_legacy_kwargs(DEPRECATED_ARGUMENT_NAMES, version='1.2.0')
    def __init__(
        self,
        idfs: Optional[Sequence[Union[str, os.PathLike]]] = None,
        script_type: Optional[str] = None,
        supply_air_temp_input_method: Optional[str] = None,
        output_type: Optional[str] = None,
        output_frequencies: Optional[Sequence[str]] = None,
        keep_existing_outputs: Optional[bool] = None,
        make_outputs_dataframe: Optional[bool] = None,
        outputs_dataframe: Optional[pd.DataFrame] = None,
        energyplus_version: str = 'auto',
        setpoint_type: Optional[str] = None,
        vrf_availability_schedule: str = 'On 24/7',
        comfort_standard: Optional[Sequence[int]] = None,
        category: Optional[Sequence[Number]] = None,
        category_cooling_offset: Number = 0,
        category_heating_offset: Number = 0,
        comfort_mode: Optional[Sequence[Number]] = None,
        setpoint_accuracy: Number = 10000,
        custom_cooling_upper_limit: Number = 0,
        custom_cooling_lower_limit: Number = 0,
        custom_heating_upper_limit: Number = 0,
        custom_heating_lower_limit: Number = 0,
        custom_slope: Number = 0,
        custom_intercept: Number = 0,
        custom_cooling_offset: Number = 0,
        custom_heating_offset: Number = 0,
        cooling_season_start: Union[int, str] = 121,
        cooling_season_end: Union[int, str] = 274,
        hvac_mode: Optional[Sequence[int]] = None,
        ventilation_control: Optional[Sequence[int]] = None,
        opening_factor_max_temp_diff: Number = 6,
        opening_factor_min_temp_diff: Number = 1,
        min_opening_factor: Number = 0.25,
        ventilation_setpoint_offset: Sequence[Number] = (0,),
        min_outdoor_temp_offset: Sequence[Number] = (50,),
        max_wind_speed: Sequence[Number] = (50,),
        setpoint_tolerance_start: Number = 0.1,
        setpoint_tolerance_end: Number = 0.1,
        setpoint_tolerance_step: Number = 0.1,
        name_suffix: str = '',
        verbose: bool = True,
        confirm: Optional[bool] = None,
        vrf_eer: Number = 2,
        vrf_cop: Number = 2.1,
        add_building_averages: bool = False,
        debug_ems: bool = False,
        hvac_zone_map: Optional[Dict[str, str]] = None,
        zone_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
        existing_hvac_operative_temperature_control: bool = True,
        existing_hvac_availability_schedule: Optional[str] = None,
        existing_hvac_widen_outdoor_temperature_limits: bool = False,
        existing_hvac_ideal_loads_backup: bool = False,
        existing_hvac_radiant_setpoints: bool = True,
        custom_outdoor_metric: Union[str, int] = 'pmot',
        custom_alpha: Number = 0.8,
        custom_days: int = 30,
        epw: Optional[Union[str, os.PathLike]] = None,
        heating_setpoint_minimum: Optional[Number] = None,
        cooling_setpoint_maximum: Optional[Number] = None,
        report_hours_below: Optional[Sequence[Number]] = None,
        custom_regimes: Optional[Sequence[CustomRegime]] = None,
        report_long_term_discomfort: bool = False,
        long_term_range: Optional[Sequence[Any]] = None,
        static_heating_setpoint: Number = STATIC_SETPOINT_DEFAULTS[0],
        static_cooling_setpoint: Number = STATIC_SETPOINT_DEFAULTS[1],
        drift_mode: Optional[str] = DRIFT_DEFAULTS['drift_mode'],
        max_drift_rate: Number = DRIFT_DEFAULTS['max_drift_rate'],
        alpha_indoor: Number = DRIFT_DEFAULTS['alpha_indoor'],
        delta_cool: Number = DRIFT_DEFAULTS['delta_cool'],
        delta_heat: Number = DRIFT_DEFAULTS['delta_heat'],
        initial_T_rm_in: Optional[Number] = DRIFT_DEFAULTS['initial_T_rm_in'],  # noqa: N803
    ):
        files = _input_files(idfs)
        print(BANNER)
        _warn_hvac_zone_map(hvac_zone_map)
        self.verbose = verbose
        checked_zone_arguments = check_zone_arguments(zone_arguments)
        epw = _check_outdoor_metric(custom_outdoor_metric, custom_alpha, custom_days, checked_zone_arguments, epw)
        has_limits = _check_setpoint_limits(heating_setpoint_minimum, cooling_setpoint_maximum, checked_zone_arguments)
        _check_static_setpoint_arguments(static_heating_setpoint, static_cooling_setpoint, checked_zone_arguments)
        drift = dict(drift_mode=drift_mode, max_drift_rate=max_drift_rate, alpha_indoor=alpha_indoor,
                     delta_cool=delta_cool, delta_heat=delta_heat, initial_T_rm_in=initial_T_rm_in)
        has_drift = _check_drift_arguments(drift, checked_zone_arguments)
        hours_below = check_hours_below(report_hours_below)
        regimes = check_custom_regimes(custom_regimes)
        (existing_hvac_operative_temperature_control, existing_hvac_widen_outdoor_temperature_limits,
         existing_hvac_ideal_loads_backup, existing_hvac_radiant_setpoints) = _check_existing_hvac_arguments(
            existing_hvac_operative_temperature_control, existing_hvac_availability_schedule,
            existing_hvac_widen_outdoor_temperature_limits, existing_hvac_ideal_loads_backup,
            existing_hvac_radiant_setpoints)

        if (script_type is None or output_type is None or output_frequencies is None or keep_existing_outputs is None
                or setpoint_type is None
                or (supply_air_temp_input_method is None and script_type not in ('ex_mm', 'ex_ac'))):
            asked = prompts.ask_model_arguments()
            script_type = asked['script_type']
            supply_air_temp_input_method = asked['supply_air_temp_input_method']
            keep_existing_outputs = asked['keep_existing_outputs']
            output_type = asked['output_type']
            output_frequencies = asked['output_frequencies']
            make_outputs_dataframe = asked['make_outputs_dataframe']
            energyplus_version = asked['energyplus_version']
            setpoint_type = asked['setpoint_type']
        energyplus_version = normalise_energyplus_version(energyplus_version)
        output_type, output_frequencies, setpoint_type = _check_model_arguments(
            script_type, supply_air_temp_input_method, output_type, output_frequencies, setpoint_type)
        if checked_zone_arguments and setpoint_type == 'pmv':
            raise ValueError("zone_arguments needs setpoint_type 'temperature': with 'pmv', the Fanger thermostats "
                             "control the zones and the arguments of the ACCIS are not used.")
        if has_limits and setpoint_type == 'pmv':
            raise ValueError("heating_setpoint_minimum and cooling_setpoint_maximum need setpoint_type 'temperature': "
                             "the Fanger thermostats of 'pmv' have setpoints of the PMV, not of the temperature.")
        if regimes and setpoint_type == 'pmv':
            raise ValueError("custom_regimes needs setpoint_type 'temperature': with 'pmv', the Fanger thermostats "
                             "control the zones and the custom model is not used.")
        if has_drift and setpoint_type == 'pmv':
            raise ValueError("drift_mode needs setpoint_type 'temperature': the Fanger thermostats of 'pmv' have "
                             "setpoints of the PMV, not of the temperature.")
        if regimes and uses_hvac_conditions(regimes) and not is_mixed_mode(script_type):
            raise ValueError("The conditions 'hvac_off' and 'hvac_on' of custom_regimes need mixed mode (script_type "
                             f"'vrf_mm' or 'ex_mm'), not {script_type!r}.")
        if epw is None and any(regime.outdoor_metric == 'monthly_mean' for regime in regimes):
            raise ValueError("The outdoor metric 'monthly_mean' of a regime of custom_regimes needs the weather file "
                             "of the simulations (argument epw), whose monthly means the EMS programs keep.")
        report_long_term_discomfort = _check_long_term_discomfort(report_long_term_discomfort, setpoint_type)
        long_term_range = _check_long_term_range(long_term_range, report_long_term_discomfort)
        if verbose:
            _print_model_arguments(script_type, supply_air_temp_input_method, output_type, output_frequencies,
                                   energyplus_version, setpoint_type)
        keep_existing_outputs = to_bool(keep_existing_outputs, 'keep_existing_outputs')
        # The outputs chosen with 'custom' are not known before
        make_outputs_dataframe = False if output_type == 'custom' else bool(make_outputs_dataframe)

        self.arguments = _Arguments(
            script_type=script_type,
            supply_air_temp_input_method=supply_air_temp_input_method,
            output_type=output_type,
            output_frequencies=output_frequencies,
            keep_existing_outputs=keep_existing_outputs,
            make_outputs_dataframe=make_outputs_dataframe,
            outputs_dataframe=outputs_dataframe,
            energyplus_version=energyplus_version,
            setpoint_type=setpoint_type,
        )
        self.input_idfs: Dict[str, Any] = {}
        self.occupied_zones: Dict[str, List[str]] = {}
        self.occupied_zones_original_name: Dict[str, List[str]] = {}
        self.windows_and_doors: Dict[str, List[str]] = {}
        self.windows_and_doors_original_name: Dict[str, List[str]] = {}
        self.zone_arguments: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.results_size = pd.DataFrame(columns=_RESULTS_SIZE_COLUMNS)

        models = []
        not_working = []
        dataframes = []
        found_zones = set()
        sizes: Dict[str, Optional[SimulationSize]] = {}
        for file in files:
            stem = file[:-len('.idf')]
            self._log(_START_MODEL, 'Starting with file:', stem)
            # eppy reads the file twice: the input model, which does not change, and the model with the ACCIS
            self.input_idfs[stem] = load_idf(file, energyplus_version)
            version = _idf_version(self.input_idfs[stem])
            _check_version(version)
            templates = hvac_template_types(self.input_idfs[stem])
            if templates:
                # The thermostats and HVAC objects of the HVACTemplate objects exist only once they are expanded
                with tempfile.TemporaryDirectory() as folder:
                    expanded = expand_objects(file, os.path.join(folder, 'expanded.idf'), version=version)
                    idf = load_idf(expanded, energyplus_version)
                self._log(f'The HVACTemplate objects of {stem} ({", ".join(templates)}) have been expanded with '
                          f'ExpandObjects: the output IDFs have the HVAC objects they stand for.')
            else:
                idf = load_idf(file, energyplus_version)
            self._log(f'IDD location is: {idf.iddname}')
            if self.arguments['energyplus_version'] == 'auto':
                self.arguments['energyplus_version'] = version
            model = AccimModel(idf, script_type, setpoint_type, verbose=verbose,
                               hvac_zone_map=hvac_zone_map, name=stem)
            self.occupied_zones[stem] = model.occupied_zones
            self.occupied_zones_original_name[stem] = model.occupied_zones_orig
            if model.is_mixed_mode:
                self.windows_and_doors[stem] = model.windows
                self.windows_and_doors_original_name[stem] = model.windows_orig
            names = zone_names(model.targets)
            aliases = {str(alias).upper() for zone_aliases in names.values() for alias in zone_aliases}
            found_zones.update(key for key in checked_zone_arguments if str(key).upper() in aliases)
            self.zone_arguments[stem] = resolve_zone_arguments(checked_zone_arguments, names, strict=False)
            if self.zone_arguments[stem]:
                self._log('The zones with their own arguments are:',
                          *(f'{zone}: {arguments}' for zone, arguments in self.zone_arguments[stem].items()))
            if model.not_working:
                not_working.append(stem)
                continue
            add_accis_objects(model, supply_air_temp_input_method,
                              vrf_availability_schedule=vrf_availability_schedule, vrf_eer=vrf_eer, vrf_cop=vrf_cop,
                              add_building_averages=add_building_averages, debug_ems=debug_ems,
                              existing_hvac_operative_temperature_control=existing_hvac_operative_temperature_control,
                              existing_hvac_availability_schedule=existing_hvac_availability_schedule,
                              existing_hvac_widen_outdoor_temperature_limits=(
                                  existing_hvac_widen_outdoor_temperature_limits),
                              existing_hvac_ideal_loads_backup=existing_hvac_ideal_loads_backup,
                              existing_hvac_radiant_setpoints=existing_hvac_radiant_setpoints)
            # The occupied hours below some temperatures, before the outputs (the standard outputs have them)
            set_hours_below_code(idf, hours_below)
            long_term_outputs = (sum(set_long_term_discomfort_code(idf, long_term_range=long_term_range).values(), [])
                                 if report_long_term_discomfort else [])
            add_outputs(model, output_type, output_frequencies, keep_existing_outputs, outputs_dataframe, file=stem)
            if hours_below and output_type == 'simplified':
                _add_hours_below_outputs(idf, output_frequencies)
            if long_term_outputs and output_type == 'simplified':
                _request_outputs(idf, long_term_outputs, output_frequencies)
            if make_outputs_dataframe:
                dataframes.append(output_variables_dataframe(idf, file=stem))
            enable_sizing_calculations(model)
            sizes[stem] = _estimate_results_size(idf, stem)
            # The text of the model (as eppy writes it) is kept instead of the model, which needs much more memory
            models.append((stem, idf.idfstr()))
            self._log('Ending with file:', stem, _END_MODEL)

        missing_zones = [key for key in checked_zone_arguments if key not in found_zones]
        if missing_zones:
            raise ValueError(f'The zones {missing_zones} of zone_arguments are not occupied zones of the input IDFs. '
                             f'Their occupied zones are {self.occupied_zones_original_name}.')
        if make_outputs_dataframe:
            self.df_outputs = (pd.concat(dataframes) if dataframes
                               else pd.DataFrame(columns=['file'] + OUTPUT_DATAFRAME_COLUMNS))
        self._log('The following IDFs will not work, so no output IDFs will be generated from them:',
                  *(not_working or ['None']))
        self._log(_START_OUTPUTS)

        generation = self._generation_arguments(
            script_type, comfort_standard=comfort_standard, category=category,
            category_cooling_offset=category_cooling_offset, category_heating_offset=category_heating_offset,
            comfort_mode=comfort_mode, setpoint_accuracy=setpoint_accuracy,
            custom_cooling_upper_limit=custom_cooling_upper_limit,
            custom_cooling_lower_limit=custom_cooling_lower_limit,
            custom_heating_upper_limit=custom_heating_upper_limit,
            custom_heating_lower_limit=custom_heating_lower_limit,
            custom_slope=custom_slope, custom_intercept=custom_intercept, custom_cooling_offset=custom_cooling_offset,
            custom_heating_offset=custom_heating_offset, cooling_season_start=cooling_season_start,
            cooling_season_end=cooling_season_end, hvac_mode=hvac_mode, ventilation_control=ventilation_control,
            opening_factor_max_temp_diff=opening_factor_max_temp_diff,
            opening_factor_min_temp_diff=opening_factor_min_temp_diff, min_opening_factor=min_opening_factor,
            ventilation_setpoint_offset=ventilation_setpoint_offset, min_outdoor_temp_offset=min_outdoor_temp_offset,
            max_wind_speed=max_wind_speed, setpoint_tolerance_start=setpoint_tolerance_start,
            setpoint_tolerance_end=setpoint_tolerance_end, setpoint_tolerance_step=setpoint_tolerance_step,
            name_suffix=name_suffix, custom_outdoor_metric=custom_outdoor_metric, custom_alpha=custom_alpha,
            custom_days=custom_days, heating_setpoint_minimum=heating_setpoint_minimum,
            cooling_setpoint_maximum=cooling_setpoint_maximum, static_heating_setpoint=static_heating_setpoint,
            static_cooling_setpoint=static_cooling_setpoint, **drift)
        self.arguments.update({k: v for k, v in vars(generation).items()})
        if has_drift:
            # The window of the limiter with the largest tolerance of the output IDFs (finding A9 of the self-audit of
            # 2026-11-11)
            _check_window_widths(drift, checked_zone_arguments,
                                 max((abs(value) for value in generation.tolerances()), default=0.0))
        self.arguments.update(verbose=verbose, confirm=confirm, zone_arguments=zone_arguments, epw=epw,
                              report_hours_below=hours_below or None, custom_regimes=list(regimes) or None,
                              report_long_term_discomfort=report_long_term_discomfort, long_term_range=long_term_range)
        if regimes and CUSTOM_COMFORT_STANDARD not in generation.comfort_standard and not any(
                arguments.get('comfort_standard') == CUSTOM_COMFORT_STANDARD
                for arguments in checked_zone_arguments.values()):
            raise ValueError(f'custom_regimes needs the custom model: comfort_standard {CUSTOM_COMFORT_STANDARD} in '
                             f'the output IDFs or in zone_arguments.')
        # Without the weather file, JPN Aqilah 2025 reads the RMOT of EnergyPlus (finding B4-1 of accim 1.2.0)
        if epw is None and setpoint_type == 'temperature' and (
                set(generation.comfort_standard) & set(WEATHER_FILE_METRICS)
                or any(arguments.get('comfort_standard') in WEATHER_FILE_METRICS
                       for arguments in checked_zone_arguments.values())):
            _warn_rmot_start('')

        paths = self._write_output_idfs(models, generation, setpoint_type, confirm, is_mixed_mode(script_type), sizes,
                                        epw, regimes)
        from eppy.modeleditor import IDF
        self.output_idfs = OutputIdfs(paths, IDF)
        self._log(_END_OUTPUTS)

    def _log(self, *lines) -> None:
        if self.verbose:
            print(*lines, sep='\n')

    @staticmethod
    def _generation_arguments(script_type: str, **kwargs) -> GenerationArguments:
        """The arguments of the output IDFs, asking them if some are missing."""
        name_suffix = kwargs.pop('name_suffix')
        # The prompts do not ask the outdoor metric of the custom model, nor the limits of the setpoints
        defaults = dict(_NOT_ASKED_ARGUMENTS)
        not_asked = {name: kwargs.pop(name, default) for name, default in defaults.items()}
        needed = ['comfort_standard', 'category', 'comfort_mode']
        if is_mixed_mode(script_type):
            needed += ['hvac_mode', 'ventilation_control']
        if any(kwargs[name] is None for name in needed):
            kwargs = prompts.ask_generation_arguments(script_type)
        if not is_mixed_mode(script_type):
            return GenerationArguments.air_conditioned(**kwargs, name_suffix=name_suffix, **not_asked)
        return GenerationArguments(**kwargs, name_suffix=name_suffix, **not_asked)

    def _check_zone_arguments(self, models, generation: GenerationArguments, combos, mixed_mode: bool) -> None:
        """Check that the zones of zone_arguments have setpoints in all the output IDFs."""
        errors = []
        for stem, _ in models:
            for zone, arguments in self.zone_arguments.get(stem, {}).items():
                for combination in combos:
                    reasons = zone_arguments_errors(zone_input_arguments(generation, combination, arguments),
                                                    mixed_mode)
                    if reasons:
                        errors.append(f'zone {zone} of {stem}, in {output_name(stem, combination)}: '
                                      f'{"; ".join(reasons)}')
        if errors:
            raise ValueError('The arguments of some zones of zone_arguments are not valid (give the comfort '
                             'standard, category and comfort mode of each of these zones):\n' + '\n'.join(errors))

    def _write_output_idfs(self, models, generation: GenerationArguments, setpoint_type: str, confirm,
                           mixed_mode: bool, sizes: Dict[str, Optional[SimulationSize]],
                           epw: Optional[str] = None, regimes: Sequence[CustomRegime] = ()) -> Dict[str, str]:
        """Write the output IDFs: for each combination, eppy saves the model with the arguments of the combination
        and the EMS code of the comfort standards of its zones only (and that of the outdoor metric of the custom
        model, which begins with the values of ``epw``, if a zone needs it, and that of the regimes of the custom
        model in its zones)."""
        from eppy.modeleditor import IDF

        combos = list(combinations(generation, setpoint_type))
        self._check_zone_arguments(models, generation, combos, mixed_mode)
        names = [output_name(stem, c, generation.name_suffix) for stem, _ in models for c in combos]
        self._log('The list of output IDFs is going to be:', *names,
                  f'And the total number of output IDFs is going to be {len(names)}')
        # Before the confirmation, so that other outputs can be chosen
        self.results_size = _results_size_table(sizes, len(combos))
        if combos and any(size is not None for size in sizes.values()):
            print(_results_size_message(sizes, len(combos)))
        paths: Dict[str, str] = {}
        if not _to_confirmation(confirm):
            self._log('IDF generation has been shut down')
            return paths
        self._log('Generating the following output IDF files:')
        for stem, text in models:
            idf = IDF(StringIO(text))
            # eppy has removed the indentation of the program lines when it has read them
            indent_programs(idf)
            for combination in combos:
                path = output_name(stem, combination, generation.name_suffix)
                self._log(path)
                set_combination(idf, generation, combination, self.zone_arguments.get(stem))
                set_setpoint_limits_code(idf)
                set_drift_limiter_code(idf, _ems_output_frequencies(idf))
                set_custom_regimes(idf, regimes)
                set_comfort_standard_code(idf, zone_comfort_standards(idf), epw)
                if has_setpoint_limits(idf):
                    warn_crossed_setpoint_limits(idf, epw)
                idf.savecopy(path)
                paths[os.path.basename(path)] = os.path.abspath(path)
        return paths


class addAccis(AddAccis):  # noqa: N801 (the name of accim 0.x)
    """Deprecated alias of :class:`AddAccis`, which also accepts the argument names of accim 0.x
    (``ScriptType``, ``Output_type``, ``ComfStand``...)."""

    def __init__(self, *args, **kwargs):
        warn_deprecated('accim.sim.accis.addAccis', 'accim.sim.accis.AddAccis')
        super().__init__(*args, **rename_legacy_kwargs(kwargs, LEGACY_ARGUMENT_NAMES, 'addAccis'))


# ----------------------------------------------------------------------------------------------------------
# IDF objects
# ----------------------------------------------------------------------------------------------------------

def add_accis_to_idf(
    idf,
    script_type: Optional[str] = None,
    supply_air_temp_input_method: Optional[str] = None,
    output_type: Optional[str] = None,
    output_frequencies: Optional[Sequence[str]] = None,
    keep_existing_outputs: Optional[bool] = None,
    outputs_dataframe: Optional[pd.DataFrame] = None,
    energyplus_version: Optional[str] = None,
    setpoint_type: Optional[str] = None,
    vrf_availability_schedule: str = 'On 24/7',
    verbose: bool = True,
    vrf_eer: Number = 2,
    vrf_cop: Number = 2.1,
    add_building_averages: bool = False,
    debug_ems: bool = False,
    hvac_zone_map: Optional[Dict[str, str]] = None,
    existing_hvac_operative_temperature_control: bool = True,
    existing_hvac_availability_schedule: Optional[str] = None,
    existing_hvac_widen_outdoor_temperature_limits: bool = False,
    existing_hvac_ideal_loads_backup: bool = False,
    existing_hvac_radiant_setpoints: bool = True,
    report_long_term_discomfort: bool = False,
    long_term_range: Optional[Sequence[Any]] = None,
) -> AccimModel:
    """Add the ACCIS to an IDF object of eppy or besos (in place).

    The arguments of the ACCIS (comfort standard, category, HVAC mode...) are those of :func:`modify_accis`
    (by default, ComfStand 1, CAT 1, ComfMod 2, HVACmode 2 and VentCtrl 0, in all the zones), which can change
    them later, also for each zone: the model has the EMS code of all the comfort standards. The arguments are those
    of :class:`AddAccis`. With the VRF systems (``script_type`` 'vrf_ac' and 'vrf_mm'), which are autosized, the zone,
    system and plant sizing calculations of the model are enabled, as :class:`AddAccis` does; with the existing HVAC
    systems, the sizing calculations do not change.

    :param idf: The IDF object.
    :param energyplus_version: The EnergyPlus version of the model; None or 'auto' to take that of its IDD.
    :param report_long_term_discomfort: True to report the long-term thermal discomfort of the occupied hours of each
        zone and of the building (see :class:`AddAccis`); False (the default) for none.
    :param long_term_range: With ``report_long_term_discomfort``, its range: None (the default) for the setpoints
        without the tolerance, or ``('en16798', category[, building_type])`` for the constant limits of EN 16798-1,
        Table B.2 (see :class:`AddAccis`).
    :return: The model, whose attributes give its occupied zones and windows.
    :raises ValueError: If an argument is missing or not valid.
    """
    if verbose:
        print(BANNER)
    _warn_hvac_zone_map(hvac_zone_map)
    (existing_hvac_operative_temperature_control, existing_hvac_widen_outdoor_temperature_limits,
     existing_hvac_ideal_loads_backup, existing_hvac_radiant_setpoints) = _check_existing_hvac_arguments(
        existing_hvac_operative_temperature_control, existing_hvac_availability_schedule,
        existing_hvac_widen_outdoor_temperature_limits, existing_hvac_ideal_loads_backup,
        existing_hvac_radiant_setpoints)
    if energyplus_version is None or str(energyplus_version).lower() == 'auto':
        energyplus_version = _idf_version(idf)
    output_type, output_frequencies, setpoint_type = _check_model_arguments(
        script_type, supply_air_temp_input_method, output_type, output_frequencies, setpoint_type)
    report_long_term_discomfort = _check_long_term_discomfort(report_long_term_discomfort, setpoint_type)
    long_term_range = _check_long_term_range(long_term_range, report_long_term_discomfort)
    if verbose:
        _print_model_arguments(script_type, supply_air_temp_input_method, output_type, output_frequencies,
                               energyplus_version, setpoint_type)
    check_choice('energyplus_version', energyplus_version, SUPPORTED_ENERGYPLUS_VERSIONS)
    keep_existing_outputs = bool(keep_existing_outputs) if not isinstance(keep_existing_outputs, str) \
        else to_bool(keep_existing_outputs, 'keep_existing_outputs')
    if verbose:
        print(_START_MODEL)
    model = AccimModel(idf, script_type, setpoint_type, verbose=verbose, hvac_zone_map=hvac_zone_map)
    add_accis_objects(model, supply_air_temp_input_method, vrf_availability_schedule=vrf_availability_schedule,
                      vrf_eer=vrf_eer, vrf_cop=vrf_cop, add_building_averages=add_building_averages,
                      debug_ems=debug_ems,
                      existing_hvac_operative_temperature_control=existing_hvac_operative_temperature_control,
                      existing_hvac_availability_schedule=existing_hvac_availability_schedule,
                      existing_hvac_widen_outdoor_temperature_limits=existing_hvac_widen_outdoor_temperature_limits,
                      existing_hvac_ideal_loads_backup=existing_hvac_ideal_loads_backup,
                      existing_hvac_radiant_setpoints=existing_hvac_radiant_setpoints)
    long_term_outputs = (sum(set_long_term_discomfort_code(idf, long_term_range=long_term_range).values(), [])
                         if report_long_term_discomfort else [])
    add_outputs(model, output_type, output_frequencies, keep_existing_outputs, outputs_dataframe)
    if long_term_outputs and output_type == 'simplified':
        _request_outputs(idf, long_term_outputs, output_frequencies)
    if script_type.startswith('vrf'):
        # EnergyPlus cannot run the VRF systems without sizing them (they are autosized). The existing HVAC systems
        # are the user's, so their sizing does not change (in accim 0.x, this function did not change it either)
        enable_sizing_calculations(model)
    if verbose:
        print(_END_MODEL)
    return model


def gen_outputs_df(
    idf,
    script_type: Optional[str] = None,
    output_type: Optional[str] = None,
    output_frequencies: Optional[Sequence[str]] = None,
    keep_existing_outputs: Optional[bool] = None,
    setpoint_type: Optional[str] = None,
    add_building_averages: bool = False,
    verbose: bool = False,
) -> pd.DataFrame:
    """Add the ACCIS to an IDF object (in place, see :func:`add_accis_to_idf`) and return a DataFrame with its
    Output:Variable objects, which can be filtered and given as ``outputs_dataframe``."""
    add_accis_to_idf(idf, script_type=script_type, output_type=output_type, output_frequencies=output_frequencies,
                     keep_existing_outputs=keep_existing_outputs, setpoint_type=setpoint_type,
                     add_building_averages=add_building_averages,
                     supply_air_temp_input_method='temperature difference', verbose=verbose)
    return output_variables_dataframe(idf)


def _programs(idf) -> Dict[str, Any]:
    return {p.Name: p for p in idf.idfobjects['EnergyManagementSystem:Program']}


@accepts_legacy_kwargs(DEPRECATED_ARGUMENT_NAMES, version='1.2.0')
def modify_accis(
    idf,
    comfort_standard: Optional[int] = None,
    category: Optional[Number] = None,
    category_cooling_offset: Number = 0,
    category_heating_offset: Number = 0,
    comfort_mode: Optional[Number] = None,
    setpoint_accuracy: Number = 10000,
    custom_cooling_upper_limit: Number = 0,
    custom_cooling_lower_limit: Number = 0,
    custom_heating_upper_limit: Number = 0,
    custom_heating_lower_limit: Number = 0,
    custom_slope: Number = 0,
    custom_intercept: Number = 0,
    custom_cooling_offset: Number = 0,
    custom_heating_offset: Number = 0,
    cooling_season_start: Union[int, str] = 121,
    cooling_season_end: Union[int, str] = 274,
    hvac_mode: Optional[int] = None,
    ventilation_control: Optional[int] = None,
    opening_factor_max_temp_diff: Number = 6,
    opening_factor_min_temp_diff: Number = 1,
    min_opening_factor: Number = 0.25,
    ventilation_setpoint_offset: Number = 0,
    min_outdoor_temp_offset: Number = 50,
    max_wind_speed: Number = 50,
    setpoint_tolerance: Number = 0.1,
    zone_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    custom_outdoor_metric: Optional[Union[str, int]] = None,
    custom_alpha: Optional[Number] = None,
    custom_days: Optional[int] = None,
    epw: Optional[Union[str, os.PathLike]] = None,
    heating_setpoint_minimum: Optional[Number] = None,
    cooling_setpoint_maximum: Optional[Number] = None,
    custom_regimes: Optional[Sequence[CustomRegime]] = None,
    static_heating_setpoint: Optional[Number] = None,
    static_cooling_setpoint: Optional[Number] = None,
    drift_mode: Optional[str] = None,
    max_drift_rate: Optional[Number] = None,
    alpha_indoor: Optional[Number] = None,
    delta_cool: Optional[Number] = None,
    delta_heat: Optional[Number] = None,
    initial_T_rm_in: Optional[Number] = None,  # noqa: N803
) -> None:
    """Set the arguments of the ACCIS of an IDF object (one value of each argument of :class:`AddAccis`), in all
    its occupied zones or, with ``zone_arguments``, in some of them.

    Each zone has its arguments in the EMS program SetInputData_<zone>. The comfort standard, category, comfort
    mode, HVAC mode and ventilation control that are None keep their values. The setpoints are set in each timestep
    by the subprograms of the comfort standard (SetAST_Master), so these arguments can also be changed later in
    the programs SetInputData_<zone>, except the comfort standard in the output IDFs of :class:`AddAccis`, which only
    have the EMS code of the comfort standards of their zones: this function adds that of the comfort standards that
    it sets (the models of :func:`add_accis_to_idf` have that of all of them). The lines of the EMS programs of the
    model are indented inside the blocks IF and WHILE.

    The outdoor metric of the custom model (``custom_outdoor_metric``, ``custom_alpha`` and ``custom_days``, see
    :class:`AddAccis`) keeps its value if it is None (the models without its EMS code have 'pmot'). If one of them (or
    ``epw``) is given, here or in ``zone_arguments``, the model gets the EMS code of the outdoor metric if it has the
    code of the custom model and a zone has a metric other than 'pmot' (and loses it otherwise), and its programs are
    written again: with ``epw``, they begin with the values of the weather file; without it, with the running mean of
    ASHRAE 55 of EnergyPlus (:func:`accim.sim.ems.outdoor_metric.set_outdoor_metric_code`). The zones of JPN Aqilah
    2025 (comfort standard 23) use the running mean of EN 16798-1 with α = 0.8 that the EMS calculates if ``epw`` is
    given or the programs of the outdoor metric of the model begin with the values of a weather file, and the RMOT of
    EnergyPlus otherwise (with a warning if this call gives them comfort standard 23; see :class:`AddAccis`).

    The models of earlier versions of accim, which have one program SetInputData for all the zones, can only have
    the same arguments in all the zones, and they get the subprograms of this version where they behave
    differently (those of ESP CTE and INT ISO7730 set the setpoints whatever the comfort mode is). Their custom model
    only has the outdoor metric 'pmot', and their setpoints have neither minimum nor maximum.

    The minimum heating setpoint and the maximum cooling setpoint (``heating_setpoint_minimum`` and
    ``cooling_setpoint_maximum``, see :class:`AddAccis`) keep their values if they are None (the models without them
    have none): a number, here or in ``zone_arguments``, gives it to the zones, with the program
    ApplySetpointLimits_<zone> (:func:`accim.sim.ems.setpoint_limits.set_setpoint_limits_code`). They bound the
    setpoint temperatures of the ACCIS, with and without the tolerance: the zones controlled by the thermostats of the
    PMV (``setpoint_type`` 'pmv', or :mod:`accim.sim.pmv_index`) do not use them. A model with them, given ``epw``,
    warns of the zones whose minimum is at or above the cooling setpoint of their comfort model, or whose maximum is at
    or below its heating setpoint, in some timestep of its run period
    (:func:`accim.sim.ems.setpoint_limits.warn_crossed_setpoint_limits`); without ``epw``, it does not warn.

    The static setpoints of JPN Aqilah 2025 (``static_heating_setpoint`` and ``static_cooling_setpoint``, see
    :class:`AddAccis`) keep their values if they are None: a number, here or in ``zone_arguments``, gives it to the
    zones whose comfort standard is JPN Aqilah 2025 once the arguments are set (the zones that get that comfort
    standard without them have the defaults, 20 and 28 °C); the other comfort standards ignore them
    (:mod:`accim.sim.ems.static_setpoints`).

    The limiter of the drift of the setpoints (``drift_mode``, ``max_drift_rate``, ``alpha_indoor``, ``delta_cool``,
    ``delta_heat`` and ``initial_T_rm_in``, see :class:`AddAccis` and :mod:`accim.sim.ems.drift_limiter`) keeps its
    arguments if they are None (the models without it have none): ``drift_mode``, here or in ``zone_arguments``, gives
    it to the zones (with the arguments given, those that they have, or the defaults), with the program
    ApplyDriftLimiter_<zone>, and the other arguments change those of the zones that have it (the other zones ignore
    them; a ValueError if no zone has it). It cannot be removed.

    The regimes of the custom model (``custom_regimes``, see :class:`AddAccis`) are kept if it is None: a list gives
    them to the zones whose comfort standard is the custom model (99) once the arguments are set, and removes them
    from the other zones (:func:`accim.sim.ems.custom_regimes.set_custom_regimes`); an empty list removes them from
    all the zones. The zones whose comfort standard changes keep their regimes otherwise, which only the custom model
    uses, unless a regime has its own outdoor metric, which would replace the outdoor metric of the zone (Tout_metric)
    that other comfort standards read: then they are removed. The zones of the comfort standards of the registry with
    regimes (:mod:`accim.sim.standards`) get those of their comfort standard, and lose them when they get another one
    (:func:`accim.sim.ems.custom_regimes.set_standard_regimes`).

    :param setpoint_tolerance: The tolerance of the setpoints.
    :param zone_arguments: The arguments of some zones, which replace those of the call in these zones:
        ``{zone: {argument: value}}``, for instance
        ``{'Block1:Zone1': {'comfort_standard': 2, 'category': 80, 'comfort_mode': 3}}`` (see :class:`AddAccis`). An
        argument that is None in the call and is not given for a zone keeps its value in the zone.
    :param custom_outdoor_metric: The outdoor metric of the custom model (see :class:`AddAccis`), or None to keep it.
    :param custom_alpha: The alpha of 'rmot_alpha', or None to keep it.
    :param custom_days: The days of 'ndrm', or None to keep them.
    :param epw: The weather file with which the outdoor metric of the custom model, and that of JPN Aqilah 2025, begin
        (see :class:`AddAccis`).
    :param heating_setpoint_minimum: The minimum heating setpoint (°C), or None to keep it.
    :param cooling_setpoint_maximum: The maximum cooling setpoint (°C), or None to keep it.
    :param custom_regimes: The regimes of the custom model (see :class:`AddAccis`), or None to keep them; an empty
        list removes them.
    :param static_heating_setpoint: The static heating setpoint of JPN Aqilah 2025 (°C), or None to keep it.
    :param static_cooling_setpoint: The static cooling setpoint of JPN Aqilah 2025 (°C), or None to keep it.
    :param drift_mode: The limiter of the drift of the setpoints, 'rate' or 'window', or None to keep it.
    :param max_drift_rate: 'rate': the largest change of the setpoints from one day to the next (K/day), or None to
        keep it.
    :param alpha_indoor: 'window': the weight of the running mean of the day before, or None to keep it.
    :param delta_cool: 'window': the largest distance of the setpoints above T_rm_in (K), or None to keep it.
    :param delta_heat: 'window': the largest distance of the setpoints below T_rm_in (K), or None to keep it.
    :param initial_T_rm_in: 'window': the first T_rm_in (°C), or None to keep it.
    :raises ValueError: If the model has no ACCIS, setpoint_accuracy is negative, zone_arguments is not valid (or
        is given for a model of an earlier version of accim), an argument of the outdoor metric is not valid (or is
        not 'pmot' in a model of an earlier version of accim), 'monthly_mean' has no weather file, a minimum or a
        maximum is not valid (or is given for a model of an earlier version of accim), the static setpoints of a zone
        of JPN Aqilah 2025 are not valid, the regimes are not valid (or no zone has the custom model, or a condition
        'hvac_off' or 'hvac_on' is given without mixed mode, or for a model of an earlier version of accim), or the
        arguments of the limiter of the drift are not valid (or no zone has or gets it, or they are given for a model
        of an earlier version of accim).
    """
    arguments = dict(
        comfort_standard=comfort_standard, category=category, category_cooling_offset=category_cooling_offset,
        category_heating_offset=category_heating_offset, comfort_mode=comfort_mode,
        setpoint_accuracy=setpoint_accuracy, custom_cooling_upper_limit=custom_cooling_upper_limit,
        custom_cooling_lower_limit=custom_cooling_lower_limit, custom_heating_upper_limit=custom_heating_upper_limit,
        custom_heating_lower_limit=custom_heating_lower_limit, custom_slope=custom_slope,
        custom_intercept=custom_intercept, custom_cooling_offset=custom_cooling_offset,
        custom_heating_offset=custom_heating_offset, cooling_season_start=cooling_season_start,
        cooling_season_end=cooling_season_end, hvac_mode=hvac_mode, ventilation_control=ventilation_control,
        opening_factor_max_temp_diff=opening_factor_max_temp_diff,
        opening_factor_min_temp_diff=opening_factor_min_temp_diff, min_opening_factor=min_opening_factor,
        ventilation_setpoint_offset=ventilation_setpoint_offset, min_outdoor_temp_offset=min_outdoor_temp_offset,
        max_wind_speed=max_wind_speed, setpoint_tolerance=setpoint_tolerance,
    )
    programs = _programs(idf)
    zone_programs = input_programs(idf)
    outdoor_metric = {name: value for name, value in zip(_OUTDOOR_METRIC_ARGUMENTS,
                                                         (custom_outdoor_metric, custom_alpha, custom_days))
                      if value is not None}
    limits = {name: value for name, value in zip(_SETPOINT_LIMIT_ARGUMENTS,
                                                 (heating_setpoint_minimum, cooling_setpoint_maximum))
              if value is not None}
    statics = {name: value for name, value in zip(STATIC_SETPOINT_ARGUMENTS,
                                                  (static_heating_setpoint, static_cooling_setpoint))
               if value is not None}
    regimes = None if custom_regimes is None else check_custom_regimes(custom_regimes)
    drift = {name: value for name, value in zip(DRIFT_ARGUMENTS, (drift_mode, max_drift_rate, alpha_indoor, delta_cool,
                                                                  delta_heat, initial_T_rm_in))
             if value is not None}
    if not zone_programs:
        if drift:
            raise ValueError('The model has the ACCIS of an earlier version of accim, which has no limiter of the '
                             'drift of the setpoints. Add the ACCIS with this version of accim to the model without '
                             'it.')
        if zone_arguments and 'SetInputData' in programs:
            raise ValueError('The model has the ACCIS of an earlier version of accim, whose arguments are the same in '
                             'all the zones (program SetInputData). To give the arguments of each zone, add the ACCIS '
                             'with this version of accim to the model without it.')
        if custom_outdoor_metric is not None and metric_code(custom_outdoor_metric) != 0:
            raise ValueError('The model has the ACCIS of an earlier version of accim, whose custom model only has the '
                             "outdoor metric 'pmot'. To use another one, add the ACCIS with this version of accim to "
                             'the model without it.')
        if limits:
            raise ValueError('The model has the ACCIS of an earlier version of accim, whose setpoints have neither '
                             'minimum nor maximum. To give them, add the ACCIS with this version of accim to the model '
                             'without it.')
        if regimes:
            raise ValueError('The model has the ACCIS of an earlier version of accim, whose custom model has one '
                             'regime. To give several, add the ACCIS with this version of accim to the model without '
                             'it.')
        if comfort_standard is not None and definition_of(comfort_standard) is not None:
            raise ValueError(f'The model has the ACCIS of an earlier version of accim, which does not have the EMS '
                             f'code of the comfort standard {comfort_standard} (JPN Aqilah 2025, and those defined by '
                             f'their data, are new in accim 1.2.0). To use it, add the ACCIS with this version of '
                             f'accim to the model without it.')
        _modify_accis_of_earlier_versions(idf, programs, **arguments)
        indent_programs(idf)
        return
    missing = [n for n in ('SetAST', 'ApplyCAT', 'SetComfTemp', 'SetAppLimits') if n not in programs]
    if missing:
        raise ValueError(f'The model has no EMS programs {missing}. Add the ACCIS first with add_accis_to_idf().')
    if setpoint_accuracy < 0:
        raise ValueError('The value for setpoint_accuracy cannot be less than 0.')
    zones = check_zone_arguments(zone_arguments)
    resolved: Dict[str, Dict[str, Any]] = {}
    if zones:
        resolved = resolve_zone_arguments(zones, zone_names(resolve_targets(idf), list(zone_programs)))
    metric_given = (bool(outdoor_metric) or epw is not None
                    or any(name in own for own in resolved.values() for name in _OUTDOOR_METRIC_ARGUMENTS))
    if metric_given:
        epw = _check_zone_outdoor_metrics(zone_programs, outdoor_metric, resolved, epw)
    limits_given = bool(limits) or any(name in own for own in resolved.values() for name in _SETPOINT_LIMIT_ARGUMENTS)
    if limits_given:
        _check_zone_setpoint_limits(zone_programs, limits, resolved)
    _check_zone_static_setpoints(zone_programs, statics, comfort_standard, resolved)
    if regimes:
        _check_zone_custom_regimes(idf, zone_programs, regimes, comfort_standard, resolved)
    drift_given = bool(drift) or any(name in own for own in resolved.values() for name in DRIFT_ARGUMENTS)
    if drift_given:
        _check_drift_arguments(drift, resolved)
        if not any('DriftMode' in read_inputs(program) or {**drift, **resolved.get(zone, {})}.get('drift_mode')
                   for zone, program in zone_programs.items()):
            raise ValueError('The arguments of the limiter of the drift of the setpoints need drift_mode: no zone has '
                             'the limiter, nor gets it in this call.')
    # The window of the limiter of each zone with it, after this call, against its tolerance of the setpoints (finding
    # A9 of the self-audit of 2026-11-11), before anything changes
    for zone, program in zone_programs.items():
        current = read_inputs(program)
        own = {**drift, **{name: value for name, value in resolved.get(zone, {}).items() if name in DRIFT_ARGUMENTS}}
        mode = own.get('drift_mode')
        if (mode == 'window') if mode is not None else current.get('DriftMode') == DRIFT_MODES['window']:
            check_window_width(own.get('delta_heat', current.get('DeltaHeat', DRIFT_DEFAULTS['delta_heat'])),
                               own.get('delta_cool', current.get('DeltaCool', DRIFT_DEFAULTS['delta_cool'])),
                               resolved.get(zone, {}).get('setpoint_tolerance', setpoint_tolerance), where=zone)
    # The comfort standard of each zone before the changes: the zones that leave a comfort standard with regimes lose
    # them (accim.sim.ems.custom_regimes.set_standard_regimes)
    previous = {zone: read_inputs(program).get('ComfStand') for zone, program in zone_programs.items()}
    for zone, program in zone_programs.items():
        current = read_inputs(program)
        values = input_values({**arguments, **outdoor_metric, **limits, **statics, **resolved.get(zone, {})})
        # The limiter of the drift: its arguments given, or those of the zone (accim.sim.ems.drift_limiter)
        values = {name: value for name, value in values.items() if name not in DRIFT_INPUTS}
        values.update(drift_inputs({name: value for name, value in {**drift, **resolved.get(zone, {})}.items()
                                    if name in DRIFT_ARGUMENTS}, current))
        # The zones that keep a comfort standard defined by its data keep its outdoor metric (accim.sim.standards)
        definition = comfort_standard_definition(current.get('ComfStand')) if 'ComfStand' not in values else None
        if definition is not None:
            values.update(standard_inputs(definition))
        not_set = set_inputs(program, values)
        # The inputs of the outdoor metric of the models without its EMS code, and the minimum and maximum of the
        # setpoints of the zones without them
        new_lines = [f'set {name} = {values[name]}' for name in not_set
                     if name in OUTDOOR_METRIC_INPUTS or name in SETPOINT_LIMIT_INPUTS or name in DRIFT_INPUTS]
        # The static setpoints of the zones of JPN Aqilah 2025 without them (those given, or the defaults)
        if has_static_setpoints(values.get('ComfStand', current.get('ComfStand'))):
            new_lines += [f'set {name} = {values.get(name, default)}'
                          for name, default in zip(STATIC_SETPOINT_INPUTS, STATIC_SETPOINT_DEFAULTS)
                          if name not in current]
        if new_lines:
            set_program_lines(program, [str(line).strip() for line in program.fieldvalues[2:]] + new_lines)
    if limits_given:
        set_setpoint_limits_code(idf)
    if drift_given:
        set_drift_limiter_code(idf, _ems_output_frequencies(idf))
    regimes_changed = False
    if regimes is not None:
        set_custom_regimes(idf, regimes)
    else:
        # The regimes of the comfort standards of the registry with regimes (task H5 of the review of accim 1.2.0)
        regimes_changed = set_standard_regimes(idf, previous)
    add_comfort_standard_code(idf, zone_comfort_standards(idf), epw)
    # The comfort standards defined by their data whose outdoor metric the EMS calculates (or with regimes) need its
    # EMS code, and the zones of JPN Aqilah 2025 that of the outdoor metric of the weather file (finding B4-1 of accim
    # 1.2.0)
    registered_metric = bool({int(n) for n in zone_comfort_standards(idf)} & outdoor_metric_standards())
    weather_zones = weather_file_zones(idf)
    # The regimes can have their own outdoor metric (task H5 of the review of accim 1.2.0)
    if metric_given or registered_metric or weather_zones or regimes is not None or regimes_changed:
        enabled = outdoor_metric_needed(idf, code_comfort_standards(idf), epw)
        set_outdoor_metric_code(idf, enabled, epw, rewrite=metric_given)
    given = {comfort_standard, *(own.get('comfort_standard') for own in resolved.values())}
    if given & set(WEATHER_FILE_METRICS) and weather_zones and not begins_with_weather_file(idf):
        _warn_rmot_start('')
    if has_setpoint_limits(idf):
        warn_crossed_setpoint_limits(idf, epw)
    indent_programs(idf)


def _check_zone_static_setpoints(zone_programs: Dict[str, Any], statics: Dict[str, Any],
                                 comfort_standard: Optional[int], zone_arguments: Dict[str, Dict[str, Any]]) -> None:
    """Check the static setpoints that each zone of JPN Aqilah 2025 gets in :func:`modify_accis` (those of the call,
    those of ``zone_arguments``, those it has or the defaults), once the comfort standards are set; the numbers given
    for the other zones are only checked to be numbers, since these zones ignore them."""
    for name, value in statics.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'{name} must be a number (°C), not {value!r}.')
    for zone, program in zone_programs.items():
        current = read_inputs(program)
        own = zone_arguments.get(zone, {})
        standard = own.get('comfort_standard', current.get('ComfStand') if comfort_standard is None
                           else comfort_standard)
        if has_static_setpoints(standard):
            values = [own.get(name, statics.get(name, current.get(variable, default)))
                      for name, variable, default in zip(STATIC_SETPOINT_ARGUMENTS, STATIC_SETPOINT_INPUTS,
                                                         STATIC_SETPOINT_DEFAULTS)]
            check_static_setpoints(*values, where=zone)


def _check_zone_custom_regimes(idf, zone_programs: Dict[str, Any], regimes: Sequence[CustomRegime],
                               comfort_standard: Optional[int], zone_arguments: Dict[str, Dict[str, Any]]) -> None:
    """Check that some zone has the custom model once :func:`modify_accis` has set the comfort standards (that of the
    call, those of ``zone_arguments`` or those that the zones have), and that the zones of the custom model are in
    mixed mode if a regime has the condition 'hvac_off' or 'hvac_on', before changing the model."""
    from accim.sim.ems.custom_regimes import hvac_off_lines

    custom = [zone for zone, program in zone_programs.items()
              if zone_arguments.get(zone, {}).get(
                  'comfort_standard', read_inputs(program).get('ComfStand') if comfort_standard is None
                  else comfort_standard) == CUSTOM_COMFORT_STANDARD]
    if not custom:
        raise ValueError(f'custom_regimes needs the custom model: no zone has comfort_standard '
                         f'{CUSTOM_COMFORT_STANDARD} (give it in the same call).')
    if uses_hvac_conditions(regimes) and any(hvac_off_lines(idf, zone) is None for zone in custom):
        raise ValueError("The conditions 'hvac_off' and 'hvac_on' of custom_regimes need mixed mode (script_type "
                         "'vrf_mm' or 'ex_mm').")


def _check_zone_setpoint_limits(zone_programs: Dict[str, Any], limits: Dict[str, Any],
                                zone_arguments: Dict[str, Dict[str, Any]]) -> None:
    """Check the minimum and maximum of the setpoints that each zone gets in :func:`modify_accis` (those of the call,
    those of ``zone_arguments`` or those it has)."""
    for zone, program in zone_programs.items():
        current = read_inputs(program)
        own = zone_arguments.get(zone, {})
        values = [own.get(name, limits.get(name, current.get(variable)))
                  for name, variable in zip(_SETPOINT_LIMIT_ARGUMENTS, SETPOINT_LIMIT_INPUTS)]
        check_setpoint_limits(*values, where=zone)


def _check_zone_outdoor_metrics(zone_programs: Dict[str, Any], outdoor_metric: Dict[str, Any],
                                zone_arguments: Dict[str, Dict[str, Any]],
                                epw: Optional[Union[str, os.PathLike]]) -> Optional[str]:
    """Check the outdoor metric of the custom model that each zone gets in :func:`modify_accis` (that of the call,
    that of ``zone_arguments`` or the one it has), with the warnings of decision D7, and the weather file; return its
    path."""
    defaults = dict(zip(_OUTDOOR_METRIC_ARGUMENTS, (0, 0.8, 30)))
    checked = set()
    codes = set()
    for zone, program in zone_programs.items():
        current = read_inputs(program)
        own = zone_arguments.get(zone, {})
        values = [own.get(name, outdoor_metric.get(name, current.get(variable, defaults[name])))
                  for name, variable in zip(_OUTDOOR_METRIC_ARGUMENTS, OUTDOOR_METRIC_INPUTS)]
        where = zone if any(name in own for name in _OUTDOOR_METRIC_ARGUMENTS) else ''
        key = (*[str(value) for value in values], where)
        if key not in checked:
            checked.add(key)
            codes.add(check_outdoor_metric_arguments(*values, where=where))
    if epw is not None:
        if not os.path.isfile(epw):
            raise ValueError(f'epw must be the path of a weather file (EPW), not {epw!r}.')
        return os.path.abspath(epw)
    if OUTDOOR_METRICS['monthly_mean'] in codes:
        raise ValueError("custom_outdoor_metric 'monthly_mean' needs the weather file of the simulations (argument "
                         "epw), whose monthly means the EMS programs keep.")
    return None


def _modify_accis_of_earlier_versions(
    idf, programs: Dict[str, Any], comfort_standard, category, category_cooling_offset, category_heating_offset,
    comfort_mode, setpoint_accuracy, custom_cooling_upper_limit, custom_cooling_lower_limit,
    custom_heating_upper_limit, custom_heating_lower_limit, custom_slope, custom_intercept, custom_cooling_offset,
    custom_heating_offset, cooling_season_start, cooling_season_end, hvac_mode, ventilation_control,
    opening_factor_max_temp_diff, opening_factor_min_temp_diff, min_opening_factor, ventilation_setpoint_offset,
    min_outdoor_temp_offset, max_wind_speed, setpoint_tolerance,
) -> None:
    """:func:`modify_accis` for the models of earlier versions of accim, which have one program SetInputData for all
    the zones, and the other arguments in SetAST, ApplyCAT, SetAppLimits and SetVOFinputData."""
    missing = [n for n in ('SetInputData', 'SetAST', 'ApplyCAT', 'SetComfTemp', 'SetAppLimits') if n not in programs]
    if missing:
        raise ValueError(f'The model has no EMS programs {missing}. Add the ACCIS first with add_accis_to_idf().')
    if setpoint_accuracy < 0:
        raise ValueError('The value for setpoint_accuracy cannot be less than 0.')
    start = to_day_of_year(cooling_season_start, 'cooling_season_start')
    end = to_day_of_year(cooling_season_end, 'cooling_season_end')

    input_data = [('ComfStand', comfort_standard), ('CAT', category), ('ComfMod', comfort_mode),
                  ('HVACmode', hvac_mode), ('VentCtrl', ventilation_control),
                  ('VSToffset', ventilation_setpoint_offset), ('MinOToffset', min_outdoor_temp_offset),
                  ('MaxWindSpeed', max_wind_speed), ('ACSTtol', -setpoint_tolerance), ('AHSTtol', setpoint_tolerance),
                  ('CoolSeasonStart', start), ('CoolSeasonEnd', end)]
    for number, (name, value) in enumerate(input_data, start=1):
        if value is not None:
            setattr(programs['SetInputData'], f'Program_Line_{number}', f'set {name} = {value}')

    programs['SetComfTemp'].Program_Line_2 = f'set ComfTemp = PMOT*{custom_slope}+{custom_intercept}'
    app_limits = programs['SetAppLimits']
    app_limits.Program_Line_2 = f'set ACSTaul = {custom_cooling_upper_limit}'
    app_limits.Program_Line_3 = f'set ACSTall = {custom_cooling_lower_limit}'
    app_limits.Program_Line_4 = f'set AHSTaul = {custom_heating_upper_limit}'
    app_limits.Program_Line_5 = f'set AHSTall = {custom_heating_lower_limit}'
    set_program_lines(programs['SetAST'], [f'set SetpointAcc = {setpoint_accuracy}', f'set m = {custom_slope}',
                                           f'set n = {custom_intercept}', 'run SetAST_Master'])
    # The models of accim before 0.8 have no SetAST_Master
    if 'SetAST_Master' not in programs:
        add_program(idf, 'SetAST_Master', master_program_lines())
        for name, lines in subprograms().items():
            if name not in programs:
                add_program(idf, name, lines)
    else:
        # The models of accim before 1.0 only set the setpoints of ESP CTE and INT ISO7730 if ComfMod is 0
        static = [cs for cs in MODULAR_COMFORT_MODES if not depends_on_comfort_mode(cs)]
        for name, lines in subprograms(static).items():
            if name in programs:
                set_program_lines(programs[name], lines)
    if 'SetVOFinputData' in programs:
        vof_input_data = programs['SetVOFinputData']
        vof_input_data.Program_Line_1 = f'set MaxTempDiffVOF = {opening_factor_max_temp_diff}'
        vof_input_data.Program_Line_2 = f'set MinTempDiffVOF = {opening_factor_min_temp_diff}'
        vof_input_data.Program_Line_3 = f'set MultiplierVOF = {min_opening_factor}'
    apply_cat = programs['ApplyCAT']
    apply_cat.Program_Line_1 = f'set CATcoolOffset = {category_cooling_offset}'
    apply_cat.Program_Line_2 = f'set CATheatOffset = {category_heating_offset}'
    apply_cat.Program_Line_4 = f'set ACSToffset = {custom_cooling_offset} + {category_cooling_offset}'
    apply_cat.Program_Line_5 = f'set AHSToffset = {custom_heating_offset} + {category_heating_offset}'
