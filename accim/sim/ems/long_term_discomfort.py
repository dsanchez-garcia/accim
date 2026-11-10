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

Method C (the PPD-weighted hours) needs the PMV, which the models of the ACCIS with temperature setpoints do not
calculate: it is not counted (see the TODO list of the repository).
"""

from typing import Dict, List, Sequence

__all__ = [
    'BUILDING',
    'BUILDING_PROGRAM',
    'OUTPUTS',
    'PROGRAM_PREFIX',
    'building_lines',
    'has_long_term_discomfort',
    'long_term_variable',
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


def long_term_variable(output: str, zone: str) -> str:
    """The EMS variable of an output of :data:`OUTPUTS` of a zone (or of the building, ``zone=BUILDING``):
    ``HoursAboveUpperLimit_<zone>``..."""
    return f'{OUTPUTS[output][0]}_{zone}'


def zone_lines(zone: str) -> List[str]:
    """The lines of the program CountLongTermDiscomfort_<zone>: the occupied hours and degree hours of the zone above
    the cooling setpoint and below the heating setpoint without the tolerance (Methods A and B of CEN/TR 16798-2:2019,
    Annex D)."""
    hot_h, cold_h, hot_kh, cold_kh = (long_term_variable(output, zone) for output in OUTPUTS)
    return [
        f'if Occ_count_{zone} > 0',
        f'if {zone}_OpT > ACSTnoTol',
        f'set {hot_h} = 1*ZoneTimeStep',
        f'set {hot_kh} = ({zone}_OpT-ACSTnoTol)*ZoneTimeStep',
        'else',
        f'set {hot_h} = 0',
        f'set {hot_kh} = 0',
        'endif',
        f'if {zone}_OpT < AHSTnoTol',
        f'set {cold_h} = 1*ZoneTimeStep',
        f'set {cold_kh} = (AHSTnoTol-{zone}_OpT)*ZoneTimeStep',
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


def has_long_term_discomfort(idf) -> bool:
    """True if the model has the long-term discomfort of :func:`set_long_term_discomfort_code`."""
    return any(str(p.Name).upper().startswith(PROGRAM_PREFIX.upper())
               for p in idf.idfobjects['EnergyManagementSystem:Program'])


def set_long_term_discomfort_code(idf, frequencies: Sequence[str] = ()) -> Dict[str, List[str]]:
    """Add to a model with the ACCIS (of accim 1.0.0 or later) the long-term discomfort of the occupied hours of each
    zone and of the building (``report_long_term_discomfort``): the programs CountLongTermDiscomfort_<zone> (run by
    RunACCIS_<zone> after CountHoursNoApp_<zone>) and CountLongTermDiscomfort_Building (with its program calling
    manager, after those of the model), their EMS global variables and the EMS output variables of :data:`OUTPUTS`
    (summed), with Output:Variable objects at the frequencies given.

    :param frequencies: The reporting frequencies of their Output:Variable objects ('Hourly'...); none by default (the
        standard outputs of AddAccis add those of all the EMS output variables).
    :return: The names of the EMS outputs of each zone and of the building, ``{zone: [output...], 'Building': [...]}``.
    :raises ValueError: If the model has no ACCIS of accim 1.0.0 or later, has them already, or has a zone named
        Building in its EMS objects.
    """
    from accim.sim.ems.inputs import input_programs
    from accim.sim.ems.programs import add_program
    from accim.sim.ems.setpoint_limits import _declared, _insert_run_line

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
            add_program(idf, f'{PROGRAM_PREFIX}{zone}', zone_lines(zone))
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
