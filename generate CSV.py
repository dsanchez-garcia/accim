import accim.data.data_postprocessing as dp

dp.genCSVconcatenated(
    source_frequency='monthly',
    frequency='monthly',
    concatenated_csv_name='ACCIM_Chile'
)

# dp.Table(
#     source_frequency='monthly',
#     frequency='monthly',
#     frequency_agg_func='sum',
#     standard_outputs=True,
#     concatenated_csv_name='ACCIM_Chile'
# )
