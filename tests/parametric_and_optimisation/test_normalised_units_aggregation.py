"""Regression tests for normalised units when hourly results are aggregated.

get_hourly_df() expands the hourly results of each simulation, and get_daily_df(),
get_monthly_df() and get_runperiod_df() aggregate that hourly table (energy is summed and
temperatures are averaged). With normalize_per_m2=True, normalize_outputs() divides the energy
columns by 3.6e6 J/kWh times the floor area of the IDF of each row and renames '[J]' to
'[kWh/m2]'. These tests pin that the normalised results stay coherent across frequencies:

- the normalised columns keep the same names in the hourly, daily, monthly and runperiod
  tables, whether the hourly table or the aggregated table is normalised;
- normalising before or after the aggregation gives the same values, and the daily, monthly
  and runperiod totals of each simulation equal the sum of its normalised hourly values,
  computed independently from the raw values in J and the area of each IDF;
- the daily, monthly and runperiod tables average the temperatures and leave them in degC;
- a table aggregated from a normalised hourly table is not normalised again (before, it was
  divided twice by the floor area), and only energy columns are normalised: columns in [C],
  [W] or [%] are left as they are (before, any column named after heating, cooling, etc.);
- each hourly or timestep value, labelled by EnergyPlus with the end of its interval, is added
  to its own day and month (before, the 24:00 value went to the next day), and a series
  without explicit year is put in a non-leap year unless it has 8784 hourly values (before,
  always in 2024, so a standard year got a 29 February).
"""
import datetime
import inspect

import numpy as np
import pandas as pd
import pytest

from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation
from accim.parametric_and_optimisation.utils import expand_to_hourly_dataframe

J_PER_KWH = 3.6e6
AREAS = {'office_a': 50.0, 'office_b': 200.0}
HOURS = 24 * 40  # from 1 January 01:00 to 10 February 00:00: two months in the monthly tables

HEATING = 'Heating:Electricity [J](Hourly)'
COOLING = 'Cooling:Electricity [J](Hourly)'
TEMPERATURE = 'BLOCK1:ZONE1:Zone Operative Temperature [C](Hourly)'
HEATING_KWH_M2 = 'Heating:Electricity [kWh/m2](Hourly)'
COOLING_KWH_M2 = 'Cooling:Electricity [kWh/m2](Hourly)'
NORMALISED_OUTPUTS = [HEATING_KWH_M2, COOLING_KWH_M2, TEMPERATURE]
ENERGY_COLUMNS = {HEATING: HEATING_KWH_M2, COOLING: COOLING_KWH_M2}

ID_COLUMNS = ['x', 'epw', 'idf']
PERIOD_COLUMN = {'daily': 'day', 'monthly': 'month', 'runperiod': None}
FREQUENCIES = list(PERIOD_COLUMN)

# (x, epw, idf, seed of the hourly values)
SIMULATIONS = [
    (1, 'Seville', 'office_a', 0),
    (1, 'Seville', 'office_b', 1),
    (2, 'Oslo', 'office_a', 2),
    (2, 'Oslo', 'office_b', 3),
]
OPTIMISATION_SIMULATIONS = [
    (0.1, 'Seville', 'office_a', 0),
    (0.2, 'Seville', 'office_b', 1),
]


class _DummyProblem:
    def __init__(self, inputs, outputs):
        self._inputs = list(inputs)
        self._outputs = list(outputs)

    def names(self, typ):
        if typ == 'inputs':
            return list(self._inputs)
        if typ == 'outputs':
            return list(self._outputs)
        if typ == 'constraints':
            return []
        raise KeyError(typ)


def _hourly_values(seed, hours=HOURS):
    """Raw hourly values of one simulation: energy in J and a constant temperature."""
    index = np.arange(hours)
    return {
        HEATING: (1.0 + index % 24 + 10.0 * seed) * J_PER_KWH,
        COOLING: (0.5 + (index * 7) % 11 + 5.0 * seed) * J_PER_KWH,
        TEMPERATURE: np.full(hours, 20.0 + seed),
    }


