"""Example of script usage with arguments."""

from accim.sim import accis

scriptTypeList = ['vrf']
outputsList = ['simplified', 'standard', 'timestep']
EPlist = ['ep95']

for i in scriptTypeList:
    for j in outputsList:
        for k in EPlist:
            accis.addAccis(
                ScriptType=i,
                Outputs=j,
                EnergyPlus_version=k,
                AdapStand=[1],
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
