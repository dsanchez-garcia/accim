from accim.data.data_postprocessing import Table

block_zone = {
    'BLOQUE1':[
        'LIVINGXROOM',
        'BEDROOM1',
        'BEDROOM2',
        'MASTERBEDROOM',
        'BATHROOM1',
        'BATHROOM2',
        'KITCHEN',
    ]
}

data_analysis = Table(
    # source_concatenated_csv_filepath='WIP_data_postprocessing/ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    source_frequency='hourly',
    frequency='monthly',
    frequency_agg_func='sum',
    standard_outputs=True,
    level=['block','building'],
    level_agg_func=['sum'],
    split_epw_names=True,
    # block_zone_hierarchy=block_zone
)

##

import pandas as pd

df = pd.read_csv(
    '../WIP_data_postprocessing/ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv')
df.columns

hierarchy_dict = {
    'BLOQUE1':[
        'LIVINGXROOM',
        'BEDROOM1',
        'BEDROOM2',
        'MASTERBEDROOM',
        'BATHROOM1',
        'BATHROOM2',
        'KITCHEN',
    ]
}

rename_dict = {}

for i in hierarchy_dict:
    for j in hierarchy_dict[i]:
        # df.columns = [k.replace(j, i + '_' + j) for k in df.columns]
        for c in df.columns:
            if i + '_' + j in c or i + ':' + j in c:
                continue
            else:
                rename_dict.update({c: c.replace(j, i + '_' + j)})

df = df.rename(columns=rename_dict)


##

import re

def extract_alphanumeric_joined_by_colon(string):
    # Define the pattern to match alphanumeric words joined by colon
    pattern = r'\b([a-zA-Z0-9_]+:[a-zA-Z0-9_]+)\b'

    # Use regular expression to find matches
    matches = re.findall(pattern, string)

    for i, j in enumerate(matches):
        if "_" in j:
            matches[i] = j.split('_')[1]


    return matches


def extract_alphanumeric_joined_by_underscore(string):
    # Define the pattern to match alphanumeric words joined by colon
    pattern = r'\b([a-zA-Z0-9_]+_[a-zA-Z0-9_]+)\b'

    # Use regular expression to find matches
    matches = re.findall(pattern, string)

    for i, j in enumerate(matches):
        if "_" in j:
            matches[i] = j.split('_')[1]


    return matches


# Example usage:
input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
result = extract_alphanumeric_joined_by_colon(input_string)
print("Alphanumeric words joined by colon:", result)


block_zones = []
for col in df.columns:
    matches = extract_alphanumeric_joined_by_colon(col)
    for i, match in enumerate(matches):
        if 'EMS' in match or 'VRF' in match:
            matches.pop(i)
    block_zones.extend(matches)
    matches = extract_alphanumeric_joined_by_underscore(col)
    for i, match in enumerate(matches):
        if 'EMS' in match or 'VRF' in match:
            matches.pop(i)
    block_zones.extend(matches)


##

import pandas as pd
from besos.eppy_funcs import get_building

df = pd.read_csv(
    '../WIP_data_postprocessing/ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv')
df.columns

building = get_building('ChileanModel.idf')
# building = get_building('OSM_SmallOffice_exHVAC.idf')


allzones = [i.Name for i in building.idfobjects['zone']]

occupied_zone_list = []
for zone in allzones:
    for col in df.columns:
        if zone.lower() in col.lower():
            occupied_zone_list.append(zone)
occupied_zone_list = list(set(occupied_zone_list))

