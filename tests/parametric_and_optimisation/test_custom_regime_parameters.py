"""Tests for the parameters of the regimes of the custom model in the parametric module (proposal B2 of accim 1.2.0,
with the factory of C1): ``custom_regime_<regime>_<field>`` (such as ``custom_regime_1_slope``), which set a coefficient
of a regime of the custom model in all the zones that have the regimes (``param_accis.modify_custom_regime``), and the
wrapper classes of ``parameters.custom_regime_parameters(n)`` (``CustAST_m_1``, ``CustAST_n_1``...).
"""
import pickle
import shutil
import warnings
from pathlib import Path

import pytest

from accim.energyplus import default_energyplus_folder
from accim.parametric_and_optimisation import parameters, params_dicts
from accim.parametric_and_optimisation.funcs_for_besos import param_accis
from accim.parametric_and_optimisation.main import ParametricSimulation
from accim.sim.arguments import CustomRegime

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists() and EPW.exists()),
                               reason='needs EnergyPlus 25.1 and the sample files of the repository')
ZONES = ['Block1_Zone1', 'Block1_Zone2']
COLD = CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16))
WARM = CustomRegime(0.33, 18.8, 2, -3, 10, 30, 10, 30)
FIELDS = ['slope', 'intercept', 'cooling_offset', 'heating_offset', 'cooling_lower_limit', 'cooling_upper_limit',
          'heating_lower_limit', 'heating_upper_limit']


def test_the_names_of_the_parameters_of_the_regimes():
    assert list(params_dicts.CUSTOM_REGIME_FIELDS) == FIELDS
    assert params_dicts.custom_regime_parameter('custom_regime_1_slope') == (1, 'slope')
    assert params_dicts.custom_regime_parameter('Custom_Regime_12_Heating_Upper_Limit') == (12, 'heating_upper_limit')
    for name in ('custom_regime_0_slope', 'custom_regime_1_m', 'custom_regime_slope', 'custom_slope', 3, None):
        assert params_dicts.custom_regime_parameter(name) is None
    # They are not in all_params (their number depends on the model): their modifiers can be sent to other processes
    assert not any(name.startswith('custom_regime_') for name in params_dicts.all_params)
    modifier = params_dicts.custom_regime_modifier('custom_regime_2_intercept')
    assert modifier.func is param_accis.modify_custom_regime
    assert modifier.keywords == {'regime': 2, 'field': 'intercept'}
    assert pickle.loads(pickle.dumps(modifier)).keywords == modifier.keywords
    with pytest.raises(KeyError, match='is not a parameter of the regimes of the custom model'):
        params_dicts.custom_regime_modifier('custom_slope')
    # The BESOS parameters, by name, with options or a range
    for values in ([0.3, 0.4], (0.2, 0.6)):
        parameter = parameters.accis_parameter('Custom_Regime_1_Slope', values)
        assert parameter.value_descriptors[0].name == 'custom_regime_1_slope'
        assert pickle.loads(pickle.dumps(parameter)).value_descriptors[0].name == 'custom_regime_1_slope'
    with pytest.raises(KeyError, match='does not exist'):
        parameters.accis_parameter('custom_regime_1_m', [0.3])


def test_the_factory_of_the_wrapper_classes():
    classes = parameters.custom_regime_parameters(2)
    names = [f'CustAST_{short}_{regime}' for regime in (1, 2)
             for short in ('m', 'n', 'ACSToffset', 'AHSToffset', 'ACSTall', 'ACSTaul', 'AHSTall', 'AHSTaul')]
    assert list(classes) == names
    assert classes['CustAST_m_1']().name == 'custom_regime_1_slope'
    assert classes['CustAST_AHSTaul_2']().name == 'custom_regime_2_heating_upper_limit'
    assert all(issubclass(cls, parameters.CustomRegimeParameter) for cls in classes.values())
    assert [(cls().regime, cls().field) for cls in classes.values()] == [(r, f) for r in (1, 2) for f in FIELDS]
    assert list(parameters.CUSTOM_REGIME_CLASS_NAMES.values()) == FIELDS
    for value in (0, 1.5, True, '2'):
        with pytest.raises(ValueError, match='n_regimes must be a number of regimes of at least 1'):
            parameters.custom_regime_parameters(value)
    for regime, field in ((0, 'slope'), (1, 'm'), (True, 'slope'), ('1', 'slope')):
        with pytest.raises(ValueError, match='The regime must be a number from 1'):
            parameters.CustomRegimeParameter(regime, field)


