"""Tests for the zone totals, the block totals and the normalised energy units of Table.

Found on 2026-10-19 with the annual results of the sample models simulated with EnergyPlus 25.1 (vrf_ac and
vrf_mm). In the OpenStudio models (one space per zone, the occupants in a SpaceList named like the Space Type of
the spaces), where Table names the zones after their spaces, Table:
- gave 0 in the columns '<zone>_Total Energy Demand (Wh) (summed)' and '<zone>_Total Energy Consumption (Wh)
  (summed)', because it looked for the outputs of the HVAC system of each zone with the name of the zone after
  renaming the zones after their spaces;
- when the names of the spaces have blanks (as the default names of OpenStudio, 'Space 1'), did not give the
  block to the EMS outputs of the zones, which end with '<Space>_<People>' with the blanks replaced by '_', so
  the block totals of these outputs were 0 (comfort hours, floor area and air volume) and the block totals of
  energy, divided by a floor area of 0, were inf;
- with normalised_energy_units=True (the default), stopped with IndexError when the names of the zones have no
  colon (as those of the sample OSM_TestResidentialUnit_v01_onlygeometry, 'Floor_1_Zone'), because it looked
  for the floor area of each zone with the name of the zone, which no floor area column has.

In all the models, Table:
- labelled the energy of each zone kWh/m2 (or Wh/m2) with normalised_energy_units=True, but did not divide it by
  the floor area of the zone (only the zone totals of the zones whose names have no colon);
- kept the raw names of the EMS outputs of the zones of DesignBuilder models
  ('EMS:COMFORTABLE HOURS_NO APPLICABILITY_BLOCK1_ZONE1 [H](HOURLY)'), and of the zones without Space objects
  whose names have blanks ('Zone 1'), which, as those of the spaces with blanks, did not get the block;
- found the columns of each zone, and of each block, by the names they contain, so the zone total of
  'Block1:Zone1' added up the outputs of 'Block1:Zone10', and the block totals of 'Block1' those of 'Block10'.

The CSV files have the names of the columns that accim and EnergyPlus give the outputs, and made-up values. A
fake IDF replaces the IDF that Table reads.
"""
from types import SimpleNamespace

import besos.eppy_funcs
import pytest

from accim.data.postprocessing.main import Table
from accim.sim.apmv_setpoints import _resolve_targets, _sanitize_ems_name


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
    return [_Obj(key='ZONE', Name=name),
            _Obj(key='ZONECONTROL:THERMOSTAT', Name=f'{name} Thermostat', Zone_or_ZoneList_Name=name)]


def _openstudio_model(zones, spaces, space_type, people):
    """One space per zone, and one People object assigned to a SpaceList named like the Space Type of the spaces."""
    return _FakeIDF(
        *[obj for zone in zones for obj in _zone(zone)],
        *[_Obj(key='SPACE', Name=space, Zone_Name=zone, Space_Type=space_type) for zone, space in zip(zones, spaces)],
        _Obj(key='SPACELIST', Name=space_type, obj=['SPACELIST', space_type, *spaces]),
        _Obj(key='PEOPLE', Name=people, Zone_or_ZoneList_or_Space_or_SpaceList_Name=space_type),
    )


# The sample OSM_TestResidentialUnit_v01_onlygeometry: the names of the zones have no colon, and those of the
# spaces have no blanks
RESIDENTIAL = dict(
    building=_openstudio_model(['Floor_1_Zone', 'Floor_2_Zone'], ['Floor_1', 'Floor_2'],
                               'Residential - Living Space', 'Residential Living Occupants'),
    ems_suffixes=['Floor_1_Residential_Living_Occupants', 'Floor_2_Residential_Living_Occupants'],
    hierarchy={'Residential': ['Floor_1', 'Floor_2']},
    zone_names=['RESIDENTIAL:FLOOR_1', 'RESIDENTIAL:FLOOR_2'],
    block='RESIDENTIAL',
)
# The default names of OpenStudio: the names of the spaces have blanks
OFFICE = dict(
    building=_openstudio_model(['Thermal Zone 1', 'Thermal Zone 2'], ['Space 1', 'Space 2'], 'Office',
                               'Office People'),
    ems_suffixes=['Space_1_Office_People', 'Space_2_Office_People'],
    hierarchy={'Block1': ['Space 1', 'Space 2']},
    zone_names=['BLOCK1:SPACE 1', 'BLOCK1:SPACE 2'],
    block='BLOCK1',
)
OPENSTUDIO_MODELS = pytest.mark.parametrize('model', [RESIDENTIAL, OFFICE], ids=['residential', 'office'])


