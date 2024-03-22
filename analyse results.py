from accim.data.postprocessing.data_postprocessing_wip import Table
import pandas as pd

data_analysis = Table(
    source_concatenated_csv_filepath='WIP_data_postprocessing/ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    source_frequency='monthly',
    frequency='monthly',
    frequency_agg_func='sum',
    # standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    split_epw_names=True,
    idfpath='ChileanModel.idf',
    level_excluded_zones=[],
    normalised_energy_units=False
    # block_zone_hierarchy=block_zone
)
##

data_analysis.df.columns
data_analysis.df.to_excel('total_to_be_deleted.xlsx')

# df_orig = pd.read_csv(
#     'WIP_data_postprocessing/ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
# )
# df_orig.columns