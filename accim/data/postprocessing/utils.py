"""
Classes and functions to perform data analytics after simulation runs.
"""

def preview_Table_cols(datasets: list = []):
    """
    Function to return the list of EnergyPlus Output:Variable outputs columns
    from the first CSV file in the path, suitable to be computed in the class Table,
    or the datasets, if entered. It is useful to know the full list of columns in the CSV files from simulation,
    so that columns can be filtered using the argument output_cols_to_keep in the class Table.

    :param datasets: The list of CSV files to be concatenated.
    :type datasets: list
    :return: The list of columns within the CSV files.
    """
    import pandas as pd
    import glob
    # Step: generating list of output columns

    if len(datasets) > 0:
        source_files = [
            f for f in datasets if
            'Table.csv' not in f and
            'Meter.csv' not in f and
            'Zsz.csv' not in f and
            '[CSVconcatenated.csv' not in f and
            '[Rows_not_corr_agg.csv' not in f and
            '[Rows_with_NaNs.csv' not in f
        ]
    else:
        allfiles = glob.glob('*.csv', recursive=True)
        # if path is None:
        #     allfiles = [i for i in os.listdir() if i.endswith('.csv')]
        # else:
        #     allfiles = [i for i in os.listdir(path) if i.endswith('.csv')]
        source_files = [f for f in allfiles if
                        'Table.csv' not in f and
                        'Meter.csv' not in f and
                        'Zsz.csv' not in f and
                        '[CSVconcatenated.csv' not in f and
                        '[Rows_not_corr_agg.csv' not in f and
                        '[Rows_with_NaNs.csv' not in f
                        ]
    sample_output_cols_df = pd.DataFrame(pd.read_csv(source_files[0]))
    sample_output_cols = [i for i in sample_output_cols_df.columns]
    return sample_output_cols

def genCSVconcatenated(
        datasets: list = None,
        source_frequency: str = None,
        frequency: str = None,
        output_cols_to_keep: list = None,
        datasets_per_chunk: int = 50,
        concatenated_csv_name: str = None,
        drop_nan: bool = True,
):
    """
    Function to generate concatenated CSV files from a large number of CSV files
    resulting from simulation runs.
    Useful in cases there are many CSVs, which could cause memory errors.

    :param list datasets: List of strings containing the names of the
        CSV files to be concatenated. If omitted, all CSV files are concatenated.
    :type datasets: list
    :param source_frequency: Used to inform accim about the frequency of the input CSVs.
        Strings can be 'timestep', 'hourly', 'daily', 'monthly' or 'runperiod'.
    :type source_frequency: str
    :param frequency: Rows will be aggregated based on this frequency.
        Strings can be 'timestep', 'hourly', 'daily', 'monthly' or 'runperiod'.
    :type frequency: str
    :param datasets_per_chunk: The number of CSV files for chuck to be concatenated.
    :type datasets_per_chunk: int
    :param concatenated_csv_name: A string used as the name for the concatenated csv file.
    :type concatenated_csv_name: str
    :param drop_nan: True to drop nan values.
    :type drop_nan: bool
    """
    import pandas as pd
    from accim.data.postprocessing.main import Table
    from time import time
    import os
    import gc

    start = time()

    # freq = 'runperiod'
    if datasets is None:
        datasets = [
            i for i in os.listdir() if
            i.endswith('.csv')
            and 'CSVconcatenated' not in i
            and '[Rows_with_NaNs' not in i
            and '[Rows_not_corr_agg' not in i
        ]
    else:
        datasets = [
            i for i in datasets if
            i.endswith('.csv')
            and 'CSVconcatenated' not in i
            and '[Rows_with_NaNs' not in i
            and '[Rows_not_corr_agg' not in i
        ]

    chunklist = []
    # datasets_per_chunk = 50
    for i in range(0, len(datasets), datasets_per_chunk):
        templist = datasets[i:i + datasets_per_chunk]
        chunklist.append(templist)

    # len(chunklist[-2])
    len(chunklist)
    for i in range(len(chunklist)):
        z = Table(
            datasets=chunklist[i],
            output_cols_to_keep=output_cols_to_keep,
            source_frequency=source_frequency,
            frequency=frequency,
            frequency_agg_func='sum',
            standard_outputs=True,
            concatenated_csv_name=f'{concatenated_csv_name}_Part{str(i).zfill(4)}',
            drop_nan=drop_nan
        )
        del z
        gc.collect()

    datasetlist_to_merge = [
        i for i in os.listdir() if
        i.endswith('.csv')
        and f'{concatenated_csv_name}_Part' in i
        and '[Rows_with_NaNs' not in i
        and '[Rows_not_corr_agg' not in i
        and frequency in i
    ]

    merged_datasets = []
    for i in datasetlist_to_merge:
        tempdf = pd.read_csv(i)
        merged_datasets.append(tempdf)

    concatenated_df = pd.concat(merged_datasets)
    concatenated_df.to_csv(f'{concatenated_csv_name}[srcfreq-{source_frequency}[freq-{frequency}[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv')

    for i in datasetlist_to_merge:
        os.remove(i)

    end = time()
    print('Time taken in seconds:')
    print(end - start)

    # todo pop up when process ends; by default True
