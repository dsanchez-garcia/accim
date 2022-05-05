class rename_epw_files:
    def __init__(
        self,
        filelist=None,
        confirm_renaming=None,
        confirm_deletion=None
    ):
        import glob
        import pandas as pd
        import datapackage
        import numpy as np
        import os
        from geopy.geocoders import Nominatim
        import pycountry
        import shutil

        if filelist is None:
            filelist = []

        match_cities = True

        if len(filelist) > 0:
            epw_files_to_rename = filelist
        else:
            # todo same as Table
            epw_files_to_rename = glob.glob('*.epw', recursive=True)

        self.epw_df = pd.DataFrame(data=epw_files_to_rename,
                              index=list(range(len(epw_files_to_rename))),
                              columns=['EPW_file_names'])

        for i in range(len(self.epw_df)):
            self.epw_df.loc[i, 'EPW_abs_path'] = os.path.abspath(self.epw_df.loc[i, 'EPW_file_names'])

        self.epw_df['EPW_names'] = self.epw_df['EPW_file_names'].str.replace('.epw', '')

        rcpdict = {
            'Present': ['Presente', 'Actual', 'Present', 'Current'],
            'RCP26': ['RCP2.6', 'RCP26'],
            'RCP45': ['RCP4.5', 'RCP45'],
            'RCP60': ['RCP6.0', 'RCP60'],
            'RCP85': ['RCP8.5', 'RCP85']
        }

        for i in range(len(self.epw_df['EPW_names'])):
            for j in rcpdict:
                for k in rcpdict[j]:
                    if k.lower() in self.epw_df.loc[i, 'EPW_names'].lower():
                        self.epw_df.loc[i, 'EPW_scenario'] = j

        rcp_not_found_list = []

        for i in range(len(self.epw_df['EPW_names'])):
            try:
                if type(self.epw_df.loc[i, 'EPW_scenario']) is float:
                    self.epw_df.loc[i, 'EPW_scenario'] = 'Present'
                    rcp_not_found_list.append(self.epw_df.loc[i, 'EPW_file_names'])
            except KeyError:
                self.epw_df.loc[i, 'EPW_scenario'] = 'Present'
                rcp_not_found_list.append(self.epw_df.loc[i, 'EPW_file_names'])

        if len(rcp_not_found_list) > 0:
            print('Since no match has been found between scenarios and EPW file name, '
                  'Present scenario has been assigned to the following EPW files:')
            print(*rcp_not_found_list, sep='\n')

        for i in range(len(self.epw_df['EPW_names'])):
            for j in range(2000, 2101, 1):
                if str(j) in self.epw_df.loc[i, 'EPW_names']:
                    self.epw_df.loc[i, 'EPW_year'] = str(j)

        for i in range(len(self.epw_df['EPW_names'])):
            if self.epw_df.loc[i, 'EPW_scenario'] == 'Present':
                self.epw_df.loc[i, 'EPW_scenario_year'] = 'Present'
            else:
                self.epw_df.loc[i, 'EPW_scenario_year'] = self.epw_df.loc[i, 'EPW_scenario'] + '-' + self.epw_df.loc[i, 'EPW_year']

        year_not_found_list = []
        for i in range(len(self.epw_df['EPW_names'])):
            try:
                if type(self.epw_df.loc[i, 'EPW_year']) is float:
                    self.epw_df.loc[i, 'EPW_year'] = 'Present'
                    year_not_found_list.append(self.epw_df.loc[i, 'EPW_file_names'])
            except KeyError:
                self.epw_df.loc[i, 'EPW_year'] = 'Present'
                year_not_found_list.append(self.epw_df.loc[i, 'EPW_file_names'])
        if len(year_not_found_list) > 0:
            print('Since no match has been found between scenarios and EPW file name, '
                  'Present year has been assigned to the following EPW files:')
            print(*year_not_found_list, sep='\n')

        # path = r'C:\Users\user\PycharmProjects\accim'
        path = os.getcwd()
        new_list = []
        for fle in epw_files_to_rename:
            # open the file and then call .read() to get the text
            with open(
                    os.path.join(path, fle),
                    "rb") as f:
                text = f.readline()
                new_list.append([str(text).split(',')])
            # f.close()

        for i in range(len(new_list)):
            self.epw_df.loc[i, 'EPW_latitude'] = new_list[i][0][6]
            self.epw_df.loc[i, 'EPW_longitude'] = new_list[i][0][7]

        geolocator = Nominatim(user_agent="geoapiExercises")
        for i in range(len(self.epw_df)):
            location = geolocator.reverse(self.epw_df.loc[i, 'EPW_latitude'] + "," + self.epw_df.loc[i, 'EPW_longitude'])
            # print(location)
            self.epw_df.loc[i, 'EPW_country_code'] = location.raw['address'].get('country_code').upper()
            # self.epw_df.loc[i, 'EPW_city'] = location.raw['address'].get('city', '')

        self.epw_df['EPW_mod'] = self.epw_df['EPW_names'].str.replace('-', '_').str.replace('.', '_').str.split('_')

        isEPWformatValid = False
        if match_cities:
            package_cities = datapackage.Package('https://datahub.io/core/world-cities/datapackage.json')

            # to load only tabular data_cities
            resources_cities = package_cities.resources
            for resource in resources_cities:
                if resource.tabular:
                    data_cities = pd.read_csv(resource.descriptor['path'])

            self.epw_df = self.epw_df.set_index([pd.RangeIndex(len(self.epw_df))])

            #  if len <1
            data_cities['subcountry'] = data_cities['subcountry'].astype(str)

            rcp = []
            for i in rcpdict:
                for j in range(len(rcpdict[i])):
                    rcp.append(rcpdict[i][j])

            locations = []
            for i in list(self.epw_df['EPW_mod']):
                for j in i:
                    if j in rcp:
                        continue
                    elif j.isnumeric():
                        continue
                    elif len(j) <= 2:
                        continue
                    else:
                        locations.append(j.lower())
            locations = list(dict.fromkeys(locations))

            data_temp_city = []
            for i in list(data_cities['name']):
                data_temp_city.append(i.lower())

            data_temp_subcountry = []
            for i in list(data_cities['subcountry']):
                data_temp_subcountry.append(i.lower())

            matches_city = list(set(locations).intersection(set(data_temp_city)))
            matches_subcountry = list(set(locations).intersection(data_temp_subcountry))
            # matches_city = list(set(locations).intersection(set(data_cities['name'].str.lower())))
            # matches_subcountry = list(set(locations).intersection(data_cities['subcountry'].str.lower()))
            matches = matches_subcountry + matches_city
            matches = list(dict.fromkeys(matches))

            cities_df_list = []

            try:
                for i in matches:
                    temp_df = data_cities.query('name.str.lower() == "%s"' % i.lower())
                    if len(temp_df) == 0:
                        temp_df = data_cities.query('subcountry.str.lower() == "%s"' % i.lower())
                    cities_df_list.append(temp_df)
                self.location_matches_df = pd.concat(cities_df_list)
                self.location_matches_df = self.location_matches_df.set_index([pd.RangeIndex(len(self.location_matches_df))])
                self.location_matches_df['country'] = self.location_matches_df['country'].astype(str)
                isEPWformatValid = True
            except ValueError:
                isEPWformatValid = False
                print('EPW files are not correctly named')

            # self.epw_df['EPW_CountryCode'] = self.epw_df['EPW_CountryCode'].astype(str)

        for i in range(len(self.epw_df['EPW_mod'])):
            for j in self.epw_df.loc[i, 'EPW_mod']:
                if j.lower() in [k.lower() for k in self.location_matches_df['name']]:
                    self.epw_df.loc[i, 'EPW_City_or_subcountry'] = j.replace(' ', '-').capitalize()
            self.epw_df.loc[i, 'EPW_country'] = pycountry.countries.get(alpha_2=self.epw_df.loc[i, 'EPW_country_code']).name.replace(' ', '-')

        for i in range(len(self.epw_df['EPW_mod'])):
            if type(self.epw_df.loc[i, 'EPW_City_or_subcountry']) is float:
                location = geolocator.reverse(self.epw_df.loc[i, 'EPW_latitude'] + "," + self.epw_df.loc[i, 'EPW_longitude'])
                try:
                    self.epw_df.loc[i, 'EPW_City_or_subcountry'] = location.raw['address'].get('city').replace(' ', '-').capitalize()
                except AttributeError:
                    self.epw_df.loc[i, 'EPW_City_or_subcountry'] = location.raw['address'].get('city').capitalize()

        for col in ['EPW_country', 'EPW_City_or_subcountry', 'EPW_scenario_year']:
            for row in range(len(self.epw_df)):
                if self.epw_df.loc[row, col] is None:
                    self.epw_df.loc[row, col] = 'UNKNOWN'

        self.epw_df['EPW_new_names'] = self.epw_df[['EPW_country', 'EPW_City_or_subcountry', 'EPW_scenario_year']].agg('_'.join, axis=1)

        print('The previous names of the EPW files are:')
        print(*list(self.epw_df['EPW_names']), sep='\n')
        print('And the new names of the EPW files are going to be:')
        print(*list(self.epw_df['EPW_new_names']), sep='\n')

        if confirm_renaming is None:
            proceed = input('Do you want to rename the file or files? [y/n]:')
            if 'y' in proceed:
                confirm_renaming = True
            elif 'n' in proceed:
                confirm_renaming = False

        if confirm_renaming:
            for i in range(len(self.epw_df)):
                shutil.copy(self.epw_df.loc[i, 'EPW_abs_path'], path + '/' + self.epw_df.loc[i, 'EPW_new_names'] + '.epw')

        if confirm_deletion is None:
            proceed = input('Do you want to delete the original EPW file or files? [y/n]:')
            if 'y' in proceed:
                confirm_deletion = True
            elif 'n' in proceed:
                confirm_deletion = False

        if confirm_deletion:
            for i in epw_files_to_rename:
                os.remove(i)


