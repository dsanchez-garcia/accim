from accim.sim import accis
accis.addAccis(
    ScriptType='vrf',
    Outputs='standard',
    EnergyPlus_version='ep96',
    TempCtrl='temp',
    AdapStand=[4, 5],
    CAT=[1],
    ComfMod=[3],
    HVACmode=[0],
    VentCtrl=[0],
    ASTtol_start=0.5,
    ASTtol_end_input=0.5,
    ASTtol_steps=0.5,
    # NameSuffix='',
    # confirmGen=True
)