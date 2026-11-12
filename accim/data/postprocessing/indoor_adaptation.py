# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Indicators of the adaptation of the occupants to the indoor climate (task F3 of block F of accim 1.2.0,
``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, section 4, F3), from the rows of each timestep or hour of the
simulations, for the comparison of the setpoints of several comfort models in the same terms:

- The causal SET band of Sun, Brager & Schiavon (2026), Energy and Buildings 370, 118097, Fig. 7a: TSV = 0.11·SET −
  2.6, whose band of TSV ±0.5 is 19.1 to 28.2 °C of SET (comfort standard 24, :mod:`accim.sim.comfort_hooks`):
  :func:`causal_band_hours`, the occupied hours with the SET within the band, above it and below it. The SET of
  reference of the band is that of pythermalcomfort (``set_tmp``), with which the SET of the database of the model was
  calculated (the ASHRAE Global Thermal Comfort Database II, version 2.1, with the defaults of the function: the
  posture, standing; decided on 2026-11-12, ``notes/decisions.md``): that of the hook of comfort standard 24
  (``SET_<zone>``), and that of :func:`table_indicators` with ``pythermalcomfort_set`` (task S4 of the review of
  accim 1.2.0), in any simulation. Without it, :func:`table_indicators` takes the SET of the Pierce two-node model of
  EnergyPlus (Engineering Reference 25.2, 19.1.4), which any model reports with
  :func:`accim.sim.people.add_thermal_comfort_outputs`, without pythermalcomfort, so that the setpoints of every
  comfort model are measured with the same SET: it approximates the reference SET with activity levels up to about
  1.05 met only, and is 0.3 K higher at 1.1 met and 1 K higher at 1.2 met (task E-F1, ``notes/decisions.md``).
