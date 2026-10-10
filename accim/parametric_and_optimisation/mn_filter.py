"""Band of plausible (m, n) pairs for the custom adaptive comfort model (CustAST).

The custom adaptive model of accim uses a linear comfort temperature, ``T_comf = m * T_out + n``.
When ``CustAST_m`` and ``CustAST_n`` are varied independently, many combinations do not
correspond to any published adaptive model (e.g. m = 0.7 with n = 22.5 gives a comfort
temperature of 36.5 degC for a running mean outdoor temperature of 20 degC).

This module bounds the (m, n) pairs with the linear adaptive models collected in a review:
the slope ``m`` of the published models is regressed on their intercept ``n``
(``m = slope * n + intercept``), and two lines parallel to the regression line, by default
through the models farthest above and below it, delimit the band of plausible pairs.

The models of the review are kept unchanged in ``_REVIEW_MODELS``. ``drop_models`` leaves
some of them out of the fit and ``add_models`` adds other models, without modifying that list.

Usage
-----
Used through ``SimulationBase.set_mn_filter`` and ``PlottingMixin.plot_mn_filter``.

Examples
--------
mn_filter = MNFilter.from_data()
mn_filter = MNFilter.from_data(drop_models=[55], add_models=[{'author': 'New model', 'm': 0.33, 'n': 18.8}])
mn_filter.contains(m=0.31, n=17.8)
"""

from typing import Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

# Models to leave out (row ids or author labels) and models to add.
ModelSelection = Union[int, str, Sequence[Union[int, str]]]
ModelRows = Union[pd.DataFrame, dict, Sequence]

REVIEW_REFERENCE = (
    "Yao, R., Zhang, S., Du, C., Schweiker, M., Hodder, S., Olesen, B.W., Toftum, J., "
    "Romana d'Ambrosio, F., Gebhardt, H., Zhou, S., Yuan, F., Li, B. (2022). Evolution and "
    "performance analysis of adaptive thermal comfort models - A comprehensive literature review. "
    "Building and Environment, 217, 109020. https://doi.org/10.1016/j.buildenv.2022.109020"
)

