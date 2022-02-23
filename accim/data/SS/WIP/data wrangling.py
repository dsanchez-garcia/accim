# import os
# import pandas as pd
# from pathlib import Path
# import numpy as np
# from collections import defaultdict
# import copy
# 
# df = pd.read_csv(r'C:\Users\user\PycharmProjects\accim\accim\data\WIP\
#                 TestModel_onlyGeometryForVRFsystem_V960_pymod'
#                  r'[AS_JPN[CA_1[CM_3[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[JPN_Tokyo.csv')
# 
# df.columns
# source_files = sorted(Path(os.getcwd()).glob('*.csv'))


# from accim.data import Main
# z = Main.Table()
# z.EnergyConsumptionTable()


import os
import pandas as pd
from pathlib import Path
import numpy as np
from collections import defaultdict
import copy

source_files = sorted(Path(os.getcwd()).glob('*.csv'))

source_files_sample = sorted(Path(os.getcwd()).glob('*.csv'))[0]
df_sample = pd.DataFrame(pd.read_csv(source_files_sample))
OpTempColumn = [i for i in df_sample.columns if 'Operative Temperature [C](Hourly)' in i]
block_zone_list_colon = [i.split(' ')[0] for i in OpTempColumn]
block_zone_list_colon = list(dict.fromkeys(block_zone_list_colon))
block_zone_list_colon = list(dict.fromkeys(block_zone_list_colon))
block_zone_list_colon = [i[:-5] for i in block_zone_list_colon]
block_zone_list_underscore = [i.replace(':', '_') for i in block_zone_list_colon]
block_list = [i.split(':')[0] for i in block_zone_list_colon]
block_list = list(dict.fromkeys(block_list))
allcols = df_sample.columns

cities = ['Canfranc',
               'Bilbao',
               'Huesca',
               'Coruna',
               'Sevilla',
               'Valencia',
               'Zaragoza',
               'Fuerteventura']
years = ['2015',
              '2016',
              '2017',
              '2018']

print(source_files)
print(os.getcwd())
summed_dataframes = []
for file in source_files:
    df = pd.DataFrame(pd.read_csv(file))
    df['source'] = file.name
    vrfCols = [col for col in df.columns if 'VRF' in col]
    vrfCols = [col for col in vrfCols if 'OUTDOOR' in col]
    vrfCols = [col for col in vrfCols if 'Hourly' in col]
    vrfCols_renamed = [i.split('_')[1].rstrip() for i in vrfCols]
    vrfCols_renamed = [i.split(' ') for i in vrfCols_renamed]
    vrfCols_renamed = [[i for i in nested if
                             i != 'Heat' and
                             i != 'Pump' and
                             i != 'Electricity' and
                             i != 'Energy' and
                             i != '[J](Hourly)'] for nested in vrfCols_renamed]
    block_zone_list_vrf = [i[0] for i in vrfCols_renamed]
    block_zone_list_vrf = list(dict.fromkeys(block_zone_list_vrf))
    block_list = [i.split(':')[0] for i in block_zone_list_vrf]
    block_list = list(dict.fromkeys(block_list))
    vrfCols_renamed = ['_'.join(i) for i in vrfCols_renamed]
    vofCols = [i for i in df.columns if 'Surface Venting Window or Door Opening Factor [](Hourly)' in i]
    VOFsample = []
    for block_zone in block_zone_list_colon:
        sublist = []
        for i in range(len(vofCols)):
            if block_zone in vofCols[i]:
                sublist.append(vofCols[i])
        VOFsample.append(sublist)
    VOFdef = [i[0] for i in VOFsample]
    vofCols_renamed = ['Ventilation Hours ' + i.split('_')[0] for i in VOFdef]

    listresult = [
        'comfHoursNoAppCols',
        'comfHoursCols',
        'disAppHotHourCols',
        'disAppColdHourCols',
        'disNonAppHotHourCols',
        'disNonAppColdHourCols',
    ]
    originalcols = defaultdict(list)
    for i in range(len(allcols)):
        for block_zone in block_zone_list_underscore:
            if f'EMS:Comfortable Hours_No Applicability_{block_zone} (summed) [H](Hourly)'.lower() in allcols[
                i].lower():
                originalcols[listresult[0]].append(allcols[i])
            elif f'EMS:Comfortable Hours_{block_zone} (summed) [H](Hourly)'.lower() in allcols[i].lower():
                originalcols[listresult[1]].append(allcols[i])
            elif f'EMS:Discomfortable Applicable Hot Hours_{block_zone} (summed) [H](Hourly)'.lower() in allcols[
                i].lower():
                originalcols[listresult[2]].append(allcols[i])
            elif f'EMS:Discomfortable Applicable Cold Hours_{block_zone} (summed) [H](Hourly)'.lower() in allcols[
                i].lower():
                originalcols[listresult[3]].append(allcols[i])
            elif f'EMS:Discomfortable Non Applicable Hot Hours_{block_zone} (summed) [H](Hourly)'.lower() in \
                    allcols[i].lower():
                originalcols[listresult[4]].append(allcols[i])
            elif f'EMS:Discomfortable Non Applicable Cold Hours_{block_zone} (summed) [H](Hourly)'.lower() in \
                    allcols[i].lower():
                originalcols[listresult[5]].append(allcols[i])
    renamedcols = copy.deepcopy(originalcols)
    for block_zone in block_zone_list_underscore:
        for i in range(len(listresult)):
            for j in range(len(originalcols[listresult[i]])):
                if f'EMS:Comfortable Hours_No Applicability_{block_zone} (summed) [H](Hourly)'.lower() in \
                        originalcols[listresult[i]][j].lower():
                    renamedcols[listresult[i]][j] = f'Comfortable Hours_No Applicability {block_zone}'
                elif f'EMS:Comfortable Hours_{block_zone} (summed) [H](Hourly)'.lower() in originalcols[listresult[i]][
                    j].lower():
                    renamedcols[listresult[i]][j] = f'Comfortable Hours {block_zone}'
                elif f'EMS:Discomfortable Applicable Hot Hours_{block_zone} (summed) [H](Hourly)'.lower() in \
                        originalcols[listresult[i]][j].lower():
                    renamedcols[listresult[i]][j] = f'Discomfortable Applicable Hot Hours {block_zone}'
                elif f'EMS:Discomfortable Applicable Cold Hours_{block_zone} (summed) [H](Hourly)'.lower() in \
                        originalcols[listresult[i]][j].lower():
                    renamedcols[listresult[i]][j] = f'Discomfortable Applicable Cold Hours {block_zone}'
                elif f'EMS:Discomfortable Non Applicable Hot Hours_{block_zone} (summed) [H](Hourly)'.lower() in \
                        originalcols[listresult[i]][j].lower():
                    renamedcols[listresult[i]][j] = f'Discomfortable Non Applicable Hot Hours {block_zone}'
                elif f'EMS:Discomfortable Non Applicable Cold Hours_{block_zone} (summed) [H](Hourly)'.lower() in \
                        originalcols[listresult[i]][j].lower():
                    renamedcols[listresult[i]][j] = f'Discomfortable Non Applicable Cold Hours {block_zone}'
    df = df.loc[:, vrfCols +
                             VOFdef +
                             originalcols['comfHoursNoAppCols'] +
                             originalcols['comfHoursCols'] +
                             originalcols['disAppHotHourCols'] +
                             originalcols['disAppColdHourCols'] +
                             originalcols['disNonAppHotHourCols'] +
                             originalcols['disNonAppColdHourCols']
              ]
    colslist = [*vrfCols_renamed,
                *vofCols_renamed,
                *renamedcols['comfHoursNoAppCols'],
                *renamedcols['comfHoursCols'],
                *renamedcols['disAppHotHourCols'],
                *renamedcols['disAppColdHourCols'],
                *renamedcols['disNonAppHotHourCols'],
                *renamedcols['disNonAppColdHourCols']]

    df.columns = colslist
    df['source'] = file
    df = df.groupby('source').agg('sum')
    df['source_temp'] = file
    summed_dataframes.append(df)
