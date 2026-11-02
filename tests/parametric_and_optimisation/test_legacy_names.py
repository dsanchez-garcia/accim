"""Tests for the names of the parameters and arguments of accim.parametric_and_optimisation in accim 0.x.

Since accim 1.0.0, the parameters (comfort_standard, custom_slope...) and the arguments of the classes
(script_type, output_frequencies...) have the names of the arguments of accim.sim. The names of accim 0.x
(ComfStand, CustAST_m, ScriptType, output_freqs...) keep working, with a DeprecationWarning, and the results of
accim 0.x get the new names of the parameters when they are loaded.
"""
import warnings

import pandas as pd
import pytest

from accim.parametric_and_optimisation import params_dicts
from accim.parametric_and_optimisation import parameters
from accim.parametric_and_optimisation.main import ParametricSimulation


def _simulation(**kwargs):
    arguments = dict(buildings=None, epws=['Test.epw'], parameters_type=None, bypass_add_accis=True)
    arguments.update(kwargs)
    return ParametricSimulation(**arguments)


def test_the_legacy_names_are_those_of_all_the_parameters():
    assert set(params_dicts.LEGACY_PARAMETER_NAMES.values()) == set(params_dicts.all_params)
    assert not set(params_dicts.LEGACY_PARAMETER_NAMES) & set(params_dicts.all_params)


@pytest.mark.parametrize('name, expected', [
    ('comfort_standard', 'comfort_standard'),
    ('Comfort_Mode', 'comfort_mode'),
    ('my_additional_parameter', 'my_additional_parameter'),
])
def test_resolve_parameter_name_keeps_the_new_names_without_warnings(name, expected):
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        assert params_dicts.resolve_parameter_name(name) == expected


@pytest.mark.parametrize('name, expected', [
    ('ComfStand', 'comfort_standard'),
    ('comfstand', 'comfort_standard'),
    ('CustAST_m', 'custom_slope'),
    ('CustAST_ASToffset', 'custom_offset'),
    ('PMV cooling setpoint', 'pmv_cooling_setpoint'),
])
def test_resolve_parameter_name_translates_the_names_of_accim_0x(name, expected):
    with pytest.warns(DeprecationWarning, match=f'use {expected!r} instead'):
        assert params_dicts.resolve_parameter_name(name) == expected


def test_rename_legacy_parameter_columns():
    df = pd.DataFrame({'ComfStand': [1], 'CustAST_m': [0.3], 'Heating': [2.0]})
    df.attrs['parameters_names'] = ['ComfStand', 'CustAST_m']
    df.attrs['outputs_names'] = ['Heating']

    with pytest.warns(DeprecationWarning, match="'ComfStand', 'CustAST_m'"):
        renamed = params_dicts.rename_legacy_parameter_columns(df, 'The plan')

    assert list(renamed.columns) == ['comfort_standard', 'custom_slope', 'Heating']
    assert renamed.attrs == {'parameters_names': ['comfort_standard', 'custom_slope'], 'outputs_names': ['Heating']}
    assert list(df.columns) == ['ComfStand', 'CustAST_m', 'Heating']


def test_rename_legacy_parameter_columns_without_legacy_names():
    df = pd.DataFrame({'comfort_standard': [1], 'Heating': [2.0]})

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        assert params_dicts.rename_legacy_parameter_columns(df) is df
    # A column with the new name wins over the one with the old name
    both = pd.DataFrame({'ComfStand': [1], 'comfort_standard': [2]})
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        assert list(params_dicts.rename_legacy_parameter_columns(both).columns) == ['ComfStand', 'comfort_standard']


def test_accis_parameter_and_parameter_accept_the_names_of_accim_0x():
    with pytest.warns(DeprecationWarning):
        parameter = parameters.accis_parameter('ComfStand', [1, 2])
    assert parameter.value_descriptors[0].name == 'comfort_standard'
    with pytest.raises(KeyError, match='does not exist'):
        parameters.accis_parameter('NotAParameter', [1, 2])

    with pytest.warns(DeprecationWarning):
        assert parameters.Parameter('CustAST_m').name == 'custom_slope'
    assert parameters.Parameter('comfort_mode').name == 'comfort_mode'
    assert parameters.ComfStand().name == 'comfort_standard'


def test_parameter_modify_only_calls_the_modifier_of_its_parameter(monkeypatch):
    calls = []
    for name in ['comfort_standard', 'category', 'custom_slope']:
        monkeypatch.setitem(params_dicts.all_params, name,
                            lambda idf, value, name=name: calls.append((name, idf, value)))

    parameters.Parameter('category').modify('idf', 90)

    assert calls == [('category', 'idf', 90)]


def test_the_classes_accept_the_argument_and_attribute_names_of_accim_0x():
    with pytest.warns(DeprecationWarning, match='output_freqs -> output_frequencies'):
        sim = _simulation(output_freqs=['daily'], verbosemode=False)

    assert sim.output_frequencies == ['daily'] and sim.bypass_add_accis is True
    with pytest.warns(DeprecationWarning, match='The attribute output_freqs is deprecated'):
        assert sim.output_freqs == ['daily']
    with pytest.warns(DeprecationWarning, match='The attribute bypass_addAccis is deprecated'):
        sim.bypass_addAccis = False
    assert sim.bypass_add_accis is False
    with pytest.raises(TypeError, match="'output_frequencies' twice"):
        _simulation(output_freqs=['daily'], output_frequencies=['hourly'])


def test_set_parameters_accepts_the_names_of_accim_0x():
    sim = _simulation(parameters_type='accim predefined model')

    with pytest.warns(DeprecationWarning) as record:
        sim.set_parameters(accis_params_dict={'ComfStand': [1, 2], 'CAT': [1, 2]}, use_dflt_values=True)

    messages = [str(w.message) for w in record]
    assert any("'ComfStand' is deprecated" in m for m in messages)
    assert any('use_dflt_values -> use_default_values' in m for m in messages)
    assert [p.value_descriptors[0].name for p in sim.parameters_list] == ['comfort_standard', 'category']


def test_sampling_custom_renames_the_columns_of_accim_0x():
    sim = _simulation()

    with pytest.warns(DeprecationWarning, match='custom_plan: the columns .* have the names of the parameters'):
        sim.sampling_custom(pd.DataFrame({'ComfStand': [1, 2], 'HVACmode': [0, 2]}))

    assert list(sim.parameters_values_df.columns) == ['comfort_standard', 'hvac_mode']


def test_the_results_of_accim_0x_get_the_new_names_when_they_are_loaded(tmp_path):
    results = pd.DataFrame({'ComfStand': [1, 2], 'CustAST_m': [0.3, 0.4], 'epw': ['A', 'A'], 'Heating': [1.0, 2.0]})
    results.attrs.update(parameters_names=['ComfStand', 'CustAST_m'], outputs_names=['Heating'], epws=['A'])
    path = tmp_path / 'results.pkl'
    results.to_pickle(path)
    sim = _simulation()

    with pytest.warns(UserWarning, match='The loaded results: the columns .* have the names of the parameters'):
        loaded = sim.load_outputs_parametric(pickle_path=str(path))

    assert list(loaded.columns[:2]) == ['comfort_standard', 'custom_slope']
    assert sim.parameters_names == ['comfort_standard', 'custom_slope']