# Linear adaptive comfort models (T_comf = m * T_out + n) listed in the review above.
# Columns: author (with the reference number in the review), year, operation mode
# (NV: naturally ventilated, MM: mixed mode, AC: air-conditioned), m, n.
_REVIEW_MODELS = (
    ('Humphreys [3]', 1978, 'NV', 0.534, 11.9),
    ('Humphreys [132]', 1981, 'NV', 0.55, 14.1),
    ('Auliciems and de Dear [133]', 1986, 'NV', 0.31, 17.6),
    ('Nicol and Roaf [55]', 1996, 'NV', 0.38, 17.0),
    ('Nicol et al. [56]', 1999, 'MM', 0.36, 18.5),
    ('Humphreys and Nicol [134]', 2000, 'NV', 0.54, 13.5),
    ('Heidari and Sharples [57]', 2002, 'NV', 0.36, 17.3),
    ('Heidari and Sharples [57]', 2002, 'NV', 0.292, 18.1),
    ('Mui and Chan [58]', 2003, 'AC', 0.158, 18.303),
    ('Nicol [135]', 2004, 'NV', 0.534, 12.9),
    ('Bouden and Ghrab [64]', 2005, 'NV', 0.68, 6.88),
    ('Ye et al. [59]', 2006, 'NV', 0.42, 15.12),
    ('Rijal et al. [78]', 2009, 'MM', 0.316, 19.2),
    ('Rijal et al. [78]', 2009, 'MM', 0.308, 18.1),
    ('Rijal et al. [78]', 2009, 'MM', 0.516, 15.4),
    ('Wang et al. [60]', 2010, 'NV', 0.486, 11.802),
    ('Nicol and Humphreys [136]', 2010, 'NV', 0.33, 18.8),
    ('Li et al. [61]', 2011, 'MM', 0.29, 15.0),
    ('Nicol et al. [137]', 2012, 'AC', 0.09, 22.6),
    ('Nguyen et al. [138]', 2012, 'NV', 0.341, 18.83),
    ('Rijal et al. [65]', 2013, 'NV', 0.531, 12.5),
    ('Rijal et al. [65]', 2013, 'AC', 0.297, 18.8),
    ('Rijal et al. [65]', 2013, 'AC', 0.307, 16.5),
    ('Ge et al. [62]', 2014, 'NV', 0.691, 12.91),
    ('Indraganti et al. [79]', 2014, 'NV', 0.26, 21.4),
    ('Indraganti et al. [79]', 2014, 'AC', 0.15, 22.1),
    ('Yau and Chew [80]', 2014, 'AC', 0.3314, 14.858),
    ('Yang et al. [63]', 2015, 'NV', 0.121, 21.489),
    ('Yang et al. [63]', 2015, 'NV', 0.271, 20.014),
    ('Yang et al. [63]', 2015, 'NV', 0.475, 17.639),
    ('Yang et al. [63]', 2015, 'NV', 0.51, 14.835),
    ('Halawa et al. [67]', 2015, 'NV', 0.53, 13.8),
    ('Haddad et al. [85]', 2016, 'NV', 0.25, 19.14),
    ('Manu et al. [68]', 2016, 'NV', 0.54, 12.83),
    ('Manu et al. [68]', 2016, 'MM', 0.28, 17.87),
    ('Rijal et al. [66]', 2017, 'MM', 0.206, 20.8),
    ('Rijal et al. [66]', 2017, 'AC', 0.065, 23.9),
    ('Barbadilla-Martín et al. [70]', 2017, 'MM', 0.24, 19.3),
    ('de Dear et al. [71]', 2018, 'MM', 0.26, 16.75),
    ('Thapa et al. [81]', 2018, 'NV', 0.556, 10.9),
    ('Indraganti and Boussaa [73]', 2018, 'AC', 0.049, 22.5),
    ('Rupp et al. [74]', 2018, 'NV', 0.56, 12.74),
    ('Rupp et al. [74]', 2018, 'AC', 0.09, 22.32),
    ('Luo et al. [75]', 2019, 'MM', 0.24, 20.66),
    ('Wu et al. [82]', 2019, 'NV', 0.19, 22.5),
    ('García et al. [76]', 2019, 'NV', 0.41, 16.0),
    ('López-Pérez et al. [77]', 2019, 'NV', 0.32, 18.45),
    ('López-Pérez et al. [77]', 2019, 'AC', 0.13, 22.7),
    ('Thapa [69]', 2020, 'NV', 0.605, 10.408),
    ('Williamson and Daniel [72]', 2020, 'NV', 0.26, 15.9),
    ('Jiao et al. [86]', 2020, 'NV', 0.706, 9.375),
    ('Jiao et al. [86]', 2020, 'NV', 0.418, 15.96),
    ('Jiao et al. [86]', 2020, 'NV', 0.84, 6.935),
    ('Fu et al. [83]', 2020, 'NV', 0.78, 9.42),
    ('Fu et al. [83]', 2020, 'AC', 0.18, 22.89),
    ('Kumar et al. [84]', 2020, 'NV', 0.81, 6.03),
)


_MODEL_COLUMNS = ['author', 'year', 'mode', 'm', 'n']


def review_models() -> pd.DataFrame:
    """Return the linear adaptive comfort models collected by Yao et al. (2022).

    Returns
    -------
    pd.DataFrame
        One row per model, with columns ``author``, ``year``, ``mode``, ``m`` and ``n``. The
        index (``id``, 0 to 55) identifies each model in ``drop_models``.

    Usage
    -----
    Default data of ``MNFilter.from_data`` and ``SimulationBase.set_mn_filter``. A new copy is
    returned on every call, so editing it does not change ``_REVIEW_MODELS``.

    Examples
    --------
    df = review_models()
    """
    df = pd.DataFrame(list(_REVIEW_MODELS), columns=_MODEL_COLUMNS)
    df.index.name = 'id'
    return df


