def descriptor_has_options(values):
    #Checking value entered is a list containing floats or a tuple containing the minimum and maximum values
    descriptor_has_options = False
    if type(values) == tuple and len(values) == 2 and all([type(i) == float or type(i) == int for i in values]):
        pass
    elif type(values) == list and all(type(j) == float or type(j) == int for j in values):
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

    # Keep only parameter columns and hourly columns
    df = df[parameter_columns + hourly_columns]

    # Convert string representations of lists into actual lists
    for col in hourly_columns:
        df[col] = df[col].apply(ast.literal_eval)

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
    expanded_df = pd.concat(df.apply(expand_hourly_data, axis=1).to_list(), ignore_index=True)

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
    return hourly_columns
