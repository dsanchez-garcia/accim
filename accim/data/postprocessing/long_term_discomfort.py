# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Indicators of the long-term thermal discomfort of the occupied hours (proposal D1).

The methods of CEN/TR 16798-2:2019, Annex D, for the long-term evaluation of the general thermal comfort conditions
from measured or simulated data, and the acceptable deviations of its Annex E:

- Method A, percentage outside the range (:func:`hours_outside_range`): the number or percentage of occupied hours
  with the operative temperature (or the PMV) outside a specified range.
- Method B, degree hours (:func:`degree_hours`): the weighting factor is 0 within the range,
  Θo,limit,lower ≤ Θo ≤ Θo,limit,upper, and wf = abs(Θo − Θo,limit) outside it; the sum of wf times the time, in hours
  (degree hours), separately for the warm period (Θo > Θo,limit,upper) and the cold period (Θo < Θo,limit,lower).
- Method C, PPD weighted (:func:`ppd_weighted_hours`): the weighting factor is 0 within the range,
  PMVlimit,lower ≤ PMV < PMVlimit,upper, and wf = PPD(PMV)/PPD(PMVlimit) outside it, with the PPD of ISO 7730:2025,
  formula (5) (:func:`ppd_from_pmv`); the sum of wf times the time, for the warm period (PMV > PMVlimit,upper) and the
  cold period (PMV < PMVlimit,lower). A PMV equal to the upper limit, which Annex D leaves in neither case, is taken as
  within the range (as in Method B).
- Annex E, Table E.1 (:func:`deviation_check`, :func:`deviation_limit`): the acceptable deviations, as percentages of
  the occupied hours of a week (20 % or 50 %), a month (12 % or 25 %) or a year (3 % or 6 %); "it is allowed on the
  6 % level to have temperatures above the criteria for 126 h during a year but not more than 20 h during a working
  week and 44 h during a working month".

ISO 7730:2025 has left out its sections on the long-term evaluation, so the reference of these indicators is
CEN/TR 16798-2. :func:`hours_below` gives the occupied hours below some temperatures, as the outputs
``HoursBelow_<T>_<zone>`` of the ACCIS (``report_hours_below`` of :class:`accim.sim.accis.AddAccis`). The ACCIS also
counts those of Methods A and B in the simulations, with the setpoints without the tolerance as the limits
(``report_long_term_discomfort`` of :class:`accim.sim.accis.AddAccis`, :mod:`accim.sim.ems.long_term_discomfort`), so
that the parametric and optimisation module can read them as objectives and constraints
(:mod:`accim.parametric_and_optimisation.objectives`).

