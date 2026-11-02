from accim.sim import accis
accis.AddAccis(
    script_type='ex_mm',
    keep_existing_outputs=False,
    output_type='standard',
    output_frequencies=['hourly'],
    energyplus_version='9.5',
    setpoint_type='temp',
    comfort_standard=[1],
    category=[1, 2, 3],
    comfort_mode=[3],
    hvac_mode=[2],
    ventilation_control=[0],
    confirm=True
)