"""Tests for the names of the occupant instances in models with Space objects.

EnergyPlus creates one instance of a People object for each space it applies to, and names it as the
Input Output Reference says ("Specifying Applicable Zone(s) or Space(s)"), which was checked with
EnergyPlus 25.2 and 26.2 in 2026-10:
- assigned to a Space: '<People Name>', also when the zone has more spaces;
- assigned to a Zone: '<People Name>' if the zone has one space, or '<Space Name> <People Name>' for
  each space;
- assigned to a SpaceList or a ZoneList: '<Space Name> <People Name>' for each space, also for lists
  of one member.
A zone without Space objects has a default space named like the zone, and a zone with Space objects
where some heat transfer surfaces have no Space Name gets a space named '<Zone Name>-Remainder'
(InternalMass, subsurfaces and shading surfaces do not count). The People:Instance objects of EnergyPlus
26.2 give their own names to their instances in the same way.

Before, _resolve_targets gave '<Space Name> <People Name>' as the key of the EMS sensors also for People
assigned to a Space or to a Zone of one space, so EnergyPlus stopped with "Invalid Output:Variable or
Output:Meter Index Key Name"; it dropped the zones without Space objects of models with Space objects,
and ignored the remainder spaces. A zone with several instances got one target per instance, and addAccis
created a ThermostatSetpoint:DualSetpoint '<Zone> Dual SP' for each, so EnergyPlus stopped with "Duplicate
name found". Now a zone with several instances is one target, named after the zone, whose occupancy is the
'Zone People Occupant Count' of the zone, and whose PMV (aPMV setpoints) is the average of the PMV of its
instances weighted by their occupants. The targets of the zones with one instance do not change, apart
from the sensor keys that were wrong.
"""
from types import SimpleNamespace

import pytest

from accim.sim.accim_Base_EMS import addEMSSensorsBase
from accim.sim.apmv_setpoints import _resolve_targets, apply_apmv_setpoints, set_pmv_input_parameters
from accim.sim.utils import scan_zones
from accim.utils import get_idf_hierarchy_with_people, get_people_hierarchy, get_people_names_for_ems


class _Obj(SimpleNamespace):
    """An eppy-like object: its fields can be read as attributes or as items."""

    def __getitem__(self, field):
        return getattr(self, field)


class _ObjectClasses(dict):
    """The idfobjects of eppy: the class names do not depend on the case, and missing classes raise KeyError."""

    def __getitem__(self, key):
        return super().__getitem__(key.upper())


class _FakeIDF:
    """A minimal IDF of EnergyPlus 26.2 with the classes that accim reads to resolve the occupant instances."""

    CLASSES = ['ZONE', 'ZONELIST', 'SPACE', 'SPACELIST', 'PEOPLE', 'PEOPLE:INSTANCE', 'BUILDINGSURFACE:DETAILED',
               'WALL:EXTERIOR', 'FENESTRATIONSURFACE:DETAILED', 'INTERNALMASS', 'SCHEDULE:COMPACT',
               'ZONECONTROL:THERMOSTAT', 'ZONECONTROL:THERMOSTAT:THERMALCOMFORT',
               'THERMOSTATSETPOINT:THERMALCOMFORT:FANGER:DUALSETPOINT', 'ENERGYMANAGEMENTSYSTEM:SENSOR',
               'ENERGYMANAGEMENTSYSTEM:ACTUATOR', 'ENERGYMANAGEMENTSYSTEM:GLOBALVARIABLE',
               'ENERGYMANAGEMENTSYSTEM:PROGRAM', 'ENERGYMANAGEMENTSYSTEM:PROGRAMCALLINGMANAGER',
               'ENERGYMANAGEMENTSYSTEM:OUTPUTVARIABLE', 'OUTPUT:VARIABLE', 'OUTPUT:METER', 'OUTPUTCONTROL:FILES']

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


def _space(name, zone):
    return _Obj(key='SPACE', Name=name, Zone_Name=zone)


def _list(key, name, members):
    return _Obj(key=key, Name=name, obj=[key, name] + list(members))


def _people(name, target):
    return _Obj(key='PEOPLE', Name=name, Zone_or_ZoneList_or_Space_or_SpaceList_Name=target,
                Number_of_People_Schedule_Name='Occupancy')


