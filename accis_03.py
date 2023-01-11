from accim.sim import accis
for i in [10, 15, 20]:
    for j in [0, 0.5, 1]:
        for k in [0, 0.2, 0.4]:
            accis.addAccis(
                ScriptType='vrf_mm',
                Output_keep_existing=False,
                Output_type='standard',
                Output_freqs=['hourly'],
                EnergyPlus_version='22.1',
                TempCtrl='temp',
                ComfStand=[15],
                CAT=[80],
                ComfMod=[3],
                HVACmode=[2],
                VentCtrl=[2],
                MaxTempDiffVOF=i,
                MinTempDiffVOF=j,
                MultiplierVOF=k,
                VSToffset=[0],
                MinOToffset=[50],
                MaxWindSpeed=[50],
                ASTtol_steps=0.1,
                ASTtol_start=0.1,
                ASTtol_end_input=0.1,
                NameSuffix=f'{i}_{j}_{k}',
                confirmGen=True
            )
