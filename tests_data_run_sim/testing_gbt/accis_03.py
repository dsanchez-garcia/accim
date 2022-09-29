from accim.sim import accis
accis.addAccis(
    ScriptType='vrf',
    Outputs='standard',
    EnergyPlus_version='ep96',
    TempCtrl='temp',
    ComfStand=[4, 5],
    CAT=[1, 2],
    ComfMod=[0],
    HVACmode=[2],
    VentCtrl=[0],
    # VSToffset=[0],
    # MinOToffset=[50],
    # MaxWindSpeed=[50],
    # ASTtol_steps=0.1,
    # ASTtol_start=0.1,
    # ASTtol_end_input=0.1,
    # confirmGen=True
)
