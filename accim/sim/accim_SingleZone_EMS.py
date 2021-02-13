"""Add EMS objects only for SingleZone mode."""


def addGlobVarListSingleZone(self):
    """
    Amend Global Variable objects for SingleZone accim to work.

    Remove existing Global Variable objects and
    add correct Global Variable objects for SingleZone accim.
    """
    globalvariablelist = [
        program
        for program in self.idf1.idfobjects["ENERGYMANAGEMENTSYSTEM:GLOBALVARIABLE"]
    ]

    for i in range(len(globalvariablelist)):
        firstglobalvariablelist = self.idf1.idfobjects[
            "ENERGYMANAGEMENTSYSTEM:GLOBALVARIABLE"
        ][-1]
        self.idf1.removeidfobject(firstglobalvariablelist)

    del globalvariablelist

    self.idf1.newidfobject(
        "EnergyManagementSystem:GlobalVariable",
        Erl_Variable_1_Name="ACST",
        Erl_Variable_2_Name="AHST",
        Erl_Variable_3_Name="ACSTnoTol",
        Erl_Variable_4_Name="AHSTnoTol",
        Erl_Variable_5_Name="AdapStand",
        Erl_Variable_6_Name="ACSTaul",
        Erl_Variable_7_Name="ACSTall",
        Erl_Variable_8_Name="AHSTaul",
        Erl_Variable_9_Name="AHSTall",
        Erl_Variable_10_Name="CAT",
        Erl_Variable_11_Name="ACSToffset",
        Erl_Variable_12_Name="AHSToffset",
        Erl_Variable_13_Name="ComfMod",
        Erl_Variable_14_Name="ComfTemp",
        Erl_Variable_15_Name="ACSTtol",
        Erl_Variable_16_Name="AHSTtol",
    )

    for zonename in self.zonenames:
        self.idf1.newidfobject(
            "EnergyManagementSystem:GlobalVariable",
            Erl_Variable_1_Name="ComfHours_" + zonename,
            Erl_Variable_2_Name="DiscomfAppHotHours_" + zonename,
            Erl_Variable_3_Name="DiscomfAppColdHours_" + zonename,
            Erl_Variable_4_Name="DiscomfNonAppHotHours_" + zonename,
            Erl_Variable_5_Name="DiscomfNonAppColdHours_" + zonename,
            Erl_Variable_6_Name="ComfHoursNoApp_" + zonename,
        )


def addEMSSensorsSingleZone(self):
    """Add EMS sensors for SingleZone accim."""
    if "RMOT" in [
        sensor.Name for sensor in self.idf1.idfobjects["EnergyManagementSystem:Sensor"]
    ]:
        print("Not added - RMOT Sensor")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Sensor",
            Name="RMOT",
            OutputVariable_or_OutputMeter_Index_Key_Name="People "
            + self.zonenames_orig[0],
            OutputVariable_or_OutputMeter_Name="Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature",
        )
        print("Added - RMOT Sensor")
    #    print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name=='RMOT'])

    if "PMOT" in [
        sensor.Name for sensor in self.idf1.idfobjects["EnergyManagementSystem:Sensor"]
    ]:
        print("Not added - PMOT Sensor")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Sensor",
            Name="PMOT",
            OutputVariable_or_OutputMeter_Index_Key_Name="People "
            + self.zonenames_orig[0],
            OutputVariable_or_OutputMeter_Name="Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature",
        )
        print("Added - PMOT Sensor")
    #    print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name=='PMOT'])

    for i in range(len(self.zonenames)):
        if self.zonenames[i] + "_OpT" in [
            sensor.Name
            for sensor in self.idf1.idfobjects["EnergyManagementSystem:Sensor"]
        ]:
            print("Not added - " + self.zonenames[i] + "_OpT Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.zonenames[i] + "_OpT",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.zonenames_orig[i],
                OutputVariable_or_OutputMeter_Name="Zone Operative Temperature",
            )
            print("Added - " + self.zonenames[i] + "_OpT Sensor")
    #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_OpT'])

    # if 'HVACConsump' in [sensor.Name for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor']]:
    #     print('Not added - HVACConsump Sensor')
    # else:
    #     self.idf1.newidfobject(
    #         'EnergyManagementSystem:Sensor',
    #         Name='HVACConsump',
    #         OutputVariable_or_OutputMeter_Index_Key_Name='Whole Building',
    #         OutputVariable_or_OutputMeter_Name='Facility Total HVAC Electric Demand Power'
    #         )
    #     print('Added - HVACConsump Sensor')
    #     print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name=='HVACConsump'])


def addEMSActuatorsSingleZone(self):
    """Add EMS actuators for SingleZone accim."""
    actuatorlist = [
        actuator.Name
        for actuator in self.idf1.idfobjects["EnergyManagementSystem:Actuator"]
    ]

    if "FORSCRIPT_AHST_Schedule" in actuatorlist:
        print("Not added - FORSCRIPT_AHST_Schedule Actuator")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Actuator",
            Name="FORSCRIPT_AHST_Schedule",
            Actuated_Component_Unique_Name="FORSCRIPT_AHST",
            Actuated_Component_Type="Schedule:Compact",
            Actuated_Component_Control_Type="Schedule Value",
        )
        print("Added - FORSCRIPT_AHST_Schedule Actuator")
    #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='FORSCRIPT_AHST_Schedule'])

    if "FORSCRIPT_ACST_Schedule" in actuatorlist:
        print("Not added - FORSCRIPT_ACST_Schedule Actuator")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Actuator",
            Name="FORSCRIPT_ACST_Schedule",
            Actuated_Component_Unique_Name="FORSCRIPT_ACST",
            Actuated_Component_Type="Schedule:Compact",
            Actuated_Component_Control_Type="Schedule Value",
        )
        print("Added - FORSCRIPT_ACST_Schedule Actuator")
    #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='FORSCRIPT_ACST_Schedule'])
    del actuatorlist


