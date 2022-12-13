"""Example of script usage with arguments."""

from accim.sim import accis

scriptTypeList = ['vrf_mm']
outputsList = ['simplified', 'standard']
EPlist = ['22.2']

for i in scriptTypeList:
    for j in outputsList:
        for k in EPlist:
            accis.addAccis(
                ScriptType=i,
                Outputs_keep_existing=False,
                Output_type=j,
                Output_freqs=['daily'],
                EnergyPlus_version=k,
                TempCtrl='temp',
                ComfStand=[1],
                CAT=[1],
                ComfMod=[1],
                HVACmode=[2],
                VentCtrl=[0],
                VSToffset=[0],
                MinOToffset=[50],
                MaxWindSpeed=[50],
                ASTtol_start=0.1,
                ASTtol_end_input=0.1,
                ASTtol_steps=0.1,
                NameSuffix=j
            )