if not(all(len(i.split(':')) == 2 for i in occupied_zone_list)):
    if block_zone_hierarchy is None:
        print(
            'Regarding occupied zones, we have not found a clear hierarchical pattern of blocks and zones. '
            'The zones we have found are:'
        )
        print(occupied_zone_list)
        block_list = list(i.upper() for i in input('Please enter all Blocks separated by semicolon (;): ').split(';'))
        hierarchy_dict = {}
        for i in block_list:
            temp_zones = list(i.upper() for i in input(f'Please enter the zones for {i}, considering these cannot be at the same time in more than one block, separated by semicolon (;): ').split(';'))
            temp_dict = {i: temp_zones}
            hierarchy_dict.update(temp_dict)
    else:
        # hierarchy_dict = block_zone_hierarchy
        hierarchy_dict = {i.upper(): [k.upper() for k in j] for i, j in block_zone_hierarchy.items()}

    for i in hierarchy_dict:
        for j in hierarchy_dict[i]:
            df.columns = [k.replace(j, i + '_' + j) for k in df.columns]
            # df.columns = [k.replace(j.upper().replace(' ', '_'), i + '_' + j) for k in df.columns]

    print('Finally, the occupied zones after renaming them following the pattern block_zone are:')
    occupied_zone_list = []
    for i in hierarchy_dict:
        for j in hierarchy_dict[i]:
            occupied_zone_list.append(f'{i}:{j}')
            # print(f'{i}_{j}')

zone_hvac = [i.Zone_or_ZoneList_Name for i in building.idfobjects['ZoneControl:Thermostat']]

block_list = list(set([i.split(':')[0] for i in occupied_zone_list]))

