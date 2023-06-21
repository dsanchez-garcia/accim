4. Detailed use
===============

4.1 First steps
---------------

There has been developed 4 main branches of functions, which are:

-  VRF system with full air-conditioning mode: This mode has been
   developed mainly to support models originated with OpenStudio, which
   up to date does not support Airflow Network objects and subsequently
   Calculated Natural Ventilation. It adds standard VRF systems for each
   occupied zone and applies the adaptive or PMV-based setpoint
   temperatures, but only works with full air-conditioning mode.

-  VRF system with mixed mode: It adds standard VRF systems for each
   occupied zone and applies the adaptive or PMV-based setpoint
   temperatures. Works with Calculated Natural Ventilation, although
   full air-conditioning mode can also be used. If mixed mode is used,
   the model must be generally developed with DesignBuilder.

-  Existing HVAC system only with full air-conditioning mode: Keeps the
   existing HVAC systems and modify the existing setpoint temperatures
   to adaptive or PMV-based setpoint temperatures. However, mixed-mode
   and naturally ventilated modes are not available in this mode.

-  Existing HVAC system with mixed mode: UNDER DEVELOPMENT. IT IS NOT
   ADVISABLE TO USE IT YET. Keeps the existing HVAC systems and modify
   the existing setpoint temperatures to adaptive or PMV-based setpoint
   temperatures, considering mixed-mode. In order to properly work,
   there must be only one object for heating and another for cooling
   that can be used to monitor if these are turned on at any timestep
   (such as ``Coil:Cooling:Water`` and ``Coil:Heating:Water``). Also,
   these objects must be named following the pattern “Zone name” “Object
   name”. For instance, an ``Coil:Heating:Electric`` object could be
   named ``Block1:Zone1 PTAC Heating Coil``, given that ``Block1:Zone1``
   is a valid zone name. On the other hand, a ``Coil:Cooling:Water``
   object named ``Main Cooling Coil 1`` would not be valid, since in
   this case the room would be ``Main``; this is the typical case of
   some equipment shared by multiple rooms. If this condition is not
   met, accim will not generate the output IDF files for that input IDF
   file. For instance, if there are ``Coil:Heating:Electric`` and
   ``Coil:Heating:DX:SingleSpeed`` objects in the same model, simulation
   will crash. Also, if there is just an
   ``ZoneHVAC:Baseboard:RadiantConvective:Water`` used for heating, and
   cooling is not monitored, simulation will also crash.

Therefore, if you are going to use the VRF system script, you’re
supposed to have one or multiple IDFs with fixed setpoint temperature,
or even without any HVAC objects at all (it doesn’t matter, since the
module is going to add a standard VRF system for each zone, and the
simulation is going to be calculated with these VRF systems), and with
Calculated Natural Ventilation if you’re going to use the Mixed Mode. On
the other hand, if you are going to use any ExistingHVAC script, again
you’re supposed to have one or multiple IDFs, however in this case there
must be a fully functional HVAC system. Therefore, you must be able to
successfully run a simulation with fixed setpoint temperatures in order
for the accim package to work. The main difference between ExistingHVAC
only with full air-conditioning and with mixed mode is that in the
latter, the existing HVAC system needs to be mapped in order to monitor
if it needs to be activated or not, and windows need to be actuated in
case conditions for natural ventilation are favourable. In both cases,
when you export the IDF, please do not request ASHRAE 55 or CEN 15251
results. accim will do so by adding the relevant fields to the People
objects.

By using any ExistingHVAC script you might not get the results that you
expect, even if there are no errors in the accim and simulation
processes. The reason lies on the HVAC system itself, and that is why
the VRFsystem script has been developed, because it has been tested that
it works.

No matter what type or functions are you going to use, the language of
the software used to create the input IDF should be English (for
example, if you use Designbuilder in Spanish, accim won’t work
properly), and it’s not recommended to use any non-standard characters
in the input IDF, just like written accents or “ñ”.

Said that, accim will transform all the IDF files located in the same
path where script is. Therefore, the quickest way to run the script is
opening a prompt command dialog in the folder where the IDF files are
located (you can do this by holding Ctrl and right-click inside the
folder, and click on ‘open PowerShell window here’). Then run Python by
typing ‘python’ in the command prompt.

First you need to import the module ‘accis’ (stands for
Adaptive-Comfort-Control-Implementation Script):

::

   >>> from accim.sim import accis

And then, you just need to call the accis function:

::

   >>> accis.addAccis()

Then you’ll be asked in the prompt to enter some information so that
python knows how do you want to set up the output IDFs:

::

   --------------------------------------------------------
   Adaptive-Comfort-Control-Implemented Model (ACCIM)
   --------------------------------------------------------

   This tool allows to apply adaptive setpoint temperatures. 
   For further information, please read the documentation: 
   https://accim.readthedocs.io/en/master/
   For a visual understanding of the tool, please visit the following jupyter notebooks:
   -    Using addAccis() to apply adaptive setpoint temperatures
   https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/addAccis/using_addAccis.ipynb
   -    Using rename_epw_files() to rename the EPWs for proper data analysis after simulation
   https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/rename_epw_files/using_rename_epw_files.ipynb
   -    Using runEp() to directly run simulations with EnergyPlus
   https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/runEp/using_runEp.ipynb
   -    Using the class Table() for data analysis
   https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/Table/using_Table.ipynb

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

where:

