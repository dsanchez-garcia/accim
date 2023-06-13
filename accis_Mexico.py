from accim.sim import accis

accis.addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='custom',
    Output_freqs=['hourly'],
    # Output_freqs=['hourly'],
    EnergyPlus_version='23.1',
    TempCtrl='temp',
    ComfStand=[2, 17, 18, 19, 20, 22],
    CoolSeasonStart='01/03',
    CoolSeasonEnd='15/10',
    CAT=[80, 3],
    ComfMod=[0, 3],
    SetpointAcc=1000,
    HVACmode=[0, 1, 2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    # confirmGen=True,
    # NameSuffix='date_inverse'
)
