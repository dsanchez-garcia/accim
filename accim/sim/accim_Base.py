# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Add EnergyPlus objects in common to both ExistingHVAC and VRFsystem."""
from accim.sim.lists import epvers_space_objs

def setComfFieldsPeople(
        self,
        EnergyPlus_version: str = None,
        TempCtrl: str = None,
        verboseMode: bool = True
):
    """
    Amend PEOPLE objects so that accim can work.
    Copy existing PEOPLE objects and adds AdaptiveASH55 and AdaptiveCEN15251
    to Thermal Comfort Model types 1 and 2 fields of the existing People
    objects.

    :param EnergyPlus_version: Inherited from class `accim.sim.accis.addAccis`
    :param TempCtrl: Inherited from class `accim.sim.accis.addAccis`
    :param verboseMode: Inherited from class `accim.sim.accis.addAccis`
    """
    ppl = ([people for people in self.idf1.idfobjects['PEOPLE']])

    # epversionslist = ['9.6', '22.1', '22.2', '23.1', '23.2', '24.1', '24.2', '25.1']

    for i in range(len(ppl)):
        if TempCtrl == 'pmv':
            if any([EnergyPlus_version.lower() == v for v in epvers_space_objs]):
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
                    Thermal_Comfort_Model_3_Type='Fanger',
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
                    Thermal_Comfort_Model_3_Type='Fanger',
                    Thermal_Comfort_Model_4_Type='',
                    Thermal_Comfort_Model_5_Type='',
                    )
                firstpeopleobject = self.idf1.idfobjects['PEOPLE'][0]
                self.idf1.removeidfobject(firstpeopleobject)
        else:
            if any([EnergyPlus_version.lower() == v for v in epvers_space_objs]):
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

    if len([i for i in self.idf1.idfobjects['zonelist']]) > 0:
        # zonelist = [i for i in self.idf1.idfobjects['zonelist']]
        # spacelist = [i for i in self.idf1.idfobjects['spacelist']]
        ppl = [i for i in self.idf1.idfobjects['people']]
        # todo if people zone or zonelist field is a zonelist, add a people object for a zone
        newppl = ppl[-1]
        newppl = self.idf1.copyidfobject(newppl)
        newppl.Name = self.occupiedZones_orig[0] + ' People'
        newppl.Zone_or_ZoneList_or_Space_or_SpaceList_Name = self.occupiedZones_orig[0]
        self.newppl = newppl

    if verboseMode:
        print('The people objects in the model have been amended.')
        # print(*peoplelist,sep="\n")
    del ppl, firstpeopleobject


def saveaccim(self, verboseMode: bool = True):
    """Save IDF.

    :param verboseMode: Inherited from class `accim.sim.accis.addAccis`
    """
    self.idf1.save()
    if verboseMode:
        print('IDF has been saved')


