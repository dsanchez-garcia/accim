import pandas as pd
import warnings
from besos import eppy_funcs as ef, sampling
from besos.evaluator import EvaluatorEP
from besos.optimizer import NSGAII, df_solution_to_solutions
from besos.parameters import RangeParameter, expand_plist, wwr, FieldSelector, Parameter, GenericSelector, \
    CategoryParameter
from besos.problem import EPProblem
from besos.eplus_funcs import get_idf_version, run_building
from matplotlib import pyplot as plt
from platypus import Archive, Hypervolume, Solution
from besos.eplus_funcs import print_available_outputs
from besos.objectives import VariableReader, MeterReader

from accim.utils import print_available_outputs_mod
import numpy as np

import accim.sim.accis_single_idf_funcs as accis
import accim.funcs_for_besos.param_accis as bf

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
    Output_gen_dataframe=True,
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

# available_outputs = print_available_outputs_mod(building)

comfstand_range = [1, 2, 3]
cat_range = [1, 2, 3]
comfmod_range = [3]

samples = pd.DataFrame(columns=['ComfStand', 'CAT', 'ComfMod'])

index_val = 0
for i in comfstand_range:
    # samples.loc[index_val, 'ComfStand'] = i
    for j in cat_range:
        # samples.loc[index_val, 'CAT'] = j
        for k in comfmod_range:
            samples.loc[index_val, 'ComfMod'] = k
            samples.loc[index_val, 'ComfStand'] = i
            samples.loc[index_val, 'CAT'] = j

            index_val = index_val + 1


# samples = samples.dropna()
#
# valid_params = {
#     0: [['n/a'], ['n/a']],
#     1: [[1, 2, 3], [0, 1, 2, 3]],
#     2: [[80, 90], [0, 1, 2, 3]],
#     3: [[80, 90], [0, 1, 2, 3]],
#     4: [[1, 2], [3]],
#     5: [[1, 2], [3]],
#     6: [[80, 90], [0, 1, 2, 3]],
#     7: [[80, 85, 90], [0, 1, 2, 3]],
#     8: [[80, 85, 90], [0, 1, 2, 3]],
#     9: [[80, 90], [0, 1, 2, 3]],
#     10: [[80, 90], [0, 1, 2, 3]],
#     11: [[80, 90], [0, 1, 2, 3]],
#     12: [[80, 90], [0, 1, 2, 3]],
#     13: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
#     14: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
#     15: [[80, 90], [0, 1, 2, 3]],
#     16: [[80, 90], [0, 1, 2, 3]],
#     17: [[80, 90], [0, 1, 2, 3]],
#     18: [[80, 90], [0, 1, 2, 3]],
#     19: [[80, 90], [0, 1, 2, 3]],
#     20: [[80, 90], [0, 1, 2, 3]],
#     21: [[80, 90], [2, 3]],
#     22: [[1, 2, 3], [0]],
# }
# samples['valid'] = 'temp'
# for i in samples.index:
#     if samples.loc[i, 'CAT'] not in valid_params[samples.loc[i, 'ComfStand']][0]:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'ComfMod'] not in valid_params[samples.loc[i, 'ComfStand']][1]:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'VentCtrl'] != 0 and samples.loc[i, 'HVACmode'] == 0:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'VSToffset'] != 0 and samples.loc[i, 'HVACmode'] == 0:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'MinOToffset'] != 0 and samples.loc[i, 'HVACmode'] == 0:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'MaxWindSpeed'] != 0 and samples.loc[i, 'HVACmode'] == 0:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'SetpointAcc'] < 0:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'MaxTempDiffVOF'] <= 0:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'MinTempDiffVOF'] <= 0:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'MinTempDiffVOF'] >= samples.loc[i, 'MaxTempDiffVOF'] <= 0:
#         samples.loc[i, 'valid'] = False
#     elif samples.loc[i, 'MultiplierVOF'] < 0 or samples.loc[i, 'MultiplierVOF'] > 1:
#         samples.loc[i, 'valid'] = False
#     else:
#         samples.loc[i, 'valid'] = True
#
# samples_cleaned = samples[samples['valid'] == True]

samples_filtered = bf.drop_invalid_param_combinations(samples)

##

# adaptive_coeff_range = [round(i, 2) for i in np.arange(-1.0, 0, 0.1)]
# adaptive_coeff_range.extend([round(i, 2) for i in np.arange(0, 1.1, 0.1)])
# len(adaptive_coeff_range)
#
# pmv_range = [round(i, 2) for i in np.arange(0.3, 0.90, 0.05)]
# len(pmv_range)
# pmv_full = [[i]*len(adaptive_coeff_range) for i in pmv_range]
# pmv_full = np.array(pmv_full).flatten().tolist()
#
# samples = pd.DataFrame(
#     {
#         "Adaptive coefficient": adaptive_coeff_range*len(pmv_range),
#         "PMV": pmv_full,
#     }
# )
#
# samples_short = samples[:5]

parameters = [
    Parameter(
        name='ComfStand',
        # selector=GenericSelector(set=change_adaptive_coeff),
        selector=GenericSelector(set=bf.modify_ComfStand),
        # value_descriptors=CategoryParameter(options=comfstand_range)
    ),
    Parameter(
        name='CAT',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=bf.modify_CAT),
        # value_descriptors=CategoryParameter(options=cat_range)
    ),
    Parameter(
        name='ComfMod',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=bf.modify_ComfMod),
        # value_descriptors=CategoryParameter(options=comfmod_range)
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

# inputs = sampling.dist_sampler(sampling.full_factorial, problem, num_samples=len(adaptive_coeff_range), level=len(pmv_range))
# inputs

# samples = pd.DataFrame(
#     {
#         "Thickness": [x / 10 for x in range(1, 10)] * 2,
#         "Watts": [8, 10, 12] * 6,
#         "wwr": [0.25, 0.5] * 9,
#     }
# )

# bundle all of the different selectors into a single list of parameters

# parameters = [
#     Parameter(selector=x) for x in (insulation_idf, lights_selector, window_to_wall)
# ]

evaluator = EvaluatorEP(
    problem=problem,
    building=building,
    out_dir='outdir'
)

outputs = evaluator.df_apply(
    samples_filtered,
    keep_input=True,
    keep_dirs=True,
    # out_dir='outdir',
    processes=5
)

# outputs_mod = outputs
# outputs_mod['energy ratio'] = outputs_mod['HVAC Electricity Usage'] / outputs_mod['Total Electricity Usage']


# todo use generate_building or _generate_building_from_row to save each idf from the parametric analysis sample

# generated_buildings = [evaluator.generate_building(df=samples_short, index=i, file_name=f'short_sample_row_{i}') for i in range(5)]
evaluator.generate_building(df=samples, index=0, file_name='num_0')
evaluator.generate_building(df=samples, index=1, file_name='num_1')
evaluator.generate_building(df=samples, index=2, file_name='num_2')
# evaluator.generate_building(df=samples_short, index=3, file_name='num_3')
# evaluator.generate_building(df=samples_short, index=4, file_name='num_4')
