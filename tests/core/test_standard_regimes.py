"""Tests for the comfort standards defined by their data with several regimes (task H5 of the review of accim 1.2.0,
decision 4 of section 6 of ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md``).

The key ``regimes`` of the YAML files (a list of regimes with the fields of :class:`accim.sim.arguments.CustomRegime`,
the last one 'always') replaces ``comfort_temperature`` and ``applicability``: the EMS code of the comfort standard
reads the inputs of the custom model, which the program of the regimes of each of its zones
(``SelectCustomRegime_<zone>``) sets in each timestep, and its outdoor metric is Tout_metric, so that a regime can have
its own. The unit tests compare its setpoints with those of the custom model with the same regimes (compute_setpoints);
the last tests simulate an output IDF of AddAccis with EnergyPlus 25.1 (verify_accim_simulation, and both backends).
"""
import copy
import dataclasses
import filecmp
import re
import warnings

import numpy as np
import pandas as pd
import pytest
import yaml

from accim.sim import standards as st
from accim.sim.arguments import CustomRegime
from accim.sim.ems import custom_regimes as cr
from accim.sim.ems import outdoor_metric as om
from accim.sim.ems import program_lines as pl
from accim.sim.ems import standard_lines as sdl
from accim.sim.ems.setast import MODULAR_COMFORT_MODES
from accim.sim.ems.setpoint_lines import SETPOINT_LINES
from accim.sim.preview import compute_setpoints
from accim.utils import get_setpoint_ems_code, get_setpoint_ems_programs

from .test_comfort_standard_registry import (AQILAH, EPW, STEPS, ZONES, _add_accis, _model, _output_idf, _programs,
                                             _run_energyplus, needs_energyplus, needs_idd)

SETPOINTS = ('Tout_metric', 'ComfTemp', 'ACST', 'AHST', 'ACSTnoTol', 'AHSTnoTol', 'applicable', 'custom_regime')
#: The regimes of the comfort standard of the tests: below 16 °C of its outdoor metric (the mean of the 7 previous
#: days of EN 16798-1, B.2), a comfort temperature of the daily mean of the previous day; otherwise, another one
COLD = {'slope': 0.5, 'intercept': 12, 'cooling_offset': 2, 'heating_offset': -2, 'cooling_lower_limit': 5,
        'cooling_upper_limit': 40, 'heating_lower_limit': 5, 'heating_upper_limit': 40,
        'condition': ['metric_below', 16], 'outdoor_metric': 'daily_mean'}
WARM = {'slope': 0.33, 'intercept': 18.8, 'cooling_offset': 3, 'heating_offset': -3, 'cooling_lower_limit': 10,
        'cooling_upper_limit': 30, 'heating_lower_limit': 10, 'heating_upper_limit': 30}
#: The scalar arguments of the custom model that the regimes replace
SCALAR = dict(custom_slope=0, custom_intercept=0, custom_cooling_offset=0, custom_heating_offset=0,
              custom_cooling_upper_limit=0, custom_cooling_lower_limit=0, custom_heating_upper_limit=0,
              custom_heating_lower_limit=0)


@pytest.fixture(autouse=True)
def empty_registry():
    """Each test begins without comfort standards in the registry, which is global, and leaves it as it was."""
    state = (dict(st.COMFORT_STANDARDS), copy.deepcopy(pl.REGISTERED_BRANCHES), dict(SETPOINT_LINES),
             copy.deepcopy(MODULAR_COMFORT_MODES))
    assert not st.registered_comfort_standards()
    yield
    for number in list(st.registered_comfort_standards()):
        st.unregister_comfort_standard(number)
    assert (dict(st.COMFORT_STANDARDS), pl.REGISTERED_BRANCHES, dict(SETPOINT_LINES), MODULAR_COMFORT_MODES) == state


