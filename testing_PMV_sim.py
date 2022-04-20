from accim.sim import accis
for i in [
    'pmv',
    'temp'
]:
    accis.addAccis(
        ScriptType='vrf',
        Outputs='standard',
        EnergyPlus_version='ep96',
        TempCtrl=i,
        AdapStand=[3],
        CAT=[90],
        ComfMod=[3],
        HVACmode=[2],
        VentCtrl=[0],
        NameSuffix=i
    )