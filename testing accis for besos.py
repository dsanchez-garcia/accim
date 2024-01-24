from eppy.modeleditor import IDF
from accim.sim import accis_single_idf as accis

import besos.eppy_funcs as ef
from besos.errors import InstallationError

## Using eppy

# iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
#
# fname = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf'
#
# IDF.setiddname(iddfile)
# idf = IDF(fname)

## Using besos
fname = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf'

try:
    idf = ef.get_building(fname)
except InstallationError:
    from accim.utils import amend_idf_version_from_dsb
    amend_idf_version_from_dsb(file_path=fname)
    idf = ef.get_building(fname)


##
# idf.idfobjects['zone']

# Using class structure

# version = f'{idf.idd_version[0]}.{idf.idd_version[1]}'

adaptive_idf = accis.addAccis(
    idf=idf,
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    EnergyPlus_version='9.4',
    TempCtrl='temperature',

)



adaptive_idf.modifyAccis(
    ComfStand=1,
    CAT=3,
    ComfMod=3,
    # SetpointAcc=1000,
    HVACmode=2,
    VentCtrl=0,
    # VSToffset=0,
    # MinOToffset=50,
    # MaxWindSpeed=50
)

# adaptive_idf_mod.idfobjects['energymanagementsystem:program']
# idf.idfobjects['energymanagementsystem:program']
adaptive_idf.SetInputData
adaptive_idf.SetVOFinputData
adaptive_idf.SetAST

idf.savecopy('z_modified_to_adaptive_2.idf')
