"""Tests for the regimes of the custom comfort model (proposal B2, :mod:`accim.sim.ems.custom_regimes`).

``custom_regimes`` is a list of :class:`accim.sim.arguments.CustomRegime`, each one with the coefficients of the custom
model (comfort standard 99) and the condition under which they apply; the order of the list is the priority (decision
D6 of the brief of 1.2.0), and the scalar arguments (``custom_slope``...) apply when no condition holds. The program
``SelectCustomRegime_<zone>`` sets the inputs of the custom model of the zone before SetAppLimits, so the programs of
the custom model do not change, and the output IDFs without regimes are those of accim 1.1.0. The unit tests run the
programs with the Erl interpreter of accim (compute_setpoints); the last tests simulate output IDFs of AddAccis with
EnergyPlus 25.1 (verify_accim_simulation, the condition 'hvac_off' in mixed mode, and both backends).
"""
import pickle
import re
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim.arguments import METRIC_CONDITIONS, REGIME_CONDITIONS, CustomRegime, check_custom_regimes
from accim.sim.ems import custom_regimes as cr
from accim.sim.ems import program_lines as pl
from accim.sim.ems.erl import ErlProgramSet
from accim.sim.ems.setast import COOLING_SEASON_LINES
from accim.sim.preview import compute_setpoints
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
ZONES = ['Block1_Zone1', 'Block1_Zone2']
STEPS = 6
#: The scalar arguments of the custom model (those of ASHRAE 55 with 80 % acceptability)
SCALAR = dict(custom_slope=0.31, custom_intercept=17.8, custom_cooling_offset=3.5, custom_heating_offset=-3.5,
              custom_cooling_lower_limit=10, custom_cooling_upper_limit=33.5, custom_heating_lower_limit=10,
              custom_heating_upper_limit=33.5)
#: The same as a regime
SCALAR_REGIME = CustomRegime(0.31, 17.8, 3.5, -3.5, 10, 33.5, 10, 33.5)
#: Two regimes with other coefficients
COLD = CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16))
WARM = CustomRegime(0.33, 18.8, 2, -3, 10, 30, 10, 30)
SETPOINTS = ('ComfTemp', 'ACST', 'AHST', 'ACSTnoTol', 'AHSTnoTol')


def _arguments(regime):
    """The scalar arguments of the custom model with the coefficients of a regime."""
    return dict(custom_slope=regime.slope, custom_intercept=regime.intercept,
                custom_cooling_offset=regime.cooling_offset, custom_heating_offset=regime.heating_offset,
                custom_cooling_lower_limit=regime.cooling_lower_limit,
                custom_cooling_upper_limit=regime.cooling_upper_limit,
                custom_heating_lower_limit=regime.heating_lower_limit,
                custom_heating_upper_limit=regime.heating_upper_limit)


# The regimes ---------------------------------------------------------------------------------------------------------

def test_a_regime_is_checked():
    assert REGIME_CONDITIONS == ('always', 'cooling_season', 'heating_season', 'hvac_off', 'hvac_on')
    assert METRIC_CONDITIONS == ('metric_below', 'metric_above', 'metric_between')
    assert SCALAR_REGIME.condition == 'always' and SCALAR_REGIME.outdoor_metric is None
    # The conditions are normalised (lower case, tuples), so that the regimes can be compared and hashed
    assert CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, 'Cooling_Season').condition == 'cooling_season'
    between = CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, ['metric_between', [10, 20.5]])
    assert between.condition == ('metric_between', (10, 20.5))
    assert between == CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, ('metric_between', (10, 20.5)))
    assert len({between, COLD, WARM, between}) == 3
    assert CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, ('METRIC_ABOVE', -5)).condition == ('metric_above', -5)
    for value in ('0.3', True, float('nan'), None):
        with pytest.raises(ValueError, match='slope of a regime of the custom model must be a number'):
            CustomRegime(value, 17, 2, -2, 10, 30, 10, 30)
    with pytest.raises(ValueError, match='heating_upper_limit of a regime'):
        CustomRegime(0.3, 17, 2, -2, 10, 30, 10, float('inf'))
    for condition in ('winter', ('metric_below', '10'), ('metric_below', (10, 20)), ('always', 1), 10):
        with pytest.raises(ValueError, match='is not a condition of a regime of the custom model'):
            CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, condition)
    with pytest.raises(ValueError, match="The condition 'metric_below' of a regime of the custom model needs a value"):
        CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, 'metric_below')
    for value in ((20, 10), (10, 10), 10, (10, 'x')):
        with pytest.raises(ValueError, match="'metric_between' of a regime of the custom model needs two numbers"):
            CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, ('metric_between', value))
    # An outdoor metric for each regime is not available (pending, see notes/questions.md)
    with pytest.raises(ValueError, match='outdoor_metric of a regime of the custom model must be None'):
        CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, outdoor_metric='rmot_alpha')


