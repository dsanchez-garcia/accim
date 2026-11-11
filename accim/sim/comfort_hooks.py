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
comfort band, so that the thermostats get them with the tolerance of the setpoints of the zone, and the minimum and
maximum of the setpoints, the hour counters and the outputs of the setpoints of the zone follow them); it also reports
the ATHB_PMV of each zone (``ATHB_PMV_<zone>``, from its mean air and mean radiant temperatures and relative humidity)
and the adapted clothing and metabolic rate (``ATHB_clo_<zone>`` and ``ATHB_met_<zone>``). As the other sensors of the
EMS at the beginning of the timestep, those of the zone are those of the previous timestep, and trm is the running mean
outdoor temperature of CEN 15251 of EnergyPlus (the sensor ``RMOT`` of the ACCIS, α = 0.8, as EN 16798-1). The
setpoints out of ``temperature_range`` are its limits: the hook reports the hours in which a setpoint of a zone is at
one of them (``ATHB_saturated_<zone>``, summed) and warns at the end of the simulation (task H4 of the review of accim
1.2.0, finding A4-1). The metabolic rate and the air speed of the hook are not those of the People objects, which
EnergyPlus uses for the internal gains and its own thermal comfort outputs: their activity level is in W/person, and
1 met is 58.2 W/m² (ISO 7730:2025) times the body surface area of 1.8 m² of EnergyPlus (Input Output Reference, the
field Activity Level Schedule Name of People), about 104.8 W/person (:data:`MET_ACTIVITY_LEVEL`); and ``air_speed`` is
the relative air speed of pythermalcomfort, which for met > 1 is the air speed of the zone plus 0.3·(met − 1)
(``pythermalcomfort.utilities.v_relative``, as ASHRAE 55 and ISO 7730). The hook warns with a metabolic rate out of
0.8 to 4 met or an air speed above 1 m/s, the ranges within which ISO 7730:2025 (section 4) uses the PMV
(:data:`accim.constants.PMV_MET_RANGE`, :data:`accim.constants.PMV_INPUT_RANGES`; finding A4-3).
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
1.0), which the EMS controls. With ``method='bisection'``, the metabolic rate, the clothing insulation and the air speed
can also be those of the schedules of the People object of each zone in each timestep (``None``), and the mean radiant
temperature that of the zone (``tr_mode='zone'``: the unknown of the bisection is then the air temperature, which the
hook converts to the operative temperature of the thermostats of the ACCIS, (air + mean radiant temperature)/2).

