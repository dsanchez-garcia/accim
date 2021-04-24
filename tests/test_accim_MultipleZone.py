import pytest
from accim.sim import accim_Main

@pytest.fixture()
def IDFobject():
    from eppy.modeleditor import IDF

    iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
    IDF.setiddname(iddfile)

    z = accim_Main.accimJob(
        filename_temp='TestModel_MultipleZone',
        ScriptType='mz',
        EnergyPlus_version='ep94',
        verboseMode=False)
    return z

def test_addMultipleZoneSch(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addMultipleZoneSch(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')

    addMultipleZoneSch_dict = {
        'On 24/7': ['Until: 24:00', '1'],
        'Control type schedule: Always 4': ['Until: 24:00', '4'],
        'Relative humidity setpoint schedule: Always 50.00': ['Until: 24:00', '50'],
        'Heating Fanger comfort setpoint: Always -0.5': ['Until: 24:00', '-0.5'],
        'Cooling Fanger comfort setpoint: Always  0.1': ['Until: 24:00', '0.1'],
        'Zone CO2 setpoint: Always 900ppm': ['Until: 24:00', '900'],
        'Min CO2 concentration: Always 600ppm': ['Until: 24:00', '600'],
        'Generic contaminant setpoint: Always 0.5ppm': ['Until: 24:00', '0.5'],
        'Air distribution effectiveness (always 1)': ['Until: 24:00', '1']
        }
    
    for i in addMultipleZoneSch_dict:
        sch = ([x
                for x
                in idf1.idfobjects['Schedule:Compact']
                if x.Name == i])
        assert sch[0].Name == i
        assert sch[0].Schedule_Type_Limits_Name == "Any Number"
        assert sch[0].Field_1 == 'Through: 12/31'
        assert sch[0].Field_2 == 'For: AllDays'
        assert sch[0].Field_3 == addMultipleZoneSch_dict[i][0]
        assert sch[0].Field_4 == addMultipleZoneSch_dict[i][1]


    sch = ([x
            for x
            in idf1.idfobjects['Schedule:Compact']
            if x.Name == 'VRF Heating Cooling (Northern Hemisphere)'])
    assert sch[0].Name == "VRF Heating Cooling (Northern Hemisphere)"
    assert sch[0].Schedule_Type_Limits_Name == "Any Number"
    assert sch[0].Field_1 == 'Through: 31 Mar'
    assert sch[0].Field_2 == 'For: AllDays'
    assert sch[0].Field_3 == 'Until: 24:00'
    assert sch[0].Field_4 == '0'
    assert sch[0].Field_5 == 'Through: 30 Sep'
    assert sch[0].Field_6 == 'For: AllDays'
    assert sch[0].Field_7 == 'Until: 24:00'
    assert sch[0].Field_8 == '1'
    assert sch[0].Field_9 == 'Through: 31 Dec'
    assert sch[0].Field_10 == 'For: AllDays'
    assert sch[0].Field_11 == 'Until: 24:00'
    assert sch[0].Field_12 == '0'


def test_addCurveObj(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addCurveObj(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')
    
    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Cubic']
                 if x.Name == 'DefaultFanEffRatioCurve'])
    assert curveobj[0].Name == 'DefaultFanEffRatioCurve'
    assert curveobj[0].Coefficient1_Constant == 0.33856828
    assert curveobj[0].Coefficient2_x == 1.72644131
    assert curveobj[0].Coefficient3_x2 == -1.49280132
    assert curveobj[0].Coefficient4_x3 == 0.42776208
    assert curveobj[0].Minimum_Value_of_x == 0.5
    assert curveobj[0].Maximum_Value_of_x == 1.5
    assert curveobj[0].Minimum_Curve_Output == 0.3
    assert curveobj[0].Maximum_Curve_Output == 1.0
    assert curveobj[0].Input_Unit_Type_for_X == ''
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Cubic']
                 if x.Name == 'VRFTUCoolCapFT'])
    assert curveobj[0].Name == 'VRFTUCoolCapFT'
    assert curveobj[0].Coefficient1_Constant == 0.504547273506488
    assert curveobj[0].Coefficient2_x == 0.0288891279198444
    assert curveobj[0].Coefficient3_x2 == -0.000010819418650677
    assert curveobj[0].Coefficient4_x3 == 0.0000101359395177008
    assert curveobj[0].Minimum_Value_of_x == 0.0
    assert curveobj[0].Maximum_Value_of_x == 50.0
    assert curveobj[0].Minimum_Curve_Output == 0.5
    assert curveobj[0].Maximum_Curve_Output == 1.5
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Cubic']
                 if x.Name == 'VRFTUHeatCapFT'])
    assert curveobj[0].Name == 'VRFTUHeatCapFT'
    assert curveobj[0].Coefficient1_Constant == -0.390708928227928
    assert curveobj[0].Coefficient2_x == 0.261815023760162
    assert curveobj[0].Coefficient3_x2 == -0.0130431603151873
    assert curveobj[0].Coefficient4_x3 == 0.000178131745997821
    assert curveobj[0].Minimum_Value_of_x == 0.0
    assert curveobj[0].Maximum_Value_of_x == 50.0
    assert curveobj[0].Minimum_Curve_Output == 0.5
    assert curveobj[0].Maximum_Curve_Output == 1.5
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Cubic']
                 if x.Name == 'VRFCoolCapFTBoundary'])
    assert curveobj[0].Name == 'VRFCoolCapFTBoundary'
    assert curveobj[0].Coefficient1_Constant == 25.73473775
    assert curveobj[0].Coefficient2_x == -0.03150043
    assert curveobj[0].Coefficient3_x2 == -0.01416595
    assert curveobj[0].Coefficient4_x3 == 0
    assert curveobj[0].Minimum_Value_of_x == 11
    assert curveobj[0].Maximum_Value_of_x == 30
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Cubic']
                 if x.Name == 'VRFCoolEIRFTBoundary'])
    assert curveobj[0].Name == 'VRFCoolEIRFTBoundary'
    assert curveobj[0].Coefficient1_Constant == 25.73473775
    assert curveobj[0].Coefficient2_x == -0.03150043
    assert curveobj[0].Coefficient3_x2 == -0.01416595
    assert curveobj[0].Coefficient4_x3 == 0
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 24
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Cubic']
                 if x.Name == 'CoolingEIRLowPLR'])
    assert curveobj[0].Name == 'CoolingEIRLowPLR'
    assert curveobj[0].Coefficient1_Constant == 0.4628123
    assert curveobj[0].Coefficient2_x == -1.0402406
    assert curveobj[0].Coefficient3_x2 == 2.17490997
    assert curveobj[0].Coefficient4_x3 == -0.5974817
    assert curveobj[0].Minimum_Value_of_x == 0
    assert curveobj[0].Maximum_Value_of_x == 1
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Capacity'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Cubic']
                 if x.Name == 'VRFHeatCapFTBoundary'])
    assert curveobj[0].Name == 'VRFHeatCapFTBoundary'
    assert curveobj[0].Coefficient1_Constant == -7.6000882
    assert curveobj[0].Coefficient2_x == 3.05090016
    assert curveobj[0].Coefficient3_x2 == -0.1162844
    assert curveobj[0].Coefficient4_x3 == 0.0
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 27
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Cubic']
                 if x.Name == 'VRFHeatEIRFTBoundary'])
    assert curveobj[0].Name == 'VRFHeatEIRFTBoundary'
    assert curveobj[0].Coefficient1_Constant == -7.6000882
    assert curveobj[0].Coefficient2_x == 3.05090016
    assert curveobj[0].Coefficient3_x2 == -0.1162844
    assert curveobj[0].Coefficient4_x3 == 0.0
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 27
    assert curveobj[0].Minimum_Curve_Output == -20
    assert curveobj[0].Maximum_Curve_Output == 15
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Cubic']
                 if x.Name == 'HeatingEIRLowPLR'])
    assert curveobj[0].Name == 'HeatingEIRLowPLR'
    assert curveobj[0].Coefficient1_Constant == 0.1400093
    assert curveobj[0].Coefficient2_x == 0.6415002
    assert curveobj[0].Coefficient3_x2 == 0.1339047
    assert curveobj[0].Coefficient4_x3 == 0.0845859
    assert curveobj[0].Minimum_Value_of_x == 0
    assert curveobj[0].Maximum_Value_of_x == 1
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Dimensionless'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Exponent']
                 if x.Name == 'DefaultFanPowerRatioCurve'])
    assert curveobj[0].Name == 'DefaultFanPowerRatioCurve'
    assert curveobj[0].Coefficient1_Constant == 0
    assert curveobj[0].Coefficient2_Constant == 1
    assert curveobj[0].Coefficient3_Constant == 3
    assert curveobj[0].Minimum_Value_of_x == 0
    assert curveobj[0].Maximum_Value_of_x == 1.5
    assert curveobj[0].Minimum_Curve_Output == 0.01
    assert curveobj[0].Maximum_Curve_Output == 1.5
    assert curveobj[0].Input_Unit_Type_for_X == ''
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'DXHtgCoilDefrostEIRFT'])
    assert curveobj[0].Name == 'DXHtgCoilDefrostEIRFT'
    assert curveobj[0].Coefficient1_Constant == 1.0
    assert curveobj[0].Coefficient2_x == 0.0
    assert curveobj[0].Coefficient3_x2 == 0.0
    assert curveobj[0].Coefficient4_y == 0.0
    assert curveobj[0].Coefficient5_y2 == 0
    assert curveobj[0].Coefficient6_xy == 0
    assert curveobj[0].Minimum_Value_of_x == 0.0
    assert curveobj[0].Maximum_Value_of_x == 50.0
    assert curveobj[0].Minimum_Value_of_y == 0.0
    assert curveobj[0].Maximum_Value_of_y == 50.0
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRFCoolCapFT'])
    assert curveobj[0].Name == 'VRFCoolCapFT'
    assert curveobj[0].Coefficient1_Constant == 0.576882692
    assert curveobj[0].Coefficient2_x == 0.017447952
    assert curveobj[0].Coefficient3_x2 == 0.000583269
    assert curveobj[0].Coefficient4_y == -1.76324E-06
    assert curveobj[0].Coefficient5_y2 == -7.474E-09
    assert curveobj[0].Coefficient6_xy == -1.30413E-07
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 24
    assert curveobj[0].Minimum_Value_of_y == -5
    assert curveobj[0].Maximum_Value_of_y == 23
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRFCoolCapFTHi'])
    assert curveobj[0].Name == 'VRFCoolCapFTHi'
    assert curveobj[0].Coefficient1_Constant == 0.6867358
    assert curveobj[0].Coefficient2_x == 0.0207631
    assert curveobj[0].Coefficient3_x2 == 0.0005447
    assert curveobj[0].Coefficient4_y == -0.0016218
    assert curveobj[0].Coefficient5_y2 == -4.259E-07
    assert curveobj[0].Coefficient6_xy == -0.0003392
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 24
    assert curveobj[0].Minimum_Value_of_y == 16
    assert curveobj[0].Maximum_Value_of_y == 43
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRFCoolEIRFT'])
    assert curveobj[0].Name == 'VRFCoolEIRFT'
    assert curveobj[0].Coefficient1_Constant == 0.989010541
    assert curveobj[0].Coefficient2_x == -0.02347967
    assert curveobj[0].Coefficient3_x2 == 0.000199711
    assert curveobj[0].Coefficient4_y == 0.005968336
    assert curveobj[0].Coefficient5_y2 == -1.0289E-07
    assert curveobj[0].Coefficient6_xy == -0.00015686
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 24
    assert curveobj[0].Minimum_Value_of_y == -5
    assert curveobj[0].Maximum_Value_of_y == 23
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRFCoolEIRFTHi'])
    assert curveobj[0].Name == 'VRFCoolEIRFTHi'
    assert curveobj[0].Coefficient1_Constant == 0.14351470
    assert curveobj[0].Coefficient2_x == 0.01860035
    assert curveobj[0].Coefficient3_x2 == -0.0003954
    assert curveobj[0].Coefficient4_y == 0.02485219
    assert curveobj[0].Coefficient5_y2 == 0.00016329
    assert curveobj[0].Coefficient6_xy == -0.0006244
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 24
    assert curveobj[0].Minimum_Value_of_y == 16
    assert curveobj[0].Maximum_Value_of_y == 43
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRFHeatCapFT'])
    assert curveobj[0].Name == 'VRFHeatCapFT'
    assert curveobj[0].Coefficient1_Constant == 1.014599599
    assert curveobj[0].Coefficient2_x == -0.002506703
    assert curveobj[0].Coefficient3_x2 == -0.000141599
    assert curveobj[0].Coefficient4_y == 0.026931595
    assert curveobj[0].Coefficient5_y2 == 1.83538E-06
    assert curveobj[0].Coefficient6_xy == -0.000358147
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 27
    assert curveobj[0].Minimum_Value_of_y == -20
    assert curveobj[0].Maximum_Value_of_y == 15
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRFHeatCapFTHi'])
    assert curveobj[0].Name == 'VRFHeatCapFTHi'
    assert curveobj[0].Coefficient1_Constant == 1.161134821
    assert curveobj[0].Coefficient2_x == 0.027478868
    assert curveobj[0].Coefficient3_x2 == -0.00168795
    assert curveobj[0].Coefficient4_y == 0.001783378
    assert curveobj[0].Coefficient5_y2 == 2.03208E-06
    assert curveobj[0].Coefficient6_xy == -6.8969E-05
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 27
    assert curveobj[0].Minimum_Value_of_y == -10
    assert curveobj[0].Maximum_Value_of_y == 15
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRFHeatEIRFT'])
    assert curveobj[0].Name == 'VRFHeatEIRFT'
    assert curveobj[0].Coefficient1_Constant == 0.87465501
    assert curveobj[0].Coefficient2_x == -0.01319754
    assert curveobj[0].Coefficient3_x2 == 0.00110307
    assert curveobj[0].Coefficient4_y == -0.0133118
    assert curveobj[0].Coefficient5_y2 == 0.00089017
    assert curveobj[0].Coefficient6_xy == -0.00012766
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 27
    assert curveobj[0].Minimum_Value_of_y == -20
    assert curveobj[0].Maximum_Value_of_y == 12
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRFHeatEIRFTHi'])
    assert curveobj[0].Name == 'VRFHeatEIRFTHi'
    assert curveobj[0].Coefficient1_Constant == 2.504005146
    assert curveobj[0].Coefficient2_x == -0.05736767
    assert curveobj[0].Coefficient3_x2 == 4.07336E-05
    assert curveobj[0].Coefficient4_y == -0.12959669
    assert curveobj[0].Coefficient5_y2 == 0.00135839
    assert curveobj[0].Coefficient6_xy == 0.00317047
    assert curveobj[0].Minimum_Value_of_x == 15
    assert curveobj[0].Maximum_Value_of_x == 27
    assert curveobj[0].Minimum_Value_of_y == -10
    assert curveobj[0].Maximum_Value_of_y == 15
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'CoolingLengthCorrectionFactor'])
    assert curveobj[0].Name == 'CoolingLengthCorrectionFactor'
    assert curveobj[0].Coefficient1_Constant == 1.0693794
    assert curveobj[0].Coefficient2_x == -0.0014951
    assert curveobj[0].Coefficient3_x2 == 2.56E-06
    assert curveobj[0].Coefficient4_y == -0.1151104
    assert curveobj[0].Coefficient5_y2 == 0.0511169
    assert curveobj[0].Coefficient6_xy == -0.0004369
    assert curveobj[0].Minimum_Value_of_x == 8
    assert curveobj[0].Maximum_Value_of_x == 175
    assert curveobj[0].Minimum_Value_of_y == 0.5
    assert curveobj[0].Maximum_Value_of_y == 1.5
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRF Piping Correction Factor for Length in Heating Mode'])
    assert curveobj[0].Name == 'VRF Piping Correction Factor for Length in Heating Mode'
    assert curveobj[0].Coefficient1_Constant == .989916
    assert curveobj[0].Coefficient2_x == .001961
    assert curveobj[0].Coefficient3_x2 == -.000036
    assert curveobj[0].Coefficient4_y == 0
    assert curveobj[0].Coefficient5_y2 == 0
    assert curveobj[0].Coefficient6_xy == 0
    assert curveobj[0].Minimum_Value_of_x == 7
    assert curveobj[0].Maximum_Value_of_x == 106.5
    assert curveobj[0].Minimum_Value_of_y == 1
    assert curveobj[0].Maximum_Value_of_y == 1
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Distance'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Dimensionless'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRF Heat Recovery Cooling Capacity Modifier'])
    assert curveobj[0].Name == 'VRF Heat Recovery Cooling Capacity Modifier'
    assert curveobj[0].Coefficient1_Constant == .9
    assert curveobj[0].Coefficient2_x == 0
    assert curveobj[0].Coefficient3_x2 == 0
    assert curveobj[0].Coefficient4_y == 0
    assert curveobj[0].Coefficient5_y2 == 0
    assert curveobj[0].Coefficient6_xy == 0
    assert curveobj[0].Minimum_Value_of_x == -100
    assert curveobj[0].Maximum_Value_of_x == 100
    assert curveobj[0].Minimum_Value_of_y == -100
    assert curveobj[0].Maximum_Value_of_y == 100
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRF Heat Recovery Cooling Energy Modifier'])
    assert curveobj[0].Name == 'VRF Heat Recovery Cooling Energy Modifier'
    assert curveobj[0].Coefficient1_Constant == 1.1
    assert curveobj[0].Coefficient2_x == 0
    assert curveobj[0].Coefficient3_x2 == 0
    assert curveobj[0].Coefficient4_y == 0
    assert curveobj[0].Coefficient5_y2 == 0
    assert curveobj[0].Coefficient6_xy == 0
    assert curveobj[0].Minimum_Value_of_x == -100
    assert curveobj[0].Maximum_Value_of_x == 100
    assert curveobj[0].Minimum_Value_of_y == -100
    assert curveobj[0].Maximum_Value_of_y == 100
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRF Heat Recovery Heating Capacity Modifier'])
    assert curveobj[0].Name == 'VRF Heat Recovery Heating Capacity Modifier'
    assert curveobj[0].Coefficient1_Constant == .9
    assert curveobj[0].Coefficient2_x == 0
    assert curveobj[0].Coefficient3_x2 == 0
    assert curveobj[0].Coefficient4_y == 0
    assert curveobj[0].Coefficient5_y2 == 0
    assert curveobj[0].Coefficient6_xy == 0
    assert curveobj[0].Minimum_Value_of_x == -100
    assert curveobj[0].Maximum_Value_of_x == 100
    assert curveobj[0].Minimum_Value_of_y == -100
    assert curveobj[0].Maximum_Value_of_y == 100
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Biquadratic']
                 if x.Name == 'VRF Heat Recovery Heating Energy Modifier'])
    assert curveobj[0].Name == 'VRF Heat Recovery Heating Energy Modifier'
    assert curveobj[0].Coefficient1_Constant == 1.1
    assert curveobj[0].Coefficient2_x == 0
    assert curveobj[0].Coefficient3_x2 == 0
    assert curveobj[0].Coefficient4_y == 0
    assert curveobj[0].Coefficient5_y2 == 0
    assert curveobj[0].Coefficient6_xy == 0
    assert curveobj[0].Minimum_Value_of_x == -100
    assert curveobj[0].Maximum_Value_of_x == 100
    assert curveobj[0].Minimum_Value_of_y == -100
    assert curveobj[0].Maximum_Value_of_y == 100
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == 'Temperature'
    assert curveobj[0].Input_Unit_Type_for_Y == 'Temperature'
    assert curveobj[0].Output_Unit_Type == 'Dimensionless'

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Quadratic']
                 if x.Name == 'VRFACCoolCapFFF'])
    assert curveobj[0].Name == 'VRFACCoolCapFFF'
    assert curveobj[0].Coefficient1_Constant == 0.8
    assert curveobj[0].Coefficient2_x == 0.2
    assert curveobj[0].Coefficient3_x2 == 0.0
    assert curveobj[0].Minimum_Value_of_x == 0.5
    assert curveobj[0].Maximum_Value_of_x == 1.5
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == ''
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Quadratic']
                 if x.Name == 'CoolingEIRHiPLR'])
    assert curveobj[0].Name == 'CoolingEIRHiPLR'
    assert curveobj[0].Coefficient1_Constant == 1.0
    assert curveobj[0].Coefficient2_x == 0.0
    assert curveobj[0].Coefficient3_x2 == 0.0
    assert curveobj[0].Minimum_Value_of_x == 1.0
    assert curveobj[0].Maximum_Value_of_x == 1.5
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == ''
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Quadratic']
                 if x.Name == 'VRFCPLFFPLR'])
    assert curveobj[0].Name == 'VRFCPLFFPLR'
    assert curveobj[0].Coefficient1_Constant == 0.85
    assert curveobj[0].Coefficient2_x == 0.15
    assert curveobj[0].Coefficient3_x2 == 0.0
    assert curveobj[0].Minimum_Value_of_x == 0.0
    assert curveobj[0].Maximum_Value_of_x == 1.0
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == ''
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Quadratic']
                 if x.Name == 'HeatingEIRHiPLR'])
    assert curveobj[0].Name == 'HeatingEIRHiPLR'
    assert curveobj[0].Coefficient1_Constant == 2.4294355
    assert curveobj[0].Coefficient2_x == -2.235887
    assert curveobj[0].Coefficient3_x2 == 0.8064516
    assert curveobj[0].Minimum_Value_of_x == 1.0
    assert curveobj[0].Maximum_Value_of_x == 1.5
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == ''
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Linear']
                 if x.Name == 'CoolingCombRatio'])
    assert curveobj[0].Name == 'CoolingCombRatio'
    assert curveobj[0].Coefficient1_Constant == 0.618055
    assert curveobj[0].Coefficient2_x == 0.381945
    assert curveobj[0].Minimum_Value_of_x == 1.0
    assert curveobj[0].Maximum_Value_of_x == 1.5
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == ''
    assert curveobj[0].Output_Unit_Type == ''

    curveobj = ([x
                 for x
                 in idf1.idfobjects['Curve:Linear']
                 if x.Name == 'HeatingCombRatio'])
    assert curveobj[0].Name == 'HeatingCombRatio'
    assert curveobj[0].Coefficient1_Constant == 0.96034
    assert curveobj[0].Coefficient2_x == 0.03966
    assert curveobj[0].Minimum_Value_of_x == 1.0
    assert curveobj[0].Maximum_Value_of_x == 1.5
    assert curveobj[0].Minimum_Curve_Output == ''
    assert curveobj[0].Maximum_Curve_Output == ''
    assert curveobj[0].Input_Unit_Type_for_X == ''
    assert curveobj[0].Output_Unit_Type == ''


