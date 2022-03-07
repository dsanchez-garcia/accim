import glob
import pandas as pd
import datapackage
import numpy as np

match_cities = True

allfiles = glob.glob('*.epw', recursive=True)
epw_df = pd.DataFrame(data=allfiles,
                      index=list(range(len(allfiles))),
                      columns=['EPW_file_names'])

epw_df['EPW_names'] = epw_df['EPW_file_names'].str.replace('.epw','')

rcpdict = {
    'Present': ['Presente', 'Actual', 'Present', 'Current'],
    'RCP2.6': ['RCP2.6', 'RCP26'],
    'RCP4.5': ['RCP4.5', 'RCP45'],
    'RCP6.0': ['RCP6.0', 'RCP60'],
    'RCP8.5': ['RCP8.5', 'RCP85']
}

for i in range(len(epw_df['EPW_names'])):
    for j in rcpdict:
        for k in rcpdict[j]:
            if k.lower() in epw_df.loc[i, 'EPW_names'].lower():
                epw_df.loc[i, 'EPW_scenario'] = j

rcp_not_found_list = []

for i in range(len(epw_df['EPW_names'])):
    if type(epw_df.loc[i, 'EPW_scenario']) is float:
        epw_df.loc[i, 'EPW_scenario'] = 'Present'
        rcp_not_found_list.append(epw_df.loc[i, 'EPW_file_names'])

if len(rcp_not_found_list) > 0:
    print('Since no match has been found between scenarios and EPW file name, '
          'Present scenario has been assigned to the following EPW files:')
    print(*rcp_not_found_list, sep='\n')

for i in range(len(epw_df['EPW_names'])):
    for j in range(2000, 2101, 1):
        if str(j) in epw_df.loc[i, 'EPW_names']:
            epw_df.loc[i, 'EPW_year'] = str(j)

for i in range(len(epw_df['EPW_names'])):
    if epw_df.loc[i, 'EPW_scenario'] == 'Present':
        epw_df.loc[i, 'EPW_scenario_year'] = 'Present'
    else:
        epw_df.loc[i, 'EPW_scenario_year'] = epw_df.loc[i, 'EPW_scenario'] + '[' + epw_df.loc[i, 'EPW_year']

year_not_found_list = []
for i in range(len(epw_df['EPW_names'])):
    if type(epw_df.loc[i, 'EPW_year']) is float:
        epw_df.loc[i, 'EPW_year'] = 'Present'
        year_not_found_list.append(epw_df.loc[i, 'EPW_file_names'])
if len(year_not_found_list) > 0:
    print('Since no match has been found between scenarios and EPW file name, '
          'Present year has been assigned to the following EPW files:')
    print(*year_not_found_list, sep='\n')


##

rcp = []
for i in rcpdict:
    for j in range(len(rcpdict[i])):
        rcp.append(rcpdict[i][j])

# rcp_present = []
# for i in rcpdict['Present']:
#     rcp_present.append(i)
#
epw_df['EPW_mod'] = epw_df['EPW_names'].str.replace('-', '_').str.replace('.', '_').str.split('_')
#
# for i in range(len(epw_df['EPW_mod'])):
#     for j in epw_df.loc[i, 'EPW_mod']:
#         if len(j) == 2:
#             epw_df.loc[i, 'EPW_CountryCode'] = j
#         else:
#             epw_df.loc[i, 'EPW_CountryCode'] = np.nan
#
#         for k in rcpdict:
#             for m in range(len(rcpdict[k])):
#                 if j in rcpdict[k][m]:
#                     epw_df.loc[i, 'EPW_Scenario'] = k
#                 else:
#                     epw_df.loc[i, 'EPW_Scenario'] = np.nan
#
#     epw_df.loc[i, 'EPW_Year'] = np.nan

##

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

    epw_df = epw_df.set_index([pd.RangeIndex(len(epw_df))])

    #  if len <1
    data_cities['subcountry'] = data_cities['subcountry'].astype(str)
    data_countries['Name'] = data_countries['Name'].astype(str)
    data_countries['Code'] = data_countries['Code'].astype(str)

    locations = []
    for i in list(epw_df['EPW_mod']):
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
##

    epw_df['EPW_CountryCode'] = epw_df['EPW_CountryCode'].astype(str)

##
for i in range(len(epw_df['EPW_mod'])):
    for j in epw_df.loc[i, 'EPW_mod']:
        if j.lower() in [k.lower() for k in cities_df['name']]:
            epw_df.loc[i, 'EPW_City_or_subcountry'] = j

##

for i in range(len(epw_df['EPW_mod'])):
    for j in epw_df.loc[i, 'EPW_mod']:
        if j in rcp_present:
            epw_df.loc[i, 'EPW_Year'] = 'Present'
        elif j in rcp:
            continue
        elif j.isnumeric():
            epw_df.loc[i, 'EPW_Year'] = int(j)
        elif len(j) == 2:
            continue
        else:
            if match_cities:
                if isEPWformatValid:
                    for k in range(len(cities_df)):
                        if epw_df.loc[i, 'EPW_CountryCode'].lower() in cities_df.loc[k, 'country'].lower():
                            epw_df.loc[i, 'EPW_Country'] = cities_df.loc[k, 'country']
                        if str(j).lower() in cities_df.loc[k, 'name'].lower():
                            epw_df.loc[i, 'EPW_City_or_subcountry'] = cities_df.loc[k, 'name']
                        elif str(j).lower() in cities_df.loc[k, 'subcountry'].lower():
                            epw_df.loc[i, 'EPW_City_or_subcountry'] = cities_df.loc[k, 'name']
                        elif str(j).isalnum():
                            epw_df.loc[i, 'EPW_City_or_subcountry'] = j.upper()
                        else:
                            epw_df.loc[i, 'EPW_City_or_subcountry'] = j.capitalize()
            else:
                epw_df.loc[i, 'EPW_City_or_subcountry'] = j.capitalize()
