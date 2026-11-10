# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Indicators of the adaptation of the occupants to the indoor climate (task F3 of block F of accim 1.2.0,
``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, section 4, F3), from the rows of each timestep or hour of the
simulations, for the comparison of the setpoints of several comfort models in the same terms:

- The causal SET band of Sun, Brager & Schiavon (2026), Energy and Buildings 370, 118097, Fig. 7a: TSV = 0.11·SET −
  2.6, whose band of TSV ±0.5 is 19.1 to 28.2 °C of SET (comfort standard 24, :mod:`accim.sim.comfort_hooks`):
  :func:`causal_band_hours`, the occupied hours with the SET within the band, above it and below it. The SET is that
  of the Pierce two-node model of EnergyPlus (Engineering Reference 25.2, 19.1.4), which any model reports with
  :func:`accim.sim.people.add_thermal_comfort_outputs`, so the setpoints of every comfort model are measured with the
  same SET (that of the hook of comfort standard 24, ``SET_<zone>``, is that of pythermalcomfort; their differences
  are in ``notes/decisions.md``, task E-F1).
- The overcooling (:func:`overcooling_hours`): the occupied hours of the cooling season with the operative temperature
  below a temperature, 22 °C by default, following Parkinson, Schiavon, de Dear & Brager (2021), *Overcooling of
  offices...*, Scientific Reports 11, as the proposal of block F does (a design decision of the proposal), or below
  the reference heating setpoint that is given instead. The cooling season is that of the ACCIS (from
  ``cooling_season_start`` to the day before ``cooling_season_end``, 121 and 274 by default, as in
  :class:`accim.sim.accis.AddAccis`).
- The neutrality by exposure (:func:`exposure_neutral_temperature`, :func:`indoor_running_mean`,
  :func:`exposure_hours`): Parkinson, de Dear & Brager (2020), Energy and Buildings 206, 109559, Fig. 6, found the
  neutral temperature of the occupants of a building close to its mean indoor temperature: Tn = 1.06 + 0.951·Tin
  (air-conditioned buildings, AC), 2.91 + 0.879·Tin (mixed mode, MM) and 2.23 + 0.897·Tin (naturally ventilated, NV),
  with Tin the mean indoor air temperature of each building during its campaign. The proposal of block F applies it to
  the exponentially weighted daily running mean of the operative temperature of the occupied hours of each zone,
  T_rm_in (the state of the limiter of the drift of the setpoints, task F2, :mod:`accim.sim.ems.drift_limiter`):
  Tn_exp = 1.06 + 0.951·T_rm_in, only as a diagnostic, never as a setpoint, since it refers to itself (the setpoints
  set the exposure, and the exposure the neutrality); and the occupied hours with abs(To − Tn_exp) > 2.5 K as a
  measure of the "expected" discomfort, a threshold that the proposal infers (it is not of the paper).
- The cooling effect of the elevated air speed of ASHRAE 55-2017 that EnergyPlus calculates (Engineering Reference
  25.2, 19.1.9; the model CoolingEffectASH55 of :func:`accim.sim.people.add_thermal_comfort_outputs`), as an
  indicator, not as a setpoint (decision of the review of accim 1.2.0 on A6, ``notes/decisions.md``).

