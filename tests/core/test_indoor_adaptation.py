"""Tests for the indicators of the adaptation to the indoor climate (task F3 of block F of accim 1.2.0,
``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, section 4; :mod:`accim.data.postprocessing.indoor_adaptation`), the
outputs of the thermal comfort models of EnergyPlus in ``Table`` and
:func:`accim.sim.people.add_thermal_comfort_outputs`.

The expected values are computed here from the formulas of the sources (Sun, Brager & Schiavon, 2026, Fig. 7a:
TSV = 0.11·SET − 2.6; Parkinson, de Dear & Brager, 2020, Fig. 6), not with the functions tested. The running mean
indoor temperature is also compared with that of the Erl of the limiter of the drift of the setpoints (task F2), and
the last test simulates the sample model with EnergyPlus 25.1.
"""
import shutil
import subprocess
import warnings
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import accim.sim.accis
from accim.data.postprocessing import indoor_adaptation as ia
from accim.data.postprocessing.main import Table
from accim.sim.targets import resolve_targets

from .test_table_pmv_index import DESIGNBUILDER, RESIDENTIAL, TWO_PEOPLE, _table, _values

MODELS = pytest.mark.parametrize('model', [DESIGNBUILDER, RESIDENTIAL, TWO_PEOPLE],
                                 ids=['designbuilder', 'residential', 'two_people'])
CSV_NAME = 'Model[CS_INT EN16798[CA_2[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X[Seville.csv'
#: The band of TSV ±0.5 of Sun, Brager & Schiavon (2026), Fig. 7a, in SET: (TSV + 2.6)/0.11
BAND = ((-0.5 + 2.6) / 0.11, (0.5 + 2.6) / 0.11)
#: Parkinson, de Dear & Brager (2020), Fig. 6
FIG6 = {'AC': (1.06, 0.951), 'MM': (2.91, 0.879), 'NV': (2.23, 0.897)}


def test_the_neutral_temperature_by_exposure():
    assert ia.EXPOSURE_NEUTRAL_TEMPERATURE == FIG6
    for building_type, (intercept, slope) in FIG6.items():
        assert ia.exposure_neutral_temperature(24.0, building_type.lower()) == pytest.approx(intercept + slope * 24)
    np.testing.assert_allclose(ia.exposure_neutral_temperature(pd.Series([20.0, 26.0])), [1.06 + 0.951 * 20,
                                                                                          1.06 + 0.951 * 26])
    with pytest.raises(ValueError, match=r"building_type must be one of \['AC', 'MM', 'NV'\]"):
        ia.exposure_neutral_temperature(24.0, 'HVAC')


def test_the_running_mean_indoor_temperature():
    # Three days of 4 rows; the second has no occupied rows, and the date of the first comes back in the fourth
    top = [20.0, 22.0, 24.0, 30.0, 25.0, 25.0, 25.0, 25.0, 26.0, 26.0, 28.0, 28.0, 18.0, 18.0, 18.0, 18.0]
    day = ['a'] * 4 + ['b'] * 4 + ['c'] * 4 + ['a'] * 4
    hours = [1.0, 1.0, 0.5, 0.0] + [0.0] * 4 + [1.0, 1.0, 0.0, 1.0] + [1.0] * 4
    first = (20 * 1 + 22 * 1 + 24 * 0.5) / 2.5
    third = (26 + 26 + 28) / 3
    expected = [np.nan] * 4 + [first] * 4 + [first] * 4 + [0.2 * third + 0.8 * first] * 4
    np.testing.assert_allclose(ia.indoor_running_mean(top, day, occupied=hours, timestep_h=hours), expected)
    # initial_T_rm_in gives the value of the first day, and alpha_indoor the weight of the previous day
    expected = [24.0] * 4 + [0.5 * first + 0.5 * 24.0] * 8 + [0.5 * third + 0.5 * (0.5 * first + 12.0)] * 4
    np.testing.assert_allclose(ia.indoor_running_mean(top, day, occupied=hours, timestep_h=hours, alpha_indoor=0.5,
                                                      initial_T_rm_in=24.0), expected)
    # Without occupancy, all the rows count with timestep_h
    np.testing.assert_allclose(ia.indoor_running_mean([20.0, 22.0, 30.0], [1, 1, 2])[2], 21.0)
    with pytest.raises(ValueError, match=r'alpha_indoor must be in \[0, 1\)'):
        ia.indoor_running_mean(top, day, alpha_indoor=1)
    with pytest.raises(ValueError, match='day has 3 values, not 16'):
        ia.indoor_running_mean(top, day[:3])


