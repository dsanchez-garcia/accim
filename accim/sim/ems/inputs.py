# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The inputs of the ACCIS: the arguments of each zone, which its EMS program ``SetInputData_<zone>`` sets.

Each occupied zone has a program ``SetInputData_<zone>`` with all the arguments of the ACCIS (comfort
standard, category, comfort mode, HVAC mode, tolerances, custom comfort model, venting opening factor...), so
the zones can have different arguments. The program ``RunACCIS_<zone>`` of each zone runs it, and then the
programs that calculate and apply the setpoints (see :mod:`accim.sim.ems.programs`).

The EMS variables keep the names of accim 0.x (``ComfStand``, ``CAT``...); :data:`INPUT_VARIABLES` gives the
argument of :func:`accim.sim.accis.modify_accis` that sets each one.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Union

from accim.sim.arguments import LEGACY_ARGUMENT_NAMES, to_day_of_year

__all__ = [
    'INPUT_PROGRAM_PREFIX',
    'INPUT_VARIABLES',
    'InputVariable',
    'RUN_PROGRAM_PREFIX',
    'ZONE_ARGUMENTS',
    'check_zone_arguments',
    'input_lines',
    'input_programs',
    'input_values',
    'read_inputs',
    'resolve_zone_arguments',
    'set_inputs',
    'zone_comfort_standards',
    'zone_names',
]

Number = Union[int, float]

#: The name of the program with the inputs of a zone is this prefix and the name of the zone in the EMS objects.
INPUT_PROGRAM_PREFIX = 'SetInputData_'
#: The name of the program that runs the ACCIS of a zone (the only one with a calling manager).
RUN_PROGRAM_PREFIX = 'RunACCIS_'


@dataclass(frozen=True)
class InputVariable:
    """An input of the ACCIS.

    :ivar variable: The name of the EMS variable.
    :ivar argument: The argument of :func:`accim.sim.accis.modify_accis` (and of the zones in ``zone_arguments``)
        that sets it.
    :ivar default: Its value in the models of :func:`accim.sim.accis.add_accis_to_idf`.
    :ivar mixed_mode_only: True for the inputs of the venting opening factor, which only the models in mixed mode
        have.
    :ivar outdoor_metric_only: True for the inputs of the outdoor metric of the custom model, which only the models
        with the EMS code of the custom model have (:mod:`accim.sim.ems.outdoor_metric`).
    :ivar optional: True for the inputs that SetInputData_<zone> only has if they are given (the floor of the heating
        setpoint and the ceiling of the cooling setpoint, :mod:`accim.sim.ems.setpoint_limits`); their default is None.
    """

    variable: str
    argument: str
    default: Optional[Number]
    mixed_mode_only: bool = False
    outdoor_metric_only: bool = False
    optional: bool = False


#: The inputs, in the order of the lines of SetInputData_<zone>. The first 12 are those of the program SetInputData
#: of accim 0.x, in the same order; the others were in SetAST, ApplyCAT, SetAppLimits and SetVOFinputData.
INPUT_VARIABLES = (
    InputVariable('ComfStand', 'comfort_standard', 1),
    InputVariable('CAT', 'category', 1),
    InputVariable('ComfMod', 'comfort_mode', 2),
    InputVariable('HVACmode', 'hvac_mode', 2),
    InputVariable('VentCtrl', 'ventilation_control', 0),
    InputVariable('VSToffset', 'ventilation_setpoint_offset', 0),
    InputVariable('MinOToffset', 'min_outdoor_temp_offset', 7),
    InputVariable('MaxWindSpeed', 'max_wind_speed', 6),
    InputVariable('ACSTtol', 'setpoint_tolerance', -0.25),
    InputVariable('AHSTtol', 'setpoint_tolerance', 0.25),
    InputVariable('CoolSeasonStart', 'cooling_season_start', 121),
    InputVariable('CoolSeasonEnd', 'cooling_season_end', 274),
    InputVariable('CATcoolOffset', 'category_cooling_offset', 0),
    InputVariable('CATheatOffset', 'category_heating_offset', 0),
    InputVariable('SetpointAcc', 'setpoint_accuracy', 10000),
    InputVariable('m', 'custom_slope', 0.31),
    InputVariable('n', 'custom_intercept', 17.8),
    InputVariable('CustAST_ACSToffset', 'custom_cooling_offset', 3.5),
    InputVariable('CustAST_AHSToffset', 'custom_heating_offset', -3.5),
    InputVariable('CustAST_ACSTaul', 'custom_cooling_upper_limit', 33.5),
    InputVariable('CustAST_ACSTall', 'custom_cooling_lower_limit', 10),
    InputVariable('CustAST_AHSTaul', 'custom_heating_upper_limit', 33.5),
    InputVariable('CustAST_AHSTall', 'custom_heating_lower_limit', 10),
    InputVariable('CustAST_metric', 'custom_outdoor_metric', 0, outdoor_metric_only=True),
    InputVariable('CustAST_alpha', 'custom_alpha', 0.8, outdoor_metric_only=True),
    InputVariable('CustAST_days', 'custom_days', 30, outdoor_metric_only=True),
    InputVariable('AHSTfloor', 'heating_setpoint_floor', None, optional=True),
    InputVariable('ACSTceil', 'cooling_setpoint_ceiling', None, optional=True),
    InputVariable('MaxTempDiffVOF', 'opening_factor_max_temp_diff', 6, mixed_mode_only=True),
    InputVariable('MinTempDiffVOF', 'opening_factor_min_temp_diff', 1, mixed_mode_only=True),
    InputVariable('MultiplierVOF', 'min_opening_factor', 0.25, mixed_mode_only=True),
)

