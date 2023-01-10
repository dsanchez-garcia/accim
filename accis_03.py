from accim.sim import accis
accis.addAccis(
    ScriptType='vrf_mm',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['timestep'],
    EnergyPlus_version='22.2',
    TempCtrl='temp',
    ComfStand=[1],
    CAT=[3],
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[2, 3],
    MaxTempDiffVOF=10,
    MinTempDiffVOF=1,
    MultiplierVOF=0,
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True
)
