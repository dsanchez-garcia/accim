from os import listdir
# csvs = [i for i in listdir() if i.endswith('.csv') and 'Zsz.csv' not in i and 'Table.csv' not in i and 'Meter.csv' not in i]
# print(*csvs, sep='\n')

from accim.data.data_postprocessing import Table
dataset_runperiod = Table(
    # datasets=[i for i in csvs if 'HM_1' not in i],
    source_frequency='hourly',
    frequency='runperiod',
    frequency_agg_func='sum',
    standard_outputs=True,
    level=['building'],
    level_agg_func=['mean'],
    level_excluded_zones=['ATTIC:ATTIC'],
    split_epw_names=True,
)

comfortable = [i for i in dataset_runperiod.df.columns if 'comfortable hours' in i.lower() and 'no applicability' in i.lower()]
print(*comfortable, sep='\n')
print(*dataset_runperiod.df.columns, sep='\n')

dataset_runperiod.format_table(
    type_of_table='custom',
    custom_cols=[
        'Building_Total_Comfortable Hours_No Applicability (h) (mean)',
        'Whole Building Facility Total HVAC Electricity Demand Rate (kWh/m2)'
    ]
)

dataset_runperiod.wrangled_table(
    reshaping='multiindex',
    # vars_to_gather=['ComfStand', 'ComfMod', 'HVACmode'],
    # baseline='CS_IND IMAC C NV[CM_3[HM_2',
    # vars_to_keep=['EPW_City_or_subcountry', 'EPW_Scenario', 'EPW_Year'],
    # comparison_mode=['baseline compared to others'],
    # comparison_cols=['relative'],
    # rename_dict={
    #     'CS_IND IMAC C NV[CM_0[HM_0': 'Ind_Stat_AC',
    #     'CS_IND IMAC C NV[CM_3[HM_0': 'Ind_Adap_AC',
    #     'CS_IND IMAC C NV[CM_3[HM_2': 'Ind_Adap_MM',
    #     'CS_INT ASHRAE55[CM_3[HM_0': 'ASH_Adap_AC'
    # },
    # transpose=True,
    excel_filename='testing_accim'
)
