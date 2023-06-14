from accim.sim import accis

x = accis.addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=True,
    Output_type='detailed',
    Output_freqs=['hourly'],
    Output_gen_dataframe=True,
    # Output_freqs=['hourly'],
    EnergyPlus_version='23.1',
    TempCtrl='temp',
    ComfStand=[17],
    CoolSeasonStart='01/03',
    CoolSeasonEnd='15/10',
    CAT=[80],
    ComfMod=[3],
    SetpointAcc=1000,
    HVACmode=[2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=False,
    # NameSuffix='date_inverse'
)

df_outputs_in = x.df_outputs
##
df_outputs_in = df_outputs_in[
    (
        df_outputs_in['variable_name'].str.contains('BLOCK1_BEDROOM1')
        |
        df_outputs_in['key_value'].str.contains('BLOCK1_BEDROOM1')
    )
    &
    (
        df_outputs_in['variable_name'].str.contains('Heating Coil Heating Rate')
        |
        df_outputs_in['variable_name'].str.contains('Cooling Coil Total Cooling Rate')
        |
        df_outputs_in['variable_name'].str.contains('Comfortable Hours_No Applicability')
    )
]
##
x = accis.addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    Output_gen_dataframe=True,
    Output_take_dataframe=df_outputs_in,
    # Output_freqs=['hourly'],
    EnergyPlus_version='23.1',
    TempCtrl='temp',
    ComfStand=[17],
    CoolSeasonStart='01/03',
    CoolSeasonEnd='15/10',
    CAT=[80],
    ComfMod=[3],
    SetpointAcc=1000,
    HVACmode=[2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    # confirmGen=False,
    # NameSuffix='date_inverse'
)
