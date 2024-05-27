from accim.data.postprocessing.main import Table
import pandas as pd

data_analysis = Table(
    # source_concatenated_csv_filepath='WIP_data_postprocessing/ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    source_frequency='hourly',
    frequency='monthly',
    frequency_agg_func='sum',
    # standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    # split_epw_names=True,
    idf_path='OSM_SmallOffice_exHVAC_always-occ_V2320[CS_INT ASHRAE55[CA_80[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf',
    level_excluded_zones=[],
    normalised_energy_units=True,

    # block_zone_hierarchy=block_zone
)
##

print(*data_analysis.df.columns, sep='\n')
data_analysis.df.to_excel('total_to_be_deleted_normalised.xlsx')

# df_orig = pd.read_csv(
#     'WIP_data_postprocessing/ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
# )
# df_orig.columns