def _data(**changes):
    """The data of the YAML file of JPN Aqilah 2025 as a comfort standard 150 with the regimes COLD and WARM, the
    outdoor metric 'rmot_7day', the category 80 without offsets and the comfort mode 3 (those of the custom model), with
    some changes (None removes a key)."""
    with open(AQILAH, encoding='utf-8') as stream:
        data = yaml.safe_load(stream)
    for key in ('comfort_temperature', 'applicability', 'alpha'):
        data.pop(key)
    data.update(number=150, label='Two regimes', title='150 = Two regimes', outdoor_metric='rmot_7day',
                categories={80: {'cooling_offset': 0, 'heating_offset': 0}}, comfort_modes=[3],
                regimes=[dict(COLD), dict(WARM)])
    for key, value in changes.items():
        if value is None:
            data.pop(key)
        else:
            data[key] = value
    return data


def _regimes(*regimes):
    """The regimes of the YAML files as CustomRegime."""
    return [CustomRegime(**{key: tuple(value) if isinstance(value, list) else value for key, value in regime.items()})
            for regime in regimes]


def _register(**changes):
    definition = st.definition_from_mapping(_data(**changes))
    st.register_comfort_standard(definition)
    return definition


# The definitions and the YAML files ----------------------------------------------------------------------------------

def test_a_yaml_file_with_regimes(tmp_path):
    path = tmp_path / 'two.yaml'
    path.write_text(yaml.safe_dump(_data()), encoding='utf-8')
    [definition] = st.load_comfort_standards(path, register=False)
    cold, warm = definition.regimes
    assert cold == CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16), 'daily_mean')
    assert warm == CustomRegime(0.33, 18.8, 3, -3, 10, 30, 10, 30)
    assert sdl.uses_regimes(definition) and sdl.needs_outdoor_metric_code(definition)
    assert definition.outdoor_metric == 'rmot_7day'
    # A comfort temperature and its applicability are a single regime 'always' (decision 4 of section 6 of v04)
    one = {**WARM, 'cooling_offset': 0, 'heating_offset': 0, 'cooling_lower_limit': 5, 'cooling_upper_limit': 30,
           'heating_lower_limit': 5, 'heating_upper_limit': 30}
    single = st.definition_from_mapping(_data(regimes=[one]))
    scalar = st.definition_from_mapping(_data(regimes=None, comfort_temperature={'slope': 0.33, 'intercept': 18.8},
                                              applicability={'metric_min': 5, 'metric_max': 30}))
    assert single == scalar and not sdl.uses_regimes(single)
    # Its EMS code does not change: that of a single regime
    assert sdl.standard_branches(single) == sdl.standard_branches(scalar)
    # A single regime with its own outdoor metric has the code of the regimes
    assert sdl.uses_regimes(st.definition_from_mapping(_data(regimes=[{**one, 'outdoor_metric': 'daily_mean'}])))
    # The conditions with a value (lists in YAML)
    between = st.definition_from_mapping(_data(regimes=[{**COLD, 'condition': ['metric_between', [10, 16]]}, WARM]))
    assert between.regimes[0].condition == ('metric_between', (10, 16))
    season = st.definition_from_mapping(_data(regimes=[{**COLD, 'condition': 'heating_season'}, WARM]))
    assert season.regimes[0].condition == 'heating_season'


