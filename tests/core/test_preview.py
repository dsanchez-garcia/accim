"""Tests for accim.sim.preview (proposal E1): the outdoor temperatures of reference of the adaptive comfort models, the
running means of EnergyPlus, and the setpoints of the ACCIS calculated without EnergyPlus.

The formulas are those of EN 16798-1:2019 (B.1, B.2), ASHRAE 55-2020 (5.4.2.1), van der Linden et al. (2006) and the
Engineering Reference of EnergyPlus 25.2 (19.1), as in section 11.4 of the proposals of 1.2.0. The unit tests use
weather files with made-up temperatures; the last tests simulate output IDFs of AddAccis with EnergyPlus 25.1 and
compare its hourly and timestep outputs with compute_setpoints (they found, on 2026-11-09, that EnergyPlus starts the
running mean of CEN 15251 with equation 19.82 without dividing it by 1 - alpha^7, that the daily means of the simulated
days are those of the first timestep of each hour, and that the EMS reads the running means of the previous day at the
first timestep of each day).
"""
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import find_energyplus
from accim.sim.preview import (
    ENERGYPLUS_CEN15251_ALPHA,
    compute_setpoints,
    energyplus_running_means,
    outdoor_metrics,
    plot_setpoints,
    read_epw_dry_bulb,
)
from accim.utils import get_setpoint_ems_code, get_setpoint_ems_programs

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
DAYS = 365


def _write_epw(path, temperatures):
    """A weather file with the hourly dry-bulb temperatures given (one value per hour, 8760), and the header lines."""
    dates = pd.date_range('2007-01-01', periods=DAYS, freq='D')
    lines = [f'HEADER {n}' for n in range(8)]
    for number, temperature in enumerate(temperatures):
        day, hour = divmod(number, 24)
        date = dates[day]
        lines.append(f'2007,{date.month},{date.day},{hour + 1},60,flags,{float(temperature)!r},8.8,86')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


def _temperatures(seed=1):
    """Hourly temperatures with a yearly and a daily cycle and noise."""
    rng = np.random.default_rng(seed)
    hours = np.arange(DAYS * 24)
    return (15 + 8 * np.sin(2 * np.pi * (hours / 24 - 110) / DAYS) + 5 * np.sin(2 * np.pi * (hours % 24 - 9) / 24)
            + rng.normal(0, 1.5, len(hours))).round(1)


@pytest.fixture
def epw(tmp_path):
    return _write_epw(tmp_path / 'weather.epw', _temperatures())


def test_read_epw_dry_bulb(epw, tmp_path):
    data = read_epw_dry_bulb(epw)
    assert list(data.columns) == ['month', 'day', 'hour', 'dry_bulb']
    assert len(data) == 8760 and data['hour'].tolist()[:25] == list(range(1, 25)) + [1]
    # The records must be whole days of hours 1 to 24
    _write_epw(tmp_path / 'short.epw', _temperatures()[:8760])
    lines = (tmp_path / 'short.epw').read_text().splitlines()
    (tmp_path / 'short.epw').write_text('\n'.join(lines[:-1]) + '\n')
    with pytest.raises(ValueError, match='whole days'):
        read_epw_dry_bulb(tmp_path / 'short.epw')


def test_outdoor_metrics_of_a_constant_temperature(tmp_path):
    metrics = outdoor_metrics(_write_epw(tmp_path / 'constant.epw', [15.0] * 8760), alpha=0.7, days=10)

    for name in ('daily_mean', 'RMOT', 'RMOT_7day', 'PMOT_n', 'Te_ref_nl', 'monthly_mean'):
        assert metrics[name].to_numpy() == pytest.approx(15.0), name
    assert metrics.attrs == {'alpha': 0.7, 'days': 10}


