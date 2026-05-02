from besos import eppy_funcs as ef

building = ef.get_building('SF_Detached_A_max_South.idf')

for obj in building.idfobjects['output:variable']:
    obj.Reporting_Frequency = 'Hourly'

building.newidfobject(
    key='outputcontrol:files',
    Output_CSV='Yes',
    Output_MTR='Yes',
    Output_ESO='Yes'
)
for output in ['DistrictHeating:Facility', 'DistrictCooling:Facility']:
    building.newidfobject(
        key='OUTPUT:METER',
        Key_Name=output,
        Reporting_Frequency='Hourly'
    )

building.idfobjects['output:meter']