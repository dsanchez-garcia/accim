from accim.sim import accis

STlist = ['ex_ac', 'ex_mm']
outputlist = ['standard', 'simplified']

for i in STlist:
    for j in outputlist:
        accis.AddAccis(
            script_type='ex_ac',
            keep_existing_outputs=True,
            output_type=j,
            output_frequencies=['hourly'],
            energyplus_version='22.2',
            setpoint_type='temp',
            comfort_standard=[1],
            category=[3],
            comfort_mode=[3],
            name_suffix=i+'_'+j,
            confirm=True
        )