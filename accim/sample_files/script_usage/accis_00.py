from accim.sim import accis

STlist = ['ex_ac', 'ex_mm']
outputlist = ['standard', 'simplified']

for i in STlist:
    for j in outputlist:
        accis.addAccis(
            ScriptType='ex_ac',
            Outputs_keep_existing=True,
            Output_type=j,
            Output_freqs=['hourly'],
            EnergyPlus_version='22.2',
            TempCtrl='temp',
            ComfStand=[1],
            CAT=[3],
            ComfMod=[3],
            NameSuffix=i+'_'+j,
            confirmGen=True
        )