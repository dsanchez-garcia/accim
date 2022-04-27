from accim.data.datawrangling import Table
z = Table(
    frequency='monthly',
    sum_or_mean='sum',
    standard_outputs=True,
    # level=['building'],
    # level_sum_or_mean=['sum', 'mean'],
    # split_epw_names=True,
    concatenated_csv_name='testing_03'
)

##

# from accim.data.datawrangling import Table
# z = Table(
#     source_concatenated_csv_filepath='testing[freq-daily[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
#     # frequency='monthly',
#     # sum_or_mean='sum',
#     # standard_outputs=True,
#     level=['building'],
#     level_sum_or_mean=['sum', 'mean'],
#     split_epw_names=True,
#     # concatenated_csv_name='testing'
# )

##

# from accim.data.datawrangling import Table
# for i in ['hourly', 'daily', 'monthly', 'runperiod']:
#     z = Table(
#         # source_concatenated_csv_filepath='testing[freq-daily[sum_or_mean-sum[standard_outputs-True[CSVconcatenated.csv',
#         frequency=i,
#         sum_or_mean='sum',
#         standard_outputs=True,
#         level=['building'],
#         level_sum_or_mean=['sum', 'mean'],
#         split_epw_names=True,
#         # concatenated_csv_name='testing'
#     )
#     z.df.to_excel(f'testing_{i}.xlsx')
