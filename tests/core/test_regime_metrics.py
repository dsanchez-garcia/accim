"""Tests for the outdoor metric of each regime of the custom model (task H5 of the review of accim 1.2.0, decision 1
of section 6 of ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md``).

The conditions of the regimes compare the outdoor metric of the zone (``custom_outdoor_metric``); a regime with its own
outdoor metric (``outdoor_metric``, ``alpha`` and ``days`` of :class:`accim.sim.arguments.CustomRegime`) calculates its
comfort temperature, setpoints and applicability with it: the program of the outdoor metric of the zone calculates it
in each timestep (``ToutRegime_<regime>_<zone>``), and the program of the regimes gives it to ``Tout_metric``. The unit
tests run the programs with the Erl interpreter of accim (compute_setpoints): a regime 'always' with its own metric
gives the setpoints of the zone with that metric. The last tests simulate an output IDF of AddAccis with EnergyPlus
25.1 (verify_accim_simulation, and both backends).
"""
import re
import warnings

import numpy as np
import pandas as pd
import pytest

from accim.sim.arguments import CustomRegime
from accim.sim.ems import custom_regimes as cr
from accim.sim.ems import outdoor_metric as om
from accim.sim.preview import compute_setpoints
from accim.utils import get_setpoint_ems_code, get_setpoint_ems_programs

from .test_custom_regimes import (EPW, SCALAR, SCALAR_REGIME, STEPS, WARM, ZONES, _add_accis, _arguments, _model,
                                  _output_idf, _programs, _run_energyplus, needs_energyplus, needs_idd)

SETPOINTS = ('Tout_metric', 'ComfTemp', 'ACST', 'AHST', 'ACSTnoTol', 'AHSTnoTol', 'applicable')
#: The outdoor metrics of a regime, with their alpha and days, and the arguments of the zone with the same metric
METRICS = {
    'rmot': ({}, {}),
    'rmot_alpha': ({'alpha': 0.7}, {'custom_alpha': 0.7}),
    'rmot_7day': ({}, {}),
    'daily_mean': ({}, {}),
    'ndrm': ({'days': 7}, {'custom_days': 7}),
    'monthly_mean': ({}, {}),
    'te_ref_nl': ({}, {}),
}


def _regime(regime, outdoor_metric, **metric):
    return CustomRegime(regime.slope, regime.intercept, regime.cooling_offset, regime.heating_offset,
                        regime.cooling_lower_limit, regime.cooling_upper_limit, regime.heating_lower_limit,
                        regime.heating_upper_limit, regime.condition, outdoor_metric, **metric)


def test_the_program_of_the_regimes_with_their_outdoor_metrics():
    own = _regime(CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16)), 'rmot_alpha', alpha=0.7)
    middle = CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, ('metric_above', 25))
    days = _regime(WARM, 'ndrm', days=7)
    lines = cr.regime_program_lines('Z', [own, middle, days], 'Tout_metric')
    assert lines[0] == 'if Tout_metric < 16'
    # The inputs of its metric, and Tout_metric from the program of the outdoor metric of the zone
    assert lines[9:13] == ['set CustAST_metric = 2', 'set CustAST_alpha = 0.7', 'set Tout_metric = ToutRegime_1_Z',
                           'set CustomRegime_Z = 1']
    assert 'set CustAST_days = 7' in lines and 'set Tout_metric = ToutRegime_3_Z' in lines
    assert 'set Tout_metric = ToutRegime_2_Z' not in lines
    # After the chain, the output of the outdoor metric of the zone is that of the regime of the timestep
    assert lines[-2:] == ['endif', 'set Tout_metric_Z = Tout_metric']
    assert cr.regime_metrics([own, middle, days]) == {1: (2, 0.7, None), 3: (5, None, 7)}
    # The regimes come back from the lines (as the parametric module and verify_accim_simulation read them)
    assert cr.parse_regime_program(lines, 'Z') == (own, middle, days)
    single = cr.regime_program_lines('Z', [_regime(SCALAR_REGIME, 'daily_mean')], 'PMOT')
    assert single[-3:] == ['set Tout_metric = ToutRegime_1_Z', 'set CustomRegime_Z = 1',
                           'set Tout_metric_Z = Tout_metric']
    assert cr.parse_regime_program(single, 'Z') == (_regime(SCALAR_REGIME, 'daily_mean'),)
    # Without the regimes with their own metric, the lines of before
    assert cr.regime_program_lines('Z', [WARM]) == cr.regime_program_lines('Z', [WARM], 'Tout_metric')
    assert not any('Tout_metric' in line for line in cr.regime_program_lines('Z', [WARM]))
    # Lines that are not those of accim
    for wrong, message in ((lines[:-1], 'does not set the output of the outdoor metric of the zone'),
                           ([line for line in lines if line != 'set Tout_metric = ToutRegime_1_Z'],
                            'sets its outdoor metric without Tout_metric'),
                           ([line for line in lines if line != 'set CustAST_metric = 2'],
                            'sets Tout_metric without its outdoor metric'),
                           (lines[:3] + ['set Other = 1'] + lines[3:], r"sets \['other'\]")):
        with pytest.raises(ValueError, match=message):
            cr.parse_regime_program(wrong, 'Z')


