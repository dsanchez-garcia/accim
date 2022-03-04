"""Add EnergyPlus objects in common to both ExistingHVAC and VRFsystem."""


def setComfFieldsPeople(self, EnergyPlus_version: str = None, verboseMode: bool = True):
    """
    Amend PEOPLE objects so that accim can work.

    Copy existing PEOPLE objects and adds AdaptiveASH55 and AdaptiveCEN15251
    to Thermal Comfort Model types 1 and 2 fields of the existing People
    objects.
    """
    ppl = ([people for people in self.idf1.idfobjects['PEOPLE']])
    for i in range(len(ppl)):
        if EnergyPlus_version.lower() == 'ep96':
            self.idf1.newidfobject(
                'PEOPLE',
                Name=ppl[i].Name,
                Zone_or_ZoneList_or_Space_or_SpaceList_Name=ppl[i].Zone_or_ZoneList_or_Space_or_SpaceList_Name,
                Number_of_People_Schedule_Name=ppl[i].Number_of_People_Schedule_Name,
                Number_of_People_Calculation_Method=ppl[i].Number_of_People_Calculation_Method,
                Number_of_People=ppl[i].Number_of_People,
                People_per_Floor_Area=ppl[i].People_per_Floor_Area,
                Floor_Area_per_Person=ppl[i].Floor_Area_per_Person,
                Fraction_Radiant=ppl[i].Fraction_Radiant,
                Sensible_Heat_Fraction=ppl[i].Sensible_Heat_Fraction,
                Activity_Level_Schedule_Name=ppl[i].Activity_Level_Schedule_Name,
                Carbon_Dioxide_Generation_Rate=ppl[i].Carbon_Dioxide_Generation_Rate,
                Enable_ASHRAE_55_Comfort_Warnings=ppl[i].Enable_ASHRAE_55_Comfort_Warnings,
                Mean_Radiant_Temperature_Calculation_Type=ppl\
                    [i].Mean_Radiant_Temperature_Calculation_Type,
                Surface_NameAngle_Factor_List_Name=ppl[i].Surface_NameAngle_Factor_List_Name,
                Work_Efficiency_Schedule_Name=ppl[i].Work_Efficiency_Schedule_Name,
                Clothing_Insulation_Calculation_Method=ppl\
                    [i].Clothing_Insulation_Calculation_Method,
                Clothing_Insulation_Calculation_Method_Schedule_Name=ppl\
                    [i].Clothing_Insulation_Calculation_Method_Schedule_Name,
                Clothing_Insulation_Schedule_Name=ppl[i].Clothing_Insulation_Schedule_Name,
                Air_Velocity_Schedule_Name=ppl[i].Air_Velocity_Schedule_Name,
                Thermal_Comfort_Model_1_Type='AdaptiveASH55',
                Thermal_Comfort_Model_2_Type='AdaptiveCEN15251',
                Thermal_Comfort_Model_3_Type='',
                Thermal_Comfort_Model_4_Type='',
                Thermal_Comfort_Model_5_Type='',
                )
            firstpeopleobject = self.idf1.idfobjects['PEOPLE'][0]
            self.idf1.removeidfobject(firstpeopleobject)
        else:
            self.idf1.newidfobject(
                'PEOPLE',
                Name=ppl[i].Name,
                Zone_or_ZoneList_Name=ppl[i].Zone_or_ZoneList_Name,
                Number_of_People_Schedule_Name=ppl[i].Number_of_People_Schedule_Name,
                Number_of_People_Calculation_Method=ppl[i].Number_of_People_Calculation_Method,
                Number_of_People=ppl[i].Number_of_People,
                People_per_Zone_Floor_Area=ppl[i].People_per_Zone_Floor_Area,
                Zone_Floor_Area_per_Person=ppl[i].Zone_Floor_Area_per_Person,
                Fraction_Radiant=ppl[i].Fraction_Radiant,
                Sensible_Heat_Fraction=ppl[i].Sensible_Heat_Fraction,
                Activity_Level_Schedule_Name=ppl[i].Activity_Level_Schedule_Name,
                Carbon_Dioxide_Generation_Rate=ppl[i].Carbon_Dioxide_Generation_Rate,
                Enable_ASHRAE_55_Comfort_Warnings=ppl[i].Enable_ASHRAE_55_Comfort_Warnings,
                Mean_Radiant_Temperature_Calculation_Type=ppl\
                    [i].Mean_Radiant_Temperature_Calculation_Type,
                Surface_NameAngle_Factor_List_Name=ppl[i].Surface_NameAngle_Factor_List_Name,
                Work_Efficiency_Schedule_Name=ppl[i].Work_Efficiency_Schedule_Name,
                Clothing_Insulation_Calculation_Method=ppl\
                    [i].Clothing_Insulation_Calculation_Method,
                Clothing_Insulation_Calculation_Method_Schedule_Name=ppl\
                    [i].Clothing_Insulation_Calculation_Method_Schedule_Name,
                Clothing_Insulation_Schedule_Name=ppl[i].Clothing_Insulation_Schedule_Name,
                Air_Velocity_Schedule_Name=ppl[i].Air_Velocity_Schedule_Name,
                Thermal_Comfort_Model_1_Type='AdaptiveASH55',
                Thermal_Comfort_Model_2_Type='AdaptiveCEN15251',
                Thermal_Comfort_Model_3_Type='',
                Thermal_Comfort_Model_4_Type='',
                Thermal_Comfort_Model_5_Type='',
                )
            firstpeopleobject = self.idf1.idfobjects['PEOPLE'][0]
            self.idf1.removeidfobject(firstpeopleobject)
    ppl = ([people for people in self.idf1.idfobjects['PEOPLE']])
    if verboseMode:
        print('The people objects in the model have been amended.')
        # print(*peoplelist,sep="\n")
    del ppl, firstpeopleobject


def saveaccim(self, verboseMode: bool = True):
    """Save IDF."""
    self.idf1.save()
    if verboseMode:
        print('IDF has been saved')
