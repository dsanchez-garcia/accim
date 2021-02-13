"""Add EnergyPlus objects in common to both SingleZone and MultipleZone."""


def setComfFieldsPeople(self):
    """
    Amend PEOPLE objects so that accim can work.

    Copy existing PEOPLE objects and adds AdaptiveASH55 and AdaptiveCEN15251
    to Thermal Comfort Model types 1 and 2 fields of the existing People
    objects.
    """
    peoplelist = [people for people in self.idf1.idfobjects["PEOPLE"]]
    for i in range(len(peoplelist)):
        self.idf1.newidfobject(
            "PEOPLE",
            Name=peoplelist[i].Name,
            Zone_or_ZoneList_Name=peoplelist[i].Zone_or_ZoneList_Name,
            Number_of_People_Schedule_Name=peoplelist[i].Number_of_People_Schedule_Name,
            Number_of_People_Calculation_Method=peoplelist[
                i
            ].Number_of_People_Calculation_Method,
            Number_of_People=peoplelist[i].Number_of_People,
            People_per_Zone_Floor_Area=peoplelist[i].People_per_Zone_Floor_Area,
            Zone_Floor_Area_per_Person=peoplelist[i].Zone_Floor_Area_per_Person,
            Fraction_Radiant=peoplelist[i].Fraction_Radiant,
            Sensible_Heat_Fraction=peoplelist[i].Sensible_Heat_Fraction,
            Activity_Level_Schedule_Name=peoplelist[i].Activity_Level_Schedule_Name,
            Carbon_Dioxide_Generation_Rate=peoplelist[i].Carbon_Dioxide_Generation_Rate,
            Enable_ASHRAE_55_Comfort_Warnings=peoplelist[
                i
            ].Enable_ASHRAE_55_Comfort_Warnings,
            Mean_Radiant_Temperature_Calculation_Type=peoplelist[
                i
            ].Mean_Radiant_Temperature_Calculation_Type,
            Surface_NameAngle_Factor_List_Name=peoplelist[
                i
            ].Surface_NameAngle_Factor_List_Name,
            Work_Efficiency_Schedule_Name=peoplelist[i].Work_Efficiency_Schedule_Name,
            Clothing_Insulation_Calculation_Method=peoplelist[
                i
            ].Clothing_Insulation_Calculation_Method,
            Clothing_Insulation_Calculation_Method_Schedule_Name=peoplelist[
                i
            ].Clothing_Insulation_Calculation_Method_Schedule_Name,
            Clothing_Insulation_Schedule_Name=peoplelist[
                i
            ].Clothing_Insulation_Schedule_Name,
            Air_Velocity_Schedule_Name=peoplelist[i].Air_Velocity_Schedule_Name,
            Thermal_Comfort_Model_1_Type="AdaptiveASH55",
            Thermal_Comfort_Model_2_Type="AdaptiveCEN15251",
            Thermal_Comfort_Model_3_Type="",
            Thermal_Comfort_Model_4_Type="",
            Thermal_Comfort_Model_5_Type="",
        )
        firstpeopleobject = self.idf1.idfobjects["PEOPLE"][0]
        self.idf1.removeidfobject(firstpeopleobject)
    del peoplelist, firstpeopleobject


def addOpTempTherm(self):
    """
    Amend ZoneControl:Thermostat:OperativeTemperature objects.

    Add ZoneControl:Thermostat:OperativeTemperature objects for each zone.
    """
    for zonename_orig in self.zonenames_orig:
        if zonename_orig + " Thermostat" in [
            thermostat.Thermostat_Name
            for thermostat in self.idf1.idfobjects[
                "ZoneControl:Thermostat:OperativeTemperature"
            ]
        ]:
            print(zonename_orig + " Thermostat already was in the model")
        else:
            self.idf1.newidfobject(
                "ZoneControl:Thermostat:OperativeTemperature",
                Thermostat_Name=zonename_orig + " Thermostat",
                Radiative_Fraction_Input_Mode="Scheduled",
                Fixed_Radiative_Fraction="",
                Radiative_Fraction_Schedule_Name="TypOperativeTempControlSch",
            )
            print(zonename_orig + " Thermostat has been added")


def addBaseSchedules(self):
    """
    Amend Schedule:Compact objects.

    Checks Schedule:Compact objects needed for SingleZone accim,
    and add them in case these are not in the model
    """
    if "On" in [schedule.Name for schedule in self.idf1.idfobjects["Schedule:Compact"]]:
        print("On Schedule already was in the model")
    else:
        self.idf1.newidfobject(
            "Schedule:Compact",
            Name="On",
            Schedule_Type_Limits_Name="Any Number",
            Field_1="Through: 12/31",
            Field_2="For: AllDays",
            Field_3="Until: 24:00,1",
        )
        print("On Schedule has been added")


def setAvailSchOn(self):
    """
    Amend availability schedules.

    Assign On Compact:Schedule to heating and cooling availability
    schedule names.
    """
    for schedule in [i for i in self.idf1.idfobjects["ZoneHVAC:IdealLoadsAirSystem"]]:
        schedule.Heating_Availability_Schedule_Name = "On"
        schedule.Cooling_Availability_Schedule_Name = "On"


def saveaccim(self):
    """Save IDF."""
    self.idf1.save()