def _people_instance(name, target):
    return _Obj(key='PEOPLE:INSTANCE', Name=name, People_Definition_Name=f'{name} Definition',
                Zone_or_ZoneList_or_Space_or_SpaceList_Name=target, Number_of_People_Schedule_Name='Occupancy')


def _surface(name, zone, space=''):
    return _Obj(key='BUILDINGSURFACE:DETAILED', Name=name, Zone_Name=zone, Space_Name=space)


def _surfaces(zone, spaces):
    """The six surfaces of a zone of the sample TestModel, each in the space given in order ('' for none)."""
    return [_surface(f'{zone}_Surface_{n}', zone, space) for n, space in enumerate(spaces, start=1)]


def _model(*objects):
    """The two zones of the sample TestModel, with the given objects."""
    return _FakeIDF([_zone('Block1:Zone1'), _zone('Block1:Zone2'), *objects])


def _keys(targets):
    return [(t['df_key'], t['ems_suffix'], t['sensor_key'], t['zone_name']) for t in targets]


ONE_SPACE_PER_ZONE = [
    _space('Space 1', 'Block1:Zone1'), _space('Space 2', 'Block1:Zone2'),
    *_surfaces('Block1:Zone1', ['Space 1'] * 6), *_surfaces('Block1:Zone2', ['Space 2'] * 6),
]
TWO_SPACES_IN_ZONE_1 = [
    _space('Space 1a', 'Block1:Zone1'), _space('Space 1b', 'Block1:Zone1'), _space('Space 2', 'Block1:Zone2'),
    *_surfaces('Block1:Zone1', ['Space 1a'] * 4 + ['Space 1b'] * 2), *_surfaces('Block1:Zone2', ['Space 2'] * 6),
]


# The instance names that EnergyPlus 25.2 and 26.2 gave in the simulations of these assignments
@pytest.mark.parametrize('objects, expected', [
    # Without Space objects
    ([_people('People Block1:Zone1', 'Block1:Zone1'), _people('People Block1:Zone2', 'Block1:Zone2')],
     ['People Block1:Zone1', 'People Block1:Zone2']),
    ([_list('ZONELIST', 'All zones', ['Block1:Zone1', 'Block1:Zone2']), _people('Office', 'All zones')],
     ['Block1:Zone1 Office', 'Block1:Zone2 Office']),
    ([_list('ZONELIST', 'Only zone 1', ['Block1:Zone1']), _people('Office', 'Only zone 1')],
     ['Block1:Zone1 Office']),
    # One space per zone, assigned to the zone, to the space or to a space list
    (ONE_SPACE_PER_ZONE + [_people('People Block1:Zone1', 'Block1:Zone1'), _people('People Block1:Zone2', 'BLOCK1:ZONE2')],
     ['People Block1:Zone1', 'People Block1:Zone2']),
    (ONE_SPACE_PER_ZONE + [_people('People Block1:Zone1', 'Space 1'), _people('People Block1:Zone2', 'space 2')],
     ['People Block1:Zone1', 'People Block1:Zone2']),
    (ONE_SPACE_PER_ZONE + [_list('SPACELIST', 'All spaces', ['Space 1', 'Space 2']), _people('Office', 'All spaces')],
     ['Space 1 Office', 'Space 2 Office']),
    (ONE_SPACE_PER_ZONE + [_list('SPACELIST', 'Only space 1', ['Space 1']), _people('Office', 'Only space 1')],
     ['Space 1 Office']),
    # Zone 1 with two spaces
    (TWO_SPACES_IN_ZONE_1 + [_people('People Block1:Zone1', 'Block1:Zone1'), _people('People Block1:Zone2', 'Block1:Zone2')],
     ['Space 1a People Block1:Zone1', 'Space 1b People Block1:Zone1', 'People Block1:Zone2']),
    (TWO_SPACES_IN_ZONE_1 + [_people('People Block1:Zone1', 'Space 1a')],
     ['People Block1:Zone1']),
    (TWO_SPACES_IN_ZONE_1 + [_people_instance('Office Occupants', 'Space 1a')],
     ['Office Occupants']),
    (TWO_SPACES_IN_ZONE_1 + [_list('SPACELIST', 'All spaces', ['Space 1a', 'Space 1b', 'Space 2']),
                             _people('Office', 'All spaces')],
     ['Space 1a Office', 'Space 1b Office', 'Space 2 Office']),
    # Zone 1 with two spaces and Zone 2 without Space objects
    ([_space('Space 1a', 'Block1:Zone1'), _space('Space 1b', 'Block1:Zone1'),
      _list('ZONELIST', 'All zones', ['Block1:Zone1', 'Block1:Zone2']), _people('Office', 'All zones')],
     ['Space 1a Office', 'Space 1b Office', 'Block1:Zone2 Office']),
    ([_space('Space 1', 'Block1:Zone1'), _people('People Block1:Zone1', 'Block1:Zone1'),
      _people('People Block1:Zone2', 'Block1:Zone2')],
     ['People Block1:Zone1', 'People Block1:Zone2']),
    # Remainder space: Zone 1 with Space 1 in the floor and the roof only
    ([_space('Space 1', 'Block1:Zone1'), *_surfaces('Block1:Zone1', ['Space 1'] * 2 + [''] * 4),
      _people('People Block1:Zone1', 'Block1:Zone1')],
     ['Space 1 People Block1:Zone1', 'Block1:Zone1-Remainder People Block1:Zone1']),
    # Two People objects in a zone without Space objects
    ([_people('People Block1:Zone1', 'Block1:Zone1'), _people('Visitors Block1:Zone1', 'Block1:Zone1')],
     ['People Block1:Zone1', 'Visitors Block1:Zone1']),
])
def test_instance_names_follow_energyplus(objects, expected):
    assert get_people_names_for_ems(_model(*objects)) == expected

    from accim.utils import get_people_instances
    assert [i['name'] for i in get_people_instances(_model(*objects))] == expected