def test_the_running_mean_is_that_of_the_limiter_of_the_drift():
    # The Erl of the limiter of task F2 (window), with the values of the sensors of each hour of four days
    from .test_drift_limiter import _day, _drift_erl

    erl = _drift_erl(drift_mode='window')
    rng = np.random.default_rng(3)
    temperatures, days, occupied, reported = [], [], [], []
    for day, hours in zip(range(10, 14), (range(8, 18), (), range(9, 13), range(0, 24))):
        operative = list(np.round(rng.uniform(19.0, 29.0, 24), 2))
        rows = _day(erl, day, (20.0, 27.0), operative=operative, occupied_hours=hours)
        temperatures += operative
        days += [day] * 24
        occupied += [1.0 if hour in hours else 0.0 for hour in range(24)]
        reported += [row['T_rm_in_Zone1'] for row in rows]
    calculated = ia.indoor_running_mean(temperatures, days, occupied=occupied)
    # The first day has no running mean yet (the limiter is inactive)
    assert np.isnan(calculated[:24]).all()
    np.testing.assert_allclose(calculated[24:], reported[24:], rtol=0, atol=1e-9)


def test_the_hours_in_the_causal_band():
    set_values = pd.Series([18.0, BAND[0], 23.6, BAND[1], 28.5, 30.0])
    hours = pd.Series([1.0, 1.0, 0.5, 1.0, 1.0, 0.0])
    result = ia.causal_band_hours(set_values, occupied=hours, timestep_h=hours)
    # Both limits within the band, as the hook of comfort standard 24 counts them
    assert (result['in_h'], result['above_h'], result['below_h'], result['occupied_h']) == (2.5, 1.0, 1.0, 4.5)
    assert result['in_pct'] == pytest.approx(100 * 2.5 / 4.5)
    mean = (18 + BAND[0] + 0.5 * 23.6 + BAND[1] + 28.5) / 4.5
    assert result['mean_set'] == pytest.approx(mean) and result['mean_tsv'] == pytest.approx(0.11 * mean - 2.6)
    # An extrapolated band, with its warning: (±1.0 + 2.6)/0.11, 14.5 to 32.7 °C
    with pytest.warns(UserWarning, match='linear extrapolation'):
        wide = ia.causal_band_hours(set_values, occupied=hours, timestep_h=hours, tsv_limit=1.0)
    assert (1.6 / 0.11, 3.6 / 0.11) == pytest.approx((14.545, 32.727), abs=1e-3)
    assert (wide['in_h'], wide['above_h'], wide['below_h']) == (4.5, 0.0, 0.0)
    with pytest.warns(UserWarning, match='linear extrapolation'):
        edges = ia.causal_band_hours(pd.Series([14.0, 15.0, 32.0, 33.0]), tsv_limit=1.0)
    assert (edges['in_h'], edges['above_h'], edges['below_h']) == (2.0, 1.0, 1.0)
    with pytest.raises(ValueError, match='tsv_limit must be 0.5'):
        ia.causal_band_hours(set_values, tsv_limit=0.6)
    assert np.isnan(ia.causal_band_hours(set_values, occupied=[0] * 6)['mean_set'])


def test_the_overcooling_hours():
    top = pd.Series([21.0, 23.0, 21.5, 20.0, 19.0])
    season = [True, True, True, True, False]
    hours = pd.Series([1.0, 1.0, 0.5, 0.0, 1.0])
    result = ia.overcooling_hours(top, season, occupied=hours, timestep_h=hours)
    assert result == {'overcooling_h': 1.5, 'cooling_season_h': 2.5, 'overcooling_pct': pytest.approx(60.0)}
    # Below a reference heating setpoint, a number or one for each row
    assert ia.overcooling_hours(top, season, occupied=hours, timestep_h=hours, threshold=21.2)['overcooling_h'] == 1.0
    assert ia.overcooling_hours(top, season, occupied=hours, timestep_h=hours,
                                threshold=[22.0, 22.0, 21.0, 22.0, 22.0])['overcooling_h'] == 1.0
    assert np.isnan(ia.overcooling_hours(top, [0] * 5, occupied=hours, timestep_h=hours)['overcooling_pct'])


