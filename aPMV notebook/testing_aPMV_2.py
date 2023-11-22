# from accim.sim.aPMV_setpoints import apply_aPMV_setpoints
#
# x = apply_aPMV_setpoints(idf='aPMV_testing_v01_no_script.idf')
#
# x.add_apmv_ems_code()

from besos import eppy_funcs as ef
from besos import eplus_funcs as ep
from besos.IDF_class import IDF
import accim.sim.aPMV_setpoints as apmv
##

building = ef.get_building('aPMV_testing_v01_no_script.idf')
# idfname = "aPMV_testing_v01_no_script.idf"
epwfile = "ESP_Sevilla.083910_IWEC.epw"
#
# building = IDF(idfname=idfname, epw=epwfile)

zones = [i.Zone_or_ZoneList_Name for i in building.idfobjects['people']]

adap_coeff_cooling = {}
adap_coeff_heating = {}
tolerance = {}

for zone in zones:
    if 'zone1' in zone.lower():
        adap_coeff_cooling.update({zone: 0.4})
        adap_coeff_heating.update({zone: -0.4})
        # pmv_cooling_sp.update({i.Name: 0.3})
        # pmv_heating_sp.update({i.Name: -0.3})
    if 'zone2' in zone.lower():
        adap_coeff_cooling.update({zone: 0.3})
        adap_coeff_heating.update({zone: -0.3})
        # pmv_cooling_sp.update({i.Name: 0.2})
        # pmv_heating_sp.update({i.Name: -0.2})

##

df = apmv.generate_df_from_args(
    building=building,
    adap_coeff_cooling=adap_coeff_cooling,
    adap_coeff_heating=adap_coeff_heating,
    pmv_cooling_sp=0.5,
    pmv_heating_sp=-0.5,
)
##

apmv.set_zones_always_occupied(building=building)

building_with_apmv = apmv.add_apmv_ems_code(
    building=building,
    adap_coeff_cooling=adap_coeff_cooling,
    adap_coeff_heating=adap_coeff_heating,
    pmv_cooling_sp=0.5,
    pmv_heating_sp=-0.5,
    # tolerance=0.2,
    cooling_season_start='01/04',
    cooling_season_end='01/10',
)

##
# building_with_apmv
# epwfile = "ESP_Sevilla.083910_IWEC.epw"
# building_with_apmv[1].run(output_directory='sim_results_apmv')
#
# building.

##
# from eppy.modeleditor import IDF
#
# iddfile = 'C:\EnergyPlusV9-4-0\Energy+.idd'
# IDF.setiddname(iddfile)
#
#
# idf = IDF(idfname, epwfile)
# idf.run(output_directory='sim_results_pmv')

##

ep.run_building(
    building=building_with_apmv,
    out_dir='aPMV notebook/sim_results_apmv',
    epw=epwfile
)

##
import pandas as pd
import matplotlib.pyplot as plt

df_apmv = pd.read_csv('aPMV notebook/sim_results_apmv/eplusout.csv')

apmv_block1_zone1 = [i for i in df_apmv.columns if 'aPMV_Block1_Zone1' in i][0]
apmv_block1_zone1_cooling = [
    i
    for i
    in df_apmv.columns
    if 'aPMV' in i
       and 'Block1_Zone1' in i
       and 'cooling' in i.lower()
       and 'no tolerance' in i.lower()
]
apmv_block1_zone1_heating = [
    i
    for i
    in df_apmv.columns
    if 'aPMV' in i
       and 'Block1_Zone1' in i
       and 'heating' in i.lower()
       and 'no tolerance' in i.lower()
]

plt.plot(df_apmv[apmv_block1_zone1], color='green')
plt.plot(df_apmv[apmv_block1_zone1_cooling], color='blue')
plt.plot(df_apmv[apmv_block1_zone1_heating], color='red')
# plt.ylim(-1, 1)