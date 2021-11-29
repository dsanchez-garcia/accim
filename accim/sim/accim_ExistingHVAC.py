def addForscriptSchExistHVAC(self, verboseMode: bool = True):
    """Add FORSCRIPT Schedules for each zone in existing HVAC zones."""
    HVACzonelist = [i.Zone_or_ZoneList_Name for i in self.idf1.idfobjects['ZONECONTROL:THERMOSTAT']]
    for zn in HVACzonelist:
        if "FORSCRIPT_AHST_" + zn in [sch.Name
                                      for sch
                                      in self.idf1.idfobjects['Schedule:Compact']]:
            if verboseMode:
                print('FORSCRIPT_AHST_' + zn + ' Schedule already was in the model')
        else:
            self.idf1.newidfobject(
                'Schedule:Compact',
                Name="FORSCRIPT_AHST_" + zn,
                Schedule_Type_Limits_Name="Any Number",
                Field_1='Through: 12/31',
                Field_2='For: AllDays',
                Field_3='Until: 24:00,20'
            )
            if verboseMode:
                print('FORSCRIPT_AHST_' + zn + ' Schedule has been added')

        if "FORSCRIPT_ACST_" + zn in [sch.Name
                                      for sch
                                      in self.idf1.idfobjects['Schedule:Compact']]:
            if verboseMode:
                print('FORSCRIPT_ACST_' + zn + ' Schedule already was in the model')
        else:
            self.idf1.newidfobject(
                'Schedule:Compact',
                Name="FORSCRIPT_ACST_" + zn,
                Schedule_Type_Limits_Name="Any Number",
                Field_1='Through: 12/31',
                Field_2='For: AllDays',
                Field_3='Until: 24:00,24'
            )
            if verboseMode:
                print('FORSCRIPT_ACST_' + zn + ' Schedule has been added')

