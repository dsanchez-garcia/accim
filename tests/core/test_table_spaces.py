"""Tests for Table with the outputs of models whose zones have several occupant instances.

Since 2026-10-18, accim simulates models with Space objects where a zone has several occupant instances (a zone
of several spaces, a SpaceList that covers several spaces of a zone, or several People objects in a zone): the
EMS objects of such a zone are named after the zone, and those of the zones with one instance keep their names
('<Space>_<People>' if the zone has Space objects; see tests/core/test_space_instance_names.py). Before, Table:
- gave each output of the occupants of a zone of two spaces one column per instance, both with the same name
  ('Block1:Zone1_EN16798-1 Running mean outdoor temperature (°C)' twice), and did not attribute to their zone
  the outputs of several People objects in a zone;
- found the occupied zones of models with SpaceLists only through the Space Types of OpenStudio (spaces whose
  Space Type is the name of the SpaceList), so it found none in a model whose spaces have no Space Type;
- with those Space Types, named a zone of two spaces after its first space, listed the second space as an
  occupied zone without results, and did not keep the zones whose names already have the pattern
  'block:zone' when it asked for the blocks;
- attributed the outputs of the occupants of a zone to another zone when their names contain the name of the
  other zone, as the instance 'Space 2 People Block1:Zone1' of Block1:Zone2 when a People object named after
  Block1:Zone1 is assigned to a SpaceList of the spaces of both zones.

The models are the sample TestModel with Space objects simulated with EnergyPlus 25.1 on 2026-10-19 (the floor
of Block1:Zone1 split in two spaces); the CSV files have the names of the columns of their outputs and made-up
values. A fake IDF replaces the IDF that Table reads.
"""
from types import SimpleNamespace

import besos.eppy_funcs
import pytest

from accim.data.postprocessing.main import Table
from accim.sim.apmv_setpoints import _resolve_targets
from accim.utils import get_people_instances


class _Obj(SimpleNamespace):
    """An eppy-like object: its fields can be read as attributes or as items."""

    def __getitem__(self, field):
        return getattr(self, field)


class _ObjectClasses(dict):
    """The idfobjects of eppy: the class names do not depend on the case, and missing classes raise KeyError."""

    def __getitem__(self, key):
        return super().__getitem__(key.upper())


class _FakeIDF:
    """A minimal IDF with the classes that Table and accim read to find the occupied zones."""

    CLASSES = ['ZONE', 'SPACE', 'SPACELIST', 'PEOPLE', 'ZONECONTROL:THERMOSTAT']

    def __init__(self, *objects):
        self.idfobjects = _ObjectClasses({c: [] for c in self.CLASSES})
        for obj in objects:
            self.idfobjects[obj.key].append(obj)


def _zone(name):
    return _Obj(key='ZONE', Name=name)


def _thermostat(zone):
    return _Obj(key='ZONECONTROL:THERMOSTAT', Name=f'{zone} Thermostat', Zone_or_ZoneList_Name=zone)


def _space(name, zone, space_type=''):
    return _Obj(key='SPACE', Name=name, Zone_Name=zone, Space_Type=space_type)


def _space_list(name, spaces):
    return _Obj(key='SPACELIST', Name=name, obj=['SPACELIST', name, *spaces])


def _people(name, target):
    return _Obj(key='PEOPLE', Name=name, Zone_or_ZoneList_or_Space_or_SpaceList_Name=target)


ZONES = [_zone('Block1:Zone1'), _zone('Block1:Zone2'), _thermostat('Block1:Zone1'), _thermostat('Block1:Zone2')]


def _two_spaces_in_zone_1(space_type=''):
    return [_space('Space 1a', 'Block1:Zone1', space_type), _space('Space 1b', 'Block1:Zone1', space_type),
            _space('Space 2', 'Block1:Zone2', space_type)]


def _space_list_model(space_type=''):
    """One People object named after Block1:Zone1, assigned to a SpaceList of the three spaces."""
    return _FakeIDF(*ZONES, *_two_spaces_in_zone_1(space_type),
                    _space_list('All spaces', ['Space 1a', 'Space 1b', 'Space 2']),
                    _people('People Block1:Zone1', 'All spaces'))


