from accim.sim import accis

STlist = ['ex_ac', 'ex_mm']
outputlist = ['standard', 'simplified', 'timestep']

for i in STlist:
    for j in outputlist:
        accis.addAccis(ScriptType='ex_ac',
                       Outputs='standard',
                       EnergyPlus_version='ep95',
                       TempCtrl='temp',
                       ComfStand=[1],
                       CAT=[3],
                       ComfMod=[3],
                       NameSuffix=i+'_'+j,
                       confirmGen=True
                       )