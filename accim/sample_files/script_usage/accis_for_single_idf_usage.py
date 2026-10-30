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
    output_keep_existing=False,
    output_type='standard',
    output_freqs=['hourly'],
    energyplus_version='9.4',
    temp_ctrl='temperature',
)
model.occupied_zones

# Setting its arguments

accis.modify_accis(
    idf,
    comf_stand=1,
    cat=3,
    comf_mod=3,
    # setpoint_acc=1000,
    hvac_mode=2,
    vent_ctrl=0,
    cool_season_start='01/02',
    cool_season_end='01/03'
    # vst_offset=0,
    # min_ot_offset=50,
    # max_wind_speed=50
)

programs = {program.Name: program for program in idf.idfobjects['EnergyManagementSystem:Program']}
programs['SetInputData']
programs['SetVOFinputData']
programs['SetAST']

# idf.savecopy('z_modified_to_adaptive_3.idf')

##

idf.idfobjects['output:variable']