summed_tot_df = pd.concat(summed_dataframes)
print(summed_tot_df)
summed_tot_df[['model',
                    'standard',
                    'cat',
                    'comfMod',
                    'hvacMode',
                    'ventControl',
                    'ventOffset',
                    'minOutTemp',
                    'maxWindSpeed',
                    'astTol',
                    'city_year']] = summed_tot_df['source_temp'].astype(str).str.extract(
    '.+\\\\(.+_pymod)\[(AS_\w+)\[(CA_\w)\[(CM_\w)\[(HM_\w)\[(VC_\w)\[(VO_\w.\w)\[(MT_\w\w.\w)\[(MW_\w\w.\w)\[(AT_\w.\w)\[(.+).csv',
    expand=True)
del summed_tot_df['source_temp']
summed_tot_df['model'] = summed_tot_df['model'].str[:-6]
summed_tot_df['standard'] = summed_tot_df['standard'].str[3:]
summed_tot_df['cat'] = summed_tot_df['cat'].str[3:]
summed_tot_df['comfMod'] = summed_tot_df['comfMod'].str[3:]
summed_tot_df['hvacMode'] = summed_tot_df['hvacMode'].str[3:]
summed_tot_df['ventControl'] = summed_tot_df['ventControl'].str[3:]
summed_tot_df['ventOffset'] = summed_tot_df['ventOffset'].str[3:]
summed_tot_df['minOutTemp'] = summed_tot_df['minOutTemp'].str[3:]
summed_tot_df['maxWindSpeed'] = summed_tot_df['maxWindSpeed'].str[3:]
summed_tot_df['astTol'] = summed_tot_df['astTol'].str[3:]
for year in years:
    for city in cities:
        summed_tot_df['city_year'] = np.where(
            (summed_tot_df['city_year'].str.contains(city, case=False)) &
            (summed_tot_df['city_year'].str.contains(year, case=False)),
            city + '_' + year,
            summed_tot_df['city_year'])
summed_tot_df[['city', 'year']] = summed_tot_df['city_year'].str.extract(r'(.+)_(.+)', expand=True)
del summed_tot_df['city_year']
