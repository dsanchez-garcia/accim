# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The fallback of the EMS for the setpoints of comfort standard 24, INT Sun2026 SET (way (a) of proposal A6 of
``notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md``, the P2 entry of ``TODO.md`` of task F1): a feedback of the setpoints of
the operative temperature on the SET of the previous timestep that EnergyPlus calculates (the Pierce model of the People
object of each zone), which the EMS of EnergyPlus runs, and so the backend of the Python API without the hook
(:func:`accim.sim.comfort_hooks.apply_sun2026_setpoints` with ``ems_fallback=True``).

In each timestep, the program ``SetSETFeedback_<zone>``, which ``RunACCIS_<zone>`` runs right before
``ApplyHookSetpoints_<zone>`` (:mod:`accim.sim.ems.hook_setpoints`), does nothing if the hook has given the setpoints of
the zone (``HookSetpoints_<zone>`` is 1: the hook runs before the EMS programs, so the backend of the API with the hook
gives its setpoints, those of the inversion of the SET of pythermalcomfort). Otherwise, if EnergyPlus has calculated the
SET of the zone in the previous timestep (``SET_Pierce_<zone>``, the output *Zone Thermal Comfort Pierce Model Standard
Effective Temperature* of its People object, above 0), it estimates each setpoint as the operative temperature whose SET
would be the setpoint of the SET if the SET grew by ``Slope`` kelvin per kelvin of operative temperature, with the
other conditions of the zone::

    EstimateAHST = <zone>_OpT + (SET heating setpoint − SET_Pierce_<zone>)/Slope
    EstimateACST = <zone>_OpT + (SET cooling setpoint − SET_Pierce_<zone>)/Slope

with ``<zone>_OpT`` the operative temperature of the zone (the sensor of the ACCIS), both of the previous timestep, and
moves each setpoint (``HookAHST_<zone>`` and ``HookACST_<zone>``) a fraction ``Relaxation`` of the way to its estimate
(in the first timestep of each environment with the SET, to the estimate itself), bounded to ``temperature_range``; it
sets ``HookSetpoints_<zone>`` to 1, so that ``ApplyHookSetpoints_<zone>`` gives them to the ACCIS as those of a hook.
The estimates do not depend on the setpoints, so the setpoints do not drift while the zone floats between them. While
the thermostat holds the zone at a setpoint, the error of its SET is multiplied by 1 − Relaxation·s/Slope in each
timestep, s being the growth of the SET per kelvin of the operative temperature that the thermostat changes (with the
air temperature, the mean radiant temperature of the previous timestep), so the setpoint converges to that of the SET if
Relaxation·s/Slope < 2, without overshoot if it is below 1. Measured with pythermalcomfort on 2026-11-18 (30 to 90 % of
relative humidity, 0.1 to 1.2 m/s, 1.0 to 1.2 met, 0.5 to 1.0 clo, operative temperatures of 16 to 32 °C and mean
radiant temperatures 0 to 4 K above them), s is 0.66 to 4.0, 1.27 in the median (0.95 with still air, 1.6 with 1.2
m/s, 4.0 at 32 °C, 90 % and 1.2 m/s): with the defaults, Relaxation 0.5 (:data:`DEFAULT_RELAXATION`) and Slope 1.0
(:data:`DEFAULT_SLOPE`, about that with still air), it converges in all of them. The proposal (a gain of about 0.8 on
the setpoint of the previous timestep) did not converge above s = 2.5 and drifted while the zone floated; the first
version of this module, a gain of 0.5 on the estimate itself, put the setpoint far from the zone at half its distance
(4.2 K above that of the hook, the heating setpoints of a week of July of the sample model).

The setpoint near which the zone is converges to that of the SET; the other one is an extrapolation, as good as the
slope: measured on 2026-11-18 with the sample model in Seville (EnergyPlus 25.1, the defaults, the People objects of the
sample model, 1.06 met, 0.137 m/s, 0.5 clo in July and 1.0 clo in January), against the setpoints of the hook (without
the tolerance, every timestep of a week): in July, the cooling setpoints 0.01 to 0.02 K above them on average (0.26 K
in absolute value, 0.62 K at the 95th percentile) and the heating setpoints 0.40 to 0.42 K above; in January, with the
zones floating far from both setpoints (the SET grows by about 0.65 K per K with 1.0 clo), the cooling setpoints 0.88 K
below and the heating setpoints 2.2 K above; the operative temperatures of the zones 0.21 to 0.22 K below those of the
hook in July (2.6 K at most, in the first timesteps of the week, and 0.45 and 0.51 K after its first day) and 0.01 to
0.02 K below them in January; and the occupied hours within the band 33.5 and 35.3 h against 28.5 and 34.3 h in July,
and 60 and 52 h against 60 and 57.5 h in January.