def test_the_program_of_the_outdoor_metric_calculates_those_of_the_regimes():
    specs = {1: (2, 0.7, None), 2: (2, None, None), 3: (5, None, 7), 4: (5, None, None), 5: (1, None, None),
             6: (7, None, None)}
    lines = om.zone_program_lines('Z', 30, regime_metrics=specs)
    # Those of the zone do not change (but for those of the running mean of the regime with its own alpha)
    zone = om.zone_program_lines('Z', 30)
    assert [line for line in lines if 'RMOTr_' not in line][:len(zone)] == zone
    assert 'set ToutRegime_1_Z = RMOTr_1_Z' in lines and 'set ToutRegime_2_Z = RMOTa_Z' in lines
    assert 'set ToutRegime_3_Z = (Tday_1+Tday_2+Tday_3+Tday_4+Tday_5+Tday_6+Tday_7)/7' in lines
    assert 'set ToutRegime_4_Z = OutdoorDaysSum/CustAST_days' in lines and 'set ToutRegime_5_Z = RMOT' in lines
    # The running mean of the regime with its own alpha: initialised and updated with the others
    assert 'set RMOTr_1_Z = PMOT' in lines and 'set RMOTr_1_Z = (1-0.7)*Tday_1+0.7*RMOTr_1_Z' in lines
    assert om.init_program_lines(['Z'], 30, {'Z': specs})[-1] == 'set RMOTr_1_Z = 0'
    assert om.global_variables(30, ['Z'], {'Z': specs})[-7:] == [
        'ToutRegime_1_Z', 'ToutRegime_2_Z', 'ToutRegime_3_Z', 'ToutRegime_4_Z', 'ToutRegime_5_Z', 'ToutRegime_6_Z',
        'RMOTr_1_Z']
    # The days of the regimes are kept
    programs = get_setpoint_ems_programs(99, 80, 3, custom_regimes=[_regime(WARM, 'ndrm', days=40)], **SCALAR)
    assert any(line.startswith('set Tday_40 = Tday_39') for line in programs[om.PROGRAM])
    # The EMS code of the setpoints of a regime with its own metric has the programs of the outdoor metric (the zone
    # has 'pmot'), and says what they are
    code = get_setpoint_ems_code(99, 80, 3, custom_regimes=[_regime(WARM, 'rmot_7day')], **SCALAR)
    assert 'SetOutdoorMetric_<zone>' in code and 'set ToutRegime_1_<zone> = (Tday_1+0.8*Tday_2' in code
    assert 'Tout_metric to ToutRegime_<regime>_<zone>, which\n! SetOutdoorMetric_<zone> calculates.' in code
    with pytest.raises(ValueError, match="'monthly_mean' needs the weather file of the simulations"):
        get_setpoint_ems_programs(99, 80, 3, custom_regimes=[_regime(WARM, 'monthly_mean')], **SCALAR)


@pytest.mark.parametrize('metric', list(METRICS))
def test_a_regime_always_with_its_metric_is_the_zone_with_that_metric(metric):
    # The setpoints of the custom model with a regime 'always' with its own outdoor metric (the zone has 'pmot') are
    # those of the zone with that metric
    own, zone = METRICS[metric]
    arguments = dict(frequency='timestep', start_date='01/11', **SCALAR)
    regime = compute_setpoints(EPW, 99, 80, 3, custom_regimes=[_regime(SCALAR_REGIME, metric, **own)], **arguments)
    expected = compute_setpoints(EPW, 99, 80, 3, custom_outdoor_metric=metric, **dict(arguments, **zone))
    assert (regime['custom_regime'] == 1).all()
    for column in SETPOINTS:
        np.testing.assert_array_equal(regime[column].to_numpy(), expected[column].to_numpy(), err_msg=column)