The functions take pandas Series (or arrays) of the same length, one value per row (a timestep or an hour), and the
occupancy: ``occupied`` (None: all the rows are occupied; or a Series of booleans, or of numbers such as the
occupants, occupied if they are greater than 0) and ``timestep_h``, the hours of each row (a number, or a Series,
such as the occupied hours of each row of the hourly outputs of the ACCIS). The rows whose values are missing (NaN)
are left out. :func:`table_indicators` gives them for the zones of a :class:`accim.data.postprocessing.main.Table`
(``Table(long_term_indicators=True)``).
"""

from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

__all__ = [
    'DEVIATION_LIMITS',
    'degree_hours',
    'deviation_check',
    'deviation_limit',
    'hours_below',
    'hours_outside_range',
    'ppd_from_pmv',
    'ppd_weighted_hours',
    'table_indicators',
]

#: The acceptable deviations of CEN/TR 16798-2:2019, Annex E, Table E.1, as percentages of the occupied hours of each
#: period: the level is named after its yearly percentage ('3%': 20 % of a week, 12 % of a month, 3 % of a year;
#: '6%': 50 %, 25 % and 6 %).
DEVIATION_LIMITS = {
    '3%': {'weekly': 20.0, 'monthly': 12.0, 'yearly': 3.0},
    '6%': {'weekly': 50.0, 'monthly': 25.0, 'yearly': 6.0},
}

Values = Union[pd.Series, np.ndarray, Sequence[float], float]


def ppd_from_pmv(pmv: Values) -> Union[np.ndarray, float]:
    """The predicted percentage of dissatisfied (%) of a PMV: PPD = 100 − 95·exp(−0.03353·PMV⁴ − 0.2179·PMV²)
    (ISO 7730:2025, clause 5, formula (5)); the dissatisfied are those who vote hot, warm, cool or cold on the
    seven-point thermal sensation scale.

    :param pmv: A PMV, or an array or Series of them.
    :return: The PPD (a number for a number, and an array otherwise).
    """
    values = np.asarray(pmv, dtype=float)
    ppd = 100.0 - 95.0 * np.exp(-0.03353 * values ** 4 - 0.2179 * values ** 2)
    return float(ppd) if np.ndim(ppd) == 0 else ppd


def _frame(values: Dict[str, Values], occupied: Any, timestep_h: Any) -> pd.DataFrame:
    """The rows with all the values, their occupancy and their hours (the occupied hours of each row)."""
    length = next((len(v) for v in values.values() if np.ndim(v) > 0), None)
    if length is None:
        raise ValueError('Give the values of the rows as pandas Series or arrays.')
    data = {}
    for name, value in values.items():
        data[name] = (np.full(length, float(value)) if np.ndim(value) == 0
                      else np.asarray(value, dtype=float).reshape(-1))
        if len(data[name]) != length:
            raise ValueError(f'{name} has {len(data[name])} values, not {length}.')
    hours = np.full(length, float(timestep_h)) if np.ndim(timestep_h) == 0 else np.asarray(timestep_h, dtype=float)
    if occupied is None:
        occupancy = np.ones(length, dtype=bool)
    else:
        occupancy = np.asarray(occupied)
        occupancy = occupancy.astype(bool) if occupancy.dtype == bool else np.nan_to_num(
            occupancy.astype(float)) > 0
    if len(hours) != length or len(occupancy) != length:
        raise ValueError(f'occupied and timestep_h must have {length} values, as the other Series.')
    frame = pd.DataFrame(data)
    frame['hours'] = np.where(occupancy, np.nan_to_num(hours), 0.0)
    return frame.dropna()


def hours_outside_range(top: Values, lower: Values, upper: Values, occupied: Any = None,
                        timestep_h: Any = 1.0) -> Dict[str, float]:
    """Method A of CEN/TR 16798-2:2019, Annex D: the occupied hours with the operative temperature (or the PMV) above
    the upper limit and below the lower limit of a range, and their percentage of the occupied hours.

    :param top: The operative temperature (or the PMV) of each row.
    :param lower: The lower limit of the range (a number, or one for each row, such as the heating setpoint without
        the tolerance of the ACCIS, ``AHSTnoTol``).
    :param upper: The upper limit of the range (``ACSTnoTol``).
    :param occupied: The occupancy of each row (see the module); None: all the rows.
    :param timestep_h: The hours of each row (a number, or a Series).
    :return: ``{'hot_h', 'cold_h', 'hot_pct', 'cold_pct', 'occupied_h'}``: the occupied hours above the upper limit
        (the warm period) and below the lower limit (the cold period), their percentages of the occupied hours, and
        the occupied hours (the percentages are NaN without occupied hours).
    """
    rows = _frame({'top': top, 'lower': lower, 'upper': upper}, occupied, timestep_h)
    occupied_h = float(rows['hours'].sum())
    hot = float(rows.loc[rows['top'] > rows['upper'], 'hours'].sum())
    cold = float(rows.loc[rows['top'] < rows['lower'], 'hours'].sum())

    def percentage(hours: float) -> float:
        return 100.0 * hours / occupied_h if occupied_h > 0 else float('nan')

    return {'hot_h': hot, 'cold_h': cold, 'hot_pct': percentage(hot), 'cold_pct': percentage(cold),
            'occupied_h': occupied_h}


def degree_hours(top: Values, lower: Values, upper: Values, occupied: Any = None,
                 timestep_h: Any = 1.0) -> Dict[str, float]:
    """Method B of CEN/TR 16798-2:2019, Annex D: the degree hours of the occupied hours, the sums of the weighting
    factor wf = abs(Θo − Θo,limit) times the time, for the warm period (Θo > Θo,limit,upper) and the cold period
    (Θo < Θo,limit,lower); wf is 0 within the range (Θo,limit,lower ≤ Θo ≤ Θo,limit,upper).

    :param top: The operative temperature of each row (°C).
    :param lower: The lower limit of the range (°C; a number or one for each row).
    :param upper: The upper limit of the range (°C).
    :param occupied: The occupancy of each row (see the module); None: all the rows.
    :param timestep_h: The hours of each row (a number, or a Series).
    :return: ``{'hot_Kh', 'cold_Kh'}``, in degree hours (K·h).
    """
    rows = _frame({'top': top, 'lower': lower, 'upper': upper}, occupied, timestep_h)
    hot = (rows['top'] - rows['upper']).clip(lower=0) * rows['hours']
    cold = (rows['lower'] - rows['top']).clip(lower=0) * rows['hours']
    return {'hot_Kh': float(hot.sum()), 'cold_Kh': float(cold.sum())}


def ppd_weighted_hours(pmv: Values, pmv_lower: Values, pmv_upper: Values, occupied: Any = None,
                       timestep_h: Any = 1.0) -> Dict[str, float]:
    """Method C of CEN/TR 16798-2:2019, Annex D: the PPD-weighted hours of the occupied hours, the sums of the
    weighting factor wf = PPD(PMV)/PPD(PMVlimit) times the time, for the warm period (PMV > PMVlimit,upper, with the
    upper limit) and the cold period (PMV < PMVlimit,lower, with the lower limit); wf is 0 within the range
    (PMVlimit,lower ≤ PMV ≤ PMVlimit,upper). The PPD is that of ISO 7730:2025, formula (5) (:func:`ppd_from_pmv`).

    :param pmv: The PMV of each row.
    :param pmv_lower: The lower limit of the PMV (a number, such as −0.5 for category II of EN 16798-1, Table B.1, or
        one for each row).
    :param pmv_upper: The upper limit of the PMV.
    :param occupied: The occupancy of each row (see the module); None: all the rows.
    :param timestep_h: The hours of each row (a number, or a Series).
    :return: ``{'hot_h', 'cold_h'}``, in weighted hours.
    """
    rows = _frame({'pmv': pmv, 'lower': pmv_lower, 'upper': pmv_upper}, occupied, timestep_h)
    ppd = ppd_from_pmv(rows['pmv'].to_numpy())
    hot = rows['pmv'] > rows['upper']
    cold = rows['pmv'] < rows['lower']
    hot_h = (ppd[hot.to_numpy()] / ppd_from_pmv(rows.loc[hot, 'upper'].to_numpy())) * rows.loc[hot, 'hours']
    cold_h = (ppd[cold.to_numpy()] / ppd_from_pmv(rows.loc[cold, 'lower'].to_numpy())) * rows.loc[cold, 'hours']
    return {'hot_h': float(hot_h.sum()), 'cold_h': float(cold_h.sum())}


def deviation_limit(occupied_hours: float, period: str = 'yearly', level: str = '6%') -> float:
    """The largest number of occupied hours outside the range within the acceptable deviation of CEN/TR 16798-2:2019,
    Annex E, Table E.1, for a period: 20 % (or 50 %) of the occupied hours of a week, 12 % (25 %) of a month, or 3 %
    (6 %) of a year (:data:`DEVIATION_LIMITS`).

    :param occupied_hours: The occupied hours of the period.
    :param period: 'weekly', 'monthly' or 'yearly'.
    :param level: The level of Table E.1, named after its yearly percentage: '3%' (20 %, 12 % and 3 %) or '6%'
        (50 %, 25 % and 6 %).
    :return: The hours (the percentage of the period times its occupied hours).
    :raises ValueError: If the period or the level is not one of Table E.1.
    """
    if level not in DEVIATION_LIMITS:
        raise ValueError(f'level must be one of {list(DEVIATION_LIMITS)} (the yearly percentages of Table E.1 of '
                         f'CEN/TR 16798-2), not {level!r}.')
    if period not in DEVIATION_LIMITS[level]:
        raise ValueError(f'period must be one of {list(DEVIATION_LIMITS[level])}, not {period!r}.')
    return DEVIATION_LIMITS[level][period] / 100.0 * float(occupied_hours)


def deviation_check(hours_outside: float, occupied_hours: float, period: str = 'yearly', level: str = '6%') -> bool:
    """Whether the hours outside the range are within the acceptable deviation of CEN/TR 16798-2:2019, Annex E,
    Table E.1, for a period: at most 20 % (or 50 %) of the occupied hours of a week, 12 % (25 %) of a month, or
    3 % (6 %) of a year (:data:`DEVIATION_LIMITS`, :func:`deviation_limit`).

    :param hours_outside: The occupied hours outside the range in the period (for instance, those above the upper
        limit, ``hot_h`` of :func:`hours_outside_range`).
    :param occupied_hours: The occupied hours of the period.
    :param period: 'weekly', 'monthly' or 'yearly'.
    :param level: The level of Table E.1, named after its yearly percentage: '3%' (20 %, 12 % and 3 %) or '6%'
        (50 %, 25 % and 6 %).
    :return: True if the hours outside are not more than the percentage of the occupied hours.
    :raises ValueError: If the period or the level is not one of Table E.1.
    """
    return float(hours_outside) <= deviation_limit(occupied_hours, period, level)


def hours_below(temp: Values, thresholds: Iterable[float] = (18, 17, 16), occupied: Any = None,
                timestep_h: Any = 1.0) -> Dict[float, float]:
    """The occupied hours with the temperature below each of some temperatures (as the outputs
    ``HoursBelow_<T>_<zone>`` of the ACCIS, ``report_hours_below`` of :class:`accim.sim.accis.AddAccis`).

    :param temp: The temperature of each row (°C), such as the operative temperature.
    :param thresholds: The temperatures (°C).
    :param occupied: The occupancy of each row (see the module); None: all the rows.
    :param timestep_h: The hours of each row (a number, or a Series).
    :return: ``{temperature: hours}``.
    """
    rows = _frame({'temp': temp}, occupied, timestep_h)
    return {threshold: float(rows.loc[rows['temp'] < float(threshold), 'hours'].sum()) for threshold in thresholds}


# Table ------------------------------------------------------------------------------------------------------------

#: The outputs of each zone with which Table(long_term_indicators=True) calculates the indicators: the upper and lower
#: limits (the setpoints without the tolerance of the ACCIS) and the occupied hours of each row (EMS outputs of the
#: zones, 'EMS:<output>_<zone> [unit](frequency)' in the columns of Table), and the operative temperature
_UPPER_LIMIT = 'EMS:ADAPTIVE COOLING SETPOINT TEMPERATURE_NO TOLERANCE_'
_LOWER_LIMIT = 'EMS:ADAPTIVE HEATING SETPOINT TEMPERATURE_NO TOLERANCE_'
_OCCUPIED_HOURS = 'EMS:OCCUPIED HOURS_'
_OPERATIVE_TEMPERATURE = 'ZONE OPERATIVE TEMPERATURE'
#: The columns of the indicators of each zone (and of the building), with the key of the results of the functions
TABLE_INDICATORS = {
    'Occupied Hours (h)': 'occupied_h',
    'Hours Above Upper Limit (h)': 'hot_h',
    'Hours Below Lower Limit (h)': 'cold_h',
    'Hours Above Upper Limit (%)': 'hot_pct',
    'Hours Below Lower Limit (%)': 'cold_pct',
    'Degree Hours Above Upper Limit (Kh)': 'hot_Kh',
    'Degree Hours Below Lower Limit (Kh)': 'cold_Kh',
}
#: The columns of the simulations of Table that describe them
_DESCRIPTIVE_COLUMNS = ('Model', 'ComfStand', 'CAT', 'ComfMod', 'HVACmode', 'VentCtrl', 'VSToffset', 'MinOToffset',
                        'MaxWindSpeed', 'ASTtol', 'NameSuffix', 'EPW')


def _zone_column(columns: Sequence[str], zone: str, prefix: Optional[str] = None) -> Optional[str]:
    """The column of an output of a zone: the EMS output 'EMS:<output>_<zone> [unit](frequency)' (``prefix``), or the
    operative temperature, '<zone>_Zone Operative Temperature (°C)' with rename_cols, or '<zone>:Zone Operative
    Temperature [C](<frequency>)' (the names of the columns of Table)."""
    zone_upper = zone.upper()
    for column in columns:
        name = str(column).upper()
        if prefix is not None:
            if name.startswith(prefix + zone_upper + ' ['):
                return column
        elif name in (f'{zone_upper}_{_OPERATIVE_TEMPERATURE} (°C)', ) or (
                name.startswith(f'{zone_upper}:{_OPERATIVE_TEMPERATURE} [')):
            return column
    return None


