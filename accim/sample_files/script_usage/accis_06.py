from accim.sim import accis
import os
try:
    accis.AddAccis(
        script_type='vrf_mm',
        output_keep_existing=False,
        output_type='detailed',
        output_freqs=['timestep', 'hourly'],
        energyplus_version='22.1',
        temp_ctrl='temp',
        comf_stand=[15],
        cat=[80],
        comf_mod=[3],
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
except KeyError:
    print('\nkey error')
    for i in [j for j in os.listdir() if j.endswith('_pymod.idf')]:
        os.remove(i)
