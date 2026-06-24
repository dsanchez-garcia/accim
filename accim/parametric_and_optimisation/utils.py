# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

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

"""Utility helpers for parametric and optimisation workflows.

This module centralises dataframe expansion, filter-mask construction,
and subplot ordering utilities used by analysis and plotting routines.

Usage
-----
Import these helpers from parametric/optimisation sessions when preparing
results for post-processing.

Examples
--------
filtered_df, report = apply_data_filter(df=my_df, data_filter=None)
order = resolve_subplot_order(values=['B', 'A'], mode='alphabetical')
"""


import numpy as np
from typing import Any, Literal, Optional


def descriptor_has_options(values):
    """Validate whether descriptor values define options or a numeric range.

    Parameters
    ----------
    values : Any
        Descriptor values provided by the user. Accepted forms are
        ``list[int|float]`` for explicit options or ``tuple(min, max)``.

    Returns
    -------
    bool
        ``True`` when ``values`` is an explicit options list; ``False`` when
        ``values`` is a two-value numeric range tuple.

    Usage
    -----
    Use this validation before building BESOS parameter descriptors.

    Examples
    --------
    has_options = descriptor_has_options([18, 20, 22])
    """
    #Checking value entered is a list containing floats or a tuple containing the minimum and maximum values

    descriptor_has_options = False
    if type(values) == tuple and len(values) == 2 and all([type(i) == float or type(i) == int or type(i) == np.float64 for i in values]):
        pass
    elif type(values) == list and all(type(j) == float or type(j) == int or type(j) == np.float64 for j in values):
        descriptor_has_options = True
    else:
        raise ValueError('values argument must be, FOR ALL CASES, '
                         'a list containing int or float, '
                         'or a tuple which contains the minimum and maximum values for the range')
    return descriptor_has_options


import pandas as pd
import ast
from datetime import datetime, timedelta


def expand_to_hourly_dataframe(
        df: pd.DataFrame,
        parameter_columns: list,
        start_date: str = '2024-01-01 01',
        hourly_columns: list = None,
):
    """Expands a dataframe with hourly data columns into an hourly dataframe.
    
    Parameters:
    df (pd.DataFrame): The input dataframe containing parameters and hourly data columns.
    parameter_columns (list): The list of column names that contain input parameters.
    start_date (str): The start date and time in the format 'YYYY-MM-DD HH'.
    
    Returns:
    pd.DataFrame: The expanded dataframe with an additional datetime column.
    
    Parameters
    ----------
    hourly_columns : Any
        Argument used by `expand_to_hourly_dataframe`.
    
    Usage
    -----
    Use `expand_to_hourly_dataframe` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = expand_to_hourly_dataframe(df=..., parameter_columns=..., start_date=..., ...)
    """

    # Identify columns with hourly data
    if hourly_columns is None:
        hourly_columns = identify_hourly_columns(df)
    if len(hourly_columns) == 0:
        raise ValueError(
            'No hourly columns were detected to expand. '
            'If you are using optimisation file outputs, check file_output_columns names '
            'or use include_file_outputs=True with file_output_columns=None.'
        )

    # print(f"Hourly columns identified: {hourly_columns}")

    # Keep only parameter columns and hourly columns
    df_subset = df[parameter_columns + hourly_columns].copy()

    # Convert string representations of lists into actual lists
    for col in hourly_columns:
        # print(f"Processing column: {col}")
        if not df_subset[col].empty and isinstance(df_subset[col].iloc[0], str):
            print(f"First element of '{col}' is a string. Attempting evaluation...")
            evaluated_values = []
            for value in df_subset[col]:
                try:
                    evaluated_values.append(ast.literal_eval(value.strip()))
                except (ValueError, TypeError, SyntaxError, Exception) as e:
                    print(f"Error evaluating in column '{col}': '{value}' - {e}")
                    evaluated_values.append(None)
            df_subset[col] = evaluated_values
        else:
            continue
            # print(f"First element of '{col}' is not a string. Assuming it's already a list.")


    # Convert start_date to datetime object
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d %H')

    # Function to expand the dataframe for hourly data
    def expand_hourly_data(row):
        num_hours = len(row[hourly_columns[0]])
        expanded_rows = {col: [row[col]] * num_hours for col in parameter_columns}
        expanded_rows['hour'] = list(range(1, num_hours + 1))
        expanded_rows['datetime'] = [start_datetime + timedelta(hours=i) for i in range(num_hours)]
        for col in hourly_columns:
            expanded_rows[col] = row[col]
        return pd.DataFrame(expanded_rows)

    # Apply the function to each row and concatenate the results
    expanded_df = pd.concat(df_subset.apply(expand_hourly_data, axis=1).to_list(), ignore_index=True)

    return expanded_df


