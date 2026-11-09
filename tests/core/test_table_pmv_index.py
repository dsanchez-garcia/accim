"""Tests for Table with the outputs of the setpoints based on the indices derived from the PMV (D2).

The setpoints of accim.sim.pmv_index (apply_apmv_setpoints, apply_epmv_setpoints, apply_pmv_setpoints) report the EMS
outputs of each zone (the index, the coefficient of the season, the setpoints of the index and the hour counters), the
schedules of the PMV setpoints of the thermostats, the mean air temperature of the zones and, with the metabolic
correction of the ePMV, the factor and the corrected activity level of each People object. Before (checked on
2026-11-09 with a simulation of 3 days of the sample model with ePMV setpoints and EnergyPlus 25.1), Table:
- stopped with "ValueError: Columns must be same length as key" with the CSV files that run_ep names '<IDF>[<EPW>.csv',
  those of the IDFs that are not output IDFs of AddAccis, such as the IDFs with these setpoints;
- with daily values and frequency_agg_func='sum', added up the index, the expectancy factor (16.8 instead of 0.7), the
  setpoints, the schedules and the mean air temperature;
- took the corrected activity level (W/person) for an energy: Wh, kWh, per m2;
- kept the EMS names of the outputs of the zones ('EMS:EPMV_BLOCK1:ZONE1 [](HOURLY)'), without block and building
  values, and dropped them with standard_outputs=True.

The CSV files have the names of the columns that EnergyPlus gives the outputs (those of the simulation above), and
made-up values. A fake IDF replaces the IDF that Table reads.
"""
import builtins
from types import SimpleNamespace

import matplotlib
matplotlib.use('Agg')
import pytest

import accim.sim.accis
from accim.data.postprocessing import pmv_index_columns
from accim.data.postprocessing.main import Table, _zorder
from accim.sim.pmv_index import (METABOLIC_CORRECTION_OUTPUTS, PMV_INDICES, PMV_SETPOINT_SCHEDULES, zone_outputs)
from accim.sim.targets import resolve_targets, sanitize_ems_name


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


# The sample model of the setpoints (DesignBuilder): one People object in each zone
DESIGNBUILDER = dict(
    building=_FakeIDF(*_zone('Block1:Zone1'), *_zone('Block1:Zone2'),
                      *[_Obj(key='PEOPLE', Name=f'People {zone}', Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone)
                        for zone in ('Block1:Zone1', 'Block1:Zone2')]),
    hierarchy=None,
    zone_names=['Block1:Zone1', 'Block1:Zone2'],
    block='Block1',
    people_zones={'People Block1:Zone1': 'Block1:Zone1', 'People Block1:Zone2': 'Block1:Zone2'},
)
# The sample residential model of OpenStudio (that of the notebooks of the aPMV and ePMV setpoints): one People object
# for the two floors, through a SpaceList named like the Space Type of their spaces, so the zones are named after their
# spaces, and the EMS outputs end with '<Space>_<People>'
RESIDENTIAL = dict(
    building=_FakeIDF(
        *_zone('Floor_1_Zone'), *_zone('Floor_2_Zone'),
        _Obj(key='SPACE', Name='Floor_1', Zone_Name='Floor_1_Zone', Space_Type='Residential - Living Space'),
        _Obj(key='SPACE', Name='Floor_2', Zone_Name='Floor_2_Zone', Space_Type='Residential - Living Space'),
        _Obj(key='SPACELIST', Name='Residential - Living Space',
             fieldvalues=['SPACELIST', 'Residential - Living Space', 'Floor_1', 'Floor_2']),
        _Obj(key='PEOPLE', Name='Residential Living Occupants',
             Zone_or_ZoneList_or_Space_or_SpaceList_Name='Residential - Living Space')),
    hierarchy={'Residential': ['Floor_1', 'Floor_2']},
    zone_names=['RESIDENTIAL:FLOOR_1', 'RESIDENTIAL:FLOOR_2'],
    block='RESIDENTIAL',
    # One People object for the two zones: its outputs of the metabolic correction are of no zone
    people_zones={'Residential Living Occupants': None},
)
INDICES = pytest.mark.parametrize('index', list(PMV_INDICES))
CSV_NAME = 'TestModel_aPMV[Seville.csv'
# A zone with two People objects (the occupants and the visitors), and a zone with one
TWO_PEOPLE = dict(
    building=_FakeIDF(*_zone('Block1:Zone1'), *_zone('Block1:Zone2'),
                      _Obj(key='PEOPLE', Name='Office People', Zone_or_ZoneList_or_Space_or_SpaceList_Name='Block1:Zone1'),
                      _Obj(key='PEOPLE', Name='Visitors', Zone_or_ZoneList_or_Space_or_SpaceList_Name='Block1:Zone1'),
                      _Obj(key='PEOPLE', Name='People Block1:Zone2',
                           Zone_or_ZoneList_or_Space_or_SpaceList_Name='Block1:Zone2')),
    hierarchy=None,
    zone_names=['Block1:Zone1', 'Block1:Zone2'],
    block='Block1',
    people_zones={'Office People': 'Block1:Zone1', 'Visitors': 'Block1:Zone1', 'People Block1:Zone2': 'Block1:Zone2'},
)
METABOLIC_OUTPUTS = [output for output, _ in METABOLIC_CORRECTION_OUTPUTS]
MODELS = pytest.mark.parametrize('model', [DESIGNBUILDER, RESIDENTIAL, TWO_PEOPLE],
                                 ids=['designbuilder', 'residential', 'two_people'])


