"""Example of script usage with arguments."""

from accim.sim import AddAccis

scriptTypeList = ['vrf_mm']
outputsList = ['simplified', 'standard']
EPlist = ['22.2']

for i in scriptTypeList:
    for j in outputsList:
        for k in EPlist:
            AddAccis(
                script_type=i,
                output_keep_existing=False,
                output_type=j,
                output_freqs=['daily'],
                energyplus_version=k,
                temp_control='temp',
                comfort_standard=[1],
                category=[1],
                comfort_mode=[1],
                hvac_mode=[2],
                vent_control=[0],
                vent_setpoint_offset=[0],
                min_outdoor_temp_offset=[50],
                max_wind_speed=[50],
                ast_tol_start=0.1,
                ast_tol_end=0.1,
                ast_tol_steps=0.1,
                name_suffix=j
            )
