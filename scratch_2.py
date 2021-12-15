from accim.sim import accis
accis.addAccis(ScriptType='ex_mm',
               Outputs='standard',
               EnergyPlus_version='ep95',
               AdapStand=[1],
               CAT=[2],
               ComfMod=[3],
               HVACmode=[2],
               VentCtrl=[0],
               confirmGen=True)