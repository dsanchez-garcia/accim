"""Example of script usage with arguments."""

from accim.sim import accis

scriptTypeList = ['vrf_mm']
outputsList = ['simplified', 'standard']
EPlist = ['22.2']

for i in scriptTypeList:
    for j in outputsList:
        for k in EPlist:
            accis.AddAccis(
                script_type=i,
                output_keep_existing=False,
                output_type=j,
                output_freqs=['daily'],
                energyplus_version=k,
                temp_ctrl='temp',
                comf_stand=[1],
                cat=[1],
                comf_mod=[1],
                hvac_mode=[2],
                vent_ctrl=[0],
                vst_offset=[0],
                min_ot_offset=[50],
                max_wind_speed=[50],
                ast_tol_start=0.1,
                ast_tol_end_input=0.1,
                ast_tol_steps=0.1,
                name_suffix=j
            )
