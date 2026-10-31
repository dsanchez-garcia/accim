"""Schema-heterogeneity tests for the outputs grouped with ``split_by``.

The hourly and aggregated output methods of ParametricSimulation and OptimisationSimulation
(get_hourly_df, get_output_df, get_daily_df, get_monthly_df and get_runperiod_df, and their
get_*_parametric / get_*_optimisation variants) accept ``split_by``: the name of a column ('idf',
'epw', a parameter) or of a category of the mapping rules (set_category_mapping). They then return
a dictionary {group: DataFrame}, also stored in ``outputs_*_hourly_by_category`` and
``outputs_*_aggregated_by_category[frequency]``.

Different models report different outputs: a building of two zones has no values for the third
zone of another one, and a meter such as NaturalGas:Facility only exists in a model with gas
equipment. The table of all the simulations keeps the union of these outputs, empty (NaN) for the
simulations that do not report them. The contract pinned here is that, with
``drop_all_empty_output_columns=True`` (the default), each group keeps the realistic schema of its
own models: the outputs without any value in the group are dropped, while the identifier columns
(parameters, 'epw', 'idf', 'pareto-optimal', categories, and 'hour'/'datetime' or the 'day'/'month'
period) are kept in every group, even where they are empty. With
``drop_all_empty_output_columns=False``, every group keeps the full schema, with the outputs its
models do not report left empty.

The fake simulations write eplusout.csv files with different columns: a house of two zones with a
gas boiler and an all-electric office of three zones, simulated with two weather files (the house
only in Seville). The tests pin:

- the hourly groups by IDF, by EPW and by category: the output columns of each group, the
  identifiers in every group, and the values of each simulation (the outputs its IDF does not
  report stay empty, never filled with the values of another column or simulation);
- the downstream handling of the groups: their aggregation to daily, monthly and runperiod tables
  (energy summed, temperatures and rates averaged, each value in its own period), their
  normalisation per m2 with the floor area of the IDF of each row (only the columns in J are
  converted, and an IDF without floor area raises a ValueError), their concatenation back into the
  full table, the hourly plots of each group, which resolve only the zones of its IDF, and the
  groups stored in the session, replaced by each call (cleared by a call without split_by or by
  loading another hourly table);
- the parametric and the optimisation variants of every method.

They also pin three fixes. Before, the sum of an output that a simulation does not report was 0.0
instead of empty, so the aggregated groups kept the energy outputs of the other IDFs (filled with
zeros) and the aggregated tables showed consumptions that EnergyPlus never reported; the
aggregation left out the simulations whose identifier was missing, such as a category that no rule
matches (the 'uncategorized' group); and normalize_outputs() left in J the groups that split_by
stored for the tables it normalised.
"""
import datetime
import inspect
import os
import re
from collections import namedtuple

import matplotlib
import numpy as np
import pandas as pd
import pytest

from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation

matplotlib.use('Agg')