# The hourly values of the outputs of each zone and of each occupant instance (RMOT and PMV), for two hours
ZONE_VALUES = {
    'Block1:Zone1': dict(temperature=[25.0, 26.0], comfortable=[1.0, 1.0], area=[15.0, 15.0], cooling=[100.0, 200.0]),
    'Block1:Zone2': dict(temperature=[27.0, 28.0], comfortable=[0.0, 1.0], area=[18.0, 18.0], cooling=[300.0, 400.0]),
}
INSTANCE_1A = ([20.0, 21.0], [0.1, 0.2])
INSTANCE_1B = ([22.0, 23.0], [0.3, 0.4])
INSTANCE_2 = ([30.0, 31.0], [-0.5, -0.6])
MEAN_OF_1A_AND_1B = ([21.0, 22.0], [0.2, 0.3])

RMOT = 'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)'
PMV = 'Zone Thermal Comfort Fanger Model PMV [](Hourly)'
CSV_NAME = 'TestModel[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X[Seville.csv'


def _outputs(ems_suffixes, instances):
    """The columns of the CSV file: the EMS outputs of each target, the outputs of each zone and of each instance."""
    columns = {'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)': [10.0, 11.0]}
    for zone, suffix in ems_suffixes.items():
        values = ZONE_VALUES[zone]
        columns[f'EMS:Comfortable Hours_No Applicability_{suffix} [H](Hourly)'] = values['comfortable']
        columns[f'EMS:Zone Floor Area_{suffix} [m2](Hourly)'] = values['area']
        columns[f'{zone.upper()}:Zone Operative Temperature [C](Hourly)'] = values['temperature']
        columns[f'{zone.upper()} VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate [W](Hourly)'] = \
            values['cooling']
    for instance, (rmot, pmv) in instances.items():
        columns[f'{instance}:{RMOT}'] = rmot
        columns[f'{instance}:{PMV}'] = pmv
    return columns


def _table(tmp_path, monkeypatch, building, ems_suffixes, instances, **kwargs):
    """Run Table on a CSV file with the outputs of the model, with the names accim and EnergyPlus give them."""
    # The names of the test data are those of accim: the EMS suffixes of the targets and the instances
    assert {t['zone_name']: t['ems_suffix'] for t in _resolve_targets(building)} == ems_suffixes
    assert [i['name'].upper() for i in get_people_instances(building)] == list(instances)

    columns = _outputs(ems_suffixes, instances)
    lines = [','.join(['Date/Time', *columns])]
    for hour in range(2):
        lines.append(','.join([f' 01/01  0{hour + 1}:00:00', *(str(v[hour]) for v in columns.values())]))
    (tmp_path / CSV_NAME).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(besos.eppy_funcs, 'get_building', lambda idf_path: building)
    arguments = dict(
        datasets=[CSV_NAME], source_frequency='hourly', frequency='hourly', frequency_agg_func='sum',
        standard_outputs=True, level=['block', 'building'], level_agg_func=['sum', 'mean'], level_excluded_zones=[],
        normalised_energy_units=False, energy_units_in_kwh=False, idf_path='model.idf',
    )
    arguments.update(kwargs)
    return Table(**arguments)


def _values(table, column):
    return table.df[column].tolist()


def test_zone_of_two_spaces_has_one_column_per_output_of_its_occupants(tmp_path, monkeypatch):
    # People assigned to the zones; Block1:Zone1 has two spaces, so two instances
    building = _FakeIDF(*ZONES, *_two_spaces_in_zone_1(), _people('People Block1:Zone1', 'Block1:Zone1'),
                        _people('People Block1:Zone2', 'Block1:Zone2'))
    table = _table(
        tmp_path, monkeypatch, building,
        ems_suffixes={'Block1:Zone1': 'Block1_Zone1', 'Block1:Zone2': 'Space_2_People_Block1_Zone2'},
        instances={'SPACE 1A PEOPLE BLOCK1:ZONE1': INSTANCE_1A, 'SPACE 1B PEOPLE BLOCK1:ZONE1': INSTANCE_1B,
                   'PEOPLE BLOCK1:ZONE2': INSTANCE_2},
    )

    assert not table.df.columns.duplicated().any()
    assert sorted(table.occupied_zone_list) == ['Block1:Zone1', 'Block1:Zone2']
    # The outputs of the occupants of a zone of several instances are averaged (they are averaged in time too)
    assert _values(table, 'Block1:Zone1_EN16798-1 Running mean outdoor temperature (°C)') == MEAN_OF_1A_AND_1B[0]
    assert _values(table, 'Block1:Zone1_PMV') == pytest.approx(MEAN_OF_1A_AND_1B[1])
    assert _values(table, 'Block1:Zone2_PMV') == INSTANCE_2[1]
    assert _values(table, 'Block1:Zone1_Zone Operative Temperature (°C)') == ZONE_VALUES['Block1:Zone1']['temperature']
    assert _values(table, 'Building_Total_PMV (mean)') == pytest.approx([(0.2 - 0.5) / 2, (0.3 - 0.6) / 2])


