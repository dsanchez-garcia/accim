"""Class for accim SingleZone and MultipleZone."""

class accimJob():
    """Class to start the accim process."""
    from os import listdir
    import numpy

    from accim.sim.accim_IDFgeneration import \
        inputdataSingleZone,\
        inputdataMultipleZone, \
        genIDFSingleZone, \
        genIDFMultipleZone
    from accim.sim.accim_Base import \
        setComfFieldsPeople, \
        addOpTempTherm, \
        addBaseSchedules, \
        saveaccim
    from accim.sim.accim_Base_EMS import \
        addEMSProgramsBase, \
        addEMSPCMBase, \
        addEMSOutputVariableBase, \
        addOutputVariablesTimestep, \
        addSimplifiedOutputVariables
    from accim.sim.accim_SingleZone import \
        addForscriptSchSingleZone
    from accim.sim.accim_SingleZone_EMS import \
        addGlobVarListSingleZone, \
        addEMSSensorsSingleZone, \
        addEMSActuatorsSingleZone, \
        addEMSProgramsSingleZone, \
        addOutputVariablesSingleZone
    from accim.sim.accim_MultipleZone import \
        setAvailSchOn, \
        addMultipleZoneSch, \
        addCurveObj, \
        addDetHVACobj, \
        addForscriptSchMultipleZone, \
        checkVentIsOn
    from accim.sim.accim_MultipleZone_EMS import \
        addGlobVarListOccZones, \
        addEMSSensorsMultipleZone, \
        addEMSActuatorsMultipleZone, \
        addEMSProgramsMultipleZone, \
        addEMSOutputVariableMultipleZone, \
        addOutputVariablesMultipleZone

    def __init__(self,
                 filename_temp,
                 ScriptType: str = None,
                 EnergyPlus_version: str = None,
                 verboseMode: bool = True):
        from eppy import modeleditor
        from eppy.modeleditor import IDF
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
                                     Only works for versions between EnergyPlus 9.1 (enter Ep91) and
                                     EnergyPlus 9.6(enter Ep96).""")
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

        self.occupiedZones = []
        for i in self.idf1.idfobjects['ZONE']:
            for k in self.idf1.idfobjects['PEOPLE']:
                if i.Name in k.Name:
                    self.occupiedZones.append(i.Name)
        self.occupiedZones_orig = [i.replace(':', '_') for i in self.occupiedZones]
        if verboseMode:
            print(f'The occupied zones in the model {filename_temp} are:')
            print(*self.occupiedZones, sep="\n")

        self.windownamelist_orig = ([window.Name
                                     for window in
                                     self.idf1.idfobjects
                                     ['AirflowNetwork:MultiZone:Component:DetailedOpening']
                                     if window.Name.endswith('_Win')]
        )
        # print(self.windownamelist_orig)
        self.windownamelist_orig_split = ([i.split('_') for i in self.windownamelist_orig])
        # print(self.windownamelist_orig_split)

        self.windownamelist = ([sub.replace(':', '_')
                                for sub
                                in ([window.Name
                                     for window
                                     in self.idf1.idfobjects
                                     ['AirflowNetwork:MultiZone:Component:DetailedOpening']
                                     if window.Name.endswith('_Win')]
                                )]
        )
        # print(self.windownamelist)
        if verboseMode:
            print(f'The windows in the model {filename_temp} are:')
            print(*self.windownamelist, sep="\n")

        if ScriptType.lower() == 'vrf' or ScriptType.lower() == 'vrfsystem':
            # self.zonenames_orig = ([zone.Name for zone in self.idf1.idfobjects['ZONE']])
            # # print(self.zonenames_orig)
            #
            # self.zonenames = ([sub.replace(':', '_')
            #                    for sub
            #                    in ([zone.Name for zone in self.idf1.idfobjects['ZONE']])])
            # # print(self.zonenames)
            self.zonenames_orig = self.occupiedZones_orig
            self.zonenames = self.zonenames
            if verboseMode:
                print(f'The zones in the model {filename_temp} are:')
                print(*self.zonenames, sep="\n")
        elif ScriptType.lower() == 'existing' or ScriptType.lower() == 'existinghvac':
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
                            temp1.append(self.ZCTlist[j].Zone_or_ZoneList_Name)
                            temp2.append(self.ZCTlist[j].Zone_or_ZoneList_Name.replace(":", "_"))
                            temp3.append(self.ZCTlist[j].Control_1_Name)
                self.HVACzonelist.append([TSPtypes[i], temp1, temp2, temp3])
            del temp1, temp2, temp3

            for i in range(len(self.HVACzonelist)):
                if len(self.HVACzonelist[i][3]) == 0:
                    print(f'There are no {self.HVACzonelist[i][0]} objects in the model')
                else:
                    print(f'Regarding {self.HVACzonelist[i][0]} objects:')
                    print(f'The zones with {self.HVACzonelist[i][0]} are:')
                    print(*self.HVACzonelist[i][1], sep="\n")
                    print(f'And the existing ThermostatSetpoint objects related to {self.HVACzonelist[i][0]} are:')
                    print(*self.HVACzonelist[i][3], sep="\n")

            self.self.zonenames_orig = []

            for i in range(len(self.HVACzonelist)):
                for k in range(len(self.HVACzonelist[i][1])):
                    if self.HVACzonelist[i][1][k] in self.self.zonenames_orig:
                        continue
                    else:
                        self.self.zonenames_orig.append(self.HVACzonelist[i][1][k])

            self.zonenames = [i.replace(':', '_') for i in self.self.zonenames_orig]

            HVACdict = {
                'Coil:Cooling:Water': 'Cooling Coil Total Cooling Rate',
                'Coil:Cooling:Water:DetailedGeometry': 'Cooling Coil Total Cooling Rate',
                # 'CoilSystem:Cooling:Water:HeatExchangerAssisted':'',
                'CoilSystem:Cooling:Water': 'Coil System Water Total Cooling Rate',
                'Coil:Heating:Water': 'Heating Coil Heating Energy',
                'Coil:Heating:Steam': 'Heating Coil Heating Energy',
                'Coil:Heating:Electric': 'Heating Coil Heating Energy',
                'Coil:Heating:Electric:MultiStage': 'Heating Coil Heating Energy',
                # estoy aqui
                'Coil:Heating:Desuperheater': '',
                'Coil:Cooling:DX:VariableRefrigerantFlow': '',
                'Coil:Heating:DX:VariableRefrigerantFlow': '',
                'Coil:Cooling:DX:VariableRefrigerantFlow:FluidTemperatureControl': '',
                'Coil:Heating:DX:VariableRefrigerantFlow:FluidTemperatureControl': '',
                'Coil:Heating:Fuel': '',
                'Coil:Heating:Gas:MultiStage': '',
                'Coil:Cooling:DX:SingleSpeed': 'Cooling Coil Total Cooling Rate',
                'Coil:Cooling:DX:TwoSpeed': '',
                'Coil:Cooling:DX:TwoStageWithHumidityControlMode': '',
                'Coil:Cooling:DX:MultiSpeed': '',
                'Coil:Cooling:DX:VariableSpeed': '',
                'CoilPerformance:DX:Cooling': '',
                'Coil:Heating:DX:SingleSpeed': '',
                'Coil:Heating:DX:MultiSpeed': '',
                'Coil:Heating:DX:VariableSpeed': '',
                'Coil:WaterHeating:Desuperheater': '',
                'CoilSystem:Cooling:DX': '',
                'CoilSystem:Heating:DX': '',
                'CoilSystem:Cooling:DX:HeatExchangerAssisted': '',
                'CoilSystem:IntegratedHeatPump:AirSource': '',
                'Coil:WaterHeating:AirToWaterHeatPump:Pumped': '',
                'Coil:WaterHeating:AirToWaterHeatPump:Wrapped': '',
                'Coil:WaterHeating:AirToWaterHeatPump:VariableSpeed': '',
                'Coil:Cooling:WaterToAirHeatPump:ParameterEstimation': '',
                'Coil:Cooling:WaterToAirHeatPump:EquationFit': '',
                'Coil:Cooling:WaterToAirHeatPump:VariableSpeedEquationFit': '',
                'Coil:Heating:WaterToAirHeatPump:ParameterEstimation': '',
                'Coil:Heating:WaterToAirHeatPump:EquationFit': '',
                'Coil:Heating:WaterToAirHeatPump:VariableSpeedEquationFit': '',
                'Coil:Cooling:DX:SingleSpeed:ThermalStorage': '',
                # not supported
                # 'Secondary Coils of DX System and Heat Pump':'',
                'Coil:Cooling:DX': '',
                'Coil:Cooling:DX:CurveFit:Performance': '',
                'Coil:Cooling:DX:CurveFit:OperatingMode': '',
                'Coil:Cooling:DX:CurveFit:Speed': '',
            }

            HVACkeylist = list(HVACdict.keys())

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
                    continue

            for i in range(len(self.ExisHVAC)):
                print(f'The names of the existing {self.ExisHVAC[i][0]} objects are:')
                print(*self.ExisHVAC[i][1], sep="\n")
                print(f'The zones related to these {self.ExisHVAC[i][0]} objects are')
                print(*self.ExisHVAC[i][2], sep='\n')
                print(f'And the windows related to these {self.ExisHVAC[i][0]} objects are:')
                print(*self.ExisHVAC[i][4], sep='\n')

        # todo aqui
