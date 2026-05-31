"""Tests for accim.run.run.

run_ep() itself launches EnergyPlus, so it is exercised here with the heavy parts
(IDD setup, file discovery, runIDFs) mocked, to verify the control flow — in
particular the fixed bug where an unsupported EnergyPlus version was re-prompted
without re-resolving the IDD path (so IDF.setiddname received 'not-supported').
"""

import builtins
import os
import types

import pytest

import accim.run.run as runmod


# --------------------------------------------------------------------------- #
# make_eplaunch_options
# --------------------------------------------------------------------------- #
def _stub_idf(version="9.6.0", idfname="model.idf"):
    ver = types.SimpleNamespace(Version_Identifier=version)
    return types.SimpleNamespace(idfobjects={"version": [ver]}, idfname=idfname)


def test_make_eplaunch_options_basic():
    idf = _stub_idf(version="9.6.0", idfname="model.idf")
    opts = runmod.make_eplaunch_options(idf, "weather.epw")
    assert opts["ep_version"] == "9-6-0"
    assert opts["output_suffix"] == "C"
    assert opts["readvars"] is True
    assert opts["expandobjects"] is True
    # output_prefix = basename(idfname + '_' + epw_stem).split('.idf')[0] + '[' + epw_stem
    assert opts["output_prefix"] == "model[weather"


def test_make_eplaunch_options_pads_two_part_version():
    idf = _stub_idf(version="23.1", idfname="m.idf")
    opts = runmod.make_eplaunch_options(idf, "city.epw")
    assert opts["ep_version"] == "23-1-0"  # padded to three parts


# --------------------------------------------------------------------------- #
# removefiles
# --------------------------------------------------------------------------- #
def test_removefiles_keeps_and_deletes(tmp_path, monkeypatch):
    keep = ["a.py", "b.idf", "c.epw", "d.csv", "e.eso"]
    delete = ["f.txt", "g.html", "h.err", "iTable.csv", "jMeter.csv", "kZsz.csv"]
    for name in keep + delete:
        (tmp_path / name).write_text("x")
    monkeypatch.chdir(tmp_path)
    runmod.removefiles()
    remaining = set(os.listdir(tmp_path))
    # plain .csv kept, but the Table/Meter/Zsz.csv ones are deleted in the 2nd pass
    assert remaining == {"a.py", "b.idf", "c.epw", "d.csv", "e.eso"}


def test_run_ep_reprompts_and_reresolves_idd(monkeypatch):
    calls = {"setidd": [], "runIDFs": 0}

    # First version is unsupported; the user then enters a supported one.
    def fake_get_idd(EnergyPlus_version=None):
        return "not-supported" if EnergyPlus_version == "99.9" else "C:/fake/Energy+.idd"

    monkeypatch.setattr(runmod, "get_idd_path_from_ep_version", fake_get_idd)
    monkeypatch.setattr(runmod.IDF, "setiddname", staticmethod(lambda p: calls["setidd"].append(p)))
    monkeypatch.setattr(runmod.os, "listdir", lambda *a, **k: [])  # no idf/epw -> no runs
    monkeypatch.setattr(runmod, "runIDFs", lambda runs, n: calls.__setitem__("runIDFs", calls["runIDFs"] + 1))
    monkeypatch.setattr(builtins, "input", lambda prompt="": "9.6")

    runmod.run_ep(run_only_accim=True, confirm_run=True, energyplus_version="99.9")

    # The IDD must be resolved to the supported version, never to 'not-supported'.
    assert calls["setidd"] == ["C:/fake/Energy+.idd"]
    assert calls["runIDFs"] == 1


def test_prompt_helpers(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt="": "y")
    assert runmod._prompt_run_only_accim() == "y"
    assert runmod._prompt_confirm_run(5) == "y"
    monkeypatch.setattr(builtins, "input", lambda prompt="": "24.2")
    assert runmod._prompt_energyplus_version() == "24.2"