def test_several_people_objects_in_a_zone_without_spaces(tmp_path, monkeypatch):
    # Without Space objects: the instances are named after the People objects, which do not name the zone
    building = _FakeIDF(*ZONES, _people('Office People', 'Block1:Zone1'), _people('Visitors', 'Block1:Zone1'),
                        _people('People Block1:Zone2', 'Block1:Zone2'))
    table = _table(
        tmp_path, monkeypatch, building,
        ems_suffixes={'Block1:Zone1': 'Block1_Zone1', 'Block1:Zone2': 'Block1_Zone2'},
        instances={'OFFICE PEOPLE': INSTANCE_1A, 'VISITORS': INSTANCE_1B, 'PEOPLE BLOCK1:ZONE2': INSTANCE_2},
    )

    assert not table.df.columns.duplicated().any()
    assert _values(table, 'Block1:Zone1_EN16798-1 Running mean outdoor temperature (°C)') == MEAN_OF_1A_AND_1B[0]
    assert _values(table, 'Block1:Zone1_PMV') == pytest.approx(MEAN_OF_1A_AND_1B[1])
    assert _values(table, 'Block1:Zone2_PMV') == INSTANCE_2[1]


# The instances of the People object 'People Block1:Zone1' assigned to the SpaceList of the three spaces:
# the instance of Block1:Zone2 has the name of Block1:Zone1, and so has its EMS suffix
SPACE_LIST_EMS_SUFFIXES = {'Block1:Zone1': 'Block1_Zone1', 'Block1:Zone2': 'Space_2_People_Block1_Zone1'}
SPACE_LIST_INSTANCES = {'SPACE 1A PEOPLE BLOCK1:ZONE1': INSTANCE_1A, 'SPACE 1B PEOPLE BLOCK1:ZONE1': INSTANCE_1B,
                        'SPACE 2 PEOPLE BLOCK1:ZONE1': INSTANCE_2}


def test_space_list_without_space_types_finds_the_zones(tmp_path, monkeypatch):
    # Spaces without the Space Types of OpenStudio: the zones keep their names, as in the model without spaces
    table = _table(tmp_path, monkeypatch, _space_list_model(), SPACE_LIST_EMS_SUFFIXES, SPACE_LIST_INSTANCES)

    assert sorted(table.occupied_zone_list) == ['Block1:Zone1', 'Block1:Zone2']
    assert table.block_list == ['Block1']
    assert not table.df.columns.duplicated().any()
    for zone, values in ZONE_VALUES.items():
        assert _values(table, f'{zone}_Zone Operative Temperature (°C)') == values['temperature']
        assert _values(table, f'{zone}_Cooling Energy Demand (Wh)') == values['cooling']
    # The occupants of Block1:Zone2 ('Space 2 People Block1:Zone1') are not taken for those of Block1:Zone1
    assert _values(table, 'Block1:Zone1_PMV') == pytest.approx(MEAN_OF_1A_AND_1B[1])
    assert _values(table, 'Block1:Zone2_PMV') == INSTANCE_2[1]
    assert _values(table, 'Block1:Zone2_EN16798-1 Running mean outdoor temperature (°C)') == INSTANCE_2[0]
    # Nor are its EMS outputs: they are named after their zone, as those of the other zones
    assert _values(table, 'Block1:Zone2_Comfortable Hours_No Applicability (h)') == \
        ZONE_VALUES['Block1:Zone2']['comfortable']
    assert _values(table, 'Block1_Total_Cooling Energy Demand (Wh) (summed)') == [400.0, 600.0]
    assert _values(table, 'Building_Total_Comfortable Hours_No Applicability (h) (summed)') == [1.0, 2.0]


