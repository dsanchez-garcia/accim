import accim.sim.apmv_setpoints as apmv
from eppy.modeleditor import IDF

# Use the eppy class IDF to create an IDF instance and save it in variable 'bem'
IDF.setiddname('C:\EnergyPlusV9-4-0\Energy+.idd')
bem = IDF("ALJARAFE CENTER_mod.idf", "ESP_Sevilla.083910_IWEC.epw")

# Specify the arguments
adap_coeff_cooling = {'Block1:Zone1': 0.3, 'Block1:Zone2': 0.25}
adap_coeff_heating = {'Block1:Zone1': -0.3, 'Block1:Zone2': -0.25}

# Call the function
bem_with_apmv = apmv.apply_apmv_setpoints(
    building=bem,
    adap_coeff_cooling=adap_coeff_cooling,
    adap_coeff_heating=adap_coeff_heating,
    pmv_cooling_sp=0.5,
    pmv_heating_sp=-0.5,
    tolerance_cooling_sp_cooling_season=-0.1,
    tolerance_cooling_sp_heating_season=-0.1,
    tolerance_heating_sp_cooling_season=0.25,
    tolerance_heating_sp_heating_season=0.25,
    cooling_season_start='01/04',
    cooling_season_end='01/10',
    outputs_freq=['hourly'],
    other_PMV_related_outputs=True,
)

