"""Add EMS objects only for MultipleZone."""


def addGlobVarListMultipleZone(self):
    """Remove existing Global Variable objects and add correct Global Variable objects for MultipleZone accim."""
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
        Erl_Variable_17_Name="VST",
        Erl_Variable_18_Name="VSToffset",
        Erl_Variable_19_Name="MaxWindSpeed",
        Erl_Variable_20_Name="VentCtrl",
        Erl_Variable_21_Name="HVACmode",
        Erl_Variable_22_Name="MinOutTemp",
        Erl_Variable_23_Name="MinOToffset",
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


def addEMSSensorsMultipleZone(self):
    """Add EMS sensors for MultipleZone accim."""
    sensorlist = [
        sensor.Name for sensor in self.idf1.idfobjects["EnergyManagementSystem:Sensor"]
    ]

    if "RMOT" in sensorlist:
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

    if "PMOT" in sensorlist:
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
        if self.zonenames[i] + "_OpT" in sensorlist:
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
        if self.zonenames[i] + "_CoolCoil" in sensorlist:
            print("Not added - " + self.zonenames[i] + "_CoolCoil Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.zonenames[i] + "_CoolCoil",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.zonenames_orig[i]
                + " VRF Indoor Unit DX Cooling Coil",
                OutputVariable_or_OutputMeter_Name="Cooling Coil Total Cooling Rate",
            )
            print("Added - " + self.zonenames[i] + "_CoolCoil Sensor")
        #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_CoolCoil'])
        if self.zonenames[i] + "_HeatCoil" in sensorlist:
            print("Not added - " + self.zonenames[i] + "_HeatCoil Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.zonenames[i] + "_HeatCoil",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.zonenames_orig[i]
                + " VRF Indoor Unit DX Heating Coil",
                OutputVariable_or_OutputMeter_Name="Heating Coil Heating Rate",
            )
            print("Added - " + self.zonenames[i] + "_HeatCoil Sensor")
        #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_HeatCoil'])
        if self.zonenames[i] + "_WindSpeed" in sensorlist:
            print("Not added - " + self.zonenames[i] + "_WindSpeed Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.zonenames[i] + "_WindSpeed",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.zonenames_orig[i],
                OutputVariable_or_OutputMeter_Name="Zone Outdoor Air Wind Speed",
            )
            print("Added - " + self.zonenames[i] + "_WindSpeed Sensor")
        #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_WindSpeed'])
        if self.zonenames[i] + "_OutT" in sensorlist:
            print("Not added - " + self.zonenames[i] + "_OutT Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.zonenames[i] + "_OutT",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.zonenames_orig[i],
                OutputVariable_or_OutputMeter_Name="Zone Outdoor Air Drybulb Temperature",
            )
            print("Added - " + self.zonenames[i] + "_OutT Sensor")
    #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_OutT'])

    # if 'HVACConsump' in sensorlist:
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

    for i in range(len(self.windownamelist)):
        if self.windownamelist[i] + "_OpT" in sensorlist:
            print("Not added - " + self.windownamelist[i] + "_OpT Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.windownamelist[i] + "_OpT",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[
                    i
                ][
                    0
                ],
                OutputVariable_or_OutputMeter_Name="Zone Operative Temperature",
            )
            print("Added - " + self.windownamelist[i] + "_OpT Sensor")

        if self.windownamelist[i] + "_CoolCoil" in sensorlist:
            print("Not added - " + self.windownamelist[i] + "_CoolCoil Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.windownamelist[i] + "_CoolCoil",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[
                    i
                ][
                    0
                ]
                + " VRF Indoor Unit DX Cooling Coil",
                OutputVariable_or_OutputMeter_Name="Cooling Coil Total Cooling Rate",
            )
            print("Added - " + self.windownamelist[i] + "_CoolCoil Sensor")

        if self.windownamelist[i] + "_HeatCoil" in sensorlist:
            print("Not added - " + self.windownamelist[i] + "_HeatCoil Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.windownamelist[i] + "_HeatCoil",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[
                    i
                ][
                    0
                ]
                + " VRF Indoor Unit DX Heating Coil",
                OutputVariable_or_OutputMeter_Name="Heating Coil Heating Rate",
            )
            print("Added - " + self.windownamelist[i] + "_HeatCoil Sensor")

        if self.windownamelist[i] + "_WindSpeed" in sensorlist:
            print("Not added - " + self.windownamelist[i] + "_WindSpeed Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.windownamelist[i] + "_WindSpeed",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[
                    i
                ][
                    0
                ],
                OutputVariable_or_OutputMeter_Name="Zone Outdoor Air Wind Speed",
            )
            print("Added - " + self.windownamelist[i] + "_WindSpeed Sensor")

        if self.windownamelist[i] + "_OutT" in sensorlist:
            print("Not added - " + self.windownamelist[i] + "_WindSpeed Sensor")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Sensor",
                Name=self.windownamelist[i] + "_OutT",
                OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[
                    i
                ][
                    0
                ],
                OutputVariable_or_OutputMeter_Name="Zone Outdoor Air Drybulb Temperature",
            )
            print("Added - " + self.windownamelist[i] + "_OutT Sensor")

    if "OutT" in sensorlist:
        print("Not added - OutT Sensor")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Sensor",
            Name="OutT",
            OutputVariable_or_OutputMeter_Index_Key_Name="Environment",
            OutputVariable_or_OutputMeter_Name="Site Outdoor Air Drybulb Temperature",
        )
        print("Added - OutT Sensor")

    del sensorlist