It also sets the outputs of the hook of comfort standard 24 from the SET of EnergyPlus: ``SET_<zone>`` (the SET of the
previous timestep), ``TSV_causal_<zone>`` (0.11·SET − 2.6), ``HoursInCausalBand_<zone>`` (the length of the timestep if
the zone is occupied, ``Occ_count_<zone>``, and its SET is within the band) and ``SETsaturated_<zone>`` (the length of
the timestep if a setpoint is at a limit of ``temperature_range``). Without the SET of the previous timestep (in the
first timestep of each environment), the setpoints are those of the comfort standard of the zone, as without the hook.
The SET is that of the Pierce model of EnergyPlus, not that of pythermalcomfort of the hook: near 1 met, about 0.05 to
0.13 K above it (E-F1, ``notes/decisions.md``), more at higher activity levels.
"""

import os
import re
from typing import Dict, List, Sequence, Tuple, Union

__all__ = ['DEFAULT_RELAXATION', 'DEFAULT_SLOPE', 'PIERCE_SENSOR_PREFIX', 'PROGRAM_PREFIX', 'feedback_zones',
           'feedback_zones_of_file', 'program_lines', 'set_set_feedback_code', 'zones_needing_a_hook']

#: The program of each zone of the feedback is this prefix and the name of the zone
PROGRAM_PREFIX = 'SetSETFeedback_'
#: The EMS sensor of each zone with the SET of the Pierce model of its People object is this prefix, '_' and the zone
PIERCE_SENSOR_PREFIX = 'SET_Pierce'
#: The fraction of the way to its estimate that each setpoint goes in each timestep (see the module)
DEFAULT_RELAXATION = 0.5
#: The slope of the SET with the operative temperature of the estimates of the setpoints, K/K (see the module)
DEFAULT_SLOPE = 1.0
#: The output of EnergyPlus of the SET of the Pierce model
_PIERCE_SET_OUTPUT = 'Zone Thermal Comfort Pierce Model Standard Effective Temperature'
_RUN_PREFIX = 'run '


def _number(value: float) -> str:
    """A number in an Erl line (as Python writes it)."""
    return repr(float(value))


def program_lines(zone: str, heating_set: float, cooling_set: float, band: Tuple[float, float], relaxation: float,
                  slope: float, temperature_range: Tuple[float, float], tsv_slope: float,
                  tsv_intercept: float) -> List[str]:
    """The lines of the program SetSETFeedback_<zone> (see the module).

    :param heating_set: The heating setpoint of the SET (°C).
    :param cooling_set: The cooling setpoint of the SET (°C).
    :param band: The SET of the limits of the band of TSV of the hours within it (°C).
    :param relaxation: The fraction of the way to the estimate that each setpoint goes in each timestep.
    :param slope: The slope of the SET with the operative temperature of the estimates (K/K).
    :param temperature_range: The range of the setpoints of the operative temperature (°C).
    :param tsv_slope: The slope of the causal TSV with the SET; ``tsv_intercept``, its intercept.
    """
    from accim.sim.ems.hook_setpoints import zone_variables

    flag, heating, cooling = zone_variables(zone)
    pierce = f'{PIERCE_SENSOR_PREFIX}_{zone}'
    saturated = f'SETsaturated_{zone}'
    hours = f'HoursInCausalBand_{zone}'
    low, high = (_number(value) for value in temperature_range)
    lines = [f'if {flag} == 0',
             f'if {pierce} > 0',
             f'set EstimateAHST = {zone}_OpT+({_number(heating_set)}-{pierce})/{_number(slope)}',
             f'set EstimateACST = {zone}_OpT+({_number(cooling_set)}-{pierce})/{_number(slope)}',
             # The first timestep of the environment with the SET (InitHookSetpoints sets them to 0): the estimates
             f'if {heating} == 0 && {cooling} == 0',
             f'set {heating} = EstimateAHST',
             f'set {cooling} = EstimateACST',
             'else',
             f'set {heating} = {heating}+{_number(relaxation)}*(EstimateAHST-{heating})',
             f'set {cooling} = {cooling}+{_number(relaxation)}*(EstimateACST-{cooling})',
             'endif',
             f'set {saturated} = 0']
    for variable in (heating, cooling):
        lines += [f'if {variable} < {low}', f'set {variable} = {low}', f'set {saturated} = ZoneTimeStep',
                  f'elseif {variable} > {high}', f'set {variable} = {high}', f'set {saturated} = ZoneTimeStep',
                  'endif']
    lines += [f'set {flag} = 1',
              f'set SET_{zone} = {pierce}',
              f'set TSV_causal_{zone} = {_number(tsv_slope)}*{pierce}+({_number(tsv_intercept)})',
              f'if Occ_count_{zone} > 0 && {pierce} >= {_number(band[0])} && {pierce} <= {_number(band[1])}',
              f'set {hours} = ZoneTimeStep',
              'else',
              f'set {hours} = 0',
              'endif',
              'else',
              f'set {saturated} = 0',
              f'set {hours} = 0',
              'endif',
              'endif']
    return lines


def feedback_zones(idf) -> List[str]:
    """The zones of a model with the feedback (the program SetSETFeedback_<zone>)."""
    prefix = PROGRAM_PREFIX.upper()
    return [str(p.Name)[len(PROGRAM_PREFIX):] for p in idf.idfobjects['EnergyManagementSystem:Program']
            if str(p.Name).upper().startswith(prefix)]


#: The programs SetSETFeedback_<zone> in the text of an IDF file
_PROGRAM_IN_FILE = re.compile(rf'^\s*EnergyManagementSystem:Program\s*,\s*{re.escape(PROGRAM_PREFIX)}([^,;!\s]+)\s*,',
                              re.IGNORECASE | re.MULTILINE)


def feedback_zones_of_file(path: Union[str, os.PathLike]) -> List[str]:
    """The zones with the feedback of the model of an IDF file, read from its text, without eppy (as
    :func:`accim.sim.ems.hook_setpoints.hook_zones_of_file`); none if the file cannot be read."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
    except OSError:
        return []
    return _PROGRAM_IN_FILE.findall(text)


