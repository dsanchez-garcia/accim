"""Example of script usage with arguments."""

from accim.sim import accis

scriptTypeList = ['vrf_mm']
outputsFreqList = [['hourly'], ['daily'], ['monthly'], ['runperiod'], ['hourly', 'daily', 'monthly', 'runperiod']]
EPlist = ['22.2']

for i in scriptTypeList:
    for j in range(len(outputsFreqList)):
        for k in EPlist:
            accis.AddAccis(
                script_type=i,
                keep_existing_outputs=False,
                output_type='standard',
                output_frequencies=outputsFreqList[j],
                energyplus_version=k,
                setpoint_type='temp',
                comfort_standard=[1],
                category=[1],
                comfort_mode=[1],
                hvac_mode=[2],
                ventilation_control=[0],
                ventilation_setpoint_offset=[0],
                min_outdoor_temp_offset=[50],
                max_wind_speed=[50],
                setpoint_tolerance_start=0.1,
                setpoint_tolerance_end=0.1,
                setpoint_tolerance_step=0.1,
                name_suffix='_'.join(outputsFreqList[j])
            )