def test_the_hours_away_from_the_neutral_temperature_by_exposure():
    top = pd.Series([20.0, 23.0, 27.0, 28.0])
    t_rm_in = pd.Series([np.nan, 22.0, 22.0, 24.0])
    hours = pd.Series([1.0, 1.0, 1.0, 0.5])
    result = ia.exposure_hours(top, t_rm_in, occupied=hours, timestep_h=hours)
    neutral = 1.06 + 0.951 * np.array([22.0, 22.0, 24.0])
    gap = np.array([23.0, 27.0, 28.0]) - neutral
    weights = np.array([1.0, 1.0, 0.5])
    assert result['outside_h'] == float(weights[np.abs(gap) > 2.5].sum())
    assert result['occupied_h'] == 2.5
    assert result['mean_t_rm_in'] == pytest.approx((22 + 22 + 12) / 2.5)
    assert result['mean_tn'] == pytest.approx((neutral * weights).sum() / 2.5)
    assert result['mean_difference'] == pytest.approx((gap * weights).sum() / 2.5)
    nv = ia.exposure_hours(top, t_rm_in, occupied=hours, timestep_h=hours, building_type='NV', difference=1.0)
    assert nv['mean_tn'] == pytest.approx(((2.23 + 0.897 * np.array([22.0, 22.0, 24.0])) * weights).sum() / 2.5)
    empty = ia.exposure_hours(top, [np.nan] * 4, occupied=hours, timestep_h=hours)
    assert empty['occupied_h'] == 0 and np.isnan(empty['outside_h']) and np.isnan(empty['mean_tn'])
    with pytest.raises(ValueError, match='difference must be greater than 0'):
        ia.exposure_hours(top, t_rm_in, difference=0)


# Table ------------------------------------------------------------------------------------------------------------

#: The outputs of the thermal comfort models, with the units of the columns of EnergyPlus, their names in Table and
#: their values in the two hours of the CSV files of test_table_pmv_index (each occupant instance adds 1 to them)
COMFORT_OUTPUTS = {
    'Zone Thermal Comfort Pierce Model Standard Effective Temperature': ('C', 'SET_Pierce (°C)', [24.0, 26.0]),
    'Zone Thermal Comfort Pierce Model Standard Effective Temperature PMV': ('', 'SET_Pierce_PMV', [0.5, 0.9]),
    'Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect': ('C', 'CoolingEffect (°C)', [0.2, 0.4]),
    'Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect Adjusted PMV': ('', 'CoolingEffect_PMV',
                                                                                      [0.4, 0.8]),
    'Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect Adjusted PPD': ('', 'CoolingEffect_PPD',
                                                                                      [8.0, 18.0]),
    'Zone Thermal Comfort Fanger Model PMV': ('', 'PMV', [0.45, 0.85]),
}


def _comfort_columns(model):
    """The columns of the outputs of the thermal comfort models of each occupant instance, and the operative
    temperature and occupied hours of each zone; {column: [first hour, second hour]}, and the values of each zone
    (the means of its instances)."""
    columns, means = {}, {}
    for number, (zone, target) in enumerate(zip(model['zone_names'], resolve_targets(model['building']))):
        columns[f'{target.zone_name.upper()}:Zone Operative Temperature [C](Hourly)'] = [25.0, 26.0]
        columns[f'EMS:Occupied Hours_{target.ems_suffix} [H](Hourly)'] = [1.0, 1.0]
        for output, (units, _, values) in COMFORT_OUTPUTS.items():
            instances = []
            for instance, key in enumerate(target.instance_keys):
                instances.append([value + number + instance for value in values])
                columns[f'{key.upper()}:{output} [{units}](Hourly)'] = instances[-1]
            means[zone, output] = [float(np.mean(hour)) for hour in zip(*instances)]
    return columns, means


@MODELS
def test_the_outputs_of_the_comfort_models_in_table(tmp_path, monkeypatch, model):
    columns, means = _comfort_columns(model)
    table = _table(tmp_path, monkeypatch, model, columns)
    zones = model['zone_names']
    for zone in zones:
        for output, (_, name, _) in COMFORT_OUTPUTS.items():
            # Named after the zone, the mean of its occupant instances
            assert _values(table, f'{zone}_{name}') == pytest.approx(means[zone, output]), (zone, name)
    # The block and building values of each output are those of its zones only (not those of the longer outputs
    # whose names contain its own, such as the PMV of the SET)
    for output, (_, name, _) in COMFORT_OUTPUTS.items():
        summed = [sum(hour) for hour in zip(*[means[zone, output] for zone in zones])]
        for group in (model['block'], 'Building'):
            assert _values(table, f'{group}_Total_{name} (summed)') == pytest.approx(summed), (group, name)
            assert _values(table, f'{group}_Total_{name} (mean)') == pytest.approx([v / len(zones) for v in summed])
    # No name contains another one (the figures take the columns whose names contain the names they are given)
    names = [c for c in table.df.columns if c.startswith(tuple(f'{zone}_' for zone in zones))
             or c.startswith((model['block'], 'Building'))]
    for name in names:
        assert [other for other in table.df.columns if name.lower() in str(other).lower()] == [name], name
    # Averaged over time
    daily = _table(tmp_path, monkeypatch, model, columns, frequency='daily')
    for zone in zones:
        for output, (_, name, _) in COMFORT_OUTPUTS.items():
            assert _values(daily, f'{zone}_{name}') == [pytest.approx(np.mean(means[zone, output]))]
    # Kept with standard_outputs=True; with rename_cols=False, they keep the names of EnergyPlus
    kept = _table(tmp_path, monkeypatch, model, columns, rename_cols=False)
    for output in COMFORT_OUTPUTS:
        assert any(c.split(' [')[0].endswith(f':{output.upper()}') for c in kept.df.columns), output


