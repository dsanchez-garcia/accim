"""Characterization (golden-file) tests for accim.data.postprocessing.Table.

Freezes the DataFrame produced by Table from the shipped sample CSVs, so any
accidental change to the post-processing/aggregation logic is detected. Table
reads the per-zone IDF to resolve zones; the sample CSVs come from a V22.2 model
whose IDD may not be installed, so we pass the structurally-identical V9.6 sample
IDF as ``idf_path`` (same Block1:Zone1/Zone2 layout).

Bootstrap:
    pytest tests/data --update-golden
"""

import difflib
import gzip
import os
import shutil
import glob
from pathlib import Path

import pytest

import accim.utils

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CSV_DIR = REPO_ROOT / "accim" / "sample_files" / "sample_CSVs"
SAMPLE_IDF = (REPO_ROOT / "accim" / "sample_files" / "sample IDFs" / "input_IDFs"
              / "TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V960.idf")
GOLDEN_DIR = Path(__file__).parent / "golden"

CONFIGS = ["runperiod", "monthly"]


def _require(version="9.6"):
    idd = accim.utils.get_idd_path_from_ep_version(version)
    if idd == "not-supported" or not os.path.exists(idd):
        pytest.skip(f"EnergyPlus {version} not installed (IDD missing: {idd})")
    if not SAMPLE_IDF.exists():
        pytest.skip(f"sample IDF missing: {SAMPLE_IDF}")
    if not list(SAMPLE_CSV_DIR.glob("*.csv")):
        pytest.skip(f"no sample CSVs in {SAMPLE_CSV_DIR}")


def _build_canonical_df(workdir, frequency):
    """Build a Table from the sample CSVs and return a canonical, deterministic
    serialization of its DataFrame (sorted columns, rounded floats)."""
    for f in glob.glob(str(SAMPLE_CSV_DIR / "*.csv")):
        shutil.copy(f, str(workdir))
    prev = os.getcwd()
    os.chdir(str(workdir))
    try:
        from accim.data.postprocessing.main import Table
        t = Table(
            source_frequency="hourly",
            frequency=frequency,
            frequency_agg_func="sum",
            standard_outputs=True,
            level=["building"],
            level_agg_func=["sum", "mean"],
            level_excluded_zones=[],
            split_epw_names=True,
            idf_path=str(SAMPLE_IDF),
        )
    finally:
        os.chdir(prev)
    df = t.df
    df = df.reindex(sorted(df.columns), axis=1)
    return df.round(6).to_csv(index=True).replace("\r\n", "\n").encode("utf-8", "surrogateescape")


def _short_diff(expected, actual, max_lines=40):
    exp = expected.decode("latin-1").splitlines()
    act = actual.decode("latin-1").splitlines()
    diff = list(difflib.unified_diff(exp, act, "golden", "actual", lineterm=""))
    if len(diff) > max_lines:
        diff = diff[:max_lines] + [f"... (+{len(diff) - max_lines} more lines)"]
    return "\n".join(diff)


@pytest.mark.parametrize("frequency", CONFIGS, ids=CONFIGS)
def test_table_characterization(frequency, tmp_path, update_golden):
    _require()
    actual = _build_canonical_df(tmp_path, frequency)
    assert actual.strip(), "Table produced an empty DataFrame"

    golden_file = GOLDEN_DIR / (f"table_{frequency}.csv.gz")
    if update_golden or not golden_file.exists():
        golden_file.parent.mkdir(parents=True, exist_ok=True)
        golden_file.write_bytes(gzip.compress(actual, mtime=0))
        return
    expected = gzip.decompress(golden_file.read_bytes())
    if actual != expected:
        (GOLDEN_DIR / f"table_{frequency}.actual.csv").write_bytes(actual)
        pytest.fail(f"Table DataFrame changed for frequency '{frequency}'.\n"
                    + _short_diff(expected, actual))