def _expected_totals_kwh_per_m2(simulations=SIMULATIONS):
    """Normalised totals of each simulation, computed from the raw values in J."""
    totals = {}
    for (x, epw, idf, seed) in simulations:
        values = _hourly_values(seed)
        totals[(x, epw, idf)] = {
            normalised: values[raw].sum() / (J_PER_KWH * AREAS[idf])
            for (raw, normalised) in ENERGY_COLUMNS.items()
        }
    return totals


def _parametric_session():
    sim = ParametricSimulation(
        buildings=None,
        epws=['Seville.epw', 'Oslo.epw'],
        parameters_type=None,
        bypass_addAccis=True,
    )
    rows = []
    for (x, epw, idf, seed) in SIMULATIONS:
        row = {'x': x, 'epw': epw, 'idf': idf}
        row.update({column: values.tolist() for (column, values) in _hourly_values(seed).items()})
        rows.append(row)
    sim.outputs_param_simulation = pd.DataFrame(rows)
    sim.outputs_param_simulation.attrs['parameters_names'] = ['x']
    sim.last_run_type = 'parametric'
    sim.building_floor_area = dict(AREAS)
    return sim


def _energyplus_timestamps(hours):
    """'Date/Time' labels of an EnergyPlus hourly CSV (the last hour of each day is 24:00)."""
    labels = []
    for index in range(hours):
        (day_index, hour) = divmod(index, 24)
        date = datetime.date(2023, 1, 1) + datetime.timedelta(days=day_index)
        labels.append(f' {date.month:02d}/{date.day:02d}  {hour + 1:02d}:00:00')
    return labels


def _optimisation_session(tmp_path):
    rows = []
    for (x, epw, idf, seed) in OPTIMISATION_SIMULATIONS:
        sim_dir = tmp_path / f'sim_{idf}'
        sim_dir.mkdir(parents=True)
        values = _hourly_values(seed)
        csv_table = pd.DataFrame({'Date/Time': _energyplus_timestamps(HOURS), **values})
        csv_table.to_csv(sim_dir / 'eplusout.csv', index=False)
        rows.append({
            'x': x,
            'Heating:Electricity': values[HEATING].sum(),
            'epw': epw,
            'idf': idf,
            'pareto-optimal': True,
            'simulation_directory': str(sim_dir),
            'simulation_output_csv_path': str(sim_dir / 'eplusout.csv'),
        })
    sim = OptimisationSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.problem = _DummyProblem(inputs=['x'], outputs=['Heating:Electricity'])
    sim.outputs_optimisation = pd.DataFrame(rows)
    sim.last_run_type = 'optimisation'
    sim.building_floor_area = dict(AREAS)
    return sim


def _aggregate(sim, frequency, **kwargs):
    return getattr(sim, f'get_{frequency}_df')(**kwargs)


def _rows_of(table, x, epw, idf):
    return table[(table['x'] == x) & (table['epw'] == epw) & (table['idf'] == idf)]


# ----------------------------------------------------------------------------- hourly table

def test_hourly_normalisation_converts_joules_to_kwh_per_m2_of_each_idf():
    sim = _parametric_session()

    hourly = sim.get_hourly_df(normalize_per_m2=True)

    assert list(hourly.columns) == ID_COLUMNS + ['hour', 'datetime'] + NORMALISED_OUTPUTS
    assert sim._is_df_type_normalized('parametric_hourly')
    for (x, epw, idf, seed) in SIMULATIONS:
        rows = _rows_of(hourly, x, epw, idf).sort_values('hour')
        values = _hourly_values(seed)
        assert len(rows) == HOURS
        assert rows[HEATING_KWH_M2].to_numpy() == pytest.approx(values[HEATING] / (J_PER_KWH * AREAS[idf]))
        assert rows[COOLING_KWH_M2].to_numpy() == pytest.approx(values[COOLING] / (J_PER_KWH * AREAS[idf]))
        assert rows[TEMPERATURE].to_numpy() == pytest.approx(values[TEMPERATURE])


# ----------------------------------------------------------------------------- names and values by frequency