@pytest.mark.parametrize('changes, message', [
    (dict(comfort_temperature={'slope': 0.33, 'intercept': 18.8}),
     re.escape("regimes replaces ['comfort_temperature', 'applicability']: give the regimes, or the comfort "
               "temperature and the applicability of one regime, not both (['comfort_temperature'] given).")),
    (dict(regimes={'slope': 0.33}), 'regimes must be a list of regimes'),
    (dict(regimes=[]), re.escape('regimes must be a list of regimes (mappings with the keys')),
    (dict(regimes=['always']), 'the regime 1 must be a mapping with the keys'),
    (dict(regimes=[{**WARM, 'colour': 'red'}]), 'the regime 1 must be a mapping with the keys'),
    (dict(regimes=[{key: value for key, value in WARM.items() if key != 'cooling_offset'}]),
     re.escape("the regime 1 needs ['cooling_offset'].")),
    (dict(regimes=[{**WARM, 'slope': 'high'}]), 'the regime 1: slope of a regime of the custom model must be a number'),
    (dict(regimes=[{**COLD, 'condition': ['metric_below']}, WARM]),
     re.escape("the regime 1: ('metric_below',) is not a condition of a regime")),
    (dict(regimes=[{**WARM, 'alpha': 0.7}]), 'the regime 1: alpha and days of a regime of the custom model are those '
                                            'of its outdoor_metric'),
    (dict(regimes=[dict(COLD)]), re.escape("must have at least one regime (a CustomRegime), the last one with the "
                                           "condition 'always'")),
    (dict(regimes=[dict(WARM), dict(COLD)]), "The regimes of the comfort standard 150: The regime 1 of custom_regimes "
                                             "has the condition 'always'"),
    (dict(regimes=[{**COLD, 'condition': 'hvac_off'}, WARM]),
     re.escape("The regimes [1] of the comfort standard 150 have the condition 'hvac_off' or 'hvac_on', which reads "
               "the HVAC system of the model (mixed mode), not the comfort model")),
])
def test_the_regimes_of_a_yaml_file_are_checked(changes, message):
    with pytest.raises(ValueError) as error:
        st.definition_from_mapping(_data(**changes), 'two.yaml')
    # The message names the file
    assert str(error.value).startswith('two.yaml: ') and re.search(message, str(error.value)), str(error.value)


def test_the_regimes_of_a_definition_are_checked():
    definition = st.definition_from_mapping(_data())
    cold, warm = definition.regimes
    with pytest.raises(ValueError, match="the last one with the condition 'always'"):
        dataclasses.replace(definition, regimes=(cold,))
    with pytest.raises(ValueError, match=r"The regimes \[1\] of the comfort standard 150 have the condition "
                                         r"'hvac_off'"):
        dataclasses.replace(definition, regimes=(dataclasses.replace(cold, condition='hvac_on'), warm))
    with pytest.raises(ValueError, match='The regimes of the comfort standard 150: custom_regimes must be a list of '
                                         'CustomRegime'):
        dataclasses.replace(definition, regimes=('always',))


# The EMS code ---------------------------------------------------------------------------------------------------------

def test_the_erl_lines_of_a_comfort_standard_with_regimes():
    definition = _register()
    assert sdl.regime_standards() == {150} and sdl.standard_metric_variable(definition) == 'Tout_metric'
    branches = sdl.standard_branches(definition)
    # The inputs of the custom model, which the program of the regimes sets
    assert branches['SetComfTemp'] == ('elseif ComfStand == 150', 'set ComfTemp = Tout_metric*m+n')
    assert branches['SetAppLimits'][1:] == ('set ACSTaul = CustAST_ACSTaul', 'set ACSTall = CustAST_ACSTall',
                                            'set AHSTaul = CustAST_AHSTaul', 'set AHSTall = CustAST_AHSTall')
    assert branches['ApplyCAT'][1:] == ('if (CAT == 80)', 'set ACSToffset = 0+CustAST_ACSToffset+CATcoolOffset',
                                        'set AHSToffset = 0+CustAST_AHSToffset+CATheatOffset', 'endif')
    assert 'if (Tout_metric >= AHSTall) && (Tout_metric <= ACSTaul)' in branches['SetVST']
    assert sdl.setpoint_lines(definition)[3][:6] == (
        'if (Tout_metric >= ACSTall) && (Tout_metric <= ACSTaul)', 'set ACST = Tout_metric*m+n+ACSToffset+ACSTtol',
        'elseif Tout_metric < ACSTall', 'set ACST = ACSTall*m+n+ACSToffset+ACSTtol', 'elseif Tout_metric > ACSTaul',
        'set ACST = ACSTaul*m+n+ACSToffset+ACSTtol')
    # Its zones have the inputs of its outdoor metric
    assert sdl.standard_inputs(definition) == {'CustAST_metric': 3, 'CustAST_alpha': 0.8, 'CustAST_days': 30}
    assert cr.standard_regimes(150) == definition.regimes and cr.standard_regimes(1) is None
    # With 'pmot' and regimes without their own outdoor metric, the code reads Tout_metric too (PMOT, from the EMS
    # code of the outdoor metric)
    st.unregister_comfort_standard(150)
    pmot = _register(outdoor_metric='pmot', regimes=[{**COLD, 'outdoor_metric': None}, WARM])
    assert sdl.needs_outdoor_metric_code(pmot) and sdl.standard_inputs(pmot)['CustAST_metric'] == 0
    assert sdl.standard_branches(pmot)['SetComfTemp'][1] == 'set ComfTemp = Tout_metric*m+n'


