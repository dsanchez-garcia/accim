"""Add EnergyPlus objects only for VRFsystem."""


def addOpTempTherm(self, verboseMode : bool = True):
    """
    Amend ZoneControl:Thermostat:OperativeTemperature objects.

    Add ZoneControl:Thermostat:OperativeTemperature objects for each zone.
    """
    for zonename_orig in self.zonenames_orig:
        if zonename_orig+' Thermostat' in [thermostat.Thermostat_Name
                                           for thermostat
                                           in self.idf1.idfobjects
                                           ['ZoneControl:Thermostat:OperativeTemperature']]:
            if verboseMode:
                print(zonename_orig+' Thermostat already was in the model')
        else:
            self.idf1.newidfobject(
                'ZoneControl:Thermostat:OperativeTemperature',
                Thermostat_Name=zonename_orig+" Thermostat",
                Radiative_Fraction_Input_Mode="Scheduled",
                Fixed_Radiative_Fraction='',
                Radiative_Fraction_Schedule_Name='TypOperativeTempControlSch'
                )
            if verboseMode:
                print(zonename_orig+' Thermostat has been added')


def addBaseSchedules(self, verboseMode : bool = True):
    """
    Amend Schedule:Compact objects.

    Checks Schedule:Compact objects needed for accim,
    and add them in case these are not in the model
    """
    if "On" in [schedule.Name for schedule in self.idf1.idfobjects['Schedule:Compact']]:
        if verboseMode:
            print("On Schedule already was in the model")
    else:
        self.idf1.newidfobject(
            'Schedule:Compact',
            Name="On",
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00,1'
            )
        if verboseMode:
            print("On Schedule has been added")


def setAvailSchOn(self, verboseMode: bool = True):
    """
    Amend availability schedules.

    Assign On Compact:Schedule to heating and cooling availability
    schedule names.
    """
    for schedule in [i for i in self.idf1.idfobjects['ZoneHVAC:IdealLoadsAirSystem']]:
        schedule.Heating_Availability_Schedule_Name='On'
        schedule.Cooling_Availability_Schedule_Name='On'
    if verboseMode:
        print('All ZoneHVAC:IdealLoadsAirSystem '
              'Heating and Cooling availability schedules has been set to on')


def addVRFsystemSch(self, verboseMode: bool = True):
    """
    Amend Schedule:Compact objects for VRFsystem.

    Add Schedule:Compact objects needed for VRFsystem to work,
    other than FORSCRIPT Schedules.
    """
    addVRFsystemSch_dict = {
        'On 24/7': 'Until: 24:00,1',
        'Control type schedule: Always 4': 'Until: 24:00,4',
        'Relative humidity setpoint schedule: Always 50.00': 'Until: 24:00,50',
        'Heating Fanger comfort setpoint: Always -0.5': 'Until: 24:00,-0.5',
        'Cooling Fanger comfort setpoint: Always  0.1': 'Until: 24:00, 0.1',
        'Zone CO2 setpoint: Always 900ppm': 'Until: 24:00, 900',
        'Min CO2 concentration: Always 600ppm': 'Until: 24:00, 600',
        'Generic contaminant setpoint: Always 0.5ppm': 'Until: 24:00, 0.5',
        'Air distribution effectiveness (always 1)': 'Until: 24:00, 1'
        }
    for i in addVRFsystemSch_dict:
        if i in [schedule.Name for schedule
                 in self.idf1.idfobjects['Schedule:Compact']]:
            if verboseMode:
                print(i+" Schedule already was in the model")
        else:
            self.idf1.newidfobject('Schedule:Compact',
                                   Name=i,
                                   Schedule_Type_Limits_Name="Any Number",
                                   Field_1='Through: 12/31',
                                   Field_2='For: AllDays',
                                   Field_3=addVRFsystemSch_dict[i])
            if verboseMode:
                print(i+" Schedule has been added")

    if "VRF Heating Cooling (Northern Hemisphere)" in [schedule.Name
                                                       for schedule
                                                       in self.idf1.idfobjects
                                                       ['Schedule:Compact']]:
        if verboseMode:
            print("VRF Heating Cooling (Northern Hemisphere) Schedule already was in the model")
    else:
        self.idf1.newidfobject(
            'Schedule:Compact',
            Name="VRF Heating Cooling (Northern Hemisphere)",
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 31 Mar',
            Field_2='For: AllDays',
            Field_3='Until: 24:00, 0',
            Field_4='Through: 30 Sep',
            Field_5='For: AllDays',
            Field_6='Until: 24:00, 1',
            Field_7='Through: 31 Dec',
            Field_8='For: AllDays',
            Field_9='Until: 24:00, 0')
        if verboseMode:
            print("VRF Heating Cooling (Northern Hemisphere) Schedule has been added")