@pytest.mark.parametrize('normalised_table', ['hourly', 'aggregated'])
@pytest.mark.parametrize('frequency', FREQUENCIES)
def test_normalised_column_names_are_the_same_at_every_frequency(frequency, normalised_table):
    sim = _parametric_session()
    if normalised_table == 'hourly':
        sim.get_hourly_df(normalize_per_m2=True)
        table = _aggregate(sim, frequency)
    else:
        sim.get_hourly_df()
        table = _aggregate(sim, frequency, normalize_per_m2=True)

    period = PERIOD_COLUMN[frequency]
    assert list(table.columns) == ID_COLUMNS + ([period] if period else []) + NORMALISED_OUTPUTS
    assert len(table.drop_duplicates(subset=ID_COLUMNS)) == len(SIMULATIONS)


@pytest.mark.parametrize('frequency', FREQUENCIES)
def test_normalising_the_hourly_or_the_aggregated_table_gives_the_same_values(frequency):
    hourly_first = _parametric_session()
    hourly_first.get_hourly_df(normalize_per_m2=True)
    aggregated_from_normalised_hourly = _aggregate(hourly_first, frequency)

    aggregated_first = _parametric_session()
    aggregated_first.get_hourly_df()
    normalised_after_aggregation = _aggregate(aggregated_first, frequency, normalize_per_m2=True)

    assert aggregated_first._is_df_type_normalized(f'parametric_{frequency}')
    pd.testing.assert_frame_equal(
        aggregated_from_normalised_hourly,
        normalised_after_aggregation,
        check_exact=False,
        rtol=1e-9,
    )


def test_runperiod_normalised_totals_equal_the_sum_of_the_normalised_hourly_values():
    sim = _parametric_session()
    hourly = sim.get_hourly_df(normalize_per_m2=True)

    runperiod = sim.get_runperiod_df().set_index(ID_COLUMNS)

    hourly_totals = hourly.groupby(ID_COLUMNS)[[HEATING_KWH_M2, COOLING_KWH_M2]].sum()
    assert len(runperiod) == len(SIMULATIONS)
    for (key, expected) in _expected_totals_kwh_per_m2().items():
        for (column, total) in expected.items():
            assert hourly_totals.loc[key, column] == pytest.approx(total)
            assert runperiod.loc[key, column] == pytest.approx(total)


def test_daily_and_monthly_normalised_totals_add_up_to_the_runperiod_total():
    sim = _parametric_session()
    sim.get_hourly_df()

    daily = sim.get_daily_df(normalize_per_m2=True)
    monthly = sim.get_monthly_df(normalize_per_m2=True)
    runperiod = sim.get_runperiod_df(normalize_per_m2=True).set_index(ID_COLUMNS)

    assert daily.groupby(ID_COLUMNS)['day'].nunique().min() >= 40
    assert monthly.groupby(ID_COLUMNS)['month'].nunique().min() == 2
    daily_totals = daily.groupby(ID_COLUMNS)[[HEATING_KWH_M2, COOLING_KWH_M2]].sum()
    monthly_totals = monthly.groupby(ID_COLUMNS)[[HEATING_KWH_M2, COOLING_KWH_M2]].sum()
    for (key, expected) in _expected_totals_kwh_per_m2().items():
        for (column, total) in expected.items():
            assert runperiod.loc[key, column] == pytest.approx(total)
            assert daily_totals.loc[key, column] == pytest.approx(total)
            assert monthly_totals.loc[key, column] == pytest.approx(total)
    # Normalising the aggregated tables leaves the hourly table in J.
    assert HEATING in sim.outputs_param_simulation_hourly.columns
    assert not sim._is_df_type_normalized('parametric_hourly')


@pytest.mark.parametrize('frequency', FREQUENCIES)
def test_temperatures_are_averaged_and_keep_their_unit_at_every_frequency(frequency):
    sim = _parametric_session()
    sim.get_hourly_df()

    table = _aggregate(sim, frequency, normalize_per_m2=True)

    for (x, epw, idf, seed) in SIMULATIONS:
        temperatures = _rows_of(table, x, epw, idf)[TEMPERATURE].tolist()
        assert len(temperatures) > 0
        assert temperatures == pytest.approx([20.0 + seed] * len(temperatures))


