from types import SimpleNamespace

import os
import pandas as pd
import pytest

from accim.parametric_and_optimisation.analysis import AnalysisMixin


class DummySimulation(AnalysisMixin):
    def __init__(self, buildings=None):
        self.buildings = buildings or []
        self.building = self.buildings[0] if self.buildings else None


def test_representative_mode_all_keeps_legacy_behavior():
    idf_a = make_idf('idf_a.idf', zones=['Z1'], floors={'Z1': 10.0})
    idf_b = make_idf('idf_b.idf', zones=['Z1'], floors={'Z1': 20.0})

    legacy_sim = DummySimulation([idf_a, idf_b])
    representative_sim = DummySimulation([idf_a, idf_b])

    legacy_result = legacy_sim.set_building_floor_area(mode='all')
    representative_result = representative_sim.set_building_floor_area(
        mode='all',
        representative_mode='all',
    )

    assert representative_result == legacy_result


def test_representative_mode_by_category_loads_fewer_idfs(monkeypatch, tmp_path):
    idf_areas = {
        'res_a': 10.0,
        'res_b': 12.0,
        'off_a': 20.0,
        'off_b': 22.0,
    }

    idf_paths = []
    for idf_name in idf_areas:
        idf_path = tmp_path / f'{idf_name}.idf'
        idf_path.write_text('! dummy idf for testing\n', encoding='ascii')
        idf_paths.append(str(idf_path))

    loaded_paths = []

    def fake_get_building(path):
        loaded_paths.append(path)
        stem = os.path.splitext(os.path.basename(path))[0]
        return make_idf(f'{stem}.idf', zones=['Z1'], floors={'Z1': idf_areas[stem]})

    monkeypatch.setattr('accim.utils.get_building', fake_get_building)

    sim = DummySimulation(buildings=[])
    sim.idf_backup_path = idf_paths
    sim.idf_mapping_rules = {
        'building_type': {
            'residential': ['res'],
            'office': ['off'],
        }
    }
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'idf': ['res_a', 'res_b', 'off_a', 'off_b'],
            'building_type': ['residential', 'residential', 'office', 'office'],
        }
    )

    result = sim.set_building_floor_area(
        mode='all',
        representative_mode='by_idf_mapping_category',
        representative_category='building_type',
    )

    loaded_stems = {os.path.splitext(os.path.basename(path))[0] for path in loaded_paths}
    assert len(loaded_paths) == 2
    assert loaded_stems == {'res_a', 'off_a'}

    assert set(result.keys()) == {'res_a', 'res_b', 'off_a', 'off_b'}
    assert result['res_a'] == pytest.approx(result['res_b'])
    assert result['off_a'] == pytest.approx(result['off_b'])


def test_by_category_invalid_representative_category_includes_available_categories():
    idf = make_idf('idf_a.idf', zones=['Z1'], floors={'Z1': 10.0})
    sim = DummySimulation([idf])
    sim.idf_mapping_rules = {
        'climate_zone': {'CZ1': 'cz1'},
        'performance': {'high': 'high'},
        'building_type': {'residential': 'res'},
    }
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'idf': ['idf_a'],
            'building_type': ['residential'],
        }
    )

    with pytest.raises(ValueError) as exc_info:
        sim.set_building_floor_area(
            mode='all',
            representative_mode='by_idf_mapping_category',
            representative_category='foo',
        )

    message = str(exc_info.value)
    assert "Invalid representative_category='foo'" in message
    assert 'climate_zone' in message
    assert 'performance' in message
    assert 'building_type' in message


def test_by_category_requires_category_column_in_outputs_param_simulation():
    idf = make_idf('idf_a.idf', zones=['Z1'], floors={'Z1': 10.0})
    sim = DummySimulation([idf])
    sim.idf_mapping_rules = {
        'building_type': {'residential': 'res'},
        'performance': {'high': 'high'},
    }
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'idf': ['idf_a'],
            'performance': ['high'],
        }
    )

    with pytest.raises(ValueError) as exc_info:
        sim.set_building_floor_area(
            mode='all',
            representative_mode='by_idf_mapping_category',
            representative_category='building_type',
        )

    message = str(exc_info.value)
    assert "Category column 'building_type' is missing in outputs_param_simulation" in message
    assert 'Available categories' in message
    assert 'building_type' in message
    assert 'performance' in message


def test_custom_map_validates_coverage_and_representative_idf_routes():
    idf_res = make_idf('res_a.idf', zones=['Z1'], floors={'Z1': 10.0})
    idf_off = make_idf('off_a.idf', zones=['Z1'], floors={'Z1': 20.0})
    sim = DummySimulation([idf_res, idf_off])
    sim.idf_mapping_rules = {
        'building_type': {
            'residential': ['res'],
            'office': ['off'],
        }
    }
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'idf': ['res_a', 'off_a'],
            'building_type': ['residential', 'office'],
        }
    )

    with pytest.raises(ValueError, match='missing category values'):
        sim.set_building_floor_area(
            mode='all',
            representative_mode='custom_map',
            representative_category='building_type',
            representative_map={'residential': 'res_a'},
        )

    with pytest.raises(ValueError, match='was not found in outputs_param_simulation IDFs'):
        sim.set_building_floor_area(
            mode='all',
            representative_mode='custom_map',
            representative_category='building_type',
            representative_map={
                'residential': 'res_a',
                'office': 'missing_idf',
            },
        )


def test_representative_by_category_allows_normalize_outputs_with_full_idf_mapping():
    idf_res = make_idf('res_a.idf', zones=['Z1'], floors={'Z1': 10.0})
    idf_off = make_idf('off_a.idf', zones=['Z1'], floors={'Z1': 20.0})
    sim = DummySimulation([idf_res, idf_off])
    sim.idf_mapping_rules = {
        'building_type': {
            'residential': ['res'],
            'office': ['off'],
        }
    }
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'idf': ['res_a', 'off_a', 'off_b'],
            'building_type': ['residential', 'office', 'office'],
            'Heating:Electricity [J]': [3600000.0, 7200000.0, 10800000.0],
        }
    )

    sim.set_building_floor_area(
        mode='all',
        representative_mode='by_idf_mapping_category',
        representative_category='building_type',
    )

    assert set(sim.building_floor_area.keys()) == {'res_a', 'off_a', 'off_b'}

    sim.normalize_outputs(df_types=['parametric'])

    assert 'Heating:Electricity [kWh/m2]' in sim.outputs_param_simulation.columns
    assert sim.outputs_param_simulation['Heating:Electricity [kWh/m2]'].tolist() == pytest.approx([
        0.1,
        0.1,
        0.15,
    ])


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