The causal SET model of Sun, Brager and Schiavon (2026), Energy and Buildings 370, 118097 (Fig. 7a: TSV = 0.11·SET −
2.6, so the comfort band of TSV ±0.5 is 19.1 to 28.2 °C of SET and the neutral SET 23.6 °C), is comfort standard 24,
'INT Sun2026 SET' (block F of the proposals of accim 1.2.0, task F1): :func:`apply_sun2026_setpoints` prepares a model
with the ACCIS and returns a :class:`Sun2026SetpointHook`, a hook of the SET by bisection whose SET setpoints are those
of the model (:func:`sun2026_set_setpoints`), with the inputs of the People objects and, by default, the mean radiant
temperature of each zone, and which reports the causal TSV of each zone and its occupied hours within the band.
"""

import math
import numbers
import warnings
from typing import Any, Dict, List, Optional, Sequence, Tuple

from accim.constants import PMV_BODY_SURFACE_AREA, PMV_INPUT_RANGES, PMV_MET_RANGE

__all__ = [
    'ATHB_SATURATED',
    'ATHB_TEMPERATURE_RANGE',
    'AthbSetpointHook',
    'MET_ACTIVITY_LEVEL',
    'SET_HEATING_WARNING_TEMPERATURE',
    'SET_METHODS',
    'SET_TEMPERATURE_RANGE',
    'SUN2026_COMFORT_MODES',
    'SUN2026_EXTRAPOLATED_TSV_LIMITS',
    'SUN2026_NEUTRAL_SET',
    'SUN2026_TSV_INTERCEPT',
    'SUN2026_TSV_LIMIT',
    'SUN2026_TSV_SLOPE',
    'SetSetpointHook',
    'Sun2026SetpointHook',
    'TR_MODES',
    'apply_athb_setpoints',
    'apply_set_setpoints',
    'apply_sun2026_setpoints',
    'athb_clo',
    'athb_met',
    'athb_pmv',
    'causal_tsv',
    'set_of_results',
    'set_zone_outputs',
    'standard_effective_temperature',
    'sun2026_set_setpoints',
    'sun2026_zone_outputs',
    'zone_outputs',
]

#: The range of the operative temperature (°C) within which the hook looks for the setpoints of the ATHB: the air
#: temperature of 10 to 30 °C within which ISO 7730:2025 (section 4) uses the PMV (the air temperature and the mean
#: radiant temperature are both the operative temperature); the setpoints out of it are its limits.
ATHB_TEMPERATURE_RANGE = (10.0, 30.0)
#: The calling point at which the hook sets the setpoints, that of the programs of the ACCIS
_CALLING_POINT = 'BEGINTIMESTEPBEFOREPREDICTOR'
#: The kind of simulation of the run periods of the weather file in the API of EnergyPlus (``kind_of_sim``, the
#: KindOfSim RunPeriodWeather of EnergyPlus; the sizing periods have other values)
_RUN_PERIOD_WEATHER = 3
#: The EMS sensors that apply_athb_setpoints adds to each zone: prefix -> output variable of EnergyPlus
_SENSORS = {
    'ATHB_MAT': 'Zone Mean Air Temperature',
    'ATHB_MRT': 'Zone Mean Radiant Temperature',
    'ATHB_RH': 'Zone Air Relative Humidity',
}
#: The EMS output variables of each zone: prefix (of the global variable and the output) -> units
_OUTPUTS = {'ATHB_PMV': '', 'ATHB_clo': 'clo', 'ATHB_met': 'met'}
#: The summed EMS output variable of each zone of the hours in which a setpoint of the ATHB is at a limit of
#: ``temperature_range`` (task H4 of the review of accim 1.2.0, finding A4-1)
ATHB_SATURATED = 'ATHB_saturated'
_SUMMED_OUTPUTS = {ATHB_SATURATED: 'H'}
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
#: The radiant temperatures of the inversion of the SET (:class:`SetSetpointHook`): 'equal_air', the mean radiant
#: temperature equal to the air temperature (the setpoints are the operative temperatures whose SET is the setpoint of
#: the SET, as in proposal A6), and 'zone', the mean radiant temperature of the zone (the setpoints are the air
#: temperatures whose SET is it with that mean radiant temperature, converted to the operative temperatures of the
#: thermostats of the ACCIS, (air + mean radiant temperature)/2: decision of the author of 2026-11-10 in
#: ``notes/decisions.md``)
TR_MODES = ('equal_air', 'zone')
#: The activity level (W/person) of a metabolic rate of 1 met: 58.2 W/m² (Engineering Reference 25.2, equation 19.28,
#: hc = 5.66·(M/58.2 − 0.85)^0.39) times the body surface area with which EnergyPlus gives the activity levels per
#: person, 1.8 m² (Input Output Reference 25.2, 1.14.2.1.10; :data:`accim.constants.PMV_BODY_SURFACE_AREA`)
MET_ACTIVITY_LEVEL = 58.2 * PMV_BODY_SURFACE_AREA
#: The EMS sensors of the inputs of the People object of each zone (output variable Schedule Value of its schedules,
#: and Zone Thermal Comfort Clothing Value of the dynamic clothing model): input -> prefix
_PEOPLE_SENSORS = {
    'activity': 'SET_Act',
    'clothing': 'SET_Clo',
    'clothing_value': 'SET_CloValue',
    'clothing_method': 'SET_CloMethod',
    'air_speed': 'SET_Vel',
}
#: The clothing insulation of the zones: from the clothing insulation schedule ('schedule'), from the output of the
#: dynamic clothing model of ASHRAE 55 of EnergyPlus ('dynamic'), or from one of them as the calculation method
#: schedule of the People object says (1 or 2, 'method'); by the Clothing Insulation Calculation Method of the People
#: object (Input Output Reference 25.2, 1.14.2.1.16 and 1.14.2.1.17)
_CLOTHING_SOURCES = {'CLOTHINGINSULATIONSCHEDULE': 'schedule', 'DYNAMICCLOTHINGMODELASHRAE55': 'dynamic',
                     'CALCULATIONMETHODSCHEDULE': 'method'}
#: The output of EnergyPlus with the clothing insulation of the dynamic clothing model of each People object, which
#: EnergyPlus 25.1 reported with the Pierce model and the method DynamicClothingModelASHRAE55 (and 0 with the method
#: ClothingInsulationSchedule; measured on 2026-11-10, task F1)
_CLOTHING_VALUE_OUTPUT = 'Zone Thermal Comfort Clothing Value'

# The causal SET model of Sun, Brager & Schiavon (2026), comfort standard 24 (block F, task F1) ----------------------

#: The causal relationship between the thermal sensation vote and the SET of Sun, Brager & Schiavon (2026), Energy and
#: Buildings 370, 118097, Fig. 7a: TSV = 0.11·SET − 2.6 (the ratios of their models SET = 0.26·Tout + 19.1 and TSV =
#: 0.03·Tout − 0.49 of the monthly mean outdoor air temperature, Tout)
SUN2026_TSV_SLOPE = 0.11
SUN2026_TSV_INTERCEPT = -2.6
#: The neutral SET (°C, TSV = 0) as Sun, Brager & Schiavon (2026) give it (2.6/0.11 = 23.64 °C)
SUN2026_NEUTRAL_SET = 23.6
#: The half-width of the comfort band of TSV that Sun, Brager & Schiavon (2026) publish (±0.5: 19.1 to 28.2 °C of SET,
#: which they round to 19 and 28 °C), the default of ``tsv_limit``; categories 80 and 90 give it
SUN2026_TSV_LIMIT = 0.5
#: The other half-widths that ``tsv_limit`` takes, a linear extrapolation of the published model (with a warning):
#: decision 2 of the author of 2026-11-10 (``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, section 6)
SUN2026_EXTRAPOLATED_TSV_LIMITS = (0.7, 1.0)
#: The comfort modes of comfort standard 24: 1, the setpoints whose SET is the limits of the band of TSV ±tsv_limit;
#: 2, those whose SET is the neutral SET ± an offset (K of SET)
SUN2026_COMFORT_MODES = {1: 'SET band', 2: 'SET neutral +/- offset'}
#: The heating setpoint (°C) below which the hook of comfort standard 24 warns in the zones without a minimum heating
#: setpoint (``heating_setpoint_minimum``): decision 3 of the author of 2026-11-10 (section 6 of the proposal of block
#: F; the inverted heating setpoint falls below it from 0.73 clo at 0.1 m/s)
SET_HEATING_WARNING_TEMPERATURE = 18.0
#: The EMS output variables of each zone of comfort standard 24, averaged (with the SET of the zone): prefix -> units
_SUN2026_OUTPUTS: Dict[str, str] = {'TSV_causal': ''}
#: The EMS output variable of each zone of comfort standard 24 with its occupied hours with the SET within the band
#: of TSV ±tsv_limit, summed
_SUN2026_HOURS = 'HoursInCausalBand'


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


def _warn_pmv_ranges(met: float, air_speed: float) -> None:
    """Warn if the metabolic rate (met) or the air speed (m/s) of a hook are out of the ranges within which ISO
    7730:2025 (section 4) uses the PMV: 0.8 to 4 met (:data:`accim.constants.PMV_MET_RANGE`) and 0 to 1 m/s of
    relative air speed (:data:`accim.constants.PMV_INPUT_RANGES`)."""
    low, high = PMV_MET_RANGE
    if not low <= met <= high:
        warnings.warn(f'met is {met} met, out of the range of {low} to {high} met within which ISO 7730:2025 '
                      f'(section 4) uses the PMV.', UserWarning, stacklevel=3)
    highest = PMV_INPUT_RANGES['air_velocity'][1]
    if air_speed > highest:
        warnings.warn(f'air_speed is {air_speed} m/s, above the relative air speed of {highest} m/s up to which ISO '
                      f'7730:2025 (section 4) uses the PMV.', UserWarning, stacklevel=3)


def _in_run_period(controller) -> bool:
    """Whether the hours of a timestep count in the hours that a hook adds up: those of the run periods of the weather
    file out of their warm-up days, which the API of EnergyPlus tells (``kind_of_sim`` and ``warmup_flag``; the
    controller updates the built-in variable WarmupFlag only for the EMS programs that read it, finding A7 of the
    self-audit of 2026-11-11); with a controller without the API, those out of the warm-up days (its WarmupFlag)."""
    api, state = getattr(controller, 'api', None), getattr(controller, 'state', None)
    if api is None or state is None:
        return not controller.get('WarmupFlag')
    exchange = api.exchange
    return exchange.kind_of_sim(state) == _RUN_PERIOD_WEATHER and not exchange.warmup_flag(state)


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
    minimum and maximum of the setpoints, the hour counters and the outputs of the setpoints of the zone follow
    them) and sets the global variables ``ATHB_PMV_<zone>``, ``ATHB_clo_<zone>`` and ``ATHB_met_<zone>``, which
    EnergyPlus reports, and ``ATHB_saturated_<zone>``: the length of the timestep (``ZoneTimeStep``, h) if a setpoint
    is at a limit of ``temperature_range`` (where the bisection stops, the setpoint of the ATHB being out of it), and 0
    otherwise. It adds up those hours in the run periods of the weather file, out of their warm-up days and not in the
    sizing periods, as the API of EnergyPlus tells them (:attr:`saturated_hours`; before the self-audit of 2026-11-11,
    finding A7, they included the warm-up days and the sizing periods), and warns of them at the end of the simulation
    (:meth:`finish`, which :func:`accim.sim.energyplus_api.run_simulation` calls; in the processes of
    :func:`accim.run.run_ep`, the warning goes to their console, and the outputs keep the hours).

    :param zones: The zones, by their names in the EMS objects (``Block1_Zone1``...).
    :param athb_cooling_setpoint: The cooling setpoint of the ATHB_PMV.
    :param athb_heating_setpoint: The heating setpoint of the ATHB_PMV, lower than the cooling one.
    :param met: The metabolic rate of the occupants (met), without the adaptation, greater than 0; it warns out of
        0.8 to 4 met (ISO 7730:2025, section 4). It is not the activity level of the People objects (W/person, about
        104.8 W/person per met, :data:`MET_ACTIVITY_LEVEL`).
    :param air_speed: The relative air speed (m/s): for met > 1, the air speed of the zone plus 0.3·(met − 1)
        (``pythermalcomfort.utilities.v_relative``); it warns above 1 m/s (ISO 7730:2025, section 4).
    :param clo: 'adaptive' (the default) for the clothing insulation of the behavioural adaptation, or the clothing
        insulation (clo), without it.
    :param tolerance_k: The largest width of the interval of the bisection (K): the setpoint is its middle.
    :param max_iterations: The largest number of iterations of the bisection.
    :param temperature_range: The range of the operative temperature of the setpoints (°C,
        :data:`ATHB_TEMPERATURE_RANGE`).
    :ivar setpoints: The last setpoints of each zone, ``{zone: (heating, cooling)}``, without the tolerance.
    :ivar saturated_hours: The hours of each zone in which a setpoint was at a limit of ``temperature_range``, in the
        run periods of the weather file out of their warm-up days, since the hook was made or prepared
        (:meth:`prepare`).
    :raises ValueError: If an argument is not valid (``met`` must be greater than 0).
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
        if self.met <= 0:
            raise ValueError(f'met must be greater than 0, not {met!r}.')
        self.air_speed = _check_number('air_speed', air_speed, 0.0)
        _warn_pmv_ranges(self.met, self.air_speed)
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
        self.saturated_hours: Dict[str, float] = {}

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

    def saturated(self, heating: float, cooling: float) -> bool:
        """True if a setpoint is at a limit of ``temperature_range`` (the bisection gives them exactly when the setpoint
        of the ATHB is out of the range)."""
        return heating in self.temperature_range or cooling in self.temperature_range

    def prepare(self) -> None:
        """Reset :attr:`saturated_hours` before a simulation (:func:`accim.sim.energyplus_api.run_simulation` calls it
        in the process of the simulation)."""
        self.saturated_hours = {}

    def finish(self) -> None:
        """Warn of the hours in which the setpoints were at a limit of ``temperature_range``, if any, after a simulation
        (:func:`accim.sim.energyplus_api.run_simulation` calls it)."""
        hours = {zone: value for zone, value in self.saturated_hours.items() if value > 0}
        if hours:
            warnings.warn(f'The setpoints of the ATHB were at a limit of temperature_range {self.temperature_range} °C '
                          f'(their ATHB_PMV setpoints are out of it) in '
                          + ', '.join(f'{zone}: {value:.2f} h' for zone, value in hours.items())
                          + ' (the outputs ATHB_saturated_<zone>): widen temperature_range, or check the setpoints and '
                            'the running mean outdoor temperature.', UserWarning, stacklevel=2)

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
            step = controller.get('ZoneTimeStep') or 0.0
            saturated = self.saturated(heating, cooling)
            controller.set(f'{ATHB_SATURATED}_{zone}', step if saturated else 0.0)
            if saturated and _in_run_period(controller):
                self.saturated_hours[zone] = self.saturated_hours.get(zone, 0.0) + step
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
                      output_frequencies: Sequence[str], summed: Optional[Dict[str, str]] = None) -> None:
    """Add to each zone the EMS sensors of a hook, and its global variables and averaged EMS output variables (and the
    summed ones of ``summed``, prefix -> units), with Output:Variable objects at the frequencies given, and the EMS
    objects with which the hook gives its setpoints to the ACCIS
    (:func:`accim.sim.ems.hook_setpoints.set_hook_setpoints_code`)."""
    from accim.sim.ems.hook_setpoints import set_hook_setpoints_code

    kinds = [(prefix, units, 'Averaged') for prefix, units in outputs.items()]
    kinds += [(prefix, units, 'Summed') for prefix, units in (summed or {}).items()]
    for zone, key in keys.items():
        for prefix, variable in sensors.items():
            building.newidfobject('EnergyManagementSystem:Sensor', Name=f'{prefix}_{zone}',
                                  OutputVariable_or_OutputMeter_Index_Key_Name=key,
                                  OutputVariable_or_OutputMeter_Name=variable)
        names = [f'{prefix}_{zone}' for prefix, _, _ in kinds]
        if names:
            building.newidfobject('EnergyManagementSystem:GlobalVariable',
                                  **{f'Erl_Variable_{n}_Name': name for n, name in enumerate(names, start=1)})
        for prefix, units, kind in kinds:
            name = f'{prefix}_{zone}'
            building.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=name,
                                  Type_of_Data_in_Variable=kind, Update_Frequency='ZoneTimestep', Units=units)
            for frequency in output_frequencies:
                building.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name,
                                      Reporting_Frequency=str(frequency).capitalize(), Schedule_Name='')
    set_hook_setpoints_code(building, list(keys))


def apply_athb_setpoints(building, athb_cooling_setpoint: float = 0.5, athb_heating_setpoint: float = -0.5,
                         met: float = 1.1, air_speed: float = 0.1, clo: Any = 'adaptive',
                         output_frequencies: Optional[Sequence[str]] = None, tolerance_k: float = 0.1,
                         max_iterations: int = 20,
                         temperature_range: Tuple[float, float] = ATHB_TEMPERATURE_RANGE) -> AthbSetpointHook:
    """Prepare a model with the ACCIS (an output IDF of :class:`accim.sim.accis.AddAccis` or a model of
    :func:`accim.sim.accis.add_accis_to_idf`, with ``setpoint_type='temperature'`` and full air-conditioning) for the
    setpoints of the ATHB (see the module), and return the hook that sets them.

    Its zones get the EMS sensors of their mean air temperature, mean radiant temperature and relative humidity
    (``ATHB_MAT_<zone>``, ``ATHB_MRT_<zone>`` and ``ATHB_RH_<zone>``), and the global variables and outputs
    ``ATHB_PMV_<zone>``, ``ATHB_clo_<zone>`` and ``ATHB_met_<zone>`` (averaged) and ``ATHB_saturated_<zone>`` (the
    hours in which a setpoint is at a limit of ``temperature_range``, summed), with Output:Variable objects at the
    frequencies given, and the program ``ApplyHookSetpoints_<zone>`` with which the hook gives its setpoints to the
    ACCIS (:mod:`accim.sim.ems.hook_setpoints`, run by ``RunACCIS_<zone>`` right after SetAST): the thermostats of the
    ACCIS (dual setpoints of the operative temperature) get them with the tolerance of the setpoints of the zone, as
    the adaptive setpoints, and the minimum and maximum of the setpoints, the hour counters (also those of the long-term
    discomfort) and the outputs of the setpoints of the zone (``Adaptive Cooling Setpoint Temperature_<zone>``, with and
    without the tolerance...) are those of the ATHB; the comfort temperature and the applicability limits stay those of
    the comfort standard of the zone. The model must be simulated with the backend of the Python API and the hook
    (``run_ep(backend='api', hooks=[hook])``): without the hook (with the EMS backend, for instance), its setpoints are
    those of the ACCIS and the outputs of the ATHB are 0.

    :param building: The model (eppy), changed in place.
    :param output_frequencies: The reporting frequencies of the outputs of the ATHB ('timestep', 'hourly'...); None
        (the default since task H4 of the review of accim 1.2.0, finding A4-3; ``('hourly',)`` before) for those of the
        EMS outputs of the model (those of the ACCIS), so that ``Table`` reads them with the other outputs.
    :return: The hook (:class:`AthbSetpointHook`), with the other arguments (see it: ``met`` greater than 0, warnings
        out of the ranges of ISO 7730:2025 of the metabolic rate and the air speed).
    :raises ValueError: If the model has no ACCIS of accim 1.0.0 or later, is in mixed mode (whose windows follow the
        setpoints of the ACCIS), has already the objects of the ATHB or of the SET (:func:`apply_set_setpoints`), or
        an argument is not valid.
    """
    keys = _model_zones(building, 'the ATHB', _HOOK_SENSOR_PREFIXES, running_mean=True)
    hook = AthbSetpointHook(list(keys), athb_cooling_setpoint=athb_cooling_setpoint,
                            athb_heating_setpoint=athb_heating_setpoint, met=met, air_speed=air_speed, clo=clo,
                            tolerance_k=tolerance_k, max_iterations=max_iterations,
                            temperature_range=temperature_range)
    _add_hook_objects(building, keys, _SENSORS, _OUTPUTS, _output_frequencies(building, output_frequencies),
                      summed=_SUMMED_OUTPUTS)
    return hook


def zone_outputs(zone: str) -> List[str]:
    """The names of the outputs of the ATHB of a zone (the averaged ones, and ``ATHB_saturated_<zone>``)."""
    return [f'{prefix}_{zone}' for prefix in (*_OUTPUTS, *_SUMMED_OUTPUTS)]


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
    prepares the model and returns it (proposal A6, and tasks G3 and F1 of the review of accim 1.2.0).

    The setpoints are the operative temperatures whose SET (with the air temperature and the mean radiant temperature
    equal to them, :func:`standard_effective_temperature`, which grows with them) is ``set_heating_setpoint`` and
    ``set_cooling_setpoint``, found by bisection within ``temperature_range`` and to ``tolerance_k``
    (:meth:`operative_temperatures`); with the metabolic rate, the clothing insulation, the air speed and the posture of
    the hook, they depend on the relative humidity of the zone only. At the beginning of each timestep before the EMS
    programs (as :class:`AthbSetpointHook`, :attr:`runs_before_programs`), the hook gives them, for the relative humidity
    of each zone of the previous timestep (the sensor ``SET_RH_<zone>``), to the ACCIS as the limits of the comfort band
    (:mod:`accim.sim.ems.hook_setpoints`: the thermostats get them with the tolerance of the setpoints of the zone, and
    the minimum and maximum of the setpoints, the hour counters and the outputs of the setpoints of the zone follow
    them).
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

    With ``method='bisection'`` (task F1 of block F), the inputs can also be those of the zones in each timestep:

    - ``met``, ``clo`` and ``air_speed`` None: the hook reads them from the People object of each zone, with the EMS
      sensors that :func:`apply_set_setpoints` and :func:`apply_sun2026_setpoints` add: the activity level of its
      schedule (``SET_Act_<zone>``, W/person) divided by :data:`MET_ACTIVITY_LEVEL`; its clothing insulation schedule
      (``SET_Clo_<zone>``), or, with the dynamic clothing model of ASHRAE 55 of EnergyPlus, the clothing insulation of
      that model (``SET_CloValue_<zone>``, the output Zone Thermal Comfort Clothing Value of its occupants, that of the
      previous timestep), as its Clothing Insulation Calculation Method says (:attr:`clothing_sources`; with
      CalculationMethodSchedule, the value of its calculation method schedule, ``SET_CloMethod_<zone>``, chooses one);
      and its air velocity schedule (``SET_Vel_<zone>``). The schedules are those of the timestep. With ``position``
      None, the posture is then that of the metabolic rate of each timestep. The work efficiency of the People objects
      is not read: the external work of the SET is 0, as in the SET of the hook with its own inputs.
    - ``tr_mode='zone'``: the mean radiant temperature is that of the zone (the sensor ``SET_MRT_<zone>``, that of the
      previous timestep), and the unknown of the bisection is the air temperature (:meth:`inverted_temperatures`); the
      hook gives the ACCIS, whose thermostats control the operative temperature, the operative temperatures (air
      temperature + mean radiant temperature)/2 of the air temperatures found (:meth:`operative_temperatures`; decision
      of the author of 2026-11-10 in ``notes/decisions.md``). With ``'equal_air'`` (the default), the mean radiant
      temperature is the air temperature and the temperatures found are the setpoints, as above.

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
        None (``method='bisection'`` only) for that of the People object of each zone in each timestep.
    :param clo: The clothing insulation (clo); out of 0 to 1.5 clo, it warns. None for that of the People objects.
    :param air_speed: The air speed (m/s); out of 0 to 2 m/s, it warns. None for that of the People objects.
    :param position: 'sitting' or 'standing' (the posture of the SET of pythermalcomfort); None (the default) for
        'sitting' with a metabolic rate of 1.2 met or less (sedentary occupants), and 'standing' above it.
    :param tolerance_k: The largest width of the interval of the bisection (K).
    :param max_iterations: The largest number of iterations of the bisection.
    :param temperature_range: The range of the temperatures of the bisection (°C, :data:`SET_TEMPERATURE_RANGE`); the
        temperatures out of it are its limits.
    :param method: 'table' (the default) or 'bisection' (:data:`SET_METHODS`).
    :param tr_mode: 'equal_air' (the default) or 'zone' (:data:`TR_MODES`; 'zone' with ``method='bisection'`` only).
    :param clothing_sources: The clothing insulation of each zone, with ``clo`` None: ``{zone: 'schedule'}`` (its
        clothing insulation schedule, the default), ``'dynamic'`` (the dynamic clothing model) or ``'method'`` (one of
        them, as the calculation method schedule says).
    :ivar setpoints: The last setpoints of each zone, ``{zone: (heating, cooling)}``, without the tolerance.
    :ivar keys: The key of each zone in the outputs of EnergyPlus (``{'Block1_Zone1': 'Block1:Zone1'}``), which
        :func:`apply_set_setpoints` sets and :func:`set_of_results` uses.
    :raises ImportError: If pythermalcomfort is not installed.
    """

    #: The hook runs before the EMS programs (:func:`accim.run.run_ep` passes it as ``before_programs``)
    runs_before_programs = True

    def __init__(self, zones: Sequence[str], set_cooling_setpoint: float, set_heating_setpoint: float,
                 met: Optional[float] = None, clo: Optional[float] = None, air_speed: Optional[float] = None,
                 position: Optional[str] = None, tolerance_k: float = 0.1, max_iterations: int = 20,
                 temperature_range: Optional[Tuple[float, float]] = None, method: str = 'table',
                 tr_mode: str = 'equal_air', clothing_sources: Optional[Dict[str, str]] = None):
        self.zones = [str(zone) for zone in zones]
        if not self.zones:
            raise ValueError('zones must name at least one zone.')
        self.set_cooling_setpoint = _check_number('set_cooling_setpoint', set_cooling_setpoint)
        self.set_heating_setpoint = _check_number('set_heating_setpoint', set_heating_setpoint)
        if not self.set_heating_setpoint < self.set_cooling_setpoint:
            raise ValueError(f'set_heating_setpoint ({set_heating_setpoint}) must be lower than set_cooling_setpoint '
                             f'({set_cooling_setpoint}).')
        if method not in SET_METHODS:
            raise ValueError(f'method must be one of {list(SET_METHODS)}, not {method!r}.')
        if tr_mode not in TR_MODES:
            raise ValueError(f'tr_mode must be one of {list(TR_MODES)}, not {tr_mode!r}.')
        from_people = [name for name, value in (('met', met), ('clo', clo), ('air_speed', air_speed)) if value is None]
        if method == 'table' and (from_people or tr_mode != 'equal_air'):
            raise ValueError(f"method='table' needs met, clo and air_speed (not {from_people}) and "
                             f"tr_mode='equal_air', with which the setpoints depend on the relative humidity only: use "
                             f"method='bisection' for the inputs of the People objects or the mean radiant "
                             f"temperature of the zones.")
        self.met = None if met is None else _check_number('met', met, 0.0)
        self.clo = None if clo is None else _check_number('clo', clo, 0.0)
        self.air_speed = None if air_speed is None else _check_number('air_speed', air_speed, 0.0)
        for name, value, (low, high) in (('met', self.met, (1.0, 4.0)), ('clo', self.clo, (0.0, 1.5)),
                                         ('air_speed', self.air_speed, (0.0, 2.0))):
            if value is not None and not low <= value <= high:
                warnings.warn(f'{name} = {value} is out of the range of the SET of pythermalcomfort ({low} to {high}).',
                              UserWarning, stacklevel=2)
        if position is None and self.met is not None:
            position = 'sitting' if self.met <= 1.2 else 'standing'
        if position not in ('standing', 'sitting', None):
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
        self.method = method
        self.tr_mode = tr_mode
        self.clothing_sources: Dict[str, str] = dict(clothing_sources or {})
        unknown = {zone: source for zone, source in self.clothing_sources.items()
                   if source not in _CLOTHING_SOURCES.values()}
        if unknown:
            raise ValueError(f'The clothing sources must be one of {sorted(set(_CLOTHING_SOURCES.values()))}, not '
                             f'{unknown}.')
        self.setpoints: Dict[str, Tuple[float, float]] = {}
        self.keys: Dict[str, str] = {}
        # The setpoints of each relative humidity of the table, calculated now (out of the callbacks of EnergyPlus)
        self.table = ([self.operative_temperatures(humidity) for humidity in _SET_HUMIDITIES]
                      if method == 'table' else None)

    def __repr__(self) -> str:
        return (f'SetSetpointHook(zones={self.zones!r}, set_cooling_setpoint={self.set_cooling_setpoint}, '
                f'set_heating_setpoint={self.set_heating_setpoint}, met={self.met}, clo={self.clo}, '
                f'air_speed={self.air_speed}, position={self.position!r}, method={self.method!r}, '
                f'tr_mode={self.tr_mode!r})')

    def posture(self, met: float) -> str:
        """The posture of the SET with a metabolic rate (met): that of the hook, or, if it has none (with the metabolic
        rate of the People objects), 'sitting' with 1.2 met or less and 'standing' above it."""
        if self.position is not None:
            return self.position
        return 'sitting' if met <= 1.2 else 'standing'

    def _inputs(self, met: Optional[float], clo: Optional[float],
                air_speed: Optional[float]) -> Tuple[float, float, float]:
        """The metabolic rate, clothing insulation and air speed given, or those of the hook."""
        values = []
        for name, given in (('met', met), ('clo', clo), ('air_speed', air_speed)):
            value = getattr(self, name) if given is None else given
            if value is None:
                raise ValueError(f'The hook reads {name} from the People objects in each timestep: give it.')
            values.append(float(value))
        return values[0], values[1], values[2]

    def prepare(self) -> None:
        """Calculate the SET with numbers and with arrays of two values (the calls of the bisection, also with the mean
        radiant temperature of the zone), which :func:`accim.sim.energyplus_api.run_simulation` does in the process of
        the simulation before it loads the library of the API of EnergyPlus, so that the first calls of ``set_tmp``
        (and the compilation of numba) are made before it (see the class). The inputs that the hook reads from the
        People objects are 1.1 met, 0.5 clo and 0.1 m/s in these calls (numba compiles the functions for the types of
        their arguments, not for their values). With ``method='table'``, it does nothing.
        """
        if self.method != 'bisection':
            return
        import numpy as np

        met = 1.1 if self.met is None else self.met
        clo = 0.5 if self.clo is None else self.clo
        air_speed = 0.1 if self.air_speed is None else self.air_speed
        position = self.posture(met)
        standard_effective_temperature(25.0, 25.0, air_speed, 50.0, met, clo, position)
        temperatures = np.array([24.0, 26.0])
        standard_effective_temperature(temperatures, temperatures, air_speed, 50.0, met, clo, position)
        standard_effective_temperature(temperatures, 25.0, air_speed, 50.0, met, clo, position)

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

    def inverted_temperatures(self, relative_humidity: float, mean_radiant_temperature: Optional[float] = None,
                              met: Optional[float] = None, clo: Optional[float] = None,
                              air_speed: Optional[float] = None) -> Tuple[float, float]:
        """The temperatures (°C) whose SET is the heating and the cooling setpoints of the SET, found by bisection (both
        at once) within the range of the temperatures (its limits, if the SET of the setpoint is out of it): with
        ``tr_mode='equal_air'``, the operative temperatures (the air and mean radiant temperatures equal to them); with
        ``'zone'``, the air temperatures with the mean radiant temperature given.

        :param relative_humidity: The relative humidity of the zone (%).
        :param mean_radiant_temperature: The mean radiant temperature of the zone (°C), with ``tr_mode='zone'``.
        :param met: The metabolic rate (met), instead of that of the hook (which it needs if the hook has none); and so
            ``clo`` (clo) and ``air_speed`` (m/s).
        :return: (heating, cooling).
        :raises ValueError: With ``tr_mode='zone'`` and no mean radiant temperature, or without an input that the hook
            reads from the People objects.
        """
        import numpy as np

        met, clo, air_speed = self._inputs(met, clo, air_speed)
        position = self.posture(met)
        if self.tr_mode == 'zone':
            if mean_radiant_temperature is None:
                raise ValueError("With tr_mode='zone', the mean radiant temperature of the zone is needed.")
            radiant = float(mean_radiant_temperature)

            def standard(temperatures):
                return np.asarray(standard_effective_temperature(temperatures, radiant, air_speed, relative_humidity,
                                                                 met, clo, position), dtype=float).reshape(2)
        else:
            def standard(temperatures):
                return np.asarray(standard_effective_temperature(temperatures, temperatures, air_speed,
                                                                 relative_humidity, met, clo, position),
                                  dtype=float).reshape(2)

        return _bisect(standard, (self.set_heating_setpoint, self.set_cooling_setpoint), self.temperature_range,
                       self.tolerance_k, self.max_iterations)

    def operative_temperatures(self, relative_humidity: float, mean_radiant_temperature: Optional[float] = None,
                               met: Optional[float] = None, clo: Optional[float] = None,
                               air_speed: Optional[float] = None) -> Tuple[float, float]:
        """The setpoints of the operative temperature (°C) that the hook gives to the ACCIS: the temperatures of
        :meth:`inverted_temperatures`, with ``tr_mode='equal_air'``, or, with ``'zone'``, the operative temperatures of
        its air temperatures with the mean radiant temperature of the zone, (air + mean radiant temperature)/2 (the
        operative temperature of the thermostats of the ACCIS, the output Zone Operative Temperature of EnergyPlus).
        The arguments are those of :meth:`inverted_temperatures`.

        :return: (heating, cooling).
        """
        heating, cooling = self.inverted_temperatures(relative_humidity, mean_radiant_temperature, met, clo, air_speed)
        if self.tr_mode == 'zone':
            radiant = float(mean_radiant_temperature)
            return (heating + radiant) / 2, (cooling + radiant) / 2
        return heating, cooling

    def zone_set(self, air_temperature, mean_radiant_temperature, relative_humidity, met: Optional[float] = None,
                 clo: Optional[float] = None, air_speed: Optional[float] = None):
        """The SET of a zone (°C) with the metabolic rate, clothing insulation, air speed and posture of the hook, or
        those given (:func:`standard_effective_temperature`); numbers, or arrays of the temperatures and humidity."""
        met, clo, air_speed = self._inputs(met, clo, air_speed)
        return standard_effective_temperature(air_temperature, mean_radiant_temperature, air_speed, relative_humidity,
                                              met, clo, self.posture(met))

    def _clothing(self, controller, zone: str) -> Optional[float]:
        """The clothing insulation of the People object of a zone in a timestep (see the class), or None if its sensor
        has no value yet (the clothing insulation of the dynamic model is 0 until EnergyPlus calculates it)."""
        source = self.clothing_sources.get(zone, 'schedule')
        if source == 'method':
            source = 'dynamic' if controller.get(f"{_PEOPLE_SENSORS['clothing_method']}_{zone}") == 2 else 'schedule'
        if source == 'dynamic':
            value = controller.get(f"{_PEOPLE_SENSORS['clothing_value']}_{zone}")
            return value if value is not None and value > 0 else None
        value = controller.get(f"{_PEOPLE_SENSORS['clothing']}_{zone}")
        return value if value is not None and value >= 0 else None

    def zone_inputs(self, controller, zone: str) -> Optional[Tuple[Optional[float], float, float, float]]:
        """The inputs of the SET of a zone in a timestep: (mean radiant temperature of the zone, or None; metabolic
        rate; clothing insulation; air speed), those of the hook or those of the People object of the zone (see the
        class); None if a sensor has no value yet."""
        radiant = controller.get(f'SET_MRT_{zone}')
        if self.tr_mode == 'zone' and radiant is None:
            return None
        met, clo, air_speed = self.met, self.clo, self.air_speed
        if met is None:
            activity = controller.get(f"{_PEOPLE_SENSORS['activity']}_{zone}")
            if activity is None or activity <= 0:
                return None
            met = activity / MET_ACTIVITY_LEVEL
        if clo is None:
            clo = self._clothing(controller, zone)
            if clo is None:
                return None
        if air_speed is None:
            air_speed = controller.get(f"{_PEOPLE_SENSORS['air_speed']}_{zone}")
            if air_speed is None or air_speed < 0:
                return None
        return radiant, met, clo, air_speed

    def _given(self, controller, zone: str, heating: float, cooling: float) -> None:
        """Called when the hook has given the setpoints of a zone (for the subclasses)."""

    def _report(self, controller, zone: str, value: float) -> None:
        """Called with the SET of a zone, once the hook has set ``SET_<zone>`` (for the subclasses)."""

    def __call__(self, controller, calling_point: str) -> None:
        if calling_point != _CALLING_POINT:
            return
        _check_before_programs(self, controller)
        for zone in self.zones:
            humidity = controller.get(f'SET_RH_{zone}')
            if humidity is None:
                continue
            inputs = self.zone_inputs(controller, zone)
            if inputs is None:
                continue
            radiant, met, clo, air_speed = inputs
            if self.table is not None:
                heating, cooling = self.setpoints_of_humidity(humidity)
            else:
                heating, cooling = self.operative_temperatures(humidity, radiant, met, clo, air_speed)
            self.setpoints[zone] = (heating, cooling)
            _give_setpoints(controller, zone, heating, cooling)
            self._given(controller, zone, heating, cooling)
            if self.method == 'bisection':
                air = controller.get(f'SET_MAT_{zone}')
                if air is not None and radiant is not None:
                    value = self.zone_set(air, radiant, humidity, met, clo, air_speed)
                    controller.set(f'SET_{zone}', value)
                    self._report(controller, zone, value)


