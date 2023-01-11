from accim.sim import accis
accis.addAccis(
    ScriptType='vrf_mm',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    EnergyPlus_version='22.1',
    TempCtrl='temp',
    ComfStand=[15],
    CAT=[80],
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[2],
    MaxTempDiffVOF=20,
    MinTempDiffVOF=1,
    MultiplierVOF=0.4,
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0,
    ASTtol_end_input=2,
    # confirmGen=True
)