def test_outdoor_metrics_formulas(epw):
    hourly = outdoor_metrics(epw, alpha=0.8, days=30)
    daily = outdoor_metrics(epw, alpha=0.8, days=30, frequency='daily')
    temperatures = _temperatures().reshape(DAYS, 24)
    mean = temperatures.mean(axis=1)

    def previous(values, day, k):
        return values[(day - k) % DAYS]

    assert len(hourly) == 8760 and len(daily) == DAYS
    assert hourly['Tout'].to_numpy() == pytest.approx(_temperatures())
    assert hourly['datetime'].iloc[0] == pd.Timestamp('2007-01-01 01:00')
    assert hourly['datetime'].iloc[-1] == pd.Timestamp('2008-01-01 00:00')
    assert daily['date'].iloc[40] == pd.Timestamp('2007-02-10')
    for day in (0, 3, 40, 200, 364):
        assert daily['daily_mean'][day] == pytest.approx(mean[day])
        # EN 16798-1 (B.1), as an infinite sum of the previous days (the year repeats)
        rmot = (1 - 0.8) * sum(0.8 ** (k - 1) * previous(mean, day, k) for k in range(1, 20 * DAYS))
        assert daily['RMOT'][day] == pytest.approx(rmot, abs=1e-9)
        # EN 16798-1 (B.2)
        weights = [1, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2]
        rmot_7day = sum(w * previous(mean, day, k) for k, w in enumerate(weights, 1)) / 3.8
        assert daily['RMOT_7day'][day] == pytest.approx(rmot_7day)
        # ASHRAE 55-2020 (5.4.2.1): the arithmetic mean of the 30 previous days
        assert daily['PMOT_n'][day] == pytest.approx(np.mean([previous(mean, day, k) for k in range(1, 31)]))
        # van der Linden et al. (2006), with the mean of the maximum and the minimum of each day
        middle = (temperatures.max(axis=1) + temperatures.min(axis=1)) / 2
        te_ref = sum(w * previous(middle, day, k) for k, w in enumerate([1, 0.8, 0.4, 0.2])) / 2.4
        assert daily['Te_ref_nl'][day] == pytest.approx(te_ref)
        # The hourly rows of the day have the values of the day
        assert hourly['RMOT'][24 * day:24 * day + 24].to_numpy() == pytest.approx(daily['RMOT'][day])
    january = temperatures[:31].mean()
    assert daily['monthly_mean'][0] == pytest.approx(january) and daily['monthly_mean'][30] == pytest.approx(january)


@pytest.mark.parametrize('arguments, message', [
    (dict(alpha=0), 'alpha must be'), (dict(alpha=1), 'alpha must be'), (dict(alpha='0.8'), 'alpha must be'),
    (dict(days=0), 'days must be'), (dict(days=366), 'days must be'), (dict(days=7.5), 'days must be'),
    (dict(frequency='weekly'), 'frequency must be'),
])
def test_outdoor_metrics_arguments(epw, arguments, message):
    with pytest.raises(ValueError, match=message):
        outdoor_metrics(epw, **arguments)


def test_energyplus_running_means_of_a_constant_temperature(tmp_path):
    means = energyplus_running_means(_write_epw(tmp_path / 'constant.epw', [15.0] * 8760))

    assert len(means) == DAYS
    assert means['PMOT'].to_numpy() == pytest.approx(15.0)
    # The running mean of CEN 15251 starts with equation 19.82, which is not divided by 1 - alpha^7, and then tends to
    # the daily mean with equation 19.83
    alpha = ENERGYPLUS_CEN15251_ALPHA
    assert means['RMOT'][0] == pytest.approx(15 * (1 - alpha ** 7))
    assert means['RMOT'][10] == pytest.approx(15 - 15 * alpha ** 7 * alpha ** 10)
    assert means['RMOT'].iloc[-1] == pytest.approx(15.0)


