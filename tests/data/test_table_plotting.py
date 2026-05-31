"""Tests for the plotting pipeline of accim.data.postprocessing.Table.

Both the data-preparation method (generate_fig_data) and the figure-drawing
method (scatter_plot) are exercised end to end on a headless (Agg) backend. Two
matplotlib-version incompatibilities in scatter_plot were fixed for this to work:
``Axes.get_shared_y_axes().join()`` (removed in matplotlib >= 3.6, replaced by
``Axes.sharey()``) and ``Legend.legendHandles`` (renamed to ``legend_handles`` in
matplotlib >= 3.7).

Interactive rename prompts are avoided by passing (identity) renaming dicts.
"""

import glob
import os
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend

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


def _build_hourly(workdir):
    for f in glob.glob(str(SAMPLE_CSV_DIR / "*.csv")):
        shutil.copy(f, str(workdir))
    prev = os.getcwd()
    os.chdir(str(workdir))
    try:
        from accim.data.postprocessing.main import Table
        t = Table(
            source_frequency="hourly", frequency="hourly",
            frequency_agg_func="sum", standard_outputs=True,
            level=["building"], level_agg_func=["sum", "mean"],
            level_excluded_zones=[], split_epw_names=True,
            idf_path=str(SAMPLE_IDF),
        )
    finally:
        os.chdir(prev)
    return t


def _cols(t):
    cols = list(t.df.columns)

    def find(sub):
        return [c for c in cols if sub in c][0]

    return {
        "x": find("EN16798-1 Running mean outdoor temperature"),
        "cool_sp": find("Adaptive Cooling Setpoint Temperature_No Tolerance"),
        "op_temp": find("Building_Total_Zone Operative Temperature"),
        "cool_dem": find("Building_Total_Cooling Energy Demand"),
    }


def test_generate_fig_data_builds_structures(tmp_path):
    _require()
    t = _build_hourly(tmp_path)
    c = _cols(t)
    t.generate_fig_data(
        vars_to_gather_rows=["ComfMod", "CAT"],
        vars_to_gather_cols=["EPW_City_or_subcountry"],
        detailed_rows=[], detailed_cols=[], data_on_y_axis_baseline_plot=[],
        data_on_x_axis=c["x"],
        data_on_y_main_axis=[["Top (C)", [c["cool_sp"], c["op_temp"]]]],
        colorlist_y_main_axis=[["Top (C)", ["b", "r"]]],
        best_fit_deg_y_main_axis=[["Top (C)", [1, 1]]],
        data_on_y_sec_axis=[["Energy", [c["cool_dem"]]]],
        colorlist_y_sec_axis=[["Energy", ["g"]]],
        best_fit_deg_y_sec_axis=[["Energy", [1]]],
        rows_renaming_dict={}, cols_renaming_dict={},
    )
    # rows = ComfMod x CAT combinations, cols = the two cities.
    assert len(t.rows) >= 2
    assert sorted(t.cols) == ["Aberdeen", "London"]
    assert hasattr(t, "y_list_main") and len(t.y_list_main) == len(t.rows)
    assert hasattr(t, "df_for_graph")


def test_scatter_plot_produces_figure(tmp_path):
    _require()
    t = _build_hourly(tmp_path)
    c = _cols(t)
    # Identity renaming dicts populate the row/col label lists (avoiding the
    # interactive rename prompt without leaving the label lists empty).
    row_vals = [f"{cm}[{cat}" for cm in sorted(set(t.df["ComfMod"]))
                for cat in sorted(set(t.df["CAT"]))]
    col_vals = sorted(set(t.df["EPW_City_or_subcountry"]))
    prev = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        t.scatter_plot(
            vars_to_gather_rows=["ComfMod", "CAT"],
            vars_to_gather_cols=["EPW_City_or_subcountry"],
            detailed_rows=[], detailed_cols=[],
            data_on_x_axis=c["x"],
            data_on_y_main_axis=[["Top (C)", [c["cool_sp"], c["op_temp"]]]],
            colorlist_y_main_axis=[["Top (C)", ["b", "r"]]],
            best_fit_deg_y_main_axis=[["Top (C)", [1, 1]]],
            data_on_y_sec_axis=[["Energy", [c["cool_dem"]]]],
            colorlist_y_sec_axis=[["Energy", ["g"]]],
            best_fit_deg_y_sec_axis=[["Energy", [1]]],
            rows_renaming_dict={r: r for r in row_vals},
            cols_renaming_dict={cv: cv for cv in col_vals},
            supxlabel="RMOT", figname="scatter_test", figsize=4,
            ratio_height_to_width=0.4, confirm_graph=True,
        )
        figs = [f for f in os.listdir(tmp_path) if f.endswith(".png")]
    finally:
        os.chdir(prev)
    assert any("scatter_test" in f for f in figs), f"no figure produced: {figs}"


def test_time_plot_produces_figure(tmp_path):
    _require()
    t = _build_hourly(tmp_path)
    c = _cols(t)
    row_vals = [f"{cm}[{cat}" for cm in sorted(set(t.df["ComfMod"]))
                for cat in sorted(set(t.df["CAT"]))]
    col_vals = sorted(set(t.df["EPW_City_or_subcountry"]))
    prev = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        t.time_plot(
            vars_to_gather_rows=["ComfMod", "CAT"],
            vars_to_gather_cols=["EPW_City_or_subcountry"],
            detailed_rows=[], detailed_cols=[],
            data_on_y_main_axis=[["Top (C)", [c["cool_sp"], c["op_temp"]]]],
            colorlist_y_main_axis=[["Top (C)", ["b", "r"]]],
            data_on_y_sec_axis=[["Energy", [c["cool_dem"]]]],
            colorlist_y_sec_axis=[["Energy", ["g"]]],
            rows_renaming_dict={r: r for r in row_vals},
            cols_renaming_dict={cv: cv for cv in col_vals},
            figname="time_test", figsize=4, confirm_graph=True,
        )
        figs = [f for f in os.listdir(tmp_path) if f.endswith(".png")]
    finally:
        os.chdir(prev)
    assert any("time_test" in f for f in figs), f"no figure produced: {figs}"
