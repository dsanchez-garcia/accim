from accim.sim import AddAccis
AddAccis(script_type='ex_ac',
               output_keep_existing=False,
               output_type='standard',
               output_freqs=['hourly'],
               energyplus_version='9.5',
               temp_control='temp',
               comfort_standard=[1],
               category=[2],
               comfort_mode=[3],
               confirm_generation=True)