def _model_without_spaces(zones, hierarchy=None):
    """No Space objects, and one People object assigned to each zone, as in the DesignBuilder models."""
    return dict(
        building=_FakeIDF(*[obj for zone in zones for obj in _zone(zone)],
                          *[_Obj(key='PEOPLE', Name=f'People {zone}', Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone)
                            for zone in zones]),
        ems_suffixes=[_sanitize_ems_name(zone) for zone in zones],
        hierarchy=hierarchy,
        zone_names=[f'{block.upper()}:{zone.upper()}' for block, block_zones in hierarchy.items()
                    for zone in block_zones] if hierarchy else zones,
    )


# The DesignBuilder models, whose zones have the pattern block:zone
DESIGNBUILDER = _model_without_spaces(['Block1:Zone1', 'Block1:Zone2'])
# Zones without Space objects whose names have blanks and no block
ZONES_WITH_BLANKS = _model_without_spaces(['Zone 1', 'Zone 2'], hierarchy={'Block1': ['Zone 1', 'Zone 2']})

# The hourly values of the outputs of each zone, for two hours: the energy of the VRF system in W (the indoor
# units) and in J (the outdoor unit)
ZONE_VALUES = [
    dict(area=10.0, volume=30.0, comfortable=[1.0, 0.0], temperature=[25.0, 26.0], cooling=[100.0, 300.0],
         heating=[50.0, 0.0], cooling_electricity=[20.0 * 3600, 60.0 * 3600], heating_electricity=[10.0 * 3600, 0.0]),
    dict(area=20.0, volume=60.0, comfortable=[1.0, 1.0], temperature=[27.0, 28.0], cooling=[200.0, 400.0],
         heating=[0.0, 100.0], cooling_electricity=[40.0 * 3600, 80.0 * 3600], heating_electricity=[0.0, 20.0 * 3600]),
]
# In Wh: the demand (cooling and heating of the indoor units) and the consumption (outdoor unit) of each zone
DEMAND = [[150.0, 300.0], [200.0, 500.0]]
CONSUMPTION = [[30.0, 60.0], [40.0, 100.0]]
CSV_NAME = 'Model[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X[Seville.csv'


def _outputs(building, ems_suffixes):
    """The columns of the CSV file: the EMS outputs of each target, and the outputs of each zone and instance."""
    columns = {'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)': [10.0, 11.0]}
    for target, suffix, values in zip(_resolve_targets(building), ems_suffixes, ZONE_VALUES):
        # The test data have the names of accim
        assert target['ems_suffix'] == suffix
        zone = target['zone_name'].upper()
        columns.update({
            f'EMS:Comfortable Hours_No Applicability_{suffix} [H](Hourly)': values['comfortable'],
            f'EMS:Zone Floor Area_{suffix} [m2](Hourly)': [values['area']] * 2,
            f'EMS:Zone Air Volume_{suffix} [m3](Hourly)': [values['volume']] * 2,
            f'{zone}:Zone Operative Temperature [C](Hourly)': values['temperature'],
            f'{target["sensor_key"].upper()}:Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor '
            f'Air Temperature [C](Hourly)': [20.0, 21.0],
            f'{zone} VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate [W](Hourly)': values['cooling'],
            f'{zone} VRF INDOOR UNIT DX HEATING COIL:Heating Coil Heating Rate [W](Hourly)': values['heating'],
            f'VRF OUTDOOR UNIT_{zone}:VRF Heat Pump Cooling Electricity Energy [J](Hourly)':
                values['cooling_electricity'],
            f'VRF OUTDOOR UNIT_{zone}:VRF Heat Pump Heating Electricity Energy [J](Hourly)':
                values['heating_electricity'],
        })
    return columns


def _table(tmp_path, monkeypatch, model, **kwargs):
    """Run Table on a CSV file with the outputs of the model."""
    columns = _outputs(model['building'], model['ems_suffixes'])
    lines = [','.join(['Date/Time', *columns])]
    for hour in range(2):
        lines.append(','.join([f' 01/01  0{hour + 1}:00:00', *(str(v[hour]) for v in columns.values())]))
    (tmp_path / CSV_NAME).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(besos.eppy_funcs, 'get_building', lambda idf_path: model['building'])
    arguments = dict(
        datasets=[CSV_NAME], source_frequency='hourly', frequency='hourly', frequency_agg_func='sum',
        standard_outputs=True, level=['block', 'building'], level_agg_func=['sum', 'mean'], level_excluded_zones=[],
        block_zone_hierarchy=model['hierarchy'], normalised_energy_units=False, energy_units_in_kwh=False,
        idf_path='model.idf',
    )
    arguments.update(kwargs)
    return Table(**arguments)


def _values(table, column):
    return table.df[column].tolist()


