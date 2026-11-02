# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Schedules of the HVAC systems: those that accim adds to the thermostats and the availability of the VRF systems
and of the existing HVAC systems, and the values of the schedules of a model."""

from typing import Dict, Iterable, Optional, Set

from accim.sim.idf_tools import try_objects
from accim.sim.model import AccimModel

__all__ = [
    'ALWAYS_ON_SCHEDULE',
    'DUAL_SETPOINT_CONTROL_SCHEDULE',
    'RADIATIVE_FRACTION_SCHEDULE',
    'add_compact_schedule',
    'add_radiative_fraction_schedule',
    'is_always_on',
    'schedule_values',
]

#: The schedule that is always 1 (the availability of the VRF systems, by default).
ALWAYS_ON_SCHEDULE = 'On 24/7'
#: The control type schedule of the thermostats that always use their ThermostatSetpoint:DualSetpoint object (4).
DUAL_SETPOINT_CONTROL_SCHEDULE = 'Control type schedule: Always 4'
#: The radiative fraction of the operative temperature that the thermostats control: 0.5, as in the output 'Zone
#: Operative Temperature', but 0 (the air temperature) on the design days, so that the sizing calculations size the
#: HVAC systems for the air temperature, as without operative temperature control.
RADIATIVE_FRACTION_SCHEDULE = 'TypOperativeTempControlSch'

#: The schedules that other objects refer to (one namespace in EnergyPlus).
_SCHEDULE_TYPES = ('Schedule:Year', 'Schedule:Compact', 'Schedule:Constant', 'Schedule:File')
_DESIGN_DAYS = {'SUMMERDESIGNDAY', 'WINTERDESIGNDAY'}


def add_compact_schedule(model: AccimModel, name: str, *fields: str, type_limits: str = 'Any Number') -> None:
    """Add a Schedule:Compact object with its fields, unless the model has one with that name."""
    if name in [s.Name for s in model.idf.idfobjects['Schedule:Compact']]:
        model.log(f'{name} Schedule already was in the model')
        return
    numbered = {f'Field_{n}': value for n, value in enumerate(fields, start=1)}
    model.idf.newidfobject('Schedule:Compact', Name=name, Schedule_Type_Limits_Name=type_limits, **numbered)
    model.log(f'{name} Schedule has been added')


def add_radiative_fraction_schedule(model: AccimModel) -> None:
    """Add the schedule of the radiative fraction of the operative temperature thermostats
    (:data:`RADIATIVE_FRACTION_SCHEDULE`) if the model does not have it."""
    add_compact_schedule(model, RADIATIVE_FRACTION_SCHEDULE, 'Through: 12/31',
                         'For: SummerDesignDay WinterDesignDay', 'Until: 24:00,0', 'For: AllOtherDays',
                         'Until: 24:00, 0.5', type_limits='Temperature')


def _schedules(idf, types: Iterable[str]) -> Dict[str, object]:
    return {obj.Name.upper(): obj for object_type in types for obj in try_objects(idf, object_type)}


def _number(value) -> Optional[float]:
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _day_values(idf, names: Iterable[str]) -> Optional[Set[float]]:
    days = _schedules(idf, ('Schedule:Day:Hourly', 'Schedule:Day:Interval', 'Schedule:Day:List'))
    values: Set[float] = set()
    for name in names:
        day = days.get(str(name).strip().upper())
        if day is None:
            return None
        kind = day.obj[0].upper()
        if kind == 'SCHEDULE:DAY:HOURLY':
            fields = day.obj[3:]
        elif kind == 'SCHEDULE:DAY:INTERVAL':
            fields = day.obj[5::2]
        else:
            fields = day.obj[5:]
        numbers = [_number(f) for f in fields if str(f).strip() != '']
        if None in numbers:
            return None
        values.update(numbers)
    return values


def _week_day_names(idf, names: Iterable[str]) -> Optional[Set[str]]:
    """The day schedules of the run periods (not those of the design days) of some week schedules."""
    weeks = _schedules(idf, ('Schedule:Week:Daily', 'Schedule:Week:Compact'))
    days: Set[str] = set()
    for name in names:
        week = weeks.get(str(name).strip().upper())
        if week is None:
            return None
        if week.obj[0].upper() == 'SCHEDULE:WEEK:DAILY':
            # Sunday to Saturday and Holiday, and the custom days, which special days can use (not the design days)
            days.update(str(d) for d in week.obj[2:10] + week.obj[12:14] if str(d).strip())
            continue
        for day_types, day in zip(week.obj[2::2], week.obj[3::2]):
            types = str(day_types).upper().replace('FOR:', '').split()
            if not set(types) <= _DESIGN_DAYS:
                days.add(str(day))
    return days


def _compact_values(fields) -> Optional[Set[float]]:
    values: Set[float] = set()
    design_days = False
    # accim writes some pairs of fields in one ('Until: 24:00,1')
    for token in (t.strip() for field in fields for t in str(field).split(',')):
        upper = token.upper()
        if not token or upper.startswith(('THROUGH:', 'UNTIL:', 'INTERPOLATE:')):
            continue
        if upper.startswith('FOR:'):
            design_days = set(upper[len('FOR:'):].split()) <= _DESIGN_DAYS
            continue
        number = _number(token)
        if number is None:
            return None
        if not design_days:
            values.add(number)
    return values


def schedule_values(idf, name: str) -> Optional[Set[float]]:
    """The values that a schedule takes on the days of the run periods (those of the design days are left out).

    :param idf: The eppy or besos IDF object.
    :param name: The name of a Schedule:Constant, Schedule:Compact or Schedule:Year object (in any case).
    :return: The set of values, or None if accim cannot read them: a Schedule:File, a schedule that is not in the
        model, or one with values that are not numbers.
    """
    schedule = _schedules(idf, _SCHEDULE_TYPES).get(str(name).strip().upper())
    if schedule is None:
        return None
    kind = schedule.obj[0].upper()
    if kind == 'SCHEDULE:CONSTANT':
        value = _number(schedule.obj[3]) if len(schedule.obj) > 3 else 0.0
        return None if value is None else {value}
    if kind == 'SCHEDULE:COMPACT':
        return _compact_values(schedule.obj[3:])
    if kind == 'SCHEDULE:YEAR':
        days = _week_day_names(idf, [w for w in schedule.obj[3::5] if str(w).strip()])
        return None if days is None else _day_values(idf, days)
    return None


def is_always_on(idf, name: str) -> Optional[bool]:
    """Whether a schedule is above 0 on all the days of the run periods (an availability schedule that never
    switches off).

    :param idf: The eppy or besos IDF object.
    :param name: The name of the schedule; a blank name (no schedule) is always on, as in EnergyPlus.
    :return: True or False, or None if accim cannot read the values of the schedule (see :func:`schedule_values`).
    """
    if not str(name).strip():
        return True
    values = schedule_values(idf, name)
    if values is None:
        return None
    return all(value > 0 for value in values)