def identify_hourly_columns(df):
    """Identifies the columns which contains strings representing lists.
    
    :param df: the pandas DataFrame
    :return: the list of column names
    
    Usage
    -----
    Use `identify_hourly_columns` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = identify_hourly_columns(df=...)
    """
    def _is_hourly_value(value):
        if isinstance(value, str):

            stripped = value.strip()
            return stripped.startswith('[') and stripped.endswith(']')
        if isinstance(value, (list, tuple, np.ndarray)):
            return True
        return False


    hourly_columns = [
        col for col in df.columns
        if len(df[col]) > 0 and df[col].apply(_is_hourly_value).all()
    ]


    if not hourly_columns:
        hourly_columns = [
            col for col in df.columns if
            df[col].astype(str).apply(lambda x: x.strip().startswith('[') and x.strip().endswith(']')).all()
        ]

    return hourly_columns

def make_all_combinations(parameters_values_dict: dict) -> pd.DataFrame:
    """Takes all values from all the parameters and return a pandas DataFrame with all possible combinations.
    
    :param parameters_values_dict: a dictionary in the format {'parameter name': list_of_values}
    :return: a pandas DataFrame with all possible combinations
    
    Usage
    -----
    Use `make_all_combinations` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = make_all_combinations(parameters_values_dict=...)
    """

    from itertools import product
    combinations = list(product(*parameters_values_dict.values()))
    parameters_values_df = pd.DataFrame(combinations, columns=parameters_values_dict.keys())
    return parameters_values_df


SUBPLOT_ORDER_MODES = ('auto', 'alphabetical', 'ascending', 'descending', 'custom')
DATA_FILTER_EMPTY_MODES = ('error', 'warn', 'ignore')


def _subplot_sort_key(value, case_sensitive: bool = False):
    """Build a deterministic sort key for subplot labels.

    Parameters
    ----------
    value : Any
        Label value to convert into a sort key.
    case_sensitive : bool, optional
        Whether sorting should preserve case.

    Returns
    -------
    str
        Sort key used by subplot ordering helpers.

    Usage
    -----
    Called internally by subplot ordering functions.

    Examples
    --------
    key = _subplot_sort_key('Cooling', case_sensitive=False)
    """
    text = str(value)
    return text if case_sensitive else text.casefold()


def _subplot_custom_match_key(value, case_sensitive: bool = False):
    """Normalize labels used in custom subplot matching.

    Parameters
    ----------
    value : Any
        Raw label value from data or user custom order.
    case_sensitive : bool, optional
        Whether matching should preserve case.

    Returns
    -------
    Any
        Comparable value used to match custom labels against data labels.

    Usage
    -----
    Used internally by custom subplot ordering logic.

    Examples
    --------
    match_key = _subplot_custom_match_key('Office', case_sensitive=False)
    """
    if isinstance(value, str):
        return value if case_sensitive else value.casefold()
    return value


def _can_sort_subplot_values_numerically(values: list) -> bool:
    """Check whether subplot values can be safely sorted as numbers.

    Parameters
    ----------
    values : list
        Sequence of subplot labels.

    Returns
    -------
    bool
        ``True`` when every value can be converted to a finite float.

    Usage
    -----
    Used internally to decide between numeric and lexical ordering.

    Examples
    --------
    numeric = _can_sort_subplot_values_numerically(['1', '2', '3'])
    """
    if len(values) == 0:
        return False
    for value in values:
        if value is None:
            return False
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return False
        if np.isnan(numeric_value):
            return False
    return True
def _is_data_filter_sequence(value: Any) -> bool:
    """Determine whether a filter value is a supported sequence type.

    Parameters
    ----------
    value : Any
        Filter condition candidate.

    Returns
    -------
    bool
        ``True`` when the value is list-like and supported by filter logic.

    Usage
    -----
    Used internally by data-filter helpers to branch scalar vs sequence logic.

    Examples
    --------
    is_sequence = _is_data_filter_sequence(['A', 'B'])
    """
    if isinstance(value, (str, bytes, dict)):
        return False
    return isinstance(value, (list, tuple, set, np.ndarray, pd.Index, pd.Series))