def test_optimisation_aggregation_of_an_existing_hourly_table_is_normalised_with_each_idf_area(tmp_path):
    sim = _optimisation_session(tmp_path)
    sim.get_hourly_df(skip_confirmation=True)

    runperiod = sim.get_runperiod_df(normalize_per_m2=True, skip_confirmation=True)

    assert list(runperiod.columns) == ['x', 'epw', 'idf', 'pareto-optimal'] + NORMALISED_OUTPUTS
    for (key, expected) in _expected_totals_kwh_per_m2(OPTIMISATION_SIMULATIONS).items():
        rows = _rows_of(runperiod, *key)
        assert len(rows) == 1
        for (column, total) in expected.items():
            assert rows[column].iloc[0] == pytest.approx(total)
    assert sim._is_df_type_normalized('optimisation_runperiod')
    assert not sim._is_df_type_normalized('optimisation_hourly')


# ----------------------------------------------------------------------------- normalisation state

def test_aggregating_a_normalised_hourly_table_does_not_normalise_it_again():
    reference = _parametric_session()
    reference.get_hourly_df()
    expected = reference.get_daily_df(normalize_per_m2=True)
    sim = _parametric_session()
    sim.get_hourly_df(normalize_per_m2=True)

    daily = sim.get_daily_df(normalize_per_m2=True)
    sim.normalize_outputs()

    assert list(daily.columns) == ID_COLUMNS + ['day'] + NORMALISED_OUTPUTS
    assert sim._is_df_type_normalized('parametric_daily')
    pd.testing.assert_frame_equal(sim.outputs_param_simulation_daily, expected, check_exact=False, rtol=1e-9)


def test_optimisation_aggregation_with_normalize_per_m2_normalises_only_once(tmp_path):
    sim = _optimisation_session(tmp_path)

    runperiod = sim.get_runperiod_df(normalize_per_m2=True, skip_confirmation=True)

    assert list(runperiod.columns) == ['x', 'epw', 'idf', 'pareto-optimal'] + NORMALISED_OUTPUTS
    for (key, expected) in _expected_totals_kwh_per_m2(OPTIMISATION_SIMULATIONS).items():
        for (column, total) in expected.items():
            assert _rows_of(runperiod, *key)[column].iloc[0] == pytest.approx(total)
    # Like the parametric methods, the hourly table built on the way stays in J.
    assert HEATING in sim.outputs_optimisation_hourly.columns
    assert not sim._is_df_type_normalized('optimisation_hourly')


# ----------------------------------------------------------------------------- energy columns

def test_normalisation_converts_only_energy_columns():
    sim = ParametricSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.building_floor_area = dict(AREAS)
    other_units = {
        'EMS:Adaptive Heating Setpoint Temperature [C](Hourly)': [20.5, 21.0],
        'EMS:Adaptive Cooling Setpoint Temperature [C](Hourly)': [25.0, 25.5],
        'BLOCK1:ZONE1 VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate [W](Hourly)': [1500.0, 0.0],
        'Whole Building:Facility Total HVAC Electricity Demand Rate [W](Hourly)': [800.0, 650.0],
        'HEATING COIL:Heating Coil Runtime Fraction [](Hourly)': [0.5, 1.0],
        'Heating Energy Share [%]': [40.0, 60.0],
        'Cooling:Electricity_kWh/m2': [3.0, 4.0],
    }
    sim.outputs_param_simulation_hourly = pd.DataFrame({
        'x': [1, 1],
        'epw': ['Seville', 'Seville'],
        'idf': ['office_a', 'office_a'],
        'hour': [1, 2],
        HEATING: [1.8e8, 3.6e8],
        'Heating:Electricity': [3.6e8, 1.8e8],
        **other_units,
    })

    sim.normalize_outputs(df_types=['parametric_hourly'])

    hourly = sim.outputs_param_simulation_hourly
    # In J, with or without unit in the name (meters and objectives have none).
    assert hourly[HEATING_KWH_M2].tolist() == pytest.approx([1.0, 2.0])
    assert hourly['Heating:Electricity_kWh/m2'].tolist() == pytest.approx([2.0, 1.0])
    for (column, values) in other_units.items():
        assert column in hourly.columns
        assert hourly[column].tolist() == values


