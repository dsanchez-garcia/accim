from accim.sim import accis
accis.addAccis(ScriptType='vrf',
               Outputs='standard',
               EnergyPlus_version='ep96',
               TempCtrl='temp',
               AdapStand=[3],
               CAT=[80],
               ComfMod=[3],
               HVACmode=[2],
               VentCtrl=[0],
               confirmGen=True)