def _outputs(model, index):
    """The columns of the CSV file of a simulation with the setpoints of an index and the metabolic correction (that
    of the ePMV, with the others to check them too), and their values in two hours of a day: {column: [first hour,
    second hour]}, and the column of each output of each zone, {(zone, output): column}."""
    columns, of_zone = {}, {}
    targets = resolve_targets(model['building'])
    for number, (zone, target) in enumerate(zip(model['zone_names'], targets)):
        suffix = target.ems_suffix
        for position, (output, (_, units, data_type)) in enumerate(zone_outputs(PMV_INDICES[index]).items()):
            column = f'EMS:{output}_{suffix} [{units}](Hourly)'
            # The counters are 0 or 1 in each hour; the other outputs, any numbers
            columns[column] = [1.0, 0.0] if units == 'H' else [number + position / 10, number + position / 10 + 0.5]
            of_zone[zone, output] = column
        for position, schedule in enumerate(PMV_SETPOINT_SCHEDULES):
            column = f'{schedule}_{target.zone_name.upper()}:Schedule Value [](Hourly)'
            columns[column] = [(-1) ** (position + 1) * 0.5, (-1) ** (position + 1) * 100.0]
            of_zone[zone, schedule] = column
        columns[f'{target.zone_name.upper()}:Zone Mean Air Temperature [C](Hourly)'] = [24.0 + number, 25.0 + number]
        of_zone[zone, 'Zone Mean Air Temperature'] = f'{target.zone_name.upper()}:Zone Mean Air Temperature [C](Hourly)'
        columns[f'{target.zone_name.upper()}:Zone Operative Temperature [C](Hourly)'] = [26.0 + number, 27.0 + number]
        for key in target.instance_keys:
            columns[f'{key.upper()}:Zone Thermal Comfort Fanger Model PMV [](Hourly)'] = [0.5, 0.7]
            columns[f'{key.upper()}:Zone Thermal Comfort Fanger Model PPD [%](Hourly)'] = [10.0, 15.0]
    for number, people in enumerate(model['building'].idfobjects['PEOPLE']):
        for output, units in METABOLIC_CORRECTION_OUTPUTS:
            column = f'EMS:{output}_{sanitize_ems_name(people.Name)} [{units}](Hourly)'
            columns[column] = ([0.95 - number / 100, 0.9 - number / 100] if units == ''
                               else [100.0 + 10 * number, 95.0 + 10 * number])
            of_zone[people.Name, output] = column
    return columns, of_zone


def _write_csv(path, columns):
    lines = [','.join(['Date/Time', *columns])]
    for hour in range(2):
        lines.append(','.join([f' 07/01  0{hour + 1}:00:00', *(str(v[hour]) for v in columns.values())]))
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _table(tmp_path, monkeypatch, model, columns, csv_name=CSV_NAME, **kwargs):
    """Run Table on a CSV file with these columns."""
    _write_csv(tmp_path / csv_name, columns)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(accim.sim.accis, 'load_idf', lambda idf_path: model['building'])
    arguments = dict(
        datasets=[csv_name], source_frequency='hourly', frequency='hourly', frequency_agg_func='sum',
        standard_outputs=True, level=['block', 'building'], level_agg_func=['sum', 'mean'], level_excluded_zones=[],
        block_zone_hierarchy=model['hierarchy'], idf_path='model.idf',
    )
    arguments.update(kwargs)
    return Table(**arguments)


