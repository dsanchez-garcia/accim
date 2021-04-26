"""Add EnergyPlus objects only for SingleZone Mode."""


def addForscriptSchSingleZone(self, verboseMode: bool = True):
    """Add FORSCRIPT schedules for SingleZone accim."""
    if "FORSCRIPT_AHST" in [sch.Name
                            for sch
                            in self.idf1.idfobjects['Schedule:Compact']]:
        if verboseMode:
            print("FORSCRIPT_AHST Schedule already was in the model")
    else:
        self.idf1.newidfobject(
            'Schedule:Compact',
            Name="FORSCRIPT_AHST",
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00,20'
            )
        # todo allow mixed mode for singlezone functions: Name="FORSCRIPT_ACST_"+zonename,
        if verboseMode:
            print("FORSCRIPT_AHST Schedule has been added")
    if "FORSCRIPT_ACST" in [sch.Name
                            for sch
                            in self.idf1.idfobjects['Schedule:Compact']]:
        if verboseMode:
            print("FORSCRIPT_ACST Schedule already was in the model")
    else:
        self.idf1.newidfobject(
            'Schedule:Compact',
            Name="FORSCRIPT_ACST",
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00,24'
            )
        if verboseMode:
            print("FORSCRIPT_ACST Schedule has been added")

    for tsds in [tsds
                 for tsds
                 in self.idf1.idfobjects['ThermostatSetpoint:DualSetpoint']]:
        tsds.Heating_Setpoint_Temperature_Schedule_Name = "FORSCRIPT_AHST"
        tsds.Cooling_Setpoint_Temperature_Schedule_Name = "FORSCRIPT_ACST"
    if verboseMode:
        print('FORSCRIPT_AHST and FORSCRIPT_ACST '
              'has been asigned to all ThermostatSetpoint:DualSetpoint objects')
