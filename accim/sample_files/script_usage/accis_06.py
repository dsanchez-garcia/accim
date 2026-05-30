from accim.sim import AddAccis
import os
try:
    AddAccis(
        script_type='vrf_mm',
        output_keep_existing=False,
        output_type='detailed',
        output_freqs=['timestep', 'hourly'],
        energyplus_version='22.1',
        temp_control='temp',
        comfort_standard=[15],
        category=[80],
        comfort_mode=[3],
        hvac_mode=[2],
        vent_control=[0],
        vent_setpoint_offset=[0],
        min_outdoor_temp_offset=[50],
        max_wind_speed=[50],
        ast_tol_steps=0.1,
        ast_tol_start=0.1,
        ast_tol_end=0.1,
        confirm_generation=True
    )
except KeyError:
    print('\nkey error')
    for i in [j for j in os.listdir() if j.endswith('_pymod.idf')]:
        os.remove(i)