def test_remainder_space_needs_surfaces_with_and_without_space_name():
    from accim.utils import get_energyplus_spaces

    surfaces = _surfaces('Block1:Zone1', ['Space 1'] * 5 + [''])
    # A window has no Space Name field (it takes the space of its base surface), and InternalMass does not count
    window = _Obj(key='FENESTRATIONSURFACE:DETAILED', Name='Window 1', Building_Surface_Name=surfaces[0].Name)
    mass = _Obj(key='INTERNALMASS', Name='Mass 1', Zone_or_ZoneList_Name='Block1:Zone1', Space_or_SpaceList_Name='')
    assert get_energyplus_spaces(_model(_space('Space 1', 'Block1:Zone1'), *surfaces, window, mass))[
        'BLOCK1:ZONE1']['remainder'] == 'Block1:Zone1-Remainder'

    surfaces[-1].Space_Name = 'Space 1'
    spaces = get_energyplus_spaces(_model(_space('Space 1', 'Block1:Zone1'), *surfaces, window, mass))
    assert spaces['BLOCK1:ZONE1'] == {'zone': 'Block1:Zone1', 'spaces': ['Space 1'], 'explicit': True,
                                      'remainder': None}
    # The default space of a zone without Space objects is named like the zone
    assert spaces['BLOCK1:ZONE2'] == {'zone': 'Block1:Zone2', 'spaces': ['Block1:Zone2'], 'explicit': False,
                                      'remainder': None}

    # Other classes of heat transfer surfaces count too
    wall = _Obj(key='WALL:EXTERIOR', Name='Wall 1', Zone_Name='Block1:Zone1', Space_Name='')
    assert get_energyplus_spaces(_model(_space('Space 1', 'Block1:Zone1'), *surfaces, wall))[
        'BLOCK1:ZONE1']['spaces'] == ['Space 1', 'Block1:Zone1-Remainder']


def test_people_of_a_space_or_a_zone_of_one_space_keep_their_target_names():
    # Before, the sensor keys were 'Space 1 People Block1:Zone1' and 'Space 2 People Block1:Zone2'
    idf = _model(*ONE_SPACE_PER_ZONE, _people('People Block1:Zone1', 'Space 1'),
                 _people('People Block1:Zone2', 'Block1:Zone2'))

    targets = _resolve_targets(idf)

    assert _keys(targets) == [
        ('Space 1 People Block1:Zone1', 'Space_1_People_Block1_Zone1', 'People Block1:Zone1', 'Block1:Zone1'),
        ('Space 2 People Block1:Zone2', 'Space_2_People_Block1_Zone2', 'People Block1:Zone2', 'Block1:Zone2'),
    ]
    assert [(t['occupancy_key'], t['occupancy_variable']) for t in targets] == [
        ('People Block1:Zone1', 'People Occupant Count'), ('People Block1:Zone2', 'People Occupant Count')]


