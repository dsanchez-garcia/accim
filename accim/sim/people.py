# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Thermal comfort models of the occupants (People, and People:Definition in EnergyPlus 26.2), and the method of their
clothing insulation (People, and People:Instance in EnergyPlus 26.2)."""

import warnings
from typing import Any, Optional

from accim.sim.hvac.schedules import schedule_values
from accim.sim.model import AccimModel
from accim.utils.people import get_people_definition, get_people_objects

__all__ = ['CLOTHING_METHODS', 'set_clothing_method', 'set_comfort_models']

#: The methods of the field Clothing Insulation Calculation Method of the People objects (in the IDDs of EnergyPlus 9.4
#: to 26.2, and of the People:Instance objects in 26.2)
CLOTHING_METHODS = ('ClothingInsulationSchedule', 'DynamicClothingModelASHRAE55', 'CalculationMethodSchedule')
#: The schedules that the fields of the People objects can name
_SCHEDULE_TYPES = ('Schedule:Year', 'Schedule:Compact', 'Schedule:Constant', 'Schedule:File')


def _comfort_models(setpoint_type: str, number: int) -> list:
    models = ['AdaptiveASH55', 'AdaptiveCEN15251', 'Fanger' if setpoint_type == 'pmv' else '']
    return (models + [''] * number)[:number]


def set_comfort_models(model: AccimModel) -> None:
    """Set the thermal comfort models that accim needs in the occupants of the model.

    The People objects and, in models of EnergyPlus 26.2 with People:Instance objects, the
    People:Definition objects they reference get AdaptiveASH55 and AdaptiveCEN15251 as models 1 and 2
    (whose running mean outdoor temperatures accim reads), Fanger as model 3 if ``setpoint_type`` is 'pmv',
    and no other model.

    :raises ValueError: If a People:Instance object references a People:Definition object that is not
        in the model.
    """
    idf = model.idf
    for people in idf.idfobjects['PEOPLE']:
        fields = [f'Thermal_Comfort_Model_{n}_Type' for n in range(1, 8)
                  if f'Thermal_Comfort_Model_{n}_Type' in people.fieldnames]
        for field, comfort_model in zip(fields, _comfort_models(model.setpoint_type, len(fields))):
            setattr(people, field, comfort_model)

    definitions = []
    # The People:Instance objects exist since EnergyPlus 26.2 (the keys of idfobjects are in capitals)
    for instance in idf.idfobjects.get('PEOPLE:INSTANCE', []):
        definition = get_people_definition(idf, instance)
        if definition is None:
            raise ValueError(
                f'The People:Instance object "{instance.Name}" references the People:Definition object '
                f'"{instance.People_Definition_Name}", which is not in the model.'
            )
        if all(definition is not d for d in definitions):
            definitions.append(definition)
    for definition in definitions:
        for n, comfort_model in enumerate(_comfort_models(model.setpoint_type, 7), start=1):
            setattr(definition, f'Thermal_Comfort_Model_{n}_Type', comfort_model)

    model.log('The people objects in the model have been amended.')
    if definitions:
        model.log('The People:Definition objects of the People:Instance objects in the model have been amended.')


def set_clothing_method(building: Any, method: str, schedule: Optional[str] = None,
                        calculation_method_schedule: Optional[str] = None, verbose: bool = True) -> None:
    """Set the Clothing Insulation Calculation Method of all the People objects (and of the People:Instance objects,
    in models of EnergyPlus 26.2), with which EnergyPlus calculates the clothing insulation of the thermal comfort
    models.

    :param building: The eppy or besos IDF object.
    :param method: 'ClothingInsulationSchedule' (the clothing insulation schedule), 'DynamicClothingModelASHRAE55' (the
        dynamic clothing model of ASHRAE 55, from the outdoor air temperature at 6 a.m.) or 'CalculationMethodSchedule'
        (a schedule chooses the method: 1, the clothing insulation schedule; 2, the dynamic model), in any case
        (:data:`CLOTHING_METHODS`).
    :param schedule: The name of the clothing insulation schedule (the field Clothing Insulation Schedule Name), with
        'ClothingInsulationSchedule', or with 'CalculationMethodSchedule' for the periods of the method 1. If None, the
        People objects keep theirs.
    :param calculation_method_schedule: With 'CalculationMethodSchedule', and only with it, the name of the schedule
        that chooses the method (the field Clothing Insulation Calculation Method Schedule Name), with the values 1 and
        2.
    :param verbose: If True, prints the changes.
    :raises ValueError: Before changing anything, if the method is not one of :data:`CLOTHING_METHODS`, if
        ``calculation_method_schedule`` is missing with 'CalculationMethodSchedule' or given with another method, if
        ``schedule`` is given with 'DynamicClothingModelASHRAE55', if a schedule is not in the model, or if the
        calculation method schedule has values other than 1 and 2.
    """
    methods = {m.upper(): m for m in CLOTHING_METHODS}
    if str(method).strip().upper() not in methods:
        raise ValueError(f'method must be one of {list(CLOTHING_METHODS)}, not {method!r}.')
    method = methods[str(method).strip().upper()]
    if method == 'CalculationMethodSchedule' and calculation_method_schedule is None:
        raise ValueError("The method 'CalculationMethodSchedule' needs calculation_method_schedule, the schedule that "
                         "chooses the method (1, the clothing insulation schedule; 2, the dynamic model).")
    if method != 'CalculationMethodSchedule' and calculation_method_schedule is not None:
        raise ValueError(f"calculation_method_schedule is only used with the method 'CalculationMethodSchedule', not "
                         f"with {method!r}.")
    if method == 'DynamicClothingModelASHRAE55' and schedule is not None:
        raise ValueError("EnergyPlus does not read the clothing insulation schedule with the method "
                         "'DynamicClothingModelASHRAE55': do not give schedule.")
    names = {str(s.Name).strip().upper() for schedule_type in _SCHEDULE_TYPES
             for s in building.idfobjects.get(schedule_type.upper(), [])}
    missing = [name for name in (schedule, calculation_method_schedule)
               if name is not None and str(name).strip().upper() not in names]
    if missing:
        raise ValueError(f'The schedules {missing} are not in the model (as {", ".join(_SCHEDULE_TYPES)} objects).')
    if calculation_method_schedule is not None:
        values = schedule_values(building, calculation_method_schedule)
        if values is not None and not values <= {1.0, 2.0}:
            raise ValueError(f'The calculation method schedule {calculation_method_schedule!r} must have the values '
                             f'1 (the clothing insulation schedule) and 2 (the dynamic model), not {sorted(values)}.')

    for people in get_people_objects(building):
        people.Clothing_Insulation_Calculation_Method = method
        if calculation_method_schedule is not None:
            people.Clothing_Insulation_Calculation_Method_Schedule_Name = calculation_method_schedule
        if schedule is not None:
            people.Clothing_Insulation_Schedule_Name = schedule
        if method != 'DynamicClothingModelASHRAE55' and not str(people.Clothing_Insulation_Schedule_Name).strip():
            warnings.warn(f"The People object '{people.Name}' has no clothing insulation schedule, which EnergyPlus "
                          f"needs with the method {method!r} for the thermal comfort models.")
        if verbose:
            print(f"Set the clothing insulation calculation method of '{people.Name}': {method}")
