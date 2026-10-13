# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Hourly analysis and plotting for ACCIM parametric and optimisation results.

This module adds to ``ParametricSimulation`` and ``OptimisationSimulation``
(through :class:`HourlyPlottingMixin`) a set of methods to examine the hourly
outputs stored by the simulations and to screen every evaluation against an
hourly comfort criterion that does not need to be part of the control or of
the optimisation problem.

Data sources
------------
Hourly methods read the long hourly dataframe produced by
``get_hourly_df_parametric()`` / ``get_hourly_df_optimisation()``
(``df_source='parametric_hourly'`` or ``'optimisation_hourly'``), or any
dataframe with the same layout passed through ``df``: one row per hour and
simulation, an ``hour`` column (1..N within each simulation), the identifier
columns (parameters, ``epw``, ``idf``...) and one column per hourly output.

Evaluation-level methods read the table returned by
:meth:`HourlyPlottingMixin.compute_hourly_indicators` (stored in
``self.hourly_indicators``; ``df_source='hourly_indicators'``), the annual
results tables (``'parametric'``, ``'optimisation'``) or any dataframe with
one row per evaluation (``df``), for example several of them concatenated.

Variables
---------
Hourly variables are given as an exact column name or as a case-insensitive
substring of it (``'Zone Operative Temperature'``, ``'Electricity:HVAC'``).
When a substring matches several columns (for example the same variable in
several zones), ``zone_aggregation`` decides how they are combined. Energy
columns in J are converted to kWh per hour (or kWh/m² with
``normalize_per_m2=True``), using ``building_floor_area`` or ``floor_area``.

Main functions and methods
--------------------------
- :func:`adaptive_comfort_band`: lower and upper limits of EN 16798-1,
  ASHRAE 55 or user-defined adaptive models for any running mean.
- :func:`running_mean_outdoor_temperature`: EN 16798-1 or ASHRAE 55 running
  mean outdoor temperature from hourly outdoor temperatures or an EPW file.
- ``compute_hourly_indicators``: one row per evaluation with hourly-based
  indicators (temperature statistics, hours and degree-hours above/below
  each comfort category, energy totals and hourly peaks, operating hours,
  comfort outcome).
- ``plot_comfort_screening``: evaluations screened against a threshold of
  hours outside a comfort band, with non-dominated and selected solutions.
- ``plot_hourly_heatmaps``: day-by-hour maps of hourly variables.
- ``plot_hourly_period``: time series of a selected period (for example the
  week with the largest difference between two cases).
- ``plot_hourly_binned_response``: one hourly variable binned against
  another (energy signature).
- ``plot_load_duration_curves``: load-duration curves, optionally with an
  annual-versus-peak panel.
- ``plot_adaptive_comfort_chart``: hourly temperatures against the running
  mean, with the limits of an adaptive comfort model.
- ``plot_hourly_scatter_matrix`` and ``plot_results_scatter_matrix``: scatter
  matrices of hourly values or of evaluation-level results.
- ``plot_monthly_distributions``: monthly distributions (ridgelines) of an
  hourly variable, optionally with the monthly comfort band.

Every plotting method accepts ``data_filter`` (same rules as the rest of the
plotting API), returns the matplotlib figure (with ``saved_path`` and
``summary`` attributes) and saves a PNG in ``out_dir``.

Examples
--------
>>> ind = sim.compute_hourly_indicators(df_source='parametric', comfort_standard='EN16798-1')
>>> sim.plot_comfort_screening(df=ind, x='E_HVAC', y='share_outside_II', col='epw')
>>> sim.get_hourly_df_parametric(simulation_indices=[0, 1], output_columns=['Operative', 'Electricity:HVAC'])
>>> sim.plot_hourly_heatmaps(variables=['Zone Operative Temperature', 'Electricity:HVAC'], case=['ComfMod', 'HVACmode'])
"""

import os
import re
import warnings
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# ----------------------------------------------------------------------------- constants

MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_NAMES = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
               'October', 'November', 'December')
MONTH_INITIALS = ('J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D')

#: Colour-blind-safe qualitative palette (Okabe and Ito), used when no palette is given.
OKABE_ITO = ('#0072B2', '#E69F00', '#009E73', '#D55E00', '#56B4E9', '#CC79A7', '#F0E442', '#000000')

#: Adaptive comfort models available by name in :func:`adaptive_comfort_band`.
#: ``categories`` maps each category to (offset above, offset below) the comfort temperature, in K.
ADAPTIVE_COMFORT_MODELS = {
    'EN16798-1': {
        'slope': 0.33, 'intercept': 18.8, 'limits': (10.0, 30.0),
        'categories': {'I': (2.0, 3.0), 'II': (3.0, 4.0), 'III': (4.0, 5.0)},
        'running_mean': 'CEN 15251 Adaptive Model Running Average',
    },
    'ASHRAE55': {
        'slope': 0.31, 'intercept': 17.8, 'limits': (10.0, 33.5),
        'categories': {'90': (2.5, 2.5), '80': (3.5, 3.5)},
        'running_mean': 'ASHRAE 55 Adaptive Model Running Average',
    },
}
_MODEL_ALIASES = {
    'en16798-1': 'EN16798-1', 'en16798': 'EN16798-1', 'en 16798-1': 'EN16798-1', 'en15251': 'EN16798-1',
    'cen15251': 'EN16798-1', 'en': 'EN16798-1', 'ashrae55': 'ASHRAE55', 'ashrae 55': 'ASHRAE55',
    'ashrae': 'ASHRAE55',
}

#: Style applied by the hourly plotting methods (overridable with ``rc``).
DEFAULT_RC = {
    'font.size': 8, 'axes.titlesize': 8.5, 'axes.labelsize': 8, 'legend.fontsize': 7.5,
    'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': '#dddddd', 'grid.linewidth': 0.5,
}


# ----------------------------------------------------------------- comfort models and running mean

def _model_definition(standard: Union[str, dict]) -> dict:
    """Return the definition dictionary of a named or user-defined adaptive model."""
    if isinstance(standard, dict):
        model = dict(standard)
        missing = [k for k in ('slope', 'intercept') if k not in model]
        if missing:
            raise ValueError(f'Custom adaptive model needs the keys {missing} (and optionally limits and categories).')
        model.setdefault('limits', (-np.inf, np.inf))
        if 'categories' not in model:
            up = model.get('upper_offset', None)
            lo = model.get('lower_offset', up)
            if up is None:
                raise ValueError("Custom adaptive model needs 'categories' {name: (above, below)} or 'upper_offset'.")
            model['categories'] = {model.get('name', 'custom'): (float(up), float(lo))}
        return model
    key = _MODEL_ALIASES.get(str(standard).strip().lower(), str(standard).strip())
    if key not in ADAPTIVE_COMFORT_MODELS:
        raise ValueError(f"Unknown comfort standard '{standard}'. Use one of {list(ADAPTIVE_COMFORT_MODELS)}, "
                         'a dict (slope, intercept, limits, categories) or a callable.')
    return ADAPTIVE_COMFORT_MODELS[key]


def comfort_categories(standard: Union[str, dict, Callable] = 'EN16798-1') -> List[str]:
    """Names of the comfort categories of an adaptive model (``['I', 'II', 'III']`` for EN 16798-1)."""
    if callable(standard) and not isinstance(standard, dict):
        return ['custom']
    return [str(c) for c in _model_definition(standard)['categories']]


def adaptive_comfort_band(
        running_mean,
        standard: Union[str, dict, Callable] = 'EN16798-1',
        category: Optional[str] = None,
        applicability: Literal['clip', 'exclude', 'extend'] = 'clip',
) -> Tuple[np.ndarray, np.ndarray]:
    """Lower and upper limits of an adaptive comfort model for each running mean value.

    Parameters
    ----------
    running_mean : array-like
        Running mean outdoor temperature (°C), hourly or daily.
    standard : str, dict or callable
        ``'EN16798-1'`` (comfort temperature 0.33 Trm + 18.8 °C, categories I, II
        and III: +2/-3, +3/-4 and +4/-5 K, applicability 10-30 °C) or
        ``'ASHRAE55'`` (0.31 Trm + 17.8 °C, 90 % and 80 % acceptability: ±2.5 and
        ±3.5 K, applicability 10-33.5 °C). A dict defines another model with
        ``slope``, ``intercept``, optional ``limits`` (lower, upper) and either
        ``categories`` ({name: (above, below)}) or ``upper_offset`` /
        ``lower_offset``. A callable receives the running mean array and must
        return ``(lower, upper)``.
    category : str, optional
        Category to use; defaults to the middle category of the model (``'II'``
        for EN 16798-1, ``'80'`` for ASHRAE 55).
    applicability : {'clip', 'exclude', 'extend'}
        Outside the applicability limits, ``'clip'`` keeps the limits of the
        nearest applicable running mean (horizontal extension, as the adaptive
        setpoints of accim), ``'exclude'`` returns NaN and ``'extend'`` applies
        the linear relationship without limits.

    Returns
    -------
    tuple of numpy.ndarray
        ``(lower, upper)`` limits in °C, with the shape of ``running_mean``.

    Examples
    --------
    >>> lo, up = adaptive_comfort_band([15, 25], 'EN16798-1', 'II')
    """
    rm = np.asarray(running_mean, dtype=float)
    if callable(standard) and not isinstance(standard, dict):
        lower, upper = standard(rm)
        return np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)
    model = _model_definition(standard)
    cats = {str(k): v for k, v in model['categories'].items()}
    if category is None:
        names = list(cats)
        category = names[len(names) // 2] if len(names) > 1 else names[0]
    if str(category) not in cats:
        raise ValueError(f"Category '{category}' not defined for this model; available: {list(cats)}")
    above, below = cats[str(category)]
    lo_lim, up_lim = model.get('limits', (-np.inf, np.inf))
    if applicability not in ('clip', 'exclude', 'extend'):
        raise ValueError("applicability must be 'clip', 'exclude' or 'extend'.")
    t = rm if applicability == 'extend' else np.clip(rm, lo_lim, up_lim)
    comfort = model['slope'] * t + model['intercept']
    lower, upper = comfort - below, comfort + above
    if applicability == 'exclude':
        outside = (rm < lo_lim) | (rm > up_lim)
        lower = np.where(outside, np.nan, lower)
        upper = np.where(outside, np.nan, upper)
    return lower, upper


def read_epw_dry_bulb(epw_path: str) -> np.ndarray:
    """Hourly dry-bulb temperature (°C) of an EnergyPlus weather file (EPW)."""
    values = []
    with open(epw_path, 'r', encoding='latin-1') as handle:
        for n, line in enumerate(handle):
            if n < 8:
                continue
            fields = line.split(',')
            if len(fields) > 6:
                values.append(float(fields[6]))
    if not values:
        raise ValueError(f'No hourly records found in {epw_path}')
    return np.asarray(values, dtype=float)


def running_mean_outdoor_temperature(
        outdoor_temperature=None,
        epw_path: Optional[str] = None,
        method: Literal['en16798', 'ashrae55'] = 'en16798',
        alpha: float = 0.8,
        days: int = 30,
        hours_per_day: int = 24,
) -> np.ndarray:
    """Running mean outdoor temperature for each hour, from hourly outdoor temperatures.

    Parameters
    ----------
    outdoor_temperature : array-like, optional
        Hourly outdoor air temperatures of a whole number of days (for example
        8,760 values). Not needed if ``epw_path`` is given.
    epw_path : str, optional
        EPW file whose dry-bulb temperature is used instead.
    method : {'en16798', 'ashrae55'}
        ``'en16798'``: exponentially weighted running mean of EN 16798-1,
        Trm(d) = (1 - alpha) Ted(d-1) + alpha Trm(d-1). ``'ashrae55'``: simple
        mean of the daily means of the previous ``days`` days (7-30 in ASHRAE 55).
    alpha : float
        Weight of the previous running mean (0.8 recommended by EN 16798-1).
    days : int
        Number of previous days for ``'ashrae55'``.
    hours_per_day : int
        Records per day.

    Returns
    -------
    numpy.ndarray
        Running mean for each hour (constant within each day). The year is
        treated as periodic, so the first days use the end of the series, as
        for a weather file.

    Notes
    -----
    EnergyPlus reports its own running means (``Zone Thermal Comfort CEN 15251
    Adaptive Model Running Average Outdoor Air Temperature`` and the ASHRAE 55
    equivalent), which are the ones used by the adaptive setpoints of accim.
    Use those outputs when they are available; this function is meant for
    simulations that did not report them.
    """
    if outdoor_temperature is None:
        if epw_path is None:
            raise ValueError('Give outdoor_temperature or epw_path.')
        outdoor_temperature = read_epw_dry_bulb(epw_path)
    t = np.asarray(outdoor_temperature, dtype=float)
    if t.size % hours_per_day:
        raise ValueError(f'{t.size} values are not a whole number of days of {hours_per_day} records.')
    daily = t.reshape(-1, hours_per_day).mean(axis=1)
    n = daily.size
    if method == 'en16798':
        rm = np.empty(n)
        state = daily.mean()
        for _ in range(2):  # second pass starts from the end of the first: periodic year
            for d in range(n):
                prev = daily[d - 1]  # d = 0 uses the last day (periodic)
                state = (1 - alpha) * prev + alpha * state
                rm[d] = state
        rm_daily = rm
    elif method == 'ashrae55':
        ext = np.concatenate([daily[-days:], daily])
        csum = np.concatenate([[0.0], np.cumsum(ext)])
        rm_daily = (csum[days:days + n] - csum[0:n]) / days
    else:
        raise ValueError("method must be 'en16798' or 'ashrae55'.")
    return np.repeat(rm_daily, hours_per_day)


# ------------------------------------------------------------------------- generic helpers

def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _find_columns(columns: Sequence, spec: str) -> List[str]:
    """Columns matching ``spec``: exact name, case-insensitive name or case-insensitive substring."""
    cols = [str(c) for c in columns]
    if spec in cols:
        return [spec]
    low = str(spec).lower()
    exact = [c for c in cols if c.lower() == low]
    if exact:
        return exact
    return [c for c in cols if low in c.lower()]


def _pretty_name(column: str) -> str:
    """Readable name of an EnergyPlus output column ('ZONE:Zone Operative Temperature [C](Hourly)')."""
    name = re.sub(r'\((Hourly|TimeStep|Daily|Monthly|RunPeriod|Annual)\)', '', str(column))
    name = re.sub(r'\[[^\]]*\]', '', name).strip()
    name = re.sub(r'_kWh/m2$', '', name).strip()
    if ':' in name:
        head, tail = name.rsplit(':', 1)
        tail = tail.strip()
        if ' ' not in name:  # meter, e.g. Electricity:HVAC
            return name
        if tail.lower() == 'schedule value':
            return head.strip()
        return tail
    return name


def _column_unit(column: str) -> str:
    m = re.search(r'\[([^\]]*)\]', str(column))
    unit = m.group(1) if m else ''
    if str(column).endswith('_kWh/m2'):
        unit = 'kWh/m2'
    return {'C': '°C', 'kWh/m2': 'kWh/m²'}.get(unit, unit)


def _short_value(value) -> Any:
    """File names instead of paths (EPW and IDF values)."""
    if isinstance(value, str) and (('/' in value) or ('\\' in value) or value.lower().endswith(('.epw', '.idf'))):
        base = re.split(r'[\\/]+', value)[-1]
        return re.sub(r'\.(epw|idf)$', '', base, flags=re.I)
    return value


def _match_label(value, labels) -> Optional[str]:
    """Label of ``value`` in ``labels``.

    Keys are matched exactly first (numbers with tolerance, tuples element by
    element), then string keys (or string elements of tuple keys) as
    case-insensitive substrings of the values, so ``{'Present': 'Present'}``
    matches ``'Seville_Present.epw'``.
    """
    if labels is None:
        return None
    if callable(labels):
        return labels(value)
    if isinstance(value, tuple) and len(value) == 1:
        value = value[0]
    try:
        if value in labels:
            return labels[value]
    except TypeError:
        pass
    probe = value if isinstance(value, tuple) else (value,)
    for matcher in (_values_equal, _element_matches):
        for key, lab in labels.items():
            kt = key if isinstance(key, tuple) else (key,)
            if len(kt) == len(probe) and all(matcher(a, b) for a, b in zip(kt, probe)):
                return lab
    text = ' | '.join(str(v) for v in probe).lower()
    for key, lab in labels.items():
        if isinstance(key, str) and key.lower() in text:
            return lab
    return None


def _element_matches(key, value) -> bool:
    if _values_equal(key, value):
        return True
    if isinstance(key, str) and isinstance(value, str):
        return key.lower() in value.lower()
    return False


def _values_equal(a, b) -> bool:
    try:
        fa, fb = float(a), float(b)
        return bool(np.isclose(fa, fb))
    except (TypeError, ValueError):
        return str(a) == str(b)


def _group_labels(df: pd.DataFrame, by, labels=None, context: str = 'group') -> pd.Series:
    """One label per row from one or several columns (``by``), mapped with ``labels``."""
    cols = _as_list(by)
    if not cols:
        return pd.Series('all', index=df.index)
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f'{context}: columns {missing} not found. Available columns: {list(df.columns)}')
    keys = df[cols].apply(lambda r: tuple(r.values), axis=1) if len(cols) > 1 else df[cols[0]].map(lambda v: (v,))
    cache = {}

    def lab(k):
        if k not in cache:
            mapped = _match_label(k if len(k) > 1 else k[0], labels)
            if mapped is None:
                parts = [_short_value(v) for v in k]
                if len(cols) == 1:
                    mapped = str(parts[0])
                else:
                    mapped = ', '.join(f'{c}={p}' for c, p in zip(cols, parts))
            cache[k] = str(mapped)
        return cache[k]

    return keys.map(lab)


def _ordered(present: Sequence, order=None, labels=None) -> list:
    """Order of the labels in ``present``: ``order`` (labels or raw values) first, then the rest."""
    present = list(dict.fromkeys(present))
    if order is None:
        return present
    out = []
    for item in order:
        lab = str(item)
        if lab not in present and labels is not None:
            mapped = _match_label(item, labels)
            lab = str(mapped) if mapped is not None else lab
        if lab not in present:
            lab = str(_short_value(item))
        if lab in present and lab not in out:
            out.append(lab)
    return out


def _colours(names: Sequence, palette=None) -> dict:
    names = list(names)
    if isinstance(palette, dict):
        cyc = iter(OKABE_ITO * 4)
        return {n: palette.get(n, next(cyc)) for n in names}
    if isinstance(palette, str):
        cmap = plt.get_cmap(palette)
        return {n: cmap(i / max(1, len(names) - 1)) for i, n in enumerate(names)}
    seq = list(palette) if palette is not None else list(OKABE_ITO)
    return {n: seq[i % len(seq)] for i, n in enumerate(names)}


def _simulation_ids(df: pd.DataFrame) -> pd.Series:
    """Simulation number of each row of a long hourly dataframe (blocks of increasing ``hour``)."""
    if '_sim' in df.columns:
        return df['_sim']
    for col in ('hour', 'datetime'):
        if col in df.columns:
            values = pd.to_datetime(df[col]) if col == 'datetime' else pd.to_numeric(df[col])
            new_block = values.diff()
            starts = (new_block.isna()) | (new_block <= (pd.Timedelta(0) if col == 'datetime' else 0))
            return starts.cumsum().astype(int) - 1
    raise KeyError("The hourly dataframe needs an 'hour' or 'datetime' column to identify simulations.")


def _calendar(n_hours: int) -> pd.DataFrame:
    """Month, day of year and hour of day for each hourly record of a non-leap year (hour-ending records)."""
    h = np.arange(n_hours)
    hours_per_year = 8760
    doy = (h % hours_per_year) // 24 + 1
    month = np.searchsorted(np.cumsum(MONTH_DAYS), doy, side='left') + 1
    start = pd.Timestamp('2025-01-01 00:00')
    return pd.DataFrame({'month': month, 'day_of_year': doy, 'hour_of_day': h % 24,
                         'timestamp': start + pd.to_timedelta(h, unit='h')})


def _smooth(values, sigma: float):
    """Gaussian smoothing of a 1-D or 2-D histogram (numpy only)."""
    r = max(1, int(round(3 * sigma)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = np.asarray(values, dtype=float)
    for axis in range(out.ndim):
        out = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), axis, out)
    return out


def _hdr_contours(ax, x, y, xlim, ylim, colour, linestyle='-', levels=(0.5, 0.9), bins=70, sigma=1.4,
                  linewidths=(1.1, 0.6)):
    """Contours enclosing the densest fractions ``levels`` of the points (highest-density regions)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return
    h, xe, ye = np.histogram2d(x[ok], y[ok], bins=bins, range=[xlim, ylim])
    if h.sum() == 0:
        return
    h = _smooth(h, sigma)
    h /= h.sum()
    flat = np.sort(h.ravel())[::-1]
    cum = np.cumsum(flat)
    xc, yc = 0.5 * (xe[1:] + xe[:-1]), 0.5 * (ye[1:] + ye[:-1])
    for lv, lw in zip(levels, list(linewidths) + [linewidths[-1]] * len(levels)):
        thr = flat[min(np.searchsorted(cum, lv), len(flat) - 1)]
        if thr > 0 and h.max() > thr:
            ax.contour(xc, yc, h.T, levels=[thr], colors=[colour], linestyles=[linestyle], linewidths=[lw])