def test_the_list_of_regimes_is_checked():
    assert check_custom_regimes(None) == () and check_custom_regimes([]) == ()
    assert check_custom_regimes(COLD) == (COLD,)
    assert check_custom_regimes([COLD, WARM]) == (COLD, WARM)
    # The last regime does not need to be 'always': the scalar arguments apply when no condition holds (D6)
    assert check_custom_regimes((COLD,)) == (COLD,)
    with pytest.raises(ValueError, match=r"The regime 1 of custom_regimes has the condition 'always', so the regimes "
                                         r"after it would never apply"):
        check_custom_regimes([WARM, COLD])
    for value in ('always', [COLD, 'always'], {'a': COLD}):
        with pytest.raises(ValueError, match='custom_regimes must be a list of CustomRegime'):
            check_custom_regimes(value)


def _body(regime, number, zone='Z'):
    return [f'set m = {regime.slope}', f'set n = {regime.intercept}',
            f'set CustAST_ACSToffset = {regime.cooling_offset}', f'set CustAST_AHSToffset = {regime.heating_offset}',
            f'set CustAST_ACSTall = {regime.cooling_lower_limit}',
            f'set CustAST_ACSTaul = {regime.cooling_upper_limit}',
            f'set CustAST_AHSTall = {regime.heating_lower_limit}',
            f'set CustAST_AHSTaul = {regime.heating_upper_limit}', f'set CustomRegime_{zone} = {number}']


def test_the_erl_lines_of_two_regimes():
    below = CustomRegime(0.3, 17, 2, -2, 10, 30, 10, 30, ('metric_below', 10))
    lines = cr.regime_program_lines('Z', [below, WARM])
    assert lines == ['if PMOT < 10', *_body(below, 1), 'else', *_body(WARM, 2), 'endif']
    # With the EMS code of the outdoor metric of the custom model, its variable
    assert cr.regime_program_lines('Z', [below, WARM], metric='Tout_metric')[0] == 'if Tout_metric < 10'
    assert cr.parse_regime_program(lines, 'Z') == (below, WARM)


def test_the_erl_lines_of_the_other_conditions():
    # A single regime 'always' is only its coefficients
    assert cr.regime_program_lines('Z', [WARM]) == _body(WARM, 1)
    # Without a regime 'always', the inputs of SetInputData_<zone> apply when no condition holds (regime 0)
    above = CustomRegime(0.2, 20, 1.5, -1.5, 5, 35, 5, 35, ('metric_above', 25.5))
    between = CustomRegime(0.1, 22, 1, -1, 0, 40, 0, 40, ('metric_between', (-2, 7.25)))
    season = CustomRegime(0.4, 15, 2.5, -2.5, 10, 30, 10, 30, 'cooling_season')
    heating = CustomRegime(0.35, 16, 3, -3, 10, 30, 10, 30, 'heating_season')
    lines = cr.regime_program_lines('Z', [above, between, season, heating])
    assert lines == ['set CustomRegime_Z = 0', *COOLING_SEASON_LINES,
                     'if PMOT > 25.5', *_body(above, 1), 'elseif (PMOT >= -2) && (PMOT <= 7.25)', *_body(between, 2),
                     'elseif CoolingSeason == 1', *_body(season, 3), 'elseif CoolingSeason == 0',
                     *_body(heating, 4), 'endif']
    assert cr.parse_regime_program(lines, 'Z') == (above, between, season, heating)
    # The conditions of the HVAC system need the lines of ApplyAST_<zone> that set NoH_NoC_reqs (mixed mode)
    off = CustomRegime(0.2, 20, 2.5, -2.5, 5, 35, 5, 35, 'hvac_off')
    on = CustomRegime(0.31, 17.8, 3.5, -3.5, 10, 33.5, 10, 33.5, 'hvac_on')
    with pytest.raises(ValueError, match="'hvac_off' and 'hvac_on' of the regimes of the custom model need mixed mode"):
        cr.regime_program_lines('Z', [off, WARM])
    for block in (pl.HVAC_OFF_FROM_COILS, pl.HVAC_OFF_FROM_LOAD):
        hvac_lines = pl.format_lines(block, zone='Z')
        lines = cr.regime_program_lines('Z', [off, on], hvac_lines=hvac_lines)
        assert lines == ['set CustomRegime_Z = 0', *hvac_lines, 'if NoH_NoC_reqs == 1', *_body(off, 1),
                         'elseif NoH_NoC_reqs == 0', *_body(on, 2), 'endif']
        assert cr.parse_regime_program(lines, 'Z') == (off, on)
    assert pl.HVAC_OFF_FROM_COILS[:2] == ('if {zone}_CoolCoil==0', 'if {zone}_HeatCoil==0')
    assert pl.HVAC_OFF_FROM_LOAD[0] == 'if {zone}_LoadToSetpoint == 0'
    # The coefficients are written without exponents
    tiny = CustomRegime(0.00001, 1e3, 0.5, -0.5, 10, 30, 10, 30)
    assert cr.regime_program_lines('Z', [tiny])[:2] == ['set m = 0.00001', 'set n = 1000']
    assert cr.condition_text(('metric_between', (-2, 7.25))) == 'metric_between -2 7.25'
    assert cr.condition_text('hvac_off') == 'hvac_off'
    # The lines that are not those of accim are not regimes
    for wrong in (['if PMOT <= 10', *_body(WARM, 1), 'endif'], ['if PMOT < 10', *_body(WARM, 2), 'endif'],
                  _body(WARM, 1)[1:], ['if PMOT < 10', *_body(WARM, 1)], [*_body(WARM, 1), 'set x = 1'], []):
        with pytest.raises(ValueError, match='The program SelectCustomRegime_Z is not a program of the regimes'):
            cr.parse_regime_program(wrong, 'Z')


