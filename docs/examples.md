# Examples

You can see some examples below with MultipleZones and SingleZone functions. All input and output IDFs are included within 'accim\sample files\' folder.

## MultipleZones functions

Say you have an IDF in some folder, called 'TestModel_MultipleZone.idf'. So, let's run the functions to get the energy models with adaptive setpoint temperatures.

```
>>> from accim.sim import accis
>>> accis.addAccis()
```
When we hit enter, we'll be asked to enter some information regarding the ScriptType, the Outputs and the EnergyPlus version:
```
Enter the ScriptType (MultipleZone or mz, or SingleZone or sz): mz
Enter the Output (Standard, Simplified or Timestep): standard
Enter the EnergyPlus version (Ep91 to Ep95): ep95
```
When we hit enter, it's going to add all the EnergyPlus objects needed, and afterwards ask us to enter the required information:
```
=======================START OF PROCESS=======================

Starting with file:
TestModel_MultipleZone
.
.
.
IDF has been saved
Ending with file:
TestModel_MultipleZone

=======================END OF PROCESS=======================

Enter the Adaptive Standard numbers separated by space (0 = CTE; 1 = EN16798-1; 2 = ASHRAE 55): 1
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Category numbers separated by space (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 90 = 90% ACCEPT): 1 2 3
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Comfort Mode numbers separated by space (0 = Static; 1 = OUT-CTE; 2 = OUT-SEN16798/SASHRAE55; 3 = OUT-AEN16798/AASHRAE55): 0 1 2 3
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
TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_2[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_2[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_2[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_2[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_3[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_3[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_3[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
TestModel_MultipleZone_pymod[AS_EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
And the total number of output IDFs is going to be 12
Do you still want to run ACCIS? [y/n]:y
```
If we entered `n`, the whole process would shut down. Otherwise, if we entered 'y', the generation of output IDF files would start, and ACCIS would print on screen each output IDF name as it generates it. 
As you can see, we are going to use the EN16798-1, all categories (1, 2 and 3), all Comfort Modes, Mixed Mode, and we just went ahead with the remaining default values.
If you enter `exit()` to quit python and enter `dir` on windows command line, you'll be able to see the output IDFs accim has created:
```
25/02/2021  19:58           234,027 TestModel_MultipleZone.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_2[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_2[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_2[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_2[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_3[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_3[CM_1[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_3[CM_2[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
12/03/2021  07:57           500,044 TestModel_MultipleZone_pymod[AS_EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf

```
Afterwards, you just need to run the simulation. In my opinion, The easiest and quickest way to do it is by using EP-Launch. Once you have run the simulations you need, you'll get the files you usually get when you run any simulation, including the hourly results on a CSV file.

## SingleZone functions

In case of SingleZone functions, it's pretty much the same thing:

Say you have an IDF in some folder, called 'TestModel_SingleZone.idf'. So, let's run the functions to get the energy models with adaptive setpoint temperatures.

```
>>> from accim.sim import accis
>>> accis.addAccis()
```
When we hit enter, we'll be asked to enter some information regarding the ScriptType, the Outputs and the EnergyPlus version:
```
Enter the ScriptType (MultipleZone or mz, or SingleZone or sz): sz
Enter the Output (Standard, Simplified or Timestep): standard
```
When we hit enter, it's going to add all the EnergyPlus objects needed, and afterwards ask us to enter the required information:
```
=======================START OF PROCESS=======================

Starting with file:
TestModel_SingleZone
.
.
.
IDF has been saved
Ending with file:
TestModel_SingleZone

=======================END OF PROCESS=======================

Enter the Adaptive Standard numbers separated by space (0 = CTE; 1 = EN16798-1; 2 = ASHRAE 55): 1
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Category numbers separated by space (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 90 = 90% ACCEPT): 1 2 3
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Comfort Mode numbers separated by space (0 = Static; 1 = OUT-CTE; 2 = OUT-SEN16798/SASHRAE55; 3 = OUT-AEN16798/AASHRAE55): 0 1 2 3
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
TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_0[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_1[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_2[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_0[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_1[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_2[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_3[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_3[CM_0[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_3[CM_1[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_3[CM_2[AT_0.1.idf
TestModel_SingleZone_pymod[AS_EN16798[CA_3[CM_3[AT_0.1.idf
And the total number of output IDFs is going to be 12
Do you still want to run ACCIS? [y/n]:
```
If we entered `n`, the whole process would shut down. Otherwise, if we entered 'y', the generation of output IDF files would start, and ACCIS would print on screen each output IDF name as it generates it. 
As you can see, we are going to use the EN16798-1, all categories (1, 2 and 3), all Comfort Modes, and we just went ahead with the remaining default values.
If you enter `exit()` to quit python and enter `dir` on windows command line, you'll be able to see the output IDFs accim has created:
```
25/02/2021  20:18            76,936 TestModel_SingleZone.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_0[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_1[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_2[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_1[CM_3[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_0[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_1[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_2[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_2[CM_3[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_3[CM_0[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_3[CM_1[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_3[CM_2[AT_0.1.idf
12/03/2021  08:11           114,617 TestModel_SingleZone_pymod[AS_EN16798[CA_3[CM_3[AT_0.1.idf
```

