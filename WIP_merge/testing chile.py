from besos.eppy_funcs import get_building

building = get_building('model_chile.idf')

x = [i for i in building.idfobjects['Schedule:Day:List'] if i.Name == str(10019)][0]
##
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

building.newidfobject(
    key='Schedule:Day:List',
    Name=10020,
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
    Value_24=1,
)

x = [i for i in building.idfobjects['Schedule:Week:Daily'] if i.Name == 'HORARIO ACT CALF MULCHEN 2O22_Jan'][0]



##
sch_daily_list = [i for i in building.idfobjects['Schedule:Week:Daily'] if 'HORARIO ACT CALF MULCHEN 2O22' in i.Name]

[building.removeidfobject(i) for i in building.idfobjects['Schedule:Week:Daily'] if 'HORARIO ACT CALF MULCHEN 2O22' in i.Name]

temp_dict = {
    'key': [],
    'Name': [],
    'Sunday_ScheduleDay_Name': [],
    'Monday_ScheduleDay_Name': [],
    'Tuesday_ScheduleDay_Name': [],
    'Wednesday_ScheduleDay_Name': [],
    'Thursday_ScheduleDay_Name': [],
    'Friday_ScheduleDay_Name': [],
    'Saturday_ScheduleDay_Name': [],
    'Holiday_ScheduleDay_Name': [],
    'SummerDesignDay_ScheduleDay_Name': [],
    'WinterDesignDay_ScheduleDay_Name': [],
    'CustomDay1_ScheduleDay_Name': [],
    'CustomDay2_ScheduleDay_Name': [],
}

for i in sch_daily_list:
    temp_dict['key'].append(i.key)
    temp_dict['Name'].append(i.Name)
    temp_dict['Sunday_ScheduleDay_Name'].append(i.Sunday_ScheduleDay_Name)
    temp_dict['Monday_ScheduleDay_Name'].append(i.Monday_ScheduleDay_Name)
    temp_dict['Tuesday_ScheduleDay_Name'].append(i.Tuesday_ScheduleDay_Name)
    temp_dict['Wednesday_ScheduleDay_Name'].append(i.Wednesday_ScheduleDay_Name)
    temp_dict['Thursday_ScheduleDay_Name'].append(i.Thursday_ScheduleDay_Name)
    temp_dict['Friday_ScheduleDay_Name'].append(i.Friday_ScheduleDay_Name)
    temp_dict['Saturday_ScheduleDay_Name'].append(i.Saturday_ScheduleDay_Name)
    temp_dict['Holiday_ScheduleDay_Name'].append(i.Holiday_ScheduleDay_Name)
    temp_dict['SummerDesignDay_ScheduleDay_Name'].append(i.SummerDesignDay_ScheduleDay_Name)
    temp_dict['WinterDesignDay_ScheduleDay_Name'].append(i.WinterDesignDay_ScheduleDay_Name)
    temp_dict['CustomDay1_ScheduleDay_Name'].append(i.CustomDay1_ScheduleDay_Name)
    temp_dict['CustomDay2_ScheduleDay_Name'].append(i.CustomDay2_ScheduleDay_Name)



print(temp_dict)
##

sch_wee_daily_dict = {
    'key': ['Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily', 'Schedule:Week:Daily'],
    'Name': ['HORARIO ACT CALF MULCHEN 2O22_Jan', 'HORARIO ACT CALF MULCHEN 2O22_Feb', 'HORARIO ACT CALF MULCHEN 2O22_Mar', 'HORARIO ACT CALF MULCHEN 2O22_Apr', 'HORARIO ACT CALF MULCHEN 2O22_May', 'HORARIO ACT CALF MULCHEN 2O22_Jun', 'HORARIO ACT CALF MULCHEN 2O22_Jul', 'HORARIO ACT CALF MULCHEN 2O22_Aug', 'HORARIO ACT CALF MULCHEN 2O22_Sep', 'HORARIO ACT CALF MULCHEN 2O22_Oct', 'HORARIO ACT CALF MULCHEN 2O22_Nov', 'HORARIO ACT CALF MULCHEN 2O22_Dec'],
    'Sunday_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'Monday_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'Tuesday_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'Wednesday_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'Thursday_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'Friday_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'Saturday_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'Holiday_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'SummerDesignDay_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'WinterDesignDay_ScheduleDay_Name': ['11', '11', '11', '11', '11', '11', '11', '11', '11', '11', '11', '11'],
    'CustomDay1_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
    'CustomDay2_ScheduleDay_Name': ['11', '11', '10019', '10019', '10020', '10020', '10020', '10020', '10019', '10020', '11', '11'],
}

