# import pandas as pd
# import warnings
from besos import eppy_funcs as ef, sampling

# from besos.evaluator import EvaluatorEP
# from besos.optimizer import NSGAII, df_solution_to_solutions
# from besos.parameters import RangeParameter, expand_plist, wwr, FieldSelector, Parameter, GenericSelector, CategoryParameter
# from besos.problem import EPProblem
# from besos.eplus_funcs import get_idf_version, run_building
# from matplotlib import pyplot as plt
# from platypus import Archive, Hypervolume, Solution
# from besos.eplus_funcs import print_available_outputs
# from besos.objectives import VariableReader, MeterReader
#
# from besos_print_available_outputs import print_available_outputs_mod
# import numpy as np

import warnings

filename = 'aPMV_testing_v01_no_script'

building = ef.get_building(
    # 'aPMV_testing_unoccupied.idf',
    # 'aPMV_testing_unoccupied_no_script.idf',
    f'{filename}.idf',
)




adap_coeff_cooling = {}
adap_coeff_heating = {}
pmv_cooling_sp = {}
pmv_heating_sp = {}

tolerance = 0.1

for i in building.idfobjects['zone']:
    if 'zone1' in i.Name.lower():
        adap_coeff_cooling.update({i.Name: 0.4})
        adap_coeff_heating.update({i.Name: -0.4})
        pmv_cooling_sp.update({i.Name: 0.3})
        pmv_heating_sp.update({i.Name: -0.3})
    if 'zone2' in i.Name.lower():
        adap_coeff_cooling.update({i.Name: 0.3})
        adap_coeff_heating.update({i.Name: -0.3})
        pmv_cooling_sp.update({i.Name: 0.2})
        pmv_heating_sp.update({i.Name: -0.2})

# breaking the script
adap_coeff_heating = {
    'Block1:Zone2': 0.55,
    # 'Block1:Zone1': 0.45,
    'Block1:Zone3': 0.35,
}

# or arguments can also be int or float

# adap_coeff_cooling = 0.1
adap_coeff_heating = -0.2
# pmv_cooling_sp = 0.3
# pmv_heating_sp = 0.4
##

from accim.sim.aPMV_setpoints import generate_df_from_args
df = generate_df_from_args(
    building=building,
    adap_coeff_heating=adap_coeff_heating,
    adap_coeff_cooling=adap_coeff_cooling,
    pmv_heating_sp=pmv_heating_sp,
    pmv_cooling_sp=pmv_cooling_sp
)