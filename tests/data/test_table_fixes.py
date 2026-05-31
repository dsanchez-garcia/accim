"""Regression tests for accim.data.postprocessing.Table fixes.

- idf_path=None now raises a clear ValueError instead of a cryptic
  ``AttributeError: 'dict' object has no attribute 'idfobjects'``.
- the 'unstack' reshaping path (which sits right after the fixed
  ``index=self.indexcols.remove('col_to_pivot')`` bug) produces a DataFrame.
"""

import glob
import gzip
import os
import shutil
from pathlib import Path

import pytest

import accim.utils

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CSV_DIR = REPO_ROOT / "accim" / "sample_files" / "sample_CSVs"
SAMPLE_IDF = (REPO_ROOT / "accim" / "sample_files" / "sample IDFs" / "input_IDFs"
              / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V960.idf")
GOLDEN_DIR = Path(__file__).parent / "golden"


def _require(version="9.6"):
    idd = accim.utils.get_idd_path_from_ep_version(version)
    if idd == "not-supported" or not os.path.exists(idd):
        pytest.skip(f"EnergyPlus {version} not installed")
    if not SAMPLE_IDF.exists() or not list(SAMPLE_CSV_DIR.glob("*.csv")):
        pytest.skip("sample IDF/CSVs missing")


def _copy_csvs(workdir):
    for f in glob.glob(str(SAMPLE_CSV_DIR / "*.csv")):
        shutil.copy(f, str(workdir))


def test_idf_path_none_raises_clear_error(tmp_path):
    _require()
    _copy_csvs(tmp_path)
    prev = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        from accim.data.postprocessing.main import Table
        with pytest.raises(ValueError, match="idf_path"):
            Table(
                source_frequency="hourly", frequency="runperiod",
                frequency_agg_func="sum", standard_outputs=True,
                level=["building"], level_agg_func=["sum", "mean"],
                level_excluded_zones=[], split_epw_names=True,
                idf_path=None,
            )
    finally:
        os.chdir(prev)


def test_unstack_reshaping_characterization(tmp_path, update_golden):
    _require()
    _copy_csvs(tmp_path)
    prev = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        from accim.data.postprocessing.main import Table
        t = Table(
            source_frequency="hourly", frequency="runperiod",
            frequency_agg_func="sum", standard_outputs=True,
            level=["building"], level_agg_func=["sum", "mean"],
            level_excluded_zones=[], split_epw_names=True,
            idf_path=str(SAMPLE_IDF),
        )
        t.format_table(type_of_table="energy demand")
        t.wrangled_table(
            reshaping="unstack", vars_to_gather=["ComfMod"], baseline="CM_0",
            comparison_mode="baseline compared to others",
            comparison_cols=["relative", "absolute"],
        )
        df = t.wrangled_df_unstacked
    finally:
        os.chdir(prev)

    df = df.reindex(sorted(df.columns), axis=1)
    actual = df.round(6).to_csv(index=True).replace("\r\n", "\n").encode("utf-8", "surrogateescape")
    assert actual.strip(), "wrangled_df_unstacked is empty"

    golden_file = GOLDEN_DIR / "table_unstack_runperiod.csv.gz"
    if update_golden or not golden_file.exists():
        golden_file.parent.mkdir(parents=True, exist_ok=True)
        golden_file.write_bytes(gzip.compress(actual, mtime=0))
        return
    expected = gzip.decompress(golden_file.read_bytes())
    if actual != expected:
        (GOLDEN_DIR / "table_unstack_runperiod.actual.csv").write_bytes(actual)
        pytest.fail("wrangled_df_unstacked changed (unstack reshaping).")
