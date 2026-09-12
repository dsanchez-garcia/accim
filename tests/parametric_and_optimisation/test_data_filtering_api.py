import matplotlib
import pandas as pd
import pytest

matplotlib.use('Agg')

from accim.parametric_and_optimisation.plotting import PlottingMixin
from accim.parametric_and_optimisation.utils import apply_data_filter


class _DummyFilterSession(PlottingMixin):
    def __init__(self):
        self.outputs_normalized = False
        self.building_floor_area = 140.0
        self.outputs_param_simulation = self._build_df()
        self.outputs_optimisation = self.outputs_param_simulation.copy()

    @staticmethod
    def _build_df() -> pd.DataFrame:
        rows = []
        for idf_name in ['idf_A', 'idf_B']:
            for epw_name in ['Seville.epw', 'Sydney.epw', 'Madrid.epw']:
                for comf_stand in [0, 1, 2]:
                    rows.append(
                        {
                            'idf': idf_name,
                            'epw': epw_name,
                            'ComfStand': comf_stand,
                            'HVACmode': comf_stand,
                            'performance': 'high' if comf_stand <= 1 else 'low',
                            'pareto-optimal': bool(comf_stand % 2 == 0),
                            'Heating:Electricity [J]': 10_000_000 + 200_000 * comf_stand,
                            'Cooling:Electricity [J]': 8_000_000 + 150_000 * comf_stand,
                        }
                    )
        return pd.DataFrame(rows)


def test_apply_data_filter_include_exclude_query():
    df = pd.DataFrame(
        {
            'epw': ['Seville.epw', 'Sydney.epw', 'Madrid.epw', 'Sydney.epw'],
            'ComfStand': [0, 1, 2, 3],
            'value': [10, 20, 30, 40],
        }
    )

    filtered, report = apply_data_filter(
        df=df,
        data_filter={
            'include': {
                'epw': ['Sydney.epw', 'Madrid.epw'],
                'ComfStand': {'between': [1, 3]},
            },
            'exclude': {
                'ComfStand': [2],
            },
            'query': 'value >= 20',
        },
    )

    assert len(filtered) == 2
    assert set(filtered['ComfStand'].tolist()) == {1, 3}
    assert report['rows_before'] == 4
    assert report['rows_after'] == 2


def test_apply_data_filter_missing_column_strict_raises():
    df = pd.DataFrame({'epw': ['Seville.epw']})

    with pytest.raises(KeyError, match='was not found'):
        apply_data_filter(
            df=df,
            data_filter={'include': {'unknown_col': ['x']}},
            strict=True,
        )


def test_get_filtered_results_table_supports_columns_and_non_strict_missing_filter():
    sim = _DummyFilterSession()

    df = sim.get_filtered_results_table(
        df_source='optimisation',
        data_filter={
            'include': {
                'epw': ['Sydney.epw'],
                'non_existing_filter_col': ['ignored'],
            },
            'exclude': {
                'ComfStand': [2],
            },
        },
        columns=['idf', 'epw', 'ComfStand'],
        data_filter_strict=False,
    )

    assert list(df.columns) == ['idf', 'epw', 'ComfStand']
    assert df['epw'].nunique() == 1
    assert df['epw'].iloc[0] == 'Sydney.epw'
    assert set(df['ComfStand'].unique().tolist()) == {0, 1}


def test_plot_parametric_scatter_applies_data_filter(tmp_path):
    sim = _DummyFilterSession()

    grid = sim.plot_parametric_scatter(
        x='ComfStand',
        y='Heating:Electricity [J]',
        df_source='parametric',
        col='epw',
        out_dir=str(tmp_path),
        data_filter={
            'include': {
                'epw': ['Sydney.epw'],
            },
        },
    )

    assert grid is not None
    assert list(grid.col_names) == ['Sydney.epw']
    assert grid.data['epw'].nunique() == 1
    assert any(tmp_path.glob('plot_parametric_scatter_*.png'))


def test_plot_categorical_boxplots_applies_data_filter(tmp_path):
    sim = _DummyFilterSession()

    grid = sim.plot_categorical_boxplots(
        df_source='parametric',
        y_vars=['Heating:Electricity [J]'],
        col='epw',
        row='idf',
        show_points=False,
        out_dir=str(tmp_path),
        data_filter={
            'include': {
                'idf': ['idf_A'],
                'epw': ['Seville.epw', 'Sydney.epw'],
            },
            'exclude': {
                'epw': ['Sydney.epw'],
            },
        },
    )

    assert grid is not None
    assert list(grid.col_names) == ['Seville.epw']
    assert list(grid.row_names) == ['idf_A']
    assert any(tmp_path.glob('plot_categorical_boxplots_*.png'))


def test_plot_parametric_scatter_empty_filter_raises(tmp_path):
    sim = _DummyFilterSession()

    with pytest.raises(ValueError, match='zero rows'):
        sim.plot_parametric_scatter(
            x='ComfStand',
            y='Heating:Electricity [J]',
            df_source='parametric',
            col='epw',
            out_dir=str(tmp_path),
            data_filter={
                'include': {
                    'epw': ['NotAvailable.epw'],
                },
            },
        )


