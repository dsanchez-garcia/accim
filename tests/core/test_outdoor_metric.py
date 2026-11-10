"""Tests for the outdoor metric of the custom comfort model (proposal B1, :mod:`accim.sim.ems.outdoor_metric`).

The custom model (comfort standard 99) calculates its comfort temperature, setpoints and applicability with the
outdoor metric of ``custom_outdoor_metric``: 'pmot' (the default, as before accim 1.2.0) and 'rmot' are the running
means of EnergyPlus; the EMS calculates the others from the outdoor dry-bulb temperature, without
EnergyManagementSystem:TrendVariable. The formulas are those of section 11.4 of the proposals of 1.2.0: EN 16798-1:2019,
Annex B, (B.1) and (B.2); ASHRAE 55-2020, 5.4.2.1; van der Linden et al. (2006). The unit tests run the EMS programs
with the Erl interpreter of accim (compute_setpoints) on a weather file with made-up temperatures and check them with
pandas; the last tests simulate output IDFs of AddAccis with EnergyPlus 25.1 (verify_accim_simulation, the native
running mean of CEN 15251 and both backends).
"""
import re
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim.ems import outdoor_metric as om
from accim.sim.ems import program_lines as pl
from accim.sim.ems.setast import MODULAR_COMFORT_MODES, get_setpoint_lines, subprograms
from accim.sim.preview import compute_setpoints, energyplus_running_means
from accim.utils import get_setpoint_ems_code, get_setpoint_ems_programs

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
# An output IDF of accim 0.x (before SetAST_Master), with one program SetInputData for all the zones
LEGACY_IDF = next((REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'runEp').glob('TestModel_V2510*.idf'), None)
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
DAYS = 365
STEPS = 6
CUSTOM = dict(custom_slope=0.33, custom_intercept=18.8, custom_cooling_offset=2, custom_heating_offset=-3,
              custom_cooling_upper_limit=30, custom_cooling_lower_limit=10, custom_heating_upper_limit=30,
              custom_heating_lower_limit=10)


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


def _temperatures(seed=2):
    """Hourly temperatures with a yearly and a daily cycle and noise."""
    rng = np.random.default_rng(seed)
    hours = np.arange(DAYS * 24)
    return (15 + 8 * np.sin(2 * np.pi * (hours / 24 - 110) / DAYS) + 5 * np.sin(2 * np.pi * (hours % 24 - 9) / 24)
            + rng.normal(0, 1.5, len(hours))).round(1)


@pytest.fixture(scope='module')
def epw(tmp_path_factory):
    return _write_epw(tmp_path_factory.mktemp('weather') / 'weather.epw', _temperatures())


@pytest.fixture(scope='module')
def daily(epw):
    """The daily mean, maximum and minimum of the weather file, with pandas."""
    hourly = pd.read_csv(epw, skiprows=8, header=None)
    temperatures = pd.Series(hourly[6].to_numpy(dtype=float),
                             index=pd.date_range('2007-01-01 00:00', periods=DAYS * 24, freq='h'))
    return temperatures.resample('D').agg(['mean', 'max', 'min']).reset_index(drop=True)