def test_the_ems_code_of_a_comfort_standard_with_regimes():
    _register()
    code = get_setpoint_ems_code(150, 80, 3)
    assert '! Outdoor metric: rmot_7day, in the EMS Tout_metric' in code
    assert ('!     1 = metric_below 16: slope 0.5, intercept 12, offsets 2 (cooling) and -2 (heating), applicability 5 '
            'to 40 (cooling) and 5 to 40 (heating), outdoor metric daily_mean') in code
    assert ('! --- SelectCustomRegime_<zone>: the regime of the comfort standard of the timestep (1 = metric_below 16, '
            '2 = always), which sets the inputs of the custom model ---') in code
    programs = get_setpoint_ems_programs(150, 80, 3)
    assert list(programs)[:5] == ['InitOutdoorMetric', 'SetOutdoorMetric', 'SetInputData_<zone>',
                                  'SetOutdoorMetric_<zone>', 'SelectCustomRegime_<zone>']
    assert programs['SelectCustomRegime_<zone>'] == cr.regime_program_lines('<zone>', _regimes(COLD, WARM),
                                                                             'Tout_metric')
    assert 'set ToutRegime_1_<zone> = Tday_1' in programs['SetOutdoorMetric_<zone>']
    # custom_regimes is that of the custom model
    with pytest.raises(ValueError, match='custom_regimes needs the custom model'):
        get_setpoint_ems_code(150, 80, 3, custom_regimes=_regimes(WARM))


@pytest.mark.parametrize('offsets', [(0, 0), (1.5, -2.5)])
def test_compute_setpoints_of_a_comfort_standard_with_regimes(offsets):
    # The setpoints of the comfort standard are those of the custom model with the same regimes (plus the offsets of
    # the category)
    _register(categories={80: {'cooling_offset': offsets[0], 'heating_offset': offsets[1]}})
    arguments = dict(frequency='timestep', start_date='01/03')
    standard = compute_setpoints(EPW, 150, 80, 3, **arguments)
    shifted = [dataclasses.replace(regime, cooling_offset=regime.cooling_offset + offsets[0],
                                   heating_offset=regime.heating_offset + offsets[1])
               for regime in _regimes(COLD, WARM)]
    custom = compute_setpoints(EPW, 99, 80, 3, custom_outdoor_metric='rmot_7day', custom_regimes=shifted, **SCALAR,
                               **arguments)
    assert list(standard.columns) == list(custom.columns)
    assert set(standard['custom_regime']) == {1, 2}
    for column in SETPOINTS:
        np.testing.assert_array_equal(standard[column].to_numpy(), custom[column].to_numpy(), err_msg=column)


def test_compute_setpoints_of_a_comfort_standard_with_pmot_and_regimes():
    # The outdoor metric 'pmot', and regimes without their own: the setpoints of the custom model with PMOT
    _register(outdoor_metric='pmot', regimes=[{**COLD, 'outdoor_metric': None, 'condition': 'heating_season'}, WARM])
    arguments = dict(frequency='timestep', start_date='01/04')
    standard = compute_setpoints(EPW, 150, 80, 3, cooling_season_start='15/05', **arguments)
    custom = compute_setpoints(EPW, 99, 80, 3, cooling_season_start='15/05', **SCALAR, **arguments,
                               custom_regimes=_regimes({**COLD, 'outdoor_metric': None, 'condition': 'heating_season'},
                                                       WARM))
    # Tout_metric is the sensor PMOT, whose value in the first timestep of each day is that of the previous day (0 in
    # the run period), as in EnergyPlus; the custom model without the EMS code of the outdoor metric reports the
    # daily PMOT
    daily = standard['PMOT'].to_numpy()
    first = np.arange(len(standard)) % (24 * 6) == 0
    np.testing.assert_array_equal(standard['Tout_metric'].to_numpy(), np.where(first, np.r_[0.0, daily[:-1]], daily))
    assert set(standard['custom_regime']) == {1, 2}
    for column in SETPOINTS[1:]:
        np.testing.assert_array_equal(standard[column].to_numpy(), custom[column].to_numpy(), err_msg=column)


