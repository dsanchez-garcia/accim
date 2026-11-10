# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The long-term thermal discomfort of the occupied hours of each zone and of the building, as EMS outputs of the
ACCIS (``report_long_term_discomfort``, proposal C2), which the parametric and optimisation module can read as
objectives and constraints (:mod:`accim.parametric_and_optimisation.objectives`).

CEN/TR 16798-2:2019, Annex D, defines the long-term indicators of the thermal comfort conditions of the occupied hours
(:mod:`accim.data.postprocessing.long_term_discomfort`, proposal D1, calculates them from the outputs of the
simulations); the EMS counts those of Methods A and B in each timestep, with the range of the comfort model of the
ACCIS, between the setpoints without the tolerance (``AHSTnoTol`` and ``ACSTnoTol``, those of the hour counters of the
ACCIS):

- Method A, the occupied hours outside the range: ``Hours Above Upper Limit_<zone>`` (the warm period: the operative
  temperature above ACSTnoTol) and ``Hours Below Lower Limit_<zone>`` (the cold period: below AHSTnoTol), in hours.
- Method B, the degree hours: wf = 0 within the range, Θo,limit,lower ≤ Θo ≤ Θo,limit,upper, and
  wf = abs(Θo − Θo,limit) outside it, times the time: ``Degree Hours Above Upper Limit_<zone>``,
  (Θo − ACSTnoTol)·Δt in the warm period, and ``Degree Hours Below Lower Limit_<zone>``, (AHSTnoTol − Θo)·Δt in the
  cold period, in degree hours (units ``Kh``).

In each timestep, the program ``CountLongTermDiscomfort_<zone>``, which ``RunACCIS_<zone>`` runs right after
``CountHoursNoApp_<zone>``, sets them to these values (Δt is the length of the timestep, ``ZoneTimeStep``) if the zone
has occupants, and to 0 otherwise; as in the other hour counters of the ACCIS, the EMS reads at the beginning of the
timestep the occupants of the timestep and the operative temperature of the previous one. The outputs are summed, so
each reporting period has its total, and the hours above and below add up to ``Occupied Discomfortable Hours_No
Applicability_<zone>`` (unless the heating setpoint is above the cooling setpoint, see
:mod:`accim.sim.ems.setpoint_limits`). The building has the sums of its zones (``Hours Above Upper Limit_Building``...),
which the program ``CountLongTermDiscomfort_Building`` adds up after those of the zones (its program calling manager
is after theirs, and the calling managers of the same calling point run in the order of the IDF). The percentages of
Method A, and the acceptable deviations of Annex E (Table E.1), divide them by the occupied hours, the outputs
``Occupied Hours_<zone>``.

The range can also be constant (``long_term_range``, finding C2-1 of the review of accim 1.2.0): the setpoints of the
ACCIS measure how well the control keeps its own band (with comfort mode 3, the static setpoints, the custom model or
the minimum and maximum of the setpoints, they are not those of a standard), so two models with different comfort
standards are not compared with them. ``long_term_range=('en16798', category)`` takes the design values of the
operative temperature of EN 16798-1:2019, Table B.2, for the buildings with mechanical cooling (the minimum for heating
and the maximum for cooling of the category, :data:`accim.constants.EN16798_TABLE_B2`), as constant limits of all the
timesteps; ``('en16798', category, building_type)`` chooses the residential or the office buildings, whose heating
minimums differ in categories III and IV (:func:`long_term_limits`).