#: Two days of the fake CSV of the indicators: 30 April (day 120, before the cooling season) and 1 May (day 121)
DATES = ['04/30'] * 24 + ['05/01'] * 24
HOUR = np.tile(np.arange(24), 2)
DAY2 = np.repeat([False, True], 24)
OCCUPIED = np.where((HOUR >= 8) & (HOUR <= 17), np.where(HOUR == 17, 0.5, 1.0), 0.0)
ZONE_DATA = {
    'Block1:Zone1': dict(top=np.where(DAY2, 17.9 + 0.4 * HOUR, 20.0 + 0.3 * HOUR), set_offset=(0.5, 1.5),
                         cooling_effect=np.full(48, 0.2), drift=np.where(DAY2 & (OCCUPIED > 0), 0.5, 0.0)),
    'Block1:Zone2': dict(top=np.where(DAY2, 30.0 - 0.1 * HOUR, 23.0 + 0.1 * (HOUR % 3)), set_offset=(-0.5,),
                         cooling_effect=0.3 + 0.01 * np.arange(48), drift=None),
}


def _indicator_columns(model):
    """The columns of the CSV file of the indicators (two days of hours) of the zones of a model of
    test_table_pmv_index with the zones Block1:Zone1 and Block1:Zone2, and the values of each zone."""
    columns = {'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)': list(20.0 + 0.1 * np.arange(48))}
    zones = {}
    for zone, target in zip(model['zone_names'], resolve_targets(model['building'])):
        data = dict(ZONE_DATA[zone])
        columns[f'{target.zone_name.upper()}:Zone Operative Temperature [C](Hourly)'] = list(data['top'])
        columns[f'EMS:Occupied Hours_{target.ems_suffix} [H](Hourly)'] = list(OCCUPIED)
        if data['drift'] is not None:
            columns[f'EMS:DriftLimitedHours_{target.ems_suffix} [H](Hourly)'] = list(data['drift'])
        offsets = data['set_offset'][:len(target.instance_keys)]
        for key, offset in zip(target.instance_keys, offsets):
            columns[f'{key.upper()}:{ia._SET_OUTPUT} [C](Hourly)'] = list(data['top'] + offset)
            columns[f'{key.upper()}:{ia._COOLING_EFFECT_OUTPUT} [C](Hourly)'] = list(data['cooling_effect'])
        data['set'] = data['top'] + float(np.mean(offsets))
        zones[zone] = data
    return columns, zones


def _indicator_table(tmp_path, monkeypatch, model, columns, **kwargs):
    lines = [','.join(['Date/Time', *columns])]
    for row, (date, hour) in enumerate(zip(DATES, HOUR)):
        lines.append(','.join([f' {date}  {hour + 1:02d}:00:00', *(str(v[row]) for v in columns.values())]))
    (tmp_path / CSV_NAME).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(accim.sim.accis, 'load_idf', lambda idf_path: model['building'])
    arguments = dict(datasets=[CSV_NAME], source_frequency='hourly', frequency='hourly', frequency_agg_func='sum',
                     standard_outputs=True, level=['block', 'building'], level_agg_func=['sum', 'mean'],
                     level_excluded_zones=[], block_zone_hierarchy=model['hierarchy'], normalised_energy_units=False,
                     idf_path='model.idf', indoor_adaptation_indicators=True)
    arguments.update(kwargs)
    return Table(**arguments)


