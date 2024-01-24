from eppy.modeleditor import IDF
from accim.sim import accis_for_dsb_from_scratch as accis

iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'

fname = 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V940.idf'

IDF.setiddname(iddfile)
idf = IDF(fname)

# idf.idfobjects['zone']



accis.addAccis(

    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    EnergyPlus_version='23.1',
    TempCtrl='temperature',
    ComfStand=[15],
    CAT=[80],
    ComfMod=[0, 3],
    SetpointAcc=1000,
    HVACmode=[1, 2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50]
)