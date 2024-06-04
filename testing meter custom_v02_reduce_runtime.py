from besos import eppy_funcs as ef, sampling
from besos.evaluator import EvaluatorEP
from besos.parameters import Parameter, GenericSelector, \
    CategoryParameter
from besos.problem import EPProblem
from besos.objectives import VariableReader, MeterReader

from accim.utils import print_available_outputs_mod, modify_timesteps, set_occupancy_to_always

import accim.sim.accis_single_idf_funcs as accis
import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf

building = ef.get_building('TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf')

accis.addAccis(
    idf=building,
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['timestep', 'hourly', 'runperiod'],
    # EnergyPlus_version='9.4',
    TempCtrl='temperature',
    # Output_gen_dataframe=True,
    # make_averages=True,
    # debugging=True
)

##

def reduce_runtime(
        idf_object,
        minimal_shadowing: bool = True,
        shading_calculation_update_frequency: int = 20,
        maximum_figures_in_shadow_overlap_calculations: int = 200,
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

# reduce_runtime(
#     idf_object=building,
#     minimal_shadowing=True,
#     shading_calculation_update_frequency=365,
#     maximum_figures_in_shadow_overlap_calculations=200
# )

# def modify_timesteps(idf_object, timesteps: int):
#     obj_timestep = [i for i in idf_object.idfobjects['Timestep']][0]
#     timestep_prev = obj_timestep.Number_of_Timesteps_per_Hour
#     obj_timestep.Number_of_Timesteps_per_Hour = timesteps
#     print(f'Number of Timesteps per Hour was previously set to '
#           f'{timestep_prev} days, and it has been modified to {timesteps} days.')

modify_timesteps(idf_object=building, timesteps=6)



set_occupancy_to_always(idf_object=building)

##


# gv = [i for i in building.idfobjects['EnergyManagementSystem:GlobalVariable']]


building.newidfobject(
    key='Meter:Custom',
    Name='Total Occupied Discomfortable hours',
    Resource_Type='Generic',
    Key_Name_1='EMS',
    Output_Variable_or_Meter_Name_1='Occupied Discomfortable Hours_No Applicability_BLOCK1_ZONE1',
    Key_Name_2='EMS',
    Output_Variable_or_Meter_Name_2='Occupied Discomfortable Hours_No Applicability_BLOCK1_ZONE2'
)

meters = [
    'HeatingCoils:EnergyTransfer',
    'CoolingCoils:EnergyTransfer',
    'Heating:Electricity',
    'Cooling:Electricity',
    'Electricity:HVAC',
    'TOTAL OCCUPIED DISCOMFORTABLE HOURS'
]
for meter in meters:
    building.newidfobject(
        key='OUTPUT:METER',
        Key_Name=meter,
        Reporting_Frequency='RunPeriod'
    )



##

[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setinputdata']
bf.modify_ComfStand(building, 99)
bf.modify_CAT(building, 80)
bf.modify_ComfMod(building, 3)
bf.modify_MinOToffset(building, 50)
bf.modify_MaxWindSpeed(building, 50)
bf.modify_VentCtrl(building, 2)

[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setvofinputdata']
bf.modify_MultiplierVOF(building, 0.1)
bf.modify_MaxTempDiffVOF(building, 6)


[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'applycat']

##
available_outputs = print_available_outputs_mod(building)

# comfstand_range = [1, 2, 3]
# cat_range = [1, 2, 3]
# comfmod_range = [3]
#
# samples = pd.DataFrame(columns=['ComfStand', 'CAT', 'ComfMod', 'CATcoolOffset', 'CATheatOffset'])
#
# index_val = 0
# for i in comfstand_range:
#     # samples.loc[index_val, 'ComfStand'] = i
#     for j in cat_range:
#         # samples.loc[index_val, 'CAT'] = j
#         for k in comfmod_range:
#             samples.loc[index_val, 'ComfMod'] = k
#             samples.loc[index_val, 'ComfStand'] = i
#             samples.loc[index_val, 'CAT'] = j
#             samples.loc[index_val, 'CATcoolOffset'] = 2
#             samples.loc[index_val, 'CATheatOffset'] = 2
#
#             index_val = index_val + 1
#
# samples_filtered = bf.drop_invalid_param_combinations(samples)

##
import numpy as np
[round(i, 2) for i in np.arange(0, 0.75, 0.05)]

parameters = [
    Parameter(
        name='CustAST_m',
        # selector=GenericSelector(set=change_adaptive_coeff),
        selector=GenericSelector(set=bf.modify_CustAST_m),
        # value_descriptors=RangeParameter(name='CustAST_m', min_val=0, max_val=0.7),
        value_descriptors=CategoryParameter(name='CustAST_m', options=[round(i, 2) for i in np.arange(0, 0.75, 0.05)]),
    ),
    Parameter(
        name='CustAST_n',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=bf.modify_CustAST_n),
        # value_descriptors=RangeParameter(name='CustAST_n', min_val=10, max_val=25),
        value_descriptors=CategoryParameter(name='CustAST_n', options=[round(i, 2) for i in np.arange(5, 24.5, 0.5)]),
    ),
    Parameter(
        name='CustAST_ASToffset',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=bf.modify_CustAST_ASToffset),
        # value_descriptors=RangeParameter(name='CustAST_AHSToffset', min_val=-5, max_val=-1),
        value_descriptors=CategoryParameter(name='CustAST_ASToffset', options=[round(i, 2) for i in np.arange(1, 5.5, 0.5)]),
    ),
    Parameter(
        name='CustAST_ASTall',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=bf.modify_CustAST_ASTall),
        # value_descriptors=RangeParameter(name='CustAST_AHSToffset', min_val=-5, max_val=-1),
        value_descriptors=CategoryParameter(name='CustAST_ASTall', options=[round(i, 2) for i in np.arange(5, 17, 1)]),
    ),
    Parameter(
        name='CustAST_ASTaul',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=bf.modify_CustAST_ASTaul),
        # value_descriptors=RangeParameter(name='CustAST_AHSToffset', min_val=-5, max_val=-1),
        value_descriptors=CategoryParameter(name='CustAST_ASTaul', options=[round(i, 2) for i in np.arange(20, 39, 1)]),
    ),
]

