"""Tests for the names of accim 0.x, which accim 1.0.0 renamed to follow PEP 8.

The old classes, functions, modules and arguments keep working with a DeprecationWarning that gives the
new name, so the scripts written for accim 0.x still run.
"""
import builtins
import importlib
import inspect
import subprocess
import sys
import warnings
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import accim
import accim.lists
from accim._deprecation import accepts_legacy_kwargs, deprecated_alias, rename_legacy_kwargs
from accim.constants import ENERGYPLUS_VERSIONS_WITH_SPACES, SUPPORTED_ENERGYPLUS_VERSIONS
from accim.sim import accis, accis_single_idf, accis_single_idf_funcs, apmv
from accim.sim.arguments import LEGACY_ARGUMENT_NAMES

REPO = Path(__file__).resolve().parents[2]


class _Reached(Exception):
    """Raised by the load_idf stub: AddAccis validated its arguments and started reading the IDFs."""


def _stub_load_idf(path, energyplus_version='auto'):
    raise _Reached(energyplus_version)


def test_version():
    assert accim.__version__ == '1.1.0'


def test_importing_accim_has_no_side_effects():
    # Before, importing accim imported besos, dask and platypus, and patched them
    script = ('import sys, accim; '
              'print(sorted(m for m in ("besos", "dask", "platypus", "eppy", "pandas") if m in sys.modules))')
    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, cwd=REPO, timeout=120)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '[]'


def test_lists_of_accim_0x():
    assert accim.lists.fullEPversionsList == list(SUPPORTED_ENERGYPLUS_VERSIONS) + ['auto']
    assert accim.lists.epvers_space_objs == list(ENERGYPLUS_VERSIONS_WITH_SPACES)


def test_addaccis_class_accepts_the_old_argument_names(monkeypatch):
    monkeypatch.setattr(accis, 'load_idf', _stub_load_idf)
    monkeypatch.setattr(builtins, 'input', lambda prompt='': pytest.fail(f'Unexpected prompt: {prompt}'))

    with pytest.warns(DeprecationWarning) as record, pytest.raises(_Reached) as reached:
        accis.addAccis(idfs=['model.idf'], ScriptType='ex_ac', Output_type='standard', Output_freqs=['hourly'],
                       Output_keep_existing=False, TempCtrl='temp', EnergyPlus_version='25.1', verboseMode=False)

    assert issubclass(accis.addAccis, accis.AddAccis)
    assert str(reached.value) == '25.1'
    messages = [str(w.message) for w in record]
    assert any('accim.sim.accis.addAccis is deprecated' in m and 'AddAccis' in m for m in messages)
    assert any('ScriptType -> script_type' in m for m in messages)


def test_an_argument_cannot_be_given_with_both_names(monkeypatch):
    monkeypatch.setattr(accis, 'load_idf', _stub_load_idf)

    with pytest.warns(DeprecationWarning), pytest.raises(TypeError, match="got the argument 'script_type' twice"):
        accis.addAccis(idfs=['model.idf'], ScriptType='ex_ac', script_type='ex_ac')


def test_the_old_argument_names_are_arguments_of_the_new_functions():
    new_names = set(inspect.signature(accis.AddAccis).parameters) | set(inspect.signature(accis.modify_accis).parameters)

    assert set(LEGACY_ARGUMENT_NAMES.values()) <= new_names


def test_arguments_with_the_names_of_accim_0x():
    arguments = accis._Arguments(comfort_standard=[1], script_type='vrf_ac')

    assert 'ComfStand' in arguments and 'comfort_standard' in arguments
    assert 'NameSuffix' not in arguments
    with pytest.warns(DeprecationWarning, match="arguments\\['ComfStand'\\] is deprecated"):
        assert arguments.get('ComfStand') == [1]
    assert arguments.get('NameSuffix', 'default') == 'default'
    assert arguments.get('script_type') == 'vrf_ac'


class _Program:
    def __init__(self, name):
        self.Name = name