def setPMVsetpoint(self, verboseMode: bool = True):
    """Sets PMV setpoints for temperature control.

    :param verboseMode: Inherited from class `accim.sim.accis.addAccis`
    """
    # previoustodo check again the difference between operative temp and fanger; see ZoneControl:Thermostat and where is it assigned
    optempthermlist = ([program for program in self.idf1.idfobjects['ZoneControl:Thermostat:OperativeTemperature']])

    for i in range(len(optempthermlist)):
        firstoptempthermlist = self.idf1.idfobjects['ZoneControl:Thermostat:OperativeTemperature'][-1]
        self.idf1.removeidfobject(firstoptempthermlist)

    fangerdict = {
        'Cooling Fanger comfort setpoint: Always 0.5': '0.5',
        'Heating Fanger comfort setpoint: Always -0.5': '-0.5'
    }
    for i in fangerdict:
        if i in [schedule.Name for schedule in self.idf1.idfobjects['Schedule:Compact']]:
            if verboseMode:
                print(f"{i} Schedule already was in the model")
        else:
            self.idf1.newidfobject(
                'Schedule:Compact',
                Name=i,
                Schedule_Type_Limits_Name="Any Number",
                Field_1='Through: 12/31',
                Field_2='For: AllDays',
                Field_3='Until: 24:00,' + fangerdict[i]
                )
            if verboseMode:
                print(f"{i} Schedule has been added")

    for zone in self.zonenames_orig:
        if f'{zone} Comfort Control' in [i.Name for i in self.idf1.idfobjects['ZoneControl:Thermostat:ThermalComfort']]:
            if verboseMode:
                print(f'{zone} Comfort Control ZoneControl:Thermostat:ThermalComfort already was in the model')
        else:
            self.idf1.newidfobject(
                'ZoneControl:Thermostat:ThermalComfort',
                Name=f'{zone} Comfort Control',
                Zone_or_ZoneList_Name=zone,
                Averaging_Method='PeopleAverage',
                Minimum_DryBulb_Temperature_Setpoint=12.8,
                Maximum_DryBulb_Temperature_Setpoint=40.0,
                Thermal_Comfort_Control_Type_Schedule_Name='Zone Comfort Control Type Sched',
                Thermal_Comfort_Control_1_Object_Type='ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint',
                Thermal_Comfort_Control_1_Name=f'{zone} Dual Comfort Setpoint'
            )
            if verboseMode:
                print(f'{zone} Comfort Control ZoneControl:Thermostat:ThermalComfort has been added')

        if f'{zone} Dual Comfort Setpoint' in [i.Name for i in self.idf1.idfobjects['ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint']]:
            if verboseMode:
                print(f'{zone} Dual Comfort Setpoint ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint already was in the model')
        else:
            self.idf1.newidfobject(
                'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint',
                Name=f'{zone} Dual Comfort Setpoint',
                Fanger_Thermal_Comfort_Heating_Schedule_Name='Heating Fanger comfort setpoint: Always -0.5',
                Fanger_Thermal_Comfort_Cooling_Schedule_Name='Cooling Fanger comfort setpoint: Always 0.5'
            )
            if verboseMode:
                print(f'{zone} Dual Comfort Setpoint ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint has been added')

def addControlFilesObjects(self, verboseMode: bool = True):
    """
    Adds an OutputControl:Files object to request the generation of CSV, MRT and ESO files.

    :param verboseMode: Inherited from class `accim.sim.accis.addAccis`
    """
    outputcontrolfiles = [i for i in self.idf1.idfobjects['OutputControl:Files']]

    if len(outputcontrolfiles) == 0:
        self.idf1.newidfobject(
            'OutputControl:Files',
            Output_CSV='Yes',
            Output_MTR='Yes',
            Output_ESO='Yes'
        )
        if verboseMode:
            print(f'Added - OutputControl:Files object')
    else:
        outputcontrolfiles[0].Output_CSV = 'Yes'
        outputcontrolfiles[0].Output_MTR = 'Yes'
        outputcontrolfiles[0].Output_ESO = 'Yes'
        if verboseMode:
            print(f'Not added - OutputControl:Files object - Output CSV, MTR and ESO fields set to Yes')

def addOutputVariableDictionaryObject(self, verboseMode: bool = True):
    """
    Adds an Output:VariableDictionary object to request the generation of the RDD file.


    :param verboseMode:
    """
    variabledictionaryfile = [i for i in self.idf1.idfobjects['Output:VariableDictionary']]

    if len(variabledictionaryfile) == 0:
        self.idf1.newidfobject(
            'Output:VariableDictionary',
            Key_Field='IDF',
            Sort_Option='Unsorted',
        )
        if verboseMode:
            print(f'Added - Output:VariableDictionary object')
    else:
        if verboseMode:
            print(f'Not added - Output:VariableDictionary object - Output CSV, MTR and ESO fields set to Yes')


def addOutputEnergyManagementSystem(self, verboseMode: bool = True):

    outputEMSobj = [i for i in self.idf1.idfobjects['Output:EnergyManagementSystem']]

    if len(outputEMSobj) == 0:
        self.idf1.newidfobject(
            key='Output:EnergyManagementSystem',
            Actuator_Availability_Dictionary_Reporting='Verbose',
            Internal_Variable_Availability_Dictionary_Reporting='Verbose',
            EMS_Runtime_Language_Debug_Output_Level='Verbose'
        )
        if verboseMode:
            print(f'Added - Output:EnergyManagementSystem object')
    else:
        if verboseMode:
            print(f'Not added - Output:EnergyManagementSystem object')

