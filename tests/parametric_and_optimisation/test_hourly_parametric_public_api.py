import pandas as pd
import pytest

from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation


def _write_hourly_csv(sim_dir, offset):
    sim_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        {
            'Date/Time': [
                '1/1  01:00:00',
                '1/1  02:00:00',
                '1/1  03:00:00',
                '1/1  04:00:00',
            ],
            'LIVING:Zone Operative Temperature [C](Hourly)': [
                21.0 + offset,
                21.5 + offset,
                22.0 + offset,
                22.5 + offset,
            ],
            'BEDROOM:Zone Operative Temperature [C](Hourly)': [
                20.5 + offset,
                21.0 + offset,
                21.5 + offset,
                22.0 + offset,
            ],
            'LIVING:Setpoint Temperature_No Tolerance [C](Hourly)': [
                20.0 + offset,
                20.0 + offset,
                20.5 + offset,
                20.5 + offset,
            ],
            'BEDROOM:Setpoint Temperature_No Tolerance [C](Hourly)': [
                19.5 + offset,
                19.5 + offset,
                20.0 + offset,
                20.0 + offset,
            ],
            'LIVING:Zone Thermal Comfort Fanger Model PMV [](Hourly)': [
                -0.2 + offset * 0.01,
                -0.1 + offset * 0.01,
                0.0 + offset * 0.01,
                0.1 + offset * 0.01,
            ],
            'BEDROOM:Zone Thermal Comfort Fanger Model PMV [](Hourly)': [
                -0.3 + offset * 0.01,
                -0.2 + offset * 0.01,
                -0.1 + offset * 0.01,
                0.0 + offset * 0.01,
            ],
            'LIVING:Running Average Outdoor Air Temperature [C](Hourly)': [
                17.0,
                17.2,
                17.4,
                17.6,
            ],
            'BEDROOM:Running Average Outdoor Air Temperature [C](Hourly)': [
                17.0,
                17.2,
                17.4,
                17.6,
            ],
        }
    )
    df.to_csv(sim_dir / 'eplusout.csv', index=False)


def _build_parametric_session_with_csv_outputs(tmp_path):
    seville_dir = tmp_path / 'sim_seville'
    sydney_dir = tmp_path / 'sim_sydney'
    _write_hourly_csv(seville_dir, offset=0.0)
    _write_hourly_csv(sydney_dir, offset=1.0)

    sim = ParametricSimulation(parameters_type=None)
    sim.outputs_param_simulation = pd.DataFrame(
        [
            {
                'CustAST_m': 0.01,
                'CustAST_n': 5.0,
                'epw': 'Seville',
                'idf': 'idf_a',
                'output_dir': str(seville_dir),
            },
            {
                'CustAST_m': 0.66,
                'CustAST_n': 17.0,
                'epw': 'Sydney',
                'idf': 'idf_a',
                'output_dir': str(sydney_dir),
            },
        ]
    )
    sim.outputs_param_simulation.attrs['parameters_names'] = ['CustAST_m', 'CustAST_n']
    sim.last_run_type = 'parametric'
    return sim


def test_get_hourly_df_parametric_csv_with_filters(tmp_path):
    sim = _build_parametric_session_with_csv_outputs(tmp_path)

    hourly = sim.get_hourly_df_parametric(
        epw_filter='Seville',
        output_columns=[
            'Zone Operative Temperature',
            'Running Average Outdoor Air Temperature',
        ],
        skip_confirmation=True,
        start_date='2024-01-01 01',
    )

    assert hourly is not None
    assert len(hourly) == 4
    assert set(hourly['epw'].unique()) == {'Seville'}
    assert any('Zone Operative Temperature' in c for c in hourly.columns)
    assert any('Running Average Outdoor Air Temperature' in c for c in hourly.columns)
    assert len([c for c in hourly.columns if 'Zone Operative Temperature' in c]) >= 2


def _csv_hourly_columns(sim_dir):
    return [c for c in pd.read_csv(sim_dir / 'eplusout.csv', nrows=0).columns if c != 'Date/Time']


# The hourly columns used to be collected in a set, so their order followed string hashing,
# which changes with every Python process: the 8 columns of these files keep their order.
def test_get_hourly_df_parametric_keeps_csv_column_order(tmp_path):
    sim = _build_parametric_session_with_csv_outputs(tmp_path)
    csv_columns = _csv_hourly_columns(tmp_path / 'sim_seville')

    hourly = sim.get_hourly_df_parametric(skip_confirmation=True, start_date='2024-01-01 01')

    assert [c for c in hourly.columns if c in csv_columns] == csv_columns