#: The arguments that can be given for each zone (``zone_arguments`` of AddAccis and modify_accis). The tolerance of
#: the setpoints is ``setpoint_tolerance``, as in modify_accis.
ZONE_ARGUMENTS = tuple(dict.fromkeys(item.argument for item in INPUT_VARIABLES))

_SET_LINE = re.compile(r'^\s*set\s+([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$', re.IGNORECASE)


def input_values(arguments: Mapping) -> Dict[str, Any]:
    """The values of the EMS variables set by some arguments of :func:`accim.sim.accis.modify_accis`.

    The arguments that are None or missing are left out. The tolerance of the cooling setpoint is the negative of
    ``setpoint_tolerance``, and the dates of the cooling season can be 'dd/mm' dates.

    :param arguments: The arguments, ``{'comfort_standard': 1, 'setpoint_tolerance': 0.1...}``.
    :return: The values, ``{'ComfStand': 1, 'ACSTtol': -0.1, 'AHSTtol': 0.1...}``.
    """
    values = {}
    for item in INPUT_VARIABLES:
        value = arguments.get(item.argument)
        if value is None:
            continue
        if item.variable == 'ACSTtol':
            value = -value
        elif item.argument in ('cooling_season_start', 'cooling_season_end'):
            value = to_day_of_year(value, item.argument)
        elif item.variable == 'CustAST_metric':
            from accim.sim.ems.outdoor_metric import metric_code
            value = metric_code(value)
        values[item.variable] = value
    return values


def input_lines(values: Optional[Mapping[str, Any]] = None, mixed_mode: bool = True,
                outdoor_metric: bool = False) -> List[str]:
    """The lines of a program SetInputData_<zone>, with the default value of the variables not given (the optional
    inputs, only if they are given).

    :param values: The values of some EMS variables (see :func:`input_values`).
    :param mixed_mode: False to leave out the inputs of the venting opening factor.
    :param outdoor_metric: True to add the inputs of the outdoor metric of the custom model (the models with its EMS
        code, see :mod:`accim.sim.ems.outdoor_metric`).
    """
    values = values or {}
    return [f'set {item.variable} = {values.get(item.variable, item.default)}'
            for item in INPUT_VARIABLES
            if (mixed_mode or not item.mixed_mode_only) and (outdoor_metric or not item.outdoor_metric_only)
            and (not item.optional or values.get(item.variable) is not None)]


def input_programs(idf) -> Dict[str, Any]:
    """The programs SetInputData_<zone> of a model, by the name of their zone in the EMS objects (empty for the
    models of earlier versions of accim, which have one program SetInputData for all the zones)."""
    prefix = INPUT_PROGRAM_PREFIX.upper()
    return {program.Name[len(prefix):]: program for program in idf.idfobjects['EnergyManagementSystem:Program']
            if program.Name.upper().startswith(prefix)}


def _value(text: str) -> Any:
    for kind in (int, float):
        try:
            return kind(text)
        except ValueError:
            pass
    return text


def read_inputs(program) -> Dict[str, Any]:
    """The values of the variables that a program sets with lines ``set <variable> = <number>``."""
    values = {}
    for line in program.fieldvalues[2:]:
        match = _SET_LINE.match(str(line))
        if match:
            values[match.group(1)] = _value(match.group(2))
    return values


def zone_comfort_standards(idf) -> Set[int]:
    """The comfort standards of the zones of a model (ComfStand in their programs SetInputData_<zone>)."""
    return {read_inputs(program)['ComfStand'] for program in input_programs(idf).values()}


