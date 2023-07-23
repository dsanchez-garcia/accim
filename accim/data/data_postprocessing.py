"""
Classes and functions to perform data analytics after simulation runs.
"""


def genCSVconcatenated(
        datasets: list = None,
        source_frequency: str = None,
        frequency: str = None,
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
    from accim.data.data_postprocessing import Table
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


class Table:
    """Generates a table or dataframe using the EnergyPlus simulation
    results CSV files available in the current folder.

    :param datasets: A list of strings. The strings are the names of the CSV files
        that you want to work with, at the working directory.
    :type datasets: list
    :param source_concatenated_csv_filepath: A string used as the filepath to read the
        previously concatenated csv file with the argument concatenated_csv_name.
    :type source_concatenated_csv_filepath: str
    :param source_frequency: Used to inform accim about the frequency
        of the input CSVs. If there are multiple frequencies in a single CSV,
        the columns for the frequencies different to the selected one will be discarded.
        String can be 'timestep', 'hourly', 'daily', 'monthly' or 'runperiod'.
    :type source_frequency: str
    :param frequency: Rows will be aggregated based on this frequency.
        String can be 'timestep', 'hourly', 'daily', 'monthly' or 'runperiod'.
        For instance, if 'daily', hourly or timesteply rows will be aggregated in days.
        String can be 'timestep', 'hourly', 'daily', 'monthly' or 'runperiod'.
    :type frequency: str
    :param frequency_agg_func: Aggregates the rows based on the defined
        frequency by sum or mean. Can be 'sum' or 'mean'.
    :type frequency_agg_func: str
    :param standard_outputs: Used to consider only standard outputs from accim.
        It can be True or False.
    :type standard_outputs: bool
    :param concatenated_csv_name: Used as the name for the concatenated csv file.
    :type concatenated_csv_name: str
    :param drop_nan: If True, drops the rows with NaNs before
        exporting the CSV using concatenated_csv_name.
    :type drop_nan: bool
    :param level: A list of strings. Strings can be 'block' and/or 'building'.
        Used to create columns with block or building values.
    :type level: list
    :param level_agg_func: A list of strings. Strings can be 'sum' and/or 'mean'.
        Used to create the columns for levels preciously stated by summing and/or averaging.
    :type level_agg_func: list
    :param level_excluded_zones: A list of strings.
        Strings must be the zones excluded from level computations.
        Used to try to match the cities in the EPW file name with actual cities.
        To be used if sample_EPWs have not been previously renamed with rename_epw_files().
    :type level_excluded_zones: list
    :param split_epw_names: It splits the EPW name into Country_City_RCPscenario-Year format.
        To be used if sample_EPWs do have been previously renamed with rename_epw_files().
    :type split_epw_names: bool
    :param normalised_energy_units: A bool, can be True or False.
        Used to show Wh or Wh/m2 units.
    :type normalised_energy_units: bool
    :param rename_cols: A bool, can be True or False.
        Used to keep the original name of EnergyPlus outputs or rename them for understanding
        purposes.
    :type rename_cols: bool
    :param energy_units_in_kwh: A bool, can be True or False.
        If True, energy units will be in kWh or kWh/m2,
        otherwise these will be in Wh or Wh/m2.
    :type energy_units_in_kwh: bool
    :param name_export_rows_with_NaN: This parameter shouldn't be generally used.
        A string used as a name to export a xlsx file with the rows with NaNs.
        Used only to check the rows with NANs.
    :type name_export_rows_with_NaN: str
    :param name_export_rows_not_corr_agg: This parameter shouldn't be generally used.
        A string used as a name to export a xlsx file with the rows not correctly aggregated.
        Used only to check the aggregations are correct.
    :type name_export_rows_not_corr_agg: str
    :ivar df: The pandas DataFrame instance.
        It is modified when method ``format_table`` is called.
    :ivar df_backup: The full pandas DataFrame instance resulting from class ``Table``.
        It is not modified, so can be used to revert the DataFrame instance to its initial state.
    :ivar cols_for_multiindex: The list of columns (or variables) that change in the dataset.
        These represent the variables that might be interesting to study, and therefore,
        the variables that are suggested to used in arguments
        ``vars_to_gather``, ``vars_to_gather_cols`` or ``vars_to_gather_rows``.
    :ivar wrangled_df_unstacked: The resulting pandas DataFrame after calling the
        method ``wrangled_table`` with ``reshaping='unstack'``
    :ivar wrangled_df_stacked: The resulting pandas DataFrame after calling the
        method ``wrangled_table`` with ``reshaping='stack'``
    :ivar wrangled_df_multiindex: The resulting pandas DataFrame after calling the
        method ``wrangled_table`` with ``reshaping='multiindex'``
    :ivar wrangled_df_pivoted: The resulting pandas DataFrame after calling the
        method ``wrangled_table`` with ``reshaping='pivot'``
    """

    def __init__(self,
                 datasets: list = None,
                 source_concatenated_csv_filepath: str = None,
                 source_frequency: str = None,
                 frequency: str = None,
                 frequency_agg_func: str = None,
                 standard_outputs: bool = None,
                 concatenated_csv_name: str = None,
                 level: list = None,
                 level_agg_func: list = None,
                 level_excluded_zones: list = None,
                 block_zone_hierarchy: dict = None,
                 split_epw_names: bool = False,
                 normalised_energy_units: bool = True,
                 rename_cols: bool = True,
                 energy_units_in_kwh: bool = True,
                 drop_nan: bool = False,
                 name_export_rows_with_NaN: str = None,
                 name_export_rows_not_corr_agg: str = None,
    ):
        """
        Constructor method
        """
        checkpoint = 0

        if datasets is None:
            datasets = []
        if level_agg_func is None:
            level_agg_func = []
        if level is None:
            level = []
        # if custom_cols is None:
        #     custom_cols = []

        import os
        import pandas as pd
        from pathlib import Path
        import datapackage
        import glob
        import numpy as np
        import csv

        self.frequency = frequency
        self.normalised_energy_units = normalised_energy_units

        # todo making guided steps to input data
        # if source_concatenated_csv_filepath is None:
        #     source_concatenated_csv_filepath = input(
        #         'You have not entered any concatenated CSV filepath. '
        #         'If you want to read the data from some concatenated CSV filepath, please add the filepath. '
        #         'Otherwise, if you want to read the data from the CSVs resulting from simulation, please hit enter.'
        #         '(filepath, or hit enter to omit): ')
        #     if len(source_concatenated_csv_filepath) == 0:
        #         source_concatenated_csv_filepath = None

        SFdict = {
            'timestep': 'Timestep',
            'hourly': 'Hourly',
            'daily': 'Daily',
            'monthly': 'Monthly',
            'runperiod': 'RunPeriod'
        }

        if source_concatenated_csv_filepath is None:
            if source_frequency not in ['timestep', 'hourly', 'daily', 'monthly', 'runperiod']:
                raise KeyError('The source frequency entered must be timestep, hourly, daily, monthly or runperiod.')

        if source_frequency == 'runperiod':
            if frequency in ['timestep', 'hourly', 'daily', 'monthly']:
                raise KeyError(f'Source frequency is {source_frequency}, therefore '
                               f'monthly, daily, hourly or timestep output frequency cannot be selected.')
        if source_frequency == 'monthly':
            if frequency in ['timestep', 'hourly', 'daily']:
                raise KeyError(f'Source frequency is {source_frequency}, therefore '
                               f'daily, hourly or timestep output frequency cannot be selected.')
        if source_frequency == 'daily':
            if frequency in ['timestep', 'hourly']:
                raise KeyError(f'Source frequency is {source_frequency}, therefore '
                               f'hourly or timestep output frequency cannot be selected.')
        if source_frequency == 'hourly':
            if frequency in ['timestep']:
                raise KeyError(f'Source frequency is {source_frequency}, therefore '
                               f'timestep output frequency cannot be selected.')

        flowchart_state_in_paper = 'A.1'

        if source_concatenated_csv_filepath is not None:
            for i in source_concatenated_csv_filepath.split('['):
                if i.split('-')[0] == 'srcfreq':
                    source_frequency = i.split('-')[1]
                    self.source_frequency = source_frequency
                if i.split('-')[0] == 'freq':
                    frequency = i.split('-')[1]
                    self.frequency = frequency
                elif i.split('-')[0] == 'frequency_agg_func':
                    frequency_agg_func = i.split('-')[1]
                elif i.split('-')[0] == 'standard_outputs':
                    standard_outputs = i.split('-')[1]
                    if standard_outputs == 'True':
                        standard_outputs = True
                    else:
                        standard_outputs = False

        if source_frequency in ['timestep', 'hourly']:
            aggregation_list_first = [
                'Date/Time',
                'Source',
                'Month/Day',
                'Month',
                'Day',
                'Hour',
                'Minute',
                'Second'
            ]
        elif source_frequency == 'daily':
            aggregation_list_first = [
                'Date/Time',
                'Source',
                'Month/Day',
                'Month',
                'Day',
            ]
        elif source_frequency == 'monthly':
            aggregation_list_first = [
                'Date/Time',
                'Source',
                # 'Month/Day',
                'Month',
            ]
        elif source_frequency == 'runperiod':
            aggregation_list_first = [
                'Date/Time',
                'Source',
            ]

        # Step: generating concatenated dataframe.
        # If source_concatenated_csv_filepath is None, then specified csv files on list format
        # are considered, otherwise all csv in the folder are considered.
        # If source_concatenated_csv_filepath is not None, then the csv path is considered to
        # build the dataframe.

        flowchart_state_in_paper = 'A.2'
        if source_concatenated_csv_filepath is None:
            if len(datasets) > 0:
                flowchart_state_in_paper = 'A.2.1'
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
                flowchart_state_in_paper = 'A.2.2'
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
                # todo check if glob.glob works with in terms of package, if not switch back to sorted
                # source_files = sorted(Path(os.getcwd()).glob('*.csv'))

            cleaned_columns = [

                # 'Date/Time',
                'Environment:Site Outdoor Air Drybulb Temperature',
                'Environment:Site Wind Speed',
                'Environment:Site Outdoor Air Relative Humidity',
                'EMS:Comfort Temperature',
                'EMS:Adaptive Cooling Setpoint Temperature',
                'EMS:Adaptive Heating Setpoint Temperature',
                'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance',
                'EMS:Adaptive Heating Setpoint Temperature_No Tolerance',
                'EMS:Ventilation Setpoint Temperature',
                'EMS:Minimum Outdoor Temperature for ventilation',
                'EMS:Comfortable Hours_No Applicability',
                'EMS:Comfortable Hours_Applicability',
                'EMS:Discomfortable Applicable Hot Hours',
                'EMS:Discomfortable Applicable Cold Hours',
                'EMS:Discomfortable Non Applicable Hot Hours',
                'EMS:Discomfortable Non Applicable Cold Hours',
                'EMS:Ventilation Hours',
                'AFN Zone Infiltration Volume',
                'AFN Zone Infiltration Air Change Rate',
                'AFN Zone Ventilation Volume',
                'AFN Zone Ventilation Air Change Rate',
                # 'Zone Thermostat Operative Temperature [C](Hourly)',
                # 'Zone Operative Temperature [C](Hourly)',
                'Zone Operative Temperature',
                'Whole Building:Facility Total HVAC Electricity Demand Rate',
                # 'Whole Building Facility Total HVAC Electricity Demand Rate (kWh)',
                'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature',
                'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature',
                '_Sch',
                'VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate',
                'VRF INDOOR UNIT DX HEATING COIL:Heating Coil Heating Rate',
                # 'VRF OUTDOOR UNIT',
                'VRF Heat Pump Cooling Electricity Rate',
                'VRF Heat Pump Heating Electricity Rate',
                'VRF Heat Pump Cooling Electricity Energy',
                'VRF Heat Pump Heating Electricity Energy',
                'Heating Coil Heating Rate',
                'Cooling Coil Total Cooling Rate',
                'Zone Air Volume',
                'Zone Floor Area',
                'Zone Thermal Comfort Fanger Model PMV',
                'Zone Thermal Comfort Fanger Model PPD'
            ]

            summed_dataframes = []

            flowchart_state_in_paper = 'A.3'
            for file in source_files:

                # with open(file) as csv_file:
                #     csv_reader = csv.reader(csv_file, delimiter=',')
                #     df = pd.DataFrame([csv_reader], index=True)

                df = pd.DataFrame(pd.read_csv(file))

                # Step: filtering outputs to only standards
                if standard_outputs:
                    keeplist = []
                    for i in cleaned_columns:
                        for j in df.columns:
                            if i in j:
                                if SFdict[source_frequency] in j:
                                    keeplist.append(j)
                    keeplist = list(dict.fromkeys(keeplist))
                    keeplist.append('Date/Time')
                    droplist = list(set(df.columns) - set(keeplist))
                    df = df.drop(droplist, axis=1)

                # df['Source'] = file.name
                df['Source'] = file

                # df['Date/Time_orig'] = df['Date/Time'].copy()
                if source_frequency in ['timestep', 'hourly']:
                    df[['TBD1', 'Month/Day', 'TBD2', 'Hour']] = df['Date/Time'].str.split(' ', expand=True)
                    df = df.drop(['TBD1', 'TBD2'], axis=1)
                    df[['Month', 'Day']] = df['Month/Day'].str.split('/', expand=True)
                    df[['Hour', 'Minute', 'Second']] = df['Hour'].str.split(':', expand=True)
                elif source_frequency == 'daily':
                    df['Month/Day'] = df['Date/Time']
                    df[['Month', 'Day']] = df['Date/Time'].str.split('/', expand=True)
                elif source_frequency == 'monthly':
                    df['Month'] = df['Date/Time']
                elif source_frequency == 'runperiod':
                    pass

                # Step: managing different aggregations on columns
                constantcols = []
                for i in [
                    'Zone Air Volume',
                    'Zone Floor Area'
                ]:
                    for j in df.columns:
                        if i in j:
                            constantcols.append(j)
                constantcols = list(dict.fromkeys(constantcols))
                constantcolsdict = {}

                for i in range(len(constantcols)):
                    tempdict = {constantcols[i]: df[constantcols[i]][0]}
                    constantcolsdict.update(tempdict)

                if source_frequency in ['timestep', 'hourly']:
                    minute_df_len = len(
                        df[
                            (df['Minute'] != '00') &
                            (df['Minute'].astype(str) != 'None') &
                            (df['Minute'] != '')
                            ]
                    )

                agg_dict = {}

                for i in aggregation_list_first:
                    agg_dict.update({i: 'first'})

                for i in constantcols:
                    agg_dict.update({i: 'first'})

                df['count'] = 1
                agg_dict.update({'count': 'count'})

                aggregation_list_mean = [
                    'Environment:Site Outdoor Air Drybulb Temperature',
                    'Environment:Site Wind Speed',
                    'Environment:Site Outdoor Air Relative Humidity',
                    'EMS:Comfort Temperature',
                    'EMS:Adaptive Cooling Setpoint Temperature',
                    'EMS:Adaptive Heating Setpoint Temperature',
                    'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance',
                    'EMS:Adaptive Heating Setpoint Temperature_No Tolerance',
                    'EMS:Ventilation Setpoint Temperature',
                    'EMS:Minimum Outdoor Temperature for ventilation',
                    # 'Zone Thermostat Operative Temperature',
                    # 'Zone Operative Temperature',
                    'Zone Operative Temperature',
                    'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature',
                    'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature',
                    'Zone Thermal Comfort Fanger Model PMV',
                    'Zone Thermal Comfort Fanger Model PPD'
                ]

                for i in df.columns:
                    for j in aggregation_list_mean:
                        if j in i:
                            agg_dict.update({i: 'mean'})

                for i in df.columns:
                    if i not in agg_dict:
                        agg_dict.update({i: frequency_agg_func})

                if source_frequency == 'timestep' or source_frequency == 'hourly':
                    # todo timestep frequency to be tested
                    if frequency == 'timestep':
                        df = df.groupby(['Source', 'Month', 'Day', 'Hour', 'Minute'], as_index=False).agg(agg_dict)
                        print(f'Input data frequency in file {file} is timestep '
                              f'and requested frequency is also timestep, '
                              f'therefore no aggregation will be performed. '
                              f'The user needs to check the output rows number is correct.')
                    if frequency == 'hourly':
                        if minute_df_len > 0:
                            df = df.groupby(['Source', 'Month', 'Day', 'Hour'], as_index=False).agg(agg_dict)
                            print(f'Input data frequency in file {file} is timestep '
                                  f'and requested frequency is hourly, '
                                  f'therefore aggregation will be performed. '
                                  f'The user needs to check the output rows number is correct.')
                        else:
                            print(f'Input data frequency in file {file} is hourly, therefore no aggregation will be performed.')
                    if frequency == 'daily':
                        df = df.groupby(['Source', 'Month', 'Day'], as_index=False).agg(agg_dict)
                    if frequency == 'monthly':
                        df = df.groupby(['Source', 'Month'], as_index=False).agg(agg_dict)
                    if frequency == 'runperiod':
                        df = df.groupby(['Source'], as_index=False).agg(agg_dict)
                    for i in constantcolsdict:
                        df[i] = constantcolsdict[i]
                    summed_dataframes.append(df)
                elif source_frequency == 'daily':
                    if frequency in ['timestep', 'hourly']:
                        print(f'Source frequency in file {file} is daily, therefore timestep or hourly aggregations cannot be performed.')
                    elif frequency == 'daily':
                        print(f'Source frequency in file {file} is daily, therefore no aggregation will be performed.')
                    elif frequency == 'monthly':
                        df = df.groupby(['Source', 'Month'], as_index=False).agg(agg_dict)
                    elif frequency == 'runperiod':
                        df = df.groupby(['Source'], as_index=False).agg(agg_dict)
                    summed_dataframes.append(df)
                elif source_frequency == 'monthly':
                    if frequency in ['timestep', 'hourly', 'daily']:
                        print(f'Source frequency in file {file} is monthly, therefore timestep, hourly or daily aggregations cannot be performed.')
                    elif frequency == 'monthly':
                        print(f'Source frequency in file {file} is monthly, therefore no aggregation will be performed.')
                    elif frequency == 'runperiod':
                        df = df.groupby(['Source'], as_index=False).agg(agg_dict)
                    summed_dataframes.append(df)
                elif source_frequency == 'runperiod':
                    if frequency in ['timestep', 'hourly', 'daily', 'monthly']:
                        print(f'Source frequency in file {file} is runperiod, therefore timestep, hourly, daily or monthly aggregations cannot be performed.')
                    elif frequency == 'runperiod':
                        print(f'Source frequency in file {file} is runperiod, therefore no aggregation will be performed.')
                    summed_dataframes.append(df)
            df = pd.concat(summed_dataframes)
            # df = df.round(decimals=2)

        else:
            # todo amend order of columns
            df = pd.read_csv(filepath_or_buffer=source_concatenated_csv_filepath)
            df = df.drop(columns=df.columns[0])
            cols = df.columns.tolist()
            cols = cols[-1:] + cols[:-1]
            df = df[cols]

        checkpoint = checkpoint + 1

        # Step: checking for NaNs and not correct aggregations based on count
        is_NaN = df.isna()
        row_has_NaN = is_NaN.any(axis=1)
        rows_with_NaN = df[row_has_NaN]
        if len(rows_with_NaN) > 0:
            print('Please bear in mind if you are using CSVs with multiple frequencies, you will get NaNs. The following rows have NaN values:')
            print(rows_with_NaN)
            if name_export_rows_with_NaN is not None:
                rows_with_NaN.to_excel(f'{name_export_rows_with_NaN}[source_freq-{source_frequency}[freq-{frequency}[Rows_with_NaNs.xlsx')

        if self.frequency == 'hourly':
            not_correct_agg = df[df['count'] != 1]
            # if len(not_correct_agg) > 0:
            #     print('The following rows have not been correctly aggregated:')
            #     print(not_correct_agg)

        if self.frequency == 'daily':
            if source_frequency == 'hourly':
                not_correct_agg = df[df['count'] != 24]
            if source_frequency == 'daily':
                not_correct_agg = df[df['count'] != 1]

            # if len(not_correct_agg) > 0:
            #     print('The following rows have not been correctly aggregated:')
            #     print(not_correct_agg)

        if self.frequency == 'monthly':

            # not_correct_agg_list = []
            # from calendar import monthrange
            # for i in range(1, 13):
            #     monthly_df = df[
            #         (
            #                 (df['Month'] == i) &
            #                 (df['count'] != (monthrange(2022, i)[1])*24)
            #         ) |
            #         (
            #                 (df['Month'] == i) &
            #                 (df['count'] != 28 * 24) &
            #                 (df['count'] != 30 * 24) &
            #                 (df['count'] != 31 * 24)
            #         )
            #     ]
            #     not_correct_agg_list.append(monthly_df)
            # not_correct_agg = pd.concat(not_correct_agg_list)

            if source_frequency == 'hourly':
                not_correct_agg = df[
                    (df['count'] != 28 * 24) &
                    (df['count'] != 30 * 24) &
                    (df['count'] != 31 * 24)
                    ]
            if source_frequency == 'daily':
                not_correct_agg = df[
                    (df['count'] != 28) &
                    (df['count'] != 30) &
                    (df['count'] != 31)
                    ]
            # if len(not_correct_agg) > 0:
            #     print('The following rows have not been correctly aggregated:')
            #     print(not_correct_agg)

        if self.frequency == 'runperiod':
            if source_frequency == 'hourly':
                not_correct_agg = df[df['count'] != 8760]
            if source_frequency == 'daily':
                not_correct_agg = df[df['count'] != 365]
            if source_frequency == 'monthly':
                not_correct_agg = df[df['count'] != 12]
            if source_frequency == 'runperiod':
                not_correct_agg = df[df['count'] != 1]
            # if len(not_correct_agg) > 0:
            #     print('The following rows have not been correctly aggregated:')
            #     print(not_correct_agg)

        try:
            if len(not_correct_agg) > 0:
                print('The following rows have not been correctly aggregated:')
                print(not_correct_agg)
                if name_export_rows_not_corr_agg is not None:
                    not_correct_agg.to_excel(
                        f'{name_export_rows_not_corr_agg}[source_freq-{source_frequency}[freq-{frequency}[Rows_not_corr_agg.xlsx')
        except UnboundLocalError:
            print('All rows have been correctly aggregated')

        checkpoint = checkpoint + 1

        if concatenated_csv_name is not None:
            # df.to_excel(
            #     f'{concatenated_csv_name}'
            #     f'[freq-{frequency}'
            #     f'[frequency_agg_func-{frequency_agg_func}'
            #     f'[standard_outputs-{standard_outputs}'
            #     f'[CSVconcatenated.xlsx'
            # )
            if drop_nan == True:
                df = df.dropna(axis='columns', how='all')
                df = df.dropna(axis='index', how='any')
            df.to_csv(
                f'{concatenated_csv_name}'
                f'[srcfreq-{source_frequency}'
                f'[freq-{frequency}'
                f'[frequency_agg_func-{frequency_agg_func}'
                f'[standard_outputs-{standard_outputs}'
                f'[CSVconcatenated.csv'
            )
            if len(rows_with_NaN) > 0:
                rows_with_NaN.to_csv(
                    f'{concatenated_csv_name}'
                    f'[srcfreq-{source_frequency}'
                    f'[freq-{frequency}'
                    f'[frequency_agg_func-{frequency_agg_func}'
                    f'[standard_outputs-{standard_outputs}'
                    f'[Rows_with_NaNs.csv'
                )
            if len(not_correct_agg) > 0:
                not_correct_agg.to_csv(
                    f'{concatenated_csv_name}'
                    f'[srcfreq-{source_frequency}'
                    f'[freq-{frequency}'
                    f'[frequency_agg_func-{frequency_agg_func}'
                    f'[standard_outputs-{standard_outputs}'
                    f'[Rows_not_corr_agg.csv'
                )
            return

        checkpoint = checkpoint + 1

        # if len(rows_with_NaN) > 0 or len(not_correct_agg) > 0:
        #     f = open(f'{concatenated_csv_name}[freq-{frequency}[frequency_agg_func-{frequency_agg_func}[standard_outputs-{standard_outputs}[Report.txt', "w+")
        #     if len(rows_with_NaN) > 0:
        #         f.write('The following rows have NaN values:\r\n')
        #         dfAsString = rows_with_NaN.to_string(header=True, index=True)
        #         f.write(dfAsString)
        #     if len(not_correct_agg) > 0:
        #         f.write('The following rows have not been correctly aggregate:\r\n')
        #         dfAsString = not_correct_agg.to_string(header=True, index=True)
        #         f.write(dfAsString)
        #     f.close()

        # df.to_excel('checkpoint_00.xlsx')

        # Step: scanning zones for occupied_zone_list
        # OpTempColumn = [i for i in df.columns if 'Zone Thermostat Operative Temperature [C](Hourly)' in i]
        # if len(OpTempColumn) == 0:
        #     OpTempColumn = [i for i in df.columns if 'Zone Operative Temperature [C](Hourly)' in i]

        # occupied_zone_list = [i.split(' ')[0][:-5]
        #                        for i
        #                        in [i
        #                              for i
        #                              in df.columns
        #                              if 'Zone Thermostat Operative Temperature [C](Hourly)' in i
        #                              ]
        #                        ]
        # if len(occupied_zone_list) == 0:

        df.columns = [i.upper() for i in df.columns]
        block_list = []
        #Step: scanning occupied zones
        if all([j == 2 for j in [i.count(':') for i in df.columns if 'ZONE OPERATIVE TEMPERATURE' in i]]):
            occupied_zone_list = [i.split(' ')[0][:-5] for i in [i for i in df.columns if 'ZONE OPERATIVE TEMPERATURE' in i]]
        else:
            if all([j == 1 for j in [i.count(':') for i in df.columns if 'ZONE OPERATIVE TEMPERATURE' in i]]):
                total_occupied_zones = [i.split(':')[0].upper() for i in df.columns if 'ZONE OPERATIVE TEMPERATURE' in i]
                for i in total_occupied_zones:
                    df.columns = [j.replace(i, i.replace(' ', '_')) for j in df.columns]
                total_occupied_zones = [i.replace(' ', '_') for i in total_occupied_zones]
            else:
                occupied_zone_list_1 = [i.split(' ')[0][:-5] for i in [i for i in df.columns if 'ZONE OPERATIVE TEMPERATURE' in i]]
                occupied_zone_list_2 = [i.split(':')[0] for i in df.columns if 'ZONE OPERATIVE TEMPERATURE' in i]
                total_occupied_zones = occupied_zone_list_1 + occupied_zone_list_2
                total_occupied_zones = list(dict.fromkeys(total_occupied_zones))
            if block_zone_hierarchy is None:
                print(
                    'Regarding occupied zones, we have not found a clear hierarchical pattern of blocks and zones. '
                    'The zones we have found are:'
                    )
                print(total_occupied_zones)
                block_list = list(i.upper() for i in input('Please enter all Blocks separated by semicolon (;): ').split(';'))
                hierarchy_dict = {}
                for i in block_list:
                    temp_zones = list(i.upper() for i in input(f'Please enter the zones for {i}, considering these cannot be at the same time in more than one block, separated by semicolon (;): ').split(';'))
                    temp_dict = {i: temp_zones}
                    hierarchy_dict.update(temp_dict)
            else:
                # hierarchy_dict = block_zone_hierarchy
                hierarchy_dict = {i.upper(): [k.upper() for k in j] for i, j in block_zone_hierarchy.items()}

            for i in hierarchy_dict:
                for j in hierarchy_dict[i]:
                    df.columns = [k.replace(j, i+'_'+j) for k in df.columns]
                    # df.columns = [k.replace(j.upper().replace(' ', '_'), i + '_' + j) for k in df.columns]

            print('Finally, the occupied zones after renaming them following the pattern block_zone are:')
            occupied_zone_list = []
            for i in hierarchy_dict:
                for j in hierarchy_dict[i]:
                    occupied_zone_list.append(f'{i}_{j}')
                    print(f'{i}_{j}')




        # if len(occupied_zone_list) == 0:
        #     occupied_zone_list = [i.split(' ')[0][:-5]
        #                     for i
        #                     in [i
        #                         for i
        #                         in df.columns
        #                         if 'Operative Temperature' in i
        #                         ]
        #                     ]
        # occupied_zone_list = [i.split(' ')[0][:-5] for i in OpTempColumn]
        occupied_zone_list = list(dict.fromkeys(occupied_zone_list))

        occBZlist_underscore = [i.replace(':', '_') for i in occupied_zone_list]

        # Step: scanning zones for hvac_zone_list

        if all([j == 2 for j in [i.count(':') for i in df.columns if 'Cooling Coil Total Cooling Rate'.upper() in i]]):
            hvac_zone_list = [i.split(' ')[0] for i in [i for i in df.columns if 'Cooling Coil Total Cooling Rate'.upper() in i]]
        else:
            if all([j == 1 for j in [i.count(':') for i in df.columns if 'Cooling Coil Total Cooling Rate'.upper() in i]]):
                hvac_zone_list = [i.split(':')[0].split()[0].upper() for i in df.columns if 'Cooling Coil Total Cooling Rate'.upper() in i]

        # hvac_zone_list = [i.split(' ')[0] for i in [i for i in df.columns if 'Cooling Coil Total Cooling Rate'.upper() in i]]

        hvac_zone_list = list(dict.fromkeys(hvac_zone_list))
        hvac_zone_list_underscore = [i.replace(':', '_') for i in hvac_zone_list]

        # Step: scanning blocks for block_list
        if len(block_list) == 0:
            if all([j == 2 for j in [i.count(':') for i in df.columns if 'ZONE OPERATIVE TEMPERATURE' in i]]):
                block_list = [i.split(':')[0] for i in occupied_zone_list]
            elif all([j == 1 for j in [i.count(':') for i in df.columns if 'ZONE OPERATIVE TEMPERATURE' in i]]):
                block_list = [i.split('_')[0] for i in occupied_zone_list]
            block_list = list(dict.fromkeys(block_list))

        # Step: renaming all columns containing BlockX_ZoneX patterns to BlockX:ZoneX.
        renamezonesdict = {}
        for i in range(len(occBZlist_underscore)):
            for j in df.columns:
                if occBZlist_underscore[i].lower() in j.lower():
                    temp = {j: j.replace(occBZlist_underscore[i], occupied_zone_list[i])}
                    renamezonesdict.update(temp)

        df = df.rename(columns=renamezonesdict)

        # Step: converting jules to Wh if any
        for i in df.columns:
            if 'VRF OUTDOOR UNIT' in i and '[J]' in i:
                df[i] = df[i] / 3600

        renamedict = {}

        for i in df.columns:
            if 'VRF OUTDOOR UNIT' in i and '[J]' in i:
                temp = {i: i.replace('[J]', '[W]')}
                renamedict.update(temp)

        df = df.rename(columns=renamedict)

        # Step: generating total (heating+cooling) energy consumption columns
        BZoutputDict = {
            'VRF INDOOR UNIT': 'Total Energy Demand (Wh)',
            'VRF OUTDOOR UNIT': 'Total Energy Consumption (Wh)'
        }
        for output in BZoutputDict:
            for block_zone in hvac_zone_list:
                df[f'{block_zone}' + '_' + BZoutputDict[output] + ' (summed)_pymod'] = df[
                    [i for i in df.columns
                     if block_zone.lower() in i.lower() and output in i and '_pymod' not in i]
                ].sum(axis=1)
        # df.to_excel('checkpoint_01.xlsx')

        # Step: generating block and or building summed or mean columns
        outputdict = {
            # 'Zone Thermostat Operative Temperature [C](Hourly)': 'Zone Thermostat Operative Temperature (°C)',
            # 'Zone Operative Temperature [C](Hourly)': 'Zone Operative Temperature (°C)',
            'Zone Operative Temperature': 'Zone Operative Temperature (°C)',
            'Comfortable Hours_No Applicability': 'Comfortable Hours_No Applicability (h)',
            'Comfortable Hours_Applicability': 'Comfortable Hours_Applicability (h)',
            'Discomfortable Applicable Hot Hours': 'Discomfortable Applicable Hot Hours (h)',
            'Discomfortable Applicable Cold Hours': 'Discomfortable Applicable Cold Hours (h)',
            'Discomfortable Non Applicable Hot Hours': 'Discomfortable Non Applicable Hot Hours (h)',
            'Discomfortable Non Applicable Cold Hours': 'Discomfortable Non Applicable Cold Hours (h)',
            'Ventilation Hours': 'Ventilation Hours (h)',
            'AFN Zone Infiltration Volume': 'AFN Zone Infiltration Volume (m3)',
            'AFN Zone Infiltration Air Change Rate': 'AFN Zone Infiltration Air Change Rate (ach)',
            'AFN Zone Ventilation Volume': 'AFN Zone Ventilation Volume (m3)',
            'AFN Zone Ventilation Air Change Rate': 'AFN Zone Ventilation Air Change Rate (ach)',

            'Cooling Coil Total Cooling Rate': 'Cooling Coil Total Cooling Rate (Wh)',
            'Heating Coil Heating Rate': 'Heating Coil Heating Rate (Wh)',

            # 'VRF Heat Pump Cooling Electricity Rate': 'VRF Heat Pump Cooling Electricity Rate (Wh)',
            # 'VRF Heat Pump Heating Electricity Rate': 'VRF Heat Pump Heating Electricity Rate (Wh)',
            'VRF Heat Pump Cooling Electricity Energy': 'VRF Heat Pump Cooling Electricity Energy (Wh)',
            'VRF Heat Pump Heating Electricity Energy': 'VRF Heat Pump Heating Electricity Energy (Wh)',

            'Coil': 'Total Energy Demand (Wh)',
            'VRF OUTDOOR UNIT': 'Total Energy Consumption (Wh)',
            'Zone Air Volume': 'Zone Air Volume (m3)',
            'Zone Floor Area': 'Zone Floor Area (m2)',
            'Zone Thermal Comfort Fanger Model PMV': 'PMV',
            'Zone Thermal Comfort Fanger Model PPD': 'PPD (%)'
        }
        # todo paper aqui
        if level_excluded_zones is None:
            print('The occupied zones are:')
            print(occupied_zone_list)
            print('The hvac zones zones are:')
            print(hvac_zone_list)
            level_excluded_zones = list(i for i in input('If you want to exclude some zones from level computations, please enter the names separated by semicolon (;), otherwise hit enter:').split(';'))
        if len(level_excluded_zones) > 0:
            if not(level_excluded_zones[0] == ''):
                not_valid_zones = []
                for i in level_excluded_zones:
                    if i not in occupied_zone_list:
                        not_valid_zones.append(i)
                while len(not_valid_zones) > 0:
                    print('The following excluded zones do not exist:')
                    print(*not_valid_zones, sep='\n')
                    print('The zones you can exclude from level computations are:')
                    print(*occupied_zone_list, sep='\n')
                    level_excluded_zones = [i for i in level_excluded_zones if i not in not_valid_zones]
                    level_excluded_zones = list(i for i in input('If you want to exclude some zones from level computations, please enter the names separated by semicolon (;), otherwise hit enter:').split(';'))
                    not_valid_zones = []
                    for i in level_excluded_zones:
                        if i not in occupied_zone_list:
                            not_valid_zones.append(i)

        if len(level_excluded_zones) == 0:
            print('No zones have been excluded from level computations.')
        elif len(level_excluded_zones) == 1:
            if level_excluded_zones[0] == '':
                level_excluded_zones = []
                print('No zones have been excluded from level computations.')

        if any('block' in i for i in level):
            for output in outputdict:
                for block in block_list:
                    if any('sum' in j for j in level_agg_func):
                        df[f'{block}' + '_Total_' + outputdict[output] + ' (summed)_pymod'] = df[
                            [i for i in df.columns if block.lower() in i.lower() and output.upper() in i.upper() and '_pymod' not in i.lower() and not (any(k.upper() in i.upper() for k in level_excluded_zones))]
                        ].sum(axis=1)
                    else:
                        if normalised_energy_units:
                            if 'Zone Air Volume' in output or 'Zone Floor Area' in output:
                                df[f'{block}' + '_Total_' + outputdict[output] + ' (summed)_pymod'] = df[
                                    [i for i in df.columns if block.lower() in i.lower() and output.upper() in i.upper() and '_pymod' not in i.lower() and not (any(k.upper() in i.upper() for k in level_excluded_zones))]
                                ].sum(axis=1)
                    if any('mean' in j for j in level_agg_func):
                        if 'Zone Air Volume' in output or 'Zone Floor Area' in output:
                            continue
                        else:
                            df[f'{block}' + '_Total_' + outputdict[output] + ' (mean)_pymod'] = df[
                                [i for i in df.columns
                                 if block.lower() in i.lower() and output.upper() in i.upper() and '_pymod' not in i.lower()]
                            ].mean(axis=1)
        if any('building' in i for i in level):
            for output in outputdict:
                if any('sum' in j for j in level_agg_func):
                    df['Building_Total_' + outputdict[output] + ' (summed)_pymod'] = df[
                        [i for i in df.columns if output.upper() in i.upper() and '_pymod' not in i.lower() and not (any(k.upper() in i for k in level_excluded_zones))]].sum(axis=1)
                else:
                    if normalised_energy_units:
                        if 'Zone Air Volume' in output or 'Zone Floor Area' in output:
                            df['Building_Total_' + outputdict[output] + ' (summed)_pymod'] = df[
                                [i for i in df.columns if output.upper() in i.upper() and '_pymod' not in i.lower() and not (any(k.upper() in i for k in level_excluded_zones))]].sum(axis=1)
                if any('mean' in j for j in level_agg_func):
                    if 'Zone Air Volume' in output or 'Zone Floor Area' in output:
                        continue
                    else:
                        df['Building_Total_' + outputdict[output] + ' (mean)_pymod'] = df[
                            [i for i in df.columns if output.upper() in i.upper() and '_pymod' not in i.lower() and not (any(k.upper() in i for k in level_excluded_zones))]].mean(axis=1)

        # df.to_excel('checkpoint_02.xlsx')

        # Step: renaming energy units
        renamedict = {}
        for i in df.columns:
            if '[W]' in i:
                temp = {i: i.replace('[W]', '(Wh)')}
                renamedict.update(temp)
        df = df.rename(columns=renamedict)

        if normalised_energy_units:
            if energy_units_in_kwh:
                energy_units = '(kWh/m2)'
            else:
                energy_units = '(Wh/m2)'
        else:
            if energy_units_in_kwh:
                energy_units = '(kWh)'
            else:
                energy_units = '(Wh)'

        # Step: normalising energy units if requested
        if normalised_energy_units:
            for i in df.columns:
                if '(Wh)' in i or '(WH)' in i:
                    for j in hvac_zone_list:
                        if j in i:
                            df[i] = df[i] / df[[i for i in df.columns if 'Zone Floor Area'.upper() in i.upper() and j.lower() in i.lower()][0]]
                    for k in block_list:
                        if k + '_Total_' in i:
                            df[i] = df[i] / df[
                                [i for i in df.columns
                                 if 'Zone Floor Area'.upper() in i.upper()
                                 and k.lower() + '_Total_'.lower() in i.lower()][0]]
                    if 'Building_Total_' in i:
                        df[i] = df[i] / df[
                            [i for i in df.columns
                             if 'Zone Floor Area'.upper() in i.upper()
                             and 'Building_Total_'.lower() in i.lower()][0]]
                    if any('building' in x for x in level):
                        # try:
                        if 'Whole Building:Facility Total HVAC Electricity Demand Rate'.upper() in i.upper():
                            df[i] = df[i] / df[[i for i in df.columns if 'Zone Floor Area'.upper() in i.upper() and 'Building_Total_'.lower() in i.lower()][0]]
                        # except IndexError:
                        #     try:
                        #         if 'Whole Building Facility Total HVAC Electricity Demand Rate' in i:
                        #             df[i] = df[i] / df[
                        #                 [i for i in df.columns
                        #                  if 'Zone Floor Area' in i
                        #                  and 'Building_Total_'.lower() in i.lower()][0]]
                        #     except IndexError:
                        #         print('Facility Total HVAC Electricity Demand Rate has not been computed in normalisez energy consumption.')

        # df.to_excel('checkpoint_03-0.xlsx')

        # Step: converting Wh to kWh if requested
        if energy_units_in_kwh:
            for col in df.columns:
                if '(Wh)'.upper() in col.upper():
                    df[col] = df[col] / 1000

        # df.to_excel('checkpoint_03-1.xlsx')

        energy_units_dict = {}
        for i in df.columns:
            if '(Wh)'.upper() in i.upper():
                temp = {i: i.replace('(Wh)', energy_units)}
                energy_units_dict.update(temp)
        df = df.rename(columns=energy_units_dict)

        # df.to_excel('checkpoint_03-2.xlsx')

        # Step: removing '_pymod' from columns
        df.set_axis(
            labels=[c[:-6] if c.endswith('_pymod') else c for c in df],
            axis=1,
            inplace=True
        )

        # Step: splitting and managing column names
        fixed_columns_orig = [
            'Model',
            'ComfStand',
            'CAT',
            'ComfMod',
            'HVACmode',
            'VentCtrl',
            'VSToffset',
            'MinOToffset',
            'MaxWindSpeed',
            'ASTtol',
            'NameSuffix',
            'EPW'
        ]
        fixed_columns = [i.upper() for i in fixed_columns_orig]

        df[fixed_columns] = df['SOURCE'].str.split('[', expand=True)

        # df['Model'] = df['Model'].str[:-6]
        # df['ComfStand'] = df['ComfStand'].str[3:]
        # df['Category'] = df['Category'].str[3:]
        # df['ComfMod'] = df['ComfMod'].str[3:]
        # df['HVACmode'] = df['HVACmode'].str[3:]
        # df['VentCtrl'] = df['VentCtrl'].str[3:]
        # df['VSToffset'] = df['VSToffset'].str[3:]
        # df['MinOToffset'] = df['MinOToffset'].str[3:]
        # df['MaxWindSpeed'] = df['MaxWindSpeed'].str[3:]
        # df['ASTtol'] = df['ASTtol'].str[3:]
        df['EPW'] = df['EPW'].str[:-4]
        df['SOURCE'] = df['SOURCE'].str[:-4]

        # Step: splitting EPW names if requested
        self.split_epw_names = split_epw_names

        if split_epw_names:
            cols_epw_base = [
                'EPW_Country_name',
                'EPW_City_or_subcountry',
                'EPW_Scenario-Year'
            ]
            df[cols_epw_base] = df['EPW'].str.split('_', expand=True)
            try:
                cols_epw_ext = [
                    'EPW_Scenario',
                    'EPW_Year',
                ]
                df[cols_epw_ext] = df['EPW_Scenario-Year'].str.split('-', expand=True)
            except ValueError:
                print('All CSVs are for present scenario.')
                df['EPW_Scenario'] = 'Present'
                df['EPW_Year'] = 'Present'
            df.EPW_Year.fillna(value='Present', inplace=True)

        df = df.set_index([pd.RangeIndex(len(df))])

        if drop_nan == True:
            df = df.dropna(axis='columns', how='all')
            df = df.dropna(axis='index', how='any')
            df = df.set_index([pd.RangeIndex(len(df))])

        # Step: do not know what it is this for
        frequency_dict = {
            'monthly': ['MONTH'],
            'daily': ['DAY', 'MONTH'],
            'hourly': ['DAY', 'MONTH', 'HOUR'],
            'timestep': ['DAY', 'MONTH', 'HOUR', 'MINUTE']
        }
        if self.frequency != 'runperiod':
            for i in frequency_dict[self.frequency]:
                for j in range(len(df)):
                    if df.loc[j, i] is None:
                        df.loc[j, i] = str(int((int(df.loc[j - 1, i]) + int(df.loc[j + 1, i])) / 2))
                    # if df.loc[j, i] == '':
                    if len(str(df.loc[j, i])) == 0:
                        df.loc[j, i] = str(int((int(df.loc[j - 1, i]) + int(df.loc[j + 1, i])) / 2))

                df[i] = df[i].astype(str).str.pad(width=2, side='left', fillchar='0')

        df = df.set_index([pd.RangeIndex(len(df))])

        # df['Hour_mod'] = df['HOUR'].copy()
        if 'hourly' in self.frequency or 'timestep' in self.frequency:
            df['HOUR'] = (pd.to_numeric(df['HOUR']) - 1).astype(str).str.pad(width=2, side='left', fillchar='0')
        # df['Hour_mod'] = df['Hour_mod'].str.replace('.0', '').str.pad(width=2, side='left', fillchar='0')
        # df['HOUR'] = df['Hour_mod']

        # todo test timestep
        if 'monthly' in self.frequency:
            df['MONTH'] = df['MONTH'].astype(str)
            # df['Date/Time'] = df['MONTH']
        if 'daily' in self.frequency:
            df[['DAY', 'MONTH']] = df[['DAY', 'MONTH']].astype(str)
            # df['Date/Time'] = df[['DAY', 'MONTH']].agg('/'.join, axis=1)
        if 'hourly' in self.frequency:
            df[['DAY', 'MONTH', 'HOUR']] = df[['DAY', 'MONTH', 'HOUR']].astype(str)
            # df['Date/Time'] = df[['DAY', 'MONTH']].agg('/'.join, axis=1) + ' ' + df['HOUR'] + ':00'
        # if 'timestep' in self.frequency:
        #     df[['DAY', 'MONTH', 'HOUR', 'MINUTE']] = df[['DAY', 'MONTH', 'HOUR', 'MINUTE']].astype(str)
        #     df['Date/Time'] = (df[['DAY', 'MONTH']].agg('/'.join, axis=1) +
        #                             ' ' +
        #                             df[['HOUR', 'MINUTE']].agg(':'.join, axis=1))

        df = df.set_index([pd.RangeIndex(len(df))])

        # Step: managing EPW names if requested
        # if manage_epw_names:
        #     rcpdict = {
        #         'Present': ['Presente', 'Actual', 'Present', 'Current'],
        #         'RCP2.6': ['RCP2.6', 'RCP26'],
        #         'RCP4.5': ['RCP4.5', 'RCP45'],
        #         'RCP6.0': ['RCP6.0', 'RCP60'],
        #         'RCP8.5': ['RCP8.5', 'RCP85']
        #     }
        #
        #     rcp = []
        #     for i in rcpdict:
        #         for j in range(len(rcpdict[i])):
        #             rcp.append(rcpdict[i][j])
        #
        #     rcp_present = []
        #     for i in rcpdict['Present']:
        #         rcp_present.append(i)
        #
        #     df['EPW_mod'] = df['EPW'].str.split('_')
        #
        #     for i in range(len(df['EPW_mod'])):
        #         for j in df.loc[i, 'EPW_mod']:
        #             if len(j) == 2:
        #                 df.loc[i, 'EPW_CountryCode'] = j
        #             else:
        #                 df.loc[i, 'EPW_CountryCode'] = np.nan
        #
        #             for k in rcpdict:
        #                 for m in range(len(rcpdict[k])):
        #                     if j in rcpdict[k][m]:
        #                         df.loc[i, 'EPW_Scenario'] = k
        #                     else:
        #                         df.loc[i, 'EPW_Scenario'] = np.nan
        #
        #         df.loc[i, 'EPW_Year'] = np.nan
        #
        #
        # if manage_epw_names:
        #     for i in range(len(df['EPW_mod'])):
        #         for j in df.loc[i, 'EPW_mod']:
        #             if j in rcp_present:
        #                 df.loc[i, 'EPW_Year'] = 'Present'
        #             elif j in rcp:
        #                 continue
        #             elif j.isnumeric():
        #                 df.loc[i, 'EPW_Year'] = int(j)
        #             elif len(j) == 2:
        #                 continue
        #             else:
        #                 df.loc[i, 'EPW_City_or_subcountry'] = j.capitalize()
        #
        #     df = df.drop(['EPW_mod'], axis=1)

        # Step: re-ordering the columns
        # cols = df.columns.tolist()
        #
        # if self.frequency == 'runperiod':
        #     # this 1 is Source
        #     freq_extension = 1
        # else:
        #     freq_extension = 1 + len(frequency_dict[self.frequency])
        #
        # if split_epw_names:
        #     epw_extension = 5
        # else:
        #     epw_extension = 0
        #
        # if self.frequency == 'runperiod':
        #     adj_extension = -3
        # if self.frequency == 'monthly':
        #     adj_extension = -4
        # if self.frequency == 'daily':
        #     adj_extension = -5
        # if self.frequency == 'hourly':
        #     adj_extension = -6
        #
        # # if source_frequency == 'daily':
        # #     adj_source_freq = 5
        # # else:
        # #     adj_source_freq = 0
        #
        # # the 2 is for Date/Time and MONTH/DAY
        # temp_num = -(len(fixed_columns) + 2 + freq_extension + epw_extension + adj_extension)
        # cols = cols[temp_num:] + cols[:temp_num]
        # # cols = cols[5:] + cols[:5]
        # df = df[cols]

        # num_cols = df._get_numeric_data().columns.to_list()
        # num_cols.remove('count')
        # num_cols = sorted(num_cols)

        cols_model = ['SOURCE'] + [i.upper() for i in fixed_columns] + ['COUNT']

        cols_date = aggregation_list_first.copy()
        cols_date = [i.upper() for i in cols_date]
        cols_date.remove('SOURCE')

        if split_epw_names:
            cols_cat = cols_model + cols_epw_base + cols_epw_ext + cols_date
        else:
            cols_cat = cols_model + cols_date

        cols_num = [i for i in df.columns if i not in cols_cat]
        # cols_num = cols_num[1:] + cols_num[:1]

        df = df[cols_cat + cols_num]

        # Step: scanning data structure
        # temp_df_datastr = df.copy()
        # temp_df_datastr = temp_df_datastr[fixed_columns]
        # mindex = pd.MultiIndex.from_frame(temp_df_datast)

        # data_structure_dict = {}
        # temp_df_datastr = df.copy()
        # for i in list(dict.fromkeys(df['Model'])):
        #     temp_dict =
        #     temp_df_datastr = temp_df_datastr[temp_df_datastr['Model'].str.isin([i])]
        #     for j in list(dict.fromkeys(temp_df_datastr['ComfStand'])):

        # if split_epw_names:
        #     df = df[cols_model+cols_epw_base+cols_epw_ext+cols_date+num_cols]
        # else:
        #     df = df[cols_model+cols_date+num_cols]

        df = df.set_index([pd.RangeIndex(len(df))])

        self.rename_cols = rename_cols

        if rename_cols:
            renaming_criteria_bz = {
                'EMS:Comfortable Hours_No Applicability': 'Comfortable Hours_No Applicability (h)',
                'EMS:Comfortable Hours_Applicability': 'Comfortable Hours_Applicability (h)',
                'EMS:Discomfortable Applicable Hot Hours': 'Discomfortable Applicable Hot Hours (h)',
                'EMS:Discomfortable Applicable Cold Hours': 'Discomfortable Applicable Cold Hours (h)',
                'EMS:Discomfortable Non Applicable Hot Hours': 'Discomfortable Non Applicable Hot Hours (h)',
                'EMS:Discomfortable Non Applicable Cold Hours': 'Discomfortable Non Applicable Cold Hours (h)',
                'Zone Air Volume': 'Zone Air Volume (m3)',
                'Zone Floor Area': 'Zone Floor Area (m2)',
                'EMS:Ventilation Hours': 'Ventilation Hours (h)',
                f'AFN Zone Infiltration Volume [m3]({SFdict[source_frequency]})': 'AFN Zone Infiltration Volume (m3)',
                f'AFN Zone Infiltration Air Change Rate [ach]({SFdict[source_frequency]})': 'AFN Zone Infiltration Air Change Rate (ach)',
                f'AFN Zone Ventilation Volume [m3]({SFdict[source_frequency]})': 'AFN Zone Ventilation Volume (m3)',
                f'AFN Zone Ventilation Air Change Rate [ach]({SFdict[source_frequency]})': 'AFN Zone Ventilation Air Change Rate (ach)',
                # f'Zone Thermostat Operative Temperature [C]({SFdict[source_frequency]})': 'Zone Thermostat Operative Temperature (°C)',
                f'Zone Operative Temperature [C]({SFdict[source_frequency]})': 'Zone Operative Temperature (°C)',
                'Zone Operative Temperature': 'Zone Operative Temperature (°C)',
                f'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature [C]({SFdict[source_frequency]})':
                    'EN16798-1 Running mean outdoor temperature (°C)',
                f'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature [C]({SFdict[source_frequency]})':
                    'ASHRAE 55 Running mean outdoor temperature (°C)',
                'AHST_Sch': 'AHST_Sch',
                'ACST_Sch': 'ACST_Sch',
                'VRF Heat Pump Cooling Electricity Energy': 'Cooling Energy Consumption',
                'VRF Heat Pump Heating Electricity Energy': 'Heating Energy Consumption',
                'Heating Coil Heating Rate': 'Heating Energy Demand',
                'Cooling Coil Total Cooling Rate': 'Cooling Energy Demand',
                'Zone Thermal Comfort Fanger Model PMV': 'PMV',
                'Zone Thermal Comfort Fanger Model PPD': 'PPD (%)'
            }

            renaming_criteria = {
                # 'Date/Time',
                f'Environment:Site Outdoor Air Drybulb Temperature [C]({SFdict[source_frequency]})':
                    'Site Outdoor Air Drybulb Temperature (°C)',
                f'Environment:Site Wind Speed [m/s]({SFdict[source_frequency]})': 'Site Wind Speed (m/s)',
                f'Environment:Site Outdoor Air Relative Humidity [%]({SFdict[source_frequency]})':
                    'Site Outdoor Air Relative Humidity (%)',
                f'EMS:Comfort Temperature [C]({SFdict[source_frequency]})': 'Comfort Temperature (°C)',
                f'EMS:Adaptive Cooling Setpoint Temperature [C]({SFdict[source_frequency]})': 'Adaptive Cooling Setpoint Temperature (°C)',
                f'EMS:Adaptive Heating Setpoint Temperature [C]({SFdict[source_frequency]})': 'Adaptive Heating Setpoint Temperature (°C)',
                f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance [C]({SFdict[source_frequency]})':
                    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
                f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance [C]({SFdict[source_frequency]})':
                    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
                f'EMS:Ventilation Setpoint Temperature [C]({SFdict[source_frequency]})': 'Ventilation Setpoint Temperature (°C)',
                f'EMS:Minimum Outdoor Temperature for ventilation [C]({SFdict[source_frequency]})':
                    'Minimum Outdoor Temperature for ventilation (°C)',
                'Whole Building:Facility Total HVAC Electricity Demand Rate':
                    'Whole Building Facility Total HVAC Electricity Demand Rate',

            }

            all_cols_renamed = {}

            all_cols_renamed.update({'SOURCE': 'Source'})

            for i in fixed_columns_orig:
                all_cols_renamed.update({i.upper(): i})

            all_cols_renamed.update({'COUNT': 'Count'})

            for i in cols_date:
                all_cols_renamed.update({i.upper(): i.capitalize()})

            for col in df.columns:
                for crit in renaming_criteria_bz:
                    if '(summed)' not in col and '(mean)' not in col:
                        if crit.upper() in col.upper():
                            for block_zone in occupied_zone_list:
                                if block_zone.upper() in col.upper():
                                    if energy_units.upper() in col.upper():
                                        temp = {col: block_zone + '_' + renaming_criteria_bz[crit] + ' ' + energy_units}
                                        all_cols_renamed.update(temp)
                                    else:
                                        temp = {col: block_zone + '_' + renaming_criteria_bz[crit]}
                                        all_cols_renamed.update(temp)

            for col in df.columns:
                for crit in renaming_criteria:
                    if '(summed)'.upper() not in col and '(mean)' not in col:
                        if crit.upper() in col.upper():
                            if energy_units.upper() in col.upper():
                                temp = {col: renaming_criteria[crit] + ' ' + energy_units}
                                all_cols_renamed.update(temp)
                            else:
                                temp = {col: renaming_criteria[crit]}
                                all_cols_renamed.update(temp)

            renaming_criteria_block = {
                'VRF Heat Pump Cooling Electricity Energy': 'Cooling Energy Consumption',
                'VRF Heat Pump Heating Electricity Energy': 'Heating Energy Consumption',
                'Heating Coil Heating Rate': 'Heating Energy Demand',
                'Cooling Coil Total Cooling Rate': 'Cooling Energy Demand'
            }

            for col in df.columns:
                for crit in renaming_criteria_block:
                    for block in block_list:
                        if block.upper() + '_Total_'.upper() + crit.upper() in col.upper():
                            if '(summed)' in col:
                                temp = {col: f'{block}_Total_{renaming_criteria_block[crit]} {energy_units} (summed)'}
                                all_cols_renamed.update(temp)
                            elif '(mean)' in col:
                                temp = {col: f'{block}_Total_{renaming_criteria_block[crit]} {energy_units} (mean)'}
                                all_cols_renamed.update(temp)
                    if 'Building_Total_'.upper() + crit.upper() in col.upper():
                        if '(summed)' in col:
                            temp = {col: f'Building_Total_{renaming_criteria_block[crit]} {energy_units} (summed)'}
                            all_cols_renamed.update(temp)
                        if '(mean)' in col:
                            temp = {col: f'Building_Total_{renaming_criteria_block[crit]} {energy_units} (mean)'}
                            all_cols_renamed.update(temp)

            df = df.rename(columns=all_cols_renamed)

        # dropping Operative temperature columns which are 0 for all rows or nan
        # optemp_df = df.filter(regex='Operative Temperature')
        # optemp_to_drop = []
        # optemp_to_drop.extend(optemp_df.columns[optemp_df.isna().any()].tolist())
        # for i in optemp_df.columns:
        #     if (optemp_df[i] == 0).all():
        #         optemp_to_drop.append(i)
        # df = df.drop(optemp_to_drop, axis=1)

        available_vars_to_gather = [
            'Model',
            'ComfStand',
            'CAT',
            'ComfMod',
            'HVACmode',
            'VentCtrl',
            'VSToffset',
            'MinOToffset',
            'MaxWindSpeed',
            'ASTtol',
            'NameSuffix',
            'EPW'
        ]

        if split_epw_names:
            available_vars_to_gather.extend([
                'EPW_Country_name',
                'EPW_City_or_subcountry',
                'EPW_Scenario-Year',
                'EPW_Scenario',
                'EPW_Year'
            ])
            available_vars_to_gather.remove('EPW')

        # todo Step: remove PMV-PPD columns if the column only have null values

        # df = df.round(decimals=2)

        cols_to_clean = []
        cols_for_multiindex = []
        for i in available_vars_to_gather:
            try:
                if (df[i][0] == df[i]).all():
                    cols_to_clean.append(i)
                elif len(list(set([j for j in df[i]]))) == 2 and (('_X' in list(set([j for j in df[i]]))[0]) or ('_X' in list(set([j for j in df[i]]))[1])):
                    cols_to_clean.append(i)
                else:
                    cols_for_multiindex.append(i)
            except KeyError:
                if (df[i][0] == df[i]).all():
                    cols_to_clean.append(i)
                elif len(list(set([j for j in df[i]]))) == 2 and (('_X' in list(set([j for j in df[i]]))[0]) or ('_X' in list(set([j for j in df[i]]))[1])):
                    cols_to_clean.append(i)
                else:
                    cols_for_multiindex.append(i)

        checkpoint += 1

        self.hvac_zone_list = hvac_zone_list
        self.occupied_zone_list = occupied_zone_list
        self.available_vars_to_gather = available_vars_to_gather
        self.block_list = block_list
        self.df = df
        self.df_backup = df

        self.frequency = frequency

        self.cols_to_clean = cols_to_clean
        self.cols_for_multiindex = cols_for_multiindex

        # df.to_excel('checkpoint_04.xlsx')

        # todo pop up when process ends; by defalt True

    def gather_vars_query(
            self,
            vars_to_gather: list = None
            ):
        """
        Used to inform the user of the variables suitable to be analysed and the available
        options from a certain gathered variables

        :param vars_to_gather: A list of variables.
        :type vars_to_gather: list
        """
        temp_df = self.df.copy()
        temp_df['col_to_pivot'] = temp_df[vars_to_gather].agg('['.join, axis=1)
        vars_to_gather_values = list(dict.fromkeys(temp_df['col_to_pivot']))
        print('The categorical columns which have different values and those values are:')
        # print(*self.cols_for_multiindex, sep='\n')
        for i in self.cols_for_multiindex:
            print(f'{i}: {list(dict.fromkeys(temp_df[i]))}')
        print('The available options resulting from the data entered in vars_to_gather would be: ')
        print(*vars_to_gather_values, sep='\n')
        del temp_df

    def format_table(self,
                     type_of_table: str = 'all',
                     custom_cols: list = None,
                     # custom_rows: list = None,
                     # split_epw_names: bool = False
                     ):
        """
        It filters the columns.

        :param type_of_table: To get previously set out tables. Can be 'energy demand' or 'comfort hours'.
        :param custom_cols: A list of strings.
        The strings will be used as a filter, and the columns that match will be selected.
        """
        if custom_cols is None:
            custom_cols = []
        # if custom_rows is None:
        #     custom_rows = []

        self.df = self.df_backup

        # self.split_epw_names = split_epw_names

        self.indexcols = [
            'Date/time',
            'Model',
            'ComfStand',
            'CAT',
            'ComfMod',
            'HVACmode',
            'VentCtrl',
            'VSToffset',
            'MinOToffset',
            'MaxWindSpeed',
            'ASTtol',
            'NameSuffix',
            'EPW',
            'Source',
            # 'col_to_pivot'
        ]
        # todo to be updated with source frequency
        if 'runperiod' in self.frequency:
            self.indexcols.remove('Date/time')
        if 'monthly' in self.frequency:
            self.indexcols.append('Month')
        if 'daily' in self.frequency:
            self.indexcols.extend(['Month', 'Day'])
        if 'hourly' in self.frequency:
            self.indexcols.extend(['Month', 'Day', 'Hour'])
        if 'timestep' in self.frequency:
            self.indexcols.extend(['Month', 'Day', 'Hour', 'Minute'])
        if self.split_epw_names:
            self.indexcols.extend([
                'EPW_Country_name',
                'EPW_City_or_subcountry',
                'EPW_Scenario-Year',
                'EPW_Scenario',
                'EPW_Year'
            ])

        self.val_cols = []
        if type_of_table == 'custom':
            for custom_col in custom_cols:
                for col in self.df.columns:
                    if custom_col.lower() in col.lower():
                        self.val_cols.append(col)
        elif type_of_table == 'energy demand':
            if self.rename_cols:
                self.val_cols = [col for col in self.df.columns if
                                 'Total Energy Demand' in col or
                                 'Cooling Energy Demand' in col or
                                 'Heating Energy Demand' in col
                                 ]
            else:
                self.val_cols = [col for col in self.df.columns if
                                 'Cooling Coil Total Cooling Rate' in col or
                                 'Heating Coil Heating Rate' in col or
                                 'Total Energy Demand' in col]
        elif type_of_table == 'comfort hours':
            self.val_cols = [col for col in self.df.columns if 'Comfortable Hours_No Applicability' in col
                             or 'Comfortable Hours_Applicability' in col
                             or 'Discomfortable Applicable Hot Hours' in col
                             or 'Discomfortable Applicable Cold Hours' in col
                             or 'Discomfortable Non Applicable Hot Hours' in col
                             or 'Discomfortable Non Applicable Cold Hours' in col
                             or 'Ventilation Hours' in col]
        elif type_of_table == 'temperature':
            self.val_cols = [
                col for col in self.df.columns
                if 'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)' in col
                   or 'Adaptive Heating Setpoint Temperature_No Tolerance (°C)' in col
                   or 'Building_Total_Zone Operative Temperature (°C) (mean)' in col
                   or 'Building_Total_Cooling Energy Demand' in col
                   or 'Building_Total_Heating Energy Demand' in col
            ]
            RMOT_col = [
                col for col in self.df.columns
                if 'Running mean outdoor temperature' in col
            ][0]
            self.val_cols.extend([RMOT_col])
        # elif type_of_table == 'all':
        #     # self.val_cols = list(set(self.df.columns) - set(self.indexcols))
        #     self.val_cols = []
        #     for col in self.df.columns:
        #         if col not in self.indexcols:
        #             self.val_cols.append(col)

        if type_of_table == 'custom':
            if len(self.val_cols) == 0:
                raise ValueError('You have not selected any column to make the custom table. '
                                 'Please check the columns you want to select. '
                                 'To see the full list of columns, enter print("name of class instance".df.columns)')

        if not (type_of_table == 'all'):
            self.df = self.df[self.indexcols + self.val_cols]

        checkpoint = 0

    def custom_order(
            self,
            ordered_list: list = None,
            column_to_order: str = None,
    ):
        """
        Used to order the string values of a column in a custom order.

        :param ordered_list: A list os strings.
            Used to order the string values of a column in a custom order.
        :type ordered_list: list
        :param column_to_order: A string.
            It should be the column whose string values should be ordered.
        :type column_to_order: str
        """
        from pandas.api.types import CategoricalDtype

        if ordered_list is None:
            ordered_list = []

        self.ordered_list = ordered_list

        custom_order = CategoricalDtype(
            ordered_list,
            ordered=True
        )

        self.df[column_to_order] = self.df[column_to_order].astype(custom_order)

    # def hvac_zone_list(self):
    #     return self.hvac_zone_list
    #
    # def occupied_zone_list(self):
    #     return self.occupied_zone_list
    #
    # def block_list(self):
    #     return block_list()

    def wrangled_table(
            self,
            reshaping: str = None,
            vars_to_gather: list = None,
            baseline: str = None,
            comparison_mode: list = ['others compared to baseline'],
            comparison_cols: list = ['absolute', 'relative'],
            check_index_and_cols: bool = False,
            vars_to_keep: list = None,
            rename_dict: dict = None,
            transpose: bool = False,
            excel_filename: str = None,
            ):
        """
        Creates a table based on the arguments.

        :param reshaping: A string.
            Can be 'pivot', 'unstack' or 'multiindex', to perform these actions.
        :type reshaping: str
        :param vars_to_gather: A list of the variables to be transposed from rows to columns.
        :type vars_to_gather: list
        :param baseline: The already transposed column you want to use as a baseline for comparisons.
            If omitted, you will be asked which one to use.
        :type baseline: str
        :param comparison_mode: A list of strings.
            Can be 'others compared to baseline' and/or 'baseline compared to others'.
            Used to customise the comparison of variables.
        :type comparison_mode: list
        :param comparison_cols: A list of strings.
            'absolute' to get the difference or 'relative' to get the percentage of reduction.
        :type comparison_cols: list
        :param check_index_and_cols: A boolean. True to check index and cols, False to skip.
        :type check_index_and_cols: bool
        :param vars_to_keep: A list of strings.
            To remove all variables from the multiindex except those to be kept.
        :type vars_to_keep: list
        :param excel_filename: A string.
            If entered, the wrangled_df will be exported to excel with that string as name.
        :type excel_filename: str
        :param transpose: True to transpose the dataframe
        :type transpose: bool
        :param rename_dict: Renames all data in the dataframe based on the format
            {'old_string': 'new_string'}
        :type rename_dict: dict
        """
        if vars_to_gather is None:
            vars_to_gather = []
        if comparison_cols is None:
            comparison_cols = ['absolute', 'relative']
        if vars_to_keep is None:
            vars_to_keep = []

        import numpy as np
        import pandas as pd

        # todo what if no variable is entered in vars_to_gather? accim should show the variables that change, and therefore could be analysed

        # todo revise stack returns a dataframe suitable for seaborn (one column for values, all others for categoricals)

        # if vars_to_gather is None:


        if reshaping == 'pivot' or reshaping == 'unstack':
            self.enter_vars_to_gather(vars_to_gather)

        checkpoint = 0

        wrangled_df = self.df.copy()

        if reshaping == 'pivot':

            self.df['col_to_pivot'] = 'temp'
            self.indexcols.append('col_to_pivot')

            wrangled_df_pivoted = wrangled_df.copy()
            del wrangled_df

            if 'Month' in wrangled_df_pivoted.columns:
                wrangled_df_pivoted['col_to_pivot'] = (wrangled_df_pivoted[vars_to_gather].agg('['.join, axis=1) + '_' +
                                                       wrangled_df_pivoted['Month'].astype(str) +
                                                       '[Month')
            else:
                wrangled_df_pivoted['col_to_pivot'] = wrangled_df_pivoted[vars_to_gather].agg('['.join, axis=1)

            self.df['col_to_pivot'] = wrangled_df_pivoted['col_to_pivot']

            checkpoint += 1

            #todo testing from here

            # todo when it is pivotted, variables not specified in vars_to_gather are summed
            # wrangled_df_pivoted = wrangled_df_pivoted.drop(['Source'], axis=1)
            # try:
            #     self.indexcols.remove('Source')
            # except ValueError:
            #     print('Since this is not the first time you run wrangled_table, '
            #           '"Source" is trying to be removed from indexcols, but has been previously removed.')
            # if self.split_epw_names:
            #     wrangled_df_pivoted = wrangled_df_pivoted.drop(['EPW', 'EPW_Scenario-Year'], axis=1)
            #     try:
            #         self.indexcols.remove('EPW')
            #         self.indexcols.remove('EPW_Scenario-Year')
            #     except ValueError:
            #         print('Since this is not the first time you run wrangled_table, '
            #               '"EPW" and "EPW_Scenario-Year" are trying to be removed from indexcols, but has been previously removed.')
            #
            #
            # cols_to_clean = []
            # cols_for_multiindex = []
            # for i in self.indexcols:
            #     try:
            #         if (wrangled_df_pivoted[i][0] == wrangled_df_pivoted[i]).all():
            #             cols_to_clean.append(i)
            #         else:
            #             cols_for_multiindex.append(i)
            #     except KeyError:
            #         wrangled_df_pivoted = wrangled_df_pivoted.set_index([pd.RangeIndex(len(wrangled_df_pivoted))])
            #         if (wrangled_df_pivoted[i][0] == wrangled_df_pivoted[i]).all():
            #             cols_to_clean.append(i)
            #         else:
            #             cols_for_multiindex.append(i)
            #
            # checkpoint += 1
            #
            # if check_index_and_cols:
            #     print('The multiindex should contain only the variables you want to compare. '
            #           'The variables and values you are going to use for the multiindex, except those already specified in vars_to_gather argument, are:')
            #     for i in cols_for_multiindex:
            #         if all([i not in j for j in vars_to_gather]):
            #             print(f'{i}: {list(dict.fromkeys(wrangled_df_pivoted[i]))}')
            #     proceed = input('If some variable is not relevant for the comparison, it should be removed. '
            #                     'Do you want to remove any? [y/n]: ')
            #     if 'y' in proceed:
            #         if len(vars_to_keep) > 0:
            #             print('The variables to keep you specified in the arguments will be overriden.')
            #         vars_to_keep = list(str(num) for num in input("Enter the variables you want to keep separated by semicolon: ").split(';'))
            #
            # if len(vars_to_keep) > 0:
            #     add_vars_to_remove = list(set(cols_for_multiindex) - set(vars_to_gather) - set(vars_to_keep))
            #     for i in add_vars_to_remove:
            #         cols_to_clean.append(i)
            #         cols_for_multiindex.remove(i)
            #
            # wrangled_df_pivoted = wrangled_df_pivoted.drop(cols_to_clean, axis=1)
            #
            # cols_for_values = list(set(wrangled_df_pivoted.columns) - set(cols_for_multiindex))
            #
            # checkpoint += 1
            #
            # wrangled_df_pivoted = wrangled_df_pivoted.pivot_table(
            #     index=cols_for_multiindex,
            #     columns='col_to_pivot',
            #     values=self.val_cols,
            #     aggfunc=np.sum,
            #     fill_value=0
            # )
            #
            # checkpoint += 1
            
            

            #todo testing until here


            wrangled_df_pivoted = wrangled_df_pivoted.pivot_table(
                index=self.indexcols.remove('col_to_pivot'),
                columns='col_to_pivot',
                values=self.val_cols,
                # if aggfunc is omitted, performs the average
                aggfunc=np.sum,
                fill_value=0)

            checkpoint += 1

            var_to_gather_values = list(dict.fromkeys(self.df['col_to_pivot']))

            if baseline not in var_to_gather_values:
                print(f'"{baseline}" is not in list of categories you want to compare. The list is:')
                print(var_to_gather_values)
                baseline = input('Please choose one from the list above (it is case-sensitive) for baseline:')

            other_than_baseline = list(set(var_to_gather_values) - set([baseline]))

            self.df = self.df.drop('col_to_pivot', axis=1)

            checkpoint += 1

            # summing monthly values to make runperiod

            if 'Month' in self.df.columns:
                for i in var_to_gather_values:
                    wrangled_df_pivoted[f'{i}_Runperiod_Total'] = wrangled_df_pivoted[
                        [j for j in wrangled_df_pivoted.columns
                         if i in j]
                    ].sum(axis=1)

                for j in other_than_baseline:
                    for i in list(dict.fromkeys(self.df['Month'])):
                        if any('relative' in k for k in comparison_cols):
                            wrangled_df_pivoted[f'1-({j}/{baseline})_{i}_Month'] = (
                                    1 -
                                    (wrangled_df_pivoted[j + f'_{i}_Month'] / wrangled_df_pivoted[baseline + f'_{i}_Month'])
                            )
                        if any('absolute' in k for k in comparison_cols):
                            wrangled_df_pivoted[f'{baseline}-{j}_{i}_Month'] = (
                                    wrangled_df_pivoted[baseline + f'_{i}_Month'] - wrangled_df_pivoted[j + f'_{i}_Month']
                            )
                    if any('relative' in k for k in comparison_cols):
                        wrangled_df_pivoted[f'1-({j}/{baseline})_Runperiod_Total'] = (
                                1 -
                                (wrangled_df_pivoted[j + '_Runperiod_Total'] / wrangled_df_pivoted[baseline + '_Runperiod_Total'])
                        )
                    if any('absolute' in k for k in comparison_cols):
                        wrangled_df_pivoted[f'{baseline} - {j}_Runperiod_Total'] = (
                                wrangled_df_pivoted[baseline + '_Runperiod_Total'] - wrangled_df_pivoted[j + '_Runperiod_Total']
                        )
            else:
                for j in other_than_baseline:
                    # if comparison_mode == 'others compared to baseline':
                    if any(['others compared to baseline' in i for i in comparison_mode]):
                        if any('relative' in k for k in comparison_cols):
                            wrangled_df_pivoted[f'1-({j}/{baseline})'] = (
                                    1 -
                                    (wrangled_df_pivoted[j] / wrangled_df_pivoted[baseline])
                            )
                        if any('absolute' in k for k in comparison_cols):
                            wrangled_df_pivoted[f'{baseline} - {j}'] = (
                                    wrangled_df_pivoted[baseline] - wrangled_df_pivoted[j]
                            )
                    if any(['baseline compared to others' in i for i in comparison_mode]):
                        if any('relative' in k for k in comparison_cols):
                            wrangled_df_pivoted[f'1-({baseline}/{j})'] = (
                                    1 -
                                    (wrangled_df_pivoted[baseline] / wrangled_df_pivoted[j])
                            )
                        if any('absolute' in k for k in comparison_cols):
                            wrangled_df_pivoted[f'{j} - {baseline}'] = (
                                    wrangled_df_pivoted[j] - wrangled_df_pivoted[baseline]
                            )

            wrangled_df_pivoted = wrangled_df_pivoted.round(decimals=2)

            if rename_dict is not None:
                wrangled_df_pivoted = wrangled_df_pivoted.replace(
                    [i for i in rename_dict],
                    [rename_dict[i] for i in rename_dict]
                )
                for i in rename_dict:
                    wrangled_df_pivoted.rename(columns=lambda s: s.replace(i, rename_dict[i]), inplace=True)
                    wrangled_df_pivoted.rename(index=lambda s: s.replace(i, rename_dict[i]), inplace=True)

            if transpose:
                wrangled_df_pivoted = wrangled_df_pivoted.transpose()

            if excel_filename is not None:
                wrangled_df_pivoted.to_excel(f'{excel_filename}.xlsx')

            self.wrangled_df_pivoted = wrangled_df_pivoted

            checkpoint += 1

        elif reshaping == 'unstack' or reshaping == 'stack' or reshaping == 'multiindex':

            wrangled_df_unstacked_or_stacked = wrangled_df.copy()
            del wrangled_df

            # todo if argument vars_to_keep is not specified, vars_to_keep should be all remaining variables apart from those in vars_to_gather

            # Step: Getting rid of unnecessary columns
            wrangled_df_unstacked_or_stacked = wrangled_df_unstacked_or_stacked.drop(['Source'], axis=1)
            try:
                self.indexcols.remove('Source')
            except ValueError:
                print('Since this is not the first time you run wrangled_table, '
                      '"Source" is trying to be removed from indexcols, but has been previously removed.')
            if self.split_epw_names:
                wrangled_df_unstacked_or_stacked = wrangled_df_unstacked_or_stacked.drop(['EPW', 'EPW_Scenario-Year'], axis=1)
                try:
                    self.indexcols.remove('EPW')
                    self.indexcols.remove('EPW_Scenario-Year')
                except ValueError:
                    print('Since this is not the first time you run wrangled_table, '
                          '"EPW" and "EPW_Scenario-Year" are trying to be removed from indexcols, but has been previously removed.')
            # removing variables where values are all the same
            cols_to_clean = []
            cols_for_multiindex = []
            for i in self.indexcols:
                try:
                    if (wrangled_df_unstacked_or_stacked[i][0] == wrangled_df_unstacked_or_stacked[i]).all():
                        cols_to_clean.append(i)
                    elif len(list(set([j for j in wrangled_df_unstacked_or_stacked[i]]))) == 2 and (('_X' in list(set([j for j in wrangled_df_unstacked_or_stacked[i]]))[0]) or ('_X' in list(set([j for j in wrangled_df_unstacked_or_stacked[i]]))[1])):
                        cols_to_clean.append(i)
                    else:
                        cols_for_multiindex.append(i)
                except KeyError:
                    wrangled_df_unstacked_or_stacked = wrangled_df_unstacked_or_stacked.set_index([pd.RangeIndex(len(wrangled_df_unstacked_or_stacked))])
                    if (wrangled_df_unstacked_or_stacked[i][0] == wrangled_df_unstacked_or_stacked[i]).all():
                        cols_to_clean.append(i)
                    elif len(list(set([j for j in wrangled_df_unstacked_or_stacked[i]]))) == 2 and (('_X' in list(set([j for j in wrangled_df_unstacked_or_stacked[i]]))[0]) or ('_X' in list(set([j for j in wrangled_df_unstacked_or_stacked[i]]))[1])):
                        cols_to_clean.append(i)
                    else:
                        cols_for_multiindex.append(i)

            checkpoint += 1



            wrangled_df_unstacked_or_stacked = wrangled_df_unstacked_or_stacked.drop(cols_to_clean, axis=1)

            cols_for_values = list(set(wrangled_df_unstacked_or_stacked.columns) - set(cols_for_multiindex))


            # todo re-review the use of check_index_and_cols and vars_to_gather to avoid repeated rows when stacking
            if len(vars_to_keep) == 0:
                if check_index_and_cols:
                    print('The multiindex should contain only the variables you want to compare. '
                          'The variables and values you are going to use for the multiindex, except those already specified in vars_to_gather argument, are:')
                    for i in cols_for_multiindex:
                        if all([i not in j for j in vars_to_gather]):
                            print(f'{i}: {list(dict.fromkeys(wrangled_df_unstacked_or_stacked[i]))}')
                    proceed = input('If some variable is not relevant for the comparison, it should be removed. '
                                    'Do you want to remove any? [y/n]: ')
                    if 'y' in proceed:
                        if len(vars_to_keep) > 0:
                            print('The variables to keep you specified in the arguments will be overriden.')
                        vars_to_keep = list(str(num) for num in input("Enter the variables you want to keep separated by semicolon: ").split(';'))

            if len(vars_to_keep) > 0:
                add_vars_to_remove = list(set(cols_for_multiindex) - set(vars_to_gather) - set(vars_to_keep))
                for i in add_vars_to_remove:
                    cols_to_clean.append(i)
                    cols_for_multiindex.remove(i)
                wrangled_df_unstacked_or_stacked = wrangled_df_unstacked_or_stacked.drop(add_vars_to_remove, axis=1)

            wrangled_df_unstacked_or_stacked = wrangled_df_unstacked_or_stacked.set_index(cols_for_multiindex)

            checkpoint += 1

            if reshaping == 'unstack':
                wrangled_df_unstacked = wrangled_df_unstacked_or_stacked.copy()
                del wrangled_df_unstacked_or_stacked

                wrangled_df_unstacked = wrangled_df_unstacked.unstack(vars_to_gather)

                checkpoint +=1

                wrangled_df_unstacked.columns = ['['.join(col).strip('[') for col in wrangled_df_unstacked.columns.values]

                var_to_gather_values = [i.split('[', maxsplit=1)[1] for i in wrangled_df_unstacked.columns]
                var_to_gather_values = list(dict.fromkeys(var_to_gather_values))

                if baseline not in var_to_gather_values:
                    print(f'"{baseline}" is not in list of categories you want to compare. The list is:')
                    print(var_to_gather_values)
                    baseline = input('Please choose one from the list above (it is case-sensitive) for baseline:')

                other_than_baseline = [i.split('[', maxsplit=1)[1] for i in wrangled_df_unstacked.columns if baseline not in i]
                other_than_baseline = list(dict.fromkeys(other_than_baseline))

                # baseline_col = [col for col in wrangled_df_unstacked.columns if baseline in col][0]

                # in this case the months are located in rows, so no need to add months to columns
                for i in cols_for_values:
                    baseline_col = [col for col in wrangled_df_unstacked.columns if baseline in col and i in col][0]
                    for j in other_than_baseline:
                        for x in [col for col in wrangled_df_unstacked.columns if i in col and j in col]:
                            if any(['others compared to baseline' in i for i in comparison_mode]):
                                if any('relative' in k for k in comparison_cols):
                                    wrangled_df_unstacked[f'{i}[1-({j}/{baseline})'] = (
                                            1 -
                                            (wrangled_df_unstacked[x] / wrangled_df_unstacked[baseline_col])
                                    )
                                if any('absolute' in k for k in comparison_cols):
                                    wrangled_df_unstacked[f'{i}[{baseline} - {j}'] = (
                                            wrangled_df_unstacked[baseline_col] - wrangled_df_unstacked[x]
                                    )
                            if any(['baseline compared to others' in i for i in comparison_mode]):
                                if any('relative' in k for k in comparison_cols):
                                    wrangled_df_unstacked[f'{i}[1-({baseline}/{j})'] = (
                                            1 -
                                            (wrangled_df_unstacked[baseline_col] / wrangled_df_unstacked[x])
                                    )
                                if any('absolute' in k for k in comparison_cols):
                                    wrangled_df_unstacked[f'{i}[{j} - {baseline}'] = (
                                            wrangled_df_unstacked[x] - wrangled_df_unstacked[baseline_col]
                                    )

                ordered_columns = []
                for i in self.val_cols:
                    for j in wrangled_df_unstacked.columns:
                        if i in j:
                            ordered_columns.append(j)

                wrangled_df_unstacked = wrangled_df_unstacked.reindex(columns=ordered_columns)

                wrangled_df_unstacked.columns = pd.MultiIndex.from_arrays(
                    [
                        [x[0] for x in wrangled_df_unstacked.columns.get_level_values(0).str.split('[', n=1)],
                        [x[1] for x in wrangled_df_unstacked.columns.get_level_values(0).str.split('[', n=1)]
                    ]
                )

                wrangled_df_unstacked = wrangled_df_unstacked.round(decimals=2)

                if rename_dict is not None:
                    wrangled_df_unstacked = wrangled_df_unstacked.replace(
                        [i for i in rename_dict],
                        [rename_dict[i] for i in rename_dict]
                    )
                    for i in rename_dict:
                        wrangled_df_unstacked.rename(columns=lambda s: s.replace(i, rename_dict[i]), inplace=True)
                        wrangled_df_unstacked.rename(index=lambda s: s.replace(i, rename_dict[i]), inplace=True)

                if transpose:
                    wrangled_df_unstacked = wrangled_df_unstacked.transpose()

                if excel_filename is not None:
                    wrangled_df_unstacked.to_excel(f'{excel_filename}.xlsx')

                self.wrangled_df_unstacked = wrangled_df_unstacked

            elif reshaping == 'stack':
                wrangled_df_stacked = wrangled_df_unstacked_or_stacked.copy()
                del wrangled_df_unstacked_or_stacked
                wrangled_df_stacked = wrangled_df_stacked.stack()
                wrangled_df_stacked = wrangled_df_stacked.to_frame()
                wrangled_df_stacked.columns = ['values']
                cols_for_multiindex.append('Variable')
                wrangled_df_stacked.index = wrangled_df_stacked.index.set_names(cols_for_multiindex)
                cols_for_multiindex.remove('Variable')

                wrangled_df_stacked = wrangled_df_stacked.round(decimals=2)

                if rename_dict is not None:
                    wrangled_df_stacked = wrangled_df_stacked.replace(
                        [i for i in rename_dict],
                        [rename_dict[i] for i in rename_dict]
                    )
                    for i in rename_dict:
                        wrangled_df_stacked.rename(columns=lambda s: s.replace(i, rename_dict[i]), inplace=True)
                        wrangled_df_stacked.rename(index=lambda s: s.replace(i, rename_dict[i]), inplace=True)

                if transpose:
                    wrangled_df_stacked = wrangled_df_stacked.transpose()

                if excel_filename is not None:
                    wrangled_df_stacked.to_excel(f'{excel_filename}.xlsx')

                self.wrangled_df_stacked = wrangled_df_stacked

            elif reshaping == 'multiindex':
                wrangled_df_multiindex = wrangled_df_unstacked_or_stacked.copy()
                del wrangled_df_unstacked_or_stacked

                if rename_dict is not None:
                    wrangled_df_multiindex = wrangled_df_multiindex.replace(
                        [i for i in rename_dict],
                        [rename_dict[i] for i in rename_dict]
                    )
                    for i in rename_dict:
                        wrangled_df_multiindex.rename(columns=lambda s: s.replace(i, rename_dict[i]), inplace=True)
                        wrangled_df_multiindex.rename(index=lambda s: s.replace(i, rename_dict[i]), inplace=True)

                if transpose:
                    wrangled_df_multiindex = wrangled_df_multiindex.transpose()

                if excel_filename is not None:
                    wrangled_df_multiindex.to_excel(f'{excel_filename}.xlsx')

                self.wrangled_df_multiindex = wrangled_df_multiindex

                print('No reshaping method has been applied, only multiindexing.')

    def enter_vars_to_gather(
            self,
            vars_to_gather=None
    ):
        """
        Function used by accim to gather variables to be combined in columns.

        :param vars_to_gather: The list of strings containing the variables.
        :type vars_to_gather: list
        """
        if vars_to_gather is None:
            vars_to_gather = []

        while (not (all(elem in self.available_vars_to_gather for elem in vars_to_gather))
               or len(vars_to_gather) != len(set(vars_to_gather))):
            print('Some of the variables to be gathered are not available or are duplicated:')
            print(vars_to_gather)
            print('The list of available variables to be gathered is:')
            print(self.available_vars_to_gather)
            vars_to_gather = (list(str(var)
                                   for var
                                   in input("Enter the variables to be gathered separated by semicolon: ").split(';')))
        return vars_to_gather


    def generate_fig_data(
            self,
            vars_to_gather_cols: list = None,
            vars_to_gather_rows: list = None,
            detailed_cols: list = None,
            detailed_rows: list = None,
            custom_cols_order: list = None,
            custom_rows_order: list = None,
            data_on_y_axis_baseline_plot: list = None,
            # adap_vs_stat_data_y_sec=None,
            baseline: str = None,
            colorlist_baseline_plot_data: list = None,
            data_on_x_axis: str = None,
            data_on_y_main_axis: list = None,
            data_on_y_sec_axis: list = None,
            colorlist_y_main_axis: list = None,
            colorlist_y_sec_axis: list = None,
            best_fit_deg_y_main_axis: list = None,
            best_fit_deg_y_sec_axis: list = None,
            best_fit_deg: list = None,
            rows_renaming_dict: dict = None,
            cols_renaming_dict: dict = None,
            ):
        """
        Generates list of data to be plotted.

        :param vars_to_gather_cols: A list of strings. The list should be the variables you want to show in subplot columns.
        :param vars_to_gather_rows: A list of strings. The list should be the variables you want to show in subplot rows.
        :param detailed_cols: A list of strings. The list should be the specific data you want to show in subplots columns. Used to filter.
        :param detailed_rows: A list of strings. The list should be the specific data you want to show in subplots rows. Used to filter.
        :param custom_cols_order: A list of strings. The list should be the specific order for the items shown in subplot columns.
        :param custom_rows_order: A list of strings. The list should be the specific order for the items shown in subplot rows.
        :param data_on_y_axis_baseline_plot: A list of strings. Used to select the data you want to show in the graph. Should be a list of the column names you want to plot in each subplot.
        :param baseline: A string, used only in data_on_y_axis_baseline_plot. The baseline should be one of the combinations in vars_to_gather_cols. It will be plotted in x-axis, while the reference combination for comparison in y-axis.
        :param colorlist_baseline_plot_data: A list of strings. Should be the colors using the matplotlib color notation for the columns entered in data_on_y_axis_baseline_plot in the same order.
        :param data_on_x_axis: A string. The column name you want to plot in the x-axis.
        :param data_on_y_main_axis: A list with nested lists and strings. Used to select the data you want to show in the scatter plot main y-axis. It needs to follow this structure:
            [['name_on_y_main_axis', [list of column names you want to plot]]
        :param data_on_y_sec_axis: A list with nested lists and strings. Used to select the data you want to show in the scatter plot secondary y-axis. It needs to follow this structure:
            [['name_on_1st_y_sec_axis', [list of column names you want to plot], ['name_on_2nd_y_sec_axis', [list of column names you want to plot], etc]
        :param colorlist_y_main_axis: A list with nested lists and strings. It should follow the same structure as data_on_y_main_axis, but replacing the column names with the colors using the matplotlib notation.
        :param colorlist_y_sec_axis: A list with nested lists and strings. It should follow the same structure as data_on_y_sec_axis, but replacing the column names with the colors using the matplotlib notation.
        :param rows_renaming_dict: A dictionary. Should follow the pattern {'old row name 1': 'new row name 1', 'old row name 2': 'new row name 2'}
        :param cols_renaming_dict: A dictionary. Should follow the pattern {'old col name 1': 'new col name 1', 'old col name 2': 'new col name 2'}
        """
        import matplotlib.pyplot as plt
        import matplotlib.lines as lines
        import copy

        if vars_to_gather_cols is None:
            vars_to_gather_cols = []
        if vars_to_gather_rows is None:
            vars_to_gather_rows = []
        if detailed_cols is None:
            detailed_cols = []
        if detailed_rows is None:
            detailed_rows = []
        if custom_cols_order is None:
            custom_cols_order = []
        if custom_rows_order is None:
            custom_rows_order = []
        if data_on_y_axis_baseline_plot is None:
            data_on_y_axis_baseline_plot = []
        self.data_on_y_axis_baseline_plot = data_on_y_axis_baseline_plot
        # if adap_vs_stat_data_y_sec is None:
        #     adap_vs_stat_data_y_sec = []
        if colorlist_baseline_plot_data is None:
            colorlist_baseline_plot_data = []
        if data_on_y_main_axis is None:
            data_on_y_main_axis = []
        self.data_on_y_main_axis = data_on_y_main_axis
        if data_on_y_sec_axis is None:
            data_on_y_sec_axis = []
        self.data_on_y_sec_axis = data_on_y_sec_axis
        if colorlist_y_main_axis is None:
            colorlist_y_main_axis = []
        if colorlist_y_sec_axis is None:
            colorlist_y_sec_axis = []

        if best_fit_deg_y_main_axis is None:
            best_fit_deg_y_main_axis = copy.deepcopy(data_on_y_main_axis)
            for i in range(len(best_fit_deg_y_main_axis)):
                for j in range(len(best_fit_deg_y_main_axis[i])):
                    if j == 1:
                        for k in range(len(best_fit_deg_y_main_axis[i][j])):
                            best_fit_deg_y_main_axis[i][j][k] = 0
        else:
            for i in range(len(best_fit_deg_y_main_axis)):
                for j in range(len(best_fit_deg_y_main_axis[i])):
                    if j == 1:
                        for k in range(len(best_fit_deg_y_main_axis[i][j])):
                            if best_fit_deg_y_main_axis[i][j][k] is True:
                                best_fit_deg_y_main_axis[i][j][k] = 1
                            elif best_fit_deg_y_main_axis[i][j][k] is False:
                                best_fit_deg_y_main_axis[i][j][k] = 0

        if best_fit_deg_y_sec_axis is None:
            best_fit_deg_y_sec_axis = copy.deepcopy(data_on_y_sec_axis)
            for i in range(len(best_fit_deg_y_sec_axis)):
                for j in range(len(best_fit_deg_y_sec_axis[i])):
                    if j == 1:
                        for k in range(len(best_fit_deg_y_sec_axis[i][j])):
                            best_fit_deg_y_sec_axis[i][j][k] = 0
        else:
            for i in range(len(best_fit_deg_y_sec_axis)):
                for j in range(len(best_fit_deg_y_sec_axis[i])):
                    if j == 1:
                        for k in range(len(best_fit_deg_y_sec_axis[i][j])):
                            if best_fit_deg_y_sec_axis[i][j][k] is True:
                                best_fit_deg_y_sec_axis[i][j][k] = 1
                            elif best_fit_deg_y_sec_axis[i][j][k] is False:
                                best_fit_deg_y_sec_axis[i][j][k] = 0

        if best_fit_deg is None:
            best_fit_deg = copy.deepcopy(data_on_y_axis_baseline_plot)
            for i in range(len(best_fit_deg)):
                best_fit_deg[i] = 0
        else:
            for i in range(len(best_fit_deg)):
                if best_fit_deg[i] is True:
                    best_fit_deg[i] = 1
                elif best_fit_deg[i] is False:
                    best_fit_deg[i] = 0

        df_for_graph = self.df.copy()

        df_for_graph['col_to_gather_in_cols'] = 'temp'
        df_for_graph['col_to_gather_in_rows'] = 'temp'

        if len(vars_to_gather_rows) == 0:
            print('In relation to the variables to be gathered in rows,')
            self.enter_vars_to_gather(vars_to_gather_rows)
        if len(vars_to_gather_cols) == 0:
            print('In relation to the variables to be gathered in columns,')
            self.enter_vars_to_gather(vars_to_gather_cols)

        df_for_graph['col_to_gather_in_rows'] = df_for_graph[vars_to_gather_rows].agg('['.join, axis=1)
        df_for_graph['col_to_gather_in_cols'] = df_for_graph[vars_to_gather_cols].agg('['.join, axis=1)

        all_cols = list(set(df_for_graph['col_to_gather_in_cols']))
        rows = list(set(df_for_graph['col_to_gather_in_rows']))

        all_cols.sort()
        cols = all_cols

        rows.sort()

        while not (all(i in cols for i in detailed_cols)):
            print('Some of the detailed data to be gathered in columns based on the argument '
                  'vars_to_gather_cols is not available. '
                  'Only the following data is available for columns:')
            print(cols)
            detailed_cols = (list(str(var)
                                  for var
                                  in input("Please enter the requested data to be arranged "
                                           "in columns separated by semicolon: ").split(';')))
        while not (all(i in rows for i in detailed_rows)):
            print('Some of the detailed data to be gathered in rows based on the argument '
                  'vars_to_gather_rows is not available. '
                  'Only the following data is available for rows:')
            print(rows)
            detailed_rows = (list(str(var)
                                  for var
                                  in input("Please enter the requested data to be arranged "
                                           "in rows separated by semicolon: ").split(';')))

        if len(detailed_cols) > 0:
            cols = detailed_cols
        if len(detailed_rows) > 0:
            rows = detailed_rows

        if len(data_on_y_axis_baseline_plot) > 0:
            if baseline is None:
                print(f'No baseline has been specified. The list of available baselines is:')
                print(all_cols)
                baseline = input('Please choose one from the list above (it is case-sensitive) for baseline:')

            while not (any(baseline in i for i in all_cols)):
                print(f'"{baseline}" is not in list of categories you want to compare. The list is:')
                print(all_cols)
                baseline = input('Please choose one from the list above (it is case-sensitive) for baseline:')

            cols = [x for x in cols if x not in set([baseline])]

        # cols.sort()
        # rows.sort()

        cols_list_to_filter = cols + [baseline]

        df_for_graph = df_for_graph[
            (df_for_graph['col_to_gather_in_cols'].isin(cols_list_to_filter)) &
            (df_for_graph['col_to_gather_in_rows'].isin(rows))
            ]

        # if baseline is not None and len(data_on_y_axis_baseline_plot) > 0:
        df_for_graph['col_to_unstack'] = df_for_graph[
            ['col_to_gather_in_cols', 'col_to_gather_in_rows']].agg('['.join, axis=1)

        columns_to_drop = [
            # 'Date/Time',
            'Model',
            'ComfStand',
            'CAT',
            'ComfMod',
            'HVACmode',
            'VentCtrl',
            'VSToffset',
            'MinOToffset',
            'MaxWindSpeed',
            'ASTtol',
            'Source',
            'EPW',
            'NameSuffix',
            'col_to_gather_in_cols',
            'col_to_gather_in_rows'
        ]
        if 'monthly' in self.frequency:
            columns_to_drop.append('Month')
        if 'daily' in self.frequency:
            columns_to_drop.extend(['Month', 'Day'])
        if 'hourly' in self.frequency:
            columns_to_drop.extend(['Month', 'Day', 'Hour'])
        if 'timestep' in self.frequency:
            columns_to_drop.extend(['Month', 'Day', 'Hour', 'Minute'])

        df_for_graph = df_for_graph.drop(
            columns=columns_to_drop
        )

        multi_index = [
            'col_to_unstack'
        ]
        if self.frequency != 'runperiod':
            multi_index.append('Date/time')

        df_for_graph.set_index(multi_index, inplace=True)
        if len(data_on_y_axis_baseline_plot) > 0:
            self.max_value = max([df_for_graph[dataset].max() for dataset in data_on_y_axis_baseline_plot])

        standard_units = ['(°C)', '(h)', '(m3)', '(m2)', '(ach)', '(Wh)', '(kWh)', '(Wh/m2)', '(kWh/m2)']

        self.y_main_units = []
        for u in standard_units:
            if any(u in x for x in self.data_on_y_main_axis):
                self.y_main_units.append(
                    [u, [d for d in self.data_on_y_main_axis if u in d]]
                )

        self.y_sec_units = []
        for u in standard_units:
            if any(u in x for x in self.data_on_y_sec_axis):
                self.y_sec_units.append(
                    [u, [d for d in self.data_on_y_sec_axis if u in d]]
                )

        df_for_graph = df_for_graph.unstack('col_to_unstack')

        df_for_graph.columns = df_for_graph.columns.map('['.join)

        if len(custom_rows_order) > 0:
            ordered_rows = [ele for ele in custom_rows_order if ele in rows]
            rows = ordered_rows
        if len(custom_cols_order) > 0:
            ordered_cols = [ele for ele in custom_cols_order if ele in cols]
            cols = ordered_cols

        self.x_list = []
        for i in range(len(rows)):
            temp_row = []
            for j in range(len(cols)):
                if len(data_on_y_axis_baseline_plot) > 0:
                    temp = [
                        [i, j],
                        f'{rows[i]}_{cols[j]}',
                        [
                            df_for_graph[[x for x in df_for_graph.columns if rows[i] in x and baseline in x and dataset in x]]
                            for dataset in data_on_y_axis_baseline_plot
                        ]
                    ]
                else:
                    temp = [
                        [i, j],
                        f'{rows[i]}_{cols[j]}',
                        df_for_graph[[x for x in df_for_graph.columns if rows[i] in x and cols[j] in x and data_on_x_axis in x]]
                    ]
                temp_row.append(temp)
            self.x_list.append(temp_row)

        self.y_list_main = []
        for i in range(len(rows)):
            temp_row = []
            if baseline is not None and len(data_on_y_axis_baseline_plot) > 0:
                for j in range(len(cols)):
                    temp = [
                        [i, j],
                        f'{rows[i]}_{cols[j]}',
                        [
                            df_for_graph[[x for x in df_for_graph.columns if rows[i] in x and cols[j] in x and dataset in x]]
                            for dataset in data_on_y_axis_baseline_plot
                        ],
                        [dataset for dataset in data_on_y_axis_baseline_plot],
                        [color for color in colorlist_baseline_plot_data],
                        [deg for deg in best_fit_deg]
                    ]
                    temp_row.append(temp)
                self.y_list_main.append(temp_row)
            else:
                for j in range(len(cols)):
                    temp_col = []
                    for k in range(len(self.data_on_y_main_axis)):
                        temp = {
                            'axis': [i, j],
                            'title': f'{rows[i]}_{cols[j]}',
                            'dataframe': [
                                df_for_graph[[x for x in df_for_graph.columns if
                                              rows[i] in x and cols[j] in x and dataset in x]]
                                for dataset in self.data_on_y_main_axis[k][1]
                            ],
                            'label': [dataset for dataset in self.data_on_y_main_axis[k][1]],
                            'color': [color for color in colorlist_y_main_axis[k][1]],
                            'best fit line deg': [deg for deg in best_fit_deg_y_main_axis[k][1]]
                        }
                        temp_col.append(temp)
                    temp_row.append(temp_col)
                self.y_list_main.append(temp_row)

        self.y_list_sec = []
        for i in range(len(rows)):
            temp_row = []
            for j in range(len(cols)):
                temp_col = []
                for k in range(len(self.data_on_y_sec_axis)):
                    # if baseline is not None and len(adap_vs_stat_data_y_sec) > 0:
                    #     temp = [
                    #         [i, j],
                    #         f'{rows[i]}_{cols[j]}',
                    #         [
                    #             df_for_graph[[x for x in df_for_graph.columns if rows[i] in x and cols[j] in x and dataset in x]]
                    #             for dataset in adap_vs_stat_data_y_sec
                    #         ],
                    #         [dataset for dataset in adap_vs_stat_data_y_sec],
                    #         [color for color in colorlist_y_sec_axis]
                    #     ]
                    # else:
                    temp = {
                        'axis': [i, j],
                        'title': f'{rows[i]}_{cols[j]}',
                        'dataframe': [
                            df_for_graph[[x for x in df_for_graph.columns if rows[i] in x and cols[j] in x and dataset in x]]
                            for dataset in data_on_y_sec_axis[k][1]
                        ],
                        'label': [dataset for dataset in data_on_y_sec_axis[k][1]],
                        'color': [color for color in colorlist_y_sec_axis[k][1]],
                        'best fit line deg': [deg for deg in best_fit_deg_y_sec_axis[k][1]]
                    }
                    temp_col.append(temp)
                temp_row.append(temp_col)
            self.y_list_sec.append(temp_row)


        print(f'The number of rows and the list of these is going to be:')
        print(f'No. of rows = {len(rows)}')
        print(f'List of rows:')
        print(*rows, sep='\n')

        self.rename_rows = 'n'

        try:
            if all([i in rows for i in [j for j in rows_renaming_dict]]):
                self.rows_new_names = []
                for i in rows:
                    for j in rows_renaming_dict:
                        if i == j:
                            self.rows_new_names.append(rows_renaming_dict[j])
                print(f'The renamed rows are going to be:')
                print(*self.rows_new_names, sep='\n')
                self.rename_rows = 'y'
        except TypeError:
            pass

        rename_rows_user_input = 'n'
        if rows_renaming_dict is None:
            rename_rows_user_input = input('Do you want to rename the rows? [y/n]: ')
        try:
            if not(all([i in rows for i in [j for j in rows_renaming_dict]])):
                rename_rows_user_input = input('Not all of the old names you have entered in rows_new_names were found. '
                                         'Therefore, if you still want to rename the rows, you will have to enter the new names now. '
                                         'Do you want to rename the rows? [y/n]: ')
        except TypeError:
            pass
        if rename_rows_user_input == 'y':
            self.rows_new_names = []
            for i in rows:
                new_name = input(f'Please enter the new name for {i}: ')
                self.rows_new_names.append(new_name)
            print(f'The renamed rows are going to be:')
            print(*self.rows_new_names, sep='\n')
            self.rename_rows = 'y'

        # elif rename_rows:
        #     if len(self.rows_new_names) == 0:
        #         self.rename_rows = input('Do you want to rename the rows? [y/n]: ')
        #         if self.rename_rows == 'y':
        #             self.rows_new_names = []
        #             for i in rows:
        #                 new_name = input(f'Please enter the new name for {i}: ')
        #                 self.rows_new_names.append(new_name)

        print(f'The number of columns and the list of these is going to be:')
        print(f'No. of columns = {len(cols)}')
        print(f'List of columns:')
        print(*cols, sep='\n')

        self.rename_cols = 'n'

        try:
            if all([i in cols for i in [j for j in cols_renaming_dict]]):
                self.cols_new_names = []
                for i in cols:
                    for j in cols_renaming_dict:
                        if i == j:
                            self.cols_new_names.append(cols_renaming_dict[j])
                print(f'The renamed columns are going to be:')
                print(*self.cols_new_names, sep='\n')
                self.rename_cols = 'y'
        except TypeError:
            pass

        rename_cols_user_input = 'n'
        if cols_renaming_dict is None:
            rename_cols_user_input = input('Column names will be the subplot titles. Do you want to rename them? [y/n]: ')
        try:
            if not(all([i in cols for i in [j for j in cols_renaming_dict]])):
                rename_cols_user_input = input('Not all of the old names you have entered in cols_new_names were found. '
                                         'Therefore, if you still want to rename the columns, you will have to enter the new names now. '
                                         'Do you want to rename the columns? [y/n]: ')
        except TypeError:
            pass

        if rename_cols_user_input == 'y':
            self.cols_new_names = []
            for i in cols:
                new_name = input(f'Please enter the new name for {i}: ')
                self.cols_new_names.append(new_name)
            print(f'The renamed columns are going to be:')
            print(*self.cols_new_names, sep='\n')
            self.rename_cols = 'y'

        # elif rename_cols:
        #     if len(self.cols_new_names) == 0:
        #         self.rename_cols = input('Column names will be the subplot titles. Do you want to rename them? [y/n]: ')
        #         if self.rename_cols == 'y':
        #             self.cols_new_names = []
        #             for i in cols:
        #                 new_name = input(f'Please enter the new name for {i}: ')
        #                 self.cols_new_names.append(new_name)

        self.rows = rows
        self.cols = cols
        self.df_for_graph = df_for_graph


    def scatter_plot(
            self,
            vars_to_gather_cols: list = None,
            vars_to_gather_rows: list = None,
            detailed_cols: list = None,
            detailed_rows: list = None,
            custom_cols_order: list = None,
            custom_rows_order: list = None,
            data_on_x_axis: str = None,
            data_on_y_main_axis: list = None,
            data_on_y_sec_axis: list = None,
            colorlist_y_main_axis: list = None,
            colorlist_y_sec_axis: list = None,
            best_fit_deg_y_main_axis: list = None,
            best_fit_deg_y_sec_axis: list = None,
            rows_renaming_dict: dict = None,
            cols_renaming_dict: dict = None,
            sharex: bool = True,
            sharey: bool = True,
            supxlabel: str = None,
            figname: str = None,
            figsize: float = 1,
            ratio_height_to_width: float = 1,
            dpi: int = 500,
            confirm_graph: bool = False,
            set_facecolor: any = (0, 0, 0, 0.10),
            best_fit_background_linewidth: float = 1,
            best_fit_linewidth: float = 0.5,
            best_fit_linestyle: any = (0, (5, 10)),
    ):
        """Used to plot a scatter plot.

        :param vars_to_gather_cols: A list of strings.
            The list should be the variables you want to show in subplot columns.
        :type vars_to_gather_cols: list
        :param vars_to_gather_rows: A list of strings.
            The list should be the variables you want to show in subplot rows.
        :type vars_to_gather_rows: list
        :param detailed_cols: A list of strings.
            The list should be the specific data you want to show in subplots columns.
            Used to filter.
        :type detailed_cols: list
        :param detailed_rows: A list of strings.
            The list should be the specific data you want to show in subplots rows.
            Used to filter.
        :type detailed_rows: list
        :param custom_cols_order: A list of strings.
            The list should be the specific order for the items shown in subplot columns.
        :type custom_cols_order: list
        :param custom_rows_order: A list of strings.
            The list should be the specific order for the items shown in subplot rows.
        :type custom_rows_order: list
        :param data_on_x_axis: A string. The column name you want to plot in the x-axis.
        :type data_on_x_axis: str
        :param data_on_y_main_axis: A list with nested lists and strings.
            Used to select the data you want to show in the scatter plot main y-axis.
            It needs to follow this structure:
            [['name_on_y_main_axis', [list of column names you want to plot]]]
        :type data_on_y_main_axis: list
        :param data_on_y_sec_axis: A list with nested lists and strings.
            Used to select the data you want to show in the scatter plot secondary y-axis.
            It needs to follow this structure:
            [[['name_on_1st_y_sec_axis', [list of column names you want to plot]], ['name_on_2nd_y_sec_axis', [list of column names you want to plot]], etc]
        :type data_on_y_sec_axis: list
        :param colorlist_y_main_axis: A list with nested lists and strings.
            It should follow the same structure as data_on_y_main_axis,
            but replacing the column names with the colors using the matplotlib notation.
        :type colorlist_y_main_axis: list
        :param colorlist_y_sec_axis: A list with nested lists and strings.
            It should follow the same structure as data_on_y_sec_axis,
            but replacing the column names with the colors using the matplotlib notation.
        :type colorlist_y_sec_axis: list
        :param best_fit_deg_y_sec_axis: A list with nested lists and strings.
            It should follow the same structure as data_on_y_sec_axis,
            but replacing the column names with the polynomial degree for the best fit lines.
        :type best_fit_deg_y_sec_axis: list
        :param best_fit_deg_y_main_axis: A list with nested lists and strings.
            It should follow the same structure as data_on_y_main_axis,
            but replacing the column names with the polynomial degree for the best fit lines.
        :type best_fit_deg_y_main_axis: list
        :param rows_renaming_dict: A dictionary. Should follow the pattern
            {'old row name 1': 'new row name 1', 'old row name 2': 'new row name 2'}
        :type rows_renaming_dict: dict
        :param cols_renaming_dict: A dictionary. Should follow the pattern
            {'old col name 1': 'new col name 1', 'old col name 2': 'new col name 2'}
        :type cols_renaming_dict: dict
        :param sharey: True to share the x-axis across all subplots
        :type sharey: bool
        :param sharex: True to share the y-axis across all subplots
        :type sharex: bool
        :param supxlabel: A string. The label shown in the x-axis.
        :type supxlabel: str
        :param figname: A string. The name of the saved figure without extension.
        :type figname: str
        :param figsize: A float. It is the figure size.
        :type figsize: float
        :param ratio_height_to_width: A float. By default, is 1 (squared). If 0.5 is entered, the figure will be half higher than wide.
        :type ratio_height_to_width: float
        :param dpi: An integer. The number of dpis for image quality.
        :type dpi: int
        :param confirm_graph: A bool. True to skip confirmation step.
        :type confirm_graph: bool
        :param set_facecolor: Usage is similar to matplotlib.axes.Axes.set_facecolor
        :type set_facecolor: any
        :param best_fit_linestyle: Anything in matplotlib linestyle notation. Use to change the style of the best fit lines.
        :type best_fit_linestyle: any
        :param best_fit_linewidth: A float. Used to change the width of the best fit lines.
        :type best_fit_linewidth: float
        :param best_fit_background_linewidth: A float.
            Used to change the width of the background best fit lines.
            Must be greater than best_fit_linewidth.
        :type best_fit_background_linewidth: float
        """
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.patheffects as pe
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import PolynomialFeatures

        # todo testing from here

        self.df = self.df.fillna(0)

        self.generate_fig_data(
            vars_to_gather_cols=vars_to_gather_cols,
            vars_to_gather_rows=vars_to_gather_rows,
            detailed_cols=detailed_cols,
            detailed_rows=detailed_rows,
            custom_cols_order=custom_cols_order,
            custom_rows_order=custom_rows_order,
            data_on_y_main_axis=data_on_y_main_axis,
            data_on_y_sec_axis=data_on_y_sec_axis,
            data_on_x_axis=data_on_x_axis,
            colorlist_y_main_axis=colorlist_y_main_axis,
            colorlist_y_sec_axis=colorlist_y_sec_axis,
            best_fit_deg_y_main_axis=best_fit_deg_y_main_axis,
            best_fit_deg_y_sec_axis=best_fit_deg_y_sec_axis,
            rows_renaming_dict=rows_renaming_dict,
            cols_renaming_dict=cols_renaming_dict,
        )

        # todo testing until here

        rows = self.rows
        cols = self.cols

        # print(f'The number of rows and the list of these is going to be:')
        # print(f'No. of rows = {len(rows)}')
        # print(f'List of rows:')
        # print(*rows, sep='\n')
        #
        # print(f'The number of columns and the list of these is going to be:')
        # print(f'No. of columns = {len(cols)}')
        # print(f'List of columns:')
        # print(*cols, sep='\n')

        if confirm_graph is False:
            proceed = input('Do you want to proceed? [y/n]:')
            if 'y' in proceed:
                confirm_graph = True
            elif 'n' in proceed:
                confirm_graph = False

        if confirm_graph:
            fig, ax = plt.subplots(
                nrows=len(rows),
                ncols=len(cols),
                sharex=sharex,
                sharey=sharey,
                constrained_layout=True,
                figsize=(figsize * len(cols), ratio_height_to_width * figsize * len(rows))
            )

            main_y_axis = []
            sec_y_axis = []

            for i in range(len(rows)):
                main_y_axis_temp_rows = []
                sec_y_axis_temp_rows = []
                for j in range(len(cols)):

                    main_y_axis_temp_cols = []
                    sec_y_axis_temp_cols = []

                    if len(rows) == 1 and len(cols) == 1:
                        for k in range(len(self.data_on_y_main_axis)):
                            main_y_axis_temp_cols.append(ax)
                        main_y_axis_temp_rows.append(main_y_axis_temp_cols)
                        if len(self.data_on_y_sec_axis) > 0:
                            for k in range(len(self.data_on_y_sec_axis)):
                                sec_y_axis_temp_cols.append(ax.twinx())
                            sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
                    elif len(cols) == 1 and len(rows) > 1:
                        for k in range(len(self.data_on_y_main_axis)):
                            main_y_axis_temp_cols.append(ax[i])
                        main_y_axis_temp_rows.append(main_y_axis_temp_cols)
                        if len(self.data_on_y_sec_axis) > 0:
                            for k in range(len(self.data_on_y_sec_axis)):
                                sec_y_axis_temp_cols.append(ax[i].twinx())
                            sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
                    elif len(rows) == 1 and len(cols) > 1:
                        # continue
                        for k in range(len(self.data_on_y_main_axis)):
                            main_y_axis_temp_cols.append(ax[j])
                        main_y_axis_temp_rows.append(main_y_axis_temp_cols)
                        if len(self.data_on_y_sec_axis) > 0:
                            for k in range(len(self.data_on_y_sec_axis)):
                                sec_y_axis_temp_cols.append(ax[j].twinx())
                            sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
                    else:
                        for k in range(len(self.data_on_y_main_axis)):
                            main_y_axis_temp_cols.append(ax[i, j])
                        main_y_axis_temp_rows.append(main_y_axis_temp_cols)
                        if len(self.data_on_y_sec_axis) > 0:
                            for k in range(len(self.data_on_y_sec_axis)):
                                sec_y_axis_temp_cols.append(ax[i, j].twinx())
                            sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
                main_y_axis.append(main_y_axis_temp_rows)
                sec_y_axis.append(sec_y_axis_temp_rows)

            # if len(rows) == 1 and len(cols) > 1:


            for i in range(len(rows)):
                for j in range(len(cols)):
                    for k in range(len(self.y_list_main[i][j])):
                        main_y_axis[i][j][k].grid(True, linestyle='-.')
                        main_y_axis[i][j][k].tick_params(axis='both',
                                                         grid_color='black',
                                                         grid_alpha=0.5)
                        main_y_axis[i][j][k].set_facecolor(set_facecolor)

                        for x in range(len(self.y_list_main[i][j][k]['dataframe'])):

                            if 'Setpoint Temperature' in self.y_list_main[i][j][k]['label'][x]:
                                zord = 1
                            else:
                                zord = 0

                            if i == 0 and j == 0:
                                main_y_axis[i][j][k].scatter(
                                    self.x_list[i][j][2],
                                    self.y_list_main[i][j][k]['dataframe'][x],
                                    c=self.y_list_main[i][j][k]['color'][x],
                                    s=1,
                                    marker='.',
                                    alpha=0.5,
                                    label=self.y_list_main[i][j][k]['label'][x],
                                    zorder=zord
                                )
                            else:
                                main_y_axis[i][j][k].scatter(
                                    self.x_list[i][j][2],
                                    self.y_list_main[i][j][k]['dataframe'][x],
                                    c=self.y_list_main[i][j][k]['color'][x],
                                    s=1,
                                    marker='.',
                                    alpha=0.5,
                                    zorder=zord
                                )

            for i in range(len(rows)):
                for j in range(len(cols)):
                    for k in range(len(self.y_list_sec[i][j])):
                        sec_y_axis[0][0][k].get_shared_y_axes().join(sec_y_axis[0][0][k], sec_y_axis[i][j][k])
                        if len(self.data_on_y_sec_axis) > 1:
                            if len(self.y_list_sec[i][j]) >= 1:
                                if j < (len(cols) - 1):
                                    sec_y_axis[i][j][k].set_yticklabels([])
                                    sec_y_axis[i][j][k].set_yticks([])
                                if j == (len(cols) - 1):
                                    sec_y_axis[i][j][k].set_ylabel(self.data_on_y_sec_axis[k][0])
                                    sec_y_axis[i][j][k].spines["right"].set_position(("axes", 1 + k * 0.15))
                                    sec_y_axis[i][j][k].spines["right"].set_visible(True)
                        for x in range(len(self.y_list_sec[i][j][k]['dataframe'])):
                            if 'Setpoint Temperature' in self.y_list_sec[i][j][k]['label'][x]:
                                zord = 1
                            else:
                                zord = 0
                            if i == 0 and j == 0:
                                sec_y_axis[i][j][k].scatter(
                                    self.x_list[i][j][2],
                                    self.y_list_sec[i][j][k]['dataframe'][x],
                                    c=self.y_list_sec[i][j][k]['color'][x],
                                    s=1,
                                    marker='.',
                                    alpha=0.5,
                                    label=self.y_list_sec[i][j][k]['label'][x],
                                    zorder=zord,
                                )
                            else:
                                sec_y_axis[i][j][k].scatter(
                                    self.x_list[i][j][2],
                                    self.y_list_sec[i][j][k]['dataframe'][x],
                                    c=self.y_list_sec[i][j][k]['color'][x],
                                    s=1,
                                    marker='.',
                                    alpha=0.5,
                                    zorder=zord,
                                )

            for i in range(len(rows)):
                for j in range(len(cols)):
                    for k in range(len(self.y_list_main[i][j])):
                        for x in range(len(self.y_list_main[i][j][k]['dataframe'])):
                            if self.y_list_main[i][j][k]['best fit line deg'][x] > 0:
                                poly_features = PolynomialFeatures(degree=self.y_list_main[i][j][k]['best fit line deg'][x], include_bias=False)
                                X_poly = poly_features.fit_transform(self.x_list[i][j][2].to_numpy())
                                lin_reg = LinearRegression()
                                lin_reg.fit(X_poly, self.y_list_main[i][j][k]['dataframe'][x].to_numpy())
                                main_y_axis[i][j][k].plot(
                                    self.x_list[i][j][2].to_numpy(),
                                    lin_reg.predict(X_poly),
                                    color=self.y_list_main[i][j][k]['color'][x],
                                    # linestyle='--',
                                    linestyle=best_fit_linestyle,
                                    linewidth=best_fit_linewidth,
                                    path_effects=[pe.Stroke(linewidth=best_fit_background_linewidth, foreground='0'), pe.Normal()],
                                    zorder=2
                                )
                    for k in range(len(self.y_list_sec[i][j])):
                        for x in range(len(self.y_list_sec[i][j][k]['dataframe'])):
                            if self.y_list_sec[i][j][k]['best fit line deg'][x] > 0:
                                poly_features = PolynomialFeatures(degree=self.y_list_sec[i][j][k]['best fit line deg'][x], include_bias=False)
                                X_poly = poly_features.fit_transform(self.x_list[i][j][2].to_numpy())
                                lin_reg = LinearRegression()
                                lin_reg.fit(X_poly, self.y_list_sec[i][j][k]['dataframe'][x].to_numpy())
                                sec_y_axis[i][j][k].plot(
                                    self.x_list[i][j][2].to_numpy(),
                                    lin_reg.predict(X_poly),
                                    color=self.y_list_sec[i][j][k]['color'][x],
                                    # linestyle='--',
                                    linestyle=best_fit_linestyle,
                                    linewidth=best_fit_linewidth,
                                    path_effects=[pe.Stroke(linewidth=best_fit_background_linewidth, foreground='0'), pe.Normal()],
                                    zorder=2
                                )

            if len(rows) == 1:
                if len(cols) == 1:
                    for i in range(len(rows)):
                        if self.rename_rows == 'y':
                        # if self.rows_new_names is not None:
                            ax.set_ylabel(self.rows_new_names[i], rotation=90, size='large')
                        else:
                            ax.set_ylabel(rows[i], rotation=90, size='large')
                    for j in range(len(cols)):
                        if self.rename_cols == 'y':
                        # if self.cols_new_names is not None:
                            ax.set_title(self.cols_new_names[j])
                        else:
                            ax.set_title(cols[j])

            if len(rows) > 1:
                if len(cols) == 1:
                    for i in range(len(rows)):
                        if self.rename_rows == 'y':
                        # if self.rows_new_names is not None:
                            ax[i].set_ylabel(self.rows_new_names[i], rotation=90, size='large')
                        else:
                            ax[i].set_ylabel(rows[i], rotation=90, size='large')
                    for j in range(len(cols)):
                        if self.rename_cols == 'y':
                        # if self.cols_new_names is not None:
                            ax[0].set_title(self.cols_new_names[j])
                        else:
                            ax[0].set_title(cols[j])
                else:
                    for i in range(len(rows)):
                        if self.rename_rows == 'y':
                        # if self.rows_new_names is not None:
                            ax[i, 0].set_ylabel(self.rows_new_names[i], rotation=90, size='large')
                        else:
                            ax[i, 0].set_ylabel(rows[i], rotation=90, size='large')
                    for j in range(len(cols)):
                        if self.rename_cols == 'y':
                        # if self.cols_new_names is not None:
                            ax[0, j].set_title(self.cols_new_names[j])
                        else:
                            ax[0, j].set_title(cols[j])

            supx = fig.supxlabel(supxlabel)
            supy = fig.supylabel(self.data_on_y_main_axis[0][0])

            leg = fig.legend(
                bbox_to_anchor=(0.5, 0),
                loc='upper center',
                fontsize='large'
                # borderaxespad=0.1,
            )
            if len(self.data_on_y_sec_axis) == 1:
                rhstext = fig.text(1, 0.5, s=self.data_on_y_sec_axis[0][0], va='center', rotation='vertical', size='large')

            if len(self.data_on_y_sec_axis) == 1:
                bbox_extra_artists_tuple = (rhstext, leg, supx, supy)
            else:
                bbox_extra_artists_tuple = (leg, supx, supy)

            for i in range(len(leg.legendHandles)):
                leg.legendHandles[i]._sizes = [30]

            # plt.subplots_adjust(bottom=0.2)
            # plt.tight_layout()

            plt.savefig(figname + '.png',
                        dpi=dpi,
                        format='png',
                        bbox_extra_artists=bbox_extra_artists_tuple,
                        bbox_inches='tight')

            plt.show()

        self.rows = rows

    def scatter_plot_with_baseline(
            self,
            vars_to_gather_cols: list = None,
            vars_to_gather_rows: list = None,
            detailed_cols: list = None,
            detailed_rows: list = None,
            custom_cols_order: list = None,
            custom_rows_order: list = None,
            data_on_y_axis_baseline_plot: list = None,
            baseline: str = None,
            colorlist_baseline_plot_data: list = None,
            best_fit_deg: list = None,
            rows_renaming_dict: dict = None,
            cols_renaming_dict: dict = None,
            supxlabel: str = None,
            supylabel: str = None,
            figname: str = None,
            figsize: int = 1,
            markersize: int = 1,
            dpi: int = 500,
            confirm_graph: bool = False,
            set_facecolor: any = (0, 0, 0, 0.10),
            best_fit_background_linewidth: float = 1,
            best_fit_linewidth: float = 0.5,
            best_fit_linestyle: any = (0, (5, 10)),
    ):
        """
        Used to plot a scatter plot with baseline.

        :param vars_to_gather_cols: A list of strings.
            The list should be the variables you want to show in subplot columns.
        :type vars_to_gather_cols: list
        :param vars_to_gather_rows: A list of strings.
            The list should be the variables you want to show in subplot rows.
        :type vars_to_gather_rows: list
        :param detailed_cols: A list of strings.
            The list should be the specific data you want to show in subplots columns.
            Used to filter.
        :type detailed_cols: list
        :param detailed_rows: A list of strings.
            The list should be the specific data you want to show in subplots rows.
            Used to filter.
        :type detailed_rows: list
        :param custom_cols_order: A list of strings.
            The list should be the specific order for the items shown in subplot columns.
        :type custom_cols_order: list
        :param custom_rows_order: A list of strings.
            The list should be the specific order for the items shown in subplot rows.
        :type custom_rows_order: list
        :param data_on_y_axis_baseline_plot: A list of strings.
            Used to select the data you want to show in the graph.
            Should be a list of the column names you want to plot in each subplot.
        :type data_on_y_axis_baseline_plot: list
        :param baseline: A string, used only in data_on_y_axis_baseline_plot.
            The baseline should be one of the combinations in vars_to_gather_cols.
            It will be plotted in x-axis,
            while the reference combination for comparison in y-axis.
        :type baseline: str
        :param colorlist_baseline_plot_data: A list of strings.
            Should be the colors using the matplotlib color notation
            for the columns entered in data_on_y_axis_baseline_plot in the same order.
        :type colorlist_baseline_plot_data: list
        :param best_fit_deg: A list with nested lists and strings.
            It should follow the same structure as data_on_y_axis_baseline_plot,
            but replacing the column names with the polynomial degree for the best fit lines.
        :type best_fit_deg: list
        :param rows_renaming_dict: A dictionary. Should follow the pattern
            {'old row name 1': 'new row name 1', 'old row name 2': 'new row name 2'}
        :type rows_renaming_dict: dict
        :param cols_renaming_dict: A dictionary. Should follow the pattern
            {'old col name 1': 'new col name 1', 'old col name 2': 'new col name 2'}
        :type cols_renaming_dict: dict
        :param supxlabel: A string. The label shown in the x-axis.
        :type supxlabel: str
        :param supylabel: A string. The label shown in the y-axis.
        :type supylabel: str
        :param figname: A string. The name of the saved figure without extension.
        :type figname: str
        :param figsize: A float. It is the figure size.
        :type figsize: float
        :param markersize: An integer. The size of the markers.
        :type markersize: int
        :param dpi: An integer. The number of dpis for image quality.
        :type dpi: int
        :param confirm_graph: A bool. True to skip confirmation step.
        :type confirm_graph: bool
        :param best_fit_linestyle: Anything in matplotlib linestyle notation.
            Use to change the style of the best fit lines.
        :type best_fit_linestyle: any
        :param best_fit_linewidth: A float. Used to change the width of the best fit lines.
        :type best_fit_linewidth: float
        :param best_fit_background_linewidth: A float. Used to change the width of the
            background best fit lines. Must be greater than best_fit_linewidth.
        :type best_fit_background_linewidth: float
        """
        import matplotlib.pyplot as plt
        import matplotlib.lines as lines
        import matplotlib.patheffects as pe
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import PolynomialFeatures


        # todo testing from here

        self.generate_fig_data(
            vars_to_gather_cols=vars_to_gather_cols,
            vars_to_gather_rows=vars_to_gather_rows,
            detailed_cols=detailed_cols,
            detailed_rows=detailed_rows,
            custom_cols_order=custom_cols_order,
            custom_rows_order=custom_rows_order,
            data_on_y_axis_baseline_plot=data_on_y_axis_baseline_plot,
            baseline=baseline,
            colorlist_baseline_plot_data=colorlist_baseline_plot_data,
            best_fit_deg=best_fit_deg,
            rows_renaming_dict=rows_renaming_dict,
            cols_renaming_dict=cols_renaming_dict,
        )

        # todo testing until here

        # print(f'The number of rows and the list of these is going to be:')
        # print(f'No. of rows = {len(self.rows)}')
        # print(f'List of self.rows:')
        # print(*self.rows, sep='\n')
        #
        # print(f'The number of columns and the list of these is going to be:')
        # print(f'No. of columns = {len(self.cols)}')
        # print(f'List of columns:')
        # print(*self.cols, sep='\n')

        if confirm_graph is False:
            proceed = input('Do you want to proceed? [y/n]:')
            if 'y' in proceed:
                confirm_graph = True
            elif 'n' in proceed:
                confirm_graph = False

        if confirm_graph:
            fig, ax = plt.subplots(nrows=len(self.rows),
                                   ncols=len(self.cols),
                                   sharex=True,
                                   sharey=True,
                                   constrained_layout=True,
                                   figsize=(figsize * len(self.cols), figsize * len(self.rows)))

            # y_list_main_scatter
            for i in range(len(self.rows)):
                for j in range(len(self.cols)):
                    if len(self.rows) == 1 and len(self.cols) == 1:
                        # ax.set_title(f'{self.rows[i]} / {self.cols[j]}')
                        ax.grid(True, linestyle='-.')
                        ax.tick_params(axis='both',
                                       grid_color='black',
                                       grid_alpha=0.5)
                        ax.set_facecolor(set_facecolor)
                        ax.add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax.add_artist((lines.Line2D(
                            [0, self.max_value / 2], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax.add_artist((lines.Line2D(
                            [0, self.max_value / 4], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax.add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value / 2],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax.add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value / 4],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))

                        for k in range(len(self.x_list[i][j][2])):
                            if i == 0 and j == 0:
                                ax.scatter(
                                    self.x_list[i][j][2][k],
                                    self.y_list_main[i][j][2][k],
                                    c=self.y_list_main[i][j][4][k],
                                    s=markersize,
                                    marker='o',
                                    alpha=0.5,
                                    label=self.y_list_main[i][j][3][k]
                                )
                                # if len(self.adap_vs_stat_data_y_sec) > 0:
                                #     ax.twinx().scatter(
                                #         self.x_list[i][j][2][k],
                                #         self.y_list_sec[i][j][2][k],
                                #         c=self.y_list_sec[i][j][4][k],
                                #         s=markersize,
                                #         marker='o',
                                #         alpha=0.5,
                                #         label=self.y_list_main[i][j][3][k]
                                #     )
                            else:
                                ax.scatter(
                                    self.x_list[i][j][2][k],
                                    self.y_list_main[i][j][2][k],
                                    c=self.y_list_main[i][j][4][k],
                                    s=markersize,
                                    marker='o',
                                    alpha=0.5,
                                )
                                # if len(self.adap_vs_stat_data_y_sec) > 0:
                                #     ax.twinx().scatter(
                                #         self.x_list[i][j][2][k],
                                #         self.y_list_sec[i][j][2][k],
                                #         c=self.y_list_sec[i][j][4][k],
                                #         s=markersize,
                                #         marker='o',
                                #         alpha=0.5,
                                #         label=self.y_list_main[i][j][3][k]
                                #     )
                            if self.y_list_main[i][j][5][k] > 0:
                                poly_features = PolynomialFeatures(degree=self.y_list_main[i][j][5][k], include_bias=False)
                                X_poly = poly_features.fit_transform(self.x_list[i][j][2][k].to_numpy())
                                lin_reg = LinearRegression()
                                lin_reg.fit(X_poly, self.y_list_main[i][j][2][k].to_numpy())
                                ax.plot(
                                    self.x_list[i][j][2][k].to_numpy(),
                                    lin_reg.predict(X_poly),
                                    color=self.y_list_main[i][j][4][k],
                                    # linestyle='--',
                                    linestyle=best_fit_linestyle,
                                    linewidth=best_fit_linewidth,
                                    path_effects=[pe.Stroke(linewidth=best_fit_background_linewidth, foreground='0'), pe.Normal()],
                                    zorder=1
                                )
                        ax.set_ylim((0, self.max_value))
                        ax.set_xlim((0, self.max_value))

                    elif len(self.cols) == 1 and len(self.rows) > 1:
                        # ax[i].set_title(f'{self.rows[i]} / {self.cols[j]}')
                        ax[i].grid(True, linestyle='-.')
                        ax[i].tick_params(axis='both',
                                          grid_color='black',
                                          grid_alpha=0.5)
                        ax[i].set_facecolor(set_facecolor)
                        ax[i].add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[i].add_artist((lines.Line2D(
                            [0, self.max_value / 2], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[i].add_artist((lines.Line2D(
                            [0, self.max_value / 4], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[i].add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value / 2],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[i].add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value / 4],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))

                        for k in range(len(self.x_list[i][j][2])):
                            if i == 0 and j == 0:
                                ax[i].scatter(
                                    self.x_list[i][j][2][k],
                                    self.y_list_main[i][j][2][k],
                                    c=self.y_list_main[i][j][4][k],
                                    s=markersize,
                                    marker='o',
                                    alpha=0.5,
                                    label=self.y_list_main[i][j][3][k]
                                )
                                # if len(self.adap_vs_stat_data_y_sec) > 0:
                                #     ax[i].twinx().scatter(
                                #         self.x_list[i][j][2][k],
                                #         self.y_list_sec[i][j][2][k],
                                #         c=self.y_list_sec[i][j][4][k],
                                #         s=markersize,
                                #         marker='o',
                                #         alpha=0.5,
                                #         label=self.y_list_main[i][j][3][k]
                                #     )
                            else:
                                ax[i].scatter(
                                    self.x_list[i][j][2][k],
                                    self.y_list_main[i][j][2][k],
                                    c=self.y_list_main[i][j][4][k],
                                    s=markersize,
                                    marker='o',
                                    alpha=0.5,
                                )
                                # if len(self.adap_vs_stat_data_y_sec) > 0:
                                #     ax[i].twinx().scatter(
                                #         self.x_list[i][j][2][k],
                                #         self.y_list_sec[i][j][2][k],
                                #         c=self.y_list_sec[i][j][4][k],
                                #         s=markersize,
                                #         marker='o',
                                #         alpha=0.5,
                                #         label=self.y_list_main[i][j][3][k]
                                #     )
                            if self.y_list_main[i][j][5][k] > 0:
                                poly_features = PolynomialFeatures(degree=self.y_list_main[i][j][5][k], include_bias=False)
                                X_poly = poly_features.fit_transform(self.x_list[i][j][2][k].to_numpy())
                                lin_reg = LinearRegression()
                                lin_reg.fit(X_poly, self.y_list_main[i][j][2][k].to_numpy())
                                ax[i].plot(
                                    self.x_list[i][j][2][k].to_numpy(),
                                    lin_reg.predict(X_poly),
                                    color=self.y_list_main[i][j][4][k],
                                    # linestyle='--',
                                    linestyle=best_fit_linestyle,
                                    linewidth=best_fit_linewidth,
                                    path_effects=[pe.Stroke(linewidth=best_fit_background_linewidth, foreground='0'), pe.Normal()],
                                    zorder=1
                                )

                        ax[i].set_ylim((0, self.max_value))
                        ax[i].set_xlim((0, self.max_value))

                    elif len(self.rows) == 1 and len(self.cols) > 1:
                        # ax[j].set_title(f'{self.rows[i]} / {self.cols[j]}')
                        ax[j].grid(True, linestyle='-.')
                        ax[j].tick_params(axis='both',
                                          grid_color='black',
                                          grid_alpha=0.5)
                        ax[j].set_facecolor(set_facecolor)
                        ax[j].add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[j].add_artist((lines.Line2D(
                            [0, self.max_value / 2], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[j].add_artist((lines.Line2D(
                            [0, self.max_value / 4], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[j].add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value / 2],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[j].add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value / 4],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))

                        for k in range(len(self.x_list[i][j][2])):
                            if i == 0 and j == 0:
                                ax[j].scatter(
                                    self.x_list[i][j][2][k],
                                    self.y_list_main[i][j][2][k],
                                    c=self.y_list_main[i][j][4][k],
                                    s=markersize,
                                    marker='o',
                                    alpha=0.5,
                                    label=self.y_list_main[i][j][3][k]
                                )
                                # if len(self.adap_vs_stat_data_y_sec) > 0:
                                #     ax[j].twinx().scatter(
                                #         self.x_list[i][j][2][k],
                                #         self.y_list_sec[i][j][2][k],
                                #         c=self.y_list_sec[i][j][4][k],
                                #         s=markersize,
                                #         marker='o',
                                #         alpha=0.5,
                                #         label=self.y_list_main[i][j][3][k]
                                #     )
                            else:
                                ax[j].scatter(
                                    self.x_list[i][j][2][k],
                                    self.y_list_main[i][j][2][k],
                                    c=self.y_list_main[i][j][4][k],
                                    s=markersize,
                                    marker='o',
                                    alpha=0.5,
                                )
                                # if len(self.adap_vs_stat_data_y_sec) > 0:
                                #     ax[j].twinx().scatter(
                                #         self.x_list[i][j][2][k],
                                #         self.y_list_sec[i][j][2][k],
                                #         c=self.y_list_sec[i][j][4][k],
                                #         s=markersize,
                                #         marker='o',
                                #         alpha=0.5,
                                #         label=self.y_list_main[i][j][3][k]
                                #     )
                            if self.y_list_main[i][j][5][k] > 0:
                                poly_features = PolynomialFeatures(degree=self.y_list_main[i][j][5][k], include_bias=False)
                                X_poly = poly_features.fit_transform(self.x_list[i][j][2][k].to_numpy())
                                lin_reg = LinearRegression()
                                lin_reg.fit(X_poly, self.y_list_main[i][j][2][k].to_numpy())
                                ax[j].plot(
                                    self.x_list[i][j][2][k].to_numpy(),
                                    lin_reg.predict(X_poly),
                                    color=self.y_list_main[i][j][4][k],
                                    # linestyle='--',
                                    linestyle=best_fit_linestyle,
                                    linewidth=best_fit_linewidth,
                                    path_effects=[pe.Stroke(linewidth=best_fit_background_linewidth, foreground='0'), pe.Normal()],
                                    zorder=1
                                )

                        ax[j].set_ylim((0, self.max_value))
                        ax[j].set_xlim((0, self.max_value))

                    else:
                        # ax[i, j].set_title(f'{self.rows[i]} / {self.cols[j]}')
                        ax[i, j].grid(True, linestyle='-.')
                        ax[i, j].tick_params(axis='both',
                                             grid_color='black',
                                             grid_alpha=0.5)
                        ax[i, j].set_facecolor(set_facecolor)
                        ax[i, j].add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[i, j].add_artist((lines.Line2D(
                            [0, self.max_value / 2], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[i, j].add_artist((lines.Line2D(
                            [0, self.max_value / 4], [0, self.max_value],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[i, j].add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value / 2],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))
                        ax[i, j].add_artist((lines.Line2D(
                            [0, self.max_value], [0, self.max_value / 4],
                            dashes=(2, 2, 2, 2),
                            linewidth=1,
                            color='gray'
                        )))

                        for k in range(len(self.x_list[i][j][2])):
                            if i == 0 and j == 0:
                                ax[i, j].scatter(
                                    self.x_list[i][j][2][k],
                                    self.y_list_main[i][j][2][k],
                                    c=self.y_list_main[i][j][4][k],
                                    s=markersize,
                                    marker='o',
                                    alpha=0.5,
                                    label=self.y_list_main[i][j][3][k]
                                )
                                # if len(self.adap_vs_stat_data_y_sec) > 0:
                                #     ax[i, j].twinx().scatter(
                                #         self.x_list[i][j][2][k],
                                #         self.y_list_sec[i][j][2][k],
                                #         c=self.y_list_sec[i][j][4][k],
                                #         s=markersize,
                                #         marker='o',
                                #         alpha=0.5,
                                #         label=self.y_list_main[i][j][3][k]
                                #     )
                            else:
                                ax[i, j].scatter(
                                    self.x_list[i][j][2][k],
                                    self.y_list_main[i][j][2][k],
                                    c=self.y_list_main[i][j][4][k],
                                    s=markersize,
                                    marker='o',
                                    alpha=0.5,
                                )
                                # if len(self.adap_vs_stat_data_y_sec) > 0:
                                #     ax[i, j].twinx().scatter(
                                #         self.x_list[i][j][2][k],
                                #         self.y_list_sec[i][j][2][k],
                                #         c=self.y_list_sec[i][j][4][k],
                                #         s=markersize,
                                #         marker='o',
                                #         alpha=0.5,
                                #         label=self.y_list_main[i][j][3][k]
                                #     )
                            if self.y_list_main[i][j][5][k] > 0:
                                poly_features = PolynomialFeatures(degree=self.y_list_main[i][j][5][k], include_bias=False)
                                X_poly = poly_features.fit_transform(self.x_list[i][j][2][k].to_numpy())
                                lin_reg = LinearRegression()
                                lin_reg.fit(X_poly, self.y_list_main[i][j][2][k].to_numpy())
                                ax[i, j].plot(
                                    self.x_list[i][j][2][k].to_numpy(),
                                    lin_reg.predict(X_poly),
                                    color=self.y_list_main[i][j][4][k],
                                    # linestyle='--',
                                    linestyle=best_fit_linestyle,
                                    linewidth=best_fit_linewidth,
                                    path_effects=[pe.Stroke(linewidth=best_fit_background_linewidth, foreground='0'), pe.Normal()],
                                    zorder=1
                                )
                        ax[i, j].set_ylim((0, self.max_value))
                        ax[i, j].set_xlim((0, self.max_value))

            if len(self.rows) == 1:
                if len(self.cols) == 1:
                    ax.set_aspect('equal',
                                  # adjustable='box',
                                  'box',
                                  share=True)
                    for i in range(len(self.rows)):
                        if self.rename_rows == 'y':
                        # if self.rows_new_names is not None:
                            ax.set_ylabel(self.rows_new_names[i], rotation=90, size='large')
                        else:
                            ax.set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        if self.rename_cols == 'y':
                        # if self.cols_new_names is not None:
                            ax.set_title(self.cols_new_names[j])
                        else:
                            ax.set_title(self.cols[j])

            if len(self.rows) > 1:
                if len(self.cols) == 1:
                    ax[0].set_aspect('equal',
                                     'box',
                                     # adjustable='box',
                                     share=True)
                    for i in range(len(self.rows)):
                        if self.rename_rows == 'y':
                        # if self.rows_new_names is not None:
                            ax[i].set_ylabel(self.rows_new_names[i], rotation=90, size='large')
                        else:
                            ax[i].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        if self.rename_cols == 'y':
                        # if self.cols_new_names is not None:
                            ax[0].set_title(self.cols_new_names[j])
                        else:
                            ax[0].set_title(self.cols[j])
                else:
                    ax[0, 0].set_aspect('equal',
                                        # adjustable='box',
                                        share=True)
                    for i in range(len(self.rows)):
                        if self.rename_rows == 'y':
                        # if self.rows_new_names is not None:
                            ax[i, 0].set_ylabel(self.rows_new_names[i], rotation=90, size='large')
                        else:
                            ax[i, 0].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        if self.rename_cols == 'y':
                        # if self.cols_new_names is not None:
                            ax[0, j].set_title(self.cols_new_names[j])
                        else:
                            ax[0, j].set_title(self.cols[j])

            supx = fig.supxlabel(supxlabel)
            supy = fig.supylabel(supylabel)

            leg = fig.legend(
                bbox_to_anchor=(0.5, 0),
                loc='upper center',
                fontsize='large'
                # borderaxespad=0.1,
            )

            for i in range(len(leg.legendHandles)):
                leg.legendHandles[i]._sizes = [30]

            # plt.subplots_adjust(
            #     # bottom=0.2,
            #     left=0.05
            # )

            # plt.tight_layout()

            plt.savefig(figname + '.png',
                        dpi=dpi,
                        format='png',
                        bbox_extra_artists=(leg, supx, supy),
                        bbox_inches='tight'
                        )

    def time_plot(
            self,
            vars_to_gather_cols: list = None,
            vars_to_gather_rows: list = None,
            detailed_cols: list = None,
            detailed_rows: list = None,
            custom_cols_order: list = None,
            custom_rows_order: list = None,
            data_on_y_main_axis: list = None,
            data_on_y_sec_axis: list = None,
            colorlist_y_main_axis: list = None,
            colorlist_y_sec_axis: list = None,
            rows_renaming_dict: dict = None,
            cols_renaming_dict: dict = None,

            sharex: bool = True,
            sharey: bool = True,
            figname: str = None,
            figsize: float = 1,
            ratio_height_to_width: float = 1,
            dpi: int = 500,
            confirm_graph: bool = False,
            set_facecolor: any = (0, 0, 0, 0.10)
    ):
        """
        Used to plot a timeplot.

        :param vars_to_gather_cols: A list of strings.
            The list should be the variables you want to show in subplot columns.
        :type vars_to_gather_cols: list
        :param vars_to_gather_rows: A list of strings.
            The list should be the variables you want to show in subplot rows.
        :type vars_to_gather_rows: list
        :param detailed_cols: A list of strings.
            The list should be the specific data you want to show in subplots columns.
            Used to filter.
        :type detailed_cols: list
        :param detailed_rows: A list of strings.
            The list should be the specific data you want to show in subplots rows.
            Used to filter.
        :type detailed_rows: list
        :param custom_cols_order: A list of strings.
            The list should be the specific order for the items shown in subplot columns.
        :type custom_cols_order: list
        :param custom_rows_order: A list of strings.
            The list should be the specific order for the items shown in subplot rows.
        :type custom_rows_order: list
        :param data_on_y_main_axis: A list with nested lists and strings.
            Used to select the data you want to show in the scatter plot main y-axis.
            It needs to follow this structure:
            [['name_on_y_main_axis', [list of column names you want to plot]]]
        :type data_on_y_main_axis: list
        :param data_on_y_sec_axis: A list with nested lists and strings.
            Used to select the data you want to show in the scatter plot secondary y-axis.
            It needs to follow this structure:
            [[['name_on_1st_y_sec_axis', [list of column names you want to plot]], ['name_on_2nd_y_sec_axis', [list of column names you want to plot]], etc]
        :type data_on_y_sec_axis: list
        :param colorlist_y_main_axis: A list with nested lists and strings.
            It should follow the same structure as data_on_y_main_axis,
            but replacing the column names with the colors using the matplotlib notation.
        :type colorlist_y_main_axis: list
        :param colorlist_y_sec_axis: A list with nested lists and strings.
            It should follow the same structure as data_on_y_sec_axis,
            but replacing the column names with the colors using the matplotlib notation.
        :type colorlist_y_sec_axis: list
        :param rows_renaming_dict: A dictionary. Should follow the pattern
            {'old row name 1': 'new row name 1', 'old row name 2': 'new row name 2'}
        :type rows_renaming_dict: dict
        :param cols_renaming_dict: A dictionary. Should follow the pattern
            {'old col name 1': 'new col name 1', 'old col name 2': 'new col name 2'}
        :type cols_renaming_dict: dict
        :param sharey: True to share the x-axis across all subplots
        :type sharey: bool
        :param sharex: True to share the y-axis across all subplots
        :type sharex: bool
        :param figname: A string. The name of the saved figure without extension.
        :type figname: str
        :param figsize: A float. It is the figure size.
        :type figsize: float
        :param ratio_height_to_width: A float. By default, is 1 (squared). If 0.5 is entered, the figure will be half higher than wide.
        :type ratio_height_to_width: float
        :param dpi: An integer. The number of dpis for image quality.
        :type dpi: int
        :param confirm_graph: A bool. True to skip confirmation step.
        :type confirm_graph: bool
        :param set_facecolor: Usage is similar to matplotlib.axes.Axes.set_facecolor
        :type set_facecolor: any
        """
        import numpy as np
        import matplotlib.pyplot as plt
        import pandas as pd
        import datetime
        import matplotlib.dates as mdates

        self.generate_fig_data(
            vars_to_gather_cols=vars_to_gather_cols,
            vars_to_gather_rows=vars_to_gather_rows,
            detailed_cols=detailed_cols,
            detailed_rows=detailed_rows,
            custom_cols_order=custom_cols_order,
            custom_rows_order=custom_rows_order,
            data_on_y_main_axis=data_on_y_main_axis,
            data_on_y_sec_axis=data_on_y_sec_axis,
            data_on_x_axis='anything',
            colorlist_y_main_axis=colorlist_y_main_axis,
            colorlist_y_sec_axis=colorlist_y_sec_axis,
            rows_renaming_dict=rows_renaming_dict,
            cols_renaming_dict=cols_renaming_dict,
        )

        # print(f'The number of self.rows and the list of these is going to be:')
        # print(f'No. of self.rows = {len(self.rows)}')
        # print(f'List of self.rows:')
        # print(*self.rows, sep='\n')
        #
        # print(f'The number of columns and the list of these is going to be:')
        # print(f'No. of columns = {len(self.cols)}')
        # print(f'List of columns:')
        # print(*self.cols, sep='\n')

        if confirm_graph is False:
            proceed = input('Do you want to proceed? [y/n]:')
            if 'y' in proceed:
                confirm_graph = True
            elif 'n' in proceed:
                confirm_graph = False

        if confirm_graph:
            self.df_for_graph['Date/time'] = self.df_for_graph.index

            freq_graph_dict = {
                'timestep': ['X?', "%d/%m %H:%M"],
                'hourly': ['H', " %d/%m %H:%M:%S"],
                # 'daily': ['D', "%d/%m"],
                'daily': ['D', " %d/%m %H:%M:%S"],
                # 'monthly': ['M', "%m"],
                'monthly': ['M', " %d/%m %H:%M:%S"],
                # todo WIP
                'runperiod': ['?', "?"]
            }

            start_date = datetime.datetime.strptime(self.df_for_graph['Date/time'][0], freq_graph_dict[self.frequency][1])
            # end_date = datetime.datetime.strptime(df_for_graph['Date/time'][len(self.df_for_graph)-1], "%d/%m %H:%M")
            # (end_date-start_date).days

            self.df_for_graph['Date/time'] = pd.date_range(
                start=start_date,
                periods=len(self.df_for_graph),
                # '2017-31-12 23:00',
                freq=freq_graph_dict[self.frequency][0]
            )

            self.df_for_graph['Date/time'] = pd.to_datetime(self.df_for_graph['Date/time'])

            fig, ax = plt.subplots(nrows=len(self.rows),
                                   ncols=len(self.cols),
                                   sharex=sharex,
                                   sharey=sharey,
                                   constrained_layout=True,
                                   figsize=(figsize * len(self.cols), ratio_height_to_width * figsize * len(self.rows)))

            main_y_axis = []
            sec_y_axis = []

            for i in range(len(self.rows)):
                main_y_axis_temp_rows = []
                sec_y_axis_temp_rows = []
                for j in range(len(self.cols)):

                    current_axis = plt.gca()
                    current_axis.xaxis.set_major_formatter(mdates.DateFormatter(freq_graph_dict[self.frequency][1]))
                    current_axis.xaxis.set_major_locator(mdates.MonthLocator())

                    main_y_axis_temp_cols = []
                    sec_y_axis_temp_cols = []

                    if len(self.rows) == 1 and len(self.cols) == 1:
                        for k in range(len(self.data_on_y_main_axis)):
                            main_y_axis_temp_cols.append(ax)
                        main_y_axis_temp_rows.append(main_y_axis_temp_cols)
                        if len(self.data_on_y_sec_axis) > 0:
                            for k in range(len(self.data_on_y_sec_axis)):
                                sec_y_axis_temp_cols.append(ax.twinx())
                            sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
                    elif len(self.cols) == 1 and len(self.rows) > 1:
                        for k in range(len(self.data_on_y_main_axis)):
                            main_y_axis_temp_cols.append(ax[i])
                        main_y_axis_temp_rows.append(main_y_axis_temp_cols)
                        if len(self.data_on_y_sec_axis) > 0:
                            for k in range(len(self.data_on_y_sec_axis)):
                                sec_y_axis_temp_cols.append(ax[i].twinx())
                            sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
                    elif len(self.cols) > 1 and len(self.rows) == 1:
                        for k in range(len(self.data_on_y_main_axis)):
                            main_y_axis_temp_cols.append(ax[j])
                        main_y_axis_temp_rows.append(main_y_axis_temp_cols)
                        if len(self.data_on_y_sec_axis) > 0:
                            for k in range(len(self.data_on_y_sec_axis)):
                                sec_y_axis_temp_cols.append(ax[j].twinx())
                            sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
                    else:
                        for k in range(len(self.data_on_y_main_axis)):
                            main_y_axis_temp_cols.append(ax[i, j])
                        main_y_axis_temp_rows.append(main_y_axis_temp_cols)
                        if len(self.data_on_y_sec_axis) > 0:
                            for k in range(len(self.data_on_y_sec_axis)):
                                sec_y_axis_temp_cols.append(ax[i, j].twinx())
                            sec_y_axis_temp_rows.append(sec_y_axis_temp_cols)
                main_y_axis.append(main_y_axis_temp_rows)
                sec_y_axis.append(sec_y_axis_temp_rows)

            for i in range(len(self.rows)):
                for j in range(len(self.cols)):

                    for k in range(len(self.y_list_main[i][j])):

                        main_y_axis[i][j][k].xaxis.set_major_formatter(
                            mdates.DateFormatter(freq_graph_dict[self.frequency][1]))
                        main_y_axis[i][j][k].xaxis.set_major_locator(mdates.MonthLocator())

                        main_y_axis[i][j][k].grid(True, linestyle='-.')
                        main_y_axis[i][j][k].tick_params(axis='both',
                                                         grid_color='black',
                                                         grid_alpha=0.5)
                        main_y_axis[i][j][k].set_facecolor(set_facecolor)

                        for x in range(len(self.y_list_main[i][j][k]['dataframe'])):
                            if 'Setpoint Temperature' in self.y_list_main[i][j][k]['label'][x]:
                                zord = 1
                            else:
                                zord = 0
                            if i == 0 and j == 0:
                                main_y_axis[i][j][k].plot(
                                    self.df_for_graph['Date/time'],
                                    self.y_list_main[i][j][k]['dataframe'][x],
                                    linewidth=1,
                                    c=self.y_list_main[i][j][k]['color'][x],
                                    # ms=markersize,
                                    # marker='o',
                                    # alpha=0.5,
                                    label=self.y_list_main[i][j][k]['label'][x],
                                    zorder=zord,
                                )
                            else:
                                main_y_axis[i][j][k].plot(
                                    self.df_for_graph['Date/time'],
                                    self.y_list_main[i][j][k]['dataframe'][x],
                                    linewidth=1,
                                    c=self.y_list_main[i][j][k]['color'][x],
                                    # ms=markersize,
                                    # marker='o',
                                    # alpha=0.5,
                                    zorder=zord,
                                )

            for i in range(len(self.rows)):
                for j in range(len(self.cols)):
                    for k in range(len(self.y_list_sec[i][j])):
                        sec_y_axis[0][0][k].get_shared_y_axes().join(sec_y_axis[0][0][k], sec_y_axis[i][j][k])
                        if len(self.data_on_y_sec_axis) > 1:
                            if len(self.y_list_sec[i][j]) >= 1:
                                if j < (len(self.cols) - 1):
                                    # sec_y_axis[i][j][k].set_yticklabels([])
                                    sec_y_axis[i][j][k].set_yticks([], [])
                                if j == (len(self.cols) - 1):
                                    sec_y_axis[i][j][k].set_ylabel(self.data_on_y_sec_axis[k][0])
                                    sec_y_axis[i][j][k].spines["right"].set_position(("axes", 1 + k * 0.15))
                                    sec_y_axis[i][j][k].spines["right"].set_visible(True)
                        for x in range(len(self.y_list_sec[i][j][k]['dataframe'])):
                            if 'Setpoint Temperature' in self.y_list_sec[i][j][k]['label'][x]:
                                zord = 1
                            else:
                                zord = 0
                            if i == 0 and j == 0:
                                sec_y_axis[i][j][k].plot(
                                    self.df_for_graph['Date/time'],
                                    self.y_list_sec[i][j][k]['dataframe'][x],
                                    linewidth=1,
                                    c=self.y_list_sec[i][j][k]['color'][x],
                                    # ms=markersize,
                                    # marker='o',
                                    # alpha=0.5,
                                    label=self.y_list_sec[i][j][k]['label'][x],
                                    zorder=zord,
                                )
                            else:
                                sec_y_axis[i][j][k].plot(
                                    self.df_for_graph['Date/time'],
                                    self.y_list_sec[i][j][k]['dataframe'][x],
                                    linewidth=1,
                                    c=self.y_list_sec[i][j][k]['color'][x],
                                    # ms=markersize,
                                    # marker='o',
                                    # alpha=0.5,
                                    zorder=zord,
                                )

            if len(self.rows) == 1:
                if len(self.cols) == 1:
                    for i in range(len(self.rows)):
                        if self.rename_rows == 'y':
                            ax.set_ylabel(self.rows_new_names[i], rotation=90, size='large')
                        else:
                            ax.set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        if self.rename_rows == 'y':
                            ax.set_title(self.cols_new_names[j])
                        else:
                            ax.set_title(self.cols[j])

            if len(self.rows) > 1:
                if len(self.cols) == 1:
                    for i in range(len(self.rows)):
                        if self.rename_rows == 'y':
                            ax[i].set_ylabel(self.rows_new_names[i], rotation=90, size='large')
                        else:
                            ax[i].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        if self.rename_rows == 'y':
                            ax[0].set_title(self.cols_new_names[j])
                        else:
                            ax[0].set_title(self.cols[j])
                else:
                    for i in range(len(self.rows)):
                        if self.rename_rows == 'y':
                            ax[i, 0].set_ylabel(self.rows_new_names[i], rotation=90, size='large')
                        else:
                            ax[i, 0].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        if self.rename_rows == 'y':
                            ax[0, j].set_title(self.cols_new_names[j])
                        else:
                            ax[0, j].set_title(self.cols[j])

            if len(self.rows) == 1:
                if len(self.cols) == 1:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                    for label in ax.get_xticklabels():
                        label.set(rotation=90, horizontalalignment='center')

            if len(self.rows) == 1 and len(self.cols) > 1:
                for j in range(len(self.cols)):
                    ax[j].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                    for label in ax[j].get_xticklabels():
                        label.set(rotation=90, horizontalalignment='center')

            if len(self.rows) > 1:
                if len(self.cols) == 1:
                    ax[len(self.rows) - 1].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                    for label in ax[len(self.rows) - 1].get_xticklabels():
                        label.set(rotation=90, horizontalalignment='center')
                else:
                    for j in range(len(self.cols)):
                        # ax[len(self.rows) - 1, j].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                        # for label in ax[len(self.rows) - 1, j].get_xticklabels():
                        #     label.set(rotation=90, horizontalalignment='center')
                        for i in range(len(self.rows)):
                            ax[i, j].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                            for label in ax[i, j].get_xticklabels():
                                label.set(rotation=90, horizontalalignment='center')

            # plt.xticks(rotation=70)

            supx = fig.supxlabel('Time')
            supy = fig.supylabel(self.data_on_y_main_axis[0][0])

            leg = fig.legend(
                bbox_to_anchor=(0.5, 0),
                loc='upper center',
                fontsize='large'
                # borderaxespad=0.1,
            )
            if len(self.data_on_y_sec_axis) == 1:
                rhstext = fig.text(1, 0.5, s=self.data_on_y_sec_axis[0][0], va='center', rotation='vertical', size='large')

            if len(self.data_on_y_sec_axis) == 1:
                bbox_extra_artists_tuple = (rhstext, leg, supx, supy)
            else:
                bbox_extra_artists_tuple = (leg, supx, supy)

            for i in range(len(leg.legendHandles)):
                leg.legendHandles[i]._sizes = [30]

            # plt.subplots_adjust(bottom=0.2)
            # plt.tight_layout()

            plt.savefig(figname + '.png',
                        dpi=dpi,
                        format='png',
                        bbox_extra_artists=bbox_extra_artists_tuple,
                        bbox_inches='tight')

            plt.show()
