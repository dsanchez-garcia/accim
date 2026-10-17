"""Tests for the arguments and prompts of addAccis.

- SupplyAirTempInputMethod is only used by the VRF systems, but before, with ScriptType 'ex_ac' or
  'ex_mm', addAccis asked for all the arguments of the first stage when it was not given, and used
  the answers instead of the arguments of the call.
- When the setpoint accuracy (SetpointAcc) was left empty in the prompts, it was 100, while the
  default of the function is 10000.
"""
import builtins
from types import SimpleNamespace

import pytest

import accim.sim.accim_Main as accim_Main
from accim.sim import accis
from accim.sim.accim_IDFgeneration import inputData

FIRST_STAGE_ARGS_WITHOUT_SUPPLY_AIR = dict(
    Output_type='standard',
    Output_freqs=['hourly'],
    Output_keep_existing=False,
    TempCtrl='temp',
)


class _ReachedAccimJob(Exception):
    """Raised by the accimJob stub: addAccis validated its arguments and started with the IDFs."""


def _stub_accim_job(*args, **kwargs):
    raise _ReachedAccimJob(kwargs.get('ScriptType'))


def _no_prompts(prompt=''):
    raise AssertionError(f'Unexpected prompt: {prompt}')


@pytest.mark.parametrize('script_type', ['ex_ac', 'ex_mm'])
def test_existing_hvac_does_not_need_supply_air_temp_input_method(monkeypatch, script_type):
    monkeypatch.setattr(accim_Main, 'accimJob', _stub_accim_job)
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    with pytest.raises(_ReachedAccimJob) as reached:
        accis.addAccis(idfs=['model.idf'], ScriptType=script_type, **FIRST_STAGE_ARGS_WITHOUT_SUPPLY_AIR)

    assert str(reached.value) == script_type


def test_vrf_system_still_asks_for_supply_air_temp_input_method(monkeypatch):
    monkeypatch.setattr(accim_Main, 'accimJob', _stub_accim_job)
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    with pytest.raises(AssertionError, match='Enter the ScriptType'):
        accis.addAccis(idfs=['model.idf'], ScriptType='vrf_ac', **FIRST_STAGE_ARGS_WITHOUT_SUPPLY_AIR)


class _StopPrompts(Exception):
    """Raised when the prompts reach the arguments after SetpointAcc."""


def test_setpoint_accuracy_left_empty_in_the_prompts_is_10000(monkeypatch):
    prompts = []

    def scripted_input(prompt=''):
        prompts.append(prompt)
        if 'Comfort Standard numbers' in prompt:
            return '1'
        if prompt == '):':
            return '1'  # category
        if 'Comfort Mode numbers' in prompt:
            return '3'
        if 'setpoint accuracy' in prompt:
            return ''
        if 'Are you sure' in prompt:
            return 'y'
        raise _StopPrompts(prompt)

    monkeypatch.setattr(builtins, 'input', scripted_input)
    job = SimpleNamespace()

    with pytest.raises(_StopPrompts, match='CAT cooling offset'):
        inputData(job, ScriptType='vrf_ac')

    assert job.SetpointAcc == 10000
    assert any('if omitted will be 10000' in p for p in prompts)