def addEMSProgramsSingleZone(self):
    """Add EMS programs for SingleZone accim."""
    programlist = [
        program.Name
        for program in self.idf1.idfobjects["EnergyManagementSystem:Program"]
    ]

    if "SetInputData" in programlist:
        print("Not added - SetInputData Program")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Program",
            Name="SetInputData",
            Program_Line_1="set AdapStand = 1",
            Program_Line_2="set CAT = 1",
            Program_Line_3="set ComfMod = 1",
            Program_Line_4="set ACSTtol = -0.25",
            Program_Line_5="set AHSTtol = 0.25",
        )
        print("Added - SetInputData Program")
        # print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetInputData'])

    if "ApplyAST" in programlist:
        print("Not added - ApplyAST Program")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Program",
            Name="ApplyAST",
            Program_Line_1="Set FORSCRIPT_ACST_Schedule = ACST",
            Program_Line_2="Set FORSCRIPT_AHST_Schedule = AHST",
        )
        print("Added - ApplyAST Program")
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'ApplyAST'])

    del programlist


def addOutputVariablesSingleZone(self):
    """Add Output:Variable objects for SingleZone accim."""
    EnvironmentalImpactFactorslist = [
        output for output in self.idf1.idfobjects["Output:EnvironmentalImpactFactors"]
    ]

    for i in range(len(EnvironmentalImpactFactorslist)):
        firstEnvironmentalImpactFactor = self.idf1.idfobjects[
            "Output:EnvironmentalImpactFactors"
        ][-1]
        self.idf1.removeidfobject(firstEnvironmentalImpactFactor)

    outputmeterlist = [output for output in self.idf1.idfobjects["Output:Meter"]]
    for i in range(len(outputmeterlist)):
        firstoutputmeter = self.idf1.idfobjects["Output:Meter"][-1]
        self.idf1.removeidfobject(firstoutputmeter)

    alloutputs = [output for output in self.idf1.idfobjects["Output:Variable"]]
    for i in range(len(alloutputs)):
        firstoutput = self.idf1.idfobjects["Output:Variable"][-1]
        self.idf1.removeidfobject(firstoutput)

    # del EnvironmentalImpactFactorslist,firstEnvironmentalImpactFactor, outputmeterlist, firstoutputmeter, alloutputs, firstoutput

    outputvariablelist = [
        program.Name
        for program in self.idf1.idfobjects["EnergyManagementSystem:OutputVariable"]
    ]
    outputlist = [
        output.Variable_Name for output in self.idf1.idfobjects["Output:Variable"]
    ]
    addittionaloutputs = [
        "Zone Thermostat Operative Temperature",
        "Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature",
        "Cooling Coil Total Cooling Rate",
        "Heating Coil Heating Rate",
        "Facility Total HVAC Electric Demand Power",
        "Facility Total HVAC Electricity Demand Rate",
        "VRF Heat Pump Cooling Electricity Energy",
        "VRF Heat Pump Heating Electricity Energy",
    ]

    for outputvariable in outputvariablelist:
        if outputvariable in outputlist:
            print("Not added - " + outputvariable + " Output:Variable data")
        elif outputvariable.startswith("WIP"):
            print(
                "Not added - "
                + outputvariable
                + " Output:Variable data because its WIP"
            )
        elif outputvariable.startswith("Adaptive Thermal Comfort Cost Index"):
            print(
                "Not added - "
                + outputvariable
                + " Output:Variable data because its ATCCI"
            )
        else:
            self.idf1.newidfobject(
                "Output:Variable",
                Key_Value="*",
                Variable_Name=outputvariable,
                Reporting_Frequency="Hourly",
                Schedule_Name="",
            )
            print("Added - " + outputvariable + " Output:Variable data")
    #        print([output for output in self.idf1.idfobjects['Output:Variable'] if output.Variable_Name == outputvariable])

    for addittionaloutput in addittionaloutputs:
        self.idf1.newidfobject(
            "Output:Variable",
            Key_Value="*",
            Variable_Name=addittionaloutput,
            Reporting_Frequency="Hourly",
            Schedule_Name="",
        )
        print("Added - " + addittionaloutput + " Output:Variable data")

    del (
        outputvariablelist,
        outputlist,
        addittionaloutputs,
    )

    self.idf1.newidfobject(
        "Output:Variable",
        Key_Value="Environment",
        Variable_Name="Site Outdoor Air Drybulb Temperature",
        Reporting_Frequency="Hourly",
        Schedule_Name="",
    )
    print("Added - Site Outdoor Air Drybulb Temperature Output:Variable data")

    self.idf1.newidfobject(
        "Output:Variable",
        Key_Value="FORSCRIPT_AHST",
        Variable_Name="Schedule Value",
        Reporting_Frequency="Hourly",
        Schedule_Name="",
    )
    print("Added - FORSCRIPT_AHST Output:Variable data")

    self.idf1.newidfobject(
        "Output:Variable",
        Key_Value="FORSCRIPT_ACST",
        Variable_Name="Schedule Value",
        Reporting_Frequency="Hourly",
        Schedule_Name="",
    )
    print("Added - FORSCRIPT_ACST Output:Variable data")

    for zonename in self.zonenames_orig:
        self.idf1.newidfobject(
            "Output:Variable",
            Key_Value=zonename,
            Variable_Name="Zone Operative Temperature",
            Reporting_Frequency="Hourly",
            Schedule_Name="",
        )
        print(
            "Added - " + zonename + " Zone Operative Temperature Output:Variable data"
        )
