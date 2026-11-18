# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The setpoints of the ACCIS without EnergyPlus (proposal E1).

- :func:`outdoor_metrics`: the outdoor temperatures of reference of the adaptive comfort models, from the dry-bulb
  temperatures of a weather file (EPW): the daily mean, the running mean of EN 16798-1:2019 (formula B.1, with any
  alpha), its approximate formula (B.2), the arithmetic mean of the n previous days (ASHRAE 55-2020, 5.4.2.1), the
  reference temperature of the Dutch ATG (van der Linden et al., 2006) and the monthly mean.
- :func:`energyplus_running_means`: the running mean outdoor temperatures that the EMS of accim reads from EnergyPlus,
  ``RMOT`` (CEN 15251) and ``PMOT`` (ASHRAE 55), as EnergyPlus calculates them (Engineering Reference 25.2, 19.1),
  also with a .stat file next to the weather file (:func:`stat_file_of`, :func:`read_stat_monthly_means`).
- :func:`compute_setpoints`: the setpoints of a comfort standard, category and comfort mode in each hour of a weather
  file, calculated by the EMS programs of the output IDFs of :class:`accim.sim.accis.AddAccis`
  (:func:`accim.utils.get_setpoint_ems_programs`, the code that :func:`accim.utils.print_setpoint_ems_code` prints)
  with the Erl interpreter of accim (:mod:`accim.sim.ems.erl`), as EnergyPlus runs them.
- :func:`plot_setpoints`: a figure of the setpoints.

