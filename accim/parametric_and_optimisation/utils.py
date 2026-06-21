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

import numpy as np
from typing import Literal, Optional


def descriptor_has_options(values):
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
    """
    Expands a dataframe with hourly data columns into an hourly dataframe.

    Parameters:
    df (pd.DataFrame): The input dataframe containing parameters and hourly data columns.
    parameter_columns (list): The list of column names that contain input parameters.
    start_date (str): The start date and time in the format 'YYYY-MM-DD HH'.

    Returns:
    pd.DataFrame: The expanded dataframe with an additional datetime column.
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
    """
    Identifies the columns which contains strings representing lists.

    :param df: the pandas DataFrame
    :return: the list of column names
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
    """
    Takes all values from all the parameters and return a pandas DataFrame with all possible combinations.

    :param parameters_values_dict: a dictionary in the format {'parameter name': list_of_values}
    :return: a pandas DataFrame with all possible combinations
    """
    from itertools import product
    combinations = list(product(*parameters_values_dict.values()))
    parameters_values_df = pd.DataFrame(combinations, columns=parameters_values_dict.keys())
    return parameters_values_df


SUBPLOT_ORDER_MODES = ('auto', 'alphabetical', 'ascending', 'descending', 'custom')


def _subplot_sort_key(value, case_sensitive: bool = False):
    text = str(value)
    return text if case_sensitive else text.casefold()


def _subplot_custom_match_key(value, case_sensitive: bool = False):
    if isinstance(value, str):
        return value if case_sensitive else value.casefold()
    return value


def _can_sort_subplot_values_numerically(values: list) -> bool:
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


def resolve_subplot_order(
        values: list,
        mode: Literal['auto', 'alphabetical', 'ascending', 'descending', 'custom'] = 'auto',
        custom_values: Optional[list] = None,
        case_sensitive: bool = False,
) -> list:
    """Resolve ordered subplot labels for one subplot dimension."""
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
    """Resolve ordered subplot labels for multiple subplot dimensions (e.g., row/col)."""
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

        missing_dims = [dim for dim in active_dimensions.keys() if dim not in custom]
        if missing_dims:
            raise ValueError(
                f"{context}: subplot_order_mode='custom' requires explicit order for active dimensions {missing_dims}. "
                f'Active dimensions: {list(active_dimensions.keys())}'
            )

        invalid_dims = [dim for dim in custom.keys() if dim not in active_dimensions]
        if invalid_dims:
            raise ValueError(
                f"{context}: subplot_order_custom includes dimensions not active in this plot: {invalid_dims}. "
                f'Active dimensions: {list(active_dimensions.keys())}'
            )

    resolved = {}
    for (dim_name, values) in active_dimensions.items():
        try:
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