def addEMSActuatorsMultipleZone(self):
    """Add EMS actuators for MultipleZone accim."""
    actuatorlist = [
        actuator.Name
        for actuator in self.idf1.idfobjects["EnergyManagementSystem:Actuator"]
    ]

    for zonename in self.zonenames:
        if "FORSCRIPT_AHST_Schedule_" + zonename in actuatorlist:
            print("Not added - FORSCRIPT_AHST_Sch_" + zonename + " Actuator")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Actuator",
                Name="FORSCRIPT_AHST_Sch_" + zonename,
                Actuated_Component_Unique_Name="FORSCRIPT_AHST_" + zonename,
                Actuated_Component_Type="Schedule:Compact",
                Actuated_Component_Control_Type="Schedule Value",
            )
            print("Added - FORSCRIPT_AHST_Sch_" + zonename + " Actuator")
        #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='FORSCRIPT_AHST_Schedule_'+zonename])

        if "FORSCRIPT_ACST_Schedule_" + zonename in actuatorlist:
            print("Not added - FORSCRIPT_ACST_Sch_" + zonename + " Actuator")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Actuator",
                Name="FORSCRIPT_ACST_Sch_" + zonename,
                Actuated_Component_Unique_Name="FORSCRIPT_ACST_" + zonename,
                Actuated_Component_Type="Schedule:Compact",
                Actuated_Component_Control_Type="Schedule Value",
            )
            print("Added - FORSCRIPT_ACST_Sch_" + zonename + " Actuator")
        #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='FORSCRIPT_ACST_Schedule_'+zonename])

    for i in range(len(self.windownamelist)):
        if self.windownamelist[i] + "_VentOpenFact" in actuatorlist:
            print("Not added - " + self.windownamelist[i] + "_OpT Actuator")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Actuator",
                Name=self.windownamelist[i] + "_VentOpenFact",
                Actuated_Component_Unique_Name=self.windownamelist_orig[i],
                Actuated_Component_Type="AirFlow Network Window/Door Opening",
                Actuated_Component_Control_Type="Venting Opening Factor",
            )
            print("Added - " + self.windownamelist[i] + "_VentOpenFact Actuator")
    del actuatorlist


