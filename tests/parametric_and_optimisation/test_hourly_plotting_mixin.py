"""Tests of the hourly analysis and plotting methods (accim.parametric_and_optimisation.hourly_plotting).

Synthetic hourly outputs with EnergyPlus-like column names are used, so no simulation is run.
"""
import os

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use('Agg')

from accim.parametric_and_optimisation.plotting import PlottingMixin
from accim.parametric_and_optimisation.hourly_plotting import (
    adaptive_comfort_band,
    comfort_categories,
    running_mean_outdoor_temperature,
    _match_label,
)

N = 8760
COLS = {
    'tout': 'ZONE:Zone Outdoor Air Drybulb Temperature [C](Hourly)',
    'rm': 'PEOPLE ZONE:Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)',
    'top': 'ZONE:Zone Operative Temperature [C](Hourly)',
    'acst': 'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance [C](Hourly)',
    'e': 'Electricity:HVAC [J](Hourly)',
    'cool': 'ZONE VRF COIL:Cooling Coil Total Cooling Rate [W](Hourly)',
    'heat': 'ZONE VRF COIL:Heating Coil Heating Rate [W](Hourly)',
    'win1': 'WIN1:AFN Surface Venting Window or Door Opening Factor [](Hourly)',
    'win2': 'WIN2:AFN Surface Venting Window or Door Opening Factor [](Hourly)',
}
EPWS = {'City_Present.epw': 0.0, 'City_2080.epw': 3.0}
CASES = {(0, 0): 'Static, AC', (3, 0): 'Adaptive, AC', (0, 2): 'Static, MM', (3, 2): 'Adaptive, MM'}