def table_indicators(df: pd.DataFrame, zones: Sequence[str]) -> pd.DataFrame:
    """The indicators of Methods A and B of CEN/TR 16798-2:2019, Annex D, of each simulation of a table of
    :class:`accim.data.postprocessing.main.Table` with timestep or hourly rows, for each occupied zone and for the
    building: the occupied hours, the hours above the upper limit and below the lower limit and their percentages of
    the occupied hours (:func:`hours_outside_range`), and the degree hours above and below (:func:`degree_hours`), with
    the setpoints without the tolerance of the ACCIS as the limits (the outputs ``Adaptive Cooling Setpoint
    Temperature_No Tolerance_<zone>`` and ``Adaptive Heating Setpoint Temperature_No Tolerance_<zone>``), the operative
    temperature of the zone, and the occupied hours of each row (the output ``Occupied Hours_<zone>`` of the ACCIS) as
    the time. The building adds up the hours of its zones. With hourly rows (and timestep outputs aggregated by Table),
    the operative temperature and the limits are the means of each hour.

    :param df: The table (``Table.df``), with the column ``Source`` (the CSV file of each simulation).
    :param zones: The occupied zones (``Table.occupied_zone_list``).
    :return: A DataFrame with a row for each simulation: ``Source``, the columns that describe the simulations
        (``Model``, ``ComfStand``... ``EPW``, those that the table has), and ``<zone>_<indicator>`` and
        ``Building_<indicator>`` for each indicator of :data:`TABLE_INDICATORS`.
    :raises ValueError: If a zone does not have the outputs that the indicators need.
    """
    columns = list(df.columns)
    found: Dict[str, Dict[str, str]] = {}
    missing: List[str] = []
    for zone in zones:
        zone_columns = {'top': _zone_column(columns, zone), 'upper': _zone_column(columns, zone, _UPPER_LIMIT),
                        'lower': _zone_column(columns, zone, _LOWER_LIMIT),
                        'hours': _zone_column(columns, zone, _OCCUPIED_HOURS)}
        absent = [name for name, column in zone_columns.items() if column is None]
        if absent:
            missing.append(f"{zone} ({', '.join(absent)})")
        found[zone] = zone_columns
    if missing:
        raise ValueError('long_term_indicators needs the operative temperature, the setpoints without the tolerance '
                         'and the occupied hours of each occupied zone (the standard outputs of AddAccis), which '
                         'these zones do not have: ' + '; '.join(missing) + '.')
    descriptive = [column for column in _DESCRIPTIVE_COLUMNS if column in df.columns]
    rows = []
    for source, group in df.groupby('Source', sort=False):
        row: Dict[str, Any] = {'Source': source}
        row.update({column: group[column].iloc[0] for column in descriptive})
        totals = dict.fromkeys(('occupied_h', 'hot_h', 'cold_h', 'hot_Kh', 'cold_Kh'), 0.0)
        for zone, zone_columns in found.items():
            hours = pd.to_numeric(group[zone_columns['hours']], errors='coerce').fillna(0.0)
            values = [pd.to_numeric(group[zone_columns[name]], errors='coerce') for name in ('top', 'lower', 'upper')]
            results = hours_outside_range(*values, occupied=hours, timestep_h=hours)
            results.update(degree_hours(*values, occupied=hours, timestep_h=hours))
            for title, key in TABLE_INDICATORS.items():
                row[f'{zone}_{title}'] = results[key]
            for key in totals:
                totals[key] += results[key]
        occupied = totals['occupied_h']
        totals['hot_pct'] = 100.0 * totals['hot_h'] / occupied if occupied > 0 else float('nan')
        totals['cold_pct'] = 100.0 * totals['cold_h'] / occupied if occupied > 0 else float('nan')
        for title, key in TABLE_INDICATORS.items():
            row[f'Building_{title}'] = totals[key]
        rows.append(row)
    return pd.DataFrame(rows)