def causal_tsv(set_value):
    """The thermal sensation vote of the causal SET model of Sun, Brager & Schiavon (2026), Energy and Buildings 370,
    118097, Fig. 7a: TSV = 0.11·SET − 2.6 (:data:`SUN2026_TSV_SLOPE`, :data:`SUN2026_TSV_INTERCEPT`).

    :param set_value: The SET (°C), a number or an array.
    :return: The TSV (a number, or an array).
    """
    return SUN2026_TSV_SLOPE * set_value + SUN2026_TSV_INTERCEPT


def _sun2026_comfort_mode(comfort_mode: Any) -> int:
    """The number of a comfort mode of comfort standard 24 (:data:`SUN2026_COMFORT_MODES`), given by its number or by
    its name."""
    if isinstance(comfort_mode, str):
        names = {name.upper(): number for number, name in SUN2026_COMFORT_MODES.items()}
        number = names.get(comfort_mode.strip().upper().replace('±', '+/-'))
        if number is not None:
            return number
    elif not isinstance(comfort_mode, bool) and comfort_mode in SUN2026_COMFORT_MODES:
        return int(comfort_mode)
    choices = [f'{number} ({name!r})' for number, name in SUN2026_COMFORT_MODES.items()]
    raise ValueError(f'comfort_mode must be one of {", ".join(choices)}, not {comfort_mode!r}.')


