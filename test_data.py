# from accim.data.datawrangling import Table
# z = Table(
#     frequency='monthly',
#     sum_or_mean='sum',
#     standard_outputs=True,
#     level=['building'],
#     level_sum_or_mean=['sum', 'mean'],
#     split_epw_names=True,
#     concatenated_csv_name='testing'
# )

##

from accim.data.datawrangling import Table
z = Table(
    source_concatenated_csv_filepath='testing[freq-monthly[sum_or_mean-sum[standard_outputs-True.csv',
    # frequency='monthly',
    # sum_or_mean='sum',
    # standard_outputs=True,
    level=['building'],
    level_sum_or_mean=['sum', 'mean'],
    split_epw_names=True,
    # concatenated_csv_name='testing'
)