class Table:

    def __init__(self,
                 datasets: list = None,
                 source_concatenated_csv_filepath: str = None,
                 frequency: str = None,
                 sum_or_mean: str = None,
                 standard_outputs: bool = None,
                 level: list = None,
                 level_sum_or_mean: list = None,
                 match_cities: bool = False,
                 manage_epw_names: bool = False,
                 split_epw_names: bool = False,
                 normalised_energy_units: bool = True,
                 rename_cols: bool = True,
                 energy_units_in_kwh: bool = True,
                 concatenated_csv_name: str = None
                 ):
        """
        Generates a table or dataframe using the EnergyPlus simulation results CSV files
        available in the current folder.

        :param frequency: A list of strings.
        Strings can be 'timestep', 'hourly', 'daily', 'monthly' and/or 'runperiod'.
        :param sum_or_mean: A string. Can be 'sum' or 'mean'.
        Aggregates the rows based on the defined frequency by sum or mean.
        :param standard_outputs: A bool, can be True or False.
        Used to consider only standard outputs from accim.
        :param level: A list of strings. Strings can be 'block' and/or 'building'.
        Used to create columns with block or building values.
        :param level_sum_or_mean: A list of strings. Strings can be 'sum' and/or 'mean'.
        Used to create the columns for levels preciously stated by summing and/or averaging.
        :param match_cities: A bool, can be True or False.
        Used to try to match the cities in the EPW file name with actual cities.
        :param manage_epw_names: A bool, can be True or False.
        Used to detect climate change scenario, country and sub-country codes and city.
        If a large number of CSVs is going to be computed
        or hourly values are going to be considered, it is recommended to be False.
        :param normalised_energy_units: A bool, can be True or False.
        Used to show Wh or Wh/m2 units.
        :param rename_cols: A bool, can be True or False.
        Used to keep the original name of EnergyPlus outputs or rename them for understanding
        purposes.
        :param energy_units_in_kwh: A bool, can be True or False. If True, energy units will be in kWh or kWh/m2,
        otherwise these will be in Wh or Wh/m2.
        :param concatenated_csv_name: A string used as the name for the concatenated csv file.


        """
        if datasets is None:
            datasets = []
        if level_sum_or_mean is None:
            level_sum_or_mean = []
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

        # Step: generating concatenated dataframe.
        # If source_concatenated_csv_filepath is None, then specified csv files on list format
        # are considered, otherwise all csv in the folder are considered.
        # If source_concatenated_csv_filepath is not None, then the csv path is considered to
        # build the dataframe.
        if source_concatenated_csv_filepath is None:
            if len(datasets) > 0:
                source_files = datasets
            else:
                allfiles = glob.glob('*.csv', recursive=True)
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
                'Date/Time',
                'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)',
                'Environment:Site Wind Speed [m/s](Hourly)',
                'Environment:Site Outdoor Air Relative Humidity [%](Hourly)',
                'EMS:Comfort Temperature [C](Hourly)',
                'EMS:Adaptive Cooling Setpoint Temperature [C](Hourly)',
                'EMS:Adaptive Heating Setpoint Temperature [C](Hourly)',
                'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance [C](Hourly)',
                'EMS:Adaptive Heating Setpoint Temperature_No Tolerance [C](Hourly)',
                'EMS:Ventilation Setpoint Temperature [C](Hourly)',
                'EMS:Minimum Outdoor Temperature for ventilation [C](Hourly)',
                'EMS:Comfortable Hours_No Applicability',
                'EMS:Comfortable Hours_Applicability',
                'EMS:Discomfortable Applicable Hot Hours',
                'EMS:Discomfortable Applicable Cold Hours',
                'EMS:Discomfortable Non Applicable Hot Hours',
                'EMS:Discomfortable Non Applicable Cold Hours',
                'EMS:Ventilation Hours',
                'AFN Zone Infiltration Volume [m3](Hourly)',
                'AFN Zone Infiltration Air Change Rate [ach](Hourly)',
                # 'Zone Thermostat Operative Temperature [C](Hourly)',
                'Zone Operative Temperature [C](Hourly)',
                'Zone Operative Temperature',
                'Whole Building:Facility Total HVAC Electricity Demand Rate [W](Hourly)',
                'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)',
                'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)',
                'FORSCRIPT',
                'VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate [W](Hourly)',
                'VRF INDOOR UNIT DX HEATING COIL:Heating Coil Heating Rate [W](Hourly)',
                # 'VRF OUTDOOR UNIT',
                'VRF Heat Pump Cooling Electricity Rate',
                'VRF Heat Pump Heating Electricity Rate',
                'VRF Heat Pump Cooling Electricity Energy',
                'VRF Heat Pump Heating Electricity Energy',
                'Heating Coil Heating Rate [W](Hourly)',
                'Cooling Coil Total Cooling Rate [W](Hourly)',
                'Zone Air Volume',
                'Zone Floor Area',
                'Zone Thermal Comfort Fanger Model PMV',
                'Zone Thermal Comfort Fanger Model PPD'
            ]

            summed_dataframes = []

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
                                keeplist.append(j)
                    keeplist = list(dict.fromkeys(keeplist))
                    droplist = list(set(df.columns) - set(keeplist))
                    df = df.drop(droplist, axis=1)

                # df['Source'] = file.name
                df['Source'] = file

                # df['Date/Time_orig'] = df['Date/Time'].copy()

                df[['TBD1', 'Month/Day', 'TBD2', 'Hour']] = df['Date/Time'].str.split(' ', expand=True)
                df = df.drop(['TBD1', 'TBD2'], axis=1)
                df[['Month', 'Day']] = df['Month/Day'].str.split('/', expand=True)
                df[['Hour', 'Minute', 'Second']] = df['Hour'].str.split(':', expand=True)


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

                minute_df_len = len(
                    df[
                        (df['Minute'] != '00') &
                        (df['Minute'].astype(str) != 'None') &
                        (df['Minute'] != '')
                        ]
                )

                agg_dict = {}
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

                for i in aggregation_list_first:
                    agg_dict.update({i: 'first'})

                df['count'] = 1
                agg_dict.update({'count': 'count'})

                aggregation_list_mean = [
                    'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)',
                    'Environment:Site Wind Speed [m/s](Hourly)',
                    'Environment:Site Outdoor Air Relative Humidity [%](Hourly)',
                    'EMS:Comfort Temperature [C](Hourly)',
                    'EMS:Adaptive Cooling Setpoint Temperature [C](Hourly)',
                    'EMS:Adaptive Heating Setpoint Temperature [C](Hourly)',
                    'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance [C](Hourly)',
                    'EMS:Adaptive Heating Setpoint Temperature_No Tolerance [C](Hourly)',
                    'EMS:Ventilation Setpoint Temperature [C](Hourly)',
                    'EMS:Minimum Outdoor Temperature for ventilation [C](Hourly)',
                    # 'Zone Thermostat Operative Temperature [C](Hourly)',
                    'Zone Operative Temperature [C](Hourly)',
                    'Zone Operative Temperature',
                    'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)',
                    'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)',
                    'Zone Thermal Comfort Fanger Model PMV',
                    'Zone Thermal Comfort Fanger Model PPD'
                ]

                for i in df.columns:
                    for j in aggregation_list_mean:
                        if j in i:
                            agg_dict.update({i: 'mean'})

                for i in df.columns:
                    if i not in agg_dict:
                        agg_dict.update({i: sum_or_mean})

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

            df = pd.concat(summed_dataframes)

        else:
            # todo amend order of columns
            df = pd.read_csv(filepath_or_buffer=source_concatenated_csv_filepath)
            df = df.drop(columns=df.columns[0])
            for i in source_concatenated_csv_filepath.split('['):
                if i.startswith('freq'):
                    frequency = i.split('-')[1]
                    self.frequency = frequency
                elif i.startswith('sum_or_mean'):
                    sum_or_mean = i.split('-')[1]
                elif i.startswith('standard_outputs'):
                    standard_outputs = i.split('-')[1]
            cols = df.columns.tolist()
            cols = cols[-1:] + cols[:-1]
            df = df[cols]

        # Step: checking for NaNs and not correct aggregations based on count
        is_NaN = df.isna()
        row_has_NaN = is_NaN.any(axis=1)
        rows_with_NaN = df[row_has_NaN]
        if len(rows_with_NaN) > 0:
            print('The following rows have NaN values:')
            print(rows_with_NaN)

        if self.frequency == 'hourly':
            not_correct_agg = df[df['count'] != 1]
            if len(not_correct_agg) > 0:
                print('The following rows have not been correctly aggregated:')
                print(not_correct_agg)

        if self.frequency == 'daily':
            not_correct_agg = df[df['count'] != 24]
            if len(not_correct_agg) > 0:
                print('The following rows have not been correctly aggregated:')
                print(not_correct_agg)

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

            not_correct_agg = df[
                (df['count'] != 28 * 24) &
                (df['count'] != 30 * 24) &
                (df['count'] != 31 * 24)
                ]
            if len(not_correct_agg) > 0:
                print('The following rows have not been correctly aggregated:')
                print(not_correct_agg)

        if self.frequency == 'runperiod':
            not_correct_agg = df[df['count'] != 8760]
            if len(not_correct_agg) > 0:
                print('The following rows have not been correctly aggregated:')
                print(not_correct_agg)


        if concatenated_csv_name is not None:
            df.to_excel(
                f'{concatenated_csv_name}'
                f'[freq-{frequency}'
                f'[sum_or_mean-{sum_or_mean}'
                f'[standard_outputs-{standard_outputs}'
                f'[CSVconcatenated.xlsx'
            )
            df.to_csv(
                f'{concatenated_csv_name}'
                f'[freq-{frequency}'
                f'[sum_or_mean-{sum_or_mean}'
                f'[standard_outputs-{standard_outputs}'
                f'[CSVconcatenated.csv'
            )
            if len(rows_with_NaN) > 0:
                rows_with_NaN.to_csv(
                    f'{concatenated_csv_name}'
                    f'[freq-{frequency}'
                    f'[sum_or_mean-{sum_or_mean}'
                    f'[standard_outputs-{standard_outputs}'
                    f'[Rows_with_NaNs.csv'
                )
            if len(not_correct_agg) > 0:
                not_correct_agg.to_csv(
                    f'{concatenated_csv_name}'
                    f'[freq-{frequency}'
                    f'[sum_or_mean-{sum_or_mean}'
                    f'[standard_outputs-{standard_outputs}'
                    f'[Rows_not_corr_agg.csv'
                )
            return

        # if len(rows_with_NaN) > 0 or len(not_correct_agg) > 0:
            #     f = open(f'{concatenated_csv_name}[freq-{frequency}[sum_or_mean-{sum_or_mean}[standard_outputs-{standard_outputs}[Report.txt', "w+")
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
        occupied_zone_list = [i.split(' ')[0][:-5]
                        for i
                        in [i
                            for i
                            in df.columns
                            if
                            # 'Zone Operative Temperature [C](Hourly)'
                            'Zone Operative Temperature'
                            in i
                            ]
                        ]
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
        hvac_zone_list = [i.split(' ')[0]
                               for i
                               in [i
                                     for i
                                     in df.columns
                                     if 'Cooling Coil Total Cooling Rate' in i
                                     ]
                               ]

        hvac_zone_list = list(dict.fromkeys(hvac_zone_list))
        hvac_zone_list_underscore = [i.replace(':', '_') for i in hvac_zone_list]

        # Step: scanning blocks for block_list
        block_list = [i.split(':')[0] for i in occupied_zone_list]
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
                df[i] = df[i]/3600

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

        if any('block' in i for i in level):
            for output in outputdict:
                for block in block_list:
                    if any('sum' in j for j in level_sum_or_mean):
                        df[f'{block}' + '_Total_' + outputdict[output] + ' (summed)_pymod'] = df[
                            [i for i in df.columns if block.lower() in i.lower() and output in i and '_pymod' not in i]
                        ].sum(axis=1)
                    if any('mean' in j for j in level_sum_or_mean):
                        if 'Zone Air Volume' in output or 'Zone Floor Area' in output:
                            continue
                        else:
                            df[f'{block}' + '_Total_' + outputdict[output] + ' (mean)_pymod'] = df[
                                [i for i in df.columns
                                 if block.lower() in i.lower() and output in i and '_pymod' not in i]
                            ].mean(axis=1)
        if any('building' in i for i in level):
            for output in outputdict:
                if any('sum' in j for j in level_sum_or_mean):
                    df['Building_Total_' + outputdict[output] + ' (summed)_pymod'] = df[
                        [i for i in df.columns if output in i and '_pymod' not in i]
                    ].sum(axis=1)
                if any('mean' in j for j in level_sum_or_mean):
                    if 'Zone Air Volume' in output or 'Zone Floor Area' in output:
                        continue
                    else:
                        df['Building_Total_' + outputdict[output] + ' (mean)_pymod'] = df[
                            [i for i in df.columns
                             if output in i and '_pymod' not in i]
                        ].mean(axis=1)

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
                if '(Wh)' in i:
                    for j in hvac_zone_list:
                        if j in i:
                            df[i] = df[i] / df[
                                [i for i in df.columns
                                 if 'Zone Floor Area' in i
                                 and j.lower() in i.lower()
                                 # and j.replace(':', '_').lower() in i.lower()
                                 ][0]]
                    for k in block_list:
                        if k + '_Total_' in i:
                            df[i] = df[i] / df[
                                [i for i in df.columns
                                 if 'Zone Floor Area' in i
                                 and k.lower() + '_Total_'.lower() in i.lower()][0]]
                    if 'Building_Total_' in i:
                        df[i] = df[i] / df[
                            [i for i in df.columns
                             if 'Zone Floor Area' in i
                             and 'Building_Total_'.lower() in i.lower()][0]]
                    if any('building' in x for x in level):
                        if 'Whole Building:Facility Total HVAC Electricity Demand Rate' in i:
                            df[i] = df[i] / df[
                                [i for i in df.columns
                                 if 'Zone Floor Area' in i
                                 and 'Building_Total_'.lower() in i.lower()][0]]

        # df.to_excel('checkpoint_03-0.xlsx')

        # Step: converting Wh to kWh if requested
        if energy_units_in_kwh:
            for col in df.columns:
                if '(Wh)' in col:
                    df[col] = df[col] / 1000

        # df.to_excel('checkpoint_03-1.xlsx')

        energy_units_dict = {}
        for i in df.columns:
            if '(Wh)' in i:
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
        fixed_columns = [
            'Model',
            'Adaptive Standard',
            'Category',
            'Comfort mode',
            'HVAC mode',
            'Ventilation control',
            'VSToffset',
            'MinOToffset',
            'MaxWindSpeed',
            'ASTtol',
            'NameSuffix',
            'EPW'
        ]

        df[fixed_columns] = df['Source'].str.split('[', expand=True)

        df['Model'] = df['Model'].str[:-6]
        # df['Adaptive Standard'] = df['Adaptive Standard'].str[3:]
        # df['Category'] = df['Category'].str[3:]
        # df['Comfort mode'] = df['Comfort mode'].str[3:]
        # df['HVAC mode'] = df['HVAC mode'].str[3:]
        # df['Ventilation control'] = df['Ventilation control'].str[3:]
        # df['VSToffset'] = df['VSToffset'].str[3:]
        # df['MinOToffset'] = df['MinOToffset'].str[3:]
        # df['MaxWindSpeed'] = df['MaxWindSpeed'].str[3:]
        # df['ASTtol'] = df['ASTtol'].str[3:]
        df['EPW'] = df['EPW'].str[:-4]
        df['Source'] = df['Source'].str[:-4]

        # Step: splitting EPW names if requested
        if split_epw_names:
            df[[
                'EPW_Country_name',
                'EPW_City_or_subcountry',
                'EPW_Scenario-Year'
            ]] = df['EPW'].str.split('_', expand=True)
            try:
                df[[
                    'EPW_Scenario',
                    'EPW_Year',
                ]] = df['EPW_Scenario-Year'].str.split('-', expand=True)
            except ValueError:
                print('All CSVs are for present scenario.')
                df['EPW_Scenario'] = 'Present'
                df['EPW_Year'] = 'Present'
            df.EPW_Year.fillna(value='Present', inplace=True)

        df = df.set_index([pd.RangeIndex(len(df))])

        # Step: do not know what it is this for
        frequency_dict = {
            'monthly': ['Month'],
            'daily': ['Day', 'Month'],
            'hourly': ['Day', 'Month', 'Hour'],
            'timestep': ['Day', 'Month', 'Hour', 'Minute']
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

        # df['Hour_mod'] = df['Hour'].copy()
        if 'hourly' in self.frequency or 'timestep' in self.frequency:
            df['Hour'] = (pd.to_numeric(df['Hour']) - 1).astype(str).str.pad(width=2, side='left', fillchar='0')
        # df['Hour_mod'] = df['Hour_mod'].str.replace('.0', '').str.pad(width=2, side='left', fillchar='0')
        # df['Hour'] = df['Hour_mod']


        # todo test timestep
        if 'monthly' in self.frequency:
            df['Month'] = df['Month'].astype(str)
            df['Date/Time'] = df['Month']
        if 'daily' in self.frequency:
            df[['Day', 'Month']] = df[['Day', 'Month']].astype(str)
            df['Date/Time'] = df[['Day', 'Month']].agg('/'.join, axis=1)
        if 'hourly' in self.frequency:
            df[['Day', 'Month', 'Hour']] = df[['Day', 'Month', 'Hour']].astype(str)
            df['Date/Time'] = df[['Day', 'Month']].agg('/'.join, axis=1) + ' ' + df['Hour'] + ':00'
        # if 'timestep' in self.frequency:
        #     df[['Day', 'Month', 'Hour', 'Minute']] = df[['Day', 'Month', 'Hour', 'Minute']].astype(str)
        #     df['Date/Time'] = (df[['Day', 'Month']].agg('/'.join, axis=1) +
        #                             ' ' +
        #                             df[['Hour', 'Minute']].agg(':'.join, axis=1))


        df = df.set_index([pd.RangeIndex(len(df))])

        # Step: managing EPW names if requested
        if manage_epw_names:
            rcpdict = {
                'Present': ['Presente', 'Actual', 'Present', 'Current'],
                'RCP2.6': ['RCP2.6', 'RCP26'],
                'RCP4.5': ['RCP4.5', 'RCP45'],
                'RCP6.0': ['RCP6.0', 'RCP60'],
                'RCP8.5': ['RCP8.5', 'RCP85']
            }

            rcp = []
            for i in rcpdict:
                for j in range(len(rcpdict[i])):
                    rcp.append(rcpdict[i][j])

            rcp_present = []
            for i in rcpdict['Present']:
                rcp_present.append(i)

            df['EPW_mod'] = df['EPW'].str.split('_')

            for i in range(len(df['EPW_mod'])):
                for j in df.loc[i, 'EPW_mod']:
                    if len(j) == 2:
                        df.loc[i, 'EPW_CountryCode'] = j
                    else:
                        df.loc[i, 'EPW_CountryCode'] = np.nan

                    for k in rcpdict:
                        for m in range(len(rcpdict[k])):
                            if j in rcpdict[k][m]:
                                df.loc[i, 'EPW_Scenario'] = k
                            else:
                                df.loc[i, 'EPW_Scenario'] = np.nan

                df.loc[i, 'EPW_Year'] = np.nan

        # Step: matching cities if requested
        isEPWformatValid = False
        if match_cities:
            package_cities = datapackage.Package('https://datahub.io/core/world-cities/datapackage.json')
            package_countries = datapackage.Package('https://datahub.io/core/country-list/datapackage.json')

            # to load only tabular data_cities
            resources_cities = package_cities.resources
            for resource in resources_cities:
                if resource.tabular:
                    data_cities = pd.read_csv(resource.descriptor['path'])

            resources_countries = package_countries.resources
            for resource in resources_countries:
                if resource.tabular:
                    data_countries = pd.read_csv(resource.descriptor['path'])

            df = df.set_index([pd.RangeIndex(len(df))])

            # todo if len <1
            data_cities['subcountry'] = data_cities['subcountry'].astype(str)
            data_countries['Name'] = data_countries['Name'].astype(str)
            data_countries['Code'] = data_countries['Code'].astype(str)

            locations = []
            for i in list(df['EPW_mod']):
                for j in i:
                    if j in rcp:
                        continue
                    elif j.isnumeric():
                        continue
                    elif len(j) <= 2:
                        continue
                    else:
                        locations.append(j.lower())
            locations = list(dict.fromkeys(locations))

            data_temp_city = []
            for i in list(data_cities['name']):
                data_temp_city.append(i.lower())

            data_temp_subcountry = []
            for i in list(data_cities['subcountry']):
                data_temp_subcountry.append(i.lower())

            matches_city = list(set(locations).intersection(set(data_temp_city)))
            matches_subcountry = list(set(locations).intersection(data_temp_subcountry))
            # matches_city = list(set(locations).intersection(set(data_cities['name'].str.lower())))
            # matches_subcountry = list(set(locations).intersection(data_cities['subcountry'].str.lower()))
            matches = matches_subcountry + matches_city
            matches = list(dict.fromkeys(matches))

            cities_df_list = []

            try:
                for i in matches:
                    temp_df = data_cities.query('name.str.lower() == "%s"' % i.lower())
                    if len(temp_df) == 0:
                        temp_df = data_cities.query('subcountry.str.lower() == "%s"' % i.lower())
                    cities_df_list.append(temp_df)
                cities_df = pd.concat(cities_df_list)
                cities_df = cities_df.set_index([pd.RangeIndex(len(cities_df))])
                cities_df['country'] = cities_df['country'].astype(str)
                isEPWformatValid = True
            except ValueError:
                isEPWformatValid = False
                print('EPW files are not correctly named')

            df['EPW_CountryCode'] = df['EPW_CountryCode'].astype(str)

        if manage_epw_names:
            for i in range(len(df['EPW_mod'])):
                for j in df.loc[i, 'EPW_mod']:
                    if j in rcp_present:
                        df.loc[i, 'EPW_Year'] = 'Present'
                    elif j in rcp:
                        continue
                    elif j.isnumeric():
                        df.loc[i, 'EPW_Year'] = int(j)
                    elif len(j) == 2:
                        continue
                    else:
                        if match_cities:
                            if isEPWformatValid:
                                for k in range(len(cities_df)):
                                    if df.loc[i, 'EPW_CountryCode'].lower() in cities_df.loc[k, 'country'].lower():
                                        df.loc[i, 'EPW_Country'] = cities_df.loc[k, 'country']
                                    if str(j).lower() in cities_df.loc[k, 'name'].lower():
                                        df.loc[i, 'EPW_City_or_subcountry'] = cities_df.loc[k, 'name']
                                    elif str(j).lower() in cities_df.loc[k, 'subcountry'].lower():
                                        df.loc[i, 'EPW_City_or_subcountry'] = cities_df.loc[k, 'name']
                                    elif str(j).isalnum():
                                        df.loc[i, 'EPW_City_or_subcountry'] = j.upper()
                                    else:
                                        df.loc[i, 'EPW_City_or_subcountry'] = j.capitalize()
                        else:
                            df.loc[i, 'EPW_City_or_subcountry'] = j.capitalize()

            df = df.drop(['EPW_mod'], axis=1)

        # Step: re-ordering the columns
        cols = df.columns.tolist()

        if self.frequency == 'runperiod':
            # this 1 is Source
            freq_extension = 1
        else:
            freq_extension = 1 + len(frequency_dict[self.frequency])

        if split_epw_names:
            epw_extension = 5
        else:
            epw_extension = 0

        # todo timestep frequency to be considered
        if self.frequency == 'runperiod':
            adj_extension = -3
        if self.frequency == 'monthly':
            adj_extension = -4
        if self.frequency == 'daily':
            adj_extension = -5
        if self.frequency == 'hourly':
            adj_extension = -6

        # the 2 is for Date/Time and Month/Day
        temp_num = -(len(fixed_columns) + 2 + freq_extension + epw_extension + adj_extension)
        cols = cols[temp_num:] + cols[:temp_num]
        # cols = cols[5:] + cols[:5]
        df = df[cols]
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
                'AFN Zone Infiltration Volume [m3](Hourly)': 'AFN Zone Infiltration Volume (m3)',
                'AFN Zone Infiltration Air Change Rate [ach](Hourly)': 'AFN Zone Infiltration Air Change Rate (ach)',
                # 'Zone Thermostat Operative Temperature [C](Hourly)': 'Zone Thermostat Operative Temperature (°C)',
                'Zone Operative Temperature [C](Hourly)': 'Zone Operative Temperature (°C)',
                'Zone Operative Temperature': 'Zone Operative Temperature (°C)',
                'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)':
                    'EN16798-1 Running mean outdoor temperature (°C)',
                'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)':
                    'ASHRAE 55 Running mean outdoor temperature (°C)',
                'FORSCRIPT_AHST': 'FORSCRIPT_AHST',
                'FORSCRIPT_ACST': 'FORSCRIPT_ACST',
                'VRF Heat Pump Cooling Electricity Energy': 'Cooling Energy Consumption',
                'VRF Heat Pump Heating Electricity Energy': 'Heating Energy Consumption',
                'Heating Coil Heating Rate': 'Heating Energy Demand',
                'Cooling Coil Total Cooling Rate': 'Cooling Energy Demand',
                'Zone Thermal Comfort Fanger Model PMV': 'PMV',
                'Zone Thermal Comfort Fanger Model PPD': 'PPD (%)'
            }

            renaming_criteria = {
                # 'Date/Time',
                'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)':
                    'Site Outdoor Air Drybulb Temperature (°C)',
                'Environment:Site Wind Speed [m/s](Hourly)': 'Site Wind Speed (m/s)',
                'Environment:Site Outdoor Air Relative Humidity [%](Hourly)':
                    'Site Outdoor Air Relative Humidity (%)',
                'EMS:Comfort Temperature [C](Hourly)': 'Comfort Temperature (°C)',
                'EMS:Adaptive Cooling Setpoint Temperature [C](Hourly)': 'Adaptive Cooling Setpoint Temperature (°C)',
                'EMS:Adaptive Heating Setpoint Temperature [C](Hourly)': 'Adaptive Heating Setpoint Temperature (°C)',
                'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance [C](Hourly)':
                    'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
                'EMS:Adaptive Heating Setpoint Temperature_No Tolerance [C](Hourly)':
                    'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
                'EMS:Ventilation Setpoint Temperature [C](Hourly)': 'Ventilation Setpoint Temperature (°C)',
                'EMS:Minimum Outdoor Temperature for ventilation [C](Hourly)':
                    'Minimum Outdoor Temperature for ventilation (°C)',
                'Whole Building:Facility Total HVAC Electricity Demand Rate':
                    'Whole Building Facility Total HVAC Electricity Demand Rate',
            }

            all_cols_renamed = {}

            for col in df.columns:
                for crit in renaming_criteria_bz:
                    if '(summed)' not in col and '(mean)' not in col:
                        if crit in col:
                            for block_zone in occupied_zone_list:
                                if block_zone in col:
                                    if energy_units in col:
                                        temp = {col: block_zone + '_' + renaming_criteria_bz[crit] + ' ' + energy_units}
                                        all_cols_renamed.update(temp)
                                    else:
                                        temp = {col: block_zone + '_' + renaming_criteria_bz[crit]}
                                        all_cols_renamed.update(temp)

            for col in df.columns:
                for crit in renaming_criteria:
                    if '(summed)' not in col and '(mean)' not in col:
                        if crit in col:
                            if energy_units in col:
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
                        if block + '_Total_' + crit in col:
                            if '(summed)' in col:
                                temp = {col: f'{block}_Total_{renaming_criteria_block[crit]} {energy_units} (summed)'}
                                all_cols_renamed.update(temp)
                            elif '(mean)' in col:
                                temp = {col: f'{block}_Total_{renaming_criteria_block[crit]} {energy_units} (mean)'}
                                all_cols_renamed.update(temp)
                    if 'Building_Total_' + crit in col:
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
            'Adaptive Standard',
            'Category',
            'Comfort mode',
            'HVAC mode',
            'Ventilation control',
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

        # todo Step: remove PMV-PPD columns if the column only have null values



        self.hvac_zone_list = hvac_zone_list
        self.occupied_zone_list = occupied_zone_list
        self.available_vars_to_gather = available_vars_to_gather
        self.block_list = block_list
        self.df = df

        self.frequency = frequency


        # df.to_excel('checkpoint_04.xlsx')


    def format_table(self,
                     type_of_table: str = 'all',
                     custom_cols: list = None,
                     custom_rows: list = None,
                     split_epw_names: bool = False
                     ):
        """

        :param type_of_table: To get previously set out tables. Can be 'energy demand' or 'comfort hours'.
        :param custom_cols: A list of strings.
        The strings will be used as a filter, and the columns that match will be selected.
        :param split_epw_names: A bool, can be True or False.
        Used to detect climate change scenario, country and sub-country codes and city.
        If a large number of CSVs is going to be computed
        or hourly values are going to be considered, it is recommended to be False.
        """
        if custom_cols is None:
            custom_cols = []
        if custom_rows is None:
            custom_rows = []


        self.split_epw_names = split_epw_names

        self.indexcols = [
            'Date/Time',
            'Model',
            'Adaptive Standard',
            'Category',
            'Comfort mode',
            'HVAC mode',
            'Ventilation control',
            'VSToffset',
            'MinOToffset',
            'MaxWindSpeed',
            'ASTtol',
            'NameSuffix',
            'EPW',
            'Source',
            # 'col_to_pivot'
        ]
        if 'runperiod' in self.frequency:
            self.indexcols.remove('Date/Time')
        if 'monthly' in self.frequency:
            self.indexcols.append('Month')
        if 'daily' in self.frequency:
            self.indexcols.extend(['Month', 'Day'])
        if 'hourly' in self.frequency:
            self.indexcols.extend(['Month', 'Day', 'Hour'])
        if 'timestep' in self.frequency:
            self.indexcols.extend(['Month', 'Day', 'Hour', 'Minute'])
        if split_epw_names:
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
                            'Heating Energy Demand' in col]
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

        if not(type_of_table == 'all'):
            self.df = self.df[self.indexcols + self.val_cols]



    def custom_order(
            self,
            ordered_list: list = None,
            column_to_order: str = None,
    ):
        from pandas.api.types import CategoricalDtype

        if ordered_list is None:
            ordered_list = []

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


    def wrangled_table(self,
                       reshaping: str = None,
                       vars_to_gather: list = None,
                       baseline: str = None,
                       comparison_cols: list = None):
        """
        Creates a table based on the arguments.

        :param vars_to_gather: A list of the variables to be transposed from rows to columns.
        :param baseline: The already transposed column you want to use as a baseline for comparisons.
        If ommited, you will be asked which one to use.
        :param comparison_cols: 'absolute' to get the difference or 'relative' to get the percentage of reduction.
        """
        if vars_to_gather is None:
            vars_to_gather = []
        if comparison_cols is None:
            comparison_cols = []

        import numpy as np

        self.df['col_to_pivot'] = 'temp'


        self.indexcols.append('col_to_pivot')

        self.enter_vars_to_gather(vars_to_gather)

        wrangled_df = self.df.copy()


        if reshaping == 'pivot':
            
            wrangled_df_pivoted = wrangled_df.copy()
            del wrangled_df
            
            if 'Month' in wrangled_df_pivoted.columns:
                wrangled_df_pivoted['col_to_pivot'] = (wrangled_df_pivoted[vars_to_gather].agg('['.join, axis=1) + '_' +
                                                    wrangled_df_pivoted['Month'].astype(str) +
                                                    '[Month')
            else:
                wrangled_df_pivoted['col_to_pivot'] = wrangled_df_pivoted[vars_to_gather].agg('['.join, axis=1)

            self.df['col_to_pivot'] = wrangled_df_pivoted['col_to_pivot']

            wrangled_df_pivoted = wrangled_df_pivoted.pivot_table(
                index=self.indexcols.remove('col_to_pivot'),
                columns='col_to_pivot',
                values=self.val_cols,
                aggfunc=np.sum,
                fill_value=0)

            var_to_gather_values = list(dict.fromkeys(self.df['col_to_pivot']))

            if baseline not in var_to_gather_values:
                print(f'"{baseline}" is not in list of categories you want to compare. The list is:')
                print(var_to_gather_values)
                baseline = input('Please choose one from the list above (it is case-sensitive) for baseline:')

            other_than_baseline = list(set(var_to_gather_values) - set([baseline]))

            self.df = self.df.drop('col_to_pivot', axis=1)

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
                    if any('relative' in k for k in comparison_cols):
                        wrangled_df_pivoted[f'1-({j}/{baseline})'] = (
                                1 -
                                (wrangled_df_pivoted[j] / wrangled_df_pivoted[baseline])
                        )
                    if any('absolute' in k for k in comparison_cols):
                        wrangled_df_pivoted[f'{baseline} - {j}'] = (
                                wrangled_df_pivoted[baseline] - wrangled_df_pivoted[j]
                        )
            self.wrangled_df_pivoted = wrangled_df_pivoted
            
        elif reshaping == 'unstack':
            
            wrangled_df_unstacked = wrangled_df.copy()
            del wrangled_df
            
            wrangled_df_unstacked = wrangled_df_unstacked.drop(['col_to_pivot'], axis=1)
            self.indexcols.remove('col_to_pivot')
            wrangled_df_unstacked = wrangled_df_unstacked.drop(['Source'], axis=1)
            self.indexcols.remove('Source')
            if self.split_epw_names:
                wrangled_df_unstacked = wrangled_df_unstacked.drop(['EPW', 'EPW_Scenario-Year'], axis=1)
                self.indexcols.remove('EPW')
                self.indexcols.remove('EPW_Scenario-Year')

            cols_to_clean = []
            cols_for_multiindex = []
            for i in self.indexcols:
                if (wrangled_df_unstacked[i][0] == wrangled_df_unstacked[i]).all():
                    cols_to_clean.append(i)
                else:
                    cols_for_multiindex.append(i)

            wrangled_df_unstacked = wrangled_df_unstacked.drop(cols_to_clean, axis=1)

            cols_for_values = list(set(wrangled_df_unstacked.columns) - set(cols_for_multiindex))

            wrangled_df_unstacked = wrangled_df_unstacked.set_index(cols_for_multiindex)

            wrangled_df_unstacked = wrangled_df_unstacked.unstack(vars_to_gather)

            # df_testing_unstacked_temp = wrangled_df_unstacked.copy()

            wrangled_df_unstacked.columns = ['['.join(col).strip('[') for col in wrangled_df_unstacked.columns.values]

            var_to_gather_values = [i.split('[', maxsplit=1)[1] for i in wrangled_df_unstacked.columns]
            var_to_gather_values = list(dict.fromkeys(var_to_gather_values))

            if baseline not in var_to_gather_values:
                print(f'"{baseline}" is not in list of categories you want to compare. The list is:')
                print(var_to_gather_values)
                baseline = input('Please choose one from the list above (it is case-sensitive) for baseline:')

            other_than_baseline = [i.split('[', maxsplit=1)[1] for i in wrangled_df_unstacked.columns if baseline not in i]
            other_than_baseline = list(dict.fromkeys(other_than_baseline))

            baseline_col = [col for col in wrangled_df_unstacked.columns if baseline in col][0]

            # in this case the months are located in rows, so no need to add months to columns
            for i in cols_for_values:
                for j in other_than_baseline:
                    for x in [col for col in wrangled_df_unstacked.columns if i in col and j in col]:
                        if any('relative' in k for k in comparison_cols):
                            wrangled_df_unstacked[f'{i}[1-({j}/{baseline})'] = (
                                    1 -
                                    (wrangled_df_unstacked[x] / wrangled_df_unstacked[baseline_col])
                            )
                        if any('absolute' in k for k in comparison_cols):
                            wrangled_df_unstacked[f'{i}[{baseline} - {j}'] = (
                                    wrangled_df_unstacked[baseline_col] - wrangled_df_unstacked[x]
                            )
            self.wrangled_df_unstacked = wrangled_df_unstacked

    def enter_vars_to_gather(
            self,
            vars_to_gather=None
    ):
        if vars_to_gather is None:
            vars_to_gather = []

        while (not(all(elem in self.available_vars_to_gather for elem in vars_to_gather))
               or len(vars_to_gather) != len(set(vars_to_gather))):
            print('Some of the variables to be gathered are not available or are duplicated:')
            print(vars_to_gather)
            print('The list of available variables to be gathered is:')
            print(self.available_vars_to_gather)
            vars_to_gather = (list(str(var)
                                   for var
                                   in input("Enter the variables to be gathered separated by semicolon: ").split(';')))
        return vars_to_gather

    # todo testing
    
    def generate_fig_data(self,
                          vars_to_gather_cols=None,
                          vars_to_gather_rows=None,
                          detailed_cols=None,
                          detailed_rows=None,
                          adap_vs_stat_data_y_main=None,
                          # adap_vs_stat_data_y_sec=None,
                          baseline: str = None,
                          colorlist_adap_vs_stat_data=None,
                          data_on_x_axis: str = None,
                          data_on_y_main_axis=None,
                          data_on_y_sec_axis=None,
                          colorlist_y_main_axis=None,
                          colorlist_y_sec_axis=None,
                          ):
        if vars_to_gather_cols is None:
            vars_to_gather_cols = []
        if vars_to_gather_rows is None:
            vars_to_gather_rows = []
        if detailed_cols is None:
            detailed_cols = []
        if detailed_rows is None:
            detailed_rows = []
        if adap_vs_stat_data_y_main is None:
            adap_vs_stat_data_y_main = []
        self.adap_vs_stat_data_y_main = adap_vs_stat_data_y_main
        # if adap_vs_stat_data_y_sec is None:
        #     adap_vs_stat_data_y_sec = []
        if colorlist_adap_vs_stat_data is None:
            colorlist_adap_vs_stat_data = []
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
            
        import matplotlib.pyplot as plt
        import matplotlib.lines as lines

        self.df_for_graph = self.df.copy()

        self.df_for_graph['col_to_gather_in_cols'] = 'temp'
        self.df_for_graph['col_to_gather_in_rows'] = 'temp'

        if len(vars_to_gather_rows) == 0:
            print('In relation to the variables to be gathered in self.rows,')
            self.enter_vars_to_gather(vars_to_gather_cols)
        if len(vars_to_gather_cols) == 0:
            print('In relation to the variables to be gathered in columns,')
            self.enter_vars_to_gather(vars_to_gather_cols)

        self.df_for_graph['col_to_gather_in_rows'] = self.df_for_graph[vars_to_gather_rows].agg('['.join, axis=1)
        self.df_for_graph['col_to_gather_in_cols'] = self.df_for_graph[vars_to_gather_cols].agg('['.join, axis=1)

        all_cols = list(set(self.df_for_graph['col_to_gather_in_cols']))
        self.rows = list(set(self.df_for_graph['col_to_gather_in_rows']))

        all_cols.sort()
        self.cols = all_cols
        self.rows.sort()

        while not(all(i in self.cols for i in detailed_cols)):
            print('Some of the detailed data to be gathered in columns based on the argument '
                  'vars_to_gather_cols is not available. '
                  'Only the following data is available for columns:')
            print(self.cols)
            detailed_cols = (list(str(var)
                                   for var
                                   in input("Please enter the requested data to be arranged "
                                            "in columns separated by semicolon: ").split(';')))
        while not(all(i in self.rows for i in detailed_rows)):
            print('Some of the detailed data to be gathered in self.rows based on the argument '
                  'vars_to_gather_rows is not available. '
                  'Only the following data is available for self.rows:')
            print(self.rows)
            detailed_rows = (list(str(var)
                                   for var
                                   in input("Please enter the requested data to be arranged "
                                            "in self.rows separated by semicolon: ").split(';')))

        if len(detailed_cols) > 0:
            self.cols = detailed_cols
        if len(detailed_rows) > 0:
            self.rows = detailed_rows


        if len(adap_vs_stat_data_y_main) > 0:
            if baseline is None:
                print(f'Any baseline has been specified. The list of available baselines is:')
                print(all_cols)
                baseline = input('Please choose one from the list above (it is case-sensitive) for baseline:')

            while not(any(baseline in i for i in all_cols)):
                print(f'"{baseline}" is not in list of categories you want to compare. The list is:')
                print(all_cols)
                baseline = input('Please choose one from the list above (it is case-sensitive) for baseline:')

            self.cols = [x for x in self.cols if x not in set([baseline])]


        self.cols.sort()
        self.rows.sort()

        cols_list_to_filter = self.cols + [baseline]

        self.df_for_graph = self.df_for_graph[
            (self.df_for_graph['col_to_gather_in_cols'].isin(cols_list_to_filter)) &
            (self.df_for_graph['col_to_gather_in_rows'].isin(self.rows))
        ]

        # if baseline is not None and len(adap_vs_stat_data_y_main) > 0:
        self.df_for_graph['col_to_unstack'] = self.df_for_graph[
            ['col_to_gather_in_cols', 'col_to_gather_in_rows']].agg('['.join, axis=1)


        columns_to_drop = [
            # 'Date/Time',
            'Model',
            'Adaptive Standard',
            'Category',
            'Comfort mode',
            'HVAC mode',
            'Ventilation control',
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

        self.df_for_graph = self.df_for_graph.drop(
            columns=columns_to_drop
        )

        multi_index = [
            'Date/Time',
            'col_to_unstack'
        ]

        self.df_for_graph.set_index(multi_index, inplace=True)
        if len(adap_vs_stat_data_y_main) > 0:
            self.max_value = max([self.df_for_graph[dataset].max() for dataset in adap_vs_stat_data_y_main])

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

        self.df_for_graph = self.df_for_graph.unstack('col_to_unstack')

        self.df_for_graph.columns = self.df_for_graph.columns.map('['.join)

        # making lists for figure
        self.x_list = []
        for i in range(len(self.rows)):
            temp_row = []
            for j in range(len(self.cols)):
                if len(adap_vs_stat_data_y_main) > 0:
                    temp = [
                        [i, j],
                        f'{self.rows[i]}_{self.cols[j]}',
                        [
                            self.df_for_graph[[x for x in self.df_for_graph.columns if self.rows[i] in x and baseline in x and dataset in x]]
                            for dataset in adap_vs_stat_data_y_main
                        ]
                    ]
                else:
                    temp = [
                        [i, j],
                        f'{self.rows[i]}_{self.cols[j]}',
                        self.df_for_graph[[x for x in self.df_for_graph.columns if self.rows[i] in x and self.cols[j] in x and data_on_x_axis in x]]
                    ]
                temp_row.append(temp)
            self.x_list.append(temp_row)

        self.y_list_main = []
        for i in range(len(self.rows)):
            temp_row = []
            if baseline is not None and len(adap_vs_stat_data_y_main) > 0:
                for j in range(len(self.cols)):
                    temp = [
                        [i, j],
                        f'{self.rows[i]}_{self.cols[j]}',
                        [
                            self.df_for_graph[[x for x in self.df_for_graph.columns if self.rows[i] in x and self.cols[j] in x and dataset in x]]
                            for dataset in adap_vs_stat_data_y_main
                        ],
                        [dataset for dataset in adap_vs_stat_data_y_main],
                        [color for color in colorlist_adap_vs_stat_data]
                    ]
                    temp_row.append(temp)
                self.y_list_main.append(temp_row)
            else:
                for j in range(len(self.cols)):
                    temp_col = []
                    for k in range(len(data_on_y_main_axis)):
                        temp = {
                            'axis': [i, j],
                            'title': f'{self.rows[i]}_{self.cols[j]}',
                            'dataframe': [
                                self.df_for_graph[[x for x in self.df_for_graph.columns if
                                                   self.rows[i] in x and self.cols[j] in x and dataset in x]]
                                for dataset in data_on_y_main_axis[k][1]
                            ],
                            'label': [dataset for dataset in data_on_y_main_axis[k][1]],
                            'color': [color for color in colorlist_y_main_axis[k][1]]
                        }
                        temp_col.append(temp)
                    temp_row.append(temp_col)
                self.y_list_main.append(temp_row)

        self.y_list_sec = []
        for i in range(len(self.rows)):
            temp_row = []
            for j in range(len(self.cols)):
                temp_col = []
                for k in range(len(self.data_on_y_sec_axis)):
                    # if baseline is not None and len(adap_vs_stat_data_y_sec) > 0:
                    #     temp = [
                    #         [i, j],
                    #         f'{self.rows[i]}_{self.cols[j]}',
                    #         [
                    #             self.df_for_graph[[x for x in self.df_for_graph.columns if self.rows[i] in x and self.cols[j] in x and dataset in x]]
                    #             for dataset in adap_vs_stat_data_y_sec
                    #         ],
                    #         [dataset for dataset in adap_vs_stat_data_y_sec],
                    #         [color for color in colorlist_y_sec_axis]
                    #     ]
                    # else:
                    temp = {
                        'axis':[i, j],
                        'title': f'{self.rows[i]}_{self.cols[j]}',
                        'dataframe': [
                            self.df_for_graph[[x for x in self.df_for_graph.columns if self.rows[i] in x and self.cols[j] in x and dataset in x]]
                            for dataset in data_on_y_sec_axis[k][1]
                            ],
                        'label':[dataset for dataset in data_on_y_sec_axis[k][1]],
                        'color': [color for color in colorlist_y_sec_axis[k][1]]
                    }
                    temp_col.append(temp)
                temp_row.append(temp_col)
            self.y_list_sec.append(temp_row)


    def scatter_plot(
            self,
            supxlabel: str = None,
            figname: str = None,
            figsize: float = 1,
            ratio_height_to_width: float = 1,
            confirm_graph: bool = False
    ):
        import numpy as np
        import matplotlib.pyplot as plt

        print(f'The number of self.rows and the list of these is going to be:')
        print(f'No. of self.rows = {len(self.rows)}')
        print(f'List of self.rows:')
        print(*self.rows, sep='\n')

        print(f'The number of columns and the list of these is going to be:')
        print(f'No. of columns = {len(self.cols)}')
        print(f'List of columns:')
        print(*self.cols, sep='\n')

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
                                   figsize=(figsize * len(self.cols), ratio_height_to_width * figsize * len(self.rows)))

            main_y_axis = []
            sec_y_axis = []

            for i in range(len(self.rows)):
                main_y_axis_temp_rows = []
                sec_y_axis_temp_rows = []
                for j in range(len(self.cols)):

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
                        main_y_axis[i][j][k].grid(True, linestyle='-.')
                        main_y_axis[i][j][k].tick_params(axis='both',
                                                      grid_color='black',
                                                      grid_alpha=0.5)
                        main_y_axis[i][j][k].set_facecolor((0, 0, 0, 0.10))

                        for x in range(len(self.y_list_main[i][j][k]['dataframe'])):
                            if i == 0 and j == 0:
                                main_y_axis[i][j][k].scatter(
                                    self.x_list[i][j][2],
                                    self.y_list_main[i][j][k]['dataframe'][x],
                                    c=self.y_list_main[i][j][k]['color'][x],
                                    s=1,
                                    marker='o',
                                    alpha=0.5,
                                    label=self.y_list_main[i][j][k]['label'][x],
                                )
                            else:
                                main_y_axis[i][j][k].scatter(
                                    self.x_list[i][j][2],
                                    self.y_list_main[i][j][k]['dataframe'][x],
                                    c=self.y_list_main[i][j][k]['color'][x],
                                    s=1,
                                    marker='o',
                                    alpha=0.5,
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
                            if i == 0 and j == 0:
                                sec_y_axis[i][j][k].scatter(
                                    self.x_list[i][j][2],
                                    self.y_list_sec[i][j][k]['dataframe'][x],
                                    c=self.y_list_sec[i][j][k]['color'][x],
                                    s=1,
                                    marker='o',
                                    alpha=0.5,
                                    label=self.y_list_sec[i][j][k]['label'][x],
                                )
                            else:
                                sec_y_axis[i][j][k].scatter(
                                    self.x_list[i][j][2],
                                    self.y_list_sec[i][j][k]['dataframe'][x],
                                    c=self.y_list_sec[i][j][k]['color'][x],
                                    s=1,
                                    marker='o',
                                    alpha=0.5,
                                )

            if len(self.rows) == 1:
                if len(self.cols) == 1:
                    for i in range(len(self.rows)):
                        ax.set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        ax.set_title(self.cols[j])

            if len(self.rows) > 1:
                if len(self.cols) == 1:
                    for i in range(len(self.rows)):
                        ax[i].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        ax[0].set_title(self.cols[j])
                else:
                    for i in range(len(self.rows)):
                        ax[i, 0].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        ax[0, j].set_title(self.cols[j])

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
                        dpi=1200,
                        format='png',
                        bbox_extra_artists=bbox_extra_artists_tuple,
                        bbox_inches='tight')

            plt.show()

    def scatter_plot_adap_vs_stat(self,
                                  supxlabel: str = None,
                                  supylabel: str = None,
                                  figname: str = None,
                                  figsize: int = 1,
                                  markersize: int = 1,
                                  confirm_graph: bool = False
                                  ):
        import matplotlib.pyplot as plt
        import matplotlib.lines as lines
        
        print(f'The number of self.rows and the list of these is going to be:')
        print(f'No. of self.rows = {len(self.rows)}')
        print(f'List of self.rows:')
        print(*self.rows, sep='\n')

        print(f'The number of columns and the list of these is going to be:')
        print(f'No. of columns = {len(self.cols)}')
        print(f'List of columns:')
        print(*self.cols, sep='\n')

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
                        ax.set_facecolor((0, 0, 0, 0.10))
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

                        ax.set_ylim((0, self.max_value))
                        ax.set_xlim((0, self.max_value))

                    elif len(self.cols) == 1 and len(self.rows) > 1:
                        # ax[i].set_title(f'{self.rows[i]} / {self.cols[j]}')
                        ax[i].grid(True, linestyle='-.')
                        ax[i].tick_params(axis='both',
                                             grid_color='black',
                                             grid_alpha=0.5)
                        ax[i].set_facecolor((0, 0, 0, 0.10))
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

                        ax[i].set_ylim((0, self.max_value))
                        ax[i].set_xlim((0, self.max_value))

                    else:
                        # ax[i, j].set_title(f'{self.rows[i]} / {self.cols[j]}')
                        ax[i, j].grid(True, linestyle='-.')
                        ax[i, j].tick_params(axis='both',
                                             grid_color='black',
                                             grid_alpha=0.5)
                        ax[i, j].set_facecolor((0, 0, 0, 0.10))
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

                        ax[i, j].set_ylim((0, self.max_value))
                        ax[i, j].set_xlim((0, self.max_value))
        
            if len(self.rows) == 1:
                if len(self.cols) == 1:
                    ax.set_aspect('equal',
                                        # adjustable='box',
                                        share=True)
                    for i in range(len(self.rows)):
                        ax.set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        ax.set_title(self.cols[j])

            if len(self.rows) > 1:
                if len(self.cols) == 1:
                    ax[0].set_aspect('equal',
                                        # adjustable='box',
                                        share=True)
                    for i in range(len(self.rows)):
                        ax[i].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        ax[0].set_title(self.cols[j])
                else:
                    ax[0, 0].set_aspect('equal',
                                        # adjustable='box',
                                        share=True)
                    for i in range(len(self.rows)):
                        ax[i, 0].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
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
    
            plt.savefig(figname+'.png',
                        dpi=1200,
                        format='png',
                        bbox_extra_artists=(leg, supx, supy),
                        bbox_inches='tight'
                        )
    
    def time_plot(
            self,
            supxlabel: str = None,
            figname: str = None,
            figsize: float = 1,
            ratio_height_to_width: float = 1,
            confirm_graph: bool = False
    ):
        import numpy as np
        import matplotlib.pyplot as plt
        import pandas as pd
        import datetime
        import matplotlib.dates as mdates

        print(f'The number of self.rows and the list of these is going to be:')
        print(f'No. of self.rows = {len(self.rows)}')
        print(f'List of self.rows:')
        print(*self.rows, sep='\n')

        print(f'The number of columns and the list of these is going to be:')
        print(f'No. of columns = {len(self.cols)}')
        print(f'List of columns:')
        print(*self.cols, sep='\n')

        if confirm_graph is False:
            proceed = input('Do you want to proceed? [y/n]:')
            if 'y' in proceed:
                confirm_graph = True
            elif 'n' in proceed:
                confirm_graph = False

        if confirm_graph:
            self.df_for_graph['Date/Time'] = self.df_for_graph.index

            freq_graph_dict = {
                'timestep': ['X?', "%d/%m %H:%M"],
                'hourly': ['H', "%d/%m %H:%M"],
                'daily': ['D', "%d/%m"],
                'monthly': ['M', "%m"],
                # todo WIP
                'runperiod': ['?', "?"]
            }

            start_date = datetime.datetime.strptime(self.df_for_graph['Date/Time'][0], freq_graph_dict[self.frequency][1])
            # end_date = datetime.datetime.strptime(self.df_for_graph['Date/Time'][len(self.df_for_graph)-1], "%d/%m %H:%M")
            # (end_date-start_date).days

            self.df_for_graph['Date/Time'] = pd.date_range(
                start=start_date,
                periods=len(self.df_for_graph),
                # '2017-31-12 23:00',
                freq=freq_graph_dict[self.frequency][0]
            )

            fig, ax = plt.subplots(nrows=len(self.rows),
                                   ncols=len(self.cols),
                                   sharex=True,
                                   sharey=True,
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
                        main_y_axis[i][j][k].set_facecolor((0, 0, 0, 0.10))

                        for x in range(len(self.y_list_main[i][j][k]['dataframe'])):
                            if i == 0 and j == 0:
                                main_y_axis[i][j][k].plot(
                                    self.df_for_graph['Date/Time'],
                                    self.y_list_main[i][j][k]['dataframe'][x],
                                    linewidth=1,
                                    c=self.y_list_main[i][j][k]['color'][x],
                                    # ms=markersize,
                                    # marker='o',
                                    # alpha=0.5,
                                    label=self.y_list_main[i][j][k]['label'][x],
                                )
                            else:
                                main_y_axis[i][j][k].plot(
                                    self.df_for_graph['Date/Time'],
                                    self.y_list_main[i][j][k]['dataframe'][x],
                                    linewidth=1,
                                    c=self.y_list_main[i][j][k]['color'][x],
                                    # ms=markersize,
                                    # marker='o',
                                    # alpha=0.5,
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
                            if i == 0 and j == 0:
                                sec_y_axis[i][j][k].plot(
                                    self.df_for_graph['Date/Time'],
                                    self.y_list_sec[i][j][k]['dataframe'][x],
                                    linewidth=1,
                                    c=self.y_list_sec[i][j][k]['color'][x],
                                    # ms=markersize,
                                    # marker='o',
                                    # alpha=0.5,
                                    label=self.y_list_sec[i][j][k]['label'][x],
                                )
                            else:
                                sec_y_axis[i][j][k].plot(
                                    self.df_for_graph['Date/Time'],
                                    self.y_list_sec[i][j][k]['dataframe'][x],
                                    linewidth=1,
                                    c=self.y_list_sec[i][j][k]['color'][x],
                                    # ms=markersize,
                                    # marker='o',
                                    # alpha=0.5,
                                )

            if len(self.rows) == 1:
                if len(self.cols) == 1:
                    for i in range(len(self.rows)):
                        ax.set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        ax.set_title(self.cols[j])

            if len(self.rows) > 1:
                if len(self.cols) == 1:
                    for i in range(len(self.rows)):
                        ax[i].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        ax[0].set_title(self.cols[j])
                else:
                    for i in range(len(self.rows)):
                        ax[i, 0].set_ylabel(self.rows[i], rotation=90, size='large')
                    for j in range(len(self.cols)):
                        ax[0, j].set_title(self.cols[j])

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
                        dpi=1200,
                        format='png',
                        bbox_extra_artists=bbox_extra_artists_tuple,
                        bbox_inches='tight')

            plt.show()
