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
:class:`AthbSetpointHook`, which the backend of the Python API runs after the EMS programs at the beginning of each
timestep (``run_ep(backend='api', hooks=[hook])``, or ``run_simulation(..., after_programs=[hook])``): for each zone,
it finds by bisection the operative temperatures whose ATHB_PMV (with the air temperature and the mean radiant
temperature equal to them, and the relative humidity of the zone) is the heating and the cooling setpoints of the
ATHB, and gives them to the setpoint schedules of the ACCIS (``AHST_Act_<zone>`` and ``ACST_Act_<zone>``) instead of
the adaptive setpoints; it also reports the ATHB_PMV of each zone (``ATHB_PMV_<zone>``, from its mean air and mean
radiant temperatures and relative humidity) and the adapted clothing and metabolic rate (``ATHB_clo_<zone>`` and
``ATHB_met_<zone>``). As the other sensors of the EMS at the beginning of the timestep, those of the zone are those of
the previous timestep, and trm is the running mean outdoor temperature of CEN 15251 of EnergyPlus (the sensor ``RMOT``
of the ACCIS, α = 0.8, as EN 16798-1). pythermalcomfort is optional (``pip install accim[comfort]``, Python 3.11 or
later); the EMS backend cannot run the hook (``run_ep(backend='ems', hooks=...)`` raises ``NotImplementedError``).
"""

import math
import numbers
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    'ATHB_TEMPERATURE_RANGE',
    'AthbSetpointHook',
    'apply_athb_setpoints',
    'athb_clo',
    'athb_met',
    'athb_pmv',
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


class AthbSetpointHook:
    """The hook of the backend of the Python API of EnergyPlus that sets the setpoints of the operative temperature of
    the ATHB in the zones of a model with the ACCIS (see the module); :func:`apply_athb_setpoints` prepares the model
    and returns it.

    It runs after the EMS programs at the beginning of each timestep (``after_programs`` of
    :func:`accim.sim.energyplus_api.run_simulation`): for each zone, it reads the running mean outdoor temperature
    (``RMOT``) and the mean air temperature, mean radiant temperature and relative humidity of the zone (the sensors
    ``ATHB_MAT_<zone>``, ``ATHB_MRT_<zone>`` and ``ATHB_RH_<zone>``), finds by bisection the operative temperatures
    whose ATHB_PMV is ``athb_heating_setpoint`` and ``athb_cooling_setpoint`` (the ATHB_PMV grows with the operative
    temperature), within ``temperature_range`` and to ``tolerance_k``, gives them to the actuators of the setpoint
    schedules of the ACCIS (``AHST_Act_<zone>`` and ``ACST_Act_<zone>``) and sets the global variables
    ``ATHB_PMV_<zone>``, ``ATHB_clo_<zone>`` and ``ATHB_met_<zone>``, which EnergyPlus reports.

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
    :ivar setpoints: The last setpoints of each zone, ``{zone: (heating, cooling)}``.
    """

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

        targets = np.array([self.athb_heating_setpoint, self.athb_cooling_setpoint])
        low = np.full(2, self.temperature_range[0])
        high = np.full(2, self.temperature_range[1])

        def athb(temperatures):
            return np.asarray(athb_pmv(temperatures, temperatures, self.air_speed, relative_humidity, self.met,
                                       t_running_mean, self.clo), dtype=float).reshape(2)

        below_range = athb(low) >= targets
        above_range = athb(high) <= targets
        for _ in range(self.max_iterations):
            if float(np.max(high - low)) <= self.tolerance_k:
                break
            middle = (low + high) / 2
            higher = athb(middle) < targets
            low = np.where(higher, middle, low)
            high = np.where(higher, high, middle)
        result = np.where(below_range, self.temperature_range[0],
                          np.where(above_range, self.temperature_range[1], (low + high) / 2))
        return float(result[0]), float(result[1])

    def __call__(self, controller, calling_point: str) -> None:
        if calling_point != _CALLING_POINT:
            return
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
            controller.set(f'AHST_Act_{zone}', heating)
            controller.set(f'ACST_Act_{zone}', cooling)
            controller.set(f'ATHB_PMV_{zone}', athb_pmv(air, radiant, self.air_speed, humidity, self.met,
                                                        t_running_mean, self.clo))
            controller.set(f'ATHB_clo_{zone}', clo_adapted)
            controller.set(f'ATHB_met_{zone}', met_adapted)


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
    frequencies given); the thermostats of the ACCIS (dual setpoints of the operative temperature, whose schedules the
    actuators ``AHST_Act_<zone>`` and ``ACST_Act_<zone>`` set) are those that the hook controls. The model must be
    simulated with the backend of the Python API and the hook (``run_ep(backend='api', hooks=[hook])``): with the EMS,
    its setpoints are those of the ACCIS and the outputs of the ATHB are 0.

    :param building: The model (eppy), changed in place.
    :param output_frequencies: The reporting frequencies of the outputs of the ATHB ('timestep', 'hourly'...).
    :return: The hook (:class:`AthbSetpointHook`), with the other arguments.
    :raises ValueError: If the model has no ACCIS of accim 1.0.0 or later, is in mixed mode (whose windows follow the
        setpoints of the ACCIS), has already the objects of the ATHB, or an argument is not valid.
    """
    from accim.sim.ems.inputs import input_programs

    zones = list(input_programs(building))
    if not zones:
        raise ValueError('The setpoints of the ATHB need the ACCIS of accim 1.0.0 or later (the programs '
                         'SetInputData_<zone>): add it with AddAccis or add_accis_to_idf first.')
    if building.getobject('EnergyManagementSystem:Program', 'SetVST') is not None:
        raise ValueError('The setpoints of the ATHB need full air-conditioning (script_type vrf_ac or ex_ac): in mixed '
                         'mode, the windows follow the setpoints of the ACCIS.')
    hook = AthbSetpointHook(zones, athb_cooling_setpoint=athb_cooling_setpoint,
                            athb_heating_setpoint=athb_heating_setpoint, met=met, air_speed=air_speed, clo=clo,
                            tolerance_k=tolerance_k, max_iterations=max_iterations,
                            temperature_range=temperature_range)
    sensors = {str(s.Name).upper(): s for s in building.idfobjects['EnergyManagementSystem:Sensor']}
    actuators = {str(a.Name).upper() for a in building.idfobjects['EnergyManagementSystem:Actuator']}
    if 'RMOT' not in sensors:
        raise ValueError('The model has no sensor RMOT (the running mean outdoor temperature of the ACCIS).')
    keys: Dict[str, str] = {}
    for zone in zones:
        missing = [name for name in (f'AHST_Act_{zone}', f'ACST_Act_{zone}') if name.upper() not in actuators]
        operative = sensors.get(f'{zone}_OpT'.upper())
        if missing or operative is None:
            raise ValueError(f'The zone {zone} has not the actuators of the setpoints and the sensor of the operative '
                             f'temperature of the ACCIS ({", ".join(missing) or zone + "_OpT"}).')
        if any(f'{prefix}_{zone}'.upper() in sensors for prefix in _SENSORS):
            raise ValueError(f'The model already has the setpoints of the ATHB (the sensors ATHB_*_{zone}).')
        keys[zone] = str(operative.OutputVariable_or_OutputMeter_Index_Key_Name)
    for zone in zones:
        for prefix, variable in _SENSORS.items():
            building.newidfobject('EnergyManagementSystem:Sensor', Name=f'{prefix}_{zone}',
                                  OutputVariable_or_OutputMeter_Index_Key_Name=keys[zone],
                                  OutputVariable_or_OutputMeter_Name=variable)
        names = [f'{prefix}_{zone}' for prefix in _OUTPUTS]
        building.newidfobject('EnergyManagementSystem:GlobalVariable',
                              **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(names, start=1)})
        for prefix, units in _OUTPUTS.items():
            name = f'{prefix}_{zone}'
            building.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=name,
                                  Type_of_Data_in_Variable='Averaged', Update_Frequency='ZoneTimestep', Units=units)
            for frequency in output_frequencies:
                building.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name,
                                      Reporting_Frequency=str(frequency).capitalize(), Schedule_Name='')
    return hook


def zone_outputs(zone: str) -> List[str]:
    """The names of the outputs of the ATHB of a zone."""
    return [f'{prefix}_{zone}' for prefix in _OUTPUTS]