def _expected(data):
    """The indicators of a zone, from the formulas of the sources."""
    w, top, set_values = OCCUPIED, data['top'], data['set']
    occupied = w.sum()
    within = (set_values >= BAND[0]) & (set_values <= BAND[1])
    mean_set = (set_values * w).sum() / occupied
    season = DAY2 & (w > 0)
    t_rm_in = (top * w)[~DAY2].sum() / w[~DAY2].sum()
    neutral = 1.06 + 0.951 * t_rm_in
    gap = top[DAY2] - neutral
    w2 = w[DAY2]
    return {
        'Occupied Hours (h)': occupied, 'Mean SET_Pierce (°C)': mean_set, 'Mean TSV_causal': 0.11 * mean_set - 2.6,
        'Hours In Causal Band (h)': w[within].sum(), 'Hours Above Causal Band (h)': w[set_values > BAND[1]].sum(),
        'Hours Below Causal Band (h)': w[set_values < BAND[0]].sum(),
        'Hours In Causal Band (%)': 100 * w[within].sum() / occupied,
        'Overcooling Hours (h)': w[season & (top < 22.0)].sum(),
        'Overcooling Hours (%)': 100 * w[season & (top < 22.0)].sum() / w[DAY2].sum(),
        'Mean T_rm_in (°C)': t_rm_in, 'Mean Tn_exp (°C)': neutral, 'Mean To - Tn_exp (K)': (gap * w2).sum() / w2.sum(),
        'Hours Outside Tn_exp Band (h)': w2[np.abs(gap) > 2.5].sum(),
        'Mean CoolingEffect (°C)': (data['cooling_effect'] * w).sum() / occupied,
        'Drift Limited Hours (h)': np.nan if data['drift'] is None else data['drift'].sum(),
    }


@pytest.mark.parametrize('model', [DESIGNBUILDER, TWO_PEOPLE], ids=['designbuilder', 'two_people'])
@pytest.mark.parametrize('rename_cols', [True, False])
def test_the_table_gives_the_indicators_of_each_zone_and_the_building(tmp_path, monkeypatch, model, rename_cols):
    columns, zones = _indicator_columns(model)
    table = _indicator_table(tmp_path, monkeypatch, model, columns, rename_cols=rename_cols)
    indicators = table.indoor_adaptation_indicators
    assert len(indicators) == 1
    row = indicators.iloc[0]
    assert (row['Source'], row['Model'], row['ComfStand'], row['EPW']) == (CSV_NAME[:-4], 'Model', 'CS_INT EN16798',
                                                                           'Seville')
    assert list(ia.TABLE_INDICATORS) == list(_expected(zones['Block1:Zone1']))
    expected = {zone: _expected(data) for zone, data in zones.items()}
    # Zone 1 is overcooled on 1 May until it reaches 22 °C; zone 2 is above the band in some hours
    assert expected['Block1:Zone1']['Overcooling Hours (h)'] > 0 and expected['Block1:Zone2'][
        'Hours Above Causal Band (h)'] > 0
    for zone, values in expected.items():
        for title, value in values.items():
            if np.isnan(value):
                assert np.isnan(row[f'{zone}_{title}']), (zone, title)
            else:
                assert row[f'{zone}_{title}'] == pytest.approx(value), (zone, title)
    # The building: the sums of the hours, and the means weighted by the hours of the zones
    first, second = expected.values()
    for title in ('Occupied Hours (h)', 'Hours In Causal Band (h)', 'Hours Above Causal Band (h)',
                  'Hours Below Causal Band (h)', 'Overcooling Hours (h)', 'Hours Outside Tn_exp Band (h)'):
        assert row[f'Building_{title}'] == pytest.approx(first[title] + second[title]), title
    for title in ('Mean SET_Pierce (°C)', 'Mean TSV_causal', 'Mean CoolingEffect (°C)'):
        assert row[f'Building_{title}'] == pytest.approx((first[title] + second[title]) / 2), title
    assert row['Building_Hours In Causal Band (%)'] == pytest.approx(
        100 * (first['Hours In Causal Band (h)'] + second['Hours In Causal Band (h)']) / (2 * OCCUPIED.sum()))
    # Only zone 1 has the limiter of the drift
    assert row['Building_Drift Limited Hours (h)'] == first['Drift Limited Hours (h)']


def test_the_table_checks_the_indicators(tmp_path, monkeypatch):
    model = DESIGNBUILDER
    columns, _ = _indicator_columns(model)
    with pytest.raises(ValueError, match="indoor_adaptation_indicators needs the rows of each timestep or hour"):
        _indicator_table(tmp_path, monkeypatch, model, columns, frequency='daily')
    # Without the occupied hours of a zone
    without = {c: v for c, v in columns.items() if not c.startswith('EMS:Occupied Hours_Block1_Zone2')}
    with pytest.raises(ValueError, match=r'need the operative temperature and the occupied hours .* Block1:Zone2 '
                                         r'\(hours\)'):
        _indicator_table(tmp_path, monkeypatch, model, without)
    # Without the SET of EnergyPlus, its indicators are NaN, with a warning
    without = {c: v for c, v in columns.items() if ia._SET_OUTPUT.upper() not in c.upper()}
    with pytest.warns(UserWarning, match=r"The zones \['Block1:Zone1', 'Block1:Zone2'\] have no SET of the Pierce"):
        table = _indicator_table(tmp_path, monkeypatch, model, without)
    row = table.indoor_adaptation_indicators.iloc[0]
    assert np.isnan(row['Block1:Zone1_Hours In Causal Band (h)']) and np.isnan(row['Building_Mean SET_Pierce (°C)'])
    assert row['Building_Overcooling Hours (h)'] > 0
    # The other tables do not have the attribute, so their files do not change
    table = _indicator_table(tmp_path, monkeypatch, model, columns, indoor_adaptation_indicators=False)
    assert not hasattr(table, 'indoor_adaptation_indicators')
    assert 'indoor_adaptation_indicators' not in table._json_content()