def _sun2026_tsv_limit(tsv_limit: Optional[float], category: Optional[int], warn: bool = True) -> float:
    """The half-width of the band of TSV of comfort standard 24: that of the category (80 and 90 give the published
    one, :data:`SUN2026_TSV_LIMIT`) or ``tsv_limit``, which can also be an extrapolated one (with a warning)."""
    if category is not None and (isinstance(category, bool) or category not in (80, 90)):
        raise ValueError(f'category must be 80 or 90 (both give the band of TSV ±{SUN2026_TSV_LIMIT}), not '
                         f'{category!r}.')
    if tsv_limit is None:
        return SUN2026_TSV_LIMIT
    value = _check_number('tsv_limit', tsv_limit)
    if value == SUN2026_TSV_LIMIT:
        return value
    if value not in SUN2026_EXTRAPOLATED_TSV_LIMITS:
        raise ValueError(f'tsv_limit must be {SUN2026_TSV_LIMIT} (the band of Sun, Brager & Schiavon, 2026) or one of '
                         f'{list(SUN2026_EXTRAPOLATED_TSV_LIMITS)} (extrapolated), not {tsv_limit!r}.')
    if warn:
        band = [round((sign * value - SUN2026_TSV_INTERCEPT) / SUN2026_TSV_SLOPE, 2) for sign in (-1, 1)]
        warnings.warn(f'tsv_limit = {value} is a linear extrapolation of the causal SET model of Sun, Brager & '
                      f'Schiavon (2026), which publishes the band of TSV ±{SUN2026_TSV_LIMIT} only: SET = '
                      f'(±tsv_limit + 2.6)/0.11 gives the band {band[0]} to {band[1]} °C of SET.', UserWarning,
                      stacklevel=3)
    return value


