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

"""Class for accim."""

class accimJob():
    """Class to start the process to add the class ``accim.sim.accis.addAccis``.

    :param idf_class_instance: the filename of the idf
    :param ScriptType: Inherited from class ``accim.sim.accis.addAccis``
    :param EnergyPlus_version: Inherited from class ``accim.sim.accis.addAccis``
    :param TempCtrl: Inherited from class ``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from class ``accim.sim.accis.addAccis``
    :param accimNotWorking: True if problems detected in class ``accim.sim.accis.addAccis``
    """
    from os import listdir
    import numpy

    # from accim.sim.accim_IDFgeneration import \
    #     inputData,\
    #     genIDF
    from accim.sim.accim_Base import \
        setComfFieldsPeople, \
        saveaccim, \
        setPMVsetpoint, \
        addControlFilesObjects, \
        addOutputVariableDictionaryObject, \
        addOutputEnergyManagementSystem
    from accim.sim.accim_Base_EMS import \
        addEMSActuatorsBase, \
        addEMSOutputVariableBase, \
        addEMSPCMBase, \
        addEMSProgramsBase, \
        addEMSSensorsBase, \
        addGlobVarList, \
        addIntVarList, \
        addOutputVariablesStandard, \
        addOutputVariablesSimplified, \
        addOutputVariablesDetailed, \
        removeExistingOutputVariables, \
        removeDuplicatedOutputVariables, \
        outputsSpecified, \
        genOutputDataframe, \
        takeOutputDataFrame, \
        makeAverages

    from accim.sim.accim_ExistingHVAC import \
        addForscriptSchExistHVAC
    from accim.sim.accim_ExistingHVAC_EMS import \
        addEMSSensorsExisHVAC
    from accim.sim.accim_VRFsystem import \
        addBaseSchedules, \
        addCurveObj, \
        addDetHVACobj, \
        addForscriptSchVRFsystem, \
        addOpTempTherm, \
        addVRFsystemSch, \
        checkVentIsOn, \
        setAvailSchOn
    from accim.sim.accim_VRFsystem_EMS import \
        addEMSSensorsVRFsystem
    from accim.sim.utils import scan_zones

    def __init__(self,
                 idf_class_instance,
                 ScriptType: str = None,
                 EnergyPlus_version: str = None,
                 TempCtrl: str = None,
                 verboseMode: bool = True,
                 ):
        """
        Constructor method.
        """
        import eppy
        from eppy import modeleditor
        from eppy.modeleditor import IDF

        # IDF.setiddname(api_environment.EnergyPlusInputIddPath)
        # idf1 = IDF(api_environment.EnergyPlusInputIdfPath)

        self.idf1 = idf_class_instance

        # Scanning occupied zones using func
        self.scan_zones()
        # # Scanning occupied zones
        # self.occupiedZones_orig = []
        #
        # # Check if model comes from OpenStudio
        #
        # # Check if ZoneList or SpaceList are used
        # occupiedZones_orig_osm = []
        #
        # self.spacelist_use = False
        # try:
        #     if len(self.idf1.idfobjects['SPACELIST']) > 0:
        #         self.spacelist_use = True
        #         self.spacenames_for_ems_uniquekey = []
        #         self.spacenames_for_ems_name = []
        #         self.spacenames_for_ems_uniquekey_people = []
        #         self.zonenames_for_ems_with_sl = []
        #         for people in self.idf1.idfobjects['PEOPLE']:
        #             for spacelist in [i for i in self.idf1.idfobjects['SPACELIST'] if i.Name == people.Zone_or_ZoneList_or_Space_or_SpaceList_Name]:
        #                 for space in [i for i in self.idf1.idfobjects['SPACE'] if i.Space_Type == spacelist.Name]:
        #                     self.spacenames_for_ems_uniquekey.append(f'{space.Name} {spacelist.Name}')
        #                     self.spacenames_for_ems_name.append(space.Name)
        #                     self.spacenames_for_ems_uniquekey_people.append(f'{space.Name} {people.Name}')
        #                     occupiedZones_orig_osm.append(space.Zone_Name)
        #                     for zone in [i for i in self.idf1.idfobjects['ZONE'] if space.Zone_Name == i.Name]:
        #                         self.zonenames_for_ems_with_sl.append(zone.Name)
        # except KeyError:
        #     idd = '-'.join([str(i) for i in self.idf1.idd_version])
        #     print('Searching Spacelist objects returned KeyError. '
        #           f'That means these are not supported in the EnergyPlus version {idd}')
        #
        # # occupiedZones_orig_osm = []
        # # if len([h for h in self.idf1.idfobjects['zonelist']]) > 0:
        # #     if len(self.idf1.idfobjects['zone']) == 1:
        # #         no_of_zones = range(1, 2)
        # #     else:
        # #         no_of_zones = range(1, len(self.idf1.idfobjects['zone']))
        # #
        # #     for i in no_of_zones:
        # #         for j in self.idf1.idfobjects['zonelist']:
        # #             for k in self.idf1.idfobjects['zone']:
        # #                 if k.Name in j[f'Zone_{i}_Name']:
        # #                     occupiedZones_orig_osm.append(k.Name)
        # #
        # #     # for i in self.idf1.idfobjects['zone']:
        # #     #     if all(i.Name not in [j for j in occupiedZones_orig_osm]):
        # #     #         occupiedZones_orig_osm.append(i.Name)
        #
        # occupiedZones_orig_dsb = []
        # for i in self.idf1.idfobjects['ZONE']:
        #     for k in self.idf1.idfobjects['PEOPLE']:
        #         try:
        #             if i.Name == k.Zone_or_ZoneList_or_Space_or_SpaceList_Name:
        #                 occupiedZones_orig_dsb.append(i.Name.upper())
        #         except eppy.bunch_subclass.BadEPFieldError:
        #             if i.Name == k.Zone_or_ZoneList_Name:
        #                 occupiedZones_orig_dsb.append(i.Name.upper())
        #
        # if self.spacelist_use:
        #     self.occupiedZones_orig = occupiedZones_orig_osm
        #     self.occupiedZones = [i.replace(' ', '_') for i in self.occupiedZones_orig]
        #     self.origin_dsb = False
        #     self.ems_objs_name = self.spacenames_for_ems_name
        #     self.ems_objs_key = self.spacenames_for_ems_uniquekey
        #     self.ems_zonenames = self.zonenames_for_ems_with_sl
        #     self.ems_zonenames_underscore = [i.replace(' ', '_') for i in self.ems_zonenames]
        # else:
        #     self.occupiedZones_orig = occupiedZones_orig_dsb
        #     self.occupiedZones = [i.replace(':', '_') for i in self.occupiedZones_orig]
        #     self.origin_dsb = True
        #     self.ems_objs_name = self.occupiedZones
        #     self.ems_objs_key = self.occupiedZones_orig
        #     self.ems_zonenames = self.occupiedZones_orig
        #     self.ems_zonenames_underscore = self.occupiedZones_orig


        if verboseMode:
            print(f'The occupied zones in the model {idf_class_instance} are:')
            print(*self.occupiedZones_orig, sep="\n")

        self.ismixedmode = False

        if (ScriptType.lower() == 'vrfsystem_mm' or
            ScriptType.lower() == 'vrf_mm' or
            ScriptType.lower() == 'existinghvac_mm' or
            ScriptType.lower() == 'ex_mm'
        ):
            self.ismixedmode = True
            self.windownamelist_orig = []

            for i in [window.Name for window in
                      self.idf1.idfobjects
                      ['AirflowNetwork:MultiZone:Component:DetailedOpening']
                      if window.Name.endswith('_Win')
                      or window.Name.endswith('_Door')
                      ]:
                for k in self.occupiedZones_orig:
                    if i.split('_')[0].lower() in k.lower():
                        self.windownamelist_orig.append(i)

            self.windownamelist = [i.replace(':', '_') for i in self.windownamelist_orig]

            # print(self.windownamelist_orig)
            self.windownamelist_orig_split = ([i.split('_') for i in self.windownamelist_orig])
            # print(self.windownamelist_orig_split)
            if verboseMode:
                print(f'The windows and doors in the model {idf_class_instance} are:')
                print(*self.windownamelist, sep="\n")

        if 'vrf' in ScriptType.lower():
            self.zonenames = self.occupiedZones
            self.zonenames_orig = self.occupiedZones_orig
            if verboseMode:
                print(f'The zones in the model {idf_class_instance} are:')
                print(*self.zonenames, sep="\n")

        elif 'ex' in ScriptType.lower():
            TSPtypes = [
                'ThermostatSetpoint:SingleHeating',
                'ThermostatSetpoint:SingleCooling',
                # ThermostatSetpoint:SingleHeatingOrCooling objects are not supported
                # 'ThermostatSetpoint:SingleHeatingOrCooling',
                'ThermostatSetpoint:DualSetpoint'
            ]
            self.ZCTlist = [i for i in self.idf1.idfobjects['ZONECONTROL:THERMOSTAT']]

            self.HVACzonelist = []

            for i in range(len(TSPtypes)):
                temp1 = []
                temp2 = []
                temp3 = []
                if len(self.idf1.idfobjects[TSPtypes[i]]) > 0:
                    for j in range(len(self.ZCTlist)):
                        if self.ZCTlist[j].Control_1_Object_Type in TSPtypes[i]:
                            temp1.append(self.ZCTlist[j].Zone_or_ZoneList_Name.upper())
                            if ':' in self.ZCTlist[j].Zone_or_ZoneList_Name:
                                temp2.append(self.ZCTlist[j].Zone_or_ZoneList_Name.upper().replace(":", "_"))
                            else:
                                temp2.append([i.Name.upper() for i in self.idf1.idfobjects['SPACE'] if i.Zone_Name.upper() == self.ZCTlist[j].Zone_or_ZoneList_Name.upper()][0])
                            temp3.append(self.ZCTlist[j].Control_1_Name)
                self.HVACzonelist.append([TSPtypes[i], temp1, temp2, temp3])
            del temp1, temp2, temp3

            if verboseMode:
                for i in range(len(self.HVACzonelist)):
                    if len(self.HVACzonelist[i][3]) == 0:
                        print(f'There are no {self.HVACzonelist[i][0]} objects in the model')
                    else:
                        print(f'Regarding {self.HVACzonelist[i][0]} objects:')
                        print(f'The zones with {self.HVACzonelist[i][0]} are:')
                        print(*self.HVACzonelist[i][1], sep="\n")
                        print(f'And the existing ThermostatSetpoint objects related to {self.HVACzonelist[i][0]} are:')
                        print(*self.HVACzonelist[i][3], sep="\n")

            self.zonenames_orig = []
            # todo currently all zones regardless the single or dual thermostat object are merged in zonenames_orig;
            #  this would be desirable to be amended

            for i in range(len(self.HVACzonelist)):
                for k in range(len(self.HVACzonelist[i][1])):
                    if self.HVACzonelist[i][1][k] in self.zonenames_orig:
                        continue
                    else:
                        self.zonenames_orig.append(self.HVACzonelist[i][1][k])
            if self.origin_dsb:
                self.zonenames = [i.replace(':', '_') for i in self.zonenames_orig]
            else:
                self.zonenames = [i.replace(' ', '_') for i in self.zonenames_orig]

            if ScriptType.lower() == 'existinghvac_mm' or ScriptType.lower() == 'ex_mm':

                self.HVACdict = {
                    # todo if there is a Coil:Heating:Whatever and another Coil:Heating:DifferentWhatever
                    #  coils and windows sensors will be duplicated and simulation will crash; it needs to be solved.

                    # Group Heating and Cooling Coils
                    'Coil:Cooling:Water': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:Water:DetailedGeometry': 'Cooling Coil Total Cooling Rate',
                    # not supported
                    # 'CoilSystem:Cooling:Water:HeatExchangerAssisted':'',
                    'CoilSystem:Cooling:Water': 'Coil System Water Total Cooling Rate',
                    'Coil:Heating:Water': 'Heating Coil Heating Energy',
                    'Coil:Heating:Steam': 'Heating Coil Heating Energy',
                    'Coil:Heating:Electric': 'Heating Coil Heating Energy',
                    'Coil:Heating:Electric:MultiStage': 'Heating Coil Heating Energy',
                    'Coil:Heating:Desuperheater': 'Heating Coil Heating Energy',
                    'Coil:Cooling:DX:VariableRefrigerantFlow': 'Cooling Coil Total Cooling Rate',
                    'Coil:Heating:DX:VariableRefrigerantFlow': 'Heating Coil Heating Energy',
                    'Coil:Cooling:DX:VariableRefrigerantFlow:FluidTemperatureControl': 'Cooling Coil Total Cooling Rate',
                    'Coil:Heating:DX:VariableRefrigerantFlow:FluidTemperatureControl': 'Heating Coil Heating Energy',
                    'Coil:Heating:Fuel': 'Heating Coil Heating Energy',
                    'Coil:Heating:Gas:MultiStage': 'Heating Coil Heating Energy',
                    'Coil:Cooling:DX:SingleSpeed': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:TwoSpeed': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:TwoStageWithHumidityControlMode': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:MultiSpeed': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:VariableSpeed': 'Cooling Coil Total Cooling Rate',
                    # not supported
                    # 'CoilPerformance:DX:Cooling': '',
                    'Coil:Heating:DX:SingleSpeed': 'Heating Coil Heating Energy',
                    'Coil:Heating:DX:MultiSpeed': 'Heating Coil Heating Energy',
                    'Coil:Heating:DX:VariableSpeed': 'Heating Coil Heating Energy',
                    'Coil:WaterHeating:Desuperheater': 'Water Heater Heating Energy',
                    # not supported
                    # 'CoilSystem:Cooling:DX': '',
                    # 'CoilSystem:Heating:DX': '',
                    # 'CoilSystem:Cooling:DX:HeatExchangerAssisted': '',
                    # 'CoilSystem:IntegratedHeatPump:AirSource': '',
                    # 'Coil:WaterHeating:AirToWaterHeatPump:Pumped': 'Heating Coil Heating Energy',
                    # 'Coil:WaterHeating:AirToWaterHeatPump:Wrapped': 'Heating Coil Heating Energy',
                    # 'Coil:WaterHeating:AirToWaterHeatPump:VariableSpeed': 'Cooling Coil Electricity Energy',
                    'Coil:Cooling:WaterToAirHeatPump:ParameterEstimation': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:WaterToAirHeatPump:EquationFit': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:WaterToAirHeatPump:VariableSpeedEquationFit': 'Cooling Coil Total Cooling Rate',
                    'Coil:Heating:WaterToAirHeatPump:ParameterEstimation': 'Heating Coil Heating Energy',
                    'Coil:Heating:WaterToAirHeatPump:EquationFit': 'Heating Coil Heating Energy',
                    'Coil:Heating:WaterToAirHeatPump:VariableSpeedEquationFit': 'Heating Coil Heating Energy',
                    'Coil:Cooling:DX:SingleSpeed:ThermalStorage': 'Cooling Coil Total Cooling Rate',
                    # not supported
                    # 'Secondary Coils of DX System and Heat Pump':'',
                    'Coil:Cooling:DX': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:CurveFit:Performance': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:CurveFit:OperatingMode': 'Cooling Coil Total Cooling Rate',
                    'Coil:Cooling:DX:CurveFit:Speed': 'Cooling Coil Total Cooling Rate',

                    # Group – Radiative / Convective Units
                    # todo many objects have heating or cooling outputs for the same field
                    'ZoneHVAC:Baseboard:RadiantConvective:Water': 'Baseboard Total Heating Rate',
                    'ZoneHVAC:Baseboard:RadiantConvective:Steam': 'Baseboard Total Heating Rate',
                    'ZoneHVAC:Baseboard:RadiantConvective:Electric': 'Baseboard Total Heating Rate',
                    'ZoneHVAC:CoolingPanel:RadiantConvective:Water': 'Cooling Panel Total Cooling Rate',
                    'ZoneHVAC:Baseboard:Convective:Water': 'Baseboard Total Heating Rate',
                    'ZoneHVAC:Baseboard:Convective:Electric': 'Baseboard Total Heating Rate',
                    # not supported
                    # ZoneHVAC:LowTemperatureRadiant:VariableFlow can be a chilled ceiling: Zone Radiant HVAC Cooling Rate
                    # also it can be a heated floor: Zone Radiant HVAC Heating Rate
                    # 'ZoneHVAC:LowTemperatureRadiant:VariableFlow': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:LowTemperatureRadiant:ConstantFlow': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:LowTemperatureRadiant:Electric': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:LowTemperatureRadiant:SurfaceGroup': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:HighTemperatureRadiant': 'Zone Radiant HVAC Heating Energy',
                    # 'ZoneHVAC:VentilatedSlab': '',
                    # 'ZoneHVAC:VentilatedSlab:SlabGroup': '',

                    # Group – Zone HVAC Air Loop Terminal Units
                    # 'AirTerminal:SingleDuct:ConstantVolume:Reheat': '',
                    # 'AirTerminal:SingleDuct:ConstantVolume:NoReheat': '',
                    # 'AirTerminal:SingleDuct:VAV:Reheat': '',
                    # 'AirTerminal:SingleDuct:VAV:Reheat:VariableSpeedFan': '',
                    # 'AirTerminal:SingleDuct:VAV:HeatAndCool:Reheat': '',
                    # 'AirTerminal:SingleDuct:VAV:NoReheat': '',
                    # 'AirTerminal:SingleDuct:VAV:HeatAndCool:NoReheat': '',
                    # 'AirTerminal:SingleDuct:SeriesPIU:Reheat': '',
                    # 'AirTerminal:SingleDuct:ParallelPIU:Reheat': '',
                    # 'AirTerminal:SingleDuct:ConstantVolume:FourPipeInduction': '',
                    # 'AirTerminal:SingleDuct:ConstantVolume:FourPipeBeam': '',
                    'AirTerminal:SingleDuct:ConstantVolume:CooledBeam': 'Zone Air Terminal Beam Chilled Water Energy',
                    # 'AirTerminal:SingleDuct:Mixer': '',
                    # 'AirTerminal:DualDuct:ConstantVolume': '',
                    # 'AirTerminal:DualDuct:VAV': '',
                    # 'AirTerminal:DualDuct:VAV:OutdoorAir': ''
                }

                HVACkeylist = list(self.HVACdict.keys())

                self.ExisHVAC = []

                for i in range(len(HVACkeylist)):
                    try:
                        temp = [i.Name for i in self.idf1.idfobjects[HVACkeylist[i]]]
                        temp_zone_orig = [i.Name.split(' ')[0] for i in self.idf1.idfobjects[HVACkeylist[i]]]
                        temp_zone = [i.Name.split(' ')[0].replace(':', '_') for i in self.idf1.idfobjects[HVACkeylist[i]]]
                        temp_win = []
                        for j in temp_zone:
                            for k in self.windownamelist:
                                if j in k:
                                    temp_win.append(k)
                        # hasta aqui
                        if len(temp) == 0:
                            continue
                        else:
                            self.ExisHVAC.append([HVACkeylist[i], temp, temp_zone_orig, temp_zone, temp_win])
                    except KeyError:
                        if verboseMode:
                            print(f'{HVACkeylist[i]} HVAC SYSTEM IS NOT SUPPORTED')
                        continue

                for i in range(len(self.ExisHVAC)):
                    for j in range(len(self.ExisHVAC[i][2])):
                        if self.ExisHVAC[i][2][j] not in self.zonenames_orig:
                            if verboseMode:
                                print(f'"{self.ExisHVAC[i][2][j]}" is not a valid room. \n'
                                      f'That means "{self.ExisHVAC[i][1][j]}" is not named following [HVAC Zone] [HVAC Element] pattern or HVAC element is shared')
                            # raise ValueError
                            self.accimNotWorking = True
                
                if verboseMode:
                    for i in range(len(self.ExisHVAC)):
                        print(f'The names of the existing {self.ExisHVAC[i][0]} objects are:')
                        print(*self.ExisHVAC[i][1], sep="\n")
                        print(f'The zones related to these {self.ExisHVAC[i][0]} objects are')
                        print(*self.ExisHVAC[i][2], sep='\n')
                        print(f'And the windows related to these {self.ExisHVAC[i][0]} objects are:')
                        print(*self.ExisHVAC[i][4], sep='\n')