def _casefold_if_needed(value: Any, case_sensitive: bool = False):
    """Case-fold text values when case-insensitive comparisons are requested.

    Parameters
    ----------
    value : Any
        Value to normalise.
    case_sensitive : bool, optional
        Whether string values should keep original case.

    Returns
    -------
    Any
        Original value or case-folded string.

    Usage
    -----
    Used by filtering utilities for consistent text matching.

    Examples
    --------
    normalized = _casefold_if_needed('Office', case_sensitive=False)
    """
    if case_sensitive or not isinstance(value, str):
        return value
    return value.casefold()


def _normalise_series_for_text(series: pd.Series, case_sensitive: bool = False) -> pd.Series:
    """Normalise a Series for text-based comparisons.

    Parameters
    ----------
    series : pd.Series
        Series to convert for textual matching.
    case_sensitive : bool, optional
        Whether strings should preserve original case.

    Returns
    -------
    pd.Series
        String-converted Series, optionally case-folded.

    Usage
    -----
    Used by scalar and sequence condition matching helpers.

    Examples
    --------
    text_series = _normalise_series_for_text(df['epw'], case_sensitive=False)
    """
    series_text = series.astype(str)
    return series_text if case_sensitive else series_text.str.casefold()


def _match_scalar_condition(series: pd.Series, condition: Any, case_sensitive: bool = False) -> pd.Series:
    """Build a boolean mask for scalar filter conditions.

    Parameters
    ----------
    series : pd.Series
        Series to evaluate.
    condition : Any
        Scalar condition value.
    case_sensitive : bool, optional
        Whether string matching should preserve case.

    Returns
    -------
    pd.Series
        Boolean mask where rows satisfy the scalar condition.

    Usage
    -----
    Used internally by `apply_data_filter` mask construction.

    Examples
    --------
    mask = _match_scalar_condition(df['epw'], 'Seville.epw', case_sensitive=False)
    """
    if isinstance(condition, str):
        lhs = _normalise_series_for_text(series, case_sensitive=case_sensitive)
        rhs = _casefold_if_needed(condition, case_sensitive=case_sensitive)
        return lhs == rhs
    return series == condition


def _match_sequence_condition(series: pd.Series, condition_values: list, case_sensitive: bool = False) -> pd.Series:
    """Build a boolean mask for sequence-based filter conditions.

    Parameters
    ----------
    series : pd.Series
        Series to evaluate.
    condition_values : list
        Accepted values for inclusion checks.
    case_sensitive : bool, optional
        Whether string matching should preserve case.

    Returns
    -------
    pd.Series
        Boolean mask where rows match one of the provided values.

    Usage
    -----
    Used internally by include/exclude filter operations.

    Examples
    --------
    mask = _match_sequence_condition(df['epw'], ['Seville.epw', 'Sydney.epw'])
    """
    if len(condition_values) == 0:
        return pd.Series(False, index=series.index)
    if all(isinstance(v, str) for v in condition_values):
        lhs = _normalise_series_for_text(series, case_sensitive=case_sensitive)
        rhs_values = [_casefold_if_needed(v, case_sensitive=case_sensitive) for v in condition_values]
        return lhs.isin(rhs_values)
    return series.isin(condition_values)
def _numeric_compare_series(series: pd.Series, op: str, value: Any, context: str) -> pd.Series:
    """Apply a numeric comparison operator to a pandas Series.

    Parameters
    ----------
    series : pd.Series
        Series to compare numerically.
    op : str
        Operator name (``gt``, ``ge``, ``lt``, ``le``).
    value : Any
        Threshold value converted to float.
    context : str
        Context label used in error messages.

    Returns
    -------
    pd.Series
        Boolean mask from the numeric comparison.

    Usage
    -----
    Used internally by `_build_filter_mask` for operator dictionaries.

    Examples
    --------
    mask = _numeric_compare_series(df['Energy'], 'lt', 1000, context='apply_data_filter')
    """
    numeric_series = pd.to_numeric(series, errors='coerce')
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as err:
        raise ValueError(f"{context}: operator '{op}' expects a numeric value.") from err
    if op == 'gt':
        return numeric_series > numeric_value
    if op == 'ge':
        return numeric_series >= numeric_value
    if op == 'lt':
        return numeric_series < numeric_value
    if op == 'le':
        return numeric_series <= numeric_value
    raise ValueError(f"{context}: unsupported numeric operator '{op}'.")
