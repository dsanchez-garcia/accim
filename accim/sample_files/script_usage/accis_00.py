from accim.sim import accis

STlist = ['ex_ac', 'ex_mm']
outputlist = ['standard', 'simplified']

for i in STlist:
    for j in outputlist:
        accis.AddAccis(
            script_type='ex_ac',
            output_keep_existing=True,
            output_type=j,
            output_freqs=['hourly'],
            energyplus_version='22.2',
            temp_ctrl='temp',
            comf_stand=[1],
            cat=[3],
            comf_mod=[3],
            name_suffix=i+'_'+j,
            confirm_gen=True
        )