def _values(table, column):
    return table.df[column].tolist()


def _renamed(index, output):
    """The name in Table of an output of the zones of the setpoints of an index ('' if it keeps its EMS name)."""
    name = PMV_INDICES[index].name
    names = {
        PMV_INDICES[index].coefficient_output: PMV_INDICES[index].coefficient_output,
        name: '' if name == 'PMV' else name,
        f'{name} Heating Setpoint': f'Heating Setpoint ({name})',
        f'{name} Cooling Setpoint': f'Cooling Setpoint ({name})',
        f'{name} Heating Setpoint No Tolerance': f'Heating Setpoint_No Tolerance ({name})',
        f'{name} Cooling Setpoint No Tolerance': f'Cooling Setpoint_No Tolerance ({name})',
        'Comfortable Hours': 'Comfortable Hours (h)',
        'Discomfortable Hot Hours': 'Discomfortable Hot Hours (h)',
        'Discomfortable Cold Hours': 'Discomfortable Cold Hours (h)',
        'Discomfortable Total Hours': 'Discomfortable Total Hours (h)',
        'Occupied hours': '',
        'PMV_H_SP': 'Thermostat Heating Setpoint (PMV)',
        'PMV_C_SP': 'Thermostat Cooling Setpoint (PMV)',
        'Zone Mean Air Temperature': 'Zone Mean Air Temperature (°C)',
        'Metabolic Correction Factor': 'Metabolic Correction Factor',
        'Corrected Activity Level': 'Corrected Activity Level (W/person)',
    }
    return names[output]


def test_every_output_of_the_zones_has_a_name_in_table():
    # A new output of the zones in accim.sim.pmv_index needs a name in Table, or to keep its EMS name on purpose
    for index in PMV_INDICES:
        for output in zone_outputs(PMV_INDICES[index]):
            assert pmv_index_columns._table_name(PMV_INDICES[index], output, zone_outputs(PMV_INDICES[index])[output][1]) \
                == _renamed(index, output)


@MODELS
@INDICES
def test_the_outputs_of_the_zones_are_named_after_their_zones(tmp_path, monkeypatch, model, index):
    columns, of_zone = _outputs(model, index)
    table = _table(tmp_path, monkeypatch, model, columns)

    assert table.occupied_zone_list == model['zone_names']
    outputs = [*zone_outputs(PMV_INDICES[index]), *PMV_SETPOINT_SCHEDULES, 'Zone Mean Air Temperature']
    for zone in model['zone_names']:
        for output in outputs:
            name = _renamed(index, output)
            if name:
                assert _values(table, f'{zone}_{name}') == columns[of_zone[zone, output]], (zone, output)
        # The PMV of EnergyPlus (the mean of the occupant instances of the zone), and that of the EMS of the PMV
        # setpoints, which keeps its name
        assert _values(table, f'{zone}_PMV') == [0.5, 0.7]
    for column, values in _metabolic_columns(model, columns, of_zone).items():
        assert _values(table, column) == pytest.approx(values), column
    assert not table.df.columns.duplicated().any()
    kept = [c for c in table.df.columns if c.startswith('EMS:OCCUPIED HOURS_')]
    assert len(kept) == 2
    if index == 'pmv':
        assert len([c for c in table.df.columns if c.startswith('EMS:PMV_')]) == 2
    # No EMS output of the zones is left with its EMS name, but these, and those of the metabolic correction of the
    # People objects of several zones
    left = [c for c in table.df.columns if c.startswith('EMS:')]
    assert sorted(left) == sorted(kept + [c for c in table.df.columns if c.startswith('EMS:PMV_')]
                                  + [c for c in _metabolic_columns(model, columns, of_zone) if c.startswith('EMS:')])


