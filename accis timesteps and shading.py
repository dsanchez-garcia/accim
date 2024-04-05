from accim.sim.accis import addAccis
from accim.utils import amend_idf_version_from_dsb
from accim.sim.chile_funcs import apply_heating_activation_time_sch
import os
from besos.eppy_funcs import get_building

orig_idf = [i for i in os.listdir() if i.endswith('.idf')
            # and '20zones' in i
            ][0]

# from besos.eppy_funcs import get_building
# x = get_building(orig_idf)
#
# [i for i in x.idfobjects['Spacelist']]

##
def reduce_runtime(
        idf_object,
        minimal_shadowing: bool = True,
        shading_calculation_update_frequency: int = 20,
        maximum_figures_in_shadow_overlap_calculations: int = 15000,
        timesteps: int = 6,
        ):

    if minimal_shadowing:
        obj_building = [i for i in idf_object.idfobjects['Building']][0]
        if obj_building.Solar_Distribution == 'MinimalShadowing':
            print('Solar distribution is already set to MinimalShadowing, therefore no action has been performed.')
        else:
            obj_building.Solar_Distribution = 'MinimalShadowing'
            print('Solar distribution has been set to MinimalShadowing.')

    obj_shadowcalc = [i for i in idf_object.idfobjects['ShadowCalculation']][0]
    shadowcalc_freq_prev = obj_shadowcalc.Shading_Calculation_Update_Frequency
    obj_shadowcalc.Shading_Calculation_Update_Frequency = shading_calculation_update_frequency
    print(f'Shading Calculation Update Frequency was previously set to '
          f'{shadowcalc_freq_prev} days, and it has been modified to {shading_calculation_update_frequency} days.')
    shadowcalc_maxfigs_prev = obj_shadowcalc.Maximum_Figures_in_Shadow_Overlap_Calculations
    obj_shadowcalc.Maximum_Figures_in_Shadow_Overlap_Calculations = maximum_figures_in_shadow_overlap_calculations
    print(f'Maximum Figures in Shadow Overlap Calculations was previously set to '
          f'{shadowcalc_maxfigs_prev} days, and it has been modified to {maximum_figures_in_shadow_overlap_calculations} days.')

    obj_timestep = [i for i in idf_object.idfobjects['Timestep']][0]
    timestep_prev = obj_timestep.Number_of_Timesteps_per_Hour
    obj_timestep.Number_of_Timesteps_per_Hour = timesteps
    print(f'Number of Timesteps per Hour was previously set to '
          f'{timestep_prev} days, and it has been modified to {timesteps} days.')


##


# todo problem spacelist with V940
x = addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    # EnergyPlus_version='auto',
    TempCtrl='temp',

    ComfStand=[2],
    # CustAST_ACSTall=10,
    # CustAST_ACSTaul=35,
    # CustAST_AHSTall=10,
    # CustAST_AHSTaul=35,
    # CustAST_ACSToffset=4,
    # CustAST_AHSToffset=-4,
    # CustAST_m=0.4,
    # CustAST_n=15,

    CAT=[80],
    # CATcoolOffset=2,
    # CATheatOffset=2,
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True,
    # VRFschedule='Heating_activation_time_chile',
    # eer=1,
    # cop=0.8,
    # NameSuffix='2_deg_higher'
    make_averages=True
)

# output_idf = x.output_idfs[[i for i in x.output_idfs.keys()][0]]
# output_idf.idfobjects['Output:variable']


##

from besos import eplus_funcs
from besos import eppy_funcs

# new_idf = r'D:\Python\accim_project\accim\smalloffice_osm_no_hvac[CS_INT ASHRAE55[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'
# new_idf = r'C:\Python\accim\smalloffice_osm_no_hvac[CS_INT ASHRAE55[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'
new_idf = [i for i in os.listdir() if i.endswith('.idf') if i != orig_idf
           # and '20zones' in i
           ][0]
# new_idf = 'OSM_SmallOffice_exHVAC_always-occ_V2320.idf'
# new_idf = 'smalloffice_osm_hvac_always_occ[CS_INT ASHRAE55[CA_80[CM_3[HM_0[VC_X[VO_X[MT_X[MW_X[AT_0.1[NS_X.idf'

building = eppy_funcs.get_building(new_idf)

eplus_funcs.run_energyplus(
    building_path=new_idf,
    epw=r'D:\Python\accim_project\accim\Mulchen-hour.epw',
    out_dir='temp_sim_outputs'
)
