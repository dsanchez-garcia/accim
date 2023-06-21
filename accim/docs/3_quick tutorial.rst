3. Quick tutorial:
==============================================================

3.1 Implementing adaptive setpoint temperatures
-----------------------------------------------

This is a very brief explanation of the usage. Therefore, if you don’t
get the results you expected or get some error, I would recommend
reading the ‘Detailed use’ section at the documentation in the link
below.

accim will take as input IDF files those located at the same path as the
script. You only need to run the following code:

3.1.1 Short version
^^^^^^^^^^^^^^^^^^^^

::

   from accim.sim import accis
   accis.addAccis()

Once you run this code, you will be asked to enter some information at
the terminal or python console to generate the output IDF files.


3.1.2 Long version
^^^^^^^^^^^^^^^^

::

   from accim.sim import accis
   accis.addAccis(
       ScriptType=str, # ScriptType: 'vrf_mm', 'vrf_ac', 'ex_mm', 'ex_ac'. For instance: ScriptType='vrf_ac',
       SupplyAirTempInputMethod=str, # SupplyAirTempInputMethod: 'supply air temperature', 'temperature difference'. For instance: SupplyAirTempInputMethod='supply air temperature',
       Output_keep_existing=bool, # Output_keep_existing: True or False. For instance: Output_keep_existing=False,
       Output_type=str, # Output_type: 'simplified', 'standard', 'detailed' or 'custom'. For instance: Output_type='standard',
       Output_freqs=list, # Output_freqs: ['timestep', 'hourly', 'daily', 'monthly', 'runperiod']. For instance: Output_freqs=['hourly', 'runperiod'],
       Output_gen_dataframe=bool, # Output_keep_existing: True or False. For instance: Output_keep_existing=False,
       Output_take_dataframe=pandas Dataframe,
       EnergyPlus_version=str, # EnergyPlus_version: '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1', '22.2' or '23.1'. For instance: EnergyPlus_version='23.1',
       TempCtrl=str, # TempCtrl: 'temperature' or 'temp', or 'pmv'. For instance: TempCtrl='temp',
       ComfStand=list, # it is the Comfort Standard. Can be any integer from 0 to 21. For instance: ComfStand=[0, 1, 2, 3],
       CAT=list, # it is the Category. Can be 1, 2, 3, 80, 85 or 90. For instance: CAT=[3, 80],
       ComfMod=list, # it is Comfort Mode. Can be 0, 1, 2 or 3. For instance: ComfMod=[0, 3],
       SetpointAcc=float, # it is the accuracy of the setpoint temperatures
       CoolSeasonStart=dd/mm date in string format or integer to represent the day of the year, # it is the start date for the cooling season
       CoolSeasonEnd=dd/mm date in string format or integer to represent the day of the year, # it is the end date for the cooling season
       HVACmode=list, # it is the HVAC mode. 0 for Full AC, 1 for NV and 2 for MM. For instance: HVACmode=[0, 2],
       VentCtrl=list, # it is the Ventilation Control. Can be 0 or 1. For instance: VentCtrl=[0, 1],
       MaxTempDiffVOF=float, # When the difference of operative and outdoor temperature exceeds MaxTempDiffVOF, windows will be opened the fraction of MultiplierVOF. For instance: MaxTempDiffVOF=20,
       MinTempDiffVOF=float, # When the difference of operative and outdoor temperature is smaller than MinTempDiffVOF, windows will be fully opened. Between min and max, windows will be linearly opened. For instance: MinTempDiffVOF=1,
       MultiplierVOF=float, # Fraction of window to be opened when temperature difference exceeds MaxTempDiffVOF. For instance: Multiplier=0.2,
       VSToffset=list, # it is the offset for the ventilation setpoint. Can be any number, float or int. For instance: VSToffset=[-1.5, -1, 0, 1, 1.5],
       MinOToffset=list, # it is the offset for the minimum outdoor temperature to ventilate. Can be any positive number, float or int. For instance: MinOToffset=[0.5, 1, 2],
       MaxWindSpeed=list, # it is the maximum wind speed allowed for ventilation. Can be any positive number, float or int. For instance: MinOToffset=[2.5, 5, 10],
       ASTtol_start=float, # it is the start of the tolerance sequence. For instance: ASTtol_start=0,
       ASTtol_end_input=float, # it is the end of the tolerance sequence. For instance: ASTtol_start=2,
       ASTtol_steps=float, # these are the steps of the tolerance sequence. For instance: ASTtol_steps=0.25,
       NameSuffix=str # NameSuffix: some text you might want to add at the end of the output IDF file name. For instance: NameSuffix='whatever',
       verboseMode=bool # verboseMode: True to print all process in screen, False to not to print it. Default is True. For instance: verboseMode=True,
       confirmGen=bool # True to confirm automatically the generation of IDFs; if False, you'll be asked to confirm in command prompt. Default is False. For instance: confirmGen=False,
   )

3.1 Other uses
--------------
Although the main use of accim is the implementation of adaptive setpoint temperatures, there are some functions, classes and methods that allow to roughly automate the whole process consisting of preparation of the epw and idf files, the simulation runs and the data analysis. For further information, please refer to the How-to Guides section in this documentation, which contains some Jupyter Notebooks that can also be found in accim's installation folder.