def test_addForscriptSchMultipleZone(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addForscriptSchMultipleZone(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')


    zonenames_orig = ([zone.Name for zone in idf1.idfobjects['ZONE']])

    zonenames = ([sub.replace(':', '_') for sub in ([zone.Name for zone in idf1.idfobjects['ZONE']])])

    for zonename in zonenames:
        obj = ([x
                for x
                in idf1.idfobjects['Schedule:Compact']
                if x.Name == "FORSCRIPT_AHST_" + zonename])
        assert obj[0].Name == "FORSCRIPT_AHST_" + zonename
        assert obj[0].Schedule_Type_Limits_Name == "Any Number"
        assert obj[0].Field_1 == 'Through: 12/31'
        assert obj[0].Field_2 == 'For: AllDays'
        assert obj[0].Field_3 == 'Until: 24:00'
        assert obj[0].Field_4 == '20'
        
        obj = ([x
                for x
                in idf1.idfobjects['Schedule:Compact']
                if x.Name == "FORSCRIPT_ACST_" + zonename])
        assert obj[0].Name == "FORSCRIPT_ACST_" + zonename
        assert obj[0].Schedule_Type_Limits_Name == "Any Number"
        assert obj[0].Field_1 == 'Through: 12/31'
        assert obj[0].Field_2 == 'For: AllDays'
        assert obj[0].Field_3 == 'Until: 24:00'
        assert obj[0].Field_4 == '24'
    
    for i in range(len(zonenames_orig)):
        obj = ([x
                for x
                in idf1.idfobjects['ThermostatSetpoint:DualSetpoint']
                if x.Name == zonenames_orig[i]+' Dual SP'])
        assert obj[0].Name == zonenames_orig[i]+' Dual SP'
        assert obj[0].Heating_Setpoint_Temperature_Schedule_Name == "FORSCRIPT_AHST_" + zonenames[i]
        assert obj[0].Cooling_Setpoint_Temperature_Schedule_Name == "FORSCRIPT_ACST_" + zonenames[i]

def test_checkVentIsOn(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.checkVentIsOn(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_MultipleZone_pymod.idf')

    obj = ([x
            for x
            in idf1.idfobjects['Schedule:Compact']
            if x.Name == "Vent_SP_temp"])
    assert obj[0].Name == "Vent_SP_temp"
    assert obj[0].Schedule_Type_Limits_Name == "Any Number"
    assert obj[0].Field_1 == 'Through: 12/31'
    assert obj[0].Field_2 == 'For: AllDays'
    assert obj[0].Field_3 == 'Until: 24:00'
    assert obj[0].Field_4 == '24'

    windowlist = ([x
                   for x
                   in idf1.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening']
                   if x.Name.endswith('_Win')])
    
    for window in windowlist:
        assert window.Height_Factor_for_Opening_Factor_1 == 1
        assert window.Start_Height_Factor_for_Opening_Factor_1 == 0
        assert window.Width_Factor_for_Opening_Factor_2 == 1
        assert window.Height_Factor_for_Opening_Factor_2 == 1
        assert window.Start_Height_Factor_for_Opening_Factor_2 == 0
    
    windowlist_2 = ([window
                     for window
                     in idf1.idfobjects['AirflowNetwork:MultiZone:Surface']
                     if window.Surface_Name.endswith('_Win')])
    for window in windowlist_2:
        assert window.Ventilation_Control_Mode == 'Temperature'
        assert window.Ventilation_Control_Zone_Temperature_Setpoint_Schedule_Name == 'Vent_SP_temp'
        assert window.Venting_Availability_Schedule_Name == 'On'

    doorlist = ([door
                 for door
                 in idf1.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening']
                 if door.Name.endswith('_Door')])
    for door in doorlist:
        assert door.Width_Factor_for_Opening_Factor_2 == 1

    doorlist_2 = ([door
                   for door
                   in idf1.idfobjects['AirflowNetwork:MultiZone:Surface']
                   if door.Surface_Name.endswith('_Door')])
    for door in doorlist_2:
        assert door.Venting_Availability_Schedule_Name == 'On'