for i in range(len(sch_wee_daily_dict['key'])):
    building.newidfobject(
        key=sch_wee_daily_dict['key'][i],
        Name=sch_wee_daily_dict['Name'][i],
        Sunday_ScheduleDay_Name=sch_wee_daily_dict['Sunday_ScheduleDay_Name'][i],
        Monday_ScheduleDay_Name=sch_wee_daily_dict['Monday_ScheduleDay_Name'][i],
        Tuesday_ScheduleDay_Name=sch_wee_daily_dict['Tuesday_ScheduleDay_Name'][i],
        Wednesday_ScheduleDay_Name=sch_wee_daily_dict['Wednesday_ScheduleDay_Name'][i],
        Thursday_ScheduleDay_Name=sch_wee_daily_dict['Thursday_ScheduleDay_Name'][i],
        Friday_ScheduleDay_Name=sch_wee_daily_dict['Friday_ScheduleDay_Name'][i],
        Saturday_ScheduleDay_Name=sch_wee_daily_dict['Saturday_ScheduleDay_Name'][i],
        Holiday_ScheduleDay_Name=sch_wee_daily_dict['Holiday_ScheduleDay_Name'][i],
        SummerDesignDay_ScheduleDay_Name=sch_wee_daily_dict['SummerDesignDay_ScheduleDay_Name'][i],
        WinterDesignDay_ScheduleDay_Name=sch_wee_daily_dict['WinterDesignDay_ScheduleDay_Name'][i],
        CustomDay1_ScheduleDay_Name=sch_wee_daily_dict['CustomDay1_ScheduleDay_Name'][i],
        CustomDay2_ScheduleDay_Name=sch_wee_daily_dict['CustomDay2_ScheduleDay_Name'][i],
    )

##

x = [i for i in building.idfobjects['Schedule:Year'] if i.Name == 'HORARIO ACT CALF MULCHEN 2O22'][0]
# building.removeidfobject(x)

building.newidfobject(
    key='Schedule:Year',
    Name='HORARIO ACT CALF MULCHEN 2O22',
    Schedule_Type_Limits_Name='Any number',
    ScheduleWeek_Name_1='HORARIO ACT CALF MULCHEN 2O22_Jan',
    Start_Month_1='1',
    Start_Day_1='1',
    End_Month_1='1',
    End_Day_1='31',
    ScheduleWeek_Name_2='HORARIO ACT CALF MULCHEN 2O22_Feb',
    Start_Month_2='2',
    Start_Day_2='1',
    End_Month_2='2',
    End_Day_2='28',
    ScheduleWeek_Name_3='HORARIO ACT CALF MULCHEN 2O22_Mar',
    Start_Month_3='3',
    Start_Day_3='1',
    End_Month_3='3',
    End_Day_3='31',
    ScheduleWeek_Name_4='HORARIO ACT CALF MULCHEN 2O22_Apr',
    Start_Month_4='4',
    Start_Day_4='1',
    End_Month_4='4',
    End_Day_4='30',
    ScheduleWeek_Name_5='HORARIO ACT CALF MULCHEN 2O22_May',
    Start_Month_5='5',
    Start_Day_5='1',
    End_Month_5='5',
    End_Day_5='31',
    ScheduleWeek_Name_6='HORARIO ACT CALF MULCHEN 2O22_Jun',
    Start_Month_6='6',
    Start_Day_6='1',
    End_Month_6='6',
    End_Day_6='30',
    ScheduleWeek_Name_7='HORARIO ACT CALF MULCHEN 2O22_Jul',
    Start_Month_7='7',
    Start_Day_7='1',
    End_Month_7='7',
    End_Day_7='31',
    ScheduleWeek_Name_8='HORARIO ACT CALF MULCHEN 2O22_Aug',
    Start_Month_8='8',
    Start_Day_8='1',
    End_Month_8='8',
    End_Day_8='31',
    ScheduleWeek_Name_9='HORARIO ACT CALF MULCHEN 2O22_Sep',
    Start_Month_9='9',
    Start_Day_9='1',
    End_Month_9='9',
    End_Day_9='30',
    ScheduleWeek_Name_10='HORARIO ACT CALF MULCHEN 2O22_Oct',
    Start_Month_10='10',
    Start_Day_10='1',
    End_Month_10='10',
    End_Day_10='31',
    ScheduleWeek_Name_11='HORARIO ACT CALF MULCHEN 2O22_Nov',
    Start_Month_11='11',
    Start_Day_11='1',
    End_Month_11='11',
    End_Day_11='30',
    ScheduleWeek_Name_12='HORARIO ACT CALF MULCHEN 2O22_Dec',
    Start_Month_12='12',
    Start_Day_12='1',
    End_Month_12='12',
    End_Day_12='31',
)


