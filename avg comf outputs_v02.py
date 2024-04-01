from accim.sim.accis import addAccis
from accim.utils import amend_idf_version_from_dsb
from accim.sim.chile_funcs import apply_heating_activation_time_sch
import os

orig_idf = [i for i in os.listdir() if i.endswith('.idf')][0]
# todo problem spacelist with V940
x = addAccis(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='standard',
    Output_freqs=['hourly'],
    # EnergyPlus_version='auto',
    TempCtrl='temp',

    ComfStand=[2],
    # CustAST_ACSTall=10,
    # CustAST_ACSTaul=35,
    # CustAST_AHSTall=10,
    # CustAST_AHSTaul=35,
    # CustAST_ACSToffset=4,
    # CustAST_AHSToffset=-4,
    # CustAST_m=0.4,
    # CustAST_n=15,

    CAT=[80],
    # CATcoolOffset=2,
    # CATheatOffset=2,
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True,
    # VRFschedule='Heating_activation_time_chile',
    # eer=1,
    # cop=0.8,
    # NameSuffix='2_deg_higher'
)

# output_idf = x.output_idfs[[i for i in x.output_idfs.keys()][0]]
# output_idf.idfobjects['Output:variable']
