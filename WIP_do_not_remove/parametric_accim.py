import pandas as pd
import warnings
from besos import eppy_funcs as ef, sampling
from besos.evaluator import EvaluatorEP
from besos.optimizer import NSGAII, df_solution_to_solutions
from besos.parameters import RangeParameter, expand_plist, wwr, FieldSelector, Parameter, GenericSelector, CategoryParameter
from besos.problem import EPProblem
from besos.eplus_funcs import get_idf_version, run_building
from matplotlib import pyplot as plt
from platypus import Archive, Hypervolume, Solution
from besos.eplus_funcs import print_available_outputs
from besos.objectives import VariableReader, MeterReader

from besos_print_available_outputs import print_available_outputs_mod
import numpy as np

import accim.sim.aPMV_setpoints as apmv


##
building = ef.get_building(
    'aPMV_testing_v01_no_script.idf'
)

##
[i for i in building.idfobjects['EnergyManagementSystem:Program']]

apmv.add_apmv_ems_code(
    building=building,
    setpoint_tolerance=0.15
)

apmv.set_zones_always_occupied(building)



##

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


available_outputs = print_available_outputs_mod(building)
##

# [i for i in building.idfobjects['output:variable'] if 'Facility' in i.Variable_Name]
#
#
# totalhvacoutput = []
# for i in range(len(available_outputs.variablereaderlist)):
#     if 'Facility' in available_outputs.variablereaderlist[i][1]:
#         totalhvacoutput.append(available_outputs.variablereaderlist[i])
# totalhvacoutput = totalhvacoutput[0]

##


# def change_adaptive_coeff(building, value):
#     # program = [p for p in building.idfobjects['EnergyManagementSystem:Program'] if 'apply_aPMV' in p.Name][0]
#     # program.Program_Line_1 = f'set adap_coeff = {value}'
#     apmv.change_adaptive_coeff(building=building, value=value)
#     return
#
# def change_PMV_setpoints(building, value):
#     # program = [p for p in building.idfobjects['EnergyManagementSystem:Program'] if 'apply_aPMV' in p.Name][0]
#     # program.Program_Line_2 = f'set PMV_H_SP = {-value}'
#     # program.Program_Line_3 = f'set PMV_C_SP = {value}'
#     apmv.change_PMV_setpoints(building=building, value=value)
#     return


##

adaptive_coeff_range = [round(i, 2) for i in np.arange(-1.0, 0, 0.1)]
adaptive_coeff_range.extend([round(i, 2) for i in np.arange(0, 1.1, 0.1)])
len(adaptive_coeff_range)

pmv_range = [round(i, 2) for i in np.arange(0.3, 0.90, 0.05)]
len(pmv_range)
pmv_full = [[i]*len(adaptive_coeff_range) for i in pmv_range]
pmv_full = np.array(pmv_full).flatten().tolist()

samples = pd.DataFrame(
    {
        "Adaptive coefficient": adaptive_coeff_range*len(pmv_range),
        "PMV": pmv_full,
    }
)

samples_short = samples[:5]

parameters = [
    Parameter(
        # name='Adaptive coefficient',
        # selector=GenericSelector(set=change_adaptive_coeff),
        selector=GenericSelector(set=apmv.change_adaptive_coeff),
        # value_descriptor=CategoryParameter(options=adaptive_coeff_range)
    ),
    Parameter(
        # name='PMV',
        # selector=GenericSelector(set=change_PMV_setpoints),
        selector=GenericSelector(set=apmv.change_PMV_setpoints),
        # value_descriptor=CategoryParameter(options=pmv_range)
    ),
]

## Objectives

objs_comfhours = []
for i in range(len(available_outputs.variablereaderlist)):
    if 'hour' in available_outputs.variablereaderlist[i][1].lower():
        objs_comfhours.append(
            VariableReader(
                key_value=available_outputs.variablereaderlist[i][0],
                variable_name=available_outputs.variablereaderlist[i][1],
                frequency=available_outputs.variablereaderlist[i][2],
                name=available_outputs.variablereaderlist[i][1]
            )
        )

##

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
    outputs=objectives+objs_comfhours
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
    samples_short,
    keep_input=True,
    keep_dirs=True,
    # out_dir='outdir',
    processes=5
)

# outputs_mod = outputs
# outputs_mod['energy ratio'] = outputs_mod['HVAC Electricity Usage'] / outputs_mod['Total Electricity Usage']


# todo use generate_building or _generate_building_from_row to save each idf from the parametric analysis sample

# generated_buildings = [evaluator.generate_building(df=samples_short, index=i, file_name=f'short_sample_row_{i}') for i in range(5)]
evaluator.generate_building(df=samples_short, index=0, file_name='num_0')
evaluator.generate_building(df=samples_short, index=1, file_name='num_1')
evaluator.generate_building(df=samples_short, index=2, file_name='num_2')
evaluator.generate_building(df=samples_short, index=3, file_name='num_3')
evaluator.generate_building(df=samples_short, index=4, file_name='num_4')