@OPENSTUDIO_MODELS
def test_zone_totals_of_openstudio_models(tmp_path, monkeypatch, model):
    table = _table(tmp_path, monkeypatch, model)

    assert table.occupied_zone_list == model['zone_names']
    zones = [z.Name for z in model['building'].idfobjects['ZONE']]
    for zone, demand, consumption in zip(zones, DEMAND, CONSUMPTION):
        assert _values(table, f'{zone}_Total Energy Demand (Wh) (summed)') == demand
        assert _values(table, f'{zone}_Total Energy Consumption (Wh) (summed)') == consumption


@OPENSTUDIO_MODELS
def test_block_totals_of_openstudio_models(tmp_path, monkeypatch, model):
    table = _table(tmp_path, monkeypatch, model, normalised_energy_units=True)
    block = model['block']

    # The EMS outputs of the zones get their names, as the other outputs of the zones
    for name, values in zip(model['zone_names'], ZONE_VALUES):
        assert _values(table, f'{name}_Comfortable Hours_No Applicability (h)') == values['comfortable']
        assert _values(table, f'{name}_Zone Floor Area (m2)') == [values['area']] * 2
    assert _values(table, f'{block}_Total_Comfortable Hours_No Applicability (h) (summed)') == [2.0, 1.0]
    assert _values(table, f'{block}_Total_Zone Floor Area (m2) (summed)') == [30.0, 30.0]
    assert _values(table, f'{block}_Total_Zone Air Volume (m3) (summed)') == [90.0, 90.0]
    assert _values(table, f'{block}_Total_Cooling Energy Demand (Wh/m2) (summed)') == \
        pytest.approx([300.0 / 30, 700.0 / 30])
    assert _values(table, f'{block}_Total_Total Energy Consumption (Wh/m2) (summed)') == \
        pytest.approx([70.0 / 30, 160.0 / 30])
    assert _values(table, f'{block}_Total_Total Energy Consumption (Wh/m2) (summed)') == \
        _values(table, 'Building_Total_Total Energy Consumption (Wh/m2) (summed)')


@OPENSTUDIO_MODELS
def test_openstudio_models_with_normalised_energy_units(tmp_path, monkeypatch, model):
    # The default arguments: the energy in kWh/m2
    table = _table(tmp_path, monkeypatch, model, normalised_energy_units=True, energy_units_in_kwh=True)

    zones = [z.Name for z in model['building'].idfobjects['ZONE']]
    for zone, name, demand, consumption, values in zip(zones, model['zone_names'], DEMAND, CONSUMPTION, ZONE_VALUES):
        assert _values(table, f'{zone}_Total Energy Demand (kWh/m2) (summed)') == \
            pytest.approx([v / 1000 / values['area'] for v in demand])
        assert _values(table, f'{zone}_Total Energy Consumption (kWh/m2) (summed)') == \
            pytest.approx([v / 1000 / values['area'] for v in consumption])
        # The energy of each zone is divided by the floor area of the zone too
        assert _values(table, f'{name}_Cooling Energy Demand (kWh/m2)') == \
            pytest.approx([v / 1000 / values['area'] for v in values['cooling']])
    assert _values(table, 'Building_Total_Total Energy Demand (kWh/m2) (summed)') == \
        pytest.approx([350.0 / 1000 / 30, 800.0 / 1000 / 30])


def test_zone_energy_of_designbuilder_models_is_divided_by_the_floor_area_of_the_zone(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, normalised_energy_units=True)

    for zone, demand, consumption, values in zip(DESIGNBUILDER['zone_names'], DEMAND, CONSUMPTION, ZONE_VALUES):
        area = values['area']
        assert _values(table, f'{zone}_Cooling Energy Demand (Wh/m2)') == \
            pytest.approx([v / area for v in values['cooling']])
        assert _values(table, f'{zone}_Heating Energy Demand (Wh/m2)') == \
            pytest.approx([v / area for v in values['heating']])
        assert _values(table, f'{zone}_Cooling Energy Consumption (Wh/m2)') == \
            pytest.approx([v / 3600 / area for v in values['cooling_electricity']])
        assert _values(table, f'{zone}_Total Energy Demand (Wh/m2) (summed)') == pytest.approx([v / area for v in demand])
        assert _values(table, f'{zone}_Total Energy Consumption (Wh/m2) (summed)') == \
            pytest.approx([v / area for v in consumption])
    # The blocks and the building, as before: their energy divided by their floor area
    assert _values(table, 'Block1_Total_Cooling Energy Demand (Wh/m2) (summed)') == \
        pytest.approx([300.0 / 30, 700.0 / 30])
    assert _values(table, 'Building_Total_Total Energy Demand (Wh/m2) (summed)') == \
        pytest.approx([350.0 / 30, 800.0 / 30])


