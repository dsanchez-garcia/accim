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
    energy_units_in_kwh=False
)

dataset_hourly.df.columns


##


dataset_hourly.format_table(
    type_of_table='custom',
    custom_cols=[
        'BLOCK1:PERIMETERXZNX4_ASHRAE 55 Running mean outdoor temperature (°C)',
        'Building_Total_Cooling Energy Demand (Wh/m2) (summed)',
        'Building_Total_Heating Energy Demand (Wh/m2) (summed)',
        'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
        'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
        'Building_Total_Zone Operative Temperature (°C) (mean)'
    ]
)
##
dataset_hourly.scatter_plot(
    vars_to_gather_cols=['ComfStand', 'ComfMod', 'HVACmode'],
    vars_to_gather_rows=['EPW_City_or_subcountry', 'EPW_Scenario-Year'],
    data_on_x_axis='BLOCK1:PERIMETERXZNX4_ASHRAE 55 Running mean outdoor temperature (°C)',
    data_on_y_main_axis=[
        [
            'Energy Demand (Wh/m2)',
            [
                'Building_Total_Cooling Energy Demand (Wh/m2) (summed)',
                'Building_Total_Heating Energy Demand (Wh/m2) (summed)',
            ]
        ],
    ],
    data_on_y_sec_axis=[
        [
            'Temperature (°C)',
            [
                'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
                'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
                'Building_Total_Zone Operative Temperature (°C) (mean)'
            ]
        ],
    ],
    colorlist_y_main_axis=[
        [
            'Energy Demand (kWh/m2)', ['cyan', 'orange']
        ],
    ],
    colorlist_y_sec_axis=[
        [
            'Temperature (°C)', ['blue', 'red', 'green']
        ],
    ],
    best_fit_deg_y_main_axis=[
        [
            'Energy Demand (kWh/m2)', [1, 1]
        ],
    ],
    cols_renaming_dict={
        # 'Ahmedabad[Present': 'Ahmedabad Present',
        # 'Ahmedabad[RCP85-2100': 'Ahmedabad RCP85-2100',
        'Shimla[Present': 'Shimla Present',
        'Shimla[RCP85-2100': 'Shimla RCP85-2100'
    },
    rows_renaming_dict={
        # 'CS_IND IMAC C NV[CM_0[HM_0': 'IND_Stat_AC',
        # 'CS_IND IMAC C NV[CM_3[HM_0': 'IND_Adap_AC',
        # 'CS_IND IMAC C NV[CM_3[HM_1': 'IND_Adap_NV',
        'CS_IND IMAC C NV[CM_3[HM_2': 'IND_Adap_MM',
        # 'CS_INT ASHRAE55[CM_3[HM_0': 'ASH_Adap_AC'
    },
    sharex=True,
    sharey=True,
    supxlabel='Prevailing mean outdoor temperature (°C)',
    figname='testing_scatterplot_case_study',
    figsize=8,
    ratio_height_to_width=0.5,
    dpi=300,
    confirm_graph=True,
    set_facecolor='#f3e97975',
    best_fit_background_linewidth=2,
    best_fit_linewidth=1,
    # best_fit_linestyle=(5, (10, 3))
)