* ScriptType can be ‘vrf_mm’, ‘vrf_ac’, ‘ex_mm’ or ‘ex_ac’, and it refers to the type of functions as explained above
* SupplyAirTempInputMethod can be ‘supply air temperature’ or ‘temperature difference’, and it is the supply air temperature input method for the VRF systems.
* Existing outputs in the IDF can be kept if entered ‘true’. Otherwise, if entered ‘false’, it will be removed for clarity purposes at results stage.
* Output_type can be ‘standard’, ‘detailed’, ‘simplified’ or ‘custom’ and it refers to the simulation results: ‘standard’ means that results will contain the full selection relevant to accim;‘detailed’ is mainly used for testing the software tool; ‘simplified’ means that results are just going to be the hourly operative temperature and VRF consumption of each zone, mainly used when you need the results not to be heavy files, because you are going to run a lot of simulations and capacity is limited; and finally, ‘custom’ allows the user to specify the outputs to be kept or removed by entering them in the python console.
* Output_freqs (Output frequencies) can be timestep, hourly, daily, monthly and/or runperiod, and these must be entered separated by space. It will add the specified output type (standard or simplified) in all entered frequencies.
* Also, a pandas DataFrame instance can be created containing all Output:Variable objects. This allows the user to filter the DataFrame as needed, so that it only contains the needed Output:Variable objects, and then it can be entered in the argument ``Output_take_dataframe``
* EnergyPlus_version can be from ‘9.1’ to ‘23.1’. It is the version of EnergyPlus you have installed in your computer. If you enter ‘9.1’, accim will look for the E+9.1.0 IDD file in path “C:\\EnergyPlusV9-1-0”.
* Temperature Control method can be ‘temperature’ or ‘temp’, or ‘pmv’. If ‘temp’ is used, the setpoint will be the operative temperature, otherwise if ‘pmv’ is used, the setpoint will be the PMV index.

accis will show on the prompt command dialog all the objects it adds,
and those that doesn’t need to be added because were already in the IDF,
and finally ask you to enter some values to set up the IDFs as you
desire. Please refer to the section titled ‘Setting up the target IDFs’.

Once you run the simulations, you might get some EnergyPlus warnings and
severe errors. This is something I’m currently working on.

4.2 Setting up the target IDFs
------------------------------

If you have run ``accis.addAccis()``, you will be asked in the prompt to
enter a few more values separated by space to set up the desired IDFs.
However, you can also skip the command prompt process by running accis
directly including the arguments in the function, whose usage would be:

::

   >>> accis.addAccis(str, # ScriptType: 'vrf_mm', 'vrf_ac', 'ex_mm', 'ex_ac'
   >>>                str, # SupplyAirTempInputMethod: 'supply air temperature', 'temperature difference'
   >>>                bool, # Output_keep_existing: True or False
   >>>                str, # Output_type: 'simplified', 'standard', 'detailed' or 'custom'
   >>>                list, # Output_freqs: ['timestep', 'hourly', 'daily', 'monthly', 'runperiod']
   >>>                bool, # Output_gen_dataframe: True or False
   >>>                pandas DataFrame, # Output_take_dataframe
   >>>                str, # EnergyPlus_version: '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1', '22.2' or '23.1'
   >>>                str, # TempCtrl: 'temperature' or 'temp', or 'pmv'
   >>>                list, # ComfStand, which is the Comfort Standard
   >>>                list, # CAT, which is the Category
   >>>                list, # ComfMod, which is Comfort Mode
   >>>                float, # SetpointAcc, which defines the accuracy of the setpoint temperatures
   >>>                str containing a date in format dd/mm, or an int # CoolSeasonStart
   >>>                str containing a date in format dd/mm, or an int # CoolSeasonEnd
   >>>                list, # HVACmode, which is the HVAC mode
   >>>                list, # VentCtrl, which is the Ventilation Control
   >>>                float, # MaxTempDiffVOF
   >>>                float, # MinTempDiffVOF
   >>>                float, # MultiplierVOF
   >>>                list, # VSToffset
   >>>                list, # MinOToffset
   >>>                list, # MaxWindSpeed
   >>>                float, # ASTtol start
   >>>                float, # ASTtol end
   >>>                float, # ASTtol steps
   >>>                str # NameSuffix: some text you might want to add at the end of the output IDF file name
   >>>                bool # verboseMode: True to print all process in screen, False to not to print it. Default is True.
   >>>                bool # confirmGen: True to confirm automatically the generation of IDFs; if False, you'll be asked to confirm in command prompt. Default is False. 
   >>>                )

Some example of the usage could be:

::

   >>> accis.addAccis(ScriptType='vrf_mm', # ScriptType: 'vrf_mm', 'vrf_ac', 'ex_mm', 'ex_ac'
   >>>                SupplyAirTempInputMethod='supply air temperature', # SupplyAirTempInputMethod: 'supply air temperature', 'temperature difference'
   >>>                Output_keep_existing=False, # Output_keep_existing: True or False
   >>>                Output_type='standard', # Output_type: 'simplified' or 'standard'
   >>>                Output_freqs=['hourly', 'runperiod'], # Output_freqs: ['timestep', 'hourly', 'daily', 'monthly', 'runperiod']
   >>>                Output_gen_dataframe=False,
   >>>                # we just omit Output_take_dataframe
   >>>                EnergyPlus_version='9.5', # EnergyPlus_version: '9.1', '9.2', '9.3', '9.4', '9.5', '9.6', '22.1', '22.2' or '23.1'
   >>>                TempCtrl='temp', # Temperature Control: 'temperature' or 'temp', or 'pmv'
   >>>                ComfStand=[0, 1, 2, 3], # ComfStand, which is the Comfort Standard
   >>>                CAT=[1, 2, 3, 80, 90], # CAT, which is the Category
   >>>                ComfMod=[0, 1, 2, 3], # ComfMod, which is Comfort Mode
   >>>                SetpointAcc=10, # Therefore, setpoints will be rounded to the first decimal
   >>>                # we just omit CoolSeasonStart, since the default date is May 1st
   >>>                # we just omit CoolSeasonEnd, since the default date is September 1st
   >>>                HVACmode=[0, 1, 2], # HVACmode, which is the HVAC mode
   >>>                VentCtrl=[0, 1], # VentCtrl, which is the Ventilation Control
   >>>                MaxTempDiffVOF=20, # When the difference of operative and outdoor temperature exceeds 20°C, windows will be opened the fraction of MultiplierVOF.
   >>>                MinTempDiffVOF=1, # When the difference of operative and outdoor temperature is smaller than 1°C, windows will be fully opened. Between min and max, windows will be linearly opened.
   >>>                MultiplierVOF=20, # Fraction of window to be opened when temperature difference exceeds MaxTempDiffVOF.
   >>>                VSToffset=[0, 1, 2], # VSToffset, which is the Ventilation Setpoint Temperature offset
   >>>                MinOToffset=[0, 1, 2], # MinOToffset, which is the Minimum Outdoor Temperature offset
   >>>                MaxWindSpeed=[10, 20, 30], # MaxWindSpeed, which is th Maximum Wind Speed
   >>>                ASTtol_start=0, # ASTtol_start, which is the start of the tolerance sequence
   >>>                ASTtol_end_input=2, # ASTtol_end_input, which is the end of the tolerance sequence
   >>>                ASTtol_steps=0.25, # ASTtol_steps, which are the steps of the tolerance sequence
   >>>                NameSuffix='standard' # Name Suffix: for example, just in case you want to clarify the outputs
   >>>                )

