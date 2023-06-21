.. role:: raw-latex(raw)
   :format: latex
..

5. Examples
===========

5.1 Class ``addAccis``: Adaptive setpoint temperatures step by step
-------------------------------------------------------------------

You can see an example below. The input file is included within
’accim:raw-latex:`\sample `files' folder, and it was originally named
“TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2310.idf”, but for
clarity purposes in this case has been renamed to “TestModel.idf”.

So, say you have an IDF in some folder, called ‘TestModel.idf’. So, you
can either open an IDE or simply a CMD dialog pointing at that path and
execute python. Let’s run the functions to get the energy models with
adaptive setpoint temperatures.

::

   >>> from accim.sim import accis
   >>> accis.addAccis()

When we hit enter, we’ll be asked to enter some information regarding
the ScriptType, the Outputs and the EnergyPlus version:

::

   --------------------------------------------------------
   Adaptive-Comfort-Control-Implemented Model (ACCIM)
   --------------------------------------------------------

   This tool allows to apply adaptive setpoint temperatures.
   For further information, please read the documentation:
   https://accim.readthedocs.io/en/master/
   For a visual understanding of the tool, please visit the following jupyter notebooks:
   -    Using addAccis() to apply adaptive setpoint temperatures
   https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/addAccis/using_addAccis.ipynb-    Using rename_epw_files() to rename the EPWs for proper data analysis after simulation
   https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/rename_epw_files/using_rename_epw_files.ipynb
   -    Using runEp() to directly run simulations with EnergyPlus
   https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/runEp/using_runEp.ipynb
   -    Using the class Table() for data analysis
   https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/Table/using_Table.ipynb

   Starting with the process.

   Now, you are going to be asked to enter some information for different arguments to generate the output IDFs with adaptive setpoint temperatures.
   If you are not sure about how to use these parameters, please take a look at the documentation in the following link:
   https://accim.readthedocs.io/en/latest/how%20to%20use.html

   Please, enter the following information:

   Enter the ScriptType (
   for VRFsystem with full air-conditioning mode: vrf_ac;
   for VRFsystem with mixed-mode: vrf_mm;
   for ExistingHVAC with mixed mode: ex_mm;
   for ExistingHVAC with full air-conditioning mode: ex_ac
   ): vrf_mm

   Enter the SupplyAirTempInputMethod (
   for Supply Air Temperature: supply air temperature;
   for Temperature Difference: temperature difference;
   ): temperature difference

   Do you want to keep the existing outputs (true or false)?: false

   Enter the Output type (standard, simplified, detailed or custom): standard

   Enter the Output frequencies separated by space (timestep, hourly, daily, monthly, runperiod): hourly runperiod

   Do you want to generate a dataframe to see all outputs? (true or false): false

   Enter the EnergyPlus version (9.1 to 23.1): 23.1

   Enter the Temperature Control method (temperature or pmv): temperature

When we hit enter, it’s going to add all the EnergyPlus objects needed:

::

   Basic input data:
   ScriptType is: vrf_mm
   Supply Air Temperature Input Method is: temperature difference
   Output type is: standard
   Output frequencies are:
   ['hourly', 'runperiod']
   EnergyPlus version is: 23.1
   Temperature Control method is: temperature

   =======================START OF GENERIC IDF FILE GENERATION PROCESS=======================

   Starting with file:
   TestModel
   IDD location is: C:\EnergyPlusV23-1-0\Energy+.idd
   The occupied zones in the model TestModel are:
   BLOCK1:ZONE2
   BLOCK1:ZONE1
   The windows and doors in the model TestModel are:
   Block1_Zone2_Wall_3_0_0_0_0_0_Win
   .
   .
   .
   Added - BLOCK1_ZONE1 VRF Indoor Unit DX Cooling Coil Reporting Frequency Runperiod Output:Variable data
   Added - BLOCK1_ZONE1 VRF Indoor Unit DX Heating Coil Reporting Frequency Runperiod Output:Variable data
   IDF has been saved
   Ending with file:
   TestModel
   =======================END OF GENERIC IDF FILE GENERATION PROCESS=======================

   The following IDFs will not work, and therefore these will be deleted:
   None

And then ask us to enter the required information to generate the output
IDF files (you can omit some by hitting enter without entering any
value):

