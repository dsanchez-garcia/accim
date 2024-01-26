from besos import eppy_funcs as ef
from besos.evaluator import EvaluatorEP
from besos.optimizer import NSGAII
from besos.parameters import RangeParameter,  Parameter, GenericSelector
from besos.problem import EPProblem
from besos.objectives import VariableReader, MeterReader

import accim.sim.accis_single_idf_funcs as accis

##

building = ef.get_building('TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf')

accis.addAccis(
    idf=building,
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    EnergyPlus_version='9.4',
    TempCtrl='temperature',
    Output_gen_dataframe=True,
)

##

def modify_accis(building, value):
    accis.modifyAccis(
        idf=building,
        ComfStand=1,
        CAT=3,
        ComfMod=3,
        # SetpointAcc=1000,
        HVACmode=2,
        VentCtrl=0,
        CoolSeasonStart='01/02',
        CoolSeasonEnd='01/03',
        VSToffset=value,
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