For clarity purposes, it’s recommended to specify the argument name as
well, as shown above. If you don’t specify all arguments, you’ll be ask
to enter them at the prompt command, and these values will be used
instead of those specified in the function call. Each argument is
explained below:

-  ComfStand: refers to the thermal comfort standard or model to be
   applied. Enter any number from 0 to 21 to select the comfort standard
   or model to be used; you can see which model is each number in the
   table below. Readthedocs doesn’t render it properly, so please take a
   look at the `Github
   repository <https://github.com/dsanchez-garcia/accim/blob/master/docs/how%20to%20use.md>`__.
   For example, if you enter ‘0 1 2 3’, you’ll get IDFs for CTE,
   EN16798-1, ASHRAE 55 and the local model developed by Rijal et al for
   Japanese dwellings. If you don’t enter any number, it’ll ask you to
   enter the numbers again.

+---+---+---+--------------------------------------------------------------+---+
| C | C | A | Reference                                                    |   |
| o | o | r |                                                              |   |
| m | m | e |                                                              |   |
| f | f | a |                                                              |   |
| S | S |   |                                                              |   |
| t | t |   |                                                              |   |
| a | a |   |                                                              |   |
| n | n |   |                                                              |   |
| d | d |   |                                                              |   |
| N | N |   |                                                              |   |
| o | a |   |                                                              |   |
| . | m |   |                                                              |   |
|   | e |   |                                                              |   |
+===+===+===+==============================================================+===+
| 0 | E | S | The Government of Spain. Royal Decree 314/2006. Approving    |   |
|   | S | p | the Spanish Technical Building Code CTE-DB-HE-1 2013:1–43.   |   |
|   | P | a | https://www.boe.es/eli/es/rd/2006/03/17/314 (accessed August |   |
|   | C | i | 6, 2021).                                                    |   |
|   | T | n |                                                              |   |
|   | E |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | I | E | European committee for standardization. EN 16798-1:2019      |   |
|   | N | u | Energy performance of buildings. Ventilation for buildings.  |   |
|   | T | r | Indoor environmental input parameters for design and         |   |
|   | E | o | assessment of energy performance of buildings addressing     |   |
|   | N | p | indoor air quality, thermal environment, lighting and        |   |
|   | 1 | e | acoustics. 2019.                                             |   |
|   | 6 |   | https://en.tien                                              |   |
|   | 7 |   | da.aenor.com/norma-bsi-bs-en-16798-1-2019-000000000030297474 |   |
|   | 9 |   | (accessed August 6, 2021).                                   |   |
|   | 8 |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 2 | I | W | ASHRAE Standard 55-2020 Thermal Environmental Conditions for |   |
|   | N | o | Human Occupancy, ASHRAE Standard (2020).                     |   |
|   | T | r |                                                              |   |
|   | A | l |                                                              |   |
|   | S | d |                                                              |   |
|   | H | w |                                                              |   |
|   | R | i |                                                              |   |
|   | A | d |                                                              |   |
|   | E | e |                                                              |   |
|   | 5 |   |                                                              |   |
|   | 5 |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 3 | J | J | Rijal, H. B., Humphreys, M. A., & Nicol, J. F. (2019).       |   |
|   | P | a | Adaptive model and the adaptive mechanisms for thermal       |   |
|   | N | p | comfort in Japanese dwellings. Energy and Buildings, 202,    |   |
|   | R | a | 109371. https://doi.org/10.1016/j.enbuild.2019.109371        |   |
|   | i | n |                                                              |   |
|   | j |   |                                                              |   |
|   | a |   |                                                              |   |
|   | l |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 4 | C | C | MOHURD, Evaluation Standard for Indoor Thermal Environment   |   |
|   | H | h | in Civil Buildings (GB/T 50785-2012), Ministry of Housing    |   |
|   | N | i | and Urban-Rural Development (MOHURD), Beijing, China, 2012.  |   |
|   | G | n |                                                              |   |
|   | B | a |                                                              |   |
|   | T |   |                                                              |   |
|   | 5 |   |                                                              |   |
|   | 0 |   |                                                              |   |
|   | 7 |   |                                                              |   |
|   | 8 |   |                                                              |   |
|   | 5 |   |                                                              |   |
|   | C |   |                                                              |   |
|   | o |   |                                                              |   |
|   | l |   |                                                              |   |
|   | d |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 5 | C | C | MOHURD, Evaluation Standard for Indoor Thermal Environment   |   |
|   | H | h | in Civil Buildings (GB/T 50785-2012), Ministry of Housing    |   |
|   | N | i | and Urban-Rural Development (MOHURD), Beijing, China, 2012.  |   |
|   | G | n |                                                              |   |
|   | B | a |                                                              |   |
|   | T |   |                                                              |   |
|   | 5 |   |                                                              |   |
|   | 0 |   |                                                              |   |
|   | 7 |   |                                                              |   |
|   | 8 |   |                                                              |   |
|   | 5 |   |                                                              |   |
|   | H |   |                                                              |   |
|   | o |   |                                                              |   |
|   | t |   |                                                              |   |
|   | M |   |                                                              |   |
|   | i |   |                                                              |   |
|   | l |   |                                                              |   |
|   | d |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 6 | C | C | Yang, L., Fu, R., He, W., He, Q., & Liu, Y. (2020). Adaptive |   |
|   | H | h | thermal comfort and climate responsive building design       |   |
|   | N | i | strategies in dry–hot and dry–cold areas: Case study in      |   |
|   | Y | n | Turpan, China. Energy and Buildings, 209, 109678.            |   |
|   | a | a | https://doi.org/10.1016/j.enbuild.2019.109678                |   |
|   | n |   |                                                              |   |
|   | g |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 7 | I | I | Manu, S., Shukla, Y., Rawal, R., Thomas, L. E., & de Dear,   |   |
|   | N | n | R. (2016). Field studies of thermal comfort across multiple  |   |
|   | D | d | climate zones for the subcontinent: India Model for Adaptive |   |
|   | I | i | Comfort (IMAC). Building and Environment, 98, 55–70.         |   |
|   | M | a | https://doi.org/10.1016/j.buildenv.2015.12.019               |   |
|   | A |   |                                                              |   |
|   | C |   |                                                              |   |
|   | C |   |                                                              |   |
|   | N |   |                                                              |   |
|   | V |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 8 | I | I | Manu, S., Shukla, Y., Rawal, R., Thomas, L. E., & de Dear,   |   |
|   | N | n | R. (2016). Field studies of thermal comfort across multiple  |   |
|   | D | d | climate zones for the subcontinent: India Model for Adaptive |   |
|   | I | i | Comfort (IMAC). Building and Environment, 98, 55–70.         |   |
|   | M | a | https://doi.org/10.1016/j.buildenv.2015.12.019               |   |
|   | A |   |                                                              |   |
|   | C |   |                                                              |   |
|   | C |   |                                                              |   |
|   | M |   |                                                              |   |
|   | M |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 9 | I | I | Rawal, R., Shukla, Y., Vardhan, V., Asrani, S., Schweiker,   |   |
|   | N | n | M., de Dear, R., Garg, V., Mathur, J., Prakash, S., Diddi,   |   |
|   | D | d | S., Ranjan, S. V., Siddiqui, A. N., & Somani, G. (2022).     |   |
|   | I | i | Adaptive thermal comfort model based on field studies in     |   |
|   | M | a | five climate zones across India. Building and Environment,   |   |
|   | A |   | 219, 109187. https://doi.org/10.1016/J.BUILDENV.2022.109187  |   |
|   | C |   |                                                              |   |
|   | R |   |                                                              |   |
|   | 7 |   |                                                              |   |
|   | D |   |                                                              |   |
|   | R |   |                                                              |   |
|   | M |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | I | I | Rawal, R., Shukla, Y., Vardhan, V., Asrani, S., Schweiker,   |   |
| 0 | N | n | M., de Dear, R., Garg, V., Mathur, J., Prakash, S., Diddi,   |   |
|   | D | d | S., Ranjan, S. V., Siddiqui, A. N., & Somani, G. (2022).     |   |
|   | I | i | Adaptive thermal comfort model based on field studies in     |   |
|   | M | a | five climate zones across India. Building and Environment,   |   |
|   | A |   | 219, 109187. https://doi.org/10.1016/J.BUILDENV.2022.109187  |   |
|   | C |   |                                                              |   |
|   | R |   |                                                              |   |
|   | 3 |   |                                                              |   |
|   | 0 |   |                                                              |   |
|   | D |   |                                                              |   |
|   | R |   |                                                              |   |
|   | M |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | I | I | Dhaka, S., Mathur, J., Brager, G., & Honnekeri, A. (2015).   |   |
| 1 | N | n | Assessment of thermal environmental conditions and           |   |
|   | D | d | quantification of thermal adaptation in naturally ventilated |   |
|   | D | i | buildings in composite climate of India. Building and        |   |
|   | h | a | Environment, 86, 17–28.                                      |   |
|   | a |   | https://doi.org/10.1016/J.BUILDENV.2014.11.024               |   |
|   | k |   |                                                              |   |
|   | a |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | R | R | Udrea, I., Croitoru, C., Nastase, I., Crutescu, R., &        |   |
| 2 | O | o | Badescu, V. (2018). First adaptive thermal comfort equation  |   |
|   | M | m | for naturally ventilated buildings in Bucharest, Romania.    |   |
|   | U | a | International Journal of Ventilation, 17(3), 149–165.        |   |
|   | d | n | https://doi.org/10.1080/14733315.2017.1356057                |   |
|   | r | i |                                                              |   |
|   | e | a |                                                              |   |
|   | a |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | A | A | Williamson, T., & Daniel, L. (2020). A new adaptive thermal  |   |
| 3 | U | u | comfort model for homes in temperate climates of Australia.  |   |
|   | S | s | Energy and Buildings, 210, 109728.                           |   |
|   | W | t | https://doi.org/10.1016/j.enbuild.2019.109728                |   |
|   | i | r |                                                              |   |
|   | l | a |                                                              |   |
|   | l | l |                                                              |   |
|   | i | i |                                                              |   |
|   | a | a |                                                              |   |
|   | m |   |                                                              |   |
|   | s |   |                                                              |   |
|   | o |   |                                                              |   |
|   | n |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | A | A | de Dear, R., Kim, J., & Parkinson, T. (2018). Residential    |   |
| 4 | U | u | adaptive comfort in a humid subtropical climate—Sydney       |   |
|   | S | s | Australia. Energy and Buildings, 158, 1296–1305.             |   |
|   | D | t | https://doi.org/10.1016/j.enbuild.2017.11.028                |   |
|   | e | r |                                                              |   |
|   | D | a |                                                              |   |
|   | e | l |                                                              |   |
|   | a | i |                                                              |   |
|   | r | a |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | B | B | Rupp, R. F., de Dear, R., & Ghisi, E. (2018). Field study of |   |
| 5 | R | r | mixed-mode office buildings in Southern Brazil using an      |   |
|   | A | a | adaptive thermal comfort framework. Energy and Buildings,    |   |
|   | R | z | 158, 1475–1486.                                              |   |
|   | u | i | https://doi.org/10.1016/J.ENBUILD.2017.11.047                |   |
|   | p | l |                                                              |   |
|   | p |   |                                                              |   |
|   | N |   |                                                              |   |
|   | V |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | B | B | Rupp, R. F., de Dear, R., & Ghisi, E. (2018). Field study of |   |
| 6 | R | r | mixed-mode office buildings in Southern Brazil using an      |   |
|   | A | a | adaptive thermal comfort framework. Energy and Buildings,    |   |
|   | R | z | 158, 1475–1486.                                              |   |
|   | u | i | https://doi.org/10.1016/J.ENBUILD.2017.11.047                |   |
|   | p | l |                                                              |   |
|   | p |   |                                                              |   |
|   | A |   |                                                              |   |
|   | C |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | M | M | I. Oropeza-Perez, A.H. Petzold-Rodriguez, C. Bonilla-Lopez,  |   |
| 7 | E | e | Adaptive thermal comfort in the main Mexican climate         |   |
|   | X | x | conditions with and without passive cooling, Energy and      |   |
|   | O | i | Buildings. 145 (2017) 251–258.                               |   |
|   | r | c | https://doi.org/10.1016/j.enbuild.2017.04.031.               |   |
|   | o | o |                                                              |   |
|   | p |   |                                                              |   |
|   | e |   |                                                              |   |
|   | z |   |                                                              |   |
|   | a |   |                                                              |   |
|   | A |   |                                                              |   |
|   | r |   |                                                              |   |
|   | i |   |                                                              |   |
|   | d |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | M | M | I. Oropeza-Perez, A.H. Petzold-Rodriguez, C. Bonilla-Lopez,  |   |
| 8 | E | e | Adaptive thermal comfort in the main Mexican climate         |   |
|   | X | x | conditions with and without passive cooling, Energy and      |   |
|   | O | i | Buildings. 145 (2017) 251–258.                               |   |
|   | r | c | https://doi.org/10.1016/j.enbuild.2017.04.031.               |   |
|   | o | o |                                                              |   |
|   | p |   |                                                              |   |
|   | e |   |                                                              |   |
|   | z |   |                                                              |   |
|   | a |   |                                                              |   |
|   | D |   |                                                              |   |
|   | r |   |                                                              |   |
|   | y |   |                                                              |   |
|   | T |   |                                                              |   |
|   | r |   |                                                              |   |
|   | o |   |                                                              |   |
|   | p |   |                                                              |   |
|   | i |   |                                                              |   |
|   | c |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 1 | M | M | I. Oropeza-Perez, A.H. Petzold-Rodriguez, C. Bonilla-Lopez,  |   |
| 9 | E | e | Adaptive thermal comfort in the main Mexican climate         |   |
|   | X | x | conditions with and without passive cooling, Energy and      |   |
|   | O | i | Buildings. 145 (2017) 251–258.                               |   |
|   | r | c | https://doi.org/10.1016/j.enbuild.2017.04.031.               |   |
|   | o | o |                                                              |   |
|   | p |   |                                                              |   |
|   | e |   |                                                              |   |
|   | z |   |                                                              |   |
|   | a |   |                                                              |   |
|   | T |   |                                                              |   |
|   | e |   |                                                              |   |
|   | m |   |                                                              |   |
|   | p |   |                                                              |   |
|   | e |   |                                                              |   |
|   | r |   |                                                              |   |
|   | a |   |                                                              |   |
|   | t |   |                                                              |   |
|   | e |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 2 | M | M | I. Oropeza-Perez, A.H. Petzold-Rodriguez, C. Bonilla-Lopez,  |   |
| 0 | E | e | Adaptive thermal comfort in the main Mexican climate         |   |
|   | X | x | conditions with and without passive cooling, Energy and      |   |
|   | O | i | Buildings. 145 (2017) 251–258.                               |   |
|   | r | c | https://doi.org/10.1016/j.enbuild.2017.04.031.               |   |
|   | o | o |                                                              |   |
|   | p |   |                                                              |   |
|   | e |   |                                                              |   |
|   | z |   |                                                              |   |
|   | a |   |                                                              |   |
|   | H |   |                                                              |   |
|   | u |   |                                                              |   |
|   | m |   |                                                              |   |
|   | T |   |                                                              |   |
|   | r |   |                                                              |   |
|   | o |   |                                                              |   |
|   | p |   |                                                              |   |
|   | i |   |                                                              |   |
|   | c |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 2 | C | C | A. Pérez-Fargallo, J.A. Pulido-Arcas, C. Rubio-Bellido, M.   |   |
| 1 | H | h | Trebilcock, B. Piderit, S. Attia, Development of a new       |   |
|   | L | i | adaptive comfort model for low income housing in the         |   |
|   | P | l | central-south of chile, Energy Build. 178 (2018) 94–106.     |   |
|   | e | e | https://doi.org/10.1016/j.enbuild.2018.08.030.               |   |
|   | r |   |                                                              |   |
|   | e |   |                                                              |   |
|   | z |   |                                                              |   |
|   | - |   |                                                              |   |
|   | F |   |                                                              |   |
|   | a |   |                                                              |   |
|   | r |   |                                                              |   |
|   | g |   |                                                              |   |
|   | a |   |                                                              |   |
|   | l |   |                                                              |   |
|   | l |   |                                                              |   |
|   | o |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+
| 2 | I | W | ISO, 2005. ISO 7730: Ergonomics of the thermal environment   |   |
| 2 | N | o | Analytical determination and interpretation of thermal       |   |
|   | T | r | comfort using calculation of the PMV and PPD indices and     |   |
|   | I | l | local thermal comfort criteria. Management 3, 605–615.       |   |
|   | S | d | https://doi.org/10.1016/j.soildyn.2004.11.005                |   |
|   | O | w |                                                              |   |
|   | 7 | i |                                                              |   |
|   | 7 | d |                                                              |   |
|   | 3 | e |                                                              |   |
|   | 0 |   |                                                              |   |
+---+---+---+--------------------------------------------------------------+---+

