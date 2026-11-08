# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The EMS code with which the ACCIS calculates the setpoints, to read it before adding the ACCIS to a model.

:func:`get_setpoint_ems_code` gives the lines of the EMS programs (in Erl, the language of the Energy Management System
of EnergyPlus) that calculate the setpoints of a comfort standard, category and comfort mode, as they are in the
output IDFs of :class:`accim.sim.accis.AddAccis`, and :func:`print_setpoint_ems_code` prints them: which setpoints
apply, and what happens out of the applicability limits of the comfort standard.
"""

from typing import Iterable, List, Optional, Union

from accim.sim.ems import program_lines as pl
from accim.sim.ems.inputs import INPUT_VARIABLES, input_values
from accim.sim.ems.programs import indent_lines
from accim.sim.ems.setast import (
    MODULAR_COMFORT_MODES,
    depends_on_comfort_mode,
    get_setpoint_lines,
    has_setpoints,
    master_program_lines,
    subprogram_name,
    subprograms,
)
from accim.sim.standards import COMFORT_STANDARDS

__all__ = ['get_setpoint_ems_code', 'print_setpoint_ems_code']

Number = Union[int, float]

#: The inputs of SetInputData_<zone> that the setpoints use (the others are those of the ventilation).
_SETPOINT_INPUTS = {'ComfStand', 'CAT', 'ComfMod', 'ACSTtol', 'AHSTtol', 'CoolSeasonStart', 'CoolSeasonEnd',
                    'CATcoolOffset', 'CATheatOffset', 'SetpointAcc'}
#: Those of the custom comfort model.
_CUSTOM_INPUTS = {'m', 'n', 'CustAST_ACSToffset', 'CustAST_AHSToffset', 'CustAST_ACSTaul', 'CustAST_ACSTall',
                  'CustAST_AHSTaul', 'CustAST_AHSTall'}
_CUSTOM = 99
_LEGEND = (
    '! In each timestep, the program RunACCIS_<zone> of each occupied zone runs these programs, in this',
    '! order; then ApplyAST_<zone> gives roundedACST and roundedAHST to the setpoint schedules of the zone',
    '! (depending on the script type and, in mixed mode, on the occupants and the windows).',
    '! RMOT and PMOT: the running and prevailing mean outdoor temperatures (outputs of EnergyPlus for the',
    '! People objects). ComfTemp: the comfort temperature. ACSTall and ACSTaul, AHSTall and AHSTaul: the lower',
    '! and upper applicability limits of the cooling and heating setpoints. ACSToffset and AHSToffset: the',
    '! offsets of the category. ACSTtol and AHSTtol: the tolerance. CoolingSeason: 1 from the day of the year',
    '! CoolSeasonStart to the day before CoolSeasonEnd. ACST and AHST: the cooling and heating setpoints;',
    '! roundedACST and roundedAHST, the same rounded with the accuracy SetpointAcc (the cooling setpoint down,',
    '! the heating setpoint up).',
)


def _number(value: Number) -> str:
    return str(int(value)) if value == int(value) else str(value)


def _section(title: str, lines: Iterable[str]) -> List[str]:
    return [f'! --- {title} ---', *indent_lines(lines), '']


def _header(comfort_standard: int, category: Optional[Number], comfort_mode: Optional[Number]) -> List[str]:
    standard = COMFORT_STANDARDS[comfort_standard]
    lines = ['! The EMS code (Erl) with which the ACCIS calculates the setpoints, as in the output IDFs of AddAccis',
             f'! Comfort standard (ComfStand): {standard.title}']
    if standard.categories:
        if category is None:
            lines.append('! Categories (CAT), whose offsets are in ApplyCAT:')
            lines += [f'!     {_number(number)} = {text}' for number, text in standard.categories.items()]
        else:
            lines.append(f'! Category (CAT): {_number(category)} = {standard.categories[category]}')
    if not depends_on_comfort_mode(comfort_standard):
        lines.append('! Comfort mode (ComfMod): the setpoints of this comfort standard do not depend on it')
    elif comfort_mode is None:
        lines.append('! Comfort modes (ComfMod), whose setpoints are in the subprograms SetAST_CS<n>_<chunk>:')
        lines += [f'!     {_number(mode)} = {standard.comfort_modes.get(mode, "")}'
                  for mode in MODULAR_COMFORT_MODES[comfort_standard] if has_setpoints(comfort_standard, mode)]
    else:
        lines.append(f'! Comfort mode (ComfMod): {_number(comfort_mode)} = '
                     f'{standard.comfort_modes.get(comfort_mode, "")}')
    return lines


def _input_lines(comfort_standard: int, category: Optional[Number], comfort_mode: Optional[Number],
                 arguments: dict) -> List[str]:
    values = input_values(dict(arguments, comfort_standard=comfort_standard, category=category,
                               comfort_mode=comfort_mode))
    wanted = _SETPOINT_INPUTS | (_CUSTOM_INPUTS if comfort_standard == _CUSTOM else set())
    lines = []
    for item in INPUT_VARIABLES:
        if item.variable not in wanted:
            continue
        if item.variable in values:
            lines.append(f'set {item.variable} = {_number(values[item.variable])}')
        elif item.variable == 'CAT' and COMFORT_STANDARDS[comfort_standard].categories:
            lines.append('! set CAT = <the category>')
        elif item.variable == 'ComfMod' and depends_on_comfort_mode(comfort_standard):
            lines.append('! set ComfMod = <the comfort mode>')
    return lines


def get_setpoint_ems_code(
    comfort_standard: int,
    category: Optional[Number] = None,
    comfort_mode: Optional[Number] = None,
    setpoint_tolerance: Number = 0.1,
    setpoint_accuracy: Number = 10000,
    cooling_season_start: Union[int, str] = 121,
    cooling_season_end: Union[int, str] = 274,
    category_cooling_offset: Number = 0,
    category_heating_offset: Number = 0,
    custom_slope: Number = 0,
    custom_intercept: Number = 0,
    custom_cooling_offset: Number = 0,
    custom_heating_offset: Number = 0,
    custom_cooling_upper_limit: Number = 0,
    custom_cooling_lower_limit: Number = 0,
    custom_heating_upper_limit: Number = 0,
    custom_heating_lower_limit: Number = 0,
) -> str:
    """The EMS code with which the ACCIS calculates the setpoints of a comfort standard, category and comfort mode, to
    read it before adding the ACCIS to a model (:func:`print_setpoint_ems_code` prints it).

    The code is that of the output IDFs of :class:`accim.sim.accis.AddAccis`, indented, in the order in which the
    program ``RunACCIS_<zone>`` of each zone runs it: the inputs of the zone in ``SetInputData_<zone>`` (those of the
    setpoints), the applicability limits (``SetAppLimits``), the offsets of the category (``ApplyCAT``), the comfort
    temperature (``SetComfTemp``), the cooling season (``SetAST_Master``), the setpoints of the comfort mode, with what
    they are out of the applicability limits, and their rounding (the subprogram ``SetAST_CS<n>_<chunk>`` that has
    them, only the lines of the comfort mode), and the setpoints without tolerance (``SetASTnoTol``). Comments (lines
    that begin with ``!``) explain the variables.

    The arguments are those of :func:`accim.sim.accis.modify_accis`, with one value each, and the same defaults.

    :param comfort_standard: The comfort standard: 0 = ESP CTE; 1 = INT EN16798-1; 2 = INT ASHRAE55; 3 = JPN Rijal;
        4 = CHN GBT50785 Cold; 5 = CHN GBT50785 HotMild; 6 = CHN Yang; 7 = IND IMAC C NV; 8 = IND IMAC C MM;
        9 = IND IMAC R 7DRM; 10 = IND IMAC R 30DRM; 11 = IND Dhaka; 12 = ROM Udrea; 13 = AUS Williamson;
        14 = AUS DeDear; 15 = BRA Rupp NV; 16 = BRA Rupp AC; 17 = MEX Oropeza Arid; 18 = MEX Oropeza DryTropic;
        19 = MEX Oropeza Temperate; 20 = MEX Oropeza HumTropic; 21 = CHL Perez-Fargallo; 22 = INT ISO7730;
        99 = CUSTOM.
    :param category: The category: 1, 2 or 3 (CAT I, II, III), or 80, 85 or 90 (% of acceptability); None for all
        of them (the offsets of each one are in ApplyCAT).
    :param comfort_mode: The comfort mode: 0 or 0.X = static; 1 or 1.X = adaptive when applicable, otherwise the local
        static model; 2 = adaptive when applicable, otherwise the international static model; 3 = adaptive when
        applicable, otherwise the adaptive setpoints extended horizontally. None for all of them (the subprograms of
        the comfort standard, whole).
    :param setpoint_tolerance: The tolerance of the setpoints.
    :param setpoint_accuracy: The accuracy of the setpoints: 2 rounds them to every half degree, 10 to the first
        decimal...
    :param cooling_season_start: The start of the cooling season (a date 'dd/mm' or a day of the year), used by
        some static models.
    :param cooling_season_end: The end of the cooling season.
    :param category_cooling_offset: An offset summed to the cooling setpoint offset of the category.
    :param category_heating_offset: An offset summed to the heating setpoint offset of the category.
    :param custom_slope: Custom model (comfort_standard 99): slope m of the comfort temperature (m * running mean
        outdoor temperature + n).
    :param custom_intercept: Custom model: intercept n of the comfort temperature.
    :param custom_cooling_offset: Custom model: offset of the cooling setpoint from the comfort temperature (positive).
    :param custom_heating_offset: Custom model: offset of the heating setpoint from the comfort temperature (negative).
    :param custom_cooling_upper_limit: Custom model: upper applicability limit of the cooling setpoint (of the running
        mean outdoor temperature).
    :param custom_cooling_lower_limit: Custom model: lower applicability limit of the cooling setpoint.
    :param custom_heating_upper_limit: Custom model: upper applicability limit of the heating setpoint.
    :param custom_heating_lower_limit: Custom model: lower applicability limit of the heating setpoint.
    :return: The lines of the programs, one after the other, separated by a comment with the name of each one.
    :raises ValueError: If the comfort standard does not exist, the category is not one of the comfort standard, or
        the comfort standard has no setpoints with the comfort mode (as in :class:`accim.sim.accis.AddAccis`).
    """
    if comfort_standard not in COMFORT_STANDARDS:
        raise ValueError(f'comfort_standard {comfort_standard!r} is not a comfort standard '
                         f'(valid: {list(COMFORT_STANDARDS)})')
    comfort_standard = int(comfort_standard)
    categories = COMFORT_STANDARDS[comfort_standard].categories
    if category is not None and categories and category not in categories:
        raise ValueError(f'category {category!r} is not a category of comfort_standard {comfort_standard} '
                         f'(valid: {list(categories)})')
    if comfort_mode is not None and not has_setpoints(comfort_standard, comfort_mode):
        valid = [mode for mode in MODULAR_COMFORT_MODES[comfort_standard] if has_setpoints(comfort_standard, mode)]
        raise ValueError(f'comfort_standard {comfort_standard} has no setpoints with comfort_mode {comfort_mode!r} '
                         f'(valid: {valid})')
    arguments = dict(
        setpoint_tolerance=setpoint_tolerance, setpoint_accuracy=setpoint_accuracy,
        cooling_season_start=cooling_season_start, cooling_season_end=cooling_season_end,
        category_cooling_offset=category_cooling_offset, category_heating_offset=category_heating_offset,
        custom_slope=custom_slope, custom_intercept=custom_intercept, custom_cooling_offset=custom_cooling_offset,
        custom_heating_offset=custom_heating_offset, custom_cooling_upper_limit=custom_cooling_upper_limit,
        custom_cooling_lower_limit=custom_cooling_lower_limit, custom_heating_upper_limit=custom_heating_upper_limit,
        custom_heating_lower_limit=custom_heating_lower_limit,
    )

    def branches(lines):
        # As in the output IDFs: the branch of the comfort standard, or 'return' if it has none
        return pl.for_comfort_standards(lines, [comfort_standard]) or ['return']

    lines = [*_header(comfort_standard, category, comfort_mode), '', *_LEGEND, '']
    lines += _section('SetInputData_<zone>: the inputs of the zone (those of the setpoints)',
                      _input_lines(comfort_standard, category, comfort_mode, arguments))
    lines += _section('SetAppLimits: the applicability limits', branches(pl.SET_APP_LIMITS))
    lines += _section('ApplyCAT: the offsets of the category', branches(pl.APPLY_CAT))
    lines += _section('SetComfTemp: the comfort temperature', branches(pl.SET_COMF_TEMP))
    lines += _section('SetAST: the setpoints', pl.SET_AST)
    lines += _section('SetAST_Master: the cooling season, and the subprograms of the comfort standard',
                      master_program_lines([comfort_standard]))
    if comfort_mode is not None and depends_on_comfort_mode(comfort_standard):
        name = subprogram_name(comfort_standard, comfort_mode)
        lines += _section(f'{name}, its lines for ComfMod == {_number(comfort_mode)}: the setpoints, and their '
                          f'rounding', get_setpoint_lines(comfort_standard, comfort_mode))
    else:
        for name, subprogram in subprograms([comfort_standard]).items():
            lines += _section(f'{name}: the setpoints, and their rounding', subprogram)
    lines += _section('SetASTnoTol: the setpoints without the tolerance (for the hour counters)', pl.SET_AST_NO_TOL)
    return '\n'.join(lines).rstrip('\n')


def print_setpoint_ems_code(comfort_standard: int, category: Optional[Number] = None,
                            comfort_mode: Optional[Number] = None, **arguments) -> None:
    """Print the EMS code with which the ACCIS calculates the setpoints of a comfort standard, category and comfort
    mode (see :func:`get_setpoint_ems_code`, which takes the same arguments).

    For instance, ``print_setpoint_ems_code(comfort_standard=1, category=2, comfort_mode=3)``.
    """
    print(get_setpoint_ems_code(comfort_standard, category, comfort_mode, **arguments))
