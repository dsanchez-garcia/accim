frequency = 'hourly'
sum_or_mean = 'sum'
standard_outputs = True
level=['building']
level_sum_or_mean=['sum']
match_cities = False
manage_epw_names = False
normalised_energy_units = True
rename_cols = True
energy_units_in_kwh = True

if level_sum_or_mean is None:
    level_sum_or_mean = []
if level is None:
    level = []
# if custom_cols is None:
#     custom_cols = []

# import os
import pandas as pd
# from pathlib import Path
import datapackage
import glob
import numpy as np
import csv

frequency = frequency
normalised_energy_units = normalised_energy_units

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

    # with open(file) as csv_file:
    #     csv_reader = csv.reader(csv_file, delimiter=',')
    #     df = pd.DataFrame([csv_reader], index=True)

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

    # df['Date/Time_orig'] = df['Date/Time'].copy()

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

    # todo timestep frequency to be removed
    # if frequency == 'timestep':
    # pass
    # df = df.groupby(['Source', 'Month', 'Day', 'Hour', 'Minute'], as_index=False).agg(sum_or_mean)
    # if frequency == 'hourly':
    # pass
    # df = df.groupby(['Source', 'Month', 'Day', 'Hour'], as_index=False).agg(sum_or_mean)
    if frequency == 'daily':
        df = df.groupby(['Source', 'Month', 'Day'], as_index=False).agg(sum_or_mean)
    if frequency == 'monthly':
        df = df.groupby(['Source', 'Month'], as_index=False).agg(sum_or_mean)
    if frequency == 'runperiod':
        df = df.groupby(['Source'], as_index=False).agg(sum_or_mean)

    for i in constantcolsdict:
        df[i] = constantcolsdict[i]

    summed_dataframes.append(df)

df = pd.concat(summed_dataframes)

# todo not working
# df['Hour_mod'] = (pd.to_numeric(df['Hour']) - 1).astype(str).str.pad(width=2, side='left', fillchar='0')
# df['Hour_mod'] = df['Hour_mod'].str.replace('.0', '').str.pad(width=2, side='left', fillchar='0')
# df['Hour'] = df['Hour_mod']

OpTempColumn = [i for i in df.columns if 'Zone Thermostat Operative Temperature [C](Hourly)' in i]
occupied_zone_list = [i.split(' ')[0][:-5] for i in OpTempColumn]
occupied_zone_list = list(dict.fromkeys(occupied_zone_list))

occBZlist_underscore = [i.replace(':', '_') for i in occupied_zone_list]

hvac_zone_list = [i.split(' ')[0]
                       for i
                       in [i
                           for i
                           in df.columns
                           if 'Cooling Coil Total Cooling Rate' in i
                           ]
                       ]

hvac_zone_list = list(dict.fromkeys(hvac_zone_list))
# hvacBZlist_underscore = [i.replace(':', '_') for i in hvac_zone_list]

block_list = [i.split(':')[0] for i in occupied_zone_list]
block_list = list(dict.fromkeys(block_list))

renamezonesdict = {}
for i in range(len(occBZlist_underscore)):
    for j in df.columns:
        if occBZlist_underscore[i].lower() in j.lower():
            temp = {j: j.replace(occBZlist_underscore[i], occupied_zone_list[i])}
            renamezonesdict.update(temp)

df = df.rename(columns=renamezonesdict)

for i in df.columns:
    if 'VRF OUTDOOR UNIT' in i:
        df[i] = df[i] / 3600

renamedict = {}

for i in df.columns:
    if 'VRF OUTDOOR UNIT' in i:
        temp = {i: i.replace('[J]', '[W]')}
        renamedict.update(temp)

df = df.rename(columns=renamedict)

BZoutputDict = {
    'VRF INDOOR UNIT': 'Total Energy Demand (Wh)',
    'VRF OUTDOOR UNIT': 'Total Energy Consumption (Wh)'
}

for output in BZoutputDict:
    for block_zone in hvac_zone_list:
        df[f'{block_zone}' + '_' + BZoutputDict[output] + ' [summed]_pymod'] = df[
            [i for i in df.columns
             if block_zone.lower() in i.lower() and output in i and '_pymod' not in i]
        ].sum(axis=1)