-  CAT: refers to the category of the thermal comfort model applied.
   Most of the Comfort Standards work with 80 and 90% acceptability
   levels, except the European EN 16798-1 (works with Categories 1, 2
   and 3), the Chinese GB/T 50785 (works with categories 1 and 2), and
   the India Model for Adaptive Comfort - Commercial (which works with
   80, 85 and 90% acceptability levels). So, for example, if you are
   going to use the EN16798-1 (ComfStand = 1), you can enter ‘1 2 3’ to
   generate setpoint temperatures for Categories 1, 2 and 3. Or, if you
   are going to use the IMAC Commercial in naturally ventilated mode
   (ComfStand = 7), you can enter ‘80 85 90’ to generate setpoint
   temperatures for these acceptability levels. All categories are
   referenced in the `full list of setpoint
   temperatures <https://raw.githack.com/dsanchez-garcia/accim/master/docs/full_setpoint_table.html>`__
   at the end of this section. Please note that the Category values must
   be consistent with the Comfort Standard values previously entered.
   If, for instance, you enter ‘1’ in the Comfort Standard value (means
   you’re asking for EN16798 model), but then enter ‘80’ or ‘90’ in the
   Category value (which are categories used in ASHRAE55), you won’t get
   the results you want.

-  ComfMod: is the Comfort Mode, and refers to the comfort modes used in
   accim. It controls if the setpoints are static (when ComfMod = 0) or
   adaptive (when ComfMod = 1, 2 or 3). When they are adaptive, it also
   controls the comfort model applied when the adaptive model is not
   applicable (that is, when the running mean outdoor temperature limits
   are exceeded), in which case a PMV-based model is applied. Each
   ComfMod for each ComfStand and CAT is referenced at the `full list of
   setpoint
   temperatures <https://raw.githack.com/dsanchez-garcia/accim/master/docs/full_setpoint_table.html>`__.
   Please refer to the research article
   https://www.mdpi.com/1996-1073/12/8/1498 for more information. Figure
   below shows the variation of setpoint temperatures when ComfMod 0
   (upper left), 1 (upper right), 2 (lower left) and 3 (lower right),
   when ComfStand is 1 (EN 16798-1, although figure shows the superseded
   standard, but the setpoint behaviour is similar)

