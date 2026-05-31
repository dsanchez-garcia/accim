"""Tests for the IDF-based helpers in accim.utils (need a sample IDF + IDD)."""

import os
from pathlib import Path

import pytest

import accim.utils

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO_ROOT / "accim" / "sample_files" / "sample IDFs" / "input_IDFs"
              / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V960.idf")


def _building():
    idd = accim.utils.get_idd_path_from_ep_version("9.6")
    if idd == "not-supported" or not os.path.exists(idd):
        pytest.skip("EnergyPlus 9.6 not installed")
    if not SAMPLE_IDF.exists():
        pytest.skip(f"sample IDF missing: {SAMPLE_IDF}")
    from besos.eppy_funcs import get_building
    return get_building(str(SAMPLE_IDF))


def test_get_idf_hierarchy():
    b = _building()
    h = accim.utils.get_idf_hierarchy(b)
    assert set(h.keys()) == {"zones", "groups"}
    zone_names = [z.lower() for z in h["zones"]]
    assert any("zone1" in z for z in zone_names)
    assert any("zone2" in z for z in zone_names)


def test_get_available_fields_idd_and_idf():
    b = _building()
    fields_idd = accim.utils.get_available_fields(b, "Zone", source="idd")
    assert "Name" in fields_idd
    fields_idf = accim.utils.get_available_fields(b, "Zone", source="idf")
    assert "Name" in fields_idf


def test_get_available_fields_invalid_source():
    b = _building()
    with pytest.raises(ValueError):
        accim.utils.get_available_fields(b, "Zone", source="bogus")


def test_modify_timesteps():
    b = _building()
    accim.utils.modify_timesteps(b, 6)
    ts = b.idfobjects["Timestep"][0]
    assert int(ts.Number_of_Timesteps_per_Hour) == 6
    with pytest.raises(ValueError):
        accim.utils.modify_timesteps(b, 7)  # not an allowable value


def test_set_occupancy_to_always_adds_schedule():
    b = _building()
    accim.utils.set_occupancy_to_always(b)
    sched_names = [s.Name for s in b.idfobjects["Schedule:Compact"]]
    assert "On 24/7" in sched_names


def test_get_people_hierarchy_and_names():
    b = _building()
    hierarchy = accim.utils.get_people_hierarchy(b)
    assert len(hierarchy) == 2
    for data in hierarchy.values():
        assert "affected_spaces" in data and "target_ref" in data

    names = accim.utils.get_people_names_for_ems(b, output_format="list")
    assert isinstance(names, list)
    names_dict = accim.utils.get_people_names_for_ems(b, output_format="dict")
    assert set(names_dict.keys()) == set(hierarchy.keys())


def test_reduce_runtime():
    b = _building()
    accim.utils.reduce_runtime(
        b,
        minimal_shadowing=True,
        timesteps=4,
        runperiod_begin_month=6, runperiod_begin_day_of_month=1,
        runperiod_end_month=7, runperiod_end_day_of_month=31,
    )
    assert b.idfobjects["Building"][0].Solar_Distribution == "MinimalShadowing"
    rp = b.idfobjects["Runperiod"][0]
    assert int(rp.Begin_Month) == 6 and int(rp.End_Month) == 7
    assert int(b.idfobjects["Timestep"][0].Number_of_Timesteps_per_Hour) == 4

    with pytest.raises(ValueError):
        accim.utils.reduce_runtime(b, timesteps=1)  # below allowed range
