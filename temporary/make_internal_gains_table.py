import pandas as pd
file = 'The Palm_v08_2_RadiantFloor_RITE_temp_PV (grid)'

df = pd.read_csv(f'{file}.csv')
df = df[3:]
# df.to_csv(f'{file}_cleaned.xlsx')

# Df to Series
df = df.squeeze()
# Series to df
df = df.str.split(';', expand=True)

# Columns as headers
df.columns = df.iloc[0]
cols = [i.replace('"','') for i in df.columns]
df.columns = cols
df = df[1:]

# Replace " with nothing
for i in df.columns:
    df[i] = [j.replace('"', '') for j in df[i]]

[i for i in df.columns]

floor_area = 'Activity - Floor Areas and Volumes - Floor area (m2)'
occupancy_density = 'Activity - Occupancy - Occupancy density (people/m2)'
occupied = 'Activity - Occupancy - Occupied?'
computers_density = 'Activity - Computers - Power density (W/m2)'
equipment_density = 'Activity - Office Equipment - Power density (W/m2)'
miscellaneous_density = 'Activity - Miscellaneous - Power density (W/m2)'
catering_density = 'Activity - Catering - Power density (W/m2)'
process_density = 'Activity - Process - Power density (W/m2)'
lighting_density = 'Lighting - General Lighting - Power density (W/m2)'

df = df.replace({
    'True': 1,
    'False': 0,
})

num_cols = [
    floor_area,
    occupancy_density,
    computers_density,
    equipment_density,
    miscellaneous_density,
    catering_density,
    process_density,
    lighting_density

]
for col in num_cols:
    df[col] = [float(i) for i in df[col]]

df = df.reset_index().drop(['index'], axis=1)



# columns_to_keep = [
#     'Zone',
#     'Block',
#     'Activity - Floor Areas and Volumes - Floor area (m2)',
#     # Occupancy
#     # 'Activity - Occupancy - Occupancy method',
#     occupied,
#     occupancy_density,
#     'Activity - Metabolic - Activity',
#     # Computers
#     computers_density,
#     # Office equipment
#     equipment_density,
#     # Miscellaneous
#     miscellaneous_density,
#     #Catering
#     catering_density,
#     # Process
#     process_density,
#     #Lighting
#     lighting_density
# ]

# cols_to_drop = [i for i in df.columns if i not in columns_to_keep]

# df = df.drop(cols_to_drop, axis=1)


# Occupancy

df['heat load per person (W/person)'] = 0
for i in range(len(df)):
    if df.loc[i, occupied] == 1:
        df.loc[i, 'heat load per person (W/person)'] = 117.2

df['Occupancy load (W)'] = df[floor_area] * df[occupancy_density] * df[occupied] * df['heat load per person (W/person)']
df['Occupancy load (W)'] = [round(i, 2) for i in df['Occupancy load (W)']]

##

# Computers
[type(i) for i in df['Activity - Computers - On']]
df[computers_density] = df[computers_density] * df['Activity - Computers - On']

# Miscellaneous
df[miscellaneous_density] = df[miscellaneous_density] * df['Activity - Miscellaneous - On']

# Office equipment
df[equipment_density] = df[equipment_density] * df['Activity - Office Equipment - On']

# catering
df[catering_density] = df[catering_density] * df['Activity - Catering - On']

# process
df[process_density] = df[process_density] * df['Activity - Process - On']

# lighting
df[lighting_density] = df[lighting_density] * df['Lighting - General Lighting - On']

# Removing columns

columns_to_keep = [
    'Zone',
    'Block',
    'Occupancy load (W)',
    computers_density,
    equipment_density,
    miscellaneous_density,
    catering_density,
    process_density,
    lighting_density
]

cols_to_drop = [i for i in df.columns if i not in columns_to_keep]

df = df.drop(cols_to_drop, axis=1)

df.to_excel('internal_loads_table.xlsx')