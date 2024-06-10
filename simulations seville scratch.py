from accim.sim import accis
from accim.utils import set_occupancy_to_always_path

set_occupancy_to_always_path('TestModel.idf')
accis.addAccis(
    idfs=['TestModel.idf'],
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_type='standard',
    Output_freqs=['hourly'],
    Output_keep_existing=False,
    TempCtrl='temp',
    ComfStand=[99],
    ComfMod=[3],
    CAT=[3],
    CustAST_m=0.24,
    CustAST_n=19.3,
    CustAST_AHSToffset=-3.5,
    CustAST_ACSToffset=3.5,
    CustAST_AHSTaul=33.5,
    CustAST_AHSTall=10,
    CustAST_ACSTaul=33.5,
    CustAST_ACSTall=10,
    HVACmode=[2],
    VentCtrl=[0],
    NameSuffix='seville'
)
##
from accim.sim import accis

accis.addAccis(
    idfs=['ALJARAFE CENTER_onlyGeometry.idf'],
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_type='standard',
    Output_freqs=['hourly'],
    Output_keep_existing=False,
    TempCtrl='temp',
    ComfStand=[2],
    CAT=[80],
    ComfMod=[3],
    HVACmode=[1],
    VentCtrl=[0],
)
##
from accim.sim import accis

accis.addAccis(
    idfs=['ALJARAFE CENTER_onlyGeometry.idf'],
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_type='standard',
    Output_freqs=['hourly'],
    Output_keep_existing=False,
    TempCtrl='temp',
    ComfMod=[3],
    CAT=[3],
    ComfStand=[99],
    CustAST_m=0,
    CustAST_n=23,
    CustAST_AHSToffset=-2,
    CustAST_ACSToffset=2,
    CustAST_AHSTaul=33.5,
    CustAST_AHSTall=10,
    CustAST_ACSTaul=33.5,
    CustAST_ACSTall=10,
    HVACmode=[1],
    VentCtrl=[0],
    NameSuffix='rite'
)

##

from besos import eplus_funcs
from besos import eppy_funcs
import os

# new_idf = r'D:\Python\accim_project\accim\smalloffice_osm_no_hvac[CS_INT ASHRAE55[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'
# new_idf = r'C:\Python\accim\smalloffice_osm_no_hvac[CS_INT ASHRAE55[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'

new_idf = [i for i in os.listdir() if i.endswith('.idf') if i != 'TestModel.idf'
           and 'TestModel' in i
           ][0]

# new_idf = 'OSM_SmallOffice_exHVAC_always-occ_V2320.idf'
# new_idf = 'smalloffice_osm_hvac_always_occ[CS_INT ASHRAE55[CA_80[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'

# new_idf = r'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940[CS_CUSTOM[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'

building = eppy_funcs.get_building(new_idf)
epws = [i for i in os.listdir() if i.endswith('.epw') and 'Seville' in i]
epwnames = [i.split('.epw')[0] for i in epws]
for i, epw in enumerate(epws):
    eplus_funcs.run_energyplus(
        building_path=new_idf,
        epw='D:/Python/accim_project/accim/'+epw,
        out_dir=f'temp_sim_outputs_rite_{epwnames[i]}'
    )
