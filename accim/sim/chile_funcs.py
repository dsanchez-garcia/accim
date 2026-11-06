# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Functions for building energy modelling research in Chile."""

from typing import List

__all__ = ['HEATING_ACTIVATION_SCHEDULE', 'apply_heating_activation_time_sch']

#: The name of the schedule of the heating activation time.
HEATING_ACTIVATION_SCHEDULE = 'Heating_activation_time_chile'
#: The heating activation in a day of each month: on (1) or off (0) until each time.
_DAY_UNTIL_23 = (('6:00', 0), ('9:00', 1), ('17:00', 0), ('23:00', 1), ('24:00', 0))
_DAY_UNTIL_24 = (('6:00', 0), ('9:00', 1), ('17:00', 0), ('24:00', 1))
#: The last day of each month, and its heating activation.
_MONTHS = (
    ('1/31', _DAY_UNTIL_23), ('2/28', _DAY_UNTIL_23), ('3/31', _DAY_UNTIL_23), ('4/30', _DAY_UNTIL_23),
    ('5/31', _DAY_UNTIL_24), ('6/30', _DAY_UNTIL_24), ('7/31', _DAY_UNTIL_24), ('8/31', _DAY_UNTIL_24),
    ('9/30', _DAY_UNTIL_23), ('10/31', _DAY_UNTIL_24), ('11/30', _DAY_UNTIL_24), ('12/31', _DAY_UNTIL_24),
)


def _schedule_fields() -> List[str]:
    """The fields of the Schedule:Compact object of the heating activation time (after its type limits)."""
    fields = []
    for last_day, periods in _MONTHS:
        fields += [f'Through: {last_day}', 'For: AllDays']
        for until, value in periods:
            fields += [f'Until: {until}', str(value)]
    return fields


def apply_heating_activation_time_sch(idf_path: str, apply_to_occupancy: bool = True) -> None:
    """
    Applies the heating activation time for Chile.
    See reference: https://www.sciencedirect.com/science/article/pii/S0378778823003833

    Adds the schedule 'Heating_activation_time_chile' to the model (read with eppy, see
    :func:`accim.sim.accis.load_idf`) and saves it as '<model>_heat_act_time_added.idf'. Nothing is saved if the model
    already has the schedule.

    :param idf_path: The path of the IDF file.
    :param apply_to_occupancy: True to apply the same schedule to the occupancy (the People objects, and the
        People:Instance objects of EnergyPlus 26.2).
    """
    from accim.sim.accis import load_idf
    from accim.utils.people import get_people_objects

    building = load_idf(idf_path)
    if building.getobject('Schedule:Compact', HEATING_ACTIVATION_SCHEDULE) is not None:
        print(f'{HEATING_ACTIVATION_SCHEDULE} already was in the model.')
        return
    fields = {f'Field_{number}': value for number, value in enumerate(_schedule_fields(), start=1)}
    building.newidfobject('Schedule:Compact', Name=HEATING_ACTIVATION_SCHEDULE, Schedule_Type_Limits_Name='Fraction',
                          **fields)
    if apply_to_occupancy:
        for people in get_people_objects(building):
            people.Number_of_People_Schedule_Name = HEATING_ACTIVATION_SCHEDULE
        print(f'{HEATING_ACTIVATION_SCHEDULE} has been used in all occupancy schedules in the model.')
    building.savecopy(idf_path.split('.idf')[0] + '_heat_act_time_added.idf')