def test_energyplus_daily_means_of_the_simulated_days(tmp_path):
    # The temperature of each hour is the number of the day: the daily mean of a simulated day is that of the first
    # timestep of each hour, interpolated between the previous hourly value and the current one, (n - 1)/n of the
    # difference with the last hour of the previous day in the first hour
    temperatures = np.repeat(np.arange(DAYS, dtype=float), 24)
    for n in (1, 4, 6):
        means = energyplus_running_means(_write_epw(tmp_path / 'days.epw', temperatures), timesteps_per_hour=n,
                                         start_date='10/02')
        assert means['date'][0] == pd.Timestamp('2007-02-10')
        simulated = means['simulated_daily_mean'].to_numpy()
        # On the first day, the hour before the first one is the last hour of the same day
        assert simulated[0] == 40
        assert simulated[1:] == pytest.approx(np.arange(41, DAYS) - (n - 1) / n / 24)
        # Before the run period, the daily means of the weather file
        assert means['PMOT'][0] == pytest.approx(np.mean(np.arange(10, 40)))
        assert means['PMOT'][1] == pytest.approx((np.sum(np.arange(11, 40)) + 40) / 30)
        assert means['PMOT'][2] == pytest.approx((np.sum(np.arange(12, 40)) + 40 + simulated[1]) / 30)


def test_energyplus_running_means_at_the_beginning_of_the_year(tmp_path):
    temperatures = _temperatures()
    mean = temperatures.reshape(DAYS, 24).mean(axis=1)
    means = energyplus_running_means(_write_epw(tmp_path / 'weather.epw', temperatures))

    # The days before 1 January are the last ones of the weather file
    assert means['PMOT'][0] == pytest.approx(mean[-30:].mean())
    alpha = ENERGYPLUS_CEN15251_ALPHA
    assert means['RMOT'][0] == pytest.approx((1 - alpha) * sum(alpha ** (k - 1) * mean[-k] for k in range(1, 8)))
    assert means['RMOT'][1] == pytest.approx(alpha * means['RMOT'][0] + (1 - alpha) * mean[0])


@pytest.mark.parametrize('arguments, message', [
    (dict(timesteps_per_hour=7), 'timesteps_per_hour must be one of'),
    (dict(start_date='31/02'), 'start_date must be'),
])
def test_energyplus_running_means_arguments(epw, arguments, message):
    with pytest.raises(ValueError, match=message):
        energyplus_running_means(epw, **arguments)


def test_energyplus_running_means_need_a_year(tmp_path):
    path = _write_epw(tmp_path / 'weather.epw', _temperatures())
    lines = path.read_text().splitlines()
    path.write_text('\n'.join(lines[:-24]) + '\n')
    with pytest.raises(ValueError, match='365 days'):
        energyplus_running_means(path)


def test_the_setpoint_programs_are_those_of_the_code():
    programs = get_setpoint_ems_programs(1, 2, 3)
    sections = {}
    name = None
    for line in get_setpoint_ems_code(1, 2, 3).splitlines():
        if line.startswith('! --- '):
            name = line[len('! --- '):].split(':')[0].split(',')[0]
            sections[name] = []
        elif name is not None and line:
            sections[name].append(line.strip())

    assert list(programs) == ['SetInputData_<zone>', 'SetAppLimits', 'ApplyCAT', 'SetComfTemp', 'SetAST',
                              'SetAST_Master', 'SetAST_CS1_0', 'SetAST_CS1_1', 'SetASTnoTol']
    for name in ('SetInputData_<zone>', 'SetAppLimits', 'ApplyCAT', 'SetComfTemp', 'SetAST', 'SetAST_Master',
                 'SetASTnoTol'):
        assert [line.strip() for line in programs[name]] == sections[name], name
    # The subprograms are whole (the code shows the lines of the comfort mode), so SetAST_Master can run them
    assert 'if (ComfMod == 3)' in [line.strip() for line in programs['SetAST_CS1_1']]