def _build_filter_mask(series: pd.Series, condition: Any, case_sensitive: bool = False, context: str = 'data_filter') -> pd.Series:
    """Build a row-selection mask from scalar, sequence, or operator rules.

    Parameters
    ----------
    series : pd.Series
        Series to evaluate.
    condition : Any
        Filter condition, either scalar, sequence, or operator dictionary.
    case_sensitive : bool, optional
        Whether string matching should preserve case.
    context : str, optional
        Context label used in validation/error messages.

    Returns
    -------
    pd.Series
        Boolean mask identifying rows that satisfy the condition.

    Usage
    -----
    Used internally by `apply_data_filter` for include/exclude operations.

    Examples
    --------
    mask = _build_filter_mask(df['building_type'], {'in': ['office', 'residential']})
    """
    if isinstance(condition, dict):
        if len(condition) == 0:
            raise ValueError(f'{context}: empty condition dict is not allowed.')
        combined_mask = pd.Series(True, index=series.index)
        for (raw_op, op_value) in condition.items():
            op = str(raw_op).strip().lower()
            if op in ('in', 'values'):
                if not _is_data_filter_sequence(op_value):
                    raise ValueError(f"{context}: operator '{raw_op}' expects a list-like value.")
                part = _match_sequence_condition(
                    series=series,
                    condition_values=list(op_value),
                    case_sensitive=case_sensitive,
                )
            elif op == 'between':
                if not _is_data_filter_sequence(op_value) or len(list(op_value)) != 2:
                    raise ValueError(f"{context}: operator 'between' expects two values [min, max].")
                (lo, hi) = list(op_value)
                lo_num = pd.to_numeric(pd.Series([lo]), errors='coerce').iloc[0]
                hi_num = pd.to_numeric(pd.Series([hi]), errors='coerce').iloc[0]
                if pd.notna(lo_num) and pd.notna(hi_num):
                    numeric_series = pd.to_numeric(series, errors='coerce')
                    part = numeric_series.between(float(lo_num), float(hi_num), inclusive='both')
                else:
                    part = series.between(lo, hi, inclusive='both')
            elif op in ('gt', 'ge', 'lt', 'le'):
                part = _numeric_compare_series(series=series, op=op, value=op_value, context=context)
            elif op in ('eq', 'ne'):
                part = _match_scalar_condition(series=series, condition=op_value, case_sensitive=case_sensitive)
                if op == 'ne':
                    part = ~part
            elif op == 'contains':
                values = [op_value] if isinstance(op_value, str) else list(op_value) if _is_data_filter_sequence(op_value) else None
                if values is None:
                    raise ValueError(f"{context}: operator 'contains' expects a string or list of strings.")
                part = pd.Series(False, index=series.index)
                lhs = series.astype(str)
                for token in values:
                    if not isinstance(token, str):
                        raise ValueError(f"{context}: operator 'contains' only supports string tokens.")
                    part |= lhs.str.contains(token, case=case_sensitive, regex=False, na=False)
            elif op == 'regex':
                if not isinstance(op_value, str):
                    raise ValueError(f"{context}: operator 'regex' expects a pattern string.")
                part = series.astype(str).str.contains(op_value, case=case_sensitive, regex=True, na=False)
            elif op == 'isna':
                part = series.isna() if bool(op_value) else ~series.isna()
            else:
                raise ValueError(
                    f"{context}: unsupported operator '{raw_op}'. Supported operators are: "
                    "in, values, between, gt, ge, lt, le, eq, ne, contains, regex, isna."
                )
            combined_mask &= part.fillna(False)
        return combined_mask
    if _is_data_filter_sequence(condition):
        return _match_sequence_condition(series=series, condition_values=list(condition), case_sensitive=case_sensitive)
    return _match_scalar_condition(series=series, condition=condition, case_sensitive=case_sensitive)
