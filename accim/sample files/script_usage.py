"""Example of script usage with arguments."""

from accim.sim import accis

scriptTypeList = ['mz', 'sz']
outputsList = ['simplified', 'standard', 'timestep']
EPlist = ['ep94']

for i in scriptTypeList:
    for j in outputsList:
        for k in EPlist:
            accis.addAccis_v03(i,
                               j,
                               k,
                               [1], [3], [2], [0], [0], [0], [50], [50], 0.1, 0.1, 0.1,
                               j)