def test_space_list_with_one_space_per_zone_does_not_change():
    # The People of OpenStudio models: one target per space, as before
    idf = _model(*ONE_SPACE_PER_ZONE, _list('SPACELIST', 'Office spaces', ['Space 1', 'Space 2']),
                 _people('Office People', 'Office spaces'))

    targets = _resolve_targets(idf)

    assert targets == [
        {'df_key': 'Space 1 Office People', 'ems_suffix': 'Space_1_Office_People', 'sensor_key': 'Space 1 Office People',
         'zone_name': 'Block1:Zone1', 'occupancy_key': 'Space 1 Office People',
         'occupancy_variable': 'People Occupant Count', 'instance_keys': ['Space 1 Office People'],
         'people_names': ['Office People']},
        {'df_key': 'Space 2 Office People', 'ems_suffix': 'Space_2_Office_People', 'sensor_key': 'Space 2 Office People',
         'zone_name': 'Block1:Zone2', 'occupancy_key': 'Space 2 Office People',
         'occupancy_variable': 'People Occupant Count', 'instance_keys': ['Space 2 Office People'],
         'people_names': ['Office People']},
    ]


def test_zone_of_several_spaces_is_one_target_with_the_occupancy_of_the_zone():
    # Before, one target per space, and addAccis created 'Block1:Zone1 Dual SP' twice
    idf = _model(*TWO_SPACES_IN_ZONE_1, _people('People Block1:Zone1', 'Block1:Zone1'),
                 _people('People Block1:Zone2', 'Block1:Zone2'))

    targets = _resolve_targets(idf)

    assert targets == [
        {'df_key': 'Block1:Zone1', 'ems_suffix': 'Block1_Zone1', 'sensor_key': 'Space 1a People Block1:Zone1',
         'zone_name': 'Block1:Zone1', 'occupancy_key': 'Block1:Zone1',
         'occupancy_variable': 'Zone People Occupant Count',
         'instance_keys': ['Space 1a People Block1:Zone1', 'Space 1b People Block1:Zone1'],
         'people_names': ['People Block1:Zone1']},
        {'df_key': 'Space 2 People Block1:Zone2', 'ems_suffix': 'Space_2_People_Block1_Zone2',
         'sensor_key': 'People Block1:Zone2', 'zone_name': 'Block1:Zone2', 'occupancy_key': 'People Block1:Zone2',
         'occupancy_variable': 'People Occupant Count', 'instance_keys': ['People Block1:Zone2'],
         'people_names': ['People Block1:Zone2']},
    ]


def test_zones_without_space_objects_in_a_model_with_spaces_are_not_dropped():
    # Before, the People of Block1:Zone2 (without Space objects) had no target
    idf = _model(_space('Space 1', 'Block1:Zone1'), *_surfaces('Block1:Zone1', ['Space 1'] * 6),
                 _people('People Block1:Zone1', 'Block1:Zone1'), _people('People Block1:Zone2', 'Block1:Zone2'))

    assert _keys(_resolve_targets(idf)) == [
        ('Space 1 People Block1:Zone1', 'Space_1_People_Block1_Zone1', 'People Block1:Zone1', 'Block1:Zone1'),
        ('Block1:Zone2', 'Block1_Zone2', 'People Block1:Zone2', 'Block1:Zone2'),
    ]


def test_remainder_space_is_included_with_a_warning():
    idf = _model(_space('Space 1', 'Block1:Zone1'), *_surfaces('Block1:Zone1', ['Space 1'] * 2 + [''] * 4),
                 _people('People Block1:Zone1', 'Block1:Zone1'))

    with pytest.warns(UserWarning, match="EnergyPlus creates the space 'Block1:Zone1-Remainder'"):
        targets = _resolve_targets(idf)

    assert [(t['df_key'], t['occupancy_key'], t['occupancy_variable'], t['instance_keys']) for t in targets] == [
        ('Block1:Zone1', 'Block1:Zone1', 'Zone People Occupant Count',
         ['Space 1 People Block1:Zone1', 'Block1:Zone1-Remainder People Block1:Zone1'])]