- The overcooling (:func:`overcooling_hours`): the occupied hours of the cooling season with the operative temperature
  below a temperature, 22 °C by default, the typical setpoint of the air-conditioned offices in summer that Parkinson,
  de Dear & Brager (2020), Energy and Buildings 206, 109559, section 4.3.2, describe as overcooled ("current
  summertime practices (~22 °C)"; a design decision of the proposal of block F, which attributed the value to
  Parkinson, Schiavon, de Dear & Brager (2021), *Overcooling of offices...*, Scientific Reports 11, a study of the
  overcooling that gives no temperature threshold: finding A13 of the self-audit of 2026-11-11), or below the
  reference heating setpoint that is given instead. The cooling season is that of the ACCIS (from
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

import copy
import os
import re
import warnings
from collections.abc import Mapping
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from accim.data.postprocessing.long_term_discomfort import _DESCRIPTIVE_COLUMNS, _frame, _zone_column

__all__ = [
    'ENERGYPLUS_OUTPUTS',
    'EXPOSURE_DIFFERENCE',
    'EXPOSURE_NEUTRAL_TEMPERATURE',
    'OVERCOOLING_TEMPERATURE',
    'PYTHERMALCOMFORT_SET_INDICATORS',
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
#: The operative temperature below which an occupied hour of the cooling season is overcooled, by default (°C; the
#: typical summer setpoint of the air-conditioned offices, "current summertime practices (~22 °C)", of Parkinson, de
#: Dear & Brager, 2020, section 4.3.2: a design decision of the proposal of block F)
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
#: The columns of the indicators of the causal band with the SET of pythermalcomfort, the reference SET of the band,
#: that :func:`table_indicators` adds with ``pythermalcomfort_set`` (task S4 of the review of accim 1.2.0), with their
#: keys
PYTHERMALCOMFORT_SET_INDICATORS = {
    'Mean SET_pythermalcomfort (°C)': 'mean_set',
    'Mean TSV_causal_pythermalcomfort': 'mean_tsv',
    'Hours In Causal Band_pythermalcomfort (h)': 'in_h',
    'Hours Above Causal Band_pythermalcomfort (h)': 'above_h',
    'Hours Below Causal Band_pythermalcomfort (h)': 'below_h',
    'Hours In Causal Band_pythermalcomfort (%)': 'in_pct',
}
#: The inputs of the SET of pythermalcomfort that ``pythermalcomfort_set`` gives, those of
#: :class:`accim.sim.comfort_hooks.SetSetpointHook`
_SET_INPUTS = ('met', 'clo', 'air_speed', 'position')
#: The value of ``pythermalcomfort_set``, or of its metabolic rate, clothing insulation or air speed, with which the
#: inputs of the occupants of each row are those of the People objects of the model of each simulation (task S4 of the
#: review of accim 1.2.0, option (ii), decided on 2026-11-12)
PEOPLE_INPUTS = 'people'
#: The key of ``pythermalcomfort_set`` with the path of the model whose People objects are read, for all the
#: simulations (by default, the model of each simulation, in the current folder)
_MODEL_KEY = 'idf'
#: The beginning of the keys of the results of the indicators of the SET of pythermalcomfort
_PYTHERMALCOMFORT = 'pythermalcomfort_'
#: The month, day, hour and minute of the dates of the CSV files of EnergyPlus (' 07/15  10:20:00')
_DATE_TIME = re.compile(r'\s*(\d+)/(\d+)\s+(\d+):(\d+)')
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
    timestep, that of the EMS of the limiter but for one timestep (the EMS takes the operative temperature of the
    previous timestep, that of its sensors at the beginning of each timestep: with the operative temperature shifted
    by one row, the function gives the T_rm_in of the EMS; finding A14 of the self-audit of 2026-11-11), and with hourly
    rows, that of the hourly means.

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
    temperature, 22 °C by default (:data:`OVERCOOLING_TEMPERATURE`, the typical summer setpoint of the air-conditioned
    offices of Parkinson, de Dear & Brager, 2020, section 4.3.2), or below the reference heating setpoint, given as
    ``threshold`` (a number or one for each row).

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


def _cooling_season(day: np.ndarray, start: int, end: int) -> np.ndarray:
    """Whether each day of the year is in the cooling season of the ACCIS (``COOLING_SEASON_LINES`` of
    :mod:`accim.sim.ems.setast`): from ``start`` to the day before ``end``, also when it goes on in the next year
    (``start`` after ``end``, as in the southern hemisphere); no day if they are equal (finding A12 of the self-audit of
    2026-11-11: before, a season in two years had no day)."""
    if start < end:
        return (day >= start) & (day < end)
    if start > end:
        return (day >= start) | (day < end)
    return np.zeros(len(day), dtype=bool)


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


def _is_people(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() == PEOPLE_INPUTS


def _pythermalcomfort_hook(pythermalcomfort_set: Any, zones: Sequence[str]):
    """The hook of the SET with which :func:`table_indicators` calculates the SET of pythermalcomfort of the zones, with
    the inputs of ``pythermalcomfort_set`` (``method='bisection'``, so that nothing is calculated when it is made), and
    where the schedules of the People objects come from when it reads inputs of the occupants from them: ``(hook,
    people, idf)``, with ``people`` the schedules of the hook given (``hook.people``) and ``idf`` the path of the
    model given, or None for both (the model of each simulation)."""
    from accim.sim.comfort_hooks import SetSetpointHook, sun2026_set_setpoints

    people, idf, given_hook = None, None, False
    if _is_people(pythermalcomfort_set):
        inputs = dict.fromkeys(_SET_INPUTS[:3], PEOPLE_INPUTS)
    elif isinstance(pythermalcomfort_set, Mapping):
        inputs = dict(pythermalcomfort_set)
        unknown = [name for name in inputs if name not in (*_SET_INPUTS, _MODEL_KEY)]
        if unknown:
            raise ValueError(f'pythermalcomfort_set takes {list(_SET_INPUTS)} (and {_MODEL_KEY!r}), not {unknown}.')
        idf = inputs.pop(_MODEL_KEY, None)
    elif not isinstance(pythermalcomfort_set, str) and all(hasattr(pythermalcomfort_set, name)
                                                           for name in _SET_INPUTS):
        inputs = {name: getattr(pythermalcomfort_set, name) for name in _SET_INPUTS}
        people = dict(getattr(pythermalcomfort_set, 'people', None) or {}) or None
        given_hook = True
    else:
        raise ValueError(f'pythermalcomfort_set must be None, a dict with the inputs of the occupants '
                         f'{list(_SET_INPUTS)}, {PEOPLE_INPUTS!r} or a hook of the SET, not {pythermalcomfort_set!r}.')
    missing = [name for name in _SET_INPUTS[:3] if inputs.get(name) is None]
    if missing and not (given_hook and people):
        hint = ('the hook reads them from the People objects, and has not their schedules (hook.people, which '
                'apply_set_setpoints and apply_sun2026_setpoints set)' if given_hook else 'they are not given')
        raise ValueError(f'pythermalcomfort_set needs the metabolic rate, clothing insulation and air speed of the '
                         f'occupants (met, clo and air_speed) as numbers, or {PEOPLE_INPUTS!r} for those of the People '
                         f'objects of the model of each simulation in each row, not None for {missing}: {hint}.')
    # The inputs of the People objects are those of the hook without them (None)
    from_people = [name for name in _SET_INPUTS[:3] if inputs.get(name) is None or _is_people(inputs.get(name))]
    inputs.update(dict.fromkeys(from_people))
    if not from_people:
        people, idf = None, None
    heating, cooling = sun2026_set_setpoints(1)
    hook = SetSetpointHook(list(zones) or ['Building'], cooling, heating, method='bisection', **inputs)
    return hook, people, idf


def _date_parts(values: Iterable[Any]) -> np.ndarray:
    """The month, day, hour and minute of the dates of the rows of a CSV file of EnergyPlus (4 columns; NaN in the rows
    without a date)."""
    parts = []
    for value in values:
        match = _DATE_TIME.match(str(value))
        parts.append([float(part) for part in match.groups()] if match else [np.nan] * 4)
    return np.array(parts, dtype=float).reshape(-1, 4)


def _people_of_simulation(source: Any, zones: Sequence[str], people: Optional[Dict[str, dict]], idf: Any,
                          models: Dict[str, Dict[str, dict]]) -> Dict[str, dict]:
    """The schedules of the People objects of the zones of a simulation (:func:`accim.sim.comfort_hooks.people_inputs`),
    by their names in the table (the keys of their outputs): those of the hook given (``people``), or those of the
    model ``idf``, or of the model of the simulation, the IDF file in the current folder whose name is that of its CSV
    file up to its weather file ('<model>[<weather file>.csv', as :func:`accim.run.run_ep` names them); the zones
    whose People objects are not found are left out.

    :param models: The schedules of the models read in this call, by their paths.
    :raises ValueError: If the model is not found, or :func:`accim.sim.comfort_hooks.people_inputs` raises it.
    """
    if people is None:
        name = str(source)[:-4] if str(source).lower().endswith('.csv') else str(source)
        path = str(idf) if idf is not None else f"{name.rsplit('[', 1)[0]}.idf"
        if path not in models:
            if not os.path.isfile(path):
                which = ('its key idf' if idf is not None
                         else 'the name of the CSV file of the simulation up to its weather file')
                raise ValueError(f'pythermalcomfort_set reads the inputs of the occupants of each row from the People '
                                 f'objects of the model of each simulation: {path!r} ({which}) is not a file of the '
                                 f'current folder {os.getcwd()!r}. Give the path of the model with the key '
                                 f"{_MODEL_KEY!r} ({{'met': 'people', 'clo': 'people', 'air_speed': 'people', "
                                 f"'idf': path}}), or the hook of the SET of the model.")
            import accim.sim.accis as accis
            from accim.sim.comfort_hooks import people_inputs

            models[path] = people_inputs(accis.load_idf(path))
        people = models[path]
    by_key = {str(values.get('key', '')).upper(): values for values in people.values()}
    return {zone: by_key[str(zone).upper()] for zone in zones if str(zone).upper() in by_key}


def _pythermalcomfort_set_of_rows(group: pd.DataFrame, source: Any, hook, zones: Sequence[str],
                                  people: Optional[Dict[str, dict]] = None, idf: Any = None,
                                  models: Optional[Dict[str, Dict[str, dict]]] = None
                                  ) -> Dict[str, Optional[np.ndarray]]:
    """The SET of pythermalcomfort of each zone in each row of the table of a simulation (see :func:`table_indicators`):
    that of each row of its CSV file (:func:`accim.sim.comfort_hooks.set_of_results`, keyed by the name of the zone),
    averaged over the rows of the CSV file of each row of the table, by its month, day and hour, and its minute in the
    tables of timesteps (EnergyPlus labels each timestep and hour with its end, and Table gives each row the hour that
    it is part of: that of the label, minus 1 for the labels that end an hour, such as 01:00 and 24:00); None for the
    zones whose outputs the CSV file has not. With a hook that reads inputs of the occupants from the People objects
    (``met``, ``clo`` or ``air_speed`` None), those of each row are those of the People objects of each zone
    (:func:`_people_of_simulation`), whose outputs the CSV file must have.

    :raises ValueError: If the CSV file is not found, or, with the inputs of the People objects, the model is not
        found, a zone has no People object in it, or the CSV file has not the outputs of their schedules.
    """
    from accim.sim.comfort_hooks import (_CLOTHING_VALUE_OUTPUT, _SET_ZONE_VARIABLES, MissingOccupantInputs,
                                         set_of_results)

    path = str(source) if str(source).lower().endswith('.csv') else f'{source}.csv'
    if not os.path.isfile(path):
        raise ValueError(f'The SET of pythermalcomfort of the indicators is calculated from the CSV file of each '
                         f'simulation (the column Source, with .csv), {path!r}, which is not in the current folder '
                         f'{os.getcwd()!r}: use the folder of the table.')
    from_people = any(getattr(hook, name) is None for name in _SET_INPUTS[:3])
    schedules: Dict[str, dict] = {}
    if from_people:
        schedules = _people_of_simulation(source, zones, people, idf, {} if models is None else models)
        without = [zone for zone in zones if zone not in schedules]
        if without:
            raise ValueError(f'The zones {without} of the table have no People objects in the model of the simulation '
                             f'{source!r}, whose schedules give the inputs of the occupants of the SET of '
                             f'pythermalcomfort ({PEOPLE_INPUTS!r}).')
    wanted = [f':{variable} ['.upper() for variable in _SET_ZONE_VARIABLES]
    if from_people:
        wanted += [':SCHEDULE VALUE [', f':{_CLOTHING_VALUE_OUTPUT} ['.upper()]
    results = pd.read_csv(path, skip_blank_lines=False, usecols=lambda column: column.strip() == 'Date/Time' or any(
        name in column.upper() for name in wanted))
    results.columns = [str(column).strip() for column in results.columns]
    if 'Date/Time' not in results.columns:
        raise ValueError(f'The CSV file {path!r} has not the column Date/Time.')
    parts = _date_parts(results['Date/Time'])
    month, day, hour, minute = (pd.to_numeric(group[name], errors='coerce').to_numpy(dtype=float)
                                if name in group.columns else np.zeros(len(group))
                                for name in ('Month', 'Day', 'Hour', 'Minute'))
    timestep_rows = bool((np.nan_to_num(minute) > 0).any())
    hour_of_row = parts[:, 2] - (parts[:, 3] == 0)
    if timestep_rows:
        keys = {'month': parts[:, 0], 'day': parts[:, 1], 'hour': hour_of_row, 'minute': parts[:, 3]}
    else:
        minute = np.zeros(len(group))
        keys = {'month': parts[:, 0], 'day': parts[:, 1], 'hour': hour_of_row, 'minute': np.zeros(len(parts))}
    rows = pd.MultiIndex.from_arrays([month, day, hour, minute])
    found: Dict[str, Optional[np.ndarray]] = {}
    for zone in zones:
        single = copy.copy(hook)
        single.zones = [zone]
        try:
            values = set_of_results(results, single, keys={zone: zone},
                                    people={zone: schedules[zone]} if from_people else None
                                    )[f'SET_{zone}'].to_numpy(dtype=float)
        except MissingOccupantInputs:
            # The outputs of the schedules of the People objects are asked for: a clear error, not NaN
            raise
        except ValueError:
            found[zone] = None
            continue
        frame = pd.DataFrame({**keys, 'set': values}).dropna(subset=list(keys))
        means = frame.groupby(list(keys))['set'].mean()
        found[zone] = means.reindex(rows).to_numpy(dtype=float)
    return found


def table_indicators(df: pd.DataFrame, zones: Sequence[str], tsv_limit: Optional[float] = None,
                     overcooling_temperature: float = OVERCOOLING_TEMPERATURE, cooling_season_start: Any = 121,
                     cooling_season_end: Any = 274, building_type: str = 'AC', alpha_indoor: float = 0.8,
                     exposure_difference: float = EXPOSURE_DIFFERENCE,
                     zone_of: Optional[Callable[[str], Optional[str]]] = None,
                     pythermalcomfort_set: Any = None) -> pd.DataFrame:
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
      365 days; a season that goes on in the next year, with ``cooling_season_start`` after ``cooling_season_end``, as
      in the ACCIS; ``Table(indoor_adaptation_indicators=True)`` takes the defaults, 1 May to 30 September, whatever
      the cooling season of the simulations, so give theirs here if it is another one);
    - ``Mean T_rm_in (°C)``, ``Mean Tn_exp (°C)``, ``Mean To - Tn_exp (K)`` and ``Hours Outside Tn_exp Band (h)``
      (:func:`indoor_running_mean` of the rows of each simulation, whose days are their dates, in the order of the
      table, and :func:`exposure_hours`); T_rm_in is calculated in the same way for every simulation, with or without
      the limiter of the drift of the setpoints (whose own T_rm_in, of the operative temperature of the previous
      timestep, is the output ``T_rm_in (°C)``);
    - with the cooling effect of EnergyPlus (``CoolingEffect (°C)``): ``Mean CoolingEffect (°C)``;
    - with the limiter of the drift of the setpoints: ``Drift Limited Hours (h)``, the sum of its output;
    - with ``pythermalcomfort_set`` (None by default; task S4 of the review of accim 1.2.0): the indicators of the
      causal band with the SET of pythermalcomfort, the reference SET of the band (that of the database of the causal
      model, which was calculated with ``set_tmp``: decided on 2026-11-12, ``notes/decisions.md``), ``Mean
      SET_pythermalcomfort (°C)``, ``Mean
      TSV_causal_pythermalcomfort``, ``Hours In Causal Band_pythermalcomfort (h)``, ``Hours Above Causal
      Band_pythermalcomfort (h)``, ``Hours Below Causal Band_pythermalcomfort (h)`` and ``Hours In Causal
      Band_pythermalcomfort (%)`` (:data:`PYTHERMALCOMFORT_SET_INDICATORS`), after those of each zone and of the
      building. The SET is :func:`accim.sim.comfort_hooks.set_of_results` (``set_tmp`` of pythermalcomfort) of each
      row of the CSV file of each simulation (the column ``Source`` with ``.csv``, in the current folder, as Table
      reads them), with the outputs *Zone Mean Air Temperature*, *Zone Mean Radiant Temperature* and *Zone Air
      Relative Humidity* of each zone, keyed by its name in the table (those that
      :func:`accim.sim.comfort_hooks.apply_set_setpoints` requests; the zones without them, such as those that Table
      names after their spaces, have NaN, with a warning), and the metabolic rate, clothing insulation, air speed and
      posture of ``pythermalcomfort_set``, averaged over the rows of the CSV file of each row of the table (the
      timesteps of each hour, as Table averages the SET of the Pierce model). These are the inputs that task E-F1
      compared. With numbers, those of the occupants are constant, so the SET of pythermalcomfort and that of the
      Pierce model have the same inputs only where the schedules of the People objects give those values (not with a
      seasonal clothing insulation or the dynamic clothing model); with ``'people'`` (task S4, option (ii), decided on
      2026-11-12), they are those of the People objects of each zone in each row, as E-F1 took them and as the hook of
      comfort standard 24 reads them in each timestep (:func:`accim.sim.comfort_hooks.set_of_results`). With the same
      inputs, in a year in Seville, E-F1 measured the SET of pythermalcomfort below that of EnergyPlus by 0.045 K on
      average (at most 0.20 K in the hourly means) standing and by 0.116 K (at most 0.34 K) sitting with 1.06 met,
      which moves the hours near the limits of the band, and by 0.33 to 0.40 K with 1.1 met and 0.94 to 1.02 K with
      1.2 met, since the code of EnergyPlus has no term of the activity in the convective coefficient of the real
      environment (``notes/decisions.md``, E-F1 measured again on 2026-11-12).

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
    :param cooling_season_end: The day after the cooling season (274, 1 October, by default); before
        ``cooling_season_start`` for a season that goes on in the next year, and no season if they are equal.
    :param building_type: 'AC' (the default), 'MM' or 'NV': the coefficients of Tn_exp.
    :param alpha_indoor: The weight of the previous day in T_rm_in (0.8 by default, as in the limiter).
    :param exposure_difference: The half-width of the band around Tn_exp (K, 2.5 by default).
    :param zone_of: The zone of a column (the function of Table), for the outputs of the occupants with
        ``rename_cols=False``; None: the longest of the zones whose name the column contains.
    :param pythermalcomfort_set: None (the default), or the inputs of the occupants of the SET of pythermalcomfort,
        to add its indicators of the causal band (see above): a dict with ``'met'`` (met), ``'clo'`` (clo),
        ``'air_speed'`` (m/s) and, optionally, ``'position'`` ('sitting' or 'standing'; by default, sitting with 1.2
        met or less and standing above it, as the hooks of the SET; 'standing' gives the SET as the database of the
        causal model calculated it, 0.03 to 0.07 K above that of the occupants sitting), such as ``{'met': 1.1,
        'clo': 0.5, 'air_speed': 0.1}``, or a hook of the SET with them
        (:class:`accim.sim.comfort_hooks.SetSetpointHook`, as that of
        :func:`accim.sim.comfort_hooks.apply_sun2026_setpoints` with its own inputs). The metabolic rate, the clothing
        insulation and the air speed can also be ``'people'`` (:data:`PEOPLE_INPUTS`; ``pythermalcomfort_set='people'``
        for the three): those of the People objects of each zone in each row of the CSV file, that is, the values of
        their activity level (divided by 58.2 W/m² and 1.8 m²), clothing insulation and air velocity schedules, or the
        clothing insulation of the dynamic clothing model of ASHRAE 55. Their schedules are read from the model of each
        simulation, the IDF file of the current folder whose name is that of its CSV file up to its weather file
        (``'<model>[<weather file>.csv'``, as :func:`accim.run.run_ep` names them), or from the model of the key
        ``'idf'``, for all the simulations; and their outputs are those that
        :func:`accim.sim.people.add_thermal_comfort_outputs` requests with ``occupant_inputs=True``. A hook that reads
        inputs from the People objects (that of :func:`accim.sim.comfort_hooks.apply_sun2026_setpoints`) gives the
        schedules of those of its model, for all the simulations. It needs pythermalcomfort and the hour of each row.
    :return: A DataFrame with a row for each simulation: ``Source``, the columns that describe the simulations
        (``Model``, ``ComfStand``... ``EPW``, those that the table has), and ``<zone>_<indicator>`` and
        ``Building_<indicator>`` for each indicator.
    :raises ValueError: If the table has no months and days (or hours, with ``pythermalcomfort_set``), a zone has not
        the operative temperature or the occupied hours, an argument is not valid, or the CSV file of a simulation is
        not found with ``pythermalcomfort_set``; and, with the inputs of the People objects, if the model of a
        simulation is not found, a zone of the table has no People objects in it, or its CSV file has not the outputs
        of their schedules (:class:`accim.sim.comfort_hooks.MissingOccupantInputs`).
    :raises ImportError: With ``pythermalcomfort_set``, if pythermalcomfort cannot be imported.
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
    hook, people, idf = (None, None, None) if pythermalcomfort_set is None else _pythermalcomfort_hook(
        pythermalcomfort_set, zones)
    # The schedules of the People objects of the models of the simulations, read once
    models: Dict[str, Dict[str, dict]] = {}
    if hook is not None and 'Hour' not in df.columns:
        raise ValueError('The indicators of the SET of pythermalcomfort need the hour of each row (a table of '
                         'timesteps or hours).')
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
    without_inputs: List[str] = []
    for source, group in df.groupby('Source', sort=False):
        row: Dict[str, Any] = {'Source': source}
        row.update({column: group[column].iloc[0] for column in descriptive})
        day = _day_of_year(group['Month'], group['Day'])
        season = _cooling_season(day, start, end)
        dates = list(zip(group['Month'].astype(str), group['Day'].astype(str)))
        python_set = {} if hook is None else _pythermalcomfort_set_of_rows(group, source, hook, list(found), people,
                                                                           idf, models)
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
            if hook is not None:
                values = python_set.get(zone)
                if values is None:
                    if zone not in without_inputs:
                        without_inputs.append(zone)
                    band = dict.fromkeys(('in_h', 'above_h', 'below_h', 'in_pct', 'occupied_h', 'mean_set',
                                          'mean_tsv'), nan)
                else:
                    band = causal_band_hours(values, occupied=hours, timestep_h=hours, tsv_limit=tsv_limit)
                band['set_h'] = band.pop('occupied_h')
                results.update({_PYTHERMALCOMFORT + key: value for key, value in band.items()})
            for title, key in TABLE_INDICATORS.items():
                row[f'{zone}_{title}'] = results[key]
            if hook is not None:
                for title, key in PYTHERMALCOMFORT_SET_INDICATORS.items():
                    row[f'{zone}_{title}'] = results[_PYTHERMALCOMFORT + key]
            for key, value in results.items():
                totals.setdefault(key, []).append(value)
        row.update(_building(totals))
        if hook is not None:
            row.update(_building(totals, pythermalcomfort=True))
        rows.append(row)
    if without_inputs:
        warnings.warn(f'The zones {without_inputs} have not the outputs Zone Mean Air Temperature, Zone Mean Radiant '
                      f'Temperature and Zone Air Relative Humidity, keyed by their names, in the CSV files of some '
                      f'simulations: their indicators of the SET of pythermalcomfort are NaN.', UserWarning,
                      stacklevel=2)
    return pd.DataFrame(rows)


def _total(totals: Dict[str, List[float]], key: str) -> float:
    """The sum of the values of the zones that have them, or NaN if none has them."""
    values = [value for value in totals[key] if not np.isnan(value)]
    return float(sum(values)) if values else float('nan')


def _weighted(totals: Dict[str, List[float]], key: str, weight: str) -> float:
    """The mean of the values of the zones that have them, weighted by their hours; NaN without them."""
    pairs = [(value, hours) for value, hours in zip(totals[key], totals[weight])
             if not np.isnan(value) and not np.isnan(hours) and hours > 0]
    hours = sum(hours for _, hours in pairs)
    return float(sum(value * hours for value, hours in pairs) / hours) if hours > 0 else float('nan')


def _percentage(totals: Dict[str, List[float]], part: str, whole: str) -> float:
    """The percentage of the sum of some hours of the zones in the sum of others; NaN without them."""
    part_h, whole_h = _total(totals, part), _total(totals, whole)
    return 100.0 * part_h / whole_h if whole_h > 0 else float('nan')


def _building(totals: Dict[str, List[float]], pythermalcomfort: bool = False) -> Dict[str, float]:
    """The indicators of the building: the sums of the hours of its zones (of those that have them), and the means of
    the zones weighted by the hours of each mean; NaN if no zone has them. With ``pythermalcomfort``, those of the SET
    of pythermalcomfort (:data:`PYTHERMALCOMFORT_SET_INDICATORS`)."""
    if pythermalcomfort:
        def key(name):
            return _PYTHERMALCOMFORT + name

        values = {name: _total(totals, key(name)) for name in ('in_h', 'above_h', 'below_h')}
        values.update(in_pct=_percentage(totals, key('in_h'), key('set_h')),
                      mean_set=_weighted(totals, key('mean_set'), key('set_h')),
                      mean_tsv=_weighted(totals, key('mean_tsv'), key('set_h')))
        return {f'Building_{title}': values[name] for title, name in PYTHERMALCOMFORT_SET_INDICATORS.items()}
    values = {key: _total(totals, key) for key in ('occupied_h', 'in_h', 'above_h', 'below_h', 'overcooling_h',
                                                   'outside_h', 'drift_h')}
    values.update(in_pct=_percentage(totals, 'in_h', 'set_h'),
                  overcooling_pct=_percentage(totals, 'overcooling_h', 'cooling_season_h'),
                  mean_set=_weighted(totals, 'mean_set', 'set_h'), mean_tsv=_weighted(totals, 'mean_tsv', 'set_h'),
                  mean_t_rm_in=_weighted(totals, 'mean_t_rm_in', 'exposure_h'),
                  mean_tn=_weighted(totals, 'mean_tn', 'exposure_h'),
                  mean_difference=_weighted(totals, 'mean_difference', 'exposure_h'),
                  mean_cooling_effect=_weighted(totals, 'mean_cooling_effect', 'cooling_effect_h'))
    return {f'Building_{title}': values[key] for title, key in TABLE_INDICATORS.items()}
