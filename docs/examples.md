# Examples

## MultipleZones functions

Say you have an IDF in some folder, called 'TestModel_Calculated.idf'. So, let's run the functions to get the energy models with adaptive setpoint temperatures. Besides, we can run it with static setpoint temperatures to see the differences between these.

```
>>> from accim.sim import accis
>>> dir(accis)
['__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__', 'addAccisMultipleZoneEp91', 'addAccisMultipleZoneEp94', 'addAccisMultipleZoneSimplifiedEp91', 'addAccisMultipleZoneSimplifiedEp94', 'addAccisMultipleZoneTimestepEp91', 'addAccisMultipleZoneTimestepEp94', 'addAccisSingleZoneEp91', 'addAccisSingleZoneEp94', 'addAccisSingleZoneSimplifiedEp91', 'addAccisSingleZoneSimplifiedEp94', 'addAccisSingleZoneTimestepEp91', 'addAccisSingleZoneTimestepEp94']
>>> accis.addAccisMultipleZoneEp94()
```
When we hit enter, it's going to add all the EnergyPlus objects needed, and afterwards ask us to enter the required information:

```
Enter the Adaptive Standard numbers separated by space (0 = CTE; 1 = EN16798-1; 2 = ASHRAE 55): 1
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Category numbers separated by space (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 90 = 90% ACCEPT): 1 2 3
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Comfort Mode numbers separated by space (0 = Static; 1 = OUT-CTE; 2 = OUT-SEN16798/SASHRAE55; 3 = OUT-AEN16798/AASHRAE55): 0 3
          Are you sure the numbers are correct? [y or [] / n]:
Enter the HVAC Mode numbers separated by space (0 = Fully Air-conditioned; 1 = Naturally ventilated; 2 = Mixed Mode): 2
          Are you sure the numbers are correct? [y or [] / n]:
Enter the Ventilation Control numbers separated by space (0 = Ventilates above neutral temperature; 1 = Ventilates above upper comfort limit): 0
          Are you sure the numbers are correct? [y or [] / n]:
Enter the VSToffset numbers separated by space (if omited, will be 0):
          Are you sure the numbers are correct? [y or [] / n]:
Enter the MinOToffset numbers separated by space (if omited, will be 50):
          Are you sure the numbers are correct? [y or [] / n]:
Enter the MaxWindSpeed numbers separated by space (if omited, will be 50):
          Are you sure the numbers are correct? [y or [] / n]:
Enter the ASTtol value from (if omited, will be 0.1):
          Are you sure the numbers are correct? [y or [] / n]:
Enter the ASTtol value to (if omited, will be 0.1):
          Are you sure the numbers are correct? [y or [] / n]:
Enter the ASTtol value steps (if omited, will be 0.1):
          Are you sure the numbers are correct? [y or [] / n]:
```
As you can see, we are going to use the EN16798-1, all categories (1, 2 and 3), Comfort Modes 0 (i.e. static) and 3 (i.e. adaptive, OUT-AEN16798), Mixed Mode, and we just went ahead with the remaining default values.
If you enter `exit()` to quit python and enter `dir` on windows command line, you'll be able to see the output IDFs accim has created:
```
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---l        20/01/2021     20:11         234001 TestModel_Calculated.idf
-a---l        25/02/2021     19:02         500044 TestModel_Calculated_pymod[AS_EN16798[CA_1[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
-a---l        25/02/2021     19:02         500044 TestModel_Calculated_pymod[AS_EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
-a---l        25/02/2021     19:02         500044 TestModel_Calculated_pymod[AS_EN16798[CA_2[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
-a---l        25/02/2021     19:02         500044 TestModel_Calculated_pymod[AS_EN16798[CA_2[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
-a---l        25/02/2021     19:02         500044 TestModel_Calculated_pymod[AS_EN16798[CA_3[CM_0[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
-a---l        25/02/2021     19:02         500044 TestModel_Calculated_pymod[AS_EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1.idf
```
Afterwards, you just need to run the simulation. In my opinion, The easiest and quickest way to do it is by using EP-Launch. Once you have run the simulations you need, you'll get the files you usually get when you run any simulation, including the hourly results on a CSV file. You can see in the image below the differences between using adaptive and static EN16798-1 setpoint temperatures (i.e. Category 3, Comfort Modes 0 and 3)

<img src="images\simulationResults.png" width="1000">

## SingleZone functions