def _metabolic_columns(model, columns, of_zone, frequency='HOURLY'):
    """The columns of Table of the outputs of the metabolic correction, and their values: those of the People objects of
    one zone are named after the zone, with the mean of the People objects of the zone; the others keep their names."""
    units = dict(METABOLIC_CORRECTION_OUTPUTS)
    expected, of_zones = {}, {}
    for people, zone in model['people_zones'].items():
        for output in METABOLIC_OUTPUTS:
            values = columns[of_zone[people, output]]
            if zone is None:
                expected[f'EMS:{output.upper()}_{sanitize_ems_name(people).upper()} [{units[output]}]({frequency})'] = \
                    values
            else:
                of_zones.setdefault(f'{zone}_{_renamed("epmv", output)}', []).append(values)
    for column, values in of_zones.items():
        expected[column] = [sum(hour) / len(hour) for hour in zip(*values)]
    return expected


@MODELS
def test_no_name_of_a_zone_contains_another_one(tmp_path, monkeypatch, model):
    # The figures of Table take the columns whose names contain the names they are given, so 'Block1:Zone1_aPMV' must
    # not take 'Block1:Zone1_Heating Setpoint (aPMV)'
    for index in PMV_INDICES:
        columns, _ = _outputs(model, index)
        table = _table(tmp_path, monkeypatch, model, columns)
        names = [c for c in table.df.columns if c.startswith(tuple(f'{zone}_' for zone in model['zone_names']))
                 or c.startswith(('Block', 'Building', model['block']))]
        for name in names:
            assert [other for other in names if name.lower() in other.lower()] == [name], (index, name)


@MODELS
def test_the_outputs_are_averaged_over_time_but_the_hours(tmp_path, monkeypatch, model):
    columns, of_zone = _outputs(model, 'epmv')
    table = _table(tmp_path, monkeypatch, model, columns, frequency='daily', frequency_agg_func='sum')

    assert len(table.df) == 1
    for zone in model['zone_names']:
        for output, (_, units, _) in zone_outputs(PMV_INDICES['epmv']).items():
            name = _renamed('epmv', output)
            column = f'{zone}_{name}' if name else next(c for c in table.df.columns
                                                         if c.startswith(f'EMS:{output.upper()}_{zone.upper()}'))
            values = columns[of_zone[zone, output]]
            expected = sum(values) if units == 'H' else sum(values) / 2
            assert _values(table, column) == [pytest.approx(expected)], (zone, output)
        for output in [*PMV_SETPOINT_SCHEDULES, 'Zone Mean Air Temperature']:
            assert _values(table, f'{zone}_{_renamed("epmv", output)}') == \
                [pytest.approx(sum(columns[of_zone[zone, output]]) / 2)]
    # The metabolic correction: the mean, and the activity level in W/person, not an energy (before,
    # 'EMS:CORRECTED ACTIVITY LEVEL_... (kWh/m2)(HOURLY)')
    for column, values in _metabolic_columns(model, columns, of_zone).items():
        assert _values(table, column) == [pytest.approx(sum(values) / 2)], column
    assert not [c for c in table.df.columns if 'ACTIVITY LEVEL' in c.upper() and 'WH' in c.upper()]


@MODELS
def test_block_and_building_values(tmp_path, monkeypatch, model):
    columns, of_zone = _outputs(model, 'apmv')
    table = _table(tmp_path, monkeypatch, model, columns)
    zones, block = model['zone_names'], model['block']

    for output in zone_outputs(PMV_INDICES['apmv']):
        name = _renamed('apmv', output)
        if not name:
            continue
        values = [columns[of_zone[zone, output]] for zone in zones]
        summed = [sum(hour) for hour in zip(*values)]
        for group in (block, 'Building'):
            assert _values(table, f'{group}_Total_{name} (summed)') == pytest.approx(summed), (group, output)
            assert _values(table, f'{group}_Total_{name} (mean)') == pytest.approx([v / 2 for v in summed])
    temperatures = [sum(hour) / 2 for hour in zip(*[columns[of_zone[zone, 'Zone Mean Air Temperature']]
                                                    for zone in zones])]
    assert _values(table, 'Building_Total_Zone Mean Air Temperature (°C) (mean)') == pytest.approx(temperatures)
    # The schedules of the thermostats (100 or -100 while the zone is empty) have no block and building values
    assert not [c for c in table.df.columns if c.startswith(('Building_Total_Thermostat', f'{block}_Total_Thermostat'))]

    # Without the excluded zones
    excluded = _table(tmp_path, monkeypatch, model, columns, level_excluded_zones=[zones[1]])
    assert _values(excluded, 'Building_Total_aPMV (mean)') == columns[of_zone[zones[0], 'aPMV']]