def test_the_regimes_in_the_erl_interpreter():
    regimes = [CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 10)),
               CustomRegime(0.2, 20, 1.5, -1.5, 5, 35, 5, 35, ('metric_above', 25)),
               CustomRegime(0.1, 22, 1, -1, 0, 40, 0, 40, ('metric_between', (12, 14)))]
    names = ['PMOT', 'CustomRegime_Z', *cr.REGIME_INPUTS.values()]
    erl = ErlProgramSet({'SelectCustomRegime_Z': cr.regime_program_lines('Z', regimes)}, global_variables=names)
    for metric, regime in ((9.99, 1), (10, 0), (25, 0), (25.01, 2), (12, 3), (14, 3), (14.01, 0), (11.99, 0)):
        # The inputs of SetInputData_<zone>, which apply when no condition holds
        for variable in cr.REGIME_INPUTS.values():
            erl.set(variable, -100)
        erl.set('PMOT', metric)
        erl.run('SelectCustomRegime_Z')
        assert erl.get('CustomRegime_Z') == regime, metric
        expected = regimes[regime - 1] if regime else None
        for field, variable in cr.REGIME_INPUTS.items():
            assert erl.get(variable) == (getattr(expected, field) if expected else -100), (metric, variable)


def _read_pmot(result):
    """The PMOT that the EMS reads in each timestep of a result of compute_setpoints at timestep frequency: that of
    the previous day at the first timestep of each day (0 at the first timestep of the run period)."""
    pmot = result['PMOT'].to_numpy()
    first = np.arange(len(result)) % (24 * STEPS) == 0
    previous = np.r_[0.0, pmot[:-1]]
    return np.where(first, previous, pmot)


def test_compute_setpoints_with_two_regimes():
    arguments = dict(frequency='timestep', start_date='01/04', **SCALAR)
    result = compute_setpoints(EPW, 99, 80, 3, custom_regimes=[COLD, WARM], **arguments)
    assert list(result.columns)[-1] == 'custom_regime'
    cold = compute_setpoints(EPW, 99, 80, 3, **dict(arguments, **_arguments(COLD)))
    warm = compute_setpoints(EPW, 99, 80, 3, **dict(arguments, **_arguments(WARM)))
    # The first regime while the PMOT that the EMS reads is below 16, and the second one otherwise
    expected = np.where(_read_pmot(result) < 16, 1, 2)
    np.testing.assert_array_equal(result['custom_regime'], expected)
    assert set(expected) == {1, 2}
    for column in SETPOINTS + ('applicable',):
        np.testing.assert_array_equal(result[column], np.where(expected == 1, cold[column], warm[column]))
    # Hourly, the means of the hours (the regime changes at the first timestep of some days)
    hourly = compute_setpoints(EPW, 99, 80, 3, custom_regimes=[COLD, WARM], start_date='01/04', **SCALAR)
    means = result['custom_regime'].to_numpy().reshape(-1, STEPS).mean(axis=1)
    np.testing.assert_allclose(hourly['custom_regime'], means, rtol=0, atol=1e-12)


