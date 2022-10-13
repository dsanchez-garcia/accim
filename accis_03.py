from accim.sim import accis
import os
mode = 'ex_ac'
# mode = 'vrf_ac'

##
accis.addAccis(
    ScriptType=mode,
    # ScriptType='vrf_ac',
    Outputs='standard',
    EnergyPlus_version='ep22.1',
    TempCtrl='temp',
    # ModelOrigin='osm',
    # ModelOrigin='dsb',
    ComfStand=[1],
    CAT=[3],
    ComfMod=[3],
    HVACmode=[0],
    VentCtrl=[0],
    # VSToffset=[0],
    # MinOToffset=[0],
    # MaxWindSpeed=[0],
    # ASTtol_steps=0.1,
    # ASTtol_start=0.1,
    # ASTtol_end_input=0.1,
    # NameSuffix='vrf_ac',
    NameSuffix=mode,
    confirmGen=True
)

##
# try:
#     accis.addAccis(
#     ScriptType=mode,
#     # ScriptType='vrf_ac',
#     Outputs='standard',
#     EnergyPlus_version='ep22.1',
#     TempCtrl='temp',
#     # ModelOrigin='osm',
#     # ModelOrigin='dsb',
#     ComfStand=[1],
#     CAT=[3],
#     ComfMod=[3],
#     HVACmode=[0],
#     VentCtrl=[0],
#     # VSToffset=[0],
#     # MinOToffset=[0],
#     # MaxWindSpeed=[0],
#     # ASTtol_steps=0.1,
#     # ASTtol_start=0.1,
#     # ASTtol_end_input=0.1,
#     # NameSuffix='vrf_ac',
#     NameSuffix=mode,
#     confirmGen=True
#     )
# except:
#     os.remove(r'C:\Users\user\PycharmProjects\accim\accim\OSM_Example_00_pymod.idf')