def addEMSProgramsMultipleZone(self):
    """Add EMS programs for MultipleZone accim."""
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
            Program_Line_3="set ComfMod = 2",
            Program_Line_4="set HVACmode = 2",
            Program_Line_5="set VentCtrl = 0",
            Program_Line_6="set VSToffset = 0",
            Program_Line_7="set MinOToffset = 7",
            Program_Line_8="set MaxWindSpeed = 6",
            Program_Line_9="set ACSTtol = -0.25",
            Program_Line_10="set AHSTtol = 0.25",
        )
        print("Added - SetInputData Program")

    if "SetVST" in programlist:
        print("Not added - SetVST Program")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Program",
            Name="SetVST",
            Program_Line_1="set MinOutTemp = AHST - MinOToffset",
            Program_Line_2="if AdapStand == 0",
            Program_Line_3="if (CurrentTime < 7)",
            Program_Line_4="set VST = (ACST+AHST)/2+VSToffset",
            Program_Line_5="elseif (CurrentTime < 15)",
            Program_Line_6="set VST = 22.5+VSToffset",
            Program_Line_7="elseif (CurrentTime < 23)",
            Program_Line_8="set VST = (ACST+AHST)/2+VSToffset",
            Program_Line_9="elseif (CurrentTime < 24)",
            Program_Line_10="set VST = (ACST+AHST)/2+VSToffset",
            Program_Line_11="endif",
            Program_Line_12="elseif AdapStand == 1",
            Program_Line_13="if (RMOT >= AHSTall) && (RMOT <= ACSTaul)",
            Program_Line_14="set VST = ComfTemp+VSToffset",
            Program_Line_15="else",
            Program_Line_16="set VST = (ACST+AHST)/2+VSToffset",
            Program_Line_17="endif",
            Program_Line_18="elseif AdapStand == 2",
            Program_Line_19="if (PMOT >= AHSTall) && (PMOT <= ACSTaul)",
            Program_Line_20="set VST = ComfTemp+VSToffset",
            Program_Line_21="else",
            Program_Line_22="set VST = (ACST+AHST)/2+VSToffset",
            Program_Line_23="endif",
            Program_Line_24="endif",
        )
        print("Added - SetVST Program")
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetVST'])

    for zonename in self.zonenames:
        if "ApplyAST_MultipleZone_" + zonename in programlist:
            print("Not added - ApplyAST_MultipleZone_" + zonename + " Program")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Program",
                Name="ApplyAST_MultipleZone_" + zonename,
                Program_Line_1="if ("
                + zonename
                + "_OpT>VST)&&("
                + zonename
                + "_OutT < VST)",
                Program_Line_2="if " + zonename + "_CoolCoil==0",
                Program_Line_3="if " + zonename + "_HeatCoil==0",
                Program_Line_4="if ("
                + zonename
                + "_OpT<ACST)&&("
                + zonename
                + "_OutT>MinOutTemp)",
                Program_Line_5="if " + zonename + "_WindSpeed <= MaxWindSpeed",
                Program_Line_6="set Ventilates_HVACmode2_" + zonename + " = 1",
                Program_Line_7="else",
                Program_Line_8="set Ventilates_HVACmode2_" + zonename + " = 0",
                Program_Line_9="endif",
                Program_Line_10="else",
                Program_Line_11="set Ventilates_HVACmode2_" + zonename + " = 0",
                Program_Line_12="endif",
                Program_Line_13="else",
                Program_Line_14="set Ventilates_HVACmode2_" + zonename + " = 0",
                Program_Line_15="endif",
                Program_Line_16="else",
                Program_Line_17="set Ventilates_HVACmode2_" + zonename + " = 0",
                Program_Line_18="endif",
                Program_Line_19="else",
                Program_Line_20="set Ventilates_HVACmode2_" + zonename + " = 0",
                Program_Line_21="endif",
                Program_Line_22="if VentCtrl == 0",
                Program_Line_23="if " + zonename + "_OutT < " + zonename + "_OpT",
                Program_Line_24="if " + zonename + "_OutT>MinOutTemp",
                Program_Line_25="if " + zonename + "_OpT > VST",
                Program_Line_26="if " + zonename + "_WindSpeed <= MaxWindSpeed",
                Program_Line_27="set Ventilates_HVACmode1_" + zonename + " = 1",
                Program_Line_28="else",
                Program_Line_29="set Ventilates_HVACmode1_" + zonename + " = 0",
                Program_Line_30="endif",
                Program_Line_31="else",
                Program_Line_32="set Ventilates_HVACmode1_" + zonename + " = 0",
                Program_Line_33="endif",
                Program_Line_34="else",
                Program_Line_35="set Ventilates_HVACmode1_" + zonename + " = 0",
                Program_Line_36="endif",
                Program_Line_37="else",
                Program_Line_38="set Ventilates_HVACmode1_" + zonename + " = 0",
                Program_Line_39="endif",
                Program_Line_40="elseif VentCtrl == 1",
                Program_Line_41="if " + zonename + "_OutT<" + zonename + "_OpT",
                Program_Line_42="if " + zonename + "_OutT>MinOutTemp",
                Program_Line_43="if " + zonename + "_OpT > ACSTnoTol",
                Program_Line_44="if " + zonename + "_WindSpeed <= MaxWindSpeed",
                Program_Line_45="set Ventilates_HVACmode1_" + zonename + " = 1",
                Program_Line_46="else",
                Program_Line_47="set Ventilates_HVACmode1_" + zonename + " = 0",
                Program_Line_48="endif",
                Program_Line_49="else",
                Program_Line_50="set Ventilates_HVACmode1_" + zonename + " = 0",
                Program_Line_51="endif",
                Program_Line_52="else",
                Program_Line_53="set Ventilates_HVACmode1_" + zonename + " = 0",
                Program_Line_54="endif",
                Program_Line_55="else",
                Program_Line_56="set Ventilates_HVACmode1_" + zonename + " = 0",
                Program_Line_57="endif",
                Program_Line_58="endif",
                Program_Line_59="if HVACmode == 0",
                Program_Line_60="set FORSCRIPT_ACST_Sch_" + zonename + " = ACST",
                Program_Line_61="set FORSCRIPT_AHST_Sch_" + zonename + " = AHST",
                Program_Line_62="elseif HVACmode == 1",
                Program_Line_63="Set FORSCRIPT_ACST_Sch_" + zonename + " = 100",
                Program_Line_64="Set FORSCRIPT_AHST_Sch_" + zonename + " = -100",
                Program_Line_65="elseif HVACmode == 2",
                Program_Line_66="if Ventilates_HVACmode2_" + zonename + " == 0",
                Program_Line_67="set FORSCRIPT_ACST_Sch_" + zonename + " = ACST",
                Program_Line_68="set FORSCRIPT_AHST_Sch_" + zonename + " = AHST",
                Program_Line_69="endif",
                Program_Line_70="endif",
            )
            print("Added - ApplyAST_MultipleZone_" + zonename + " Program")
        #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'ApplyAST_MultipleZone_'+windowname])

    for windowname in self.windownamelist:
        if "SetWindowOperation_" + windowname in programlist:
            print("Not added - SetWindowOperation_" + windowname + " Program")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Program",
                Name="SetWindowOperation_" + windowname,
                Program_Line_1="if ("
                + windowname
                + "_OpT>VST)&&("
                + windowname
                + "_OutT < VST)",
                Program_Line_2="if " + windowname + "_CoolCoil==0",
                Program_Line_3="if " + windowname + "_HeatCoil==0",
                Program_Line_4="if ("
                + windowname
                + "_OpT<ACST)&&("
                + windowname
                + "_OutT>MinOutTemp)",
                Program_Line_5="if " + windowname + "_WindSpeed <= MaxWindSpeed",
                Program_Line_6="set Ventilates_HVACmode2_" + windowname + " = 1",
                Program_Line_7="else",
                Program_Line_8="set Ventilates_HVACmode2_" + windowname + " = 0",
                Program_Line_9="endif",
                Program_Line_10="else",
                Program_Line_11="set Ventilates_HVACmode2_" + windowname + " = 0",
                Program_Line_12="endif",
                Program_Line_13="else",
                Program_Line_14="set Ventilates_HVACmode2_" + windowname + " = 0",
                Program_Line_15="endif",
                Program_Line_16="else",
                Program_Line_17="set Ventilates_HVACmode2_" + windowname + " = 0",
                Program_Line_18="endif",
                Program_Line_19="else",
                Program_Line_20="set Ventilates_HVACmode2_" + windowname + " = 0",
                Program_Line_21="endif",
                Program_Line_22="if VentCtrl == 0",
                Program_Line_23="if " + windowname + "_OutT < " + windowname + "_OpT",
                Program_Line_24="if " + windowname + "_OutT>MinOutTemp",
                Program_Line_25="if " + windowname + "_OpT > VST",
                Program_Line_26="if " + windowname + "_WindSpeed <= MaxWindSpeed",
                Program_Line_27="set Ventilates_HVACmode1_" + windowname + " = 1",
                Program_Line_28="else",
                Program_Line_29="set Ventilates_HVACmode1_" + windowname + " = 0",
                Program_Line_30="endif",
                Program_Line_31="else",
                Program_Line_32="set Ventilates_HVACmode1_" + windowname + " = 0",
                Program_Line_33="endif",
                Program_Line_34="else",
                Program_Line_35="set Ventilates_HVACmode1_" + windowname + " = 0",
                Program_Line_36="endif",
                Program_Line_37="else",
                Program_Line_38="set Ventilates_HVACmode1_" + windowname + " = 0",
                Program_Line_39="endif",
                Program_Line_40="elseif VentCtrl == 1",
                Program_Line_41="if " + windowname + "_OutT<" + windowname + "_OpT",
                Program_Line_42="if " + windowname + "_OutT>MinOutTemp",
                Program_Line_43="if " + windowname + "_OpT > ACSTnoTol",
                Program_Line_44="if " + windowname + "_WindSpeed <= MaxWindSpeed",
                Program_Line_45="set Ventilates_HVACmode1_" + windowname + " = 1",
                Program_Line_46="else",
                Program_Line_47="set Ventilates_HVACmode1_" + windowname + " = 0",
                Program_Line_48="endif",
                Program_Line_49="else",
                Program_Line_50="set Ventilates_HVACmode1_" + windowname + " = 0",
                Program_Line_51="endif",
                Program_Line_52="else",
                Program_Line_53="set Ventilates_HVACmode1_" + windowname + " = 0",
                Program_Line_54="endif",
                Program_Line_55="else",
                Program_Line_56="set Ventilates_HVACmode1_" + windowname + " = 0",
                Program_Line_57="endif",
                Program_Line_58="endif",
                Program_Line_59="if HVACmode == 0",
                Program_Line_60="set " + windowname + "_VentOpenFact = 0",
                Program_Line_61="elseif HVACmode == 1",
                Program_Line_62="if Ventilates_HVACmode1_" + windowname + " == 1",
                Program_Line_63="set " + windowname + "_VentOpenFact = 1",
                Program_Line_64="else",
                Program_Line_65="set " + windowname + "_VentOpenFact = 0",
                Program_Line_66="endif",
                Program_Line_67="elseif HVACmode == 2",
                Program_Line_68="if Ventilates_HVACmode2_" + windowname + " == 1",
                Program_Line_69="set " + windowname + "_VentOpenFact = 1",
                Program_Line_70="else",
                Program_Line_71="set " + windowname + "_VentOpenFact = 0",
                Program_Line_72="endif",
                Program_Line_73="endif",
            )
            print("Added - SetWindowOperation_" + windowname + " Program")
        #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetWindowOperation_'+windowname])

    del programlist