.. figure:: https://www.mdpi.com/energies/energies-12-01498/article_deploy/html/images/energies-12-01498-g002.png
   :alt: ComfMod


-  SetpointAcc: refers to the accuracy of the setpoint temperatures. Any
   number, integer or float, can be entered in this argument. For
   instance, if 1 was entered, the cooling setpoint would be rounded to
   the nearest integer below adaptive upper comfort limit minus
   tolerance (ASTtol), and the heating setpoint would be rounded to the
   nearest integer above adaptive lower comfort limit plus tolerance. If
   27.46 and 20.46 were the upper and lower comfort limits and its
   tolerances were respectively -0.1 and +0.1, then the nearest integers
   to 27.36 and 20.56 would be 27 and 21, and therefore, these would be
   the cooling and heating setpoint temperatures. If 2 was used instead,
   then the rounding would be done to the nearest half. If 10 were used,
   the rounding would be done to the first decimal. If 0.5 or 0.1 were
   used, the rounding would be done respectively every 2 or 10 celsius
   degrees.

-  CoolSeasonStart: it is the start of the cooling season, only used
   when EN16798-1, ASHRAE 55 or ISO7730 are entered in ComfStand
   (respectively, ComfStand = 1, 2 and 22) and setpoint behaviour is set
   to static (i.e. ComfMod = 0). This argument can take the number of
   the day in the year (i.e. an integer) or a string containing a date
   in format dd/mm (for instance, “01/05”). Values of CoolSeasonStart
   greater than CoolSeasonEnd can be used, therefore denoting the
   location of the EPW file should be in the south hemisphere.

