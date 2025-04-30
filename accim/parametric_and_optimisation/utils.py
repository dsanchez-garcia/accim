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
    hourly_columns = [
        col for col in df.columns if
        df[col].apply(lambda x: isinstance(x, str) and x.startswith('[') and x.endswith(']')).all()
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