J_PER_KWH = 3.6e6
HOURS = 24 * 32  # from 1 January 01:00 to 2 February 00:00: 32 days in two months
SOURCES = ['parametric', 'optimisation']
FREQUENCIES = ['daily', 'monthly', 'runperiod']
PERIOD_COLUMN = {'daily': 'day', 'monthly': 'month', 'runperiod': None}
PERIOD_LABELS = {
    'daily': [str(datetime.date(2023, 1, 1) + datetime.timedelta(days=day)) for day in range(HOURS // 24)],
    'monthly': ['2023-01', '2023-02'],
}
ROWS_PER_SIMULATION = {None: HOURS, 'daily': HOURS // 24, 'monthly': 2, 'runperiod': 1}

IDENTIFIERS = {'parametric': ['x', 'epw', 'idf'], 'optimisation': ['x', 'epw', 'idf', 'pareto-optimal']}
HOURLY_GROUPS = {
    'parametric': 'outputs_param_simulation_hourly_by_category',
    'optimisation': 'outputs_optimisation_hourly_by_category',
}
AGGREGATED_GROUPS = {
    'parametric': 'outputs_param_simulation_aggregated_by_category',
    'optimisation': 'outputs_optimisation_aggregated_by_category',
}


def _temperature(zone):
    return f'BLOCK1:ZONE{zone}:Zone Operative Temperature [C](Hourly)'


def _heating(zone):
    return f'BLOCK1:ZONE{zone}:Zone Air System Sensible Heating Energy [J](Hourly)'


COOLING_RATE = 'BLOCK1:ZONE3:Zone Air System Sensible Cooling Rate [W](Hourly)'
ELECTRICITY = 'Electricity:Facility [J](Hourly)'
GAS = 'NaturalGas:Facility [J](Hourly)'

ZONES = {'house': (1, 2), 'office': (1, 2, 3)}
OUTPUTS_BY_IDF = {
    # A house of two zones with a gas boiler.
    'house': [column for zone in ZONES['house'] for column in (_temperature(zone), _heating(zone))]
    + [ELECTRICITY, GAS],
    # An all-electric office of three zones, whose zone 3 reports its cooling, off in winter (0 W).
    'office': [column for zone in ZONES['office'] for column in (_temperature(zone), _heating(zone))]
    + [COOLING_RATE, ELECTRICITY],
}
AREAS = {'house': 50.0, 'office': 200.0}

Simulation = namedtuple('Simulation', ['x', 'epw', 'idf', 'seed'])
SIMULATIONS = [
    Simulation(1, 'Seville', 'house', 0),
    Simulation(2, 'Seville', 'house', 1),
    Simulation(1, 'Seville', 'office', 2),
    Simulation(1, 'Oslo', 'office', 3),
]


def _reported_outputs(simulations):
    """Outputs reported by the IDFs of the simulations, in the order the hourly table gets them."""
    outputs = []
    for simulation in simulations:
        for column in OUTPUTS_BY_IDF[simulation.idf]:
            if column not in outputs:
                outputs.append(column)
    return outputs


def _normalised(column):
    return column.replace('[J]', '[kWh/m2]')


ALL_OUTPUTS = _reported_outputs(SIMULATIONS)
KNOWN_OUTPUTS = set(ALL_OUTPUTS) | {_normalised(column) for column in ALL_OUTPUTS}


def _hourly_values(column, seed):
    """Raw hourly values of an output in one simulation, different for each output and simulation."""
    hour = np.arange(HOURS)
    if column == COOLING_RATE:
        return np.zeros(HOURS)
    position = ALL_OUTPUTS.index(column)
    if '[C]' in column:
        return 18.0 + seed + 0.5 * position + 0.1 * (hour % 24)
    return (1.0 + hour % 24 + 10.0 * seed + position) * J_PER_KWH


def _expected_values(column, simulation, frequency=None, normalised=False):
    """Values of an output of a simulation, computed independently from the raw hourly values."""
    values = _hourly_values(column, simulation.seed)
    if normalised and '[J]' in column:
        values = values / (J_PER_KWH * AREAS[simulation.idf])
    if frequency is None:
        return values
    periods = {
        'daily': np.split(values, HOURS // 24),
        'monthly': np.split(values, [31 * 24]),
        'runperiod': [values],
    }[frequency]
    reduce = np.sum if '[J]' in column else np.mean
    return np.array([reduce(period) for period in periods])


def _simulations_where(**conditions):
    return [s for s in SIMULATIONS if all(getattr(s, key) == value for (key, value) in conditions.items())]


def _output_columns(table):
    return [column for column in table.columns if column in KNOWN_OUTPUTS]


def _rows_of(table, simulation):
    return table[(table['x'] == simulation.x) & (table['epw'] == simulation.epw) & (table['idf'] == simulation.idf)]


def _assert_group_holds(group, simulations, frequency=None, normalised=False):
    """Each simulation of the group has its own rows, with the values of the outputs of its IDF.

    In the hourly groups, the outputs that its IDF does not report must also be empty in its rows.
    """
    assert len(group) == len(simulations) * ROWS_PER_SIMULATION[frequency]
    for simulation in simulations:
        rows = _rows_of(group, simulation)
        if frequency is None:
            rows = rows.sort_values('hour')
            assert rows['hour'].tolist() == list(range(1, HOURS + 1))
        elif PERIOD_COLUMN[frequency] is not None:
            rows = rows.sort_values(PERIOD_COLUMN[frequency])
            assert rows[PERIOD_COLUMN[frequency]].astype(str).tolist() == PERIOD_LABELS[frequency]
        else:
            assert len(rows) == 1
        for column in OUTPUTS_BY_IDF[simulation.idf]:
            name = _normalised(column) if normalised else column
            expected = _expected_values(column, simulation, frequency, normalised)
            assert rows[name].to_numpy() == pytest.approx(expected), (simulation, name)
        if frequency is None:
            for column in ALL_OUTPUTS:
                name = _normalised(column) if normalised else column
                if column not in OUTPUTS_BY_IDF[simulation.idf] and name in group.columns:
                    assert rows[name].isna().all(), (simulation, name)


def _energyplus_timestamps(hours):
    """'Date/Time' labels of an EnergyPlus hourly CSV (the last hour of each day is 24:00)."""
    labels = []
    for index in range(hours):
        (day_index, hour) = divmod(index, 24)
        date = datetime.date(2023, 1, 1) + datetime.timedelta(days=day_index)
        labels.append(f' {date.month:02d}/{date.day:02d}  {hour + 1:02d}:00:00')
    return labels


class _DummyProblem:
    def __init__(self, inputs, outputs):
        self._names = {'inputs': list(inputs), 'outputs': list(outputs), 'constraints': []}

    def names(self, typ):
        return list(self._names[typ])


@pytest.fixture(autouse=True)
def _work_in_tmp_path(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)


@pytest.fixture(scope='module')
def simulation_dirs(tmp_path_factory):
    """Folder of each simulation, with an eplusout.csv holding only the outputs of its IDF."""
    root = tmp_path_factory.mktemp('split_by_schemas')
    timestamps = _energyplus_timestamps(HOURS)
    folders = {}
    for simulation in SIMULATIONS:
        folder = root / f'sim_{simulation.seed}'
        folder.mkdir()
        outputs = {column: _hourly_values(column, simulation.seed) for column in OUTPUTS_BY_IDF[simulation.idf]}
        pd.DataFrame({'Date/Time': timestamps, **outputs}).to_csv(folder / 'eplusout.csv', index=False)
        folders[simulation] = str(folder)
    return folders


def _session(source, simulation_dirs):
    """Results of the four simulations, as loaded after a parametric run or an optimisation."""
    rows = []
    for simulation in SIMULATIONS:
        folder = simulation_dirs[simulation]
        row = {
            'x': simulation.x if source == 'parametric' else float(simulation.x),
            'Electricity:Facility': _hourly_values(ELECTRICITY, simulation.seed).sum(),
            'epw': simulation.epw,
            'idf': simulation.idf,
        }
        if source == 'parametric':
            row['output_dir'] = folder
        else:
            row['pareto-optimal'] = True
            row['simulation_directory'] = folder
            row['simulation_output_csv_path'] = os.path.join(folder, 'eplusout.csv')
        rows.append(row)
    sim_class = ParametricSimulation if source == 'parametric' else OptimisationSimulation
    sim = sim_class(buildings=None, epws=['Seville.epw', 'Oslo.epw'], parameters_type=None, bypass_addAccis=True)
    if source == 'parametric':
        sim.outputs_param_simulation = pd.DataFrame(rows)
        sim.outputs_param_simulation.attrs['parameters_names'] = ['x']
    else:
        sim.problem = _DummyProblem(inputs=['x'], outputs=['Electricity:Facility'])
        sim.outputs_optimisation = pd.DataFrame(rows)
    sim.last_run_type = source
    sim.building_floor_area = dict(AREAS)
    return sim


def _call(sim, method, **kwargs):
    return getattr(sim, method)(skip_confirmation=True, **kwargs)


def _table(sim, source, frequency=None):
    prefix = 'outputs_param_simulation' if source == 'parametric' else 'outputs_optimisation'
    return getattr(sim, f"{prefix}_{frequency or 'hourly'}")


# ----------------------------------------------------------------------------- default contract

SPLIT_METHODS = {
    ParametricSimulation: [
        'get_hourly_df_parametric', 'get_hourly_df', 'get_output_df', 'get_daily_df', 'get_monthly_df',
        'get_runperiod_df',
    ],
    OptimisationSimulation: [
        'get_hourly_df_optimisation', 'get_output_df_optimisation', 'get_daily_df_optimisation',
        'get_monthly_df_optimisation', 'get_runperiod_df_optimisation', 'get_hourly_df', 'get_output_df',
        'get_daily_df', 'get_monthly_df', 'get_runperiod_df',
    ],
}


def test_every_method_with_split_by_drops_the_empty_output_columns_by_default():
    for (sim_class, method_names) in SPLIT_METHODS.items():
        for name in method_names:
            parameters = inspect.signature(getattr(sim_class, name)).parameters
            assert parameters['split_by'].default is None, (sim_class.__name__, name)
            assert parameters['drop_all_empty_output_columns'].default is True, (sim_class.__name__, name)


# ----------------------------------------------------------------------------- hourly groups

@pytest.mark.parametrize('source', SOURCES)
def test_hourly_groups_by_idf_keep_only_the_outputs_their_idf_reports(simulation_dirs, source):
    sim = _session(source, simulation_dirs)

    groups = _call(sim, 'get_hourly_df', split_by='idf')

    full = _table(sim, source)
    first_columns = IDENTIFIERS[source] + ['hour', 'datetime']
    assert list(full.columns[:len(first_columns)]) == first_columns
    assert set(_output_columns(full)) == set(ALL_OUTPUTS)
    assert getattr(sim, HOURLY_GROUPS[source]) is groups
    assert list(groups) == ['house', 'office']
    assert set(_output_columns(groups['house'])) == set(OUTPUTS_BY_IDF['house'])
    assert set(_output_columns(groups['office'])) == set(OUTPUTS_BY_IDF['office'])
    for (idf, group) in groups.items():
        unreported = set(ALL_OUTPUTS) - set(OUTPUTS_BY_IDF[idf])
        # The schema of the full table, in the same order, without the outputs the IDF does not report.
        assert list(group.columns) == [column for column in full.columns if column not in unreported]
        _assert_group_holds(group, _simulations_where(idf=idf))
    # Only the outputs without any value are dropped: an output reported as 0 is kept.
    assert (groups['office'][COOLING_RATE] == 0.0).all()


@pytest.mark.parametrize('source', SOURCES)
def test_hourly_groups_by_epw_keep_the_outputs_of_the_idfs_simulated_with_each_epw(simulation_dirs, source):
    sim = _session(source, simulation_dirs)

    groups = _call(sim, 'get_hourly_df', split_by='epw')

    assert list(groups) == ['Seville', 'Oslo']
    # Seville is simulated with both IDFs, Oslo only with the office.
    assert set(_output_columns(groups['Seville'])) == set(ALL_OUTPUTS)
    assert set(_output_columns(groups['Oslo'])) == set(OUTPUTS_BY_IDF['office'])
    first_columns = IDENTIFIERS[source] + ['hour', 'datetime']
    for (epw, group) in groups.items():
        assert list(group.columns[:len(first_columns)]) == first_columns
        _assert_group_holds(group, _simulations_where(epw=epw))


@pytest.mark.parametrize('source', SOURCES)
def test_hourly_groups_without_dropping_share_the_full_schema_with_empty_unreported_outputs(
        simulation_dirs, source):
    sim = _session(source, simulation_dirs)

    groups = _call(sim, 'get_hourly_df', split_by='idf', drop_all_empty_output_columns=False)

    full = _table(sim, source)
    for (idf, group) in groups.items():
        assert list(group.columns) == list(full.columns)
        unreported = [column for column in ALL_OUTPUTS if column not in OUTPUTS_BY_IDF[idf]]
        assert len(unreported) > 0
        assert group[unreported].isna().all().all()
        _assert_group_holds(group, _simulations_where(idf=idf))


@pytest.mark.parametrize('table', ['hourly', 'runperiod'])
@pytest.mark.parametrize('source', SOURCES)
def test_groups_concatenate_back_into_the_full_table_without_misaligned_columns(simulation_dirs, source, table):
    sim = _session(source, simulation_dirs)

    groups = _call(sim, f'get_{table}_df', split_by='idf')

    full = _table(sim, source, None if table == 'hourly' else table)
    recombined = pd.concat(list(groups.values()), ignore_index=True)
    assert set(recombined.columns) == set(full.columns)
    keys = IDENTIFIERS[source] + (['hour'] if table == 'hourly' else [])
    pd.testing.assert_frame_equal(
        recombined[list(full.columns)].sort_values(keys).reset_index(drop=True),
        full.sort_values(keys).reset_index(drop=True),
    )


@pytest.mark.parametrize('source', SOURCES)
def test_a_call_without_split_by_clears_the_groups_stored_for_its_table(simulation_dirs, source):
    sim = _session(source, simulation_dirs)
    _call(sim, 'get_hourly_df', split_by='idf')
    _call(sim, 'get_daily_df', split_by='idf')

    hourly = _call(sim, 'get_hourly_df')
    daily = _call(sim, 'get_daily_df')

    assert isinstance(hourly, pd.DataFrame) and isinstance(daily, pd.DataFrame)
    assert getattr(sim, HOURLY_GROUPS[source]) is None
    assert getattr(sim, AGGREGATED_GROUPS[source])['daily'] is None


# ----------------------------------------------------------------------------- groups by category

@pytest.mark.parametrize('source', SOURCES)
def test_groups_by_an_idf_category_keep_the_category_and_the_outputs_of_their_idf(simulation_dirs, source):
    sim = _session(source, simulation_dirs)
    sim.set_category_mapping(idf_mapping_rules={'use': {'residential': 'house', 'tertiary': 'office'}})

    hourly_groups = _call(sim, 'get_hourly_df', split_by='use')
    runperiod_groups = _call(sim, 'get_runperiod_df', split_by='use')

    assert list(hourly_groups) == ['residential', 'tertiary']
    assert set(runperiod_groups) == {'residential', 'tertiary'}
    for (category, idf) in [('residential', 'house'), ('tertiary', 'office')]:
        simulations = _simulations_where(idf=idf)
        hourly = hourly_groups[category]
        assert set(hourly['use']) == {category}
        assert set(_output_columns(hourly)) == set(OUTPUTS_BY_IDF[idf])
        _assert_group_holds(hourly, simulations)
        # The category column added by the hourly split stays an identifier: one row per simulation.
        runperiod = runperiod_groups[category]
        assert runperiod['use'].tolist() == [category] * len(simulations)
        _assert_group_holds(runperiod, simulations, 'runperiod')


@pytest.mark.parametrize('source', SOURCES)
def test_identifier_columns_are_kept_in_the_groups_where_they_are_empty(simulation_dirs, source):
    sim = _session(source, simulation_dirs)
    # The rules do not cover the office: its simulations have no 'use'.
    sim.set_category_mapping(idf_mapping_rules={'use': {'residential': 'house'}})
    sim.apply_category_mapping(df_types=[source])

    groups = _call(sim, 'get_hourly_df', split_by='epw')

    oslo = groups['Oslo']
    assert set(IDENTIFIERS[source] + ['use', 'hour', 'datetime']) <= set(oslo.columns)
    assert oslo['use'].isna().all()
    assert set(_output_columns(oslo)) == set(OUTPUTS_BY_IDF['office'])
    assert set(groups['Seville']['use'].dropna()) == {'residential'}


@pytest.mark.parametrize('source', SOURCES)
def test_aggregation_keeps_the_simulations_of_the_uncategorized_group(simulation_dirs, source):
    sim = _session(source, simulation_dirs)
    sim.set_category_mapping(idf_mapping_rules={'use': {'residential': 'house'}})
    hourly_groups = _call(sim, 'get_hourly_df', split_by='use')
    assert set(hourly_groups) == {'residential', 'uncategorized'}

    runperiod_groups = _call(sim, 'get_runperiod_df', split_by='use')

    # Before, the simulations without category were left out of the aggregated tables.
    assert set(runperiod_groups) == {'residential', 'uncategorized'}
    runperiod = _table(sim, source, 'runperiod')
    assert len(runperiod) == len(SIMULATIONS)
    assert runperiod.loc[runperiod['idf'] == 'office', 'use'].isna().all()
    _assert_group_holds(runperiod_groups['residential'], _simulations_where(idf='house'), 'runperiod')
    _assert_group_holds(runperiod_groups['uncategorized'], _simulations_where(idf='office'), 'runperiod')


@pytest.mark.parametrize('source', SOURCES)
def test_aggregation_keeps_the_simulations_whose_results_have_no_category(simulation_dirs, source):
    sim = _session(source, simulation_dirs)
    # As at the end of a run when the rules are set before it; no rule covers the office.
    sim.set_category_mapping(idf_mapping_rules={'use': {'residential': 'house'}})
    sim.apply_category_mapping(df_types=[source])

    daily = _call(sim, 'get_daily_df')

    assert len(daily) == len(SIMULATIONS) * ROWS_PER_SIMULATION['daily']
    for simulation in SIMULATIONS:
        rows = _rows_of(daily, simulation)
        assert rows['use'].isna().all() == (simulation.idf == 'office')
    _assert_group_holds(daily, SIMULATIONS, 'daily')


# ----------------------------------------------------------------------------- aggregated groups

@pytest.mark.parametrize('frequency', FREQUENCIES)
@pytest.mark.parametrize('source', SOURCES)
def test_aggregated_groups_keep_the_values_of_the_outputs_of_their_idf(simulation_dirs, source, frequency):
    sim = _session(source, simulation_dirs)

    groups = _call(sim, f'get_{frequency}_df', split_by='idf')

    assert set(groups) == {'house', 'office'}
    assert getattr(sim, AGGREGATED_GROUPS[source])[frequency] is groups
    first_columns = IDENTIFIERS[source] + ([PERIOD_COLUMN[frequency]] if PERIOD_COLUMN[frequency] else [])
    for (idf, group) in groups.items():
        assert list(group.columns[:len(first_columns)]) == first_columns
        assert set(_output_columns(group)) == set(OUTPUTS_BY_IDF[idf])
        _assert_group_holds(group, _simulations_where(idf=idf), frequency)


@pytest.mark.parametrize('source', SOURCES)
def test_aggregated_groups_drop_every_output_their_idf_does_not_report(simulation_dirs, source):
    sim = _session(source, simulation_dirs)
    hourly_groups = _call(sim, 'get_hourly_df', split_by='idf')

    for frequency in FREQUENCIES:
        groups = _call(sim, f'get_{frequency}_df', split_by='idf')
        for (idf, group) in groups.items():
            # The same outputs as the hourly group of the IDF. Before, the energy outputs of the
            # other IDF (zone 3, NaturalGas:Facility) were kept, filled with zeros.
            assert set(_output_columns(group)) == set(_output_columns(hourly_groups[idf])), (frequency, idf)
            assert set(_output_columns(group)) == set(OUTPUTS_BY_IDF[idf]), (frequency, idf)


@pytest.mark.parametrize('source', SOURCES)
def test_aggregated_groups_without_dropping_leave_empty_the_outputs_their_idf_does_not_report(
        simulation_dirs, source):
    sim = _session(source, simulation_dirs)
    _call(sim, 'get_hourly_df')

    for frequency in FREQUENCIES:
        groups = _call(sim, f'get_{frequency}_df', split_by='idf', drop_all_empty_output_columns=False)
        full = _table(sim, source, frequency)
        for (idf, group) in groups.items():
            assert list(group.columns) == list(full.columns)
            for column in ALL_OUTPUTS:
                if column not in OUTPUTS_BY_IDF[idf]:
                    assert group[column].isna().all(), (frequency, idf, column)
            _assert_group_holds(group, _simulations_where(idf=idf), frequency)


def test_aggregation_without_identifier_columns_leaves_empty_the_sums_without_values():
    sim = ParametricSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    # A table built with include_summary_columns=False: no identifier columns.
    table = pd.DataFrame({
        'datetime': pd.date_range('2023-01-01 01:00', periods=48, freq='h'),
        ELECTRICITY: np.arange(1.0, 49.0) * J_PER_KWH,
        GAS: np.nan,
        _temperature(1): 20.0,
    })

    runperiod = sim._aggregate_hourly_dataframe(df_hourly=table, frequency='runperiod')
    daily = sim._aggregate_hourly_dataframe(df_hourly=table, frequency='daily')

    assert runperiod[ELECTRICITY].tolist() == [1176.0 * J_PER_KWH]
    assert runperiod[GAS].isna().all()
    assert runperiod[_temperature(1)].tolist() == [20.0]
    assert daily[ELECTRICITY].tolist() == [300.0 * J_PER_KWH, 876.0 * J_PER_KWH]
    assert daily[GAS].isna().all()


# ----------------------------------------------------------------------------- normalisation per m2

@pytest.mark.parametrize('split_by', ['idf', 'epw'])
@pytest.mark.parametrize('source', SOURCES)
def test_hourly_groups_normalised_per_m2_divide_each_row_by_the_floor_area_of_its_idf(
        simulation_dirs, source, split_by):
    sim = _session(source, simulation_dirs)

    groups = _call(sim, 'get_hourly_df', split_by=split_by, normalize_per_m2=True)

    assert sim._is_df_type_normalized(f'{source}_hourly')
    for (key, group) in groups.items():
        # The groups by EPW hold rows of both IDFs (Seville), each one with its own floor area.
        simulations = _simulations_where(**{split_by: key})
        expected_outputs = {_normalised(column) for column in _reported_outputs(simulations)}
        assert set(_output_columns(group)) == expected_outputs
        _assert_group_holds(group, simulations, normalised=True)


@pytest.mark.parametrize('normalised_table', ['hourly', 'aggregated'])
@pytest.mark.parametrize('source', SOURCES)
def test_monthly_groups_normalised_per_m2_divide_each_row_by_the_floor_area_of_its_idf(
        simulation_dirs, source, normalised_table):
    sim = _session(source, simulation_dirs)
    _call(sim, 'get_hourly_df', normalize_per_m2=(normalised_table == 'hourly'))

    # When the hourly table is already in kWh/m2, the monthly table must not be divided again.
    groups = _call(sim, 'get_monthly_df', split_by='epw', normalize_per_m2=True)

    assert sim._is_df_type_normalized(f'{source}_monthly')
    assert sim._is_df_type_normalized(f'{source}_hourly') == (normalised_table == 'hourly')
    assert set(groups) == {'Seville', 'Oslo'}
    for (epw, group) in groups.items():
        simulations = _simulations_where(epw=epw)
        assert set(_output_columns(group)) == {_normalised(column) for column in _reported_outputs(simulations)}
        _assert_group_holds(group, simulations, 'monthly', normalised=True)


@pytest.mark.parametrize('method', ['get_hourly_df', 'get_runperiod_df'])
@pytest.mark.parametrize('source', SOURCES)
def test_grouped_normalisation_rejects_an_idf_without_floor_area(simulation_dirs, source, method):
    sim = _session(source, simulation_dirs)
    sim.building_floor_area = {'house': AREAS['house']}

    with pytest.raises(ValueError, match=re.escape("has no floor area for the IDF(s) ['office']")):
        _call(sim, method, split_by='idf', normalize_per_m2=True)

    frequency = None if method == 'get_hourly_df' else 'runperiod'
    # The table is left complete and in J, and no group in kWh/m2 is stored.
    assert not sim._is_df_type_normalized(f"{source}_{frequency or 'hourly'}")
    assert set(_output_columns(_table(sim, source, frequency))) == set(ALL_OUTPUTS)
    if frequency is None:
        assert getattr(sim, HOURLY_GROUPS[source]) is None
    else:
        stored = getattr(sim, AGGREGATED_GROUPS[source]).get(frequency) or {}
        for group in stored.values():
            assert set(_output_columns(group)) <= set(ALL_OUTPUTS)


@pytest.mark.parametrize('source', SOURCES)
def test_normalize_outputs_normalises_the_stored_groups_with_the_floor_area_of_each_idf(simulation_dirs, source):
    sim = _session(source, simulation_dirs)
    hourly_groups = _call(sim, 'get_hourly_df', split_by='epw')
    daily_groups = _call(sim, 'get_daily_df', split_by='epw')

    sim.normalize_outputs(df_types=[f'{source}_hourly', f'{source}_daily'])

    assert sim._is_df_type_normalized(f'{source}_hourly') and sim._is_df_type_normalized(f'{source}_daily')
    # The stored groups are the ones returned by the methods, converted in place. Before, they were left in J.
    assert getattr(sim, HOURLY_GROUPS[source]) is hourly_groups
    assert getattr(sim, AGGREGATED_GROUPS[source])['daily'] is daily_groups
    for (groups, frequency) in [(hourly_groups, None), (daily_groups, 'daily')]:
        for (epw, group) in groups.items():
            # The Seville group holds rows of both IDFs, each one divided by the area of its IDF.
            assert not [column for column in group.columns if '[J]' in column]
            _assert_group_holds(group, _simulations_where(epw=epw), frequency, normalised=True)


@pytest.mark.parametrize('source', SOURCES)
def test_normalize_outputs_leaves_the_table_and_its_groups_unchanged_when_a_group_has_no_floor_area(
        simulation_dirs, source):
    sim = _session(source, simulation_dirs)
    groups = _call(sim, 'get_hourly_df', split_by='idf')
    # A group whose IDF has no floor area (the table itself can be normalised).
    groups['office']['idf'] = 'school'
    table_before = _table(sim, source).copy()
    groups_before = {name: group.copy() for (name, group) in groups.items()}

    with pytest.raises(ValueError, match=re.escape("has no floor area for the IDF(s) ['school'] of the group")):
        sim.normalize_outputs(df_types=[f'{source}_hourly'])

    assert not sim._is_df_type_normalized(f'{source}_hourly')
    pd.testing.assert_frame_equal(_table(sim, source), table_before)
    for (name, group) in groups.items():
        pd.testing.assert_frame_equal(group, groups_before[name])


@pytest.mark.parametrize('source', SOURCES)
def test_loading_another_hourly_table_drops_the_groups_of_the_replaced_one(simulation_dirs, tmp_path, source):
    sim = _session(source, simulation_dirs)
    # Results of the house only, saved to be loaded later.
    house = [index for (index, simulation) in enumerate(SIMULATIONS) if simulation.idf == 'house']
    results = sim.outputs_param_simulation if source == 'parametric' else sim.outputs_optimisation
    results.iloc[house].to_csv(tmp_path / 'results.csv', index=False)
    _call(sim, 'get_hourly_df', simulation_indices=house).to_csv(tmp_path / 'hourly.csv', index=False)
    _call(sim, 'get_hourly_df', split_by='idf')

    getattr(sim, f'load_outputs_{source}')(
        csv_path=str(tmp_path / 'results.csv'),
        hourly_csv_path=str(tmp_path / 'hourly.csv'),
    )

    assert getattr(sim, HOURLY_GROUPS[source]) is None
    # Only the loaded IDF needs a floor area: the groups of the replaced table (with the office) are gone.
    sim.building_floor_area = {'house': AREAS['house']}
    sim.normalize_outputs(df_types=[f'{source}_hourly'])
    assert sim._is_df_type_normalized(f'{source}_hourly')
    assert _normalised(_heating(1)) in _table(sim, source).columns


# ----------------------------------------------------------------------------- plots of the groups

@pytest.mark.parametrize('source', SOURCES)
def test_hourly_plots_of_each_group_resolve_only_the_zones_of_its_idf(simulation_dirs, tmp_path, source):
    sim = _session(source, simulation_dirs)
    groups = _call(sim, 'get_hourly_df', split_by='idf')

    for (idf, group) in groups.items():
        # The variable matches the heating of 2 zones in the house group and of 3 in the office group.
        fig = sim.plot_load_duration_curves(
            'Zone Air System Sensible Heating Energy',
            df=group,
            panel='x',
            hue='epw',
            zone_aggregation='sum',
            normalize_per_m2=True,
            out_dir=str(tmp_path),
            filename=f'load_duration_{idf}',
            dpi=30,
        )

        assert os.path.isfile(tmp_path / f'load_duration_{idf}.png')
        simulations = _simulations_where(idf=idf)
        assert len(fig.summary) == len(simulations)
        for simulation in simulations:
            panel = str(_rows_of(group, simulation)['x'].iloc[0])
            row = fig.summary[(fig.summary['panel'] == panel) & (fig.summary['hue'] == simulation.epw)]
            expected = sum(
                _hourly_values(_heating(zone), simulation.seed).sum() for zone in ZONES[idf]
            ) / (J_PER_KWH * AREAS[idf])
            assert row['total'].tolist() == pytest.approx([expected])
