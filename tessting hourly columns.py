import pandas as pd

def identify_list_columns(df):
    """
    Identifies the columns which contain actual lists as elements.

    :param df: the pandas DataFrame
    :return: the list of column names
    """
    list_columns = [
        col for col in df.columns if
        df[col].apply(lambda x: isinstance(x, list)).any()
    ]
    return list_columns

# Ejemplo de uso (si tus columnas contienen listas reales)
data = {'col_float': [1.1, 2.2, 3.3],
        'col_lista': [[1.1, 2.2], [3.3], [4.4, 5.5, 6.6]],
        'col_mixta': [1.0, [2.0], 3.0]}
df = pd.DataFrame(data)

list_cols = identify_list_columns(df)
print(list_cols)