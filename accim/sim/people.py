# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Thermal comfort models of the occupants (People, and People:Definition in EnergyPlus 26.2)."""

from accim.sim.idf_tools import try_objects
from accim.sim.model import AccimModel
from accim.utils.people import get_people_definition

__all__ = ['set_comfort_models']


def _comfort_models(temp_ctrl: str, number: int) -> list:
    models = ['AdaptiveASH55', 'AdaptiveCEN15251', 'Fanger' if temp_ctrl == 'pmv' else '']
    return (models + [''] * number)[:number]


def set_comfort_models(model: AccimModel) -> None:
    """Set the thermal comfort models that accim needs in the occupants of the model.

    The People objects and, in models of EnergyPlus 26.2 with People:Instance objects, the
    People:Definition objects they reference get AdaptiveASH55 and AdaptiveCEN15251 as models 1 and 2
    (whose running mean outdoor temperatures accim reads), Fanger as model 3 if ``temp_ctrl`` is 'pmv',
    and no other model.

    :raises ValueError: If a People:Instance object references a People:Definition object that is not
        in the model.
    """
    idf = model.idf
    for people in idf.idfobjects['PEOPLE']:
        fields = [f'Thermal_Comfort_Model_{n}_Type' for n in range(1, 8)
                  if f'Thermal_Comfort_Model_{n}_Type' in people.fieldnames]
        for field, comfort_model in zip(fields, _comfort_models(model.temp_ctrl, len(fields))):
            setattr(people, field, comfort_model)

    definitions = []
    for instance in try_objects(idf, 'PEOPLE:INSTANCE'):
        definition = get_people_definition(idf, instance)
        if definition is None:
            raise ValueError(
                f'The People:Instance object "{instance.Name}" references the People:Definition object '
                f'"{instance.People_Definition_Name}", which is not in the model.'
            )
        if all(definition is not d for d in definitions):
            definitions.append(definition)
    for definition in definitions:
        for n, comfort_model in enumerate(_comfort_models(model.temp_ctrl, 7), start=1):
            setattr(definition, f'Thermal_Comfort_Model_{n}_Type', comfort_model)

    model.log('The people objects in the model have been amended.')
    if definitions:
        model.log('The People:Definition objects of the People:Instance objects in the model have been amended.')
