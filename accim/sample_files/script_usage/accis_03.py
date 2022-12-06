from accim.sim import accis
accis.addAccis(
    ScriptType='vrf',
    Outputs='standard',
    EnergyPlus_version='9.6',
    TempCtrl='temp',
    ComfStand=[0, 1, 2, 3],
    CAT=[1, 2, 3, 80, 90],
    ComfMod=[0, 1, 2, 3],
    HVACmode=[0, 1, 2],
    VentCtrl=[0, 1],
    VSToffset=[0],
    MinOToffset=[0],
    MaxWindSpeed=[0],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True
)
