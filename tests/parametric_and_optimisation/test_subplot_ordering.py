import matplotlib
import pandas as pd
import pytest

matplotlib.use('Agg')

from accim.parametric_and_optimisation.plotting import PlottingMixin
from accim.parametric_and_optimisation.utils import resolve_subplot_order, resolve_subplot_orders


class _DummySubplotOrderingSession(PlottingMixin):
    def __init__(self):
        self.outputs_normalized = False
        self.building_floor_area = 120.0
        self.outputs_param_simulation = self._build_df()
        self.outputs_optimisation = self.outputs_param_simulation.copy()

    @staticmethod
    def _build_df() -> pd.DataFrame:
        rows = []
        for epw in ['madrid', 'seville', 'granada']:
            for building_type in ['MF_Block', 'SF_Detached']:
                for performance in ['high', 'low']:
                    for comf_stand in [2, 0, 1]:
                        rows.append(
                            {
                                'epw': epw,
                                'building_type': building_type,
                                'performance': performance,
                                'ComfStand': comf_stand,
                                'HVACmode': comf_stand,
                                'Heating:Electricity [J]': 10_000_000 + 100_000 * comf_stand,
                                'Cooling:Electricity [J]': 8_000_000 + 120_000 * comf_stand,
                            }
                        )
        return pd.DataFrame(rows)


def test_resolve_subplot_order_numeric_and_alphabetical_modes():
    assert resolve_subplot_order([3, 1, 2], mode='ascending') == [1, 2, 3]
    assert resolve_subplot_order(['3', '1', '2'], mode='descending') == ['3', '2', '1']
    assert resolve_subplot_order(['beta', 'Alpha', 'gamma'], mode='alphabetical') == ['Alpha', 'beta', 'gamma']


def test_resolve_subplot_order_custom_invalid_value_raises():
    with pytest.raises(ValueError, match='Invalid values'):
        resolve_subplot_order(
            values=['seville', 'madrid'],
            mode='custom',
            custom_values=['lisbon', 'madrid'],
        )


def test_resolve_subplot_orders_custom_missing_dimension_raises():
    with pytest.raises(ValueError, match='requires explicit order for active dimensions'):
        resolve_subplot_orders(
            dimension_values={'col': ['a', 'b'], 'row': ['x', 'y']},
            mode='custom',
            custom={'col': ['a', 'b']},
            context='test_subplot_ordering',
        )


def test_plot_categorical_boxplots_custom_subplot_order(tmp_path):
    sim = _DummySubplotOrderingSession()

    grid = sim.plot_categorical_boxplots(
        df_source='parametric',
        y_vars=['Heating:Electricity [J]'],
        col='epw',
        row='building_type',
        hue='performance',
        show_points=False,
        out_dir=str(tmp_path),
        subplot_order_mode='custom',
        subplot_order_custom={
            'col': ['granada', 'seville', 'madrid'],
            'row': ['SF_Detached', 'MF_Block'],
        },
    )

    assert grid.col_names == ['granada', 'seville', 'madrid']
    assert grid.row_names == ['SF_Detached', 'MF_Block']


def test_plot_parametric_scatter_descending_subplot_order(tmp_path):
    sim = _DummySubplotOrderingSession()

    grid = sim.plot_parametric_scatter(
        x='ComfStand',
        y='Heating:Electricity [J]',
        df_source='parametric',
        hue='performance',
        col='epw',
        row='building_type',
        out_dir=str(tmp_path),
        subplot_order_mode='descending',
    )

    assert grid.col_names == ['seville', 'madrid', 'granada']
    assert grid.row_names == ['SF_Detached', 'MF_Block']


def test_plot_parametric_scatter_ordering_without_subplots_raises(tmp_path):
    sim = _DummySubplotOrderingSession()

    with pytest.raises(ValueError, match='no active subplot dimensions'):
        sim.plot_parametric_scatter(
            x='ComfStand',
            y='Heating:Electricity [J]',
            df_source='parametric',
            out_dir=str(tmp_path),
            subplot_order_mode='ascending',
        )


def test_plot_parametric_scatter_custom_dimension_not_active_raises(tmp_path):
    sim = _DummySubplotOrderingSession()

    with pytest.raises(ValueError, match='not active in this plot'):
        sim.plot_parametric_scatter(
            x='ComfStand',
            y='Heating:Electricity [J]',
            df_source='parametric',
            col='epw',
            row=None,
            out_dir=str(tmp_path),
            subplot_order_mode='custom',
            subplot_order_custom={
                'col': ['granada', 'seville', 'madrid'],
                'row': ['MF_Block', 'SF_Detached'],
            },
        )

