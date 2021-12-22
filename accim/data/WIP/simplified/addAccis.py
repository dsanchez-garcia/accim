from accim.sim import accis
accis.addAccis(ScriptType='vrf',
               Outputs='simplified',
               EnergyPlus_version='ep96',
               AdapStand=[3],
               CAT=[1, 2, 3],
               ComfMod=[3],
               HVACmode=[2],
               VentCtrl=[0],
               NameSuffix='simplified'
               )

# from accim.run import run
# run.runEp(runOnlyAccim=True,
#           confirmRun=True)