# ----------------------------------------------------------------------------- calendar

def _single_simulation_session(hourly_heating_kwh_per_m2):
    # 'office_a' has 50 m2: the hourly values normalise to the given kWh/m2.
    sim = ParametricSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.building_floor_area = dict(AREAS)
    heating_j = np.asarray(hourly_heating_kwh_per_m2, dtype=float) * J_PER_KWH * AREAS['office_a']
    sim.outputs_param_simulation = pd.DataFrame([
        {'x': 1, 'epw': 'Seville', 'idf': 'office_a', HEATING: heating_j.tolist()},
    ])
    sim.outputs_param_simulation.attrs['parameters_names'] = ['x']
    sim.last_run_type = 'parametric'
    return sim


def _hours_per_month(february_days):
    return [24.0 * days for days in (31, february_days, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)]


def test_daily_totals_gather_the_24_hourly_values_of_each_energyplus_day():
    sim = _single_simulation_session(np.arange(1, 73))
    sim.get_hourly_df(normalize_per_m2=True)

    daily = sim.get_daily_df()

    assert daily['day'].astype(str).tolist() == ['2023-01-01', '2023-01-02', '2023-01-03']
    assert daily[HEATING_KWH_M2].tolist() == pytest.approx([300.0, 876.0, 1452.0])


def test_monthly_totals_of_a_full_energyplus_year_follow_its_calendar():
    sim = _single_simulation_session(np.ones(8760))
    hourly = sim.get_hourly_df(normalize_per_m2=True)

    monthly = sim.get_monthly_df()

    assert hourly['datetime'].iloc[0] == pd.Timestamp('2023-01-01 01:00')
    assert hourly['datetime'].iloc[-1] == pd.Timestamp('2024-01-01 00:00')
    assert monthly['month'].astype(str).tolist() == [f'2023-{month:02d}' for month in range(1, 13)]
    assert monthly[HEATING_KWH_M2].tolist() == pytest.approx(_hours_per_month(february_days=28))


def test_a_full_year_of_8784_hourly_values_is_put_in_a_leap_year():
    sim = _single_simulation_session(np.ones(8784))
    hourly = sim.get_hourly_df(normalize_per_m2=True)

    monthly = sim.get_monthly_df()

    assert hourly['datetime'].iloc[0] == pd.Timestamp('2024-01-01 01:00')
    assert hourly['datetime'].iloc[-1] == pd.Timestamp('2025-01-01 00:00')
    assert monthly[HEATING_KWH_M2].tolist() == pytest.approx(_hours_per_month(february_days=29))


def test_an_explicit_start_date_keeps_its_year():
    sim = _single_simulation_session(np.ones(8760))

    hourly = sim.get_hourly_df(start_date='2024-01-01 01')

    assert hourly['datetime'].iloc[0] == pd.Timestamp('2024-01-01 01:00')
    assert (hourly['datetime'] == pd.Timestamp('2024-02-29 12:00')).any()
    assert hourly['datetime'].iloc[-1] == pd.Timestamp('2024-12-31 00:00')


def _write_full_year_csv(sim_dir, hours):
    sim_dir.mkdir(parents=True)
    csv_table = pd.DataFrame({'Date/Time': _energyplus_timestamps(hours), HEATING: np.full(hours, J_PER_KWH)})
    csv_table.to_csv(sim_dir / 'eplusout.csv', index=False)
    return str(sim_dir / 'eplusout.csv')


