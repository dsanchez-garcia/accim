# from accim.utils import update_idf_version
# from os import listdir
# idfs = [i for i in listdir() if i.endswith('.idf')]
# for idf in idfs:
#     update_idf_version(
#         input_idf_path=idf,
#         ep_version_target='25.1.0',
#         # output_idf_name ='OSM_SmallOffice_noHVAC_always-occ_V{version}.idf'
#     )

##

# base_idf = 'TestModel_ExistingHVAC_PTAC.idf'
base_idf = 'OSM_SmallOffice_exHVAC_always-occ.idf'
output_idf = base_idf.replace('.idf', '') + '[CS_AUS DeDear[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'

from accim.sim import accis
accis.addAccis(
    idfs=[base_idf],
    ScriptType='ex_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    # EnergyPlus_version='auto',
    TempCtrl='temp',
    ComfStand=[14],
    CAT=[80],
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True
)

##

from besos.eplus_funcs import run_building, run_energyplus

run_energyplus(
    # building_path='TestResidentialUnit_v01_onlygeometry_SchNatVent[CS_AUS DeDear[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf',
    # building_path='OSM_SmallOffice_exHVAC_always-occ.idf',
    # building_path='TestModel_ExistingHVAC_PTAC.idf',
    # building_path=output_idf,
    epw='Sydney.epw',
    out_dir='temp_output_dir_9'
)
