# How to use
## First steps
There has been developed 2 main branches of functions, which are:

- MultipleZones: Work with multiple zones, add standard VRF systems for each zone and apply the adaptive setpoint temperatures.

- SingleZone: Work with single thermal zones, keep the current HVAC systems and modify the current setpoint temperatures to adaptive setpoint temperatures.

Therefore, if you are going to use the MultipleZones functions, you're supposed to have one or multiple IDFs with fixed setpoint temperature, or even without any HVAC objects at all (it doesn't matter, since the module is going to add a standard VRF system for each zone, and the simulation is going to be calculated with these VRF systems), and with Calculated Natural Ventilation if you're going to use the Mixed Mode.
On the other hand, if you are going to use the SingleZone functions, again you're supposed to have one or multiple IDFs, however in this case there must be a fully functional HVAC system. Therefore, you must be able to successfully run a simulation with fixed setpoint temperatures in order for the accim package to work.

No matter what type or functions are you going to use, the language of the software used to create the input IDF should be English (for example, if you use Designbuilder in Spanish, accim won't work properly), and it's not recommended to use any non-standard characters in the input IDF, just like written accents or "ñ".

Said that, accim will transform all the IDF files located in the same path where script is. Therefore, the quickest way to run the script is opening a prompt command dialog in the folder where the IDF files are located (you can do this by holding Ctrl and right-click inside the folder, and click on 'open PowerShell window here'). Then run Python by typing 'python' in the command prompt.

First you need to import the module 'accis' (stands for Adaptive Comfort Control Implementation Script):
```
>>> from accim.sim import accis
```
And then, you just need to call the accis function:
```
>>> accis.addAccis()
```
Then you'll be asked in the prompt to enter some information so that python knows how do you want to set up the output IDFs:
```
Enter the ScriptType (MultipleZone or mz, or SingleZone or sz): mz
Enter the Output (Standard, Simplified or Timestep): standard
Enter the EnergyPlus version (Ep91 or Ep94): ep94
```
where
- ScriptType can be MultipleZone or SingleZone, and it refers to the type of functions as explained above
- Outputs can be Standard, Simplified or Timestep, and it refers to the simulation results: Standard means that results will contain the full selection; Simplified means that results are just going to be the hourly operative temperature and VRF consumption of each zone, mainly used when you need the results not to be heavy files, because you are going to run a lot of simulations and capacity is limited; and Timestep means that results are going to be the full selection in Timestep frequency, so this is only recommended for tests, or small number of simulations.
- EnergyPlus version can be Ep91 or Ep94, and it refers to the IDF EnergyPlus version, which could be EnergyPlus 9.1.0 or EnergyPlus 9.4.0. You can try with other EnergyPlus versions, but it's not guaranteed to work, and you'll still need to be entering ep91 or ep94 in the information.

Besides, `addAccis()` can take the same values we entered before in the prompt command as arguments. The usage of this function will be detailed below. An example of this, to get the same results as shown in the command prompt would be:
```
>>> accis.addAccis('mz','standard','ep94')
```
accis will show on the prompt command dialog all the objects it adds, and those that doesn't need to be added because were already in the IDF, and finally ask you to enter some values to set up the IDFs as you desire. Please refer to the section titled 'Setting up the target IDFs'.

Once you run the simulations, you might get some EnergyPlus warnings and severe errors. This is something I'm currently working on.

## Setting up the target IDFs
### MultipleZones functions

If you run `accis.addAccis('mz', whateverOutputs, whateverEPversion)`, you will be ask in the prompt to enter a few values separated by space to set up the desired IDFs. However, you can also skip the command prompt process by running accis directly including the arguments in the function, whose usage would be:
```
>>> accis.addAccis(str, # ScriptType: 'multiplezone' or 'mz', 'singlezone' or 'sz'
>>>                str, # Outputs: 'simplified', 'standard' or 'timestep'
>>>                str, # EP version: 'ep91' or 'ep94'
>>>                list, # Adaptive Standard
>>>                list, # Category
>>>                list, # Comfort Mode
>>>                list, # HVAC Mode
>>>                list, # Ventilation Control
>>>                list, # VSToffset
>>>                list, # MinOToffset
>>>                list, # MaxWindSpeed
>>>                float, # ASTtol start
>>>                float, # ASTtol end
>>>                float, # ASTtol steps
>>>                str # NameSuffix: some text you might want to add at the end of the output IDF file name
>>>                )
```
Some example of the usage could be:
```
>>> accis.addAccis('mz', # ScriptType: 'multiplezone' or 'mz', 'singlezone' or 'sz'
>>>                'standard', # Outputs: 'simplified', 'standard' or 'timestep'
>>>                'ep94', # EP version: 'ep91' or 'ep94'
>>>                [0, 1, 2], # Adaptive Standard
>>>                [1, 2, 3, 80, 90], # Category
>>>                [0, 1, 2, 3], # Comfort Mode
>>>                [0, 1, 2], # HVAC Mode
>>>                [0, 1], # Ventilation Control
>>>                [0, 1, 2], # VSToffset
>>>                [0, 1, 2], # MinOToffset
>>>                [10, 20, 30], # MaxWindSpeed
>>>                0, # ASTtol start
>>>                2, # ASTtol end
>>>                0.25, # ASTtol steps
>>>                'standard' # Name Suffix: for example, just in case you want to clarify the outputs
>>>                )
```
Each argument is explained below:

- Adaptive Standard: refers to the adaptive thermal comfort model to be applied. Enter 0 for CTE, 1 for EN16798-1 and 2 for ASHRAE 55. For example, if you enter '0 1 2', you'll get IDFs for all the models. If you don't enter any number, or if some of the numbers entered are not 0, 1 or 2, it'll ask you to enter the numbers again.

- Category:  refers to the category of the adaptive thermal comfort model applied. Enter 1 for CAT I, 2 for CAT II,  and 3 for CAT III of EN16798; 80 for 80% acceptability and 90 for 90% acceptability in ASHRAE55. So, for example, if you enter '1 2 3 80 90' you'll get all categories for EN16798 and ASHRAE55 models, or if you enter '1 2 80' you'll get categories 1 and 2 for EN16798, and 80% acceptability for ASHRAE55. Please note that the Category values must be consistent with the Adaptive Standard values previously entered. If, for instance, you enter '1' in the Adaptive Standard value (means you're asking for EN16798 model), but then enter '80' or '90' in the Category value (which are categories used in ASHRAE55), you won't get the results you want.

- Comfort Mode: refers to the comfort modes, which can be explained as follows:
In static mode, static (or PMV-based) setpoint temperatures are applied all the time; in OUT-CTE mode, adaptive setpoint temperatures are applied as long as the adaptive comfort model is applicable; otherwise, CTE (which is the Spanish Technical Building Code) setpoint temperatures (which are static) are applied; in OUT-SEN16798/SASHRAE55, adaptive setpoint temperatures are applied as long as the adaptive comfort model is applicable; otherwise, EN16798-1 or ASHRAE 55 static setpoint temperatures are applied; and in OUT-AEN16798/AASHRAE55, adaptive setpoint temperatures are applied as long as the adaptive comfort model is applicable; otherwise, EN16798-1 or ASHRAE 55 highest and lowest adaptive comfort limits are horizontally extended. Please refer to the research article https://www.mdpi.com/1996-1073/12/8/1498 for more information. Therefore, enter 0 for Static; 1 for OUT-CTE, 2 for OUT-SEN16798/SASHRAE55 and 3 for OUT-AEN16798/AASHRAE55). For example, if you enter '0 1 2 3' you'll be getting all different Comfort Modes.

- HVAC Mode: refers to the HVAC mode applied. Enter 0 for Fully Air-conditioned, 1 for Naturally ventilated and/or 2 for Mixed Mode. Please note that Calculated natural ventilation must be enabled so that Mixed Mode works. So, for example, if you enter '0 1 2' you'll be getting all HVAC modes, or if you just enter '0 1' you'll be getting just Fully Air-conditioned and Naturally ventilated.

- Ventilation Control: refers to the ventilation control, only used in Mixed Mode (HVAC Mode '2'). If you enter '0', ventilation will be allowed if operative temperature exceeds neutral temperature (also known as comfort temperature); if you enter '1', ventilation will be allowed if operative temperature exceeds the upper comfort limit. In other words, sets the value of the neutral temperature or the upper comfort limit to the Ventilation Setpoint Temperature (VST). Either way, if you enter '0 1' you'll be getting both ventilation control modes.

- VSToffset: stands for Ventilation Setpoint Temperature (VST) offset, again only used in Mixed Mode (HVAC Mode '2'). Applies the entered values as an offset to the VST, in Celsius degrees. Values entered can be positive or negative float or integers, and must be space-separated. For example, if you enter '-2 -1 0 1 2' you'll be getting offsets of -2°C, -1°C, 0°C, 1°C and 2°C to the VST. If you don't enter any number, it'll be used '0' as the default value.

- MinOToffset: stands for Minimum Outdoor Temperature offset, again only used in Mixed Mode (HVAC Mode '2'). Sets the minimum outdoor temperature an offset to the heating setpoint temperature. For example, if you enter '1' (please, note that the numbers must be positive), ventilation won't be allowed if outdoor temperature falls below 1°C below the heating setpoint, in order to prevent from entering excessive cold. Therefore, below said limit, windows are closed and, if needed, air conditioning starts to work. Entered values can be float or integers, but always positive numbers, and must be space-separated. For example, if you enter '0 1 2' you'll be getting offsets of 0°C, 1°C and 2°C to the heating setpoint temperature. If you don't enter any number, it'll be used '50' as the default value (that is 50°C below heating setpoint temperature, and therefore no limit is applied).

- MaxWindSpeed: stands for maximum wind speed, again only used in Mixed Mode (HVAC Mode '2'). Sets the maximum wind speed in which ventilation is allowed, in m/s. Therefore, if you enter '20', ventilation won't be allowed if wind speed is greater than 20 m/s. Entered values can be float or integers, but always positive numbers, and must be space-separated. For example, if you enter '5 10 15 20' you'll be getting different IDFs with maximum wind speeds of 5 m/s, 10 m/s, 15 m/s and 20 m/s. If you don't enter any number, it'll be used '50' as the default value (that is 50 m/s, and therefore no limit is applied).

- ASTtol: stands for Adaptive Setpoint Temperature tolerance. It applies the number that you enter as a tolerance for the adaptive heating and cooling setpoint temperatures. The  original problem was that, if we assigned the adaptive setpoint straight to the comfort limit (i.e. you enter '0' for ASTtol), there were a few hours that fell outside the comfort zone because of the error in some decimals in the simulation of the operative temperature. Therefore, the original purpose of this feature is to control that all hours are comfortable hours (i.e. operative temperature falls within the comfort zone), and we can make that sure by considering a little tolerance of 0.10 °C. For example, say that adaptive cooling and heating setpoints are originally 29.5 and 21.5°C at some day; if you enter '1' for ASTtol, then the setpoints would be modified to 28.5 and 22.5°C (1°C below original cooling setpoint, and 1°C above original heating setpoint). The function will create a sequence of numbers based on the entered values. So, numbers must be entered in 3 stages: first, the start of the sequence; second, the end of the sequence, and third, the steps. So for example, if you enter '0' for the start, '1' for the end, and '0.25' for the steps, you would be getting ASTtol values of 0°C, 0.25°C, 0.5°C, 0.75°C and 1°C. If you don't enter any number, it'll be used '0.1' as the default value (as previously said, to make sure all hours are comfortable hours), and you would be getting only one variation of 0.1°C.

So, below you can see a sample name of an IDF created by using ACCIM's MultipleZone functions. The package takes the original IDF file as a reference, saves a copy, run all the functions so that setpoint temperatures are transformed from static to adaptive, an changes its name based on the values previously entered:

__TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[standard__

where:

- 'TestModel_MultipleZone' is the name of the original IDF, which is copied with the suffix '_pymod' so that the original file stays unmodified.

- AS refers to the Adaptive Standard, and it's followed by the adaptive thermal comfort applied (could be 'CTE', 'EN16798' or 'ASHRAE55').

- CA refers to the Category, which could be 1, 2 or 3 if AS is EN16798, or 80 or 90 if AS is ASHRAE55.

- CM refers to the Comfort Mode, which could be 0 (Static), 1 (OUT-CTE), 2 (OUT-SEN16798 or OUT-SASHRAE55), OR 3 (OUT-AEN16798 or OUT-AASHRAE55).
- HM refers to the HVAC Mode, which could be 0 (Full air conditioning), 1 (Naturally ventilated), or 2 (Mixed Mode).

- VC refers to the Ventilation Control, which could be 0 (ventilates above neutral temperature), or 1 (ventilates above upper comfort limit).

- VO refers to the Ventilation setpoint temperature offset, which could be any number, float or integer, positive or negative.

- MT refers to the Minimum Outdoor Temperature offset, which could be any number, float or integer, but always positive number.

- MW refers to the Maximum Wind Speed, which could be any number, float or integer, but always positive number.

- AT refers to the Adaptive Setpoint Temperature offset, which could be any number, float or integer, but always positive number. Please remember this number comes from a 3-stage process (refer to the explanation above).

- 'standard' is the suffix, which can be whatever you want. For example, this allows you to make a for loop with 'spandard', 'simplified' and 'timestep' and run the simulations with all type of outputs.

If some inputs are not used or don't make sense, you'll be able to se an 'X' in the output IDF file. For example, if you use CTE as Adaptive Standard, then the inputs for Category and Comfort Mode (which are only for EN16798-1 and ASHRAE 55) are not used in the process, and the output IDF would contain in its name 'AS_CTE[CA_X[CM_X'. Another similar case occurs if you use Full air-conditioning HVAC Mode (i.e. enter '0' for HVAC Mode), where the output IDF would contain in its name '[HM_0[VC_X[VO_X[MT_X[MW_X'.

### SingleZone functions

Just as previously explained for MultipleZones scripts, if you run `accis.addAccis('sz', whateverOutputs, whateverEPversion)`, you will be ask in the prompt to enter a few values separated by space to set up the desired IDFs. However, you can also skip the command prompt process by running accis directly including the arguments in the function, whose usage would be:
```
>>> accis.addAccis(str, # ScriptType: 'multiplezone' or 'mz', 'singlezone' or 'sz'
>>>                str, # Outputs: 'simplified', 'standard' or 'timestep'
>>>                str, # EP version: 'ep91' or 'ep94'
>>>                list, # Adaptive Standard
>>>                list, # Category
>>>                list, # Comfort Mode
>>>                float, # ASTtol start
>>>                float, # ASTtol end
>>>                float, # ASTtol steps
>>>                str # NameSuffix: some text you might want to add at the end of the output IDF file name
>>>                )
```
Some example of the usage could be:
```
>>> accis.addAccis('sz', # ScriptType: 'multiplezone' or 'mz', 'singlezone' or 'sz'
>>>                'standard', # Outputs: 'simplified', 'standard' or 'timestep'
>>>                'ep94', # EP version: 'ep91' or 'ep94'
>>>                [0, 1, 2], # Adaptive Standard
>>>                [1, 2, 3, 80, 90], # Category
>>>                [0, 1, 2, 3], # Comfort Mode
>>>                0, # ASTtol start
>>>                2, # ASTtol end
>>>                0.25, # ASTtol steps
>>>                'standard' # Name Suffix: for example, just in case you want to clarify the outputs
>>>                )
```
Each argument is explained below:

- Adaptive Standard: same as explained above; please refer to MultipleZone functions.

- Category: same as explained above; please refer to MultipleZone functions.

- Comfort Mode: same as explained above; please refer to MultipleZone functions.

- ASTtol: same as explained above; please refer to MultipleZone functions.

You can see these are the same inputs from MultipleZone functions, however, since some of them were only necessary for Mixed Mode and SingleZone functions work only with Full air-conditioning mode, these are omitted in this branch.

So, below you can see a sample name of an IDF created by using ACCIM's SingleZone functions. The package takes the original IDF file as a reference, saves a copy, run all the functions so that setpoint temperatures are transformed from static to adaptive, an changes its name based on the values previously entered:

__TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0.1[standard__

where (same as previously explained in MultipleZone functions):

- 'TestModel_MultipleZone' is the name of the original IDF, which is copied with the suffix '_pymod' so that the original file stays unmodified.

- AS refers to the Adaptive Standard, and it's followed by the adaptive thermal comfort applied (could be 'CTE', 'EN16798' or 'ASHRAE55').

- CA refers to the Category, which could be 1, 2 or 3 if AS is EN16798, or 80 or 90 if AS is ASHRAE55.

- CM refers to the Comfort Mode, which could be 0 (Static), 1 (OUT-CTE), 2 (OUT-SEN16798 or OUT-SASHRAE55), OR 3 (OUT-AEN16798 or OUT-AASHRAE55).

- 'standard' is the suffix, which can be whatever you want. For example, this allows you to make a for loop with 'spandard', 'simplified' and 'timestep' and run the simulations with all type of outputs.