##

def avg(result):
    return result.data["Value"].sum()/2

def mean(result):
    return result.data["Value"].mean()

# Objectives

objs_comfhours = []
for i in range(len(available_outputs.variablereaderlist)):
    if (
            'Occupied Discomfortable Hours_No Applicability_Building_Average' == available_outputs.variablereaderlist[i][1]
    ):
        objs_comfhours.append(
            VariableReader(
                key_value=available_outputs.variablereaderlist[i][0],
                variable_name=available_outputs.variablereaderlist[i][1],
                frequency=available_outputs.variablereaderlist[i][2],
                name=available_outputs.variablereaderlist[i][1]
            )
        )
    elif (
            'Adaptive Cooling Setpoint Temperature' == available_outputs.variablereaderlist[i][1] or
            'Adaptive Heating Setpoint Temperature' == available_outputs.variablereaderlist[i][1]
    ):
        objs_comfhours.append(
            VariableReader(
                key_value=available_outputs.variablereaderlist[i][0],
                variable_name=available_outputs.variablereaderlist[i][1],
                frequency=available_outputs.variablereaderlist[i][2],
                name=available_outputs.variablereaderlist[i][1],
                func=mean
            )
        )



objs_meters = [MeterReader(key_name=i, name=i) for i in meters]

obj_avg = [MeterReader(key_name='TOTAL OCCUPIED DISCOMFORTABLE HOURS', func=avg, name='AVERAGE OCCUPIED DISCOMFORTABLE HOURS')]


problem = EPProblem(
    inputs=parameters,
    # outputs=objectives+objs_comfhours
    outputs=objs_meters+obj_avg+objs_comfhours
)

##


inputs_lhs = sampling.dist_sampler(sampling.lhs, problem, num_samples=5)
inputs_lhs

num_samples = 1
# for p in parameters:
#     num_samples = num_samples*len(p.value_descriptor.options)
for p in parameters:
    num_samples = num_samples*len(p.value_descriptors[0].options)


# inputs_full_factorial = sampling.dist_sampler(sampling.full_factorial, problem)

##


evaluator = EvaluatorEP(
    problem=problem,
    building=building,
    epw='Sydney.epw',
    out_dir='besos_outdir_6timesteps_sydney_vof-0.1-max-6'
)

outputs = evaluator.df_apply(
    inputs_lhs,
    keep_input=True,
    keep_dirs=True,
    # out_dir='outdir',
    processes=5
)

outputs.to_excel('outputs_with_avg_to_be_refined.xlsx')
# outputs_mod = outputs
# outputs_mod['energy ratio'] = outputs_mod['HVAC Electricity Usage'] / outputs_mod['Total Electricity Usage']

# generated_buildings = [evaluator.generate_building(df=samples_short, index=i, file_name=f'short_sample_row_{i}') for i in range(5)]
# evaluator.generate_building(df=inputs_lhs, index=0, file_name='num_0')
# evaluator.generate_building(df=inputs_lhs, index=1, file_name='num_1')
# evaluator.generate_building(df=inputs_lhs, index=2, file_name='num_2')
# evaluator.generate_building(df=inputs_lhs, index=3, file_name='num_3')
# evaluator.generate_building(df=inputs_lhs, index=4, file_name='num_4')

##
