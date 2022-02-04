class Table:

    def __init__(self,
                 frequency: str = None,
                 sum_or_mean: str = None,
                 standard_outputs: bool = None,
                 level=None,
                 level_sum_or_mean=None,
                 match_cities: bool = False,
                 normalised_energy_units: bool = False):
        if level_sum_or_mean is None:
            level_sum_or_mean = []
        if level is None:
            level = []

        import os
        import pandas as pd
        from pathlib import Path
        import datapackage
        import glob
        import numpy as np

        self.frequency = frequency
        self.normalised_energy_units = normalised_energy_units

        # todo check if glob.glob works with in terms of package, if not switch back to sorted
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
            'EMS:Comfortable Hours',
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
        occBZlist_colon = [i.split(' ')[0][:-5] for i in OpTempColumn]
        occBZlist_colon = list(dict.fromkeys(occBZlist_colon))
        occBZlist_underscore = [i.replace(':', '_') for i in occBZlist_colon]

        self.hvacBZlist_colon = [i.split(' ')[0]
                            for i
                            in [i
                                for i
                                in self.df.columns
                                if 'Cooling Coil Total Cooling Rate' in i
                                ]
                            ]

        self.hvacBZlist_colon = list(dict.fromkeys(self.hvacBZlist_colon))
        hvacBZlist_underscore = [i.replace(':', '_') for i in self.hvacBZlist_colon]

        self.block_list = [i.split(':')[0] for i in occBZlist_colon]
        self.block_list = list(dict.fromkeys(self.block_list))

        renamezonesdict = {}
        for i in range(len(occBZlist_underscore)):
            for j in self.df.columns:
                if occBZlist_underscore[i].lower() in j.lower():
                    temp = {j: j.replace(occBZlist_underscore[i], occBZlist_colon[i])}
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
            'Cooling Coil Total Cooling Rate': 'Cooling Energy Demand (Cooling Coil Total Cooling Rate) (Wh)',
            'Heating Coil Heating Rate': 'Heating Energy Demand (Heating Coil Heating Rate) (Wh)',
            'VRF Heat Pump Cooling Electricity Energy': 'Cooling Energy Consumption (VRF Heat Pump Cooling Electricity Energy) (Wh)',
            'VRF Heat Pump Heating Electricity Energy': 'Heating Energy Consumption (VRF Heat Pump Heating Electricity Energy) (Wh)',
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

        if normalised_energy_units:
            for i in self.df.columns:
                if '[W]' in i or '(Wh)' in i:
                    for j in self.hvacBZlist_colon:
                        if j in i:
                            self.df[i] = self.df[i] / self.df[
                                [i for i in self.df.columns
                                 if 'Zone Floor Area' in i
                                 and j.lower() in i.lower()][0]]
                    for k in self.block_list:
                        if k+'_Total_' in i:
                            self.df[i] = self.df[i] / self.df[
                                [i for i in self.df.columns
                                 if 'Zone Floor Area' in i
                                 and k.lower()+'_Total_'.lower() in i.lower()][0]]
                    if 'Building_Total_' in i:
                        self.df[i] = self.df[i] / self.df[
                            [i for i in self.df.columns
                             if 'Zone Floor Area' in i
                             and 'Building_Total_'.lower() in i.lower()][0]]

            normUnitsDict = {}

            for i in self.df.columns:
                if '(Wh)' in i:
                    temp = {i: i.replace('(Wh)', '(Wh/m2)')}
                    normUnitsDict.update(temp)

            self.df = self.df.rename(columns=normUnitsDict)

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
        self.df['Adaptive Standard'] = self.df['Adaptive Standard'].str[3:]
        self.df['Category'] = self.df['Category'].str[3:]
        self.df['Comfort mode'] = self.df['Comfort mode'].str[3:]
        self.df['HVAC mode'] = self.df['HVAC mode'].str[3:]
        self.df['Ventilation control'] = self.df['Ventilation control'].str[3:]
        self.df['VSToffset'] = self.df['VSToffset'].str[3:]
        self.df['MinOToffset'] = self.df['MinOToffset'].str[3:]
        self.df['MaxWindSpeed'] = self.df['MaxWindSpeed'].str[3:]
        self.df['ASTtol'] = self.df['ASTtol'].str[3:]
        self.df['EPW'] = self.df['EPW'].str[:-4]
        self.df['Source'] = self.df['Source'].str[:-4]

        self.df = self.df.set_index([pd.RangeIndex(len(self.df))])

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

            # todo if len <1
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

    def returndf(self):
        return self.df

    def energy_demand_table(self,
                            stages_no: int = None,
                            var_to_gather_1: str = None,
                            var_to_gather_2: str = None,
                            var_to_gather_3: str = None,
                            baseline: str = None):
        # todo easy-use mode (accim.data to show the var_to_gather available and the baselines available depending on the input data)

        import numpy as np

        enDemCols = [col for col in self.df.columns if 'Cooling Coil Total Cooling Rate' in col
                     or 'Heating Coil Heating Rate' in col
                     or '_Total Energy Demand' in col
                     or '_Total_Cooling Energy Demand' in col
                     or '_Total_Heating Energy Demand' in col]

        indexcols = [
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
            'EPW_CountryCode',
            'EPW_Scenario',
            'EPW_Year',
            'EPW_City_or_subcountry',
            'Source',
            'col_to_pivot'
        ]
        if 'monthly' in self.frequency:
            indexcols.append('Month')
        if 'daily' in self.frequency:
            indexcols.append('Day')
        if 'hourly' in self.frequency:
            indexcols.append('Hour')
        if 'timestep' in self.frequency:
            indexcols.append('Minute')

        # var_to_gather_1 = 'Adaptive Standard'

        self.df['col_to_pivot'] = 'temp'
        orig_indexcols = indexcols

        self.enDemDf = self.df[indexcols + enDemCols]

        if stages_no == 1:
            if 'Month' in self.enDemDf.columns:
                self.enDemDf['col_to_pivot'] = (self.enDemDf[var_to_gather_1] +
                                           '_' +
                                           self.enDemDf['Month'].astype(str) +
                                           '_Month')
            else:
                self.enDemDf['col_to_pivot'] = self.enDemDf[var_to_gather_1]
        elif stages_no == 2:
            if 'Month' in self.enDemDf.columns:
                self.enDemDf['col_to_pivot'] = (self.enDemDf[var_to_gather_1] +
                                           '_' +
                                           self.enDemDf[var_to_gather_2] +
                                           '_' +
                                           self.enDemDf['Month'].astype(str) +
                                           '_Month')
            else:
                self.enDemDf['col_to_pivot'] = (self.enDemDf[var_to_gather_1] +
                                            '_' +
                                           self.enDemDf[var_to_gather_2]
                                           )
        elif stages_no == 3:
            if 'Month' in self.enDemDf.columns:
                self.enDemDf['col_to_pivot'] = (self.enDemDf[var_to_gather_1] +
                                           '_' +
                                           self.enDemDf[var_to_gather_2] +
                                           '_' +
                                           self.enDemDf[var_to_gather_3] +
                                           '_' +
                                           self.enDemDf['Month'].astype(str) +
                                           '_Month')
            else:
                self.enDemDf['col_to_pivot'] = (self.enDemDf[var_to_gather_1] +
                                            '_' +
                                           self.enDemDf[var_to_gather_2] +
                                           '_' +
                                           self.enDemDf[var_to_gather_3]
                                           )

        self.df['col_to_pivot'] = self.enDemDf['col_to_pivot']

        self.enDemDf = self.enDemDf.pivot_table(
            index=indexcols.remove('col_to_pivot'),
            columns='col_to_pivot',
            values=enDemCols,
            aggfunc=np.sum,
            fill_value=0)

        # baseline = 'ASHRAE55'
        var_to_gather_values = list(dict.fromkeys(self.df['col_to_pivot']))
        other_than_baseline = list(set(var_to_gather_values) - set([baseline]))

        self.df = self.df.drop('col_to_pivot', axis=1)

        # sumando mensuales para hacer runperiod

        if 'Month' in self.df.columns:
            for i in var_to_gather_values:
                self.enDemDf[f'{i}_Runperiod_Total'] = self.enDemDf[
                    [j for j in self.enDemDf.columns
                     if i in j]
                ].sum(axis=1)

            for j in other_than_baseline:
                for i in list(dict.fromkeys(self.df['Month'])):
                    self.enDemDf[f'1-({baseline}/{j})_{i}_Month'] = (
                            1-
                            (self.enDemDf[j + f'_{i}_Month'] / self.enDemDf[baseline + f'_{i}_Month'])
                    )
                self.enDemDf[f'1-({baseline}/{j})_Runperiod_Total'] = (
                        1-
                        (self.enDemDf[j + '_Runperiod_Total'] / self.enDemDf[baseline + '_Runperiod_Total'])
                )
        else:
            for j in other_than_baseline:
                self.enDemDf[f'1-({baseline}/{j})'] = (
                        1 -
                        (self.enDemDf[j] / self.enDemDf[baseline])
                )

        renametabledict = {}
        if self.normalised_energy_units:
            energy_units = '(Wh/m2)'
        else:
            energy_units = '(Wh)'

        for i in self.enDemDf.index:
            for j in ['Heating', 'Cooling', 'Total']:
                for block in self.block_list:
                    if block+'_Total_'+j in i:
                        if '[summed]' in i:
                            temp = {i: f'{block}_Total_{j} Energy Demand {energy_units} [summed]'}
                            renametabledict.update(temp)
                        if '[mean]' in i:
                            temp = {i: f'{block}_Total_{j} Energy Demand {energy_units} [mean]'}
                            renametabledict.update(temp)
                if 'Building_Total_' + j in i:
                    if '[summed]' in i:
                        temp = {i: f'Building_Total_{j} Energy Demand {energy_units} [summed]'}
                        renametabledict.update(temp)
                    if '[mean]' in i:
                        temp = {i: f'Building_Total_{j} Energy Demand {energy_units} [mean]'}
                        renametabledict.update(temp)
            for k in self.hvacBZlist_colon:
                if 'Total Cooling Rate'.lower() in i.lower() and k.lower() in i.lower():
                    temp = {i: f'{k}_Cooling Energy Demand {energy_units}'}
                    renametabledict.update(temp)
                if 'Heating Rate'.lower() in i.lower() and k.lower() in i.lower():
                    temp = {i: f'{k}_Heating Energy Demand {energy_units}'}
                    renametabledict.update(temp)
                if 'Total Energy Demand'.lower() in i.lower() and k.lower() in i.lower():
                    temp = {i: f'{k}_Total Energy Demand {energy_units}'}
                    renametabledict.update(temp)

        self.enDemDf = self.enDemDf.rename(index=renametabledict)