The equations of the running means are those of section 11.4 of the proposals of 1.2.0
(``notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md``): EN 16798-1:2019, Annex B, formulas (B.1) and (B.2); ASHRAE 55-2020,
5.4.2.1; van der Linden, A.C. et al. (2006), Adaptive temperature limits: A new guideline in the Netherlands, Energy and
Buildings 38, 8-17; and the EnergyPlus Engineering Reference 25.2, 19.1, equations (19.70) to (19.72) and (19.82) to
(19.84).
"""

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from accim._deprecation import accepts_legacy_kwargs
from accim.sim.arguments import DEPRECATED_ARGUMENT_NAMES

__all__ = [
    'ENERGYPLUS_ASHRAE55_DAYS',
    'ENERGYPLUS_CEN15251_ALPHA',
    'SETPOINT_EMS_VARIABLES',
    'TIMESTEPS_PER_HOUR',
    'compute_setpoints',
    'energyplus_running_means',
    'outdoor_metrics',
    'plot_setpoints',
    'read_epw_dry_bulb',
    'read_stat_monthly_means',
    'stat_file_of',
]

PathLike = Union[str, Path]
Number = Union[int, float]

#: The numbers of timesteps per hour that EnergyPlus accepts (field Number of Timesteps per Hour of the object Timestep,
#: Energy+.idd), 6 by default
TIMESTEPS_PER_HOUR = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60)
#: The alpha of the running mean of CEN 15251 in EnergyPlus (Engineering Reference 25.2, equation 19.84)
ENERGYPLUS_CEN15251_ALPHA = 0.8
#: The number of days of the running mean of ASHRAE 55 in EnergyPlus (Engineering Reference 25.2, equation 19.70)
ENERGYPLUS_ASHRAE55_DAYS = 30
#: The weights of the daily means of the 7 previous days in the approximate running mean of EN 16798-1:2019, formula
#: (B.2), and their sum
_B2_WEIGHTS = (1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2)
_B2_DIVISOR = 3.8
#: The weights of the day and the 3 previous days in the reference temperature of the Dutch ATG (van der Linden et al.,
#: 2006), each the mean of the maximum and the minimum of the day, and their sum
_ATG_WEIGHTS = (1.0, 0.8, 0.4, 0.2)
_ATG_DIVISOR = 2.4
#: The line of a .stat file before its monthly statistics of the dry-bulb temperatures, and the position of the line of
#: their daily averages after it (the line 'Daily Avg'), as EnergyPlus reads them (CalcThermalComfortAdaptiveASH55 of
#: ThermalComfort.cc, EnergyPlus 25.1)
_STAT_SECTION = 'Monthly Statistics for Dry Bulb temperatures'
_STAT_DAILY_AVERAGES = 8
#: The year of the dates of the rows: weather files of 365 days have no 29 February
_YEAR = 2007
_LEAP_YEAR = 2008
#: The line of the header of a weather file whose second field, LeapYear Observed, says whether the file observes leap
#: years ('Yes' or 'No')
_LEAP_YEAR_LINE = 'HOLIDAYS/DAYLIGHT SAVINGS'
#: The columns of :func:`compute_setpoints` that the EMS of each zone of an output IDF reports, and their EMS variables:
#: the outputs ``<output>_<zone>`` of :data:`accim.sim.ems.objects.ZONE_SETPOINT_OUTPUT_VARIABLES` ('Adaptive Cooling
#: Setpoint Temperature' is roundedACST, and 'Adaptive Cooling Setpoint Temperature_No Tolerance' is ACSTnoTol)
SETPOINT_EMS_VARIABLES = {'ComfTemp': 'ComfTemp', 'ACST': 'roundedACST', 'AHST': 'roundedAHST',
                          'ACSTnoTol': 'ACSTnoTol', 'AHSTnoTol': 'AHSTnoTol'}
_REPORTED = tuple(SETPOINT_EMS_VARIABLES.items())
#: The zone of the programs of compute_setpoints (the programs of a zone of an output IDF)
_ZONE = 'Z'


def read_epw_dry_bulb(epw: PathLike) -> pd.DataFrame:
    """The hourly dry-bulb temperatures of a weather file (EPW), one row per hour.

    The first 8 lines of the file are its header, as EnergyPlus reads it; the records are the hours 1 to 24 of each
    day (the hour 1 is the first hour of the day). The file is read as Latin-1, whose bytes are all characters: the
    header of many weather files has the names of their location in another encoding than UTF-8 (such as the Seville.epw
    of the sample files of accim), and the records are ASCII.

    :param epw: The path of the weather file.
    :return: A DataFrame with the columns ``month``, ``day``, ``hour`` and ``dry_bulb`` (°C).
    :raises ValueError: If the file does not have whole days of hourly records.
    """
    data = pd.read_csv(epw, skiprows=8, header=None, usecols=[1, 2, 3, 6], encoding='latin-1')
    data.columns = ['month', 'day', 'hour', 'dry_bulb']
    hours = data['hour'].to_numpy()
    if len(data) == 0 or len(data) % 24 or not (hours.reshape(-1, 24) == np.arange(1, 25)).all():
        raise ValueError(f'{epw} does not have whole days of hourly records (hours 1 to 24 of each day).')
    return data


def stat_file_of(epw: PathLike) -> Optional[Path]:
    """The .stat file of a weather file: the file with its name and the extension .stat in its folder, where EnergyPlus
    looks for it when it simulates with the weather file; None if there is none.

    :param epw: The path of the weather file (EPW).
    :return: The path of the .stat file, or None.
    """
    path = Path(epw).with_suffix('.stat')
    return path if path.is_file() else None


def read_stat_monthly_means(stat_file: PathLike) -> np.ndarray:
    """The monthly means of the daily dry-bulb temperatures of a .stat file (its line ``Daily Avg`` of the monthly
    statistics of the dry-bulb temperatures), from January to December.

    With a .stat file next to the weather file of a simulation (:func:`stat_file_of`), EnergyPlus takes the mean of the
    month of each day as the running mean of ASHRAE 55 of the day (``PMOT``), instead of the mean of the daily means of
    the 30 previous days (Engineering Reference 25.2, 19.1; :func:`energyplus_running_means`). The means are read as
    ``CalcThermalComfortAdaptiveASH55`` of ``ThermalComfort.cc`` (EnergyPlus 25.1) reads them: the 8th line after the
    first one that has 'Monthly Statistics for Dry Bulb temperatures', split by tabs, its columns 3 to 14, which is the
    line ``Daily Avg`` in the .stat files of the weather files of EnergyPlus and in those of the Future Weather
    Generator (:func:`accim.data.morphing.morph_epws`). The file is read as Latin-1 (the degree sign of its headers is
    written in several encodings).

    :param stat_file: The path of the .stat file.
    :return: An array of the 12 monthly means (°C).
    :raises ValueError: If the file has no such line, or the line of the daily averages has not 12 numbers in those
        columns (EnergyPlus would take 0 °C for the months that it cannot read, without an error).
    """
    with open(stat_file, 'r', encoding='latin-1') as file:
        lines = file.read().splitlines()
    found = next((number for number, line in enumerate(lines) if _STAT_SECTION in line), None)
    if found is None:
        raise ValueError(f"{stat_file} has no line '{_STAT_SECTION}', whose daily averages of each month EnergyPlus "
                         f"takes as the running mean of ASHRAE 55 when the .stat file is next to the weather file.")
    position = found + _STAT_DAILY_AVERAGES
    columns = lines[position].split('\t')[2:14] if position < len(lines) else []
    try:
        means = np.array([float(column) for column in columns])
    except ValueError:
        means = np.array([])
    if len(means) != 12:
        raise ValueError(f"{stat_file}: its line {position + 1}, {_STAT_DAILY_AVERAGES} lines after '{_STAT_SECTION}', "
                         f"has not the daily averages of the 12 months in its columns 3 to 14 (separated by tabs), "
                         f"where EnergyPlus reads them.")
    return means


def _stat_means(epw: PathLike, stat_file: Union[PathLike, None]) -> Tuple[Optional[Path], Optional[np.ndarray]]:
    """The .stat file of the running mean of ASHRAE 55 (that of the weather file with 'auto', none with None, or the
    one given) and its monthly means."""
    if stat_file is None:
        return None, None
    if isinstance(stat_file, str) and stat_file == 'auto':
        path = stat_file_of(epw)
        if path is None:
            return None, None
    else:
        path = Path(stat_file)
        if not path.is_file():
            raise FileNotFoundError(f'The .stat file {stat_file} does not exist.')
    return path, read_stat_monthly_means(path)


def _observes_leap_years(epw: PathLike) -> bool:
    """True if the header of a weather file says that it observes leap years: the second field of its line
    'HOLIDAYS/DAYLIGHT SAVINGS', LeapYear Observed, begins with 'Y'."""
    with open(epw, 'r', encoding='latin-1') as file:
        for number, line in enumerate(file):
            if number >= 8:
                break
            if line.upper().startswith(_LEAP_YEAR_LINE):
                fields = line.split(',')
                return len(fields) > 1 and fields[1].strip().upper().startswith('Y')
    return False


def _energyplus_days(epw: PathLike) -> Tuple[pd.DataFrame, np.ndarray]:
    """The hourly records of a weather file as EnergyPlus 25.1 simulates them with the adaptive comfort models of the
    People objects, and the daily means of the days of the file by their position, as it reads the days before the
    run period (see :func:`energyplus_running_means`).

    :return: The records of the simulated year of 365 days (those of 29 February left out), as
        :func:`read_epw_dry_bulb` gives them, and the daily means of all the days of the file, in their order.
    :raises ValueError: If the header of the file says that it observes leap years, with which EnergyPlus does not
        simulate the adaptive comfort models, or the file has not 365 days, or 366 with 29 February.
    """
    if _observes_leap_years(epw):
        raise ValueError(f'The header of {epw} says that it observes leap years ({_LEAP_YEAR_LINE}, LeapYear Observed: '
                         f'Yes): EnergyPlus 25.1 does not simulate the adaptive comfort models of the People objects, '
                         f'whose running means the ACCIS reads, with such a weather file (the severe error '
                         f'"AdaptiveComfort Reporting does not work correctly with leap years in weather files", '
                         f'before the simulation).')
    hourly = read_epw_dry_bulb(epw)
    by_position = hourly['dry_bulb'].to_numpy(dtype=float).reshape(-1, 24).mean(axis=1)
    leap_day = ((hourly['month'] == 2) & (hourly['day'] == 29)).to_numpy()
    if len(by_position) == 366 and leap_day.sum() == 24:
        hourly = hourly[~leap_day].reset_index(drop=True)
    if len(hourly) != 365 * 24:
        raise ValueError(f'{epw} has {len(by_position)} days: the running means of EnergyPlus need a weather file of a '
                         f'whole year of 365 days (8760 hours), or of 366 days with 29 February.')
    return hourly, by_position


def _dates(month: np.ndarray, day: np.ndarray, number_of_days: int) -> pd.DatetimeIndex:
    year = _LEAP_YEAR if number_of_days == 366 else _YEAR
    return pd.to_datetime(pd.DataFrame({'year': year, 'month': month, 'day': day}))


def _previous(values: np.ndarray, days: int) -> np.ndarray:
    """The values of ``days`` days before each day; the first days take those of the end of the file, as if the year
    repeated (as EnergyPlus does at the beginning of a run period)."""
    return np.roll(values, days)


def outdoor_metrics(epw: PathLike, alpha: float = 0.8, days: int = 30, frequency: str = 'hourly') -> pd.DataFrame:
    """The outdoor temperatures of reference of the adaptive comfort models, from the dry-bulb temperatures of a weather
    file, for each hour (or day) of the file.

    The running means of each day are calculated with the daily means of the previous days; those of the first days
    take the last days of the file, as if the year repeated:

    - ``daily_mean``, ``daily_max`` and ``daily_min``: the mean, maximum and minimum of the 24 hourly values of the
      day.
    - ``RMOT``: the running mean outdoor temperature of EN 16798-1:2019, formula (B.1),
      Θrm = (1 − α)·{Θed−1 + α·Θed−2 + α²·Θed−3 + …}, where Θed−i is the daily mean of the i-th previous day, with the
      ``alpha`` given (0.8 is the value that the standard recommends); for a year that repeats, the infinite sum is
      that of the days of the year divided by 1 − α^n (n, the days of the file).
    - ``RMOT_7day``: its approximate formula, (B.2),
      Θrm = (Θed−1 + 0.8·Θed−2 + 0.6·Θed−3 + 0.5·Θed−4 + 0.4·Θed−5 + 0.3·Θed−6 + 0.2·Θed−7)/3.8.
    - ``PMOT_n``: the prevailing mean outdoor temperature of ASHRAE 55-2020 (5.4.2.1), the arithmetic mean of the daily
      means of the ``days`` previous days (7 to 30 in the standard).
    - ``Te_ref_nl``: the reference temperature of the Dutch ATG (van der Linden et al., 2006),
      Te,ref = (T0 + 0.8·T−1 + 0.4·T−2 + 0.2·T−3)/2.4, where Ti is the mean of the maximum and the minimum of the day i
      (0, the day itself).
    - ``monthly_mean``: the mean of the month.

    These are the definitions of the standards. EnergyPlus calculates the running means that the EMS of accim reads
    in another way (see :func:`energyplus_running_means`).

    :param epw: The path of the weather file (EPW).
    :param alpha: The alpha of ``RMOT``, between 0 and 1 (not included).
    :param days: The number of days of ``PMOT_n``, at least 1 and not more than the days of the file.
    :param frequency: 'hourly' for a row for each hour, with its dry-bulb temperature (``Tout``) and its date and time
        (``datetime``, the end of the hour, as EnergyPlus reports it); 'daily' for a row for each day (``date``).
    :return: A DataFrame with these columns, and ``alpha`` and ``days`` in its ``attrs``.
    :raises ValueError: If ``alpha``, ``days`` or ``frequency`` are not valid, or the file does not have whole days.
    """
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not 0 < alpha < 1:
        raise ValueError(f'alpha must be a number between 0 and 1 (not included), not {alpha!r}.')
    if frequency not in ('hourly', 'daily'):
        raise ValueError(f"frequency must be 'hourly' or 'daily', not {frequency!r}.")
    hourly = read_epw_dry_bulb(epw)
    temperatures = hourly['dry_bulb'].to_numpy(dtype=float).reshape(-1, 24)
    number_of_days = len(temperatures)
    if isinstance(days, bool) or not isinstance(days, (int, np.integer)) or not 1 <= days <= number_of_days:
        raise ValueError(f'days must be an integer between 1 and {number_of_days}, not {days!r}.')
    mean = temperatures.mean(axis=1)
    maximum = temperatures.max(axis=1)
    minimum = temperatures.min(axis=1)

    # EN 16798-1 (B.1), for a year that repeats
    rmot = sum(alpha ** (k - 1) * _previous(mean, k) for k in range(1, number_of_days + 1))
    rmot = rmot * (1 - alpha) / (1 - alpha ** number_of_days)
    # EN 16798-1 (B.2)
    rmot_7day = sum(w * _previous(mean, k) for k, w in enumerate(_B2_WEIGHTS, 1)) / _B2_DIVISOR
    # ASHRAE 55-2020 (5.4.2.1), arithmetic mean
    pmot = sum(_previous(mean, k) for k in range(1, days + 1)) / days
    # van der Linden et al. (2006)
    middle = (maximum + minimum) / 2
    te_ref = sum(w * _previous(middle, k) for k, w in enumerate(_ATG_WEIGHTS)) / _ATG_DIVISOR

    first_hours = hourly.iloc[::24]
    months = first_hours['month'].to_numpy()
    monthly = pd.Series(mean).groupby(months).transform('mean').to_numpy()
    daily = pd.DataFrame({
        'date': _dates(months, first_hours['day'].to_numpy(), number_of_days),
        'daily_mean': mean, 'daily_max': maximum, 'daily_min': minimum, 'RMOT': rmot, 'RMOT_7day': rmot_7day,
        'PMOT_n': pmot, 'Te_ref_nl': te_ref, 'monthly_mean': monthly,
    })
    if frequency == 'daily':
        result = daily
    else:
        repeated = daily.drop(columns='date').loc[np.repeat(np.arange(number_of_days), 24)].reset_index(drop=True)
        datetimes = (_dates(hourly['month'].to_numpy(), hourly['day'].to_numpy(), number_of_days)
                     + pd.to_timedelta(hourly['hour'].to_numpy(), unit='h'))
        result = pd.concat([pd.DataFrame({'datetime': datetimes, 'Tout': hourly['dry_bulb'].to_numpy(dtype=float)}),
                            repeated], axis=1)
    result.attrs.update(alpha=alpha, days=days)
    return result


def _energyplus_daily(epw: PathLike, timesteps_per_hour: int, start_date: Union[int, str],
                      stat_file: Union[PathLike, None] = 'auto') -> Tuple[pd.DataFrame, pd.DataFrame, int]:
    """The daily running means of EnergyPlus (see :func:`energyplus_running_means`), the hourly records of the
    simulated year (:func:`_energyplus_days`) and the index of the first day of the run period."""
    from accim.sim.arguments import to_day_of_year

    if timesteps_per_hour not in TIMESTEPS_PER_HOUR:
        raise ValueError(f'timesteps_per_hour must be one of {list(TIMESTEPS_PER_HOUR)} (those of EnergyPlus), '
                         f'not {timesteps_per_hour!r}.')
    stat_path, stat_means = _stat_means(epw, stat_file)
    hourly, by_position = _energyplus_days(epw)
    temperatures = hourly['dry_bulb'].to_numpy(dtype=float).reshape(-1, 24)
    number_of_days = len(temperatures)
    first = to_day_of_year(start_date, 'start_date') - 1
    if first >= number_of_days:
        raise ValueError(f'start_date {start_date!r} is not a day of the weather file.')
    n = timesteps_per_hour
    file_mean = temperatures.mean(axis=1)
    # The daily mean of each simulated day: the mean of the outdoor temperatures of the first timestep of each hour,
    # which EnergyPlus interpolates between the previous and the current hourly values; on the first day of the run
    # period, the hour before the first one is the last hour of the same day (EnergyPlus repeats the first day in its
    # warm-up)
    previous_last = _previous(temperatures[:, 23], 1)
    previous_last[first] = temperatures[first, 23]
    simulated = file_mean + (n - 1) / n * (previous_last - temperatures[:, 23]) / 24

    def daily_mean(day: int) -> float:
        # The days before the run period are those of the weather file (the last ones for the first days of the year),
        # by their position in it, in a year of 365 days (the same days as by their dates in a file of 365 days)
        if day >= first:
            return simulated[day]
        if day == first - 1 and 1 <= first <= length - 1:
            # A run period that begins on the 2nd to the 30th of January: ThermalComfort.cc reads the days of January
            # before it and then the last days of December, and at the first BeginDayFlag writes the last day read (the
            # 365th of the file, 31 December in a file of 365 days) over the day before the run period, which stays in
            # the 30 days of PMOT for 30 days
            return by_position[number_of_days - 1]
        return by_position[day % number_of_days]

    alpha = ENERGYPLUS_CEN15251_ALPHA
    length = ENERGYPLUS_ASHRAE55_DAYS
    days = range(first, number_of_days)
    # ASHRAE 55: the simple mean of the 30 previous daily means (equation 19.70)
    pmot = np.array([np.mean([daily_mean(day - k) for k in range(1, length + 1)]) for day in days])
    # CEN 15251: at the beginning, the weighted sum of the 7 previous days of equation (19.82), which is not divided by
    # 1 - alpha^7 (also by their position in the file); then, each day, equation (19.83) with the daily mean of the
    # previous day
    rmot = np.empty(len(days))
    rmot[0] = (1 - alpha) * sum(alpha ** (k - 1) * by_position[(first - k) % number_of_days] for k in range(1, 8))
    for index in range(1, len(days)):
        rmot[index] = alpha * rmot[index - 1] + (1 - alpha) * simulated[first + index - 1]
    first_hours = hourly.iloc[24 * first::24]
    if stat_means is not None:
        # With a .stat file, the mean of the month of each day (CalcThermalComfortAdaptiveASH55 with useStatData, at
        # each BeginDayFlag)
        pmot = stat_means[first_hours['month'].to_numpy() - 1]
    result = pd.DataFrame({
        'date': _dates(first_hours['month'].to_numpy(), first_hours['day'].to_numpy(), number_of_days),
        'daily_mean': file_mean[first:], 'simulated_daily_mean': simulated[first:], 'RMOT': rmot, 'PMOT': pmot,
    })
    result.attrs['stat_file'] = None if stat_path is None else str(stat_path)
    return result, hourly, first


def energyplus_running_means(epw: PathLike, timesteps_per_hour: int = 6, start_date: Union[int, str] = 1,
                             stat_file: Union[PathLike, None] = 'auto') -> pd.DataFrame:
    """The running mean outdoor temperatures that EnergyPlus calculates for the adaptive comfort models of the People
    objects, which the EMS of accim reads (``RMOT``, *Zone Thermal Comfort CEN 15251 Adaptive Model Running Average
    Outdoor Air Temperature*, and ``PMOT``, *Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air
    Temperature*), for each day of a run period that begins on ``start_date`` and lasts until the end of the year of
    the weather file.

    As in the Engineering Reference of EnergyPlus 25.2 (19.1), both are calculated from the weather file, which must
    have a whole year:

    - ``PMOT`` is the simple mean of the daily means of the 30 previous days (equation 19.70).
    - ``RMOT`` is, on the first day of the run period, (1 − α)·{Tod−1 + α·Tod−2 + … + α⁶·Tod−7} with α = 0.8
      (equation 19.82, which is not divided by 1 − α⁷, so it is lower than the running mean of EN 16798-1 in the first
      days), and, on the next days, (1 − α)·Tod−1 + α·To−1 (equation 19.83).

    The daily means of the days before the run period are those of the 24 hourly values of the weather file (the last
    days of the file for the first days of the year). Those of the simulated days are the means of the outdoor
    temperatures of the first timestep of each hour, which EnergyPlus interpolates between the hourly values of the
    file (on the first day, the hour before the first one is the last hour of the same day). These are the values that
    EnergyPlus 25.1 reports (checked with a simulation of a year of the sample model; its source code,
    ``ThermalComfort.cc``, does the same). With a run period that begins between the 2nd and the 30th of January,
    ``CalcThermalComfortAdaptiveASH55`` of ``ThermalComfort.cc`` (EnergyPlus 25.1) reads the days of January before it
    and then the last days of December, and its first ``BeginDayFlag`` writes the mean of the last day read, 31
    December, over that of the day before the run period, so ``PMOT`` takes the mean of 31 December in its place for 30
    days; this is reproduced too (finding E1-1 of the review of accim 1.2.0; with ``Seville_Present.epw`` from 8 January,
    ``PMOT`` is 0.14 °C lower than the mean of the 30 previous days, as EnergyPlus 25.1 reports it). ``RMOT`` has no
    such step.

    With a .stat file next to the weather file (``Seville.stat`` for ``Seville.epw``, as the Future Weather Generator
    writes them, :func:`accim.data.morphing.morph_epws`, and as the weather files of EnergyPlus come), EnergyPlus takes
    as ``PMOT`` of each day the mean of its month in the .stat file (Engineering Reference 25.2, 19.1;
    :func:`read_stat_monthly_means`), and so does this function with ``stat_file='auto'`` (the default; before accim
    1.2.0, the .stat file was not read): checked with EnergyPlus 25.1, a .stat file next to the weather file and a run
    period of January and February. ``RMOT`` does not use it.

    With a weather file of 366 days, with 29 February, measured with EnergyPlus 25.1 (task E1 of the review of accim
    1.2.0): if its header says that it observes leap years (the field LeapYear Observed of its line 'HOLIDAYS/DAYLIGHT
    SAVINGS' is Yes, whatever its number of days), EnergyPlus does not simulate the adaptive comfort models of the
    People objects, which the ACCIS reads (the severe error "AdaptiveComfort Reporting does not work correctly with
    leap years in weather files" stops it before the simulation), and this function raises a ``ValueError``. If it
    says No, EnergyPlus simulates a year of 365 days, whatever the year of the run period, with the records of the
    dates of the simulated days (those of 29 February left out), but it reads the days before the run period by their
    position in the file, counting a year of 365 days: after 28 February, the 30 days of ``PMOT`` and the 7 of ``RMOT``
    of the first day of the run period are one day earlier than their dates (29 February in, the day before the run
    period out), and for the first days of January, the last days of the file before its 366th (30 December in the
    place of 31 December). This function does the same (checked with EnergyPlus 25.1 and run periods from January,
    March and December, in a leap year and in another one).

    :param epw: The path of the weather file (EPW), of 365 days, or of 366 with 29 February and without leap years in
        its header.
    :param timesteps_per_hour: The number of timesteps per hour of the model (the object Timestep, 6 by default).
    :param start_date: The first day of the run period, a date 'dd/mm' or a day of the year (1, by default).
    :param stat_file: 'auto' (the default) for the .stat file next to the weather file, if there is one
        (:func:`stat_file_of`), as EnergyPlus; None for the running mean of the weather file, without a .stat file; or
        the path of a .stat file (that of the weather file of the simulation, if it is elsewhere).
    :return: A DataFrame with a row for each day: ``date``, ``daily_mean`` (of the file), ``simulated_daily_mean``,
        ``RMOT`` and ``PMOT``, and the path of the .stat file read (or None) in ``attrs['stat_file']``.
    :raises ValueError: If the weather file does not have 365 days or 366 with 29 February, its header says that it
        observes leap years, the .stat file has not the monthly means where EnergyPlus reads them, or the arguments are
        not valid.
    :raises FileNotFoundError: If the .stat file given does not exist.
    """
    return _energyplus_daily(epw, timesteps_per_hour, start_date, stat_file)[0]


def _metric(comfort_standard: int, comfort_mode: Optional[Number]) -> Optional[str]:
    """The running mean with which the setpoints of a comfort standard and comfort mode are calculated: RMOT or PMOT,
    as in their lines (or in its comfort temperature), or None (static setpoints)."""
    import re

    from accim.sim.ems import program_lines as pl
    from accim.sim.ems.setast import depends_on_comfort_mode, get_setpoint_lines, subprograms

    if comfort_mode is not None and depends_on_comfort_mode(comfort_standard):
        lines = get_setpoint_lines(comfort_standard, comfort_mode)
    else:
        lines = [line for program in subprograms([comfort_standard]).values() for line in program]
    for candidates in (lines, pl.for_comfort_standards(pl.set_comf_temp_lines(), [comfort_standard])):
        found = {name for name in ('RMOT', 'PMOT')
                 if any(re.search(rf'\b{name}\b', line) for line in candidates if not line.strip().startswith('!'))}
        if len(found) == 1:
            return found.pop()
    return None


@accepts_legacy_kwargs(DEPRECATED_ARGUMENT_NAMES, version='1.2.0')
def compute_setpoints(epw: PathLike, comfort_standard: int, category: Optional[Number] = None,
                      comfort_mode: Optional[Number] = None, *, timesteps_per_hour: int = 6,
                      start_date: Union[int, str] = 1, frequency: str = 'hourly', outdoor_metric_start: str = 'epw',
                      stat_file: Union[PathLike, None] = 'auto', **custom_arguments) -> pd.DataFrame:
    """The setpoints of the ACCIS for a comfort standard, category and comfort mode in each hour of a weather file,
    without EnergyPlus.

    The EMS programs of the output IDFs of :class:`accim.sim.accis.AddAccis` that calculate the setpoints
    (:func:`accim.utils.get_setpoint_ems_programs`, those that :func:`accim.utils.print_setpoint_ems_code` prints) run
    with the Erl interpreter of accim (:mod:`accim.sim.ems.erl`) in each timestep, as the program ``RunACCIS_<zone>`` of a
    zone runs them, with the running means of EnergyPlus (:func:`energyplus_running_means`, also those of the run
    periods that begin between the 2nd and the 30th of January, whose running mean of ASHRAE 55 takes the mean of 31
    December in place of that of the day before the run period, as EnergyPlus 25.1 does): at the first timestep of
    each day, the EMS still reads those of the previous day (and 0 at the first timestep of the run period), since its
    programs run before EnergyPlus calculates them, as in EnergyPlus 25.1. The hourly values are the means of those of
    the timesteps, as EnergyPlus reports the EMS outputs (``Averaged``), so they are those of the hourly EMS outputs of
    an output IDF simulated with the same weather file, run period and timesteps per hour.

    With the custom model (comfort standard 99) and an outdoor metric other than 'pmot' (``custom_outdoor_metric``),
    the programs of the outdoor metric (:mod:`accim.sim.ems.outdoor_metric`) also run in each timestep, with the outdoor
    temperature of EnergyPlus (interpolated between the hourly values of the weather file, which it has at the end of
    each hour; with 'te_ref_nl' and ``outdoor_metric_start`` 'epw', T0 is the mean of the maximum and minimum of the day
    of the weather file in all its timesteps, as the sensor of the Schedule:File object of the output IDFs gives it,
    :func:`accim.sim.ems.outdoor_metric.mid_range_values`), and so they do with JPN Aqilah 2025 (23) and
    ``outdoor_metric_start`` 'epw', whose running mean is then
    that of EN 16798-1 with α = 0.8 that the EMS calculates (as in the output IDFs of AddAccis with the weather file,
    :data:`accim.sim.ems.standard_lines.WEATHER_FILE_METRICS`), and with IND IMAC R 7DRM (9), whose outdoor metric is
    always the arithmetic mean of the 7 previous days that the EMS calculates
    (:data:`accim.sim.ems.standard_lines.BUILT_IN_METRICS`). With its regimes (``custom_regimes``), the program of
    the regimes (:mod:`accim.sim.ems.custom_regimes`) runs before SetAppLimits; their conditions 'hvac_off' and
    'hvac_on' depend on the HVAC system of the simulation, so they cannot be calculated without EnergyPlus.

    :param epw: The path of the weather file (EPW), of a whole year of 365 days, or of 366 with 29 February and without
        leap years in its header, whose rows are those of the dates of the simulated year of 365 days, without 29
        February, as in EnergyPlus (see :func:`energyplus_running_means`; T0 of 'te_ref_nl' too, which EnergyPlus reads
        from the Schedule:File object of 8784 hours by the dates of the simulated days). The initial values of the
        outdoor metrics that the EMS calculates from the weather file (``outdoor_metric_start`` 'epw') are those of the
        days before the run period by their position in the file (:func:`accim.sim.ems.outdoor_metric.initial_values`),
        as the output IDFs of AddAccis with the weather file have them.
    :param comfort_standard: The comfort standard (see :func:`accim.utils.get_setpoint_ems_code`).
    :param category: The category, which the comfort standards with categories need.
    :param comfort_mode: The comfort mode, which the comfort standards whose setpoints depend on it need.
    :param timesteps_per_hour: The number of timesteps per hour of the model (6 by default, as in EnergyPlus).
    :param start_date: The first day of the run period, a date 'dd/mm' or a day of the year (1, by default); the
        values go from that day to the end of the year.
    :param frequency: 'hourly' (by default) or 'timestep'.
    :param outdoor_metric_start: The values with which the outdoor metric of the custom model begins: 'epw' (by
        default), those of the weather file, as in the output IDFs of AddAccis with its argument ``epw``; 'pmot', the
        running mean of ASHRAE 55 of EnergyPlus, as in those without it. JPN Aqilah 2025 (23) reads, with 'epw', the
        running mean of EN 16798-1 with α = 0.8 that begins with the values of the weather file, and, with 'pmot', the
        RMOT of EnergyPlus, as the output IDFs of AddAccis with and without ``epw``. The mean of the 7 previous days of
        IND IMAC R 7DRM (9) begins with the values of the weather file ('epw') or with PMOT ('pmot').
    :param stat_file: The .stat file whose monthly means EnergyPlus takes as PMOT: 'auto' (the default), the one next to
        the weather file, if there is one; None, none; or its path (see :func:`energyplus_running_means`).
    :param custom_arguments: The other arguments of :func:`accim.utils.get_setpoint_ems_code` (``setpoint_tolerance``,
        ``setpoint_accuracy``, ``cooling_season_start``, ``custom_slope``, ``custom_outdoor_metric``,
        ``custom_regimes``, ``static_heating_setpoint``...), with the same defaults.
    :return: A DataFrame with a row for each hour (or timestep): ``datetime`` (the end of the hour or timestep, as
        EnergyPlus reports it), ``Tout`` (the outdoor dry-bulb temperature: that of the weather file, or that of
        EnergyPlus, interpolated, for each timestep), ``RMOT`` and ``PMOT`` (those of EnergyPlus for the day),
        ``Tout_metric`` (the one of them with which the setpoints are calculated, NaN for static setpoints; with the
        custom model and an outdoor metric other than 'pmot', or with IND IMAC R 7DRM, the one that its EMS programs
        calculate, as the outputs ``Tout_metric_<zone>``), ``ComfTemp`` (the comfort temperature), ``ACST`` and
        ``AHST`` (the cooling and
        heating setpoints, rounded with ``setpoint_accuracy``, which the EMS gives to the thermostats: the outputs
        *Adaptive Cooling Setpoint Temperature* and *Adaptive Heating Setpoint Temperature*), ``ACSTnoTol`` and
        ``AHSTnoTol`` (without the tolerance), ``applicable`` (1 if the running mean is within the applicability
        limits, as the hour counters of the ACCIS count it, at the end of the hour) and ``cooling_season`` (1 in the
        cooling season); with ``custom_regimes``, also ``custom_regime`` (the number of the regime, from 1, or 0 for the
        scalar arguments; the mean of the hour, as the output ``CustomRegime_<zone>``). Values that the programs do not
        set (such as the comfort temperature of static setpoints) are NaN. Its ``attrs`` have the arguments, the
        running mean of the setpoints (``metric``) and the .stat file read (``stat_file``, or None).
    :raises ValueError: If the arguments are not valid (as in :func:`accim.utils.get_setpoint_ems_programs` and
        :func:`energyplus_running_means`), a regime of ``custom_regimes`` has the condition 'hvac_off' or 'hvac_on', or
        ``drift_mode`` is given (the limiter of the drift depends on the indoor temperature of the simulation).
    """
    from accim.sim.arguments import check_custom_regimes
    from accim.sim.ems import custom_regimes as cr
    from accim.sim.ems import outdoor_metric as om
    from accim.sim.ems import program_lines as pl
    from accim.sim.ems.erl import ErlProgramSet, variables_in_programs
    from accim.sim.ems.standard_lines import (WEATHER_FILE_METRICS, built_in_metric, weather_file_definition,
                                              weather_file_lines)
    from accim.utils.ems_code import get_setpoint_ems_programs

    if frequency not in ('hourly', 'timestep'):
        raise ValueError(f"frequency must be 'hourly' or 'timestep', not {frequency!r}.")
    if outdoor_metric_start not in ('epw', 'pmot'):
        raise ValueError(f"outdoor_metric_start must be 'epw' or 'pmot', not {outdoor_metric_start!r}.")
    if cr.uses_hvac_conditions(check_custom_regimes(custom_arguments.get('custom_regimes'))):
        raise ValueError("compute_setpoints cannot evaluate the conditions 'hvac_off' and 'hvac_on' of custom_regimes: "
                         "they depend on the HVAC system of the simulation in the previous timestep.")
    if custom_arguments.get('drift_mode') is not None:
        raise ValueError('compute_setpoints cannot calculate the limiter of the drift of the setpoints (drift_mode): '
                         'it depends on the operative temperature and the occupants of the zone in the simulation.')
    programs = get_setpoint_ems_programs(comfort_standard, category, comfort_mode,
                                         epw=epw if outdoor_metric_start == 'epw' else None, start_date=start_date,
                                         **custom_arguments)
    # The records of the simulated year: those of 29 February are left out, as EnergyPlus does
    running_means, hourly, first = _energyplus_daily(epw, timesteps_per_hour, start_date, stat_file)
    temperatures = hourly['dry_bulb'].to_numpy(dtype=float).reshape(-1, 24)

    inputs = f'SetInputData_{_ZONE}'
    # The programs of the zone (SetInputData_<zone>, and the outdoor metric of the custom model)
    programs = {name.replace('<zone>', _ZONE): [line.replace('<zone>', _ZONE) for line in lines]
                for name, lines in programs.items()}
    # The custom model with an outdoor metric other than 'pmot' (accim.sim.ems.outdoor_metric), or JPN Aqilah 2025 with
    # the weather file (accim.sim.ems.standard_lines.WEATHER_FILE_METRICS)
    outdoor_metric = om.PROGRAM in programs
    weather_file = outdoor_metric and int(comfort_standard) in WEATHER_FILE_METRICS
    zone_metric = f'{om.ZONE_PROGRAM_PREFIX}{_ZONE}'
    # T0 of 'te_ref_nl' from the weather file: the Schedule Value of the Schedule:File object of each day (task H2)
    mid_ranges = None
    if any(om.MID_RANGE_SENSOR in line for line in programs.get(zone_metric, [])):
        mid_ranges = om.mid_range_values(epw)[::24]
        if len(mid_ranges) == 366:
            # A weather file with 29 February: the Schedule:File object has 8784 hours, of which EnergyPlus reads
            # those of the dates of the simulated year, without 29 February
            mid_ranges = mid_ranges[:59] + mid_ranges[60:]
    # The hour counters of the zone tell whether the running mean is within the applicability limits
    counter = f'CountHours_{_ZONE}'
    programs[counter] = weather_file_lines(counter, pl.format_lines(pl.count_hours_lines(outdoor_metric), zone=_ZONE),
                                           weather_file)
    names = set().union(*variables_in_programs(programs).values())
    erl = ErlProgramSet(programs, global_variables=names)
    order = ['SetAppLimits', 'ApplyCAT', 'SetComfTemp', 'SetAST', 'SetASTnoTol', counter]
    # The minimum and maximum of the setpoints of the zone (accim.sim.ems.setpoint_limits), right after SetASTnoTol
    limits = f'ApplySetpointLimits_{_ZONE}'
    if limits in programs:
        order.insert(order.index('SetASTnoTol') + 1, limits)
    # The regimes of the custom model (accim.sim.ems.custom_regimes), right before SetAppLimits
    regimes = f'{cr.PROGRAM_PREFIX}{_ZONE}'
    if regimes in programs:
        order.insert(0, regimes)
    # The programs that run in each timestep (those of the outdoor metric keep the daily values)
    every_timestep = [om.PROGRAM, inputs, zone_metric] if outdoor_metric else []
    if not outdoor_metric:
        order.insert(0, inputs)
    uses_time = 'CURRENTTIME' in names
    reported = _REPORTED + ((('Tout_metric', pl.OUTDOOR_METRIC_VARIABLE),) if outdoor_metric else ())
    if regimes in programs:
        reported += (('custom_regime', f'{cr.OUTPUT_PREFIX}{_ZONE}'),)

    n = timesteps_per_hour
    # InitASTvariables, at the beginning of the run period
    for name in ('ACST', 'AHST', 'ComfTemp'):
        erl.set(name, None)
    erl.set('CoolingSeason', 0)
    erl.set('ZoneTimeStep', 1 / n)
    erl.set(f'{_ZONE}_OpT', 0)
    file_hours = hourly['dry_bulb'].to_numpy(dtype=float)[24 * first:]
    if outdoor_metric:
        erl.set('WarmupFlag', 0)
        erl.run(om.INIT_PROGRAM)
        months = hourly['month'].to_numpy()[24 * first::24]
        # The outdoor temperature of each timestep, interpolated between the hourly values as in EnergyPlus (the
        # value of the weather file at the end of each hour); on the first day, from the last hour of the same day
        last_hours = np.r_[temperatures[first, 23], file_hours[:-1]]

    rmot_day = running_means['RMOT'].to_numpy()
    pmot_day = running_means['PMOT'].to_numpy()
    records: List[Tuple] = []
    previous_inputs = None
    previous_record: Tuple = ()
    for index in range(len(running_means)):
        day = first + index
        for hour in range(1, 25):
            for step in range(1, n + 1):
                if hour == 1 and step == 1:
                    rmot, pmot = (rmot_day[index - 1], pmot_day[index - 1]) if index else (0.0, 0.0)
                else:
                    rmot, pmot = rmot_day[index], pmot_day[index]
                current_time = hour - 1 + step / n
                tout_metric = None
                if outdoor_metric:
                    fraction = step / n
                    hour_index = 24 * index + hour - 1
                    erl.set('OutT', last_hours[hour_index] * (1 - fraction) + file_hours[hour_index] * fraction)
                    erl.set('RMOT', rmot)
                    erl.set('PMOT', pmot)
                    erl.set('DayOfYear', day + 1)
                    erl.set('Month', int(months[index]))
                    erl.set('Hour', hour - 1)
                    erl.set('TimeStepNum', step)
                    # The end of the timestep, in minutes of the hour (60 at the end of the hour)
                    erl.set('Minute', step * 60 / n)
                    if mid_ranges is not None:
                        erl.set(om.MID_RANGE_SENSOR, mid_ranges[day])
                    for program in every_timestep:
                        erl.run(program)
                    tout_metric = erl.get(pl.OUTDOOR_METRIC_VARIABLE)
                timestep_inputs = (rmot, pmot, tout_metric, day, current_time if uses_time else None)
                if timestep_inputs != previous_inputs:
                    # The programs give the same values with the same inputs
                    erl.set('RMOT', rmot)
                    erl.set('PMOT', pmot)
                    erl.set('DayOfYear', day + 1)
                    erl.set('CurrentTime', current_time)
                    for program in order:
                        erl.run(program)
                    values = [erl.get(variable) for _, variable in reported]
                    non_applicable = [erl.get(f'{name}_{_ZONE}')
                                      for name in ('DiscomfNonAppHotHours', 'DiscomfNonAppColdHours')]
                    previous_record = (*[np.nan if v is None else v for v in values],
                                       int(not any(non_applicable)), int(erl.get('CoolingSeason') or 0))
                    previous_inputs = timestep_inputs
                records.append(previous_record)

    columns = [column for column, _ in reported] + ['applicable', 'cooling_season']
    steps = pd.DataFrame.from_records(records, columns=columns)
    days = len(running_means)
    day_index = np.repeat(np.arange(days), 24 * n)
    if outdoor_metric:
        from accim.sim.standards import comfort_standard_definition

        definition = comfort_standard_definition(comfort_standard) or weather_file_definition(comfort_standard)
        if definition is not None:
            metric = definition.outdoor_metric
        elif built_in_metric(comfort_standard) is not None:
            # IND IMAC R 7DRM (9): the mean of the 7 previous days
            metric = built_in_metric(comfort_standard)[0]
        else:
            metric = om.metric_name(custom_arguments.get('custom_outdoor_metric', 'pmot'))
    else:
        metric = _metric(int(comfort_standard), comfort_mode)
    starts = hourly.iloc[24 * first:]
    hour_ends = (_dates(starts['month'].to_numpy(), starts['day'].to_numpy(), 365)
                 + pd.to_timedelta(starts['hour'].to_numpy(), unit='h'))
    averaged = [column for column, _ in reported]
    if frequency == 'timestep':
        # EnergyPlus interpolates the outdoor temperature between the hourly values (on the first day, from the last
        # hour of the same day)
        last = np.r_[temperatures[first, 23], file_hours[:-1]]
        fractions = np.tile(np.arange(1, n + 1) / n, len(file_hours))
        tout = np.repeat(last, n) + (np.repeat(file_hours, n) - np.repeat(last, n)) * fractions
        datetimes = ((hour_ends - pd.Timedelta(hours=1)).repeat(n)
                     + pd.to_timedelta(np.tile(np.arange(1, n + 1) * 60 // n, len(file_hours)), unit='min'))
        result = steps
        daily_rows = day_index
    else:
        groups = np.repeat(np.arange(len(file_hours)), n)
        result = steps[averaged].groupby(groups).mean()
        ends = steps[['applicable', 'cooling_season']].groupby(groups).last()
        result = pd.concat([result, ends], axis=1).reset_index(drop=True)
        tout = file_hours
        datetimes = hour_ends
        daily_rows = np.repeat(np.arange(days), 24)
    result.insert(0, 'datetime', np.asarray(datetimes))
    result.insert(1, 'Tout', tout)
    result.insert(2, 'RMOT', rmot_day[daily_rows])
    result.insert(3, 'PMOT', pmot_day[daily_rows])
    if outdoor_metric:
        result.insert(4, 'Tout_metric', result.pop('Tout_metric'))
    else:
        result.insert(4, 'Tout_metric', result[metric] if metric else np.nan)
    if 'custom_regime' in result:
        result['custom_regime'] = result.pop('custom_regime')
    result.attrs.update(comfort_standard=int(comfort_standard), category=category, comfort_mode=comfort_mode,
                        timesteps_per_hour=n, start_date=start_date, metric=metric,
                        stat_file=running_means.attrs['stat_file'])
    return result


def plot_setpoints(df: pd.DataFrame, ax=None):
    """Plot the setpoints of :func:`compute_setpoints`: the cooling and heating setpoints, the comfort temperature and
    the running mean with which they are calculated.

    :param df: The DataFrame of :func:`compute_setpoints`.
    :param ax: The matplotlib Axes to plot on; a new figure if None.
    :return: The Axes.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['datetime'], df['ACST'], color='tab:blue', linewidth=0.8, label='Cooling setpoint (ACST)')
    ax.plot(df['datetime'], df['AHST'], color='tab:red', linewidth=0.8, label='Heating setpoint (AHST)')
    if df['ComfTemp'].notna().any():
        ax.plot(df['datetime'], df['ComfTemp'], color='black', linewidth=0.6, linestyle='--',
                label='Comfort temperature')
    if df['Tout_metric'].notna().any():
        metric = df.attrs.get('metric') or 'Running mean'
        ax.plot(df['datetime'], df['Tout_metric'], color='tab:green', linewidth=0.8,
                label=f'Running mean outdoor temperature ({metric})')
    ax.set_ylabel('Temperature (°C)')
    ax.legend(loc='best', fontsize='small')
    return ax