def test_the_conditions_compare_the_metric_of_the_zone():
    # The zone has 'rmot_7day'; the first regime applies below 16 °C of it, with the daily mean of the previous day
    cold = _regime(CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16)), 'daily_mean')
    arguments = dict(frequency='timestep', start_date='01/03', **SCALAR)
    result = compute_setpoints(EPW, 99, 80, 3, custom_outdoor_metric='rmot_7day', custom_regimes=[cold, WARM],
                               **arguments)
    zone = compute_setpoints(EPW, 99, 80, 3, custom_outdoor_metric='rmot_7day', **arguments)
    daily = compute_setpoints(EPW, 99, 80, 3, custom_outdoor_metric='daily_mean', **dict(arguments, **_arguments(cold)))
    warm = compute_setpoints(EPW, 99, 80, 3, custom_outdoor_metric='rmot_7day', **dict(arguments, **_arguments(WARM)))
    expected = np.where(zone['Tout_metric'] < 16, 1, 2)
    np.testing.assert_array_equal(result['custom_regime'], expected)
    assert set(expected) == {1, 2}
    # The outdoor metric and the setpoints of each regime
    for column in SETPOINTS:
        np.testing.assert_array_equal(result[column], np.where(expected == 1, daily[column], warm[column]),
                                      err_msg=column)


# The model ---------------------------------------------------------------------------------------------------------

@needs_idd
def test_add_accis_with_the_outdoor_metrics_of_the_regimes(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf

    regimes = [_regime(CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16)), 'rmot_alpha', alpha=0.7),
               _regime(WARM, 'ndrm', days=7)]
    outputs = _add_accis(tmp_path / 'regimes', monkeypatch, comfort_standard=[99], category=[80],
                         custom_regimes=regimes, epw=str(EPW))
    [idf] = [load_idf(path) for path in outputs.values()]
    # The zones have 'pmot', but the regimes need the EMS code of the outdoor metric, which begins with the weather file
    assert om.has_outdoor_metric_code(idf) and om.begins_with_weather_file(idf)
    assert cr.custom_regimes_of(idf) == {zone: tuple(regimes) for zone in ZONES}
    assert om.zone_regime_metrics(idf) == {zone: {1: (2, 0.7, None), 2: (5, None, 7)} for zone in ZONES}
    declared = {str(name).strip() for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
                for name in g.fieldvalues[1:] if str(name).strip()}
    for zone in ZONES:
        program = _programs(idf)[f'SetOutdoorMetric_{zone}']
        assert f'set ToutRegime_2_{zone} = (Tday_1+Tday_2+Tday_3+Tday_4+Tday_5+Tday_6+Tday_7)/7' in program
        # The running mean with the alpha of the regime begins with the weather file
        assert any(re.fullmatch(rf'set RMOTr_1_{zone} = \d+\.\d+', line) for line in program)
        assert {f'ToutRegime_1_{zone}', f'ToutRegime_2_{zone}', f'RMOTr_1_{zone}'} <= declared
        assert _programs(idf)[f'SelectCustomRegime_{zone}'][0] == 'if Tout_metric < 16'
    # 'monthly_mean' of a regime needs the weather file
    with pytest.raises(ValueError, match="The outdoor metric 'monthly_mean' of a regime of custom_regimes needs the "
                                         "weather file"):
        _add_accis(tmp_path / 'monthly', monkeypatch, comfort_standard=[99], category=[80],
                   custom_regimes=[_regime(WARM, 'monthly_mean')])