def set_inputs(program, values: Mapping[str, Any]) -> List[str]:
    """Set the values of some variables in the lines ``set <variable> = ...`` of a program.

    :param program: A program SetInputData_<zone>.
    :param values: The values, by EMS variable (the names are case-insensitive, as in the EMS).
    :return: The variables that the program does not set, whose lines are not added (the inputs of the venting
        opening factor of the models without natural ventilation, for instance).
    """
    wanted = {str(name).upper(): (name, value) for name, value in values.items()}
    found = set()
    for number, line in enumerate(program.fieldvalues[2:], start=1):
        match = _SET_LINE.match(str(line))
        if match and match.group(1).upper() in wanted:
            _, value = wanted[match.group(1).upper()]
            setattr(program, f'Program_Line_{number}', f'set {match.group(1)} = {value}')
            found.add(match.group(1).upper())
    return [name for key, (name, _) in wanted.items() if key not in found]


def check_zone_arguments(zone_arguments: Optional[Mapping]) -> Dict[Any, Dict[str, Any]]:
    """Check the argument ``zone_arguments``: ``{zone: {argument: value}}``, with one value of each argument.

    :return: The arguments of each zone, as dictionaries (empty if ``zone_arguments`` is None).
    :raises ValueError: If it is not a dictionary of dictionaries, or an argument cannot be given for a zone.
    """
    if zone_arguments is None:
        return {}
    example = "{'Block1:Zone1': {'comfort_standard': 2, 'category': 80, 'comfort_mode': 3}}"
    if not isinstance(zone_arguments, Mapping):
        raise ValueError(f'zone_arguments must be a dictionary with the arguments of each zone, such as {example}, '
                         f'not {zone_arguments!r}.')
    checked = {}
    for zone, arguments in zone_arguments.items():
        if not isinstance(arguments, Mapping):
            raise ValueError(f'The arguments of the zone {zone!r} in zone_arguments must be a dictionary, such as '
                             f'{example}, not {arguments!r}.')
        for name, value in arguments.items():
            if name not in ZONE_ARGUMENTS:
                new_name = LEGACY_ARGUMENT_NAMES.get(name)
                hint = f" Its name is '{new_name}'." if new_name in ZONE_ARGUMENTS else ''
                raise ValueError(f'{name!r} (zone {zone!r}) cannot be given for each zone in zone_arguments.{hint} '
                                 f'The arguments of each zone are {list(ZONE_ARGUMENTS)}.')
            if value is None or isinstance(value, (list, tuple, set, Mapping)):
                raise ValueError(f'The argument {name!r} of the zone {zone!r} in zone_arguments must be one value '
                                 f'(a number, or a date for the cooling season), not {value!r}.')
            if name == 'setpoint_accuracy' and isinstance(value, (int, float)) and value < 0:
                raise ValueError(f'The value for setpoint_accuracy cannot be less than 0 (zone {zone!r}).')
        checked[zone] = dict(arguments)
    return checked


def zone_names(targets: Iterable, zones: Optional[Sequence[str]] = None) -> Dict[str, List[str]]:
    """The names that identify each zone in ``zone_arguments``, by its name in the EMS objects.

    A zone can be given by its name, by the key of its target (the name of the zone, or '<space> <people>' as in
    the dictionaries of :func:`accim.sim.apmv.apply_apmv_setpoints`) or by its name in the EMS objects.

    :param targets: The targets of the model (:func:`accim.sim.targets.resolve_targets`).
    :param zones: The names of the zones in the EMS objects, if only some of them (those with a program
        SetInputData_<zone>, for instance).
    """
    names = {}
    for target in targets:
        if zones is None or target.ems_suffix in zones:
            names[target.ems_suffix] = list(dict.fromkeys([target.zone_name, target.df_key, target.ems_suffix]))
    for zone in zones or ():
        names.setdefault(zone, [zone])
    return names


def resolve_zone_arguments(zone_arguments: Mapping, names: Mapping[str, Sequence[str]],
                           strict: bool = True) -> Dict[str, Dict[str, Any]]:
    """The arguments of each zone of ``zone_arguments`` (already checked), by the name of the zone in the EMS objects.

    :param zone_arguments: ``{zone: {argument: value}}``; the zones can be given by any of their names, in any case.
    :param names: The names of each zone (see :func:`zone_names`).
    :param strict: True to raise a ValueError if a zone is not in the model; False to leave it out.
    :raises ValueError: If ``strict`` is True and a zone is not in the model.
    """
    lookup = {}
    for zone, zone_aliases in names.items():
        for alias in zone_aliases:
            lookup.setdefault(str(alias).upper(), zone)
    resolved: Dict[str, Dict[str, Any]] = {}
    unknown = []
    for key, arguments in zone_arguments.items():
        zone = lookup.get(str(key).upper())
        if zone is None:
            unknown.append(key)
            continue
        resolved.setdefault(zone, {}).update(arguments)
    if unknown and strict:
        valid = [aliases[0] for aliases in names.values()]
        raise ValueError(f'The zones {unknown} of zone_arguments are not occupied zones of the model. Its occupied '
                         f'zones are {valid}.')
    return resolved