def _drop_mask(df: pd.DataFrame, drop_models: ModelSelection) -> np.ndarray:
    """Boolean mask of the rows of df selected by ``drop_models`` (row ids and/or author labels).

    Parameters
    ----------
    df : pd.DataFrame
        Models, indexed by id.
    drop_models : int, str or sequence of int and str
        Row ids (index labels of df) and/or author labels (every model with that label, compared
        without case or surrounding spaces).

    Returns
    -------
    np.ndarray
        True for the rows to leave out.

    Usage
    -----
    Internal helper of ``MNFilter.from_data``.

    Examples
    --------
    mask = _drop_mask(review_models(), [17, 'Kumar et al. [84]'])
    """
    if isinstance(drop_models, (str, int, np.integer)):
        drop_models = [drop_models]
    mask = np.zeros(len(df), dtype=bool)
    authors = None
    if 'author' in df.columns:
        authors = df['author'].astype(str).str.strip().str.casefold().to_numpy()
    for item in drop_models:
        if isinstance(item, (bool, np.bool_)):
            raise TypeError('drop_models: give row ids (int) or author labels (str), not booleans.')
        if isinstance(item, (int, np.integer)):
            hits = np.asarray(df.index == item, dtype=bool)
            if not hits.any():
                raise ValueError(
                    f'drop_models: no model has the id {item}. The ids are the index of '
                    'review_models() (0 to 55) or of the data given.'
                )
        elif isinstance(item, str):
            if authors is None:
                raise ValueError('drop_models: the data has no author column; give row ids instead.')
            hits = authors == item.strip().casefold()
            if not hits.any():
                raise ValueError(
                    f"drop_models: no model has the author label '{item}'. Use the labels of "
                    "review_models(), e.g. 'Li et al. [61]'."
                )
        else:
            raise TypeError(f'drop_models: {item!r} is not a row id (int) or an author label (str).')
        mask |= hits
    return mask


def _added_models(add_models: ModelRows) -> pd.DataFrame:
    """Return ``add_models`` as a DataFrame with the columns of ``review_models``.

    Parameters
    ----------
    add_models : pd.DataFrame, dict or sequence
        A DataFrame with columns m and n (author, year and mode are optional), a dict, or a list
        of dicts or of tuples, either (m, n) or (author, year, mode, m, n) as in ``_REVIEW_MODELS``.

    Returns
    -------
    pd.DataFrame
        One row per model; models without an author are labelled 'Added model 1', 'Added model 2'...

    Usage
    -----
    Internal helper of ``MNFilter.from_data``.

    Examples
    --------
    df = _added_models([(0.33, 18.8), ('My model', 2024, 'MM', 0.30, 18.0)])
    """
    if isinstance(add_models, pd.DataFrame):
        df = add_models.copy()
    else:
        if isinstance(add_models, np.ndarray):
            add_models = add_models.tolist()
        single = isinstance(add_models, dict) or (
            isinstance(add_models, (tuple, list))
            and all(not isinstance(item, (dict, tuple, list)) for item in add_models)
        )
        rows = []
        for item in ([add_models] if single else add_models):
            if isinstance(item, dict):
                rows.append(dict(item))
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                rows.append({'m': item[0], 'n': item[1]})
            elif isinstance(item, (tuple, list)) and len(item) == len(_MODEL_COLUMNS):
                rows.append(dict(zip(_MODEL_COLUMNS, item)))
            else:
                raise ValueError(
                    f'add_models: {item!r} is not a model. Give dicts with m and n (author, year and '
                    'mode are optional), or tuples (m, n) or (author, year, mode, m, n).'
                )
        df = pd.DataFrame(rows)
    missing = [c for c in ('m', 'n') if c not in df.columns]
    if missing:
        raise ValueError(f'add_models: every model needs m and n; missing: {missing}.')
    df = df.reset_index(drop=True)
    for column in ('author', 'year', 'mode'):
        if column not in df.columns:
            df[column] = None
    for column in ('m', 'n'):
        values = pd.to_numeric(df[column], errors='coerce')
        if values.isna().any():
            raise ValueError(f'add_models: {column} must be a number in every model.')
        df[column] = values.astype(float)
    years = pd.to_numeric(df['year'], errors='coerce')
    if (years.isna() == df['year'].isna()).all() and (years.dropna() % 1 == 0).all():
        df['year'] = years.astype('Int64')  # whole years, also when some are missing
    unnamed = (df['author'].isna() | (df['author'].astype(str).str.strip() == '')).to_numpy()
    if unnamed.any():
        df['author'] = df['author'].astype(object)
        df.loc[unnamed, 'author'] = [f'Added model {i + 1}' for i in np.flatnonzero(unnamed)]
    extra = [c for c in df.columns if c not in _MODEL_COLUMNS]
    return df[_MODEL_COLUMNS + extra]


