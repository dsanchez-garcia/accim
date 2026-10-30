from accim.sim.accis import AddAccis

x = AddAccis(
    script_type='vrf_mm',
    supply_air_temp_input_method='supply air temperature',
    output_keep_existing=False,
    output_type='standard',
    output_freqs=['hourly'],
    output_gen_dataframe=False,
    energyplus_version='23.2',
    temp_ctrl='temp',

)