def test_get_hourly_df_parametric_keeps_requested_column_order(tmp_path):
    sim = _build_parametric_session_with_csv_outputs(tmp_path)
    csv_columns = _csv_hourly_columns(tmp_path / 'sim_seville')

    hourly = sim.get_hourly_df_parametric(
        output_columns=['BEDROOM', 'LIVING'],
        skip_confirmation=True,
        start_date='2024-01-01 01',
    )

    expected = [c for c in csv_columns if c.startswith('BEDROOM')] + [c for c in csv_columns if c.startswith('LIVING')]
    assert [c for c in hourly.columns if c in csv_columns] == expected


def test_get_hourly_df_optimisation_keeps_csv_column_order(tmp_path):
    sim_dir = tmp_path / 'sim_seville'
    _write_hourly_csv(sim_dir, offset=0.0)
    sim = OptimisationSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.outputs_optimisation = pd.DataFrame(
        [
            {
                'CustAST_m': 0.01,
                'epw': 'Seville',
                'pareto-optimal': True,
                'simulation_output_csv_path': str(sim_dir / 'eplusout.csv'),
            },
        ]
    )
    sim.last_run_type = 'optimisation'
    csv_columns = _csv_hourly_columns(sim_dir)

    hourly = sim.get_hourly_df_optimisation(skip_confirmation=True, start_date='2024-01-01 01')

    assert [c for c in hourly.columns if c in csv_columns] == csv_columns


def test_get_hourly_df_parametric_simulation_indices_override_filter(tmp_path):
    sim = _build_parametric_session_with_csv_outputs(tmp_path)

    hourly = sim.get_hourly_df_parametric(
        epw_filter='Seville',
        simulation_indices=[1],
        output_columns=['Zone Operative Temperature'],
        skip_confirmation=True,
        start_date='2024-01-01 01',
    )

    assert hourly is not None
    assert len(hourly) == 4
    assert set(hourly['epw'].unique()) == {'Sydney'}


def test_get_hourly_df_parametric_partial_missing_output_columns_warns(tmp_path):
    sim = _build_parametric_session_with_csv_outputs(tmp_path)

    with pytest.warns(UserWarning, match='Some requested CSV columns were not found'):
        hourly = sim.get_hourly_df_parametric(
            output_columns=[
                'Zone Operative Temperature',
                'Running Average Outdoor Air Temperature',
                'Definitely Missing Output Pattern',
            ],
            skip_confirmation=True,
            start_date='2024-01-01 01',
        )

    assert hourly is not None
    assert len(hourly) == 8
    assert len([c for c in hourly.columns if 'Zone Operative Temperature' in c]) >= 2


def test_get_hourly_df_parametric_all_missing_output_columns_raises(tmp_path):
    sim = _build_parametric_session_with_csv_outputs(tmp_path)

    with pytest.raises(ValueError, match='Failed to resolve requested output_columns'):
        sim.get_hourly_df_parametric(
            output_columns=['Definitely Missing Output Pattern'],
            skip_confirmation=True,
            start_date='2024-01-01 01',
        )


def test_get_hourly_df_wrapper_supports_embedded_list_columns():
    sim = ParametricSimulation(parameters_type=None)
    sim.outputs_param_simulation = pd.DataFrame(
        {
            'CustAST_m': [0.01, 0.66],
            'epw': ['Seville', 'Sydney'],
            'idf': ['idf_a', 'idf_a'],
            'Zone Operative Temperature': [[20.0, 21.0, 22.0], [23.0, 24.0, 25.0]],
            'Running Average Outdoor Air Temperature': [[16.0, 16.0, 16.0], [17.0, 17.0, 17.0]],
        }
    )
    sim.outputs_param_simulation.attrs['parameters_names'] = ['CustAST_m']
    sim.last_run_type = 'parametric'

    hourly = sim.get_hourly_df(start_date='2024-01-01 01')

    assert hourly is not None
    assert len(hourly) == 6
    assert 'datetime' in hourly.columns
    assert 'hour' in hourly.columns


def test_get_hourly_df_columns_parametric_fallback_to_csv(tmp_path):
    sim = _build_parametric_session_with_csv_outputs(tmp_path)

    cols = sim.get_hourly_df_columns()

    assert isinstance(cols, list)
    assert len(cols) > 0
    assert any('Zone Operative Temperature' in c for c in cols)
    assert 'Date/Time' not in cols

