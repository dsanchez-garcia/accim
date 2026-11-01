# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The occupied hours within the setpoints of the ACCIS, as a percentage, to measure them and filter simulations.

The ACCIS counts, for each occupied zone, the occupied hours (the EMS output ``Occupied Hours_<zone>``) and the
occupied hours in which the operative temperature is within the setpoints without tolerance, that is, within the
comfort limits of the comfort model (``Occupied Comfortable Hours_No Applicability_<zone>``). The percentage of a
zone is the ratio of their sums; that of the building, the ratio of their sums over all the zones (the occupied
hours of each zone weigh the same).

:func:`hours_within_setpoints` gives these percentages for the CSV files of the simulations (one row for each
file), or for a table with one row for each simulation and the sums of these outputs (the results of the parametric
module, for instance); :func:`filter_by_hours_within_setpoints` keeps the simulations whose percentage reaches a
minimum.
"""

import os
import re
import warnings
from typing import Iterable, List, Optional, Union

import numpy as np
import pandas as pd

__all__ = [
    'BUILDING',
    'OCCUPIED_HOURS',
    'PERCENTAGE',
    'WITHIN_SETPOINTS',
    'filter_by_hours_within_setpoints',
    'hours_within_setpoints',
    'percentage_column',
]

#: The EMS output of the occupied hours of each zone (``Occupied Hours_<zone>``).
OCCUPIED_HOURS = 'Occupied Hours'
#: The EMS output of the occupied hours within the setpoints without tolerance of each zone.
WITHIN_SETPOINTS = 'Occupied Comfortable Hours_No Applicability'
#: The name of the columns of the percentages (``Occupied Hours Within Setpoints_<zone> [%]``).
PERCENTAGE = 'Occupied Hours Within Setpoints'
#: The name of the building in the column of its percentage.
BUILDING = 'Building'

_FREQUENCIES = ('timestep', 'hourly', 'daily', 'monthly', 'runperiod', 'annual', 'detailed', 'each call')
# The frequency whose columns are summed when a CSV file has the outputs at several frequencies (they add up to the
# same hours)
_FREQUENCY_ORDER = ('runperiod', 'annual', 'monthly', 'daily', 'hourly', 'timestep', 'detailed', 'each call', '')
# The building averages of make_averages, which are not zones
_NOT_ZONES = ('BUILDING_AVERAGE',)
# The CSV files of EnergyPlus and of Table that have no outputs of the zones
_AUXILIARY_CSV = ('Meter.csv', 'Table.csv', 'Zsz.csv', 'Ssz.csv', 'Map.csv', 'Screen.csv', 'CSVconcatenated.csv',
                  'Rows_not_corr_agg.csv', 'Rows_with_NaNs.csv')

PathLike = Union[str, os.PathLike]


def percentage_column(zone: str) -> str:
    """The name of the column of the percentage of a zone, or of the building (``zone=BUILDING``)."""
    return f'{PERCENTAGE}_{zone} [%]'


def _parse(column) -> tuple:
    """The name, units and frequency of a column: 'EMS:Occupied Hours_ZONE1 [H](Hourly)' -> ('Occupied
    Hours_ZONE1', 'H', 'hourly'). Columns without units or frequency (those of the readers of the parametric
    module) give None and ''."""
    text = str(column).strip()
    frequency = ''
    match = re.search(r'\(([^()]*)\)$', text)
    if match and match.group(1).strip().lower() in _FREQUENCIES:
        frequency = match.group(1).strip().lower()
        text = text[:match.start()].rstrip()
    units = None
    match = re.search(r'\[([^\[\]]*)\]$', text)
    if match:
        units = match.group(1).strip()
        text = text[:match.start()].rstrip()
    if text.upper().startswith('EMS:'):
        text = text[4:]
    return text, units, frequency


def _counter(column) -> Optional[tuple]:
    """(output, zone, frequency) if the column is one of the two counters of a zone, else None."""
    name, units, frequency = _parse(column)
    if units is not None and units.upper() != 'H':
        return None
    for output in (WITHIN_SETPOINTS, OCCUPIED_HOURS):
        prefix = f'{output}_'
        if name.upper().startswith(prefix.upper()):
            zone = name[len(prefix):]
            if zone and zone.upper() not in _NOT_ZONES:
                return output, zone, frequency
    return None


def _total(value) -> float:
    """The sum of a value of a table: a number, or the list of values of a time series (return_time_series)."""
    if isinstance(value, (list, tuple, np.ndarray, pd.Series)):
        values = pd.to_numeric(pd.Series(list(value), dtype=object), errors='coerce')
        return float(values.sum()) if values.notna().any() else np.nan
    number = pd.to_numeric(pd.Series([value], dtype=object), errors='coerce').iloc[0]
    return float(number)


def _counter_columns(columns) -> dict:
    """The columns to sum for each zone: {ZONE: (zone, {output: column})}, at one frequency for each zone."""
    found = {}
    for column in columns:
        counter = _counter(column)
        if counter is None:
            continue
        output, zone, frequency = counter
        found.setdefault(zone.upper(), (zone, {}))[1].setdefault(frequency, {}).setdefault(output, column)
    zones = {}
    for key, (zone, by_frequency) in found.items():
        for frequency in _FREQUENCY_ORDER:
            outputs = by_frequency.get(frequency, {})
            if len(outputs) == 2:
                zones[key] = (zone, outputs)
                break
    return zones


def _add_percentages(df: pd.DataFrame, zones: dict) -> pd.DataFrame:
    """Add the percentage of each zone and of the building to a table whose rows are simulations."""
    occupied = pd.DataFrame(index=df.index)
    within = pd.DataFrame(index=df.index)
    percentages = {}
    for key, (zone, outputs) in zones.items():
        occupied[key] = [_total(v) for v in df[outputs[OCCUPIED_HOURS]]]
        within[key] = [_total(v) for v in df[outputs[WITHIN_SETPOINTS]]]
        percentages[percentage_column(zone)] = (100 * within[key] / occupied[key]).where(occupied[key] > 0)
    total_occupied = occupied.sum(axis=1, min_count=1)
    percentages[percentage_column(BUILDING)] = (100 * within.sum(axis=1, min_count=1) / total_occupied).where(
        total_occupied > 0)
    result = df.copy()
    for column, values in percentages.items():
        result[column] = values
    return result


def _csv_files(results) -> tuple:
    """The CSV files to read (from files and folders), and those given explicitly."""
    items = [results] if isinstance(results, (str, os.PathLike)) else list(results)
    files, explicit = [], set()
    for item in items:
        path = os.fspath(item)
        if os.path.isdir(path):
            # The names of the CSV files of run_ep have '[', which glob would take for a pattern
            files += sorted(os.path.normpath(os.path.join(path, name)) for name in os.listdir(path)
                            if name.lower().endswith('.csv') and not any(name.endswith(a) for a in _AUXILIARY_CSV))
        elif os.path.isfile(path):
            files.append(path)
            explicit.add(path)
        else:
            raise FileNotFoundError(f'{path} is neither a CSV file nor a folder.')
    return list(dict.fromkeys(files)), explicit


def _summary_of_csv_files(files: List[str], explicit: set) -> pd.DataFrame:
    """One row for each CSV file that has the counters: the file, and the sums of the counters of each zone."""
    rows, skipped = [], []
    for file in files:
        columns = pd.read_csv(file, nrows=0).columns
        zones = _counter_columns(columns)
        if not zones:
            skipped.append(file)
            continue
        wanted = {column for _, outputs in zones.values() for column in outputs.values()}
        data = pd.read_csv(file, usecols=lambda c: c in wanted)
        row = {'Source': file}
        for zone, outputs in zones.values():
            for output in (OCCUPIED_HOURS, WITHIN_SETPOINTS):
                row[f'{output}_{zone}'] = float(pd.to_numeric(data[outputs[output]], errors='coerce').sum())
        rows.append(row)
    if not rows:
        raise ValueError(
            f'None of the {len(files)} CSV files has the EMS outputs "{OCCUPIED_HOURS}_<zone>" and '
            f'"{WITHIN_SETPOINTS}_<zone>" of the ACCIS: the models need them as Output:Variable objects '
            f"(output_type 'standard', 'detailed' or 'custom' of AddAccis).")
    skipped_explicit = [f for f in skipped if f in explicit]
    if skipped_explicit:
        warnings.warn(f'These CSV files have no hours of the ACCIS and have been skipped: {skipped_explicit}',
                      UserWarning, stacklevel=3)
    return pd.DataFrame(rows)


def hours_within_setpoints(results: Union[pd.DataFrame, PathLike, Iterable[PathLike]]) -> pd.DataFrame:
    """The percentage of the occupied hours within the setpoints of each zone and of the building.

    The occupied hours within the setpoints of a zone are those in which its operative temperature is within the
    setpoints without tolerance (the comfort limits of its comfort model), as the ACCIS counts them in the EMS
    output ``Occupied Comfortable Hours_No Applicability_<zone>``; the percentage is their ratio to the occupied
    hours (``Occupied Hours_<zone>``). That of the building is the ratio of their sums over all the zones.

    :param results: The results of the simulations, either:

        - the CSV files of the simulations (a path, or a list of paths; a folder stands for its CSV files, except
          those of meters, tables and sizing): the outputs of each file are added up, whatever their frequency
          (the hourly values and the run period values give the same sums), including the sizing periods if the
          model simulates them;
        - or a table with one row for each simulation and the sums of the outputs of the zones in columns named
          after them, such as the results of the parametric module with readers of these outputs (whose columns
          are ``Occupied Hours_<zone>`` and ``Occupied Comfortable Hours_No Applicability_<zone>`` unless the
          readers have other names), or a table of :class:`~accim.data.postprocessing.main.Table` (its columns
          ``EMS:OCCUPIED HOURS_<ZONE> [H](HOURLY)``..., with the rows of the frequency of the table: the
          percentages are then those of each row, a month for instance).
    :return: For CSV files, a table with one row for each file: ``Source`` (the path of the file), the sums of the
        two outputs of each zone (``Occupied Hours_<zone>`` and ``Occupied Comfortable Hours_No
        Applicability_<zone>``) and the percentages; for a table, a copy of it with the percentages. The columns of
        the percentages are ``Occupied Hours Within Setpoints_<zone> [%]`` for each zone and ``Occupied Hours
        Within Setpoints_Building [%]`` (see :func:`percentage_column`); a zone without occupied hours has no
        percentage (NaN).
    :raises ValueError: If the results have no outputs of the hours of the zones.

    Example::

        from accim.data.postprocessing.setpoint_hours import hours_within_setpoints

        summary = hours_within_setpoints('.')    # the CSV files of the simulations of run_ep in this folder
        print(summary[['Source', 'Occupied Hours Within Setpoints_Building [%]']])
    """
    if isinstance(results, pd.DataFrame):
        zones = _counter_columns(results.columns)
        if not zones:
            raise ValueError(
                f'The table has no columns "{OCCUPIED_HOURS}_<zone>" and "{WITHIN_SETPOINTS}_<zone>" (the sums of '
                f'these EMS outputs of the ACCIS). In the parametric module, add the readers of these outputs before '
                f"running the simulations, for instance with select_outputs(variables=['{OCCUPIED_HOURS}_', "
                f"'{WITHIN_SETPOINTS}_'], match='contains').")
        return _add_percentages(results, zones)
    files, explicit = _csv_files(results)
    summary = _summary_of_csv_files(files, explicit)
    return _add_percentages(summary, _counter_columns(summary.columns))


def _zones_of(table: pd.DataFrame) -> dict:
    """The zones of the percentage columns of a table: {ZONE: column}, without the building."""
    prefix, suffix = f'{PERCENTAGE}_', ' [%]'
    zones = {}
    for column in table.columns:
        name = str(column)
        if name.startswith(prefix) and name.endswith(suffix) and name != percentage_column(BUILDING):
            zones[name[len(prefix):-len(suffix)].upper()] = column
    return zones


def filter_by_hours_within_setpoints(
        results: Union[pd.DataFrame, PathLike, Iterable[PathLike]],
        min_percentage: float,
        zones: Union[str, Iterable[str]] = 'building',
) -> pd.DataFrame:
    """Keep the simulations whose occupied hours within the setpoints reach a percentage.

    :param results: The results of the simulations, as in :func:`hours_within_setpoints`, or its table.
    :param min_percentage: The minimum percentage (0 to 100) of the occupied hours within the setpoints.
    :param zones: Where the percentage must be reached: ``'building'`` (the default), the percentage of the whole
        building; ``'all'``, that of every zone with occupied hours (and the building must have some); or a list of
        zones (the names in the columns of the percentages, in any case), each of which must reach it (a zone of the
        list without occupied hours does not).
    :return: The rows of the table of :func:`hours_within_setpoints` that reach the percentage. For CSV files,
        ``Source`` lists the files, which can be given to :class:`~accim.data.postprocessing.main.Table` as
        ``datasets``.
    :raises ValueError: If ``min_percentage`` is not a number from 0 to 100, ``zones`` is not valid or a zone of
        the list has no percentage.

    Example::

        from accim.data.postprocessing.main import Table
        from accim.data.postprocessing.setpoint_hours import filter_by_hours_within_setpoints

        kept = filter_by_hours_within_setpoints('.', min_percentage=90)
        table = Table(datasets=list(kept['Source']), source_frequency='hourly', frequency='runperiod', ...)
    """
    if isinstance(min_percentage, bool) or not isinstance(min_percentage, (int, float, np.number)) \
            or not 0 <= min_percentage <= 100:
        raise ValueError(f'min_percentage must be a number from 0 to 100, not {min_percentage!r}.')
    table = hours_within_setpoints(results)
    building = table[percentage_column(BUILDING)]
    zone_columns = _zones_of(table)
    if isinstance(zones, str):
        if zones.lower() == 'building':
            keep = building >= min_percentage
        elif zones.lower() == 'all':
            keep = building.notna()
            for column in zone_columns.values():
                keep &= table[column].isna() | (table[column] >= min_percentage)
        else:
            raise ValueError(f"zones must be 'building', 'all' or a list of zones, not {zones!r}.")
    else:
        zones = list(zones)
        if not zones:
            raise ValueError("zones must be 'building', 'all' or a list of zones, not an empty list.")
        missing = [zone for zone in zones if str(zone).upper() not in zone_columns]
        if missing:
            raise ValueError(f'The zones {missing} have no percentage; the zones are '
                             f'{sorted(c[len(PERCENTAGE) + 1:-4] for c in zone_columns.values())}.')
        keep = pd.Series(True, index=table.index)
        for zone in zones:
            keep &= table[zone_columns[str(zone).upper()]] >= min_percentage
    return table.loc[keep.fillna(False).astype(bool)].copy()
