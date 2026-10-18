"""Tests for the People:Definition and People:Instance objects of EnergyPlus 26.2.

EnergyPlus 26.2 can describe the occupants with a People:Instance object (name, zone, zone list,
space or space list, and schedules) that references a People:Definition object (number of people,
heat gain fractions and thermal comfort models), instead of a People object. EnergyPlus names the
outputs of the instances after the People:Instance object, with the same rules as for People
objects, never after the People:Definition object.

Before, accim only read People objects: scan_zones stopped with a ValueError when the model only had
People:Instance objects, setComfFieldsPeople stopped with an UnboundLocalError without People objects,
and _resolve_targets, the aPMV functions and the hierarchy functions of accim.utils ignored the
People:Instance objects. The tests with EnergyPlus 26.2 are in test_energyplus_versions.py, and the
test of the occupied floor area of the parametric module in
tests/parametric_and_optimisation/test_analysis_floor_area.py.
"""
from types import SimpleNamespace

import pytest

from accim.sim.accim_Base import setComfFieldsPeople
from accim.sim.apmv_setpoints import (_resolve_targets, get_available_target_names, set_pmv_input_parameters,
                                      set_zones_always_occupied)
from accim.sim.utils import scan_zones
from accim.utils import (get_idf_hierarchy_with_people, get_people_definition, get_people_hierarchy,
                         get_people_objects, is_people_instance, set_occupancy_to_always)

COMFORT_MODEL_FIELDS = [f'Thermal_Comfort_Model_{n}_Type' for n in range(1, 8)]


class _Obj(SimpleNamespace):
    """An eppy-like object: its fields can be read as attributes or as items."""

    def __getitem__(self, field):
        return getattr(self, field)


class _ObjectClasses(dict):
    """The idfobjects of eppy, whose class names do not depend on the case."""

    def __getitem__(self, key):
        return super().__getitem__(key.upper())


class _FakeIDF:
    """A minimal IDF of EnergyPlus 26.2 with the object classes that accim reads for the occupants."""

    CLASSES = ['ZONE', 'ZONELIST', 'SPACE', 'SPACELIST', 'PEOPLE', 'PEOPLE:DEFINITION', 'PEOPLE:INSTANCE',
               'SCHEDULE:COMPACT']

    def __init__(self, objects, classes=CLASSES):
        self.idfobjects = _ObjectClasses({c: [] for c in classes})
        for obj in objects:
            self.idfobjects[obj.key].append(obj)

    def newidfobject(self, key, **fields):
        obj = _Obj(key=key.upper(), **fields)
        self.idfobjects[key].append(obj)
        return obj


def _zone(name):
    return _Obj(key='ZONE', Name=name)


def _zonelist(name, zones):
    fields = {f'Zone_{n}_Name': z for n, z in enumerate(zones, start=1)}
    return _Obj(key='ZONELIST', Name=name, obj=['ZoneList', name] + zones, **fields)


def _space(name, zone):
    return _Obj(key='SPACE', Name=name, Zone_Name=zone)


def _spacelist(name, spaces):
    fields = {f'Space_{n}_Name': s for n, s in enumerate(spaces, start=1)}
    return _Obj(key='SPACELIST', Name=name, obj=['SpaceList', name] + spaces, **fields)


def _definition(name, **fields):
    models = {field: '' for field in COMFORT_MODEL_FIELDS}
    models.update(fields)
    return _Obj(key='PEOPLE:DEFINITION', Name=name, **models)


def _instance(name, definition, target):
    return _Obj(key='PEOPLE:INSTANCE', Name=name, People_Definition_Name=definition,
                Zone_or_ZoneList_or_Space_or_SpaceList_Name=target, Number_of_People_Schedule_Name='Occupancy',
                Activity_Level_Schedule_Name='Activity', Work_Efficiency_Schedule_Name='',
                Clothing_Insulation_Schedule_Name='', Air_Velocity_Schedule_Name='')


def _people(name, target):
    return _Obj(key='PEOPLE', Name=name, Zone_or_ZoneList_or_Space_or_SpaceList_Name=target,
                Number_of_People_Schedule_Name='Occupancy')


