from accim.data.data_postprocessing import Table
z = Table(
    source_concatenated_csv_filepath='Australia_ACCIM[srcfreq-hourly[freq-runperiod[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    level=['building'],
    level_agg_func=['sum', 'mean'],
    level_excluded_zones=[],
    split_epw_names=True,
    normalised_energy_units=True,
    rename_cols=True,
    energy_units_in_kwh=True,
)

z.format_table(
    type_of_table='temperature',
    # custom_cols=[  # if type_of_table is 'custom', custom_cols is used to filter the desired columns to keep
    #     'Adaptive Cooling Setpoint Temperature_No Tolerance (°C)',
    #     'Adaptive Heating Setpoint Temperature_No Tolerance (°C)',
    #     'Building_Total_Zone Operative Temperature (°C) (mean)',
    #     'BLOCK1:LIVINGROOM_ASHRAE 55 Running mean outdoor temperature (°C)',
    #     'Building_Total_Cooling Energy Demand (kWh/m2) (summed)',
    #     'Building_Total_Heating Energy Demand (kWh/m2) (summed)',
    #
    #     # 'Building_Total_AFN Zone Infiltration Air Change Rate (ach) (summed)'
    # ]
)

print(*z.df.columns, sep='\n')

df_mod = z.df.copy()

df_mod['ComfMod'] = [
    i.replace('CM_0.1', 'CM_0').replace('CM_0.2', 'CM_0').replace('CM_0.3', 'CM_0').replace('CM_0.4', 'CM_0').replace('CM_0.5', 'CM_0')
    for i
    in df_mod['ComfMod']
]

z.df = df_mod


# df_filtered = z.df.copy()
# df_filtered = df_filtered[
#     (df_filtered['Building_Total_Zone Operative Temperature (°C) (mean)'] < df_filtered['Adaptive Cooling Setpoint Temperature_No Tolerance (°C)'])
#     &
#     (df_filtered['Building_Total_Zone Operative Temperature (°C) (mean)'] > df_filtered['Adaptive Heating Setpoint Temperature_No Tolerance (°C)'])
#     ]
# z.df = df_filtered


z.df.columns = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('Building_Total_', '')
    .replace(' (summed)', '')
    for i in z.val_cols]
z.df.columns = [i
    .replace('_No Tolerance', '')
    for i in z.df.columns]
z.val_cols = [i
    .replace('_No Tolerance', '')
    for i in z.val_cols]



z.scatter_plot(
    vars_to_gather_cols=['ComfStand', 'ComfMod'],
    vars_to_gather_rows=['EPW_City_or_subcountry'],
    # detailed_rows=['GC01-Florianopolis', 'GC07-Chapeco', 'GC20-Palmas'],
    # detailed_cols=['CS_BRA Rupp NV[CM_0[HM_0', 'CS_INT ASHRAE55[CM_3[HM_0', 'CS_BRA Rupp NV[CM_3[HM_2'],
    # custom_rows_order=data_daily.ordered_list,
    # custom_cols_order=['CS_BRA Rupp NV[CM_0[HM_0', 'CS_INT ASHRAE55[CM_3[HM_0', 'CS_BRA Rupp NV[CM_3[HM_2'],
    data_on_x_axis='BLOCK1:STUDYNOOK_ASHRAE 55 Running mean outdoor temperature (°C)',
    data_on_y_sec_axis=[ #list which includes the name of the axis on the first place, and then in the second place, a list which includes the column names you want to plot
        [
            'Indoor Operative Temperature (°C)',
            [
                'Adaptive Cooling Setpoint Temperature (°C)',
                'Adaptive Heating Setpoint Temperature (°C)',
                'Zone Operative Temperature (°C) (mean)',
            ]
        ],
    ],
    data_on_y_main_axis=[ # similarly to above, a list including the name of the secondary y-axis and the column names you want to plot in it
        [
            'Energy (kWh/m2)',
            [
                'Cooling Energy Demand (kWh/m2)',
                'Heating Energy Demand (kWh/m2)',
            ]
        ],
    ],
    colorlist_y_sec_axis=[
        [
            'Indoor Operative Temperature (°C)',
            [
                'b',
                'r',
                'g',
            ]
        ],
    ],
    colorlist_y_main_axis=[
        [
            'Energy (kWh/m2)',
            [
                'cyan',
                'orange',
            ]
        ]
    ],
    best_fit_deg_y_main_axis=[
        [
            'Energy (kWh/m2)',
            [
                1,
                1,
            ]
        ]
    ],

    supxlabel='Prevailing Mean Outdoor Temperature (°C)', # data label on x axis
    figname=f'Fig_XX_scatterplot_PMOT_v00_300dpi',
    figsize=4,
    ratio_height_to_width=0.5,
    confirm_graph=True,
    dpi=300
)