def sun2026_set_setpoints(comfort_mode: Any = 1, tsv_limit: Optional[float] = None,
                          set_offset: Optional[float] = None, category: Optional[int] = None) -> Tuple[float, float]:
    """The heating and cooling setpoints of the SET (°C) of comfort standard 24, INT Sun2026 SET (the causal SET model
    of Sun, Brager & Schiavon, 2026, Energy and Buildings 370, 118097, Fig. 7a: TSV = 0.11·SET − 2.6; decisions of the
    author of 2026-11-10, ``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, section 6):

    - comfort mode 1, 'SET band': the SET of the limits of the band of TSV ±tsv_limit, SET = (∓tsv_limit + 2.6)/0.11
      (19.09 and 28.18 °C with 0.5, which the paper rounds to 19 and 28 °C);
    - comfort mode 2, 'SET neutral +/- offset': the neutral SET of the paper, 23.6 °C, ∓ ``set_offset`` (K of SET).

    :param comfort_mode: 1 or 'SET band' (the default), or 2 or 'SET neutral +/- offset'.
    :param tsv_limit: The half-width of the band of TSV: None for that of the paper (0.5, also that of the categories
        80 and 90); 0.7 and 1.0 are a linear extrapolation of the model, with a warning.
    :param set_offset: With comfort mode 2, and only with it, the offset of the setpoints from the neutral SET (K, a
        positive number).
    :param category: 80 or 90 (both give the band of TSV ±0.5), or None.
    :return: (heating, cooling).
    :raises ValueError: If an argument is not valid.
    """
    mode = _sun2026_comfort_mode(comfort_mode)
    limit = _sun2026_tsv_limit(tsv_limit, category)
    if mode == 1:
        if set_offset is not None:
            raise ValueError("set_offset is only used with comfort mode 2 ('SET neutral +/- offset').")
        return ((-limit - SUN2026_TSV_INTERCEPT) / SUN2026_TSV_SLOPE,
                (limit - SUN2026_TSV_INTERCEPT) / SUN2026_TSV_SLOPE)
    if set_offset is None:
        raise ValueError("Comfort mode 2 ('SET neutral +/- offset') needs set_offset, the offset of the setpoints from "
                         f'the neutral SET of {SUN2026_NEUTRAL_SET} °C (K).')
    offset = _check_number('set_offset', set_offset)
    if offset <= 0:
        raise ValueError(f'set_offset must be greater than 0, not {set_offset!r}.')
    return SUN2026_NEUTRAL_SET - offset, SUN2026_NEUTRAL_SET + offset