def test_compute_setpoints_with_the_seasons_and_without_a_regime_always():
    arguments = dict(frequency='timestep', start_date='01/04', cooling_season_start='05/04', **SCALAR)
    season = CustomRegime(0.4, 15, 2.5, -2.5, 10, 30, 10, 30, 'cooling_season')
    result = compute_setpoints(EPW, 99, 80, 3, custom_regimes=[COLD, season], **arguments)
    scalar = compute_setpoints(EPW, 99, 80, 3, **arguments)
    cold = compute_setpoints(EPW, 99, 80, 3, **dict(arguments, **_arguments(COLD)))
    cooling = compute_setpoints(EPW, 99, 80, 3, **dict(arguments, **_arguments(season)))
    # The first regime has the priority; the cooling season begins on 5 April; otherwise the scalar arguments
    expected = np.where(_read_pmot(result) < 16, 1, np.where(result['cooling_season'] == 1, 2, 0))
    np.testing.assert_array_equal(result['custom_regime'], expected)
    assert set(expected) == {0, 1, 2}
    np.testing.assert_array_equal(result['cooling_season'], scalar['cooling_season'])
    for column in SETPOINTS:
        found = np.select([expected == 1, expected == 2], [cold[column], cooling[column]], scalar[column])
        np.testing.assert_array_equal(result[column], found)


def test_the_scalar_arguments_are_a_single_regime_always():
    arguments = dict(frequency='timestep', start_date='01/03', **SCALAR)
    scalar = compute_setpoints(EPW, 99, 80, 3, **arguments)
    single = compute_setpoints(EPW, 99, 80, 3, custom_regimes=[SCALAR_REGIME], **arguments)
    assert (single['custom_regime'] == 1).all()
    pd.testing.assert_frame_equal(single.drop(columns='custom_regime'), scalar)
    # No regimes: the same columns as before
    assert list(compute_setpoints(EPW, 99, 80, 3, custom_regimes=[], **arguments).columns) == list(scalar.columns)


def test_compute_setpoints_cannot_evaluate_the_hvac_conditions():
    with pytest.raises(ValueError, match="compute_setpoints cannot evaluate the conditions 'hvac_off' and 'hvac_on'"):
        compute_setpoints(EPW, 99, 80, 3, custom_regimes=[CustomRegime(0.2, 20, 2, -2, 5, 35, 5, 35, 'hvac_on')],
                          **SCALAR)


def test_table_averages_the_regimes_over_time():
    from accim.data.postprocessing.main import _averaged_outputs

    # The number of the regime is averaged, not summed, when Table aggregates the rows
    assert any(output in 'EMS:CustomRegime_Block1_Zone1 [](Hourly)' for output in _averaged_outputs())


def test_compute_setpoints_with_regimes_and_the_outdoor_metric():
    # The conditions compare the outdoor metric of the custom model, Tout_metric
    arguments = dict(frequency='timestep', start_date='01/04', custom_outdoor_metric='rmot_7day', **SCALAR)
    result = compute_setpoints(EPW, 99, 80, 3, custom_regimes=[COLD, WARM], **arguments)
    expected = np.where(result['Tout_metric'] < 16, 1, 2)
    np.testing.assert_array_equal(result['custom_regime'], expected)
    assert set(expected) == {1, 2}
    cold = compute_setpoints(EPW, 99, 80, 3, **dict(arguments, **_arguments(COLD)))
    warm = compute_setpoints(EPW, 99, 80, 3, **dict(arguments, **_arguments(WARM)))
    for column in SETPOINTS:
        np.testing.assert_array_equal(result[column], np.where(expected == 1, cold[column], warm[column]))


def test_the_ems_code_of_the_regimes():
    plain = get_setpoint_ems_code(99, 80, 3, **SCALAR)
    assert get_setpoint_ems_code(99, 80, 3, custom_regimes=None, **SCALAR) == plain
    assert 'SelectCustomRegime' not in plain
    code = get_setpoint_ems_code(99, 80, 3, custom_regimes=[COLD, WARM], **SCALAR)
    title = ('! --- SelectCustomRegime_<zone>: the regime of the custom model of the timestep (1 = metric_below 16, '
             '2 = always), which sets its inputs ---')
    assert title in code
    section = code[code.index(title):].split('\n\n')[0].split('\n')[1:]
    assert [line.strip() for line in section] == cr.regime_program_lines('<zone>', [COLD, WARM])
    assert section[1] == '    set m = 0.5'
    # Before SetAppLimits, after the inputs of the zone
    assert code.index('SetInputData_<zone>') < code.index(title) < code.index('! --- SetAppLimits')
    assert '! SelectCustomRegime_<zone>: the regimes of the custom model (custom_regimes)' in code
    programs = get_setpoint_ems_programs(99, 80, 3, custom_regimes=[COLD, WARM], **SCALAR)
    names = list(programs)
    assert names.index('SelectCustomRegime_<zone>') == names.index('SetAppLimits') - 1
    assert programs['SelectCustomRegime_<zone>'] == cr.regime_program_lines('<zone>', [COLD, WARM])
    with pytest.raises(ValueError, match='custom_regimes needs the custom model'):
        get_setpoint_ems_code(1, 2, 3, custom_regimes=[WARM])
    # The conditions of the HVAC system: those of the script type
    off = CustomRegime(0.2, 20, 2.5, -2.5, 5, 35, 5, 35, 'hvac_off')
    with pytest.raises(ValueError, match="need script_type 'vrf_mm' or 'ex_mm'"):
        get_setpoint_ems_code(99, 80, 3, custom_regimes=[off], script_type='vrf_ac', **SCALAR)
    lines = get_setpoint_ems_code(99, 80, 3, custom_regimes=[off], script_type='vrf_mm', **SCALAR).split('\n')
    assert lines[lines.index('if <zone>_CoolCoil==0') + 1] == '    if <zone>_HeatCoil==0'
    lines = get_setpoint_ems_code(99, 80, 3, custom_regimes=[off], script_type='ex_mm', **SCALAR).split('\n')
    assert 'if <zone>_LoadToSetpoint == 0' in lines
    # With the outdoor metric, Tout_metric
    code = get_setpoint_ems_code(99, 80, 3, custom_regimes=[COLD, WARM], custom_outdoor_metric='daily_mean',
                                 **SCALAR)
    assert 'if Tout_metric < 16' in code.split('\n')


