"""Tests for the interactive prompt layer (accim.sim.prompts).

These give coverage to the interactive code path (which the golden tests do not
exercise, since they always pass explicit arguments) by mocking builtins.input
with a scripted sequence of answers.
"""

import builtins

import pytest

from accim.sim import prompts


def _scripted_input(answers):
    it = iter(answers)

    def fake_input(prompt=""):
        return next(it)

    return fake_input


def test_collect_basic_inputs_vrf(monkeypatch):
    answers = [
        "vrf_mm",                    # ScriptType
        "supply air temperature",    # SupplyAirTempInputMethod (vrf only)
        "false",                     # keep existing outputs
        "standard",                  # Output type
        "hourly",                    # Output freqs
        "false",                     # generate dataframe
        "auto",                      # EnergyPlus version
        "temperature",               # Temp control
    ]
    monkeypatch.setattr(builtins, "input", _scripted_input(answers))
    result = prompts.collect_basic_inputs()
    assert result == {
        "script_type": "vrf_mm",
        "supply_air_temp_method": "supply air temperature",
        "output_keep_existing": "false",
        "output_type": "standard",
        "output_freqs": ["hourly"],
        "output_gen_dataframe": False,
        "energyplus_version": "auto",
        "temp_control": "temperature",
    }


def test_collect_basic_inputs_ex_has_no_supply_method(monkeypatch):
    # ex_* script types must NOT prompt for the supply air temperature method.
    answers = [
        "ex_mm",                     # ScriptType
        "true",                      # keep existing outputs
        "detailed",                  # Output type
        "hourly runperiod",          # Output freqs (two)
        "true",                      # generate dataframe
        "9.6",                       # EnergyPlus version
        "pmv",                       # Temp control
    ]
    monkeypatch.setattr(builtins, "input", _scripted_input(answers))
    result = prompts.collect_basic_inputs()
    assert result["script_type"] == "ex_mm"
    assert result["supply_air_temp_method"] is None
    assert result["output_freqs"] == ["hourly", "runperiod"]
    assert result["output_gen_dataframe"] is True
    assert result["temp_control"] == "pmv"


def test_collect_basic_inputs_retries_on_invalid(monkeypatch):
    # An invalid ScriptType must be re-prompted until a valid one is entered.
    answers = [
        "not_a_type",                # invalid ScriptType -> retry
        "vrf_ac",                    # valid ScriptType
        "temperature difference",    # SupplyAirTempInputMethod
        "false",                     # keep existing
        "simplified",               # Output type
        "monthly",                   # Output freqs
        "false",                     # generate dataframe
        "25.1",                      # EnergyPlus version
        "temp",                      # Temp control
    ]
    monkeypatch.setattr(builtins, "input", _scripted_input(answers))
    result = prompts.collect_basic_inputs()
    assert result["script_type"] == "vrf_ac"
    assert result["supply_air_temp_method"] == "temperature difference"
    assert result["output_type"] == "simplified"
