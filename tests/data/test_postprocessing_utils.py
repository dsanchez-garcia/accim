"""Tests for accim.data.postprocessing.utils (preview_Table_cols, genCSVconcatenated)."""

import glob
import os
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CSV_DIR = REPO_ROOT / "accim" / "sample_files" / "sample_CSVs"


def _require_csvs():
    if not list(SAMPLE_CSV_DIR.glob("*.csv")):
        pytest.skip("sample CSVs missing")


def _copy_csvs(workdir):
    for f in glob.glob(str(SAMPLE_CSV_DIR / "*.csv")):
        shutil.copy(f, str(workdir))


def test_preview_table_cols_from_cwd(tmp_path, monkeypatch):
    _require_csvs()
    _copy_csvs(tmp_path)
    monkeypatch.chdir(tmp_path)
    from accim.data.postprocessing.utils import preview_Table_cols
    cols = preview_Table_cols()
    assert isinstance(cols, list) and len(cols) > 5
    assert "Date/Time" in cols


def test_preview_table_cols_with_datasets(tmp_path, monkeypatch):
    _require_csvs()
    _copy_csvs(tmp_path)
    monkeypatch.chdir(tmp_path)
    from accim.data.postprocessing.utils import preview_Table_cols
    files = [os.path.basename(f) for f in glob.glob(str(tmp_path / "*.csv"))]
    cols = preview_Table_cols(datasets=files)
    assert "Date/Time" in cols


def test_gen_csv_concatenated_writes_file(tmp_path, monkeypatch):
    # genCSVconcatenated builds per-chunk Table instances with concatenated_csv_name
    # set, which save + return early (before any IDF zone scanning), so no idf_path
    # is needed here.
    _require_csvs()
    _copy_csvs(tmp_path)
    monkeypatch.chdir(tmp_path)
    from accim.data.postprocessing.utils import genCSVconcatenated
    genCSVconcatenated(
        source_frequency="hourly", frequency="runperiod",
        concatenated_csv_name="gen", datasets_per_chunk=2, drop_nan=True,
    )
    final = [f for f in os.listdir(tmp_path)
             if f.startswith("gen[") and f.endswith("CSVconcatenated.csv")]
    assert len(final) == 1, f"concatenated CSV not produced: {os.listdir(tmp_path)}"
    # the per-chunk part files are cleaned up
    assert not [f for f in os.listdir(tmp_path) if "_Part" in f]
