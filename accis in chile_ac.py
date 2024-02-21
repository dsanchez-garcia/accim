from accim.sim.accis import addAccis

# idfpath = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf'
idfpath = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940_heat_act_time_added.idf'


# apply_heating_activation_time_sch('comb 03.idf')

# apply_heating_activation_time_sch(idfpath)

##
x = addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='detailed',
    Output_freqs=['timestep'],
    EnergyPlus_version='9.4',
    TempCtrl='temp',
    ComfStand=[1],
    CAT=[3],
    ComfMod=[3],
    HVACmode=[0],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True,
    VRFschedule='Heating_activation_time_chile',
)

##

from besos import eplus_funcs
from besos import eppy_funcs

# new_idf = [i for i in os.listdir() if i.endswith('.idf') and idfpath not in i][0]
new_idf = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940_heat_act_time_added[CS_INT EN16798[CA_3[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'

building = eppy_funcs.get_building(new_idf)

eplus_funcs.run_energyplus(
    building_path=new_idf,
    epw='Mulchen-hour.epw',
    out_dir='temp_sim_outputs'
)