def _spearman(a, b) -> float:
    a = pd.Series(np.asarray(a, float))
    b = pd.Series(np.asarray(b, float))
    ok = a.notna() & b.notna()
    if ok.sum() < 3:
        return np.nan
    return a[ok].rank().corr(b[ok].rank())


def _limits(values, pad: float = 0.04) -> tuple:
    v = np.concatenate([np.asarray(x, float).ravel() for x in values]) if len(values) else np.array([0.0, 1.0])
    v = v[np.isfinite(v)]
    if v.size == 0:
        return (0.0, 1.0)
    a, b = float(v.min()), float(v.max())
    d = (b - a) or (abs(a) * 0.1 or 1.0)
    return (a - pad * d, b + pad * d)


def _free_spot(ax, target, points, size=(0.25, 0.085)):
    """Axes-fraction position for a label near ``target`` that covers the fewest plotted points."""
    tr = ax.transData + ax.transAxes.inverted()
    pts = np.asarray(points, float).reshape(-1, 2)
    pts = pts[np.isfinite(pts).all(axis=1)]
    p = tr.transform(pts) if len(pts) else np.empty((0, 2))
    t = tr.transform([target])[0]
    w, h = size
    best, best_key = (0.5, 0.9), None
    for cx in np.linspace(w / 2 + 0.02, 1 - w / 2 - 0.02, 30):
        for cy in np.linspace(h / 2 + 0.04, 1 - h / 2 - 0.04, 30):
            if abs(t[0] - cx) < w / 2 + 0.03 and abs(t[1] - cy) < h / 2 + 0.05:
                continue
            inside = int(((np.abs(p[:, 0] - cx) < w / 2 + 0.02) & (np.abs(p[:, 1] - cy) < h / 2 + 0.03)).sum())
            key = (inside, round(float(np.hypot(cx - t[0], (cy - t[1]) * 1.3)), 3))
            if best_key is None or key < best_key:
                best, best_key = (cx, cy), key
    return best


def _panel_letter(i: int) -> str:
    letters = 'abcdefghijklmnopqrstuvwxyz'
    return letters[i] if i < len(letters) else f'{letters[i // 26 - 1]}{letters[i % 26]}'


def _match_rows(data: pd.DataFrame, rows: pd.DataFrame, match_on=None, parameter_names=None, exclude=()) -> np.ndarray:
    """Rows of ``data`` that correspond to the rows of ``rows`` (for example selected solutions).

    Matching uses ``match_on`` if given; otherwise the simulation path columns
    shared by both tables (``simulation_output_csv_path``, ``simulation_directory``,
    ``output_dir``), else the parameter columns (and ``epw``), else every shared
    column except ``exclude``. Numbers are compared with tolerance and NaN equals NaN.
    """
    shared = [c for c in rows.columns if c in data.columns and c not in exclude and c != '_orig_index']
    if match_on is not None:
        keys = list(match_on)
    else:
        path_cols = [c for c in ('simulation_output_csv_path', 'simulation_directory', 'output_dir') if c in shared]
        if path_cols:
            keys = path_cols[:1]
        elif parameter_names:
            keys = [c for c in shared if c in parameter_names] + [c for c in ('epw',) if c in shared]
        else:
            keys = shared
    if not keys:
        raise ValueError('No columns to match the selected rows; pass match_on.')
    mask = np.zeros(len(data), bool)
    for _, r in rows.iterrows():
        m = np.ones(len(data), bool)
        for k in keys:
            col = data[k]
            val = r[k]
            if k in ('simulation_output_csv_path', 'simulation_directory', 'output_dir'):
                norm = col.astype(str).str.replace('\\', '/', regex=False).str.rstrip('/').str.lower()
                target = str(val).replace('\\', '/').rstrip('/').lower()
                m = m & (norm == target).to_numpy()
            elif pd.api.types.is_numeric_dtype(col) and not pd.api.types.is_bool_dtype(col):
                num = pd.to_numeric(col, errors='coerce').to_numpy(float)
                if pd.isna(val):
                    m = m & np.isnan(num)
                else:
                    m = m & np.isclose(num, float(val))
            else:
                m = m & (col.map(lambda v: str(_short_value(v))) == str(_short_value(val))).to_numpy()
        mask = mask | m
    return mask


# ------------------------------------------------------------------------------ the mixin