# AddAccis and modify_accis ------------------------------------------------------------------------------------------

def _add_accis(folder, monkeypatch, **arguments):
    from accim.sim.accis import AddAccis

    folder.mkdir(exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    values = dict(script_type='vrf_mm', supply_air_temp_input_method='temperature difference', output_type='standard',
                  output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                  setpoint_type='temperature', comfort_standard=[1, 99], category=[1], comfort_mode=[3],
                  hvac_mode=[2], ventilation_control=[0], confirm=True, verbose=False, **SCALAR)
    values.update(arguments)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(**values)
    return {path.name: path for path in folder.glob('TestModel[[]*.idf')}


def _programs(idf):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
            for p in idf.idfobjects['EnergyManagementSystem:Program']}


def _global_variables(idf):
    return [[str(name).strip() for name in g.fieldvalues[1:] if str(name).strip()]
            for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']]


def _regime_objects(idf):
    """The objects of the regimes of a model: programs, global variables, EMS output variables and Output:Variable
    objects."""
    return (sorted(p.Name for p in idf.idfobjects['EnergyManagementSystem:Program']
                   if p.Name.startswith(cr.PROGRAM_PREFIX)),
            sorted(names[0] for names in _global_variables(idf) if names[0].startswith(cr.OUTPUT_PREFIX)),
            sorted((o.Name, o.EMS_Variable_Name, o.Type_of_Data_in_Variable, o.Update_Frequency, o.Units)
                   for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']
                   if o.Name.startswith(cr.OUTPUT_PREFIX)),
            sorted((o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']
                   if o.Variable_Name.startswith(cr.OUTPUT_PREFIX)))


@needs_idd
def test_add_accis_adds_the_regimes(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf

    reference = _add_accis(tmp_path / 'reference', monkeypatch)
    # Without regimes, the output IDFs are those of accim 1.1.0 (the scalar arguments are the only regime)
    for value in (None, []):
        same = _add_accis(tmp_path / f'none{value is None}', monkeypatch, custom_regimes=value)
        assert sorted(same) == sorted(reference) and len(reference) == 2
        assert all(same[name].read_bytes() == reference[name].read_bytes() for name in reference)
    outputs = _add_accis(tmp_path / 'regimes', monkeypatch, custom_regimes=[COLD, WARM])
    assert sorted(outputs) == sorted(reference)
    for name in reference:
        idf, before = load_idf(outputs[name]), load_idf(reference[name])
        if '[CS_INT EN16798[' in name:
            # The output IDFs of the other comfort standards do not have them
            assert outputs[name].read_bytes() == reference[name].read_bytes()
            continue
        programs, programs_before = _programs(idf), _programs(before)
        added = [f'SelectCustomRegime_{zone}' for zone in ZONES]
        assert set(programs) - set(programs_before) == set(added)
        assert [p for p in programs if p not in added] == list(programs_before)
        for zone in ZONES:
            assert programs[f'SelectCustomRegime_{zone}'] == cr.regime_program_lines(zone, [COLD, WARM])
            run = programs[f'RunACCIS_{zone}']
            assert run[run.index('run SetAppLimits') - 1] == f'run SelectCustomRegime_{zone}'
            assert [line for line in run if line != f'run SelectCustomRegime_{zone}'] == programs_before[
                f'RunACCIS_{zone}']
        changed = {f'RunACCIS_{zone}' for zone in ZONES} | set(added)
        assert all(programs[p] == programs_before[p] for p in programs if p not in changed)
        variables, variables_before = _global_variables(idf), _global_variables(before)
        assert variables[:len(variables_before)] == variables_before
        assert sorted(variables[len(variables_before):]) == [[f'CustomRegime_{zone}'] for zone in ZONES]
        assert _regime_objects(idf) == (
            sorted(added), [f'CustomRegime_{zone}' for zone in ZONES],
            [(f'CustomRegime_{zone}', f'CustomRegime_{zone}', 'Averaged', 'ZoneTimestep', '') for zone in ZONES],
            [(f'CustomRegime_{zone}', 'Hourly') for zone in ZONES])
        assert cr.custom_regimes_of(idf) == {zone: (COLD, WARM) for zone in ZONES}


@needs_idd
def test_the_regimes_with_zone_arguments_and_the_outdoor_metric(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf
    from accim.sim.ems.outdoor_metric import has_outdoor_metric_code

    # Only the zones of the custom model have the regimes
    outputs = _add_accis(tmp_path / 'zone', monkeypatch, comfort_standard=[1], category=[1], custom_regimes=[COLD],
                         zone_arguments={'Block1:Zone2': {'comfort_standard': 99, 'category': 80}})
    [idf] = [load_idf(path) for path in outputs.values()]
    assert cr.custom_regimes_of(idf) == {'Block1_Zone2': (COLD,)}
    assert 'run SelectCustomRegime_Block1_Zone1' not in _programs(idf)['RunACCIS_Block1_Zone1']
    # With the EMS code of the outdoor metric, the conditions compare Tout_metric
    outputs = _add_accis(tmp_path / 'metric', monkeypatch, comfort_standard=[99], category=[80],
                         custom_outdoor_metric='rmot_7day', epw=str(EPW), custom_regimes=[COLD, WARM])
    [idf] = [load_idf(path) for path in outputs.values()]
    assert has_outdoor_metric_code(idf)
    for zone in ZONES:
        assert _programs(idf)[f'SelectCustomRegime_{zone}'] == cr.regime_program_lines(zone, [COLD, WARM],
                                                                                      'Tout_metric')
    assert cr.custom_regimes_of(idf) == {zone: (COLD, WARM) for zone in ZONES}


@needs_idd
def test_add_accis_checks_the_regimes(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="custom_regimes needs setpoint_type 'temperature'"):
        _add_accis(tmp_path, monkeypatch, setpoint_type='pmv', custom_regimes=[WARM])
    off = CustomRegime(0.2, 20, 2.5, -2.5, 5, 35, 5, 35, 'hvac_off')
    with pytest.raises(ValueError, match=r"'hvac_off' and 'hvac_on' of custom_regimes need mixed mode .* not 'vrf_ac'"):
        _add_accis(tmp_path, monkeypatch, script_type='vrf_ac', custom_regimes=[off])
    with pytest.raises(ValueError, match='custom_regimes needs the custom model: comfort_standard 99'):
        _add_accis(tmp_path, monkeypatch, comfort_standard=[1], category=[1], custom_regimes=[WARM])
    with pytest.raises(ValueError, match='only the last regime can have it'):
        _add_accis(tmp_path, monkeypatch, custom_regimes=[WARM, COLD])
    with pytest.raises(ValueError, match='custom_regimes must be a list of CustomRegime'):
        _add_accis(tmp_path, monkeypatch, custom_regimes='always')
    assert not list(tmp_path.glob('TestModel[[]*.idf'))
    # In mixed mode, the condition reads the coils of the VRF systems of accim, as ApplyAST_<zone>
    from accim.sim.accis import load_idf

    outputs = _add_accis(tmp_path / 'mixed', monkeypatch, comfort_standard=[99], category=[80],
                         custom_regimes=[off, WARM])
    [idf] = [load_idf(path) for path in outputs.values()]
    for zone in ZONES:
        hvac_lines = pl.format_lines(pl.HVAC_OFF_FROM_COILS, zone=zone)
        assert cr.hvac_off_lines(idf, zone) == hvac_lines
        assert _programs(idf)[f'ApplyAST_{zone}'][:len(hvac_lines)] == hvac_lines
        assert _programs(idf)[f'SelectCustomRegime_{zone}'] == cr.regime_program_lines(zone, [off, WARM],
                                                                                      hvac_lines=hvac_lines)


def _model(tmp_path, script_type='vrf_mm'):
    from accim.sim.accis import add_accis_to_idf, load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    idf = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type=script_type, supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    return idf


@needs_idd
def test_modify_accis_sets_keeps_and_removes_the_regimes(tmp_path):
    from accim.sim.accis import modify_accis

    idf = _model(tmp_path)
    before = {name: lines for name, lines in _programs(idf).items()}
    variables_before = _global_variables(idf)
    with pytest.raises(ValueError, match='custom_regimes needs the custom model: no zone has comfort_standard 99'):
        modify_accis(idf, custom_regimes=[WARM])
    assert not cr.has_custom_regimes(idf)
    modify_accis(idf, comfort_standard=99, category=80, comfort_mode=3, custom_regimes=[COLD, WARM], **SCALAR)
    assert cr.custom_regimes_of(idf) == {zone: (COLD, WARM) for zone in ZONES}
    # None keeps them
    modify_accis(idf, setpoint_tolerance=0.2, **SCALAR)
    assert cr.custom_regimes_of(idf) == {zone: (COLD, WARM) for zone in ZONES}
    # Others replace them, without duplicating their objects
    season = CustomRegime(0.4, 15, 2.5, -2.5, 10, 30, 10, 30, 'cooling_season')
    modify_accis(idf, custom_regimes=[season], **SCALAR)
    assert cr.custom_regimes_of(idf) == {zone: (season,) for zone in ZONES}
    programs = _programs(idf)
    for zone in ZONES:
        assert programs[f'RunACCIS_{zone}'].count(f'run SelectCustomRegime_{zone}') == 1
    names, variables, outputs, requested = _regime_objects(idf)
    assert len(names) == len(variables) == len(outputs) == len(requested) == 2
    # With the outdoor metric, Tout_metric; back to 'pmot', PMOT
    with pytest.warns(UserWarning, match='begins with the running mean of ASHRAE 55'):
        modify_accis(idf, custom_outdoor_metric='rmot_7day', custom_regimes=[COLD, WARM], **SCALAR)
    assert _programs(idf)['SelectCustomRegime_Block1_Zone1'][0] == 'if Tout_metric < 16'
    modify_accis(idf, custom_outdoor_metric='pmot', **SCALAR)
    assert _programs(idf)['SelectCustomRegime_Block1_Zone1'][0] == 'if PMOT < 16'
    # An empty list removes them all
    modify_accis(idf, comfort_standard=1, category=1, custom_regimes=[], **SCALAR)
    assert _regime_objects(idf) == ([], [], [], [])
    assert all(lines == before[name] for name, lines in _programs(idf).items() if name.startswith('RunACCIS_'))
    assert _global_variables(idf) == variables_before
    # The conditions of the HVAC system need mixed mode
    off = CustomRegime(0.2, 20, 2.5, -2.5, 5, 35, 5, 35, 'hvac_off')
    other = _model(tmp_path, 'vrf_ac')
    with pytest.raises(ValueError, match="'hvac_off' and 'hvac_on' of custom_regimes need mixed mode"):
        modify_accis(other, comfort_standard=99, category=80, comfort_mode=3, custom_regimes=[off])
    assert not cr.has_custom_regimes(other)


@needs_idd
@pytest.mark.skipif(LEGACY_IDF is None, reason='needs the output IDF of accim 0.x of the repository')
def test_the_models_of_earlier_versions_have_one_regime(tmp_path):
    from accim.sim.accis import load_idf, modify_accis

    shutil.copy(LEGACY_IDF, tmp_path / 'legacy.idf')
    building = load_idf(tmp_path / 'legacy.idf')
    with pytest.raises(ValueError, match='whose custom model has one regime'):
        modify_accis(building, comfort_standard=99, custom_regimes=[WARM])
    modify_accis(building, comfort_standard=99, comfort_mode=3, custom_regimes=[])
    assert not cr.has_custom_regimes(building)


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')


def _output_idf(folder, monkeypatch, begin, end, frequency, script_type='vrf_ac', variables=(), **arguments):
    """An output IDF of AddAccis of the sample model (the custom model, category 80), whose input IDF has the run
    period given, with some output variables of EnergyPlus."""
    from accim.sim.accis import AddAccis, load_idf

    folder.mkdir(parents=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    model = load_idf(folder / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    model.save()
    monkeypatch.chdir(folder)
    values = dict(script_type=script_type, supply_air_temp_input_method='temperature difference',
                  output_type='standard', output_frequencies=[frequency], keep_existing_outputs=False,
                  energyplus_version='auto', setpoint_type='temperature', comfort_standard=[99], category=[80],
                  comfort_mode=[3], hvac_mode=[2], ventilation_control=[0], confirm=True, verbose=False, **SCALAR)
    values.update(arguments)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(**values)
    [path] = folder.glob('TestModel[[]*.idf')
    idf = load_idf(path)
    for variable in variables:
        idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=variable,
                         Reporting_Frequency=frequency.capitalize())
    idf.saveas(str(folder / 'model.idf'))
    return folder / 'model.idf'


def _run_energyplus(model, folder):
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    result = subprocess.run([str(energyplus), '-d', str(folder), '-p', 'run', '-s', 'C', '-r', '-x', '-w', str(EPW),
                             str(model)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    return pd.read_csv(folder / 'run.csv')


#: Three regimes for the first days of April in Seville (PMOT from 15.4 to 16.5 °C): below 16 °C, the cooling season
#: (from 5 April) and the others
SEASON = CustomRegime(0.4, 15, 2.5, -2.5, 10, 30, 10, 30, 'cooling_season')


@needs_energyplus
def test_the_regimes_in_energyplus(tmp_path, monkeypatch, capsys):
    from accim.utils.verification import verify_accim_simulation

    regimes = [COLD, SEASON, WARM]
    model = _output_idf(tmp_path / 'april', monkeypatch, (4, 1), (4, 7), 'timestep', cooling_season_start='05/04',
                        custom_regimes=regimes)
    results = _run_energyplus(model, tmp_path / 'april' / 'out')
    assert len(results) == 7 * 24 * STEPS
    # The setpoints and the regimes are those of compute_setpoints (check 4)
    mismatches = verify_accim_simulation(str(tmp_path / 'april' / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0 or not mismatches['check'].str.match('Check4').any()
    for zone in ZONES:
        for check in ('Check4_custom_regime', 'Check4_ACST', 'Check4_AHST', 'Check4_ComfTemp'):
            assert re.search(rf"'{zone}' {check} \(.*\): 0 mismatch\(es\) in 1008 timesteps", output), (zone, check)
        found = results[f'EMS:CustomRegime_{zone} [](TimeStep)']
        # The three regimes apply in the week
        assert set(found) == {1, 2, 3}
        assert (found.iloc[4 * 24 * STEPS:] == 2).all()


@needs_energyplus
def test_the_condition_hvac_off_in_energyplus(tmp_path, monkeypatch):
    # Mixed mode in June: the VRF system of each zone is off while the zone is not occupied, and cools while it is
    off = CustomRegime(0.2, 20, 2.5, -2.5, 5, 35, 5, 35, 'hvac_off')
    model = _output_idf(tmp_path / 'june', monkeypatch, (6, 1), (6, 7), 'timestep', script_type='vrf_mm',
                        custom_regimes=[off, WARM],
                        variables=('Cooling Coil Total Cooling Rate', 'Heating Coil Heating Rate'))
    results = _run_energyplus(model, tmp_path / 'june' / 'out')
    arguments = dict(frequency='timestep', start_date='01/06')
    first = compute_setpoints(EPW, 99, 80, 3, **dict(arguments, **_arguments(off)))
    second = compute_setpoints(EPW, 99, 80, 3, **dict(arguments, **_arguments(WARM)))
    for zone in ZONES:
        regime = results[f'EMS:CustomRegime_{zone} [](TimeStep)'].to_numpy()
        assert set(regime) == {1, 2}
        # The regime 1 when the coils of the VRF system of the zone were off in the previous timestep, which the EMS
        # reads at the beginning of the timestep (the outputs of the coils are the means of the timestep, whose
        # systems timesteps are those of the zone in this model)
        key = zone.replace('_', ':').upper()
        cooling = results[f'{key} VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate [W](TimeStep)']
        heating = results[f'{key} VRF INDOOR UNIT DX HEATING COIL:Heating Coil Heating Rate [W](TimeStep)']
        coils_off = ((cooling == 0) & (heating == 0)).to_numpy()
        np.testing.assert_array_equal(regime[1:], np.where(coils_off[:-1], 1, 2))
        # The setpoints are those of the regime of each timestep
        for column, output in (('ACST', 'Adaptive Cooling Setpoint Temperature'),
                               ('AHST', 'Adaptive Heating Setpoint Temperature')):
            found = results[f'EMS:{output}_{zone} [C](TimeStep)'].to_numpy()
            expected = np.where(regime == 1, first[column].to_numpy()[:len(found)],
                                second[column].to_numpy()[:len(found)])
            np.testing.assert_allclose(found, expected, rtol=0, atol=1e-9)


@needs_energyplus
def test_the_ems_and_api_backends_give_the_same_regimes(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations

    off = CustomRegime(0.2, 20, 2.5, -2.5, 5, 35, 5, 35, 'hvac_off')
    model = _output_idf(tmp_path / 'model', monkeypatch, (4, 1), (4, 10), 'hourly', script_type='vrf_mm',
                        cooling_season_start='05/04', custom_regimes=[COLD, off, SEASON])
    ems_results = _run_energyplus(model, tmp_path / 'ems')
    results = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    assert len(ems_results) == 10 * 24
    regimes = ems_results['EMS:CustomRegime_Block1_Zone1 [](Hourly)']
    assert regimes.min() < 1 and regimes.max() > 2
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
