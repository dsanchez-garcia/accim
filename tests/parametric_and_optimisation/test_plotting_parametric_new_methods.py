import os

import matplotlib
import pandas as pd
import pytest

matplotlib.use('Agg')

from accim.parametric_and_optimisation.plotting import PlottingMixin


class _DummyPlotSession(PlottingMixin):
    def __init__(self):
        self.outputs_normalized = False
        self.building_floor_area = 150.0
        self.epw_mapping_rules = {
            'city': {
                'seville': ['sev'],
                'sydney': ['syd'],
            }
        }
        self.idf_mapping_rules = {
            'building_type': {
                'residential': ['idf_A'],
                'office': ['idf_B'],
            }
        }
        self.outputs_param_simulation = self._build_df()
        self.outputs_optimisation = self.outputs_param_simulation.copy()

    @staticmethod
    def _build_df() -> pd.DataFrame:
        rows = []
        for idf_name in ['idf_A', 'idf_B']:
            building_type = 'residential' if idf_name == 'idf_A' else 'office'
            for epw_name in ['Seville.epw', 'Sydney.epw']:
                city = 'seville' if epw_name == 'Seville.epw' else 'sydney'
                for comf_stand in [0, 1, 2, 3]:
                    for hvac_mode in [0, 1, 2]:
                        rows.append(
                            {
                                'idf': idf_name,
                                'building_type': building_type,
                                'epw': epw_name,
                                'city': city,
                                'ComfStand': comf_stand,
                                'HVACmode': hvac_mode,
                                'performance': 'high' if comf_stand <= 1 else 'low',
                                'CAT': 80 + comf_stand,
                                'Heating:Electricity [J]': (
                                    12_000_000
                                    + 350_000 * comf_stand
                                    + 180_000 * hvac_mode
                                    + (200_000 if idf_name == 'idf_B' else 0)
                                ),
                                'Cooling:Electricity [J]': (
                                    9_000_000
                                    + 500_000 * comf_stand
                                    + 220_000 * hvac_mode
                                    + (300_000 if epw_name == 'Sydney.epw' else 0)
                                ),
                            }
                        )
        return pd.DataFrame(rows)


def test_plot_parametric_scatter_generates_png(tmp_path):
    sim = _DummyPlotSession()
    grid = sim.plot_parametric_scatter(
        x='ComfStand',
        y='Heating:Electricity [J]',
        df_source='parametric',
        hue='epw',
        col='idf',
        add_trend='linear',
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )

    assert grid is not None
    assert any(tmp_path.glob('plot_parametric_scatter_*.png'))


def test_plot_parametric_scatter_filename_template_with_mapping_placeholders(tmp_path):
    sim = _DummyPlotSession()
    grid = sim.plot_parametric_scatter(
        x='ComfStand',
        y='Heating:Electricity [J]',
        df_source='parametric',
        out_dir=str(tmp_path),
        filename_template='scatter_type-{building_type}_city-{city}.png',
        data_filter={
            'include': {
                'building_type': ['residential'],
                'city': ['seville'],
            }
        },
    )

    expected_path = tmp_path / 'scatter_type-residential_city-seville.png'
    assert grid is not None
    assert expected_path.exists()


def test_plot_parametric_lines_generates_pngs(tmp_path):
    sim = _DummyPlotSession()
    saved = sim.plot_parametric_lines(
        x='ComfStand',
        y_vars=['Heating:Electricity [J]', 'Cooling:Electricity [J]'],
        df_source='parametric',
        hue='epw',
        col='idf',
        estimator='mean',
        errorbar=('ci', 95),
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )

    assert set(saved.keys()) == {'Heating:Electricity [J]', 'Cooling:Electricity [J]'}
    for output_path in saved.values():
        assert os.path.exists(output_path)


def test_plot_parametric_lines_filename_template_with_placeholders(tmp_path):
    sim = _DummyPlotSession()
    saved = sim.plot_parametric_lines(
        x='ComfStand',
        y_vars=['Heating:Electricity [J]'],
        df_source='parametric',
        out_dir=str(tmp_path),
        filename_template='lines_{y_var}_{building_type}_{city}.png',
        data_filter={
            'include': {
                'building_type': ['office'],
                'city': ['sydney'],
            }
        },
    )

    expected_path = tmp_path / 'lines_Heating_Electricity_J_office_sydney.png'
    assert saved['Heating:Electricity [J]'] == str(expected_path)
    assert expected_path.exists()


def test_plot_parametric_lines_filename_template_duplicate_output_raises(tmp_path):
    sim = _DummyPlotSession()

    with pytest.raises(ValueError, match='duplicate output path'):
        sim.plot_parametric_lines(
            x='ComfStand',
            y_vars=['Heating:Electricity [J]', 'Cooling:Electricity [J]'],
            df_source='parametric',
            out_dir=str(tmp_path),
            filename_template='lines_same_{building_type}_{city}.png',
            data_filter={
                'include': {
                    'building_type': ['residential'],
                    'city': ['seville'],
                }
            },
        )