class Sun2026SetpointHook(SetSetpointHook):
    """The hook of comfort standard 24, INT Sun2026 SET (the causal SET model of Sun, Brager & Schiavon, 2026; task F1
    of block F): a hook of the SET by bisection (:class:`SetSetpointHook` with ``method='bisection'``) whose setpoints
    of the SET are those of its comfort mode (:func:`sun2026_set_setpoints`), with the inputs of the People objects of
    the zones and, by default, the mean radiant temperature of each zone (``tr_mode='zone'``, decision 4 of the author
    of 2026-11-10); :func:`apply_sun2026_setpoints` prepares the model and returns it.

    Besides the SET of each zone (``SET_<zone>``), it sets in each timestep the causal TSV of the zone
    (``TSV_causal_<zone>``, :func:`causal_tsv` of its SET) and its occupied hours with the SET within the band of TSV
    ±tsv_limit (``HoursInCausalBand_<zone>``: the length of the timestep in hours, ZoneTimeStep, if the zone is
    occupied, the sensor ``Occ_count_<zone>`` of the ACCIS, and its SET is within the band, and 0 otherwise; as the hour
    counters of the ACCIS, the SET is that of the conditions of the previous timestep and the occupants those of the
    timestep), which EnergyPlus reports (the band is that of ``tsv_limit`` in both comfort modes). The minimum and
    maximum of the setpoints of B5 (``heating_setpoint_minimum`` and ``cooling_setpoint_maximum``) bound its setpoints
    in the EMS after it, as those of any hook (decision 3 of the author: no own minimum): in each zone without a
    minimum heating setpoint (``heating_minimums``) whose heating setpoint falls below
    :data:`SET_HEATING_WARNING_TEMPERATURE`, it warns once (in the process of the simulation), and keeps the first such
    setpoint in :attr:`low_heating_setpoints`.

    :param zones: The zones, by their names in the EMS objects.
    :param comfort_mode: 1 or 'SET band' (the default), or 2 or 'SET neutral +/- offset'
        (:data:`SUN2026_COMFORT_MODES`).
    :param category: 80 (the default) or 90: both give the band of TSV ±0.5.
    :param tsv_limit: The half-width of the band of TSV (None for 0.5; 0.7 and 1.0 with a warning).
    :param set_offset: With comfort mode 2, the offset of the setpoints from the neutral SET (K).
    :param tr_mode: 'zone' (the default) or 'equal_air' (:data:`TR_MODES`).
    :param heating_minimums: The minimum heating setpoint of each zone (°C, ``{zone: None}`` without it), which
        :func:`apply_sun2026_setpoints` reads from the model.
    :param met: ``met``, ``clo``, ``air_speed``, ``position``, ``tolerance_k`` (0.05 K by default), ``max_iterations``,
        ``temperature_range`` and ``clothing_sources``: those of :class:`SetSetpointHook` (the metabolic rate, the
        clothing insulation and the air speed are those of the People objects by default: decision 5 of the author).
    :ivar band: The SET of the limits of the band of TSV ±tsv_limit (°C).
    :ivar low_heating_setpoints: The first heating setpoint below :data:`SET_HEATING_WARNING_TEMPERATURE` of each zone
        without a minimum heating setpoint.
    """

    #: Its comfort standard (:mod:`accim.sim.standards`)
    comfort_standard = 24

    def __init__(self, zones: Sequence[str], comfort_mode: Any = 1, category: int = 80,
                 tsv_limit: Optional[float] = None, set_offset: Optional[float] = None, tr_mode: str = 'zone',
                 met: Optional[float] = None, clo: Optional[float] = None, air_speed: Optional[float] = None,
                 position: Optional[str] = None, tolerance_k: float = 0.05, max_iterations: int = 20,
                 temperature_range: Optional[Tuple[float, float]] = None,
                 heating_minimums: Optional[Dict[str, Optional[float]]] = None,
                 clothing_sources: Optional[Dict[str, str]] = None):
        heating, cooling = sun2026_set_setpoints(comfort_mode, tsv_limit, set_offset, category)
        super().__init__(zones, cooling, heating, met=met, clo=clo, air_speed=air_speed, position=position,
                         tolerance_k=tolerance_k, max_iterations=max_iterations, temperature_range=temperature_range,
                         method='bisection', tr_mode=tr_mode, clothing_sources=clothing_sources)
        self.comfort_mode = _sun2026_comfort_mode(comfort_mode)
        self.category = category
        self.tsv_limit = _sun2026_tsv_limit(tsv_limit, category, warn=False)
        self.set_offset = None if set_offset is None else float(set_offset)
        self.band = ((-self.tsv_limit - SUN2026_TSV_INTERCEPT) / SUN2026_TSV_SLOPE,
                     (self.tsv_limit - SUN2026_TSV_INTERCEPT) / SUN2026_TSV_SLOPE)
        minimums = dict(heating_minimums or {})
        self.heating_minimums: Dict[str, Optional[float]] = {zone: minimums.get(zone) for zone in self.zones}
        self.low_heating_setpoints: Dict[str, float] = {}

    def __repr__(self) -> str:
        return (f'Sun2026SetpointHook(zones={self.zones!r}, comfort_mode={self.comfort_mode}, '
                f'category={self.category!r}, tsv_limit={self.tsv_limit}, set_offset={self.set_offset}, '
                f'tr_mode={self.tr_mode!r})')

    def _given(self, controller, zone: str, heating: float, cooling: float) -> None:
        if (heating >= SET_HEATING_WARNING_TEMPERATURE or self.heating_minimums.get(zone) is not None
                or zone in self.low_heating_setpoints):
            return
        self.low_heating_setpoints[zone] = heating
        warnings.warn(f'The heating setpoint of comfort standard 24 (INT Sun2026 SET) of the zone {zone} is '
                      f'{heating:.2f} °C, below {SET_HEATING_WARNING_TEMPERATURE} °C, and the zone has no minimum '
                      f'heating setpoint: give heating_setpoint_minimum (AddAccis, modify_accis or zone_arguments) '
                      f'before apply_sun2026_setpoints to bound it (the inverted heating setpoint falls below 18 °C '
                      f'from about 0.73 clo at 0.1 m/s).', UserWarning, stacklevel=2)

    def _report(self, controller, zone: str, value: float) -> None:
        controller.set(f'TSV_causal_{zone}', causal_tsv(value))
        occupants = controller.get(f'Occ_count_{zone}')
        step = controller.get('ZoneTimeStep')
        occupied = occupants is not None and occupants > 0 and step is not None
        controller.set(f'{_SUN2026_HOURS}_{zone}',
                       step if occupied and self.band[0] <= value <= self.band[1] else 0.0)


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


#: The prefixes of the EMS sensors of the zones of the hooks of the ATHB and of the SET, which a model cannot have twice
_HOOK_SENSOR_PREFIXES = tuple(_SENSORS) + tuple(_SET_SENSORS) + tuple(_PEOPLE_SENSORS.values())
#: The fields of the People objects that the hooks of the SET read, by input
_PEOPLE_FIELDS = {
    'activity': 'Activity_Level_Schedule_Name',
    'work_efficiency': 'Work_Efficiency_Schedule_Name',
    'clothing_method': 'Clothing_Insulation_Calculation_Method',
    'clothing_method_schedule': 'Clothing_Insulation_Calculation_Method_Schedule_Name',
    'clothing': 'Clothing_Insulation_Schedule_Name',
    'air_speed': 'Air_Velocity_Schedule_Name',
}