def apply_data_filter(
        df: pd.DataFrame,
        data_filter: Optional[dict] = None,
        case_sensitive: bool = False,
        strict: bool = True,
        on_empty: Literal['error', 'warn', 'ignore'] = 'error',
        context: str = 'apply_data_filter',
) -> tuple[pd.DataFrame, dict]:
    """Apply include/exclude/query row filtering and return (filtered_df, report).
    
    Parameters
    ----------
    df : Any
        Input dataframe used by this routine.
    data_filter : Any
        Argument used by `apply_data_filter`.
    case_sensitive : Any
        Argument used by `apply_data_filter`.
    strict : Any
        Boolean or mode flag controlling behaviour.
    on_empty : Any
        Argument used by `apply_data_filter`.
    context : Any
        Label or identifier used for diagnostics and reporting.
    
    Usage
    -----
    Use `apply_data_filter` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = apply_data_filter(df=..., data_filter=..., case_sensitive=..., ...)
    """
    if on_empty not in DATA_FILTER_EMPTY_MODES:
        raise ValueError(f"{context}: on_empty must be one of {DATA_FILTER_EMPTY_MODES}.")
    filtered_df = df.copy()
    rows_before = len(filtered_df)
    report = {
        'rows_before': rows_before,
        'rows_after': rows_before,
        'rows_removed': 0,
        'applied_rules': [],
        'missing_columns': [],
    }
    if data_filter is None:
        return (filtered_df, report)
    if not isinstance(data_filter, dict):
        raise TypeError(f'{context}: data_filter must be a dict or None.')
    allowed_keys = {'include', 'exclude', 'query'}
    unknown_keys = [k for k in data_filter.keys() if k not in allowed_keys]
    if unknown_keys:
        raise ValueError(f"{context}: unsupported data_filter keys {unknown_keys}. Allowed keys: {sorted(allowed_keys)}.")
    for block_name in ('include', 'exclude'):
        block = data_filter.get(block_name, None)
        if block is None:
            continue
        if not isinstance(block, dict):
            raise TypeError(f"{context}: data_filter['{block_name}'] must be a dict.")
        mask = pd.Series(True, index=filtered_df.index)
        for (column, condition) in block.items():
            if column not in filtered_df.columns:
                missing_msg = (
                    f"{context}: column '{column}' from data_filter['{block_name}'] was not found. "
                    f'Available columns: {list(filtered_df.columns)}'
                )
                if strict:
                    raise KeyError(missing_msg)
                report['missing_columns'].append(column)
                continue
            column_mask = _build_filter_mask(
                series=filtered_df[column],
                condition=condition,
                case_sensitive=case_sensitive,
                context=f"{context} ({block_name}.{column})",
            )
            if block_name == 'include':
                mask &= column_mask.fillna(False)
            else:
                mask &= ~column_mask.fillna(False)
            report['applied_rules'].append(f'{block_name}:{column}')
        filtered_df = filtered_df.loc[mask].copy()
    queries = data_filter.get('query', None)
    if queries is not None:
        query_list = [queries] if isinstance(queries, str) else list(queries)
        for query_expr in query_list:
            if not isinstance(query_expr, str) or len(query_expr.strip()) == 0:
                raise ValueError(f'{context}: each query expression must be a non-empty string.')
            try:
                filtered_df = filtered_df.query(query_expr, engine='python').copy()
            except Exception as err:
                raise ValueError(f"{context}: invalid query expression '{query_expr}'. {err}") from err
            report['applied_rules'].append(f'query:{query_expr}')
    rows_after = len(filtered_df)
    report['rows_after'] = rows_after
    report['rows_removed'] = rows_before - rows_after
    if rows_after == 0:
        empty_msg = f"{context}: filtering returned zero rows."
        if on_empty == 'error':
            raise ValueError(empty_msg)
        if on_empty == 'warn':
            print(f'[!] Warning: {empty_msg}')
    return (filtered_df, report)
