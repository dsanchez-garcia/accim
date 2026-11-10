# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The EMS code with which the ACCIS calculates the setpoints, to read it before adding the ACCIS to a model.

:func:`get_setpoint_ems_code` gives the lines of the EMS programs (in Erl, the language of the Energy Management System
of EnergyPlus) that calculate the setpoints of a comfort standard, category and comfort mode, as they are in the
output IDFs of :class:`accim.sim.accis.AddAccis`, and :func:`print_setpoint_ems_code` prints them: which setpoints
apply, and what happens out of the applicability limits of the comfort standard.
"""

from typing import Dict, Iterable, List, Optional, Sequence, Union

from accim._deprecation import accepts_legacy_kwargs
from accim.sim.arguments import DEPRECATED_ARGUMENT_NAMES, CustomRegime, check_custom_regimes
from accim.sim.ems import custom_regimes as cr
from accim.sim.ems import outdoor_metric as om
from accim.sim.ems import program_lines as pl
from accim.sim.ems import setpoint_limits as sl
from accim.sim.ems import static_setpoints as ss
from accim.sim.ems.erl import format_number
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
from accim.sim.ems.standard_lines import (
    WEATHER_FILE_METRICS,
    metric_variable,
    needs_outdoor_metric_code,
    standard_inputs,
    weather_file_definition,
    weather_file_lines,
)
from accim.sim.standards import COMFORT_STANDARDS, FIRST_REGISTRY_NUMBER, comfort_standard_definition, definition_of

__all__ = ['get_setpoint_ems_code', 'get_setpoint_ems_programs', 'print_setpoint_ems_code']

Number = Union[int, float]

#: The inputs of SetInputData_<zone> that the setpoints use (the others are those of the ventilation).
_SETPOINT_INPUTS = {'ComfStand', 'CAT', 'ComfMod', 'ACSTtol', 'AHSTtol', 'CoolSeasonStart', 'CoolSeasonEnd',
                    'CATcoolOffset', 'CATheatOffset', 'SetpointAcc'}
#: Those of the custom comfort model.
_CUSTOM_INPUTS = {'m', 'n', 'CustAST_ACSToffset', 'CustAST_AHSToffset', 'CustAST_ACSTaul', 'CustAST_ACSTall',
                  'CustAST_AHSTaul', 'CustAST_AHSTall'}
#: Those of the outdoor metric of the custom model, with a metric other than 'pmot'.
_OUTDOOR_METRIC_INPUTS = set(om.INPUTS)
_CUSTOM = 99
#: The zone of the programs of the outdoor metric of a zone
_ZONE = '<zone>'
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
_OUTDOOR_METRIC_LEGEND = (
    '! Tout_metric: the outdoor metric of the custom model (custom_outdoor_metric), or of a comfort standard defined',
    '! by its data, with which it calculates its comfort temperature, setpoints and applicability. SetOutdoorMetric',
    '! runs in each timestep before the programs of the zones, and InitOutdoorMetric at the beginning of each',
    '! environment; OutT is the outdoor dry-bulb temperature (Site Outdoor Air Drybulb Temperature). Without the',
    '! weather file (argument epw of AddAccis), the daily means begin with PMOT; with it, with those of the weather',
    '! file.',
)
_LIMIT_LEGEND = (
    '! AHSTmin and ACSTmax: the minimum heating setpoint and the maximum cooling setpoint of the',
    '! zone (heating_setpoint_minimum and cooling_setpoint_maximum), whatever the comfort standard and comfort mode;',
    '! ApplySetpointLimits_<zone>, after SetASTnoTol, bounds AHST and ACST and rounds them again (the setpoints',
    '! bounded by the minimum or the maximum are the minimum or the maximum), and bounds AHSTnoTol and ACSTnoTol too.',
)
_REGIME_LEGEND = (
    '! SelectCustomRegime_<zone>: the regimes of the custom model (custom_regimes), in their order of priority. The',
    '! first one whose condition holds sets the inputs of the custom model (m, n, CustAST_ACSToffset...), which',
    '! SetAppLimits, ApplyCAT, SetComfTemp and SetAST use, and CustomRegime_<zone>, its number; if none holds',
    '! (CustomRegime_<zone> = 0), the inputs of SetInputData_<zone> apply. NoH_NoC_reqs is 1 if the HVAC system',
    '! of the zone neither heated nor cooled in the previous timestep (mixed mode).',
)
#: The lines that set NoH_NoC_reqs in each script type of mixed mode (accim.sim.ems.program_lines)
_HVAC_OFF_LINES = {'vrf_mm': pl.HVAC_OFF_FROM_COILS, 'ex_mm': pl.HVAC_OFF_FROM_LOAD}


def _number(value: Number) -> str:
    return format_number(value)


def _section(title: str, lines: Iterable[str]) -> List[str]:
    return [f'! --- {title} ---', *indent_lines(lines), '']


def _header(comfort_standard: int, category: Optional[Number], comfort_mode: Optional[Number],
            arguments: Optional[dict] = None, weather_file: bool = False) -> List[str]:
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
    lines += _definition_lines(comfort_standard, arguments or {}, weather_file)
    return lines


def _evidence_text(value) -> str:
    """A value of the evidence of a comfort standard, in one line."""
    if isinstance(value, dict):
        return '{' + ', '.join(f'{key}: {_evidence_text(item)}' for key, item in value.items()) + '}'
    if isinstance(value, (list, tuple)):
        return '[' + ', '.join(_evidence_text(item) for item in value) + ']'
    return str(value)


def _metric_text(definition) -> str:
    metric = definition.outdoor_metric
    if metric == 'rmot_alpha':
        metric += f' (alpha {definition.alpha})'
    elif metric == 'ndrm':
        metric += f' ({definition.days} days)'
    return metric


def _definition_lines(comfort_standard: int, arguments: dict, weather_file: bool = False) -> List[str]:
    """The comments with the source, the outdoor metric and the evidence of a comfort standard defined by its data
    (:mod:`accim.sim.standards`: JPN Aqilah 2025, built in, and those of the registry), or none. With
    ``weather_file``, the outdoor metric of JPN Aqilah 2025 is that of the models with the values of the weather file
    (:data:`accim.sim.ems.standard_lines.WEATHER_FILE_METRICS`), and its static setpoints are those of ``arguments``
    (:mod:`accim.sim.ems.static_setpoints`)."""
    definition = definition_of(comfort_standard)
    if definition is None:
        return []
    kind = 'defined by its data' if definition.number >= FIRST_REGISTRY_NUMBER else 'built in, defined by its data'
    lines = [f'! Comfort standard {kind} (accim.sim.standards): {definition.citation}']
    if weather_file and comfort_standard in WEATHER_FILE_METRICS:
        weather = weather_file_definition(comfort_standard)
        lines.append(f'! Outdoor metric: {_metric_text(weather)}, in the EMS '
                     f'{metric_variable(weather.outdoor_metric)}, which begins with the values of the weather file '
                     f'(without it, {_metric_text(definition)}, in the EMS '
                     f'{metric_variable(definition.outdoor_metric)})')
    else:
        lines.append(f'! Outdoor metric: {_metric_text(definition)}, in the EMS '
                     f'{metric_variable(definition.outdoor_metric)}')
    if ss.has_static_setpoints(comfort_standard):
        heating, cooling = (arguments.get(name, default) for name, default in zip(ss.ARGUMENTS, ss.DEFAULTS))
        lines.append(f'! Static setpoints: {heating} for heating and {cooling} for cooling (the inputs StaticAHST and '
                     f'StaticACST of the zone: static_heating_setpoint and static_cooling_setpoint)')
    elif definition.static_setpoints is not None:
        lines.append(f'! Static setpoints: {definition.static_setpoints[0]} for heating and '
                     f'{definition.static_setpoints[1]} for cooling')
    lines.append('! Evidence:')
    lines += [f'!     {key}: {_evidence_text(value)}' for key, value in definition.evidence.items()]
    return lines


def _input_lines(comfort_standard: int, category: Optional[Number], comfort_mode: Optional[Number],
                 arguments: dict, outdoor_metric: bool = False) -> List[str]:
    values = input_values(dict(arguments, comfort_standard=comfort_standard, category=category,
                               comfort_mode=comfort_mode))
    wanted = _SETPOINT_INPUTS | (_CUSTOM_INPUTS if comfort_standard == _CUSTOM else set())
    if outdoor_metric:
        wanted |= _OUTDOOR_METRIC_INPUTS
        # JPN Aqilah 2025 with the weather file: the inputs of its outdoor metric (accim.sim.ems.outdoor_metric)
        weather = weather_file_definition(comfort_standard)
        if weather is not None:
            values.update(standard_inputs(weather))
    # The minimum and maximum of the setpoints, if they are given, and the static setpoints of JPN Aqilah 2025
    wanted |= set(sl.INPUTS)
    if ss.has_static_setpoints(comfort_standard):
        wanted |= set(ss.INPUTS)
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


def _limit_program(arguments: dict) -> List[str]:
    """The lines of the program of the minimum and maximum of the setpoints of a zone (none without them)."""
    minimum, maximum = arguments.get('heating_setpoint_minimum'), arguments.get('cooling_setpoint_maximum')
    sl.check_setpoint_limits(minimum, maximum)
    if minimum is None and maximum is None:
        return []
    return sl.limit_program_lines(minimum is not None, maximum is not None)


def _check_static_setpoints(comfort_standard: int, arguments: dict) -> None:
    """Check the static setpoints of JPN Aqilah 2025 (:mod:`accim.sim.ems.static_setpoints`), which the other comfort
    standards ignore."""
    if ss.has_static_setpoints(comfort_standard):
        ss.check_static_setpoints(*(arguments.get(name, default) for name, default in zip(ss.ARGUMENTS, ss.DEFAULTS)))


def _regime_program(comfort_standard: int, arguments: dict, outdoor_metric: bool) -> List[str]:
    """The lines of the program of the regimes of the custom model of a zone (none without them), as in the output
    IDFs of AddAccis with the script type ``script_type`` (which the conditions 'hvac_off' and 'hvac_on' need)."""
    regimes = check_custom_regimes(arguments.get('custom_regimes'))
    if not regimes:
        return []
    if comfort_standard != _CUSTOM:
        raise ValueError(f'custom_regimes needs the custom model (comfort_standard {_CUSTOM}), not comfort_standard '
                         f'{comfort_standard}.')
    hvac_lines = None
    if cr.uses_hvac_conditions(regimes):
        script_type = arguments.get('script_type')
        if script_type not in _HVAC_OFF_LINES:
            raise ValueError(f"The conditions 'hvac_off' and 'hvac_on' of custom_regimes need script_type 'vrf_mm' or "
                             f"'ex_mm' (mixed mode), whose HVAC systems they read, not {script_type!r}.")
        hvac_lines = pl.format_lines(_HVAC_OFF_LINES[script_type], zone=_ZONE)
    return cr.regime_program_lines(_ZONE, regimes, pl.OUTDOOR_METRIC_VARIABLE if outdoor_metric else 'PMOT',
                                   hvac_lines)


def _outdoor_metric_programs(comfort_standard: int, arguments: dict, epw, start_date) -> Dict[str, List[str]]:
    """The programs of the outdoor metric of the custom model, as in the output IDFs of AddAccis with the weather file
    ``epw`` and a RunPeriod that begins on ``start_date`` (none if the comfort standard is not the custom model or its
    metric is 'pmot'), or those of the outdoor metric of a comfort standard defined by its data (none if EnergyPlus
    calculates it), or, with ``epw``, those of the outdoor metric of JPN Aqilah 2025 with the weather file
    (:data:`accim.sim.ems.standard_lines.WEATHER_FILE_METRICS`)."""
    definition = comfort_standard_definition(comfort_standard)
    if definition is None and epw is not None:
        definition = weather_file_definition(comfort_standard)
    if definition is not None:
        if not needs_outdoor_metric_code(definition):
            return {}
        metric, alpha, days = definition.outdoor_metric, definition.alpha, definition.days
    elif comfort_standard != _CUSTOM:
        return {}
    else:
        metric, alpha, days = (arguments[name] for name in ('custom_outdoor_metric', 'custom_alpha', 'custom_days'))
    code = om.check_outdoor_metric_arguments(metric, alpha, days)
    if code == 0:
        return {}
    initial = None
    if epw is not None:
        from accim.sim.arguments import to_day_of_year

        ring = om.ring_days([days])
        initial = om.initial_values(epw, to_day_of_year(start_date, 'start_date'), ring, {_ZONE: alpha})
    elif code == om.OUTDOOR_METRICS['monthly_mean']:
        raise ValueError("custom_outdoor_metric 'monthly_mean' needs the weather file of the simulations (argument "
                         "epw), whose monthly means the EMS programs keep.")
    ring = om.ring_days([days])
    return {
        om.INIT_PROGRAM: om.init_program_lines([_ZONE], ring),
        om.PROGRAM: om.building_program_lines(ring, initial),
        f'{om.ZONE_PROGRAM_PREFIX}{_ZONE}': om.zone_program_lines(
            _ZONE, ring, None if initial is None else initial['running_means'][_ZONE], initial is not None),
    }


def _checked_arguments(comfort_standard: int, category: Optional[Number], comfort_mode: Optional[Number],
                       **arguments) -> dict:
    """Check the comfort standard, category and comfort mode, as :class:`accim.sim.accis.AddAccis` does, and return the
    other arguments, with the defaults of :func:`get_setpoint_ems_code`."""
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
    return arguments


@accepts_legacy_kwargs(DEPRECATED_ARGUMENT_NAMES, version='1.2.0')
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
    custom_outdoor_metric: Union[str, int] = 'pmot',
    custom_alpha: Number = 0.8,
    custom_days: int = 30,
    epw=None,
    start_date: Union[int, str] = 1,
    heating_setpoint_minimum: Optional[Number] = None,
    cooling_setpoint_maximum: Optional[Number] = None,
    custom_regimes: Optional[Sequence[CustomRegime]] = None,
    script_type: Optional[str] = None,
    static_heating_setpoint: Number = ss.DEFAULTS[0],
    static_cooling_setpoint: Number = ss.DEFAULTS[1],
) -> str:
    """The EMS code with which the ACCIS calculates the setpoints of a comfort standard, category and comfort mode, to
    read it before adding the ACCIS to a model (:func:`print_setpoint_ems_code` prints it).

    The code is that of the output IDFs of :class:`accim.sim.accis.AddAccis`, indented, in the order in which the
    program ``RunACCIS_<zone>`` of each zone runs it: the inputs of the zone in ``SetInputData_<zone>`` (those of the
    setpoints), the applicability limits (``SetAppLimits``), the offsets of the category (``ApplyCAT``), the comfort
    temperature (``SetComfTemp``), the cooling season (``SetAST_Master``), the setpoints of the comfort mode, with what
    they are out of the applicability limits, and their rounding (the subprogram ``SetAST_CS<n>_<chunk>`` that has
    them, only the lines of the comfort mode), and the setpoints without tolerance (``SetASTnoTol``). With the custom
    model and an outdoor metric other than 'pmot', the programs of the outdoor metric come first
    (``InitOutdoorMetric`` and ``SetOutdoorMetric``, which do not belong to a zone, and ``SetOutdoorMetric_<zone>``,
    after the inputs of the zone; see :mod:`accim.sim.ems.outdoor_metric`). With the regimes of the custom model, the
    program ``SelectCustomRegime_<zone>`` comes before ``SetAppLimits`` (see :mod:`accim.sim.ems.custom_regimes`).
    With a minimum heating setpoint or a maximum cooling setpoint, the program
    ``ApplySetpointLimits_<zone>`` follows ``SetASTnoTol`` (see :mod:`accim.sim.ems.setpoint_limits`). Comments (lines
    that begin with ``!``) explain the variables.

    The arguments are those of :func:`accim.sim.accis.modify_accis`, with one value each, and the same defaults.

    :param comfort_standard: The comfort standard: 0 = ESP CTE; 1 = INT EN16798-1; 2 = INT ASHRAE55; 3 = JPN Rijal;
        4 = CHN GBT50785 Cold; 5 = CHN GBT50785 HotMild; 6 = CHN Yang; 7 = IND IMAC C NV; 8 = IND IMAC C MM;
        9 = IND IMAC R 7DRM; 10 = IND IMAC R 30DRM; 11 = IND Dhaka; 12 = ROM Udrea; 13 = AUS Williamson;
        14 = AUS DeDear; 15 = BRA Rupp NV; 16 = BRA Rupp AC; 17 = MEX Oropeza Arid; 18 = MEX Oropeza DryTropic;
        19 = MEX Oropeza Temperate; 20 = MEX Oropeza HumTropic; 21 = CHL Perez-Fargallo; 22 = INT ISO7730;
        23 = JPN Aqilah2025; 99 = CUSTOM; and those of the registry (100 or more, :mod:`accim.sim.standards`).
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
    :param custom_outdoor_metric: Custom model: its outdoor metric (see :class:`accim.sim.accis.AddAccis`).
    :param custom_alpha: Custom model, 'rmot_alpha': the alpha of the running mean.
    :param custom_days: Custom model, 'ndrm': the number of previous days.
    :param epw: Custom model with an outdoor metric other than 'pmot': the weather file with which its programs begin
        (argument ``epw`` of :class:`accim.sim.accis.AddAccis`); None to begin with PMOT. JPN Aqilah 2025 (23): with
        it, the code of the output IDFs of AddAccis with the weather file, whose running mean is that of EN 16798-1
        with α = 0.8 that the EMS calculates from it; without it, that of the output IDFs without it, which reads the
        RMOT of EnergyPlus (:data:`accim.sim.ems.standard_lines.WEATHER_FILE_METRICS`).
    :param start_date: The first day of the RunPeriod of the model (a date 'dd/mm' or a day of the year), with which
        the programs of the outdoor metric begin with the values of ``epw``.
    :param heating_setpoint_minimum: The minimum heating setpoint (°C), or None for none.
    :param cooling_setpoint_maximum: The maximum cooling setpoint (°C), or None for none.
    :param custom_regimes: Custom model: its regimes (see :class:`accim.sim.accis.AddAccis`), or None for none.
    :param script_type: The script type of the output IDFs ('vrf_mm' or 'ex_mm'), which the conditions 'hvac_off' and
        'hvac_on' of the regimes of the custom model need (they read the coils of the VRF systems of accim, or the
        load of the thermostats of the existing HVAC systems); None otherwise.
    :param static_heating_setpoint: JPN Aqilah 2025: its static heating setpoint (°C), the input ``StaticAHST`` of the
        zone (:mod:`accim.sim.ems.static_setpoints`); the other comfort standards ignore it.
    :param static_cooling_setpoint: JPN Aqilah 2025: its static cooling setpoint (°C), the input ``StaticACST``.
    :return: The lines of the programs, one after the other, separated by a comment with the name of each one.
    :raises ValueError: If the comfort standard does not exist, the category is not one of the comfort standard, or
        the comfort standard has no setpoints with the comfort mode (as in :class:`accim.sim.accis.AddAccis`), or the
        arguments of the outdoor metric are not valid ('monthly_mean' needs ``epw``), or the minimum and the maximum,
        or the static setpoints of JPN Aqilah 2025, or the regimes (they need the custom model, and their conditions
        'hvac_off' and 'hvac_on' the script type).
    """
    if comfort_standard not in COMFORT_STANDARDS:
        raise ValueError(f'comfort_standard {comfort_standard!r} is not a comfort standard '
                         f'(valid: {list(COMFORT_STANDARDS)})')
    comfort_standard = int(comfort_standard)
    arguments = _checked_arguments(
        comfort_standard, category, comfort_mode,
        setpoint_tolerance=setpoint_tolerance, setpoint_accuracy=setpoint_accuracy,
        cooling_season_start=cooling_season_start, cooling_season_end=cooling_season_end,
        category_cooling_offset=category_cooling_offset, category_heating_offset=category_heating_offset,
        custom_slope=custom_slope, custom_intercept=custom_intercept, custom_cooling_offset=custom_cooling_offset,
        custom_heating_offset=custom_heating_offset, custom_cooling_upper_limit=custom_cooling_upper_limit,
        custom_cooling_lower_limit=custom_cooling_lower_limit, custom_heating_upper_limit=custom_heating_upper_limit,
        custom_heating_lower_limit=custom_heating_lower_limit, custom_outdoor_metric=custom_outdoor_metric,
        custom_alpha=custom_alpha, custom_days=custom_days, heating_setpoint_minimum=heating_setpoint_minimum,
        cooling_setpoint_maximum=cooling_setpoint_maximum, custom_regimes=custom_regimes, script_type=script_type,
        static_heating_setpoint=static_heating_setpoint, static_cooling_setpoint=static_cooling_setpoint,
    )
    metric_programs = _outdoor_metric_programs(comfort_standard, arguments, epw, start_date)
    outdoor_metric = bool(metric_programs)
    # JPN Aqilah 2025 with the weather file reads its outdoor metric, Tout_metric (finding B4-1 of accim 1.2.0)
    weather_file = outdoor_metric and comfort_standard in WEATHER_FILE_METRICS
    limit_lines = _limit_program(arguments)
    _check_static_setpoints(comfort_standard, arguments)
    regime_lines = _regime_program(comfort_standard, arguments, outdoor_metric)

    def branches(lines, name=''):
        # As in the output IDFs: the branch of the comfort standard, or 'return' if it has none
        lines = pl.for_comfort_standards(lines, [comfort_standard]) or ['return']
        return weather_file_lines(name, lines, weather_file)

    lines = [*_header(comfort_standard, category, comfort_mode, arguments, weather_file), '', *_LEGEND]
    if outdoor_metric:
        lines += _OUTDOOR_METRIC_LEGEND
    if regime_lines:
        lines += _REGIME_LEGEND
    if limit_lines:
        lines += _LIMIT_LEGEND
    lines.append('')
    if outdoor_metric:
        lines += _section('InitOutdoorMetric: at the beginning of each environment, the outdoor metric restarts',
                          metric_programs[om.INIT_PROGRAM])
        lines += _section('SetOutdoorMetric: in each timestep, before the programs of the zones, the daily outdoor '
                          'temperatures', metric_programs[om.PROGRAM])
    lines += _section('SetInputData_<zone>: the inputs of the zone (those of the setpoints)',
                      _input_lines(comfort_standard, category, comfort_mode, arguments, outdoor_metric))
    if outdoor_metric:
        lines += _section('SetOutdoorMetric_<zone>: the outdoor metric of the zone, Tout_metric',
                          metric_programs[f'{om.ZONE_PROGRAM_PREFIX}{_ZONE}'])
    if regime_lines:
        conditions = ', '.join(f'{number} = {cr.condition_text(regime.condition)}' for number, regime
                               in enumerate(check_custom_regimes(arguments['custom_regimes']), start=1))
        lines += _section(f'{cr.PROGRAM_PREFIX}{_ZONE}: the regime of the custom model of the timestep ({conditions}), '
                          f'which sets its inputs', regime_lines)
    lines += _section('SetAppLimits: the applicability limits', branches(pl.set_app_limits_lines()))
    lines += _section('ApplyCAT: the offsets of the category', branches(pl.apply_cat_lines()))
    lines += _section('SetComfTemp: the comfort temperature',
                      branches(pl.set_comf_temp_lines(outdoor_metric), 'SetComfTemp'))
    lines += _section('SetAST: the setpoints', pl.SET_AST)
    lines += _section('SetAST_Master: the cooling season, and the subprograms of the comfort standard',
                      master_program_lines([comfort_standard]))
    if comfort_mode is not None and depends_on_comfort_mode(comfort_standard):
        name = subprogram_name(comfort_standard, comfort_mode)
        lines += _section(f'{name}, its lines for ComfMod == {_number(comfort_mode)}: the setpoints, and their '
                          f'rounding', weather_file_lines(name, get_setpoint_lines(comfort_standard, comfort_mode,
                                                                                 outdoor_metric), weather_file))
    else:
        for name, subprogram in subprograms([comfort_standard], outdoor_metric).items():
            lines += _section(f'{name}: the setpoints, and their rounding',
                              weather_file_lines(name, subprogram, weather_file))
    lines += _section('SetASTnoTol: the setpoints without the tolerance (for the hour counters)', pl.SET_AST_NO_TOL)
    if limit_lines:
        lines += _section(f'{sl.PROGRAM_PREFIX}{_ZONE}: after SetASTnoTol, the minimum heating setpoint and the '
                          f'maximum cooling setpoint of the zone, the rounding again, and the minimum and maximum '
                          f'of the setpoints without the tolerance', limit_lines)
    return '\n'.join(lines).rstrip('\n')


@accepts_legacy_kwargs(DEPRECATED_ARGUMENT_NAMES, version='1.2.0')
def print_setpoint_ems_code(comfort_standard: int, category: Optional[Number] = None,
                            comfort_mode: Optional[Number] = None, **arguments) -> None:
    """Print the EMS code with which the ACCIS calculates the setpoints of a comfort standard, category and comfort
    mode (see :func:`get_setpoint_ems_code`, which takes the same arguments).

    For instance, ``print_setpoint_ems_code(comfort_standard=1, category=2, comfort_mode=3)``.
    """
    print(get_setpoint_ems_code(comfort_standard, category, comfort_mode, **arguments))


@accepts_legacy_kwargs(DEPRECATED_ARGUMENT_NAMES, version='1.2.0')
def get_setpoint_ems_programs(
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
    custom_outdoor_metric: Union[str, int] = 'pmot',
    custom_alpha: Number = 0.8,
    custom_days: int = 30,
    epw=None,
    start_date: Union[int, str] = 1,
    heating_setpoint_minimum: Optional[Number] = None,
    cooling_setpoint_maximum: Optional[Number] = None,
    custom_regimes: Optional[Sequence[CustomRegime]] = None,
    script_type: Optional[str] = None,
    static_heating_setpoint: Number = ss.DEFAULTS[0],
    static_cooling_setpoint: Number = ss.DEFAULTS[1],
) -> Dict[str, List[str]]:
    """The EMS programs with which the ACCIS calculates the setpoints of a comfort standard, category and comfort mode,
    as they are in the output IDFs of :class:`accim.sim.accis.AddAccis`, to run them with the Erl interpreter of
    :mod:`accim.sim.ems.erl` (as :func:`accim.sim.preview.compute_setpoints` does).

    They are the programs of :func:`get_setpoint_ems_code`, by name and in the same order, except that the subprograms
    ``SetAST_CS<n>_<chunk>`` are whole (``get_setpoint_ems_code`` shows the lines of the comfort mode only) and that
    ``SetInputData_<zone>`` sets the category and the comfort mode, which must be given if the comfort standard has
    categories or setpoints that depend on the comfort mode. ``SetAST`` runs ``SetAST_Master``, which runs the
    subprograms. With the custom model and an outdoor metric other than 'pmot', the programs of the outdoor metric
    come first: ``InitOutdoorMetric``, ``SetOutdoorMetric`` and ``SetOutdoorMetric_<zone>``, whose lines name the
    variables of the zone with '<zone>'. With the regimes of the custom model, ``SelectCustomRegime_<zone>`` runs
    before ``SetAppLimits``. With a minimum or a maximum of the setpoints, ``ApplySetpointLimits_<zone>`` runs after
    ``SetASTnoTol``.

    :param comfort_standard: The comfort standard (see :func:`get_setpoint_ems_code`).
    :param category: The category.
    :param comfort_mode: The comfort mode.
    :return: The lines of each program, by name: (``InitOutdoorMetric``, ``SetOutdoorMetric``),
        ``SetInputData_<zone>``, (``SetOutdoorMetric_<zone>``), (``SelectCustomRegime_<zone>``), ``SetAppLimits``,
        ``ApplyCAT``, ``SetComfTemp``, ``SetAST``, ``SetAST_Master``, the subprograms, ``SetASTnoTol`` and
        (``ApplySetpointLimits_<zone>``).
    :raises ValueError: As :func:`get_setpoint_ems_code`, and if the category or the comfort mode is missing.

    The other arguments are those of :func:`get_setpoint_ems_code`, with the same defaults.
    """
    arguments = _checked_arguments(
        comfort_standard, category, comfort_mode,
        setpoint_tolerance=setpoint_tolerance, setpoint_accuracy=setpoint_accuracy,
        cooling_season_start=cooling_season_start, cooling_season_end=cooling_season_end,
        category_cooling_offset=category_cooling_offset, category_heating_offset=category_heating_offset,
        custom_slope=custom_slope, custom_intercept=custom_intercept, custom_cooling_offset=custom_cooling_offset,
        custom_heating_offset=custom_heating_offset, custom_cooling_upper_limit=custom_cooling_upper_limit,
        custom_cooling_lower_limit=custom_cooling_lower_limit, custom_heating_upper_limit=custom_heating_upper_limit,
        custom_heating_lower_limit=custom_heating_lower_limit, custom_outdoor_metric=custom_outdoor_metric,
        custom_alpha=custom_alpha, custom_days=custom_days, heating_setpoint_minimum=heating_setpoint_minimum,
        cooling_setpoint_maximum=cooling_setpoint_maximum, custom_regimes=custom_regimes, script_type=script_type,
        static_heating_setpoint=static_heating_setpoint, static_cooling_setpoint=static_cooling_setpoint,
    )
    comfort_standard = int(comfort_standard)
    if category is None and COMFORT_STANDARDS[comfort_standard].categories:
        raise ValueError(f'comfort_standard {comfort_standard} needs a category '
                         f'(valid: {list(COMFORT_STANDARDS[comfort_standard].categories)})')
    if comfort_mode is None and depends_on_comfort_mode(comfort_standard):
        valid = [mode for mode in MODULAR_COMFORT_MODES[comfort_standard] if has_setpoints(comfort_standard, mode)]
        raise ValueError(f'comfort_standard {comfort_standard} needs a comfort_mode (valid: {valid})')
    metric_programs = _outdoor_metric_programs(comfort_standard, arguments, epw, start_date)
    outdoor_metric = bool(metric_programs)
    # JPN Aqilah 2025 with the weather file reads its outdoor metric, Tout_metric (finding B4-1 of accim 1.2.0)
    weather_file = outdoor_metric and comfort_standard in WEATHER_FILE_METRICS
    _check_static_setpoints(comfort_standard, arguments)

    def branches(lines, name=''):
        lines = pl.for_comfort_standards(lines, [comfort_standard]) or ['return']
        return weather_file_lines(name, lines, weather_file)

    inputs = [line for line in _input_lines(comfort_standard, category, comfort_mode, arguments, outdoor_metric)
              if not line.startswith('!')]
    zone_program = f'{om.ZONE_PROGRAM_PREFIX}{_ZONE}'
    programs = {name: list(lines) for name, lines in metric_programs.items() if name != zone_program}
    programs['SetInputData_<zone>'] = inputs
    if outdoor_metric:
        programs[zone_program] = list(metric_programs[zone_program])
    regime_lines = _regime_program(comfort_standard, arguments, outdoor_metric)
    if regime_lines:
        programs[f'{cr.PROGRAM_PREFIX}{_ZONE}'] = regime_lines
    programs.update({
        'SetAppLimits': branches(pl.set_app_limits_lines()),
        'ApplyCAT': branches(pl.apply_cat_lines()),
        'SetComfTemp': branches(pl.set_comf_temp_lines(outdoor_metric), 'SetComfTemp'),
        'SetAST': list(pl.SET_AST),
        'SetAST_Master': master_program_lines([comfort_standard]),
    })
    programs.update({name: weather_file_lines(name, lines, weather_file)
                     for name, lines in subprograms([comfort_standard], outdoor_metric).items()})
    programs['SetASTnoTol'] = list(pl.SET_AST_NO_TOL)
    limit_lines = _limit_program(arguments)
    if limit_lines:
        programs[f'{sl.PROGRAM_PREFIX}{_ZONE}'] = limit_lines
    return programs