def _people_inputs(building, zones: Sequence[str], needed: Sequence[str], pierce: bool = False) -> Dict[str, dict]:
    """The schedules of the People objects of each zone that a hook of the SET reads (task F1): ``{zone: {'activity':
    name, 'clothing': name, 'clothing_method_schedule': name, 'air_speed': name, 'clothing_source': 'schedule',
    'dynamic' or 'method', 'occupants': the key of the outputs of its first occupant instance}}``.

    :param needed: The inputs that the hook reads from the People objects: 'met', 'clo' and 'air_speed'.
    :param pierce: True if the People objects get the Pierce model, which needs the work efficiency, clothing insulation
        and air velocity schedules (Input Output Reference 25.2, 1.14.2.1.20).
    :raises ValueError: If a zone has no People object, its People objects have different schedules, or a schedule
        that the hook or the Pierce model needs is missing.
    """
    from accim.sim.targets import resolve_targets
    from accim.utils.people import get_people_objects

    targets = {target.ems_suffix.upper(): target for target in resolve_targets(building)}
    objects = {str(people.Name).strip().upper(): people for people in get_people_objects(building)}
    inputs: Dict[str, dict] = {}
    for zone in zones:
        target = targets.get(str(zone).upper())
        people = [] if target is None else [objects[name.upper()] for name in target.people_names
                                            if name.upper() in objects]
        if not people:
            raise ValueError(f'The zone {zone} has no People object, whose schedules the hook of the SET reads.')
        values = {}
        for name, field in _PEOPLE_FIELDS.items():
            found = list(dict.fromkeys(str(getattr(item, field, '') or '').strip() for item in people))
            if len({value.upper() for value in found}) > 1:
                raise ValueError(f'The People objects of the zone {zone} ({", ".join(str(p.Name) for p in people)}) '
                                 f'have different values of {field.replace("_", " ")} ({found}): the hook of the SET '
                                 f'reads one of each zone.')
            values[name] = found[0]
        source = _CLOTHING_SOURCES.get((values['clothing_method'] or 'ClothingInsulationSchedule').upper())
        if source is None:
            raise ValueError(f"The People objects of the zone {zone} have the clothing insulation calculation method "
                             f"{values['clothing_method']!r}, which the hook of the SET does not read.")
        required = ['activity'] if 'met' in needed else []
        if 'clo' in needed or pierce:
            required += ['clothing'] if source == 'schedule' else []
            required += ['clothing', 'clothing_method_schedule'] if source == 'method' else []
        required += ['air_speed'] if 'air_speed' in needed or pierce else []
        required += ['work_efficiency'] if pierce else []
        missing = [_PEOPLE_FIELDS[name].replace('_', ' ') for name in dict.fromkeys(required) if not values[name]]
        if missing:
            raise ValueError(f'The People objects of the zone {zone} have no {", ".join(missing)}, which '
                             f'{"the Pierce model and " if pierce else ""}the hook of the SET need.')
        inputs[zone] = dict(values, clothing_source=source, occupants=target.sensor_key)
    return inputs


def _add_people_sensors(building, inputs: Dict[str, dict], needed: Sequence[str]) -> None:
    """Add the EMS sensors of the inputs of the People objects of each zone that a hook of the SET reads (see
    :class:`SetSetpointHook`): Schedule Value of their schedules, and Zone Thermal Comfort Clothing Value of their
    first occupant instance with the dynamic clothing model."""
    for zone, values in inputs.items():
        sensors = []
        if 'met' in needed:
            sensors.append(('activity', values['activity'], 'Schedule Value'))
        if 'clo' in needed:
            source = values['clothing_source']
            if source in ('schedule', 'method'):
                sensors.append(('clothing', values['clothing'], 'Schedule Value'))
            if source in ('dynamic', 'method'):
                sensors.append(('clothing_value', values['occupants'], _CLOTHING_VALUE_OUTPUT))
            if source == 'method':
                sensors.append(('clothing_method', values['clothing_method_schedule'], 'Schedule Value'))
        if 'air_speed' in needed:
            sensors.append(('air_speed', values['air_speed'], 'Schedule Value'))
        for name, key, variable in sensors:
            building.newidfobject('EnergyManagementSystem:Sensor', Name=f'{_PEOPLE_SENSORS[name]}_{zone}',
                                  OutputVariable_or_OutputMeter_Index_Key_Name=key,
                                  OutputVariable_or_OutputMeter_Name=variable)


def _output_frequencies(building, output_frequencies: Optional[Sequence[str]]) -> List[str]:
    """The reporting frequencies of the outputs of a hook: those given, or those of the EMS outputs of the model."""
    if output_frequencies is None:
        return _model_output_frequencies(building)
    return [str(frequency).capitalize() for frequency in output_frequencies]


#: The thermal comfort models of the People objects with which EnergyPlus reports the output Zone Thermal Comfort
#: Clothing Value (ThermalComfort.cc of EnergyPlus 25.1, the outputs of the Fanger, Pierce and KSU models)
_CLOTHING_VALUE_MODELS = ('FANGER', 'PIERCE', 'KSU')


def _needs_comfort_model(building, people: Dict[str, dict]) -> bool:
    """Whether the People objects of the zones of a hook of the SET that read the clothing insulation of the dynamic
    clothing model (the sensors ``SET_CloValue_<zone>``) need a thermal comfort model that reports it: True if one of
    the objects with the thermal comfort models of the model (the People objects, or the People:Definition objects of
    EnergyPlus 26.2) has none of :data:`_CLOTHING_VALUE_MODELS`."""
    from accim.sim.people import _comfort_model_targets

    if not any(values['clothing_source'] in ('dynamic', 'method') for values in people.values()):
        return False
    for target in _comfort_model_targets(building):
        models = {str(getattr(target, field) or '').strip().upper() for field in target.fieldnames
                  if field.startswith('Thermal_Comfort_Model_')}
        if not models & set(_CLOTHING_VALUE_MODELS):
            return True
    return False


def apply_set_setpoints(building, set_cooling_setpoint: float, set_heating_setpoint: float,
                        met: Optional[float] = None, clo: Optional[float] = None, air_speed: Optional[float] = None,
                        position: Optional[str] = None, tolerance_k: float = 0.1, max_iterations: int = 20,
                        temperature_range: Optional[Tuple[float, float]] = None, method: str = 'table',
                        output_frequencies: Optional[Sequence[str]] = None,
                        tr_mode: str = 'equal_air') -> SetSetpointHook:
    """Prepare a model with the ACCIS (temperature setpoints and full air-conditioning, as :func:`apply_athb_setpoints`)
    for the setpoints of the standard effective temperature (SET), and return the hook that sets them
    (:class:`SetSetpointHook`, proposal A6, and tasks G3 and F1 of the review of accim 1.2.0).

    Its zones get the EMS sensors ``SET_MAT_<zone>``, ``SET_MRT_<zone>`` and ``SET_RH_<zone>`` (mean air temperature, mean
    radiant temperature and relative humidity), the outputs of these variables of EnergyPlus (*Zone Mean Air
    Temperature*, *Zone Mean Radiant Temperature* and *Zone Air Relative Humidity*, with which :func:`set_of_results`
    calculates the SET of the zones after the simulation), with ``method='bisection'`` the global variable and output
    ``SET_<zone>`` (the SET of the zone, averaged), and the program ``ApplyHookSetpoints_<zone>`` with which the hook
    gives its setpoints to the ACCIS (:mod:`accim.sim.ems.hook_setpoints`; see :func:`apply_athb_setpoints`). The
    setpoints of the SET have no default: they are those of the study; so the metabolic rate, the clothing insulation
    and the air speed, unless the hook reads them from the People object of each zone in each timestep (None, with
    ``method='bisection'``: the zones then get the EMS sensors of their schedules, ``SET_Act_<zone>``,
    ``SET_Clo_<zone>`` or ``SET_CloValue_<zone>`` and ``SET_CloMethod_<zone>``, and ``SET_Vel_<zone>``, see
    :class:`SetSetpointHook`). With ``clo`` None and the clothing insulation of the dynamic clothing model in a zone
    (the Clothing Insulation Calculation Method DynamicClothingModelASHRAE55, or CalculationMethodSchedule), the People
    objects get the Pierce model (:func:`accim.sim.people.add_thermal_comfort_model`) unless they all have the Fanger,
    Pierce or KSU model, since EnergyPlus reports the clothing insulation that the sensors ``SET_CloValue_<zone>``
    read (*Zone Thermal Comfort Clothing Value*) only with them, and stops before the simulation otherwise (finding A3
    of the self-audit of 2026-11-11). The model must be simulated with the backend of the Python API and the hook
    (``run_ep(backend='api', hooks=[hook])``): without it, its setpoints are those of the ACCIS (and ``SET_<zone>`` is
    0).

    :param building: The model (eppy), changed in place.
    :param met: The metabolic rate (met), or None for that of the People objects (with ``method='bisection'``); and so
        ``clo`` and ``air_speed``.
    :param method: 'table' (the default) or 'bisection' (see :class:`SetSetpointHook`).
    :param output_frequencies: The reporting frequencies of the outputs ('timestep', 'hourly'...); None (the default)
        for those of the EMS outputs of the model (those of the ACCIS), or hourly if it has none.
    :param tr_mode: 'equal_air' (the default: the setpoints are the operative temperatures whose SET is that of the
        setpoint with the mean radiant temperature equal to the air temperature) or 'zone' (with
        ``method='bisection'``: the air temperatures whose SET is that of the setpoint with the mean radiant
        temperature of the zone, given to the thermostats of the ACCIS as operative temperatures, see
        :class:`SetSetpointHook`).
    :return: The hook, with the other arguments, and the keys of the zones in the outputs (``hook.keys``).
    :raises ValueError: If the model has no ACCIS of accim 1.0.0 or later, is in mixed mode, has already the objects of
        the SET or of the ATHB (both would set the same thermostats), has not the People objects whose inputs the hook
        reads (or, when they get the Pierce model, the schedules that it needs, or an empty field for it), or an
        argument is not valid.
    """
    keys = _model_zones(building, 'the SET', _HOOK_SENSOR_PREFIXES, running_mean=False)
    needed = [name for name, value in (('met', met), ('clo', clo), ('air_speed', air_speed)) if value is None]
    people = _people_inputs(building, list(keys), needed) if needed else {}
    # The clothing insulation of the dynamic clothing model is an output of the thermal comfort models of EnergyPlus
    # (finding A3 of the self-audit of 2026-11-11), which the People objects need for the sensors SET_CloValue_<zone>
    pierce = 'clo' in needed and _needs_comfort_model(building, people)
    if pierce:
        people = _people_inputs(building, list(keys), needed, pierce=True)
    hook = SetSetpointHook(list(keys), set_cooling_setpoint=set_cooling_setpoint,
                           set_heating_setpoint=set_heating_setpoint, met=met, clo=clo, air_speed=air_speed,
                           position=position, tolerance_k=tolerance_k, max_iterations=max_iterations,
                           temperature_range=temperature_range, method=method, tr_mode=tr_mode,
                           clothing_sources={zone: values['clothing_source'] for zone, values in people.items()})
    hook.keys = dict(keys)
    if pierce:
        from accim.sim.people import add_thermal_comfort_model

        # It raises its errors before changing anything
        add_thermal_comfort_model(building, 'Pierce')
    frequencies = _output_frequencies(building, output_frequencies)
    _add_hook_objects(building, keys, _SET_SENSORS, _SET_OUTPUTS if method == 'bisection' else {}, frequencies)
    _add_people_sensors(building, people, needed)
    _add_zone_output_variables(building, keys, _SET_ZONE_VARIABLES, frequencies)
    return hook


