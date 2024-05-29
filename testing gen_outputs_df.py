from besos import eppy_funcs as ef

from accim.utils import print_available_outputs_mod

import accim.sim.accis_single_idf_funcs as accis
import accim.parametric.funcs_for_besos.param_accis as bf

building = ef.get_building('ALJARAFE CENTER_onlyGeometry.idf')

outputs_df = accis.gen_outputs_df(
    idf=building,
    ScriptType='vrf_mm',
    Output_type='standard',
    Output_freqs=['hourly', 'runperiod'],
    Output_keep_existing=False,
    TempCtrl='temperature',
    make_averages=True
)

outputs_df_filtered = outputs_df.copy()

variable_name_outputs = list(set([i for i in outputs_df.variable_name]))
ashrae_pmot = [i for i in variable_name_outputs if 'ASHRAE 55' in i and 'Running' in i][0]

optemp = [i for i in variable_name_outputs if 'Operative' in i]


outputs_df_filtered = outputs_df_filtered[(
    outputs_df_filtered.reporting_frequency.str.contains('Hourly')
    &
    (
        outputs_df_filtered.variable_name.str.contains('Setpoint Temperature_No Tolerance')
        |
        outputs_df_filtered.variable_name.str.contains('Zone Operative Temperature')
        |
        outputs_df_filtered.variable_name.str.contains(ashrae_pmot)
    )
)
]


accis.addAccis(

    idf=building,
    ScriptType='vrf_mm',
    Output_type='standard',
    Output_freqs=['hourly', 'runperiod'],
    Output_keep_existing=False,
    TempCtrl='temperature',
    make_averages=True,

    Output_take_dataframe=outputs_df_filtered,

    SupplyAirTempInputMethod='temperature difference',
    # Output_type='custom',
    # EnergyPlus_version='9.4',
    # Output_gen_dataframe=True,
    # make_averages=True,
    # debugging=True
)
##

meters = [
    'Electricity:HVAC',
]

for meter in meters:
    building.newidfobject(
        key='OUTPUT:METER',
        Key_Name=meter,
        Reporting_Frequency='hourly'
    )


[i.Variable_Name for i in building.idfobjects['output:variable']]
[i for i in building.idfobjects['output:variable']]
[i for i in building.idfobjects['output:meter']]

##

[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setinputdata']
bf.modify_ComfStand(building, 99)
bf.modify_CAT(building, 80)
bf.modify_ComfMod(building, 3)
bf.modify_MinOToffset(building, 50)
bf.modify_MaxWindSpeed(building, 50)
bf.modify_VentCtrl(building, 2)
bf.modify_ASTtol(building, 0.1)

[i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setvofinputdata']
bf.modify_MultiplierVOF(building, 0.1)
bf.modify_MaxTempDiffVOF(building, 6)


# [i for i in building.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'applycat']

##
available_outputs = print_available_outputs_mod(building)

