from accim.sim import AddAccis
AddAccis(
    script_type='vrf_mm',
    supply_air_temp_method='temperature difference',
    output_keep_existing=False,
    output_type='standard',
    output_freqs=['hourly'],
    energyplus_version='22.2',
    temp_control='temp',
    comfort_standard=[1, 2, 12],
    category=[3, 80],
    comfort_mode=[0, 3],
    hvac_mode=[0, 2],
    vent_control=[0],
    vent_setpoint_offset=[0],
    min_outdoor_temp_offset=[50],
    max_wind_speed=[50],
    ast_tol_steps=0.1,
    ast_tol_start=0.1,
    ast_tol_end=0.1,
    confirm_generation=True
)