def test_rename_cols_false_keeps_the_ems_names(tmp_path, monkeypatch):
    columns, of_zone = _outputs(DESIGNBUILDER, 'apmv')
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, rename_cols=False)

    assert _values(table, 'EMS:APMV_BLOCK1:ZONE1 [](HOURLY)') == columns[of_zone['Block1:Zone1', 'aPMV']]
    assert not [c for c in table.df.columns if c.startswith('Block1:Zone1_')]
    # The block and building values have the names of Table, as those of the other outputs
    assert 'Building_Total_aPMV (mean)' in table.df.columns


def test_standard_outputs_keep_the_outputs_of_the_setpoints(tmp_path, monkeypatch):
    columns, _ = _outputs(DESIGNBUILDER, 'epmv')
    columns['ELECTRICITY:HVAC [J](Hourly)'] = [1.0, 2.0]
    standard = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, standard_outputs=True)
    everything = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, standard_outputs=False)

    assert set(everything.df.columns) - set(standard.df.columns) == {'ELECTRICITY:HVAC [J](HOURLY)'}


def test_comfort_hours_table(tmp_path, monkeypatch):
    columns, _ = _outputs(DESIGNBUILDER, 'epmv')
    for rename_cols in (True, False):
        table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, rename_cols=rename_cols)
        table.format_table(type_of_table='comfort hours')
        hours = [c for c in table.val_cols if not c.startswith(('Building', 'Block1_'))]
        # The four counters of each zone, and their block and building values; not the occupied hours
        assert len(hours) == 8, hours
        assert len(table.val_cols) == 8 + 4 * 2 * 2
        assert not [c for c in table.val_cols if 'OCCUPIED' in c.upper()]


def test_csv_files_of_other_idfs(tmp_path, monkeypatch):
    columns, _ = _outputs(DESIGNBUILDER, 'pmv')
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, csv_name='TestModel_PMV[Seville_Present.csv')

    row = table.df.iloc[0]
    assert (row['Model'], row['EPW'], row['Source']) == ('TestModel_PMV', 'Seville_Present', 'TestModel_PMV[Seville_Present')
    assert [row[c] for c in ('ComfStand', 'CAT', 'ComfMod', 'HVACmode', 'VentCtrl', 'VSToffset', 'MinOToffset',
                             'MaxWindSpeed', 'ASTtol', 'NameSuffix')] == \
        ['CS_X', 'CA_X', 'CM_X', 'HM_X', 'VC_X', 'VO_X', 'MT_X', 'MW_X', 'AT_X', 'NS_X']


def test_csv_files_of_output_idfs_and_of_other_idfs_together(tmp_path, monkeypatch):
    columns, _ = _outputs(DESIGNBUILDER, 'apmv')
    accim_name = 'TestModel[CS_INT EN16798[CA_2[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X[Seville.csv'
    _write_csv(tmp_path / accim_name, {c: v for c, v in columns.items() if 'ZONE OPERATIVE' in c.upper()})
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, datasets=[accim_name, CSV_NAME])

    assert sorted(set(table.df['Model'])) == ['TestModel', 'TestModel_aPMV']
    assert sorted(set(table.df['ComfStand'])) == ['CS_INT EN16798', 'CS_X']
    # As the arguments of AddAccis that do not apply ('VC_X'), CS_X does not make ComfStand a variable of the table
    assert 'Model' in table.cols_for_multiindex and 'ComfStand' not in table.cols_for_multiindex


@pytest.mark.parametrize('csv_name', ['eplusout.csv', 'TestModel[CS_INT EN16798[Seville.csv'])
def test_other_names_of_csv_files_stop_table(tmp_path, monkeypatch, csv_name):
    columns, _ = _outputs(DESIGNBUILDER, 'apmv')
    with pytest.raises(ValueError, match=r"is not that of a simulation of run_ep"):
        _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, csv_name=csv_name)