-  CoolSeasonEnd: Similar to CoolSeasonStart, but it is the end of the
   cooling season. Again, only used when EN16798-1, ASHRAE 55 or ISO7730
   are entered in ComfStand (respectively, ComfStand = 1, 2 and 22) and
   setpoint behaviour is set to static (i.e. ComfMod = 0). Again, this
   argument can take the number of the day in the year (i.e. an integer)
   or a string containing a date in format dd/mm (for instance,
   “01/05”). Values of CoolSeasonEnd smaller than CoolSeasonStart can be
   used, therefore denoting the location of the EPW file should be in
   the south hemisphere.

-  HVACmode: refers to the HVAC mode applied. Enter 0 for Fully
   Air-conditioned (AC), 1 for Naturally ventilated (NV) and/or 2 for
   Mixed Mode (MM). Please note that Calculated natural ventilation must
   be enabled so that Mixed Mode works. So, for example, if you enter ‘0
   1 2’ you’ll be getting all HVAC modes, or if you just enter ‘0 1’
   you’ll be getting just Fully Air-conditioned and Naturally
   ventilated.

-  VentCtrl: refers to the ventilation control, only used in for NV and
   MM. When using NV, If you enter ‘0’, ventilation will be allowed if
   operative temperature exceeds neutral temperature (also known as
   comfort temperature); if you enter ‘1’, ventilation will be allowed
   if operative temperature exceeds the upper comfort limit. In other
   words, sets the value of the neutral temperature or the upper comfort
   limit to the Ventilation Setpoint Temperature (VST). When using MM, 0
   = Ventilates above neutral temperature and fully opens doors and
   windows; 1 = Ventilates above lower comfort limit and fully opens
   doors and windows; 2 = Ventilates above neutral temperature and opens
   doors and windows based on the customised venting opening factor; and
   3 = Ventilates above lower comfort limit and opens doors and windows
   based on the customised venting opening factor. Either way, if you
   enter ‘0 1’ you’ll be getting both ventilation control modes.

