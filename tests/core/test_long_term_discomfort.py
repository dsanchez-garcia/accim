"""Tests for the indicators of the long-term thermal discomfort (proposal D1,
:mod:`accim.data.postprocessing.long_term_discomfort`): the methods A, B and C of CEN/TR 16798-2:2019, Annex D, the
acceptable deviations of its Annex E (Table E.1), the PPD of ISO 7730:2025 (formula 5), the occupied hours below some
temperatures, and ``Table(long_term_indicators=True)``.

As decision D8 of the brief of 1.2.0 says, Table D.1 of the TR is not reproduced (its PPD weights need a calculation
of the PMV): the weights of Method B (1, 2 and 3 K) are checked analytically, those of Method C with the PPD of the
formula, and the PPD of the formula is computed in the tests, not typed.
"""
import math
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import accim.sim.accis
from accim.data.postprocessing import long_term_discomfort as ltd
from accim.data.postprocessing.main import Table
from accim.sim.targets import resolve_targets


def _ppd(pmv):
    """ISO 7730:2025, formula (5), computed here independently of accim."""
    return 100 - 95 * math.exp(-0.03353 * pmv ** 4 - 0.2179 * pmv ** 2)


def test_the_ppd_of_iso_7730():
    assert ltd.ppd_from_pmv(0) == 5.0
    for pmv in (0.5, -0.5, 1, -1, 2):
        assert ltd.ppd_from_pmv(pmv) == pytest.approx(_ppd(pmv), abs=1e-12)
    assert round(ltd.ppd_from_pmv(0.5), 1) == round(_ppd(0.5), 1) == 10.2
    assert round(ltd.ppd_from_pmv(1), 1) == round(_ppd(1), 1) == 26.1
    np.testing.assert_allclose(ltd.ppd_from_pmv(pd.Series([-1, 0, 1])), [_ppd(-1), 5, _ppd(1)], rtol=0, atol=1e-12)


# The temperatures of Table D.1 of CEN/TR 16798-2 (20 to 29 °C) and its range of 23 to 26 °C
TEMPERATURES = pd.Series([20.0, 21, 22, 23, 24, 25, 26, 27, 28, 29])


def test_method_b_gives_the_weights_of_table_d1():
    # wf = |Θo − Θo,limit| outside the range, 0 within it (both limits included): 3, 2 and 1 K at 20, 21 and 22 °C,
    # and 1, 2 and 3 K at 27, 28 and 29 °C
    for temperature, weight in zip(TEMPERATURES, [3, 2, 1, 0, 0, 0, 0, 1, 2, 3]):
        result = ltd.degree_hours(pd.Series([temperature]), 23, 26)
        assert result['hot_Kh'] + result['cold_Kh'] == weight
    assert ltd.degree_hours(TEMPERATURES, 23, 26) == {'hot_Kh': 6.0, 'cold_Kh': 6.0}
    # The time of each row, and only the occupied rows
    occupied = pd.Series([True] * 5 + [False] * 5)
    assert ltd.degree_hours(TEMPERATURES, 23, 26, occupied, timestep_h=0.25) == {'hot_Kh': 0.0, 'cold_Kh': 1.5}
    # Limits for each row (the setpoints of each hour)
    upper = pd.Series([26.0] * 7 + [28.0] * 3)
    assert ltd.degree_hours(TEMPERATURES, 23, upper)['hot_Kh'] == 0 + 0 + 1


