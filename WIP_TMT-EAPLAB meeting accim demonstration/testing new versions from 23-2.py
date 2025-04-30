# from besos import eppy_funcs as ef
#
# building = ef.get_building('TestModel_V2420.idf')
#



from accim.sim.accis import addAccis
import os

idfs = [i for i in os.listdir() if i.endswith('.idf') and '_V2510' in i]

accis_instance = addAccis(
    idfs=idfs,
    EnergyPlus_version='auto',
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    TempCtrl='temp',
    ComfStand=[14],
    CAT=[80],
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True
    )



##

# epversion = '9.6'
# epversionslist = ['9.6', '22.1', '22.2', '23.1']
#
# any([epversion == i for i in epversionslist])