def resolve_subplot_order(
        values: list,
        mode: Literal['auto', 'alphabetical', 'ascending', 'descending', 'custom'] = 'auto',
        custom_values: Optional[list] = None,
        case_sensitive: bool = False,
) -> list:
    """Resolve ordered subplot labels for one subplot dimension.
    
    Parameters
    ----------
    values : Any
        Argument used by `resolve_subplot_order`.
    mode : Any
        Argument used by `resolve_subplot_order`.
    custom_values : Any
        Argument used by `resolve_subplot_order`.
    case_sensitive : Any
        Argument used by `resolve_subplot_order`.
    
    Usage
    -----
    Use `resolve_subplot_order` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = resolve_subplot_order(values=..., mode=..., custom_values=..., ...)
    """
    values_list = list(values)
    if mode not in SUBPLOT_ORDER_MODES:
        raise ValueError(f"subplot_order_mode must be one of: {', '.join(SUBPLOT_ORDER_MODES)}")
    if mode == 'auto':
        return values_list
    if mode == 'alphabetical':
        return sorted(values_list, key=lambda x: _subplot_sort_key(x, case_sensitive=case_sensitive))
    if mode in ('ascending', 'descending'):
        reverse = mode == 'descending'
        if _can_sort_subplot_values_numerically(values_list):
            return sorted(values_list, key=lambda x: float(x), reverse=reverse)
        return sorted(
            values_list,
            key=lambda x: _subplot_sort_key(x, case_sensitive=case_sensitive),
            reverse=reverse,
        )
    if custom_values is None:
        raise ValueError("subplot_order_mode='custom' requires custom values for the active subplot dimension.")
    custom_list = list(custom_values)
    available_by_key = {}
    for value in values_list:
        key = _subplot_custom_match_key(value, case_sensitive=case_sensitive)
        if key not in available_by_key:
            available_by_key[key] = value
    invalid_values = []
    seen_keys = set()
    ordered_values = []
    for value in custom_list:
        key = _subplot_custom_match_key(value, case_sensitive=case_sensitive)
        if key not in available_by_key:
            invalid_values.append(value)
            continue
        if key in seen_keys:
            continue
        ordered_values.append(available_by_key[key])
        seen_keys.add(key)
    if invalid_values:
        raise ValueError(
            'Custom subplot order contains values that are not present in the data. '
            f'Invalid values: {invalid_values}. Available values: {values_list}'
        )
    # Preserve any remaining categories not explicitly listed in custom_values.
    for value in values_list:
        key = _subplot_custom_match_key(value, case_sensitive=case_sensitive)
        if key not in seen_keys:
            ordered_values.append(value)
            seen_keys.add(key)
    return ordered_values
def resolve_subplot_orders(
        dimension_values: dict,
        mode: Literal['auto', 'alphabetical', 'ascending', 'descending', 'custom'] = 'auto',
        custom: Optional[dict] = None,
        case_sensitive: bool = False,
        context: str = 'Subplot ordering',
) -> dict:
    """Resolve ordered subplot labels for multiple subplot dimensions (e.g., row/col).
    
    Parameters
    ----------
    dimension_values : Any
        Argument used by `resolve_subplot_orders`.
    mode : Any
        Argument used by `resolve_subplot_orders`.
    custom : Any
        Argument used by `resolve_subplot_orders`.
    case_sensitive : Any
        Argument used by `resolve_subplot_orders`.
    context : Any
        Label or identifier used for diagnostics and reporting.
    
    Usage
    -----
    Use `resolve_subplot_orders` within ACCIM parametric and optimisation workflows.
    
    Examples
    --------
    result = resolve_subplot_orders(dimension_values=..., mode=..., custom=..., ...)
    """
    if mode not in SUBPLOT_ORDER_MODES:
        raise ValueError(f"subplot_order_mode must be one of: {', '.join(SUBPLOT_ORDER_MODES)}")
    if custom is not None and not isinstance(custom, dict):
        raise TypeError('subplot_order_custom must be a dictionary or None.')
    active_dimensions = {
        dim_name: list(values)
        for (dim_name, values) in (dimension_values or {}).items()
        if values is not None
    }
    if mode != 'auto' and len(active_dimensions) == 0:
        raise ValueError(
            f"{context}: subplot_order_mode='{mode}' was requested but there are no active subplot dimensions."
        )
    if mode != 'custom' and custom is not None:
        raise ValueError("subplot_order_custom can only be used when subplot_order_mode='custom'.")
    if mode == 'custom':
        if custom is None:
            raise ValueError("subplot_order_mode='custom' requires subplot_order_custom.")
        invalid_dims = [dim for dim in custom.keys() if dim not in active_dimensions]
        if invalid_dims:
            raise ValueError(
                f"{context}: subplot_order_custom includes dimensions not active in this plot: {invalid_dims}. "
                f'Active dimensions: {list(active_dimensions.keys())}'
            )
    resolved = {}
    for (dim_name, values) in active_dimensions.items():
        try:
            if mode == 'custom' and dim_name not in custom:
                # Allow partial custom configuration: unspecified dimensions preserve current order.
                resolved[dim_name] = resolve_subplot_order(
                    values=values,
                    mode='auto',
                    custom_values=None,
                    case_sensitive=case_sensitive,
                )
                continue
            resolved[dim_name] = resolve_subplot_order(
                values=values,
                mode=mode,
                custom_values=custom.get(dim_name) if mode == 'custom' else None,
                case_sensitive=case_sensitive,
            )
        except Exception as err:
            raise ValueError(
                f"{context}: invalid subplot order for dimension '{dim_name}'. {err}"
            ) from err
    return resolved

