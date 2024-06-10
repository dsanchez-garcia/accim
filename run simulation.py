from besos import eplus_funcs
from besos import eppy_funcs
import os

# new_idf = r'D:\Python\accim_project\accim\smalloffice_osm_no_hvac[CS_INT ASHRAE55[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'
# new_idf = r'C:\Python\accim\smalloffice_osm_no_hvac[CS_INT ASHRAE55[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'

# new_idf = [i for i in os.listdir() if i.endswith('.idf') if i != 'TestModel.idf'
#            and 'TestModel' in i
#            ][0]

# new_idf = 'OSM_SmallOffice_exHVAC_always-occ_V2320.idf'
# new_idf = 'smalloffice_osm_hvac_always_occ[CS_INT ASHRAE55[CA_80[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'

# new_idf = r'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940[CS_CUSTOM[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'

new_idf = 'test_vrf_pmv.idf'

building = eppy_funcs.get_building(new_idf)
epws = [i for i in os.listdir() if i.endswith('.epw') and 'Seville' in i]
epwnames = [i.split('.epw')[0] for i in epws]
for i, epw in enumerate(epws):
    eplus_funcs.run_energyplus(
        building_path=new_idf,
        epw='D:/Python/accim_project/accim/'+epw,
        out_dir=f'temp_sim_outputs_pmv_{epwnames[i]}'
    )