def test_two_people_objects_in_a_zone_are_one_target():
    # Before, two targets with the same EMS suffix 'Block1_Zone1'
    idf = _model(_people('People Block1:Zone1', 'Block1:Zone1'), _people('Visitors', 'Block1:Zone1'))

    targets = _resolve_targets(idf)

    assert [(t['df_key'], t['ems_suffix'], t['instance_keys'], t['people_names']) for t in targets] == [
        ('Block1:Zone1', 'Block1_Zone1', ['People Block1:Zone1', 'Visitors'], ['People Block1:Zone1', 'Visitors'])]


def test_hierarchy_functions_use_the_spaces_of_energyplus():
    idf = _model(_space('Space 1', 'Block1:Zone1'), *_surfaces('Block1:Zone1', ['Space 1'] * 2 + [''] * 4),
                 _list('ZONELIST', 'All zones', ['Block1:Zone1', 'Block1:Zone2']), _people('Office', 'All zones'))

    assert get_people_hierarchy(idf) == {
        'Office': {'target_ref': 'All zones', 'inferred_type': 'ZoneList',
                   'affected_spaces': ['Space 1', 'Block1:Zone1-Remainder', 'Block1:Zone2']},
    }
    zones = get_idf_hierarchy_with_people(idf)['zones']
    assert zones['Block1:Zone1']['spaces'] == [{'name': 'Space 1', 'people': 'Office'},
                                               {'name': 'Block1:Zone1-Remainder', 'people': 'Office'}]
    assert zones['Block1:Zone2']['spaces'] == [{'name': 'Block1:Zone2', 'people': 'Office'}]
    assert get_people_names_for_ems(idf, output_format='dict') == {
        'Office': ['Space 1 Office', 'Block1:Zone1-Remainder Office', 'Block1:Zone2 Office']}


def test_set_pmv_input_parameters_reaches_people_of_a_zone_of_one_space():
    # Before, no target key matched the People of a zone of one space, so they were not changed
    idf = _model(*ONE_SPACE_PER_ZONE, _people('People Block1:Zone1', 'Block1:Zone1'),
                 _people('People Block1:Zone2', 'Block1:Zone2'))

    set_pmv_input_parameters(idf, air_velocity={'Space 1 People Block1:Zone1': 0.3}, work_efficiency=0.0,
                             verbose_mode=False)

    zone1, zone2 = idf.idfobjects['PEOPLE']
    assert zone1.Air_Velocity_Schedule_Name == 'Sch_Vel_People_Block1_Zone1'
    assert not hasattr(zone2, 'Air_Velocity_Schedule_Name')
    assert zone2.Work_Efficiency_Schedule_Name == 'Sch_Eff_People_Block1_Zone2'


def test_scan_zones_gives_the_occupancy_sensors():
    job = SimpleNamespace(idf1=_model(*TWO_SPACES_IN_ZONE_1, _people('People Block1:Zone1', 'Block1:Zone1'),
                                      _people('People Block1:Zone2', 'Block1:Zone2')))

    scan_zones(job)

    assert job.ems_objs_name == ['Block1_Zone1', 'Space_2_People_Block1_Zone2']
    assert job.ems_objs_key == ['Space 1a People Block1:Zone1', 'People Block1:Zone2']
    assert job.ems_occupancy_keys == ['Block1:Zone1', 'People Block1:Zone2']
    assert job.ems_occupancy_variables == ['Zone People Occupant Count', 'People Occupant Count']


def test_addaccis_occupancy_sensors_of_a_zone_with_several_instances():
    job = SimpleNamespace(idf1=_model(*TWO_SPACES_IN_ZONE_1, _people('People Block1:Zone1', 'Block1:Zone1'),
                                      _people('People Block1:Zone2', 'Block1:Zone2')))
    scan_zones(job)

    addEMSSensorsBase(job, ScriptType='vrf_ac', verboseMode=False)

    sensors = {s.Name: (s.OutputVariable_or_OutputMeter_Index_Key_Name, s.OutputVariable_or_OutputMeter_Name)
               for s in job.idf1.idfobjects['EnergyManagementSystem:Sensor']}
    assert sensors['Occ_count_Block1_Zone1'] == ('Block1:Zone1', 'Zone People Occupant Count')
    assert sensors['Occ_count_Space_2_People_Block1_Zone2'] == ('People Block1:Zone2', 'People Occupant Count')
    # The running mean outdoor temperatures are read from the first instance
    assert sensors['RMOT'][0] == sensors['PMOT'][0] == 'Space 1a People Block1:Zone1'


