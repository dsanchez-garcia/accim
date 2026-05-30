from besos import eppy_funcs as ef
from besos.evaluator import EvaluatorEP
from besos.optimizer import NSGAII
from besos.parameters import RangeParameter,  Parameter, GenericSelector
from besos.problem import EPProblem
from besos.objectives import VariableReader, MeterReader

import accim.sim.single as accis

##

building = ef.get_building('TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf')

accis.add_accis(
    idf=building,
    script_type='vrf_mm',
    supply_air_temp_method='temperature difference',
    output_keep_existing=False,
    output_type='standard',
    output_freqs=['hourly'],
    energyplus_version='9.4',
    temp_control='temperature',
    output_gen_dataframe=True,
)

##

def modify_accis(building, value):
    accis.modify_accis(
        idf=building,
        comfort_standard=1,
        category=3,
        comfort_mode=3,
        # SetpointAcc=1000,
        hvac_mode=2,
        vent_control=0,
        cooling_season_start='01/02',
        cooling_season_end='01/03',
        vent_setpoint_offset=value,
        # MinOToffset=50,
        # MaxWindSpeed=50
    )
    return

##
parameters_set = [
    Parameter(
        name='VSToffset',
        selector=GenericSelector(set=modify_accis),
        value_descriptor=RangeParameter(min_val=0.1, max_val=0.9)
    ),
]

##

objectives = [
    MeterReader("Electricity:Facility", name="Electricity Usage"),
]

evaluator = EvaluatorEP(
    problem=EPProblem(
        inputs=parameters_set,
        outputs=objectives,
        minimize_outputs=[
            True
        ],
    ),
    building=building,
)


results1 = NSGAII(evaluator, evaluations=1, population_size=3)