def sun2026_zone_outputs(zone: str) -> List[str]:
    """The names of the outputs of comfort standard 24 of a zone (:func:`apply_sun2026_setpoints`): its SET, its causal
    TSV and its occupied hours within the band of TSV."""
    return [f'{prefix}_{zone}' for prefix in (*_SET_OUTPUTS, *_SUN2026_OUTPUTS, _SUN2026_HOURS)]


def apply_sun2026_setpoints(building, comfort_mode: Any = 1, category: int = 80, tsv_limit: Optional[float] = None,
                            set_offset: Optional[float] = None, tr_mode: str = 'zone', position: Optional[str] = None,
                            tolerance_k: float = 0.05, max_iterations: int = 20,
                            temperature_range: Optional[Tuple[float, float]] = None,
                            output_frequencies: Optional[Sequence[str]] = None) -> Sun2026SetpointHook:
    """Prepare a model with the ACCIS (temperature setpoints and full air-conditioning, as :func:`apply_set_setpoints`)
    for comfort standard 24, INT Sun2026 SET (the causal SET model of Sun, Brager & Schiavon, 2026, Energy and
    Buildings 370, 118097; task F1 of block F, with the decisions of the author of 2026-11-10 in
    ``notes/decisions.md``), and return its hook (:class:`Sun2026SetpointHook`), which the backend of the Python API
    runs (``run_ep(backend='api', hooks=[hook])``).

    The setpoints of the SET of its comfort mode (:func:`sun2026_set_setpoints`: the band of TSV ±tsv_limit, 19.1 and
    28.2 °C with 0.5, or the neutral SET of 23.6 °C ± ``set_offset``) are inverted by bisection in each timestep (to
    0.05 K by default, within 10 to 40 °C) with the relative humidity of each zone, by default its mean radiant
    temperature (``tr_mode='zone'``: the air temperatures found are given to the thermostats of the ACCIS as the
    operative temperatures (air + mean radiant temperature)/2), and the metabolic rate, clothing insulation and air
    speed of the schedules of its People object (with its Clothing Insulation Calculation Method, which
    :func:`accim.sim.people.set_clothing_method` sets: a schedule or the dynamic clothing model of ASHRAE 55; the fans
    are those of the air velocity schedule). Its zones get the objects of :func:`apply_set_setpoints` with
    ``method='bisection'`` and the inputs of the People objects, the outputs ``TSV_causal_<zone>`` (averaged) and
    ``HoursInCausalBand_<zone>`` (summed, hours) of the hook (:func:`sun2026_zone_outputs`), and the People objects get
    the Pierce model (:func:`accim.sim.people.add_thermal_comfort_model`) and the output of its SET,
    ``Zone Thermal Comfort Pierce Model Standard Effective Temperature``, for the comparison of the SET of EnergyPlus
    with that of accim (``notes/decisions.md``, task E-F1). The minimum and maximum of the setpoints of the zones
    (``heating_setpoint_minimum`` and ``cooling_setpoint_maximum`` of B5) bound its setpoints after the inversion: give
    them before this function, which reads the minimums for the warning of the hook (see
    :class:`Sun2026SetpointHook`). Comfort standard 24 has no EMS code: :class:`accim.sim.accis.AddAccis` cannot write
    it, and the EMS backend cannot run the hook (the fallback of an Erl loop on the SET of the previous timestep, v03
    A6a, is an entry of ``TODO.md``); the comfort temperature and the applicability limits of the zones stay those of
    their comfort standard.

    :param building: The model (eppy), changed in place.
    :param comfort_mode: 1 or 'SET band' (the default), or 2 or 'SET neutral +/- offset'.
    :param category: 80 (the default) or 90: both give the band of TSV ±0.5 of the paper.
    :param tsv_limit: The half-width of the band of TSV: None for 0.5; 0.7 and 1.0 are a linear extrapolation of the
        model, with a warning.
    :param set_offset: With comfort mode 2, the offset of the setpoints from the neutral SET (K of SET).
    :param tr_mode: 'zone' (the default) or 'equal_air' (the mean radiant temperature equal to the air temperature).
    :param position: The posture of the SET, or None (the default) for 'sitting' with 1.2 met or less and 'standing'
        above it, with the metabolic rate of each timestep.
    :param tolerance_k: The largest width of the interval of the bisection (K), 0.05 by default.
    :param max_iterations: The largest number of iterations of the bisection.
    :param temperature_range: The range of the temperatures of the bisection (°C), 10 to 40 °C by default.
    :param output_frequencies: The reporting frequencies of the outputs; None (the default) for those of the EMS outputs
        of the model.
    :return: The hook, with the keys of the zones in the outputs (``hook.keys``).
    :raises ValueError: If the model has no ACCIS of accim 1.0.0 or later, is in mixed mode, has already the objects of
        the SET or of the ATHB, its People objects have not the schedules that the hook and the Pierce model need (or
        no empty field for the Pierce model), or an argument is not valid.
    """
    from accim.sim.ems.setpoint_limits import zone_limits
    from accim.sim.people import PIERCE_SET_OUTPUT, add_thermal_comfort_model

    keys = _model_zones(building, 'comfort standard 24 (INT Sun2026 SET)', _HOOK_SENSOR_PREFIXES, running_mean=False)
    needed = ['met', 'clo', 'air_speed']
    people = _people_inputs(building, list(keys), needed, pierce=True)
    limits = zone_limits(building)
    hook = Sun2026SetpointHook(list(keys), comfort_mode=comfort_mode, category=category, tsv_limit=tsv_limit,
                               set_offset=set_offset, tr_mode=tr_mode, position=position, tolerance_k=tolerance_k,
                               max_iterations=max_iterations, temperature_range=temperature_range,
                               heating_minimums={zone: limits.get(zone, {}).get('AHSTmin') for zone in keys},
                               clothing_sources={zone: values['clothing_source'] for zone, values in people.items()})
    hook.keys = dict(keys)
    # The Pierce model first: add_thermal_comfort_model raises its errors before changing anything
    add_thermal_comfort_model(building, 'Pierce')
    frequencies = _output_frequencies(building, output_frequencies)
    _add_hook_objects(building, keys, _SET_SENSORS, {**_SET_OUTPUTS, **_SUN2026_OUTPUTS}, frequencies,
                      summed={_SUN2026_HOURS: 'H'})
    _add_people_sensors(building, people, needed)
    _add_zone_output_variables(building, keys, _SET_ZONE_VARIABLES, frequencies)
    occupants = {zone: values['occupants'] for zone, values in people.items()}
    _add_zone_output_variables(building, occupants, [PIERCE_SET_OUTPUT], frequencies)
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

    missing = [name for name in ('met', 'clo', 'air_speed') if getattr(hook, name) is None]
    if missing:
        raise ValueError(f'The hook reads {missing} from the People objects of the zones in each timestep, which the '
                         f"results have not: its SET is the output SET_<zone> (method='bisection').")
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
