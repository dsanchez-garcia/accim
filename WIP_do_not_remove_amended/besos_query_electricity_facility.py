
from besos import eppy_funcs as ef
from besos.evaluator import EvaluatorEP
from besos.optimizer import NSGAII
from besos.parameters import RangeParameter,  Parameter, GenericSelector
from besos.problem import EPProblem
from besos.objectives import VariableReader, MeterReader


##

building = ef.get_building('testmodel_daylighting_v02.idf')


zones_from_idf = [z.Name for z in building.idfobjects['zone']]

##

# Parameters that set the WWR. North comes first and removes all windows from the building.

def north_wwr(building, value):
    building.remove_windows()
    building.set_wwr(
        wwr=value,
        construction="Window construction - 1001",
        force=True,
        orientation='north'
    )
    return

def east_wwr(building, value):
    building.set_wwr(
        wwr=value,
        construction="Window construction - 1001",
        force=True,
        orientation='east'
    )
    return

def south_wwr(building, value):
    building.set_wwr(
        wwr=value,
        construction="Window construction - 1001",
        force=True,
        orientation='south'
    )
    return

def west_wwr(building, value):
    building.set_wwr(
        wwr=value,
        construction="Window construction - 1001",
        force=True,
        orientation='west'
    )
    return



##

parameters_set = [
    Parameter(
        name='North WWR',
        selector=GenericSelector(set=north_wwr),
        value_descriptor=RangeParameter(min_val=0.1, max_val=0.9)
    ),
    Parameter(
        name='East WWR',
        selector=GenericSelector(set=east_wwr),
        value_descriptor=RangeParameter(min_val=0.1, max_val=0.9)
    ),
    Parameter(
        name='South WWR',
        selector=GenericSelector(set=south_wwr),
        value_descriptor=RangeParameter(min_val=0.1, max_val=0.9)
    ),
    Parameter(
        name='West WWR',
        selector=GenericSelector(set=west_wwr),
        value_descriptor=RangeParameter(min_val=0.1, max_val=0.9)
    ),
]

building.newidfobject(
    key='output:meter',
    Key_Name='Electricity:Facility',
    Reporting_Frequency='Runperiod'
)

objectives_daylight = []
for z in zones_from_idf:
    obj = VariableReader(
        key_value=z,
        variable_name='Daylighting Reference Point 1 Illuminance',
        frequency='RunPeriod'
    )
    objectives_daylight.append(obj)


building.newidfobject(
    key='output:variable',
    Key_Value='Whole Building',
    Variable_Name='Facility Total HVAC Electricity Demand Rate',
    Reporting_Frequency='RunPeriod'
)


objectives = [
    MeterReader("Electricity:Facility", name="Electricity Usage"),
    # VariableReader(
    #     key_value='Whole Building',
    #     variable_name='Facility Total HVAC Electricity Demand Rate',
    #     frequency='RunPeriod',
    #     name='HVAC Electricity usage'
    # )
]

total_objs = objectives_daylight + objectives


evaluator = EvaluatorEP(
    problem=EPProblem(
        inputs=parameters_set,
        outputs=total_objs,
        minimize_outputs=[
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            # True,
            True
        ],
    ),
    building=building,
)


results1 = NSGAII(evaluator, evaluations=1, population_size=3)