def test_deprecated_class_keeps_the_positional_arguments_of_accim_0x(monkeypatch):
    # In accim 0.x, Output_gen_dataframe was its 7th argument, which add_accis_to_idf does not have
    calls = []

    def fake_add_accis_to_idf(idf, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(occupied_zones=['Z1'], occupied_zones_orig=['Z 1'], is_mixed_mode=False)

    monkeypatch.setattr(accis, 'add_accis_to_idf', fake_add_accis_to_idf)
    idf = SimpleNamespace(idfobjects={'EnergyManagementSystem:Program': [_Program('SetAST')]})

    with pytest.warns(DeprecationWarning, match='accim.sim.accis_single_idf.addAccis is deprecated'):
        job = accis_single_idf.addAccis(idf, 'vrf_ac', 'temperature difference', 'standard', ['hourly'], False, False,
                                        None, '25.1', 'temperature')

    assert calls[0]['energyplus_version'] == '25.1' and calls[0]['setpoint_type'] == 'temperature'
    assert calls[0]['outputs_dataframe'] is None and 'make_outputs_dataframe' not in calls[0]
    assert job.arguments['ScriptType'] == 'vrf_ac' and job.arguments['EnergyPlus_version'] == '25.1'
    assert (job.occupied_zones, job.SetAST.Name, job.SetInputData) == (['Z1'], 'SetAST', None)


def test_modify_param_checks_the_name_of_the_parameter():
    with pytest.warns(DeprecationWarning), pytest.raises(ValueError, match='The Foo parameter you have entered'):
        accis_single_idf_funcs.modify_param(None, 'Foo', 1)
    with pytest.warns(DeprecationWarning):
        accis_single_idf_funcs.modify_param(None, 'comfstand', 1)


def test_apmv_setpoints_module_is_a_deprecated_alias_of_apmv(monkeypatch):
    monkeypatch.delitem(sys.modules, 'accim.sim.apmv_setpoints', raising=False)

    with pytest.warns(DeprecationWarning, match='use accim.sim.apmv instead'):
        module = importlib.import_module('accim.sim.apmv_setpoints')

    assert module.apply_apmv_setpoints is apmv.apply_apmv_setpoints
    assert module._resolve_targets is apmv._resolve_targets


def test_apmv_functions_have_pep8_arguments_and_accept_the_old_ones():
    assert 'other_pmv_related_outputs' in inspect.signature(apmv.apply_apmv_setpoints).parameters
    assert {'supply_air_temp_input_method', 'vrf_availability_schedule'} <= \
           set(inspect.signature(apmv.add_vrf_system).parameters)


def test_the_old_apmv_argument_names_are_arguments_of_the_new_functions():
    functions = [apmv.apply_apmv_setpoints, apmv.generate_df_from_args, apmv.add_vrf_system,
                 apmv.set_zones_always_occupied, apmv.add_ems_debug_output, apmv.set_pmv_input_parameters]
    new_names = set().union(*(inspect.signature(f).parameters for f in functions))

    assert set(apmv._LEGACY_ARGUMENTS.values()) <= new_names
    assert not set(apmv._LEGACY_ARGUMENTS) & new_names


def test_generate_df_from_args_accepts_the_names_of_accim_0x():
    values = dict(adap_coeff_cooling=0.3, adap_coeff_heating=-0.3, pmv_cooling_sp=0.4, pmv_heating_sp=-0.4,
                  tolerance_cooling_sp_cooling_season=-0.1, tolerance_cooling_sp_heating_season=-0.2,
                  tolerance_heating_sp_cooling_season=0.1, tolerance_heating_sp_heating_season=0.2)
    defaults = {f'dflt_for_{name}': 0 for name in values}

    with pytest.warns(DeprecationWarning, match='adap_coeff_cooling -> adaptive_coefficient_cooling'):
        df = apmv.generate_df_from_args(['Zone1 People'], ['Zone1_People'], **values, **defaults)

    expected = {apmv._LEGACY_ARGUMENTS[name]: value for name, value in values.items()}
    assert df.loc['Zone1 People', list(expected)].to_dict() == expected
    assert df.loc['Zone1 People', 'underscore_zonename'] == 'Zone1_People'


def test_change_adaptive_coeff_accepts_the_columns_of_accim_0x():
    program = SimpleNamespace(Name='set_zone_input_data_Zone1_People', Program_Line_1='', Program_Line_2='')
    building = SimpleNamespace(idfobjects={'EnergyManagementSystem:Program': [program]})
    df = pd.DataFrame({'adap_coeff_cooling': [0.3], 'adap_coeff_heating': [-0.2],
                       'underscore_zonename': ['Zone1_People']}, index=['Zone1 People'])

    with pytest.warns(DeprecationWarning, match='adap_coeff_cooling'):
        apmv.change_adaptive_coeff(building, df)

    # The EMS variables keep the names of accim 0.x
    assert program.Program_Line_1 == 'set adap_coeff_cooling_Zone1_People = 0.3'
    assert program.Program_Line_2 == 'set adap_coeff_heating_Zone1_People = -0.2'


def test_accepts_legacy_kwargs_only_renames_the_arguments_of_the_function():
    @accepts_legacy_kwargs({'oldName': 'new_name', 'otherOld': 'other_new'})
    def function(new_name=0):
        return new_name

    with pytest.warns(DeprecationWarning):
        assert function(oldName=2) == 2
    # other_new is not an argument of the function, so otherOld is an unexpected argument, as before
    with pytest.raises(TypeError, match='otherOld'):
        function(otherOld=1)


def test_accepts_legacy_kwargs():
    @accepts_legacy_kwargs({'oldName': 'new_name'})
    def function(new_name=0, other=0):
        return new_name, other

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        assert function(new_name=1, other=2) == (1, 2)
    with pytest.warns(DeprecationWarning, match='oldName -> new_name'):
        assert function(oldName=3) == (3, 0)
    assert list(inspect.signature(function).parameters) == ['new_name', 'other']


def test_deprecated_alias():
    def new_function(value_name=1):
        return value_name * 2

    old = deprecated_alias(new_function, 'module.oldFunction', 'module.new_function',
                           legacy_kwargs={'valueName': 'value_name'})

    assert old.__name__ == 'oldFunction'
    assert 'module.new_function' in old.__doc__
    with pytest.warns(DeprecationWarning, match='module.oldFunction is deprecated .* use module.new_function'):
        assert old(valueName=4) == 8


def test_rename_legacy_kwargs():
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        assert rename_legacy_kwargs({'a': 1}, {'A': 'a'}, 'f') == {'a': 1}
    with pytest.warns(DeprecationWarning):
        assert rename_legacy_kwargs({'A': 1, 'b': 2}, {'A': 'a'}, 'f') == {'a': 1, 'b': 2}
    with pytest.raises(TypeError, match="got the argument 'a' twice"):
        rename_legacy_kwargs({'A': 1, 'a': 2}, {'A': 'a'}, 'f')