@needs_idd
def test_modify_accis_with_the_outdoor_metrics_of_the_regimes(tmp_path):
    from accim.sim.accis import modify_accis

    idf = _model(tmp_path)
    modify_accis(idf, comfort_standard=99, category=80, comfort_mode=3, **SCALAR)
    assert not om.has_outdoor_metric_code(idf)
    regimes = [_regime(CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16)), 'rmot_7day'), WARM]
    with pytest.warns(UserWarning, match='begins with the running mean of ASHRAE 55'):
        modify_accis(idf, custom_regimes=regimes, **SCALAR)
    assert om.has_outdoor_metric_code(idf) and cr.custom_regimes_of(idf) == {zone: tuple(regimes) for zone in ZONES}
    assert om.zone_regime_metrics(idf) == {zone: {1: (3, None, None)} for zone in ZONES}
    # The regimes without their own metric: the zones have 'pmot', so the EMS code of the outdoor metric goes
    modify_accis(idf, custom_regimes=[WARM], **SCALAR)
    assert not om.has_outdoor_metric_code(idf)
    assert _programs(idf)['SelectCustomRegime_Block1_Zone1'] == cr.regime_program_lines('Block1_Zone1', [WARM])
    with pytest.raises(ValueError, match="'monthly_mean' needs the weather file of the simulation"):
        modify_accis(idf, custom_regimes=[_regime(WARM, 'monthly_mean')], **SCALAR)


@needs_idd
def test_the_programs_of_the_outdoor_metric_of_the_regimes_keep_the_weather_file(tmp_path):
    from accim.sim.accis import modify_accis

    idf = _model(tmp_path)
    regimes = [_regime(CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16)), 'rmot_alpha', alpha=0.7),
               WARM]
    modify_accis(idf, comfort_standard=99, category=80, comfort_mode=3, custom_regimes=regimes, epw=str(EPW), **SCALAR)
    assert om.begins_with_weather_file(idf)
    programs = {name: lines for name, lines in _programs(idf).items() if 'OutdoorMetric' in name}
    # Other arguments, or the same regimes: the programs calculate the outdoor metrics of the regimes, so they stay,
    # with the values of the weather file with which they begin
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        modify_accis(idf, setpoint_tolerance=0.2)
        modify_accis(idf, custom_regimes=regimes, **SCALAR)
    assert {name: lines for name, lines in _programs(idf).items() if 'OutdoorMetric' in name} == programs
    # Other outdoor metrics of the regimes: the programs are written again, beginning with PMOT without the weather file
    with pytest.warns(UserWarning, match='written again with the outdoor metrics of its regimes'):
        modify_accis(idf, custom_regimes=[_regime(WARM, 'ndrm', days=7)], **SCALAR)
    assert not om.begins_with_weather_file(idf)
    assert om.zone_regime_metrics(idf) == {zone: {1: (5, None, 7)} for zone in ZONES}


# EnergyPlus ---------------------------------------------------------------------------------------------------------

@needs_energyplus
def test_the_outdoor_metrics_of_the_regimes_in_energyplus(tmp_path, monkeypatch, capsys):
    from accim.sim.energyplus_api import run_simulations
    from accim.utils.verification import verify_accim_simulation

    # The zones have 'rmot_7day' (16.1 to 17.7 °C in 1-7 April in Seville); below 16.5 °C of it, the running mean of
    # EN 16798-1 with alpha 0.7, and otherwise the mean of the 7 previous days (ASHRAE 55)
    regimes = [_regime(CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16.5)), 'rmot_alpha', alpha=0.7),
               _regime(WARM, 'ndrm', days=7)]
    model = _output_idf(tmp_path / 'april', monkeypatch, (4, 1), (4, 7), 'timestep', custom_outdoor_metric='rmot_7day',
                        epw=str(EPW), custom_regimes=regimes)
    results = _run_energyplus(model, tmp_path / 'april' / 'out')
    assert len(results) == 7 * 24 * STEPS
    # The setpoints, the outdoor metric and the regimes are those of compute_setpoints (check 4)
    mismatches = verify_accim_simulation(str(tmp_path / 'april' / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0 or not mismatches['check'].str.match('Check4').any()
    for zone in ZONES:
        for check in ('Check4_custom_regime', 'Check4_Tout_metric', 'Check4_ACST', 'Check4_AHST', 'Check4_ComfTemp'):
            assert re.search(rf"'{zone}' {check} \(.*\): 0 mismatch\(es\) in 1008 timesteps", output), (zone, check)
        found = results[f'EMS:CustomRegime_{zone} [](TimeStep)']
        assert set(found) == {1, 2}
    # Both backends give the same results
    api = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})], processes=1)
    assert api[0].success, api[0].error
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / 'api' / 'run.csv'), results, check_exact=True)
