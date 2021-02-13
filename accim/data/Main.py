class Table():
    import os
    import pandas as pd
    from pathlib import Path
    import numpy as np
    from collections import defaultdict
    import copy
    pass

    def __init__(self):
        import os
        import pandas as pd
        from pathlib import Path
        import numpy as np
        from collections import defaultdict
        import copy
        self.source_files = sorted(Path(os.getcwd()).glob('*.csv'))

        self.source_files_sample = sorted(Path(os.getcwd()).glob('*.csv'))[0]
        df_sample = pd.DataFrame(pd.read_csv(self.source_files_sample))
        OpTempColumn = [i for i in df_sample.columns if 'Operative Temperature [C](Hourly)' in i]
        self.block_zone_list_colon = [i.split(' ')[0] for i in OpTempColumn]
        self.block_zone_list_colon = list(dict.fromkeys(self.block_zone_list_colon))
        self.block_zone_list_colon = list(dict.fromkeys(self.block_zone_list_colon))
        self.block_zone_list_colon = [i[:-5] for i in self.block_zone_list_colon]
        self.block_zone_list_underscore = [i.replace(':', '_') for i in self.block_zone_list_colon]
        self.block_list = [i.split(':')[0] for i in self.block_zone_list_colon]
        self.block_list = list(dict.fromkeys(self.block_list))
        self.allcols = df_sample.columns

        self.cities = ['Canfranc',
                       'Bilbao',
                       'Huesca',
                       'Coruna',
                       'Sevilla',
                       'Valencia',
                       'Zaragoza',
                       'Fuerteventura']
        self.years = ['2015',
                      '2016',
                      '2017',
                      '2018']

        print(self.source_files)
        print(os.getcwd())
        summed_dataframes = []
        for file in self.source_files:
            self.df = pd.DataFrame(pd.read_csv(file))
            self.df['source'] = file.name
            self.vrfCols = [col for col in self.df.columns if 'VRF' in col]
            self.vrfCols = [col for col in self.vrfCols if 'OUTDOOR' in col]
            self.vrfCols = [col for col in self.vrfCols if 'Hourly' in col]
            self.vrfCols_renamed = [i.split('_')[1].rstrip() for i in self.vrfCols]
            self.vrfCols_renamed = [i.split(' ') for i in self.vrfCols_renamed]
            self.vrfCols_renamed = [[i for i in nested if
                                     i != 'Heat' and
                                     i != 'Pump' and
                                     i != 'Electricity' and
                                     i != 'Energy' and
                                     i != '[J](Hourly)'] for nested in self.vrfCols_renamed]
            self.block_zone_list_vrf = [i[0] for i in self.vrfCols_renamed]
            self.block_zone_list_vrf = list(dict.fromkeys(self.block_zone_list_vrf))
            self.block_list = [i.split(':')[0] for i in self.block_zone_list_vrf]
            self.block_list = list(dict.fromkeys(self.block_list))
            self.vrfCols_renamed = ['_'.join(i) for i in self.vrfCols_renamed]
            vofCols = [i for i in self.df.columns if 'Surface Venting Window or Door Opening Factor [](Hourly)' in i]
            VOFsample = []
            for block_zone in self.block_zone_list_colon:
                sublist = []
                for i in range(len(vofCols)):
                    if block_zone in vofCols[i]:
                        sublist.append(vofCols[i])
                VOFsample.append(sublist)
            VOFdef = [i[0] for i in VOFsample]
            self.vofCols_renamed = ['Ventilation Hours '+i.split('_')[0] for i in VOFdef]

            listresult = [
                'comfHoursNoAppCols',
                'comfHoursCols',
                'disAppHotHourCols',
                'disAppColdHourCols',
                'disNonAppHotHourCols',
                'disNonAppColdHourCols',
                ]
            originalcols = defaultdict(list)
            for i in range(len(self.allcols)):
                for block_zone in self.block_zone_list_underscore:
                    if f'EMS:Comfortable Hours_No Applicability_{block_zone} (summed) [H](Hourly)'.lower() in self.allcols[i].lower():
                        originalcols[listresult[0]].append(self.allcols[i])
                    elif f'EMS:Comfortable Hours_{block_zone} (summed) [H](Hourly)'.lower() in self.allcols[i].lower():
                        originalcols[listresult[1]].append(self.allcols[i])
                    elif f'EMS:Discomfortable Applicable Hot Hours_{block_zone} (summed) [H](Hourly)'.lower() in self.allcols[i].lower():
                        originalcols[listresult[2]].append(self.allcols[i])
                    elif f'EMS:Discomfortable Applicable Cold Hours_{block_zone} (summed) [H](Hourly)'.lower() in self.allcols[i].lower():
                        originalcols[listresult[3]].append(self.allcols[i])
                    elif f'EMS:Discomfortable Non Applicable Hot Hours_{block_zone} (summed) [H](Hourly)'.lower() in self.allcols[i].lower():
                        originalcols[listresult[4]].append(self.allcols[i])
                    elif f'EMS:Discomfortable Non Applicable Cold Hours_{block_zone} (summed) [H](Hourly)'.lower() in self.allcols[i].lower():
                        originalcols[listresult[5]].append(self.allcols[i])
            renamedcols = copy.deepcopy(originalcols)
            for block_zone in self.block_zone_list_underscore:
                for i in range(len(listresult)):
                    for j in range(len(originalcols[listresult[i]])):
                        if f'EMS:Comfortable Hours_No Applicability_{block_zone} (summed) [H](Hourly)'.lower() in originalcols[listresult[i]][j].lower():
                            renamedcols[listresult[i]][j] = f'Comfortable Hours_No Applicability {block_zone}'
                        elif f'EMS:Comfortable Hours_{block_zone} (summed) [H](Hourly)'.lower() in originalcols[listresult[i]][j].lower():
                            renamedcols[listresult[i]][j] = f'Comfortable Hours {block_zone}'
                        elif f'EMS:Discomfortable Applicable Hot Hours_{block_zone} (summed) [H](Hourly)'.lower() in originalcols[listresult[i]][j].lower():
                            renamedcols[listresult[i]][j] = f'Discomfortable Applicable Hot Hours {block_zone}'
                        elif f'EMS:Discomfortable Applicable Cold Hours_{block_zone} (summed) [H](Hourly)'.lower() in originalcols[listresult[i]][j].lower():
                            renamedcols[listresult[i]][j] = f'Discomfortable Applicable Cold Hours {block_zone}'
                        elif f'EMS:Discomfortable Non Applicable Hot Hours_{block_zone} (summed) [H](Hourly)'.lower() in originalcols[listresult[i]][j].lower():
                            renamedcols[listresult[i]][j] = f'Discomfortable Non Applicable Hot Hours {block_zone}'
                        elif f'EMS:Discomfortable Non Applicable Cold Hours_{block_zone} (summed) [H](Hourly)'.lower() in originalcols[listresult[i]][j].lower():
                            renamedcols[listresult[i]][j] = f'Discomfortable Non Applicable Cold Hours {block_zone}'
            self.df = self.df.loc[:, self.vrfCols +
                                  VOFdef +
                                  originalcols['comfHoursNoAppCols'] +
                                  originalcols['comfHoursCols'] +
                                  originalcols['disAppHotHourCols'] +
                                  originalcols['disAppColdHourCols'] +
                                  originalcols['disNonAppHotHourCols'] +
                                  originalcols['disNonAppColdHourCols']
                                  ]
            colslist = [*self.vrfCols_renamed,
                        *self.vofCols_renamed,
                        *renamedcols['comfHoursNoAppCols'],
                        *renamedcols['comfHoursCols'],
                        *renamedcols['disAppHotHourCols'],
                        *renamedcols['disAppColdHourCols'],
                        *renamedcols['disNonAppHotHourCols'],
                        *renamedcols['disNonAppColdHourCols']]

            self.df.columns = colslist
            self.df['source'] = file
            self.df = self.df.groupby('source').agg('sum')
            self.df['source_temp'] = file
            summed_dataframes.append(self.df)
        self.summed_tot_df = pd.concat(summed_dataframes)
        print(self.summed_tot_df)
        self.summed_tot_df[['model',
                            'standard',
                            'cat',
                            'comfMod',
                            'hvacMode',
                            'ventControl',
                            'ventOffset',
                            'minOutTemp',
                            'maxWindSpeed',
                            'astTol',
                            'city_year']] = self.summed_tot_df['source_temp'].astype(str).str.extract('.+\\\\(.+_pymod)\[(AS_\w+)\[(CA_\w)\[(CM_\w)\[(HM_\w)\[(VC_\w)\[(VO_\w.\w)\[(MT_\w\w.\w)\[(MW_\w\w.\w)\[(AT_\w.\w)\[(.+).csv', expand=True)
        del self.summed_tot_df['source_temp']
        self.summed_tot_df['model'] = self.summed_tot_df['model'].str[:-6]
        self.summed_tot_df['standard'] = self.summed_tot_df['standard'].str[3:]
        self.summed_tot_df['cat'] = self.summed_tot_df['cat'].str[3:]
        self.summed_tot_df['comfMod'] = self.summed_tot_df['comfMod'].str[3:]
        self.summed_tot_df['hvacMode'] = self.summed_tot_df['hvacMode'].str[3:]
        self.summed_tot_df['ventControl'] = self.summed_tot_df['ventControl'].str[3:]
        self.summed_tot_df['ventOffset'] = self.summed_tot_df['ventOffset'].str[3:]
        self.summed_tot_df['minOutTemp'] = self.summed_tot_df['minOutTemp'].str[3:]
        self.summed_tot_df['maxWindSpeed'] = self.summed_tot_df['maxWindSpeed'].str[3:]
        self.summed_tot_df['astTol'] = self.summed_tot_df['astTol'].str[3:]
        for year in self.years:
            for city in self.cities:
                self.summed_tot_df['city_year'] = np.where(
                    (self.summed_tot_df['city_year'].str.contains(city, case=False)) &
                    (self.summed_tot_df['city_year'].str.contains(year, case=False)),
                    city+'_'+year,
                    self.summed_tot_df['city_year'])
        self.summed_tot_df[['city', 'year']] = self.summed_tot_df['city_year'].str.extract(r'(.+)_(.+)', expand=True)
        del self.summed_tot_df['city_year']

    def EnergyConsumptionTable(self):
        """Generate the Energy consumption table for csv files in\
        current working directory."""
        import os
        multiindex = ['model',
                      'standard',
                      'cat',
                      'comfMod',
                      'hvacMode',
                      'ventControl',
                      'ventOffset',
                      'minOutTemp',
                      'maxWindSpeed',
                      'astTol',
                      'city',
                      'year']

        self.EnergyConsumpTable = self.summed_tot_df.loc[:, multiindex + self.vrfCols_renamed]
        self.EnergyConsumpTable = self.EnergyConsumpTable.apply(lambda x: x/3600000 if x.name in self.vrfCols_renamed else x)
        for block in self.block_list:
            print(block)
            self.EnergyConsumpTable[f'{block}_Total'] = self.EnergyConsumpTable[[i for i in self.EnergyConsumpTable.columns if block in i]].sum(axis=1)
            print('f{block}_Total')
            self.EnergyConsumpTable[f'{block}_Heating'] = self.EnergyConsumpTable[[i for i in self.EnergyConsumpTable.columns if block in i and '_Heating' in i]].sum(axis=1)
            print(f'{block}_Heating')
            self.EnergyConsumpTable[f'{block}_Cooling'] = self.EnergyConsumpTable[[i for i in self.EnergyConsumpTable.columns if block in i and '_Cooling' in i]].sum(axis=1)
            print(f'{block}_Cooling')
        for block_zone in self.block_zone_list_vrf:
            print(block_zone)
            self.EnergyConsumpTable[f'{block_zone}_Total'] = self.EnergyConsumpTable[f'{block_zone}_Heating'] + self.EnergyConsumpTable[f'{block_zone}_Cooling']
        self.EnergyConsumpTable['Total Heating'] = self.EnergyConsumpTable[[i for i in self.EnergyConsumpTable.columns if 'Heating' in i and 'VRF' not in i]].sum(axis=1)
        self.EnergyConsumpTable['Total Cooling'] = self.EnergyConsumpTable[[i for i in self.EnergyConsumpTable.columns if 'Cooling' in i and 'VRF' not in i]].sum(axis=1)
        self.EnergyConsumpTable['Total'] = self.EnergyConsumpTable['Total Cooling'] + self.EnergyConsumpTable['Total Heating']
        block_zone_cols = [i for i in self.EnergyConsumpTable.columns if 'VRF' in i]
        block_cols = []
        for i in range(len(self.EnergyConsumpTable.columns)):
            for block in self.block_list:
                if block in self.EnergyConsumpTable.columns[i] and 'VRF' not in self.EnergyConsumpTable.columns[i]:
                    block_cols.append(self.EnergyConsumpTable.columns[i])
        block_cols
        total_cols = ['Total Heating', 'Total Cooling', 'Total']
        colsorder = multiindex+total_cols
        self.EnergyConsumpTable = self.EnergyConsumpTable.loc[:, colsorder]
        self.EnergyConsumpTable = self.EnergyConsumpTable.reindex(columns=colsorder)
        return self.EnergyConsumpTable
        self.EnergyConsumpTable.to_excel(excel_writer=os.getcwd() +
                                         '/Energy consumption table.xlsx',
                                         sheet_name='Total Energy Consumption',
                                         float_format="%.2f",
                                         engine='xlsxwriter')
        
    def EnergyConsumpHorBarPlot(self):
        """Generate the Energy consumption horizontal barplot\
            from the EnergyConsumptionTable."""
        #intenta buscar el archivo os.getcwd() +'/Energy consumption table.xlsx' o self.EnergyConsumptionTable, y si no existe, self.EnergyConsumptionTable() y partimos de self.EnergyConsumptionTable
        pass