def addEMSOutputVariableMultipleZone(self):
    """Add EMS output variables for MultipleZone accim."""
    outputvariablelist = [
        program.Name
        for program in self.idf1.idfobjects["EnergyManagementSystem:OutputVariable"]
    ]

    if "Ventilation Setpoint Temperature" in outputvariablelist:
        print("Not added - Ventilation Setpoint Temperature Output Variable")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:OutputVariable",
            Name="Ventilation Setpoint Temperature",
            EMS_Variable_Name="VST",
            Type_of_Data_in_Variable="Averaged",
            Update_Frequency="ZoneTimestep",
            EMS_Program_or_Subroutine_Name="",
            Units="C",
        )
        print("Added - Ventilation Setpoint Temperature Output Variable")
    #    print([outputvariable for outputvariable in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable'] if outputvariable.Name == 'Ventilation Setpoint Temperature'])

    if "Minimum Outdoor Temperature for MultipleZone ventilation" in outputvariablelist:
        print(
            "Not added - Minimum Outdoor Temperature for MultipleZone ventilation Output Variable"
        )
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:OutputVariable",
            Name="Minimum Outdoor Temperature for MultipleZone ventilation",
            EMS_Variable_Name="MinOutTemp",
            Type_of_Data_in_Variable="Averaged",
            Update_Frequency="ZoneTimestep",
            EMS_Program_or_Subroutine_Name="",
            Units="C",
        )
        print("Added - Ventilation Setpoint Temperature Output Variable")
    #    print([outputvariable for outputvariable in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable'] if outputvariable.Name == 'Minimum Outdoor Temperature for MultipleZone ventilation'])
    del outputvariablelist


