from accim.sim import accis
accis.addAccis(ScriptType='ex_ac',
               Outputs='standard',
               EnergyPlus_version='ep95',
               AdapStand=[1],
               CAT=[2],
               ComfMod=[3],
               confirmGen=True)