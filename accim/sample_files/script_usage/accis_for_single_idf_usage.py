from eppy.modeleditor import IDF
from accim.sim import AddAccisToIdf, modify_accis

import besos.eppy_funcs as ef
from besos.errors import InstallationError

# Using besos
fname = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf'

try:
    idf = ef.get_building(fname)
except InstallationError:
    from accim.utils import amend_idf_version_from_dsb
    amend_idf_version_from_dsb(file_path=fname)
    idf = ef.get_building(fname)

# Apply the generic ACCIS to the in-memory IDF (modifies `idf` in place)
AddAccisToIdf(
    idf=idf,
    script_type='vrf_mm',
    supply_air_temp_method='temperature difference',
    output_keep_existing=False,
    output_type='standard',
    output_freqs=['hourly'],
    energyplus_version='9.4',
    temp_control='temperature',
)

# Apply a concrete comfort-model variant to the same IDF
modify_accis(
    idf=idf,
    comfort_standard=1,
    category=3,
    comfort_mode=3,
    # setpoint_accuracy=1000,
    hvac_mode=2,
    vent_control=0,
    cooling_season_start='01/02',
    cooling_season_end='01/03',
    # vent_setpoint_offset=0,
    # min_outdoor_temp_offset=50,
    # max_wind_speed=50,
)

idf.idfobjects['output:variable']
