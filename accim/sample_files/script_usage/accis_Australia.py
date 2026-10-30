from accim.sim import accis
accis.AddAccis(
    script_type='vrf_mm',
    supply_air_temp_input_method='temperature difference',
    output_keep_existing=False,
    output_type='standard',
    output_freqs=['hourly'],
    energyplus_version='22.2',
    temp_ctrl='temp',
    comf_stand=[14],
    cat=[80],
    comf_mod=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3],
    hvac_mode=[2],
    vent_ctrl=[0],
    vst_offset=[0],
    min_ot_offset=[50],
    max_wind_speed=[50],
    ast_tol_steps=0.1,
    ast_tol_start=0.1,
    ast_tol_end_input=0.1,
    confirm_gen=True
)