def _model_label(model_id, row: pd.Series) -> str:
    """Text of one model, e.g. "17: Li et al. [61] (2011, MM; m = 0.29, n = 15)"."""
    details = []
    for key in ('year', 'mode'):
        value = row.get(key)
        if value is None or (not isinstance(value, str) and pd.isna(value)):
            continue
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        details.append(str(value))
    prefix = (', '.join(details) + '; ') if details else ''
    return f"{model_id}: {row.get('author', '')} ({prefix}m = {float(row['m']):g}, n = {float(row['n']):g})"


class MNFilter:
    """Band of plausible (m, n) pairs, bounded by two lines parallel to the regression of m on n.

    A pair is inside the band when its residual ``r = m - (slope * n + intercept)`` satisfies
    ``-offset_lower <= r <= offset_upper``.

    Parameters
    ----------
    slope : float
        Slope of the regression line ``m = slope * n + intercept``.
    intercept : float
        Intercept of the regression line.
    offset_lower : float
        Distance, in m, from the regression line to the lower bound (non-negative).
    offset_upper : float
        Distance, in m, from the regression line to the upper bound (non-negative).
    data : pd.DataFrame, optional
        Models used to fit the band (columns ``m`` and ``n``; ``from_data`` adds ``origin``:
        'review', 'data' or 'added').
    r_value : float, optional
        Pearson correlation coefficient between n and m in ``data``.
    source : str, optional
        Description of the data source.
    removed_data : pd.DataFrame, optional
        Models left out of the fit with ``drop_models``.

    Usage
    -----
    Build it with ``MNFilter.from_data`` and pass it to the simulation classes through
    ``set_mn_filter``.

    Examples
    --------
    mn_filter = MNFilter.from_data(offset=0.17)
    """

    def __init__(self, slope: float, intercept: float, offset_lower: float, offset_upper: float,
                 data: Optional[pd.DataFrame] = None, r_value: Optional[float] = None, source: str = '',
                 removed_data: Optional[pd.DataFrame] = None):
        if offset_lower < 0 or offset_upper < 0:
            raise ValueError('MNFilter: the offsets must be non-negative.')
        self.slope = float(slope)
        self.intercept = float(intercept)
        self.offset_lower = float(offset_lower)
        self.offset_upper = float(offset_upper)
        self.data = data
        self.r_value = None if r_value is None else float(r_value)
        self.source = source
        self.removed_data = removed_data

    @classmethod
    def from_data(cls, data: Optional[pd.DataFrame] = None,
                  offset: Union[str, float, Tuple[float, float]] = 'farthest',
                  add_models: Optional[ModelRows] = None,
                  drop_models: Optional[ModelSelection] = None) -> 'MNFilter':
        """Fit the band to a set of linear adaptive comfort models.

        Parameters
        ----------
        data : pd.DataFrame, optional
            Models with columns ``m`` and ``n`` (other columns are kept for plotting).
            By default, the models collected by Yao et al. (2022), see ``review_models``.
        offset : {'farthest'} or float or tuple of two floats
            ``'farthest'`` (default): the bounds pass through the models farthest above and below
            the regression line. A float: symmetric distance, in m, from the regression line
            (e.g. 0.17). A tuple ``(lower, upper)``: distances below and above the line.
        add_models : pd.DataFrame, dict or sequence, optional
            Models added to ``data``: a DataFrame with columns m and n (author, year and mode are
            optional), a dict, or a list of dicts or of tuples, either (m, n) or
            (author, year, mode, m, n). They get the ids that follow the last id of ``data``.
        drop_models : int, str or sequence of int and str, optional
            Models of ``data`` left out of the fit: row ids (the index of ``review_models()``,
            0 to 55, or of ``data``) and/or author labels (e.g. 'Li et al. [61]', which leaves out
            every model with that label).

        Returns
        -------
        MNFilter
            Fitted band. ``data`` holds the models used, with their ids as index and an
            ``origin`` column; ``removed_data`` holds the models left out.

        Usage
        -----
        Called by ``SimulationBase.set_mn_filter``. Models are dropped first and added afterwards,
        and the band (including the 'farthest' offsets) is fitted to the result.

        Examples
        --------
        mn_filter = MNFilter.from_data(offset='farthest')
        mn_filter = MNFilter.from_data(drop_models=['Kumar et al. [84]'], add_models=[(0.33, 18.8)])
        """
        if data is None:
            df = review_models()
            df['origin'] = 'review'
            source = 'Yao et al. (2022), ' + str(len(df)) + ' linear adaptive models'
        else:
            df = pd.DataFrame(data).copy()
            if not df.index.is_unique:
                df = df.reset_index(drop=True)
            if 'origin' not in df.columns:
                df['origin'] = 'data'
            source = 'user data, ' + str(len(df)) + ' models'
        missing = [c for c in ('m', 'n') if c not in df.columns]
        if missing:
            raise ValueError(f'MNFilter: the data must have columns m and n; missing: {missing}.')
        integer_ids = len(df) > 0 and pd.api.types.is_integer_dtype(df.index)
        next_id = int(df.index.max()) + 1 if integer_ids else len(df)
        df['m'] = pd.to_numeric(df['m'], errors='coerce')
        df['n'] = pd.to_numeric(df['n'], errors='coerce')
        df = df.dropna(subset=['m', 'n'])
        removed = df.iloc[0:0]
        if drop_models is not None and not (isinstance(drop_models, (list, tuple)) and len(drop_models) == 0):
            mask = _drop_mask(df, drop_models)
            removed = df.loc[mask].copy()
            df = df.loc[~mask].copy()
        added_count = 0
        has_additions = add_models is not None and not (
            len(add_models) == 0 if isinstance(add_models, (pd.DataFrame, list, tuple, dict, np.ndarray)) else False
        )
        if has_additions:
            added = _added_models(add_models)
            added['origin'] = 'added'
            added.index = pd.RangeIndex(next_id, next_id + len(added), name=df.index.name)
            added_count = len(added)
            df = pd.concat([df, added])
        changes = []
        if len(removed) > 0:
            changes.append(f'{len(removed)} removed')
        if added_count > 0:
            changes.append(f'{added_count} added')
        if changes:
            source += ' (' + ' and '.join(changes) + f'; {len(df)} used)'
        if len(df) < 3:
            raise ValueError('MNFilter: at least three (m, n) pairs are needed to fit the band.')
        m_values = df['m'].to_numpy(dtype=float)
        n_values = df['n'].to_numpy(dtype=float)
        slope, intercept = np.polyfit(n_values, m_values, 1)
        residuals = m_values - (slope * n_values + intercept)
        if isinstance(offset, str):
            if offset != 'farthest':
                raise ValueError("MNFilter: offset must be 'farthest', a number or a (lower, upper) tuple.")
            offset_lower = max(0.0, -float(residuals.min()))
            offset_upper = max(0.0, float(residuals.max()))
        elif isinstance(offset, (tuple, list)):
            if len(offset) != 2:
                raise ValueError('MNFilter: an offset tuple must be (lower, upper).')
            offset_lower, offset_upper = float(offset[0]), float(offset[1])
        else:
            offset_lower = offset_upper = float(offset)
        r_value = float(np.corrcoef(n_values, m_values)[0, 1])
        return cls(slope, intercept, offset_lower, offset_upper, data=df, r_value=r_value, source=source,
                   removed_data=removed)

    def residuals(self, m, n) -> np.ndarray:
        """Vertical distance (in m) from each pair to the regression line."""
        return np.asarray(m, dtype=float) - (self.slope * np.asarray(n, dtype=float) + self.intercept)

    def contains(self, m, n, tolerance: float = 1e-9):
        """Return True (or a boolean array) for the pairs inside the band, bounds included."""
        r = self.residuals(m, n)
        inside = (r >= -self.offset_lower - tolerance) & (r <= self.offset_upper + tolerance)
        return bool(inside) if np.ndim(inside) == 0 else inside

    def m_bounds(self, n) -> Tuple[np.ndarray, np.ndarray]:
        """Lower and upper bound of m for the given n."""
        base = self.slope * np.asarray(n, dtype=float) + self.intercept
        return base - self.offset_lower, base + self.offset_upper

    def n_bounds(self, m) -> Tuple[np.ndarray, np.ndarray]:
        """Lower and upper bound of n inside the band for the given m (inf if unbounded, nan if empty)."""
        m = np.asarray(m, dtype=float)
        if abs(self.slope) < 1e-12:
            inside = (m - self.intercept >= -self.offset_lower) & (m - self.intercept <= self.offset_upper)
            low = np.where(inside, -np.inf, np.nan)
            high = np.where(inside, np.inf, np.nan)
            return low, high
        n_a = (m - self.intercept + self.offset_lower) / self.slope
        n_b = (m - self.intercept - self.offset_upper) / self.slope
        return np.minimum(n_a, n_b), np.maximum(n_a, n_b)

    def feasible_n_interval(self, m, n_min: float, n_max: float) -> Tuple[np.ndarray, np.ndarray]:
        """Interval of n inside both the band and [n_min, n_max] for the given m (low > high if empty)."""
        low, high = self.n_bounds(m)
        low = np.where(np.isnan(low), np.inf, np.maximum(low, n_min))
        high = np.where(np.isnan(high), -np.inf, np.minimum(high, n_max))
        return low, high

    def check_ranges(self, m_min: float, m_max: float, n_min: float, n_max: float, samples: int = 2001) -> None:
        """Raise ValueError if, for some m in [m_min, m_max], no n in [n_min, n_max] is inside the band."""
        m_grid = np.linspace(float(m_min), float(m_max), int(samples))
        low, high = self.feasible_n_interval(m_grid, float(n_min), float(n_max))
        empty = m_grid[low > high + 1e-12]
        if empty.size > 0:
            raise ValueError(
                f'The m-n band does not include any n in [{n_min}, {n_max}] for m between '
                f'{empty.min():.3f} and {empty.max():.3f}. Narrow the CustAST_m range or widen the '
                'CustAST_n range.'
            )

    def map_n(self, m, n_raw, n_min: float, n_max: float):
        """Map n_raw from [n_min, n_max] linearly onto the interval of n inside the band for m."""
        low, high = self.feasible_n_interval(m, float(n_min), float(n_max))
        if np.any(low > high + 1e-12):
            raise ValueError('The m-n band does not include any n in the CustAST_n range for this m.')
        span = float(n_max) - float(n_min)
        if span <= 0:
            fraction = np.zeros_like(np.asarray(n_raw, dtype=float))
        else:
            fraction = np.clip((np.asarray(n_raw, dtype=float) - float(n_min)) / span, 0.0, 1.0)
        mapped = low + fraction * (high - low)
        return float(mapped) if np.ndim(mapped) == 0 else mapped

    def sample_inside(self, u_m, u_n, m_min: float, m_max: float, n_min: float, n_max: float,
                      grid: int = 4001) -> Tuple[np.ndarray, np.ndarray]:
        """Map points of the unit square onto the part of the band within the m and n ranges.

        ``u_m`` sets m through the inverse cumulative distribution of m over the area of that part of
        the band, so m is more likely where the band is wider within [n_min, n_max]; ``u_n`` places n
        linearly within the interval of n inside the band for that m. Uniform (u_m, u_n) give pairs
        uniformly distributed over the band, as when drawing in the ranges and discarding the pairs
        outside, and a Latin hypercube in (u_m, u_n) keeps one pair per stratum of each.

        Parameters
        ----------
        u_m, u_n : array-like
            Values in [0, 1].
        m_min, m_max, n_min, n_max : float
            Ranges of CustAST_m and CustAST_n.
        grid : int
            Points of the m grid used to invert the cumulative distribution.

        Returns
        -------
        tuple of np.ndarray
            m and n, inside the band and within the ranges.

        Usage
        -----
        Called by ``SimulationBase.sampling_lhs`` when an m-n filter is set.

        Examples
        --------
        m, n = MNFilter.from_data().sample_inside([0.1, 0.9], [0.5, 0.5], 0.0, 0.7, 5.0, 22.5)
        """
        u_m = np.clip(np.asarray(u_m, dtype=float), 0.0, 1.0)
        u_n = np.clip(np.asarray(u_n, dtype=float), 0.0, 1.0)
        n_min, n_max = float(n_min), float(n_max)
        # Values of m with some n of [n_min, n_max] inside the band (the bounds are lines in n).
        m_lower, _ = self.m_bounds(np.array([n_min, n_max]))
        _, m_upper = self.m_bounds(np.array([n_min, n_max]))
        m_low = max(float(m_min), float(np.min(m_lower)))
        m_high = min(float(m_max), float(np.max(m_upper)))
        if not m_high > m_low:
            raise ValueError('The m-n band does not overlap the CustAST_m and CustAST_n ranges.')
        m_grid = np.linspace(m_low, m_high, int(grid))
        low, high = self.feasible_n_interval(m_grid, n_min, n_max)
        width = np.clip(np.nan_to_num(high - low, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
        area = np.concatenate([[0.0], np.cumsum(0.5 * (width[1:] + width[:-1]) * np.diff(m_grid))])
        if not area[-1] > 0:
            raise ValueError('The m-n band does not overlap the CustAST_m and CustAST_n ranges.')
        cdf = area / area[-1]
        increasing = np.r_[True, np.diff(cdf) > 0]
        m = np.interp(u_m, cdf[increasing], m_grid[increasing])
        low, high = self.feasible_n_interval(m, n_min, n_max)
        n = low + u_n * np.clip(high - low, 0.0, None)
        return m, n

    def equation(self, digits: int = 4) -> str:
        """Regression line as text."""
        sign = '+' if self.intercept >= 0 else '-'
        return f'm = {self.slope:.{digits}f} n {sign} {abs(self.intercept):.{digits}f}'

    def describe(self) -> str:
        """Short description of the band, with the models removed and added, if any."""
        r2 = '' if self.r_value is None else f', R2 = {self.r_value ** 2:.3f}'
        lines = [f'm-n filter ({self.source}{r2}): {self.equation()}; band from {self.offset_lower:.4f} below '
                 f'to {self.offset_upper:.4f} above the regression line.']
        if self.removed_data is not None and len(self.removed_data) > 0:
            lines.append('  Models removed: ' + '; '.join(
                _model_label(model_id, row) for model_id, row in self.removed_data.iterrows()))
        if self.data is not None and 'origin' in self.data.columns:
            added = self.data[self.data['origin'] == 'added']
            if len(added) > 0:
                lines.append('  Models added: ' + '; '.join(
                    _model_label(model_id, row) for model_id, row in added.iterrows()))
        return '\n'.join(lines)

    def models_table(self) -> pd.DataFrame:
        """Models used for the band and models removed, with their residual from the regression line.

        Returns
        -------
        pd.DataFrame
            One row per model, indexed by id, with the model columns plus ``used`` (False for the
            models removed) and ``residual`` (m minus the m of the regression line; the 'farthest'
            bounds pass through the lowest and highest residuals of the models used).

        Usage
        -----
        Helps choose ``drop_models``, e.g. ``models_table().sort_values('residual')``.

        Examples
        --------
        table = MNFilter.from_data().models_table()
        """
        frames = []
        if self.data is not None:
            frames.append(self.data.assign(used=True))
        if self.removed_data is not None and len(self.removed_data) > 0:
            frames.append(self.removed_data.assign(used=False))
        if not frames:
            return pd.DataFrame(columns=_MODEL_COLUMNS + ['used', 'residual'])
        table = pd.concat(frames)
        try:
            table = table.sort_index()
        except TypeError:  # ids of mixed types (e.g. text ids in the data, numbers for added models)
            pass
        table['residual'] = self.residuals(table['m'], table['n'])
        return table

    def to_dict(self) -> dict:
        """Band parameters, e.g. for run signatures and summaries."""
        return {
            'slope': self.slope,
            'intercept': self.intercept,
            'offset_lower': self.offset_lower,
            'offset_upper': self.offset_upper,
            'r_value': self.r_value,
            'source': self.source,
        }


class MNFilterMapping:
    """Picklable mapping of the optimiser's CustAST_n variable into the m-n band.

    The algorithm proposes CustAST_m and CustAST_n within their ranges. Before each evaluation,
    CustAST_n is mapped linearly from [n_min, n_max] onto the interval of n inside the band for the
    proposed CustAST_m, so every simulated combination lies inside the band.

    Parameters
    ----------
    band : dict
        Output of ``MNFilter.to_dict``.
    m_index, n_index : int
        Positions of CustAST_m and CustAST_n in the problem inputs.
    n_min, n_max : float
        Range of CustAST_n.

    Usage
    -----
    Attached to each evaluator by ``SimulationBase.run_optimisation``.

    Examples
    --------
    mapping = MNFilterMapping(mn_filter.to_dict(), 0, 1, 5.0, 22.5)
    """

    def __init__(self, band: dict, m_index: int, n_index: int, n_min: float, n_max: float):
        self.band = dict(band)
        self.m_index = int(m_index)
        self.n_index = int(n_index)
        self.n_min = float(n_min)
        self.n_max = float(n_max)

    def _filter(self) -> MNFilter:
        return MNFilter(self.band['slope'], self.band['intercept'], self.band['offset_lower'],
                        self.band['offset_upper'])

    def map_inputs(self, values: Sequence) -> list:
        """Return a copy of the input vector with CustAST_n mapped into the band."""
        mapped = list(values)
        mapped[self.n_index] = self._filter().map_n(float(mapped[self.m_index]), float(mapped[self.n_index]),
                                                    self.n_min, self.n_max)
        return mapped

    def map_dataframe(self, df: pd.DataFrame, m_column: str = 'CustAST_m', n_column: str = 'CustAST_n') -> pd.DataFrame:
        """Return a copy of df with the n column mapped into the band (rows without values are kept)."""
        if df is None or df.empty or m_column not in df.columns or n_column not in df.columns:
            return df
        out = df.copy()
        valid = out[m_column].notna() & out[n_column].notna()
        if valid.any():
            out.loc[valid, n_column] = self._filter().map_n(
                out.loc[valid, m_column].astype(float).to_numpy(),
                out.loc[valid, n_column].astype(float).to_numpy(),
                self.n_min, self.n_max,
            )
        return out
