"""Tests for accim.data.postprocessing.main.Table.time_plot with pandas 3.

Before, time_plot read the first date with Series[0], which pandas 3 takes as a label (KeyError: 0),
and built the dates with the frequency aliases 'H' and 'M', which pandas 3 no longer accepts.
The test uses the first 48 hours of two of the CSVs of the sample notebook of Table.
"""
import builtins
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import pandas as pd
import pytest

from accim.data.postprocessing.main import Table

TABLE_DIR = Path(__file__).resolve().parents[2] / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'Table'
MODEL = 'TestModel[CS_INT EN16798[CA_1[CM_0[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_X'
HOURS = 48

pytestmark = pytest.mark.skipif(not TABLE_DIR.is_dir(), reason='needs the sample files of the repository')


@pytest.fixture
def hourly_table(tmp_path, monkeypatch):
    shutil.copy(TABLE_DIR / 'TestModel.idf', tmp_path)
    for city in ['Aberdeen', 'London']:
        csv_name = f'{MODEL}[United-Kingdom_{city}_Present.csv'
        lines = (TABLE_DIR / csv_name).read_bytes().splitlines(keepends=True)
        (tmp_path / csv_name).write_bytes(b''.join(lines[:HOURS + 1]))
    monkeypatch.chdir(tmp_path)
    return Table(
        source_frequency='hourly',
        frequency='hourly',
        frequency_agg_func='sum',
        standard_outputs=True,
        level=['building'],
        level_agg_func=['mean'],
        level_excluded_zones=[],
        split_epw_names=True,
        idf_path='TestModel.idf',
    )


def test_time_plot_builds_hourly_dates(hourly_table, tmp_path, monkeypatch):
    # Answer 'n' to the questions about renaming the rows and columns of subplots.
    monkeypatch.setattr(builtins, 'input', lambda prompt='': 'n')
    temperature = next(c for c in hourly_table.df.columns
                       if c.startswith('Building_Total_Zone Operative Temperature'))

    hourly_table.time_plot(
        vars_to_gather_rows=['EPW'],
        vars_to_gather_cols=['ComfMod'],
        data_on_y_main_axis=[['Temperature', [temperature]]],
        colorlist_y_main_axis=[['Temperature', ['g']]],
        figname='time_plot_test',
        figsize=2,
        dpi=50,
        confirm_graph=True,
    )

    dates = hourly_table.df_for_graph['Date/time']
    assert dates.iloc[0] == pd.Timestamp('1900-01-01 01:00')
    assert (dates.diff().dropna() == pd.Timedelta(hours=1)).all()
    assert (tmp_path / 'time_plot_test.png').exists()