Method C (the PPD-weighted hours) needs the PMV, which the models of the ACCIS with temperature setpoints do not
calculate: it is not counted for them; the setpoints based on the PMV count it (``report_ppd_weighted_hours`` of
:func:`accim.sim.pmv_index.apply_pmv_index_setpoints`).
"""

import numbers
from typing import Any, Dict, List, Optional, Sequence, Tuple

from accim.constants import EN16798_TABLE_B2
from accim.sim.ems.erl import format_number

__all__ = [
    'BUILDING',
    'BUILDING_PROGRAM',
    'LONG_TERM_RANGES',
    'OUTPUTS',
    'PROGRAM_PREFIX',
    'building_lines',
    'has_long_term_discomfort',
    'long_term_limits',
    'long_term_variable',
    'model_long_term_limits',
    'output_names',
    'set_long_term_discomfort_code',
    'zone_lines',
]

#: The program of the long-term discomfort of each zone is this prefix and the name of the zone
PROGRAM_PREFIX = 'CountLongTermDiscomfort_'
#: The suffix of the variables and outputs of the building
BUILDING = 'Building'
#: The program of the sums of the zones
BUILDING_PROGRAM = f'{PROGRAM_PREFIX}{BUILDING}'
#: The EMS outputs of each zone and of the building, ``<output>_<zone>`` and ``<output>_Building``:
#: output -> (EMS variable, ``<variable>_<zone>``, units); in the order of :func:`zone_lines`
OUTPUTS = {
    'Hours Above Upper Limit': ('HoursAboveUpperLimit', 'H'),
    'Hours Below Lower Limit': ('HoursBelowLowerLimit', 'H'),
    'Degree Hours Above Upper Limit': ('DegreeHoursAboveUpperLimit', 'Kh'),
    'Degree Hours Below Lower Limit': ('DegreeHoursBelowLowerLimit', 'Kh'),
}
_RUN_PREFIX = 'run '
#: The constant ranges of ``long_term_range``: 'en16798', the design values of EN 16798-1:2019, Table B.2
LONG_TERM_RANGES = ('en16798',)
#: The categories of Table B.2 (I to IV) and its building types
_CATEGORIES = (1, 2, 3, 4)
_BUILDING_TYPES = tuple(dict.fromkeys(building_type for building_type, _ in EN16798_TABLE_B2))


def long_term_limits(long_term_range: Any) -> Optional[Tuple[float, float]]:
    """The constant lower and upper limits of the range of the long-term discomfort of a ``long_term_range``: None for
    the setpoints without the tolerance of the ACCIS (the default); ``('en16798', category)`` or ``('en16798',
    category, building_type)``, the minimum for heating and the maximum for cooling of the category (1 to 4, I to IV)
    of EN 16798-1:2019, Table B.2 (:data:`accim.constants.EN16798_TABLE_B2`): 21.0 and 25.5 °C (I), 20.0 and 26.0 °C
    (II), 18.0 (residential) or 19.0 (office) and 27.0 °C (III), and 16.0 (residential) or 18.0 (office) and 28.0 °C
    (IV). The building type ('residential' or 'office') is needed in categories III and IV.

    :raises ValueError: If the range is not valid.
    """
    if long_term_range is None:
        return None
    if isinstance(long_term_range, str) or not isinstance(long_term_range, (tuple, list)) or not (
            2 <= len(long_term_range) <= 3):
        raise ValueError(f"long_term_range must be None or ('en16798', category) or ('en16798', category, "
                         f"building_type), not {long_term_range!r}.")
    name, category = str(long_term_range[0]).strip().lower(), long_term_range[1]
    if name not in LONG_TERM_RANGES:
        raise ValueError(f'The range of long_term_range must be one of {list(LONG_TERM_RANGES)}, not '
                         f'{long_term_range[0]!r}.')
    if isinstance(category, bool) or not isinstance(category, numbers.Integral) or category not in _CATEGORIES:
        raise ValueError(f'The category of long_term_range must be 1, 2, 3 or 4 (I to IV of EN 16798-1, Table B.2), '
                         f'not {category!r}.')
    if len(long_term_range) == 3:
        building_type = str(long_term_range[2]).strip().lower()
        if building_type not in _BUILDING_TYPES:
            raise ValueError(f'The building type of long_term_range must be one of {list(_BUILDING_TYPES)}, not '
                             f'{long_term_range[2]!r}.')
        return EN16798_TABLE_B2[building_type, int(category)]
    values = {EN16798_TABLE_B2[building_type, int(category)] for building_type in _BUILDING_TYPES}
    if len(values) > 1:
        raise ValueError(f"The limits of category {category} of EN 16798-1, Table B.2, depend on the building type "
                         f"({', '.join(f'{t}: {EN16798_TABLE_B2[t, int(category)]}' for t in _BUILDING_TYPES)}): "
                         f"give long_term_range=('en16798', {category}, building_type).")
    return values.pop()


def long_term_variable(output: str, zone: str) -> str:
    """The EMS variable of an output of :data:`OUTPUTS` of a zone (or of the building, ``zone=BUILDING``):
    ``HoursAboveUpperLimit_<zone>``..."""
    return f'{OUTPUTS[output][0]}_{zone}'


def zone_lines(zone: str, limits: Optional[Tuple[float, float]] = None) -> List[str]:
    """The lines of the program CountLongTermDiscomfort_<zone>: the occupied hours and degree hours of the zone above
    the upper limit and below the lower limit of the range (Methods A and B of CEN/TR 16798-2:2019, Annex D).

    :param zone: The name of the zone in the EMS objects.
    :param limits: The constant lower and upper limits (°C, :func:`long_term_limits`); None (the default) for the
        setpoints without the tolerance of the ACCIS (AHSTnoTol and ACSTnoTol).
    """
    hot_h, cold_h, hot_kh, cold_kh = (long_term_variable(output, zone) for output in OUTPUTS)
    lower, upper = ('AHSTnoTol', 'ACSTnoTol') if limits is None else (format_number(value) for value in limits)
    return [
        f'if Occ_count_{zone} > 0',
        f'if {zone}_OpT > {upper}',
        f'set {hot_h} = 1*ZoneTimeStep',
        f'set {hot_kh} = ({zone}_OpT-{upper})*ZoneTimeStep',
        'else',
        f'set {hot_h} = 0',
        f'set {hot_kh} = 0',
        'endif',
        f'if {zone}_OpT < {lower}',
        f'set {cold_h} = 1*ZoneTimeStep',
        f'set {cold_kh} = ({lower}-{zone}_OpT)*ZoneTimeStep',
        'else',
        f'set {cold_h} = 0',
        f'set {cold_kh} = 0',
        'endif',
        'else',
        f'set {hot_h} = 0',
        f'set {cold_h} = 0',
        f'set {hot_kh} = 0',
        f'set {cold_kh} = 0',
        'endif',
    ]


def building_lines(zones: Sequence[str]) -> List[str]:
    """The lines of the program CountLongTermDiscomfort_Building: the sums of the outputs of the zones (one zone in
    each line)."""
    lines = []
    for output in OUTPUTS:
        total = long_term_variable(output, BUILDING)
        lines.append(f'set {total} = 0')
        lines += [f'set {total} = {total}+{long_term_variable(output, zone)}' for zone in zones]
    return lines


def output_names(zones: Sequence[str]) -> List[str]:
    """The names of the EMS outputs of some zones and of the building."""
    return [f'{output}_{zone}' for zone in list(zones) + [BUILDING] for output in OUTPUTS]


def model_long_term_limits(idf) -> Dict[str, Optional[Tuple[float, float]]]:
    """The range of the long-term discomfort of each zone of a model, as its program CountLongTermDiscomfort_<zone>
    writes it: ``{zone: (lower, upper)}`` with constant limits (``long_term_range``), or ``{zone: None}`` with the
    setpoints without the tolerance."""
    limits: Dict[str, Optional[Tuple[float, float]]] = {}
    for program in idf.idfobjects['EnergyManagementSystem:Program']:
        name = str(program.Name)
        if not name.upper().startswith(PROGRAM_PREFIX.upper()) or name.upper() == BUILDING_PROGRAM.upper():
            continue
        zone = name[len(PROGRAM_PREFIX):]
        lines = [str(line).strip() for line in program.fieldvalues[2:]]
        upper = next((line.split('>', 1)[1].strip() for line in lines if line.startswith(f'if {zone}_OpT >')), None)
        lower = next((line.split('<', 1)[1].strip() for line in lines if line.startswith(f'if {zone}_OpT <')), None)
        try:
            limits[zone] = (float(lower), float(upper))
        except (TypeError, ValueError):
            limits[zone] = None
    return limits


def has_long_term_discomfort(idf) -> bool:
    """True if the model has the long-term discomfort of :func:`set_long_term_discomfort_code`."""
    return any(str(p.Name).upper().startswith(PROGRAM_PREFIX.upper())
               for p in idf.idfobjects['EnergyManagementSystem:Program'])


def set_long_term_discomfort_code(idf, frequencies: Sequence[str] = (),
                                  long_term_range: Any = None) -> Dict[str, List[str]]:
    """Add to a model with the ACCIS (of accim 1.0.0 or later) the long-term discomfort of the occupied hours of each
    zone and of the building (``report_long_term_discomfort``): the programs CountLongTermDiscomfort_<zone> (run by
    RunACCIS_<zone> after CountHoursNoApp_<zone>) and CountLongTermDiscomfort_Building (with its program calling
    manager, after those of the model), their EMS global variables and the EMS output variables of :data:`OUTPUTS`
    (summed), with Output:Variable objects at the frequencies given.

    :param frequencies: The reporting frequencies of their Output:Variable objects ('Hourly'...); none by default (the
        standard outputs of AddAccis add those of all the EMS output variables).
    :param long_term_range: The range: None (the default) for the setpoints without the tolerance of the ACCIS, or
        ``('en16798', category)`` or ``('en16798', category, building_type)`` for the constant limits of EN
        16798-1:2019, Table B.2 (:func:`long_term_limits`).
    :return: The names of the EMS outputs of each zone and of the building, ``{zone: [output...], 'Building': [...]}``.
    :raises ValueError: If the model has no ACCIS of accim 1.0.0 or later, has them already, has a zone named
        Building in its EMS objects, or the range is not valid.
    """
    from accim.sim.ems.inputs import input_programs
    from accim.sim.ems.programs import add_program
    from accim.sim.ems.setpoint_limits import _declared, _insert_run_line

    limits = long_term_limits(long_term_range)
    zones = list(input_programs(idf))
    if not zones:
        raise ValueError('The long-term discomfort needs the ACCIS of accim 1.0.0 or later (the programs '
                         'SetInputData_<zone>): add it with this version of accim to the model without it.')
    if has_long_term_discomfort(idf):
        raise ValueError('The model already has the long-term discomfort (programs CountLongTermDiscomfort_<zone>).')
    if any(zone.upper() == BUILDING.upper() for zone in zones):
        raise ValueError(f'A zone of the model is named {BUILDING} in the EMS objects, as the outputs of the '
                         f'building of the long-term discomfort.')
    declared = _declared(idf)
    names: Dict[str, List[str]] = {}
    for zone in zones + [BUILDING]:
        if zone == BUILDING:
            add_program(idf, BUILDING_PROGRAM, building_lines(zones))
            idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=BUILDING_PROGRAM,
                             EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor',
                             Program_Name_1=BUILDING_PROGRAM)
        else:
            add_program(idf, f'{PROGRAM_PREFIX}{zone}', zone_lines(zone, limits))
            _insert_run_line(idf, zone, f'{_RUN_PREFIX}{PROGRAM_PREFIX}{zone}', f'run CountHoursNoApp_{zone}')
        variables = [long_term_variable(output, zone) for output in OUTPUTS]
        new = [variable for variable in variables if variable.upper() not in declared]
        if new:
            idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                             **{f'Erl_Variable_{n}_Name': variable for n, variable in enumerate(new, start=1)})
        names[zone] = []
        for output, variable in zip(OUTPUTS, variables):
            name = f'{output}_{zone}'
            idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=variable,
                             Type_of_Data_in_Variable='Summed', Update_Frequency='ZoneTimestep',
                             Units=OUTPUTS[output][1])
            for frequency in frequencies:
                idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name,
                                 Reporting_Frequency=frequency, Schedule_Name='')
            names[zone].append(name)
    return names
