from besos import eppy_funcs as ef
import accim.sim.aPMV_setpoints as apmv

# Use the function get_building to create a besos.IDF_class instance
building = ef.get_building('Office_in_Seville.idf')

# Specify the arguments
adap_coeff_cooling = {'Block1:Zone1': 0.3, 'Block1:Zone2': 0.25}
adap_coeff_heating = {'Block1:Zone1': -0.3, 'Block1:Zone2': -0.25}

# Call the function
building_with_apmv = apmv.add_apmv_ems_code(
    building=building,
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