@pytest.mark.parametrize('arguments, message', [
    (dict(comfort_standard=1, comfort_mode=3), 'needs a category'),
    (dict(comfort_standard=1, category=2), 'needs a comfort_mode'),
    (dict(comfort_standard=1, category=5, comfort_mode=3), 'is not a category'),
    (dict(comfort_standard=50), 'is not a comfort standard'),
])
def test_the_setpoint_programs_need_the_category_and_comfort_mode(arguments, message):
    with pytest.raises(ValueError, match=message):
        get_setpoint_ems_programs(**arguments)


def test_compute_setpoints_of_en16798(epw):
    result = compute_setpoints(epw, 1, 2, 3, setpoint_tolerance=0.1)
    means = energyplus_running_means(epw)

    assert list(result.columns) == ['datetime', 'Tout', 'RMOT', 'PMOT', 'Tout_metric', 'ComfTemp', 'ACST', 'AHST',
                                    'ACSTnoTol', 'AHSTnoTol', 'applicable', 'cooling_season']
    assert len(result) == 8760 and result.attrs['metric'] == 'RMOT'
    assert result['Tout_metric'].equals(result['RMOT'])
    rmot = np.repeat(means['RMOT'].to_numpy(), 24)
    assert result['RMOT'].to_numpy() == pytest.approx(rmot)
    later = result['datetime'].dt.hour != 1
    # Out of the first hour of each day, the setpoints of the running mean of the day (EN 16798-1, category II: +3 and
    # -4 K, horizontally extended out of 10 to 30 °C)
    expected = 0.33 * np.clip(rmot, 10, 30) + 18.8
    assert result['ComfTemp'][later & (rmot >= 10)].to_numpy() == pytest.approx((0.33 * rmot + 18.8)[later & (rmot >= 10)])
    assert result['ACSTnoTol'][later].to_numpy() == pytest.approx((expected + 3)[later], abs=1e-4)
    assert result['AHSTnoTol'][later].to_numpy() == pytest.approx((expected - 4)[later], abs=1e-4)
    assert result['ACST'][later].to_numpy() == pytest.approx((expected + 3 - 0.1)[later], abs=1e-4)
    applicable = (rmot >= 10) & (rmot <= 30)
    assert (result['applicable'][later].to_numpy() == applicable[later]).all()
    # In the first hour of each day (but the first one), the first timestep has the running mean of the previous day
    previous = np.roll(np.repeat(means['RMOT'].to_numpy(), 24), 24)
    first_hours = ~later.to_numpy()
    comfort = (0.33 * previous + 18.8) / 6 + (0.33 * rmot + 18.8) * 5 / 6
    assert result['ComfTemp'][first_hours].to_numpy()[1:] == pytest.approx(comfort[first_hours][1:])
    # The cooling season, from 1 May to 30 September
    season = result.groupby(result['datetime'].dt.date)['cooling_season'].last()
    assert season[pd.Timestamp('2007-04-30').date()] == 0 and season[pd.Timestamp('2007-05-01').date()] == 1
    assert season[pd.Timestamp('2007-09-30').date()] == 1 and season[pd.Timestamp('2007-10-01').date()] == 0


def test_compute_setpoints_of_esp_cte_follow_the_time(epw):
    # CurrentTime is the time at the end of the timestep: the timestep that ends at 8:00 has the setpoints of the day.
    # The ROUNDING lines of the EMS lower a cooling setpoint that is already a multiple of 1/SetpointAcc by one step
    # (27 is 26.9999 with SetpointAcc 10000), and keep such a heating setpoint
    result = compute_setpoints(epw, 0, frequency='timestep', setpoint_tolerance=0)
    steps = result.set_index('datetime')
    assert steps.loc['2007-01-03 07:50', 'ACST'] == pytest.approx(26.9999)
    assert steps.loc['2007-01-03 08:00', 'ACST'] == pytest.approx(24.9999)
    assert steps.loc['2007-01-03 07:50', 'AHST'] == 17 and steps.loc['2007-01-03 08:00', 'AHST'] == 20
    assert steps.loc['2007-01-03 07:50', 'ACSTnoTol'] == 27
    assert result.attrs['metric'] is None and result['Tout_metric'].isna().all()
    # Static setpoints: no comfort temperature
    assert result['ComfTemp'].isna().all()
    hourly = compute_setpoints(epw, 0, setpoint_tolerance=0).set_index('datetime')
    assert hourly.loc['2007-01-03 08:00', 'ACST'] == pytest.approx((5 * 26.9999 + 24.9999) / 6)