class HourlyPlottingMixin:
    """Hourly analysis, comfort screening and hourly plots for simulation classes.

    The methods work on the outputs already stored by a parametric or
    optimisation run (nothing is simulated) and are inherited by
    ``ParametricSimulation`` and ``OptimisationSimulation``. They can also be
    used on dataframes passed through ``df``.

    Examples
    --------
    >>> ind = sim.compute_hourly_indicators(df_source='parametric')
    >>> sim.plot_comfort_screening(df=ind, x='E_HVAC', y='share_outside_II')
    """

    # ---------------------------------------------------------------- data access helpers

    def _hp_source(
            self,
            df: Optional[pd.DataFrame],
            df_source: Optional[str],
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: str = 'error',
            context: str = 'hourly plot',
    ) -> pd.DataFrame:
        """Copy of the requested dataframe after ``data_filter``."""
        if df is not None:
            data = df.copy()
        elif df_source in ('hourly_indicators', 'indicators'):
            data = getattr(self, 'hourly_indicators', None)
            if data is None or len(data) == 0:
                raise ValueError('No hourly indicators found. Run compute_hourly_indicators() first or pass df.')
            data = data.copy()
        elif hasattr(self, '_get_plot_source_df'):
            data = self._get_plot_source_df(df_source=df_source)
        else:
            raise ValueError('Pass a dataframe through df.')
        if data_filter is not None:
            if hasattr(self, '_apply_plot_data_filter'):
                data, _ = self._apply_plot_data_filter(
                    df=data, data_filter=data_filter, data_filter_case_sensitive=data_filter_case_sensitive,
                    data_filter_strict=data_filter_strict, data_filter_on_empty=data_filter_on_empty,
                    context=context)
            else:  # standalone use
                from accim.parametric_and_optimisation.utils import apply_data_filter
                data, _ = apply_data_filter(df=data, data_filter=data_filter, case_sensitive=data_filter_case_sensitive,
                                            strict=data_filter_strict, on_empty=data_filter_on_empty, context=context)
        if data.empty:
            raise ValueError(f'{context}: no rows to plot after filtering.')
        return data

    def _hp_floor_area(self, data: pd.DataFrame, floor_area=None):
        """Floor area (float or Series aligned with ``data``) for per-m² values, or None."""
        area = floor_area if floor_area is not None else getattr(self, 'building_floor_area', None)
        if area is None:
            return None
        if isinstance(area, dict):
            if 'idf' in data.columns:
                mapped = data['idf'].map(lambda v: _match_label(v, area))
                if mapped.isna().any() and len(area) == 1:
                    mapped = mapped.fillna(list(area.values())[0])
                return pd.to_numeric(mapped, errors='coerce')
            return float(list(area.values())[0])
        return float(area)

    @staticmethod
    def _hp_series(data: pd.DataFrame, spec, zone_aggregation: str = 'mean', context: str = '') -> Tuple[pd.Series, str]:
        """Values of an hourly variable given by name or substring; several matches are aggregated."""
        if isinstance(spec, pd.Series):
            return spec, str(spec.name)
        cols = _find_columns(data.columns, str(spec))
        if not cols:
            raise KeyError(f"{context}: no column matches '{spec}'. Some available columns: "
                           f"{[c for c in data.columns][:25]}")
        if len(cols) == 1:
            return pd.to_numeric(data[cols[0]], errors='coerce'), cols[0]
        if zone_aggregation in (None, 'error'):
            raise KeyError(f"{context}: '{spec}' matches several columns {cols}; give the exact name or zone_aggregation.")
        block = data[cols].apply(pd.to_numeric, errors='coerce')
        if zone_aggregation == 'first':
            return block.iloc[:, 0], cols[0]
        return getattr(block, zone_aggregation)(axis=1), cols[0]

    def _hp_values(self, data: pd.DataFrame, spec, zone_aggregation='mean', energy_unit='kWh',
                   normalize_per_m2=False, floor_area=None, context='') -> Tuple[np.ndarray, str, str]:
        """(values, unit, default label) of a variable, with energy in J converted to kWh (per m² if asked)."""
        s, col = self._hp_series(data, spec, zone_aggregation, context)
        unit = _column_unit(col)
        values = s.to_numpy(dtype=float)
        if unit == 'J':
            if energy_unit == 'J':
                pass
            else:
                values = values / (3.6e6 if energy_unit == 'kWh' else 3.6e3)
                unit = energy_unit
                if normalize_per_m2:
                    area = self._hp_floor_area(data, floor_area)
                    if area is None:
                        warnings.warn('normalize_per_m2=True but no floor area is set; values left per building.')
                    else:
                        values = values / (area.to_numpy(float) if isinstance(area, pd.Series) else area)
                        unit = f'{energy_unit}/m²'
        name = _pretty_name(col)
        label = f'{name} ({unit})' if unit else name
        return values, unit, label

    @staticmethod
    def _hp_save(owner, fig, out_dir: str, filename: Optional[str], filename_template: Optional[str],
                 default_filename: str, context: str, template_context: Optional[dict] = None, dpi: int = 300,
                 close: bool = True):
        """Save ``fig`` with the filename rules of the plotting API and return the path."""
        if filename is not None and filename_template is not None:
            raise ValueError(f'{context}: use either filename or filename_template, not both.')
        os.makedirs(out_dir or '.', exist_ok=True)
        if filename is not None:
            path = os.path.join(out_dir, filename if filename.lower().endswith(('.png', '.pdf', '.svg', '.jpg'))
                                else f'{filename}.png')
        elif hasattr(owner, '_resolve_output_filename'):
            ctx = {}
            for k, v in (template_context or {}).items():
                ctx[str(k)] = owner._safe_plot_token(v) if hasattr(owner, '_safe_plot_token') else str(v)
            path = owner._resolve_output_filename(out_dir=out_dir, default_filename=default_filename,
                                                  filename_template=filename_template, template_context=ctx,
                                                  context=context)
        else:
            name = filename_template.format(**(template_context or {})) if filename_template else default_filename
            path = os.path.join(out_dir, name if name.lower().endswith('.png') else f'{name}.png')
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        fig.savefig(path, dpi=dpi, bbox_inches='tight')
        fig.saved_path = path
        print(f'  {context} saved: {path}')
        if close:
            plt.close(fig)
        return path

    # ------------------------------------------------------------- reading simulation files

    @staticmethod
    def _hp_relocate(path: str, path_replacements: Optional[dict]) -> str:
        """Apply ``{old_prefix: new_prefix}`` replacements to a stored path (moved result folders)."""
        if not path_replacements:
            return path
        norm = str(path).replace('\\', '/')
        for old, new in path_replacements.items():
            o = str(old).replace('\\', '/').rstrip('/')
            if norm.lower().startswith(o.lower()):
                rest = norm[len(o):].lstrip('/')
                return os.path.join(str(new), *rest.split('/'))
        return path

    def _hp_csv_path(self, row: pd.Series, path_replacements: Optional[dict] = None) -> str:
        if hasattr(self, '_resolve_simulation_file_path'):
            path = self._resolve_simulation_file_path(row=row, file_source='csv')
        elif pd.notna(row.get('simulation_output_csv_path', np.nan)):
            path = str(row['simulation_output_csv_path'])
        elif pd.notna(row.get('simulation_directory', np.nan)):
            path = os.path.join(str(row['simulation_directory']), 'eplusout.csv')
        elif pd.notna(row.get('output_dir', np.nan)):
            path = os.path.join(str(row['output_dir']), 'eplusout.csv')
        else:
            raise ValueError('The results row has no simulation path (simulation_output_csv_path, '
                             'simulation_directory or output_dir).')
        return self._hp_relocate(path, path_replacements)

    @staticmethod
    def _hp_read_csv_columns(path: str, specs: Sequence[str]) -> pd.DataFrame:
        """Read only the columns of an EnergyPlus CSV that match ``specs`` (names or substrings)."""
        header = pd.read_csv(path, nrows=0).columns
        wanted = []
        for spec in specs:
            wanted += [c for c in _find_columns(header, spec) if c not in wanted]
        if not wanted:
            return pd.DataFrame(index=pd.RangeIndex(0))
        # skip_blank_lines=False keeps every record aligned (EnergyPlus CSV files have no blank lines)
        return pd.read_csv(path, usecols=wanted, skip_blank_lines=False)

    # -------------------------------------------------------------------- indicators

    def compute_hourly_indicators(
            self,
            df_source: str = 'parametric',
            df: Optional[pd.DataFrame] = None,
            temperature: str = 'Zone Operative Temperature',
            running_mean: Union[str, dict, None] = 'auto',
            running_mean_method: Literal['en16798', 'ashrae55'] = 'en16798',
            outdoor_temperature: Optional[str] = 'Outdoor Air Drybulb Temperature',
            comfort_standard: Union[str, dict, Callable] = 'EN16798-1',
            categories: Optional[Sequence[str]] = None,
            applicability: Literal['clip', 'exclude', 'extend'] = 'clip',
            energy: Optional[dict] = None,
            normalize_per_m2: bool = True,
            floor_area: Optional[Union[float, dict]] = None,
            cooling_rate: Optional[str] = 'Cooling Coil Total Cooling Rate',
            heating_rate: Optional[str] = 'Heating Coil Heating Rate',
            temperature_thresholds: Sequence[float] = (),
            occupied: Optional[Union[str, Callable, np.ndarray]] = None,
            outcome_category: Optional[str] = None,
            max_share_outside: float = 0.05,
            zone_aggregation: str = 'mean',
            path_replacements: Optional[dict] = None,
            epw_files: Optional[dict] = None,
            keep_columns: Optional[Sequence[str]] = None,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            store: bool = True,
            verbose: bool = True,
    ) -> pd.DataFrame:
        """One row per evaluation with indicators computed from its hourly outputs.

        The indicators do not need to be outputs or objectives of the original
        study: they are calculated after simulation from the stored hourly
        values, so the same evaluations can be screened against any adaptive
        comfort criterion.

        Parameters
        ----------
        df_source : str
            ``'parametric'`` or ``'optimisation'`` reads the CSV file of every
            evaluation listed in the results table (one at a time, so the whole
            campaign can be processed without expanding it hourly);
            ``'parametric_hourly'`` or ``'optimisation_hourly'`` uses the long
            hourly dataframe already built with ``get_hourly_df_*``.
        df : pandas.DataFrame, optional
            Results table (one row per evaluation, with simulation paths) or
            long hourly dataframe to use instead of ``df_source``.
        temperature : str
            Indoor temperature evaluated against the comfort band (name or
            substring; several zones are combined with ``zone_aggregation``).
        running_mean : str, dict or None
            Running mean outdoor temperature: a column (name or substring);
            ``'auto'`` (the EnergyPlus running mean of the comfort standard, or
            the calculation from ``outdoor_temperature`` / the EPW file when the
            simulation did not report it); ``'compute'`` (always calculated with
            ``running_mean_method``); a dict ``{epw: hourly values}`` (EPW names or
            substrings), for example from :meth:`get_hourly_series_by_epw`; or
            None to skip the comfort indicators.
        running_mean_method : {'en16798', 'ashrae55'}
            Method of :func:`running_mean_outdoor_temperature` when it is calculated.
        outdoor_temperature : str, optional
            Hourly outdoor temperature column used to calculate the running mean.
            If absent, the EPW file of the evaluation is read (``epw`` column or
            ``epw_files``).
        comfort_standard : str, dict or callable
            Adaptive model of :func:`adaptive_comfort_band`.
        categories : sequence of str, optional
            Categories evaluated (default: all categories of the model).
        applicability : {'clip', 'exclude', 'extend'}
            Treatment of running means outside the applicability limits.
        energy : dict, optional
            ``{name: column}`` energy outputs to total; default
            ``{'E_HVAC': 'Electricity:HVAC'}``. Values in J are reported in kWh
            (kWh/m² with ``normalize_per_m2``); ``{name}_peak`` and ``{name}_p99``
            give the hourly maximum and 99th percentile in kWh.
        normalize_per_m2 : bool
            Divide annual energy totals by the floor area (``building_floor_area``
            or ``floor_area``).
        floor_area : float or dict, optional
            Floor area in m² (or ``{idf: area}``) overriding ``building_floor_area``.
        cooling_rate, heating_rate : str, optional
            Coil outputs used to count the hours with cooling, heating or neither
            (None to skip).
        temperature_thresholds : sequence of float
            Absolute temperatures for ``hours_above_{t}`` (for example 28 and 30).
        occupied : str, callable or array, optional
            Hours to evaluate: a column (hours with values > 0, for example an
            occupancy schedule), a function of a calendar dataframe (``month``,
            ``day_of_year``, ``hour_of_day``) returning a boolean mask, or a boolean
            array. Default: every hour.
        outcome_category : str, optional
            Category used to classify each evaluation as ``'meets'`` (share of
            hours outside the band <= ``max_share_outside``), ``'too warm'`` or
            ``'too cool'`` (most hours outside the band above or below it).
            Default: the middle category.
        max_share_outside : float
            Tolerance for the outcome classification (0.05 = 5 % of the hours).
        zone_aggregation : {'mean', 'max', 'min', 'sum', 'first'}
            How several matching columns are combined.
        path_replacements : dict, optional
            ``{old_prefix: new_prefix}`` for result folders moved after simulation.
        epw_files : dict, optional
            ``{epw: path}`` of the weather files, when the ``epw`` column does not
            hold a readable path.
        keep_columns : sequence of str, optional
            Result columns copied to the output (default: every scalar column).
        data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Row filter applied to the source dataframe before processing.
        store : bool
            Keep the result in ``self.hourly_indicators``.
        verbose : bool
            Print progress.

        Returns
        -------
        pandas.DataFrame
            One row per evaluation: the result columns, ``T_mean``, ``T_min``,
            ``T_p05``, ``T_p50``, ``T_p95``, ``T_max``, ``hours_above_{t}``,
            ``share_above_{c}``, ``share_below_{c}``, ``share_outside_{c}``,
            ``Kh_above_{c}``, ``Kh_below_{c}`` and ``Kh_outside_{c}`` (degree-hours)
            for each category ``c``, the energy totals and peaks, ``hours_cooling``,
            ``hours_heating``, ``hours_idle``, ``n_hours`` and ``comfort_outcome``.
            ``attrs['units']`` gives the units and ``attrs['comfort']`` the settings.

        Examples
        --------
        >>> ind = sim.compute_hourly_indicators(df_source='optimisation', comfort_standard='EN16798-1',
        ...                                     energy={'E_HVAC': 'Electricity:HVAC'}, temperature_thresholds=[28])
        >>> ind[['E_HVAC', 'share_outside_II', 'comfort_outcome']].head()
        """
        energy = {'E_HVAC': 'Electricity:HVAC'} if energy is None else dict(energy)
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, context='compute_hourly_indicators')
        if callable(comfort_standard) and not isinstance(comfort_standard, dict):
            cats = ['custom']
        else:
            cats = [str(c) for c in (categories or comfort_categories(comfort_standard))]
        outcome_cat = str(outcome_category) if outcome_category is not None else (cats[len(cats) // 2] if cats else None)
        if running_mean is not None and outcome_cat not in cats:
            cats.append(outcome_cat)
        model_rm = None
        if not callable(comfort_standard) or isinstance(comfort_standard, dict):
            try:
                model_rm = _model_definition(comfort_standard).get('running_mean')
            except ValueError:
                model_rm = None
        epw_cache = {}

        def rm_for(frame: pd.DataFrame, epw_value) -> Optional[np.ndarray]:
            if running_mean is None:
                return None
            if isinstance(running_mean, dict):
                key = _match_label(epw_value, {k: k for k in running_mean})
                if key is None:
                    raise KeyError(f'running_mean has no entry for epw {epw_value!r}; keys: {list(running_mean)}')
                return np.asarray(running_mean[key], dtype=float)
            if running_mean not in ('auto', 'compute'):
                return self._hp_series(frame, running_mean, 'first', 'running_mean')[0].to_numpy(float)
            if running_mean == 'auto' and model_rm is not None and _find_columns(frame.columns, model_rm):
                return self._hp_series(frame, model_rm, 'first', 'running_mean')[0].to_numpy(float)
            if outdoor_temperature is not None and _find_columns(frame.columns, outdoor_temperature):
                tout = self._hp_series(frame, outdoor_temperature, 'first', 'outdoor_temperature')[0]
                return running_mean_outdoor_temperature(tout.to_numpy(float), method=running_mean_method)
            path = None
            if epw_files:
                key = _match_label(epw_value, {k: k for k in epw_files})
                path = epw_files.get(key) if key is not None else None
            if path is None and isinstance(epw_value, str):
                path = self._hp_relocate(epw_value, path_replacements)
            if path is None or not os.path.exists(str(path)):
                raise FileNotFoundError(
                    f'Running mean not available for epw {epw_value!r}: the simulation does not report it, '
                    'there is no outdoor temperature column and the EPW file was not found. '
                    'Pass running_mean as a dict, epw_files or path_replacements.')
            if path not in epw_cache:
                epw_cache[path] = running_mean_outdoor_temperature(epw_path=path, method=running_mean_method)
            return epw_cache[path]

        def indicators_of(frame: pd.DataFrame, epw_value, area) -> dict:
            out = {}
            n = len(frame)
            cal = _calendar(n)
            if occupied is None:
                mask = np.ones(n, bool)
            elif callable(occupied):
                mask = np.asarray(occupied(cal), bool)
            elif isinstance(occupied, str):
                mask = self._hp_series(frame, occupied, 'max', 'occupied')[0].to_numpy(float) > 0
            else:
                mask = np.asarray(occupied, bool)
            out['n_hours'] = int(mask.sum())
            t = self._hp_series(frame, temperature, zone_aggregation, 'temperature')[0].to_numpy(float)
            tm = t[mask]
            out.update({'T_mean': np.nanmean(tm), 'T_min': np.nanmin(tm), 'T_p05': np.nanpercentile(tm, 5),
                        'T_p50': np.nanpercentile(tm, 50), 'T_p95': np.nanpercentile(tm, 95), 'T_max': np.nanmax(tm)})
            for thr in temperature_thresholds:
                out[f'hours_above_{thr:g}'] = int((tm > thr).sum())
            rm = rm_for(frame, epw_value)
            if rm is not None:
                if len(rm) != n:
                    raise ValueError(f'running mean has {len(rm)} values but the simulation has {n} hours.')
                for c in cats:
                    lower, upper = adaptive_comfort_band(rm, comfort_standard, None if c == 'custom' else c,
                                                         applicability)
                    lo, up = lower[mask], upper[mask]
                    valid = np.isfinite(lo) & np.isfinite(up) & np.isfinite(tm)
                    above = np.where(valid, np.clip(tm - up, 0, None), 0.0)
                    below = np.where(valid, np.clip(lo - tm, 0, None), 0.0)
                    nv = max(int(valid.sum()), 1)
                    out[f'share_above_{c}'] = float((above > 0).sum() / nv)
                    out[f'share_below_{c}'] = float((below > 0).sum() / nv)
                    out[f'share_outside_{c}'] = float(((above > 0) | (below > 0)).sum() / nv)
                    out[f'Kh_above_{c}'] = float(above.sum())
                    out[f'Kh_below_{c}'] = float(below.sum())
                    out[f'Kh_outside_{c}'] = float(above.sum() + below.sum())
                if outcome_cat is not None:
                    share = out[f'share_outside_{outcome_cat}']
                    if share <= max_share_outside:
                        out['comfort_outcome'] = 'meets'
                    elif out[f'share_above_{outcome_cat}'] >= out[f'share_below_{outcome_cat}']:
                        out['comfort_outcome'] = 'too warm'
                    else:
                        out['comfort_outcome'] = 'too cool'
            for name, spec in energy.items():
                s, col = self._hp_series(frame, spec, 'sum', f'energy {name}')
                unit = _column_unit(col)
                e = s.to_numpy(float)
                e_kwh = e / 3.6e6 if unit == 'J' else e
                total = np.nansum(e_kwh[mask])
                if normalize_per_m2 and area is not None:
                    total = total / area
                out[name] = float(total)
                out[f'{name}_peak'] = float(np.nanmax(e_kwh[mask]))
                out[f'{name}_p99'] = float(np.nanpercentile(e_kwh[mask], 99))
            cool = heat = None
            if cooling_rate and _find_columns(frame.columns, cooling_rate):
                cool = self._hp_series(frame, cooling_rate, 'sum', 'cooling_rate')[0].to_numpy(float)[mask]
                out['hours_cooling'] = int((cool > 0).sum())
            if heating_rate and _find_columns(frame.columns, heating_rate):
                heat = self._hp_series(frame, heating_rate, 'sum', 'heating_rate')[0].to_numpy(float)[mask]
                out['hours_heating'] = int((heat > 0).sum())
            if cool is not None or heat is not None:
                idle = np.ones(int(mask.sum()), bool)
                if cool is not None:
                    idle &= cool <= 0
                if heat is not None:
                    idle &= heat <= 0
                out['hours_idle'] = int(idle.sum())
            return out

        rows = []
        is_hourly = 'hour' in data.columns and len(data) > data['hour'].nunique()
        if is_hourly:
            sim = _simulation_ids(data)
            id_cols = [c for c in data.columns if c not in ('hour', 'datetime', '_sim')
                       and data.groupby(sim)[c].nunique(dropna=False).max() <= 1]
            if keep_columns is not None:
                id_cols = [c for c in keep_columns if c in data.columns]
            groups = list(data.groupby(sim, sort=True))
            for k, (sid, frame) in enumerate(groups):
                first = frame.iloc[0]
                area = None
                if normalize_per_m2:
                    a = self._hp_floor_area(frame.iloc[:1], floor_area)
                    area = float(a.iloc[0]) if isinstance(a, pd.Series) else a
                row = {c: first[c] for c in id_cols}
                row.update(indicators_of(frame.reset_index(drop=True), first.get('epw', None), area))
                rows.append(row)
                if verbose and (k + 1) % 50 == 0:
                    print(f'  [compute_hourly_indicators] {k + 1}/{len(groups)} simulations')
        else:
            scalar = [c for c in data.columns if not data[c].map(lambda v: isinstance(v, (list, tuple, np.ndarray))).any()]
            id_cols = [c for c in (keep_columns if keep_columns is not None else scalar) if c in data.columns]
            specs = [temperature] + list(energy.values())
            for extra in (running_mean if isinstance(running_mean, str) and running_mean not in ('auto', 'compute') else None,
                          model_rm if running_mean == 'auto' else None, outdoor_temperature, cooling_rate, heating_rate,
                          occupied if isinstance(occupied, str) else None):
                if extra:
                    specs.append(extra)
            n_rows = len(data)
            for k, (idx, r) in enumerate(data.iterrows()):
                path = self._hp_csv_path(r, path_replacements)
                if not os.path.exists(path):
                    raise FileNotFoundError(f'Simulation CSV not found: {path}. Use path_replacements if the '
                                            'results folder was moved.')
                frame = self._hp_read_csv_columns(path, specs)
                area = None
                if normalize_per_m2:
                    a = self._hp_floor_area(data.loc[[idx]], floor_area)
                    area = float(a.iloc[0]) if isinstance(a, pd.Series) else a
                row = {c: r[c] for c in id_cols}
                row.update(indicators_of(frame, r.get('epw', None), area))
                rows.append(row)
                if verbose and ((k + 1) % 100 == 0 or k + 1 == n_rows):
                    print(f'  [compute_hourly_indicators] {k + 1}/{n_rows} simulations')
        result = pd.DataFrame(rows)
        units = {'T_mean': '°C', 'T_min': '°C', 'T_p05': '°C', 'T_p50': '°C', 'T_p95': '°C', 'T_max': '°C'}
        for c in cats:
            units.update({f'share_above_{c}': '-', f'share_below_{c}': '-', f'share_outside_{c}': '-',
                          f'Kh_above_{c}': 'K·h', f'Kh_below_{c}': 'K·h', f'Kh_outside_{c}': 'K·h'})
        for name in energy:
            units[name] = 'kWh/m²' if normalize_per_m2 and self._hp_floor_area(data.iloc[:1], floor_area) is not None else 'kWh'
            units[f'{name}_peak'] = 'kWh'
            units[f'{name}_p99'] = 'kWh'
        result.attrs['units'] = units
        result.attrs['comfort'] = {'standard': comfort_standard if isinstance(comfort_standard, (str, dict)) else 'callable',
                                   'categories': cats, 'applicability': applicability,
                                   'outcome_category': outcome_cat, 'max_share_outside': max_share_outside}
        if store:
            self.hourly_indicators = result
        return result

    def get_hourly_series_by_epw(
            self,
            variable: str,
            df_source: str = 'parametric_hourly',
            df: Optional[pd.DataFrame] = None,
            path_replacements: Optional[dict] = None,
    ) -> Dict[str, np.ndarray]:
        """Hourly values of a weather-dependent variable for each weather file.

        Useful to reuse the running mean or the outdoor temperature reported by
        one simulation in analyses of simulations that did not report them (they
        depend only on the weather file).

        Parameters
        ----------
        variable : str
            Column name or substring (for example ``'CEN 15251 Adaptive Model
            Running Average'``).
        df_source : str
            Long hourly dataframe (``'parametric_hourly'``...) or results table
            (``'parametric'``, ``'optimisation'``: the first simulation file of
            each EPW is read).
        df : pandas.DataFrame, optional
            Dataframe used instead of ``df_source``.
        path_replacements : dict, optional
            ``{old_prefix: new_prefix}`` for moved result folders.

        Returns
        -------
        dict
            ``{epw name: numpy array}`` (EPW file names without extension).

        Examples
        --------
        >>> rm = sim_ex1.get_hourly_series_by_epw('CEN 15251 Adaptive Model Running Average', df_source='parametric')
        >>> ind3 = sim_ex3.compute_hourly_indicators(df_source='parametric', running_mean=rm)
        """
        data = self._hp_source(df, df_source, context='get_hourly_series_by_epw')
        if 'epw' not in data.columns:
            raise KeyError("The dataframe needs an 'epw' column.")
        out = {}
        if 'hour' in data.columns and len(data) > data['hour'].nunique():
            sim = _simulation_ids(data)
            for sid, frame in data.groupby(sim, sort=True):
                key = str(_short_value(frame['epw'].iloc[0]))
                if key not in out:
                    out[key] = self._hp_series(frame, variable, 'first', 'get_hourly_series_by_epw')[0].to_numpy(float)
        else:
            for epw_value, frame in data.groupby('epw', sort=False):
                path = self._hp_csv_path(frame.iloc[0], path_replacements)
                values = self._hp_read_csv_columns(path, [variable])
                if values.shape[1] == 0:
                    raise KeyError(f"'{variable}' not found in {path}")
                out[str(_short_value(epw_value))] = values.iloc[:, 0].to_numpy(float)
        return out

    def attach_hourly_series_by_epw(
            self,
            name: str,
            series_by_epw: Dict[str, Sequence[float]],
            df_source: str = 'parametric_hourly',
            df: Optional[pd.DataFrame] = None,
            inplace: bool = True,
    ) -> pd.DataFrame:
        """Add to a long hourly dataframe a column taken from ``{epw: hourly values}``.

        For example, the outdoor temperature or running mean of each weather
        file (from :meth:`get_hourly_series_by_epw`) can be attached to the
        hourly outputs of simulations that did not report it.

        Parameters
        ----------
        name : str
            New column name.
        series_by_epw : dict
            ``{epw name or substring: hourly values}``.
        df_source : str
            ``'parametric_hourly'`` or ``'optimisation_hourly'``.
        df : pandas.DataFrame, optional
            Dataframe used instead of ``df_source`` (a modified copy is returned).
        inplace : bool
            When ``df`` is None, also update the stored hourly dataframe.

        Returns
        -------
        pandas.DataFrame
            Dataframe with the new column.
        """
        data = self._hp_source(df, df_source, context='attach_hourly_series_by_epw')
        sim = _simulation_ids(data)
        pos = data.groupby(sim).cumcount().to_numpy()
        values = np.full(len(data), np.nan)
        keys = {k: k for k in series_by_epw}
        for sid in pd.unique(sim):
            rows = np.flatnonzero((sim == sid).to_numpy())
            key = _match_label(data['epw'].iloc[rows[0]], keys)
            if key is None:
                raise KeyError(f"No series for epw {data['epw'].iloc[rows[0]]!r}; keys: {list(series_by_epw)}")
            arr = np.asarray(series_by_epw[key], dtype=float)
            values[rows] = arr[pos[rows] % len(arr)]
        data[name] = values
        if df is None and inplace:
            attr = {'parametric_hourly': 'outputs_param_simulation_hourly',
                    'optimisation_hourly': 'outputs_optimisation_hourly'}.get(df_source)
            if attr is not None and getattr(self, attr, None) is not None and len(getattr(self, attr)) == len(data):
                getattr(self, attr)[name] = values
        return data

    # ------------------------------------------------------------- hourly frame for plots

    def _hp_frame(self, data: pd.DataFrame, variables: Dict[str, Any], zone_aggregation='mean', energy_unit='kWh',
                  normalize_per_m2=False, floor_area=None, context='') -> Tuple[pd.DataFrame, dict, dict]:
        """Numeric frame with ``_sim``, ``_h`` (hour index) and the requested variables (converted)."""
        sim = _simulation_ids(data)
        frame = pd.DataFrame({'_sim': sim.to_numpy(), '_h': data.groupby(sim).cumcount().to_numpy()},
                             index=data.index)
        units, labels = {}, {}
        for key, spec in variables.items():
            vals, unit, label = self._hp_values(data, spec, zone_aggregation, energy_unit, normalize_per_m2,
                                                floor_area, context)
            frame[key] = vals
            units[key], labels[key] = unit, label
        return frame, units, labels

    # --------------------------------------------------------------- shared plot helpers

    @staticmethod
    def _hp_rc(rc: Optional[dict]) -> dict:
        style = dict(DEFAULT_RC)
        if rc:
            style.update(rc)
        return style

    @staticmethod
    def _hp_cases(data: pd.DataFrame, frame: pd.DataFrame, by, labels, order, context: str) -> Tuple[pd.Series, list]:
        """Label of each row for the grouping ``by`` and the ordered list of labels."""
        lab = _group_labels(data, by, labels, context)
        names = _ordered(pd.unique(lab), order, labels)
        if not names:
            raise ValueError(f'{context}: no groups left after applying the order {order}.')
        return lab, names

    @staticmethod
    def _hp_one_series(frame: pd.DataFrame, mask: np.ndarray, key: str, context: str) -> np.ndarray:
        """Hourly values of ``key`` for the rows in ``mask``; several simulations are averaged hour by hour."""
        sub = frame.loc[mask, ['_sim', '_h', key]]
        n_sims = sub['_sim'].nunique()
        if n_sims == 0:
            return np.array([])
        if n_sims > 1:
            warnings.warn(f'{context}: {n_sims} simulations share the same group; their hourly values are averaged. '
                          'Use data_filter or a finer grouping to select one simulation per panel.')
        return sub.groupby('_h')[key].mean().to_numpy(float)

    # ------------------------------------------------------------------- heat maps

    def plot_hourly_heatmaps(
            self,
            variables: Union[Sequence[str], Dict[str, str]],
            df: Optional[pd.DataFrame] = None,
            df_source: str = 'parametric_hourly',
            case: Optional[Union[str, Sequence[str]]] = None,
            case_labels: Optional[dict] = None,
            case_order: Optional[Sequence] = None,
            variable_labels: Optional[dict] = None,
            cmaps: Optional[dict] = None,
            value_ranges: Optional[dict] = None,
            annotate: Union[bool, dict] = True,
            zone_aggregation: str = 'mean',
            energy_unit: str = 'kWh',
            normalize_per_m2: bool = False,
            floor_area: Optional[float] = None,
            panel_size: Tuple[float, float] = (3.55, 1.7),
            figsize: Optional[Tuple[float, float]] = None,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            out_dir: str = '.',
            filename: Optional[str] = None,
            filename_template: Optional[str] = None,
            dpi: int = 300,
            rc: Optional[dict] = None,
            close: bool = True,
    ):
        """Day-by-hour maps (carpet plots) of hourly variables, one row per case.

        Parameters
        ----------
        variables : list or dict
            Hourly variables (names or substrings), one column of panels each; a
            dict ``{label: variable}`` also sets the panel titles.
        df, df_source
            Long hourly dataframe (default ``'parametric_hourly'``).
        case : str or list of str, optional
            Column(s) whose combinations define the rows (for example
            ``['ComfMod', 'HVACmode']``); each row should hold one simulation.
        case_labels : dict, optional
            ``{value or tuple of values: label}``; strings may be substrings.
        case_order : list, optional
            Order of the rows (labels or values); rows not listed are omitted.
        variable_labels : dict, optional
            ``{variable: colour-bar label}``.
        cmaps : dict, optional
            ``{variable: colormap}`` (defaults: 'YlOrRd' for temperatures,
            'Blues' for energy, 'viridis' otherwise).
        value_ranges : dict, optional
            ``{variable: (vmin, vmax)}`` shared by all rows.
        annotate : bool or dict
            Write the annual mean (temperatures) or annual total (energy) in each
            panel; a dict ``{variable: callable(values) -> str}`` customises it.
        zone_aggregation, energy_unit, normalize_per_m2, floor_area
            Variable resolution and units (energy in J is shown in kWh per hour).
        panel_size, figsize
            Size of each panel or of the whole figure (inches).
        data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Row filter.
        out_dir, filename, filename_template, dpi, rc, close
            Output settings; ``rc`` updates the matplotlib style.

        Returns
        -------
        matplotlib.figure.Figure
            With ``saved_path`` and ``summary`` (annual mean or total per panel).

        Examples
        --------
        >>> sim.plot_hourly_heatmaps(['Zone Operative Temperature', 'Electricity:HVAC'],
        ...                          case=['ComfMod', 'HVACmode'], data_filter={'include': {'epw': {'contains': 'Present'}}})
        """
        var_map = dict(variables) if isinstance(variables, dict) else {str(v): v for v in variables}
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, 'plot_hourly_heatmaps')
        frame, units, labels = self._hp_frame(data, var_map, zone_aggregation, energy_unit, False, None,
                                              'plot_hourly_heatmaps')
        lab, rows = self._hp_cases(data, frame, case, case_labels, case_order, 'plot_hourly_heatmaps')
        area = self._hp_floor_area(data.iloc[:1], floor_area)
        area = float(area.iloc[0]) if isinstance(area, pd.Series) else area
        n_r, n_c = len(rows), len(var_map)
        summary = []
        with plt.rc_context(self._hp_rc(rc)):
            fig, axes = plt.subplots(n_r, n_c, squeeze=False, sharex=True, sharey=True, layout='constrained',
                                     figsize=figsize or (panel_size[0] * n_c, panel_size[1] * n_r + 0.9))
            images = {}
            for j, key in enumerate(var_map):
                unit = units[key]
                if cmaps and key in cmaps:
                    cmap = cmaps[key]
                elif unit == '°C':
                    cmap = 'YlOrRd'
                elif 'kWh' in unit or unit in ('J', 'W', 'Wh'):
                    cmap = 'Blues'
                else:
                    cmap = 'viridis'
                vr = (value_ranges or {}).get(key)
                if vr is None:
                    sel = frame.loc[lab.isin(rows), key]
                    vr = (float(np.nanmin(sel)), float(np.nanmax(sel)))
                for i, row_name in enumerate(rows):
                    ax = axes[i, j]
                    vals = self._hp_one_series(frame, (lab == row_name).to_numpy(), key, 'plot_hourly_heatmaps')
                    n_days = len(vals) // 24
                    grid = vals[:n_days * 24].reshape(n_days, 24).T
                    images[j] = ax.imshow(grid, aspect='auto', origin='lower', cmap=cmap, vmin=vr[0], vmax=vr[1],
                                          extent=[0.5, n_days + 0.5, -0.5, 23.5], interpolation='nearest')
                    ax.grid(False)
                    ax.set_yticks([0, 6, 12, 18, 23])
                    if n_days >= 365:
                        starts = np.cumsum((0,) + MONTH_DAYS[:-1]) + 1
                        ax.set_xticks(starts)
                        ax.set_xticklabels(MONTH_INITIALS)
                    if unit == '°C':
                        stat, text = float(np.nanmean(vals)), f'mean {np.nanmean(vals):.1f} °C'
                    elif unit.startswith('kWh'):
                        total = float(np.nansum(vals))
                        if area and unit == 'kWh':
                            stat, text = total / area, f'{total / area:.1f} kWh/m² per year'
                        else:
                            stat, text = total, f'{total:.0f} {unit} per year'
                    else:
                        stat, text = float(np.nanmean(vals)), f'mean {np.nanmean(vals):.2f} {unit}'.strip()
                    if isinstance(annotate, dict) and key in annotate:
                        text = annotate[key](vals)
                    if annotate:
                        ax.text(0.985, 0.94, text, transform=ax.transAxes, ha='right', va='top', fontsize=7,
                                bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.85))
                    summary.append({'case': row_name, 'variable': key, 'value': stat, 'text': text})
                    if j == 0:
                        ax.set_ylabel(f'{row_name}\nHour of day' if case is not None else 'Hour of day')
                    if i == 0:
                        ax.set_title(f'({_panel_letter(j)}) {_pretty_name(key) if key == str(var_map[key]) else key}',
                                     fontweight='bold')
                    if i == n_r - 1:
                        ax.set_xlabel('Month' if n_days >= 365 else 'Day')
            for j, key in enumerate(var_map):
                cb = fig.colorbar(images[j], ax=axes[:, j], location='bottom', aspect=30, shrink=0.95, pad=0.01)
                cb.set_label((variable_labels or {}).get(key, labels[key]))
            fig.summary = pd.DataFrame(summary)
            self._hp_save(self, fig, out_dir, filename, filename_template, 'plot_hourly_heatmaps.png',
                          'plot_hourly_heatmaps', {'plot': 'hourly_heatmaps'}, dpi, close)
        return fig

    # ------------------------------------------------------------------- selected period

    @staticmethod
    def _hp_window_start(values: np.ndarray, days: int, how: str) -> int:
        """First hour (multiple of 24) of the ``days``-day window with the largest/smallest sum of ``values``."""
        n_days = len(values) // 24
        daily = np.asarray(values[:n_days * 24], float).reshape(n_days, 24).sum(axis=1)
        window = np.convolve(daily, np.ones(days), mode='valid')
        k = int(np.argmin(window)) if how == 'min' else int(np.argmax(window))
        return 24 * k

    def plot_hourly_period(
            self,
            variables: Union[Sequence[str], Dict[str, str]],
            df: Optional[pd.DataFrame] = None,
            df_source: str = 'parametric_hourly',
            case: Optional[Union[str, Sequence[str]]] = None,
            case_labels: Optional[dict] = None,
            case_order: Optional[Sequence] = None,
            col: Optional[str] = 'epw',
            col_labels: Optional[dict] = None,
            col_order: Optional[Sequence] = None,
            start: Optional[Union[str, int, dict]] = None,
            days: int = 7,
            select: Optional[dict] = None,
            energy_variable: Optional[str] = None,
            shade: Optional[Tuple[str, str]] = None,
            colors: Optional[dict] = None,
            linestyles: Optional[dict] = None,
            ylim: Optional[Tuple[float, float]] = None,
            energy_ylim: Optional[Tuple[float, float]] = None,
            ylabel: str = 'Temperature (°C)',
            energy_label: Optional[str] = None,
            notes: Optional[dict] = None,
            zone_aggregation: str = 'mean',
            energy_unit: str = 'kWh',
            floor_area: Optional[float] = None,
            panel_size: Tuple[float, float] = (3.55, 2.9),
            figsize: Optional[Tuple[float, float]] = None,
            legend_ncol: int = 3,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            out_dir: str = '.',
            filename: Optional[str] = None,
            filename_template: Optional[str] = None,
            dpi: int = 300,
            rc: Optional[dict] = None,
            close: bool = True,
    ):
        """Hourly time series of a period (for example one week) for several cases and weather files.

        Rows are cases and columns are the values of ``col`` (weather files by
        default); each column can use its own period, given by ``start`` or chosen
        automatically with ``select``.

        Parameters
        ----------
        variables : list or dict
            Variables drawn as lines in the upper panels (``{label: variable}``
            sets the legend labels).
        case, case_labels, case_order
            Grouping of the rows (see :meth:`plot_hourly_heatmaps`).
        col, col_labels, col_order
            Grouping of the columns.
        start : str, int or dict, optional
            First day of the period: ``'MM-DD'``, day of the year (1-365) or
            ``{column label: start}``.
        days : int
            Length of the period in days.
        select : dict, optional
            Automatic choice of the period when ``start`` is not given, as
            ``{'method': 'max' | 'min' | 'max_difference', 'variable': name,
            'cases': (case_a, case_b)}`` (the same for every column) or
            ``{column label: {...}}``. ``'max'``/``'min'`` use the sum of ``variable``
            for the first case listed in ``cases`` (default: the first row);
            ``'max_difference'`` maximises the sum of ``variable`` in ``case_a``
            minus ``case_b`` (for example the largest saving of one strategy).
        energy_variable : str, optional
            Variable drawn as a filled step in a lower panel (for example
            ``'Electricity:HVAC'``); its total over the period is given in the title
            (per m² when a floor area is available).
        shade : tuple, optional
            ``(variable, label)``: hours in which the variable is above zero are
            shaded (for example ``('Window or Door Opening Factor', 'Windows open')``).
        colors, linestyles : dict, optional
            ``{variable or label: value}`` for the lines.
        ylim, energy_ylim : tuple, optional
            Limits of the upper and lower panels.
        notes : dict, optional
            ``{(case label, column label): text}`` written in the panel.
        zone_aggregation, energy_unit, floor_area
            Variable resolution and units.
        panel_size, figsize, legend_ncol
            Layout.
        data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Row filter.
        out_dir, filename, filename_template, dpi, rc, close
            Output settings.

        Returns
        -------
        matplotlib.figure.Figure
            With ``saved_path`` and ``summary`` (period, energy and shaded hours per panel).

        Examples
        --------
        >>> sim.plot_hourly_period(
        ...     variables={'Outdoor air': 'Outdoor Air Drybulb', 'Operative temperature': 'Zone Operative Temperature'},
        ...     case='ComfMod', energy_variable='Electricity:HVAC',
        ...     select={'method': 'max_difference', 'variable': 'Electricity:HVAC', 'cases': ('0', '3')})
        """
        var_map = dict(variables) if isinstance(variables, dict) else {_pretty_name(str(v)): v for v in variables}
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, 'plot_hourly_period')
        needed = {f'v{i}': spec for i, spec in enumerate(var_map.values())}
        if energy_variable is not None:
            needed['energy'] = energy_variable
        if shade is not None:
            needed['shade'] = shade[0]
        frame, units, labels = self._hp_frame(data, {k: v for k, v in needed.items() if k != 'shade'},
                                              zone_aggregation, energy_unit, False, None, 'plot_hourly_period')
        if shade is not None:
            frame['shade'] = self._hp_series(data, shade[0], 'max', 'shade')[0].to_numpy(float)
        sel_vars = {}
        if select is not None:
            specs = [select] if 'method' in select else list(select.values())
            for k, spec in enumerate(specs):
                if spec.get('variable') is not None and spec['variable'] not in sel_vars:
                    name = f'sel{len(sel_vars)}'
                    frame[name] = self._hp_values(data, spec['variable'], zone_aggregation, energy_unit)[0]
                    sel_vars[spec['variable']] = name
        rlab, rows = self._hp_cases(data, frame, case, case_labels, case_order, 'plot_hourly_period')
        clab, cols = self._hp_cases(data, frame, col, col_labels, col_order, 'plot_hourly_period')
        area = self._hp_floor_area(data.iloc[:1], floor_area)
        area = float(area.iloc[0]) if isinstance(area, pd.Series) else area
        calendar = _calendar(int(frame.groupby('_sim')['_h'].max().max()) + 1)
        windows = {}
        for c in cols:
            st = start.get(c) if isinstance(start, dict) else start
            if st is not None:
                if isinstance(st, str):
                    mm, dd = (int(x) for x in st.split('-'))
                    doy = int(np.sum(MONTH_DAYS[:mm - 1]) + dd)
                else:
                    doy = int(st)
                windows[c] = (24 * (doy - 1), f'from {st}')
                continue
            if select is None:
                raise ValueError('plot_hourly_period: give start or select.')
            spec = select if 'method' in select else select.get(c)
            if spec is None:
                raise ValueError(f'plot_hourly_period: no select rule for column {c!r}.')
            method = spec.get('method', 'max')
            sv = sel_vars.get(spec.get('variable'), 'v0')
            cases_sel = [str(x) for x in _as_list(spec.get('cases'))] or [rows[0]]
            cases_sel = [_match_label(x, case_labels) or x for x in cases_sel]
            in_col = (clab == c).to_numpy()
            a = self._hp_one_series(frame, in_col & (rlab == cases_sel[0]).to_numpy(), sv, 'plot_hourly_period')
            if method == 'max_difference':
                if len(cases_sel) < 2:
                    raise ValueError("select method 'max_difference' needs two cases.")
                b = self._hp_one_series(frame, in_col & (rlab == cases_sel[1]).to_numpy(), sv, 'plot_hourly_period')
                values = a - b
                how = 'max'
            else:
                values, how = a, method
            windows[c] = (self._hp_window_start(values, days, how), f'{method} of {spec.get("variable")}')
        palette = _colours(list(var_map), colors if colors is not None else
                           ['#9a9a9a', '#4d4d4d', '#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00'])
        styles = linestyles or {}
        n_r, n_c = len(rows), len(cols)
        summary = []
        with plt.rc_context(self._hp_rc(rc)):
            fig = plt.figure(figsize=figsize or (panel_size[0] * n_c, panel_size[1] * n_r + 0.6), layout='constrained')
            outer = fig.add_gridspec(n_r, n_c)
            letter = 0
            first_axes = None
            for i, r in enumerate(rows):
                for j, c in enumerate(cols):
                    h0, how = windows[c]
                    sl = slice(h0, h0 + 24 * days)
                    t = calendar['timestamp'].iloc[sl]
                    mask = ((rlab == r) & (clab == c)).to_numpy()
                    if energy_variable is not None:
                        g = outer[i, j].subgridspec(2, 1, height_ratios=[3, 1], hspace=0.05)
                        ax, axe = fig.add_subplot(g[0]), fig.add_subplot(g[1])
                    else:
                        ax, axe = fig.add_subplot(outer[i, j]), None
                    first_axes = first_axes or ax
                    if shade is not None:
                        sh = self._hp_one_series(frame, mask, 'shade', 'plot_hourly_period')[sl]
                        ax.fill_between(t, 0, 1, where=sh > 0, transform=ax.get_xaxis_transform(), color='#E69F00',
                                        alpha=0.22, lw=0, step='post', label=shade[1])
                    for k, (vlabel, spec) in enumerate(var_map.items()):
                        vals = self._hp_one_series(frame, mask, f'v{k}', 'plot_hourly_period')[sl]
                        ax.plot(t, vals, color=palette[vlabel], lw=1.1, ls=styles.get(vlabel, '-'), label=vlabel)
                    if ylim is not None:
                        ax.set_ylim(*ylim)
                    ax.set_xlim(t.iloc[0], t.iloc[-1] + pd.Timedelta(hours=1))
                    title = f'({_panel_letter(letter)}) {c}, {r}' if n_c > 1 or col is not None else f'({_panel_letter(letter)}) {r}'
                    row_summary = {'case': r, 'column': c, 'start': str(t.iloc[0].strftime('%m-%d')),
                                   'end': str(t.iloc[-1].strftime('%m-%d')), 'selection': how}
                    if axe is not None:
                        e = self._hp_one_series(frame, mask, 'energy', 'plot_hourly_period')[sl]
                        axe.fill_between(t, 0, e, step='post', color='0.45', lw=0)
                        axe.set_xlim(ax.get_xlim())
                        if energy_ylim is not None:
                            axe.set_ylim(*energy_ylim)
                        axe.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 7)))
                        axe.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
                        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 7)))
                        ax.set_xticklabels([])
                        total = float(np.nansum(e))
                        if area and units['energy'] == 'kWh':
                            title += f': {total / area:.2f} kWh/m² in the period'
                            row_summary['energy_per_m2'] = total / area
                        else:
                            title += f': {total:.1f} {units["energy"]} in the period'
                        row_summary['energy'] = total
                        row_summary['energy_peak'] = float(np.nanmax(e)) if len(e) else np.nan
                        if j == 0:
                            axe.set_ylabel(energy_label or f'{_pretty_name(str(energy_variable))}\n({units["energy"]})')
                        else:
                            axe.set_yticklabels([])
                    else:
                        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 7)))
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
                    if shade is not None:
                        row_summary['shaded_hours'] = int((self._hp_one_series(frame, mask, 'shade',
                                                                               'plot_hourly_period')[sl] > 0).sum())
                    summary.append(row_summary)
                    ax.set_title(title, loc='left', fontsize=8)
                    if notes and (r, c) in notes:
                        ax.text(0.5, 0.05, notes[(r, c)], transform=ax.transAxes, ha='center', va='bottom',
                                fontsize=6.8, style='italic', color='0.3')
                    if j == 0:
                        ax.set_ylabel(ylabel)
                    else:
                        ax.set_yticklabels([])
                    letter += 1
            handles, names = first_axes.get_legend_handles_labels()
            fig.legend(handles, names, loc='outside lower center', ncol=legend_ncol, frameon=False)
            fig.summary = pd.DataFrame(summary)
            self._hp_save(self, fig, out_dir, filename, filename_template, 'plot_hourly_period.png',
                          'plot_hourly_period', {'plot': 'hourly_period'}, dpi, close)
        return fig

    # -------------------------------------------------------------- binned (signature)

    def plot_hourly_binned_response(
            self,
            x: str = 'Outdoor Air Drybulb Temperature',
            y: str = 'Electricity:HVAC',
            df: Optional[pd.DataFrame] = None,
            df_source: str = 'parametric_hourly',
            hue: Optional[Union[str, Sequence[str]]] = None,
            hue_labels: Optional[dict] = None,
            hue_order: Optional[Sequence] = None,
            palette=None,
            linestyles: Optional[dict] = None,
            col: Optional[str] = 'epw',
            col_labels: Optional[dict] = None,
            col_order: Optional[Sequence] = None,
            bin_width: float = 1.0,
            bins: Optional[Sequence[float]] = None,
            min_count: int = 10,
            statistic: Literal['mean', 'median'] = 'mean',
            band: Optional[Tuple[float, float]] = (0.25, 0.75),
            idle_when_zero: Optional[Sequence[str]] = None,
            idle_label: str = 'Hours without heating or cooling',
            xlim: Optional[Tuple[float, float]] = None,
            ylim: Optional[Tuple[float, float]] = None,
            xlabel: Optional[str] = None,
            ylabel: Optional[str] = None,
            zone_aggregation: str = 'mean',
            energy_unit: str = 'kWh',
            normalize_per_m2: bool = False,
            floor_area: Optional[float] = None,
            panel_size: Tuple[float, float] = (3.55, 3.1),
            figsize: Optional[Tuple[float, float]] = None,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            out_dir: str = '.',
            filename: Optional[str] = None,
            filename_template: Optional[str] = None,
            dpi: int = 300,
            rc: Optional[dict] = None,
            close: bool = True,
    ):
        """Hourly values of ``y`` grouped in bins of ``x`` (for example an energy signature).

        Each line gives the mean (or median) of ``y`` in each bin of ``x`` for one
        group, and the shading its interquartile range (``band``).

        Parameters
        ----------
        x, y : str
            Hourly variables (names or substrings). Energy in J is shown in kWh per
            hour (per m² with ``normalize_per_m2``).
        hue, hue_labels, hue_order, palette, linestyles
            Groups drawn as separate lines.
        col, col_labels, col_order
            One panel per value of ``col`` (weather files by default).
        bin_width, bins : float or sequence
            Width of the bins of ``x`` or explicit bin edges.
        min_count : int
            Bins with fewer hours are not drawn.
        statistic : {'mean', 'median'}
            Line statistic.
        band : tuple or None
            Quantiles of the shaded band.
        idle_when_zero : list of str, optional
            Variables (for example the cooling and heating coil rates) that are
            all zero in the hours without conditioning; the range of the median of
            ``y`` in those hours across groups is drawn as a grey band and reported
            in ``summary``.
        idle_label : str
            Text of that band.
        xlim, ylim, xlabel, ylabel
            Axes settings.
        zone_aggregation, energy_unit, normalize_per_m2, floor_area
            Variable resolution and units.
        panel_size, figsize
            Layout.
        data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Row filter.
        out_dir, filename, filename_template, dpi, rc, close
            Output settings.

        Returns
        -------
        matplotlib.figure.Figure
            With ``saved_path`` and ``summary`` (binned statistics and idle levels).

        Examples
        --------
        >>> sim.plot_hourly_binned_response(x='Outdoor Air Drybulb', y='Electricity:HVAC', hue=['ComfMod', 'HVACmode'],
        ...                                 idle_when_zero=['Cooling Coil Total Cooling Rate', 'Heating Coil Heating Rate'])
        """
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, 'plot_hourly_binned_response')
        frame, units, labels = self._hp_frame(data, {'x': x, 'y': y}, zone_aggregation, energy_unit,
                                              normalize_per_m2, floor_area, 'plot_hourly_binned_response')
        if idle_when_zero:
            idle = np.ones(len(frame), bool)
            for spec in idle_when_zero:
                idle &= self._hp_series(data, spec, 'sum', 'idle_when_zero')[0].to_numpy(float) <= 0
            frame['idle'] = idle
        hlab, groups = self._hp_cases(data, frame, hue, hue_labels, hue_order, 'plot_hourly_binned_response')
        clab, cols = self._hp_cases(data, frame, col, col_labels, col_order, 'plot_hourly_binned_response')
        colours = _colours(groups, palette)
        styles = linestyles or {}
        if bins is None:
            lo = np.floor(np.nanmin(frame['x']) / bin_width) * bin_width
            hi = np.ceil(np.nanmax(frame['x']) / bin_width) * bin_width + bin_width
            bins = np.arange(lo, hi + 1e-9, bin_width)
        summary = []
        with plt.rc_context(self._hp_rc(rc)):
            fig, axes = plt.subplots(1, len(cols), squeeze=False, sharex=True, sharey=True, layout='constrained',
                                     figsize=figsize or (panel_size[0] * len(cols), panel_size[1]))
            for j, c in enumerate(cols):
                ax = axes[0, j]
                idle_levels = []
                for g in groups:
                    mask = ((hlab == g) & (clab == c)).to_numpy()
                    if not mask.any():
                        continue
                    sub = pd.DataFrame({'x': frame['x'].to_numpy()[mask], 'y': frame['y'].to_numpy()[mask]})
                    sub['bin'] = pd.cut(sub['x'], bins)
                    grp = sub.groupby('bin', observed=True)['y']
                    st = pd.DataFrame({'mid': [b.mid for b in grp.size().index], 'n': grp.size().to_numpy(),
                                       'stat': (grp.mean() if statistic == 'mean' else grp.median()).to_numpy()})
                    if band is not None:
                        st['lo'] = grp.quantile(band[0]).to_numpy()
                        st['hi'] = grp.quantile(band[1]).to_numpy()
                    st = st[st['n'] >= min_count]
                    if band is not None:
                        ax.fill_between(st['mid'], st['lo'], st['hi'], color=colours[g], alpha=0.12, lw=0)
                    ax.plot(st['mid'], st['stat'], color=colours[g], ls=styles.get(g, '-'), lw=1.4, label=g)
                    rec = {'group': g, 'column': c}
                    if idle_when_zero:
                        idle_mask = frame['idle'].to_numpy()[mask]
                        level = float(np.median(sub['y'].to_numpy()[idle_mask])) if idle_mask.any() else np.nan
                        idle_levels.append(level)
                        rec.update({'idle_level': level, 'idle_hours': int(idle_mask.sum())})
                    rec['bins'] = st.reset_index(drop=True)
                    summary.append(rec)
                if idle_when_zero and np.isfinite(idle_levels).any():
                    lo_i, hi_i = np.nanmin(idle_levels), np.nanmax(idle_levels)
                    ax.axhspan(lo_i, hi_i if hi_i > lo_i else lo_i + 1e-3, color='0.6', alpha=0.25, lw=0)
                    ax.text(0.98, 0.02, f'{idle_label}: {lo_i:.2f}–{hi_i:.2f} {units["y"]}', transform=ax.transAxes,
                            ha='right', va='bottom', fontsize=6.8, color='0.3', style='italic')
                ax.set_title(f'({_panel_letter(j)}) {c}' if col is not None else '', loc='left', fontweight='bold')
                ax.set_xlabel(xlabel or labels['x'])
                if j == 0:
                    ax.set_ylabel(ylabel or labels['y'])
            if xlim is not None:
                axes[0, 0].set_xlim(*xlim)
            if ylim is not None:
                axes[0, 0].set_ylim(*ylim)
            axes[0, 0].legend(loc='upper left', frameon=False)
            fig.summary = pd.DataFrame(summary)
            self._hp_save(self, fig, out_dir, filename, filename_template, 'plot_hourly_binned_response.png',
                          'plot_hourly_binned_response', {'plot': 'hourly_binned_response'}, dpi, close)
        return fig

    # ------------------------------------------------------------ load-duration curves

    def plot_load_duration_curves(
            self,
            variable: str = 'Electricity:HVAC',
            df: Optional[pd.DataFrame] = None,
            df_source: str = 'parametric_hourly',
            panel: Optional[Union[str, Sequence[str]]] = None,
            panel_labels: Optional[dict] = None,
            panel_order: Optional[Sequence] = None,
            hue: Optional[Union[str, Sequence[str]]] = 'epw',
            hue_labels: Optional[dict] = None,
            hue_order: Optional[Sequence] = None,
            palette=None,
            n_cols: int = 2,
            hours_in_thousands: bool = True,
            ylim: Optional[Tuple[float, float]] = None,
            ylabel: Optional[str] = None,
            suptitle: Optional[str] = None,
            peak_df: Optional[pd.DataFrame] = None,
            peak_x: str = 'E_HVAC',
            peak_y: str = 'E_HVAC_peak',
            peak_hue: Optional[str] = 'epw',
            peak_hue_labels: Optional[dict] = None,
            peak_marker_by: Optional[str] = None,
            peak_markers: Optional[dict] = None,
            peak_marker_labels: Optional[dict] = None,
            peak_xlabel: Optional[str] = None,
            peak_ylabel: Optional[str] = None,
            peak_title: Optional[str] = None,
            zone_aggregation: str = 'sum',
            energy_unit: str = 'kWh',
            normalize_per_m2: bool = False,
            floor_area: Optional[float] = None,
            figsize: Optional[Tuple[float, float]] = None,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            out_dir: str = '.',
            filename: Optional[str] = None,
            filename_template: Optional[str] = None,
            dpi: int = 300,
            rc: Optional[dict] = None,
            close: bool = True,
    ):
        """Load-duration curves of an hourly variable, optionally with an annual-versus-peak panel.

        Parameters
        ----------
        variable : str
            Hourly variable sorted in descending order (energy in J is shown in kWh
            per hour).
        panel, panel_labels, panel_order
            One panel per group (for example per control strategy).
        hue, hue_labels, hue_order, palette
            Curves within each panel (weather files by default).
        n_cols : int
            Columns of the grid of panels.
        hours_in_thousands : bool
            Hours axis in thousands.
        ylim, ylabel, suptitle
            Axes settings.
        peak_df : pandas.DataFrame, optional
            Evaluation-level table (for example from
            :meth:`compute_hourly_indicators`) for an extra panel of ``peak_y``
            against ``peak_x``, coloured by ``peak_hue`` and with markers by
            ``peak_marker_by`` (``peak_markers``: ``{value: marker}``).
        peak_x, peak_y, peak_hue, peak_hue_labels, peak_marker_by, peak_markers, peak_marker_labels, peak_xlabel, peak_ylabel, peak_title
            Settings of that panel (``peak_marker_labels``: ``{value: legend text}``).
        zone_aggregation, energy_unit, normalize_per_m2, floor_area
            Variable resolution and units.
        figsize, data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Layout and row filter.
        out_dir, filename, filename_template, dpi, rc, close
            Output settings.

        Returns
        -------
        matplotlib.figure.Figure
            With ``saved_path`` and ``summary`` (peak, hours above zero and total per curve).

        Examples
        --------
        >>> sim.plot_load_duration_curves('Electricity:HVAC', panel=['ComfMod', 'HVACmode'], hue='epw',
        ...                               peak_df=sim.hourly_indicators)
        """
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, 'plot_load_duration_curves')
        frame, units, labels = self._hp_frame(data, {'v': variable}, zone_aggregation, energy_unit, normalize_per_m2,
                                              floor_area, 'plot_load_duration_curves')
        plab, panels = self._hp_cases(data, frame, panel, panel_labels, panel_order, 'plot_load_duration_curves')
        hlab, hues = self._hp_cases(data, frame, hue, hue_labels, hue_order, 'plot_load_duration_curves')
        colours = _colours(hues, palette)
        n_p = len(panels)
        n_cols = max(1, min(n_cols, n_p))
        n_rows = int(np.ceil(n_p / n_cols))
        summary = []
        with plt.rc_context(self._hp_rc(rc)):
            if peak_df is not None:
                fig = plt.figure(figsize=figsize or (7.1, 1.8 * n_rows + 0.6), layout='constrained')
                left, right = fig.subfigures(1, 2, width_ratios=[1.2, 1], wspace=0.04)
            else:
                fig = plt.figure(figsize=figsize or (2.3 * n_cols + 0.6, 1.8 * n_rows + 0.6), layout='constrained')
                left, right = fig, None
            axs = np.atleast_2d(left.subplots(n_rows, n_cols, sharex=True, sharey=True, squeeze=False))
            scale = 1000.0 if hours_in_thousands else 1.0
            for k, p in enumerate(panels):
                ax = axs[k // n_cols, k % n_cols]
                for hname in hues:
                    mask = ((plab == p) & (hlab == hname)).to_numpy()
                    if not mask.any():
                        continue
                    v = self._hp_one_series(frame, mask, 'v', 'plot_load_duration_curves')
                    curve = np.sort(v)[::-1]
                    ax.plot(np.arange(1, len(curve) + 1) / scale, curve, color=colours[hname], lw=1.2, label=hname)
                    summary.append({'panel': p, 'hue': hname, 'peak': float(curve[0]),
                                    'hours_above_zero': int((curve > 1e-9).sum()), 'total': float(curve.sum())})
                ax.set_title(f'({_panel_letter(k)}) {p}', loc='left', fontsize=7.5)
                if k % n_cols == 0:
                    ax.set_ylabel(ylabel if ylabel else (f"{units['v']} per hour" if units['v'].startswith('kWh')
                                                         else labels['v']))
            for k in range(n_p, n_rows * n_cols):
                axs[k // n_cols, k % n_cols].set_visible(False)
            if ylim is not None:
                axs[0, 0].set_ylim(*ylim)
            axs[0, 0].set_xlim(0, (len(_calendar(int(frame['_h'].max()) + 1))) / scale)
            axs[0, 0].legend(frameon=False, fontsize=6.5, loc='upper right')
            left.supxlabel('Hours of the year, sorted' + (' (thousands)' if hours_in_thousands else ''), fontsize=8)
            if suptitle:
                left.suptitle(suptitle, fontsize=8)
            if right is not None:
                ax = right.subplots()
                pdf = peak_df.copy()
                for colname in (peak_x, peak_y):
                    if colname not in pdf.columns:
                        raise KeyError(f"peak_df has no column '{colname}'")
                ph = _group_labels(pdf, peak_hue, peak_hue_labels if peak_hue_labels is not None else hue_labels,
                                   'peak_hue') if peak_hue else pd.Series('all', index=pdf.index)
                ph_names = _ordered(pd.unique(ph), hue_order, peak_hue_labels or hue_labels)
                pcols = _colours(ph_names, palette if isinstance(palette, dict) else None)
                pcols.update({n: colours[n] for n in ph_names if n in colours})
                markers = peak_markers or {}
                mk_values = list(pd.unique(pdf[peak_marker_by])) if peak_marker_by else [None]
                default_markers = ['o', '^', 's', 'D', 'v', 'P']
                for name in ph_names:
                    for m_i, mv in enumerate(mk_values):
                        sel = (ph == name)
                        if peak_marker_by:
                            sel &= pdf[peak_marker_by].map(lambda v: _values_equal(v, mv))
                        s_ = pdf[sel]
                        mk = markers.get(mv, default_markers[m_i % len(default_markers)]) if peak_marker_by else 'o'
                        ax.scatter(s_[peak_x], s_[peak_y], color=pcols[name], marker=mk, s=16, edgecolors='k',
                                   linewidths=0.25, zorder=3)
                handles = [Line2D([], [], ls='', marker='s', color=pcols[n], ms=5, label=n) for n in ph_names]
                if peak_marker_by:
                    for m_i, mv in enumerate(mk_values):
                        mk = markers.get(mv, default_markers[m_i % len(default_markers)])
                        handles.append(Line2D([], [], ls='', marker=mk, color='0.6', mec='k', mew=0.3, ms=4.5,
                                              label=str(_match_label(mv, peak_marker_labels) or _short_value(mv))))
                ax.legend(handles=handles, frameon=False, fontsize=6.5, loc='upper left')
                units_attr = getattr(peak_df, 'attrs', {}).get('units', {})
                ax.set_xlabel(peak_xlabel or f'{peak_x} ({units_attr.get(peak_x, "")})'.replace(' ()', ''))
                ax.set_ylabel(peak_ylabel or f'{peak_y} ({units_attr.get(peak_y, "")})'.replace(' ()', ''))
                ax.set_title(peak_title or f'({_panel_letter(n_p)}) {peak_y} against {peak_x}', loc='left',
                             fontsize=7.5)
            fig.summary = pd.DataFrame(summary)
            self._hp_save(self, fig, out_dir, filename, filename_template, 'plot_load_duration_curves.png',
                          'plot_load_duration_curves', {'plot': 'load_duration_curves'}, dpi, close)
        return fig

    # ------------------------------------------------------------ adaptive comfort chart

    def plot_adaptive_comfort_chart(
            self,
            temperature: str = 'Zone Operative Temperature',
            running_mean: Union[str, dict] = 'auto',
            df: Optional[pd.DataFrame] = None,
            df_source: str = 'parametric_hourly',
            row: Optional[Union[str, Sequence[str]]] = None,
            row_labels: Optional[dict] = None,
            row_order: Optional[Sequence] = None,
            col: Optional[Union[str, Sequence[str]]] = 'epw',
            col_labels: Optional[dict] = None,
            col_order: Optional[Sequence] = None,
            hue: Optional[str] = None,
            hue_bins: Optional[Sequence[float]] = None,
            hue_labels: Optional[dict] = None,
            palette=None,
            scatter_filter: Optional[dict] = None,
            annotate_by: Optional[Union[str, Sequence[str]]] = None,
            annotate_labels: Optional[dict] = None,
            annotation_title: str = 'hours outside the band',
            comfort_standard: Union[str, dict, Callable] = 'EN16798-1',
            category: Optional[str] = 'II',
            applicability: Literal['clip', 'exclude', 'extend'] = 'clip',
            band_label: Optional[str] = None,
            point_size: float = 1.2,
            alpha: float = 0.4,
            ylim: Optional[Tuple[float, float]] = None,
            xlabel: Optional[str] = None,
            ylabel: Optional[str] = None,
            zone_aggregation: str = 'mean',
            panel_size: Tuple[float, float] = (3.55, 2.5),
            figsize: Optional[Tuple[float, float]] = None,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            out_dir: str = '.',
            filename: Optional[str] = None,
            filename_template: Optional[str] = None,
            dpi: int = 300,
            rc: Optional[dict] = None,
            close: bool = True,
    ):
        """Hourly indoor temperature against the running mean, with the limits of an adaptive comfort model.

        Useful for controls without temperature setpoints (aPMV) or to compare
        any control with a comfort criterion that is applied after simulation.

        Parameters
        ----------
        temperature : str
            Hourly indoor temperature (name or substring).
        running_mean : str or dict
            Column of the running mean, ``'auto'`` (the EnergyPlus running mean of
            ``comfort_standard``) or ``{epw: hourly values}`` (for example from
            :meth:`get_hourly_series_by_epw`).
        row, row_labels, row_order, col, col_labels, col_order
            Panel grid (for example rows by setpoint, columns by weather file).
        hue : str, optional
            Column (or hourly variable) colouring the points; ``hue_bins`` bins
            numeric values and ``hue_labels`` names the bins or values (for example
            the clothing schedule, ``hue_bins=[0, 0.75, 2]``).
        palette : list or dict, optional
            Colours of the hue groups.
        scatter_filter : dict, optional
            ``data_filter`` rules restricting the points drawn; the annotation
            still uses every simulation of the panel.
        annotate_by : str or list, optional
            Column(s) defining the simulations of a panel whose share of hours
            outside the band is written in the panel (one line per value).
        annotate_labels : dict, optional
            ``{value: label}`` for those lines.
        annotation_title : str
            First line of the annotation box.
        comfort_standard, category, applicability
            Comfort band of :func:`adaptive_comfort_band` (dashed lines).
        band_label : str, optional
            Legend text of the band.
        point_size, alpha, ylim, xlabel, ylabel
            Scatter and axes settings.
        zone_aggregation, panel_size, figsize
            Variable resolution and layout.
        data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Row filter.
        out_dir, filename, filename_template, dpi, rc, close
            Output settings.

        Returns
        -------
        matplotlib.figure.Figure
            With ``saved_path`` and ``summary`` (share of hours outside, above and
            below the band and median temperature per panel and annotation group).

        Examples
        --------
        >>> rm = sim_ex1.get_hourly_series_by_epw('CEN 15251 Adaptive Model Running Average')
        >>> sim_apmv.plot_adaptive_comfort_chart(running_mean=rm, row='PMV setpoint', col='epw',
        ...                                      hue='CLOTHING SCHEDULE', hue_bins=[0, 0.75, 2],
        ...                                      annotate_by='Adaptive cooling coefficient')
        """
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, 'plot_adaptive_comfort_chart')
        frame, units, labels = self._hp_frame(data, {'t': temperature}, zone_aggregation, 'kWh', False, None,
                                              'plot_adaptive_comfort_chart')
        if isinstance(running_mean, dict):
            frame['rm'] = self.attach_hourly_series_by_epw('_rm', running_mean, df=data[['epw', 'hour']] if 'hour'
                                                           in data.columns else data, inplace=False)['_rm'].to_numpy()
            rm_label = 'Running mean outdoor temperature (°C)'
        else:
            spec = running_mean
            if running_mean == 'auto':
                spec = _model_definition(comfort_standard).get('running_mean') if not callable(comfort_standard) \
                    or isinstance(comfort_standard, dict) else None
                if spec is None:
                    raise ValueError("running_mean='auto' needs a named comfort standard; give the column instead.")
            frame['rm'] = self._hp_series(data, spec, 'first', 'running_mean')[0].to_numpy(float)
            rm_label = 'Running mean outdoor temperature (°C)'
        lower, upper = adaptive_comfort_band(frame['rm'].to_numpy(), comfort_standard, category, applicability)
        frame['lo'], frame['up'] = lower, upper
        rlab, rows = self._hp_cases(data, frame, row, row_labels, row_order, 'plot_adaptive_comfort_chart')
        clab, cols = self._hp_cases(data, frame, col, col_labels, col_order, 'plot_adaptive_comfort_chart')
        if hue is not None:
            if hue in data.columns and hue_bins is None:
                hraw = data[hue]
            else:
                hraw = self._hp_series(data, hue, 'max', 'hue')[0] if hue not in data.columns else data[hue]
            if hue_bins is not None:
                binned = pd.cut(pd.to_numeric(hraw, errors='coerce'), hue_bins)
                cats_ = list(binned.cat.categories)
                # hue_labels may map the bin intervals, their position (0, 1...) or their text ('(0.0, 0.75]')
                names_by_bin = {}
                for k_b, b in enumerate(cats_):
                    lab_b = None
                    if hue_labels:
                        lab_b = hue_labels.get(b, hue_labels.get(k_b, hue_labels.get(str(b))))
                    names_by_bin[b] = str(lab_b) if lab_b is not None else str(b)
                hlab = binned.map(lambda b: names_by_bin.get(b, 'n/a')).astype(str)
            else:
                hlab = _group_labels(data, hue, hue_labels, 'hue')
            hnames = list(dict.fromkeys(hlab))
            if hue_bins is not None and hue_labels:
                order = [v for v in hue_labels.values() if v in hnames]
                hnames = order + [h for h in hnames if h not in order]
        else:
            hlab = pd.Series('Hours', index=data.index)
            hnames = ['Hours']
        hcol = _colours(hnames, palette if palette is not None else ['#0072B2', '#E69F00', '#009E73', '#D55E00'])
        draw_mask = np.ones(len(data), bool)
        if scatter_filter is not None:
            from accim.parametric_and_optimisation.utils import apply_data_filter
            kept, _ = apply_data_filter(df=data, data_filter=scatter_filter, case_sensitive=data_filter_case_sensitive,
                                        strict=data_filter_strict, on_empty='ignore', context='scatter_filter')
            draw_mask = data.index.isin(kept.index)
        alab = _group_labels(data, annotate_by, annotate_labels, 'annotate_by') if annotate_by is not None else None
        summary = []
        with plt.rc_context(self._hp_rc(rc)):
            fig, axes = plt.subplots(len(rows), len(cols), squeeze=False, sharex=True, sharey=True,
                                     layout='constrained',
                                     figsize=figsize or (panel_size[0] * len(cols), panel_size[1] * len(rows) + 0.5))
            letter = 0
            box = dict(boxstyle='round,pad=0.25', fc='white', ec='0.8', lw=0.5, alpha=0.9)
            for i, r in enumerate(rows):
                for j, c in enumerate(cols):
                    ax = axes[i, j]
                    pmask = ((rlab == r) & (clab == c)).to_numpy()
                    rm_p = frame['rm'].to_numpy()[pmask]
                    if rm_p.size:
                        xs = np.linspace(np.nanmin(rm_p), np.nanmax(rm_p), 200)
                        blo, bup = adaptive_comfort_band(xs, comfort_standard, category, applicability)
                        ax.plot(xs, bup, color='0.25', lw=1.0, ls='--',
                                label=band_label or (f'{comfort_standard} Cat. {category} limits'
                                                     if isinstance(comfort_standard, str) else 'Comfort limits'))
                        ax.plot(xs, blo, color='0.25', lw=1.0, ls='--')
                    for h in hnames:
                        m = pmask & draw_mask & (hlab == h).to_numpy()
                        ax.scatter(frame['rm'].to_numpy()[m], frame['t'].to_numpy()[m], s=point_size, color=hcol[h],
                                   alpha=alpha, lw=0, rasterized=True, label=h)
                    groups = [None] if alab is None else list(dict.fromkeys(alab[pmask]))
                    lines = []
                    for g in groups:
                        m = pmask if g is None else pmask & (alab == g).to_numpy()
                        t = frame['t'].to_numpy()[m]
                        lo, up = frame['lo'].to_numpy()[m], frame['up'].to_numpy()[m]
                        valid = np.isfinite(lo) & np.isfinite(up)
                        above = (t > up + 1e-9) & valid
                        below = (t < lo - 1e-9) & valid
                        nv = max(int(valid.sum()), 1)
                        rec = {'row': r, 'col': c, 'group': g, 'share_outside': float((above | below).sum() / nv),
                               'share_above': float(above.sum() / nv), 'share_below': float(below.sum() / nv),
                               'median_temperature': float(np.nanmedian(t)) if t.size else np.nan}
                        summary.append(rec)
                        lines.append(f'{g}: {100 * rec["share_outside"]:.1f}%' if g is not None
                                     else f'{100 * rec["share_outside"]:.1f}%')
                    if lines:
                        ax.text(0.03, 0.97, f'{annotation_title}\n' + '\n'.join(lines), transform=ax.transAxes,
                                ha='left', va='top', fontsize=6.8, bbox=box)
                    title = ', '.join(x for x in ([c] if col is not None else []) + ([r] if row is not None else []))
                    ax.set_title(f'({_panel_letter(letter)}) {title}'.strip(), loc='left', fontsize=8)
                    letter += 1
                    if j == 0:
                        ax.set_ylabel(ylabel or labels['t'])
                    if i == len(rows) - 1:
                        ax.set_xlabel(xlabel or rm_label)
            if ylim is not None:
                axes[0, 0].set_ylim(*ylim)
            handles, names = axes[0, 0].get_legend_handles_labels()
            handles = [handles[0]] + [Line2D([], [], ls='', marker='o', color=hcol[h], ms=5) for h in hnames]
            names = [names[0]] + hnames
            fig.legend(handles, names, loc='outside lower center', ncol=min(4, len(names)), frameon=False)
            fig.summary = pd.DataFrame(summary)
            self._hp_save(self, fig, out_dir, filename, filename_template, 'plot_adaptive_comfort_chart.png',
                          'plot_adaptive_comfort_chart', {'plot': 'adaptive_comfort_chart'}, dpi, close)
        return fig

    # ---------------------------------------------------------------- scatter matrices

    @staticmethod
    def _hp_matrix(cols, labels, lims, lower, upper, diag, figsize, ticks=None, ticklabels=None,
                   margins=(0.085, 0.985, 0.075, 0.9)):
        """Scatter-matrix layout; the diagonal draws on a twin axis so the left column keeps its row ticks."""
        n = len(cols)
        fig, axes = plt.subplots(n, n, figsize=figsize, squeeze=False)
        l, r, b, t = margins
        fig.subplots_adjust(left=l, right=r, bottom=b, top=t, wspace=0.08, hspace=0.08)
        ticks, ticklabels = ticks or {}, ticklabels or {}
        for i, yc in enumerate(cols):
            for j, xc in enumerate(cols):
                ax = axes[i, j]
                ax.set_xlim(lims[xc])
                ax.set_ylim(lims[yc])
                for s in ('top', 'right'):
                    ax.spines[s].set_visible(True)
                    ax.spines[s].set_color('0.75')
                if i == j:
                    ax.set_facecolor('#f6f6f4')
                    tw = ax.twinx()
                    tw.set_yticks([])
                    tw.grid(False)
                    for s in tw.spines.values():
                        s.set_visible(False)
                    diag(tw, xc)
                elif i > j:
                    lower(ax, xc, yc)
                else:
                    upper(ax, xc, yc)
                if xc in ticks:
                    ax.set_xticks(ticks[xc])
                    if xc in ticklabels:
                        ax.set_xticklabels(ticklabels[xc])
                if yc in ticks:
                    ax.set_yticks(ticks[yc])
                    if yc in ticklabels:
                        ax.set_yticklabels(ticklabels[yc])
                ax.set_xlim(lims[xc])
                ax.set_ylim(lims[yc])
                ax.tick_params(length=2, pad=1.5)
                if i < n - 1:
                    ax.tick_params(labelbottom=False)
                else:
                    ax.set_xlabel(labels[xc])
                if j > 0:
                    ax.tick_params(labelleft=False)
                else:
                    ax.set_ylabel(labels[yc])
        fig.align_ylabels(axes[:, 0])
        return fig, axes

    def plot_hourly_scatter_matrix(
            self,
            variables: Union[Sequence[str], Dict[str, str]],
            df: Optional[pd.DataFrame] = None,
            df_source: str = 'parametric_hourly',
            hue: Optional[Union[str, Sequence[str]]] = None,
            hue_labels: Optional[dict] = None,
            hue_order: Optional[Sequence] = None,
            palette=None,
            linestyles: Optional[dict] = None,
            weather_variables: Optional[Sequence[str]] = None,
            weather_by: str = 'epw',
            weather_labels: Optional[dict] = None,
            weather_colors: Optional[dict] = None,
            labels: Optional[dict] = None,
            limits: Optional[dict] = None,
            n_sample: int = 2500,
            upper: Literal['hdr', 'scatter', 'none'] = 'hdr',
            hdr_levels: Sequence[float] = (0.5, 0.9),
            bins: int = 45,
            seed: int = 1,
            note: Optional[Union[str, Callable]] = None,
            zone_aggregation: str = 'mean',
            energy_unit: str = 'kWh',
            normalize_per_m2: bool = False,
            floor_area: Optional[float] = None,
            figsize: Tuple[float, float] = (7.1, 7.1),
            legend_ncol: Optional[int] = None,
            title: Optional[str] = None,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            out_dir: str = '.',
            filename: Optional[str] = None,
            filename_template: Optional[str] = None,
            dpi: int = 300,
            rc: Optional[dict] = None,
            close: bool = True,
    ):
        """Scatter matrix of hourly values for several groups (cases).

        Lower panels show a random sample of hours of each group, upper panels the
        contours enclosing the densest fractions of all hours (``hdr_levels``) and
        diagonal panels the distribution of each variable. Variables that depend
        only on the weather file (``weather_variables``) are drawn once per weather
        file, in grey.

        Parameters
        ----------
        variables : list or dict
            Hourly variables (names or substrings); ``{key: variable}`` lets
            ``labels`` and ``limits`` refer to short keys.
        hue, hue_labels, hue_order, palette, linestyles
            Groups compared in each panel.
        weather_variables : list, optional
            Keys of ``variables`` that depend only on the weather file.
        weather_by, weather_labels, weather_colors
            Column identifying the weather file, its labels and colours.
        labels, limits : dict, optional
            ``{key: axis label}`` and ``{key: (min, max)}``.
        n_sample : int
            Hours drawn per group in the lower panels.
        upper : {'hdr', 'scatter', 'none'}
            Content of the upper panels.
        hdr_levels : sequence of float
            Fractions of hours enclosed by the contours.
        bins : int
            Bins of the diagonal histograms.
        seed : int
            Random seed of the sample.
        note : str or callable, optional
            Text for the bottom-right panel, or ``callable(summary) -> str``.
        zone_aggregation, energy_unit, normalize_per_m2, floor_area
            Variable resolution and units.
        figsize, legend_ncol, title
            Layout.
        data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Row filter.
        out_dir, filename, filename_template, dpi, rc, close
            Output settings.

        Returns
        -------
        matplotlib.figure.Figure
            With ``saved_path`` and ``summary`` (median, interquartile range and
            Spearman correlations of each group).

        Examples
        --------
        >>> sim.plot_hourly_scatter_matrix(
        ...     {'tout': 'Outdoor Air Drybulb', 'rm': 'CEN 15251 Adaptive Model Running Average',
        ...      'top': 'Zone Operative Temperature', 'e': 'Electricity:HVAC'},
        ...     hue=['ComfMod', 'HVACmode'], weather_variables=['tout', 'rm'])
        """
        var_map = dict(variables) if isinstance(variables, dict) else {str(v): v for v in variables}
        keys = list(var_map)
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, 'plot_hourly_scatter_matrix')
        frame, units, deflabels = self._hp_frame(data, var_map, zone_aggregation, energy_unit, normalize_per_m2,
                                                 floor_area, 'plot_hourly_scatter_matrix')
        hlab, groups = self._hp_cases(data, frame, hue, hue_labels, hue_order, 'plot_hourly_scatter_matrix')
        colours = _colours(groups, palette)
        styles = linestyles or {}
        weather = set(weather_variables or [])
        wlab = _group_labels(data, weather_by, weather_labels, 'weather_by') if weather else None
        wnames = _ordered(pd.unique(wlab[hlab.isin(groups)]), None) if weather else []
        wcols = weather_colors or dict(zip(wnames, ['0.55', '0.15', '0.35', '0.7', '0.25']))
        labels = {**deflabels, **(labels or {})}
        rng = np.random.default_rng(seed)
        series = {}
        for g in groups:
            m = (hlab == g).to_numpy()
            series[g] = {k: frame[k].to_numpy()[m] for k in keys}
        sample = {g: rng.choice(len(series[g][keys[0]]), min(n_sample, len(series[g][keys[0]])), replace=False)
                  for g in groups}
        wseries = {}
        for w in wnames:
            first = next(g for g in groups if ((hlab == g) & (wlab == w)).any())
            m = ((hlab == first) & (wlab == w)).to_numpy()
            sims = frame.loc[m, '_sim'].unique()
            m = m & (frame['_sim'] == sims[0]).to_numpy()
            wseries[w] = {k: frame[k].to_numpy()[m] for k in keys}
        lims = dict(limits or {})
        for k in keys:
            if k not in lims:
                lims[k] = _limits([series[g][k] for g in groups])
        summary = []
        for g in groups:
            rec = {'group': g}
            for k in keys:
                v = series[g][k]
                rec[f'{k}_median'] = float(np.nanmedian(v))
                rec[f'{k}_iqr'] = float(np.nanpercentile(v, 75) - np.nanpercentile(v, 25))
            for a in range(len(keys)):
                for b in range(a + 1, len(keys)):
                    rec[f'rho_{keys[a]}_{keys[b]}'] = _spearman(series[g][keys[a]], series[g][keys[b]])
            summary.append(rec)
        summary = pd.DataFrame(summary)

        def is_weather(*ks):
            return bool(weather) and all(k in weather for k in ks)

        def lower(ax, xc, yc):
            if is_weather(xc, yc):
                for w in wnames:
                    idx = rng.choice(len(wseries[w][xc]), min(n_sample, len(wseries[w][xc])), replace=False)
                    ax.scatter(wseries[w][xc][idx], wseries[w][yc][idx], s=1.2, c=wcols[w], alpha=0.35,
                               linewidths=0, rasterized=True)
                return
            xs, ys, cs = [], [], []
            for g in groups:
                idx = sample[g]
                xs.append(series[g][xc][idx])
                ys.append(series[g][yc][idx])
                cs += [colours[g]] * len(idx)
            x, y, c = np.concatenate(xs), np.concatenate(ys), np.array(cs, dtype=object)
            order = rng.permutation(len(x))  # no group systematically on top
            ax.scatter(x[order], y[order], s=1.2, c=list(c[order]), alpha=0.35, linewidths=0, rasterized=True)

        def upper_fn(ax, xc, yc):
            if upper == 'none':
                ax.set_visible(False)
                return
            if is_weather(xc, yc):
                for w in wnames:
                    if upper == 'hdr':
                        _hdr_contours(ax, wseries[w][xc], wseries[w][yc], lims[xc], lims[yc], wcols[w],
                                      levels=hdr_levels)
                    else:
                        ax.scatter(wseries[w][yc][:n_sample], wseries[w][xc][:n_sample], s=1.2, c=wcols[w], alpha=0.3)
                return
            for g in groups:
                if upper == 'hdr':
                    _hdr_contours(ax, series[g][xc], series[g][yc], lims[xc], lims[yc], colours[g],
                                  styles.get(g, '-'), levels=hdr_levels)
                else:
                    idx = sample[g]
                    ax.scatter(series[g][xc][idx], series[g][yc][idx], s=1.2, c=colours[g], alpha=0.3,
                               linewidths=0, rasterized=True)

        def diag(tw, k):
            edges = np.linspace(*lims[k], bins + 1)
            tops = []
            items = ([(wcols[w], '-', wseries[w][k]) for w in wnames] if k in weather
                     else [(colours[g], styles.get(g, '-'), series[g][k]) for g in groups])
            for colr, ls, v in items:
                h, e = np.histogram(v[np.isfinite(v)], bins=edges)
                h = h / max(h.sum(), 1)
                tw.step(e[:-1], h, where='post', color=colr, ls=ls, lw=1.1)
                srt = np.sort(h)
                tops.append(srt[-2] if (len(srt) > 1 and srt[-1] > 3 * srt[-2]) else srt[-1])
            tw.set_ylim(0, 1.15 * max(max(tops), 1e-9))

        with plt.rc_context(self._hp_rc({'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5, 'axes.labelsize': 7.2,
                                         **(rc or {})})):
            n_leg = len(groups) + len(wnames)
            ncol = legend_ncol or min(n_leg, 5)
            n_lines = int(np.ceil(n_leg / ncol))
            top = 0.955 - 0.025 * (n_lines - 1) - (0.035 if title else 0)
            fig, axes = self._hp_matrix(keys, labels, lims, lower, upper_fn, diag, figsize,
                                        margins=(0.085, 0.985, 0.075, top))
            handles = [Line2D([], [], color=colours[g], ls=styles.get(g, '-'), lw=1.4, label=g) for g in groups]
            handles += [Line2D([], [], color=wcols[w], lw=1.4,
                               label='Weather variables' + ('' if len(wnames) == 1 else f', {w}')) for w in wnames]
            fig.legend(handles=handles, loc='upper center', ncol=ncol, frameon=False, bbox_to_anchor=(0.53, 0.995),
                       fontsize=7)
            if title:
                fig.text(0.53, top + 0.03, title, ha='center', va='center', fontsize=7.2, color='0.25')
            if note is not None:
                text = note(summary) if callable(note) else str(note)
                axes[-1, -1].text(0.97, 0.95, text, transform=axes[-1, -1].transAxes, ha='right', va='top',
                                  fontsize=5.6, color='0.3')
            fig.summary = summary
            self._hp_save(self, fig, out_dir, filename, filename_template, 'plot_hourly_scatter_matrix.png',
                          'plot_hourly_scatter_matrix', {'plot': 'hourly_scatter_matrix'}, dpi, close)
        return fig

    def plot_results_scatter_matrix(
            self,
            columns: Sequence[str],
            df: Optional[pd.DataFrame] = None,
            df_source: str = 'hourly_indicators',
            hue: Optional[Union[str, Sequence[str]]] = None,
            hue_labels: Optional[dict] = None,
            hue_order: Optional[Sequence] = None,
            palette=None,
            marker_by: Optional[str] = None,
            marker_styles: Optional[dict] = None,
            upper: Literal['spearman', 'pearson', 'scatter', 'hdr', 'none'] = 'spearman',
            diag: Literal['hist', 'stacked', 'none'] = 'hist',
            color_by: Optional[str] = None,
            cmap: str = 'viridis',
            color_range: Optional[Tuple[float, float]] = None,
            color_label: Optional[str] = None,
            log_columns: Optional[Sequence[str]] = None,
            percent_columns: Optional[Sequence[str]] = None,
            labels: Optional[dict] = None,
            limits: Optional[dict] = None,
            bins: int = 30,
            legend_counts: bool = True,
            figsize: Tuple[float, float] = (7.1, 7.1),
            title: Optional[str] = None,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            out_dir: str = '.',
            filename: Optional[str] = None,
            filename_template: Optional[str] = None,
            dpi: int = 300,
            rc: Optional[dict] = None,
            close: bool = True,
    ):
        """Scatter matrix of evaluation-level results (parameters, outputs or hourly indicators).

        Parameters
        ----------
        columns : list of str
            Columns of the table (parameters, annual results, indicators of
            :meth:`compute_hourly_indicators`...).
        df, df_source
            Table with one row per evaluation (default: ``self.hourly_indicators``).
        hue, hue_labels, hue_order, palette
            Categorical grouping colouring the lower panels and the histograms
            (for example a control family or ``'comfort_outcome'``).
        marker_by : str, optional
            Column defining marker styles (for example sampled versus optimised
            evaluations); ``marker_styles`` = ``{value: {'s': size, 'edgecolor':
            'k' or 'none', 'alpha': a, 'label': text}}``.
        upper : {'spearman', 'pearson', 'scatter', 'hdr', 'none'}
            Upper panels: correlation coefficient of each group, points coloured
            by ``color_by`` (or by group), density contours, or nothing.
        diag : {'hist', 'stacked', 'none'}
            Histograms per group (step lines) or stacked bars.
        color_by, cmap, color_range, color_label
            Continuous colouring of the upper scatter panels, with a colour bar.
        log_columns : list, optional
            Columns drawn as log10(1 + value) with ticks in original units.
        percent_columns : list, optional
            Shares (0-1) drawn as percentages.
        labels, limits : dict, optional
            Axis labels and limits by column.
        bins : int
            Histogram bins.
        legend_counts : bool
            Add the number of evaluations of each group to the legend.
        figsize, title
            Layout.
        data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Row filter.
        out_dir, filename, filename_template, dpi, rc, close
            Output settings.

        Returns
        -------
        matplotlib.figure.Figure
            With ``saved_path`` and ``summary`` (correlations per group and pair).

        Examples
        --------
        >>> sim.plot_results_scatter_matrix(['CustAST_m', 'CustAST_n', 'E_HVAC', 'share_outside_II'],
        ...                                 hue='comfort_outcome', upper='scatter', color_by='T_mean',
        ...                                 percent_columns=['share_outside_II'])
        """
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, 'plot_results_scatter_matrix')
        cols = list(columns)
        missing = [c for c in cols + ([color_by] if color_by else []) if c not in data.columns]
        if missing:
            raise KeyError(f'plot_results_scatter_matrix: columns not found {missing}')
        plot = pd.DataFrame(index=data.index)
        log_columns, percent_columns = set(log_columns or []), set(percent_columns or [])
        units = getattr(data, 'attrs', {}).get('units', {})
        deflabels = {}
        for c in cols:
            v = pd.to_numeric(data[c], errors='coerce')
            if c in percent_columns:
                v = 100 * v
            if c in log_columns:
                v = np.log10(1 + v.clip(lower=0))
            plot[c] = v
            unit = '%' if c in percent_columns else units.get(c, '')
            deflabels[c] = f'{c} ({unit})' if unit and unit != '-' else c
        labels = {**deflabels, **(labels or {})}
        hlab = _group_labels(data, hue, hue_labels, 'hue') if hue is not None else pd.Series('all', index=data.index)
        groups = _ordered(pd.unique(hlab), hue_order, hue_labels)
        colours = _colours(groups, palette)
        mlab = data[marker_by] if marker_by else pd.Series('all', index=data.index)
        mvalues = list(pd.unique(mlab))
        mstyles = {}
        for k, mv in enumerate(mvalues):
            st = dict((marker_styles or {}).get(mv, {}))
            st.setdefault('s', 6 if len(mvalues) == 1 else (14 if k else 5))
            st.setdefault('edgecolor', 'none' if len(mvalues) == 1 or k == 0 else 'k')
            st.setdefault('alpha', 0.75)
            mstyles[mv] = st
        lims = dict(limits or {})
        for c in cols:
            if c not in lims:
                lims[c] = (-4.0, 104.0) if c in percent_columns else _limits([plot[c].to_numpy()])
        ticks, ticklabels = {}, {}
        for c in log_columns:
            lo, hi = lims[c]
            dec = [0] + [10 ** k for k in range(1, 9) if np.log10(1 + 10 ** k) <= hi + 1e-9]
            ticks[c] = list(np.log10(1 + np.array(dec, float)))
            ticklabels[c] = ['0' if d == 0 else ('1' if d == 1 else ('10' if d == 10 else f'10$^{{{int(np.log10(d))}}}$'))
                             for d in dec]
        norm = None
        if color_by is not None:
            cvals = pd.to_numeric(data[color_by], errors='coerce')
            norm = Normalize(*(color_range or (float(cvals.min()), float(cvals.max()))))
        summary = []
        for g in groups:
            m = (hlab == g).to_numpy()
            rec = {'group': g, 'n': int(m.sum())}
            for a in range(len(cols)):
                for b in range(a + 1, len(cols)):
                    rec[f'rho_{cols[a]}__{cols[b]}'] = _spearman(plot[cols[a]][m], plot[cols[b]][m])
            summary.append(rec)
        summary = pd.DataFrame(summary)

        def lower(ax, xc, yc):
            for k, g in enumerate(groups):
                for mv in mvalues:
                    m = ((hlab == g) & (mlab == mv)).to_numpy()
                    st = mstyles[mv]
                    ax.scatter(plot[xc][m], plot[yc][m], s=st['s'], c=colours[g], alpha=st['alpha'],
                               edgecolors=st['edgecolor'], linewidths=0.3, rasterized=True, zorder=2 + k * 0.01)

        def upper_fn(ax, xc, yc):
            if upper == 'none':
                ax.set_visible(False)
                return
            if upper in ('spearman', 'pearson'):
                ax.grid(False)
                for k, g in enumerate(groups):
                    m = (hlab == g).to_numpy()
                    if upper == 'spearman':
                        rho = _spearman(plot[xc][m], plot[yc][m])
                    else:
                        rho = pd.Series(plot[xc][m]).corr(pd.Series(plot[yc][m]))
                    yy = 0.82 - (0.64 / max(len(groups) - 1, 1)) * k if len(groups) > 1 else 0.5
                    ax.scatter([0.16], [yy], s=22, c=[colours[g]], transform=ax.transAxes, clip_on=False,
                               edgecolors='none')
                    ax.text(0.27, yy, f'ρ = {rho:+.2f}' if upper == 'spearman' else f'r = {rho:+.2f}',
                            transform=ax.transAxes, va='center', fontsize=6.6, color='0.15')
                return
            if upper == 'hdr':
                for g in groups:
                    m = (hlab == g).to_numpy()
                    _hdr_contours(ax, plot[xc][m], plot[yc][m], lims[xc], lims[yc], colours[g], bins=40)
                return
            order = data.sort_values(color_by).index if color_by else data.index
            for mv in mvalues:
                idx = [i for i in order if _values_equal(mlab[i], mv) or mlab[i] == mv]
                st = mstyles[mv]
                if color_by:
                    ax.scatter(plot.loc[idx, xc], plot.loc[idx, yc], s=st['s'], c=data.loc[idx, color_by], cmap=cmap,
                               norm=norm, alpha=0.85, edgecolors=st['edgecolor'], linewidths=0.3, rasterized=True)
                else:
                    ax.scatter(plot.loc[idx, xc], plot.loc[idx, yc], s=st['s'], c=[colours[g] for g in hlab[idx]],
                               alpha=0.85, edgecolors=st['edgecolor'], linewidths=0.3, rasterized=True)

        def diag_fn(tw, c):
            if diag == 'none':
                return
            edges = np.linspace(*lims[c], bins + 1)
            if diag == 'stacked':
                stack = [plot[c][(hlab == g).to_numpy()].dropna().to_numpy() for g in groups]
                tw.hist(stack, bins=edges, histtype='barstacked', color=[colours[g] for g in groups], rwidth=0.88,
                        alpha=0.85)
                return
            tops = []
            for g in groups:
                v = plot[c][(hlab == g).to_numpy()].dropna().to_numpy()
                h, e = np.histogram(v, bins=edges)
                h = h / max(h.sum(), 1)
                tw.step(e[:-1], h, where='post', color=colours[g], lw=1.2)
                tops.append(h.max() if len(h) else 0)
            tw.set_ylim(0, 1.12 * max(max(tops), 1e-9))

        with plt.rc_context(self._hp_rc({'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5, 'axes.labelsize': 7.2,
                                         **(rc or {})})):
            bottom = 0.135 if (upper == 'scatter' and color_by) else 0.075
            two_lines = marker_by and len(mvalues) > 1 and marker_by not in _as_list(hue)
            top = (0.925 if two_lines else 0.945) - (0.035 if title else 0)
            fig, axes = self._hp_matrix(cols, labels, lims, lower, upper_fn, diag_fn, figsize, ticks, ticklabels,
                                        margins=(0.085, 0.985, bottom, top))
            counts = hlab.value_counts()
            handles = []
            if hue is not None:
                handles += [Patch(color=colours[g], label=f'{g}: {counts.get(g, 0)}' if legend_counts else g)
                            for g in groups]
            if marker_by and len(mvalues) > 1 and marker_by not in _as_list(hue):
                mc = mlab.value_counts()
                for mv in mvalues:
                    st = mstyles[mv]
                    lab = st.get('label', str(mv))
                    handles.append(Line2D([], [], ls='', marker='o', color='0.55',
                                          mec='k' if st['edgecolor'] != 'none' else '0.55', mew=0.4,
                                          ms=2.2 + st['s'] ** 0.5 * 0.6,
                                          label=f'{lab}: {mc.get(mv, 0)}' if legend_counts else lab))
            if handles:
                fig.legend(handles=handles, loc='upper center', ncol=3, frameon=False, bbox_to_anchor=(0.53, 0.997),
                           fontsize=6.8, handlelength=1.2, columnspacing=1.0)
            if title:
                fig.text(0.53, top + 0.025, title, ha='center', va='center', fontsize=7.2, color='0.25')
            if upper == 'scatter' and color_by:
                cax = fig.add_axes([0.25, 0.03, 0.5, 0.012])
                cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation='horizontal')
                cb.set_label(color_label or f'Upper panels: {color_by}', fontsize=7)
                cb.ax.tick_params(labelsize=6.5)
            fig.summary = summary
            self._hp_save(self, fig, out_dir, filename, filename_template, 'plot_results_scatter_matrix.png',
                          'plot_results_scatter_matrix', {'plot': 'results_scatter_matrix'}, dpi, close)
        return fig

    # ---------------------------------------------------------- monthly distributions

    def plot_monthly_distributions(
            self,
            variable: str = 'Zone Operative Temperature',
            df: Optional[pd.DataFrame] = None,
            df_source: str = 'parametric_hourly',
            panel: Optional[Union[str, Sequence[str]]] = None,
            panel_labels: Optional[dict] = None,
            panel_order: Optional[Sequence] = None,
            palette=None,
            compare_by: Optional[str] = 'epw',
            compare_labels: Optional[dict] = None,
            compare_order: Optional[Sequence] = None,
            band: Optional[dict] = None,
            value_range: Optional[Tuple[float, float]] = None,
            bin_width: float = 0.2,
            smooth: float = 1.5,
            height: float = 1.2,
            xlim: Optional[Tuple[float, float]] = None,
            xticks: Optional[Sequence[float]] = None,
            xlabel: Optional[str] = None,
            zone_aggregation: str = 'mean',
            energy_unit: str = 'kWh',
            panel_width: float = 1.78,
            figsize: Optional[Tuple[float, float]] = None,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            out_dir: str = '.',
            filename: Optional[str] = None,
            filename_template: Optional[str] = None,
            dpi: int = 300,
            rc: Optional[dict] = None,
            close: bool = True,
    ):
        """Monthly distributions (ridgelines) of an hourly variable.

        Each panel is a group (for example a control strategy) with one smoothed
        distribution per month. With ``compare_by`` (weather files by default) the
        first value is drawn filled and the others as lines, so two climates can be
        compared month by month.

        Parameters
        ----------
        variable : str
            Hourly variable (name or substring).
        panel, panel_labels, panel_order, palette
            One panel per group; ``palette`` gives the fill colours.
        compare_by, compare_labels, compare_order
            Column compared within each panel (first value filled, the rest as lines).
        band : dict, optional
            Monthly mean of an adaptive comfort band drawn under each month:
            ``{'running_mean': column, 'auto' or {epw: values}, 'standard':
            'EN16798-1', 'category': 'II', 'applicability': 'clip'}``.
        value_range, bin_width, smooth, height
            Histogram range, bin width, Gaussian smoothing (in bins) and height of
            each distribution (in month spacings).
        xlim, xticks, xlabel
            Axes settings.
        zone_aggregation, energy_unit, panel_width, figsize
            Variable resolution and layout.
        data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Row filter.
        out_dir, filename, filename_template, dpi, rc, close
            Output settings.

        Returns
        -------
        matplotlib.figure.Figure
            With ``saved_path`` and ``summary`` (monthly median and, with ``band``,
            shares of hours above and below the band per panel, value of
            ``compare_by`` and month).

        Examples
        --------
        >>> sim.plot_monthly_distributions('Zone Operative Temperature', panel=['ComfMod', 'HVACmode'],
        ...                                compare_by='epw', band={'running_mean': 'auto', 'category': 'II'})
        """
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, 'plot_monthly_distributions')
        frame, units, labels = self._hp_frame(data, {'v': variable}, zone_aggregation, energy_unit, False, None,
                                              'plot_monthly_distributions')
        cal = _calendar(int(frame['_h'].max()) + 1)
        frame['month'] = cal['month'].to_numpy()[frame['_h'].to_numpy()]
        plab, panels = self._hp_cases(data, frame, panel, panel_labels, panel_order, 'plot_monthly_distributions')
        clab, comps = self._hp_cases(data, frame, compare_by, compare_labels, compare_order,
                                     'plot_monthly_distributions')
        fills = _colours(panels, palette)
        if band is not None:
            standard = band.get('standard', 'EN16798-1')
            rm_spec = band.get('running_mean', 'auto')
            if isinstance(rm_spec, dict):
                rm = self.attach_hourly_series_by_epw('_rm', rm_spec, df=data[['epw', 'hour']] if 'hour' in data.columns
                                                      else data, inplace=False)['_rm'].to_numpy()
            else:
                spec = _model_definition(standard)['running_mean'] if rm_spec == 'auto' else rm_spec
                rm = self._hp_series(data, spec, 'first', 'band running_mean')[0].to_numpy(float)
            lo, up = adaptive_comfort_band(rm, standard, band.get('category', 'II'), band.get('applicability', 'clip'))
            frame['lo'], frame['up'] = lo, up
        vals = frame['v'].to_numpy()
        vr = value_range or (np.floor(np.nanmin(vals)) - 1, np.ceil(np.nanmax(vals)) + 1)
        edges = np.arange(vr[0], vr[1] + bin_width / 2, bin_width)
        xc = 0.5 * (edges[1:] + edges[:-1])
        band_greys = ['0.78', '0.35', '0.55', '0.2']
        summary = []
        with plt.rc_context(self._hp_rc(rc)):
            fig, axes = plt.subplots(1, len(panels), squeeze=False, sharey=True,
                                     figsize=figsize or (panel_width * len(panels) + 0.4, 6.4))
            axes = axes[0]
            fig.subplots_adjust(left=0.1, right=0.99, bottom=0.12, top=0.955, wspace=0.08)
            for j, p in enumerate(panels):
                ax = axes[j]
                for m in range(1, 13):
                    base = 12 - m
                    ax.axhline(base, color='0.82', lw=0.5, zorder=0)
                    if band is not None:
                        for k, cname in enumerate(comps):
                            sel = (plab == p).to_numpy() & (clab == cname).to_numpy() & (frame['month'] == m).to_numpy()
                            if sel.any():
                                b_lo, b_up = np.nanmean(frame['lo'].to_numpy()[sel]), np.nanmean(frame['up'].to_numpy()[sel])
                                ax.plot([b_lo, b_up], [base - 0.12 * k, base - 0.12 * k], color=band_greys[k % 4],
                                        lw=3.2 if k == 0 else 0.8, solid_capstyle='butt', zorder=1)
                    for k, cname in enumerate(comps):
                        sel = (plab == p).to_numpy() & (clab == cname).to_numpy() & (frame['month'] == m).to_numpy()
                        v = vals[sel]
                        v = v[np.isfinite(v)]
                        if v.size == 0:
                            continue
                        h, _ = np.histogram(v, bins=edges)
                        h = _smooth(h.astype(float), smooth) if smooth else h.astype(float)
                        h = height * h / h.max() if h.max() > 0 else h
                        if k == 0:
                            ax.fill_between(xc, base, base + h, color=fills[p], alpha=0.75, lw=0, zorder=2 + 0.01 * m)
                        else:
                            ax.plot(xc, np.where(h > 0.015, base + h, np.nan), color=['k', '0.3', '0.5'][(k - 1) % 3],
                                    lw=0.7, zorder=3 + 0.01 * m)
                        rec = {'panel': p, 'compare': cname, 'month': m, 'median': float(np.median(v))}
                        if band is not None:
                            lo_m, up_m = frame['lo'].to_numpy()[sel], frame['up'].to_numpy()[sel]
                            rec['share_above'] = float(np.mean(frame['v'].to_numpy()[sel] > up_m))
                            rec['share_below'] = float(np.mean(frame['v'].to_numpy()[sel] < lo_m))
                        summary.append(rec)
                ax.set_title(p, fontsize=7.5, fontweight='bold')
                if xlim is not None:
                    ax.set_xlim(*xlim)
                if xticks is not None:
                    ax.set_xticks(xticks)
                ax.grid(axis='y', visible=False)
                ax.set_xlabel(xlabel or labels['v'])
            axes[0].set_yticks(range(12))
            axes[0].set_yticklabels(MONTH_NAMES[::-1])
            axes[0].set_ylim(-0.4, 12.6)
            handles = [Patch(color='0.45', alpha=0.75, label=f'{comps[0]} (filled)')]
            handles += [Line2D([], [], color=['k', '0.3', '0.5'][(k - 1) % 3], lw=0.8, label=f'{c} (line)')
                        for k, c in enumerate(comps) if k > 0]
            if band is not None:
                cat = band.get('category', 'II')
                handles += [Line2D([], [], color=band_greys[k % 4], lw=3.2 if k == 0 else 0.8,
                                   label=f'Cat. {cat} band, monthly mean ({c})') for k, c in enumerate(comps)]
            fig.legend(handles=handles, loc='lower center', ncol=min(4, len(handles)), frameon=False, fontsize=6.6,
                       bbox_to_anchor=(0.54, 0.0))
            fig.summary = pd.DataFrame(summary)
            self._hp_save(self, fig, out_dir, filename, filename_template, 'plot_monthly_distributions.png',
                          'plot_monthly_distributions', {'plot': 'monthly_distributions'}, dpi, close)
        return fig

    # ------------------------------------------------------------------ comfort screening

    def plot_comfort_screening(
            self,
            df: Optional[pd.DataFrame] = None,
            df_source: str = 'hourly_indicators',
            x: str = 'E_HVAC',
            y: str = 'share_outside_II',
            color: Optional[str] = 'T_mean',
            row: Optional[str] = None,
            row_labels: Optional[dict] = None,
            row_order: Optional[Sequence] = None,
            col: Optional[str] = 'epw',
            col_labels: Optional[dict] = None,
            col_order: Optional[Sequence] = None,
            marker_by: Optional[str] = None,
            marker_styles: Optional[dict] = None,
            highlight: Optional[str] = 'pareto-optimal',
            highlight_label: str = 'Non-dominated',
            selections: Optional[dict] = None,
            selection_markers: Optional[dict] = None,
            match_on: Optional[Sequence[str]] = None,
            threshold: Optional[float] = 0.05,
            y_as_percent: bool = True,
            mark_best: bool = True,
            best_format: str = '{x:.1f}',
            best_legend_label: Optional[str] = None,
            cmap: str = 'viridis',
            color_range: Optional[Tuple[float, float]] = None,
            row_ylims: Optional[dict] = None,
            annotations: Optional[List[dict]] = None,
            xlabel: Optional[str] = None,
            ylabel: Optional[str] = None,
            color_label: Optional[str] = None,
            panel_size: Tuple[float, float] = (3.55, 2.35),
            figsize: Optional[Tuple[float, float]] = None,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
            out_dir: str = '.',
            filename: Optional[str] = None,
            filename_template: Optional[str] = None,
            dpi: int = 300,
            rc: Optional[dict] = None,
            close: bool = True,
    ):
        """Screen evaluations against a tolerance of hours outside a comfort band.

        Each point is an evaluation (for example from
        :meth:`compute_hourly_indicators`), with ``x`` (energy) against ``y``
        (share of hours outside the band) and coloured by ``color``. A dashed line
        marks ``threshold`` and a ring the lowest ``x`` among the evaluations at or
        below it. Non-dominated evaluations (``highlight``) and selected solutions
        (``selections``, for example the knee point and TOPSIS choices) can be
        marked, so the comfort criterion can be compared with the objectives of the
        original study.

        Parameters
        ----------
        df, df_source
            Table with one row per evaluation (default ``self.hourly_indicators``);
            several studies can be concatenated, with a column identifying them.
        x, y, color : str
            Columns of the axes and of the colour scale (``color=None`` uses grey).
        row, row_labels, row_order, col, col_labels, col_order
            Panel grid (for example rows by control family, columns by weather file).
        marker_by : str, optional
            Column giving the marker style of each evaluation; ``marker_styles`` =
            ``{value: {'marker': 'o', 's': 22, 'edgecolor': 'none', 'alpha': 0.9,
            'label': text}}`` (for example sampled designs larger than optimisation
            evaluations).
        highlight : str, optional
            Boolean column drawn with black edges (default ``'pareto-optimal'``;
            ignored if absent).
        highlight_label : str
            Legend text of ``highlight``.
        selections : dict, optional
            ``{label: rows}`` marked with open symbols, where ``rows`` is a boolean
            column name, a list of index labels or a dataframe matched on
            ``match_on`` (for example the output of ``get_best_compromise_solution``).
        selection_markers : dict, optional
            ``{label: {'marker': 'D', 's': 46}}``.
        match_on : list of str, optional
            Columns used to match selection dataframes (default: the columns shared
            with ``df`` among the parameters and ``epw``).
        threshold : float, optional
            Tolerance on ``y`` (in the units of ``y``; 0.05 = 5 % of the hours).
        y_as_percent : bool
            Draw ``y`` multiplied by 100.
        mark_best : bool
            Ring and label the lowest ``x`` with ``y <= threshold`` in each panel.
        best_format : str
            Format of that label (``{x}``).
        best_legend_label : str, optional
            Legend text of the ring (default: 'Lowest {x}, ≤ threshold').
        cmap, color_range, color_label
            Colour scale.
        row_ylims : dict, optional
            ``{row label: (ymin, ymax)}``.
        annotations : list of dict, optional
            Free text in a panel: ``{'row': label, 'col': label, 'text': str,
            'xy': (x, y) in data units (``y`` as drawn), 'xytext': (x, y) in axes
            fraction (optional, draws a line to ``xy``), 'kwargs': {...}}``.
        xlabel, ylabel, panel_size, figsize
            Axes and layout.
        data_filter, data_filter_case_sensitive, data_filter_strict, data_filter_on_empty
            Row filter.
        out_dir, filename, filename_template, dpi, rc, close
            Output settings.

        Returns
        -------
        matplotlib.figure.Figure
            With ``saved_path`` and ``summary``: per panel, the number of
            evaluations, how many meet the threshold (and how many highlighted ones
            do), the best evaluation and the ``y`` of each selection.

        Examples
        --------
        >>> knee = sim.get_best_compromise_solution(method='knee_point')
        >>> sim.plot_comfort_screening(x='E_HVAC', y='share_outside_II', col='epw',
        ...                            selections={'Knee point': knee}, selection_markers={'Knee point': {'marker': 'D'}})
        """
        data = self._hp_source(df, df_source, data_filter, data_filter_case_sensitive, data_filter_strict,
                               data_filter_on_empty, 'plot_comfort_screening')
        for c in [x, y] + ([color] if color else []):
            if c not in data.columns:
                raise KeyError(f"plot_comfort_screening: column '{c}' not found.")
        data = data.reset_index(drop=False).rename(columns={'index': '_orig_index'})
        yscale = 100.0 if y_as_percent else 1.0
        rlab = _group_labels(data, row, row_labels, 'row') if row else pd.Series('all', index=data.index)
        clab = _group_labels(data, col, col_labels, 'col') if col else pd.Series('all', index=data.index)
        rows = _ordered(pd.unique(rlab), row_order, row_labels)
        cols = _ordered(pd.unique(clab), col_order, col_labels)
        mlab = data[marker_by] if marker_by else pd.Series('all', index=data.index)
        mvalues = list(pd.unique(mlab))
        mstyles = {}
        for mv in mvalues:
            st = dict((marker_styles or {}).get(mv, {}))
            st.setdefault('marker', 'o')
            st.setdefault('s', 20)
            st.setdefault('edgecolor', 'none')
            st.setdefault('alpha', 0.85)
            st.setdefault('label', str(mv))
            mstyles[mv] = st
        hl = data[highlight].fillna(False).astype(bool) if highlight and highlight in data.columns else None
        sel_masks = {}
        params = getattr(self, 'parameters_list', None)
        for lab, rows_spec in (selections or {}).items():
            if isinstance(rows_spec, str):
                sel_masks[lab] = data[rows_spec].fillna(False).astype(bool).to_numpy()
            elif isinstance(rows_spec, pd.DataFrame):
                sel_masks[lab] = _match_rows(data, rows_spec, match_on,
                                             [p.name for p in params] if params else None, exclude=(x, y, color))
            else:
                sel_masks[lab] = data['_orig_index'].isin(list(rows_spec)).to_numpy()
        default_sel = [{'marker': 'D', 's': 46}, {'marker': '*', 's': 120}, {'marker': 's', 's': 46},
                       {'marker': 'P', 's': 60}]
        smk = {lab: {**default_sel[k % 4], **(selection_markers or {}).get(lab, {})} for k, lab in enumerate(sel_masks)}
        cvals = pd.to_numeric(data[color], errors='coerce') if color else None
        norm = Normalize(*(color_range or ((float(cvals.min()), float(cvals.max())) if color else (0, 1))))
        cm = plt.get_cmap(cmap)
        summary = []
        with plt.rc_context(self._hp_rc(rc)):
            fig = plt.figure(figsize=figsize or (panel_size[0] * len(cols), panel_size[1] * len(rows) + 1.3),
                             layout='constrained')
            sfs = fig.subfigures(len(rows) + 1, 1, height_ratios=[1] * len(rows) + [0.56], hspace=0.02)
            panel_axes = {}
            letter = 0
            for i, r in enumerate(rows):
                if row:
                    sfs[i].suptitle(r, fontweight='bold', fontsize=8.5)
                axs = np.atleast_1d(sfs[i].subplots(1, len(cols), sharex=True, sharey=True))
                for j, c in enumerate(cols):
                    ax = axs[j]
                    panel_axes[(r, c)] = ax
                    pm = ((rlab == r) & (clab == c)).to_numpy()
                    pts = []
                    for mv in mvalues:
                        m = pm & (mlab == mv).to_numpy()
                        if hl is not None:
                            m_plain = m & ~hl.to_numpy()
                        else:
                            m_plain = m
                        st = mstyles[mv]
                        kw = dict(marker=st['marker'], s=st['s'], alpha=st['alpha'], edgecolors=st['edgecolor'],
                                  linewidths=0.4, zorder=3)
                        xs, ys = data[x].to_numpy()[m_plain], yscale * data[y].to_numpy()[m_plain]
                        if color:
                            ax.scatter(xs, ys, c=cvals.to_numpy()[m_plain], cmap=cm, norm=norm, **kw)
                        else:
                            ax.scatter(xs, ys, color='0.5', **kw)
                        pts += list(zip(data[x].to_numpy()[m], yscale * data[y].to_numpy()[m]))
                        if hl is not None:
                            mh = m & hl.to_numpy()
                            kwh = dict(kw, s=max(st['s'], 14), edgecolors='k', linewidths=0.35, zorder=4, alpha=1)
                            if color:
                                ax.scatter(data[x].to_numpy()[mh], yscale * data[y].to_numpy()[mh],
                                           c=cvals.to_numpy()[mh], cmap=cm, norm=norm, **kwh)
                            else:
                                ax.scatter(data[x].to_numpy()[mh], yscale * data[y].to_numpy()[mh], color='0.5', **kwh)
                    rec = {'row': r, 'col': c, 'n': int(pm.sum())}
                    for lab, smask in sel_masks.items():
                        m = pm & smask
                        ax.scatter(data[x].to_numpy()[m], yscale * data[y].to_numpy()[m], marker=smk[lab]['marker'],
                                   s=smk[lab]['s'], facecolors='white', edgecolors='k', linewidths=0.9, zorder=6)
                        if m.any():
                            rec[f'{lab}_{y}'] = data[y].to_numpy()[m].tolist()
                            rec[f'{lab}_{x}'] = data[x].to_numpy()[m].tolist()
                    if threshold is not None:
                        ax.axhline(threshold * yscale, color='0.35', ls=(0, (4, 3)), lw=0.8, zorder=1)
                        ok = pm & (data[y].to_numpy() <= threshold)
                        rec['n_meeting'] = int(ok.sum())
                        if hl is not None:
                            rec['n_highlight'] = int((pm & hl.to_numpy()).sum())
                            rec['n_highlight_meeting'] = int((ok & hl.to_numpy()).sum())
                        if mark_best and ok.any():
                            k_best = np.flatnonzero(ok)[np.argmin(data[x].to_numpy()[ok])]
                            xy = (float(data[x].iloc[k_best]), float(yscale * data[y].iloc[k_best]))
                            ax.scatter(*xy, s=170, facecolors='none', edgecolors='#D55E00', linewidths=1.4, zorder=7)
                            rec.update({'best_x': xy[0], 'best_y': float(data[y].iloc[k_best]),
                                        'best_index': data['_orig_index'].iloc[k_best]})
                            rec['_label'] = (ax, xy, pts)
                    summary.append(rec)
                    ax.set_title(f'({_panel_letter(letter)}) {c}' if col else f'({_panel_letter(letter)})', loc='left')
                    letter += 1
                    if j == 0:
                        ax.set_ylabel(ylabel or ('Hours outside the band (%)' if y.startswith('share_') and y_as_percent
                                                 else y))
                    ax.set_xlabel(xlabel or f'{x} ({getattr(data, "attrs", {}).get("units", {}).get(x, "")})'
                                  .replace(' ()', ''))
                if row_ylims and r in row_ylims:
                    axs[0].set_ylim(*row_ylims[r])
            for note in annotations or []:  # free annotations, e.g. to name a branch of points
                ax = panel_axes.get((note.get('row', rows[0]), note.get('col', cols[0])))
                if ax is None:
                    continue
                kw = dict(fontsize=7, style='italic', color='0.3', zorder=8, ha='center', va='center')
                if note.get('xytext') is not None:
                    kw.update(xytext=note['xytext'], textcoords='axes fraction',
                              arrowprops=dict(arrowstyle='-', color='0.45', lw=0.6, shrinkA=2, shrinkB=3))
                kw.update(note.get('kwargs', {}))
                ax.annotate(note['text'], xy=note['xy'], **kw)
            for rec in summary:  # labels once the limits are final
                lab = rec.pop('_label', None)
                if lab is not None and best_format:
                    ax, xy, pts = lab
                    ax.get_xlim(), ax.get_ylim()
                    spot = _free_spot(ax, xy, pts + [xy])
                    ax.annotate(best_format.format(x=xy[0], y=xy[1]), xy=xy, xytext=spot, textcoords='axes fraction',
                                ha='center', va='center', color='#B34700', fontsize=7.5, zorder=8,
                                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85),
                                arrowprops=dict(arrowstyle='-', color='#B34700', lw=0.7, shrinkA=0, shrinkB=7))
            bottom = sfs[-1]
            handles = []
            if marker_by:
                for mv in mvalues:
                    st = mstyles[mv]
                    handles.append(Line2D([], [], ls='', marker=st['marker'], color='0.45',
                                          mec='k' if st['edgecolor'] not in ('none', None) else '0.45', mew=0.4,
                                          ms=max(2.5, st['s'] ** 0.5 * 0.9), label=st['label']))
            if hl is not None and hl.any():
                handles.append(Line2D([], [], ls='', marker='o', color='0.6', mec='k', mew=0.4, ms=4,
                                      label=highlight_label))
            for lab in sel_masks:
                handles.append(Line2D([], [], ls='', marker=smk[lab]['marker'], mfc='white', mec='k',
                                      ms=max(5, smk[lab]['s'] ** 0.5 * 0.8), label=lab))
            if threshold is not None:
                if mark_best:
                    handles.append(Line2D([], [], ls='', marker='o', mfc='none', mec='#D55E00', mew=1.4, ms=10,
                                          label=best_legend_label or
                                          f'Lowest {x}, ≤ {threshold * yscale:g}{"%" if y_as_percent else ""}'))
                handles.append(Line2D([], [], color='0.35', ls=(0, (4, 3)), lw=0.8,
                                      label=f'{threshold * yscale:g}{"% of hours" if y_as_percent else ""}'))
            if color:
                cax = bottom.add_axes([0.12, 0.79, 0.76, 0.085])
                cb = bottom.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cm), cax=cax, orientation='horizontal')
                cb.set_label(color_label or f'{color} ({getattr(data, "attrs", {}).get("units", {}).get(color, "")})'
                             .replace(' ()', ''))
            if handles:
                bottom.legend(handles=handles, loc='lower center', ncol=3, frameon=False, columnspacing=1.2,
                              handletextpad=0.4, bbox_to_anchor=(0.5, 0.0))
            fig.summary = pd.DataFrame(summary)
            self._hp_save(self, fig, out_dir, filename, filename_template, 'plot_comfort_screening.png',
                          'plot_comfort_screening', {'plot': 'comfort_screening'}, dpi, close)
        return fig
