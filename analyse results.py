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
    source_concatenated_csv_filepath='ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    source_frequency='monthly',
    frequency='monthly',
    frequency_agg_func='sum',
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    split_epw_names=True,
    block_zone_hierarchy=block_zone
)

##

import pandas as pd

df = pd.read_csv('ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv')
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

def find_alphanumeric_with_semicolon(string):
    # Define the pattern to match alphanumeric characters on both sides of a semicolon
    pattern = r'\b([a-zA-Z0-9]+):([a-zA-Z0-9]+)\b'

    # Use regular expression to find matches
    matches = re.findall(pattern, string)

    # Return the matches
    return matches

# Example usage:
# input_string = "abc123:def456 ghi789:jkl123"
input_string = 'VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)'
result = find_alphanumeric_with_semicolon(input_string)
print("Alphanumeric characters with semicolon:", result)

##

import re

def find_first_two_alphanumeric_with_semicolon(string):
    # Define the pattern to match alphanumeric characters on both sides of a semicolon
    pattern = r'\b([a-zA-Z0-9]+):([a-zA-Z0-9]+)\b'

    # Use regular expression to find matches
    matches = re.findall(pattern, string)

    # Return only the first two matches
    return matches

# Example usage:
input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
result = find_first_two_alphanumeric_with_semicolon(input_string)
print("First two matches:", result)

##

def extract_first_two_alphanumeric(string):
    # Split the string at colons (:)
    parts = string.split(':')

    # Extract the first two alphanumeric words
    alphanumeric_words = []
    for part in parts:
        # Using regular expression to match alphanumeric characters
        alphanumeric = ''.join(filter(str.isalnum, part))
        if alphanumeric:
            alphanumeric_words.append(alphanumeric)
            if len(alphanumeric_words) == 2:
                break

    return alphanumeric_words

# Example usage:
input_string = "VRF OUTDOOR UNIT_BLOQUE1:BEDROOM1:VRF Heat Pump Heating Electricity Energy [J](Monthly)"
result = extract_first_two_alphanumeric(input_string)
print("First two alphanumeric words:", result)