def test_compute_setpoints_timesteps(epw):
    result = compute_setpoints(epw, 2, 80, 3, timesteps_per_hour=4, frequency='timestep', start_date='20/12')

    assert len(result) == 12 * 24 * 4
    assert result['datetime'].iloc[0] == pd.Timestamp('2007-12-20 00:15')
    assert result['datetime'].iloc[-1] == pd.Timestamp('2008-01-01 00:00')
    # The outdoor temperature of each timestep, interpolated; on the first day, from the last hour of the same day
    temperatures = _temperatures().reshape(DAYS, 24)
    first = temperatures[353]
    assert result['Tout'].iloc[3] == pytest.approx(first[0])
    assert result['Tout'].iloc[0] == pytest.approx(first[23] + (first[0] - first[23]) / 4)
    assert result['Tout'].iloc[5] == pytest.approx(first[0] + 2 * (first[1] - first[0]) / 4)
    # The running mean of the first timestep of the run period is 0 (EnergyPlus has not calculated it yet)
    assert result['ComfTemp'].iloc[0] == pytest.approx(17.8)
    assert result['ComfTemp'].iloc[1] == pytest.approx(0.31 * result['PMOT'].iloc[1] + 17.8)


@pytest.mark.parametrize('arguments, message', [
    (dict(frequency='daily'), 'frequency must be'),
    (dict(timesteps_per_hour=8), 'timesteps_per_hour must be one of'),
    (dict(setpoint_tolerance=0.1, unknown=1), 'unexpected keyword argument'),
])
def test_compute_setpoints_arguments(epw, arguments, message):
    with pytest.raises((ValueError, TypeError), match=message):
        compute_setpoints(epw, 1, 2, 3, **arguments)


def test_plot_setpoints(epw):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    ax = plot_setpoints(compute_setpoints(epw, 1, 2, 3).iloc[:24 * 30])
    labels = [line.get_label() for line in ax.get_lines()]
    assert labels == ['Cooling setpoint (ACST)', 'Heating setpoint (AHST)', 'Comfort temperature',
                      'Running mean outdoor temperature (RMOT)']
    plt.close(ax.figure)


def _energyplus():
    folder = find_energyplus('25.1', required=False)
    return folder if folder is not None and SAMPLE_IDF.exists() and EPW.exists() else None


