from accim.sim import AddAccis
AddAccis(
    script_type='ex_mm',
    output_keep_existing=False,
    output_type='standard',
    output_freqs=['hourly'],
    energyplus_version='9.5',
    temp_control='temp',
    comfort_standard=[1],
    category=[1, 2, 3],
    comfort_mode=[3],
    hvac_mode=[2],
    vent_control=[0],
    confirm_generation=True
)