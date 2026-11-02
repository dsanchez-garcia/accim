from accim.sim import accis
import os
try:
    accis.AddAccis(
        script_type='vrf_mm',
        keep_existing_outputs=False,
        output_type='detailed',
        output_frequencies=['timestep', 'hourly'],
        energyplus_version='22.1',
        setpoint_type='temp',
        comfort_standard=[15],
        category=[80],
        comfort_mode=[3],
        hvac_mode=[2],
        ventilation_control=[0],
        ventilation_setpoint_offset=[0],
        min_outdoor_temp_offset=[50],
        max_wind_speed=[50],
        setpoint_tolerance_step=0.1,
        setpoint_tolerance_start=0.1,
        setpoint_tolerance_end=0.1,
        confirm=True
    )
except KeyError:
    print('\nkey error')
    for i in [j for j in os.listdir() if j.endswith('_pymod.idf')]:
        os.remove(i)