# AddAccis, modify_accis -----------------------------------------------------------------------------------------------

@needs_idd
def test_add_accis_with_a_comfort_standard_with_regimes(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf

    reference = _add_accis(tmp_path / 'reference', monkeypatch)
    definition = _register()
    written = _add_accis(tmp_path / 'registry', monkeypatch, comfort_standard=[1, 150], category=[1, 80],
                         comfort_mode=[3], epw=str(EPW))
    # The output IDFs of the built-in comfort standards are those without the registry
    for name in [name for name in reference if '[CM_3' in name]:
        assert filecmp.cmp(reference[name], written[name], shallow=False), name
    [name] = [name for name in written if 'CS_Two regimes' in name]
    idf = load_idf(written[name])
    programs = _programs(idf)
    assert programs['SetComfTemp'] == ['if ComfStand == 150', 'set ComfTemp = Tout_metric*m+n', 'endif']
    # Its zones have the program of its regimes, whose conditions compare its outdoor metric, which begins with the
    # weather file
    assert cr.custom_regimes_of(idf) == {zone: definition.regimes for zone in ZONES}
    assert om.has_outdoor_metric_code(idf) and om.begins_with_weather_file(idf)
    assert om.zone_regime_metrics(idf) == {zone: {1: (4, None, None)} for zone in ZONES}
    for zone in ZONES:
        assert programs[f'SelectCustomRegime_{zone}'][0] == 'if Tout_metric < 16'
        assert f'run SelectCustomRegime_{zone}' in programs[f'RunACCIS_{zone}']
    # A comfort standard with 'pmot' and regimes without their own outdoor metric has the EMS code of the outdoor
    # metric too (its code reads Tout_metric)
    st.unregister_comfort_standard(150)
    _register(outdoor_metric='pmot', regimes=[{**COLD, 'outdoor_metric': None}, WARM])
    [path] = _add_accis(tmp_path / 'pmot', monkeypatch, comfort_standard=[150], category=[80],
                        comfort_mode=[3]).values()
    idf = load_idf(path)
    assert om.has_outdoor_metric_code(idf) and not om.zone_regime_metrics(idf)
    assert _programs(idf)[f'SelectCustomRegime_{ZONES[0]}'][0] == 'if Tout_metric < 16'


@needs_idd
def test_modify_accis_with_a_comfort_standard_with_regimes(tmp_path):
    from accim.sim.accis import modify_accis
    from accim.sim.ems.inputs import input_programs, read_inputs

    idf = _model(tmp_path)
    definition = _register()
    modify_accis(idf, comfort_standard=150, category=80, comfort_mode=3, epw=str(EPW))
    assert cr.custom_regimes_of(idf) == {zone: definition.regimes for zone in ZONES}
    assert om.has_outdoor_metric_code(idf) and om.begins_with_weather_file(idf)
    assert all(read_inputs(program)['CustAST_metric'] == 3 for program in input_programs(idf).values())
    # The zones that keep it keep its regimes, and the programs of the outdoor metric, which calculate those of the
    # regimes, keep the values of the weather file with which they begin
    programs = _programs(idf)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        modify_accis(idf, setpoint_tolerance=0.2)
    assert cr.custom_regimes_of(idf) == {zone: definition.regimes for zone in ZONES}
    assert all(_programs(idf)[name] == lines for name, lines in programs.items() if 'OutdoorMetric' in name)
    # A zone that gets another comfort standard loses them; the programs of the outdoor metric are written again
    with pytest.warns(UserWarning, match='written again with the outdoor metrics of its regimes, beginning with the '
                                         'running mean of ASHRAE 55'):
        modify_accis(idf, zone_arguments={'Block1:Zone2': dict(comfort_standard=3, category=80, comfort_mode=1)})
    assert cr.custom_regimes_of(idf) == {ZONES[0]: definition.regimes}
    assert om.zone_regime_metrics(idf) == {ZONES[0]: {1: (4, None, None)}}
    # Also the custom model, whose regimes are those of custom_regimes
    regimes = _regimes({**COLD, 'outdoor_metric': None}, WARM)
    modify_accis(idf, comfort_standard=99, comfort_mode=3, zone_arguments={'Block1:Zone2': dict(comfort_standard=150)},
                 custom_regimes=regimes, **SCALAR)
    assert cr.custom_regimes_of(idf) == {ZONES[0]: tuple(regimes), ZONES[1]: definition.regimes}
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        modify_accis(idf, comfort_standard=99, comfort_mode=3)
    assert cr.custom_regimes_of(idf) == {ZONES[0]: tuple(regimes)}
    # The zones that leave the custom model keep its regimes, unless they have their own outdoor metric (which would
    # replace the outdoor metric of the zone that other comfort standards read)
    modify_accis(idf, comfort_standard=1, category=1, comfort_mode=3)
    assert cr.custom_regimes_of(idf) == {ZONES[0]: tuple(regimes)}
    own = _regimes(COLD, WARM)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        modify_accis(idf, comfort_standard=99, comfort_mode=3, custom_regimes=own, **SCALAR)
    assert cr.custom_regimes_of(idf) == {zone: tuple(own) for zone in ZONES}
    assert om.zone_regime_metrics(idf) == {zone: {1: (4, None, None)} for zone in ZONES}
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        modify_accis(idf, comfort_standard=1, category=1, comfort_mode=3)
    assert not cr.custom_regimes_of(idf) and not om.zone_regime_metrics(idf)
    # The zones keep the outdoor metric of the comfort standard that they had (CustAST_metric 3, 'rmot_7day'), whose
    # programs no longer calculate those of the regimes
    assert all(read_inputs(program)['CustAST_metric'] == 3 for program in input_programs(idf).values())
    assert om.has_outdoor_metric_code(idf)
    assert not any(line.startswith('set ToutRegime_') for lines in _programs(idf).values() for line in lines)


# EnergyPlus ---------------------------------------------------------------------------------------------------------

@needs_energyplus
def test_a_comfort_standard_with_regimes_in_energyplus(tmp_path, monkeypatch, capsys):
    from accim.sim.energyplus_api import run_simulations
    from accim.utils.verification import verify_accim_simulation

    # The outdoor metric of the comfort standard is 'rmot_7day' (16.1 to 17.7 °C in 1-7 April in Seville); below
    # 16.5 °C of it, the daily mean of the previous day
    _register(regimes=[{**COLD, 'condition': ['metric_below', 16.5]}, WARM],
              categories={80: {'cooling_offset': 1, 'heating_offset': -1}})
    model = _output_idf(tmp_path / 'april', monkeypatch, (4, 1), (4, 7), 'timestep', comfort_standard=[150],
                        category=[80], comfort_mode=[3])
    results = _run_energyplus(model, tmp_path / 'april' / 'out')
    assert len(results) == 7 * 24 * STEPS
    # The setpoints, the outdoor metric and the regimes are those of compute_setpoints (check 4)
    mismatches = verify_accim_simulation(str(tmp_path / 'april' / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0 or not mismatches['check'].str.match('Check4').any()
    for zone in ZONES:
        for check in ('Check4_custom_regime', 'Check4_Tout_metric', 'Check4_ACST', 'Check4_AHST', 'Check4_ComfTemp'):
            assert re.search(rf"'{zone}' {check} \(.*\): 0 mismatch\(es\) in 1008 timesteps", output), (zone, check)
        assert set(results[f'EMS:CustomRegime_{zone} [](TimeStep)']) == {1, 2}
    # Both backends give the same results
    api = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})], processes=1)
    assert api[0].success, api[0].error
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / 'api' / 'run.csv'), results, check_exact=True)