-  MaxTempDiffVOF: Maximum Temperature Difference for Venting Opening
   Factor. Maximum temperature difference between indoor operative and
   outdoor temperatures, which when exceeded, windows and doors are
   opened only the fraction specified in the MultiplierVOF argument. If
   temperature difference oscillates between maximum and minimum, the
   windows and doors are opened based on the linear equation. Follows
   the same operation as explained in `Designbuilder help
   website <https://designbuilder.co.uk/helpv7.0/Content/CalculatedNatVent.htm>`__.

-  MinTempDiffVOF: Minimum Temperature Difference for Venting Opening
   Factor. Minimum temperature difference between indoor operative and
   outdoor temperatures, which when smaller, windows and doors are fully
   opened. If temperature difference oscillates between maximum and
   minimum, the windows and doors are opened based on the linear
   equation. Follows the same operation as explained in `Designbuilder
   help
   website <https://designbuilder.co.uk/helpv7.0/Content/CalculatedNatVent.htm>`__.

-  MultiplierVOF: Multiplier for modulating the Venting Opening Factor.
   The fraction of the windows that will be opened when temperature
   difference exceeds MaxTempDiffVOF. Follows the same operation as
   explained in `Designbuilder help
   website <https://designbuilder.co.uk/helpv7.0/Content/CalculatedNatVent.htm>`__.
   |Venting Opening Factor|

-  VSToffset: stands for Ventilation Setpoint Temperature (VST) offset,
   again only used in Mixed Mode (HVAC Mode ‘2’). Applies the entered
   values as an offset to the VST, in Celsius degrees. Values entered
   can be positive or negative float or integers, and must be
   space-separated. For example, if you enter ‘-2 -1 0 1 2’ you’ll be
   getting offsets of -2°C, -1°C, 0°C, 1°C and 2°C to the VST. If you
   don’t enter any number, it’ll be used ‘0’ as the default value.

-  MinOToffset: stands for Minimum Outdoor Temperature offset, again
   only used in Mixed Mode (HVAC Mode ‘2’). Sets the minimum outdoor
   temperature an offset to the heating setpoint temperature. For
   example, if you enter ‘1’ (please, note that the numbers must be
   positive), ventilation won’t be allowed if outdoor temperature falls
   below 1°C below the heating setpoint, in order to prevent from
   entering excessive cold. Therefore, below said limit, windows are
   closed and, if needed, air conditioning starts to work. Entered
   values can be float or integers, but always positive numbers, and
   must be space-separated. For example, if you enter ‘0 1 2’ you’ll be
   getting offsets of 0°C, 1°C and 2°C to the heating setpoint
   temperature. If you don’t enter any number, it’ll be used ‘50’ as the
   default value (that is 50°C below heating setpoint temperature, and
   therefore no limit is applied).

-  MaxWindSpeed: stands for maximum wind speed, again only used in Mixed
   Mode (HVAC Mode ‘2’). Sets the maximum wind speed in which
   ventilation is allowed, in m/s. Therefore, if you enter ‘20’,
   ventilation won’t be allowed if wind speed is greater than 20 m/s.
   Entered values can be float or integers, but always positive numbers,
   and must be space-separated. For example, if you enter ‘5 10 15 20’
   you’ll be getting different IDFs with maximum wind speeds of 5 m/s,
   10 m/s, 15 m/s and 20 m/s. If you don’t enter any number, it’ll be
   used ‘50’ as the default value (that is 50 m/s, and therefore no
   limit is applied).

-  ASTtol: stands for Adaptive Setpoint Temperature tolerance. It
   applies the number that you enter as a tolerance for the adaptive
   heating and cooling setpoint temperatures. The original problem was
   that, if we assigned the adaptive setpoint straight to the comfort
   limit (i.e. you enter ‘0’ for ASTtol), there were a few hours that
   fell outside the comfort zone because of the error in some decimals
   in the simulation of the operative temperature. Therefore, the
   original purpose of this feature is to control that all hours are
   comfortable hours (i.e. operative temperature falls within the
   comfort zone), and we can make that sure by considering a little
   tolerance of 0.10 °C. For example, say that adaptive cooling and
   heating setpoints are originally 29.5 and 21.5°C at some day; if you
   enter ‘1’ for ASTtol, then the setpoints would be modified to 28.5
   and 22.5°C (1°C below original cooling setpoint, and 1°C above
   original heating setpoint). The function will create a sequence of
   numbers based on the entered values. So, numbers must be entered in 3
   stages: first, the start of the sequence; second, the end of the
   sequence, and third, the steps. So for example, if you enter ‘0’ for
   the start, ‘1’ for the end, and ‘0.25’ for the steps, you would be
   getting ASTtol values of 0°C, 0.25°C, 0.5°C, 0.75°C and 1°C. If you
   don’t enter any number, it’ll be used ‘0.1’ as the default value (as
   previously said, to make sure all hours are comfortable hours), and
   you would be getting only one variation of 0.1°C.

-  NameSuffix: the text you would like to add at the end of the file
   name.

-  verboseMode: True to print all process in screen, False to not to
   print it. Default is True.

-  confirmGen: Generally, this argument should be left as default. True
   to confirm automatically the generation of IDFs; if False, you’ll be
   asked to confirm in command prompt. Default is False. So, if you are
   going to set it True, be sure about the number of IDFs you are going
   to generate, because these might be thousands.

So, below you can see a sample name of an IDF created by using accim’s
VRFsystem functions. The package takes the original IDF file as a
reference, saves a copy, run all the functions so that setpoint
temperatures are transformed from static to adaptive, an changes its
name based on the values previously entered:

