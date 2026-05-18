from types import SimpleNamespace

import pytest

from accim.parametric_and_optimisation.analysis import AnalysisMixin


class DummySimulation(AnalysisMixin):
    def __init__(self, buildings=None):
        self.buildings = buildings or []
        self.building = self.buildings[0] if self.buildings else None


def obj(**fields):
    instance = SimpleNamespace(**fields)
    instance.fieldnames = list(fields)
    return instance


def make_idf(idfname, zones, floors, people_target=None, zonelist_zones=None,
             thermostat_zones=None, equipment_connection_zones=None):
    idfobjects = {
        'ZONE': [obj(Name=z) for z in zones],
        'BuildingSurface:Detailed': [
            obj(
                Name=f'Floor_{zone}',
                Surface_Type='Floor',
                Zone_Name=zone,
                Space_Name='',
                area=area,
            )
            for zone, area in floors.items()
        ],
    }

    if people_target:
        idfobjects['PEOPLE'] = [
            obj(
                Name='People',
                Zone_or_ZoneList_or_Space_or_SpaceList_Name=people_target,
            )
        ]

    if zonelist_zones:
        zonelist_fields = {'Name': people_target or 'Allzones'}
        for index, zone in enumerate(zonelist_zones, start=1):
            zonelist_fields[f'Zone_{index}_Name'] = zone
        idfobjects['ZONELIST'] = [obj(**zonelist_fields)]

    if thermostat_zones:
        idfobjects['ZONECONTROL:THERMOSTAT'] = [
            obj(Name=f'{zone} Thermostat', Zone_or_ZoneList_Name=zone)
            for zone in thermostat_zones
        ]

    if equipment_connection_zones:
        idfobjects['ZONEHVAC:EQUIPMENTCONNECTIONS'] = [
            obj(
                Zone_Name=zone,
                Zone_Conditioning_Equipment_List_Name=f'{zone} Equipment',
                Zone_Air_Inlet_Node_or_NodeList_Name=f'{zone} Supply Inlet',
            )
            for zone in equipment_connection_zones
        ]

    return SimpleNamespace(idfname=idfname, idfobjects=idfobjects)


def test_occupied_uses_people_zonelist_while_air_conditioned_uses_hvac_zones():
    idf = make_idf(
        'SF_Detached_A_max_South.idf',
        zones=['LivingRoom', 'Hall', 'OFFICE'],
        floors={'LivingRoom': 8.4, 'Hall': 7.2, 'OFFICE': 5.2},
        people_target='Allzones',
        zonelist_zones=['LivingRoom', 'OFFICE'],
        thermostat_zones=['LivingRoom', 'Hall', 'OFFICE'],
    )
    sim = DummySimulation([idf])

    assert sim.set_building_floor_area(mode='occupied') == pytest.approx(13.6)
    assert sim.set_building_floor_area(mode='air-conditioned') == pytest.approx(20.8)
    assert sim.set_building_floor_area(mode='air-condicioned') == pytest.approx(20.8)


def test_air_conditioned_detects_zone_hvac_equipment_connections():
    idf = make_idf(
        'equipment_connections.idf',
        zones=['Conditioned', 'Unconditioned'],
        floors={'Conditioned': 30.0, 'Unconditioned': 12.0},
        equipment_connection_zones=['Conditioned'],
    )
    sim = DummySimulation([idf])

    assert sim.set_building_floor_area(mode='air-conditioned') == pytest.approx(30.0)


def test_list_mode_accepts_global_list_and_per_idf_dictionary():
    idf_a = make_idf('idf_a.idf', zones=['Z1', 'Z2'], floors={'Z1': 10.0, 'Z2': 5.0})
    idf_b = make_idf('idf_b.idf', zones=['Z1', 'Z2'], floors={'Z1': 20.0, 'Z2': 8.0})
    sim = DummySimulation([idf_a, idf_b])

    global_result = sim.set_building_floor_area(mode='list', zones_list=['Z1'])
    assert global_result['idf_a'] == pytest.approx(10.0)
    assert global_result['idf_b'] == pytest.approx(20.0)

    per_idf_result = sim.set_building_floor_area(
        mode='list',
        zones_list={'idf_a': ['Z1'], 'idf_b.idf': ['Z2']},
    )
    assert per_idf_result['idf_a'] == pytest.approx(10.0)
    assert per_idf_result['idf_b'] == pytest.approx(8.0)


def test_custom_mode_accepts_string_float_and_per_idf_dictionary():
    assert DummySimulation().set_building_floor_area(mode='custom', custom_area='101,96') == pytest.approx(101.96)

    idf_a = make_idf('idf_a.idf', zones=['Z1'], floors={'Z1': 10.0})
    idf_b = make_idf('idf_b.idf', zones=['Z1'], floors={'Z1': 20.0})
    sim = DummySimulation([idf_a, idf_b])

    result = sim.set_building_floor_area(
        mode='custom',
        custom_area={'idf_a': '10.5', 'idf_b.idf': 20.25},
    )
    assert result['idf_a'] == pytest.approx(10.5)
    assert result['idf_b'] == pytest.approx(20.25)


def test_per_idf_dictionary_rejects_missing_or_unknown_keys():
    idf_a = make_idf('idf_a.idf', zones=['Z1'], floors={'Z1': 10.0})
    idf_b = make_idf('idf_b.idf', zones=['Z1'], floors={'Z1': 20.0})
    sim = DummySimulation([idf_a, idf_b])

    with pytest.raises(ValueError, match='missing IDF keys'):
        sim.set_building_floor_area(mode='custom', custom_area={'idf_a': 10.0})

    with pytest.raises(ValueError, match='unknown IDF keys'):
        sim.set_building_floor_area(
            mode='list',
            zones_list={'idf_a': ['Z1'], 'idf_b': ['Z1'], 'idf_c': ['Z1']},
        )
