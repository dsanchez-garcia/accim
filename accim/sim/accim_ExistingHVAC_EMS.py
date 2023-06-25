"""Module for EMS functions and models with existing HVAC systems"""


def addEMSSensorsExisHVAC(self, verboseMode : bool = True):
    """
    Adds the EMS sensors for models with existing HVAC system.

    :param self: Used as a method for class ``accim.sim.accim_Main.accimJob``
    :param verboseMode: Inherited from class ``accim.sim.accis.addAccis``
    """
    sensorlist = ([sensor.Name for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor']])
    for i in range(len(self.ExisHVAC)):
        for j in range(len(self.ExisHVAC[i][1])):
            if 'Cool' in self.ExisHVAC[i][1][j] or 'Cool' in self.HVACdict[self.ExisHVAC[i][0]]:
                if self.ExisHVAC[i][3][j] + '_CoolCoil' in sensorlist:
                    if verboseMode:
                        print('Not added - ' + self.ExisHVAC[i][3][j] + '_CoolCoil Sensor')
                else:
                    self.idf1.newidfobject(
                        'EnergyManagementSystem:Sensor',
                        Name=self.ExisHVAC[i][3][j] + '_CoolCoil',
                        OutputVariable_or_OutputMeter_Index_Key_Name=self.ExisHVAC[i][1][j],
                        OutputVariable_or_OutputMeter_Name=self.HVACdict[self.ExisHVAC[i][0]]
                    )
                    if verboseMode:
                        print('Added - ' + self.ExisHVAC[i][3][j] + '_CoolCoil Sensor')
                for k in range(len(self.ExisHVAC[i][4])):
                    if self.ExisHVAC[i][3][j] in self.ExisHVAC[i][4][k]:
                        if self.ExisHVAC[i][4][k] + '_CoolCoil' in sensorlist:
                            if verboseMode:
                                print('Not added - ' + self.ExisHVAC[i][4][k] + '_CoolCoil Sensor')
                        else:
                            self.idf1.newidfobject(
                                'EnergyManagementSystem:Sensor',
                                Name=self.ExisHVAC[i][4][k] + '_CoolCoil',
                                OutputVariable_or_OutputMeter_Index_Key_Name=self.ExisHVAC[i][1][j],
                                OutputVariable_or_OutputMeter_Name=self.HVACdict[self.ExisHVAC[i][0]]
                            )
                            if verboseMode:
                                print('Added - ' + self.ExisHVAC[i][4][k] + '_CoolCoil Sensor')
                #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.ExisHVAC[i][3][j]+'_CoolCoil'])
            if 'Heating' in self.ExisHVAC[i][1][j] or 'Heating' in self.HVACdict[self.ExisHVAC[i][0]]:
                if self.ExisHVAC[i][3][j] + '_HeatCoil' in sensorlist:
                    if verboseMode:
                        print('Not added - ' + self.ExisHVAC[i][3][j] + '_HeatCoil Sensor')
                else:
                    self.idf1.newidfobject(
                        'EnergyManagementSystem:Sensor',
                        Name=self.ExisHVAC[i][3][j] + '_HeatCoil',
                        OutputVariable_or_OutputMeter_Index_Key_Name=self.ExisHVAC[i][1][j],
                        OutputVariable_or_OutputMeter_Name=self.HVACdict[self.ExisHVAC[i][0]]
                    )
                    if verboseMode:
                        print('Added - ' + self.ExisHVAC[i][3][j] + '_HeatCoil Sensor')
                # probando
                for k in range(len(self.ExisHVAC[i][4])):
                    if self.ExisHVAC[i][3][j] in self.ExisHVAC[i][4][k]:
                        if self.ExisHVAC[i][4][k] + '_HeatCoil' in sensorlist:
                            if verboseMode:
                                print('Not added - ' + self.ExisHVAC[i][4][k] + '_HeatCoil Sensor')
                        else:
                            self.idf1.newidfobject(
                                'EnergyManagementSystem:Sensor',
                                Name=self.ExisHVAC[i][4][k] + '_HeatCoil',
                                OutputVariable_or_OutputMeter_Index_Key_Name=self.ExisHVAC[i][1][j],
                                OutputVariable_or_OutputMeter_Name=self.HVACdict[self.ExisHVAC[i][0]]
                            )
                            if verboseMode:
                                print('Added - ' + self.ExisHVAC[i][4][k] + '_HeatCoil Sensor')