@pytest.mark.parametrize(('hours', 'year'), [(8760, 2023), (8784, 2024)])
@pytest.mark.parametrize('source', ['parametric', 'optimisation'])
def test_the_start_date_read_from_the_csv_files_gets_its_year_from_the_length_of_the_series(tmp_path, source, hours, year):
    csv_path = _write_full_year_csv(tmp_path / 'sim', hours)
    if source == 'parametric':
        sim = ParametricSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
        sim.outputs_param_simulation = pd.DataFrame([
            {'x': 1, 'epw': 'Seville', 'idf': 'office_a', 'output_dir': str(tmp_path / 'sim')},
        ])
        sim.outputs_param_simulation.attrs['parameters_names'] = ['x']
        sim.last_run_type = 'parametric'
        hourly = sim.get_hourly_df_parametric(skip_confirmation=True, start_date=None)
    else:
        sim = OptimisationSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
        sim.problem = _DummyProblem(inputs=['x'], outputs=['Heating:Electricity'])
        sim.outputs_optimisation = pd.DataFrame([
            {'x': 1.0, 'epw': 'Seville', 'idf': 'office_a', 'pareto-optimal': True, 'simulation_output_csv_path': csv_path},
        ])
        sim.last_run_type = 'optimisation'
        hourly = sim.get_hourly_df(skip_confirmation=True)

    assert hourly['datetime'].iloc[0] == pd.Timestamp(f'{year}-01-01 01:00')
    assert hourly['datetime'].iloc[-1] == pd.Timestamp(f'{year + 1}-01-01 00:00')


def test_hourly_methods_keep_their_default_start_date():
    for name in ('get_hourly_df', 'get_output_df', 'get_daily_df', 'get_monthly_df', 'get_runperiod_df'):
        assert inspect.signature(getattr(ParametricSimulation, name)).parameters['start_date'].default == '2024-01-01 01'
        assert inspect.signature(getattr(OptimisationSimulation, name)).parameters['start_date'].default is None
    assert inspect.signature(expand_to_hourly_dataframe).parameters['start_date'].default == '2024-01-01 01'


def _timeline_table(labels):
    return pd.DataFrame({'epw': 'Seville', 'idf': 'office_a', 'datetime': pd.to_datetime(labels), HEATING: 1.0})


def test_timestep_values_are_grouped_into_the_day_and_month_of_their_interval():
    sim = ParametricSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    # 15-minute values from 31 January 00:15 to 2 February 00:00 (the 24:00 of 1 February).
    labels = pd.date_range('2023-01-31 00:15', periods=4 * 24 * 2, freq='15min')
    table = _timeline_table(labels)

    daily = sim._aggregate_hourly_dataframe(df_hourly=table, source='parametric', frequency='daily')
    monthly = sim._aggregate_hourly_dataframe(df_hourly=table, source='parametric', frequency='monthly')

    assert daily['day'].astype(str).tolist() == ['2023-01-31', '2023-02-01']
    assert daily[HEATING].tolist() == [96.0, 96.0]
    assert monthly['month'].astype(str).tolist() == ['2023-01', '2023-02']
    assert monthly[HEATING].tolist() == [96.0, 96.0]


@pytest.mark.parametrize(
    ('labels', 'frequency', 'expected_periods', 'expected_sums'),
    [
        (pd.date_range('2023-01-01 00:00', periods=48, freq='h'), 'daily', ['2023-01-01', '2023-01-02'], [24.0, 24.0]),
        (pd.date_range('2023-01-01', periods=3, freq='D'), 'daily', ['2023-01-01', '2023-01-02', '2023-01-03'], [1.0] * 3),
        (pd.date_range('2023-01-01', periods=3, freq='MS'), 'monthly', ['2023-01', '2023-02', '2023-03'], [1.0] * 3),
    ],
    ids=['hourly_labels_at_interval_start', 'daily_values', 'monthly_values'],
)
def test_labels_at_the_start_of_each_interval_and_daily_or_monthly_values_are_grouped_as_they_are(
        labels, frequency, expected_periods, expected_sums):
    sim = ParametricSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)

    table = sim._aggregate_hourly_dataframe(df_hourly=_timeline_table(labels), source='parametric', frequency=frequency)

    period_column = PERIOD_COLUMN[frequency]
    assert table[period_column].astype(str).tolist() == expected_periods
    assert table[HEATING].tolist() == expected_sums