def test_apmv_ems_of_a_zone_with_several_instances():
    idf = _model(*TWO_SPACES_IN_ZONE_1, _people('People Block1:Zone1', 'Block1:Zone1'),
                 _people('People Block1:Zone2', 'Block1:Zone2'))

    apply_apmv_setpoints(idf, verbose_mode=False)

    sensors = {s.Name: (s.OutputVariable_or_OutputMeter_Index_Key_Name, s.OutputVariable_or_OutputMeter_Name)
               for s in idf.idfobjects['EnergyManagementSystem:Sensor']}
    assert sensors == {
        'PMV_Block1_Zone1_1': ('Space 1a People Block1:Zone1', 'Zone Thermal Comfort Fanger Model PMV'),
        'People_Occupant_Count_Block1_Zone1_1': ('Space 1a People Block1:Zone1', 'People Occupant Count'),
        'PMV_Block1_Zone1_2': ('Space 1b People Block1:Zone1', 'Zone Thermal Comfort Fanger Model PMV'),
        'People_Occupant_Count_Block1_Zone1_2': ('Space 1b People Block1:Zone1', 'People Occupant Count'),
        'People_Occupant_Count_Block1_Zone1': ('Block1:Zone1', 'Zone People Occupant Count'),
        'PMV_Space_2_People_Block1_Zone2': ('People Block1:Zone2', 'Zone Thermal Comfort Fanger Model PMV'),
        'People_Occupant_Count_Space_2_People_Block1_Zone2': ('People Block1:Zone2', 'People Occupant Count'),
    }
    global_variables = {gv.Erl_Variable_1_Name for gv in idf.idfobjects['EnergyManagementSystem:GlobalVariable']}
    assert 'PMV_Block1_Zone1' in global_variables
    assert 'PMV_Space_2_People_Block1_Zone2' not in global_variables
    # One thermostat and one actuator per heating and cooling schedule for each zone
    assert len(idf.idfobjects['ZoneControl:Thermostat:ThermalComfort']) == 2
    assert sorted(a.Actuated_Component_Unique_Name for a in idf.idfobjects['EnergyManagementSystem:Actuator']) == [
        'PMV_C_SP_Block1:Zone1', 'PMV_C_SP_Block1:Zone2', 'PMV_H_SP_Block1:Zone1', 'PMV_H_SP_Block1:Zone2']

    programs = {p.Name: p for p in idf.idfobjects['EnergyManagementSystem:Program']}
    assert 'average_PMV_Space_2_People_Block1_Zone2' not in programs
    average = programs['average_PMV_Block1_Zone1']
    n_lines = sum(1 for field in vars(average) if field.startswith('Program_Line_'))
    assert [getattr(average, f'Program_Line_{n}') for n in range(1, n_lines + 1)] == [
        'set PMV_wsum_Block1_Zone1 = 0', 'set Occ_sum_Block1_Zone1 = 0', 'set PMV_sum_Block1_Zone1 = 0',
        'set PMV_wsum_Block1_Zone1 = PMV_wsum_Block1_Zone1 + PMV_Block1_Zone1_1*People_Occupant_Count_Block1_Zone1_1',
        'set Occ_sum_Block1_Zone1 = Occ_sum_Block1_Zone1 + People_Occupant_Count_Block1_Zone1_1',
        'set PMV_sum_Block1_Zone1 = PMV_sum_Block1_Zone1 + PMV_Block1_Zone1_1',
        'set PMV_wsum_Block1_Zone1 = PMV_wsum_Block1_Zone1 + PMV_Block1_Zone1_2*People_Occupant_Count_Block1_Zone1_2',
        'set Occ_sum_Block1_Zone1 = Occ_sum_Block1_Zone1 + People_Occupant_Count_Block1_Zone1_2',
        'set PMV_sum_Block1_Zone1 = PMV_sum_Block1_Zone1 + PMV_Block1_Zone1_2',
        'if Occ_sum_Block1_Zone1 > 0',
        'set PMV_Block1_Zone1 = PMV_wsum_Block1_Zone1/Occ_sum_Block1_Zone1',
        'else',
        'set PMV_Block1_Zone1 = PMV_sum_Block1_Zone1/2',
        'endif',
    ]
    # The PMV of the zone is calculated before the aPMV that uses it
    calling_order = [pcm.Program_Name_1 for pcm in idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']]
    assert calling_order.index('average_PMV_Block1_Zone1') < calling_order.index('monitor_aPMV_Block1_Zone1')
