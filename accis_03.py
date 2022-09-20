from accim.sim import accis
accis.addAccis(
    ScriptType='vrf',
    Outputs='standard',
    EnergyPlus_version='ep96',
    TempCtrl='temp',
    ComfStand=[14],
    CAT=[80],
    ComfMod=[3],
    HVACmode=[0],
    VentCtrl=[0],
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    ASTtol_steps=0.1,
    # NameSuffix='',
    # confirmGen=True
)

#test