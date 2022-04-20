"""Class for accim."""

class accimJob():
    """Class to start the accim process."""
    from os import listdir
    import numpy

    from accim.sim.accim_IDFgeneration import \
        inputData,\
        genIDF
    from accim.sim.accim_Base import \
        setComfFieldsPeople, \
        saveaccim
    from accim.sim.accim_Base_EMS import \
        addEMSActuatorsBase, \
        addEMSOutputVariableBase, \
        addEMSPCMBase, \
        addEMSProgramsBase, \
        addEMSSensorsBase, \
        addGlobVarList, \
        addIntVarList, \
        addOutputVariablesBase, \
        addOutputVariablesTimestep, \
        addSimplifiedOutputVariables
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
        setAvailSchOn, \
        setPMVsetpoint
    from accim.sim.accim_VRFsystem_EMS import \
        addEMSSensorsVRFsystem

    def __init__(self,
                 filename_temp,
                 ScriptType: str = None,
                 EnergyPlus_version: str = None,
                 TempCtrl: str = None,
                 verboseMode: bool = True,
                 accimNotWorking: bool = False):
        from eppy import modeleditor
        from eppy.modeleditor import IDF
        self.accimNotWorking = accimNotWorking

        if EnergyPlus_version.lower() == 'ep91':
            iddfile = 'C:/EnergyPlusV9-1-0/Energy+.idd'
        elif EnergyPlus_version.lower() == 'ep92':
            iddfile = 'C:/EnergyPlusV9-2-0/Energy+.idd'
        elif EnergyPlus_version.lower() == 'ep93':
            iddfile = 'C:/EnergyPlusV9-3-0/Energy+.idd'
        elif EnergyPlus_version.lower() == 'ep94':
            iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
        elif EnergyPlus_version.lower() == 'ep95':
            iddfile = 'C:/EnergyPlusV9-5-0/Energy+.idd'
        elif EnergyPlus_version.lower() == 'ep96':
            iddfile = 'C:/EnergyPlusV9-6-0/Energy+.idd'
        else:
            raise ValueError("""EnergyPlus version not supported.\n
                                     Only works for versions between EnergyPlus 9.1 (enter ep91) and
                                     EnergyPlus 9.6(enter ep96).""")
        if verboseMode:
            print('IDD location is: '+iddfile)
        IDF.setiddname(iddfile)

        fname1 = filename_temp+'.idf'
        self.idf0 = IDF(fname1)
        self.idf0.savecopy(filename_temp+'_pymod.idf')

        self.filename = filename_temp+'_pymod'
        fname1 = self.filename+'.idf'
        self.idf1 = IDF(fname1)
        self.filename = filename_temp+'_pymod'

        # print(self.filename)

        self.occupiedZones_orig = []
        for i in self.idf1.idfobjects['ZONE']:
            for k in self.idf1.idfobjects['PEOPLE']:
                if i.Name in k.Name:
                    self.occupiedZones_orig.append(i.Name.upper())
        self.occupiedZones = [i.replace(':', '_') for i in self.occupiedZones_orig]
        if verboseMode:
            print(f'The occupied zones in the model {filename_temp} are:')
            print(*self.occupiedZones_orig, sep="\n")

        if (ScriptType.lower() == 'vrfsystem' or
            ScriptType.lower() == 'vrf' or
            ScriptType.lower() == 'existinghvac_mm' or
            ScriptType.lower() == 'ex_mm'
        ):

            self.windownamelist_orig = []

            for i in [window.Name for window in
                      self.idf1.idfobjects
                      ['AirflowNetwork:MultiZone:Component:DetailedOpening']
                      if window.Name.endswith('_Win')]:
                for k in self.occupiedZones_orig:
                    if i.split('_')[0].lower() in k.lower():
                        self.windownamelist_orig.append(i)

            self.windownamelist = [i.replace(':', '_') for i in self.windownamelist_orig]

            # print(self.windownamelist_orig)
            self.windownamelist_orig_split = ([i.split('_') for i in self.windownamelist_orig])
            # print(self.windownamelist_orig_split)
            if verboseMode:
                print(f'The windows in the model {filename_temp} are:')
                print(*self.windownamelist, sep="\n")

        if ScriptType.lower() == 'vrfsystem' or ScriptType.lower() == 'vrf':
            self.zonenames = self.occupiedZones
            self.zonenames_orig = self.occupiedZones_orig
            if verboseMode:
                print(f'The zones in the model {filename_temp} are:')
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
                            temp2.append(self.ZCTlist[j].Zone_or_ZoneList_Name.upper().replace(":", "_"))
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

            self.zonenames = [i.replace(':', '_') for i in self.zonenames_orig]

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
