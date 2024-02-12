from besos.eppy_funcs import get_building

building = get_building('model_chile.idf')

x = [i for i in building.idfobjects['Schedule:Day:List'] if i.Name == str(10019)][0]

building.newidfobject(
    key='Schedule:Day:Interval',
    Name=11,
    Schedule_Type_Limits_Name='Any number',
    Interpolate_to_Timestep='No',
    Time_1='24:00',
    Value_Until_Time_1=0
)

building.newidfobject(
    key='Schedule:Day:List',
    Name=10019,
    Schedule_Type_Limits_Name='Any number',
    Interpolate_to_Timestep='No',
    Minutes_per_Item=60,
    Value_1=0,
    Value_2=0,
    Value_3=0,
    Value_4=0,
    Value_5=0,
    Value_6=0,
    Value_7=1,
    Value_8=1,
    Value_9=1,
    Value_10=0,
    Value_11=0,
    Value_12=0,
    Value_13=0,
    Value_14=0,
    Value_15=0,
    Value_16=0,
    Value_17=0,
    Value_18=1,
    Value_19=1,
    Value_20=1,
    Value_21=1,
    Value_22=1,
    Value_23=1,
    Value_24=0,
)