def test_method_a_counts_the_occupied_hours_outside_the_range():
    result = ltd.hours_outside_range(TEMPERATURES, 23, 26)
    assert result == {'hot_h': 3.0, 'cold_h': 3.0, 'hot_pct': 30.0, 'cold_pct': 30.0, 'occupied_h': 10.0}
    # The occupants of each row (occupied if more than 0), and the hours of each row
    occupants = pd.Series([0, 2, 2, 1, 1, 1, 1, 1, 0, 3])
    result = ltd.hours_outside_range(TEMPERATURES, 23, 26, occupants, timestep_h=0.5)
    assert (result['hot_h'], result['cold_h'], result['occupied_h']) == (1.0, 1.0, 4.0)
    assert (result['hot_pct'], result['cold_pct']) == (25.0, 25.0)
    # The rows with missing values are left out; without occupied hours, the percentages are NaN
    with_nan = TEMPERATURES.copy()
    with_nan[0] = np.nan
    assert ltd.hours_outside_range(with_nan, 23, 26)['occupied_h'] == 9.0
    assert math.isnan(ltd.hours_outside_range(TEMPERATURES, 23, 26, occupied=[False] * 10)['hot_pct'])
    with pytest.raises(ValueError, match='lower has 3 values, not 10'):
        ltd.hours_outside_range(TEMPERATURES, [23, 23, 23], 26)
    with pytest.raises(ValueError, match='as pandas Series or arrays'):
        ltd.hours_outside_range(25, 23, 26)


def test_method_c_weights_the_hours_with_the_ppd():
    pmv = pd.Series([-1.0, -0.5, 0.0, 0.5, 0.7, 1.0])
    result = ltd.ppd_weighted_hours(pmv, -0.5, 0.5)
    # wf = PPD(PMV)/PPD(PMVlimit) outside the range, 0 within it: PMVlimit,lower <= PMV < PMVlimit,upper, as the literal
    # text of Annex D (verdict #20 of the review of 1.2.0), so the PMV of the upper limit is in the warm period, wf = 1
    assert result['cold_h'] == pytest.approx(_ppd(-1) / _ppd(-0.5), abs=1e-12)
    assert result['hot_h'] == pytest.approx(1 + (_ppd(0.7) + _ppd(1.0)) / _ppd(0.5), abs=1e-12)
    assert ltd.ppd_weighted_hours(pd.Series([0.5]), -0.5, 0.5) == {'hot_h': 1.0, 'cold_h': 0.0}
    assert ltd.ppd_weighted_hours(pd.Series([-0.5, 0.4999]), -0.5, 0.5) == {'hot_h': 0.0, 'cold_h': 0.0}
    # The PPD weights are larger than the degrees of the PMV beyond the limits
    assert result['hot_h'] > 2
    occupied = pd.Series([True, True, True, True, False, True])
    assert ltd.ppd_weighted_hours(pmv, -0.5, 0.5, occupied, timestep_h=2)['hot_h'] == pytest.approx(
        2 * (1 + _ppd(1.0) / _ppd(0.5)), abs=1e-12)


def test_the_acceptable_deviations_of_table_e1():
    assert ltd.DEVIATION_LIMITS == {'3%': {'weekly': 20.0, 'monthly': 12.0, 'yearly': 3.0},
                                    '6%': {'weekly': 50.0, 'monthly': 25.0, 'yearly': 6.0}}
    # The working time of Table E.1: 40 h a week, 175 h a month and 2100 h a year; 126 h a year on the 6 % level
    assert ltd.deviation_check(126, 2100) and not ltd.deviation_check(127, 2100)
    assert ltd.deviation_check(63, 2100, level='3%') and not ltd.deviation_check(64, 2100, level='3%')
    assert ltd.deviation_check(20, 40, 'weekly') and not ltd.deviation_check(21, 40, 'weekly')
    assert ltd.deviation_check(8, 40, 'weekly', '3%') and not ltd.deviation_check(9, 40, 'weekly', '3%')
    assert ltd.deviation_check(21, 175, 'monthly', '3%') and not ltd.deviation_check(22, 175, 'monthly', '3%')
    # 25 % of 175 h is 43.75 h (44 h in Table E.1)
    assert ltd.deviation_check(43.75, 175, 'monthly') and not ltd.deviation_check(44, 175, 'monthly')
    with pytest.raises(ValueError, match='level must be one of'):
        ltd.deviation_check(1, 100, level='5%')
    with pytest.raises(ValueError, match='period must be one of'):
        ltd.deviation_check(1, 100, period='daily')
    # The largest hours outside the range (the bounds of the constraints of the optimisation, proposal C2)
    assert ltd.deviation_limit(2100) == 126.0 and ltd.deviation_limit(2100, level='3%') == 63.0
    assert ltd.deviation_limit(40, 'weekly') == 20.0 and ltd.deviation_limit(40, 'weekly', '3%') == 8.0
    assert ltd.deviation_limit(175, 'monthly') == 43.75 and ltd.deviation_limit(175, 'monthly', '3%') == 21.0
    with pytest.raises(ValueError, match='level must be one of'):
        ltd.deviation_limit(100, level='5%')
    with pytest.raises(ValueError, match='period must be one of'):
        ltd.deviation_limit(100, period='daily')


