class rename_epw_files:
    def __init__(
            self,
            filelist=None,
            confirm_renaming=None,
            confirm_deletion=None,
            match_cities: bool = None
    ):
        """
        Renames the EPW files following the name convention 'Country_City_RCPscenario-Year'.
        The Country and City fields are computed based on the coordinates of the EPW,
        and the RCPscenario and Year are taken from the original name.
        If no reference is found, the sample_EPWs are considered to be  for Present scenario.
        :param filelist: A list of the EPW files. If omitted, it will rename all sample_EPWs in that folder.
        :param confirm_renaming: True or False, #to skip renaming confirmation on prompt command or console
        :param confirm_deletion: True or False #to skip deletion confirmation on prompt command or console
        :param match_cities: True or False. Default is False. It takes the possible city names and checks it is in an extensive list of cities. It's computationally very expensive.
        """
        import glob
        import pandas as pd
        import datapackage
        import numpy as np
        import os
        from geopy.geocoders import Nominatim
        import pycountry
        import shutil
        from unidecode import unidecode

        if filelist is None:
            filelist = []

        if len(filelist) > 0:
            epw_files_to_rename = filelist
        else:
            # todo same as Table
            epw_files_to_rename = glob.glob('*.epw', recursive=True)

        epw_df = pd.DataFrame(data=epw_files_to_rename,
                              index=list(range(len(epw_files_to_rename))),
                              columns=['EPW_file_names'])

        for i in range(len(epw_df)):
            epw_df.loc[i, 'EPW_abs_path'] = os.path.abspath(epw_df.loc[i, 'EPW_file_names'])

        epw_df['EPW_names'] = epw_df['EPW_file_names'].str.replace('.epw', '')

        epw_df['EPW_mod'] = epw_df['EPW_names'].str.replace('-', '_').str.replace('.', '_').str.split('_')

        epw_df['EPW_mod_filtered'] = epw_df['EPW_names'].str.replace('-', '_').str.replace('.', '_').str.split('_')

        rcpdict = {
            'Present': ['Presente', 'Actual', 'Present', 'Current'],
            'RCP26': ['RCP2.6', 'RCP26', 'RCP2.5', 'RCP25'],
            'RCP45': ['RCP4.5', 'RCP45'],
            'RCP60': ['RCP6.0', 'RCP60'],
            'RCP85': ['RCP8.5', 'RCP85']
        }

        for i in range(len(epw_df['EPW_names'])):
            for j in rcpdict:
                for k in rcpdict[j]:
                    if k.lower() in epw_df.loc[i, 'EPW_names'].lower():
                        epw_df.loc[i, 'EPW_scenario'] = j
                        try:
                            epw_df.loc[i, 'EPW_mod_filtered'].remove([x for x in epw_df.loc[i, 'EPW_mod_filtered'] if x.lower() in k.lower()][0])
                        except IndexError:
                            continue

        rcp_not_found_list = []

        for i in range(len(epw_df['EPW_names'])):
            try:
                if type(epw_df.loc[i, 'EPW_scenario']) is float:
                    epw_df.loc[i, 'EPW_scenario'] = 'Present'
                    rcp_not_found_list.append(epw_df.loc[i, 'EPW_file_names'])
            except KeyError:
                epw_df.loc[i, 'EPW_scenario'] = 'Present'
                rcp_not_found_list.append(epw_df.loc[i, 'EPW_file_names'])

        if len(rcp_not_found_list) > 0:
            print('Since no match has been found between scenarios and EPW file name, '
                  'Present scenario has been assigned to the following EPW files:')
            print(*rcp_not_found_list, sep='\n')

        for i in range(len(epw_df['EPW_names'])):
            for j in range(2000, 2101, 10):
                if str(j) in epw_df.loc[i, 'EPW_names']:
                    try:
                        epw_df.loc[i, 'EPW_year'] = str(j)
                        epw_df.loc[i, 'EPW_mod_filtered'].remove(str(j))
                    except ValueError:
                        continue
                        # print('Year has nt ben identified.')

        for i in range(len(epw_df['EPW_names'])):
            if epw_df.loc[i, 'EPW_scenario'] == 'Present':
                epw_df.loc[i, 'EPW_scenario_year'] = 'Present'
            else:
                epw_df.loc[i, 'EPW_scenario_year'] = epw_df.loc[i, 'EPW_scenario'] + '-' + epw_df.loc[i, 'EPW_year']

        year_not_found_list = []
        for i in range(len(epw_df['EPW_names'])):
            try:
                if type(epw_df.loc[i, 'EPW_year']) is float:
                    epw_df.loc[i, 'EPW_year'] = 'Present'
                    year_not_found_list.append(epw_df.loc[i, 'EPW_file_names'])
            except KeyError:
                epw_df.loc[i, 'EPW_year'] = 'Present'
                year_not_found_list.append(epw_df.loc[i, 'EPW_file_names'])
        if len(year_not_found_list) > 0:
            print('Since no match has been found between scenarios and EPW file name, '
                  'Present year has been assigned to the following EPW files:')
            print(*year_not_found_list, sep='\n')

        # path = r'C:\Users\user\PycharmProjects\accim'
        path = os.getcwd()
        new_list = []
        for file in epw_files_to_rename:
            # open the file and then call .read() to get the text
            with open(
                    os.path.join(path, file),
                    "rb") as f:
                text = f.readline()
                new_list.append([str(text).split(',')])
            # f.close()

        for i in range(len(new_list)):
            epw_df.loc[i, 'EPW_latitude'] = new_list[i][0][6]
            epw_df.loc[i, 'EPW_longitude'] = new_list[i][0][7]

        geolocator = Nominatim(user_agent="geoapiExercises")
        for i in range(len(epw_df)):
            location = geolocator.reverse(epw_df.loc[i, 'EPW_latitude'] + "," + epw_df.loc[i, 'EPW_longitude'])
            # print(location)
            epw_df.loc[i, 'EPW_country_code'] = location.raw['address'].get('country_code').upper()
            # epw_df.loc[i, 'EPW_city'] = location.raw['address'].get('city', '')

        # Method: match cities
        isEPWformatValid = False
        if match_cities:
            package_cities = datapackage.Package('https://datahub.io/core/world-cities/datapackage.json')

            # to load only tabular data_cities
            resources_cities = package_cities.resources
            for resource in resources_cities:
                if resource.tabular:
                    data_cities = pd.read_csv(resource.descriptor['path'])

            epw_df = epw_df.set_index([pd.RangeIndex(len(epw_df))])

            #  if len <1
            data_cities['subcountry'] = data_cities['subcountry'].astype(str)

            rcp = []
            for i in rcpdict:
                for j in range(len(rcpdict[i])):
                    rcp.append(rcpdict[i][j])

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
                location_matches_df = pd.concat(cities_df_list)
                location_matches_df = location_matches_df.set_index([pd.RangeIndex(len(location_matches_df))])
                location_matches_df['country'] = location_matches_df['country'].astype(str)
                isEPWformatValid = True
            except ValueError:
                isEPWformatValid = False
                print('EPW files are not correctly named')

            for i in range(len(epw_df['EPW_mod'])):
                for j in epw_df.loc[i, 'EPW_mod']:
                    if j.lower() in [k.lower() for k in location_matches_df['name']]:
                        epw_df.loc[i, 'EPW_City_or_subcountry'] = j.replace(' ', '-').capitalize()
                epw_df.loc[i, 'EPW_country'] = pycountry.countries.get(
                    alpha_2=epw_df.loc[i, 'EPW_country_code']).name.replace(' ', '-')

            # epw_df['EPW_CountryCode'] = epw_df['EPW_CountryCode'].astype(str)
        else:
            # Method: geolocation
            epw_df['EPW_City_or_subcountry'] = 'UNKNOWN'
            for i in range(len(epw_df['EPW_mod_filtered'])):
                location = geolocator.reverse(epw_df.loc[i, 'EPW_latitude'] + "," + epw_df.loc[i, 'EPW_longitude'])
                for j in epw_df.loc[i, 'EPW_mod_filtered']:
                    try:
                        if j.lower() in str(unidecode(location.raw['address']['city_district'])).lower():
                            epw_df.loc[i, 'EPW_City_or_subcountry'] = j.replace(' ', '-').capitalize()
                    except KeyError:
                        try:
                            if j.lower() in str(unidecode(location.raw['address']['city'])).lower():
                                epw_df.loc[i, 'EPW_City_or_subcountry'] = j.replace(' ', '-').capitalize()
                        except KeyError:
                            try:
                                if j.lower() in str(unidecode(location.raw['address']['municipality'])).lower():
                                    epw_df.loc[i, 'EPW_City_or_subcountry'] = j.replace(' ', '-').capitalize()
                            except KeyError:
                                try:
                                    if j.lower() in str(unidecode(location.address)).lower():
                                        epw_df.loc[i, 'EPW_City_or_subcountry'] = j.replace(' ', '-').capitalize()
                                except KeyError:
                                    print(f'No city or subcountry has been found in file {epw_df.loc[i, "EPW_names"]}')
                                    epw_df.loc[i, 'EPW_City_or_subcountry'] = 'UNKNOWN'
                epw_df.loc[i, 'EPW_country'] = pycountry.countries.get(alpha_2=epw_df.loc[i, 'EPW_country_code']).name.replace(' ', '-')

            for i in range(len(epw_df['EPW_mod_filtered'])):
                try:
                    if type(epw_df.loc[i, 'EPW_City_or_subcountry']) is float:
                        location = geolocator.reverse(epw_df.loc[i, 'EPW_latitude'] + "," + epw_df.loc[i, 'EPW_longitude'])
                        try:
                            epw_df.loc[i, 'EPW_City_or_subcountry'] = str(location.raw['address'].get('city').replace(' ', '-')).capitalize()
                        except AttributeError:
                            epw_df.loc[i, 'EPW_City_or_subcountry'] = str(location.raw['address'].get('city')).capitalize()
                    if type(epw_df.loc[i, 'EPW_country']) is float:
                        location = geolocator.reverse(epw_df.loc[i, 'EPW_latitude'] + "," + epw_df.loc[i, 'EPW_longitude'])
                        try:
                            epw_df.loc[i, 'EPW_country'] = location.raw['address'].get('country').replace(' ', '-').capitalize()
                        except AttributeError:
                            epw_df.loc[i, 'EPW_country'] = location.raw['address'].get('country').capitalize()
                except KeyError:
                    continue

        for col in ['EPW_country', 'EPW_City_or_subcountry', 'EPW_scenario_year']:
            for row in range(len(epw_df)):
                try:
                    if epw_df.loc[row, col] is None:
                        epw_df.loc[row, col] = 'UNKNOWN'
                except KeyError:
                    continue

        epw_df['EPW_new_names'] = epw_df[['EPW_country', 'EPW_City_or_subcountry', 'EPW_scenario_year']].agg('_'.join, axis=1)

        print('\nThe previous and new names of the EPW files and their unique IDs are:')
        for i in range(len(epw_df)):
            print(f'ID: {i} / {epw_df.loc[i, "EPW_names"]} / {epw_df.loc[i, "EPW_new_names"]}')
        # print(*list(epw_df['EPW_names']), sep='\n')
        # print('And the new names of the EPW files are going to be:')
        # print(*list(epw_df['EPW_new_names']), sep='\n')

        # Checking there are no duplicates
        unique_list = []
        duplicated_list = []
        duplicated_id_list = []
        for i in range(len(epw_df)):
            if epw_df.loc[i, 'EPW_new_names'] not in unique_list:
                unique_list.append(epw_df.loc[i, 'EPW_new_names'])
            else:
                duplicated_list.append(epw_df.loc[i, 'EPW_new_names'])
                duplicated_id_list.append(i)
        if len(duplicated_list) > 0:
            duplicated_list = list(set(duplicated_list))
            duplicated_id_list = list(set(duplicated_id_list))
            print('\nDuplicates have been found in the renamed EPW files, '
                  'therefore these need to be amended in the next stage:')
            print(duplicated_list)

        amendments_list = list(
            int(i)
            for i
            in input('\nIf any of the city or subcountry names needs some amendment '
                     '(if you are not happy with any of the available options, '
                     'you can exclude it from renaming at the next stage), '
                     'please enter the EPW IDs separated by space:').split()
        )
        while len(list(set([i for i in amendments_list if amendments_list.count(i) > 1]))) > 0:
            amendments_list = list(
                int(i)
                for i
                in input('Some of the EPW IDs you just entered are duplicated. '
                         'Please enter again the epw IDs separated by space:').split()
            )

        epw_df['location_address'] = 'temp'

        for i in duplicated_id_list:
            if i not in amendments_list:
                amendments_list.append(i)
        amendments_list = sorted(amendments_list)

        if len(amendments_list) > 0:
            manually_rename = input('If you rename them manually, the process will be faster than searching the geolocation. '
                                    'Please enter "y" to rename them manually, or "n" to proceed with the geolocation: ')
            if manually_rename == 'n':
                for i in amendments_list:
                    location = geolocator.reverse(epw_df.loc[i, 'EPW_latitude'] + "," + epw_df.loc[i, 'EPW_longitude'])
                    try:
                        epw_df.loc[i, 'EPW_mod_filtered'].append(str(unidecode(location.raw['address']['city_district'])))
                    except KeyError:
                        # print(f'The city district field is not available for file {epw_df.loc[i, "EPW_names"]}')
                        pass
                    try:
                        epw_df.loc[i, 'EPW_mod_filtered'].append(str(unidecode(location.raw['address']['city'])))
                    except KeyError:
                        # print(f'The city field is not available for file {epw_df.loc[i, "EPW_names"]}')
                        pass

                    try:
                        epw_df.loc[i, 'EPW_mod_filtered'].append(str(unidecode(location.raw['address']['municipality'])))
                    except KeyError:
                        # print(f'The municipality is not available for file {epw_df.loc[i, "EPW_names"]}')
                        pass

                    epw_df.loc[i, 'location_address'] = str(location.address)

        if len(amendments_list) > 0:
            epw_df['amended_city_or_subcountry'] = 'temp'
            if manually_rename == 'n':
                for i in amendments_list:
                    print(f'\nRegarding the file ID: {i} / old name: {epw_df.loc[i, "EPW_names"]} / new name: {epw_df.loc[i, "EPW_new_names"]}, the available options for city or subcountry are:')
                    print(epw_df.loc[i, "EPW_mod_filtered"])
                    print("If you haven't found yet the correct city or subcountry, it may be in the following address:")
                    print(epw_df.loc[i, "location_address"])
                    epw_df.loc[i, 'amended_city_or_subcountry'] = input('Please enter the amended city or subcountry, which must be unique: ').replace(' ', '-')
                    temp_name = f'{epw_df.loc[i, "EPW_country"]}_{epw_df.loc[i, "amended_city_or_subcountry"]}_{epw_df.loc[i, "EPW_scenario_year"]}'
                    epw_df.loc[i, 'EPW_new_names'] = temp_name
                    while list(epw_df['EPW_new_names']).count(temp_name) > 1:
                        print(f"{epw_df.loc[i, 'EPW_new_names']} already exists in the EPW file list, therefore you need to select a different city or subcountry name.")
                        epw_df.loc[i, 'amended_city_or_subcountry'] = input('Please enter again the amended city or subcountry, which must be unique: ').replace(' ', '-')
                        temp_name = f'{epw_df.loc[i, "EPW_country"]}_{epw_df.loc[i, "amended_city_or_subcountry"]}_{epw_df.loc[i, "EPW_scenario_year"]}'
                        epw_df.loc[i, 'EPW_new_names'] = temp_name

            elif manually_rename == 'y':
                for i in amendments_list:
                    print(f'\nRegarding the file ID: {i} / old name: {epw_df.loc[i, "EPW_names"]} / new name: {epw_df.loc[i, "EPW_new_names"]}')
                    epw_df.loc[i, 'amended_city_or_subcountry'] = input('Please enter the amended city or subcountry, which must be unique: ').replace(' ', '-')
                    temp_name = f'{epw_df.loc[i, "EPW_country"]}_{epw_df.loc[i, "amended_city_or_subcountry"]}_{epw_df.loc[i, "EPW_scenario_year"]}'
                    epw_df.loc[i, 'EPW_new_names'] = temp_name
                    while list(epw_df['EPW_new_names']).count(temp_name) > 1:
                        print(f"{epw_df.loc[i, 'EPW_new_names']} already exists in the EPW file list, therefore you need to select a different city or subcountry name.")
                        epw_df.loc[i, 'amended_city_or_subcountry'] = input('Please enter again the amended city or subcountry, which must be unique: ').replace(' ', '-')
                        temp_name = f'{epw_df.loc[i, "EPW_country"]}_{epw_df.loc[i, "amended_city_or_subcountry"]}_{epw_df.loc[i, "EPW_scenario_year"]}'
                        epw_df.loc[i, 'EPW_new_names'] = temp_name

            print('\nThe previous and new names of the EPW files after city or subcountry name amendments and their unique IDs are:')
            for i in amendments_list:
                print(f'ID: {i} / {epw_df.loc[i, "EPW_names"]} / {epw_df.loc[i, "EPW_new_names"]}')

        exclusion_list = list(
            name
            for name
            in input('\nIf you want to exclude some EPWs from renaming, '
                     'please enter the new names separated by space, '
                     'otherwise, hit enter to continue:').split()
        )

        if confirm_renaming is None:
            proceed = input('\nDo you want to rename the file or files? [y/n]:')
            if 'y' in proceed:
                confirm_renaming = True
            elif 'n' in proceed:
                confirm_renaming = False

        if confirm_renaming:
            for i in range(len(epw_df)):
                if epw_df.loc[i, 'EPW_new_names'] not in exclusion_list:
                    try:
                        shutil.copy(epw_df.loc[i, 'EPW_abs_path'], path + '/' + epw_df.loc[i, 'EPW_new_names'] + '.epw')
                        print(f'The file {epw_df.loc[i, "EPW_names"]} has been renamed to {epw_df.loc[i, "EPW_new_names"]}')
                    except shutil.SameFileError:
                        print(f'The old and new names of file {epw_df.loc[i, "EPW_names"]} are the same.')
                        epw_files_to_rename.remove(epw_df.loc[i, "EPW_names"] + '.epw')

        if confirm_deletion is None:
            proceed = input('\nDo you want to delete the original EPW file or files? [y/n]:')
            if 'y' in proceed:
                confirm_deletion = True
            elif 'n' in proceed:
                confirm_deletion = False

        if confirm_deletion:
            for i in epw_files_to_rename:
                os.remove(i)
                print(f'The file {i} has been deleted.')

        # todo pop up when process ends; by defalt True