::

   =======================START OF OUTPUT IDF FILES GENERATION PROCESS=======================

   The information you will be required to enter below will be used to generate the customised output IDFs:
   Enter the Comfort Standard numbers separated by space (
   0 = ESP CTE;
   1 = INT EN16798-1;
   2 = INT ASHRAE55;
   3 = JPN Rijal;
   4 = CHN GBT50785 Cold;
   5 = CHN GBT50785 HotMild;
   6 = CHN Yang;
   7 = IND IMAC C NV;
   8 = IND IMAC C MM;
   9 = IND IMAC R 7DRM;
   10 = IND IMAC R 30DRM;
   11 = IND Dhaka;
   12 = ROM Udrea;
   13 = AUS Williamson;
   14 = AUS DeDear;
   15 = BRA Rupp NV;
   16 = BRA Rupp AC;
   17 = MEX Oropeza Arid;
   18 = MEX Oropeza DryTropic;
   19 = MEX Oropeza Temperate;
   20 = MEX Oropeza HumTropic;
   21 = CHL Perez-Fargallo;
   22 = INT ISO7730;
   Please refer to the full list of setpoint temperatures at https://raw.githack.com/dsanchez-garcia/accim/master/docs/full_setpoint_table.html
   ): 1 2 7
             Are you sure the numbers are correct? [y or [] / n]:

   For the comfort standard 1 = INT EN16798, the available categories you can choose are:
   1 = EN16798 Category I
   2 = EN16798 Category II
   3 = EN16798 Category III
   For the comfort standard 2 = INT ASHRAE55, the available categories you can choose are:
   80 = ASHRAE 55 80% acceptability
   90 = ASHRAE 55 90% acceptability
   For the comfort standard 7 = IND IMAC C NV, the available categories you can choose are:
   80 = 80% acceptability
   85 = 85% acceptability
   90 = 90% acceptability
   Enter the Category numbers separated by space (
   1 = CAT I / CAT A;
   2 = CAT II / CAT B;
   3 = CAT III / CAT C;
   80 = 80% ACCEPT;
   85 = 85% ACCEPT;
   90 = 90% ACCEPT;
   Please refer to the full list of setpoint temperatures at https://raw.githack.com/dsanchez-garcia/accim/master/docs/full_setpoint_table.html
   ): 2 3 85 90
             Are you sure the numbers are correct? [y or [] / n]:

   For the comfort standard 1 = INT EN16798, the available ComfMods you can choose are:
   0 = EN16798 Static setpoints
   1 = EN16798 Adaptive setpoints when applicable, otherwise CTE
   2 = EN16798 Adaptive setpoints when applicable, otherwise EN16798 Static setpoints
   3 = EN16798 Adaptive setpoints when applicable, otherwise EN16798 Adaptive setpoints horizontally extended
   For the comfort standard 2 = INT ASHRAE55, the available ComfMods you can choose are:
   0 = ISO 7730 Static setpoints
   1 = ASHRAE 55 Adaptive setpoints when applicable, otherwise CTE
   2 = ASHRAE 55 Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints
   3 = ASHRAE 55 Adaptive setpoints when applicable, otherwise ASHRAE 55 Adaptive setpoints horizontally extended
   For the comfort standard 7 = IND IMAC C NV, the available ComfMods you can choose are:
   0 = Indian Building Code Static setpoints
   1 = IMAC C NV Model Adaptive setpoints when applicable, otherwise Indian Building Code Static setpoints
   2 = IMAC C NV Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints
   3 = IMAC C NV Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended
   Enter the Comfort Mode numbers separated by space (
   0 or 0.X = Static;
   1, 1.X, 2, 3 = Adaptive;
   Please refer to the full list of setpoint temperatures at https://raw.githack.com/dsanchez-garcia/accim/master/docs/full_setpoint_table.html
   ): 0 3
             Are you sure the numbers are correct? [y or [] / n]:
             
   Enter the setpoint accuracy number (any number greater than 0): 100
             Are you sure the number is correct? [y or [] / n]:
             
   Enter the start of the cooling season in numeric date format dd/mm or the day of the year: 01/05
             Are you sure the number is correct? [y or [] / n]:
             
   Enter the end of the cooling season in numeric date format dd/mm or the day of the year: 01/10
             Are you sure the number is correct? [y or [] / n]:

   Enter the HVAC Mode numbers separated by space (
   0 = Fully Air-conditioned;
   1 = Naturally ventilated;
   2 = Mixed Mode;
   ): 2
             Are you sure the numbers are correct? [y or [] / n]:

   Enter the Ventilation Control numbers separated by space (
   If HVACmode = 1:
      0 = Ventilates above neutral temperature;
      1 = Ventilates above upper comfort limit;
   If HVACmode = 2:
      0 = Ventilates above neutral temperature and fully opens doors and windows;
      1 = Ventilates above lower comfort limit and fully opens doors and windows;
      2 = Ventilates above neutral temperature and opens doors and windows based on the customised venting opening factor;
      3 = Ventilates above lower comfort limit and opens doors and windows based on the customised venting opening factor;
   ): 2 3
             Are you sure the numbers are correct? [y or [] / n]:
   Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): 15
             Are you sure the number is correct? [y or [] / n]:
   Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): 1
             Are you sure the number is correct? [y or [] / n]:
   Enter the multiplier number for Ventilation Opening Factor (any number between 0 and 1): 0.2
             Are you sure the number is correct? [y or [] / n]:

   Enter the VSToffset numbers separated by space (if omitted, will be 0):
             Are you sure the numbers are correct? [y or [] / n]:

   Enter the MinOToffset numbers separated by space (if omitted, will be 50):
             Are you sure the numbers are correct? [y or [] / n]:

   Enter the MaxWindSpeed numbers separated by space (if omitted, will be 50):
             Are you sure the numbers are correct? [y or [] / n]:

   Enter the ASTtol value from (if omitted, will be 0.1):
             Are you sure the numbers are correct? [y or [] / n]:
   Enter the ASTtol value to (if omitted, will be 0.1):
             Are you sure the numbers are correct? [y or [] / n]:
   Enter the ASTtol value steps (if omitted, will be 0.1):
             Are you sure the numbers are correct? [y or [] / n]:

