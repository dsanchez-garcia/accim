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

"""Module for EMS functions and models with existing HVAC systems"""


def add_ems_sensors_existing_hvac(self, verbose : bool = True):
    """
    Adds the EMS sensors for models with existing HVAC system.

    :param self: Used as a method for class ``accim.sim.engine.AccimJob``
    :param verbose: Inherited from class ``accim.sim.AddAccis``
    """
    sensorlist = ([sensor.Name for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor']])
    for i in range(len(self.ExisHVAC)):
        for j in range(len(self.ExisHVAC[i][1])):
            if 'Cool' in self.ExisHVAC[i][1][j] or 'Cool' in self.HVACdict[self.ExisHVAC[i][0]]:
                zone_for_coil = self.ExisHVAC[i][3][j]
                matching_ems_names = []
                if hasattr(self, 'ems_zonenames') and hasattr(self, 'ems_objs_name'):
                    for z_idx, z_name in enumerate(self.ems_zonenames):
                        if z_name.upper() == zone_for_coil.upper():
                            matching_ems_names.append(self.ems_objs_name[z_idx])
                if not matching_ems_names:
                    matching_ems_names.append(zone_for_coil)

                for ems_name in matching_ems_names:
                    if ems_name + '_CoolCoil' in sensorlist:
                        if verbose:
                            print('Not added - ' + ems_name + '_CoolCoil Sensor')
                    else:
                        self.idf1.newidfobject(
                            'EnergyManagementSystem:Sensor',
                            Name=ems_name + '_CoolCoil',
                            OutputVariable_or_OutputMeter_Index_Key_Name=self.ExisHVAC[i][1][j],
                            OutputVariable_or_OutputMeter_Name=self.HVACdict[self.ExisHVAC[i][0]]
                        )
                        sensorlist.append(ems_name + '_CoolCoil')
                        if verbose:
                            print('Added - ' + ems_name + '_CoolCoil Sensor')
                for k in range(len(self.ExisHVAC[i][4])):
                    if self.ExisHVAC[i][3][j].lower() in self.ExisHVAC[i][4][k].lower():
                        if self.ExisHVAC[i][4][k] + '_CoolCoil' in sensorlist:
                            if verbose:
                                print('Not added - ' + self.ExisHVAC[i][4][k] + '_CoolCoil Sensor')
                        else:
                            self.idf1.newidfobject(
                                'EnergyManagementSystem:Sensor',
                                Name=self.ExisHVAC[i][4][k] + '_CoolCoil',
                                OutputVariable_or_OutputMeter_Index_Key_Name=self.ExisHVAC[i][1][j],
                                OutputVariable_or_OutputMeter_Name=self.HVACdict[self.ExisHVAC[i][0]]
                            )
                            sensorlist.append(self.ExisHVAC[i][4][k] + '_CoolCoil')
                            if verbose:
                                print('Added - ' + self.ExisHVAC[i][4][k] + '_CoolCoil Sensor')
                #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.ExisHVAC[i][3][j]+'_CoolCoil'])
            if 'Heating' in self.ExisHVAC[i][1][j] or 'Heating' in self.HVACdict[self.ExisHVAC[i][0]]:
                zone_for_coil = self.ExisHVAC[i][3][j]
                matching_ems_names = []
                if hasattr(self, 'ems_zonenames') and hasattr(self, 'ems_objs_name'):
                    for z_idx, z_name in enumerate(self.ems_zonenames):
                        if z_name.upper() == zone_for_coil.upper():
                            matching_ems_names.append(self.ems_objs_name[z_idx])
                if not matching_ems_names:
                    matching_ems_names.append(zone_for_coil)

                for ems_name in matching_ems_names:
                    if ems_name + '_HeatCoil' in sensorlist:
                        if verbose:
                            print('Not added - ' + ems_name + '_HeatCoil Sensor')
                    else:
                        self.idf1.newidfobject(
                            'EnergyManagementSystem:Sensor',
                            Name=ems_name + '_HeatCoil',
                            OutputVariable_or_OutputMeter_Index_Key_Name=self.ExisHVAC[i][1][j],
                            OutputVariable_or_OutputMeter_Name=self.HVACdict[self.ExisHVAC[i][0]]
                        )
                        sensorlist.append(ems_name + '_HeatCoil')
                        if verbose:
                            print('Added - ' + ems_name + '_HeatCoil Sensor')
                # probando
                for k in range(len(self.ExisHVAC[i][4])):
                    if self.ExisHVAC[i][3][j].lower() in self.ExisHVAC[i][4][k].lower():
                        if self.ExisHVAC[i][4][k] + '_HeatCoil' in sensorlist:
                            if verbose:
                                print('Not added - ' + self.ExisHVAC[i][4][k] + '_HeatCoil Sensor')
                        else:
                            self.idf1.newidfobject(
                                'EnergyManagementSystem:Sensor',
                                Name=self.ExisHVAC[i][4][k] + '_HeatCoil',
                                OutputVariable_or_OutputMeter_Index_Key_Name=self.ExisHVAC[i][1][j],
                                OutputVariable_or_OutputMeter_Name=self.HVACdict[self.ExisHVAC[i][0]]
                            )
                            sensorlist.append(self.ExisHVAC[i][4][k] + '_HeatCoil')
                            if verbose:
                                print('Added - ' + self.ExisHVAC[i][4][k] + '_HeatCoil Sensor')

    # Keep the list of coil sensors for the init program
    self._exis_hvac_coil_sensors = [s for s in sensorlist if s.endswith('_CoolCoil') or s.endswith('_HeatCoil')]
    del sensorlist


def add_ems_init_existing_hvac(self, verbose: bool = True):
    """
    Adds an EMS Program and ProgramCallingManager with BeginNewEnvironment calling
    point to initialize all coil sensor variables to 0. This prevents EnergyPlus from
    raising a fatal "variable not initialized" error at the very first timestep, before
    the HVAC system has produced any output values.

    :param self: Used as a method for class ``accim.sim.engine.AccimJob``
    :param verbose: Inherited from class ``accim.sim.AddAccis``
    """
    programlist = [p.Name for p in self.idf1.idfobjects['EnergyManagementSystem:Program']]
    pcmlist = [p.Name for p in self.idf1.idfobjects['EnergyManagementSystem:ProgramCallingManager']]

    init_prog_name = 'InitExisHVACCoils'

    if init_prog_name in programlist:
        if verbose:
            print(f'Not added - {init_prog_name} Program (already exists)')
        return

    coil_sensors = getattr(self, '_exis_hvac_coil_sensors', [])
    if not coil_sensors:
        # Fall back: derive from ems_objs_name
        coil_sensors = []
        for name in getattr(self, 'ems_objs_name', []):
            coil_sensors.append(name + '_CoolCoil')
            coil_sensors.append(name + '_HeatCoil')

    if not coil_sensors:
        if verbose:
            print(f'No coil sensors found, skipping {init_prog_name}')
        return

    # Build kwargs for newidfobject: each SET line initialises one sensor variable
    prog_kwargs = {'Name': init_prog_name}
    for idx, sensor_name in enumerate(coil_sensors, start=1):
        prog_kwargs[f'Program_Line_{idx}'] = f'SET {sensor_name} = 0'

    self.idf1.newidfobject('EnergyManagementSystem:Program', **prog_kwargs)
    if verbose:
        print(f'Added - {init_prog_name} Program ({len(coil_sensors)} coil variables initialised)')

    # Register the init program under BeginNewEnvironment so it runs before any ApplyAST
    if init_prog_name not in pcmlist:
        self.idf1.newidfobject(
            'EnergyManagementSystem:ProgramCallingManager',
            Name=init_prog_name,
            EnergyPlus_Model_Calling_Point='BeginNewEnvironment',
            Program_Name_1=init_prog_name
        )
        if verbose:
            print(f'Added - {init_prog_name} ProgramCallingManager (BeginNewEnvironment)')