def _simulate(tmp_path, monkeypatch, begin, end, frequency, zone_arguments, **arguments):
    """An output IDF of AddAccis of the sample model simulated with EnergyPlus 25.1 for a run period: its CSV file."""
    from accim.sim.accis import AddAccis, load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=[frequency], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', confirm=True, verbose=False, zone_arguments=zone_arguments, **arguments)
    output_idf = sorted(tmp_path.glob('TestModel[[]*.idf'))[0]
    idf = load_idf(output_idf)
    run_period = idf.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    idf.saveas(str(tmp_path / 'model.idf'))
    energyplus = _energyplus() / 'energyplus.exe'
    result = subprocess.run([str(energyplus), '-d', str(tmp_path / 'out'), '-p', 'run', '-s', 'C', '-r', '-x',
                             '-w', str(EPW), str(tmp_path / 'model.idf')], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    return pd.read_csv(tmp_path / 'out' / 'run.csv')


def _compare(results, zone, preview, tolerance):
    """The EMS outputs of a zone against compute_setpoints."""
    def column(text):
        [name] = [c for c in results.columns if c.startswith(f'EMS:{text}_{zone} [')]
        return results[name].to_numpy()

    preview = preview.iloc[:len(results)]
    # Null (the comfort temperature of static setpoints) is reported as 0
    for ours, theirs in (('ComfTemp', 'Comfort Temperature'), ('ACST', 'Adaptive Cooling Setpoint Temperature'),
                         ('AHST', 'Adaptive Heating Setpoint Temperature'),
                         ('ACSTnoTol', 'Adaptive Cooling Setpoint Temperature_No Tolerance'),
                         ('AHSTnoTol', 'Adaptive Heating Setpoint Temperature_No Tolerance')):
        np.testing.assert_allclose(np.nan_to_num(preview[ours].to_numpy()), column(theirs), rtol=0, atol=tolerance,
                                   err_msg=f'{zone} {ours}')


def _running_means(results):
    [cen] = [c for c in results.columns if 'CEN 15251 Adaptive Model Running Average' in c and 'ZONE1' in c]
    [ashrae] = [c for c in results.columns if 'ASHRAE 55 Adaptive Model Running Average' in c and 'ZONE1' in c]
    return results[cen].to_numpy(), results[ashrae].to_numpy()


@pytest.mark.skipif(_energyplus() is None, reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_compute_setpoints_as_energyplus_from_the_beginning_of_the_year(tmp_path, monkeypatch):
    # INT EN16798-1 (RMOT) in zone 1 and INT ASHRAE 55 (PMOT) in zone 2, 36 days of January and February: the running
    # mean of ASHRAE 55 has the days of the weather file at the beginning and then those of the simulation
    results = _simulate(tmp_path, monkeypatch, (1, 1), (2, 5), 'hourly',
                        {'Block1:Zone2': {'comfort_standard': 2, 'category': 80, 'comfort_mode': 3}},
                        comfort_standard=[1], category=[2], comfort_mode=[3])
    en16798 = compute_setpoints(EPW, 1, 2, 3)
    ashrae = compute_setpoints(EPW, 2, 80, 3)

    assert len(results) == 36 * 24
    # The accuracy of the setpoints: SetpointAcc of AddAccis (10000 by default)
    _compare(results, 'Block1_Zone1', en16798, 1e-4)
    _compare(results, 'Block1_Zone2', ashrae, 1e-4)
    cen, ashrae_mean = _running_means(results)
    np.testing.assert_allclose(en16798['RMOT'][:len(results)], cen, atol=1e-9)
    np.testing.assert_allclose(en16798['PMOT'][:len(results)], ashrae_mean, atol=1e-9)


@pytest.mark.skipif(_energyplus() is None, reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_compute_setpoints_as_energyplus_in_timesteps_from_july(tmp_path, monkeypatch):
    # The custom model (PMOT) in zone 1 and ESP CTE (static setpoints by the time of the day) in zone 2, 4 days of July
    # in timesteps
    custom = dict(custom_slope=0.31, custom_intercept=17.8, custom_cooling_offset=3.5, custom_heating_offset=-3.5,
                  custom_cooling_upper_limit=33.5, custom_cooling_lower_limit=10, custom_heating_upper_limit=33.5,
                  custom_heating_lower_limit=10)
    results = _simulate(tmp_path, monkeypatch, (7, 1), (7, 4), 'timestep', {'Block1:Zone2': {'comfort_standard': 0}},
                        comfort_standard=[99], category=[1], comfort_mode=[3], **custom)
    preview_custom = compute_setpoints(EPW, 99, None, 3, start_date='01/07', frequency='timestep', **custom)
    preview_cte = compute_setpoints(EPW, 0, start_date='01/07', frequency='timestep')

    assert len(results) == 4 * 24 * 6
    _compare(results, 'Block1_Zone1', preview_custom, 1e-4)
    _compare(results, 'Block1_Zone2', preview_cte, 1e-4)
    cen, ashrae_mean = _running_means(results)
    np.testing.assert_allclose(preview_custom['RMOT'][:len(results)], cen, atol=1e-9)
    np.testing.assert_allclose(preview_custom['PMOT'][:len(results)], ashrae_mean, atol=1e-9)