Afterwards, ACCIS will let us know which the output IDFs are going to
be, the total number of them and will ask for our confirmation to
proceed:

::

   The list of output IDFs is going to be:
   TestModel[CS_INT EN16798[CA_2[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_2[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_2[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_2[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_3[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_3[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_3[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_3[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT ASHRAE55[CA_90[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT ASHRAE55[CA_90[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT ASHRAE55[CA_90[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT ASHRAE55[CA_90[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_85[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_85[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_85[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_85[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_90[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_90[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_90[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_90[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   And the total number of output IDFs is going to be 20
   Do you still want to run ACCIS? [y/n]: y

If we entered ``n``, the whole process would shut down. Otherwise, if we
entered ‘y’, the generation of output IDF files would start, and ACCIS
would print on screen each output IDF name as it generates it. As you
can see, we are going to use the EN16798-1, ASHRAE 55 and IMAC
Commercial for naturally ventilated buildings, categories 2 and 3 for
EN16798, 90% acceptability levels for ASHRAE 55, 85 and 90%
acceptability levels for IMAC C NV, all with ComfMod 0 (with static
setpoint temperatures) and 3 (with adaptive setpoint temperatures when
the model is applicable, otherwise horizontally extending the adaptive
setpoint temperatures), Mixed Mode, and we just went ahead with the
remaining default values.

::

   Generating the following output IDF files:
   TestModel[CS_INT EN16798[CA_2[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_2[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_2[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_2[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_3[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_3[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_3[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT EN16798[CA_3[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT ASHRAE55[CA_90[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT ASHRAE55[CA_90[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT ASHRAE55[CA_90[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_INT ASHRAE55[CA_90[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_85[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_85[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_85[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_85[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_90[CM_0.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_90[CM_0.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_90[CM_3.0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
   TestModel[CS_IND IMAC C NV[CA_90[CM_3.0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf

   =======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================

Afterwards, you just need to run the simulation. Once you have run the
simulations you need, you’ll get the files you usually get when you run
any simulation, including the hourly results on a CSV file.

5.2 Renaming epw files for later data analysis
------------------------------------------

You can see a Jupyter Notebook in the link below:

https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/rename_epw_files/using_rename_epw_files.ipynb

You can also execute it at your computer, at the accim package folder
within your site_packages path, in
accim/sample_files/jupyter_notebooks/rename_epw_files/using_rename_epw_files.ipynb

The path should be something like this, with your username instead of
YOUR_USERNAME:

\_C::raw-latex:`\Users`:raw-latex:`\YOUR`\_USERNAME:raw-latex:`\AppData`:raw-latex:`\Local`:raw-latex:`\Programs`:raw-latex:`\Python`:raw-latex:`\Python39`:raw-latex:`\Lib`:raw-latex:`\site`-packages:raw-latex:`\accim`:raw-latex:`\sample`\_files:raw-latex:`\jupyter`\_notebooks:raw-latex:`\rename`\_epw_files:raw-latex:`\using`\ *rename_epw_files.ipynb*

5.3 Running simulations
-------------------

You can see a Jupyter Notebook in the link below:

https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/runEp/using_runEp.ipynb

You can also execute it at your computer, at the accim package folder
within your site_packages path, in
accim/sample_files/jupyter_notebooks/runEp/using_runEp.ipynb

The path should be something like this, with your username instead of
YOUR_USERNAME:

\_C::raw-latex:`\Users`:raw-latex:`\YOUR`\_USERNAME:raw-latex:`\AppData`:raw-latex:`\Local`:raw-latex:`\Programs`:raw-latex:`\Python`:raw-latex:`\Python39`:raw-latex:`\Lib`:raw-latex:`\site`-packages:raw-latex:`\accim`:raw-latex:`\sample`\_files:raw-latex:`\jupyter`\_notebooks:raw-latex:`\runEp`:raw-latex:`\using`\ *runEp.ipynb*

This script has been created by eppy’s development team
(https://eppy.readthedocs.io/en/latest/runningeplus.html, specifically
from section ‘Running in parallel processes using Generators’), however
I did some changes. Anyway, you probably should check out eppy package,
since it’s absolutely awesome.

By using this script, the EnergyPlus version used to simulate the IDFs
will be the IDF’s version. Therefore, if your IDF is in version 9.4, but
you don’t have EnergyPlus 9.4 installed, you’ll get an error.

The main difference is that this one allows to run simulations with
several EPW files. It takes all EPW files and IDF files located in the
script folder, and runs them. So for example, say you have 2 no. IDFs
(1.idf and 2.idf) and 2 no. EPW files (a.epw and b.epw). Then, this
script will run the following simulations: 1[a; 1[b; 2[a; 2[b. The
character ‘[’ has been used as separator in order to not to be in
conflict with other programs. Besides, there’s a package within accim
currently being developed (within folder data) in order to generate
tables and graphs automatically.

So, how to use it?

Say you have already run any of the accis functions, and therefore you
might have a folder with the following files:

::

   Mode                 LastWriteTime         Length Name
   ----                 -------------         ------ ----
   -a---l        20/07/2019     12:42        1407718 Bilbao_2015.epw
   -a---l        20/07/2019     12:43        1408160 Bilbao_2016.epw
   -a----        27/02/2021     15:01         114617 TestModel_SingleZone.idf
   -a---l        27/02/2021     15:01         114617 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0.1.idf
   -a---l        27/02/2021     15:01         114617 TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_3[AT_0.1.idf

So, now we can run the simulations:

::

   >>> from accim.run import run
   >>> dir(run)
   ['IDF', '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__', 'make_eplaunch_options', 'os', 'removefiles', 'runEp', 'runIDFs']
   >>> run.runEp()

``runEp()`` is going to ask you if you want to run the simulations only
with IDF files generated by accim. If you enter ‘y’, it’ll run only
accim output IDFs, otherwise if you enter ‘n’, it will run all idfs in
the folder. As you can see below, we didn’t need to remove the original
IDF ‘TestModel_SingleZone.idf’ from the folder. Then, it will let you
know the IDFs and EPWs that are going to be used in the simulations.
Besides, it’ll let you know the total number of simulations, and will
ask for your confirmation, because you might start thousands of
simulations by mistake. Further, ``runEp()``\ can take a total number of
3 arguments, which are 2 boolean arguments, and one integer:
``runEp(runOnlyAccim=True, confirmRun=True, num_CPUs=4)``. If you
entered these, you would skip the command prompt process and jump
straight to the simulation process. Since we entered 4 for the num_CPUs
argument, the simulations would be run by using 4 CPS at the same time.

::

   >>> run.runEp()
   Do you want to run only accim output IDFs? [y or n]:y
   The IDFs we are going to run are: ['TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0.1.idf', 'TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_3[AT_0.1.idf']
    and the No. of IDFs is going to be 2
   The EPWs we are going to run are: ['Bilbao_2015.epw', 'Bilbao_2016.epw']
    and the No. of EPWs is going to be 2
   Therefore, the simulations are going to be:
   TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0.1.idf[Bilbao_2015.epw
   TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0.1.idf[Bilbao_2016.epw
   TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_3[AT_0.1.idf[Bilbao_2015.epw
   TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_3[AT_0.1.idf[Bilbao_2016.epw
    and the No. of simulations is going to be 4
   The number of simulations is going to be 4. Do you still want to proceed?[y or n]:y

Afterwards, you’ll see the calculations progress if you use the windows
prompt command, and you’ll get an extensive list of simulation files,
similar to this:

::

   Mode                 LastWriteTime         Length Name
   ----                 -------------         ------ ----
   -a---l        20/07/2019     12:42        1407718 Bilbao_2015.epw
   -a---l        20/07/2019     12:43        1408160 Bilbao_2016.epw
   -a---l        27/02/2021     15:01         114617 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0.1.idf
   -a---l        27/02/2021     16:47           1721 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.audit
   -a---l        27/02/2021     16:47           9179 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.bnd
   -a---l        27/02/2021     16:47        2023160 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.csv
   -a---l        27/02/2021     16:47           6181 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.dxf
   -a---l        27/02/2021     16:47          30483 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.eio
   -a---l        27/02/2021     16:47             99 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.end
   -a---l        27/02/2021     16:47           5351 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.err
   -a---l        27/02/2021     16:47        2968770 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.eso
   -a---l        27/02/2021     16:47              0 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.mdd
   -a---l        27/02/2021     16:47          13352 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.mtd
   -a---l        27/02/2021     16:47              0 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.rdd
   -a---l        27/02/2021     16:47           1107 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.rvaudit
   -a---l        27/02/2021     16:47           2667 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.shd
   -a---l        27/02/2021     16:47          34187 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015Table.csv
   -a---l        27/02/2021     16:47         139585 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015Table.htm
   -a---l        27/02/2021     16:47           3421 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015Zsz.csv
   .
   .
   .

You might need to keep these in order to debug some error, or any other
reason, but if you don’t need to keep these except csv values with
hourly results, you can run the ``removefiles()`` function:

::

   >>> run.removefiles()

And now your working directory should look like this:

::

   Mode                 LastWriteTime         Length Name
   ----                 -------------         ------ ----
   -a---l        20/07/2019     12:42        1407718 Bilbao_2015.epw
   -a---l        20/07/2019     12:43        1408160 Bilbao_2016.epw
   -a---l        27/02/2021     15:01         114617 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0.1.idf
   -a---l        27/02/2021     16:47        2023160 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2015.csv
   -a---l        27/02/2021     16:47        2017212 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0[Bilbao_2016.csv
   -a---l        27/02/2021     15:01         114617 TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_3[AT_0.1.idf
   -a---l        27/02/2021     16:47        2023114 TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_3[AT_0[Bilbao_2015.csv
   -a---l        27/02/2021     16:47        2017070 TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_3[AT_0[Bilbao_2016.csv

As you can see, ``removefiles()`` removes everything except EPW files,
IDFs, .py scripts and the hourly CSV values which contains the results
of the simulations.

5.4 Functions and methods for data analysis; making figures and tables
------------------------------------------------------------------

You can see a Jupyter Notebook in the link below:

`https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/Table/using_Table.ipynb <https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/runEp/using_runEp.ipynb>`__

You can also execute it at your computer, at the accim package folder
within your site_packages path, in
accim/sample_files/jupyter_notebooks/Table/using_Table.ipynb

The path should be something like this, with your username instead of
YOUR_USERNAME:

\_C::raw-latex:`\Users`:raw-latex:`\YOUR`\_USERNAME:raw-latex:`\AppData`:raw-latex:`\Local`:raw-latex:`\Programs`:raw-latex:`\Python`:raw-latex:`\Python39`:raw-latex:`\Lib`:raw-latex:`\site`-packages:raw-latex:`\accim`:raw-latex:`\sample`\_files:raw-latex:`\jupyter`\_notebooks:raw-latex:`\Table`:raw-latex:`\using`\ *Table.ipynb*