def _two_zone_model(*extra_objects):
    """The two zones of the sample TestModel, each with a People:Instance of one shared People:Definition."""
    return _FakeIDF([
        _zone('Block1:Zone1'), _zone('Block1:Zone2'), _definition('Office Definition'),
        _instance('People Block1:Zone1', 'Office Definition', 'Block1:Zone1'),
        _instance('People Block1:Zone2', 'Office Definition', 'Block1:Zone2'),
        *extra_objects,
    ])


def test_get_people_objects_returns_people_and_people_instances():
    people = _people('Old People', 'Block1:Zone1')
    idf = _two_zone_model(people)

    assert [p.Name for p in get_people_objects(idf)] == ['Old People', 'People Block1:Zone1', 'People Block1:Zone2']
    assert [is_people_instance(p) for p in get_people_objects(idf)] == [False, True, True]


def test_get_people_objects_without_people_instance_class():
    # The IDDs before EnergyPlus 26.2 have no People:Instance objects
    idf = _FakeIDF([_people('People Zone1', 'Zone1')], classes=['PEOPLE'])

    assert [p.Name for p in get_people_objects(idf)] == ['People Zone1']


def test_get_people_definition_ignores_case():
    idf = _two_zone_model()
    instance = _instance('People Zone3', 'OFFICE DEFINITION', 'Zone3')

    assert get_people_definition(idf, instance) is idf.idfobjects['PEOPLE:DEFINITION'][0]
    assert get_people_definition(idf, _instance('People Zone4', 'Missing', 'Zone4')) is None


def test_resolve_targets_uses_the_names_of_the_people_instances():
    # The outputs that the EMS sensors read are named after the People:Instance, not after its People:Definition
    targets = _resolve_targets(_two_zone_model())

    assert targets == [
        {'df_key': 'Block1:Zone1', 'ems_suffix': 'Block1_Zone1', 'sensor_key': 'People Block1:Zone1',
         'zone_name': 'Block1:Zone1'},
        {'df_key': 'Block1:Zone2', 'ems_suffix': 'Block1_Zone2', 'sensor_key': 'People Block1:Zone2',
         'zone_name': 'Block1:Zone2'},
    ]


def test_resolve_targets_expands_a_people_instance_of_a_zone_list():
    # EnergyPlus names each instance '<space> <People:Instance name>', and the default space of a zone
    # without Space objects has the name of the zone
    idf = _FakeIDF([
        _zone('Block1:Zone1'), _zone('Block1:Zone2'), _zonelist('Occupied Zones', ['Block1:Zone1', 'Block1:Zone2']),
        _definition('Office Definition'), _instance('Office Occupants', 'Office Definition', 'Occupied Zones'),
    ])

    assert [(t['sensor_key'], t['zone_name']) for t in _resolve_targets(idf)] == [
        ('Block1:Zone1 Office Occupants', 'Block1:Zone1'),
        ('Block1:Zone2 Office Occupants', 'Block1:Zone2'),
    ]
    assert get_available_target_names(idf) == ['Block1:Zone1 Office Occupants', 'Block1:Zone2 Office Occupants']


def test_scan_zones_reads_people_instance_objects():
    job = SimpleNamespace(idf1=_two_zone_model())

    scan_zones(job)

    assert sorted(job.occupiedZones_orig) == ['Block1:Zone1', 'Block1:Zone2']
    assert job.ems_objs_name == ['Block1_Zone1', 'Block1_Zone2']
    assert job.ems_objs_key == ['People Block1:Zone1', 'People Block1:Zone2']
    assert job.ems_zonenames == ['Block1:Zone1', 'Block1:Zone2']


def test_scan_zones_rejects_models_without_people_or_people_instances():
    idf = _FakeIDF([_zone('Block1:Zone1'), _definition('Office Definition')])

    with pytest.raises(ValueError, match='The model has no People objects or People:Instance objects'):
        scan_zones(SimpleNamespace(idf1=idf))