def test_the_arguments_of_the_indicators(tmp_path, monkeypatch):
    model = DESIGNBUILDER
    columns, zones = _indicator_columns(model)
    table = _indicator_table(tmp_path, monkeypatch, model, columns, indoor_adaptation_indicators=False)
    df, occupied = table.df, table.occupied_zone_list
    # Another overcooling temperature (a reference heating setpoint) and cooling season, the NV coefficients and
    # another band around Tn_exp
    row = ia.table_indicators(df, occupied, overcooling_temperature=23.0, cooling_season_start='30/04',
                              cooling_season_end=122, building_type='nv', exposure_difference=1.0).iloc[0]
    data = zones['Block1:Zone1']
    assert row['Block1:Zone1_Overcooling Hours (h)'] == pytest.approx(OCCUPIED[data['top'] < 23.0].sum())
    t_rm_in = (data['top'] * OCCUPIED)[~DAY2].sum() / OCCUPIED[~DAY2].sum()
    assert row['Block1:Zone1_Mean Tn_exp (°C)'] == pytest.approx(2.23 + 0.897 * t_rm_in)
    gap = data['top'][DAY2] - (2.23 + 0.897 * t_rm_in)
    assert row['Block1:Zone1_Hours Outside Tn_exp Band (h)'] == pytest.approx(OCCUPIED[DAY2][np.abs(gap) > 1].sum())
    for arguments, message in ((dict(overcooling_temperature='22'), 'overcooling_temperature must be a number'),
                               (dict(cooling_season_start='31/02'), 'cooling_season_start must be a date'),
                               (dict(building_type='AC1'), 'building_type must be one of'),
                               (dict(alpha_indoor=1.0), r'alpha_indoor must be in \[0, 1\)'),
                               (dict(exposure_difference=-1), 'exposure_difference must be greater than 0'),
                               (dict(tsv_limit=2), 'tsv_limit must be 0.5')):
        with pytest.raises(ValueError, match=message):
            ia.table_indicators(df, occupied, **arguments)
    with pytest.raises(ValueError, match='need the month and the day of each row'):
        ia.table_indicators(df.drop(columns=['Month']), occupied)


# add_thermal_comfort_outputs ----------------------------------------------------------------------------------------

def _thermal_comfort_fields(people):
    return [str(getattr(people, f'Thermal_Comfort_Model_{n}_Type')).strip() for n in range(1, 8)]


