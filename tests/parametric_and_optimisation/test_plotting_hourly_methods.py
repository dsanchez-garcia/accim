import matplotlib
import pandas as pd

matplotlib.use('Agg')

from accim.parametric_and_optimisation.plotting import PlottingMixin


class _DummyHourlyPlotSession(PlottingMixin):
    def __init__(self):
        self.outputs_param_simulation_hourly = self._build_hourly_df()
        self.outputs_optimisation_hourly = self.outputs_param_simulation_hourly.copy()

    @staticmethod
    def _build_hourly_df() -> pd.DataFrame:
        rows = []
        base_dt = pd.Timestamp('2024-01-01 00:00:00')
        for epw in ['Seville', 'Sydney']:
            for cust_m in [0.01, 0.66]:
                for cust_n in [5.0, 17.0]:
                    for hour in range(1, 7):
                        rows.append(
                            {
                                'datetime': base_dt + pd.Timedelta(hours=hour),
                                'hour': hour,
                                'epw': epw,
                                'CustAST_m': cust_m,
                                'CustAST_n': cust_n,
                                'LIVING:Running Average Outdoor Air Temperature [C](Hourly)': 16.0 + 0.3 * hour,
                                'LIVING:Zone Operative Temperature [C](Hourly)': 21.0 + 0.5 * hour + cust_m,
                                'LIVING:Setpoint Temperature_No Tolerance [C](Hourly)': 20.0 + 0.2 * hour,
                                'LIVING:Zone Thermal Comfort Fanger Model PMV [](Hourly)': -0.4 + 0.05 * hour,
                            }
                        )
        return pd.DataFrame(rows)


def test_prepare_hourly_long_df_default_tokens():
    sim = _DummyHourlyPlotSession()

    df_long = sim.prepare_hourly_long_df(
        df_source='parametric_hourly',
        epw_filter='Seville',
    )

    assert not df_long.empty
    assert {'variable', 'value'}.issubset(set(df_long.columns))
    assert df_long['epw'].astype(str).str.contains('Seville').all()


def test_prepare_hourly_long_df_supports_optimisation_hourly_source():
    sim = _DummyHourlyPlotSession()

    df_long = sim.prepare_hourly_long_df(
        df_source='optimisation_hourly',
        epw_filter='Sydney',
    )

    assert not df_long.empty
    assert df_long['epw'].astype(str).str.contains('Sydney').all()


def test_plot_hourly_scatter_generates_png(tmp_path):
    sim = _DummyHourlyPlotSession()

    grid = sim.plot_hourly_scatter(
        df_source='parametric_hourly',
        epw_filter='Seville',
        out_dir=str(tmp_path),
        y_label='Indoor Operative Temperature (C)',
    )

    assert grid is not None
    assert any(tmp_path.glob('plot_hourly_scatter_*.png'))


def test_plot_hourly_lines_generates_png(tmp_path):
    sim = _DummyHourlyPlotSession()

    grid = sim.plot_hourly_lines(
        df_source='parametric_hourly',
        epw_filter='Sydney',
        out_dir=str(tmp_path),
        y_label='Indoor Operative Temperature (C)',
    )

    assert grid is not None
    assert any(tmp_path.glob('plot_hourly_lines_*.png'))

