from accim.sim.accis import addAccis

x = addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='supply air temperature',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    Output_gen_dataframe=False,
    EnergyPlus_version='23.2',
    TempCtrl='temp',

)