from accim.sim import accis
accis.AddAccis(
    script_type='vrf_mm',
    supply_air_temp_input_method='temperature difference',
    keep_existing_outputs=False,
    output_type='standard',
    output_frequencies=['hourly'],
    energyplus_version='22.2',
    setpoint_type='temp',
    comfort_standard=[0, 1, 2, 3],
    category=[1, 2, 3, 80, 90],
    comfort_mode=[0, 1, 2, 3],
    hvac_mode=[0, 1, 2],
    ventilation_control=[0, 1],
    ventilation_setpoint_offset=[0],
    min_outdoor_temp_offset=[0],
    max_wind_speed=[0],
    setpoint_tolerance_step=0.1,
    setpoint_tolerance_start=0.1,
    setpoint_tolerance_end=0.1,
    # confirm=True
)
