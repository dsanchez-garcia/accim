from accim.sim.accis import AddAccis

x = AddAccis(
    script_type='vrf_mm',
    supply_air_temp_input_method='supply air temperature',
    keep_existing_outputs=False,
    output_type='standard',
    output_frequencies=['hourly'],
    make_outputs_dataframe=False,
    energyplus_version='23.2',
    setpoint_type='temp',

)