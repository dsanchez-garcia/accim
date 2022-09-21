# Examples

You can see an example below. All input and output IDFs are included within 'accim\sample files\' folder.


Say you have an IDF in some folder, called 'TestModel_onlyGeometryForVRFsystem.idf'. So, let's run the functions to get the energy models with adaptive setpoint temperatures.

```
>>> from accim.sim import accis
>>> accis.addAccis()
```
When we hit enter, we'll be asked to enter some information regarding the ScriptType, the Outputs and the EnergyPlus version:
```
Enter the ScriptType (for VRFsystem: vrf; for ExistingHVAC with mixed mode: ex_mm; or for ExistingHVAC only with full air-conditioning mode: ex_ac): vrf
Enter the Output (standard, simplified or timestep): standard
Enter the EnergyPlus version (ep91 to ep96): ep96
Enter the Temperature Control method (temperature or pmv): temperature
```
When we hit enter, it's going to add all the EnergyPlus objects needed, and afterwards ask us to enter the required information:
```
ScriptType is: vrf
Outputs are: standard
EnergyPlus version is: ep96
Temperature Control method is: temperature

=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================

Starting with file:
TestModel_onlyGeometryForVRFsystem
IDD location is: C:/EnergyPlusV9-6-0/Energy+.idd
The occupied zones in the model TestModel_onlyGeometryForVRFsystem are:
Block1:Zone2
Block1:Zone1
.
.
.
Added - Block2_Zone1 VRF Indoor Unit DX Cooling Coil Output:Variable data
Added - Block2_Zone1 VRF Indoor Unit DX Heating Coil Output:Variable data
IDF has been saved
Ending with file:
TestModel_onlyGeometryForVRFsystem

=======================END OF GENERIC IDF FILE GENERATION PROCESS=======================

The following IDFs will not work, and therefore these will be deleted:
None

=======================START OF OUTPUT IDF FILES GENERATION PROCESS=======================

The information you will be required to enter below will be used to generate the customised output IDFs:
Enter the Comfort Standard numbers separated by space (
0 = CTE;
1 = EN16798-1;
2 = ASHRAE 55;
3 = JPN·Rijal;
4 = GBT50785·Cold;
5 = GBT50785·HotMild;
6 = CHN·Yang;
7 = IMAC·C·NV;
8 = IMAC·C·MM;
9 = IMAC·R·7DRM;
10 = IMAC·R·30DRM;
11 = IND·Dhaka;
12 = ROM·Udrea;
13 = AUS·Williamson;
14 = AUS·DeDear;
15 = BRA·Rupp·NV;
16 = BRA·Rupp·AC;
): 1
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Category numbers separated by space (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 85 = 85% ACCEPT; 90 = 90% ACCEPT; Please refer to the full list of setpoint temperatures at https://github.com/dsanchez-garcia/accim/blob/master/docs/images/full_table.png): 1 2 3
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Comfort Mode numbers separated by space (0 = Static; 1, 2, 3 = Adaptive; Please refer to the full list of setpoint temperatures at https://github.com/dsanchez-garcia/accim/blob/master/docs/images/full_table.png): 0 1 2 3
          Are you sure the numbers are correct? [y or [] / n]:
Enter the HVAC Mode numbers separated by space (0 = Fully Air-conditioned; 1 = Naturally ventilated; 2 = Mixed Mode): 2
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Ventilation Control numbers separated by space (0 = Ventilates above neutral temperature; 1 = Ventilates above upper comfort limit): 0
          Are you sure the numbers are correct? [y or [] / n]:
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
The list of output IDFs is going to be:
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
And the total number of output IDFs is going to be 12
Do you still want to run ACCIS? [y/n]: y
```
If we entered `n`, the whole process would shut down. Otherwise, if we entered 'y', the generation of output IDF files would start, and ACCIS would print on screen each output IDF name as it generates it. 
As you can see, we are going to use the EN16798-1, all categories (1, 2 and 3), all Comfort Modes, Mixed Mode, and we just went ahead with the remaining default values.
```
Generating the following output IDF files:
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf

=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================
```
If you enter `exit()` to quit python and enter `dir` on windows command line, you'll be able to see the output IDFs accim has created:
```
25/02/2021  19:58           234,027 TestModel_onlyGeometryForVRFsystem.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_2[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf
12/03/2021  07:57           500,044 TestModel_onlyGeometryForVRFsystem[CS_EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf

```
Afterwards, you just need to run the simulation. In my opinion, The easiest and quickest way to do it is by using EP-Launch. Once you have run the simulations you need, you'll get the files you usually get when you run any simulation, including the hourly results on a CSV file.