@pytest.mark.parametrize('TempCtrl, model_3', [('temperature', ''), ('pmv', 'Fanger')])
def test_setcomffieldspeople_sets_the_comfort_models_in_the_people_definitions(TempCtrl, model_3):
    # Models 4 to 7 are emptied, as in the People objects that setComfFieldsPeople creates again
    shared = _definition('Office Definition', Thermal_Comfort_Model_4_Type='Pierce', Thermal_Comfort_Model_7_Type='KSU')
    unused = _definition('Unused Definition', Thermal_Comfort_Model_1_Type='KSU')
    idf = _FakeIDF([
        shared, unused,
        _instance('People Block1:Zone1', 'Office Definition', 'Block1:Zone1'),
        _instance('People Block1:Zone2', 'OFFICE DEFINITION', 'Block1:Zone2'),
    ])

    setComfFieldsPeople(SimpleNamespace(idf1=idf), TempCtrl=TempCtrl, verboseMode=False)

    assert [getattr(shared, f) for f in COMFORT_MODEL_FIELDS] == [
        'AdaptiveASH55', 'AdaptiveCEN15251', model_3, '', '', '', '']
    # A People:Definition that no People:Instance references does not change
    assert [getattr(unused, f) for f in COMFORT_MODEL_FIELDS] == ['KSU', '', '', '', '', '', '']
    assert len(idf.idfobjects['PEOPLE:INSTANCE']) == 2


def test_setcomffieldspeople_rejects_a_missing_people_definition():
    idf = _FakeIDF([_instance('People Block1:Zone1', 'Missing Definition', 'Block1:Zone1')])

    with pytest.raises(ValueError, match='references the People:Definition object "Missing Definition"'):
        setComfFieldsPeople(SimpleNamespace(idf1=idf), TempCtrl='temperature', verboseMode=False)


def test_set_pmv_input_parameters_changes_the_people_instances_and_their_definitions():
    idf = _two_zone_model()

    set_pmv_input_parameters(idf, air_velocity={'Block1:Zone1': 0.3}, work_efficiency=0.0, verbose_mode=False)

    zone1, zone2 = idf.idfobjects['PEOPLE:INSTANCE']
    assert zone1.Air_Velocity_Schedule_Name == 'Sch_Vel_People_Block1_Zone1'
    assert zone2.Air_Velocity_Schedule_Name == ''
    assert zone1.Work_Efficiency_Schedule_Name == 'Sch_Eff_People_Block1_Zone1'
    assert zone2.Work_Efficiency_Schedule_Name == 'Sch_Eff_People_Block1_Zone2'
    schedules = {s.Name: s.Field_3 for s in idf.idfobjects['Schedule:Compact']}
    assert schedules['Sch_Vel_People_Block1_Zone1'] == 'Until: 24:00,0.3'
    assert schedules['Sch_Eff_People_Block1_Zone2'] == 'Until: 24:00,0.0'
    # The thermal comfort models of the instances are in their People:Definition
    assert idf.idfobjects['PEOPLE:DEFINITION'][0].Thermal_Comfort_Model_1_Type == 'Fanger'


def test_always_occupied_functions_change_the_people_instances():
    idf = _two_zone_model(_people('Old People', 'Block1:Zone1'))

    set_zones_always_occupied(idf, verbose_mode=False)
    assert {p.Number_of_People_Schedule_Name for p in get_people_objects(idf)} == {'On'}

    set_occupancy_to_always(idf)
    assert {p.Number_of_People_Schedule_Name for p in get_people_objects(idf)} == {'On 24/7'}


def test_hierarchy_functions_include_the_people_instances():
    idf = _FakeIDF([
        _zone('Block1:Zone1'), _zone('Block1:Zone2'),
        _space('Space 1', 'Block1:Zone1'), _space('Space 2', 'Block1:Zone2'),
        _spacelist('All Spaces', ['Space 1', 'Space 2']),
        _definition('Office Definition'), _instance('Office Occupants', 'Office Definition', 'All Spaces'),
    ])

    assert get_people_hierarchy(idf) == {
        'Office Occupants': {'target_ref': 'All Spaces', 'inferred_type': 'SpaceList',
                             'affected_spaces': ['Space 1', 'Space 2']},
    }
    zones = get_idf_hierarchy_with_people(idf)['zones']
    assert zones['Block1:Zone1']['spaces'] == [{'name': 'Space 1', 'people': 'Office Occupants'}]
    assert zones['Block1:Zone2']['spaces'] == [{'name': 'Space 2', 'people': 'Office Occupants'}]
