from accim.sim import accis

accis.addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    EnergyPlus_version='23.1',
    TempCtrl='temp',
    # ComfStand=[2, 17, 18, 19, 20],
    ComfStand=[22],
    CoolSeasonStart='01/11',
    CoolSeasonEnd='01/04',
    CAT=[3],
    ComfMod=[0],
    SetpointAcc=1000,
    HVACmode=[2],
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
