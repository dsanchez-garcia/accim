from accim.sim import accis

import besos.eppy_funcs as ef
from besos.errors import InstallationError

# Using eppy

# from eppy.modeleditor import IDF
# iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
#
# fname = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf'
#
# IDF.setiddname(iddfile)
# idf = IDF(fname)

# Using besos
fname = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf'

try:
    idf = ef.get_building(fname)
except InstallationError:
    from accim.utils import amend_idf_version_from_dsb
    amend_idf_version_from_dsb(file_path=fname)
    idf = ef.get_building(fname)

# Adding the ACCIS to the IDF object

model = accis.add_accis_to_idf(
    idf,
    script_type='vrf_mm',
    supply_air_temp_input_method='temperature difference',
    keep_existing_outputs=False,
    output_type='standard',
    output_frequencies=['hourly'],
    energyplus_version='9.4',
    setpoint_type='temperature',
)
model.occupied_zones

# Setting its arguments, in all the zones

accis.modify_accis(
    idf,
    comfort_standard=1,
    category=3,
    comfort_mode=3,
    # setpoint_accuracy=1000,
    hvac_mode=2,
    ventilation_control=0,
    cooling_season_start='01/02',
    cooling_season_end='01/03'
    # ventilation_setpoint_offset=0,
    # min_outdoor_temp_offset=50,
    # max_wind_speed=50
)

# Each zone can have its own arguments: here, the zone Block1:Zone2 has the ASHRAE 55 model and no natural
# ventilation, and the other zones keep those above. The arguments of each zone are in its EMS program
# SetInputData_<zone>.

accis.modify_accis(
    idf,
    comfort_standard=1,
    category=3,
    comfort_mode=3,
    hvac_mode=2,
    ventilation_control=0,
    zone_arguments={'Block1:Zone2': {'comfort_standard': 2, 'category': 80, 'hvac_mode': 0}},
)

programs = {program.Name: program for program in idf.idfobjects['EnergyManagementSystem:Program']}
programs['SetInputData_Block1_Zone1']
programs['SetInputData_Block1_Zone2']
programs['RunACCIS_Block1_Zone1']

# idf.savecopy('z_modified_to_adaptive_3.idf')

##

idf.idfobjects['output:variable']