def test_add_thermal_comfort_outputs(tmp_path, monkeypatch):
    from accim.sim.people import THERMAL_COMFORT_OUTPUTS, add_thermal_comfort_outputs

    from .test_pierce_set import _accis_model, needs_idd

    if needs_idd.args[0]:
        pytest.skip(needs_idd.kwargs['reason'])
    idf = _accis_model(tmp_path / 'model', monkeypatch)
    before = len(idf.idfobjects['Output:Variable'])
    people = idf.idfobjects['People'][0]
    fields = [_thermal_comfort_fields(p) for p in idf.idfobjects['People']]

    # The errors, before changing anything
    with pytest.raises(ValueError, match=r"models must be some of \['Fanger', 'Pierce', 'CoolingEffectASH55'\], not "
                                         r"'KSU'"):
        add_thermal_comfort_outputs(idf, ['Pierce', 'KSU'])
    with pytest.raises(ValueError, match='not an empty list'):
        add_thermal_comfort_outputs(idf, [])
    schedule, people.Air_Velocity_Schedule_Name = people.Air_Velocity_Schedule_Name, ''
    with pytest.raises(ValueError, match=r'"People Block1:Zone\d" \(Air Velocity Schedule Name\)'):
        add_thermal_comfort_outputs(idf, 'Pierce')
    people.Air_Velocity_Schedule_Name = schedule
    # One empty field in a People object for two models: neither model is added to any object
    for n, model in zip(range(4, 8), ('KSU', 'AnkleDraftASH55', 'KSU', 'AnkleDraftASH55')):
        setattr(people, f'Thermal_Comfort_Model_{n}_Type', model)
    with pytest.raises(ValueError, match="has no empty field for the thermal comfort model 'CoolingEffectASH55'"):
        add_thermal_comfort_outputs(idf, ['Pierce', 'CoolingEffectASH55'])
    for n in range(4, 8):
        setattr(people, f'Thermal_Comfort_Model_{n}_Type', '')
    assert [_thermal_comfort_fields(p) for p in idf.idfobjects['People']] == fields
    assert len(idf.idfobjects['Output:Variable']) == before

    add_thermal_comfort_outputs(idf, ['pierce', 'CoolingEffectASH55', 'Pierce'])
    for item in idf.idfobjects['People']:
        assert _thermal_comfort_fields(item)[:5] == ['AdaptiveASH55', 'AdaptiveCEN15251', 'Pierce',
                                                     'CoolingEffectASH55', '']
    keys = [key for target in resolve_targets(idf) for key in target.instance_keys]
    requested = [(o.Key_Value, o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']]
    outputs = THERMAL_COMFORT_OUTPUTS['Pierce'] + THERMAL_COMFORT_OUTPUTS['CoolingEffectASH55']
    # At the frequency of the EMS outputs of the model (timestep), for each occupant instance
    assert sorted(requested[before:]) == sorted((key, output, 'Timestep') for key in keys for output in outputs)
    # Once
    add_thermal_comfort_outputs(idf, 'Pierce')
    assert len(idf.idfobjects['Output:Variable']) == before + len(keys) * len(outputs)
    add_thermal_comfort_outputs(idf, 'Fanger', output_frequencies=['hourly'])
    assert [(o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']][-1] == (
        'Zone Thermal Comfort Fanger Model PPD', 'Hourly')
    assert _thermal_comfort_fields(people)[:6] == ['AdaptiveASH55', 'AdaptiveCEN15251', 'Pierce',
                                                   'CoolingEffectASH55', 'Fanger', '']
    # The clothing insulation schedule is not needed with the dynamic clothing model of ASHRAE 55
    people.Clothing_Insulation_Calculation_Method = 'DynamicClothingModelASHRAE55'
    people.Clothing_Insulation_Schedule_Name = ''
    add_thermal_comfort_outputs(idf, 'Pierce')
    people.Clothing_Insulation_Calculation_Method = 'CalculationMethodSchedule'
    with pytest.raises(ValueError, match='Clothing Insulation Schedule Name, Clothing Insulation Calculation Method '
                                         'Schedule Name'):
        add_thermal_comfort_outputs(idf, 'Pierce')


def test_the_cooling_effect_needs_a_choice_of_the_idd():
    from accim.sim.people import add_thermal_comfort_model

    class People(SimpleNamespace):
        key = 'PEOPLE'
        fieldnames = [f'Thermal_Comfort_Model_{n}_Type' for n in range(1, 8)]

        def getfieldidd(self, field):
            # The choices of the IDD of EnergyPlus 9.4
            return {'key': ['Fanger', 'Pierce', 'KSU', 'AdaptiveASH55', 'AdaptiveCEN15251']}

    people = People(Name='People 1', **{field: '' for field in People.fieldnames})
    building = SimpleNamespace(idfobjects={'PEOPLE': [people]})
    with pytest.raises(ValueError, match="'CoolingEffectASH55' is not a choice of the field Thermal Comfort Model 1 "
                                         "Type of the PEOPLE objects in the IDD of the model"):
        add_thermal_comfort_model(building, 'CoolingEffectASH55')
    assert people.Thermal_Comfort_Model_1_Type == ''
    add_thermal_comfort_model(building, 'Pierce')
    assert people.Thermal_Comfort_Model_1_Type == 'Pierce'


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus():
    from accim.energyplus import find_energyplus

    from .test_pierce_set import EPW, SAMPLE_IDF

    folder = find_energyplus('25.1', required=False)
    return folder if folder is not None and SAMPLE_IDF.exists() and EPW.exists() else None


@pytest.mark.skipif(_energyplus() is None, reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_the_indicators_of_a_simulation(tmp_path, monkeypatch):
    from accim.sim.accis import AddAccis, load_idf
    from accim.sim.people import add_thermal_comfort_outputs

    from .test_pierce_set import EPW, SAMPLE_IDF

    folder = tmp_path / 'model'
    folder.mkdir()
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    model = load_idf(folder / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month, run_period.End_Month, run_period.End_Day_of_Month = (
        4, 29, 5, 2)
    model.save()
    monkeypatch.chdir(folder)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', comfort_standard=[1], category=[2], comfort_mode=[3], confirm=True,
                 verbose=False)
    [path] = folder.glob('TestModel[[]*.idf')
    idf = load_idf(path)
    add_thermal_comfort_outputs(idf, ['Fanger', 'Pierce', 'CoolingEffectASH55'])
    idf.saveas(str(tmp_path / 'model.idf'))
    result = subprocess.run([str(_energyplus() / 'energyplus.exe'), '-d', str(tmp_path / 'out'), '-p', 'run', '-s',
                             'C', '-r', '-x', '-w', str(EPW), str(tmp_path / 'model.idf')],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    results = pd.read_csv(tmp_path / 'out' / 'run.csv')
    assert len(results) == 4 * 24
    # Each output of each People object (Input Output Reference 25.2, 1.14.2.2)
    from accim.sim.people import THERMAL_COMFORT_OUTPUTS

    targets = resolve_targets(idf)
    for target in targets:
        for outputs in THERMAL_COMFORT_OUTPUTS.values():
            for output in outputs:
                assert [c for c in results.columns if c.upper().startswith(f'{target.sensor_key}:{output} ['.upper())]
    # The table of the simulation, and its indicators
    tables = tmp_path / 'tables'
    tables.mkdir()
    shutil.copy(tmp_path / 'out' / 'run.csv', tables / CSV_NAME)
    shutil.copy(tmp_path / 'model.idf', tables / 'model.idf')
    monkeypatch.chdir(tables)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        table = Table(datasets=[CSV_NAME], source_frequency='hourly', frequency='hourly', frequency_agg_func='sum',
                      standard_outputs=True, level=['building'], level_agg_func=['sum', 'mean'],
                      level_excluded_zones=[], idf_path='model.idf', indoor_adaptation_indicators=True)
    row = table.indoor_adaptation_indicators.iloc[0]
    for target, zone in zip(targets, table.occupied_zone_list):
        def column(name):
            [found] = [c for c in results.columns if c.upper().startswith(name.upper())]
            return results[found].to_numpy(dtype=float)

        hours = column(f'EMS:Occupied Hours_{target.ems_suffix} [')
        set_values = column(f'{target.sensor_key}:{ia._SET_OUTPUT} [')
        effect = column(f'{target.sensor_key}:{ia._COOLING_EFFECT_OUTPUT} [')
        assert hours.sum() > 0
        assert row[f'{zone}_Occupied Hours (h)'] == pytest.approx(hours.sum())
        assert row[f'{zone}_Mean SET_Pierce (°C)'] == pytest.approx((set_values * hours).sum() / hours.sum())
        assert row[f'{zone}_Mean CoolingEffect (°C)'] == pytest.approx((effect * hours).sum() / hours.sum())
        within = (set_values >= BAND[0]) & (set_values <= BAND[1])
        assert row[f'{zone}_Hours In Causal Band (h)'] == pytest.approx(hours[within].sum())
        # The cooling season starts on 1 May: two of the four days
        assert 0 <= row[f'{zone}_Overcooling Hours (h)'] <= hours[2 * 24:].sum()
        assert np.isfinite(row[f'{zone}_Mean Tn_exp (°C)'])
        assert np.isnan(row[f'{zone}_Drift Limited Hours (h)'])
    # Table names the outputs after the zones
    for zone in table.occupied_zone_list:
        for name in ia.ENERGYPLUS_OUTPUTS.values():
            assert f'{zone}_{name}' in table.df.columns, (zone, name)


@pytest.mark.parametrize('rename_cols', [True, False])
def test_the_comfort_hours_table_takes_the_hours_in_the_causal_band(tmp_path, monkeypatch, rename_cols):
    from accim.data.postprocessing import optional_output_columns as ooc

    model = DESIGNBUILDER
    columns = {}
    for target in resolve_targets(model['building']):
        columns[f'{target.zone_name.upper()}:Zone Operative Temperature [C](Hourly)'] = [25.0, 26.0]
        columns[f'EMS:HoursInCausalBand_{target.ems_suffix} [H](Hourly)'] = [1.0, 0.0]
        columns[f'EMS:DriftLimitedHours_{target.ems_suffix} [H](Hourly)'] = [0.0, 1.0]
    table = _table(tmp_path, monkeypatch, model, columns, rename_cols=rename_cols)
    table.format_table(type_of_table='comfort hours')
    assert ooc.comfort_hours()[-1] == 'HoursInCausalBand (h)'
    causal = [c for c in table.val_cols if 'HOURSINCAUSALBAND' in c.upper()]
    # The 2 zones, and their block and building values (summed and mean); not the hours of the limiter of the drift
    assert len(causal) == 2 + 2 * 2, causal
    assert not [c for c in table.val_cols if 'DRIFT' in c.upper()]
