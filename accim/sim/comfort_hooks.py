# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Setpoints that the EMS cannot calculate, which Python sets in the backend of the Python API of EnergyPlus
(:mod:`accim.sim.energyplus_api`): the setpoints of the operative temperature of the adaptive thermal heat balance
(ATHB), proposal A4.

The ATHB framework (Schweiker & Wagner, 2015, Building and Environment 94, 252–262; Schweiker, 2022, Indoor Air 32,
e13018) adds the physiological, behavioural and psychological adaptation to the heat balance model of Fanger. accim
uses the implementation of pythermalcomfort (``pythermalcomfort.models.pmv_athb``, version 4.8.1, whose coefficients
are those of the models "Trm * METad" of the clothing and "Lad * Trm * METad" of the thermal sensation of Schweiker,
2022), with the running mean outdoor temperature trm (°C) and the metabolic rate met (met):

- physiological adaptation: met_adapted = met − 0.234·trm/58.2 (:func:`athb_met`);
- behavioural adaptation: clo_adapted = 10^(−0.17168 − 0.000485·trm + 0.08176·met_adapted
  − 0.00527·trm·met_adapted) (:func:`athb_clo`), unless the clothing insulation is given;
- the PMV of Fanger with met_adapted and clo_adapted (and no external work), the transfer coefficient
  ts = 0.303·exp(−0.036·met_adapted·58.15) + 0.028, and the thermal load L_adapted = PMV/ts;
- psychological adaptation: ATHB_PMV = 1.484 + 0.0276·L − 0.9602·met_adapted − 0.0342·trm + 0.0002264·L·trm
  + 0.018696·met_adapted·trm − 0.0002909·L·met_adapted·trm, rounded to 3 decimals.

The EMS cannot calculate it: it needs the whole PMV (with the iteration of the temperature of the clothing surface)
with the adapted clothing and metabolic rate in each timestep, and EnergyPlus only calculates the PMV with the
parameters of the People objects. :func:`apply_athb_setpoints` prepares a model with the ACCIS and returns an
:class:`AthbSetpointHook`, which the backend of the Python API runs at the beginning of each timestep before the EMS
programs (``run_ep(backend='api', hooks=[hook])``, or ``run_simulation(..., before_programs=[hook])``): for each zone,
it finds by bisection the operative temperatures whose ATHB_PMV (with the air temperature and the mean radiant
temperature equal to them, and the relative humidity of the zone) is the heating and the cooling setpoints of the
ATHB, and gives them to the ACCIS instead of the adaptive setpoints (:mod:`accim.sim.ems.hook_setpoints`: the program
``ApplyHookSetpoints_<zone>``, which ``RunACCIS_<zone>`` runs right after SetAST, takes them as the limits of the
comfort band, so that the thermostats get them with the tolerance of the setpoints of the zone, and the floor and
ceiling of the setpoints, the hour counters and the outputs of the setpoints of the zone follow them); it also reports
the ATHB_PMV of each zone (``ATHB_PMV_<zone>``, from its mean air and mean radiant temperatures and relative humidity)
and the adapted clothing and metabolic rate (``ATHB_clo_<zone>`` and ``ATHB_met_<zone>``). As the other sensors of the
EMS at the beginning of the timestep, those of the zone are those of the previous timestep, and trm is the running mean
outdoor temperature of CEN 15251 of EnergyPlus (the sensor ``RMOT`` of the ACCIS, α = 0.8, as EN 16798-1).
pythermalcomfort is optional (``pip install accim[comfort]``, Python 3.11 or later); the EMS backend cannot run the hook
(``run_ep(backend='ems', hooks=...)`` raises ``NotImplementedError``), and without it the setpoints are those of the
ACCIS.

