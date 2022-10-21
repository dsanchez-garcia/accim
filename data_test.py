

from accim.data.datawrangling import Table
dataset_hourly = Table(
    #datasets=list Since we are not specifying any list, it will use all available CSVs in the folder
    frequency='hourly',
    frequency_sum_or_mean='sum', #this makes the sum or average when aggregating in days, months or runperiod; since the original CSV frequency is in hour, it won't make any aeffect
    standard_outputs=True,
    level=['building'],
    level_sum_or_mean=['sum'],
    #match_cities=bool Only used when EPW file has NOT been previously renamed
    #manage_epw_names=bool Only used when EPW file has NOT been previously renamed
    split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
    concatenated_csv_name='notebook_example' #Useful when working with large datasets. It saves the output dataset to a CSV file, so you don't need to re-do some work. Afterwards, it can be imported with source_concatenated_csv_filepath argument.
)

dataset_hourly = Table(
    # split_epw_names=True, #to split EPW names based on the format Country_City_RCPscenario-YEar
    # frequency='hourly',
    # frequency_sum_or_mean='sum',
    source_concatenated_csv_filepath='notebook_example[freq-hourly[frequency_sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv'
)