##
# def find_alphanumeric_with_semicolon(string):
#     # Define the pattern to match alphanumeric characters on both sides of a semicolon
#     pattern = r'\b([a-zA-Z0-9]+):([a-zA-Z0-9]+)\b'
#
#     # Use regular expression to find matches
#     matches = re.findall(pattern, string)
#
#     # Return the matches
#     return matches
#
# # Example usage:
# # input_string = "abc123:def456 ghi789:jkl123"
# input_string = 'VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)'
# result = find_alphanumeric_with_semicolon(input_string)
# print("Alphanumeric characters with semicolon:", result)
#
# ##
#
# import re
#
# def find_first_two_alphanumeric_with_semicolon(string):
#     # Define the pattern to match alphanumeric characters on both sides of a semicolon
#     pattern = r'\b([a-zA-Z0-9]+):([a-zA-Z0-9]+)\b'
#
#     # Use regular expression to find matches
#     matches = re.findall(pattern, string)
#
#     # Return only the first two matches
#     return matches
#
# # Example usage:
# input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
# result = find_first_two_alphanumeric_with_semicolon(input_string)
# print("First two matches:", result)
#
# ##
#
# def extract_first_two_alphanumeric(string):
#     # Split the string at colons (:)
#     parts = string.split(':')
#
#     # Extract the first two alphanumeric words
#     alphanumeric_words = []
#     for part in parts:
#         # Using regular expression to match alphanumeric characters
#         alphanumeric = ''.join(filter(str.isalnum, part))
#         if alphanumeric:
#             alphanumeric_words.append(alphanumeric)
#             if len(alphanumeric_words) == 2:
#                 break
#
#     return alphanumeric_words
#
# # Example usage:
# input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
# result = extract_first_two_alphanumeric(input_string)
# print("First two alphanumeric words:", result)
#
# ##
#
# import re
#
# def extract_first_two_alphanumeric(string):
#     # Split the string at colons (:)
#     parts = string.split(':')
#
#     # Extract the first two alphanumeric words
#     alphanumeric_words = []
#     for part in parts:
#         # Split the part by underscore (_) and extract the first alphanumeric word
#         words = re.findall(r'\w+', part)
#         for word in words:
#             if word.isalnum():
#                 alphanumeric_words.append(word)
#                 if len(alphanumeric_words) == 2:
#                     break
#         if len(alphanumeric_words) == 2:
#             break
#
#     return alphanumeric_words
#
# # Example usage:
# input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
# result = extract_first_two_alphanumeric(input_string)
# print("First two alphanumeric words:", result)
#
#
# ##
#
# def extract_first_two_alphanumeric(string):
#     # Split the string at colons (:)
#     parts = string.split(':')
#
#     # Extract the first two alphanumeric words
#     alphanumeric_words = []
#     for part in parts:
#         # Remove leading and trailing spaces
#         part = part.strip()
#         # Extract alphanumeric words from the part
#         words = ''.join(c for c in part if c.isalnum() or c == '_').split('_')
#         # Check if the part contains at least one alphanumeric word
#         for word in words:
#             if word:
#                 alphanumeric_words.append(word)
#                 if len(alphanumeric_words) == 2:
#                     break
#         if len(alphanumeric_words) == 2:
#             break
#
#     return alphanumeric_words
#
# # Example usage:
# input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
# result = extract_first_two_alphanumeric(input_string)
# print("First two alphanumeric words:", result)
#
# ##
#
# import re
#
# def extract_alphanumeric_with_colon(string):
#     # Define the pattern to match alphanumeric words joined by ":"
#     pattern = r'\b[a-zA-Z0-9_]+\b'
#
#     # Use regular expression to find matches
#     matches = re.findall(pattern, string)
#
#     # Join the matches separated by ":"
#     result = ':'.join(matches)
#
#     return result
#
# # Example usage:
# input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
# result = extract_alphanumeric_with_colon(input_string)
# print("Alphanumeric words joined by colon:", result)
#
# ##
#
# import re
#
# def extract_alphanumeric_with_colon(string):
#     # Define the pattern to match alphanumeric words joined by ":"
#     # allowing other non-alphanumeric characters such as "_" and " "
#     pattern = r'\b[a-zA-Z0-9_]+(?::[a-zA-Z0-9_]+)*\b'
#
#     # Use regular expression to find matches
#     matches = re.findall(pattern, string)
#
#     # Join the matches separated by ":"
#     result = ':'.join(matches)
#
#     return result
#
# # Example usage:
# input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
# result = extract_alphanumeric_with_colon(input_string)
# print("Alphanumeric words joined by colon:", result)
#
# ##
#
# import re
#
# def find_alphanumeric_with_colon(string):
#     # Define the pattern to match alphanumeric characters on both sides of a colon
#     pattern = r'\b([a-zA-Z0-9]+):([a-zA-Z0-9]+):([a-zA-Z0-9]+)'
#
#     # Use regular expression to find matches
#     matches = re.findall(pattern, string)
#
#     # If there are no matches with alphanumeric characters on both sides of a colon,
#     # extract alphanumeric substrings joined by ":"
#     # if not matches:
#     #     # Define the pattern to match alphanumeric substrings joined by colon
#     #     pattern = r'\b(?:[a-zA-Z0-9]+:?)+\b'
#     #     # Use regular expression to find matches
#     #     matches = re.findall(pattern, string)
#
#     return matches
#
# # Example usage:
# input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
# result = find_alphanumeric_with_colon(input_string)
# print("Alphanumeric characters with colon or joined by colon:", result)
#
# ##
#
# import re
#
# def extract_alphanumeric_with_colon(string):
#     # Define the pattern to match alphanumeric words separated by ":"
#     pattern = r'\b[a-zA-Z0-9_]+\b'
#
#     # Use regular expression to find matches
#     matches = re.findall(pattern, string)
#
#     return matches
#
# # Example usage:
# input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
# result = extract_alphanumeric_with_colon(input_string)
# print("Alphanumeric words separated by colon:", result)
#
# ##
# string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
#
# # Split the string at colons (:)
# parts = string.split(':')
#
# # Extract the first two alphanumeric words
# alphanumeric_words = []
# for part in parts:
#     # Using regular expression to match alphanumeric characters
#     alphanumeric = ''.join(filter(str.isalnum, part))
#     if alphanumeric:
#         alphanumeric_words.append(alphanumeric)
#         if len(alphanumeric_words) == 2:
#             break
#
#
# # Example usage:
# result = extract_first_two_alphanumeric(input_string)
# print("First two alphanumeric words:", result)
#
# ##
#
# import re
#
# def find_alphanumeric_joined_by_colon(string):
#     # Define the pattern to match alphanumeric words joined by colon
#     pattern = r'\b(?:[a-zA-Z0-9]+[^a-zA-Z0-9:])+[a-zA-Z0-9]+\b'
#
#     # Use regular expression to find matches
#     matches = re.findall(pattern, string)
#
#     return matches
#
# # Example usage:
# input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
# result = find_alphanumeric_joined_by_colon(input_string)
# print("Alphanumeric words joined by colon but separated by non-alphanumeric characters:", result)