def set_set_feedback_code(idf, people: Dict[str, str], heating_set: float, cooling_set: float,
                          band: Tuple[float, float], relaxation: float, slope: float,
                          temperature_range: Tuple[float, float], tsv_slope: float, tsv_intercept: float) -> None:
    """Add the feedback to the zones of a model prepared for the setpoints of the SET of comfort standard 24 (with the
    objects of the hook, :func:`accim.sim.comfort_hooks.apply_sun2026_setpoints`, and the Pierce model in its People
    objects): the sensor of the SET of the Pierce model of each zone, its program SetSETFeedback_<zone>, and the line
    that runs it in RunACCIS_<zone> right after SetAST, before ApplyHookSetpoints_<zone>.

    :param people: The name of the People object of each zone (the key of its outputs), by the name of the zone in the
        EMS objects.
    :param heating_set: The setpoints of the SET, the band, the gain, the range and the line of the causal TSV: see
        :func:`program_lines`.
    """
    from accim.sim.ems.programs import add_program, set_program_lines
    from accim.sim.ems.setpoint_limits import _insert_run_line

    for zone, key in people.items():
        sensor = f'{PIERCE_SENSOR_PREFIX}_{zone}'
        if idf.getobject('EnergyManagementSystem:Sensor', sensor) is None:
            idf.newidfobject('EnergyManagementSystem:Sensor', Name=sensor,
                             OutputVariable_or_OutputMeter_Index_Key_Name=key,
                             OutputVariable_or_OutputMeter_Name=_PIERCE_SET_OUTPUT)
        name = f'{PROGRAM_PREFIX}{zone}'
        lines = program_lines(zone, heating_set, cooling_set, band, relaxation, slope, temperature_range, tsv_slope,
                              tsv_intercept)
        existing = idf.getobject('EnergyManagementSystem:Program', name)
        if existing is None:
            add_program(idf, name, lines)
        else:
            set_program_lines(existing, lines)
        _insert_run_line(idf, zone, f'{_RUN_PREFIX}{name}', 'run SetAST')


def zones_needing_a_hook(hook_zones: Sequence[str], feedback: Sequence[str]) -> List[str]:
    """The zones prepared for a hook that need it: those without the feedback."""
    with_feedback = {zone.upper() for zone in feedback}
    return [zone for zone in hook_zones if zone.upper() not in with_feedback]
