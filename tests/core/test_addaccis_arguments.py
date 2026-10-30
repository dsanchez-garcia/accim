"""Tests for the arguments and prompts of AddAccis (addAccis in accim 0.x).

- supply_air_temp_input_method is only used by the VRF systems, but before, with script_type 'ex_ac' or
  'ex_mm', addAccis asked for all the arguments of the first stage when it was not given, and used
  the answers instead of the arguments of the call.
- When the setpoint accuracy (setpoint_acc) was left empty in the prompts, it was 100, while the
  default of the function is 10000.
- The prompts of the arguments of the output IDFs replaced name_suffix, verbose_mode and confirm_gen
  with their defaults.
"""
import builtins

import pytest

from accim.sim import accis, prompts
from accim.sim.generation import GenerationArguments

FIRST_STAGE_ARGS_WITHOUT_SUPPLY_AIR = dict(
    output_type='standard',
    output_freqs=['hourly'],
    output_keep_existing=False,
    temp_ctrl='temp',
)


class _ReachedLoadIdf(Exception):
    """Raised by the load_idf stub: AddAccis validated its arguments and started reading the IDFs."""


def _stub_load_idf(path, energyplus_version='auto'):
    raise _ReachedLoadIdf(energyplus_version)


def _no_prompts(prompt=''):
    raise AssertionError(f'Unexpected prompt: {prompt}')


@pytest.mark.parametrize('script_type', ['ex_ac', 'ex_mm'])
def test_existing_hvac_does_not_need_supply_air_temp_input_method(monkeypatch, script_type):
    monkeypatch.setattr(accis, 'load_idf', _stub_load_idf)
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    with pytest.raises(_ReachedLoadIdf):
        accis.AddAccis(idfs=['model.idf'], script_type=script_type, verbose_mode=False,
                       **FIRST_STAGE_ARGS_WITHOUT_SUPPLY_AIR)


def test_vrf_system_still_asks_for_supply_air_temp_input_method(monkeypatch):
    monkeypatch.setattr(accis, 'load_idf', _stub_load_idf)
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    with pytest.raises(AssertionError, match='Enter the ScriptType'):
        accis.AddAccis(idfs=['model.idf'], script_type='vrf_ac', **FIRST_STAGE_ARGS_WITHOUT_SUPPLY_AIR)


@pytest.mark.parametrize('arguments, message', [
    (dict(script_type='vrf', supply_air_temp_input_method='temperature difference'), 'is not a valid script_type'),
    (dict(script_type='vrf_ac', supply_air_temp_input_method='difference'),
     'is not a valid supply_air_temp_input_method'),
])
def test_invalid_arguments_are_rejected_before_reading_the_idfs(monkeypatch, arguments, message):
    monkeypatch.setattr(accis, 'load_idf', _stub_load_idf)

    with pytest.raises(ValueError, match=message):
        accis.AddAccis(idfs=['model.idf'], verbose_mode=False, **arguments, **FIRST_STAGE_ARGS_WITHOUT_SUPPLY_AIR)


def test_input_files_skip_the_output_idfs(tmp_path, monkeypatch):
    for name in ['b.idf', 'a.idf', 'a[CS_INT EN16798[NS_X.idf', 'a_pymod.idf', 'notes.txt']:
        (tmp_path / name).write_text('')
    monkeypatch.chdir(tmp_path)

    assert accis._input_files(None) == ['a.idf', 'b.idf']
    assert accis._input_files('b.idf') == ['b.idf']
    with pytest.raises(FileNotFoundError):
        accis._input_files(['notes.txt'])


def _scripted_answers(prompts_seen):
    def scripted_input(prompt=''):
        prompts_seen.append(prompt)
        if 'Comfort Standard numbers' in prompt:
            return '1'
        if prompt == '):':
            return '1'  # category
        if 'Comfort Mode numbers' in prompt:
            return '3'
        if 'Are you sure' in prompt:
            return 'y'
        return ''  # the defaults
    return scripted_input


def test_setpoint_accuracy_left_empty_in_the_prompts_is_10000():
    prompts_seen = []

    args = prompts.ask_generation_arguments('vrf_ac', ask=_scripted_answers(prompts_seen))

    assert args['setpoint_acc'] == 10000
    assert any('if omitted will be 10000' in p for p in prompts_seen)
    assert (args['comf_stand'], args['cat'], args['comf_mod']) == ([1], [1], [3.0])
    assert args['ast_tol_start'] == args['ast_tol_end_input'] == args['ast_tol_steps'] == 0.1
    # Fully air-conditioned: no natural ventilation
    assert args['hvac_mode'] == [0]


def test_the_prompts_keep_the_name_suffix_of_the_call(monkeypatch):
    monkeypatch.setattr(builtins, 'input', _scripted_answers([]))

    generation = accis.AddAccis._generation_arguments(
        'vrf_ac', comf_stand=None, cat=None, cat_cool_offset=0, cat_heat_offset=0, comf_mod=None, setpoint_acc=10000,
        cust_ast_acst_aul=0, cust_ast_acst_all=0, cust_ast_ahst_aul=0, cust_ast_ahst_all=0, cust_ast_m=0,
        cust_ast_n=0, cust_ast_acst_offset=0, cust_ast_ahst_offset=0, cool_season_start=121, cool_season_end=274,
        hvac_mode=None, vent_ctrl=None, max_temp_diff_vof=6, min_temp_diff_vof=1, multiplier_vof=0.25,
        vst_offset=[0], min_ot_offset=[50], max_wind_speed=[50], ast_tol_start=0.1, ast_tol_end_input=0.1,
        ast_tol_steps=0.1, name_suffix='suffix')

    assert isinstance(generation, GenerationArguments)
    assert generation.name_suffix == 'suffix'
    assert (generation.comf_stand, generation.cat, generation.comf_mod) == ([1], [1], [3.0])


def test_arguments_are_also_available_with_the_names_of_accim_0x():
    arguments = accis._Arguments(script_type='vrf_ac', comf_stand=[1])

    with pytest.warns(DeprecationWarning, match="arguments\\['ScriptType'\\] is deprecated"):
        assert arguments['ScriptType'] == 'vrf_ac'
    with pytest.raises(KeyError):
        arguments['NotAnArgument']
