# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

""" Functions for building energy modelling research in Chile"""


from besos import IDF_class
def apply_heating_activation_time_sch(idf_path: str, apply_to_occupancy: bool = True) -> object:
    """
    Applies the heating activation time for Chile.
    See reference: https://www.sciencedirect.com/science/article/pii/S0378778823003833

    :param idf_path: The eppy or besos idf class instance.
    :type idf_path: IDF_class
    :param apply_to_occupancy: True to apply the same schedule to the occupancy.
    :type apply_to_occupancy: bool
    """
    # idf_path ='shoebox_sch.idf'

    from besos.eppy_funcs import get_building

    building = get_building(idf_path)

    sch_comp = [i.Name for i in building.idfobjects['SCHEDULE:COMPACT']]

    if 'Heating_activation_time_chile' not in sch_comp:
        building.newidfobject(
            key='SCHEDULE:COMPACT',
            Name='Heating_activation_time_chile',
            Schedule_Type_Limits_Name='Fraction',
            Field_1='Through: 1/31',
            Field_2='For: AllDays',
            Field_3='Until: 6:00',
            Field_4='0',
            Field_5='Until: 9:00',
            Field_6='1',
            Field_7='Until: 17:00',
            Field_8='0',
            Field_9='Until: 23:00',
            Field_10='1',
            Field_11='Until: 24:00',
            Field_12='0',
            Field_13='Through: 2/28',
            Field_14='For: AllDays',
            Field_15='Until: 6:00',
            Field_16='0',
            Field_17='Until: 9:00',
            Field_18='1',
            Field_19='Until: 17:00',
            Field_20='0',
            Field_21='Until: 23:00',
            Field_22='1',
            Field_23='Until: 24:00',
            Field_24='0',
            Field_25='Through: 3/31',
            Field_26='For: AllDays',
            Field_27='Until: 6:00',
            Field_28='0',
            Field_29='Until: 9:00',
            Field_30='1',
            Field_31='Until: 17:00',
            Field_32='0',
            Field_33='Until: 23:00',
            Field_34='1',
            Field_35='Until: 24:00',
            Field_36='0',
            Field_37='Through: 4/30',
            Field_38='For: AllDays',
            Field_39='Until: 6:00',
            Field_40='0',
            Field_41='Until: 9:00',
            Field_42='1',
            Field_43='Until: 17:00',
            Field_44='0',
            Field_45='Until: 23:00',
            Field_46='1',
            Field_47='Until: 24:00',
            Field_48='0',
            Field_49='Through: 5/31',
            Field_50='For: AllDays',
            Field_51='Until: 6:00',
            Field_52='0',
            Field_53='Until: 9:00',
            Field_54='1',
            Field_55='Until: 17:00',
            Field_56='0',
            Field_57='Until: 24:00',
            Field_58='1',
            Field_59='Through: 6/30',
            Field_60='For: AllDays',
            Field_61='Until: 6:00',
            Field_62='0',
            Field_63='Until: 9:00',
            Field_64='1',
            Field_65='Until: 17:00',
            Field_66='0',
            Field_67='Until: 24:00',
            Field_68='1',
            Field_69='Through: 7/31',
            Field_70='For: AllDays',
            Field_71='Until: 6:00',
            Field_72='0',
            Field_73='Until: 9:00',
            Field_74='1',
            Field_75='Until: 17:00',
            Field_76='0',
            Field_77='Until: 24:00',
            Field_78='1',
            Field_79='Through: 8/31',
            Field_80='For: AllDays',
            Field_81='Until: 6:00',
            Field_82='0',
            Field_83='Until: 9:00',
            Field_84='1',
            Field_85='Until: 17:00',
            Field_86='0',
            Field_87='Until: 24:00',
            Field_88='1',
            Field_89='Through: 9/30',
            Field_90='For: AllDays',
            Field_91='Until: 6:00',
            Field_92='0',
            Field_93='Until: 9:00',
            Field_94='1',
            Field_95='Until: 17:00',
            Field_96='0',
            Field_97='Until: 23:00',
            Field_98='1',
            Field_99='Until: 24:00',
            Field_100='0',
            Field_101='Through: 10/31',
            Field_102='For: AllDays',
            Field_103='Until: 6:00',
            Field_104='0',
            Field_105='Until: 9:00',
            Field_106='1',
            Field_107='Until: 17:00',
            Field_108='0',
            Field_109='Until: 24:00',
            Field_110='1',
            Field_111='Through: 11/30',
            Field_112='For: AllDays',
            Field_113='Until: 6:00',
            Field_114='0',
            Field_115='Until: 9:00',
            Field_116='1',
            Field_117='Until: 17:00',
            Field_118='0',
            Field_119='Until: 24:00',
            Field_120='1',
            Field_121='Through: 12/31',
            Field_122='For: AllDays',
            Field_123='Until: 6:00',
            Field_124='0',
            Field_125='Until: 9:00',
            Field_126='1',
            Field_127='Until: 17:00',
            Field_128='0',
            Field_129='Until: 24:00',
            Field_130='1'
        )
        new_idf = idf_path.split('.idf')[0] + '_heat_act_time_added.idf'
        building.savecopy(new_idf)
        sch_added = True
    else:
        print('Heating_activation_time_chile already was in the model.')
        sch_added = False

    if apply_to_occupancy:
        if sch_added:
            for people in [i for i in building.idfobjects['people']]:
                people.Number_of_People_Schedule_Name = 'Heating_activation_time_chile'
            print('Heating_activation_time_chile has been used in all occupancy schedules in the model.')
            building.savecopy(new_idf)





