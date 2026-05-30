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

"""Add EMS objects only for VRFsystem."""


def addEMSSensorsVRFsystem(self, ScriptType: str = None, verboseMode: bool = True):
    """Add EMS sensors for VRF system accim.

    :param self: Used as a method for class ``accim.sim.accim_Main.accimJob``
    :param ScriptType: Inherited from class ``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from class ``accim.sim.accis.addAccis``
    """
    sensorlist = ([sensor.Name for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor']])
    for i in range(len(self.ems_objs_name)):
        if self.ems_objs_name[i] + '_CoolCoil' in sensorlist:
            if verboseMode:
                print('Not added - ' + self.ems_objs_name[i] + '_CoolCoil Sensor')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=self.ems_objs_name[i] + '_CoolCoil',
                OutputVariable_or_OutputMeter_Index_Key_Name=self.ems_zonenames[i] + ' VRF Indoor Unit DX Cooling Coil',
                OutputVariable_or_OutputMeter_Name='Cooling Coil Total Cooling Rate'
            )
            if verboseMode:
                print('Added - ' + self.ems_objs_name[i] + '_CoolCoil Sensor')
        #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_CoolCoil'])
        if self.ems_objs_name[i] + '_HeatCoil' in sensorlist:
            if verboseMode:
                print('Not added - ' + self.ems_objs_name[i] + '_HeatCoil Sensor')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=self.ems_objs_name[i] + '_HeatCoil',
                OutputVariable_or_OutputMeter_Index_Key_Name=self.ems_zonenames[i] + ' VRF Indoor Unit DX Heating Coil',
                OutputVariable_or_OutputMeter_Name='Heating Coil Heating Rate'
            )
            if verboseMode:
                print('Added - ' + self.ems_objs_name[i] + '_HeatCoil Sensor')
    #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_HeatCoil'])

    if ScriptType == 'vrf_mm':
        for i in range(len(self.windownamelist)):
            if self.windownamelist[i]+'_CoolCoil' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.windownamelist[i]+'_CoolCoil Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.windownamelist[i]+'_CoolCoil',
                    OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[i][0]+' VRF Indoor Unit DX Cooling Coil',
                    OutputVariable_or_OutputMeter_Name='Cooling Coil Total Cooling Rate'
                    )
                if verboseMode:
                    print('Added - '+self.windownamelist[i]+'_CoolCoil Sensor')

            if self.windownamelist[i]+'_HeatCoil' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.windownamelist[i]+'_HeatCoil Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.windownamelist[i]+'_HeatCoil',
                    OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[i][0]+' VRF Indoor Unit DX Heating Coil',
                    OutputVariable_or_OutputMeter_Name='Heating Coil Heating Rate'
                    )
                if verboseMode:
                    print('Added - '+self.windownamelist[i]+'_HeatCoil Sensor')

    del sensorlist
