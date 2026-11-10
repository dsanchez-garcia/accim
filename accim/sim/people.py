# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Thermal comfort models of the occupants (People, and People:Definition in EnergyPlus 26.2), and the method of their
clothing insulation (People, and People:Instance in EnergyPlus 26.2)."""

import warnings
from typing import Any, Optional, Sequence, Union

from accim.sim.hvac.schedules import schedule_values
from accim.sim.model import AccimModel
from accim.utils.people import get_people_definition, get_people_objects

__all__ = ['CLOTHING_METHODS', 'PIERCE_SET_OUTPUT', 'THERMAL_COMFORT_MODELS', 'THERMAL_COMFORT_OUTPUTS',
           'add_thermal_comfort_model', 'add_thermal_comfort_outputs', 'set_clothing_method', 'set_comfort_models']

#: The methods of the field Clothing Insulation Calculation Method of the People objects (in the IDDs of EnergyPlus 9.4
#: to 26.2, and of the People:Instance objects in 26.2)
CLOTHING_METHODS = ('ClothingInsulationSchedule', 'DynamicClothingModelASHRAE55', 'CalculationMethodSchedule')
#: The schedules that the fields of the People objects can name
_SCHEDULE_TYPES = ('Schedule:Year', 'Schedule:Compact', 'Schedule:Constant', 'Schedule:File')
#: The thermal comfort models that :func:`add_thermal_comfort_model` adds (choices of the fields Thermal Comfort Model n
#: Type of the People objects; AdaptiveASH55 and AdaptiveCEN15251 are those of the ACCIS, :func:`set_comfort_models`):
#: Fanger, Pierce and KSU, in the IDDs of EnergyPlus 9.4 to 26.2, and CoolingEffectASH55, the elevated air speed
#: cooling effect of ASHRAE 55-2017 (Engineering Reference 25.2, 19.1.9; task F3 of block F), in the IDDs that have it
#: (not that of 9.4)
THERMAL_COMFORT_MODELS = ('Fanger', 'Pierce', 'KSU', 'CoolingEffectASH55')
#: The output of the standard effective temperature of the Pierce model of each People object (Engineering Reference
#: 25.2, 19.1.4; the output exists when the People object has the model Pierce)
PIERCE_SET_OUTPUT = 'Zone Thermal Comfort Pierce Model Standard Effective Temperature'
#: The outputs of each People object of the thermal comfort models that :func:`add_thermal_comfort_outputs` requests
#: (Input Output Reference 25.2, 1.14.2.2: the PMV and PPD of Fanger; the SET of the Pierce model and its PMV,
#: calculated with the SET, Engineering Reference 25.2, equation 19.41; and the cooling effect of the elevated air speed
#: of ASHRAE 55 with the PMV and PPD adjusted by it, 1.14.2.2.45 to 1.14.2.2.47)
THERMAL_COMFORT_OUTPUTS = {
    'Fanger': ('Zone Thermal Comfort Fanger Model PMV', 'Zone Thermal Comfort Fanger Model PPD'),
    'Pierce': (PIERCE_SET_OUTPUT, 'Zone Thermal Comfort Pierce Model Standard Effective Temperature PMV'),
    'CoolingEffectASH55': ('Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect',
                           'Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect Adjusted PMV',
                           'Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect Adjusted PPD'),
}
#: The fields of the People objects that the thermal comfort models of :data:`THERMAL_COMFORT_OUTPUTS` need (Input
#: Output Reference 25.2, 1.14.2.1: the work efficiency, clothing insulation and air velocity schedules; the clothing
#: insulation schedule is not read with the dynamic clothing model of ASHRAE 55)
_COMFORT_MODEL_FIELDS = ('Work_Efficiency_Schedule_Name', 'Clothing_Insulation_Schedule_Name',
                         'Air_Velocity_Schedule_Name')


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


def _idd_keys(target: Any, field: str) -> Optional[set]:
    """The choices of a field of an object in the IDD of the model (in capitals), or None if eppy does not give them."""
    try:
        keys = target.getfieldidd(field).get('key')
    except (AttributeError, KeyError, TypeError, ValueError):
        return None
    return None if not keys else {str(key).strip().upper() for key in keys}


def _comfort_model_targets(building: Any) -> list:
    """The objects with the fields Thermal Comfort Model n Type: the People objects and, in models of EnergyPlus 26.2,
    the People:Definition objects that the People:Instance objects reference.

    :raises ValueError: If a People:Instance object references a People:Definition object that is not in the model.
    """
    targets = list(building.idfobjects['PEOPLE'])
    for instance in building.idfobjects.get('PEOPLE:INSTANCE', []):
        definition = get_people_definition(building, instance)
        if definition is None:
            raise ValueError(f'The People:Instance object "{instance.Name}" references the People:Definition object '
                             f'"{instance.People_Definition_Name}", which is not in the model.')
        if all(definition is not target for target in targets):
            targets.append(definition)
    return targets


def _comfort_model_changes(building: Any, comfort_models: Sequence[str]) -> list:
    """The fields Thermal Comfort Model n Type that get some thermal comfort models, in their order (the first empty
    fields of each object without them), without changing anything: a list of (object, field, model).

    :raises ValueError: If a model is not one of :data:`THERMAL_COMFORT_MODELS` or is not a choice of the field in the
        IDD of the model, a People:Instance object references a People:Definition object that is not in the model, or
        an object has not enough empty fields.
    """
    names = {m.upper(): m for m in THERMAL_COMFORT_MODELS}
    chosen = []
    for comfort_model in comfort_models:
        if str(comfort_model).strip().upper() not in names:
            raise ValueError(f'comfort_model must be one of {list(THERMAL_COMFORT_MODELS)}, not {comfort_model!r}.')
        if names[str(comfort_model).strip().upper()] not in chosen:
            chosen.append(names[str(comfort_model).strip().upper()])
    changes = []
    for target in _comfort_model_targets(building):
        fields = [f'Thermal_Comfort_Model_{n}_Type' for n in range(1, 8)
                  if f'Thermal_Comfort_Model_{n}_Type' in target.fieldnames]
        keys = _idd_keys(target, fields[0]) if fields else None
        values = {field: str(getattr(target, field)).strip() for field in fields}
        for comfort_model in chosen:
            if keys is not None and comfort_model.upper() not in keys:
                raise ValueError(f'The thermal comfort model {comfort_model!r} is not a choice of the field Thermal '
                                 f'Comfort Model 1 Type of the {target.key} objects in the IDD of the model (the IDD '
                                 f'of EnergyPlus 9.4 has no CoolingEffectASH55).')
            if comfort_model.upper() in (value.upper() for value in values.values()):
                continue
            empty = next((field for field, value in values.items() if not value), None)
            if empty is None:
                raise ValueError(f'The {target.key} object "{target.Name}" has no empty field for the thermal '
                                 f'comfort model {comfort_model!r}.')
            values[empty] = comfort_model
            changes.append((target, empty, comfort_model))
    return changes


def _apply_comfort_model_changes(changes: list, verbose: bool) -> None:
    for target, field, comfort_model in changes:
        setattr(target, field, comfort_model)
        if verbose:
            print(f"Added the thermal comfort model {comfort_model} to '{target.Name}'")


def add_thermal_comfort_model(building: Any, comfort_model: str, verbose: bool = False) -> None:
    """Add a thermal comfort model to the People objects (and, in models of EnergyPlus 26.2 with People:Instance
    objects, to the People:Definition objects they reference) in their first field Thermal Comfort Model n Type that
    is empty, keeping the models they have (those of the ACCIS, AdaptiveASH55 and AdaptiveCEN15251, and Fanger with
    the PMV-based setpoints); the objects that have it already do not change. EnergyPlus then reports the outputs of
    the model for each People object, such as the standard effective temperature of the Pierce two-node model
    (:data:`PIERCE_SET_OUTPUT`), with the inputs of the People object (activity level, work efficiency, clothing
    insulation and air velocity schedules) and the conditions of its zone; :func:`add_thermal_comfort_outputs` also
    requests them.

    :param building: The eppy or besos IDF object.
    :param comfort_model: 'Fanger', 'Pierce', 'KSU' or 'CoolingEffectASH55' (:data:`THERMAL_COMFORT_MODELS`), in any
        case.
    :param verbose: If True, prints the changes.
    :raises ValueError: Before changing anything, if the model is not one of :data:`THERMAL_COMFORT_MODELS` or is not
        a choice of the field in the IDD of the model (CoolingEffectASH55 is not in that of EnergyPlus 9.4), a
        People:Instance object references a People:Definition object that is not in the model, or an object has no
        empty field for it.
    """
    _apply_comfort_model_changes(_comfort_model_changes(building, [comfort_model]), verbose)


def add_thermal_comfort_outputs(building: Any, models: Union[str, Sequence[str]] = ('Pierce',),
                                output_frequencies: Optional[Sequence[str]] = None, verbose: bool = False) -> None:
    """Add some thermal comfort models to the People objects (:func:`add_thermal_comfort_model`) and request their
    outputs for each occupant instance (:data:`THERMAL_COMFORT_OUTPUTS`), which ``Table`` names and with which
    :mod:`accim.data.postprocessing.indoor_adaptation` calculates the indicators of the adaptation to the indoor
    climate (task F3 of block F of accim 1.2.0), in any model, with the ACCIS or not:

    - 'Fanger': the PMV and the PPD;
    - 'Pierce' (the default): the SET of the Pierce two-node model (Engineering Reference 25.2, 19.1.4) and the PMV
      calculated with it (equation 19.41);
    - 'CoolingEffectASH55': the cooling effect of the elevated air speed of ASHRAE 55-2017 (the temperature that,
      subtracted from the air temperature and the mean radiant temperature, gives the same SET in still air, 0.1 m/s,
      as in the elevated air speed; Engineering Reference 25.2, 19.1.9, equation 19.94) and the PMV and PPD adjusted
      by it (Input Output Reference 25.2, 1.14.2.2.45 to 1.14.2.2.47), as an indicator, not as a setpoint (decision
      of the review of accim 1.2.0 on A6, ``notes/decisions.md``).

    EnergyPlus calculates them with the activity level, work efficiency, clothing insulation and air velocity schedules
    of the People objects (Input Output Reference 25.2, 1.14.2.1) and the conditions of their zones. The outputs that
    the model requests already (with the key of the occupant instance or '*') are not requested again.

    :param building: The eppy or besos IDF object, changed in place.
    :param models: The models, one or several of 'Fanger', 'Pierce' and 'CoolingEffectASH55', in any case.
    :param output_frequencies: The reporting frequencies of the outputs ('timestep', 'hourly'...); None (the default)
        for those of the EMS outputs of the model (those of the ACCIS), or hourly if it has none.
    :param verbose: If True, prints the models added.
    :raises ValueError: Before changing anything, if a model is not one of :data:`THERMAL_COMFORT_OUTPUTS`, the model
        has no occupants, an object of the occupants has not the schedules that the models need (the work efficiency,
        the air velocity and the clothing insulation schedules, the latter not with the dynamic clothing model of
        ASHRAE 55, and the calculation method schedule with 'CalculationMethodSchedule'), or a model cannot be added
        (see :func:`add_thermal_comfort_model`).
    """
    from accim.sim.comfort_hooks import _add_zone_output_variables, _model_output_frequencies
    from accim.sim.targets import resolve_targets

    names = {m.upper(): m for m in THERMAL_COMFORT_OUTPUTS}
    chosen = []
    for model in ([models] if isinstance(models, str) else list(models)):
        if str(model).strip().upper() not in names:
            raise ValueError(f'models must be some of {list(THERMAL_COMFORT_OUTPUTS)}, not {model!r}.')
        if names[str(model).strip().upper()] not in chosen:
            chosen.append(names[str(model).strip().upper()])
    if not chosen:
        raise ValueError(f'models must be some of {list(THERMAL_COMFORT_OUTPUTS)}, not an empty list.')
    targets = resolve_targets(building)
    if not targets:
        raise ValueError('The model has no occupants (People objects), whose thermal comfort these outputs are.')
    missing = []
    for people in get_people_objects(building):
        method = str(getattr(people, 'Clothing_Insulation_Calculation_Method', '') or '').strip().upper()
        fields = [field for field in _COMFORT_MODEL_FIELDS
                  if not (field == 'Clothing_Insulation_Schedule_Name' and method == 'DYNAMICCLOTHINGMODELASHRAE55')]
        if method == 'CALCULATIONMETHODSCHEDULE':
            fields.append('Clothing_Insulation_Calculation_Method_Schedule_Name')
        absent = [field.replace('_', ' ') for field in fields
                  if field in people.fieldnames and not str(getattr(people, field, '') or '').strip()]
        if absent:
            missing.append(f'"{people.Name}" ({", ".join(absent)})')
    if missing:
        raise ValueError('The thermal comfort models need the work efficiency, clothing insulation and air velocity '
                         'schedules of the occupants (Input Output Reference 25.2, 1.14.2.1), which these objects '
                         'have not: ' + '; '.join(missing) + '.')
    changes = _comfort_model_changes(building, chosen)
    if output_frequencies is None:
        frequencies = _model_output_frequencies(building)
    else:
        frequencies = [str(frequency).capitalize() for frequency in output_frequencies]
    _apply_comfort_model_changes(changes, verbose)
    keys = {key: key for target in targets for key in target.instance_keys}
    _add_zone_output_variables(building, keys, [output for model in chosen
                                                for output in THERMAL_COMFORT_OUTPUTS[model]], frequencies)


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
