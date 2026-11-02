from accim.sim import accis
accis.AddAccis(script_type='ex_ac',
               keep_existing_outputs=False,
               output_type='standard',
               output_frequencies=['hourly'],
               energyplus_version='9.5',
               setpoint_type='temp',
               comfort_standard=[1],
               category=[2],
               comfort_mode=[3],
               confirm=True)