As in :mod:`accim.data.postprocessing.long_term_discomfort`, the functions take pandas Series (or arrays) of the same
length, one value per row, and the occupancy: ``occupied`` (None: all the rows are occupied; or a Series of booleans,
or of numbers, occupied if they are greater than 0) and ``timestep_h``, the hours of each row (a number, or a Series,
such as the occupied hours of each row of the outputs of the ACCIS); the rows whose values are missing (NaN) are left
out. :func:`table_indicators` gives them for the zones and the building of each simulation of a
:class:`accim.data.postprocessing.main.Table` (``Table(indoor_adaptation_indicators=True)``), which also names the
outputs of EnergyPlus of these models (:data:`ENERGYPLUS_OUTPUTS`).
"""

import warnings
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from accim.data.postprocessing.long_term_discomfort import _DESCRIPTIVE_COLUMNS, _frame, _zone_column

__all__ = [
    'ENERGYPLUS_OUTPUTS',
    'EXPOSURE_DIFFERENCE',
    'EXPOSURE_NEUTRAL_TEMPERATURE',
    'OVERCOOLING_TEMPERATURE',
    'TABLE_INDICATORS',
    'causal_band_hours',
    'exposure_hours',
    'exposure_neutral_temperature',
    'indoor_running_mean',
    'overcooling_hours',
    'table_indicators',
]

#: The outputs of EnergyPlus of the thermal comfort models of :func:`accim.sim.people.add_thermal_comfort_outputs`
#: (Input Output Reference 25.2, 1.14.2.2) that Table keeps with ``standard_outputs=True``, averages over time and,
#: with ``rename_cols=True``, names ``<zone>_<name>``, so that no name contains another one (``SET (°C)`` is the SET
#: of the hook of the SET, and ``PMV`` and ``PPD (%)`` those of the Fanger model)
ENERGYPLUS_OUTPUTS = {
    'Zone Thermal Comfort Pierce Model Standard Effective Temperature': 'SET_Pierce (°C)',
    'Zone Thermal Comfort Pierce Model Standard Effective Temperature PMV': 'SET_Pierce_PMV',
    'Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect': 'CoolingEffect (°C)',
    'Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect Adjusted PMV': 'CoolingEffect_PMV',
    'Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect Adjusted PPD': 'CoolingEffect_PPD',
}
#: Parkinson, de Dear & Brager (2020), Energy and Buildings 206, 109559, Fig. 6: the neutral temperature against the
#: mean indoor temperature of the building, Tn = intercept + slope·Tin, of the air-conditioned (AC), mixed-mode (MM)
#: and naturally ventilated (NV) buildings: (intercept in °C, slope)
EXPOSURE_NEUTRAL_TEMPERATURE = {'AC': (1.06, 0.951), 'MM': (2.91, 0.879), 'NV': (2.23, 0.897)}
#: The operative temperature below which an occupied hour of the cooling season is overcooled, by default (°C;
#: Parkinson, Schiavon, de Dear & Brager, 2021, as the proposal of block F cites them)
OVERCOOLING_TEMPERATURE = 22.0
#: The difference between the operative temperature and Tn_exp beyond which the proposal of block F counts the
#: "expected" discomfort (K; a value that the proposal infers, not of Parkinson et al., 2020)
EXPOSURE_DIFFERENCE = 2.5
#: The columns of the indicators of each zone and of the building in :func:`table_indicators`, with their keys
TABLE_INDICATORS = {
    'Occupied Hours (h)': 'occupied_h',
    'Mean SET_Pierce (°C)': 'mean_set',
    'Mean TSV_causal': 'mean_tsv',
    'Hours In Causal Band (h)': 'in_h',
    'Hours Above Causal Band (h)': 'above_h',
    'Hours Below Causal Band (h)': 'below_h',
    'Hours In Causal Band (%)': 'in_pct',
    'Overcooling Hours (h)': 'overcooling_h',
    'Overcooling Hours (%)': 'overcooling_pct',
    'Mean T_rm_in (°C)': 'mean_t_rm_in',
    'Mean Tn_exp (°C)': 'mean_tn',
    'Mean To - Tn_exp (K)': 'mean_difference',
    'Hours Outside Tn_exp Band (h)': 'outside_h',
    'Mean CoolingEffect (°C)': 'mean_cooling_effect',
    'Drift Limited Hours (h)': 'drift_h',
}
_BUILDING_TYPES = tuple(EXPOSURE_NEUTRAL_TEMPERATURE)
_SET_OUTPUT = 'Zone Thermal Comfort Pierce Model Standard Effective Temperature'
_COOLING_EFFECT_OUTPUT = 'Zone Thermal Comfort ASHRAE 55 Elevated Air Speed Cooling Effect'
_OCCUPIED_HOURS = 'EMS:OCCUPIED HOURS_'
_DRIFT_LIMITED_HOURS = ('DriftLimitedHours', 'EMS:DRIFTLIMITEDHOURS_')
#: The cumulative days of the months of a year of 365 days (the cooling season of the ACCIS takes the dates 'dd/mm' of
#: such a year, :func:`accim.sim.arguments.to_day_of_year`)
_MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30])

Values = Union[pd.Series, np.ndarray, Sequence[float], float]


def _building_type(building_type: str) -> str:
    value = str(building_type).strip().upper()
    if value not in EXPOSURE_NEUTRAL_TEMPERATURE:
        raise ValueError(f'building_type must be one of {list(_BUILDING_TYPES)} (Parkinson, de Dear & Brager, 2020, '
                         f'Fig. 6), not {building_type!r}.')
    return value


def exposure_neutral_temperature(t_rm_in: Values, building_type: str = 'AC') -> Union[np.ndarray, float]:
    """The neutral temperature by exposure, Tn_exp = intercept + slope·T_rm_in, with the coefficients of Parkinson, de
    Dear & Brager (2020), Energy and Buildings 206, 109559, Fig. 6 (:data:`EXPOSURE_NEUTRAL_TEMPERATURE`): 1.06 +
    0.951·Tin for air-conditioned buildings ('AC', the default), 2.91 + 0.879·Tin for mixed-mode ones ('MM') and 2.23 +
    0.897·Tin for naturally ventilated ones ('NV'). A diagnostic, never a setpoint (it refers to itself).

    :param t_rm_in: The running mean indoor temperature (°C), a number or an array (:func:`indoor_running_mean`).
    :param building_type: 'AC', 'MM' or 'NV', in any case.
    :return: Tn_exp (°C; a number for a number, and an array otherwise).
    :raises ValueError: If the building type is not one of them.
    """
    intercept, slope = EXPOSURE_NEUTRAL_TEMPERATURE[_building_type(building_type)]
    values = intercept + slope * np.asarray(t_rm_in, dtype=float)
    return float(values) if np.ndim(values) == 0 else values


def _occupied_hours(length: int, occupied: Any, timestep_h: Any) -> np.ndarray:
    """The occupied hours of each row (0 in the rows without occupants), as :mod:`long_term_discomfort` takes them."""
    hours = np.full(length, float(timestep_h)) if np.ndim(timestep_h) == 0 else np.asarray(timestep_h, dtype=float)
    if occupied is None:
        occupancy = np.ones(length, dtype=bool)
    else:
        occupancy = np.asarray(occupied)
        occupancy = occupancy.astype(bool) if occupancy.dtype == bool else np.nan_to_num(
            occupancy.astype(float)) > 0
    if len(hours) != length or len(occupancy) != length:
        raise ValueError(f'occupied and timestep_h must have {length} values, as the other Series.')
    return np.where(occupancy, np.nan_to_num(hours), 0.0)


def indoor_running_mean(top: Values, day: Sequence[Any], occupied: Any = None, timestep_h: Any = 1.0,
                        alpha_indoor: float = 0.8, initial_T_rm_in: Optional[float] = None) -> np.ndarray:  # noqa: N803
    """The running mean indoor temperature T_rm_in of each row: the exponentially weighted daily running mean of the
    operative temperature of the occupied hours, T_rm_in(d) = (1 − alpha_indoor)·T_occ_mean(d − 1) +
    alpha_indoor·T_rm_in(d − 1), with the definition and the start of the limiter of the drift of the setpoints (task
    F2, :mod:`accim.sim.ems.drift_limiter`; decision 6 of the author of 2026-11-10): T_rm_in is missing (NaN) until the
    end of the first day with occupied hours, and then starts with the mean of that day, unless ``initial_T_rm_in``
    gives the value of the first day; the days without occupied hours do not change it. T_occ_mean(d) is the mean of
    the operative temperature of the occupied rows of the day, weighted by their occupied hours: with the rows of each
    timestep, the mean of the EMS of the limiter, which takes the operative temperature of the previous timestep (that
    of the EMS sensors at the beginning of each timestep), and with hourly rows, that of the hourly means.

    :param top: The operative temperature of each row (°C).
    :param day: The day of each row, in the order of the simulation: a value that changes from one day to the next, such
        as the date (month, day); the rows of a day are consecutive, so a date repeated in another year is another day.
    :param occupied: The occupancy of each row (see the module); None: all the rows.
    :param timestep_h: The hours of each row (a number, or a Series).
    :param alpha_indoor: The weight of the previous day, from 0 to 1 (1 excluded), 0.8 by default.
    :param initial_T_rm_in: The value of the first day (°C), or None.
    :return: T_rm_in of each row (°C, an array).
    :raises ValueError: If ``alpha_indoor`` is not within 0 and 1 or the Series have different lengths.
    """
    if isinstance(alpha_indoor, bool) or not 0 <= float(alpha_indoor) < 1:
        raise ValueError(f'alpha_indoor must be in [0, 1), not {alpha_indoor!r}.')
    values = np.asarray(top, dtype=float).reshape(-1)
    days = list(day)
    if len(days) != len(values):
        raise ValueError(f'day has {len(days)} values, not {len(values)}.')
    hours = _occupied_hours(len(values), occupied, timestep_h)
    valid = ~np.isnan(values) & (hours > 0)
    # The number of the day of each row: a new day where the value changes
    runs = np.cumsum([index == 0 or days[index] != days[index - 1] for index in range(len(days))])
    frame = pd.DataFrame({'run': runs, 'weighted': np.where(valid, values * hours, 0.0),
                          'hours': np.where(valid, hours, 0.0)})
    sums = frame.groupby('run', sort=True)[['weighted', 'hours']].sum()
    alpha = float(alpha_indoor)
    current = np.nan if initial_T_rm_in is None else float(initial_T_rm_in)
    of_run = {}
    for run, (weighted, total) in sums.iterrows():
        of_run[run] = current
        if total > 0:
            mean = weighted / total
            current = mean if np.isnan(current) else (1 - alpha) * mean + alpha * current
    return np.array([of_run[run] for run in runs], dtype=float)


def causal_band_hours(set_values: Values, occupied: Any = None, timestep_h: Any = 1.0,
                      tsv_limit: Optional[float] = None) -> Dict[str, float]:
    """The occupied hours with the SET within the causal band of Sun, Brager & Schiavon (2026), Energy and Buildings
    370, 118097, Fig. 7a (TSV = 0.11·SET − 2.6), above it and below it: the band of TSV ±tsv_limit, from (−tsv_limit +
    2.6)/0.11 to (tsv_limit + 2.6)/0.11 °C of SET, both included, as the hook of comfort standard 24 counts them
    (:func:`accim.sim.comfort_hooks.sun2026_set_setpoints`).

    :param set_values: The SET of each row (°C), such as that of the Pierce model of EnergyPlus.
    :param occupied: The occupancy of each row (see the module); None: all the rows.
    :param timestep_h: The hours of each row (a number, or a Series).
    :param tsv_limit: The half-width of the band of TSV: None for 0.5 (19.09 to 28.18 °C), the band of the paper; 0.7
        and 1.0 are a linear extrapolation of the model, with a warning.
    :return: ``{'in_h', 'above_h', 'below_h', 'in_pct', 'occupied_h', 'mean_set', 'mean_tsv'}``: the occupied hours
        within, above and below the band, the percentage within it of the occupied hours with a SET, those hours, and
        the mean SET and causal TSV of the occupied hours (weighted by their hours; NaN without occupied hours).
    :raises ValueError: If ``tsv_limit`` is not valid.
    """
    from accim.sim.comfort_hooks import causal_tsv, sun2026_set_setpoints

    heating, cooling = sun2026_set_setpoints(1, tsv_limit)
    rows = _frame({'set': set_values}, occupied, timestep_h)
    occupied_h = float(rows['hours'].sum())
    within = (rows['set'] >= heating) & (rows['set'] <= cooling)
    in_h = float(rows.loc[within, 'hours'].sum())
    mean = float((rows['set'] * rows['hours']).sum() / occupied_h) if occupied_h > 0 else float('nan')
    return {'in_h': in_h, 'above_h': float(rows.loc[rows['set'] > cooling, 'hours'].sum()),
            'below_h': float(rows.loc[rows['set'] < heating, 'hours'].sum()),
            'in_pct': 100.0 * in_h / occupied_h if occupied_h > 0 else float('nan'), 'occupied_h': occupied_h,
            'mean_set': mean, 'mean_tsv': float(causal_tsv(mean))}


def overcooling_hours(top: Values, cooling_season: Any, occupied: Any = None, timestep_h: Any = 1.0,
                      threshold: Values = OVERCOOLING_TEMPERATURE) -> Dict[str, float]:
    """The overcooled hours: the occupied hours of the cooling season with the operative temperature below a
    temperature, 22 °C by default (:data:`OVERCOOLING_TEMPERATURE`; Parkinson, Schiavon, de Dear & Brager, 2021, as the
    proposal of block F cites them), or below the reference heating setpoint, given as ``threshold`` (a number or one
    for each row).

    :param top: The operative temperature of each row (°C).
    :param cooling_season: Whether each row is in the cooling season (booleans, or numbers: in it if greater than 0).
    :param occupied: The occupancy of each row (see the module); None: all the rows.
    :param timestep_h: The hours of each row (a number, or a Series).
    :param threshold: The temperature (°C), a number or one for each row.
    :return: ``{'overcooling_h', 'cooling_season_h', 'overcooling_pct'}``: the overcooled hours, the occupied hours of
        the cooling season, and the percentage of these that are overcooled (NaN without them).
    """
    season = np.asarray(cooling_season)
    season = season.astype(bool) if season.dtype == bool else np.nan_to_num(season.astype(float)) > 0
    rows = _frame({'top': top, 'threshold': threshold, 'season': season.astype(float)}, occupied, timestep_h)
    rows = rows[rows['season'] > 0]
    season_h = float(rows['hours'].sum())
    over = float(rows.loc[rows['top'] < rows['threshold'], 'hours'].sum())
    return {'overcooling_h': over, 'cooling_season_h': season_h,
            'overcooling_pct': 100.0 * over / season_h if season_h > 0 else float('nan')}


def exposure_hours(top: Values, t_rm_in: Values, occupied: Any = None, timestep_h: Any = 1.0,
                   building_type: str = 'AC', difference: float = EXPOSURE_DIFFERENCE) -> Dict[str, float]:
    """The neutrality by exposure of the occupied hours: Tn_exp of each row (:func:`exposure_neutral_temperature` of its
    T_rm_in), the occupied hours with abs(To − Tn_exp) greater than ``difference`` (2.5 K by default, the value that
    the proposal of block F infers, :data:`EXPOSURE_DIFFERENCE`), and the means of T_rm_in, Tn_exp and To − Tn_exp. A
    diagnostic: Tn_exp refers to the exposure that the setpoints themselves give.

    :param top: The operative temperature of each row (°C).
    :param t_rm_in: The running mean indoor temperature of each row (°C, :func:`indoor_running_mean`; the rows without
        it are left out).
    :param occupied: The occupancy of each row (see the module); None: all the rows.
    :param timestep_h: The hours of each row (a number, or a Series).
    :param building_type: 'AC' (the default), 'MM' or 'NV', the coefficients of Tn_exp.
    :param difference: The largest difference within the band (K), greater than 0.
    :return: ``{'outside_h', 'occupied_h', 'mean_t_rm_in', 'mean_tn', 'mean_difference'}``: the occupied hours outside
        the band, the occupied hours with T_rm_in, and the means of these hours (weighted by their hours); all but the
        occupied hours are NaN without them.
    :raises ValueError: If the building type or the difference is not valid.
    """
    if isinstance(difference, bool) or not float(difference) > 0:
        raise ValueError(f'difference must be greater than 0 (K), not {difference!r}.')
    neutral = exposure_neutral_temperature(t_rm_in, building_type)
    rows = _frame({'top': top, 't_rm_in': t_rm_in, 'tn': neutral}, occupied, timestep_h)
    occupied_h = float(rows['hours'].sum())
    gap = rows['top'] - rows['tn']

    def mean(values):
        return float((values * rows['hours']).sum() / occupied_h) if occupied_h > 0 else float('nan')

    outside = float(rows.loc[gap.abs() > float(difference), 'hours'].sum()) if occupied_h > 0 else float('nan')
    return {'outside_h': outside, 'occupied_h': occupied_h, 'mean_t_rm_in': mean(rows['t_rm_in']),
            'mean_tn': mean(rows['tn']), 'mean_difference': mean(gap)}


# Table ------------------------------------------------------------------------------------------------------------

def _day_of_year(month: Any, day: Any) -> np.ndarray:
    """The day of the year of each row, in a year of 365 days, as the dates 'dd/mm' of the cooling season of the ACCIS
    (29 February is day 60, as 1 March)."""
    months = pd.to_numeric(pd.Series(month), errors='coerce').to_numpy(dtype=float)
    days = pd.to_numeric(pd.Series(day), errors='coerce').to_numpy(dtype=float)
    index = np.clip(np.nan_to_num(months, nan=1).astype(int) - 1, 0, 11)
    return np.where(np.isnan(months) | np.isnan(days), np.nan, _MONTH_STARTS[index] + days)


def _longest_zone(column: str, zones: Sequence[str]) -> Optional[str]:
    """The longest of the zones whose name the column contains, ignoring the case, or None."""
    found = [zone for zone in zones if zone.upper() in str(column).upper()]
    return max(found, key=len) if found else None


def _people_columns(columns: Sequence[str], zone: str, output: str, zone_of: Callable[[str], Optional[str]]) -> list:
    """The columns of an output of EnergyPlus of the occupants of a zone: '<zone>_<name in Table>' with rename_cols, or
    those of its occupant instances, '<key>:<output> [unit](frequency)', whose zone is the zone."""
    name = f'{zone}_{ENERGYPLUS_OUTPUTS[output]}'.upper()
    renamed = [column for column in columns if str(column).upper() == name]
    if renamed:
        return renamed
    return [column for column in columns
            if str(column).upper().split(' [')[0].endswith(f':{output.upper()}')
            and (zone_of(column) or '').upper() == zone.upper()]


def _mean_of(group: pd.DataFrame, columns: list) -> Optional[pd.Series]:
    """The mean of some columns in each row (the outputs of the occupant instances of a zone), or None without them."""
    if not columns:
        return None
    return group[columns].apply(pd.to_numeric, errors='coerce').mean(axis=1)


def table_indicators(df: pd.DataFrame, zones: Sequence[str], tsv_limit: Optional[float] = None,
                     overcooling_temperature: float = OVERCOOLING_TEMPERATURE, cooling_season_start: Any = 121,
                     cooling_season_end: Any = 274, building_type: str = 'AC', alpha_indoor: float = 0.8,
                     exposure_difference: float = EXPOSURE_DIFFERENCE,
                     zone_of: Optional[Callable[[str], Optional[str]]] = None) -> pd.DataFrame:
    """The indicators of the adaptation to the indoor climate of each simulation of a table of
    :class:`accim.data.postprocessing.main.Table` with timestep or hourly rows, for each occupied zone and for the
    building (:data:`TABLE_INDICATORS`), with the occupied hours of each row of the ACCIS (the output ``Occupied
    Hours_<zone>``) as the time and the operative temperature of each zone:

    - ``Occupied Hours (h)``;
    - with the SET of the Pierce model of EnergyPlus of the occupants of the zone (``SET_Pierce (°C)``, the mean of
      its occupant instances; :func:`accim.sim.people.add_thermal_comfort_outputs`): ``Mean SET_Pierce (°C)``,
      ``Mean TSV_causal`` and the occupied hours within the causal band, above and below it, and the percentage within
      it (:func:`causal_band_hours`);
    - ``Overcooling Hours (h)`` and ``(%)`` (:func:`overcooling_hours`), in the cooling season from
      ``cooling_season_start`` to the day before ``cooling_season_end`` (by the month and day of each row, in a year of
      365 days);
    - ``Mean T_rm_in (°C)``, ``Mean Tn_exp (°C)``, ``Mean To - Tn_exp (K)`` and ``Hours Outside Tn_exp Band (h)``
      (:func:`indoor_running_mean` of the rows of each simulation, whose days are their dates, in the order of the
      table, and :func:`exposure_hours`); T_rm_in is calculated in the same way for every simulation, with or without
      the limiter of the drift of the setpoints (whose own T_rm_in, of the operative temperature of the previous
      timestep, is the output ``T_rm_in (°C)``);
    - with the cooling effect of EnergyPlus (``CoolingEffect (°C)``): ``Mean CoolingEffect (°C)``;
    - with the limiter of the drift of the setpoints: ``Drift Limited Hours (h)``, the sum of its output.

    The building adds up the hours of its zones and weights their means by their hours, of the zones that have each
    output. With hourly rows (and timestep outputs aggregated by Table with ``frequency_agg_func='sum'``), the
    temperatures are the means of each hour. The indicators of an output that a zone does not have are NaN (with a
    warning).

    :param df: The table (``Table.df``), with the columns ``Source`` (the CSV file of each simulation), ``Month`` and
        ``Day``.
    :param zones: The occupied zones (``Table.occupied_zone_list``).
    :param tsv_limit: The half-width of the causal band of TSV (None for 0.5).
    :param overcooling_temperature: The temperature below which the occupied hours of the cooling season are
        overcooled (°C, 22 by default), or the reference heating setpoint.
    :param cooling_season_start: The first day of the cooling season ('dd/mm' or the day of the year; 121, 1 May, by
        default, as in AddAccis).
    :param cooling_season_end: The day after the cooling season (274, 1 October, by default).
    :param building_type: 'AC' (the default), 'MM' or 'NV': the coefficients of Tn_exp.
    :param alpha_indoor: The weight of the previous day in T_rm_in (0.8 by default, as in the limiter).
    :param exposure_difference: The half-width of the band around Tn_exp (K, 2.5 by default).
    :param zone_of: The zone of a column (the function of Table), for the outputs of the occupants with
        ``rename_cols=False``; None: the longest of the zones whose name the column contains.
    :return: A DataFrame with a row for each simulation: ``Source``, the columns that describe the simulations
        (``Model``, ``ComfStand``... ``EPW``, those that the table has), and ``<zone>_<indicator>`` and
        ``Building_<indicator>`` for each indicator.
    :raises ValueError: If the table has no months and days, a zone has not the operative temperature or the occupied
        hours, or an argument is not valid.
    """
    from accim.sim.arguments import to_day_of_year

    if 'Month' not in df.columns or 'Day' not in df.columns:
        raise ValueError('The indicators of the adaptation to the indoor climate need the month and the day of each '
                         'row (a table of timesteps or hours).')
    start = to_day_of_year(cooling_season_start, 'cooling_season_start')
    end = to_day_of_year(cooling_season_end, 'cooling_season_end')
    _building_type(building_type)
    if isinstance(overcooling_temperature, bool) or not isinstance(overcooling_temperature, (int, float)):
        raise ValueError(f'overcooling_temperature must be a number (°C), not {overcooling_temperature!r}.')
    if isinstance(alpha_indoor, bool) or not 0 <= float(alpha_indoor) < 1:
        raise ValueError(f'alpha_indoor must be in [0, 1), not {alpha_indoor!r}.')
    if isinstance(exposure_difference, bool) or not float(exposure_difference) > 0:
        raise ValueError(f'exposure_difference must be greater than 0 (K), not {exposure_difference!r}.')
    if tsv_limit is not None:
        from accim.sim.comfort_hooks import sun2026_set_setpoints

        sun2026_set_setpoints(1, tsv_limit)
    zones = list(zones)
    if zone_of is None:
        def zone_of(column):
            return _longest_zone(column, zones)
    columns = list(df.columns)
    found: Dict[str, Dict[str, Any]] = {}
    missing: List[str] = []
    for zone in zones:
        zone_columns = {'top': _zone_column(columns, zone), 'hours': _zone_column(columns, zone, _OCCUPIED_HOURS)}
        absent = [name for name, column in zone_columns.items() if column is None]
        if absent:
            missing.append(f"{zone} ({', '.join(absent)})")
        zone_columns['set'] = _people_columns(columns, zone, _SET_OUTPUT, zone_of)
        zone_columns['cooling_effect'] = _people_columns(columns, zone, _COOLING_EFFECT_OUTPUT, zone_of)
        renamed, prefix = _DRIFT_LIMITED_HOURS
        zone_columns['drift'] = next((c for c in columns if str(c).upper() == f'{zone}_{renamed} (h)'.upper()),
                                     None) or _zone_column(columns, zone, prefix)
        found[zone] = zone_columns
    if missing:
        raise ValueError('The indicators of the adaptation to the indoor climate need the operative temperature and '
                         'the occupied hours of each occupied zone (the standard outputs of AddAccis), which these '
                         'zones do not have: ' + '; '.join(missing) + '.')
    without_set = [zone for zone, zone_columns in found.items() if not zone_columns['set']]
    if without_set:
        warnings.warn(f'The zones {without_set} have no SET of the Pierce model of EnergyPlus (request it with '
                      f'accim.sim.people.add_thermal_comfort_outputs): their indicators of the causal band are NaN.',
                      UserWarning, stacklevel=2)
    descriptive = [column for column in _DESCRIPTIVE_COLUMNS if column in df.columns]
    nan = float('nan')
    rows = []
    for source, group in df.groupby('Source', sort=False):
        row: Dict[str, Any] = {'Source': source}
        row.update({column: group[column].iloc[0] for column in descriptive})
        day = _day_of_year(group['Month'], group['Day'])
        season = (day >= start) & (day < end)
        dates = list(zip(group['Month'].astype(str), group['Day'].astype(str)))
        totals: Dict[str, List[float]] = {}
        for zone, zone_columns in found.items():
            hours = pd.to_numeric(group[zone_columns['hours']], errors='coerce').fillna(0.0).to_numpy()
            top = pd.to_numeric(group[zone_columns['top']], errors='coerce').to_numpy()
            results: Dict[str, float] = {'occupied_h': float(hours.sum())}
            set_values = _mean_of(group, zone_columns['set'])
            if set_values is None:
                results.update(dict.fromkeys(('in_h', 'above_h', 'below_h', 'in_pct', 'mean_set', 'mean_tsv',
                                              'set_h'), nan))
            else:
                band = causal_band_hours(set_values.to_numpy(), occupied=hours, timestep_h=hours, tsv_limit=tsv_limit)
                results['set_h'] = band.pop('occupied_h')
                results.update(band)
            results.update(overcooling_hours(top, season, occupied=hours, timestep_h=hours,
                                             threshold=float(overcooling_temperature)))
            t_rm_in = indoor_running_mean(top, dates, occupied=hours, timestep_h=hours, alpha_indoor=alpha_indoor)
            exposure = exposure_hours(top, t_rm_in, occupied=hours, timestep_h=hours, building_type=building_type,
                                      difference=exposure_difference)
            results['exposure_h'] = exposure.pop('occupied_h')
            results.update(exposure)
            cooling_effect = _mean_of(group, zone_columns['cooling_effect'])
            if cooling_effect is None:
                results['mean_cooling_effect'], results['cooling_effect_h'] = nan, nan
            else:
                rows_ce = _frame({'ce': cooling_effect.to_numpy()}, hours, hours)
                ce_h = float(rows_ce['hours'].sum())
                results['cooling_effect_h'] = ce_h
                results['mean_cooling_effect'] = (float((rows_ce['ce'] * rows_ce['hours']).sum() / ce_h)
                                                  if ce_h > 0 else nan)
            drift = zone_columns['drift']
            results['drift_h'] = (float(pd.to_numeric(group[drift], errors='coerce').sum()) if drift is not None
                                  else nan)
            for title, key in TABLE_INDICATORS.items():
                row[f'{zone}_{title}'] = results[key]
            for key, value in results.items():
                totals.setdefault(key, []).append(value)
        row.update(_building(totals))
        rows.append(row)
    return pd.DataFrame(rows)


def _building(totals: Dict[str, List[float]]) -> Dict[str, float]:
    """The indicators of the building: the sums of the hours of its zones (of those that have them), and the means of
    the zones weighted by the hours of each mean; NaN if no zone has them."""
    def total(key):
        values = [value for value in totals[key] if not np.isnan(value)]
        return float(sum(values)) if values else float('nan')

    def weighted(key, weight):
        pairs = [(value, hours) for value, hours in zip(totals[key], totals[weight])
                 if not np.isnan(value) and not np.isnan(hours) and hours > 0]
        hours = sum(hours for _, hours in pairs)
        return float(sum(value * hours for value, hours in pairs) / hours) if hours > 0 else float('nan')

    def percentage(part, whole):
        part, whole = total(part), total(whole)
        return 100.0 * part / whole if whole > 0 else float('nan')

    values = {key: total(key) for key in ('occupied_h', 'in_h', 'above_h', 'below_h', 'overcooling_h', 'outside_h',
                                          'drift_h')}
    values.update(in_pct=percentage('in_h', 'set_h'), overcooling_pct=percentage('overcooling_h', 'cooling_season_h'),
                  mean_set=weighted('mean_set', 'set_h'), mean_tsv=weighted('mean_tsv', 'set_h'),
                  mean_t_rm_in=weighted('mean_t_rm_in', 'exposure_h'), mean_tn=weighted('mean_tn', 'exposure_h'),
                  mean_difference=weighted('mean_difference', 'exposure_h'),
                  mean_cooling_effect=weighted('mean_cooling_effect', 'cooling_effect_h'))
    return {f'Building_{title}': values[key] for title, key in TABLE_INDICATORS.items()}
