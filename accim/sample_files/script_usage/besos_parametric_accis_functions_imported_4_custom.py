from besos import eppy_funcs as ef, sampling
from besos.evaluator import EvaluatorEP
from besos.parameters import RangeParameter, Parameter, GenericSelector
from besos.problem import EPProblem
from besos.objectives import MeterReader

import accim.sim.accis_single_idf_funcs as accis
import accim.parametric.funcs_for_besos.param_accis as bf

building = ef.get_building('TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2310.idf')

accis.addAccis(
    idf=building,
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    # EnergyPlus_version='9.4',
    TempCtrl='temperature',
    # Output_gen_dataframe=True,
)

# gv = [i for i in building.idfobjects['EnergyManagementSystem:GlobalVariable']]

building.newidfobject(
    key='OUTPUT:METER',
    Key_Name='Electricity:Facility',
    Reporting_Frequency='RunPeriod'
)

building.newidfobject(
    key='OUTPUT:METER',
    Key_Name='Electricity:HVAC',
    Reporting_Frequency='RunPeriod'
)
##

[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setinputdata']
bf.modify_ComfStand(building, 99)
bf.modify_CAT(building, 80)
bf.modify_ComfMod(building, 3)
bf.modify_MinOToffset(building, 50)


##
# available_outputs = print_available_outputs_mod(building)

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

parameters = [
    Parameter(
        name='CustAST_m',
        # selector=GenericSelector(set=change_adaptive_coeff),
        selector=GenericSelector(set=bf.modify_CustAST_m),
        value_descriptors=RangeParameter(name='CustAST_m', min_val=0, max_val=0.7)
    ),
    Parameter(
        name='CustAST_n',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=bf.modify_CustAST_n),
        value_descriptors=RangeParameter(name='CustAST_n', min_val=10, max_val=25)
    ),
    Parameter(
        name='CustAST_ACSToffset',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=bf.modify_CustAST_ACSToffset),
        value_descriptors=RangeParameter(name='CustAST_ACSToffset', min_val=1, max_val=5)
    ),
    Parameter(
        name='CustAST_AHSToffset',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=bf.modify_CustAST_AHSToffset),
        value_descriptors=RangeParameter(name='CustAST_AHSToffset', min_val=-5, max_val=-1)
    ),

]

# Objectives

# objs_comfhours = []
# for i in range(len(available_outputs.variablereaderlist)):
#     if 'hour' in available_outputs.variablereaderlist[i][1].lower():
#         objs_comfhours.append(
#             VariableReader(
#                 key_value=available_outputs.variablereaderlist[i][0],
#                 variable_name=available_outputs.variablereaderlist[i][1],
#                 frequency=available_outputs.variablereaderlist[i][2],
#                 name=available_outputs.variablereaderlist[i][1]
#             )
#         )

#

objectives = [
    MeterReader("Electricity:Facility", name="Total Electricity Usage"),
    MeterReader("Electricity:HVAC", name="HVAC Electricity Usage"),

    # VariableReader(
    #     key_value='Whole Building',
    #     variable_name='Facility Total HVAC Electricity Demand Rate',
    #     frequency='Hourly',
    #     name='HVAC Electricity usage'
    # )
]

problem = EPProblem(
    inputs=parameters,
    # outputs=objectives+objs_comfhours
    outputs=objectives
)

##


inputs_lhs = sampling.dist_sampler(sampling.lhs, problem, num_samples=5)
inputs_lhs

##


evaluator = EvaluatorEP(
    problem=problem,
    building=building,
    out_dir='outdir'
)

outputs = evaluator.df_apply(
    inputs_lhs,
    keep_input=True,
    keep_dirs=True,
    # out_dir='outdir',
    processes=5
)

# outputs_mod = outputs
# outputs_mod['energy ratio'] = outputs_mod['HVAC Electricity Usage'] / outputs_mod['Total Electricity Usage']

# generated_buildings = [evaluator.generate_building(df=samples_short, index=i, file_name=f'short_sample_row_{i}') for i in range(5)]
evaluator.generate_building(df=inputs_lhs, index=0, file_name='num_0')
evaluator.generate_building(df=inputs_lhs, index=1, file_name='num_1')
evaluator.generate_building(df=inputs_lhs, index=2, file_name='num_2')
# evaluator.generate_building(df=samples_short, index=3, file_name='num_3')
# evaluator.generate_building(df=samples_short, index=4, file_name='num_4')
