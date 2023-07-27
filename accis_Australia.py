from accim.sim import accis

y = accis.addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=True,
    Output_type='detailed',
    Output_freqs=['hourly'],
    Output_gen_dataframe=True,
    # Output_freqs=['hourly'],
    EnergyPlus_version='23.1',
    TempCtrl='temp',
    ComfStand=[2, 13, 14],
    CoolSeasonStart='01/12',
    CoolSeasonEnd='28/02',
    CAT=[80],
    ComfMod=[3],
    SetpointAcc=1000,
    HVACmode=[1],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True,
    # NameSuffix='date_inverse'
)
