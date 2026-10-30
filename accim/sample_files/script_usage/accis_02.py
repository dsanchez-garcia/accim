from accim.sim import accis
accis.AddAccis(script_type='ex_ac',
               output_keep_existing=False,
               output_type='standard',
               output_freqs=['hourly'],
               energyplus_version='9.5',
               temp_ctrl='temp',
               comf_stand=[1],
               cat=[2],
               comf_mod=[3],
               confirm_gen=True)