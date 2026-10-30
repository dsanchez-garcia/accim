from accim.sim import accis
accis.AddAccis(
    script_type='ex_mm',
    output_keep_existing=False,
    output_type='standard',
    output_freqs=['hourly'],
    energyplus_version='9.5',
    temp_ctrl='temp',
    comf_stand=[1],
    cat=[1, 2, 3],
    comf_mod=[3],
    hvac_mode=[2],
    vent_ctrl=[0],
    confirm_gen=True
)