def _metric(epw, metric, start_date=1, outdoor_metric_start='epw', **arguments):
    """Tout_metric of compute_setpoints in each timestep, as an array of days."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        result = compute_setpoints(epw, 99, None, 3, frequency='timestep', start_date=start_date,
                                   outdoor_metric_start=outdoor_metric_start, custom_outdoor_metric=metric,
                                   **dict(CUSTOM, **arguments))
    return result, result['Tout_metric'].to_numpy().reshape(-1, 24 * STEPS)


# The metrics and their arguments -------------------------------------------------------------------------------

def test_the_metrics_and_their_codes():
    assert om.OUTDOOR_METRICS == {'pmot': 0, 'rmot': 1, 'rmot_alpha': 2, 'rmot_7day': 3, 'daily_mean': 4, 'ndrm': 5,
                                  'monthly_mean': 6, 'te_ref_nl': 7}
    assert (om.metric_code('RMOT_alpha'), om.metric_code(5), om.metric_code(5.0)) == (2, 5, 5)
    assert (om.metric_name(7), om.metric_name('ndrm')) == ('te_ref_nl', 'ndrm')
    for value in ('rmot_beta', 8, True, None):
        with pytest.raises(ValueError, match='custom_outdoor_metric must be one of'):
            om.metric_code(value)


@pytest.mark.parametrize('metric, alpha, days, message', [
    # Decision D7: ASHRAE 55-2020 (5.4.2.1), a warning and not an error
    ('rmot_alpha', 0.95, 30, r'custom_alpha 0\.95 is outside 0\.6 to 0\.9'),
    ('rmot_alpha', 0.5, 30, r'custom_alpha 0\.5 is outside 0\.6 to 0\.9'),
    ('ndrm', 0.8, 40, r'custom_days 40 is outside the 7 to 30 days'),
    ('ndrm', 0.8, 5, r'custom_days 5 is outside the 7 to 30 days'),
    # The alpha of 'ndrm' and the days of 'rmot_alpha' are not used
    ('ndrm', 0.95, 30, None),
    ('rmot_alpha', 0.8, 40, None),
    ('rmot_alpha', 0.6, 7, None),
    ('ndrm', 0.9, 30, None),
])
def test_alpha_and_days_outside_ashrae_55_warn(metric, alpha, days, message):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        assert om.check_outdoor_metric_arguments(metric, alpha, days) == om.OUTDOOR_METRICS[metric]
    messages = [str(warning.message) for warning in caught]
    if message is None:
        assert messages == []
    else:
        assert len(messages) == 1 and re.search(message, messages[0])


@pytest.mark.parametrize('alpha, days, message', [
    (0, 30, 'custom_alpha must be a number between 0 and 1'),
    (1, 30, 'custom_alpha must be a number between 0 and 1'),
    ('0.8', 30, 'custom_alpha must be a number between 0 and 1'),
    (True, 30, 'custom_alpha must be a number between 0 and 1'),
    (0.8, 0, 'custom_days must be an integer of at least 1'),
    (0.8, 7.5, 'custom_days must be an integer of at least 1'),
    (0.8, '7', 'custom_days must be an integer of at least 1'),
])
def test_invalid_alpha_and_days_raise(alpha, days, message):
    with pytest.raises(ValueError, match=message):
        om.check_outdoor_metric_arguments('rmot_alpha', alpha, days)


def test_the_ring_keeps_30_days_at_least():
    assert om.ring_days() == 30
    assert om.ring_days([7, 30]) == 30
    assert om.ring_days([7, 45.0]) == 45


# The EMS code -------------------------------------------------------------------------------------------------

def test_the_programs_of_the_custom_model_use_the_outdoor_metric():
    # Only the line of the custom model changes in SetComfTemp
    changed = [(old, new) for old, new in zip(pl.SET_COMF_TEMP, pl.SET_COMF_TEMP_OUTDOOR_METRIC) if old != new]
    assert changed == [('set ComfTemp = PMOT*m+n', 'set ComfTemp = Tout_metric*m+n')]
    # The hour counters of the other comfort standards do not change; those of the custom model use Tout_metric
    for standard in MODULAR_COMFORT_MODES:
        base = pl.for_comfort_standards(pl.COUNT_HOURS, [standard])
        variant = pl.for_comfort_standards(pl.COUNT_HOURS_OUTDOOR_METRIC, [standard])
        if standard == 99:
            assert 'PMOT' not in ' '.join(variant) and variant == [line.replace('PMOT', 'Tout_metric') for line in base]
        else:
            assert variant == base
    # SetVST gets a branch of the custom model before the branch that compares PMOT with the limits
    inserted = [line for line in pl.SET_VST_OUTDOOR_METRIC]
    start = inserted.index('elseif ComfStand == 99')
    assert inserted[start + 1] == 'if (Tout_metric >= AHSTall) && (Tout_metric <= ACSTaul)'
    assert inserted[:start] + inserted[start + 6:] == list(pl.SET_VST)
    # The subprograms of the setpoints of the custom model, and only them
    custom = subprograms([99], outdoor_metric=True)['SetAST_CS99_0']
    assert not any(re.search(r'\bPMOT\b', line) for line in custom)
    assert custom == [re.sub(r'\bPMOT\b', 'Tout_metric', line) for line in subprograms([99])['SetAST_CS99_0']]
    others = [n for n in MODULAR_COMFORT_MODES if n != 99]
    assert subprograms(others, outdoor_metric=True) == subprograms(others)
    assert get_setpoint_lines(1, 3, outdoor_metric=True) == get_setpoint_lines(1, 3)


def test_the_comfort_standards_of_a_chain():
    assert pl.chain_comfort_standards(pl.COUNT_HOURS) is None
    assert pl.chain_comfort_standards(pl.for_comfort_standards(pl.COUNT_HOURS, [2, 99])) == {2, 99}
    assert pl.chain_comfort_standards(pl.for_comfort_standards(pl.COUNT_HOURS_OUTDOOR_METRIC, [99, 1])) == {1, 99}
    with pytest.raises(ValueError):
        pl.chain_comfort_standards(['return'])


def test_the_setpoint_ems_code_of_the_outdoor_metric():
    # 'pmot' is the code of accim 1.1.0, and the other comfort standards do not use the outdoor metric
    assert get_setpoint_ems_code(99, comfort_mode=3, custom_outdoor_metric='pmot') == get_setpoint_ems_code(
        99, comfort_mode=3)
    assert 'SetOutdoorMetric' not in get_setpoint_ems_code(99, comfort_mode=3)
    assert get_setpoint_ems_code(1, 2, 3, custom_outdoor_metric='rmot_alpha') == get_setpoint_ems_code(1, 2, 3)

    code = get_setpoint_ems_code(99, comfort_mode=3, custom_outdoor_metric='rmot_alpha', custom_alpha=0.7)
    for text in ('! --- InitOutdoorMetric', '! --- SetOutdoorMetric:', '! --- SetOutdoorMetric_<zone>',
                 'set CustAST_metric = 2', 'set CustAST_alpha = 0.7', 'set CustAST_days = 30',
                 'set ComfTemp = Tout_metric*m+n', 'set RMOTa_<zone> = (1-CustAST_alpha)*Tday_1',
                 'if (Tout_metric >= ACSTall) && (Tout_metric <= ACSTaul)'):
        assert text in code, text
    programs = get_setpoint_ems_programs(99, comfort_mode=3, custom_outdoor_metric='rmot_alpha')
    assert list(programs)[:5] == ['InitOutdoorMetric', 'SetOutdoorMetric', 'SetInputData_<zone>',
                                  'SetOutdoorMetric_<zone>', 'SetAppLimits']
    # Without the weather file, the programs begin with PMOT
    assert 'if (OutdoorInit == 0) && (PMOT <> 0)' in programs['SetOutdoorMetric']
    assert not any(line.startswith('if DayOfYear ==') for line in programs['SetOutdoorMetric'])


def test_the_setpoint_ems_code_checks_the_outdoor_metric(epw):
    with pytest.raises(ValueError, match="'monthly_mean' needs the weather file"):
        get_setpoint_ems_programs(99, comfort_mode=3, custom_outdoor_metric='monthly_mean')
    with pytest.raises(ValueError, match='custom_outdoor_metric must be one of'):
        get_setpoint_ems_code(99, comfort_mode=3, custom_outdoor_metric='rmot_beta')
    with pytest.warns(UserWarning, match=r'custom_alpha 0\.95 is outside 0\.6 to 0\.9'):
        get_setpoint_ems_code(99, comfort_mode=3, custom_outdoor_metric='rmot_alpha', custom_alpha=0.95)
    # With the weather file, the programs begin with its values on the first day of the run period
    programs = get_setpoint_ems_programs(99, comfort_mode=3, custom_outdoor_metric='monthly_mean', epw=epw,
                                         start_date='01/07')
    assert 'if DayOfYear == 182' in programs['SetOutdoorMetric']
    assert sum(line.startswith('set OutdoorMonthlyMean = ') for line in programs['SetOutdoorMetric']) == 12


def test_the_numbers_of_the_programs():
    # Finding B1-2 of the review of 1.2.0: one formatter of the numbers of the EMS programs, positional, with the
    # shortest digits that give the same float
    from accim.sim.ems.erl import format_number

    assert [format_number(value) for value in (20, 20.0, 0.8, -0.5, 1e-05, 12.345, np.float64(0.33), 1e16)] == [
        '20', '20', '0.8', '-0.5', '0.00001', '12.345', '0.33', '10000000000000000']
    # As the programs of the outdoor metric write them: with '.0' (as repr), but without exponent
    assert [format_number(value, keep_decimal=True) for value in (20, 12.345, 1e-05, -3.0)] == [
        '20.0', '12.345', '0.00001', '-3.0']
    assert all(om._number(value) == repr(float(value)) for value in (20, 12.345, 0.1 + 0.2, -7.25, 1234.5))
    for value in (float('nan'), float('inf'), -np.inf):
        with pytest.raises(ValueError, match='it is not finite'):
            format_number(value)
    # The programs of the outdoor metric with a value that repr writes with an exponent
    lines = om.building_program_lines(30, {'start_day': 1, 'daily_means': [1e-05] * 30, 'mid_ranges': [0.0] * 3,
                                           'running_means': {}, 'monthly_means': [-2.5e-06] * 12})
    assert 'set Tday_1 = 0.00001' in lines and 'set OutdoorMonthlyMean = -0.0000025' in lines
    assert not any(re.search(r'\de-?\d', line) for line in lines)


def test_a_weather_file_without_some_months(tmp_path, epw):
    # Finding B1-2 of the review of 1.2.0: the programs keep the monthly means of the 12 months of the weather file
    lines = epw.read_text(encoding='utf-8').splitlines()
    partial = tmp_path / 'partial.epw'
    # The header and January to October
    partial.write_text('\n'.join(lines[:8 + 304 * 24]) + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match=r'has no days of the months \[11, 12\]: the EMS programs of the outdoor '
                                         r'metric keep the monthly means'):
        om.initial_values(partial, 1, 30, {'Zone1': 0.8})
    with pytest.raises(ValueError, match=r'has no days of the months \[11, 12\]'):
        get_setpoint_ems_programs(99, comfort_mode=3, custom_outdoor_metric='rmot_alpha', epw=partial)


# The programs, run by the Erl interpreter ----------------------------------------------------------------------

def test_the_running_mean_of_en16798_with_alpha(epw, daily):
    # EN 16798-1 (B.1) in its recursive form, Trm = (1 - alpha)*Ted-1 + alpha*Trm-1, from the values of the weather
    # file (the year repeats, as outdoor_metrics calculates them)
    for alpha in (0.8, 0.7):
        _, metric = _metric(epw, 'rmot_alpha', custom_alpha=alpha)
        # The value of each day, after the first timestep (the programs keep the daily mean at the end of the day)
        values = metric[:, 1]
        expected = np.empty(DAYS)
        expected[0] = values[0]
        for day in range(1, DAYS):
            expected[day] = (1 - alpha) * daily['mean'][day - 1] + alpha * expected[day - 1]
        np.testing.assert_allclose(values, expected, rtol=0, atol=1e-9)
        # The first value is the infinite sum of (B.1) for the year that repeats, and the value does not change during
        # the day
        means = daily['mean'].to_numpy()
        previous = np.array([means[-k % DAYS] for k in range(1, DAYS + 1)])
        first = (1 - alpha) * np.sum(alpha ** np.arange(DAYS) * previous) / (1 - alpha ** DAYS)
        assert values[0] == pytest.approx(first, abs=1e-9)
        assert (np.ptp(metric, axis=1) == 0).all()


def test_the_7_day_running_mean_and_the_mean_of_n_days(epw, daily):
    # EN 16798-1 (B.2) and ASHRAE 55-2020 (5.4.2.1) with pandas: rolling(7).mean() of the previous days
    means = daily['mean']
    weights = (1, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2)
    b2 = sum(weight * means.shift(k) for k, weight in enumerate(weights, start=1)) / 3.8
    _, metric = _metric(epw, 'rmot_7day')
    np.testing.assert_allclose(metric[7:, 1], b2[7:], rtol=0, atol=1e-9)
    for days in (7, 30, 45):
        _, metric = _metric(epw, 'ndrm', custom_days=days)
        expected = means.rolling(days).mean().shift(1)
        np.testing.assert_allclose(metric[days:, 1], expected[days:], rtol=0, atol=1e-9)
        # The first days take the last days of the weather file
        np.testing.assert_allclose(metric[0, 1], np.r_[means.to_numpy()[-days:]].mean(), rtol=0, atol=1e-9)


def test_the_daily_and_monthly_means(epw, daily):
    _, metric = _metric(epw, 'daily_mean')
    np.testing.assert_allclose(metric[1:, 1], daily['mean'][:-1], rtol=0, atol=1e-9)
    assert metric[0, 1] == pytest.approx(daily['mean'].iloc[-1], abs=1e-9)
    result, metric = _metric(epw, 'monthly_mean')
    months = pd.date_range('2007-01-01', periods=DAYS, freq='D').month
    expected = daily['mean'].groupby(months).transform('mean')
    np.testing.assert_allclose(metric[:, 1], expected, rtol=0, atol=1e-9)
    # The value is that of the month of the timestep, for the whole day
    assert (np.ptp(metric, axis=1) == 0).all() and result.attrs['metric'] == 'monthly_mean'


def test_the_reference_temperature_of_the_atg(epw, daily):
    # van der Linden et al. (2006): (T0 + 0.8*T-1 + 0.4*T-2 + 0.2*T-3)/2.4, with each T the mean of the maximum and
    # minimum of the day; T0, of the day so far (the hours that have ended)
    middle = (daily['max'] + daily['min']) / 2
    _, metric = _metric(epw, 'te_ref_nl')
    expected = (middle + 0.8 * middle.shift(1) + 0.4 * middle.shift(2) + 0.2 * middle.shift(3)) / 2.4
    np.testing.assert_allclose(metric[3:, -1], expected[3:], rtol=0, atol=1e-9)
    hourly = pd.read_csv(epw, skiprows=8, header=None)[6].to_numpy(dtype=float).reshape(DAYS, 24)
    previous = (0.8 * middle.shift(1) + 0.4 * middle.shift(2) + 0.2 * middle.shift(3)).to_numpy()
    for hour in (0, 5, 17):
        so_far = (hourly[:, :hour + 1].max(axis=1) + hourly[:, :hour + 1].min(axis=1)) / 2
        np.testing.assert_allclose(metric[3:, STEPS * hour + STEPS - 1], ((so_far + previous) / 2.4)[3:], rtol=0,
                                   atol=1e-9)


def test_the_native_running_mean_of_cen_15251(epw):
    # 'rmot' is the sensor RMOT, which the EMS reads as the running mean of the previous day at the first timestep
    result, metric = _metric(epw, 'rmot')
    rmot = result['RMOT'].to_numpy().reshape(-1, 24 * STEPS)
    np.testing.assert_array_equal(metric[:, 1:], rmot[:, 1:])
    np.testing.assert_array_equal(metric[1:, 0], rmot[:-1, 1])
    assert metric[0, 0] == 0


def test_without_the_weather_file_the_metric_begins_with_pmot(epw, daily):
    # Decision D3: without the weather file, the daily means begin with PMOT, as soon as EnergyPlus has calculated it
    # (it is 0 at the first timestep of the run period)
    pmot = energyplus_running_means(epw)['PMOT'].to_numpy()
    _, metric = _metric(epw, 'daily_mean', outdoor_metric_start='pmot')
    assert metric[0, 0] == 0
    np.testing.assert_allclose(metric[0, 1:], pmot[0], rtol=0, atol=1e-12)
    np.testing.assert_allclose(metric[1:, 1], daily['mean'][:-1], rtol=0, atol=1e-9)
    _, metric = _metric(epw, 'rmot_alpha', outdoor_metric_start='pmot')
    assert metric[0, 1] == pytest.approx(pmot[0], abs=1e-12)
    assert metric[1, 1] == pytest.approx(0.2 * daily['mean'][0] + 0.8 * pmot[0], abs=1e-9)
    # With the weather file, from any day of the year
    _, metric = _metric(epw, 'daily_mean', start_date='01/07')
    assert metric[0, 1] == pytest.approx(daily['mean'][180], abs=1e-9)
    with pytest.raises(ValueError, match="outdoor_metric_start must be 'epw' or 'pmot'"):
        _metric(epw, 'daily_mean', outdoor_metric_start='file')


def test_the_custom_model_uses_its_outdoor_metric(epw):
    result, _ = _metric(epw, 'ndrm', custom_days=7)
    inside = (result['Tout_metric'] >= 10) & (result['Tout_metric'] <= 30)
    np.testing.assert_allclose(result.loc[inside, 'ComfTemp'], 0.33 * result.loc[inside, 'Tout_metric'] + 18.8,
                               rtol=0, atol=1e-9)
    np.testing.assert_allclose(result.loc[inside, 'ACSTnoTol'], result.loc[inside, 'ComfTemp'] + 2, rtol=0, atol=1e-9)
    assert (result['applicable'] == inside.astype(int)).all()
    hourly = compute_setpoints(epw, 99, None, 3, custom_outdoor_metric='ndrm', custom_days=7, **CUSTOM)
    assert hourly.attrs['metric'] == 'ndrm'
    np.testing.assert_allclose(hourly['Tout_metric'], result['Tout_metric'].to_numpy().reshape(-1, STEPS).mean(axis=1))


# The models ---------------------------------------------------------------------------------------------------

def _add_accis(folder, monkeypatch, **arguments):
    from accim.sim.accis import AddAccis

    folder.mkdir(exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(script_type='vrf_mm', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', category=[1], comfort_mode=[3], hvac_mode=[2], ventilation_control=[0],
                 confirm=True, verbose=False, **CUSTOM, **arguments)
    return {path.name: path for path in folder.glob('TestModel[[]*.idf')}


def _programs(idf):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
            for p in idf.idfobjects['EnergyManagementSystem:Program']}


@needs_idd
def test_add_accis_adds_the_outdoor_metric_to_the_custom_model_only(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf

    outputs = _add_accis(tmp_path / 'metric', monkeypatch, comfort_standard=[1, 99], custom_outdoor_metric='rmot_alpha',
                         custom_alpha=0.7, epw=str(EPW))
    reference = _add_accis(tmp_path / 'reference', monkeypatch, comfort_standard=[1, 99])
    assert sorted(outputs) == sorted(reference) and len(outputs) == 2
    custom, en16798 = (next(name for name in outputs if f'[CS_{label}[' in name) for label in ('CUSTOM', 'INT EN16798'))
    # The output IDFs of the other comfort standards, and those of the custom model with 'pmot', are those of 1.1.0
    assert outputs[en16798].read_bytes() == reference[en16798].read_bytes()
    assert not om.has_outdoor_metric_code(load_idf(reference[custom]))

    idf = load_idf(outputs[custom])
    programs = _programs(idf)
    zones = ['Block1_Zone1', 'Block1_Zone2']
    assert {'SetOutdoorMetric', 'InitOutdoorMetric', *(f'SetOutdoorMetric_{zone}' for zone in zones)} <= set(programs)
    assert om.begins_with_weather_file(idf) and 'if DayOfYear == 1' in programs['SetOutdoorMetric']
    for zone in zones:
        assert {'set CustAST_metric = 2', 'set CustAST_alpha = 0.7', 'set CustAST_days = 30'} <= set(
            programs[f'SetInputData_{zone}'])
        run = programs[f'RunACCIS_{zone}']
        assert run[run.index(f'run SetInputData_{zone}') + 1] == f'run SetOutdoorMetric_{zone}'
        assert programs[f'CountHours_{zone}'] == pl.for_comfort_standards(
            pl.format_lines(pl.COUNT_HOURS_OUTDOOR_METRIC, zone=zone), [99])
    assert programs['SetComfTemp'] == pl.for_comfort_standards(pl.SET_COMF_TEMP_OUTDOOR_METRIC, [99])
    assert programs['SetVST'] == list(pl.SET_VST_OUTDOOR_METRIC)
    assert not any(re.search(r'\bPMOT\b', line) for line in programs['SetAST_CS99_0'])
    managers = [(m.Name, m.EnergyPlus_Model_Calling_Point)
                for m in idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']]
    names = [name for name, _ in managers]
    assert names.index('SetOutdoorMetric') < min(i for i, name in enumerate(names) if name.startswith('RunACCIS_'))
    assert ('InitOutdoorMetric', 'BeginNewEnvironment') in managers
    outputs_ems = {o.Name: o.EMS_Variable_Name for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    assert outputs_ems['Tout_metric'] == 'Tout_metric'
    assert all(outputs_ems[f'Tout_metric_{zone}'] == f'Tout_metric_{zone}' for zone in zones)
    requested = {(o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']}
    assert ('Tout_metric_Block1_Zone1', 'Hourly') in requested


@needs_idd
def test_add_accis_checks_the_outdoor_metric(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="'monthly_mean' needs the weather file"):
        _add_accis(tmp_path, monkeypatch, comfort_standard=[99], custom_outdoor_metric='monthly_mean')
    with pytest.raises(ValueError, match="'monthly_mean' needs the weather file"):
        _add_accis(tmp_path, monkeypatch, comfort_standard=[99],
                   zone_arguments={'Block1:Zone2': {'custom_outdoor_metric': 'monthly_mean'}})
    with pytest.raises(ValueError, match='epw must be the path of a weather file'):
        _add_accis(tmp_path, monkeypatch, comfort_standard=[99], custom_outdoor_metric='ndrm', epw='missing.epw')
    with pytest.raises(ValueError, match='custom_outdoor_metric must be one of'):
        _add_accis(tmp_path, monkeypatch, comfort_standard=[99], custom_outdoor_metric='weekly_mean')
    assert not list(tmp_path.glob('TestModel[[]*.idf'))
    from accim.sim.accis import AddAccis

    with pytest.warns(UserWarning, match=r'custom_alpha 0\.95 is outside 0\.6 to 0\.9'):
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                 output_type='simplified', output_frequencies=['hourly'], keep_existing_outputs=False,
                 energyplus_version='auto', setpoint_type='temperature', comfort_standard=[99], category=[1],
                 comfort_mode=[3], confirm=False, verbose=False, custom_outdoor_metric='rmot_alpha',
                 custom_alpha=0.95, **CUSTOM)


@needs_idd
def test_modify_accis_adds_and_removes_the_outdoor_metric(tmp_path):
    from accim.sim.accis import add_accis_to_idf, load_idf, modify_accis

    def model():
        shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
        idf = load_idf(tmp_path / 'model.idf')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            add_accis_to_idf(idf, script_type='vrf_mm', supply_air_temp_input_method='temperature difference',
                             output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                             setpoint_type='temperature', verbose=False)
        return idf

    reference = model()
    modify_accis(reference, comfort_standard=99, comfort_mode=3)
    idf = model()
    with pytest.warns(UserWarning, match='custom_days 40 is outside'):
        modify_accis(idf, comfort_standard=99, comfort_mode=3, custom_outdoor_metric='ndrm', custom_days=40,
                     zone_arguments={'Block1:Zone2': {'custom_outdoor_metric': 'rmot_7day'}})
    programs = _programs(idf)
    # The models of add_accis_to_idf have the code of all the comfort standards (with those defined by their data that
    # are built in, JPN Aqilah 2025, at the end of the chains)
    assert programs['SetComfTemp'] == list(pl.set_comf_temp_lines(True))
    assert programs['CountHours_Block1_Zone1'] == pl.format_lines(pl.count_hours_lines(True), zone='Block1_Zone1')
    assert programs['SetVST'] == list(pl.set_vst_lines(True))
    assert 'set Tday_40 = Tday_39' in programs['SetOutdoorMetric']
    assert 'set CustAST_metric = 3' in programs['SetInputData_Block1_Zone2']
    assert 'set CustAST_metric = 5' in programs['SetInputData_Block1_Zone1']
    # Back to 'pmot': the model is as without the outdoor metric
    modify_accis(idf, custom_outdoor_metric='pmot', zone_arguments={'Block1:Zone2': {'custom_outdoor_metric': 'pmot'}})
    assert idf.idfstr() == reference.idfstr()
    # The arguments that are None keep their values
    modify_accis(idf, comfort_standard=99, comfort_mode=3, custom_outdoor_metric='te_ref_nl')
    modify_accis(idf, category=1)
    assert 'set CustAST_metric = 7' in _programs(idf)['SetInputData_Block1_Zone1']


@needs_idd
@pytest.mark.skipif(LEGACY_IDF is None, reason='needs the output IDF of accim 0.x of the repository')
def test_the_models_of_earlier_versions_only_have_pmot(tmp_path):
    from accim.sim.accis import load_idf, modify_accis

    shutil.copy(LEGACY_IDF, tmp_path / 'legacy.idf')
    building = load_idf(tmp_path / 'legacy.idf')
    with pytest.raises(ValueError, match="only has the\\s+outdoor metric 'pmot'"):
        modify_accis(building, comfort_standard=99, comfort_mode=3, custom_outdoor_metric='rmot_alpha')
    modify_accis(building, comfort_standard=99, comfort_mode=3, custom_outdoor_metric='pmot')
    assert not om.has_outdoor_metric_code(building)


# EnergyPlus ---------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')


def _output_idf(tmp_path, monkeypatch, begin, end, frequency, **arguments):
    """An output IDF of AddAccis of the sample model with the custom model, whose input IDF has the run period given
    (with whose first day the outdoor metric begins)."""
    from accim.sim.accis import AddAccis, load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    model = load_idf(tmp_path / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    model.save()
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=[frequency], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', comfort_standard=[99], category=[1], comfort_mode=[3], confirm=True,
                 verbose=False, **CUSTOM, **arguments)
    [output_idf] = tmp_path.glob('TestModel[[]*.idf')
    shutil.copy(output_idf, tmp_path / 'model.idf')
    return tmp_path / 'model.idf'


def _run_energyplus(model, folder):
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    result = subprocess.run([str(energyplus), '-d', str(folder), '-p', 'run', '-s', 'C', '-r', '-x', '-w', str(EPW),
                             str(model)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    return pd.read_csv(folder / 'run.csv')


def _expected_metric(metric, days, custom_days=30, alpha=0.8):
    """The outdoor metric of each timestep of the first days of the year of the weather file of the simulations,
    with numpy and pandas from its hourly values, as an array of days x timesteps (NaN where it is not calculated):
    the days before the run period are the last ones of the file, with which the programs begin (decision D3). The
    daily metrics have the value of the day in all its timesteps; te_ref_nl, whose T0 is the mean of the maximum and
    the minimum of the hours of the day that have ended, only at the end of each hour (before the end of the first
    hour of the day, T0 is the outdoor temperature of the timestep)."""
    hourly = pd.read_csv(EPW, skiprows=8, header=None)[6].to_numpy(dtype=float).reshape(-1, 24)
    means = hourly.mean(axis=1)
    year = len(means)

    def before(values, k):
        # The values of k days before each day of the run period
        return np.roll(values, k)[:days]

    if metric == 'rmot_alpha':
        # EN 16798-1 (B.1): Trm = (1 - alpha)*Ted-1 + alpha*Trm-1, from its infinite sum for the year that repeats
        daily = np.empty(days)
        daily[0] = (1 - alpha) * sum(alpha ** (k - 1) * means[-k] for k in range(1, year + 1)) / (1 - alpha ** year)
        for day in range(1, days):
            daily[day] = (1 - alpha) * means[day - 1] + alpha * daily[day - 1]
    elif metric == 'rmot_7day':
        # EN 16798-1 (B.2)
        weights = (1, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2)
        daily = sum(weight * before(means, k) for k, weight in enumerate(weights, start=1)) / 3.8
    elif metric == 'ndrm':
        # ASHRAE 55-2020 (5.4.2.1): the arithmetic mean of the daily means of the custom_days previous days
        daily = pd.Series(np.r_[means[-custom_days:], means[:days]]).rolling(custom_days).mean().shift(1)
        daily = daily.to_numpy()[custom_days:]
    else:
        # van der Linden et al. (2006): (T0 + 0.8*T-1 + 0.4*T-2 + 0.2*T-3)/2.4, with each T the mean of the maximum and
        # the minimum of the day (T0, of the hours of the day that have ended)
        middle = (hourly.max(axis=1) + hourly.min(axis=1)) / 2
        previous = 0.8 * before(middle, 1) + 0.4 * before(middle, 2) + 0.2 * before(middle, 3)
        values = np.full((days, 24 * STEPS), np.nan)
        for hour in range(24):
            so_far = (hourly[:days, :hour + 1].max(axis=1) + hourly[:days, :hour + 1].min(axis=1)) / 2
            values[:, STEPS * hour + STEPS - 1] = (so_far + previous) / 2.4
        return values
    return np.repeat(daily, 24 * STEPS).reshape(days, -1)


@needs_energyplus
@pytest.mark.parametrize('metrics', [('rmot_alpha', 'te_ref_nl'), ('rmot_7day', 'ndrm')])
def test_the_outdoor_metrics_in_energyplus(tmp_path, monkeypatch, capsys, metrics):
    from accim.utils.verification import verify_accim_simulation

    # EN 16798-1 (B.1) in zone 1 and the ATG in zone 2, or EN 16798-1 (B.2) in zone 1 and the mean of 30 days of
    # ASHRAE 55 in zone 2, January and February in timesteps, from the weather file
    model = _output_idf(tmp_path, monkeypatch, (1, 1), (2, 28), 'timestep', custom_outdoor_metric=metrics[0],
                        zone_arguments={'Block1:Zone2': {'custom_outdoor_metric': metrics[1]}}, epw=str(EPW))
    results = _run_energyplus(model, tmp_path / 'out')
    days = 59
    assert len(results) == days * 24 * STEPS

    # The setpoints and the outdoor metric of each zone are those of compute_setpoints
    mismatches = verify_accim_simulation(str(tmp_path / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0 or not mismatches['check'].str.startswith('Check4').any()
    for zone in ('Block1_Zone1', 'Block1_Zone2'):
        assert f"'{zone}' Check4_Tout_metric (Tout_metric_{zone} of compute_setpoints): 0 mismatch(es)" in output

    # And those of their equations with numpy and pandas, directly from the weather file (section 3.4 of the review
    # of accim 1.2.0)
    for zone, metric in zip(('Block1_Zone1', 'Block1_Zone2'), metrics):
        [column] = [c for c in results.columns if c.startswith(f'EMS:Tout_metric_{zone} [')]
        found = results[column].to_numpy().reshape(days, -1)
        expected = _expected_metric(metric, days)
        checked = ~np.isnan(expected)
        assert checked.sum() >= days * 24
        np.testing.assert_allclose(found[checked], expected[checked], rtol=0, atol=1e-9, err_msg=metric)
    if metrics[0] != 'rmot_alpha':
        return

    # rmot_alpha with alpha 0.8 is the running mean of CEN 15251 of EnergyPlus once the beginning of that one, its
    # equation 19.82 (not divided by 1 - alpha^7), has faded: 0.11 K after 14 days in Seville in January, below 0.05 K
    # after 21 (the daily means of EnergyPlus are those of the first timestep of each hour, the others those of the
    # weather file)
    [metric] = [c for c in results.columns if c.startswith('EMS:Tout_metric_Block1_Zone1 [')]
    [native] = [c for c in results.columns if 'CEN 15251 Adaptive Model Running Average' in c and 'ZONE1' in c]
    difference = np.abs(results[metric].to_numpy() - results[native].to_numpy()).reshape(days, -1)[:, 1]
    assert difference[21:].max() < 0.05
    assert difference[14] > 0.05


@needs_energyplus
def test_the_ems_and_api_backends_give_the_same_outdoor_metrics(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations

    # The mean of 7 days in zone 1 and the daily mean in zone 2, 10 days of January, beginning with PMOT
    model = _output_idf(tmp_path, monkeypatch, (1, 1), (1, 10), 'hourly', custom_outdoor_metric='ndrm',
                        custom_days=7, zone_arguments={'Block1:Zone2': {'custom_outdoor_metric': 'daily_mean'}})
    ems_results = _run_energyplus(model, tmp_path / 'ems')
    results = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    assert len(ems_results) == 10 * 24
    assert any(column.startswith('EMS:Tout_metric_Block1_Zone2 [') for column in ems_results.columns)
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