def _custom_model(tmp_path, regimes=(COLD, WARM)):
    from accim.sim.accis import add_accis_to_idf, load_idf, modify_accis

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(building, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    modify_accis(building, comfort_standard=99, category=80, comfort_mode=3, custom_regimes=list(regimes))
    return building


@needs_idd
def test_the_modifiers_of_the_regimes(tmp_path):
    from accim.sim.ems.custom_regimes import custom_regimes_of

    building = _custom_model(tmp_path)
    classes = parameters.custom_regime_parameters(2)
    classes['CustAST_m_1']().modify(building, 0.45)
    classes['CustAST_ACSTaul_2']().modify(building, 31.5)
    param_accis.modify_custom_regime(building, -2.5, 1, 'heating_offset')
    expected = (CustomRegime(0.45, 12, 2, -2.5, 5, 40, 5, 40, ('metric_below', 16)),
                CustomRegime(0.33, 18.8, 2, -3, 10, 31.5, 10, 30))
    assert custom_regimes_of(building) == {zone: expected for zone in ZONES}
    with pytest.raises(ValueError, match='has 2 regimes of the custom model, so it has no regime 3'):
        parameters.CustomRegimeParameter(3, 'slope').modify(building, 0.3)
    with pytest.raises(ValueError, match="'m' is not a coefficient of a regime of the custom model"):
        param_accis.modify_custom_regime(building, 0.3, 1, 'm')
    with pytest.raises(ValueError, match='slope of a regime of the custom model must be a number'):
        param_accis.modify_custom_regime(building, 'x', 1, 'slope')
    assert custom_regimes_of(building) == {zone: expected for zone in ZONES}
    other = _custom_model(tmp_path, regimes=())
    with pytest.raises(ValueError, match='The model has no regimes of the custom model'):
        classes['CustAST_n_1']().modify(other, 17)


@needs_idd
def test_a_two_point_design_of_a_regime(tmp_path, monkeypatch):
    from besos.evaluator import EvaluatorEP

    from accim.sim.accis import load_idf, modify_accis
    from accim.sim.ems.custom_regimes import custom_regimes_of

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)
    building = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        simulation = ParametricSimulation(buildings=[building], epws=[str(EPW)], parameters_type='accim custom model',
                                          output_frequencies=['hourly'], verbose=False)
    modify_accis(simulation.building, comfort_standard=99, category=80, comfort_mode=3, custom_regimes=[COLD, WARM])
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        simulation.set_parameters({'custom_regime_1_slope': [0.4, 0.6], 'custom_intercept': [17.8]})
    simulation.set_problem()
    simulation.sampling_full_set()
    plan = simulation.parameters_values_df
    assert plan['custom_regime_1_slope'].tolist() == [0.4, 0.6]
    # The parameters of the regimes are applied by BESOS (also in other processes, which receive them pickled)
    additional = simulation._get_additional_problem_parameters()
    assert [p.value_descriptors[0].name for p in additional] == ['custom_regime_1_slope']
    pickle.dumps(additional)
    # The IDFs of the design, as the simulations of the parametric module get them (without running EnergyPlus)
    evaluator = EvaluatorEP(problem=simulation.problem, building=simulation.building, epw=str(EPW))
    for row, value in enumerate(plan['custom_regime_1_slope']):
        evaluator.generate_building(plan, row, str(tmp_path / f'design_{row}'))
        generated = load_idf(tmp_path / f'design_{row}.idf')
        regimes = custom_regimes_of(generated)
        assert set(regimes) == set(ZONES)
        assert all(found == (CustomRegime(value, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 16)), WARM)
                   for found in regimes.values())
    # The other types of parameters do not take them
    with pytest.raises(ValueError, match='are not allowed in parameters_type'):
        ParametricSimulation(buildings=None, epws=['Test.epw'], parameters_type='accim predefined model',
                             bypass_add_accis=True).set_parameters({'custom_regime_1_slope': [0.4]})
