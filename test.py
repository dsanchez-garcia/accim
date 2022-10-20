from accim.sim import accis
accis.addAccis(
    ScriptType='vrf_mm',
    Outputs='standard',
    EnergyPlus_version='22.2',
    TempCtrl='temp',
    ComfStand=[1, 7],
    CAT=[2, 90],
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[0],
    MaxWindSpeed=[0],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True
)
