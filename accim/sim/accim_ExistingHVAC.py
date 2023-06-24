"""Module for function in EnergyPlus scope related to models with existing HVAC systems"""

def addForscriptSchExistHVAC(self, verboseMode: bool = True):
    """Add Schedules for each zone in existing HVAC zones to override the existing setpoint temperatures.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    for i in range(len(self.HVACzonelist)):
        if len(self.HVACzonelist[i][3]) == 0:
            continue
        else:
            if 'ThermostatSetpoint:DualSetpoint' in self.HVACzonelist[i][0]:
                for j in range(len(self.HVACzonelist[i][2])):
                    if "AHST_Sch_" + self.HVACzonelist[i][2][j] in [sch.Name
                                                                     for sch
                                                                     in self.idf1.idfobjects['Schedule:Compact']]:
                        if verboseMode:
                            print('AHST_Sch_' + self.HVACzonelist[i][2][j] + ' Schedule already was in the model')
                    else:
                        self.idf1.newidfobject(
                            'Schedule:Compact',
                            Name="AHST_Sch_" + self.HVACzonelist[i][2][j],
                            Schedule_Type_Limits_Name="Any Number",
                            Field_1='Through: 12/31',
                            Field_2='For: AllDays',
                            Field_3='Until: 24:00,20'
                        )
                        if verboseMode:
                            print('AHST_Sch_' + self.HVACzonelist[i][2][j] + ' Schedule has been added')

                    if "ACST_Sch_" + self.HVACzonelist[i][2][j] in [sch.Name
                                                                     for sch
                                                                     in self.idf1.idfobjects['Schedule:Compact']]:
                        if verboseMode:
                            print('ACST_Sch_' + self.HVACzonelist[i][2][j] + ' Schedule already was in the model')
                    else:
                        self.idf1.newidfobject(
                            'Schedule:Compact',
                            Name="ACST_Sch_" + self.HVACzonelist[i][2][j],
                            Schedule_Type_Limits_Name="Any Number",
                            Field_1='Through: 12/31',
                            Field_2='For: AllDays',
                            Field_3='Until: 24:00,24'
                        )
                        if verboseMode:
                            print('ACST_Sch_' + self.HVACzonelist[i][2][j] + ' Schedule has been added')
            elif 'ThermostatSetpoint:SingleHeating' in self.HVACzonelist[i][0]:
                for j in range(len(self.HVACzonelist[i][2])):
                    if "AHST_Sch_" + self.HVACzonelist[i][2][j] in [sch.Name
                                                                     for sch
                                                                     in self.idf1.idfobjects['Schedule:Compact']]:
                        if verboseMode:
                            print('AHST_Sch_' + self.HVACzonelist[i][2][j] + ' Schedule already was in the model')
                    else:
                        self.idf1.newidfobject(
                            'Schedule:Compact',
                            Name="AHST_Sch_" + self.HVACzonelist[i][2][j],
                            Schedule_Type_Limits_Name="Any Number",
                            Field_1='Through: 12/31',
                            Field_2='For: AllDays',
                            Field_3='Until: 24:00,20'
                        )
                        if verboseMode:
                            print('AHST_Sch_' + self.HVACzonelist[i][2][j] + ' Schedule has been added')
            elif 'ThermostatSetpoint:SingleCooling' in self.HVACzonelist[i][0]:
                if "ACST_Sch_" + self.HVACzonelist[i][2][j] in [sch.Name
                                                                 for sch
                                                                 in self.idf1.idfobjects['Schedule:Compact']]:
                    if verboseMode:
                        print('ACST_Sch_' + self.HVACzonelist[i][2][j] + ' Schedule already was in the model')
                else:
                    self.idf1.newidfobject(
                        'Schedule:Compact',
                        Name="ACST_Sch_" + self.HVACzonelist[i][2][j],
                        Schedule_Type_Limits_Name="Any Number",
                        Field_1='Through: 12/31',
                        Field_2='For: AllDays',
                        Field_3='Until: 24:00,24'
                    )
                    if verboseMode:
                        print('ACST_Sch_' + self.HVACzonelist[i][2][j] + ' Schedule has been added')

    for j in range(len(self.HVACzonelist)):
        for k in range(len(self.HVACzonelist[j][3])):
            if self.HVACzonelist[j][0] in 'ThermostatSetpoint:SingleHeating':
                for SP in [h for h in self.idf1.idfobjects[self.HVACzonelist[j][0]] if h.Name in self.HVACzonelist[j][3][k]]:
                    SP.Setpoint_Temperature_Schedule_Name = "AHST_Sch_" + self.HVACzonelist[j][2][k]
            elif self.HVACzonelist[j][0] in 'ThermostatSetpoint:SingleCooling':
                for SP in [h for h in self.idf1.idfobjects[self.HVACzonelist[j][0]] if h.Name in self.HVACzonelist[j][3][k]]:
                    SP.Setpoint_Temperature_Schedule_Name = "ACST_Sch_" + self.HVACzonelist[j][2][k]
            elif self.HVACzonelist[j][0] in 'ThermostatSetpoint:DualSetpoint':
                for SP in [h for h in self.idf1.idfobjects[self.HVACzonelist[j][0]] if h.Name in self.HVACzonelist[j][3][k]]:
                    SP.Heating_Setpoint_Temperature_Schedule_Name = "AHST_Sch_" + self.HVACzonelist[j][2][k]
                    SP.Cooling_Setpoint_Temperature_Schedule_Name = "ACST_Sch_" + self.HVACzonelist[j][2][k]


