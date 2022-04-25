from accim.sim import accis
accis.addAccis(ScriptType='vrf',
               Outputs='standard',
               EnergyPlus_version='ep96',
               AdapStand=[2, 3],
               CAT=[80, 90],
               ComfMod=[0, 3],
               HVACmode=[0, 2],
               VentCtrl=[1],
               VSToffset=[0],
               MinOToffset=[0],
               MaxWindSpeed=[0],
               ASTtol_steps=0.1,
               ASTtol_start=0.1,
               ASTtol_end_input=0.1,
               # confirmGen=True
               )