def test_ems_outputs_of_designbuilder_models_are_named_after_their_zones(tmp_path, monkeypatch):
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER)

    for zone, values in zip(DESIGNBUILDER['zone_names'], ZONE_VALUES):
        assert _values(table, f'{zone}_Comfortable Hours_No Applicability (h)') == values['comfortable']
        assert _values(table, f'{zone}_Zone Floor Area (m2)') == [values['area']] * 2
        assert _values(table, f'{zone}_Zone Air Volume (m3)') == [values['volume']] * 2
        assert _values(table, f'{zone}_Zone Operative Temperature (°C)') == values['temperature']
    assert not [c for c in table.df.columns if c.startswith('EMS:') and 'BLOCK1_ZONE' in c]
    assert _values(table, 'Block1_Total_Comfortable Hours_No Applicability (h) (summed)') == [2.0, 1.0]


def test_zones_without_spaces_with_blanks_in_their_names(tmp_path, monkeypatch):
    # As the spaces with blanks: the EMS outputs end with 'Zone_1', and Table adds the block to 'Zone 1'
    table = _table(tmp_path, monkeypatch, ZONES_WITH_BLANKS, normalised_energy_units=True)

    assert table.occupied_zone_list == ['BLOCK1:ZONE 1', 'BLOCK1:ZONE 2']
    for zone, name, demand, values in zip(['Zone 1', 'Zone 2'], ZONES_WITH_BLANKS['zone_names'], DEMAND,
                                          ZONE_VALUES):
        assert _values(table, f'{name}_Comfortable Hours_No Applicability (h)') == values['comfortable']
        assert _values(table, f'{name}_Cooling Energy Demand (Wh/m2)') == \
            pytest.approx([v / values['area'] for v in values['cooling']])
        assert _values(table, f'{zone}_Total Energy Demand (Wh/m2) (summed)') == \
            pytest.approx([v / values['area'] for v in demand])
    assert _values(table, 'BLOCK1_Total_Comfortable Hours_No Applicability (h) (summed)') == [2.0, 1.0]
    assert _values(table, 'BLOCK1_Total_Zone Floor Area (m2) (summed)') == [30.0, 30.0]
    assert _values(table, 'BLOCK1_Total_Cooling Energy Demand (Wh/m2) (summed)') == \
        pytest.approx([300.0 / 30, 700.0 / 30])


@pytest.mark.parametrize('zones', [['Block1:Zone1', 'Block1:Zone10'], ['Block1:Zone1', 'Block10:Zone1']],
                         ids=['zones', 'blocks'])
def test_names_that_contain_the_name_of_another_zone_or_block(tmp_path, monkeypatch, zones):
    model = _model_without_spaces(zones)
    table = _table(tmp_path, monkeypatch, model, normalised_energy_units=True)

    assert sorted(table.occupied_zone_list) == sorted(zones)
    assert not table.df.columns.duplicated().any()
    for zone, demand, values in zip(zones, DEMAND, ZONE_VALUES):
        area = values['area']
        assert _values(table, f'{zone}_Cooling Energy Demand (Wh/m2)') == \
            pytest.approx([v / area for v in values['cooling']])
        assert _values(table, f'{zone}_Total Energy Demand (Wh/m2) (summed)') == pytest.approx([v / area for v in demand])
        assert _values(table, f'{zone}_Comfortable Hours_No Applicability (h)') == values['comfortable']
    blocks = sorted({zone.split(':')[0] for zone in zones})
    if len(blocks) == 1:
        assert _values(table, 'Block1_Total_Cooling Energy Demand (Wh/m2) (summed)') == \
            pytest.approx([300.0 / 30, 700.0 / 30])
    else:
        # Each block has one zone
        for block, values in zip(['Block1', 'Block10'], ZONE_VALUES):
            assert _values(table, f'{block}_Total_Zone Floor Area (m2) (summed)') == [values['area']] * 2
            assert _values(table, f'{block}_Total_Cooling Energy Demand (Wh/m2) (summed)') == \
                pytest.approx([v / values['area'] for v in values['cooling']])
            assert _values(table, f'{block}_Total_Comfortable Hours_No Applicability (h) (summed)') == \
                values['comfortable']


def test_excluded_zone_whose_name_is_part_of_the_name_of_another_zone(tmp_path, monkeypatch):
    model = _model_without_spaces(['Block1:Zone1', 'Block1:Zone10'])
    table = _table(tmp_path, monkeypatch, model, level_excluded_zones=['Block1:Zone1'])

    # Only the outputs of Block1:Zone10 (the second zone) are added up
    assert _values(table, 'Building_Total_Cooling Energy Demand (Wh) (summed)') == ZONE_VALUES[1]['cooling']
    assert _values(table, 'Block1_Total_Comfortable Hours_No Applicability (h) (summed)') == \
        ZONE_VALUES[1]['comfortable']
