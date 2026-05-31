"""Method-level tests for accim.data.postprocessing.Table.

Exercises the construction and the working format_table presets on the shipped
sample CSVs (passing the structurally-identical V9.6 sample IDF as idf_path).
"""

import glob
import os
import shutil
from pathlib import Path

import pytest

import accim.utils

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CSV_DIR = REPO_ROOT / "accim" / "sample_files" / "sample_CSVs"
SAMPLE_IDF = (REPO_ROOT / "accim" / "sample_files" / "sample IDFs" / "input_IDFs"
              / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V960.idf")


def _require():
    idd = accim.utils.get_idd_path_from_ep_version("9.6")
    if idd == "not-supported" or not os.path.exists(idd):
        pytest.skip("EnergyPlus 9.6 not installed")
    if not SAMPLE_IDF.exists() or not list(SAMPLE_CSV_DIR.glob("*.csv")):
        pytest.skip("sample IDF/CSVs missing")


def _build(workdir, frequency="runperiod"):
    for f in glob.glob(str(SAMPLE_CSV_DIR / "*.csv")):
        shutil.copy(f, str(workdir))
    prev = os.getcwd()
    os.chdir(str(workdir))
    try:
        from accim.data.postprocessing.main import Table
        return Table(
            source_frequency="hourly", frequency=frequency,
            frequency_agg_func="sum", standard_outputs=True,
            level=["building"], level_agg_func=["sum", "mean"],
            level_excluded_zones=[], split_epw_names=True,
            idf_path=str(SAMPLE_IDF),
        )
    finally:
        os.chdir(prev)


def test_construction_hourly_smoke(tmp_path):
    _require()
    t = _build(tmp_path, "hourly")
    # 4 CSVs x 8760 hours, and the wide set of standard output columns.
    assert t.df.shape[0] == 4 * 8760
    assert t.df.shape[1] > 100


@pytest.mark.parametrize("type_of_table", ["energy demand", "comfort hours", "temperature"])
def test_format_table_presets(tmp_path, type_of_table):
    _require()
    t = _build(tmp_path, "runperiod")
    t.format_table(type_of_table=type_of_table)
    assert len(t.val_cols) > 0, f"{type_of_table} selected no value columns"
    # the formatted df keeps the index columns + the selected value columns
    for c in t.val_cols:
        assert c in t.df.columns


def test_format_table_custom(tmp_path):
    _require()
    t = _build(tmp_path, "runperiod")
    t.format_table(
        type_of_table="custom",
        custom_cols=["Building_Total_Cooling Energy Demand"],
    )
    assert len(t.val_cols) > 0


def test_format_table_custom_empty_raises(tmp_path):
    _require()
    t = _build(tmp_path, "runperiod")
    with pytest.raises(ValueError):
        t.format_table(type_of_table="custom", custom_cols=["__no_such_column__"])
