def addForscriptSchExistHVAC(self, verboseMode: bool = True):
    """Add FORSCRIPT Schedules for each zone in existing HVAC zones."""
    for i in range(len(self.HVACzonelist)):
        if len(self.HVACzonelist[i][3]) == 0:
            continue
        else:
            if 'ThermostatSetpoint:DualSetpoint' in self.HVACzonelist[i][0]:
                for j in range(len(self.HVACzonelist[i][2])):
                    if "FORSCRIPT_AHST_" + self.HVACzonelist[i][2][j] in [sch.Name
                                                                     for sch
                                                                     in self.idf1.idfobjects['Schedule:Compact']]:
                        if verboseMode:
                            print('FORSCRIPT_AHST_' + self.HVACzonelist[i][2][j] + ' Schedule already was in the model')
                    else:
                        self.idf1.newidfobject(
                            'Schedule:Compact',
                            Name="FORSCRIPT_AHST_" + self.HVACzonelist[i][2][j],
                            Schedule_Type_Limits_Name="Any Number",
                            Field_1='Through: 12/31',
                            Field_2='For: AllDays',
                            Field_3='Until: 24:00,20'
                        )
                        if verboseMode:
                            print('FORSCRIPT_AHST_' + self.HVACzonelist[i][2][j] + ' Schedule has been added')

                    if "FORSCRIPT_ACST_" + self.HVACzonelist[i][2][j] in [sch.Name
                                                                     for sch
                                                                     in self.idf1.idfobjects['Schedule:Compact']]:
                        if verboseMode:
                            print('FORSCRIPT_ACST_' + self.HVACzonelist[i][2][j] + ' Schedule already was in the model')
                    else:
                        self.idf1.newidfobject(
                            'Schedule:Compact',
                            Name="FORSCRIPT_ACST_" + self.HVACzonelist[i][2][j],
                            Schedule_Type_Limits_Name="Any Number",
                            Field_1='Through: 12/31',
                            Field_2='For: AllDays',
                            Field_3='Until: 24:00,24'
                        )
                        if verboseMode:
                            print('FORSCRIPT_ACST_' + self.HVACzonelist[i][2][j] + ' Schedule has been added')
            elif 'ThermostatSetpoint:SingleHeating' in self.HVACzonelist[i][0]:
                for j in range(len(self.HVACzonelist[i][2])):
                    if "FORSCRIPT_AHST_" + self.HVACzonelist[i][2][j] in [sch.Name
                                                                     for sch
                                                                     in self.idf1.idfobjects['Schedule:Compact']]:
                        if verboseMode:
                            print('FORSCRIPT_AHST_' + self.HVACzonelist[i][2][j] + ' Schedule already was in the model')
                    else:
                        self.idf1.newidfobject(
                            'Schedule:Compact',
                            Name="FORSCRIPT_AHST_" + self.HVACzonelist[i][2][j],
                            Schedule_Type_Limits_Name="Any Number",
                            Field_1='Through: 12/31',
                            Field_2='For: AllDays',
                            Field_3='Until: 24:00,20'
                        )
                        if verboseMode:
                            print('FORSCRIPT_AHST_' + self.HVACzonelist[i][2][j] + ' Schedule has been added')
            elif 'ThermostatSetpoint:SingleCooling' in self.HVACzonelist[i][0]:
                if "FORSCRIPT_ACST_" + self.HVACzonelist[i][2][j] in [sch.Name
                                                                 for sch
                                                                 in self.idf1.idfobjects['Schedule:Compact']]:
                    if verboseMode:
                        print('FORSCRIPT_ACST_' + self.HVACzonelist[i][2][j] + ' Schedule already was in the model')
                else:
                    self.idf1.newidfobject(
                        'Schedule:Compact',
                        Name="FORSCRIPT_ACST_" + self.HVACzonelist[i][2][j],
                        Schedule_Type_Limits_Name="Any Number",
                        Field_1='Through: 12/31',
                        Field_2='For: AllDays',
                        Field_3='Until: 24:00,24'
                    )
                    if verboseMode:
                        print('FORSCRIPT_ACST_' + self.HVACzonelist[i][2][j] + ' Schedule has been added')

    for j in range(len(self.HVACzonelist)):
        for k in range(len(self.HVACzonelist[j][3])):
            if self.HVACzonelist[j][0] in 'ThermostatSetpoint:SingleHeating':
                for SP in [h for h in self.idf1.idfobjects[self.HVACzonelist[j][0]] if h.Name in self.HVACzonelist[j][3][k]]:
                    SP.Setpoint_Temperature_Schedule_Name = "FORSCRIPT_AHST_" + self.HVACzonelist[j][2][k]
            elif self.HVACzonelist[j][0] in 'ThermostatSetpoint:SingleCooling':
                for SP in [h for h in self.idf1.idfobjects[self.HVACzonelist[j][0]] if h.Name in self.HVACzonelist[j][3][k]]:
                    SP.Setpoint_Temperature_Schedule_Name = "FORSCRIPT_ACST_" + self.HVACzonelist[j][2][k]
            elif self.HVACzonelist[j][0] in 'ThermostatSetpoint:DualSetpoint':
                for SP in [h for h in self.idf1.idfobjects[self.HVACzonelist[j][0]] if h.Name in self.HVACzonelist[j][3][k]]:
                    SP.Heating_Setpoint_Temperature_Schedule_Name = "FORSCRIPT_AHST_" + self.HVACzonelist[j][2][k]
                    SP.Cooling_Setpoint_Temperature_Schedule_Name = "FORSCRIPT_ACST_" + self.HVACzonelist[j][2][k]