def addOutputVariablesMultipleZone(self):
    """Add Output:Variable objects for MultipleZone accim."""
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
        outputvariable.Name
        for outputvariable in self.idf1.idfobjects[
            "EnergyManagementSystem:OutputVariable"
        ]
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
        "AFN Surface Venting Window or Door Opening Factor",
        "AFN Zone Infiltration Air Change Rate",
        "AFN Zone Infiltration Volume",
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

    zonenames = [
        sub.replace(":", "_")
        for sub in ([zone.Name for zone in self.idf1.idfobjects["ZONE"]])
    ]
    for zonename in zonenames:
        self.idf1.newidfobject(
            "Output:Variable",
            Key_Value="FORSCRIPT_AHST_" + zonename,
            Variable_Name="Schedule Value",
            Reporting_Frequency="Hourly",
            Schedule_Name="",
        )
        print("Added - FORSCRIPT_AHST_" + zonename + " Output:Variable data")

        self.idf1.newidfobject(
            "Output:Variable",
            Key_Value="FORSCRIPT_ACST_" + zonename,
            Variable_Name="Schedule Value",
            Reporting_Frequency="Hourly",
            Schedule_Name="",
        )
        print("Added - FORSCRIPT_ACST_" + zonename + " Output:Variable data")

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

        self.idf1.newidfobject(
            "Output:Variable",
            Key_Value=zonename + " VRF Indoor Unit DX Cooling Coil",
            Variable_Name="Cooling Coil Total Cooling Rate",
            Reporting_Frequency="Hourly",
            Schedule_Name="",
        )
        print(
            "Added - "
            + zonename
            + " VRF Indoor Unit DX Cooling Coil Output:Variable data"
        )

        self.idf1.newidfobject(
            "Output:Variable",
            Key_Value=zonename + " VRF Indoor Unit DX Heating Coil",
            Variable_Name="Heating Coil Heating Rate",
            Reporting_Frequency="Hourly",
            Schedule_Name="",
        )
        print(
            "Added - "
            + zonename
            + " VRF Indoor Unit DX Heating Coil Output:Variable data"
        )

        self.idf1.newidfobject(
            "Output:Variable",
            Key_Value=zonename,
            Variable_Name="Zone Outdoor Air Wind Speed",
            Reporting_Frequency="Hourly",
            Schedule_Name="",
        )
        print(
            "Added - " + zonename + " Zone Outdoor Air Wind Speed Output:Variable data"
        )
