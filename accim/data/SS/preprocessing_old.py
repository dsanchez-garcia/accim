# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Submodule to perform data processing before simulation run.
"""
class give_address_ssl:
    """
    Search address from coordinates using nominatim.openstreetmap.org.
    Version 1 to avoid ssl error.

    :param latitude: The latitude from the EPW file.
    :type latitude: float
    :param longitude: The longitude from the EPW file.
    :type longitude: float
    """
    def __init__(
            self,
            latitude: float,
            longitude: float,
    ):
        """
        Constructor method.
        """
        import requests
        import ssl
        import certifi

        # Set up SSL context with OpenStreetMap certificate added to trust store
        context = ssl.create_default_context()
        cafile = certifi.where()
        context.load_verify_locations(cafile)
        context.check_hostname = True

        # Make request to OpenStreetMap API with SSL verification enabled
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={latitude}&lon={longitude}"
        response = requests.get(url, verify=cafile, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).json()

        # Extract address information from response
        self.address = response['address']

        # Print the full address
        self.full_address = ", ".join([v for k,v in self.address.items() if v and k != 'country_code'])

class give_address_openssl:
    """
    Search address from coordinates using nominatim.openstreetmap.org.
    Version 2 to avoid ssl error.

    :param latitude: The latitude from the EPW file.
    :type latitude: float
    :param longitude: The longitude from the EPW file.
    :type longitude: float
    """
    def __init__(
            self,
            latitude: float,
            longitude: float,
    ):
        import requests
        import certifi
        import OpenSSL
        import ssl
        import socket

        # Obtain the certificate chain
        ctx = ssl.create_default_context()
        sock = ctx.wrap_socket(socket.socket(), server_hostname="nominatim.openstreetmap.org")
        sock.connect(("nominatim.openstreetmap.org", 443))
        cert = sock.getpeercert(True)
        cert_chain = [OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)]

        # Set up SSL context with certificate chain added to trust store
        cafile = certifi.where()
        context = ssl.create_default_context(cafile=cafile)
        for cert in cert_chain:
            context.load_verify_locations(cadata=cert.dump())

        # Make request to OpenStreetMap API with SSL verification enabled
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={latitude}&lon={longitude}"
        response = requests.get(url, verify=cafile, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).json()

        # Extract address information from response
        self.address = response['address']

        # Print the full address
        self.full_address = ", ".join([v for k,v in self.address.items() if v and k != 'country_code'])


class give_address:
    """
    Search address from coordinates using nominatim.openstreetmap.org.
    Version 3 to avoid ssl error.

    :param latitude: The latitude from the EPW file.
    :type latitude: float
    :param longitude: The longitude from the EPW file.
    :type longitude: float
    """
    def __init__(
            self,
            latitude: float,
            longitude: float,
    ):
        import requests

        # Make request to OpenStreetMap API
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={latitude}&lon={longitude}"
        response = requests.get(url).json()

        # Extract address information from response
        self.address = response['address']

        # Print the full address
        self.full_address = ", ".join([v for k,v in self.address.items() if v and k != 'country_code'])


class rename_epw_files:
    """
    Renames the EPW files following the name convention 'Country_City_RCPscenario-Year'.
    The Country and City fields are computed based on the coordinates of the EPW,
    and the RCPscenario and Year are taken from the original name.
    If no reference is found, the sample_EPWs are considered to be  for Present scenario.

    :param filelist: A list of the EPW files.
        If omitted, it will rename all sample_EPWs in that folder.
    :type filelist: list
    :param rename_dict: A dict to set the city field for each EPW file.
        It must follow the pattern
        {'city name to be search in epw file name': 'city name for the epw file if found`}
    :type rename_dict: dict
    :param confirm_renaming: True or False,
        to skip renaming confirmation on prompt command or console
    :type confirm_renaming: bool
    :param confirm_deletion: True or False,
        to skip deletion confirmation on prompt command or console
    :type confirm_deletion: bool
    """
    def __init__(
            self,
            filelist=None,
            rename_dict: dict = None,
            confirm_renaming=None,
            confirm_deletion=None,
    ):
        """
        Constructor method.
        """
        import glob
        import pandas as pd
        import datapackage
        import numpy as np
        import os
        # from geopy.exc import GeocoderUnavailable
        # from geopy.geocoders import Nominatim
        import pycountry
        import shutil
        from unidecode import unidecode
        from time import time
        import requests

        checkpoint = 0

        start = time()

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

        checkpoint = checkpoint + 1

        for i in range(len(epw_df)):
            epw_df.loc[i, 'EPW_abs_path'] = os.path.abspath(epw_df.loc[i, 'EPW_file_names'])

        epw_df['EPW_names'] = epw_df['EPW_file_names'].str.replace('.epw', '')

        epw_df['EPW_mod'] = epw_df['EPW_names'].str.replace('-', '_').str.replace('.', '_').str.split('_')

        epw_df['EPW_mod_filtered'] = epw_df['EPW_names'].str.replace('-', '_').str.replace('.', '_').str.split('_')

        future_scenario_dict = {
            'Present': ['Presente', 'Actual', 'Present', 'Current'],
            'RCP26': ['RCP2.6', 'RCP26', 'RCP2.5', 'RCP25'],
            'RCP45': ['RCP4.5', 'RCP45'],
            'RCP60': ['RCP6.0', 'RCP60'],
            'RCP85': ['RCP8.5', 'RCP85'],
            'SSP126': ['ssp126'],
            'SSP245': ['ssp245'],
            'SSP370': ['ssp370'],
            'SSP585': ['ssp585'],
        }

        for i in range(len(epw_df['EPW_names'])):
            for j in future_scenario_dict:
                for k in future_scenario_dict[j]:
                    if k.lower() in epw_df.loc[i, 'EPW_names'].lower():
                        epw_df.loc[i, 'EPW_scenario'] = j
                        try:
                            epw_df.loc[i, 'EPW_mod_filtered'].remove([x for x in epw_df.loc[i, 'EPW_mod_filtered'] if x.lower() in k.lower()][0])
                        except IndexError:
                            continue

        future_scenario_not_found_list = []

        for i in range(len(epw_df['EPW_names'])):
            try:
                if type(epw_df.loc[i, 'EPW_scenario']) is float:
                    epw_df.loc[i, 'EPW_scenario'] = 'Present'
                    future_scenario_not_found_list.append(epw_df.loc[i, 'EPW_file_names'])
            except KeyError:
                epw_df.loc[i, 'EPW_scenario'] = 'Present'
                future_scenario_not_found_list.append(epw_df.loc[i, 'EPW_file_names'])

        if len(future_scenario_not_found_list) > 0:
            print('Since no match has been found between RCP or SSP scenarios and EPW file name, '
                  'Present scenario has been assigned to the following EPW files:')
            print(*future_scenario_not_found_list, sep='\n')

        for i in range(len(epw_df['EPW_names'])):
            for j in range(2000, 2101, 10):
                if str(j) in epw_df.loc[i, 'EPW_names']:
                    try:
                        epw_df.loc[i, 'EPW_year'] = str(j)
                        epw_df.loc[i, 'EPW_mod_filtered'].remove(str(j))
                    except ValueError:
                        continue
                        # print('Year has not been identified.')

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
            print('Since no match has been found between RCP or SSP scenario Year and EPW file name, '
                  'Present year has been assigned to the following EPW files:')
            print(*year_not_found_list, sep='\n')

        checkpoint = checkpoint + 1

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

        checkpoint = checkpoint + 1

        epw_df['EPW_city_or_subcountry'] = 'UNKNOWN'


        # todo trying to make it work with own class
        for i in range(len(epw_df)):
            if rename_dict is not None:
                for k in rename_dict:
                    if k.lower() in epw_df.loc[i, 'EPW_names'].lower():
                        epw_df.loc[i, 'EPW_city_or_subcountry'] = rename_dict[k].replace(' ', '-').capitalize()
            try:
                osm_address = give_address(epw_df.loc[i, 'EPW_latitude'], epw_df.loc[i, 'EPW_longitude'])

                epw_df.loc[i, 'EPW_country_code'] = osm_address.address['country_code'].upper()
                epw_df.loc[i, 'EPW_country'] = pycountry.countries.get(alpha_2=epw_df.loc[i, 'EPW_country_code']).name.replace(' ', '-')
                epw_df.loc[i, 'location_address'] = unidecode(osm_address.full_address)

                for j in epw_df.loc[i, 'EPW_mod_filtered']:
                    if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                        try:
                            if j.lower() in str(unidecode(osm_address.address['city_district'])).lower():
                                epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
                        except KeyError:
                            pass
                    if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                        try:
                            if j.lower() in str(unidecode(osm_address.address['city'])).lower():
                                epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
                        except KeyError:
                            pass
                    if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                        try:
                            if j.lower() in str(unidecode(osm_address.address['municipality'])).lower():
                                epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
                        except KeyError:
                            pass
            except requests.exceptions.SSLError:
                try:
                    osm_address = give_address_ssl(epw_df.loc[i, 'EPW_latitude'], epw_df.loc[i, 'EPW_longitude'])

                    epw_df.loc[i, 'EPW_country_code'] = osm_address.address['country_code'].upper()
                    epw_df.loc[i, 'EPW_country'] = pycountry.countries.get(alpha_2=epw_df.loc[i, 'EPW_country_code']).name.replace(' ', '-')
                    epw_df.loc[i, 'location_address'] = unidecode(osm_address.full_address)

                    for j in epw_df.loc[i, 'EPW_mod_filtered']:
                        if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                            try:
                                if j.lower() in str(unidecode(osm_address.address['city_district'])).lower():
                                    epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
                            except KeyError:
                                pass
                        if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                            try:
                                if j.lower() in str(unidecode(osm_address.address['city'])).lower():
                                    epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
                            except KeyError:
                                pass
                        if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                            try:
                                if j.lower() in str(unidecode(osm_address.address['municipality'])).lower():
                                    epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
                            except KeyError:
                                pass
                except requests.exceptions.SSLError:
                    try:
                        osm_address = give_address_openssl(epw_df.loc[i, 'EPW_latitude'], epw_df.loc[i, 'EPW_longitude'])

                        epw_df.loc[i, 'EPW_country_code'] = osm_address.address['country_code'].upper()
                        epw_df.loc[i, 'EPW_country'] = pycountry.countries.get(alpha_2=epw_df.loc[i, 'EPW_country_code']).name.replace(' ', '-')
                        epw_df.loc[i, 'location_address'] = unidecode(osm_address.full_address)

                        for j in epw_df.loc[i, 'EPW_mod_filtered']:
                            if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                                try:
                                    if j.lower() in str(unidecode(osm_address.address['city_district'])).lower():
                                        epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
                                except KeyError:
                                    pass
                            if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                                try:
                                    if j.lower() in str(unidecode(osm_address.address['city'])).lower():
                                        epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
                                except KeyError:
                                    pass
                            if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                                try:
                                    if j.lower() in str(unidecode(osm_address.address['municipality'])).lower():
                                        epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
                                except KeyError:
                                    pass
                    except AttributeError:
                        epw_df.loc[i, 'EPW_country_code'] = 'UNKNOWN'
                        epw_df.loc[i, 'EPW_country'] = 'UNKNOWN'
                        epw_df.loc[i, 'location_address'] = 'UNKNOWN'
                        epw_df.loc[i, 'EPW_city_or_subcountry'] = 'UNKNOWN'
                        print(f"For some reason, accim cannot connect to OpenStreetMap to get the address of file {epw_df.loc[i, 'EPW_names']}. It gets an SSL error.")

        checkpoint +=1

        # todo consider except Using geolocator
        # geolocator = Nominatim(user_agent="geoapiExercises")
        # for i in range(len(epw_df)):
        #     try:
        #         location = geolocator.reverse(epw_df.loc[i, 'EPW_latitude'] + "," + epw_df.loc[i, 'EPW_longitude'])
        #         # print(location)
        #         epw_df.loc[i, 'EPW_country_code'] = location.raw['address'].get('country_code').upper()
        #         epw_df.loc[i, 'EPW_country'] = pycountry.countries.get(alpha_2=epw_df.loc[i, 'EPW_country_code']).name.replace(' ', '-')
        #         # epw_df.loc[i, 'EPW_country'] = location.raw['address'].get('country').replace(' ', '-')
        #         # epw_df.loc[i, 'EPW_city'] = location.raw['address'].get('city', '')
        #         # epw_df.loc[i, 'geolocator_address'] = location.raw['display_name']
        #         epw_df.loc[i, 'location_address'] = unidecode(location.address)
        #
        #
        #     # for i in range(len(epw_df['EPW_mod_filtered'])):
        #     #     location = geolocator.reverse(epw_df.loc[i, 'EPW_latitude'] + "," + epw_df.loc[i, 'EPW_longitude'])
        #         for j in epw_df.loc[i, 'EPW_mod_filtered']:
        #             if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
        #                 try:
        #                     if j.lower() in str(unidecode(location.raw['address']['city_district'])).lower():
        #                         epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
        #                 except KeyError:
        #                     pass
        #             if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
        #                 try:
        #                     if j.lower() in str(unidecode(location.raw['address']['city'])).lower():
        #                         epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
        #                 except KeyError:
        #                     pass
        #             if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
        #                 try:
        #                     if j.lower() in str(unidecode(location.raw['address']['municipality'])).lower():
        #                         epw_df.loc[i, 'EPW_city_or_subcountry'] = j.replace(' ', '-').capitalize()
        #                 except KeyError:
        #                     pass
        #     except GeocoderUnavailable:
        #         pass



            #todo for the unknowns, propose the city, city_district or municipality fields






        checkpoint = checkpoint + 1

        for i in range(len(epw_df['EPW_mod_filtered'])):
            try:
                if type(epw_df.loc[i, 'EPW_city_or_subcountry']) is float:
                    osm_address = give_address(epw_df.loc[i, 'EPW_latitude'], epw_df.loc[i, 'EPW_longitude'])
                    # location = geolocator.reverse(epw_df.loc[i, 'EPW_latitude'] + "," + epw_df.loc[i, 'EPW_longitude'])
                    try:
                        epw_df.loc[i, 'EPW_city_or_subcountry'] = str(osm_address.address['city'].replace(' ', '-')).capitalize()
                        # epw_df.loc[i, 'EPW_city_or_subcountry'] = str(location.raw['address'].get('city').replace(' ', '-')).capitalize()
                    except AttributeError:
                        epw_df.loc[i, 'EPW_city_or_subcountry'] = str(osm_address.address['city']).capitalize()
                        # epw_df.loc[i, 'EPW_city_or_subcountry'] = str(location.raw['address'].get('city')).capitalize()
                if type(epw_df.loc[i, 'EPW_country']) is float:
                    osm_address = give_address(epw_df.loc[i, 'EPW_latitude'], epw_df.loc[i, 'EPW_longitude'])
                    # location = geolocator.reverse(epw_df.loc[i, 'EPW_latitude'] + "," + epw_df.loc[i, 'EPW_longitude'])
                    try:
                        epw_df.loc[i, 'EPW_country'] = osm_address.address['country'].replace(' ', '-').capitalize()
                        # epw_df.loc[i, 'EPW_country'] = location.raw['address'].get('country').replace(' ', '-').capitalize()
                    except AttributeError:
                        epw_df.loc[i, 'EPW_country'] = osm_address.address['country'].capitalize()
                        # epw_df.loc[i, 'EPW_country'] = location.raw['address'].get('country').capitalize()
            except KeyError:
                continue

        for col in ['EPW_country', 'EPW_city_or_subcountry', 'EPW_scenario_year']:
            for row in range(len(epw_df)):
                try:
                    if epw_df.loc[row, col] is None:
                        epw_df.loc[row, col] = 'UNKNOWN'
                except KeyError:
                    continue
        # todo workflow here
        checkpoint = checkpoint + 1

        epw_df['EPW_new_names'] = epw_df[['EPW_country', 'EPW_city_or_subcountry', 'EPW_scenario_year']].agg('_'.join, axis=1)

        checkpoint = checkpoint + 1

        end = time()
        time_taken = round(end - start, 2)
        time_per_epw = round(time_taken / len(epw_df), 2)
        print(f'The geolocation process has taken: {time_taken} seconds ({time_per_epw} s/EPW)')

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
        unknown_id_list = []
        for i in range(len(epw_df)):
            if epw_df.loc[i, 'EPW_new_names'] not in unique_list:
                unique_list.append(epw_df.loc[i, 'EPW_new_names'])
            else:
                duplicated_list.append(epw_df.loc[i, 'EPW_new_names'])
                unique_list.remove(epw_df.loc[i, 'EPW_new_names'])
        for i in range(len(epw_df)):
            if epw_df.loc[i, 'EPW_new_names'] in duplicated_list:
                duplicated_id_list.append(i)
        if len(duplicated_list) > 0:
            duplicated_list = list(set(duplicated_list))
            duplicated_id_list = list(set(duplicated_id_list))
            print('\nDuplicates have been found in the renamed EPW files, '
                  'therefore these need to be amended in the next stage:')
            print(duplicated_list)
        for i in range(len(epw_df)):
            if 'UNKNOWN' in epw_df.loc[i, 'EPW_city_or_subcountry']:
                unknown_id_list.append(i)
        if len(unknown_id_list) > 0:
            print('\n"UNKNOWN" city or subcountry have been found in the renamed EPW files, '
                  'therefore these need to be amended in the next stage.')

        checkpoint = checkpoint + 1

        amendments_list = list(
            int(i)
            for i
            in input('\nIf any of the city or subcountry names needs some amendment '
                     '(if you are not happy with any of the available options, '
                     'you can exclude it from renaming at the next stage), '
                     'please enter the EPW IDs separated by space; otherwise, hit enter to omit:').split()
        )
        while len(list(set([i for i in amendments_list if amendments_list.count(i) > 1]))) > 0:
            amendments_list = list(
                int(i)
                for i
                in input('Some of the EPW IDs you just entered are duplicated. '
                         'Please enter again the epw IDs separated by space:').split()
            )

        for i in duplicated_id_list:
            if i not in amendments_list:
                amendments_list.append(i)
        for i in unknown_id_list:
            if i not in amendments_list:
                amendments_list.append(i)

        amendments_list = sorted(amendments_list)

        if len(amendments_list) > 0:
            epw_df['amended_city_or_subcountry'] = 'temp'
            for i in amendments_list:
                print(f'\nRegarding the file ID: {i} / old name: {epw_df.loc[i, "EPW_names"]} / new name: {epw_df.loc[i, "EPW_new_names"]}, the address obtained from coordinates is: ')
                print(epw_df.loc[i, "location_address"])
                epw_df.loc[i, 'amended_city_or_subcountry'] = input('Please enter the amended city or subcountry, which must be unique: ').replace(' ', '-').replace('_', '-')
                temp_name = f'{epw_df.loc[i, "EPW_country"]}_{epw_df.loc[i, "amended_city_or_subcountry"]}_{epw_df.loc[i, "EPW_scenario_year"]}'
                epw_df.loc[i, 'EPW_new_names'] = temp_name
                while list(epw_df['EPW_new_names']).count(temp_name) > 1:
                    print(f"{epw_df.loc[i, 'EPW_new_names']} already exists in the EPW file list, therefore you need to select a different city or subcountry name.")
                    epw_df.loc[i, 'amended_city_or_subcountry'] = input('Please enter again the amended city or subcountry, which must be unique: ').replace(' ', '-').replace('_', '-')
                    temp_name = f'{epw_df.loc[i, "EPW_country"]}_{epw_df.loc[i, "amended_city_or_subcountry"]}_{epw_df.loc[i, "EPW_scenario_year"]}'
                    epw_df.loc[i, 'EPW_new_names'] = temp_name

            print('\nThe previous and new names of the EPW files after city or subcountry name amendments and their unique IDs are:')
            for i in amendments_list:
                print(f'ID: {i} / {epw_df.loc[i, "EPW_names"]} / {epw_df.loc[i, "EPW_new_names"]}')

        print('\nThe final list of previous and new names of the EPW files and their unique IDs is:')
        for i in range(len(epw_df)):
            print(f'ID: {i} / {epw_df.loc[i, "EPW_names"]} / {epw_df.loc[i, "EPW_new_names"]}')
        exclusion_list = list(
            int(id)
            for id
            in input('\nIf you want to exclude some EPWs from renaming, '
                     'please enter the IDs separated by space, '
                     'otherwise, hit enter to continue:').split()
        )

        if confirm_renaming is None:
            proceed = input('\nDo you want to copy and rename the file or files? [y/n]:')
            if 'y' in proceed:
                confirm_renaming = True
            elif 'n' in proceed:
                confirm_renaming = False

        checkpoint = checkpoint + 1

        if confirm_renaming:
            for i in range(len(epw_df)):
                if i not in exclusion_list:
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

        # todo pop up when process ends; by default True