outputdict = {
    'Zone Thermostat Operative Temperature [C](Hourly)': 'Zone Thermostat Operative Temperature (°C)',
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
        for block in block_list:
            if any('sum' in j for j in level_sum_or_mean):
                df[f'{block}' + '_Total_' + outputdict[output] + ' [summed]_pymod'] = df[
                    [i for i in df.columns
                     if block.lower() in i.lower() and output in i and '_pymod' not in i]
                ].sum(axis=1)
            if any('mean' in j for j in level_sum_or_mean):
                df[f'{block}' + '_Total_' + outputdict[output] + ' [mean]_pymod'] = df[
                    [i for i in df.columns
                     if block.lower() in i.lower() and output in i and '_pymod' not in i]
                ].mean(axis=1)
if any('building' in i for i in level):
    for output in outputdict:
        if any('sum' in j for j in level_sum_or_mean):
            df['Building_Total_' + outputdict[output] + ' [summed]_pymod'] = df[
                [i for i in df.columns
                 if output in i and '_pymod' not in i]
            ].sum(axis=1)
        if any('mean' in j for j in level_sum_or_mean):
            df['Building_Total_' + outputdict[output] + ' [mean]_pymod'] = df[
                [i for i in df.columns
                 if output in i and '_pymod' not in i]
            ].mean(axis=1)

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

print(*df.columns, sep='\n')

if normalised_energy_units:
    for i in df.columns:
        if '(Wh)' in i:
            for j in hvac_zone_list:
                if j in i:
                    df[i] = df[i] / df[
                        [i for i in df.columns
                         if 'Zone Floor Area' in i
                         and j.lower() in i.lower()][0]]
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

if energy_units_in_kwh:
    for col in df.columns:
        if '(Wh)' in col:
            df[col] = df[col] / 1000

energy_units_dict = {}
for i in df.columns:
    if '(Wh)' in i:
        temp = {i: i.replace('(Wh)', energy_units)}
        energy_units_dict.update(temp)
df = df.rename(columns=energy_units_dict)

df.set_axis(
    labels=[c[:-6] if c.endswith('_pymod') else c for c in df],
    axis=1,
    inplace=True
)

df[['Model',
         'Adaptive Standard',
         'Category',
         'Comfort mode',
         'HVAC mode',
         'Ventilation control',
         'VSToffset',
         'MinOToffset',
         'MaxWindSpeed',
         'ASTtol',
         'EPW']] = df['Source'].str.split('[', expand=True)



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

df = df.set_index([pd.RangeIndex(len(df))])

type(df.loc[9, 'Hour'])
df.loc[9, 'Hour']

##

missing = df.loc[47579]
missing2 = df.loc[47580]
missing3 = df.loc[47578]
#
# df.loc[47579, 'Month'] == ''
#
# int(df.loc[47578, 'Day'])
# int(df.loc[47580, 'Day'])
# for i in range(len(df)):
#     if df.loc[i, 'Month'] is None:
#         df.loc[i, 'Month'] = str(int((int(df.loc[i-1, 'Month']) + int(df.loc[i+1, 'Month']))/2))
#     if df.loc[i, 'Day'] is None:
#         df.loc[i, 'Day'] = str(int((int(df.loc[i-1, 'Day']) + int(df.loc[i+1, 'Day']))/2))
#     if df.loc[i, 'Hour'] is None:
#         df.loc[i, 'Hour'] = str(int((int(df.loc[i-1, 'Hour']) + int(df.loc[i+1, 'Hour']))/2))
#     if df.loc[i, 'Minute'] is None:
#         df.loc[i, 'Minute'] = str(int((int(df.loc[i-1, 'Minute']) + int(df.loc[i+1, 'Minute']))/2))
#     if df.loc[i, 'Second'] is None:
#         df.loc[i, 'Second'] = str(int((int(df.loc[i-1, 'Second']) + int(df.loc[i+1, 'Second']))/2))

for i in ['Month', 'Day', 'Hour', 'Minute', 'Second']:
    for j in range(len(df)):
        if df.loc[j, i] is None:
            df.loc[j, i] = str(int((int(df.loc[j-1, i]) + int(df.loc[j+1, i]))/2))
        if df.loc[j, i] == '':
            df.loc[j, i] = str(int((int(df.loc[j-1, i]) + int(df.loc[j+1, i]))/2))

    # todo changes 10 for 0
    # df[i] = df[i].str.replace('.0', '')
    df[i] = df[i].str.pad(width=2, side='left', fillchar='0')

df = df.set_index([pd.RangeIndex(len(df))])


##
df['Hour_mod'] = df['Hour'].copy()
df['Hour_mod_temp'] = df['Hour'].copy()
df['Hour_mod'] = (pd.to_numeric(df['Hour']) - 1).astype(str).str.pad(width=2, side='left', fillchar='0')
# df['Hour_mod'] = df['Hour_mod'].str.replace('.0', '').str.pad(width=2, side='left', fillchar='0')
df['Hour'] = df['Hour_mod']


# df[['Day', 'Month']] = df[['Day', 'Month']].astype(str)


# todo date/time column
if 'monthly' in frequency:

    df['Date/Time'] = df['Month']
if 'daily' in frequency:
    df['Date/Time'] = df[['Day', 'Month']].agg('/'.join, axis=1)


# type(df.loc[0, 'Day'])
# df['Day']
# df['Date/Time'] = 'temp'

if 'hourly' in frequency:
    df['Date/Time'] = df[['Day', 'Month']].agg('/'.join, axis=1) + ' ' + df['Hour'] + ':00'


if 'timestep' in frequency:
    df['Date/Time'] = (df[['Day', 'Month']].agg('/'.join, axis=1) +
                            ' ' +
                            df[['Hour', 'Minute']].agg(':'.join, axis=1))

df = df.set_index([pd.RangeIndex(len(df))])
##