@pytest.mark.parametrize('hierarchy', [{'Block1': ['Space 2']}, {'Block1': ['Block1:Zone1', 'Space 2']}])
def test_space_list_with_openstudio_space_types_keeps_the_zone_of_two_spaces(tmp_path, monkeypatch, hierarchy):
    # The Space Types of OpenStudio: the zone of one space is named after its space, as in OpenStudio models,
    # and the zone of two spaces after the zone, as its EMS objects. Only the space needs a block.
    table = _table(tmp_path, monkeypatch, _space_list_model('All spaces'), SPACE_LIST_EMS_SUFFIXES,
                   SPACE_LIST_INSTANCES, block_zone_hierarchy=hierarchy, normalised_energy_units=True)

    assert sorted(table.occupied_zone_list) == ['BLOCK1:SPACE 2', 'BLOCK1:ZONE1']
    assert table.block_list == ['BLOCK1']
    assert not table.df.columns.duplicated().any()
    for zone, name in [('Block1:Zone1', 'BLOCK1:ZONE1'), ('Block1:Zone2', 'BLOCK1:SPACE 2')]:
        assert _values(table, f'{name}_Zone Operative Temperature (°C)') == ZONE_VALUES[zone]['temperature']
        assert _values(table, f'{name}_Comfortable Hours_No Applicability (h)') == ZONE_VALUES[zone]['comfortable']
    assert _values(table, 'BLOCK1:ZONE1_PMV') == pytest.approx(MEAN_OF_1A_AND_1B[1])
    assert _values(table, 'BLOCK1:SPACE 2_PMV') == INSTANCE_2[1]
    assert _values(table, 'BLOCK1_Total_Zone Floor Area (m2) (summed)') == [33.0, 33.0]


def test_openstudio_model_with_one_space_per_zone_keeps_the_names_of_the_spaces(tmp_path, monkeypatch):
    # The OpenStudio models that worked before: one space per zone, People in a SpaceList named like the
    # Space Type of the spaces
    building = _FakeIDF(*ZONES, _space('Space 1', 'Block1:Zone1', 'All spaces'),
                        _space('Space 2', 'Block1:Zone2', 'All spaces'),
                        _space_list('All spaces', ['Space 1', 'Space 2']), _people('Occupants', 'All spaces'))
    table = _table(
        tmp_path, monkeypatch, building,
        ems_suffixes={'Block1:Zone1': 'Space_1_Occupants', 'Block1:Zone2': 'Space_2_Occupants'},
        instances={'SPACE 1 OCCUPANTS': INSTANCE_1A, 'SPACE 2 OCCUPANTS': INSTANCE_2},
        block_zone_hierarchy={'Block1': ['Space 1', 'Space 2']},
    )

    assert sorted(table.occupied_zone_list) == ['BLOCK1:SPACE 1', 'BLOCK1:SPACE 2']
    for zone, name in [('Block1:Zone1', 'BLOCK1:SPACE 1'), ('Block1:Zone2', 'BLOCK1:SPACE 2')]:
        assert _values(table, f'{name}_Zone Operative Temperature (°C)') == ZONE_VALUES[zone]['temperature']
    assert _values(table, 'BLOCK1:SPACE 1_PMV') == INSTANCE_1A[1]
    assert _values(table, 'BLOCK1:SPACE 2_PMV') == INSTANCE_2[1]
    # The EMS outputs ('..._Space_1_Occupants', with the blank of the space replaced by '_') are named after
    # the spaces too, so they get the block (see tests/core/test_table_columns.py)
    assert _values(table, 'BLOCK1:SPACE 1_Comfortable Hours_No Applicability (h)') == \
        ZONE_VALUES['Block1:Zone1']['comfortable']
    assert _values(table, 'BLOCK1_Total_Comfortable Hours_No Applicability (h) (summed)') == [1.0, 2.0]


def test_model_without_spaces_keeps_its_columns(tmp_path, monkeypatch):
    # The DesignBuilder models that worked before: one People object per zone, without Space objects
    building = _FakeIDF(*ZONES, _people('People Block1:Zone1', 'Block1:Zone1'),
                        _people('People Block1:Zone2', 'Block1:Zone2'))
    table = _table(
        tmp_path, monkeypatch, building,
        ems_suffixes={'Block1:Zone1': 'Block1_Zone1', 'Block1:Zone2': 'Block1_Zone2'},
        instances={'PEOPLE BLOCK1:ZONE1': INSTANCE_1A, 'PEOPLE BLOCK1:ZONE2': INSTANCE_2},
    )

    assert sorted(table.occupied_zone_list) == ['Block1:Zone1', 'Block1:Zone2']
    assert _values(table, 'Block1:Zone1_PMV') == INSTANCE_1A[1]
    assert _values(table, 'Block1:Zone2_PMV') == INSTANCE_2[1]
    # The EMS outputs are named after their zones (see tests/core/test_table_columns.py)
    assert _values(table, 'Block1:Zone1_Comfortable Hours_No Applicability (h)') == \
        ZONE_VALUES['Block1:Zone1']['comfortable']
    assert _values(table, 'Block1:Zone2_Cooling Energy Demand (Wh)') == ZONE_VALUES['Block1:Zone2']['cooling']
