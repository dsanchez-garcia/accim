
from accim.data.data_postprocessing import Table
dataset_hourly = Table(
    source_frequency='hourly',
    frequency='hourly',
    frequency_agg_func='sum',
    standard_outputs=True,
    level=['building'],
    level_agg_func=['mean', 'sum'],
    level_excluded_zones=['ATTIC:ATTIC'],
    split_epw_names=True,
)

dataset_hourly.format_table(
    type_of_table='custom',
    custom_cols=[
        'BLOCK1:PERIMETERXZNX4_ASHRAE 55 Running mean outdoor temperature (°C)',
        'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
        'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'Building_Total_Zone Operative Temperature (°C) (mean)'
    ]
)



dataset_hourly.scatter_plot_with_baseline(
    vars_to_gather_rows=['EPW_City_or_subcountry', 'EPW_Scenario-Year'],
    vars_to_gather_cols=['ComfStand', 'ComfMod', 'HVACmode'],
    detailed_cols=[
        'CS_IND IMAC C NV[CM_0[HM_0',
    #     'CS_IND IMAC C NV[CM_3[HM_0',
    #     'CS_INT ASHRAE55[CM_3[HM_0'
    ],
    data_on_y_axis_baseline_plot=[
                'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
                'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    ],
    colorlist_baseline_plot_data=[
                'blue',
                'red'
    ],
    baseline='CS_IND IMAC C NV[CM_3[HM_2',
    rows_renaming_dict={
        # 'Ahmedabad[Present': 'Ahmedabad Present',
        # 'Ahmedabad[RCP85-2100': 'Ahmedabad RCP85-2100',
        'Shimla[Present': 'Shimla Present',
        'Shimla[RCP85-2100': 'Shimla RCP85-2100'
    },
    cols_renaming_dict={
        'CS_IND IMAC C NV[CM_0[HM_0': 'IND_Stat_AC',
        # 'CS_IND IMAC C NV[CM_3[HM_0': 'IND_Adap_AC',
        # 'CS_INT ASHRAE55[CM_3[HM_0': 'ASH_Adap_AC'
    },
    supxlabel='IND_Adap_MM Hourly Energy Demand (kWh/m²)',
    supylabel='Reference Hourly Energy Demand (kWh/m²)',
    figname='testing_scatterplotbaseline_case_study',
    figsize=3,
    dpi=300,
    confirm_graph=True
)