The setpoints of the standard effective temperature (SET), proposal A6, work in the same way
(:func:`apply_set_setpoints`, :class:`SetSetpointHook`): the operative temperatures whose SET of pythermalcomfort
(``pythermalcomfort.models.set_tmp``, :func:`standard_effective_temperature`) is the heating and the cooling setpoints
of the SET. With the metabolic rate, the clothing insulation and the air speed of the hook, they depend on the relative
humidity of the zone only, so the hook can calculate them for each relative humidity when it is made and interpolate
them (``method='table'``, the default, which does not calculate the SET in the callbacks of EnergyPlus), or calculate
them by bisection in each timestep and report the SET of each zone (``method='bisection'``). ``set_tmp`` is compiled by
numba: in the development environment of accim 1.2.0 (Python 3.14.3, numba 0.68.1, pythermalcomfort 4.8.1, EnergyPlus
25.1), its first call in a process stopped it with an access violation when the library of the API of EnergyPlus had
been loaded in the process before (in a callback of the API, or before the simulation), and worked when it was made
before loading that library, after which it also works in the callbacks; the review of 1.2.0 ran it inside the
callbacks with Python 3.12 and numba 0.68.1 without such a call. So ``run_simulation`` calls the method ``prepare`` of
the hooks in the process of the simulation before it loads the library (:meth:`SetSetpointHook.prepare`). Those of the
predicted percentage of dissatisfied (PPD) of the categories of ISO 7730:2025 (Table A.1: PPD < 6, 10, 15 and 25 %) are
those of the PMV of :func:`accim.sim.apmv.apply_pmv_setpoints` (−0.2 and 0.2, −0.5 and 0.5, −0.7 and 0.7, and −1.0 and
1.0), which the EMS controls.
"""

import math
import numbers
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    'ATHB_TEMPERATURE_RANGE',
    'AthbSetpointHook',
    'SET_METHODS',
    'SET_TEMPERATURE_RANGE',
    'SetSetpointHook',
    'apply_athb_setpoints',
    'apply_set_setpoints',
    'athb_clo',
    'athb_met',
    'athb_pmv',
    'set_of_results',
    'set_zone_outputs',
    'standard_effective_temperature',
    'zone_outputs',
]

#: The range of the operative temperature (°C) within which the hook looks for the setpoints of the ATHB: the air
#: temperature of 10 to 30 °C within which ISO 7730:2025 (section 4) uses the PMV (the air temperature and the mean
#: radiant temperature are both the operative temperature); the setpoints out of it are its limits.
ATHB_TEMPERATURE_RANGE = (10.0, 30.0)
#: The calling point at which the hook sets the setpoints, that of the programs of the ACCIS
_CALLING_POINT = 'BEGINTIMESTEPBEFOREPREDICTOR'
#: The EMS sensors that apply_athb_setpoints adds to each zone: prefix -> output variable of EnergyPlus
_SENSORS = {
    'ATHB_MAT': 'Zone Mean Air Temperature',
    'ATHB_MRT': 'Zone Mean Radiant Temperature',
    'ATHB_RH': 'Zone Air Relative Humidity',
}
#: The EMS output variables of each zone: prefix (of the global variable and the output) -> units
_OUTPUTS = {'ATHB_PMV': '', 'ATHB_clo': 'clo', 'ATHB_met': 'met'}
#: The range of the operative temperature (°C) within which the hook of the SET looks for its setpoints: the air and
#: mean radiant temperatures of 10 to 40 °C, the limits of the inputs of the SET of pythermalcomfort
#: (``pythermalcomfort.models.set_tmp``, 4.8.1); the setpoints out of it are its limits.
SET_TEMPERATURE_RANGE = (10.0, 40.0)
#: The methods of the setpoints of the SET (:class:`SetSetpointHook`): 'table' (the setpoints of each relative humidity,
#: calculated when the hook is made and interpolated) and 'bisection' (calculated in each timestep, with the output of
#: the SET of each zone)
SET_METHODS = ('table', 'bisection')
#: The EMS sensors that apply_set_setpoints adds to each zone: its relative humidity (the setpoints of the SET depend on
#: it) and its mean air and mean radiant temperatures (the SET of the zone, with method='bisection')
_SET_SENSORS = {
    'SET_MAT': 'Zone Mean Air Temperature',
    'SET_MRT': 'Zone Mean Radiant Temperature',
    'SET_RH': 'Zone Air Relative Humidity',
}
#: The EMS output variables of each zone with method='bisection': prefix -> units
_SET_OUTPUTS: Dict[str, str] = {'SET': 'C'}
#: The output variables of EnergyPlus of each zone that apply_set_setpoints requests, from which set_of_results
#: calculates the SET of the zones after the simulation
_SET_ZONE_VARIABLES = tuple(_SET_SENSORS.values())
#: The relative humidities (%) of the table of the setpoints of the SET of each hook
_SET_HUMIDITIES = tuple(float(value) for value in range(0, 101))


def athb_met(met: float, t_running_mean: float) -> float:
    """The metabolic rate with the physiological adaptation of the ATHB (met): met − 0.234·trm/58.2
    (``pythermalcomfort.models.pmv_athb``, 4.8.1; Schweiker, 2022, Table 1, MET = 48.5 − 0.23·Trm W/m²).

    :param met: The metabolic rate (met).
    :param t_running_mean: The running mean outdoor temperature (°C).
    """
    return float(met) - 0.234 * float(t_running_mean) / 58.2


def athb_clo(met: float, t_running_mean: float) -> float:
    """The clothing insulation with the behavioural adaptation of the ATHB (clo):
    10^(−0.17168 − 0.000485·trm + 0.08176·met_adapted − 0.00527·trm·met_adapted), with the adapted metabolic rate of
    :func:`athb_met` (``pythermalcomfort.models.pmv_athb``, 4.8.1; the model "Trm * METad" of Schweiker, 2022, Table 2).

    :param met: The metabolic rate (met), without the adaptation.
    :param t_running_mean: The running mean outdoor temperature (°C).
    """
    met_adapted = athb_met(met, t_running_mean)
    trm = float(t_running_mean)
    return 10 ** (-0.17168 - 0.000485 * trm + 0.08176 * met_adapted - 0.00527 * trm * met_adapted)


def _pmv_athb():
    try:
        from pythermalcomfort.models import pmv_athb
    except ImportError as error:
        raise ImportError('The setpoints of the ATHB need pythermalcomfort (4.8 or later, Python 3.11 or later): '
                          'install it with pip install accim[comfort] (or pip install pythermalcomfort).') from error
    return pmv_athb


def athb_pmv(air_temperature, mean_radiant_temperature, air_speed, relative_humidity, met, t_running_mean,
             clo: Any = 'adaptive'):
    """The ATHB_PMV of pythermalcomfort (``pythermalcomfort.models.pmv_athb``, see the module).

    :param air_temperature: The air temperature (°C), a number or an array.
    :param mean_radiant_temperature: The mean radiant temperature (°C).
    :param air_speed: The relative air speed (m/s).
    :param relative_humidity: The relative humidity (%).
    :param met: The metabolic rate (met), without the adaptation.
    :param t_running_mean: The running mean outdoor temperature (°C).
    :param clo: 'adaptive' for the clothing insulation of the behavioural adaptation, or the clothing insulation
        (clo), without it.
    :return: The ATHB_PMV (a number, or an array for arrays).
    :raises ImportError: If pythermalcomfort is not installed.
    """
    pmv_athb = _pmv_athb()
    result = pmv_athb(tdb=air_temperature, tr=mean_radiant_temperature, vr=air_speed, rh=relative_humidity, met=met,
                      t_running_mean=t_running_mean, clo=False if clo == 'adaptive' else clo).athb_pmv
    try:
        return float(result)
    except TypeError:
        return result


def _check_number(name: str, value: Any, low: Optional[float] = None, high: Optional[float] = None) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real) or not math.isfinite(value):
        raise ValueError(f'{name} must be a number, not {value!r}.')
    if (low is not None and value < low) or (high is not None and value > high):
        raise ValueError(f'{name} must be between {low} and {high}, not {value!r}.')
    return float(value)


def _check_before_programs(hook, controller) -> None:
    """Stop if a hook of the setpoints runs after the EMS programs: the program ApplyHookSetpoints_<zone> reads its
    setpoints in the programs of the timestep (:mod:`accim.sim.ems.hook_setpoints`)."""
    if any(item is hook for item in getattr(controller, 'after_programs', ())):
        raise RuntimeError(f'{type(hook).__name__} must run before the EMS programs: pass it as before_programs of '
                           f"run_simulation (run_ep(backend='api', hooks=[hook]) does it), since the program "
                           f'ApplyHookSetpoints_<zone> gives its setpoints to the ACCIS.')


def _give_setpoints(controller, zone: str, heating: float, cooling: float) -> None:
    """Give the setpoints of a hook to the ACCIS of a zone (the global variables of
    :mod:`accim.sim.ems.hook_setpoints`, which the program ApplyHookSetpoints_<zone> reads)."""
    from accim.sim.ems.hook_setpoints import zone_variables

    flag, heating_variable, cooling_variable = zone_variables(zone)
    controller.set(heating_variable, heating)
    controller.set(cooling_variable, cooling)
    controller.set(flag, 1.0)


def _bisect(index, targets: Tuple[float, float], temperature_range: Tuple[float, float], tolerance: float,
            max_iterations: int) -> Tuple[float, float]:
    """The operative temperatures at which an index that grows with them is each of two targets, by one bisection of
    both: ``index(temperatures)`` gives the index of an array of two temperatures. The targets out of the range give
    its limits.

    :return: The two temperatures, in the order of the targets.
    """
    import numpy as np

    targets = np.asarray(targets, dtype=float)
    low = np.full(2, temperature_range[0])
    high = np.full(2, temperature_range[1])
    below_range = index(low) >= targets
    above_range = index(high) <= targets
    for _ in range(max_iterations):
        if float(np.max(high - low)) <= tolerance:
            break
        middle = (low + high) / 2
        higher = index(middle) < targets
        low = np.where(higher, middle, low)
        high = np.where(higher, high, middle)
    result = np.where(below_range, temperature_range[0], np.where(above_range, temperature_range[1], (low + high) / 2))
    return float(result[0]), float(result[1])


class AthbSetpointHook:
    """The hook of the backend of the Python API of EnergyPlus that sets the setpoints of the operative temperature of
    the ATHB in the zones of a model with the ACCIS (see the module); :func:`apply_athb_setpoints` prepares the model
    and returns it.

    It runs at the beginning of each timestep before the EMS programs (``before_programs`` of
    :func:`accim.sim.energyplus_api.run_simulation`; :func:`accim.run.run_ep` passes it so, since
    :attr:`runs_before_programs` is True): for each zone, it reads the running mean outdoor temperature (``RMOT``) and
    the mean air temperature, mean radiant temperature and relative humidity of the zone (the sensors
    ``ATHB_MAT_<zone>``, ``ATHB_MRT_<zone>`` and ``ATHB_RH_<zone>``), finds by bisection the operative temperatures
    whose ATHB_PMV is ``athb_heating_setpoint`` and ``athb_cooling_setpoint`` (the ATHB_PMV grows with the operative
    temperature), within ``temperature_range`` and to ``tolerance_k``, gives them to the ACCIS as the limits of the
    comfort band (the variables of :mod:`accim.sim.ems.hook_setpoints`: the program ``ApplyHookSetpoints_<zone>``, run
    right after SetAST, gives the thermostats these setpoints with the tolerance of the setpoints of the zone, and the
    floor and ceiling of the setpoints, the hour counters and the outputs of the setpoints of the zone follow them) and
    sets the global variables ``ATHB_PMV_<zone>``, ``ATHB_clo_<zone>`` and ``ATHB_met_<zone>``, which EnergyPlus
    reports.

    :param zones: The zones, by their names in the EMS objects (``Block1_Zone1``...).
    :param athb_cooling_setpoint: The cooling setpoint of the ATHB_PMV.
    :param athb_heating_setpoint: The heating setpoint of the ATHB_PMV, lower than the cooling one.
    :param met: The metabolic rate of the occupants (met), without the adaptation.
    :param air_speed: The relative air speed (m/s).
    :param clo: 'adaptive' (the default) for the clothing insulation of the behavioural adaptation, or the clothing
        insulation (clo), without it.
    :param tolerance_k: The largest width of the interval of the bisection (K): the setpoint is its middle.
    :param max_iterations: The largest number of iterations of the bisection.
    :param temperature_range: The range of the operative temperature of the setpoints (°C,
        :data:`ATHB_TEMPERATURE_RANGE`).
    :ivar setpoints: The last setpoints of each zone, ``{zone: (heating, cooling)}``, without the tolerance.
    """

    #: The hook runs before the EMS programs (:func:`accim.run.run_ep` passes it as ``before_programs``)
    runs_before_programs = True

    def __init__(self, zones: Sequence[str], athb_cooling_setpoint: float = 0.5, athb_heating_setpoint: float = -0.5,
                 met: float = 1.1, air_speed: float = 0.1, clo: Any = 'adaptive', tolerance_k: float = 0.1,
                 max_iterations: int = 20, temperature_range: Tuple[float, float] = ATHB_TEMPERATURE_RANGE):
        self.zones = [str(zone) for zone in zones]
        if not self.zones:
            raise ValueError('zones must name at least one zone.')
        self.athb_cooling_setpoint = _check_number('athb_cooling_setpoint', athb_cooling_setpoint)
        self.athb_heating_setpoint = _check_number('athb_heating_setpoint', athb_heating_setpoint)
        if not self.athb_heating_setpoint < self.athb_cooling_setpoint:
            raise ValueError(f'athb_heating_setpoint ({athb_heating_setpoint}) must be lower than '
                             f'athb_cooling_setpoint ({athb_cooling_setpoint}).')
        self.met = _check_number('met', met, 0.0)
        self.air_speed = _check_number('air_speed', air_speed, 0.0)
        if clo != 'adaptive':
            clo = _check_number('clo', clo, 0.0)
        self.clo = clo
        self.tolerance_k = _check_number('tolerance_k', tolerance_k, 0.0)
        if self.tolerance_k <= 0:
            raise ValueError('tolerance_k must be greater than 0.')
        if isinstance(max_iterations, bool) or not isinstance(max_iterations, int) or max_iterations < 1:
            raise ValueError(f'max_iterations must be a positive integer, not {max_iterations!r}.')
        self.max_iterations = max_iterations
        low, high = (_check_number('temperature_range', value) for value in temperature_range)
        if not low < high:
            raise ValueError(f'temperature_range must be (lower, higher), not {temperature_range!r}.')
        self.temperature_range = (low, high)
        self.setpoints: Dict[str, Tuple[float, float]] = {}

    def __repr__(self) -> str:
        return (f'AthbSetpointHook(zones={self.zones!r}, athb_cooling_setpoint={self.athb_cooling_setpoint}, '
                f'athb_heating_setpoint={self.athb_heating_setpoint}, met={self.met}, air_speed={self.air_speed}, '
                f'clo={self.clo!r})')

    def operative_temperatures(self, relative_humidity: float, t_running_mean: float) -> Tuple[float, float]:
        """The operative temperatures (°C) whose ATHB_PMV is the heating and the cooling setpoints of the ATHB, found by
        bisection (both at once), within the range of the temperatures (its limits, if the ATHB_PMV of the setpoint is
        out of it).

        :param relative_humidity: The relative humidity of the zone (%).
        :param t_running_mean: The running mean outdoor temperature (°C).
        :return: (heating, cooling).
        """
        import numpy as np

        def athb(temperatures):
            return np.asarray(athb_pmv(temperatures, temperatures, self.air_speed, relative_humidity, self.met,
                                       t_running_mean, self.clo), dtype=float).reshape(2)

        return _bisect(athb, (self.athb_heating_setpoint, self.athb_cooling_setpoint), self.temperature_range,
                       self.tolerance_k, self.max_iterations)

    def __call__(self, controller, calling_point: str) -> None:
        if calling_point != _CALLING_POINT:
            return
        _check_before_programs(self, controller)
        t_running_mean = controller.get('RMOT')
        if t_running_mean is None:
            return
        met_adapted = athb_met(self.met, t_running_mean)
        clo_adapted = athb_clo(self.met, t_running_mean) if self.clo == 'adaptive' else self.clo
        for zone in self.zones:
            air, radiant, humidity = (controller.get(f'{prefix}_{zone}') for prefix in _SENSORS)
            if air is None or radiant is None or humidity is None:
                continue
            heating, cooling = self.operative_temperatures(humidity, t_running_mean)
            self.setpoints[zone] = (heating, cooling)
            _give_setpoints(controller, zone, heating, cooling)
            controller.set(f'ATHB_PMV_{zone}', athb_pmv(air, radiant, self.air_speed, humidity, self.met,
                                                        t_running_mean, self.clo))
            controller.set(f'ATHB_clo_{zone}', clo_adapted)
            controller.set(f'ATHB_met_{zone}', met_adapted)


def _model_zones(building, what: str, prefixes: Sequence[str], running_mean: bool) -> Dict[str, str]:
    """The zones of a model with the ACCIS of accim 1.0.0 or later and full air-conditioning, with the key of the
    sensor of the operative temperature of each one, checked for the setpoints of a hook.

    :param what: The setpoints, for the messages ('the ATHB'...).
    :param prefixes: The prefixes of the sensors of the zones of the hooks, which the model must not have.
    :param running_mean: True if the hook needs the sensor RMOT of the ACCIS.
    :raises ValueError: If the model is not valid for the hook.
    """
    from accim.sim.ems.inputs import input_programs

    zones = list(input_programs(building))
    if not zones:
        raise ValueError(f'The setpoints of {what} need the ACCIS of accim 1.0.0 or later (the programs '
                         f'SetInputData_<zone>): add it with AddAccis or add_accis_to_idf first.')
    if building.getobject('EnergyManagementSystem:Program', 'SetVST') is not None:
        raise ValueError(f'The setpoints of {what} need full air-conditioning (script_type vrf_ac or ex_ac): in mixed '
                         f'mode, the windows follow the setpoints of the ACCIS.')
    sensors = {str(s.Name).upper(): s for s in building.idfobjects['EnergyManagementSystem:Sensor']}
    actuators = {str(a.Name).upper() for a in building.idfobjects['EnergyManagementSystem:Actuator']}
    if running_mean and 'RMOT' not in sensors:
        raise ValueError('The model has no sensor RMOT (the running mean outdoor temperature of the ACCIS).')
    keys: Dict[str, str] = {}
    for zone in zones:
        missing = [name for name in (f'AHST_Act_{zone}', f'ACST_Act_{zone}') if name.upper() not in actuators]
        operative = sensors.get(f'{zone}_OpT'.upper())
        if missing or operative is None:
            raise ValueError(f'The zone {zone} has not the actuators of the setpoints and the sensor of the operative '
                             f'temperature of the ACCIS ({", ".join(missing) or zone + "_OpT"}).')
        if any(f'{prefix}_{zone}'.upper() in sensors for prefix in prefixes):
            raise ValueError(f'The model already has the setpoints of the ATHB or of the SET (the sensors '
                             f'ATHB_*_{zone} or SET_*_{zone}), which set the same thermostats.')
        keys[zone] = str(operative.OutputVariable_or_OutputMeter_Index_Key_Name)
    return keys


def _add_hook_objects(building, keys: Dict[str, str], sensors: Dict[str, str], outputs: Dict[str, str],
                      output_frequencies: Sequence[str]) -> None:
    """Add to each zone the EMS sensors of a hook, and its global variables and averaged EMS output variables, with
    Output:Variable objects at the frequencies given, and the EMS objects with which the hook gives its setpoints to
    the ACCIS (:func:`accim.sim.ems.hook_setpoints.set_hook_setpoints_code`)."""
    from accim.sim.ems.hook_setpoints import set_hook_setpoints_code

    for zone, key in keys.items():
        for prefix, variable in sensors.items():
            building.newidfobject('EnergyManagementSystem:Sensor', Name=f'{prefix}_{zone}',
                                  OutputVariable_or_OutputMeter_Index_Key_Name=key,
                                  OutputVariable_or_OutputMeter_Name=variable)
        names = [f'{prefix}_{zone}' for prefix in outputs]
        if names:
            building.newidfobject('EnergyManagementSystem:GlobalVariable',
                                  **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(names, start=1)})
        for prefix, units in outputs.items():
            name = f'{prefix}_{zone}'
            building.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=name,
                                  Type_of_Data_in_Variable='Averaged', Update_Frequency='ZoneTimestep', Units=units)
            for frequency in output_frequencies:
                building.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name,
                                      Reporting_Frequency=str(frequency).capitalize(), Schedule_Name='')
    set_hook_setpoints_code(building, list(keys))


def apply_athb_setpoints(building, athb_cooling_setpoint: float = 0.5, athb_heating_setpoint: float = -0.5,
                         met: float = 1.1, air_speed: float = 0.1, clo: Any = 'adaptive',
                         output_frequencies: Sequence[str] = ('hourly',), tolerance_k: float = 0.1,
                         max_iterations: int = 20,
                         temperature_range: Tuple[float, float] = ATHB_TEMPERATURE_RANGE) -> AthbSetpointHook:
    """Prepare a model with the ACCIS (an output IDF of :class:`accim.sim.accis.AddAccis` or a model of
    :func:`accim.sim.accis.add_accis_to_idf`, with ``setpoint_type='temperature'`` and full air-conditioning) for the
    setpoints of the ATHB (see the module), and return the hook that sets them.

    Its zones get the EMS sensors of their mean air temperature, mean radiant temperature and relative humidity
    (``ATHB_MAT_<zone>``, ``ATHB_MRT_<zone>`` and ``ATHB_RH_<zone>``), and the global variables and outputs
    ``ATHB_PMV_<zone>``, ``ATHB_clo_<zone>`` and ``ATHB_met_<zone>`` (averaged, with Output:Variable objects at the
    frequencies given), and the program ``ApplyHookSetpoints_<zone>`` with which the hook gives its setpoints to the
    ACCIS (:mod:`accim.sim.ems.hook_setpoints`, run by ``RunACCIS_<zone>`` right after SetAST): the thermostats of the
    ACCIS (dual setpoints of the operative temperature) get them with the tolerance of the setpoints of the zone, as
    the adaptive setpoints, and the floor and ceiling of the setpoints, the hour counters (also those of the long-term
    discomfort) and the outputs of the setpoints of the zone (``Adaptive Cooling Setpoint Temperature_<zone>``, with and
    without the tolerance...) are those of the ATHB; the comfort temperature and the applicability limits stay those of
    the comfort standard of the zone. The model must be simulated with the backend of the Python API and the hook
    (``run_ep(backend='api', hooks=[hook])``): without the hook (with the EMS backend, for instance), its setpoints are
    those of the ACCIS and the outputs of the ATHB are 0.

    :param building: The model (eppy), changed in place.
    :param output_frequencies: The reporting frequencies of the outputs of the ATHB ('timestep', 'hourly'...).
    :return: The hook (:class:`AthbSetpointHook`), with the other arguments.
    :raises ValueError: If the model has no ACCIS of accim 1.0.0 or later, is in mixed mode (whose windows follow the
        setpoints of the ACCIS), has already the objects of the ATHB or of the SET (:func:`apply_set_setpoints`), or
        an argument is not valid.
    """
    keys = _model_zones(building, 'the ATHB', list(_SENSORS) + list(_SET_SENSORS), running_mean=True)
    hook = AthbSetpointHook(list(keys), athb_cooling_setpoint=athb_cooling_setpoint,
                            athb_heating_setpoint=athb_heating_setpoint, met=met, air_speed=air_speed, clo=clo,
                            tolerance_k=tolerance_k, max_iterations=max_iterations,
                            temperature_range=temperature_range)
    _add_hook_objects(building, keys, _SENSORS, _OUTPUTS, output_frequencies)
    return hook


def zone_outputs(zone: str) -> List[str]:
    """The names of the outputs of the ATHB of a zone."""
    return [f'{prefix}_{zone}' for prefix in _OUTPUTS]


def set_zone_outputs(zone: str) -> List[str]:
    """The names of the outputs of the SET of a zone (with ``method='bisection'``)."""
    return [f'{prefix}_{zone}' for prefix in _SET_OUTPUTS]


# The standard effective temperature (SET), proposal A6 -------------------------------------------------------------

def standard_effective_temperature(air_temperature, mean_radiant_temperature, air_speed, relative_humidity, met, clo,
                                   position: str = 'standing'):
    """The standard effective temperature (SET, °C) of pythermalcomfort (``pythermalcomfort.models.set_tmp``, 4.8.1,
    Gagge et al., 1986): the temperature of an imaginary environment at 50 % of relative humidity, with an air speed
    below 0.1 m/s and the mean radiant temperature equal to the air temperature, in which the total heat loss from the
    skin of an imaginary occupant is the same as in the actual environment with the actual clothing and activity. It is
    calculated without the limits of the inputs of pythermalcomfort (``limit_inputs=False``, which would give NaN out of
    10 < tdb < 40 °C, 10 < tr < 40 °C, 0 < v < 2 m/s, 1 < met < 4 and 0 < clo < 1.5) and without rounding.

    :param air_temperature: The air temperature (°C), a number or an array.
    :param mean_radiant_temperature: The mean radiant temperature (°C).
    :param air_speed: The air speed (m/s).
    :param relative_humidity: The relative humidity (%).
    :param met: The metabolic rate (met).
    :param clo: The clothing insulation (clo).
    :param position: 'standing' (the default of pythermalcomfort) or 'sitting'.
    :return: The SET (a number, or an array for arrays).
    :raises ImportError: If pythermalcomfort is not installed.
    """
    try:
        from pythermalcomfort.models import set_tmp
    except ImportError as error:
        raise ImportError('The setpoints of the SET need pythermalcomfort (4.8 or later, Python 3.11 or later): '
                          'install it with pip install accim[comfort] (or pip install pythermalcomfort).') from error
    result = set_tmp(tdb=air_temperature, tr=mean_radiant_temperature, v=air_speed, rh=relative_humidity, met=met,
                     clo=clo, position=position, limit_inputs=False, round_output=False).set
    try:
        return float(result)
    except TypeError:
        return result


class SetSetpointHook:
    """The hook of the backend of the Python API of EnergyPlus that sets the setpoints of the operative temperature of
    the standard effective temperature (SET) in the zones of a model with the ACCIS; :func:`apply_set_setpoints`
    prepares the model and returns it (proposal A6, and task G3 of the review of accim 1.2.0).

    The setpoints are the operative temperatures whose SET (with the air temperature and the mean radiant temperature
    equal to them, :func:`standard_effective_temperature`, which grows with them) is ``set_heating_setpoint`` and
    ``set_cooling_setpoint``, found by bisection within ``temperature_range`` and to ``tolerance_k``
    (:meth:`operative_temperatures`); with the metabolic rate, the clothing insulation, the air speed and the posture of
    the hook, they depend on the relative humidity of the zone only. At the beginning of each timestep before the EMS
    programs (as :class:`AthbSetpointHook`, :attr:`runs_before_programs`), the hook gives them, for the relative humidity
    of each zone of the previous timestep (the sensor ``SET_RH_<zone>``), to the ACCIS as the limits of the comfort band
    (:mod:`accim.sim.ems.hook_setpoints`: the thermostats get them with the tolerance of the setpoints of the zone, and
    the floor and ceiling of the setpoints, the hour counters and the outputs of the setpoints of the zone follow them).
    With ``method``:

    - ``'table'`` (the default): the setpoints of each relative humidity from 0 to 100 % (every 1 %) are calculated when
      the hook is made, and interpolated linearly in each timestep (:meth:`setpoints_of_humidity`), so pythermalcomfort
      does not run in the callbacks of EnergyPlus (about 1.5 s to make the hook).
    - ``'bisection'``: the setpoints are calculated by bisection in each timestep (about ten SET for each zone), and the
      SET of each zone, from its mean air temperature, mean radiant temperature and relative humidity of the previous
      timestep (the sensors ``SET_MAT_<zone>``, ``SET_MRT_<zone>`` and ``SET_RH_<zone>``), is the global variable
      ``SET_<zone>``, which EnergyPlus reports. ``set_tmp`` of pythermalcomfort is compiled by numba: in the development
      environment of accim 1.2.0 (Python 3.14.3, numba 0.68.1, pythermalcomfort 4.8.1, EnergyPlus 25.1), its first
      call in a process stopped it with an access violation (exit code -1073741819) when the library of the API of
      EnergyPlus had been loaded in the process before, inside a callback or not, and worked when it was made before
      loading the library, after which it also works in the callbacks (the review of 1.2.0 ran it inside the callbacks
      with Python 3.12 and numba 0.68.1 without such a call; with NUMBA_DISABLE_JIT=1, pythermalcomfort 4.8.1 fails).
      So :func:`accim.sim.energyplus_api.run_simulation` calls :meth:`prepare` in the process of the simulation before
      it loads the library. The first call compiles the functions of pythermalcomfort the first time (16 s with an
      empty cache of numba in that environment: 13.6 s to import pythermalcomfort and 2.3 s for the first SET; 7 s in
      that of the review), which numba keeps in its cache on disk for the next processes.

    The SET of pythermalcomfort is that of the code of ASHRAE 55: it takes the air speed as at least 0.1 m/s, and above
    0.85 met its convective heat transfer coefficient is at least 5.66·(met − 0.85)^0.39, larger than that of the air
    speed, 8.6·v^0.53, below about 0.16 m/s at 1.1 met and 0.21 m/s at 1.2 met (pythermalcomfort 4.8.1,
    ``models/two_nodes_gagge.py``): the setpoints do not change with air speeds below those (with 50 % of relative
    humidity, 0.5 clo and setpoints of 21 and 27 °C of the SET, the same with 0.05, 0.1 and 0.15 m/s at 1.1 met, and up
    to 0.2 m/s at 1.2 met). The posture changes the radiative area of the body (0.70 sitting, 0.73 standing): with those
    inputs, the setpoints sitting are 0.004 to 0.008 K (heating) and 0.05 K (cooling) above those standing. The SET of a
    zone weighs its air and mean radiant temperatures with its convective and radiative coefficients, not equally as
    the operative temperature of its thermostat: at the setpoints of those inputs (1.1 met, sitting), with the mean
    radiant temperature 3 K above or below the air temperature, the SET of the zone is up to 0.10 K (heating) and 0.07
    K (cooling) away from its setpoint.

    :param zones: The zones, by their names in the EMS objects.
    :param set_cooling_setpoint: The cooling setpoint of the SET (°C).
    :param set_heating_setpoint: The heating setpoint of the SET (°C), lower than the cooling one.
    :param met: The metabolic rate of the occupants (met); out of 1 to 4 met (the limits of pythermalcomfort), it warns.
    :param clo: The clothing insulation (clo); out of 0 to 1.5 clo, it warns.
    :param air_speed: The air speed (m/s); out of 0 to 2 m/s, it warns.
    :param position: 'sitting' or 'standing' (the posture of the SET of pythermalcomfort); None (the default) for
        'sitting' with ``met`` of 1.2 met or less (sedentary occupants), and 'standing' above it.
    :param tolerance_k: The largest width of the interval of the bisection (K).
    :param max_iterations: The largest number of iterations of the bisection.
    :param temperature_range: The range of the operative temperature of the setpoints (°C,
        :data:`SET_TEMPERATURE_RANGE`); the setpoints out of it are its limits.
    :param method: 'table' (the default) or 'bisection' (:data:`SET_METHODS`).
    :ivar setpoints: The last setpoints of each zone, ``{zone: (heating, cooling)}``, without the tolerance.
    :ivar keys: The key of each zone in the outputs of EnergyPlus (``{'Block1_Zone1': 'Block1:Zone1'}``), which
        :func:`apply_set_setpoints` sets and :func:`set_of_results` uses.
    :raises ImportError: If pythermalcomfort is not installed.
    """

    #: The hook runs before the EMS programs (:func:`accim.run.run_ep` passes it as ``before_programs``)
    runs_before_programs = True

    def __init__(self, zones: Sequence[str], set_cooling_setpoint: float, set_heating_setpoint: float, met: float,
                 clo: float, air_speed: float, position: Optional[str] = None, tolerance_k: float = 0.1,
                 max_iterations: int = 20, temperature_range: Optional[Tuple[float, float]] = None,
                 method: str = 'table'):
        import warnings

        self.zones = [str(zone) for zone in zones]
        if not self.zones:
            raise ValueError('zones must name at least one zone.')
        self.set_cooling_setpoint = _check_number('set_cooling_setpoint', set_cooling_setpoint)
        self.set_heating_setpoint = _check_number('set_heating_setpoint', set_heating_setpoint)
        if not self.set_heating_setpoint < self.set_cooling_setpoint:
            raise ValueError(f'set_heating_setpoint ({set_heating_setpoint}) must be lower than set_cooling_setpoint '
                             f'({set_cooling_setpoint}).')
        self.met = _check_number('met', met, 0.0)
        self.clo = _check_number('clo', clo, 0.0)
        self.air_speed = _check_number('air_speed', air_speed, 0.0)
        for name, value, (low, high) in (('met', self.met, (1.0, 4.0)), ('clo', self.clo, (0.0, 1.5)),
                                         ('air_speed', self.air_speed, (0.0, 2.0))):
            if not low <= value <= high:
                warnings.warn(f'{name} = {value} is out of the range of the SET of pythermalcomfort ({low} to {high}).',
                              UserWarning, stacklevel=2)
        if position is None:
            position = 'sitting' if self.met <= 1.2 else 'standing'
        if position not in ('standing', 'sitting'):
            raise ValueError(f"position must be 'standing', 'sitting' or None, not {position!r}.")
        self.position = position
        self.tolerance_k = _check_number('tolerance_k', tolerance_k, 0.0)
        if self.tolerance_k <= 0:
            raise ValueError('tolerance_k must be greater than 0.')
        if isinstance(max_iterations, bool) or not isinstance(max_iterations, int) or max_iterations < 1:
            raise ValueError(f'max_iterations must be a positive integer, not {max_iterations!r}.')
        self.max_iterations = max_iterations
        temperature_range = SET_TEMPERATURE_RANGE if temperature_range is None else temperature_range
        low, high = (_check_number('temperature_range', value) for value in temperature_range)
        if not low < high:
            raise ValueError(f'temperature_range must be (lower, higher), not {temperature_range!r}.')
        self.temperature_range = (low, high)
        if method not in SET_METHODS:
            raise ValueError(f'method must be one of {list(SET_METHODS)}, not {method!r}.')
        self.method = method
        self.setpoints: Dict[str, Tuple[float, float]] = {}
        self.keys: Dict[str, str] = {}
        # The setpoints of each relative humidity of the table, calculated now (out of the callbacks of EnergyPlus)
        self.table = ([self.operative_temperatures(humidity) for humidity in _SET_HUMIDITIES]
                      if method == 'table' else None)

    def __repr__(self) -> str:
        return (f'SetSetpointHook(zones={self.zones!r}, set_cooling_setpoint={self.set_cooling_setpoint}, '
                f'set_heating_setpoint={self.set_heating_setpoint}, met={self.met}, clo={self.clo}, '
                f'air_speed={self.air_speed}, position={self.position!r}, method={self.method!r})')

    def prepare(self) -> None:
        """Calculate the SET once with numbers and once with an array of two values (the calls of the bisection), which
        :func:`accim.sim.energyplus_api.run_simulation` does in the process of the simulation before it loads the
        library of the API of EnergyPlus, so that the first calls of ``set_tmp`` (and the compilation of numba) are made
        before it (see the class). With ``method='table'``, it does nothing.
        """
        if self.method != 'bisection':
            return
        import numpy as np

        standard_effective_temperature(25.0, 25.0, self.air_speed, 50.0, self.met, self.clo, self.position)
        temperatures = np.array([24.0, 26.0])
        standard_effective_temperature(temperatures, temperatures, self.air_speed, 50.0, self.met, self.clo,
                                       self.position)

    def setpoints_of_humidity(self, relative_humidity: float) -> Tuple[float, float]:
        """The setpoints of a relative humidity (%): with ``method='table'``, interpolated linearly in the table of the
        hook (from 0 to 100 %, every 1 %; the humidities out of it take those of its ends); with ``'bisection'``, those
        of :meth:`operative_temperatures`.

        :return: (heating, cooling).
        """
        import numpy as np

        if self.table is None:
            return self.operative_temperatures(relative_humidity)
        humidity = min(max(float(relative_humidity), _SET_HUMIDITIES[0]), _SET_HUMIDITIES[-1])
        return (float(np.interp(humidity, _SET_HUMIDITIES, [row[0] for row in self.table])),
                float(np.interp(humidity, _SET_HUMIDITIES, [row[1] for row in self.table])))

    def operative_temperatures(self, relative_humidity: float) -> Tuple[float, float]:
        """The operative temperatures (°C) whose SET is the heating and the cooling setpoints, found by bisection (both
        at once), within the range of the temperatures (its limits, if the SET of the setpoint is out of it).

        :param relative_humidity: The relative humidity of the zone (%).
        :return: (heating, cooling).
        """
        import numpy as np

        def standard(temperatures):
            return np.asarray(standard_effective_temperature(temperatures, temperatures, self.air_speed,
                                                             relative_humidity, self.met, self.clo, self.position),
                              dtype=float).reshape(2)

        return _bisect(standard, (self.set_heating_setpoint, self.set_cooling_setpoint), self.temperature_range,
                       self.tolerance_k, self.max_iterations)

    def zone_set(self, air_temperature, mean_radiant_temperature, relative_humidity):
        """The SET of a zone (°C) with the metabolic rate, clothing insulation, air speed and posture of the hook
        (:func:`standard_effective_temperature`); numbers or arrays."""
        return standard_effective_temperature(air_temperature, mean_radiant_temperature, self.air_speed,
                                              relative_humidity, self.met, self.clo, self.position)

    def __call__(self, controller, calling_point: str) -> None:
        if calling_point != _CALLING_POINT:
            return
        _check_before_programs(self, controller)
        for zone in self.zones:
            humidity = controller.get(f'SET_RH_{zone}')
            if humidity is None:
                continue
            heating, cooling = self.setpoints_of_humidity(humidity)
            self.setpoints[zone] = (heating, cooling)
            _give_setpoints(controller, zone, heating, cooling)
            if self.method == 'bisection':
                air, radiant = controller.get(f'SET_MAT_{zone}'), controller.get(f'SET_MRT_{zone}')
                if air is not None and radiant is not None:
                    controller.set(f'SET_{zone}', self.zone_set(air, radiant, humidity))


def _model_output_frequencies(building) -> List[str]:
    """The reporting frequencies of the Output:Variable objects of the EMS output variables of a model (those of the
    ACCIS, in an output IDF of :class:`accim.sim.accis.AddAccis`), in their order; ``['Hourly']`` if it has none."""
    ems_outputs = {str(o.Name).strip().upper() for o in building.idfobjects['EnergyManagementSystem:OutputVariable']}
    frequencies: List[str] = []
    for output in building.idfobjects['Output:Variable']:
        if str(output.Variable_Name).strip().upper() in ems_outputs:
            frequency = str(output.Reporting_Frequency).strip().capitalize()
            if frequency and frequency not in frequencies:
                frequencies.append(frequency)
    return frequencies or ['Hourly']


def _add_zone_output_variables(building, keys: Dict[str, str], variables: Sequence[str],
                               frequencies: Sequence[str]) -> None:
    """Request some output variables of EnergyPlus of each zone (Output:Variable objects with the key of the zone), at
    the frequencies given, unless the model requests them already (with the key of the zone or '*')."""
    requested = {(str(o.Key_Value).strip().upper(), str(o.Variable_Name).strip().upper(),
                  str(o.Reporting_Frequency).strip().upper()) for o in building.idfobjects['Output:Variable']}
    for key in keys.values():
        for variable in variables:
            for frequency in frequencies:
                frequency = str(frequency).capitalize()
                if any((name, variable.upper(), frequency.upper()) in requested for name in (key.upper(), '*')):
                    continue
                building.newidfobject('Output:Variable', Key_Value=key, Variable_Name=variable,
                                      Reporting_Frequency=frequency, Schedule_Name='')
                requested.add((key.upper(), variable.upper(), frequency.upper()))


def apply_set_setpoints(building, set_cooling_setpoint: float, set_heating_setpoint: float, met: float, clo: float,
                        air_speed: float, position: Optional[str] = None, tolerance_k: float = 0.1,
                        max_iterations: int = 20, temperature_range: Optional[Tuple[float, float]] = None,
                        method: str = 'table', output_frequencies: Optional[Sequence[str]] = None) -> SetSetpointHook:
    """Prepare a model with the ACCIS (temperature setpoints and full air-conditioning, as :func:`apply_athb_setpoints`)
    for the setpoints of the standard effective temperature (SET), and return the hook that sets them
    (:class:`SetSetpointHook`, proposal A6, and task G3 of the review of accim 1.2.0).

    Its zones get the EMS sensors ``SET_MAT_<zone>``, ``SET_MRT_<zone>`` and ``SET_RH_<zone>`` (mean air temperature, mean
    radiant temperature and relative humidity), the outputs of these variables of EnergyPlus (*Zone Mean Air
    Temperature*, *Zone Mean Radiant Temperature* and *Zone Air Relative Humidity*, with which :func:`set_of_results`
    calculates the SET of the zones after the simulation), with ``method='bisection'`` the global variable and output
    ``SET_<zone>`` (the SET of the zone, averaged), and the program ``ApplyHookSetpoints_<zone>`` with which the hook
    gives its setpoints to the ACCIS (:mod:`accim.sim.ems.hook_setpoints`; see :func:`apply_athb_setpoints`). The
    setpoints of the SET, the metabolic rate, the clothing insulation and the air speed have no default: they are those
    of the study. The model must be simulated with the backend of the Python API and the hook
    (``run_ep(backend='api', hooks=[hook])``): without it, its setpoints are those of the ACCIS (and ``SET_<zone>`` is
    0).

    :param building: The model (eppy), changed in place.
    :param method: 'table' (the default) or 'bisection' (see :class:`SetSetpointHook`).
    :param output_frequencies: The reporting frequencies of the outputs ('timestep', 'hourly'...); None (the default)
        for those of the EMS outputs of the model (those of the ACCIS), or hourly if it has none.
    :return: The hook, with the other arguments, and the keys of the zones in the outputs (``hook.keys``).
    :raises ValueError: If the model has no ACCIS of accim 1.0.0 or later, is in mixed mode, has already the objects of
        the SET or of the ATHB (both would set the same thermostats), or an argument is not valid.
    """
    keys = _model_zones(building, 'the SET', list(_SENSORS) + list(_SET_SENSORS), running_mean=False)
    hook = SetSetpointHook(list(keys), set_cooling_setpoint=set_cooling_setpoint,
                           set_heating_setpoint=set_heating_setpoint, met=met, clo=clo, air_speed=air_speed,
                           position=position, tolerance_k=tolerance_k, max_iterations=max_iterations,
                           temperature_range=temperature_range, method=method)
    hook.keys = dict(keys)
    frequencies = (_model_output_frequencies(building) if output_frequencies is None
                   else [str(frequency).capitalize() for frequency in output_frequencies])
    _add_hook_objects(building, keys, _SET_SENSORS, _SET_OUTPUTS if method == 'bisection' else {}, frequencies)
    _add_zone_output_variables(building, keys, _SET_ZONE_VARIABLES, frequencies)
    return hook


def _results_column(results, key: str, variable: str, frequency: Optional[str]):
    """The column of an output of EnergyPlus of a key in the results of a simulation (its CSV file), or None."""
    start = f'{key}:{variable} ['.upper()
    names = [name for name in results.columns if str(name).upper().startswith(start)
             and (frequency is None or str(name).upper().endswith(f'({frequency.upper()})'))]
    return results[names[0]] if names else None


def set_of_results(results, hook: SetSetpointHook, keys: Optional[Dict[str, str]] = None,
                   frequency: Optional[str] = None):
    """The SET of the zones of a hook of the SET in each row of the results of a simulation (task G3 of the review of
    accim 1.2.0): :func:`standard_effective_temperature` of the outputs *Zone Mean Air Temperature*, *Zone Mean Radiant
    Temperature* and *Zone Air Relative Humidity* of each zone (those that :func:`apply_set_setpoints` requests), with
    the metabolic rate, clothing insulation, air speed and posture of the hook. The outputs of each row are those of the
    timestep or hour (means), so this SET is that of the row, while the output ``SET_<zone>`` of the hook with
    ``method='bisection'`` is that of the values of the previous timestep, which the sensors read.

    :param results: The results: a DataFrame of the CSV file of the simulation (with the names of the columns of
        EnergyPlus, ``BLOCK1:ZONE1:Zone Mean Air Temperature [C](Hourly)``), or its path.
    :param hook: The hook (:class:`SetSetpointHook`).
    :param keys: The key of each zone of the hook in the outputs (``{'Block1_Zone1': 'Block1:Zone1'}``); by default,
        ``hook.keys`` (set by :func:`apply_set_setpoints`), or the name of the zone with ':' for '_'.
    :param frequency: The frequency of the columns ('Hourly', 'TimeStep'...), if the results have several; by default,
        the first column of each output.
    :return: A DataFrame with the index of the results and a column ``SET_<zone>`` for each zone (NaN in the rows
        without the three outputs).
    :raises ValueError: If the results have not the three outputs of a zone.
    """
    import numpy as np
    import pandas as pd

    if not isinstance(results, pd.DataFrame):
        results = pd.read_csv(results)
    keys = dict(keys or hook.keys or {})
    columns = {}
    for zone in hook.zones:
        key = keys.get(zone, zone.replace('_', ':'))
        found = [_results_column(results, key, variable, frequency) for variable in _SET_ZONE_VARIABLES]
        if any(column is None for column in found):
            missing = [variable for variable, column in zip(_SET_ZONE_VARIABLES, found) if column is None]
            raise ValueError(f'The results have not the outputs {missing} of the zone {zone} (key {key!r}).')
        air, radiant, humidity = (column.to_numpy(dtype=float) for column in found)
        valid = ~(np.isnan(air) | np.isnan(radiant) | np.isnan(humidity))
        values = np.full(len(results), np.nan)
        if valid.any():
            values[valid] = np.asarray(hook.zone_set(air[valid], radiant[valid], humidity[valid]), dtype=float)
        columns[f'SET_{zone}'] = values
    return pd.DataFrame(columns, index=results.index)
