from accim.sim import accis
accis.addAccis(ScriptType='ex_ac',
               Outputs_keep_existing=False,
               Output_type='standard',
               Output_freqs=['hourly'],
               EnergyPlus_version='9.5',
               TempCtrl='temp',
               ComfStand=[1],
               CAT=[2],
               ComfMod=[3],
               confirmGen=True)