def test_time_plot_of_the_index_and_its_setpoints(tmp_path, monkeypatch):
    columns, _ = _outputs(DESIGNBUILDER, 'epmv')
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns)
    monkeypatch.setattr(builtins, 'input', lambda prompt='': 'n')
    data = ['Block1:Zone1_ePMV', 'Block1:Zone1_Heating Setpoint (ePMV)', 'Block1:Zone1_Cooling Setpoint (ePMV)']

    table.time_plot(vars_to_gather_rows=['Model'], vars_to_gather_cols=['EPW'],
                    data_on_y_main_axis=[['ePMV', data]], colorlist_y_main_axis=[['ePMV', ['k', 'b', 'r']]],
                    figname='time_plot_epmv', figsize=2, dpi=50, confirm_graph=True)

    # One column for each name
    frames = table.y_list_main[0][0][0]['dataframe']
    assert [len(frame.columns) for frame in frames] == [1, 1, 1]
    assert [frame.columns[0].split('[')[0] for frame in frames] == data
    assert (tmp_path / 'time_plot_epmv.png').exists()
    # The setpoints are drawn over the index, as the setpoint temperatures over the temperatures
    assert [_zorder(name) for name in data] == [0, 1, 1]
    assert _zorder('Building_Total_Zone Operative Temperature (°C) (mean)') == 0
    assert _zorder('Block1:Zone1_Adaptive Cooling Setpoint Temperature (°C)') == 1

def test_wrangled_table_of_the_outputs_of_the_setpoints(tmp_path, monkeypatch):
    # Two models (the second with twice the values of the first) in two cities, in a table of the run period: the
    # ePMV and the hours within the setpoints of each model, compared with those of the first one
    columns, of_zone = _outputs(DESIGNBUILDER, 'epmv')
    datasets = []
    for scale, model in ((1.0, 'TestModel_e07'), (2.0, 'TestModel_e09')):
        for city in ('Seville', 'Madrid'):
            datasets.append(f'{model}[{city}.csv')
            _write_csv(tmp_path / datasets[-1], {c: [v * scale for v in values] for c, values in columns.items()})
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, datasets=datasets, frequency='runperiod')
    values = ['Block1:Zone1_ePMV', 'Block1:Zone1_Comfortable Hours (h)']

    table.format_table(type_of_table='custom', custom_cols=values)
    assert table.val_cols == values
    table.wrangled_table(reshaping='unstack', vars_to_gather=['Model'], baseline='TestModel_e07',
                         comparison_mode=['others compared to baseline'], comparison_cols=['absolute'])

    unstacked = table.wrangled_df_unstacked
    assert sorted(unstacked.index) == ['Madrid', 'Seville']
    epmv = sum(columns[of_zone['Block1:Zone1', 'ePMV']]) / 2
    hours = sum(columns[of_zone['Block1:Zone1', 'Comfortable Hours']])
    assert list(unstacked.columns) == [(value, label) for value in values
                                       for label in ['TestModel_e07', 'TestModel_e09', 'TestModel_e07 - TestModel_e09']]
    assert unstacked[(values[0], 'TestModel_e07')].tolist() == [pytest.approx(epmv)] * 2
    assert unstacked[(values[0], 'TestModel_e09')].tolist() == [pytest.approx(2 * epmv)] * 2
    assert unstacked[(values[1], 'TestModel_e07 - TestModel_e09')].tolist() == [pytest.approx(-hours)] * 2


def test_energy_per_m2_of_the_simulations_without_floor_areas(tmp_path, monkeypatch, capsys):
    # The setpoints based on the PMV do not report the floor areas of the zones (the EMS outputs Zone Floor Area of
    # AddAccis), so the block and building totals of energy per m2 were infinite (divided by a total floor area of 0)
    columns, _ = _outputs(DESIGNBUILDER, 'apmv')
    for number, zone in enumerate(('BLOCK1:ZONE1', 'BLOCK1:ZONE2')):
        columns[f'{zone} VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate [W](Hourly)'] = \
            [100.0 * (number + 1), 0.0]
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, normalised_energy_units=True,
                   energy_units_in_kwh=False)

    totals = [c for c in table.df.columns if c.startswith(('Building_Total_', 'Block1_Total_')) and 'Wh/m2' in c]
    assert totals and all(table.df[c].isna().all() for c in totals), totals
    assert 'normalised_energy_units=False' in capsys.readouterr().out

    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, normalised_energy_units=False,
                   energy_units_in_kwh=False)
    assert _values(table, 'Building_Total_Cooling Energy Demand (Wh) (summed)') == [300.0, 0.0]
