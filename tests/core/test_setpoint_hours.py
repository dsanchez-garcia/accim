"""Tests for accim.data.postprocessing.setpoint_hours: the percentage of the occupied hours within the setpoints of
each zone and of the building, from the CSV files of the simulations or from a table of results, and the filter of
the simulations by a minimum percentage.

The CSV files have the names of the columns that EnergyPlus gives the EMS outputs of accim, and made-up values.
"""
import math

import pandas as pd
import pytest

from accim.data.postprocessing.setpoint_hours import (
    BUILDING,
    filter_by_hours_within_setpoints,
    hours_within_setpoints,
    percentage_column,
)

OCC = 'EMS:Occupied Hours_{zone} [H]({frequency})'
WITHIN = 'EMS:Occupied Comfortable Hours_No Applicability_{zone} [H]({frequency})'


def _csv(path, zones, frequency='Hourly', extra=None):
    """A CSV file of EnergyPlus with two hourly rows: zones is {zone: (occupied, within)} for each row."""
    columns = {'Date/Time': [' 01/01  01:00:00', ' 01/01  02:00:00'],
               'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)': [10.0, 11.0]}
    for zone, (occupied, within) in zones.items():
        columns[OCC.format(zone=zone, frequency=frequency)] = occupied
        columns[WITHIN.format(zone=zone, frequency=frequency)] = within
        columns[f'EMS:Comfortable Hours_No Applicability_{zone} [H]({frequency})'] = [1.0, 1.0]
    columns.update(extra or {})
    pd.DataFrame(columns).to_csv(path, index=False)
    return str(path)


def test_percentages_of_the_csv_files(tmp_path):
    first = _csv(tmp_path / 'Model[A.csv', {'BLOCK1_ZONE1': ([1.0, 1.0], [1.0, 0.5]),
                                            'BLOCK1_ZONE2': ([1.0, 0.0], [0.0, 0.0])})
    second = _csv(tmp_path / 'Model[B.csv', {'BLOCK1_ZONE1': ([1.0, 1.0], [1.0, 1.0]),
                                             'BLOCK1_ZONE2': ([1.0, 1.0], [1.0, 1.0])})

    summary = hours_within_setpoints([first, second])

    assert list(summary['Source']) == [first, second]
    assert list(summary['Occupied Hours_BLOCK1_ZONE1']) == [2.0, 2.0]
    assert list(summary['Occupied Comfortable Hours_No Applicability_BLOCK1_ZONE1']) == [1.5, 2.0]
    assert list(summary[percentage_column('BLOCK1_ZONE1')]) == [75.0, 100.0]
    assert list(summary[percentage_column('BLOCK1_ZONE2')]) == [0.0, 100.0]
    # The building: the occupied hours of each zone weigh the same (1.5 of 3 hours)
    assert list(summary[percentage_column(BUILDING)]) == [50.0, 100.0]


def test_a_zone_without_occupied_hours_has_no_percentage(tmp_path):
    csv = _csv(tmp_path / 'Model[A.csv', {'Z1': ([1.0, 1.0], [1.0, 1.0]), 'Z2': ([0.0, 0.0], [0.0, 0.0])})

    summary = hours_within_setpoints(csv)

    assert math.isnan(summary[percentage_column('Z2')].item())
    assert summary[percentage_column(BUILDING)].item() == 100.0


def test_several_frequencies_and_building_averages_are_not_added_twice(tmp_path):
    # The run period values of the same outputs, and the building averages of add_building_averages
    extra = {OCC.format(zone='Z1', frequency='RunPeriod'): [None, 2.0],
             WITHIN.format(zone='Z1', frequency='RunPeriod'): [None, 1.0],
             'EMS:Occupied Hours_Building_Average [H](Hourly)': [1.0, 1.0],
             'EMS:Occupied Comfortable Hours_No Applicability_Building_Average [H](Hourly)': [1.0, 1.0]}
    csv = _csv(tmp_path / 'Model[A.csv', {'Z1': ([1.0, 1.0], [1.0, 0.0])}, extra=extra)

    summary = hours_within_setpoints(csv)

    assert summary['Occupied Hours_Z1'].item() == 2.0
    assert [c for c in summary.columns if c.endswith('[%]')] == [percentage_column('Z1'), percentage_column(BUILDING)]
    assert summary[percentage_column(BUILDING)].item() == 50.0


def test_a_folder_stands_for_its_csv_files_of_results(tmp_path):
    _csv(tmp_path / 'Model[A.csv', {'Z1': ([1.0, 1.0], [1.0, 1.0])})
    pd.DataFrame({'Date/Time': ['x'], 'Electricity:Facility [J](Hourly)': [1.0]}).to_csv(
        tmp_path / 'Model[AMeter.csv', index=False)

    summary = hours_within_setpoints(tmp_path)

    assert [p.split('\\')[-1].split('/')[-1] for p in summary['Source']] == ['Model[A.csv']


