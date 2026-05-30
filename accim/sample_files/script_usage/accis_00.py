from accim.sim import AddAccis

STlist = ['ex_ac', 'ex_mm']
outputlist = ['standard', 'simplified']

for i in STlist:
    for j in outputlist:
        AddAccis(
            script_type='ex_ac',
            output_keep_existing=True,
            output_type=j,
            output_freqs=['hourly'],
            energyplus_version='22.2',
            temp_control='temp',
            comfort_standard=[1],
            category=[3],
            comfort_mode=[3],
            name_suffix=i+'_'+j,
            confirm_generation=True
        )