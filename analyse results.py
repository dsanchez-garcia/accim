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
    level_excluded_zones=[]
    # block_zone_hierarchy=block_zone
)

data_analysis.df.columns

df_orig = pd.read_csv(
    'WIP_data_postprocessing/ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
)
df_orig.columns