def addCurveObj(self, verboseMode: bool = True):
    """Add Curve Objects needed for VRFsystem to work."""
    # curvecubiclist=([i for i in self.idf1.idfobjects['Curve:Cubic']])
    # print(curvecubiclist)

    if 'DefaultFanEffRatioCurve' in [i.Name for i in self.idf1.idfobjects['Curve:Cubic']]:
        if verboseMode:
            print('DefaultFanEffRatioCurve Curve:Cubic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Cubic',
            Name='DefaultFanEffRatioCurve',
            Coefficient1_Constant='0.33856828',
            Coefficient2_x='1.72644131',
            Coefficient3_x2='-1.49280132',
            Coefficient4_x3='0.42776208',
            Minimum_Value_of_x='0.5',
            Maximum_Value_of_x='1.5',
            Minimum_Curve_Output='0.3',
            Maximum_Curve_Output='1.0',
            Input_Unit_Type_for_X='',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("DefaultFanEffRatioCurve Curve:Cubic Object has been added")

    if 'VRFTUCoolCapFT' in [i.Name for i in self.idf1.idfobjects['Curve:Cubic']]:
        if verboseMode:
            print('VRFTUCoolCapFT Curve:Cubic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Cubic',
            Name='VRFTUCoolCapFT',
            Coefficient1_Constant='0.504547273506488',
            Coefficient2_x='0.0288891279198444',
            Coefficient3_x2='-0.000010819418650677',
            Coefficient4_x3='0.0000101359395177008',
            Minimum_Value_of_x='0.0',
            Maximum_Value_of_x='50.0',
            Minimum_Curve_Output='0.5',
            Maximum_Curve_Output='1.5',
            Input_Unit_Type_for_X='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFTUCoolCapFT Curve:Cubic Object has been added")

    if 'VRFTUHeatCapFT' in [i.Name for i in self.idf1.idfobjects['Curve:Cubic']]:
        if verboseMode:
            print('VRFTUHeatCapFT Curve:Cubic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Cubic',
            Name='VRFTUHeatCapFT',
            Coefficient1_Constant='-0.390708928227928',
            Coefficient2_x='0.261815023760162',
            Coefficient3_x2='-0.0130431603151873',
            Coefficient4_x3='0.000178131745997821',
            Minimum_Value_of_x='0.0',
            Maximum_Value_of_x='50.0',
            Minimum_Curve_Output='0.5',
            Maximum_Curve_Output='1.5',
            Input_Unit_Type_for_X='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFTUHeatCapFT Curve:Cubic Object has been added")

    if 'VRFCoolCapFTBoundary' in [i.Name for i in self.idf1.idfobjects['Curve:Cubic']]:
        if verboseMode:
            print('VRFCoolCapFTBoundary Curve:Cubic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Cubic',
            Name='VRFCoolCapFTBoundary',
            Coefficient1_Constant='25.73473775',
            Coefficient2_x='-0.03150043',
            Coefficient3_x2='-0.01416595',
            Coefficient4_x3='0',
            Minimum_Value_of_x='11',
            Maximum_Value_of_x='30',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("VRFCoolCapFTBoundary Curve:Cubic Object has been added")

    if 'VRFCoolEIRFTBoundary' in [i.Name for i in self.idf1.idfobjects['Curve:Cubic']]:
        print('VRFCoolEIRFTBoundary Curve:Cubic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Cubic',
            Name='VRFCoolEIRFTBoundary',
            Coefficient1_Constant='25.73473775',
            Coefficient2_x='-0.03150043',
            Coefficient3_x2='-0.01416595',
            Coefficient4_x3='0',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='24',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("VRFCoolEIRFTBoundary Curve:Cubic Object has been added")

    if 'CoolingEIRLowPLR' in [i.Name for i in self.idf1.idfobjects['Curve:Cubic']]:
        if verboseMode:
            print('CoolingEIRLowPLR Curve:Cubic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Cubic',
            Name='CoolingEIRLowPLR',
            Coefficient1_Constant='0.4628123',
            Coefficient2_x='-1.0402406',
            Coefficient3_x2='2.17490997',
            Coefficient4_x3='-0.5974817',
            Minimum_Value_of_x='0',
            Maximum_Value_of_x='1',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Output_Unit_Type='Capacity'
            )
        if verboseMode:
            print("CoolingEIRLowPLR Curve:Cubic Object has been added")

    if 'VRFHeatCapFTBoundary' in [i.Name for i in self.idf1.idfobjects['Curve:Cubic']]:
        if verboseMode:
            print('VRFHeatCapFTBoundary Curve:Cubic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Cubic',
            Name='VRFHeatCapFTBoundary',
            Coefficient1_Constant='-7.6000882',
            Coefficient2_x='3.05090016',
            Coefficient3_x2='-0.1162844',
            Coefficient4_x3='0.0',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='27',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("VRFHeatCapFTBoundary Curve:Cubic Object has been added")

    if 'VRFHeatEIRFTBoundary' in [i.Name for i in self.idf1.idfobjects['Curve:Cubic']]:
        if verboseMode:
            print('VRFHeatEIRFTBoundary Curve:Cubic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Cubic',
            Name='VRFHeatEIRFTBoundary',
            Coefficient1_Constant='-7.6000882',
            Coefficient2_x='3.05090016',
            Coefficient3_x2='-0.1162844',
            Coefficient4_x3='0.0',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='27',
            Minimum_Curve_Output='-20',
            Maximum_Curve_Output='15',
            Input_Unit_Type_for_X='Temperature',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("VRFHeatEIRFTBoundary Curve:Cubic Object has been added")

    if 'HeatingEIRLowPLR' in [i.Name for i in self.idf1.idfobjects['Curve:Cubic']]:
        if verboseMode:
            print('HeatingEIRLowPLR Curve:Cubic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Cubic',
            Name='HeatingEIRLowPLR',
            Coefficient1_Constant='0.1400093',
            Coefficient2_x='0.6415002',
            Coefficient3_x2='0.1339047',
            Coefficient4_x3='0.0845859',
            Minimum_Value_of_x='0',
            Maximum_Value_of_x='1',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Dimensionless',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("HeatingEIRLowPLR Curve:Cubic Object has been added")

    # curveexponentlist=[i for i in self.idf1.idfobjects['Curve:Exponent']]
    # print(curveexponentlist)

    if 'DefaultFanPowerRatioCurve' in [i.Name for i in self.idf1.idfobjects['Curve:Exponent']]:
        if verboseMode:
            print('DefaultFanPowerRatioCurve Curve:Exponent Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Exponent',
            Name='DefaultFanPowerRatioCurve',
            Coefficient1_Constant='0',
            Coefficient2_Constant='1',
            Coefficient3_Constant='3',
            Minimum_Value_of_x='0',
            Maximum_Value_of_x='1.5',
            Minimum_Curve_Output='0.01',
            Maximum_Curve_Output='1.5',
            Input_Unit_Type_for_X='',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("DefaultFanPowerRatioCurve Curve:Exponent Object has been added")

    # curvebiquadraticlist=[i for i in self.idf1.idfobjects['Curve:Biquadratic']]
    # print(curvebiquadraticlist)

    if 'DXHtgCoilDefrostEIRFT' in [i.Name for i in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('DXHtgCoilDefrostEIRFT Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='DXHtgCoilDefrostEIRFT',
            Coefficient1_Constant='1.0',
            Coefficient2_x='0.0',
            Coefficient3_x2='0.0',
            Coefficient4_y='0.0',
            Coefficient5_y2='0',
            Coefficient6_xy='0',
            Minimum_Value_of_x='0.0',
            Maximum_Value_of_x='50.0',
            Minimum_Value_of_y='0.0',
            Maximum_Value_of_y='50.0',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("DXHtgCoilDefrostEIRFT Curve:Biquadratic Object has been added")

    if 'VRFCoolCapFT' in [i.Name for i in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('VRFCoolCapFT Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRFCoolCapFT',
            Coefficient1_Constant='0.576882692',
            Coefficient2_x='0.017447952',
            Coefficient3_x2='0.000583269',
            Coefficient4_y='-1.76324E-06',
            Coefficient5_y2='-7.474E-09',
            Coefficient6_xy='-1.30413E-07',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='24',
            Minimum_Value_of_y='-5',
            Maximum_Value_of_y='23',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFCoolCapFT Curve:Biquadratic Object has been added")

    if 'VRFCoolCapFTHi' in [i.Name for i in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('VRFCoolCapFTHi Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRFCoolCapFTHi',
            Coefficient1_Constant='0.6867358',
            Coefficient2_x='0.0207631',
            Coefficient3_x2='0.0005447',
            Coefficient4_y='-0.0016218',
            Coefficient5_y2='-4.259E-07',
            Coefficient6_xy='-0.0003392',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='24',
            Minimum_Value_of_y='16',
            Maximum_Value_of_y='43',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFCoolCapFTHi Curve:Biquadratic Object has been added")

    if 'VRFCoolEIRFT' in [i.Name for i in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('VRFCoolEIRFT Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRFCoolEIRFT',
            Coefficient1_Constant='0.989010541',
            Coefficient2_x='-0.02347967',
            Coefficient3_x2='0.000199711',
            Coefficient4_y='0.005968336',
            Coefficient5_y2='-1.0289E-07',
            Coefficient6_xy='-0.00015686',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='24',
            Minimum_Value_of_y='-5',
            Maximum_Value_of_y='23',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFCoolEIRFT Curve:Biquadratic Object has been added")

    if 'VRFCoolEIRFTHi' in [i.Name for i in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('VRFCoolEIRFTHi Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRFCoolEIRFTHi',
            Coefficient1_Constant='0.14351470',
            Coefficient2_x='0.01860035',
            Coefficient3_x2='-0.0003954',
            Coefficient4_y='0.02485219',
            Coefficient5_y2='0.00016329',
            Coefficient6_xy='-0.0006244',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='24',
            Minimum_Value_of_y='16',
            Maximum_Value_of_y='43',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFCoolEIRFTHi Curve:Biquadratic Object has been added")

    if 'VRFHeatCapFT' in [i.Name for i in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('VRFHeatCapFT Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRFHeatCapFT',
            Coefficient1_Constant='1.014599599',
            Coefficient2_x='-0.002506703',
            Coefficient3_x2='-0.000141599',
            Coefficient4_y='0.026931595',
            Coefficient5_y2='1.83538E-06',
            Coefficient6_xy='-0.000358147',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='27',
            Minimum_Value_of_y='-20',
            Maximum_Value_of_y='15',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFHeatCapFT Curve:Biquadratic Object has been added")

    if 'VRFHeatCapFTHi' in [i.Name for i in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('VRFHeatCapFTHi Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRFHeatCapFTHi',
            Coefficient1_Constant='1.161134821',
            Coefficient2_x='0.027478868',
            Coefficient3_x2='-0.00168795',
            Coefficient4_y='0.001783378',
            Coefficient5_y2='2.03208E-06',
            Coefficient6_xy='-6.8969E-05',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='27',
            Minimum_Value_of_y='-10',
            Maximum_Value_of_y='15',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFHeatCapFTHi Curve:Biquadratic Object has been added")

    if 'VRFHeatEIRFT' in [i.Name for i in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('VRFHeatEIRFT Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRFHeatEIRFT',
            Coefficient1_Constant='0.87465501',
            Coefficient2_x='-0.01319754',
            Coefficient3_x2='0.00110307',
            Coefficient4_y='-0.0133118',
            Coefficient5_y2='0.00089017',
            Coefficient6_xy='-0.00012766',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='27',
            Minimum_Value_of_y='-20',
            Maximum_Value_of_y='12',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFHeatEIRFT Curve:Biquadratic Object has been added")

    if 'VRFHeatEIRFTHi' in [i.Name for i in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('VRFHeatEIRFTHi Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRFHeatEIRFTHi',
            Coefficient1_Constant='2.504005146',
            Coefficient2_x='-0.05736767',
            Coefficient3_x2='4.07336E-05',
            Coefficient4_y='-0.12959669',
            Coefficient5_y2='0.00135839',
            Coefficient6_xy='0.00317047',
            Minimum_Value_of_x='15',
            Maximum_Value_of_x='27',
            Minimum_Value_of_y='-10',
            Maximum_Value_of_y='15',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRFHeatEIRFTHi Curve:Biquadratic Object has been added")

    if 'CoolingLengthCorrectionFactor' in [i.Name
                                           for i
                                           in self.idf1.idfobjects['Curve:Biquadratic']]:
        if verboseMode:
            print('CoolingLengthCorrectionFactor Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='CoolingLengthCorrectionFactor',
            Coefficient1_Constant='1.0693794',
            Coefficient2_x='-0.0014951',
            Coefficient3_x2='2.56E-06',
            Coefficient4_y='-0.1151104',
            Coefficient5_y2='0.0511169',
            Coefficient6_xy='-0.0004369',
            Minimum_Value_of_x='8',
            Maximum_Value_of_x='175',
            Minimum_Value_of_y='0.5',
            Maximum_Value_of_y='1.5',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("CoolingLengthCorrectionFactor Curve:Biquadratic Object has been added")

    if 'VRF Piping Correction Factor for Length in Heating Mode' in [i.Name
                                                                     for i
                                                                     in self.idf1.idfobjects
                                                                     ['Curve:Biquadratic']]:
        if verboseMode:
            print('VRF Piping Correction Factor for Length in '
                  'Heating Mode Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRF Piping Correction Factor for Length in Heating Mode',
            Coefficient1_Constant='.989916',
            Coefficient2_x='.001961',
            Coefficient3_x2='-.000036',
            Coefficient4_y='0',
            Coefficient5_y2='0',
            Coefficient6_xy='0',
            Minimum_Value_of_x='7',
            Maximum_Value_of_x='106.5',
            Minimum_Value_of_y='1',
            Maximum_Value_of_y='1',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Distance',
            Input_Unit_Type_for_Y='Dimensionless',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRF Piping Correction Factor for Length in "
                  "Heating Mode Curve:Biquadratic Object has been added")

    if 'VRF Heat Recovery Cooling Capacity Modifier' in [i.Name
                                                         for i
                                                         in self.idf1.idfobjects
                                                         ['Curve:Biquadratic']]:
        if verboseMode:
            print('VRF Heat Recovery Cooling Capacity Modifier '
                  'Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRF Heat Recovery Cooling Capacity Modifier',
            Coefficient1_Constant='.9',
            Coefficient2_x='0',
            Coefficient3_x2='0',
            Coefficient4_y='0',
            Coefficient5_y2='0',
            Coefficient6_xy='0',
            Minimum_Value_of_x='-100',
            Maximum_Value_of_x='100',
            Minimum_Value_of_y='-100',
            Maximum_Value_of_y='100',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRF Heat Recovery Cooling Capacity Modifier "
                  "Curve:Biquadratic Object has been added")

    if 'VRF Heat Recovery Cooling Energy Modifier' in [i.Name
                                                       for i
                                                       in self.idf1.idfobjects
                                                       ['Curve:Biquadratic']]:
        if verboseMode:
            print('VRF Heat Recovery Cooling Energy Modifier '
                  'Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRF Heat Recovery Cooling Energy Modifier',
            Coefficient1_Constant='1.1',
            Coefficient2_x='0',
            Coefficient3_x2='0',
            Coefficient4_y='0',
            Coefficient5_y2='0',
            Coefficient6_xy='0',
            Minimum_Value_of_x='-100',
            Maximum_Value_of_x='100',
            Minimum_Value_of_y='-100',
            Maximum_Value_of_y='100',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRF Heat Recovery Cooling Energy Modifier "
                  "Curve:Biquadratic Object has been added")

    if 'VRF Heat Recovery Heating Capacity Modifier' in [i.Name
                                                         for i
                                                         in self.idf1.idfobjects
                                                         ['Curve:Biquadratic']]:
        if verboseMode:
            print('VRF Heat Recovery Heating Capacity Modifier '
                  'Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRF Heat Recovery Heating Capacity Modifier',
            Coefficient1_Constant='.9',
            Coefficient2_x='0',
            Coefficient3_x2='0',
            Coefficient4_y='0',
            Coefficient5_y2='0',
            Coefficient6_xy='0',
            Minimum_Value_of_x='-100',
            Maximum_Value_of_x='100',
            Minimum_Value_of_y='-100',
            Maximum_Value_of_y='100',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRF Heat Recovery Heating Capacity Modifier "
                  "Curve:Biquadratic Object has been added")

    if 'VRF Heat Recovery Heating Energy Modifier' in [i.Name
                                                       for i
                                                       in self.idf1.idfobjects
                                                       ['Curve:Biquadratic']]:
        if verboseMode:
            print('VRF Heat Recovery Heating Energy Modifier '
                  'Curve:Biquadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Biquadratic',
            Name='VRF Heat Recovery Heating Energy Modifier',
            Coefficient1_Constant='1.1',
            Coefficient2_x='0',
            Coefficient3_x2='0',
            Coefficient4_y='0',
            Coefficient5_y2='0',
            Coefficient6_xy='0',
            Minimum_Value_of_x='-100',
            Maximum_Value_of_x='100',
            Minimum_Value_of_y='-100',
            Maximum_Value_of_y='100',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='Temperature',
            Input_Unit_Type_for_Y='Temperature',
            Output_Unit_Type='Dimensionless'
            )
        if verboseMode:
            print("VRF Heat Recovery Heating Energy Modifier "
                  "Curve:Biquadratic Object has been added")

    # curvequadraticlist=[i for i in self.idf1.idfobjects['Curve:Quadratic']]
    # print(curvequadraticlist)

    if 'VRFACCoolCapFFF' in [i.Name for i in self.idf1.idfobjects['Curve:Quadratic']]:
        if verboseMode:
            print('VRFACCoolCapFFF Curve:Quadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Quadratic',
            Name='VRFACCoolCapFFF',
            Coefficient1_Constant='0.8',
            Coefficient2_x='0.2',
            Coefficient3_x2='0.0',
            Minimum_Value_of_x='0.5',
            Maximum_Value_of_x='1.5',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("VRFACCoolCapFFF Curve:Quadratic Object has been added")

    if 'CoolingEIRHiPLR' in [i.Name for i in self.idf1.idfobjects['Curve:Quadratic']]:
        if verboseMode:
            print('CoolingEIRHiPLR Curve:Quadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Quadratic',
            Name='CoolingEIRHiPLR',
            Coefficient1_Constant='1.0',
            Coefficient2_x='0.0',
            Coefficient3_x2='0.0',
            Minimum_Value_of_x='1.0',
            Maximum_Value_of_x='1.5',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("CoolingEIRHiPLR Curve:Quadratic Object has been added")

    if 'VRFCPLFFPLR' in [i.Name for i in self.idf1.idfobjects['Curve:Quadratic']]:
        if verboseMode:
            print('VRFCPLFFPLR Curve:Quadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Quadratic',
            Name='VRFCPLFFPLR',
            Coefficient1_Constant='0.85',
            Coefficient2_x='0.15',
            Coefficient3_x2='0.0',
            Minimum_Value_of_x='0.0',
            Maximum_Value_of_x='1.0',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("VRFCPLFFPLR Curve:Quadratic Object has been added")

    if 'HeatingEIRHiPLR' in [i.Name for i in self.idf1.idfobjects['Curve:Quadratic']]:
        if verboseMode:
            print('HeatingEIRHiPLR Curve:Quadratic Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Quadratic',
            Name='HeatingEIRHiPLR',
            Coefficient1_Constant='2.4294355',
            Coefficient2_x='-2.235887',
            Coefficient3_x2='0.8064516',
            Minimum_Value_of_x='1.0',
            Maximum_Value_of_x='1.5',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("HeatingEIRHiPLR Curve:Quadratic Object has been added")

    # curvelinearlist=[i for i in self.idf1.idfobjects['Curve:Linear']]
    # print(curvelinearlist)

    if 'CoolingCombRatio' in [i.Name for i in self.idf1.idfobjects['Curve:Linear']]:
        if verboseMode:
            print('CoolingCombRatio Curve:Linear Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Linear',
            Name='CoolingCombRatio',
            Coefficient1_Constant='0.618055',
            Coefficient2_x='0.381945',
            Minimum_Value_of_x='1.0',
            Maximum_Value_of_x='1.5',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("CoolingCombRatio Curve:Linear Object has been added")

    if 'HeatingCombRatio' in [i.Name for i in self.idf1.idfobjects['Curve:Linear']]:
        if verboseMode:
            print('HeatingCombRatio Curve:Linear Object already was in the model')
    else:
        self.idf1.newidfobject(
            'Curve:Linear',
            Name='HeatingCombRatio',
            Coefficient1_Constant='0.96034',
            Coefficient2_x='0.03966',
            Minimum_Value_of_x='1.0',
            Maximum_Value_of_x='1.5',
            Minimum_Curve_Output='',
            Maximum_Curve_Output='',
            Input_Unit_Type_for_X='',
            Output_Unit_Type=''
            )
        if verboseMode:
            print("HeatingCombRatio Curve:Linear Object has been added")


def addDetHVACobj(self, EnergyPlus_version: str = None, verboseMode: bool = True, TempCtrl: str = None):
    """Add Detailed HVAC objects for VRFsystem to work."""
    for zn in self.zonenames_orig:
        if 'VRF Outdoor Unit_'+zn in [i.Heat_Pump_Name
                                      for i
                                      in self.idf1.idfobjects
                                      ['AirConditioner:VariableRefrigerantFlow']]:
            if verboseMode:
                print('VRF Outdoor Unit_'+
                      zn+
                      ' AirConditioner:VariableRefrigerantFlow '
                      'Object already was in the model')
        else:
            if EnergyPlus_version.lower() == 'ep96':
                self.idf1.newidfobject(
                    'AirConditioner:VariableRefrigerantFlow',
                    Heat_Pump_Name='VRF Outdoor Unit_'+zn,
                    Availability_Schedule_Name='On 24/7',
                    Gross_Rated_Total_Cooling_Capacity='autosize',
                    Gross_Rated_Cooling_COP=2,
                    Minimum_Condenser_Inlet_Node_Temperature_in_Cooling_Mode=-6,
                    Maximum_Condenser_Inlet_Node_Temperature_in_Cooling_Mode=43,
                    # Minimum_Outdoor_Temperature_in_Cooling_Mode=-6,
                    # Maximum_Outdoor_Temperature_in_Cooling_Mode=43,
                    Cooling_Capacity_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name=
                    'VRFCoolCapFT',
                    Cooling_Capacity_Ratio_Boundary_Curve_Name='VRFCoolCapFTBoundary',
                    Cooling_Capacity_Ratio_Modifier_Function_of_High_Temperature_Curve_Name=
                    'VRFCoolCapFTHi',
                    Cooling_Energy_Input_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name=
                    'VRFCoolEIRFT',
                    Cooling_Energy_Input_Ratio_Boundary_Curve_Name='VRFCoolEIRFTBoundary',
                    Cooling_Energy_Input_Ratio_Modifier_Function_of_High_Temperature_Curve_Name=
                    'VRFCoolEIRFTHi',
                    Cooling_Energy_Input_Ratio_Modifier_Function_of_Low_PartLoad_Ratio_Curve_Name=
                    'CoolingEIRLowPLR',
                    Cooling_Energy_Input_Ratio_Modifier_Function_of_High_PartLoad_Ratio_Curve_Name=
                    'CoolingEIRHiPLR',
                    Cooling_Combination_Ratio_Correction_Factor_Curve_Name=
                    'CoolingCombRatio',
                    Cooling_PartLoad_Fraction_Correlation_Curve_Name='VRFCPLFFPLR',
                    Gross_Rated_Heating_Capacity='autosize',
                    Rated_Heating_Capacity_Sizing_Ratio=1,
                    Gross_Rated_Heating_COP=2.1,
                    Minimum_Condenser_Inlet_Node_Temperature_in_Heating_Mode=-20,
                    Maximum_Condenser_Inlet_Node_Temperature_in_Heating_Mode=40,
                    Heating_Capacity_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name=
                    'VRFHeatCapFT',
                    Heating_Capacity_Ratio_Boundary_Curve_Name='VRFHeatCapFTBoundary',
                    Heating_Capacity_Ratio_Modifier_Function_of_High_Temperature_Curve_Name=
                    'VRFHeatCapFTHi',
                    Heating_Energy_Input_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name=
                    'VRFHeatEIRFT',
                    Heating_Energy_Input_Ratio_Boundary_Curve_Name='VRFHeatEIRFTBoundary',
                    Heating_Energy_Input_Ratio_Modifier_Function_of_High_Temperature_Curve_Name=
                    'VRFHeatEIRFTHi',
                    Heating_Performance_Curve_Outdoor_Temperature_Type='WetBulbTemperature',
                    Heating_Energy_Input_Ratio_Modifier_Function_of_Low_PartLoad_Ratio_Curve_Name=
                    'HeatingEIRLowPLR',
                    Heating_Energy_Input_Ratio_Modifier_Function_of_High_PartLoad_Ratio_Curve_Name=
                    'HeatingEIRHiPLR',
                    Heating_Combination_Ratio_Correction_Factor_Curve_Name=
                    'HeatingCombRatio',
                    Heating_PartLoad_Fraction_Correlation_Curve_Name='VRFCPLFFPLR',
                    Minimum_Heat_Pump_PartLoad_Ratio=0.2,
                    Zone_Name_for_Master_Thermostat_Location='',
                    Master_Thermostat_Priority_Control_Type='LoadPriority',
                    Thermostat_Priority_Schedule_Name='',
                    Zone_Terminal_Unit_List_Name='VRF Outdoor Unit_'+zn+' Zone List',
                    Heat_Pump_Waste_Heat_Recovery='Yes',
                    Equivalent_Piping_Length_used_for_Piping_Correction_Factor_in_Cooling_Mode=50,
                    Vertical_Height_used_for_Piping_Correction_Factor=15,
                    Piping_Correction_Factor_for_Length_in_Cooling_Mode_Curve_Name=
                    'CoolingLengthCorrectionFactor',
                    Piping_Correction_Factor_for_Height_in_Cooling_Mode_Coefficient=0,
                    Equivalent_Piping_Length_used_for_Piping_Correction_Factor_in_Heating_Mode=50,
                    Piping_Correction_Factor_for_Length_in_Heating_Mode_Curve_Name=
                    'VRF Piping Correction Factor for Length in Heating Mode',
                    Piping_Correction_Factor_for_Height_in_Heating_Mode_Coefficient=0,
                    Crankcase_Heater_Power_per_Compressor=15,
                    Number_of_Compressors=2,
                    Ratio_of_Compressor_Size_to_Total_Compressor_Capacity=0.5,
                    Maximum_Outdoor_DryBulb_Temperature_for_Crankcase_Heater=5,
                    Defrost_Strategy='Resistive',
                    Defrost_Control='Timed',
                    Defrost_Energy_Input_Ratio_Modifier_Function_of_Temperature_Curve_Name='',
                    Defrost_Time_Period_Fraction=0,
                    Resistive_Defrost_Heater_Capacity='autosize',
                    Maximum_Outdoor_Drybulb_Temperature_for_Defrost_Operation=5,
                    Condenser_Type='AirCooled',
                    Condenser_Inlet_Node_Name='VRF Outdoor Unit_'+
                                              zn+
                                              ' Outdoor Air Node',
                    Condenser_Outlet_Node_Name='',
                    Water_Condenser_Volume_Flow_Rate='autosize',
                    Evaporative_Condenser_Effectiveness=0.9,
                    Evaporative_Condenser_Air_Flow_Rate='autosize',
                    Evaporative_Condenser_Pump_Rated_Power_Consumption='autosize',
                    Supply_Water_Storage_Tank_Name='',
                    Basin_Heater_Capacity=0,
                    Basin_Heater_Setpoint_Temperature=2,
                    Basin_Heater_Operating_Schedule_Name='On 24/7',
                    Fuel_Type='Electricity',
                    Minimum_Condenser_Inlet_Node_Temperature_in_Heat_Recovery_Mode=-10,
                    Maximum_Condenser_Inlet_Node_Temperature_in_Heat_Recovery_Mode=40,
                    Heat_Recovery_Cooling_Capacity_Modifier_Curve_Name=
                    'VRF Heat Recovery Cooling Capacity Modifier',
                    Initial_Heat_Recovery_Cooling_Capacity_Fraction=0.5,
                    Heat_Recovery_Cooling_Capacity_Time_Constant=0.15,
                    Heat_Recovery_Cooling_Energy_Modifier_Curve_Name=
                    'VRF Heat Recovery Cooling Energy Modifier',
                    Initial_Heat_Recovery_Cooling_Energy_Fraction=1,
                    Heat_Recovery_Cooling_Energy_Time_Constant=0,
                    Heat_Recovery_Heating_Capacity_Modifier_Curve_Name=
                    'VRF Heat Recovery Heating Capacity Modifier',
                    Initial_Heat_Recovery_Heating_Capacity_Fraction=1,
                    Heat_Recovery_Heating_Capacity_Time_Constant=0.15,
                    Heat_Recovery_Heating_Energy_Modifier_Curve_Name=
                    'VRF Heat Recovery Heating Energy Modifier',
                    Initial_Heat_Recovery_Heating_Energy_Fraction=1,
                    Heat_Recovery_Heating_Energy_Time_Constant=0
                    )
            else:
                self.idf1.newidfobject(
                    'AirConditioner:VariableRefrigerantFlow',
                    Heat_Pump_Name='VRF Outdoor Unit_' + zn,
                    Availability_Schedule_Name='On 24/7',
                    Gross_Rated_Total_Cooling_Capacity='autosize',
                    Gross_Rated_Cooling_COP=2,
                    # Minimum_Condenser_Inlet_Node_Temperature_in_Cooling_Mode=-6,
                    # Maximum_Condenser_Inlet_Node_Temperature_in_Cooling_Mode=43,
                    Minimum_Outdoor_Temperature_in_Cooling_Mode=-6,
                    Maximum_Outdoor_Temperature_in_Cooling_Mode=43,
                    Cooling_Capacity_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name=
                    'VRFCoolCapFT',
                    Cooling_Capacity_Ratio_Boundary_Curve_Name='VRFCoolCapFTBoundary',
                    Cooling_Capacity_Ratio_Modifier_Function_of_High_Temperature_Curve_Name=
                    'VRFCoolCapFTHi',
                    Cooling_Energy_Input_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name=
                    'VRFCoolEIRFT',
                    Cooling_Energy_Input_Ratio_Boundary_Curve_Name='VRFCoolEIRFTBoundary',
                    Cooling_Energy_Input_Ratio_Modifier_Function_of_High_Temperature_Curve_Name=
                    'VRFCoolEIRFTHi',
                    Cooling_Energy_Input_Ratio_Modifier_Function_of_Low_PartLoad_Ratio_Curve_Name=
                    'CoolingEIRLowPLR',
                    Cooling_Energy_Input_Ratio_Modifier_Function_of_High_PartLoad_Ratio_Curve_Name=
                    'CoolingEIRHiPLR',
                    Cooling_Combination_Ratio_Correction_Factor_Curve_Name=
                    'CoolingCombRatio',
                    Cooling_PartLoad_Fraction_Correlation_Curve_Name='VRFCPLFFPLR',
                    Gross_Rated_Heating_Capacity='autosize',
                    Rated_Heating_Capacity_Sizing_Ratio=1,
                    Gross_Rated_Heating_COP=2.1,
                    Minimum_Outdoor_Temperature_in_Heating_Mode=-20,
                    Maximum_Outdoor_Temperature_in_Heating_Mode=40,
                    Heating_Capacity_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name=
                    'VRFHeatCapFT',
                    Heating_Capacity_Ratio_Boundary_Curve_Name='VRFHeatCapFTBoundary',
                    Heating_Capacity_Ratio_Modifier_Function_of_High_Temperature_Curve_Name=
                    'VRFHeatCapFTHi',
                    Heating_Energy_Input_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name=
                    'VRFHeatEIRFT',
                    Heating_Energy_Input_Ratio_Boundary_Curve_Name='VRFHeatEIRFTBoundary',
                    Heating_Energy_Input_Ratio_Modifier_Function_of_High_Temperature_Curve_Name=
                    'VRFHeatEIRFTHi',
                    Heating_Performance_Curve_Outdoor_Temperature_Type='WetBulbTemperature',
                    Heating_Energy_Input_Ratio_Modifier_Function_of_Low_PartLoad_Ratio_Curve_Name=
                    'HeatingEIRLowPLR',
                    Heating_Energy_Input_Ratio_Modifier_Function_of_High_PartLoad_Ratio_Curve_Name=
                    'HeatingEIRHiPLR',
                    Heating_Combination_Ratio_Correction_Factor_Curve_Name=
                    'HeatingCombRatio',
                    Heating_PartLoad_Fraction_Correlation_Curve_Name='VRFCPLFFPLR',
                    Minimum_Heat_Pump_PartLoad_Ratio=0.2,
                    Zone_Name_for_Master_Thermostat_Location='',
                    Master_Thermostat_Priority_Control_Type='LoadPriority',
                    Thermostat_Priority_Schedule_Name='',
                    Zone_Terminal_Unit_List_Name='VRF Outdoor Unit_' + zn + ' Zone List',
                    Heat_Pump_Waste_Heat_Recovery='Yes',
                    Equivalent_Piping_Length_used_for_Piping_Correction_Factor_in_Cooling_Mode=50,
                    Vertical_Height_used_for_Piping_Correction_Factor=15,
                    Piping_Correction_Factor_for_Length_in_Cooling_Mode_Curve_Name=
                    'CoolingLengthCorrectionFactor',
                    Piping_Correction_Factor_for_Height_in_Cooling_Mode_Coefficient=0,
                    Equivalent_Piping_Length_used_for_Piping_Correction_Factor_in_Heating_Mode=50,
                    Piping_Correction_Factor_for_Length_in_Heating_Mode_Curve_Name=
                    'VRF Piping Correction Factor for Length in Heating Mode',
                    Piping_Correction_Factor_for_Height_in_Heating_Mode_Coefficient=0,
                    Crankcase_Heater_Power_per_Compressor=15,
                    Number_of_Compressors=2,
                    Ratio_of_Compressor_Size_to_Total_Compressor_Capacity=0.5,
                    Maximum_Outdoor_DryBulb_Temperature_for_Crankcase_Heater=5,
                    Defrost_Strategy='Resistive',
                    Defrost_Control='Timed',
                    Defrost_Energy_Input_Ratio_Modifier_Function_of_Temperature_Curve_Name='',
                    Defrost_Time_Period_Fraction=0,
                    Resistive_Defrost_Heater_Capacity='autosize',
                    Maximum_Outdoor_Drybulb_Temperature_for_Defrost_Operation=5,
                    Condenser_Type='AirCooled',
                    Condenser_Inlet_Node_Name='VRF Outdoor Unit_' +
                                              zn +
                                              ' Outdoor Air Node',
                    Condenser_Outlet_Node_Name='',
                    Water_Condenser_Volume_Flow_Rate='autosize',
                    Evaporative_Condenser_Effectiveness=0.9,
                    Evaporative_Condenser_Air_Flow_Rate='autosize',
                    Evaporative_Condenser_Pump_Rated_Power_Consumption='autosize',
                    Supply_Water_Storage_Tank_Name='',
                    Basin_Heater_Capacity=0,
                    Basin_Heater_Setpoint_Temperature=2,
                    Basin_Heater_Operating_Schedule_Name='On 24/7',
                    Fuel_Type='Electricity',
                    Minimum_Outdoor_Temperature_in_Heat_Recovery_Mode=-10,
                    Maximum_Outdoor_Temperature_in_Heat_Recovery_Mode=40,
                    Heat_Recovery_Cooling_Capacity_Modifier_Curve_Name=
                    'VRF Heat Recovery Cooling Capacity Modifier',
                    Initial_Heat_Recovery_Cooling_Capacity_Fraction=0.5,
                    Heat_Recovery_Cooling_Capacity_Time_Constant=0.15,
                    Heat_Recovery_Cooling_Energy_Modifier_Curve_Name=
                    'VRF Heat Recovery Cooling Energy Modifier',
                    Initial_Heat_Recovery_Cooling_Energy_Fraction=1,
                    Heat_Recovery_Cooling_Energy_Time_Constant=0,
                    Heat_Recovery_Heating_Capacity_Modifier_Curve_Name=
                    'VRF Heat Recovery Heating Capacity Modifier',
                    Initial_Heat_Recovery_Heating_Capacity_Fraction=1,
                    Heat_Recovery_Heating_Capacity_Time_Constant=0.15,
                    Heat_Recovery_Heating_Energy_Modifier_Curve_Name=
                    'VRF Heat Recovery Heating Energy Modifier',
                    Initial_Heat_Recovery_Heating_Energy_Fraction=1,
                    Heat_Recovery_Heating_Energy_Time_Constant=0
                )

            if verboseMode:
                print('VRF Outdoor Unit_'+
                      zn+
                      ' AirConditioner:VariableRefrigerantFlow '
                      'Object has been added')

    OANDlist = [i for i in self.idf1.idfobjects['OutdoorAir:NodeList']]
    # print(OANDlist)

    for i in range(len(OANDlist)):
        firstOAND = self.idf1.idfobjects['OutdoorAir:NodeList'][-1]
        self.idf1.removeidfobject(firstOAND)

    del OANDlist

    ZTULlist = [i for i in self.idf1.idfobjects['ZoneTerminalUnitList']]
    # print(ZTULlist)

    for i in range(len(ZTULlist)):
        firstZTUL = self.idf1.idfobjects['ZoneTerminalUnitList'][-1]
        self.idf1.removeidfobject(firstZTUL)

    del ZTULlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'OutdoorAir:NodeList',
            Node_or_NodeList_Name_1='VRF Outdoor Unit_'+zn+' Outdoor Air Node'
            )
        if verboseMode:
            print('VRF Outdoor Unit_'+
                  zn+
                  ' Outdoor Air Node Object has been added')

        self.idf1.newidfobject(
            'ZoneTerminalUnitList',
            Zone_Terminal_Unit_List_Name='VRF Outdoor Unit_'+zn+' Zone List',
            Zone_Terminal_Unit_Name_1=zn+' VRF Indoor Unit'
            )
        if verboseMode:
            print('VRF Outdoor Unit_'+zn+' Zone List Object has been added')

    ZCTlist = [i for i in self.idf1.idfobjects['ZoneControl:Thermostat']]
    # print(ZCTlist)

    for i in range(len(ZCTlist)):
        firstZCT = self.idf1.idfobjects['ZoneControl:Thermostat'][-1]
        self.idf1.removeidfobject(firstZCT)

    del ZCTlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'ZoneControl:Thermostat',
            Name=zn+' Thermostat',
            Zone_or_ZoneList_Name=zn,
            Control_Type_Schedule_Name='Control type schedule: Always 4',
            Control_1_Object_Type='ThermostatSetpoint:DualSetpoint',
            Control_1_Name=zn+' Dual SP'
            )

    sizingzonelist = [i for i in self.idf1.idfobjects['Sizing:Zone']]
    # print(sizingzonelist)

    for i in range(len(sizingzonelist)):
        firstsizingzone = self.idf1.idfobjects['Sizing:Zone'][-1]
        self.idf1.removeidfobject(firstsizingzone)

    del sizingzonelist

    if TempCtrl == 'pmv':
        supply_air_temp_input_method = 'SupplyAirTemperature'
    elif TempCtrl.lower() == 'temp' or TempCtrl.lower() == 'temperature':
        supply_air_temp_input_method = 'TemperatureDifference'

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'Sizing:Zone',
            Zone_or_ZoneList_Name=zn,
            Zone_Cooling_Design_Supply_Air_Temperature_Input_Method=
            supply_air_temp_input_method,
            Zone_Cooling_Design_Supply_Air_Temperature=14,
            Zone_Cooling_Design_Supply_Air_Temperature_Difference=0.5,
            Zone_Heating_Design_Supply_Air_Temperature_Input_Method=
            supply_air_temp_input_method,
            Zone_Heating_Design_Supply_Air_Temperature=50,
            Zone_Heating_Design_Supply_Air_Temperature_Difference=0.5,
            Zone_Cooling_Design_Supply_Air_Humidity_Ratio=0.009,
            Zone_Heating_Design_Supply_Air_Humidity_Ratio=0.004,
            Design_Specification_Outdoor_Air_Object_Name=
            zn+' Design Specification Outdoor Air Object',
            Zone_Heating_Sizing_Factor=1.25,
            Zone_Cooling_Sizing_Factor=1.15,
            Cooling_Design_Air_Flow_Method='DesignDay',
            Cooling_Design_Air_Flow_Rate=0,
            Cooling_Minimum_Air_Flow_per_Zone_Floor_Area=0.00076,
            Cooling_Minimum_Air_Flow=0,
            Cooling_Minimum_Air_Flow_Fraction=0,
            Heating_Design_Air_Flow_Method='DesignDay',
            Heating_Design_Air_Flow_Rate=0,
            Heating_Maximum_Air_Flow_per_Zone_Floor_Area=0.00203,
            Heating_Maximum_Air_Flow=0.14158,
            Heating_Maximum_Air_Flow_Fraction=0.3,
            Design_Specification_Zone_Air_Distribution_Object_Name=
            zn+' Design Specification Zone Air Distribution Object',
            Account_for_Dedicated_Outdoor_Air_System='Yes',
            Dedicated_Outdoor_Air_System_Control_Strategy='NeutralSupplyAir',
            Dedicated_Outdoor_Air_Low_Setpoint_Temperature_for_Design='autosize',
            Dedicated_Outdoor_Air_High_Setpoint_Temperature_for_Design='autosize'
            )
        if verboseMode:
            print(zn+' Sizing:Zone Object has been added')

    DSOAlist = [i
                for i
                in self.idf1.idfobjects['DesignSpecification:OutdoorAir']]
    # print(DSOAlist)

    for i in range(len(DSOAlist)):
        firstDSOA = self.idf1.idfobjects['DesignSpecification:OutdoorAir'][-1]
        self.idf1.removeidfobject(firstDSOA)

    del DSOAlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'DesignSpecification:OutdoorAir',
            Name=zn+' Design Specification Outdoor Air Object',
            Outdoor_Air_Method='Flow/Person',
            Outdoor_Air_Flow_per_Person=0.00944,
            Outdoor_Air_Flow_per_Zone_Floor_Area=0,
            Outdoor_Air_Flow_per_Zone=0,
            Outdoor_Air_Flow_Air_Changes_per_Hour=0,
            Outdoor_Air_Schedule_Name='On 24/7'
            )
        if verboseMode:
            print(zn+' Design Specification Outdoor Air Object has been added')

    DSZADlist = [i
                 for i
                 in self.idf1.idfobjects
                 ['DesignSpecification:ZoneAirDistribution']]
    # print(DSZADlist)

    for i in range(len(DSZADlist)):
        firstDSZAD = self.idf1.idfobjects[
            'DesignSpecification:ZoneAirDistribution'
        ][-1]
        self.idf1.removeidfobject(firstDSZAD)

    del DSZADlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'DesignSpecification:ZoneAirDistribution',
            Name=zn+' Design Specification Zone Air Distribution Object',
            Zone_Air_Distribution_Effectiveness_in_Cooling_Mode=1,
            Zone_Air_Distribution_Effectiveness_in_Heating_Mode=1,
            Zone_Air_Distribution_Effectiveness_Schedule_Name='',
            Zone_Secondary_Recirculation_Fraction=0
            )
        if verboseMode:
            print(zn+' Design Specification Zone Air Distribution '
                     'Object has been added')

    nodelistlist = [i for i in self.idf1.idfobjects['NodeList']]
    # print(nodelistlist)

    for i in range(len(nodelistlist)):
        firstnodelist = self.idf1.idfobjects['NodeList'][-1]
        self.idf1.removeidfobject(firstnodelist)

    del nodelistlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'NodeList',
            Name=zn+' Air Inlet Node List',
            Node_1_Name=zn+' VRF Indoor Unit Supply Outlet'
            )
        self.idf1.newidfobject(
            'NodeList',
            Name=zn+' Air Exhaust Node List',
            Node_1_Name=zn+' VRF Indoor Unit Return'
            )
        if verboseMode:
            print(zn+' Nodelist Objects has been added')

    ZHEClist = [i
                for i
                in self.idf1.idfobjects['ZoneHVAC:EquipmentConnections']]
    # print(ZHEClist)

    for i in range(len(ZHEClist)):
        firstZHEC = self.idf1.idfobjects['ZoneHVAC:EquipmentConnections'][-1]
        self.idf1.removeidfobject(firstZHEC)

    del ZHEClist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'ZoneHVAC:EquipmentConnections',
            Zone_Name=zn,
            Zone_Conditioning_Equipment_List_Name=zn+' Equipment',
            Zone_Air_Inlet_Node_or_NodeList_Name=zn+' Air Inlet Node List',
            Zone_Air_Exhaust_Node_or_NodeList_Name=zn+' Air Exhaust Node List',
            Zone_Air_Node_Name=zn+' Zone Air Node',
            Zone_Return_Air_Node_or_NodeList_Name=zn+' Return Outlet'
            )
        if verboseMode:
            print(zn+' ZoneHVAC:EquipmentConnections Objects has been added')

    ZHELlist = [i for i in self.idf1.idfobjects['ZoneHVAC:EquipmentList']]
    # print(ZHELlist)

    for i in range(len(ZHELlist)):
        firstZHEL = self.idf1.idfobjects['ZoneHVAC:EquipmentList'][-1]
        self.idf1.removeidfobject(firstZHEL)

    del ZHELlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'ZoneHVAC:EquipmentList',
            defaultvalues=False,
            Name=zn+' Equipment',
            Load_Distribution_Scheme='SequentialLoad',
            Zone_Equipment_1_Object_Type=
            'ZoneHVAC:TerminalUnit:VariableRefrigerantFlow',
            Zone_Equipment_1_Name=zn+' VRF Indoor Unit',
            Zone_Equipment_1_Cooling_Sequence=1,
            Zone_Equipment_1_Heating_or_NoLoad_Sequence=1,
            Zone_Equipment_1_Sequential_Cooling_Fraction_Schedule_Name='',
            Zone_Equipment_1_Sequential_Heating_Fraction_Schedule_Name=''
            )
        if verboseMode:
            print(zn+' ZoneHVAC:EquipmentList Objects has been added')

    ZHTUVRFlist = [i
                   for i
                   in self.idf1.idfobjects
                   ['ZoneHVAC:TerminalUnit:VariableRefrigerantFlow']]
    # print(ZHTUVRFlist)

    for i in range(len(ZHTUVRFlist)):
        firstZHTUVRF = self.idf1.idfobjects[
            'ZoneHVAC:TerminalUnit:VariableRefrigerantFlow'
        ][-1]
        self.idf1.removeidfobject(firstZHTUVRF)

    del ZHTUVRFlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'ZoneHVAC:TerminalUnit:VariableRefrigerantFlow',
            Zone_Terminal_Unit_Name=zn+' VRF Indoor Unit',
            Terminal_Unit_Availability_Schedule='On 24/7',
            Terminal_Unit_Air_Inlet_Node_Name=zn+' VRF Indoor Unit Return',
            Terminal_Unit_Air_Outlet_Node_Name=
            zn+' VRF Indoor Unit Supply Outlet',
            Cooling_Supply_Air_Flow_Rate='autosize',
            No_Cooling_Supply_Air_Flow_Rate='autosize',
            Heating_Supply_Air_Flow_Rate='autosize',
            No_Heating_Supply_Air_Flow_Rate='autosize',
            Cooling_Outdoor_Air_Flow_Rate=0,
            Heating_Outdoor_Air_Flow_Rate=0,
            No_Load_Outdoor_Air_Flow_Rate=0,
            Supply_Air_Fan_Operating_Mode_Schedule_Name='On 24/7',
            Supply_Air_Fan_Placement='DrawThrough',
            Supply_Air_Fan_Object_Type='Fan:ConstantVolume',
            Supply_Air_Fan_Object_Name=zn+' VRF Indoor Unit Supply Fan',
            Outside_Air_Mixer_Object_Type='',
            Outside_Air_Mixer_Object_Name='',
            Cooling_Coil_Object_Type='Coil:Cooling:DX:VariableRefrigerantFlow',
            Cooling_Coil_Object_Name=zn+' VRF Indoor Unit DX Cooling Coil',
            Heating_Coil_Object_Type='Coil:Heating:DX:VariableRefrigerantFlow',
            Heating_Coil_Object_Name=zn+' VRF Indoor Unit DX Heating Coil',
            Zone_Terminal_Unit_On_Parasitic_Electric_Energy_Use=30,
            Zone_Terminal_Unit_Off_Parasitic_Electric_Energy_Use=20,
            Rated_Heating_Capacity_Sizing_Ratio='',
            Availability_Manager_List_Name=''
            )
        if verboseMode:
            print(zn+' ZoneHVAC:TerminalUnit:VariableRefrigerantFlow '
                     'Object has been added')

    CCDXVRFlist = [i
                   for i
                   in self.idf1.idfobjects
                   ['Coil:Cooling:DX:VariableRefrigerantFlow']]
    # print(CCDXVRFlist)

    for i in range(len(CCDXVRFlist)):
        firstCCDCVRF = self.idf1.idfobjects[
            'Coil:Cooling:DX:VariableRefrigerantFlow'
        ][-1]
        self.idf1.removeidfobject(firstCCDCVRF)

    del CCDXVRFlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'Coil:Cooling:DX:VariableRefrigerantFlow',
            Name=zn+' VRF Indoor Unit DX Cooling Coil',
            Availability_Schedule_Name='On 24/7',
            Gross_Rated_Total_Cooling_Capacity='autosize',
            Gross_Rated_Sensible_Heat_Ratio='autosize',
            Rated_Air_Flow_Rate='autosize',
            Cooling_Capacity_Ratio_Modifier_Function_of_Temperature_Curve_Name=
            'VRFTUCoolCapFT',
            Cooling_Capacity_Modifier_Curve_Function_of_Flow_Fraction_Name=
            'VRFACCoolCapFFF',
            Coil_Air_Inlet_Node=zn+' VRF Indoor Unit Return',
            Coil_Air_Outlet_Node=zn+' VRF Indoor Unit DX Cooling Coil Outlet',
            Name_of_Water_Storage_Tank_for_Condensate_Collection=''
            )
        if verboseMode:
            print(zn+' Coil:Cooling:DX:VariableRefrigerantFlow '
                     'Object has been added')

    CHDXVRFlist = [i
                   for i
                   in self.idf1.idfobjects
                   ['Coil:Heating:DX:VariableRefrigerantFlow']]
    # print(CHDXVRFlist)

    for i in range(len(CHDXVRFlist)):
        firstCHDXVRF = self.idf1.idfobjects[
            'Coil:Heating:DX:VariableRefrigerantFlow'
        ][-1]
        self.idf1.removeidfobject(firstCHDXVRF)

    del CHDXVRFlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'Coil:Heating:DX:VariableRefrigerantFlow',
            Name=zn+' VRF Indoor Unit DX Heating Coil',
            Availability_Schedule='On 24/7',
            Gross_Rated_Heating_Capacity='autosize',
            Rated_Air_Flow_Rate='autosize',
            Coil_Air_Inlet_Node=zn+' VRF Indoor Unit DX Cooling Coil Outlet',
            Coil_Air_Outlet_Node=zn+' VRF Indoor Unit DX Heating Coil Outlet',
            Heating_Capacity_Ratio_Modifier_Function_of_Temperature_Curve_Name=
            'VRFTUHeatCapFT',
            Heating_Capacity_Modifier_Function_of_Flow_Fraction_Curve_Name=
            'VRFACCoolCapFFF'
            )
        if verboseMode:
            print(zn+' Coil:Heating:DX:VariableRefrigerantFlow '
                     'Object has been added')

    FCVlist = [i for i in self.idf1.idfobjects['Fan:ConstantVolume']]
    # print(FCVlist)

    for i in range(len(FCVlist)):
        firstFCV = self.idf1.idfobjects['Fan:ConstantVolume'][-1]
        self.idf1.removeidfobject(firstFCV)

    del FCVlist

    for zn in self.zonenames_orig:
        self.idf1.newidfobject(
            'Fan:ConstantVolume',
            Name=zn+' VRF Indoor Unit Supply Fan',
            Availability_Schedule_Name='On 24/7',
            Fan_Total_Efficiency=0.7,
            Pressure_Rise=100,
            Maximum_Flow_Rate='autosize',
            Motor_Efficiency=0.9,
            Motor_In_Airstream_Fraction=1,
            Air_Inlet_Node_Name=zn+' VRF Indoor Unit DX Heating Coil Outlet',
            Air_Outlet_Node_Name=zn+' VRF Indoor Unit Supply Outlet',
            EndUse_Subcategory='General'
            )
        if verboseMode:
            print(zn+' Fan:ConstantVolume Object has been added')


def addForscriptSchVRFsystem(self, verboseMode: bool = True):
    """Add FORSCRIPT Schedules for each zone for VRFsystem."""
    for zn in self.zonenames:
        if "FORSCRIPT_AHST_"+zn in [sch.Name
                                    for sch
                                    in self.idf1.idfobjects['Schedule:Compact']]:
            if verboseMode:
                print('FORSCRIPT_AHST_'+zn+' Schedule already was in the model')
        else:
            self.idf1.newidfobject(
                'Schedule:Compact',
                Name="FORSCRIPT_AHST_"+zn,
                Schedule_Type_Limits_Name="Any Number",
                Field_1='Through: 12/31',
                Field_2='For: AllDays',
                Field_3='Until: 24:00,20'
                )
            if verboseMode:
                print('FORSCRIPT_AHST_'+zn+' Schedule has been added')

        if "FORSCRIPT_ACST_"+zn in [sch.Name
                                    for sch
                                    in self.idf1.idfobjects['Schedule:Compact']]:
            if verboseMode:
                print('FORSCRIPT_ACST_'+zn+' Schedule already was in the model')
        else:
            self.idf1.newidfobject(
                'Schedule:Compact',
                Name="FORSCRIPT_ACST_"+zn,
                Schedule_Type_Limits_Name="Any Number",
                Field_1='Through: 12/31',
                Field_2='For: AllDays',
                Field_3='Until: 24:00,24'
                )
            if verboseMode:
                print('FORSCRIPT_ACST_'+zn+' Schedule has been added')

    # allschedules=([i for i in self.idf1.idfobjects['Schedule:Compact']])
    # print(allschedules)

    TSDSlist = ([i
                 for i
                 in self.idf1.idfobjects['ThermostatSetpoint:DualSetpoint']])
    # print(TSDSlist)

    for i in range(len(TSDSlist)):
        firstTSDS = self.idf1.idfobjects['ThermostatSetpoint:DualSetpoint'][-1]
        self.idf1.removeidfobject(firstTSDS)

    del TSDSlist

    for i in range(len(self.zonenames_orig)):
        self.idf1.newidfobject(
            'ThermostatSetpoint:DualSetpoint',
            Name=self.zonenames_orig[i]+' Dual SP',
            Heating_Setpoint_Temperature_Schedule_Name=
            "FORSCRIPT_AHST_"+self.zonenames[i],
            Cooling_Setpoint_Temperature_Schedule_Name=
            "FORSCRIPT_ACST_"+self.zonenames[i]
            )


def checkVentIsOn(self, verboseMode: bool = True):
    """Check ventilation settings."""
    if "Vent_SP_temp" in [sch.Name
                          for sch
                          in self.idf1.idfobjects['Schedule:Compact']]:
        if verboseMode:
            print("Vent_SP_temp Schedule already was in the model")
    else:
        self.idf1.newidfobject(
            'Schedule:Compact',
            Name="Vent_SP_temp",
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00,24'
            )
        if verboseMode:
            print("Vent_SP_temp Schedule has been added")

    Wlist = ([w
              for w
              in self.idf1.idfobjects
              ['AirflowNetwork:MultiZone:Component:DetailedOpening']
              if w.Name.endswith('_Win')])
    # print(Wlist)
    for w in Wlist:
        w.Height_Factor_for_Opening_Factor_1 = 1
        w.Start_Height_Factor_for_Opening_Factor_1 = 0
        w.Width_Factor_for_Opening_Factor_2 = 1
        w.Height_Factor_for_Opening_Factor_2 = 1
        w.Start_Height_Factor_for_Opening_Factor_2 = 0

    Wlist_2 = ([w
                for w
                in self.idf1.idfobjects
                ['AirflowNetwork:MultiZone:Surface']
                if w.Surface_Name.endswith('_Win')])
    # print(Wlist_2)
    for w in Wlist_2:
        w.Ventilation_Control_Mode = 'Temperature'
        w.Ventilation_Control_Zone_Temperature_Setpoint_Schedule_Name = 'Vent_SP_temp'
        w.Venting_Availability_Schedule_Name = 'On'

    # Checking if all internal doors are always opened

    Dlist = ([d
              for d
              in self.idf1.idfobjects
              ['AirflowNetwork:MultiZone:Component:DetailedOpening']
              if d.Name.endswith('_Door')])
    for d in Dlist:
        d.Width_Factor_for_Opening_Factor_2 = 1

    Dlist_2 = ([d
                for d
                in self.idf1.idfobjects
                ['AirflowNetwork:MultiZone:Surface']
                if d.Surface_Name.endswith('_Door')])
    for d in Dlist_2:
        d.Venting_Availability_Schedule_Name = 'On'