def test_csv_files_without_the_hours(tmp_path):
    other = tmp_path / 'other.csv'
    pd.DataFrame({'Date/Time': ['x'], 'Zone Operative Temperature [C](Hourly)': [20.0]}).to_csv(other, index=False)
    csv = _csv(tmp_path / 'Model[A.csv', {'Z1': ([1.0, 1.0], [1.0, 1.0])})

    with pytest.warns(UserWarning, match='have no hours of the ACCIS'):
        summary = hours_within_setpoints([csv, other])
    assert list(summary['Source']) == [csv]
    with pytest.raises(ValueError, match='None of the 1 CSV files'):
        hours_within_setpoints(other)
    with pytest.raises(FileNotFoundError):
        hours_within_setpoints(tmp_path / 'missing.csv')


def test_percentages_of_a_table_of_results():
    # The results of the parametric module: the readers sum the hourly values and are named after the outputs (here
    # the second one keeps the time series)
    results = pd.DataFrame({
        'CustAST_m': [0.2, 0.3],
        'Occupied Hours_BLOCK1_ZONE1': [100.0, 100.0],
        'Occupied Comfortable Hours_No Applicability_BLOCK1_ZONE1': [90.0, 60.0],
        'Occupied Hours_BLOCK1_ZONE2': [[1.0, 1.0], [1.0, 1.0]],
        'Occupied Comfortable Hours_No Applicability_BLOCK1_ZONE2': [[1.0, 1.0], [0.0, 1.0]],
    })

    table = hours_within_setpoints(results)

    assert list(table.columns[:5]) == list(results.columns)
    assert list(table[percentage_column('BLOCK1_ZONE1')]) == [90.0, 60.0]
    assert list(table[percentage_column('BLOCK1_ZONE2')]) == [100.0, 50.0]
    assert list(table[percentage_column(BUILDING)]) == pytest.approx([100 * 92 / 102, 100 * 61 / 102])
    # The table is not changed, and the percentages can be computed again
    assert percentage_column(BUILDING) not in results
    assert hours_within_setpoints(table).equals(table)


def test_percentages_of_a_table_of_table():
    # The columns of Table: in upper case, with the zones named block:zone
    df = pd.DataFrame({'EMS:OCCUPIED HOURS_BLOCK1:ZONE1 [H](HOURLY)': [10.0],
                       'EMS:OCCUPIED COMFORTABLE HOURS_NO APPLICABILITY_BLOCK1:ZONE1 [H](HOURLY)': [9.0]})

    assert hours_within_setpoints(df)[percentage_column('BLOCK1:ZONE1')].item() == 90.0
    with pytest.raises(ValueError, match='has no columns'):
        hours_within_setpoints(pd.DataFrame({'Occupied Hours': [1.0]}))


@pytest.fixture
def results():
    return pd.DataFrame({
        'case': ['a', 'b', 'c', 'd'],
        'Occupied Hours_Z1': [10.0, 10.0, 10.0, 0.0],
        'Occupied Comfortable Hours_No Applicability_Z1': [10.0, 9.0, 5.0, 0.0],
        'Occupied Hours_Z2': [10.0, 10.0, 0.0, 0.0],
        'Occupied Comfortable Hours_No Applicability_Z2': [8.0, 10.0, 0.0, 0.0],
    })


@pytest.mark.parametrize('zones, kept', [
    ('building', ['a', 'b']),
    ('all', ['b']),
    (['z1'], ['a', 'b']),
    (['Z2'], ['b']),
])
def test_filter_the_simulations(results, zones, kept):
    filtered = filter_by_hours_within_setpoints(results, min_percentage=90, zones=zones)

    assert list(filtered['case']) == kept


def test_filter_by_zone_keeps_zones_without_occupied_hours_in_all(results):
    # In 'c', Z2 has no occupied hours: with 'all', only Z1 (50 %) counts
    assert list(filter_by_hours_within_setpoints(results, 50, zones='all')['case']) == ['a', 'b', 'c']
    # A zone of the list without occupied hours does not reach the percentage
    assert list(filter_by_hours_within_setpoints(results, 0, zones=['Z2'])['case']) == ['a', 'b']


@pytest.mark.parametrize('kwargs, message', [
    (dict(min_percentage=101), 'from 0 to 100'),
    (dict(min_percentage='90'), 'from 0 to 100'),
    (dict(min_percentage=90, zones='each'), "must be 'building', 'all' or a list"),
    (dict(min_percentage=90, zones=[]), 'not an empty list'),
    (dict(min_percentage=90, zones=['Z3']), r"The zones \['Z3'\] have no percentage"),
])
def test_wrong_arguments_of_the_filter(results, kwargs, message):
    with pytest.raises(ValueError, match=message):
        filter_by_hours_within_setpoints(results, **kwargs)


def test_filter_the_csv_files(tmp_path):
    good = _csv(tmp_path / 'Model[A.csv', {'Z1': ([1.0, 1.0], [1.0, 1.0])})
    _csv(tmp_path / 'Model[B.csv', {'Z1': ([1.0, 1.0], [1.0, 0.0])})

    kept = filter_by_hours_within_setpoints(tmp_path, min_percentage=75)

    assert [p.replace('\\', '/').split('/')[-1] for p in kept['Source']] == [good.replace('\\', '/').split('/')[-1]]
