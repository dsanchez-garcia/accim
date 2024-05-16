#
# import accim.data.postprocessing.utils as utils
# for freq in ['hourly', 'runperiod']:
#     utils.genCSVconcatenated(
#         source_frequency='hourly',
#         frequency=freq,
#         concatenated_csv_name=f'accim_seville_{freq}'
#     )
#
# ##
# import accim.data.postprocessing.main as dpp
#
# hourly_results = dpp.Table(
#     source_concatenated_csv_filepath='accim_seville_hourly[srcfreq-hourly[freq-hourly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
#     frequency='hourly',
#     frequency_agg_func='sum',
#     standard_outputs=True,
#     level=['building'],
#     level_agg_func=['sum'],
#     split_epw_names=True,
#     idfpath='ALJARAFE CENTER_onlyGeometry.idf'
# )

##

import accim.data.postprocessing.main as dpp

runperiod_results = dpp.Table(
    source_concatenated_csv_filepath='accim_seville_runperiod[srcfreq-hourly[freq-runperiod[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    frequency='runperiod',
    frequency_agg_func='sum',
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    split_epw_names=True,
    idfpath='ALJARAFE CENTER_onlyGeometry.idf'
)

