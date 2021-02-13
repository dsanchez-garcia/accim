"""Add EnergyPlus objects only for SingleZone Mode."""


def addForscriptSchSingleZone(self):
    """Add FORSCRIPT schedules for SingleZone accim."""
    if "FORSCRIPT_AHST" in [
        schedule.Name for schedule in self.idf1.idfobjects["Schedule:Compact"]
    ]:
        print("FORSCRIPT_AHST Schedule already was in the model")
    else:
        self.idf1.newidfobject(
            "Schedule:Compact",
            Name="FORSCRIPT_AHST",
            Schedule_Type_Limits_Name="Any Number",
            Field_1="Through: 12/31",
            Field_2="For: AllDays",
            Field_3="Until: 24:00,20",
        )
        print("FORSCRIPT_AHST Schedule has been added")
    if "FORSCRIPT_ACST" in [
        schedule.Name for schedule in self.idf1.idfobjects["Schedule:Compact"]
    ]:
        print("FORSCRIPT_ACST Schedule already was in the model")
    else:
        self.idf1.newidfobject(
            "Schedule:Compact",
            Name="FORSCRIPT_ACST",
            Schedule_Type_Limits_Name="Any Number",
            Field_1="Through: 12/31",
            Field_2="For: AllDays",
            Field_3="Until: 24:00,24",
        )
        print("FORSCRIPT_ACST Schedule has been added")

    for program in [
        program for program in self.idf1.idfobjects["ThermostatSetpoint:DualSetpoint"]
    ]:
        program.Heating_Setpoint_Temperature_Schedule_Name = "FORSCRIPT_AHST"
        program.Cooling_Setpoint_Temperature_Schedule_Name = "FORSCRIPT_ACST"
    print(
        "FORSCRIPT_AHST and FORSCRIPT_ACST has been asigned to all ThermostatSetpoint:DualSetpoint objects"
    )
