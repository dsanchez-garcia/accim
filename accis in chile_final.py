from accim.sim.accis import addAccis
from accim.utils import amend_idf_version_from_dsb
from accim.sim.chile_funcs import apply_heating_activation_time_sch



x = addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='custom',
    Output_freqs=['monthly'],
    EnergyPlus_version='23.1',
    TempCtrl='temp',
    ComfStand=[21],
    CAT=[80],
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=1.9,
    ASTtol_start=1.9,
    ASTtol_end_input=1.9,
    confirmGen=True,
    VRFschedule='Heating_activation_time_chile',
    eer=1,
    cop=0.8,
)

# output_idf = x.output_idfs[[i for i in x.output_idfs.keys()][0]]
# output_idf.idfobjects['Output:variable']


##

from besos import eplus_funcs
from besos import eppy_funcs

# new_idf = [i for i in os.listdir() if i.endswith('.idf') and idfpath not in i][0]
# new_idf = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940_heat_act_time_added[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'
# new_idf = 'caso_01.1_2_heat_act_time_added[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'
# new_idf = 'caso_01.1_3[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'
# new_idf = 'testmodel_chile_2_heat_act_time_added[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'
# new_idf = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'
# new_idf = 'testmodel_chile_2_lightweight_uninsulated_heat_act_time_added[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'
# new_idf = 'COMB 03_mod_no-door_lightweight_uninsulated_heat_act_time_added[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'
new_idf = 'COMB 03_mod_no-door_lightweight_uninsulated_heat_act_time_added[CS_CHL Perez-Fargallo[CA_80[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'

building = eppy_funcs.get_building(new_idf)

eplus_funcs.run_energyplus(
    building_path=new_idf,
    epw='CHL_Concepcion.856820_IWEC.epw',
    out_dir='temp_sim_outputs'
)
