class Table:

    def __init__(self,
                 frequency: str = None,
                 sum_or_mean: str = None,
                 standard_outputs: bool = None,
                 level=None,
                 level_sum_or_mean=None,
                 match_cities: bool = False,
                 manage_epw_names: bool = False,
                 normalised_energy_units: bool = True,
                 rename_cols: bool = True,
                 energy_units_in_kwh: bool = True,
                 type_of_table: str = 'all',
                 custom_cols=None
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
        :param type_of_table: To get previously set out tables. Can be 'energy demand' or 'comfort hours'.
        :param custom_cols: A list of strings.
        The strings will be used as a filter, and the columns that match will be selected.

        """
        if level_sum_or_mean is None:
            level_sum_or_mean = []
        if level is None:
            level = []
        if custom_cols is None:
            custom_cols = []

        # import os
        import pandas as pd
        # from pathlib import Path
        import datapackage
        import glob
        import numpy as np

        self.frequency = frequency
        self.normalised_energy_units = normalised_energy_units

        #  check if glob.glob works with in terms of package, if not switch back to sorted
        # source_files = sorted(Path(os.getcwd()).glob('*.csv'))

        allfiles = glob.glob('*.csv', recursive=True)
        source_files = [f for f in allfiles if 'Table.csv' not in f and 'Zsz.csv' not in f]

        cleaned_columns = [
            'Date/Time',
            'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)',
            'Environment:Site Wind Speed [m/s](Hourly)',
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
            'Zone Thermostat Operative Temperature [C](Hourly)',
            'Whole Building:Facility Total HVAC Electricity Demand Rate [W](Hourly)',
            'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)',
            'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)',
            'FORSCRIPT',
            'VRF INDOOR UNIT DX COOLING COIL:Cooling Coil Total Cooling Rate [W](Hourly)',
            'VRF INDOOR UNIT DX HEATING COIL:Heating Coil Heating Rate [W](Hourly)',
            'VRF OUTDOOR UNIT',
            'Heating Coil Heating Rate [W](Hourly)',
            'Cooling Coil Total Cooling Rate [W](Hourly)',
            'Zone Air Volume',
            'Zone Floor Area'
        ]

        summed_dataframes = []

        for file in source_files:
            df = pd.DataFrame(pd.read_csv(file))
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

            df[['TBD1', 'Month/Day', 'TBD2', 'Hour']] = df['Date/Time'].str.split(' ', expand=True)
            df = df.drop(['TBD1', 'TBD2'], axis=1)
            df[['Month', 'Day']] = df['Month/Day'].str.split('/', expand=True)
            df[['Hour', 'Minute', 'Second']] = df['Hour'].str.split(':', expand=True)

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

            if frequency == 'timestep':
                df = df.groupby(['Source', 'Month', 'Day', 'Hour', 'Minute'], as_index=False).agg(sum_or_mean)
            if frequency == 'hourly':
                df = df.groupby(['Source', 'Month', 'Day', 'Hour'], as_index=False).agg(sum_or_mean)
            if frequency == 'daily':
                df = df.groupby(['Source', 'Month', 'Day'], as_index=False).agg(sum_or_mean)
            if frequency == 'monthly':
                df = df.groupby(['Source', 'Month'], as_index=False).agg(sum_or_mean)
            if frequency == 'runperiod':
                df = df.groupby(['Source'], as_index=False).agg(sum_or_mean)

            for i in constantcolsdict:
                df[i] = constantcolsdict[i]

            summed_dataframes.append(df)

        self.df = pd.concat(summed_dataframes)

        OpTempColumn = [i for i in self.df.columns if 'Zone Thermostat Operative Temperature [C](Hourly)' in i]
        self.occBZlist_colon = [i.split(' ')[0][:-5] for i in OpTempColumn]
        self.occBZlist_colon = list(dict.fromkeys(self.occBZlist_colon))
        self.occupied_zone_list = self.occBZlist_colon

        occBZlist_underscore = [i.replace(':', '_') for i in self.occBZlist_colon]

        self.hvacBZlist_colon = [i.split(' ')[0]
                                 for i
                                 in [i
                                     for i
                                     in self.df.columns
                                     if 'Cooling Coil Total Cooling Rate' in i
                                     ]
                                 ]

        self.hvacBZlist_colon = list(dict.fromkeys(self.hvacBZlist_colon))
        # hvacBZlist_underscore = [i.replace(':', '_') for i in self.hvac_zone_list]
        self.hvac_zone_list = self.hvacBZlist_colon

        self.block_list = [i.split(':')[0] for i in self.occBZlist_colon]
        self.block_list = list(dict.fromkeys(self.block_list))

        renamezonesdict = {}
        for i in range(len(occBZlist_underscore)):
            for j in self.df.columns:
                if occBZlist_underscore[i].lower() in j.lower():
                    temp = {j: j.replace(occBZlist_underscore[i], self.occBZlist_colon[i])}
                    renamezonesdict.update(temp)

        self.df = self.df.rename(columns=renamezonesdict)

        for i in self.df.columns:
            if 'VRF OUTDOOR UNIT' in i:
                self.df[i] = self.df[i]/3600

        renamedict = {}

        for i in self.df.columns:
            if 'VRF OUTDOOR UNIT' in i:
                temp = {i: i.replace('[J]', '[W]')}
                renamedict.update(temp)

        self.df = self.df.rename(columns=renamedict)

        BZoutputDict = {
            'VRF INDOOR UNIT': 'Total Energy Demand (Wh)',
            'VRF OUTDOOR UNIT': 'Total Energy Consumption (Wh)'
        }

        for output in BZoutputDict:
            for block_zone in self.hvacBZlist_colon:
                self.df[f'{block_zone}' + '_' + BZoutputDict[output] + ' [summed]_pymod'] = self.df[
                    [i for i in self.df.columns
                     if block_zone.lower() in i.lower() and output in i and '_pymod' not in i]
                ].sum(axis=1)

        outputdict = {
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
            'VRF Heat Pump Cooling Electricity Energy': 'VRF Heat Pump Cooling Electricity Energy (Wh)',
            'VRF Heat Pump Heating Electricity Energy': 'VRF Heat Pump Heating Electricity Energy (Wh)',
            'Coil': 'Total Energy Demand (Wh)',
            'VRF OUTDOOR UNIT': 'Total Energy Consumption (Wh)',
            'Zone Air Volume': 'Zone Air Volume (m3)',
            'Zone Floor Area': 'Zone Floor Area (m2)'
            }

        if any('block' in i for i in level):
            for output in outputdict:
                for block in self.block_list:
                    if any('sum' in j for j in level_sum_or_mean):
                        self.df[f'{block}' + '_Total_' + outputdict[output] + ' [summed]_pymod'] = self.df[
                            [i for i in self.df.columns
                             if block.lower() in i.lower() and output in i and '_pymod' not in i]
                        ].sum(axis=1)
                    if any('mean' in j for j in level_sum_or_mean):
                        self.df[f'{block}' + '_Total_' + outputdict[output] + ' [mean]_pymod'] = self.df[
                            [i for i in self.df.columns
                             if block.lower() in i.lower() and output in i and '_pymod' not in i]
                        ].mean(axis=1)
        if any('building' in i for i in level):
            for output in outputdict:
                if any('sum' in j for j in level_sum_or_mean):
                    self.df['Building_Total_' + outputdict[output] + ' [summed]_pymod'] = self.df[
                        [i for i in self.df.columns
                         if output in i and '_pymod' not in i]
                    ].sum(axis=1)
                if any('mean' in j for j in level_sum_or_mean):
                    self.df['Building_Total_' + outputdict[output] + ' [mean]_pymod'] = self.df[
                        [i for i in self.df.columns
                         if output in i and '_pymod' not in i]
                    ].mean(axis=1)

        renamedict = {}
        for i in self.df.columns:
            if '[W]' in i:
                temp = {i: i.replace('[W]', '(Wh)')}
                renamedict.update(temp)
        self.df = self.df.rename(columns=renamedict)

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

        if normalised_energy_units:
            for i in self.df.columns:
                if '(Wh)' in i:
                    for j in self.hvacBZlist_colon:
                        if j in i:
                            self.df[i] = self.df[i] / self.df[
                                [i for i in self.df.columns
                                 if 'Zone Floor Area' in i
                                 and j.lower() in i.lower()][0]]
                    for k in self.block_list:
                        if k + '_Total_' in i:
                            self.df[i] = self.df[i] / self.df[
                                [i for i in self.df.columns
                                 if 'Zone Floor Area' in i
                                 and k.lower() + '_Total_'.lower() in i.lower()][0]]
                    if 'Building_Total_' in i:
                        self.df[i] = self.df[i] / self.df[
                            [i for i in self.df.columns
                             if 'Zone Floor Area' in i
                             and 'Building_Total_'.lower() in i.lower()][0]]
                    if 'Whole Building:Facility Total HVAC Electricity Demand Rate' in i:
                        self.df[i] = self.df[i] / self.df[
                            [i for i in self.df.columns
                             if 'Zone Floor Area' in i
                             and 'Building_Total_'.lower() in i.lower()][0]]

        if energy_units_in_kwh:
            for col in self.df.columns:
                if '(Wh)' in col:
                    self.df[col] = self.df[col] / 1000

        energy_units_dict = {}
        for i in self.df.columns:
            if '(Wh)' in i:
                temp = {i: i.replace('(Wh)', energy_units)}
                energy_units_dict.update(temp)
        self.df = self.df.rename(columns=energy_units_dict)

        self.df.set_axis(
            labels=[c[:-6] if c.endswith('_pymod') else c for c in self.df],
            axis=1,
            inplace=True
        )

        self.df[['Model',
                 'Adaptive Standard',
                 'Category',
                 'Comfort mode',
                 'HVAC mode',
                 'Ventilation control',
                 'VSToffset',
                 'MinOToffset',
                 'MaxWindSpeed',
                 'ASTtol',
                 'EPW']] = self.df['Source'].str.split('[', expand=True)

        self.df['Model'] = self.df['Model'].str[:-6]
        # self.df['Adaptive Standard'] = self.df['Adaptive Standard'].str[3:]
        # self.df['Category'] = self.df['Category'].str[3:]
        # self.df['Comfort mode'] = self.df['Comfort mode'].str[3:]
        # self.df['HVAC mode'] = self.df['HVAC mode'].str[3:]
        # self.df['Ventilation control'] = self.df['Ventilation control'].str[3:]
        # self.df['VSToffset'] = self.df['VSToffset'].str[3:]
        # self.df['MinOToffset'] = self.df['MinOToffset'].str[3:]
        # self.df['MaxWindSpeed'] = self.df['MaxWindSpeed'].str[3:]
        # self.df['ASTtol'] = self.df['ASTtol'].str[3:]
        self.df['EPW'] = self.df['EPW'].str[:-4]
        self.df['Source'] = self.df['Source'].str[:-4]

        self.df = self.df.set_index([pd.RangeIndex(len(self.df))])

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

            self.df['EPW_mod'] = self.df['EPW'].str.split('_')

            for i in range(len(self.df['EPW_mod'])):
                for j in self.df.loc[i, 'EPW_mod']:
                    if len(j) == 2:
                        self.df.loc[i, 'EPW_CountryCode'] = j
                    else:
                        self.df.loc[i, 'EPW_CountryCode'] = np.nan

                    for k in rcpdict:
                        for m in range(len(rcpdict[k])):
                            if j in rcpdict[k][m]:
                                self.df.loc[i, 'EPW_Scenario'] = k
                            else:
                                self.df.loc[i, 'EPW_Scenario'] = np.nan

                self.df.loc[i, 'EPW_Year'] = np.nan

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

            self.df = self.df.set_index([pd.RangeIndex(len(self.df))])

            #  if len <1
            data_cities['subcountry'] = data_cities['subcountry'].astype(str)
            data_countries['Name'] = data_countries['Name'].astype(str)
            data_countries['Code'] = data_countries['Code'].astype(str)

            locations = []
            for i in list(self.df['EPW_mod']):
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

            self.df['EPW_CountryCode'] = self.df['EPW_CountryCode'].astype(str)

        if manage_epw_names:
            for i in range(len(self.df['EPW_mod'])):
                for j in self.df.loc[i, 'EPW_mod']:
                    if j in rcp_present:
                        self.df.loc[i, 'EPW_Year'] = 'Present'
                    elif j in rcp:
                        continue
                    elif j.isnumeric():
                        self.df.loc[i, 'EPW_Year'] = int(j)
                    elif len(j) == 2:
                        continue
                    else:
                        if match_cities:
                            if isEPWformatValid:
                                for k in range(len(cities_df)):
                                    if self.df.loc[i, 'EPW_CountryCode'].lower() in cities_df.loc[k, 'country'].lower():
                                        self.df.loc[i, 'EPW_Country'] = cities_df.loc[k, 'country']
                                    if str(j).lower() in cities_df.loc[k, 'name'].lower():
                                        self.df.loc[i, 'EPW_City_or_subcountry'] = cities_df.loc[k, 'name']
                                    elif str(j).lower() in cities_df.loc[k, 'subcountry'].lower():
                                        self.df.loc[i, 'EPW_City_or_subcountry'] = cities_df.loc[k, 'name']
                                    elif str(j).isalnum():
                                        self.df.loc[i, 'EPW_City_or_subcountry'] = j.upper()
                                    else:
                                        self.df.loc[i, 'EPW_City_or_subcountry'] = j.capitalize()
                        else:
                            self.df.loc[i, 'EPW_City_or_subcountry'] = j.capitalize()

            self.df = self.df.drop(['EPW_mod'], axis=1)

        cols = self.df.columns.tolist()
        cols = cols[-15:] + cols[:-15]
        self.df = self.df[cols]
        self.df = self.df.set_index([pd.RangeIndex(len(self.df))])

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
                'Zone Thermostat Operative Temperature [C](Hourly)': 'Zone Thermostat Operative Temperature (°C)',
                'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)':
                    'EN16798-1 Running mean outdoor temperature (°C)',
                'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature [C](Hourly)':
                    'ASHRAE 55 Running mean outdoor temperature (°C)',
                'FORSCRIPT_AHST': 'FORSCRIPT_AHST',
                'FORSCRIPT_ACST': 'FORSCRIPT_ACST',
                'VRF Heat Pump Cooling Electricity Energy': 'Cooling Energy Consumption',
                'VRF Heat Pump Heating Electricity Energy': 'Heating Energy Consumption',
                'Heating Coil Heating Rate': 'Heating Energy Demand',
                'Cooling Coil Total Cooling Rate': 'Cooling Energy Demand'
            }

            renaming_criteria = {
                # 'Date/Time',
                'Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)':
                    'Site Outdoor Air Drybulb Temperature (°C)',
                'Environment:Site Wind Speed [m/s](Hourly)': 'Site Wind Speed (m/s)',
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

            for col in self.df.columns:
                for crit in renaming_criteria_bz:
                    if '[summed]' not in col and '[mean]' not in col:
                        if crit in col:
                            for block_zone in self.occBZlist_colon:
                                if block_zone in col:
                                    if energy_units in col:
                                        temp = {col: block_zone + '_' + renaming_criteria_bz[crit] + ' ' + energy_units}
                                        all_cols_renamed.update(temp)
                                    else:
                                        temp = {col: block_zone + '_' + renaming_criteria_bz[crit]}
                                        all_cols_renamed.update(temp)

            for col in self.df.columns:
                for crit in renaming_criteria:
                    if '[summed]' not in col and '[mean]' not in col:
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

            for col in self.df.columns:
                for crit in renaming_criteria_block:
                    for block in self.block_list:
                        if block + '_Total_' + crit in col:
                            if '[summed]' in col:
                                temp = {col: f'{block}_Total_{renaming_criteria_block[crit]} {energy_units} [summed]'}
                                all_cols_renamed.update(temp)
                            elif '[mean]' in col:
                                temp = {col: f'{block}_Total_{renaming_criteria_block[crit]} {energy_units} [mean]'}
                                all_cols_renamed.update(temp)
                    if 'Building_Total_' + crit in col:
                        if '[summed]' in col:
                            temp = {col: f'Building_Total_{renaming_criteria_block[crit]} {energy_units} [summed]'}
                            all_cols_renamed.update(temp)
                        if '[mean]' in col:
                            temp = {col: f'Building_Total_{renaming_criteria_block[crit]} {energy_units} [mean]'}
                            all_cols_renamed.update(temp)

            self.df = self.df.rename(columns=all_cols_renamed)

        self.indexcols = [
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
            'EPW',
            'Source',
            # 'col_to_pivot'
        ]
        if 'monthly' in self.frequency:
            self.indexcols.append('Month')
        if 'daily' in self.frequency:
            self.indexcols.append('Day')
        if 'hourly' in self.frequency:
            self.indexcols.append('Hour')
        if 'timestep' in self.frequency:
            self.indexcols.append('Minute')
        if manage_epw_names:
            self.indexcols.extend([
                'EPW_CountryCode',
                'EPW_Scenario',
                'EPW_Year',
                'EPW_City_or_subcountry'
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



    def returndf(self):
        return self.df

    def hvac_zone_list(self):
        return self.hvac_zone_list

    def occupied_zone_list(self):
        return self.occupied_zone_list

    def block_list(self):
        return self.block_list()

    def wrangled_table(self,
                       vars_to_gather=None,
                       baseline: str = None,
                       comparison_cols=None):
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
            'EPW'
            ]

        self.indexcols.append('col_to_pivot')

        while (not(all(elem in available_vars_to_gather for elem in vars_to_gather))
               or len(vars_to_gather) != len(set(vars_to_gather))):
            print('Some of the variables to be gathered are not available or are duplicated:')
            print(vars_to_gather)
            print('The list of available variables to be gathered is:')
            print(available_vars_to_gather)
            vars_to_gather = (list(str(var)
                                   for var
                                   in input("Enter the variables to be gathered separated by semicolon: ").split(';')))

        self.wrangled_df = self.df

        if 'Month' in self.wrangled_df.columns:
            self.wrangled_df['col_to_pivot'] = (self.wrangled_df[vars_to_gather].agg('['.join, axis=1) +
                                                self.wrangled_df['Month'].astype(str) +
                                                '[Month')
        else:
            self.wrangled_df['col_to_pivot'] = self.wrangled_df[vars_to_gather].agg('['.join, axis=1)

        self.df['col_to_pivot'] = self.wrangled_df['col_to_pivot']

        self.wrangled_df = self.wrangled_df.pivot_table(
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
                self.wrangled_df[f'{i}_Runperiod_Total'] = self.wrangled_df[
                    [j for j in self.wrangled_df.columns
                     if i in j]
                ].sum(axis=1)

            for j in other_than_baseline:
                for i in list(dict.fromkeys(self.df['Month'])):
                    if any('relative' in k for k in comparison_cols):
                        self.wrangled_df[f'1-({j}/{baseline})_{i}_Month'] = (
                                1 -
                                (self.wrangled_df[j + f'_{i}_Month'] / self.wrangled_df[baseline + f'_{i}_Month'])
                        )
                    if any('absolute' in k for k in comparison_cols):
                        self.wrangled_df[f'{baseline}-{j}_{i}_Month'] = (
                                self.wrangled_df[baseline + f'_{i}_Month'] - self.wrangled_df[j + f'_{i}_Month']
                        )
                if any('relative' in k for k in comparison_cols):
                    self.wrangled_df[f'1-({j}/{baseline})_Runperiod_Total'] = (
                            1 -
                            (self.wrangled_df[j + '_Runperiod_Total'] / self.wrangled_df[baseline + '_Runperiod_Total'])
                    )
                if any('absolute' in k for k in comparison_cols):
                    self.wrangled_df[f'{baseline} - {j}_Runperiod_Total'] = (
                            self.wrangled_df[baseline + '_Runperiod_Total'] - self.wrangled_df[j + '_Runperiod_Total']
                    )
        else:
            for j in other_than_baseline:
                if any('relative' in k for k in comparison_cols):
                    self.wrangled_df[f'1-({j}/{baseline})'] = (
                            1 -
                            (self.wrangled_df[j] / self.wrangled_df[baseline])
                    )
                if any('absolute' in k for k in comparison_cols):
                    self.wrangled_df[f'{baseline} - {j}'] = (
                            self.wrangled_df[baseline] - self.wrangled_df[j]
                    )