def test_plot_parametric_heatmap_generates_png(tmp_path):
    sim = _DummyPlotSession()
    path = sim.plot_parametric_heatmap(
        x='ComfStand',
        y='HVACmode',
        z='Heating:Electricity [J]',
        df_source='parametric',
        col='idf',
        row='epw',
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )

    assert os.path.exists(path)


def test_plot_parametric_contour_generates_png(tmp_path):
    sim = _DummyPlotSession()
    path = sim.plot_parametric_contour(
        x='ComfStand',
        y='HVACmode',
        z='Cooling:Electricity [J]',
        df_source='parametric',
        col='idf',
        row='epw',
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )

    assert os.path.exists(path)


def test_plot_parametric_distributions_violin_and_boxen(tmp_path):
    sim = _DummyPlotSession()

    violin_saved = sim.plot_parametric_distributions(
        x='HVACmode',
        y_vars=['Heating:Electricity [J]'],
        kind='violin',
        df_source='parametric',
        hue='epw',
        col='idf',
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )
    assert os.path.exists(violin_saved['Heating:Electricity [J]'])

    boxen_saved = sim.plot_parametric_distributions(
        x='HVACmode',
        y_vars=['Cooling:Electricity [J]'],
        kind='boxen',
        df_source='parametric',
        hue='epw',
        col='idf',
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )
    assert os.path.exists(boxen_saved['Cooling:Electricity [J]'])


def test_plot_parametric_ecdf_generates_png(tmp_path):
    sim = _DummyPlotSession()
    path = sim.plot_parametric_ecdf(
        x='Heating:Electricity [J]',
        df_source='parametric',
        hue='epw',
        col='idf',
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )

    assert os.path.exists(path)


def test_plot_parametric_density2d_generates_pngs(tmp_path):
    sim = _DummyPlotSession()

    hexbin_path = sim.plot_parametric_density_2d(
        x='Heating:Electricity [J]',
        y='Cooling:Electricity [J]',
        kind='hexbin',
        df_source='parametric',
        col='idf',
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )
    assert os.path.exists(hexbin_path)

    kde_path = sim.plot_parametric_density_2d(
        x='Heating:Electricity [J]',
        y='Cooling:Electricity [J]',
        kind='kde',
        df_source='parametric',
        hue='epw',
        col='idf',
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )
    assert os.path.exists(kde_path)


def test_plot_parametric_radar_generates_png_and_returns_df(tmp_path):
    sim = _DummyPlotSession()
    agg_df = sim.plot_parametric_radar(
        metrics=['Heating:Electricity [J]', 'Cooling:Electricity [J]', 'ComfStand'],
        group_by='epw',
        df_source='parametric',
        normalize_per_m2=True,
        out_dir=str(tmp_path),
    )

    assert not agg_df.empty
    assert any(tmp_path.glob('plot_parametric_radar_*.png'))


@pytest.mark.parametrize('hue_var', ['epw', 'idf'])
def test_plot_categorical_boxplots_hue_id_vars_regression(tmp_path, hue_var):
    sim = _DummyPlotSession()
    grid = sim.plot_categorical_boxplots(
        df_source='parametric',
        y_vars=['Heating:Electricity [J]'],
        hue=hue_var,
        show_points=False,
        out_dir=str(tmp_path),
    )

    assert grid is not None
    assert any(tmp_path.glob('plot_categorical_boxplots_*.png'))


def test_plot_categorical_boxplots_custom_col_order_without_row_order(tmp_path):
    sim = _DummyPlotSession()
    desired_city_order = ['sydney', 'seville']

    grid = sim.plot_categorical_boxplots(
        df_source='parametric',
        y_vars=['Heating:Electricity [J]'],
        col='city',
        row='building_type',
        hue='performance',
        show_points=False,
        out_dir=str(tmp_path),
        subplot_order_mode='custom',
        subplot_order_custom={'col': desired_city_order},
    )

    expected_row_order = (
        sim.outputs_param_simulation['building_type']
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    assert grid is not None
    assert list(grid.col_names) == desired_city_order
    assert list(grid.row_names) == expected_row_order


def test_plot_categorical_boxplots_filename_template_with_mapping_placeholders(tmp_path):
    sim = _DummyPlotSession()

    grid = sim.plot_categorical_boxplots(
        df_source='parametric',
        y_vars=['Heating:Electricity [J]'],
        row='building_type',
        col='city',
        show_points=False,
        out_dir=str(tmp_path),
        filename_template='boxplot_type-{building_type}_city-{city}.png',
        data_filter={
            'include': {
                'building_type': ['residential'],
                'city': ['seville'],
            }
        },
    )

    expected_path = tmp_path / 'boxplot_type-residential_city-seville.png'
    assert grid is not None
    assert expected_path.exists()