def test_the_hours_below_some_temperatures():
    assert ltd.hours_below(TEMPERATURES, (22, 21)) == {22: 2.0, 21: 1.0}
    assert ltd.hours_below(TEMPERATURES, [25.5], occupied=pd.Series([1] * 3 + [0] * 7), timestep_h=0.5) == {25.5: 1.5}


# Table ------------------------------------------------------------------------------------------------------------

class _Obj(SimpleNamespace):
    def __getitem__(self, field):
        return getattr(self, field)


class _ObjectClasses(dict):
    def __getitem__(self, key):
        return super().__getitem__(key.upper())


class _FakeIDF:
    """A model of DesignBuilder (zones 'Block1:Zone1'...), with the classes that Table reads."""

    CLASSES = ['ZONE', 'SPACE', 'SPACELIST', 'PEOPLE', 'ZONECONTROL:THERMOSTAT']

    def __init__(self, zones):
        self.idfobjects = _ObjectClasses({c: [] for c in self.CLASSES})
        for zone in zones:
            self.idfobjects['ZONE'].append(_Obj(key='ZONE', Name=zone))
            self.idfobjects['ZONECONTROL:THERMOSTAT'].append(
                _Obj(key='ZONECONTROL:THERMOSTAT', Name=f'{zone} Thermostat', Zone_or_ZoneList_Name=zone))
            self.idfobjects['PEOPLE'].append(
                _Obj(key='PEOPLE', Name=f'People {zone}', Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone))


BUILDING = _FakeIDF(['Block1:Zone1', 'Block1:Zone2'])
CSV_NAME = 'Model[CS_INT EN16798[CA_2[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X[Seville.csv'
# Four hours of each zone: the operative temperature, the setpoints without the tolerance and the occupied hours
ZONES = {
    'Block1:Zone1': dict(temperature=[19.0, 22.0, 27.5, 30.0], lower=[20.0] * 4, upper=[26.0, 26.0, 26.0, 28.0],
                         occupied=[1.0, 1.0, 0.5, 0.0]),
    'Block1:Zone2': dict(temperature=[21.0, 25.0, 26.5, 18.0], lower=[20.0] * 4, upper=[26.0] * 4,
                         occupied=[0.0, 1.0, 1.0, 1.0]),
}


def _table(tmp_path, monkeypatch, columns=None, **kwargs):
    if columns is None:
        columns = {'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)': [10.0, 11.0, 12.0, 13.0]}
        for target, values in zip(resolve_targets(BUILDING), ZONES.values()):
            suffix, zone = target.ems_suffix, target.zone_name.upper()
            columns.update({
                f'EMS:Comfortable Hours_No Applicability_{suffix} [H](Hourly)': [0.0] * 4,
                f'EMS:Zone Floor Area_{suffix} [m2](Hourly)': [10.0] * 4,
                f'EMS:Zone Air Volume_{suffix} [m3](Hourly)': [30.0] * 4,
                f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{suffix} [C](Hourly)': values['upper'],
                f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{suffix} [C](Hourly)': values['lower'],
                f'EMS:Occupied Hours_{suffix} [H](Hourly)': values['occupied'],
                f'{zone}:Zone Operative Temperature [C](Hourly)': values['temperature'],
            })
    lines = [','.join(['Date/Time', *columns])]
    for hour in range(4):
        lines.append(','.join([f' 01/01  0{hour + 1}:00:00', *(str(v[hour]) for v in columns.values())]))
    (tmp_path / CSV_NAME).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(accim.sim.accis, 'load_idf', lambda idf_path: BUILDING)
    arguments = dict(datasets=[CSV_NAME], source_frequency='hourly', frequency='hourly', frequency_agg_func='sum',
                     standard_outputs=True, level=['block', 'building'], level_agg_func=['sum', 'mean'],
                     level_excluded_zones=[], normalised_energy_units=False, energy_units_in_kwh=False,
                     idf_path='model.idf', long_term_indicators=True)
    arguments.update(kwargs)
    return Table(**arguments)


