from accim.sim import accis
import os
try:
    accis.addAccis(
        ScriptType='vrf_mm',
        Output_keep_existing=False,
        Output_type='detailed',
        Output_freqs=['timestep', 'hourly'],
        EnergyPlus_version='9.4',
        TempCtrl='temp',
        ComfStand=[15],
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
except KeyError:
    print('\nkey error')
    for i in [j for j in os.listdir() if j.endswith('_pymod.idf')]:
        os.remove(i)