**TestModel_onlyGeometryForVRFsystem[CS_INT
EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[standard**

where:

-  ‘TestModel_onlyGeometryForVRFsystem’ is the name of the original IDF.

-  CS refers to the Comfort Standard, and it’s followed by the thermal
   comfort standard applied (could be ‘ESP CTE’, ‘INT EN16798’, ‘INT
   ASHRAE55’, ‘JPN Rijal’, etc).

-  CA refers to the Category, which could be 1, 2 or 3 if CS is EN16798,
   80 or 90 if CS is ASHRAE55 or other models, or 80, 85 or 90 in case
   of the IMAC C.

-  CM refers to the Comfort Mode, which could be 0 (Static), 1, 2, or 3
   (Adaptive modes).

-  HM refers to the HVAC Mode, which could be 0 (Full air conditioning),
   1 (Naturally ventilated), or 2 (Mixed Mode).

-  VC refers to the Ventilation Control, which could be 0, 1, 2 or 3.

-  VO refers to the Ventilation setpoint temperature offset, which could
   be any number, float or integer, positive or negative.

-  MT refers to the Minimum Outdoor Temperature offset, which could be
   any number, float or integer, but always positive number.

-  MW refers to the Maximum Wind Speed, which could be any number, float
   or integer, but always positive number.

-  AT refers to the Adaptive Setpoint Temperature offset, which could be
   any number, float or integer, but always positive number. Please
   remember this number comes from a 3-stage process (refer to the
   explanation above).

-  ‘standard’ is the suffix, which can be whatever you want. For
   example, this allows you to make a for loop with ‘standard’,
   ‘simplified’ and ‘timestep’ and run the simulations with all type of
   outputs.

If some inputs are not used or don’t make sense, you’ll be able to se an
‘X’ in the output IDF file. For example, if you use CTE as Comfort
Standard, then the inputs for Category and Comfort Mode (which are only
for EN16798-1 and ASHRAE 55) are not used in the process, and the output
IDF would contain in its name ‘CS_ESP CTE[CA_X[CM_X’. Another similar
case occurs if you use Full air-conditioning HVAC Mode (i.e. enter ‘0’
for HVAC Mode), or if you use the ‘ex_ac’ ScriptType, where the output
IDF would contain in its name ‘[HM_0[VC_X[VO_X[MT_X[MW_X’.

4.3 Full list of setpoint temperatures
--------------------------------------

Depending on the arguments ComfStand, CAT and ComfMod, cooling and
heating setpoint temperatures will be the following:

(If it is too small, you can look at it also at the `Github
repository <https://raw.githack.com/dsanchez-garcia/accim/master/docs/full_setpoint_table.html>`__)

.. figure:: images/full_table.png
   :alt: full_table.png


.. |Venting Opening Factor| image:: images/VentingOpeningFactor.png

4.4 Putting it into practice: Adaptive setpoint temperatures step by step
-------------------------------------------------------------------

You can see a Jupyter Notebook either in the How-to Guide section of this documentation or in the link below:

https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/addAccis/using_addAccis.ipynb

You can also execute it at your computer. You just need to find the folder containing the .ipynb and all other files at the accim package folder
within your site_packages path, in

accim/sample_files/jupyter_notebooks/addAccis

The path should be something like this, with your username instead of
YOUR_USERNAME:

*C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\accim\\sample_files\\jupyter_notebooks\\addAccis*

Then, you just need to copy the folder to a different path (i.e. Desktop), open a cmd dialog pointing at it, and run "jupyter notebook". After that, an internet browser will pop up, and you will be able to open the .ipynb file.

You can also see an example below. The input file is included within
:file:`accim/sample_files/sample IDFs` folder, and it was originally named
:file:`TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2310.idf`, but for
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

4.5 Renaming epw files for later data analysis
------------------------------------------

You can see a Jupyter Notebook either in the How-to Guide section of this documentation or in the link below:

https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/rename_epw_files/using_rename_epw_files.ipynb

You can also execute it at your computer. You just need to find the folder containing the .ipynb and all other files at the accim package folder
within your site_packages path, in

accim/sample_files/jupyter_notebooks/rename_epw_files

The path should be something like this, with your username instead of
YOUR_USERNAME:

*C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\accim\\sample_files\\jupyter_notebooks\\rename_epw_files*

Then, you just need to copy the folder to a different path (i.e. Desktop), open a cmd dialog pointing at it, and run "jupyter notebook". After that, an internet browser will pop up, and you will be able to open the .ipynb file.

4.6 Running simulations
-------------------

You can see a Jupyter Notebook either in the How-to Guide section of this documentation or in the link below:

https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/runEp/using_runEp.ipynb

You can also execute it at your computer. You just need to find the folder containing the .ipynb and all other files at the accim package folder
within your site_packages path, in

accim/sample_files/jupyter_notebooks/runEp

The path should be something like this, with your username instead of
YOUR_USERNAME:

*C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\accim\\sample_files\\jupyter_notebooks\\runEp*

Then, you just need to copy the folder to a different path (i.e. Desktop), open a cmd dialog pointing at it, and run "jupyter notebook". After that, an internet browser will pop up, and you will be able to open the .ipynb file.

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

4.7 Functions and methods for data analysis; making figures and tables
------------------------------------------------------------------

You can see a Jupyter Notebook either in the How-to Guide section of this documentation or in the link below:

`https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/Table/using_Table.ipynb <https://github.com/dsanchez-garcia/accim/blob/master/accim/sample_files/jupyter_notebooks/runEp/using_runEp.ipynb>`__

You can also execute it at your computer. You just need to find the folder containing the .ipynb and all other files at the accim package folder
within your site_packages path, in

accim/sample_files/jupyter_notebooks/Table

The path should be something like this, with your username instead of
YOUR_USERNAME:

*C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\accim\\sample_files\\jupyter_notebooks\\Table*

Then, you just need to copy the folder to a different path (i.e. Desktop), open a cmd dialog pointing at it, and run "jupyter notebook". After that, an internet browser will pop up, and you will be able to open the .ipynb file.