@pytest.mark.parametrize('rename_cols', [True, False])
def test_the_table_gives_the_indicators_of_each_zone_and_the_building(tmp_path, monkeypatch, rename_cols):
    table = _table(tmp_path, monkeypatch, rename_cols=rename_cols)
    indicators = table.long_term_indicators
    assert len(indicators) == 1
    row = indicators.iloc[0]
    assert (row['Source'], row['Model'], row['ComfStand'], row['EPW']) == (
        CSV_NAME[:-4], 'Model', 'CS_INT EN16798', 'Seville')
    expected = {}
    for zone, values in ZONES.items():
        frame = pd.DataFrame(values)
        hours = frame['occupied']
        hot = frame['temperature'] > frame['upper']
        cold = frame['temperature'] < frame['lower']
        above = (frame['temperature'] - frame['upper']).clip(lower=0)
        below = (frame['lower'] - frame['temperature']).clip(lower=0)
        expected[zone] = {
            'Occupied Hours (h)': hours.sum(), 'Hours Above Upper Limit (h)': hours[hot].sum(),
            'Hours Below Lower Limit (h)': hours[cold].sum(),
            'Degree Hours Above Upper Limit (Kh)': (hours * above).sum(),
            'Degree Hours Below Lower Limit (Kh)': (hours * below).sum(),
        }
    # Zone 1: 1 h below (19 °C), 0.5 h above (27.5 °C, 1.5 K); the hour at 30 °C is not occupied
    assert expected['Block1:Zone1']['Hours Below Lower Limit (h)'] == 1.0
    assert expected['Block1:Zone1']['Degree Hours Above Upper Limit (Kh)'] == 0.75
    for zone, values in expected.items():
        for title, value in values.items():
            assert row[f'{zone}_{title}'] == pytest.approx(value), (zone, title)
        assert row[f'{zone}_Hours Above Upper Limit (%)'] == pytest.approx(
            100 * values['Hours Above Upper Limit (h)'] / values['Occupied Hours (h)'])
    for title in expected['Block1:Zone1']:
        assert row[f'Building_{title}'] == pytest.approx(sum(values[title] for values in expected.values()))
    # 1 h below in each zone, of 2.5 and 3 occupied hours
    assert row['Building_Hours Below Lower Limit (%)'] == pytest.approx(100 * 2.0 / 5.5)


def test_the_table_checks_the_indicators(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="long_term_indicators needs the rows of each timestep or hour"):
        _table(tmp_path, monkeypatch, frequency='daily')
    # Without the occupied hours of the zones
    columns = {'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)': [10.0] * 4}
    for target, values in zip(resolve_targets(BUILDING), ZONES.values()):
        columns[f'EMS:Comfortable Hours_No Applicability_{target.ems_suffix} [H](Hourly)'] = [0.0] * 4
        columns[f'{target.zone_name.upper()}:Zone Operative Temperature [C](Hourly)'] = values['temperature']
    with pytest.raises(ValueError, match=r'long_term_indicators needs .* Block1:Zone1 \(upper, lower, hours\)'):
        _table(tmp_path, monkeypatch, columns=columns)
    # The other tables do not have the attribute, so their files do not change
    table = _table(tmp_path, monkeypatch, long_term_indicators=False)
    assert not hasattr(table, 'long_term_indicators') and 'long_term_indicators' not in table._json_content()


