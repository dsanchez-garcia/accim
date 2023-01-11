# Examples

You can see an example below. The input file is included within 'accim\sample files\' folder.


Say you have an IDF in some folder, called 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220.idf'. So, let's run the functions to get the energy models with adaptive setpoint temperatures.

```
>>> from accim.sim import accis
>>> accis.addAccis()
```
When we hit enter, we'll be asked to enter some information regarding the ScriptType, the Outputs and the EnergyPlus version:
```
Enter the ScriptType (
for VRFsystem with full air-conditioning mode: vrf_ac;
for VRFsystem with mixed-mode: vrf_mm;
for ExistingHVAC with mixed mode: ex_mm;
for ExistingHVAC with full air-conditioning mode: ex_ac
): vrf_mm
Do you want to keep the existing outputs (true or false)?: false
Enter the Output type (standard, simplified or existing): standard
Enter the Output frequencies separated by space (timestep, hourly, daily, monthly, runperiod): hourly runperiod
Enter the EnergyPlus version (9.1 to 22.2): 22.2
Enter the Temperature Control method (temperature or pmv): temperature
```
When we hit enter, it's going to add all the EnergyPlus objects needed:
```
Basic input data:
ScriptType is: vrf_mm
Output type is: standard
Output frequencies are: 
['hourly', 'runperiod']
EnergyPlus version is: 22.2
Temperature Control method is: temperature

=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================

Starting with file:
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220
IDD location is: C:\EnergyPlusV22-2-0\Energy+.idd
The occupied zones in the model TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220 are:
BLOCK1:ZONE2
BLOCK1:ZONE1
The windows in the model TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220 are:
Block1_Zone2_Wall_3_0_0_0_0_0_Win
Block1_Zone2_Wall_4_0_0_0_0_0_Win.
.
.
Added - BLOCK1_ZONE1 VRF Indoor Unit DX Cooling Coil Output:Variable data
Added - BLOCK1_ZONE1 VRF Indoor Unit DX Heating Coil Output:Variable data
IDF has been saved
Ending with file:
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220

=======================END OF GENERIC IDF FILE GENERATION PROCESS=======================

The following IDFs will not work, and therefore these will be deleted:
None
```
And then ask us to enter the required information to generate the output IDF files (you can omit some of it by hitting enter without entering any value):
```
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
1 = CAT I;
2 = CAT II;
3 = CAT III;
80 = 80% ACCEPT;
85 = 85% ACCEPT;
90 = 90% ACCEPT;
Please refer to the full list of setpoint temperatures at https://github.com/dsanchez-garcia/accim/blob/master/docs/images/full_table.png
): 2 3 85 90
          Are you sure the numbers are correct? [y or [] / n]: 
For the comfort standard 1 = INT EN16798, the available ComfMods you can choose are: 
0 = EN16798 Static setpoints
1 = EN16798 Adaptive setpoints when applicable, otherwise CTE
2 = EN16798 Adaptive setpoints when applicable, otherwise EN16798 Static setpoints
3 = EN16798 Adaptive setpoints when applicable, otherwise EN16798 Adaptive setpoints horizontally extended
For the comfort standard 2 = INT ASHRAE55, the available ComfMods you can choose are: 
0 = ASHRAE 55 Static setpoints (calculated with Clima Tool)
1 = ASHRAE 55 Adaptive setpoints when applicable, otherwise CTE
2 = ASHRAE 55 Adaptive setpoints when applicable, otherwise ASHRAE 55 Static setpoints
3 = ASHRAE 55 Adaptive setpoints when applicable, otherwise ASHRAE 55 Adaptive setpoints horizontally extended
For the comfort standard 7 = IND IMAC C NV, the available ComfMods you can choose are: 
0 = Indian Building Code Static setpoints
1 = IMAC C NV Model Adaptive setpoints when applicable, otherwise Indian Building Code Static setpoints
2 = IMAC C NV Model Adaptive setpoints when applicable, otherwise ASHRAE 55 Static setpoints
3 = IMAC C NV Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended
Enter the Comfort Mode numbers separated by space (
0 = Static;
1, 2, 3 = Adaptive;
Please refer to the full list of setpoint temperatures at https://github.com/dsanchez-garcia/accim/blob/master/docs/images/full_table.png
): 0 3
          Are you sure the numbers are correct? [y or [] / n]: 
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
          Are you sure the number is correct? [y or [] / n]: 1
Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): 1
          Are you sure the number is correct? [y or [] / n]: 
Enter the multiplier number for Ventilation Opening Factor (any number larger than 0): 0.2
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
```
Afterwards, ACCIS will let us know which the output IDFs are going to be, the total number of them and will ask for our confirmation to proceed:
```
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_2[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_2[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_2[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_2[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_3[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_3[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_3[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_3[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT ASHRAE55[CA_90[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT ASHRAE55[CA_90[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT ASHRAE55[CA_90[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT ASHRAE55[CA_90[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_85[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_85[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_85[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_85[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_90[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_90[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_90[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_90[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
And the total number of output IDFs is going to be 20
Do you still want to run ACCIS? [y/n]: y
```
If we entered `n`, the whole process would shut down. Otherwise, if we entered 'y', the generation of output IDF files would start, and ACCIS would print on screen each output IDF name as it generates it. 
As you can see, we are going to use the EN16798-1, ASHRAE 55 and IMAC Commercial for naturally ventilated buildings, categories 2 and 3 for EN16798, 90% acceptability levels for ASHRAE 55, 85 and 90% acceptability levels for IMAC C NV, all with ComfMod 0 (with static setpoint temperatures) and 3 (with adaptive setpoint temperatures when the model is applicable, otherwise horizontally extending the adaptive setpoint temperatures), Mixed Mode, and we just went ahead with the remaining default values.
```
Generating the following output IDF files:
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_2[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_2[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_2[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_2[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_3[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_3[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_3[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT EN16798[CA_3[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT ASHRAE55[CA_90[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT ASHRAE55[CA_90[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT ASHRAE55[CA_90[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_INT ASHRAE55[CA_90[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_85[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_85[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_85[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_85[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_90[CM_0[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_90[CM_0[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_90[CM_3[HM_2[VC_2[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2220[CS_IND IMAC C NV[CA_90[CM_3[HM_2[VC_3[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf

=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================
```
Afterwards, you just need to run the simulation. In my opinion, The easiest and quickest way to do it is by using EP-Launch. Once you have run the simulations you need, you'll get the files you usually get when you run any simulation, including the hourly results on a CSV file.
