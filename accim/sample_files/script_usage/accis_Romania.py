from accim.sim import accis
accis.AddAccis(
    script_type='vrf_mm',
    supply_air_temp_input_method='temperature difference',
    keep_existing_outputs=False,
    output_type='standard',
    output_frequencies=['hourly'],
    energyplus_version='22.2',
    setpoint_type='temp',
    comfort_standard=[1, 2, 12],
    category=[3, 80],
    comfort_mode=[0, 3],
    hvac_mode=[0, 2],
    ventilation_control=[0],
    ventilation_setpoint_offset=[0],
    min_outdoor_temp_offset=[50],
    max_wind_speed=[50],
    setpoint_tolerance_step=0.1,
    setpoint_tolerance_start=0.1,
    setpoint_tolerance_end=0.1,
    confirm=True
)
