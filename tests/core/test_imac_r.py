"""Tests for comfort standards 9 and 10, IND IMAC R 7DRM and 30DRM (the decisions of 2026-11-12,
``notes/decisions.md``).

They are models A and B of Rawal et al. (2022), Building and Environment 219, 109187 (section 4.4 and Fig. 15):
``Tneut = 0.39·Tout-7DRM + 18.42`` and ``Tneut = 0.42·Tout-30DRM + 17.60``, with the 7-day and 30-day running means of
the outdoor temperature (simple means: the paper tells them apart from their weighted versions), applicable from 5.5 to
33 °C. Until accim 1.2.0, 9 read PMOT (the mean of 30 days of EnergyPlus) and the setpoints of 10 read RMOT (the
exponential running mean of EnergyPlus). Now 10 reads PMOT, and 9 the arithmetic mean of the daily means of the 7
previous days that the EMS code of the outdoor metric calculates (``'ndrm'`` with 7 days, ``Tout_metric``), which
begins with the values of the weather file (or with PMOT without it, with a warning); and the heating setpoint of
comfort mode 1 of 9 out of the applicability limits is below the line of the Indian building code, as that of 10, not
above it. The last tests simulate output IDFs of AddAccis with EnergyPlus 25.1 (verify_accim_simulation, and both
backends).
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
from accim.sim.ems import program_lines as pl
from accim.sim.ems import standard_lines as sdl
from accim.sim.ems.setpoint_lines import SETPOINT_LINES
from accim.sim.preview import compute_setpoints, outdoor_metrics
from accim.utils import get_setpoint_ems_code, get_setpoint_ems_programs

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
ZONES = ['Block1_Zone1', 'Block1_Zone2']
STEPS = 6
METRIC_INPUTS = {'CustAST_metric': 5, 'CustAST_alpha': 0.8, 'CustAST_days': 7}
#: The offsets of the categories (Rawal et al., 2022: ±2.15 K for 90 % and ±3.6 K for 80 %), and those of the line of
#: the Indian building code of comfort modes 0 and 1
OFFSETS = {80: 3.6, 90: 2.15}
STATIC_OFFSETS = {80: 2.72, 90: 1.5}
TOLERANCE = 0.1


# The EMS code ---------------------------------------------------------------------------------------------------------

def test_comfort_standard_10_reads_the_mean_of_30_days():
    # Model B: Tneut = 0.42·Tout-30DRM + 17.60. PMOT is the simple mean of the 30 previous days of EnergyPlus
    for mode in (0, 1, 2, 3):
        lines = SETPOINT_LINES[(10, mode)]
        assert not any(re.search(r'\bRMOT\b|Tout_metric', line) for line in lines), mode
    assert 'set ACST = PMOT*0.42+17.6+ACSToffset+ACSTtol' in SETPOINT_LINES[(10, 3)]
    assert 'set AHST = PMOT*0.078+23.25-2.72+AHSTtol' in SETPOINT_LINES[(10, 1)]
    assert pl.for_comfort_standards(pl.set_comf_temp_lines(), [10]) == [
        'if ComfStand == 10', 'set ComfTemp = PMOT*0.42+17.6', 'endif']
    # Its applicability, in the hour counters and in the ventilation setpoint (it was RMOT, with INT EN16798)
    assert pl.for_comfort_standards(pl.count_hours_lines(), [10])[:2] == [
        'if ComfStand == 10', 'if (PMOT >= AHSTall) && (PMOT <= ACSTaul)']
    assert pl.COUNT_HOURS[0] == 'if ComfStand == 1' and 'elseif ComfStand == 1' in pl.SET_VST
    assert not any('ComfStand == 10' in line for line in pl.SET_VST + pl.COUNT_HOURS)
    assert sdl.own_metric_inputs(10) is None and sdl.built_in_metric(10) is None
    code = get_setpoint_ems_code(10, 80, 3)
    assert 'RMOT*' not in code and 'SetOutdoorMetric' not in code


def test_comfort_standard_9_reads_the_mean_of_7_days():
    # Model A: Tneut = 0.39·Tout-7DRM + 18.42. EnergyPlus has no arithmetic mean of 7 days: the EMS calculates it
    assert sdl.BUILT_IN_METRICS == {9: ('ndrm', 0.8, 7)}
    assert sdl.built_in_metric(9) == ('ndrm', 0.8, 7) and sdl.built_in_metric('x') is None
    assert sdl.own_metric_inputs(9) == METRIC_INPUTS
    assert 9 in sdl.outdoor_metric_standards()
    for mode in (1, 2, 3):
        lines = SETPOINT_LINES[(9, mode)]
        assert 'set ACST = Tout_metric*0.39+18.42+ACSToffset+ACSTtol' in lines
        assert 'set AHST = Tout_metric*0.39+18.42+AHSToffset+AHSTtol' in lines
        # PMOT, only in the line of the Indian building code (comfort mode 1, out of the limits), as 7, 8 and 10
        assert all('*0.078+23.25' in line for line in lines if re.search(r'\bPMOT\b', line)), mode
        assert not any(re.search(r'\bRMOT\b', line) for line in lines)
    assert not any('Tout_metric' in line for line in SETPOINT_LINES[(9, 0)])
    assert pl.for_comfort_standards(pl.set_comf_temp_lines(), [9]) == [
        'if ComfStand == 9', 'set ComfTemp = Tout_metric*0.39+18.42', 'endif']
    assert pl.for_comfort_standards(pl.count_hours_lines(), [9])[:2] == [
        'if ComfStand == 9', 'if (Tout_metric >= AHSTall) && (Tout_metric <= ACSTaul)']
    # The ventilation setpoint: its branch, only in the models with its code
    assert pl.registered_standards_in(pl.set_vst_lines(comfort_standards=[9])) == {9}
    vst = list(pl.set_vst_lines(comfort_standards=[9]))
    assert vst[vst.index('elseif ComfStand == 9') + 1] == 'if (Tout_metric >= AHSTall) && (Tout_metric <= ACSTaul)'
    assert pl.set_vst_lines(comfort_standards=[2]) == pl.SET_VST
    # The applicability limits and the offsets of the categories are those of the paper, for both
    for standard in (9, 10):
        assert pl.for_comfort_standards(pl.set_app_limits_lines(), [standard]) == [
            f'if ComfStand == {standard}', 'set ACSTaul = 33', 'set ACSTall = 5.5', 'set AHSTaul = 33',
            'set AHSTall = 5.5', 'endif']
        assert pl.for_comfort_standards(pl.apply_cat_lines(), [standard])[1:] == [
            'if (CAT == 90)', 'set ACSToffset = 2.15+CATcoolOffset', 'set AHSToffset = -2.15+CATheatOffset',
            'elseif (CAT == 80)', 'set ACSToffset = 3.6+CATcoolOffset', 'set AHSToffset = -3.6+CATheatOffset',
            'endif', 'endif']


def test_the_heating_setpoint_of_9_in_comfort_mode_1_is_below_the_static_line():
    # Out of the limits, it was the line of the Indian building code plus 2.72 or 1.5 K, the values of the cooling
    # setpoint, so both setpoints were equal but for the tolerances
    lines = SETPOINT_LINES[(9, 1)]
    assert [line for line in lines if line.startswith('set AHST = PMOT')] == [
        'set AHST = PMOT*0.078+23.25-2.72+AHSTtol', 'set AHST = PMOT*0.078+23.25-1.5+AHSTtol']
    assert [line for line in lines if line.startswith('set ACST = PMOT')] == [
        'set ACST = PMOT*0.078+23.25+2.72+ACSTtol', 'set ACST = PMOT*0.078+23.25+1.5+ACSTtol']
    assert [line for line in lines if 'PMOT' in line] == [line for line in SETPOINT_LINES[(10, 1)]
                                                          if '0.078' in line]


@pytest.mark.parametrize('category', [80, 90])
def test_out_of_the_limits_comfort_mode_1_of_9_has_a_dead_band(category):
    # Without the weather file, at the first timestep of the run period PMOT is 0 for the EMS, so the mean of the 7
    # previous days is 0, out of the limits (5.5 to 33 °C): the line of the Indian building code with PMOT = 0
    first = compute_setpoints(EPW, 9, category, 1, frequency='timestep', outdoor_metric_start='pmot').iloc[0]
    assert first['Tout_metric'] == 0 and first['applicable'] == 0
    # (the setpoints of the thermostats are rounded to 4 decimals, the cooling one down and the heating one up)
    assert first['ACST'] == pytest.approx(23.25 + STATIC_OFFSETS[category] - TOLERANCE, abs=2e-4)
    assert first['AHST'] == pytest.approx(23.25 - STATIC_OFFSETS[category] + TOLERANCE, abs=2e-4)
    assert first['ACSTnoTol'] == pytest.approx(23.25 + STATIC_OFFSETS[category])
    assert first['AHSTnoTol'] == pytest.approx(23.25 - STATIC_OFFSETS[category])


def test_the_ems_code_of_9_has_the_programs_of_the_outdoor_metric():
    code = get_setpoint_ems_code(9, 80, 3, epw=EPW)
    assert '! Outdoor metric: ndrm (7 days), in the EMS Tout_metric' in code
    for line in ('set CustAST_metric = 5', 'set CustAST_days = 7', 'set Tout_metric = OutdoorDaysSum/CustAST_days',
                 'set ComfTemp = Tout_metric*0.39+18.42', 'if DayOfYear == 1'):
        assert line in code, line
    programs = get_setpoint_ems_programs(9, 80, 3)
    assert list(programs)[:4] == ['InitOutdoorMetric', 'SetOutdoorMetric', 'SetInputData_<zone>',
                                  'SetOutdoorMetric_<zone>']
    # Without the weather file, the daily means begin with PMOT
    assert not any(line.startswith('if DayOfYear ==') for line in programs['SetOutdoorMetric'])
    # The arguments of the outdoor metric of the custom model do not change it
    assert get_setpoint_ems_programs(9, 80, 3, custom_outdoor_metric='rmot_alpha', custom_days=12) == programs


def test_without_the_code_of_the_outdoor_metric_9_stops_the_simulation():
    # A zone whose comfort standard is changed to 9 by editing its program SetInputData_<zone>, in a model without the
    # EMS code of the outdoor metric (those of add_accis_to_idf, or the output IDFs of other comfort standards), stops
    # EnergyPlus instead of reading another running mean: Tout_metric is not initialised. AddAccis, modify_accis and
    # the parameter comfort_standard of the parametric module add that code
    from accim.sim.ems.erl import ErlProgramSet, ErlRuntimeError, variables_in_programs

    programs = {name: lines for name, lines in get_setpoint_ems_programs(9, 80, 3).items()
                if 'OutdoorMetric' not in name}
    erl = ErlProgramSet(programs, global_variables=set().union(*variables_in_programs(programs).values()))
    erl.strict = True
    for name, value in dict(RMOT=20.0, PMOT=21.0, DayOfYear=30.0, CurrentTime=6.0).items():
        erl.set(name, value)
    for name in ('SetInputData_<zone>', 'SetAppLimits', 'ApplyCAT'):
        erl.run(name)
    with pytest.raises(ErlRuntimeError, match="Variable = 'TOUT_METRIC' used in expression has not been initialized"):
        erl.run('SetComfTemp')
    # With it, as the programs of the outdoor metric set it
    erl.set('Tout_metric', 20.0)
    erl.run('SetComfTemp')
    assert erl.get('ComfTemp') == pytest.approx(0.39 * 20 + 18.42)


# compute_setpoints ----------------------------------------------------------------------------------------------------

def _mean_of_7_days(frame):
    """The arithmetic mean of the daily means of the 7 previous days of the weather file, for each row of a frame of
    compute_setpoints (the hour 24 of a day ends at 00:00 of the next one)."""
    daily = outdoor_metrics(EPW, days=7, frequency='daily').set_index('date')['PMOT_n']
    ends = pd.DatetimeIndex(frame['datetime'])
    days = (ends - pd.Timedelta(seconds=1)).normalize()
    return daily.reindex(days).to_numpy()


@pytest.mark.parametrize('start_date', ['01/01', '08/01', '01/07'])
@pytest.mark.parametrize('comfort_mode', [1, 2, 3])
def test_compute_setpoints_of_9(start_date, comfort_mode):
    frame = compute_setpoints(EPW, 9, 80, comfort_mode, start_date=start_date)
    assert frame.attrs['metric'] == 'ndrm'
    metric = _mean_of_7_days(frame)
    # From the first timestep, with the values of the weather file: the days before the run period are those of the
    # file (the last ones of the year before 1 January)
    np.testing.assert_allclose(frame['Tout_metric'], metric, rtol=0, atol=1e-9)
    assert ((metric > 5.5) & (metric < 33)).all() and (frame['applicable'] == 1).all()
    np.testing.assert_allclose(frame['ComfTemp'], 0.39 * metric + 18.42, rtol=0, atol=1e-9)
    np.testing.assert_allclose(frame['ACSTnoTol'], 0.39 * metric + 18.42 + OFFSETS[80], rtol=0, atol=1e-9)
    np.testing.assert_allclose(frame['AHSTnoTol'], 0.39 * metric + 18.42 - OFFSETS[80], rtol=0, atol=1e-9)
    # It is not the mean of 30 days, which it read before
    assert np.abs(frame['Tout_metric'] - frame['PMOT']).max() > 2


def test_compute_setpoints_of_9_without_the_weather_file():
    frame = compute_setpoints(EPW, 9, 90, 3, frequency='timestep', start_date='01/03', outdoor_metric_start='pmot')
    steps = 24 * STEPS
    # The first day, PMOT (0 at the first timestep, as the EMS reads it); after 7 days, the mean of the 7 previous days
    assert frame['Tout_metric'].iloc[0] == 0
    np.testing.assert_allclose(frame['Tout_metric'].iloc[1:steps], frame['PMOT'].iloc[1:steps], rtol=0, atol=1e-9)
    late = frame.iloc[7 * steps:]
    np.testing.assert_allclose(late['Tout_metric'], _mean_of_7_days(late), rtol=0, atol=1e-9)


@pytest.mark.parametrize('comfort_mode', [1, 2, 3])
def test_compute_setpoints_of_10(comfort_mode):
    frame = compute_setpoints(EPW, 10, 90, comfort_mode, frequency='timestep', start_date='01/07')
    assert frame.attrs['metric'] == 'PMOT' and 'ComfTemp' in frame
    # The EMS reads the PMOT of the previous day at the first timestep of each day (0 at the first one of all)
    later = np.arange(len(frame)) % (24 * STEPS) != 0
    pmot = frame['PMOT'].to_numpy()[later]
    np.testing.assert_allclose(frame['ComfTemp'].to_numpy()[later], 0.42 * pmot + 17.6, rtol=0, atol=1e-9)
    np.testing.assert_allclose(frame['ACSTnoTol'].to_numpy()[later], 0.42 * pmot + 17.6 + OFFSETS[90], rtol=0,
                               atol=1e-9)
    np.testing.assert_allclose(frame['AHSTnoTol'].to_numpy()[later], 0.42 * pmot + 17.6 - OFFSETS[90], rtol=0,
                               atol=1e-9)
    # It is not the exponential running mean, which its setpoints read before
    assert np.abs(frame['PMOT'] - frame['RMOT']).max() > 1


def test_the_temperature_table_of_their_simulations():
    from accim.data.postprocessing.main import _running_mean_outputs

    assert _running_mean_outputs(['CS_IND IMAC R 30DRM'], ['CM_3']) == ['ASHRAE 55']
    assert _running_mean_outputs(['CS_IND IMAC R 7DRM'], ['CM_3']) == ['Tout_metric']
    # Comfort mode 1 of 9: the line of the Indian building code reads the mean of 30 days too
    assert _running_mean_outputs(['CS_IND IMAC R 7DRM'], ['CM_1']) == ['ASHRAE 55', 'Tout_metric']
    assert _running_mean_outputs(['CS_IND IMAC R 7DRM'], ['CM_0']) == ['ASHRAE 55']


# AddAccis and modify_accis --------------------------------------------------------------------------------------------

def _add_accis(folder, monkeypatch, **arguments):
    from accim.sim.accis import AddAccis

    folder.mkdir(exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    values = dict(script_type='vrf_mm', supply_air_temp_input_method='temperature difference', output_type='standard',
                  output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                  setpoint_type='temperature', comfort_standard=[9], category=[80], comfort_mode=[3],
                  hvac_mode=[2], ventilation_control=[0], confirm=True, verbose=False)
    values.update(arguments)
    AddAccis(**values)
    return {path.name: path for path in folder.glob('TestModel[[]*.idf')}


def _programs(idf):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
            for p in idf.idfobjects['EnergyManagementSystem:Program']}


def _metric_inputs(idf):
    from accim.sim.ems.inputs import input_programs, read_inputs

    return {zone: {name: read_inputs(program).get(name) for name in METRIC_INPUTS}
            for zone, program in input_programs(idf).items()}


def _start_warnings(caught):
    return [w for w in caught if 'begins with the running mean of ASHRAE 55' in str(w.message)]


@needs_idd
def test_add_accis_with_9_and_the_weather_file(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf
    from accim.sim.ems.outdoor_metric import begins_with_weather_file, has_outdoor_metric_code

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        written = _add_accis(tmp_path / 'model', monkeypatch, comfort_standard=[9, 10], epw=str(EPW))
    assert not _start_warnings(caught)
    names = sorted(written)
    assert [name.split('[')[1] for name in names] == ['CS_IND IMAC R 30DRM', 'CS_IND IMAC R 7DRM']
    thirty, seven = (load_idf(written[name]) for name in names)
    # 9: the EMS code of the outdoor metric, which begins with the values of the weather file, and its inputs
    assert has_outdoor_metric_code(seven) and begins_with_weather_file(seven)
    assert _metric_inputs(seven) == {zone: METRIC_INPUTS for zone in ZONES}
    programs = _programs(seven)
    assert programs['SetComfTemp'] == ['if ComfStand == 9', 'set ComfTemp = Tout_metric*0.39+18.42', 'endif']
    assert sorted(name for name in programs if name.startswith('SetAST_CS')) == ['SetAST_CS9_0', 'SetAST_CS9_1']
    assert programs['SetVST'].count('elseif ComfStand == 9') == 1
    for zone in ZONES:
        assert programs[f'CountHours_{zone}'][:2] == ['if ComfStand == 9',
                                                     'if (Tout_metric >= AHSTall) && (Tout_metric <= ACSTaul)']
        assert f'run SetOutdoorMetric_{zone}' in programs[f'RunACCIS_{zone}']
    assert seven.getobject('EnergyManagementSystem:OutputVariable', 'Tout_metric_Block1_Zone1') is not None
    # 10: PMOT, without that code, nor its inputs
    assert not has_outdoor_metric_code(thirty)
    assert _metric_inputs(thirty) == {zone: dict.fromkeys(METRIC_INPUTS) for zone in ZONES}
    programs = _programs(thirty)
    assert programs['SetComfTemp'] == ['if ComfStand == 10', 'set ComfTemp = PMOT*0.42+17.6', 'endif']
    assert 'elseif ComfStand == 9' not in programs['SetVST'] and 'elseif ComfStand == 1' in programs['SetVST']
    assert not any(re.search(r'\bRMOT\b', line) for name, lines in programs.items()
                   if name.startswith(('SetAST_CS', 'CountHours_')) for line in lines)


@needs_idd
def test_add_accis_with_9_without_the_weather_file_warns(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf
    from accim.sim.ems.outdoor_metric import begins_with_weather_file, has_outdoor_metric_code

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        written = _add_accis(tmp_path / 'model', monkeypatch, comfort_mode=[1],
                             # The outdoor metric of the custom model does not replace that of 9
                             custom_outdoor_metric='rmot_alpha', custom_alpha=0.7)
    [warning] = {str(w.message) for w in _start_warnings(caught)}
    assert "['ndrm']" in warning and 'argument epw' in warning and 'IND IMAC R 7DRM' in warning
    [path] = written.values()
    idf = load_idf(path)
    assert has_outdoor_metric_code(idf) and not begins_with_weather_file(idf)
    assert _metric_inputs(idf) == {zone: METRIC_INPUTS for zone in ZONES}


@needs_idd
def test_modify_accis_with_9(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf, modify_accis
    from accim.sim.ems.outdoor_metric import begins_with_weather_file, has_outdoor_metric_code

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        written = _add_accis(tmp_path / 'model', monkeypatch, comfort_standard=[1], category=[2])
    [path] = written.values()
    idf = load_idf(path)
    assert not has_outdoor_metric_code(idf)
    # A zone gets 9: the model gets its code and that of the outdoor metric, which begins with PMOT, with the warning
    with pytest.warns(UserWarning, match='begins with the running mean of ASHRAE 55'):
        modify_accis(idf, zone_arguments={'Block1:Zone1': {'comfort_standard': 9, 'category': 90, 'comfort_mode': 2}})
    assert has_outdoor_metric_code(idf) and not begins_with_weather_file(idf)
    programs = _programs(idf)
    assert programs['SetComfTemp'] == ['if ComfStand == 1', 'set ComfTemp = RMOT*0.33+18.8', 'elseif ComfStand == 9',
                                       'set ComfTemp = Tout_metric*0.39+18.42', 'endif']
    assert _metric_inputs(idf)['Block1_Zone1'] == METRIC_INPUTS
    assert _metric_inputs(idf)['Block1_Zone2']['CustAST_metric'] == 0
    # With the weather file, it begins with its values; the zone keeps its outdoor metric in the calls that do not
    # change its comfort standard, whatever the outdoor metric of the custom model that they give
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        modify_accis(idf, epw=str(EPW), custom_outdoor_metric='rmot_alpha', custom_alpha=0.7)
    assert not _start_warnings(caught)
    assert begins_with_weather_file(idf)
    assert _metric_inputs(idf) == {'Block1_Zone1': METRIC_INPUTS,
                                   'Block1_Zone2': {'CustAST_metric': 2, 'CustAST_alpha': 0.7, 'CustAST_days': 30}}
    # The zone leaves it for the custom model: it does not inherit the mean of 7 days ('pmot', its default)
    modify_accis(idf, zone_arguments={'Block1:Zone1': dict(
        comfort_standard=99, comfort_mode=3, custom_slope=0.3, custom_intercept=18, custom_cooling_offset=3,
        custom_heating_offset=-3, custom_cooling_upper_limit=30, custom_cooling_lower_limit=10,
        custom_heating_upper_limit=30, custom_heating_lower_limit=10)})
    assert _metric_inputs(idf)['Block1_Zone1'] == sdl.DEFAULT_METRIC_INPUTS
    # Back to 9, and then to the custom model with an outdoor metric given: that one
    modify_accis(idf, zone_arguments={'Block1:Zone1': {'comfort_standard': 9, 'category': 80, 'comfort_mode': 3}})
    assert _metric_inputs(idf)['Block1_Zone1'] == METRIC_INPUTS
    modify_accis(idf, zone_arguments={'Block1:Zone1': {'comfort_standard': 99, 'comfort_mode': 3,
                                                       'custom_outdoor_metric': 'daily_mean'}})
    assert _metric_inputs(idf)['Block1_Zone1'] == {'CustAST_metric': 4, 'CustAST_alpha': 0.8, 'CustAST_days': 7}


@needs_idd
def test_a_model_loses_the_outdoor_metric_code_when_its_zones_leave_9(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf, modify_accis
    from accim.sim.ems.outdoor_metric import has_outdoor_metric_code

    written = _add_accis(tmp_path / 'model', monkeypatch, epw=str(EPW))
    [path] = written.values()
    idf = load_idf(path)
    assert has_outdoor_metric_code(idf)
    modify_accis(idf, comfort_standard=2, category=80, comfort_mode=3)
    assert not has_outdoor_metric_code(idf)
    assert _metric_inputs(idf) == {zone: dict.fromkeys(METRIC_INPUTS) for zone in ZONES}
    programs = _programs(idf)
    assert 'set ComfTemp = PMOT*0.31+17.8' in programs['SetComfTemp']
    assert not any(name.startswith('SetOutdoorMetric') for name in programs)


@needs_idd
def test_the_models_of_add_accis_to_idf_get_the_code_of_the_outdoor_metric_with_9(tmp_path):
    from accim.sim.accis import add_accis_to_idf, load_idf, modify_accis
    from accim.sim.ems.outdoor_metric import has_outdoor_metric_code

    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    idf = load_idf(tmp_path / 'TestModel.idf')
    add_accis_to_idf(idf, script_type='vrf_mm', supply_air_temp_input_method='temperature difference',
                     output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                     setpoint_type='temperature', verbose=False)
    # The code of all the comfort standards: that of 9 reads Tout_metric, which no program calculates yet
    programs = _programs(idf)
    assert 'set ComfTemp = Tout_metric*0.39+18.42' in programs['SetComfTemp']
    assert programs['SetVST'].count('elseif ComfStand == 9') == 1 and not has_outdoor_metric_code(idf)
    with pytest.warns(UserWarning, match='begins with the running mean of ASHRAE 55'):
        modify_accis(idf, comfort_standard=9, category=80, comfort_mode=3)
    assert has_outdoor_metric_code(idf)
    assert _metric_inputs(idf) == {zone: METRIC_INPUTS for zone in ZONES}


# EnergyPlus -----------------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')


def _output_idf(folder, monkeypatch, begin, end, frequency, **arguments):
    """The output IDF of AddAccis of the sample model (mixed mode) with IND IMAC R 7DRM (category 80, comfort mode 3),
    whose input IDF has the run period given."""
    from accim.sim.accis import AddAccis, load_idf

    folder.mkdir(parents=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    model = load_idf(folder / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    model.save()
    monkeypatch.chdir(folder)
    values = dict(script_type='vrf_mm', supply_air_temp_input_method='temperature difference',
                  output_type='standard', output_frequencies=[frequency], keep_existing_outputs=False,
                  energyplus_version='auto', setpoint_type='temperature', comfort_standard=[9], category=[80],
                  comfort_mode=[3], hvac_mode=[2], ventilation_control=[0], confirm=True, verbose=False)
    values.update(arguments)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(**values)
    [path] = folder.glob('TestModel[[]*.idf')
    shutil.copy(path, folder / 'model.idf')
    return folder / 'model.idf'


def _run_energyplus(model, folder):
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    result = subprocess.run([str(energyplus), '-d', str(folder), '-p', 'run', '-s', 'C', '-r', '-x', '-w', str(EPW),
                             str(model)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    return pd.read_csv(folder / 'run.csv')


def _check_4(folder, model, capsys, rows, checks):
    from accim.utils.verification import verify_accim_simulation

    mismatches = verify_accim_simulation(str(folder / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0 or not mismatches['check'].str.match('Check4').any(), output
    for zone in ZONES:
        for check in checks:
            assert re.search(rf"'{zone}' {check} \(.*\): 0 mismatch\(es\) in {rows} timesteps", output), (zone, check)


@needs_energyplus
def test_comfort_standard_9_with_the_weather_file_in_energyplus(tmp_path, monkeypatch, capsys):
    # From 8 January (a run period that begins between the 2nd and the 30th of January), comfort mode 1 in the second
    # zone
    folder = tmp_path / 'weather'
    model = _output_idf(folder, monkeypatch, (1, 8), (1, 21), 'timestep', epw=str(EPW),
                        zone_arguments={'Block1:Zone2': {'comfort_mode': 1, 'category': 90}})
    results = _run_energyplus(model, folder / 'out')
    assert len(results) == 14 * 24 * STEPS
    _check_4(folder, model, capsys, 2016, ('Check4_ACST', 'Check4_AHST', 'Check4_ComfTemp', 'Check4_Tout_metric'))
    # The mean of the 7 previous days of the weather file, from the first timestep
    metric = results['EMS:Tout_metric_Block1_Zone1 [C](TimeStep)']
    expected = compute_setpoints(EPW, 9, 80, 3, frequency='timestep', start_date='08/01')
    np.testing.assert_allclose(metric.to_numpy(), expected['Tout_metric'].to_numpy()[:len(metric)], rtol=0, atol=1e-6)
    np.testing.assert_allclose(metric.to_numpy(), _mean_of_7_days(expected.iloc[:len(metric)]), rtol=0, atol=1e-6)
    comfort = results['EMS:Comfort Temperature_Block1_Zone1 [C](TimeStep)']
    np.testing.assert_allclose(comfort.to_numpy(), 0.39 * metric.to_numpy() + 18.42, rtol=0, atol=1e-6)


@needs_energyplus
def test_comfort_standard_9_without_the_weather_file_in_energyplus(tmp_path, monkeypatch, capsys):
    folder = tmp_path / 'pmot'
    model = _output_idf(folder, monkeypatch, (3, 1), (3, 10), 'timestep', comfort_mode=[1], category=[90])
    results = _run_energyplus(model, folder / 'out')
    assert len(results) == 10 * 24 * STEPS
    _check_4(folder, model, capsys, 1440, ('Check4_ACST', 'Check4_AHST', 'Check4_ComfTemp', 'Check4_Tout_metric'))
    # At the first timestep, out of the limits (the EMS reads PMOT = 0): the line of the Indian building code, with
    # the heating setpoint below the cooling setpoint
    cooling = results['EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_Block1_Zone1 [C](TimeStep)']
    heating = results['EMS:Adaptive Heating Setpoint Temperature_No Tolerance_Block1_Zone1 [C](TimeStep)']
    assert cooling.iloc[0] == pytest.approx(23.25 + 1.5) and heating.iloc[0] == pytest.approx(23.25 - 1.5)
    assert (cooling - heating).iloc[1:].to_numpy() == pytest.approx(2 * OFFSETS[90])


@needs_energyplus
def test_comfort_standard_10_in_energyplus(tmp_path, monkeypatch, capsys):
    folder = tmp_path / 'thirty'
    model = _output_idf(folder, monkeypatch, (1, 8), (1, 14), 'timestep', comfort_standard=[10], comfort_mode=[1])
    results = _run_energyplus(model, folder / 'out')
    assert len(results) == 7 * 24 * STEPS
    _check_4(folder, model, capsys, 1008, ('Check4_ACST', 'Check4_AHST', 'Check4_ComfTemp'))
    assert not [column for column in results if 'Tout_metric' in column]
    pmot = results[[c for c in results if 'ASHRAE 55 Adaptive Model Running Average Outdoor' in c][0]]
    comfort = results['EMS:Comfort Temperature_Block1_Zone1 [C](TimeStep)']
    # The EMS reads the PMOT of the previous timestep
    np.testing.assert_allclose(comfort.to_numpy()[1:], 0.42 * pmot.to_numpy()[:-1] + 17.6, rtol=0, atol=1e-6)


@needs_energyplus
@pytest.mark.parametrize('comfort_standard, arguments', [(9, {'epw': str(EPW)}), (9, {}), (10, {})])
def test_the_ems_and_api_backends_give_the_same_results(tmp_path, monkeypatch, comfort_standard, arguments):
    from accim.sim.energyplus_api import run_simulations

    model = _output_idf(tmp_path / 'model', monkeypatch, (6, 1), (6, 10), 'hourly',
                        comfort_standard=[comfort_standard], category=[90], comfort_mode=[1], **arguments)
    ems_results = _run_energyplus(model, tmp_path / 'ems')
    results = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    assert len(ems_results) == 10 * 24
    assert ('EMS:Tout_metric_Block1_Zone1 [C](Hourly)' in ems_results) == (comfort_standard == 9)
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