def _hourly_values(warming: float, comf_mod: int, hvac_mode: int) -> dict:
    h = np.arange(N)
    tout = 17 + warming + 9 * np.sin(2 * np.pi * (h / N - 0.3)) + 5 * np.sin(2 * np.pi * ((h % 24) / 24 - 0.35))
    rm = running_mean_outdoor_temperature(tout)
    if comf_mod == 3:
        acst = 0.33 * np.clip(rm, 10, 30) + 18.8 + 4
    else:
        acst = np.where(np.isin((h // 24) // 30, [4, 5, 6, 7, 8]), 27.0, 25.0)
    free = tout - 2 if hvac_mode == 2 else tout + 6
    top = np.minimum(np.maximum(free, 20.0), acst)
    cool = np.clip(free - acst, 0, None) * 900.0
    heat = np.clip(20.0 - free, 0, None) * 500.0
    e = (0.45 + (cool + heat) / 3000.0) * 3.6e6
    win = ((hvac_mode == 2) & (tout < top - 1)).astype(float) * np.ones(N)
    return {'tout': tout, 'rm': rm, 'top': top, 'acst': acst, 'e': e, 'cool': cool, 'heat': heat, 'win1': win,
            'win2': 0.5 * win}


def _results_and_hourly(tmp_path):
    rows, frames = [], []
    for epw, warming in EPWS.items():
        for (cm, hm) in CASES:
            values = _hourly_values(warming, cm, hm)
            folder = tmp_path / f'sim_{epw[:-4]}_{cm}_{hm}'
            folder.mkdir()
            csv = pd.DataFrame({COLS[k]: v for k, v in values.items()})
            csv.insert(0, 'Date/Time', [' 01/01  01:00:00'] * N)
            csv.to_csv(folder / 'eplusout.csv', index=False)
            rows.append({'ComfMod': float(cm), 'HVACmode': float(hm), 'epw': epw, 'idf': 'office',
                         'Electricity:HVAC': values['e'].sum(), 'output_dir': str(folder)})
            frame = pd.DataFrame({COLS[k]: v for k, v in values.items()})
            frame.insert(0, 'datetime', pd.date_range('2024-01-01 01:00', periods=N, freq='h'))
            frame.insert(0, 'hour', np.arange(1, N + 1))
            for col in ('idf', 'epw', 'HVACmode', 'ComfMod'):
                frame.insert(0, col, rows[-1][col])
            frames.append(frame)
    return pd.DataFrame(rows), pd.concat(frames, ignore_index=True)


class _Session(PlottingMixin):
    def __init__(self, results, hourly):
        self.outputs_param_simulation = results
        self.outputs_param_simulation_hourly = hourly
        self.outputs_optimisation = None
        self.outputs_optimisation_hourly = None
        self.building_floor_area = 312.0


@pytest.fixture(scope='module')
def session(tmp_path_factory):
    tmp = tmp_path_factory.mktemp('hourly')
    results, hourly = _results_and_hourly(tmp)
    return _Session(results, hourly)


# ------------------------------------------------------------------ functions

def test_adaptive_comfort_band_standards():
    lo, up = adaptive_comfort_band([20.0, 35.0, 5.0], 'EN16798-1', 'II')
    assert np.allclose(lo, [21.4, 0.33 * 30 + 18.8 - 4, 0.33 * 10 + 18.8 - 4])
    assert np.allclose(up, [28.4, 0.33 * 30 + 18.8 + 3, 0.33 * 10 + 18.8 + 3])
    lo, up = adaptive_comfort_band([35.0], 'EN16798-1', 'II', applicability='exclude')
    assert np.isnan(lo).all() and np.isnan(up).all()
    lo, up = adaptive_comfort_band([20.0], 'ASHRAE55', '80')
    assert np.allclose([lo[0], up[0]], [20.5, 27.5])
    lo, up = adaptive_comfort_band([20.0], {'slope': 0.3, 'intercept': 18.0, 'upper_offset': 2, 'lower_offset': 3})
    assert np.allclose([lo[0], up[0]], [21.0, 26.0])
    lo, up = adaptive_comfort_band(np.array([20.0]), lambda rm: (rm, rm + 1))
    assert np.allclose([lo[0], up[0]], [20.0, 21.0])
    assert comfort_categories('EN16798-1') == ['I', 'II', 'III']
    assert comfort_categories('ASHRAE55') == ['90', '80']


def test_running_mean_methods():
    flat = np.full(N, 12.0)
    assert np.allclose(running_mean_outdoor_temperature(flat), 12.0)
    steps = np.repeat(np.arange(365, dtype=float), 24)
    rm = running_mean_outdoor_temperature(steps, method='ashrae55', days=7)
    assert np.isclose(rm[24 * 100], np.mean(np.arange(93, 100)))
    rm_en = running_mean_outdoor_temperature(steps, method='en16798', alpha=0.8)
    day = 200
    assert np.isclose(rm_en[24 * day], 0.2 * (day - 1) + 0.8 * rm_en[24 * (day - 1)])


def test_match_label_substrings_and_tuples():
    labels = {'Present': 'Present', ('knee_point', '2080'): 'Knee, 2080', (0, 2): 'Static, MM'}
    assert _match_label('D:/x/City_Present.epw', labels) == 'Present'
    assert _match_label(('knee_point', 'City_2080'), labels) == 'Knee, 2080'
    assert _match_label((0.0, 2.0), labels) == 'Static, MM'
    assert _match_label('other', labels) is None


# ----------------------------------------------------------------- indicators

def test_compute_hourly_indicators_files_and_hourly_agree(session):
    from_files = session.compute_hourly_indicators(df_source='parametric', temperature_thresholds=(28,), verbose=False)
    from_hourly = session.compute_hourly_indicators(df_source='parametric_hourly', verbose=False, store=False)
    assert len(from_files) == len(from_hourly) == 8
    for col in ('E_HVAC', 'T_mean', 'share_outside_II', 'Kh_above_III', 'E_HVAC_peak', 'hours_cooling', 'hours_idle'):
        assert np.allclose(from_files[col].to_numpy(float), from_hourly[col].to_numpy(float)), col
    first = session.outputs_param_simulation.iloc[0]
    assert np.isclose(from_files['E_HVAC'].iloc[0], first['Electricity:HVAC'] / 3.6e6 / 312.0)
    assert set(from_files['comfort_outcome']) <= {'meets', 'too warm', 'too cool'}
    assert from_files.attrs['units']['E_HVAC'] == 'kWh/m²'
    assert session.hourly_indicators is from_files


def test_compute_hourly_indicators_options(session):
    rm = session.get_hourly_series_by_epw('CEN 15251 Adaptive Model Running Average')
    assert set(rm) == {'City_Present', 'City_2080'}
    ind = session.compute_hourly_indicators(df_source='parametric_hourly', running_mean=rm, comfort_standard='ASHRAE55',
                                           occupied=lambda cal: cal['hour_of_day'].between(8, 18).to_numpy(),
                                           normalize_per_m2=False, store=False, verbose=False)
    assert (ind['n_hours'] == 365 * 11).all()
    assert {'share_outside_80', 'share_outside_90'} <= set(ind.columns)
    assert ind.attrs['units']['E_HVAC'] == 'kWh'


def test_attach_hourly_series_by_epw(session):
    data = session.attach_hourly_series_by_epw('rm copy', session.get_hourly_series_by_epw('CEN 15251'),
                                               df=session.outputs_param_simulation_hourly)
    assert np.allclose(data['rm copy'], data[COLS['rm']])


# ---------------------------------------------------------------------- plots

def _png(fig):
    assert os.path.exists(fig.saved_path)
    return fig.summary


def test_plot_hourly_heatmaps(session, tmp_path):
    summary = _png(session.plot_hourly_heatmaps(['Zone Operative Temperature', 'Electricity:HVAC'],
                                                case=['ComfMod', 'HVACmode'], case_labels=CASES,
                                                data_filter={'include': {'epw': {'contains': 'Present'}}},
                                                out_dir=str(tmp_path)))
    assert len(summary) == 8


def test_plot_hourly_period_selects_windows(session, tmp_path):
    fig = session.plot_hourly_period(
        {'Outdoor air': 'Outdoor Air Drybulb', 'Operative temperature': 'Zone Operative Temperature'},
        case='ComfMod', case_labels={0: 'Static', 3: 'Adaptive'}, col='epw',
        col_labels={'Present': 'Present', '2080': '2080'},
        select={'Present': {'method': 'max_difference', 'variable': 'Electricity:HVAC', 'cases': ('Static', 'Adaptive')},
                '2080': {'method': 'max', 'variable': 'Outdoor Air Drybulb'}},
        energy_variable='Electricity:HVAC', shade=('Window or Door Opening Factor', 'Windows open'),
        data_filter={'include': {'HVACmode': 2}}, out_dir=str(tmp_path))
    summary = _png(fig)
    assert len(summary) == 4 and 'energy_per_m2' in summary


def test_plot_hourly_binned_response(session, tmp_path):
    summary = _png(session.plot_hourly_binned_response(
        x='Outdoor Air Drybulb', y='Electricity:HVAC', hue=['ComfMod', 'HVACmode'], hue_labels=CASES,
        idle_when_zero=['Cooling Coil Total Cooling Rate', 'Heating Coil Heating Rate'], out_dir=str(tmp_path)))
    assert np.allclose(summary['idle_level'].dropna(), 0.45)


def test_plot_load_duration_curves_with_peak_panel(session, tmp_path):
    ind = session.compute_hourly_indicators(df_source='parametric_hourly', store=False, verbose=False)
    summary = _png(session.plot_load_duration_curves('Electricity:HVAC', panel=['ComfMod', 'HVACmode'],
                                                     panel_labels=CASES, hue='epw', peak_df=ind,
                                                     peak_marker_by='HVACmode', peak_marker_labels={0: 'AC', 2: 'MM'},
                                                     out_dir=str(tmp_path)))
    assert (summary['peak'] > 0).all()


def test_plot_adaptive_comfort_chart(session, tmp_path):
    summary = _png(session.plot_adaptive_comfort_chart(row='HVACmode', col='epw', hue='ComfMod',
                                                       hue_labels={0: 'Static', 3: 'Adaptive'},
                                                       annotate_by='ComfMod', out_dir=str(tmp_path)))
    assert {'share_outside', 'share_above', 'share_below'} <= set(summary.columns)


def test_plot_hourly_scatter_matrix(session, tmp_path):
    summary = _png(session.plot_hourly_scatter_matrix(
        {'tout': 'Outdoor Air Drybulb', 'rm': 'CEN 15251', 'top': 'Zone Operative Temperature', 'e': 'Electricity:HVAC'},
        hue=['ComfMod', 'HVACmode'], hue_labels=CASES, weather_variables=['tout', 'rm'], n_sample=500,
        data_filter={'include': {'epw': {'contains': 'Present'}}}, out_dir=str(tmp_path)))
    assert len(summary) == 4 and 'top_iqr' in summary


def test_plot_monthly_distributions_with_band(session, tmp_path):
    summary = _png(session.plot_monthly_distributions('Zone Operative Temperature', panel=['ComfMod', 'HVACmode'],
                                                      panel_labels=CASES, compare_by='epw',
                                                      band={'running_mean': 'auto', 'category': 'II'},
                                                      out_dir=str(tmp_path)))
    assert set(summary['month']) == set(range(1, 13)) and 'share_above' in summary


def test_plot_results_scatter_matrix_and_screening(session, tmp_path):
    ind = session.compute_hourly_indicators(df_source='parametric', verbose=False)
    ind['pareto-optimal'] = ind['E_HVAC'] < ind['E_HVAC'].median()
    summary = _png(session.plot_results_scatter_matrix(['E_HVAC', 'T_mean', 'share_outside_II', 'Kh_outside_II'],
                                                       hue='HVACmode', upper='spearman',
                                                       log_columns=['Kh_outside_II'],
                                                       percent_columns=['share_outside_II'], out_dir=str(tmp_path)))
    assert len(summary) == 2
    _png(session.plot_results_scatter_matrix(['ComfMod', 'E_HVAC', 'share_outside_II'], hue='comfort_outcome',
                                             upper='scatter', color_by='T_mean', diag='stacked',
                                             out_dir=str(tmp_path), filename='outcome.png'))
    selected = session.outputs_param_simulation.iloc[[0]]
    summary = _png(session.plot_comfort_screening(col='epw', row='HVACmode', highlight='pareto-optimal',
                                                  selections={'Selected': selected}, threshold=0.05,
                                                  out_dir=str(tmp_path)))
    assert summary['n'].sum() == 8
    assert summary.filter(like='Selected_').notna().any().any()
