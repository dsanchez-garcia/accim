from accim.sim import accis
accis.addAccis(
    ScriptType='ex_mm',
    Outputs_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    EnergyPlus_version='9.5',
    TempCtrl='temp',
    ComfStand=[1],
    CAT=[1, 2, 3],
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[0],
    confirmGen=True
)