def _timestep_csv(path, steps=6, hours=2):
    """A CSV file of timestep outputs, with the names that EnergyPlus gives their columns ('[C](TimeStep)'), of two
    hours: the operative temperature, the setpoints without the tolerance and the occupied hours of the zones."""
    rows = steps * hours
    stamps = [f' 01/01  {(n + 1) * 60 // steps // 60:02d}:{(n + 1) * 60 // steps % 60:02d}:00' for n in range(rows)]
    columns = {'Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)': [10.0 + n for n in range(rows)]}
    values = {}
    for number, target in enumerate(resolve_targets(BUILDING)):
        suffix, zone = target.ems_suffix, target.zone_name.upper()
        temperature = [20.0 + number + 0.5 * n for n in range(rows)]
        occupied = [1 / steps if n % steps >= 2 else 0.0 for n in range(rows)]
        columns.update({
            f'EMS:Comfortable Hours_No Applicability_{suffix} [H](TimeStep)': [0.0] * rows,
            f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{suffix} [C](TimeStep)': [24.0] * rows,
            f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{suffix} [C](TimeStep)': [21.0] * rows,
            f'EMS:Occupied Hours_{suffix} [H](TimeStep)': occupied,
            f'{zone}:Zone Operative Temperature [C](TimeStep)': temperature,
        })
        values[target.zone_name] = (temperature, occupied)
    lines = [','.join(['Date/Time', *columns])]
    lines += [','.join([stamp, *(str(v[n]) for v in columns.values())]) for n, stamp in enumerate(stamps)]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return stamps, values


def test_the_table_of_timestep_outputs(tmp_path, monkeypatch, capsys):
    # The P1 entry of TODO.md (finding D1-1 of the review of 1.2.0): EnergyPlus names the columns of the timestep
    # outputs '(TimeStep)', which the standard outputs did not find, and labels each timestep with its end, so the
    # timesteps 00:10 to 01:00 are the first hour
    stamps, values = _timestep_csv(tmp_path / CSV_NAME)
    assert stamps[:2] == [' 01/01  00:10:00', ' 01/01  00:20:00'] and stamps[5] == ' 01/01  01:00:00'
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(accim.sim.accis, 'load_idf', lambda idf_path: BUILDING)
    arguments = dict(datasets=[CSV_NAME], source_frequency='timestep', frequency_agg_func='sum',
                     standard_outputs=True, level=['building'], level_agg_func=['sum'], level_excluded_zones=[],
                     normalised_energy_units=False, energy_units_in_kwh=False, idf_path='model.idf')
    table = Table(frequency='hourly', long_term_indicators=True, **arguments)
    assert table.occupied_zone_list == ['Block1:Zone1', 'Block1:Zone2']
    # The hours as those of the hourly outputs (Table numbers them by their beginning: 01:00:00 is the hour 00)
    assert list(table.df['Hour']) == ['00', '01'] and list(table.df['Minute']) == ['00', '00']
    for zone, (temperature, occupied) in values.items():
        operative = table.df[f'{zone}_Zone Operative Temperature (°C)'].tolist()
        assert operative == pytest.approx([np.mean(temperature[:6]), np.mean(temperature[6:])])
        hours = table.df[[c for c in table.df.columns if c.upper().startswith(f'EMS:OCCUPIED HOURS_{zone.upper()}')]]
        assert hours.iloc[:, 0].tolist() == pytest.approx([sum(occupied[:6]), sum(occupied[6:])])
    assert 'have not been correctly aggregated' not in capsys.readouterr().out
    # The indicators of the hourly means: the second hour is above 24 °C in both zones
    row = table.long_term_indicators.iloc[0]
    assert row['Block1:Zone1_Occupied Hours (h)'] == pytest.approx(4 / 3)
    assert row['Block1:Zone1_Hours Above Upper Limit (h)'] == pytest.approx(2 / 3)
    # The timesteps keep their rows with frequency 'timestep', in the hour that they are part of (00:10 to 01:00, the
    # hour 00; before, 00:10 to 00:50 got the hour -1)
    table = Table(frequency='timestep', **arguments)
    assert len(table.df) == 12 and list(table.df['Hour']) == ['00'] * 6 + ['01'] * 6
