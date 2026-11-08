# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The size of the output files of a simulation of a model, estimated from its outputs without simulating it.

:func:`accim.run.run_ep` runs each IDF with each EPW with EnergyPlus and ReadVarsESO, as EP-Launch, which write
(with the names 'IDF name[EPW name'): the ESO file (the values of the report variables and meters, as text), the CSV
file (the same values, as a table), the MTR and Meter.csv files (those of the meters), the SQL file (with an
Output:SQLite object) and other smaller files (EIO, HTML tables...). The ESO and CSV files are usually more than
90 % of them, and their size is that of their values: the series that the Output:Variable and Output:Meter objects of
the model report (each key of each variable, at each frequency), times the times each series is reported (8760 hours
in a year...), times the bytes of each value (about 17 in the ESO file and 11 in the CSV file, from the files of
EnergyPlus 25.1).

The keys of an Output:Variable object with the key '*' are counted from the objects of the model that report the
variable (the zones for 'Zone ...', the People objects for 'Zone Thermal Comfort ...', the coils, the nodes...); those
of the variables that this module does not know are counted as one, and the notes of the estimate name them. The values
take more or fewer characters depending on the numbers (0.0 or 21.4507762339585), and the other files are estimated
roughly, so the sizes are approximate: in 16 simulations of the output IDFs of AddAccis and of example files of
EnergyPlus, the estimates of the results of more than 5 MB were within 10 % of the files, and those of smaller results
(where the other files are a larger part) within 45 %. :func:`accim.run.estimate_results_size` can also measure them
with a simulation (``simulate=True``).
"""

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

__all__ = ['FREQUENCIES', 'MEMORY_PER_VALUE', 'SIZE_COLUMNS', 'SimulationSize', 'estimate_simulation_size',
           'format_size']

#: The reporting frequencies, from the most to the least frequent.
FREQUENCIES = ('timestep', 'hourly', 'daily', 'monthly', 'runperiod', 'annual')
_FREQUENCY_ALIASES = {'detailed': 'timestep', 'environment': 'runperiod', '': 'hourly'}
_FREQUENCY_TEXT = {'timestep': 'timestep', 'hourly': 'hour', 'daily': 'day', 'monthly': 'month',
                   'runperiod': 'run period', 'annual': 'year'}

# The bytes of the files of EnergyPlus 25.1 (with the line ends of Windows), measured in the simulations of the
# calibration: the sample model of accim and 5ZoneAirCooled, with the outputs of AddAccis and their own, at every
# frequency. In the ESO and MTR files, each value is a line, with the minimum and the maximum and when they happen
# from daily up; each time a frequency is reported, a line with the time stamp; and each series, a line of the data
# dictionary.
_ESO_VALUE = {'timestep': 16.5, 'hourly': 16.6, 'daily': 52.5, 'monthly': 62.0, 'runperiod': 68.0, 'annual': 68.0}
_ESO_STAMP = {'timestep': 38.9, 'hourly': 38.9, 'daily': 23.8, 'monthly': 9.8, 'runperiod': 7.0, 'annual': 7.0}
_ESO_DICTIONARY = {'timestep': 75.0, 'hourly': 75.0, 'daily': 115.0, 'monthly': 125.0, 'runperiod': 140.0,
                   'annual': 140.0}
_ESO_FIXED = 900.0
_ESO_ENVIRONMENT = 90.0
# In the CSV files, a row for each time stamp of the most frequent frequency (the others are in the same rows, at
# their times), with the date and a comma for each column, and each value without its comma; the header has the name
# of each column (key, variable, units and frequency).
_CSV_VALUE = {'timestep': 10.5, 'hourly': 10.5, 'daily': 13.0, 'monthly': 13.0, 'runperiod': 13.0, 'annual': 13.0}
_CSV_ROW = 18.0
_CSV_VARIABLE_COLUMN = 62.0
_CSV_METER_COLUMN = 33.0
# The SQL file: a row of about 20 bytes for each value, and the tables of the HTML file with 'SimpleAndTabular'.
_SQL_VALUE = 20.0
_SQL_STAMP = 30.0
_SQL_FIXED = 50_000.0
# The other files (EIO, BND, MTD, RDD, MDD, Zsz.csv, ERR...) grow with the model; the tables of the summary reports
# (Table.htm, Table.csv), with the reports and the zones.
_OTHER_FIXED = 150_000.0
_OTHER_PER_ZONE = 50_000.0
_TABLES_PER_ZONE_ALL_SUMMARY = 180_000.0
_TABLES_PER_REPORT = 20_000.0
_TABLES_PER_ZONE = 20_000.0
#: The bytes of each value of the CSV files in memory, as float64 (as in ``get_hourly_df_parametric``).
MEMORY_PER_VALUE = 8
#: The columns of :meth:`SimulationSize.megabytes`.
SIZE_COLUMNS = ['eso_mb', 'csv_mb', 'mtr_mb', 'meter_csv_mb', 'sql_mb', 'other_mb', 'simulation_mb', 'kept_mb',
                'csv_memory_mb']

#: The base surfaces and subsurfaces, which report the variables 'Surface ...'.
_SURFACES = ('BuildingSurface:Detailed', 'Wall:Detailed', 'RoofCeiling:Detailed', 'Floor:Detailed', 'Wall:Exterior',
             'Roof', 'Wall:Adiabatic', 'Wall:Underground', 'Wall:Interzone', 'Ceiling:Adiabatic',
             'Ceiling:Interzone', 'Floor:GroundContact', 'Floor:Adiabatic', 'Floor:Interzone')
_SUBSURFACES = ('FenestrationSurface:Detailed', 'Window', 'Door', 'GlazedDoor', 'Window:Interzone', 'Door:Interzone',
                'GlazedDoor:Interzone')
_SCHEDULES = ('Schedule:Compact', 'Schedule:Constant', 'Schedule:Year', 'Schedule:File')
#: The components of the AirflowNetwork:MultiZone:Surface objects that open (windows and doors).
_OPENING_COMPONENTS = ('AirflowNetwork:MultiZone:Component:DetailedOpening',
                       'AirflowNetwork:MultiZone:Component:SimpleOpening',
                       'AirflowNetwork:MultiZone:Component:HorizontalOpening')
#: Variables renamed by EnergyPlus 9.4, which accim requests with both names: {old name: new name}. Each version
#: reports one of them.
_RENAMED_VARIABLES = {'facility total hvac electric demand power': 'facility total hvac electricity demand rate'}
#: The objects whose energy goes to the district heating and cooling meters (without them, these meters do not
#: exist).
_DISTRICT_OBJECTS = ('DistrictHeating', 'DistrictCooling', 'ZoneHVAC:IdealLoadsAirSystem')
#: Other variables (with the key '*'), by the beginning of their names, and the beginning of the types of the objects
#: that report them.
_OTHER_OBJECTS = (
    ('chilled water thermal storage ', 'ThermalStorage:ChilledWater:'),
    ('ice thermal storage ', 'ThermalStorage:Ice:'),
    ('district heating ', 'DistrictHeating'),
    ('district cooling ', 'DistrictCooling'),
    ('evaporative cooler ', 'EvaporativeCooler:'),
    ('heat exchanger ', 'HeatExchanger:'),
    ('humidifier ', 'Humidifier:'),
    ('zone air terminal ', 'AirTerminal:'),
    ('water use equipment ', 'WaterUse:Equipment'),
    ('generator ', 'Generator:'),
    ('inverter ', 'ElectricLoadCenter:Inverter:'),
    ('electric load center ', 'ElectricLoadCenter:Distribution'),
)
_METERS_IN_REPORT_FILES = ('Output:Meter', 'Output:Meter:Cumulative')
_METERS_IN_METER_FILES_ONLY = ('Output:Meter:MeterFileOnly', 'Output:Meter:Cumulative:MeterFileOnly')


def format_size(size: float) -> str:
    """A size in bytes with the unit that fits it (kB, MB, GB or TB, of 1000 bytes...)."""
    for unit, factor in (('TB', 1e12), ('GB', 1e9), ('MB', 1e6), ('kB', 1e3)):
        if size >= factor:
            return f'{size / factor:.1f} {unit}'
    return f'{size:.0f} bytes'


@dataclass
class SimulationSize:
    """The size of the output files of a simulation, in bytes.

    :ivar eso: The ESO file (the values of the report variables and meters).
    :ivar csv: The CSV file of the ESO file.
    :ivar mtr: The MTR file (the values of the meters).
    :ivar meter_csv: The CSV file of the MTR file ('Meter.csv').
    :ivar sql: The SQL file (with an Output:SQLite object).
    :ivar other: The other files (EIO, ERR, the tables of the summary reports...).
    :ivar csv_values: The cells of the CSV file (its rows times its columns).
    :ivar series: The series that the ESO and MTR files report at each frequency (each key of each variable, and each
        meter); empty if the size was measured.
    :ivar notes: What the size does not include, or includes approximately.
    """

    eso: float = 0.0
    csv: float = 0.0
    mtr: float = 0.0
    meter_csv: float = 0.0
    sql: float = 0.0
    other: float = 0.0
    csv_values: int = 0
    series: Dict[str, int] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        """All the files."""
        return self.eso + self.csv + self.mtr + self.meter_csv + self.sql + self.other

    @property
    def kept(self) -> float:
        """The files that :func:`accim.run.remove_files` keeps: the ESO and CSV files."""
        return self.eso + self.csv

    @property
    def csv_memory(self) -> float:
        """The memory to read the values of the CSV file, as float64 (8 bytes each)."""
        return self.csv_values * MEMORY_PER_VALUE

    def megabytes(self) -> Dict[str, float]:
        """The sizes in MB (of 10^6 bytes), as in the tables of :class:`accim.sim.accis.AddAccis` and
        :func:`accim.run.estimate_results_size`: the files, the whole simulation, the files that
        :func:`accim.run.remove_files` keeps and the memory to read the values of the CSV file."""
        return {'eso_mb': self.eso / 1e6, 'csv_mb': self.csv / 1e6, 'mtr_mb': self.mtr / 1e6,
                'meter_csv_mb': self.meter_csv / 1e6, 'sql_mb': self.sql / 1e6, 'other_mb': self.other / 1e6,
                'simulation_mb': self.total / 1e6, 'kept_mb': self.kept / 1e6, 'csv_memory_mb': self.csv_memory / 1e6}

    def describe(self) -> str:
        """The size and that of the main files, for instance '30.1 MB (ESO 16.3 MB, CSV 11.3 MB, MTR and Meter.csv
        2.0 MB, other files 0.5 MB)'."""
        parts = [f'ESO {format_size(self.eso)}', f'CSV {format_size(self.csv)}']
        meters = self.mtr + self.meter_csv
        # Small meter files (no meters) are among the other files
        other = self.other + (meters if meters < 1e5 else 0)
        if meters >= 1e5:
            parts.append(f'MTR and Meter.csv {format_size(meters)}')
        if self.sql:
            parts.append(f'SQL {format_size(self.sql)}')
        parts.append(f'other files {format_size(other)}')
        return f'{format_size(self.total)} ({", ".join(parts)})'

    def describe_series(self) -> str:
        """The series reported at each frequency, for instance '110 values every hour'."""
        parts = [f'{count} every {_FREQUENCY_TEXT[frequency]}' for frequency, count in self.series.items() if count]
        if not parts:
            return ''
        parts[0] = parts[0].replace(' every ', ' values every ', 1)
        return ', '.join(parts)


def _objects(idf, object_type: str) -> list:
    """The objects of a type, or none if the IDD of the model does not have it (eppy and besos take the type in
    capitals)."""
    return list(idf.idfobjects.get(object_type.upper(), []))


def _text(value) -> str:
    return '' if value is None else str(value).strip()


def _field(obj, name: str) -> str:
    """The value of a field, or '' if the IDD of the model does not have it."""
    try:
        return _text(getattr(obj, name))
    except Exception:  # noqa: BLE001 (eppy raises its own errors for the fields that the IDD does not have)
        return ''


def _yes(value: str, default: bool) -> bool:
    return default if not value else value.lower() == 'yes'


def _integer(value: str, default: int) -> int:
    try:
        return int(float(value))
    except ValueError:
        return default


def _count(idf, *object_types: str) -> int:
    return sum(len(_objects(idf, object_type)) for object_type in object_types)


def _count_starting(idf, prefix: str, excluding: str = '') -> int:
    """The objects of the types whose names begin with a text (and do not contain another one)."""
    prefix, excluding = prefix.upper(), excluding.upper()
    return sum(len(objects) for object_type, objects in idf.idfobjects.items()
               if object_type.upper().startswith(prefix) and not (excluding and excluding in object_type.upper()))


@dataclass(frozen=True)
class _Period:
    """An environment that EnergyPlus simulates: its days and the months it touches."""

    days: int
    months: int


def _date(year: int, month: int, day: int) -> datetime.date:
    try:
        return datetime.date(year, month, day)
    except ValueError:  # 29 February of a year that is not a leap year, or a day out of the month
        return datetime.date(year, month, 28)


def _period(obj, with_years: bool) -> _Period:
    begin_year = _integer(_field(obj, 'Begin_Year'), 0) if with_years else 0
    end_year = _integer(_field(obj, 'End_Year'), 0) if with_years else 0
    # Without years, a year that is not a leap year, as EnergyPlus
    year = begin_year or 2001
    begin = _date(year, _integer(_field(obj, 'Begin_Month'), 1), _integer(_field(obj, 'Begin_Day_of_Month'), 1))
    end = _date(end_year or year, _integer(_field(obj, 'End_Month'), 12), _integer(_field(obj, 'End_Day_of_Month'), 31))
    if end < begin:
        end = _date(end.year + 1, end.month, end.day)
    return _Period((end - begin).days + 1, (end.year - begin.year) * 12 + end.month - begin.month + 1)


def _environments(idf) -> Tuple[List[_Period], List[_Period]]:
    """The sizing periods and the run periods that EnergyPlus simulates (SimulationControl: 'Run Simulation for Sizing
    Periods' and 'Run Simulation for Weather File Run Periods', both Yes by default)."""
    controls = _objects(idf, 'SimulationControl')
    control = controls[0] if controls else None
    sizing = []
    if _yes(_field(control, 'Run_Simulation_for_Sizing_Periods') if control else '', True):
        sizing += [_Period(1, 1)] * _count(idf, 'SizingPeriod:DesignDay')
        sizing += [_period(obj, with_years=False) for obj in _objects(idf, 'SizingPeriod:WeatherFileDays')]
        # The weeks of the weather file (extreme or typical)
        sizing += [_Period(7, 1)] * _count(idf, 'SizingPeriod:WeatherFileConditionType')
    runs = []
    if _yes(_field(control, 'Run_Simulation_for_Weather_File_Run_Periods') if control else '', True):
        runs = [_period(obj, with_years=True) for obj in _objects(idf, 'RunPeriod')]
    return sizing, runs


def _intervals(periods: List[_Period], timesteps: int) -> Dict[str, int]:
    """The times that a series of each frequency is reported in some environments."""
    days = sum(period.days for period in periods)
    return {'timestep': days * 24 * timesteps, 'hourly': days * 24, 'daily': days,
            'monthly': sum(period.months for period in periods), 'runperiod': len(periods),
            'annual': sum(max(1, round(period.days / 365)) for period in periods)}


def _frequency(value: str) -> str:
    text = value.lower()
    text = _FREQUENCY_ALIASES.get(text, text)
    return text if text in FREQUENCIES else 'hourly'


def _nodes(idf) -> int:
    """The nodes of the model, which report the variables 'System Node ...': the different names in its fields of
    nodes (the fields whose names have 'Node' and end with 'Name'), with the nodes of the NodeList objects instead of
    their names."""
    node_lists = {_field(obj, 'Name').lower(): [_text(value).lower() for value in obj.fieldvalues[2:] if _text(value)]
                  for obj in _objects(idf, 'NodeList')}
    nodes = set()
    for object_type, objects in idf.idfobjects.items():
        if object_type.upper() == 'NODELIST':
            continue
        for obj in objects:
            for name, value in zip(obj.fieldnames, obj.fieldvalues):
                if 'node' in name.lower() and name.lower().endswith('name') and _text(value):
                    node = _text(value).lower()
                    nodes.update(node_lists.get(node, [node]))
    return len(nodes)


def _airflow_network(idf) -> bool:
    """True if EnergyPlus simulates the AirflowNetwork of the model (which then reports the variables 'AFN ...' and
    ignores the ZoneInfiltration and ZoneVentilation objects)."""
    controls = _objects(idf, 'AirflowNetwork:SimulationControl')
    if not controls:
        return False
    control = _field(controls[0], 'AirflowNetwork_Control') or 'NoMultizoneOrDistribution'
    return control.upper() != 'NOMULTIZONEORDISTRIBUTION'


def _keys(idf, variable: str) -> Optional[int]:
    """The keys of a variable with the key '*': the objects of the model that report it (None if this module does not
    know which ones)."""
    from accim.utils.people import get_people_objects

    name = variable.lower()
    afn = _airflow_network(idf)
    if name.startswith(('site ', 'facility ', 'building ', 'environmental impact ', 'hvac system ')):
        return 1
    if name.startswith('afn zone '):
        return _count(idf, 'AirflowNetwork:MultiZone:Zone') if afn else 0
    if name.startswith('afn surface venting '):
        # Only the surfaces whose component opens (not the cracks)
        openings = {_field(obj, 'Name').lower() for object_type in _OPENING_COMPONENTS
                    for obj in _objects(idf, object_type)}
        surfaces = _objects(idf, 'AirflowNetwork:MultiZone:Surface')
        return sum(1 for surface in surfaces if _field(surface, 'Leakage_Component_Name').lower() in openings) \
            if afn else 0
    if name.startswith('afn surface '):
        return _count(idf, 'AirflowNetwork:MultiZone:Surface') if afn else 0
    if name.startswith('afn '):
        return _count(idf, 'AirflowNetwork:MultiZone:Zone', 'AirflowNetwork:MultiZone:Surface') if afn else 0
    if name.startswith(('zone thermal comfort ', 'people ')):
        return len(get_people_objects(idf))
    if name.startswith('zone ideal loads '):
        return _count(idf, 'ZoneHVAC:IdealLoadsAirSystem')
    if name.startswith('zone ventilation '):
        return 0 if afn else _count(idf, 'ZoneVentilation:DesignFlowRate', 'ZoneVentilation:WindandStackOpenArea')
    if name.startswith('zone infiltration '):
        return 0 if afn else _count_starting(idf, 'ZoneInfiltration:')
    if name.startswith('zone vrf air terminal '):
        return _count(idf, 'ZoneHVAC:TerminalUnit:VariableRefrigerantFlow')
    if name == 'zone thermostat operative temperature':
        # The zones with a thermostat (the air temperature, of all the zones)
        return min(_count(idf, 'ZoneControl:Thermostat'), _count(idf, 'Zone'))
    if name.startswith('zone '):
        return _count(idf, 'Zone')
    if name.startswith('space '):
        return _count(idf, 'Space') or _count(idf, 'Zone')
    if name.startswith('lights '):
        return _count(idf, 'Lights')
    if name.startswith('electric equipment '):
        return _count(idf, 'ElectricEquipment')
    if name.startswith('gas equipment '):
        return _count(idf, 'GasEquipment')
    if name.startswith('other equipment '):
        return _count(idf, 'OtherEquipment')
    if name.startswith(('surface window ', 'surface shading device ')):
        return _count(idf, *_SUBSURFACES)
    if name.startswith('surface '):
        return _count(idf, *_SURFACES, *_SUBSURFACES)
    if name.startswith('cooling coil '):
        # Not the performance, operating mode and speed objects of Coil:Cooling:DX
        return _count_starting(idf, 'Coil:Cooling:', excluding=':CurveFit:')
    if name.startswith('heating coil '):
        return _count_starting(idf, 'Coil:Heating:')
    if name.startswith('vrf heat pump '):
        return _count_starting(idf, 'AirConditioner:VariableRefrigerantFlow')
    if name.startswith('fan '):
        return _count_starting(idf, 'Fan:')
    if name.startswith('pump '):
        return _count_starting(idf, 'Pump:') + _count_starting(idf, 'HeaderedPumps:')
    if name.startswith('boiler '):
        return _count_starting(idf, 'Boiler:')
    if name.startswith('chiller '):
        return _count_starting(idf, 'Chiller:')
    if name.startswith('cooling tower '):
        return _count_starting(idf, 'CoolingTower:')
    if name.startswith('baseboard '):
        return _count_starting(idf, 'ZoneHVAC:Baseboard:')
    if name.startswith('unitary system '):
        return _count(idf, 'AirLoopHVAC:UnitarySystem')
    if name.startswith('air system '):
        return _count(idf, 'AirLoopHVAC')
    if name.startswith('water heater '):
        return _count_starting(idf, 'WaterHeater:')
    if name == 'schedule value':
        return _count(idf, *_SCHEDULES)
    if name.startswith('system node '):
        return _nodes(idf)
    if name.startswith('plant load profile '):
        return _count(idf, 'LoadProfile:Plant')
    if name.startswith('plant '):
        return _count(idf, 'PlantLoop', 'CondenserLoop')
    for prefix, object_prefix in _OTHER_OBJECTS:
        if name.startswith(prefix):
            return _count_starting(idf, object_prefix)
    return None


def _variable_series(idf) -> Tuple[Dict[str, int], List[str], bool]:
    """The series of the Output:Variable objects at each frequency, the variables with the key '*' whose keys were
    counted as one, and whether some variable is reported at each HVAC timestep (Detailed)."""
    ems_variables = {_field(obj, 'Name').lower() for obj in _objects(idf, 'EnergyManagementSystem:OutputVariable')}
    requests: Dict[Tuple[str, str], Tuple[set, list]] = {}
    names = {}
    detailed = False
    for output in _objects(idf, 'Output:Variable'):
        variable = _field(output, 'Variable_Name')
        key = _field(output, 'Key_Value')
        frequency_text = _field(output, 'Reporting_Frequency')
        detailed = detailed or frequency_text.lower() == 'detailed'
        keys, every_key = requests.setdefault((variable.lower(), _frequency(frequency_text)), (set(), []))
        if key in ('', '*'):
            every_key.append(True)
        else:
            keys.add(key.lower())
        names[variable.lower()] = variable
    series = dict.fromkeys(FREQUENCIES, 0)
    uncounted = set()
    for (variable, frequency), (keys, every_key) in requests.items():
        if (_RENAMED_VARIABLES.get(variable), frequency) in requests:
            # The old name of a variable that is also requested with its new one
            continue
        if variable in ems_variables:
            # The EMS output variables have one key, 'EMS'
            count = 1
        elif every_key:
            count = _keys(idf, variable)
            if count is None:
                count = max(1, len(keys))
                uncounted.add(names[variable])
        else:
            count = len(keys)
        series[frequency] += count
    return series, sorted(uncounted), detailed


def _meter_series(idf) -> Tuple[Dict[str, int], Dict[str, int]]:
    """The meters at each frequency in the ESO file (Output:Meter, Output:Meter:Cumulative) and in the MTR file (those
    and the MeterFileOnly ones)."""
    in_report_files = {frequency: set() for frequency in FREQUENCIES}
    in_meter_files = {frequency: set() for frequency in FREQUENCIES}
    district = any(_count_starting(idf, prefix) for prefix in _DISTRICT_OBJECTS)
    for object_type in _METERS_IN_REPORT_FILES + _METERS_IN_METER_FILES_ONLY:
        for meter in _objects(idf, object_type):
            identity = _field(meter, 'Key_Name').lower()
            if identity.startswith('district') and not district:
                continue
            frequency = _frequency(_field(meter, 'Reporting_Frequency'))
            in_meter_files[frequency].add(identity)
            if object_type in _METERS_IN_REPORT_FILES:
                in_report_files[frequency].add(identity)
    return ({frequency: len(meters) for frequency, meters in in_report_files.items()},
            {frequency: len(meters) for frequency, meters in in_meter_files.items()})


def _report_file(series: Dict[str, int], intervals: Dict[str, int], environments: int) -> float:
    """The bytes of an ESO or MTR file."""
    size = _ESO_FIXED + environments * _ESO_ENVIRONMENT
    for frequency in FREQUENCIES:
        if series[frequency]:
            size += series[frequency] * _ESO_DICTIONARY[frequency]
            size += intervals[frequency] * (_ESO_STAMP[frequency] + series[frequency] * _ESO_VALUE[frequency])
    return size


def _csv_file(series: Dict[str, int], intervals: Dict[str, int], column: float) -> Tuple[float, int]:
    """The bytes and the cells of the CSV file of an ESO or MTR file."""
    columns = sum(series.values())
    if not columns:
        return 0.0, 0
    rows = next(intervals[frequency] for frequency in FREQUENCIES if series[frequency])
    values = sum(series[frequency] * intervals[frequency] * _CSV_VALUE[frequency] for frequency in FREQUENCIES)
    return 11 + columns * column + rows * (_CSV_ROW + columns) + values, rows * columns


def _tables(idf, zones: int) -> float:
    """The bytes of the tables of the summary reports (Table.htm, Table.csv...)."""
    reports = [_text(value) for obj in _objects(idf, 'Output:Table:SummaryReports')
               for value in obj.fieldvalues[1:] if _text(value)]
    if not reports:
        return 0.0
    if any(report.lower().startswith('allsummary') for report in reports):
        return _TABLES_PER_ZONE_ALL_SUMMARY * max(zones, 1)
    return _TABLES_PER_REPORT * len(reports) + _TABLES_PER_ZONE * zones


def estimate_simulation_size(idf) -> SimulationSize:
    """Estimate, without simulating the model, the size of the output files of one of its simulations with
    :func:`accim.run.run_ep` (with any weather file).

    From the Output:Variable and Output:Meter objects of the model (the keys of the variables with the key '*' are
    counted from the objects that report them), its run periods and sizing periods (SimulationControl), its timesteps
    per hour, and its OutputControl:Files, Output:SQLite and Output:Table:SummaryReports objects. See the module
    :mod:`accim.sim.results_size` for how accurate it is.

    :param idf: The model, an eppy (or besos) IDF object.
    :return: The estimated sizes of the files, in bytes.
    """
    sizing, runs = _environments(idf)
    timesteps_objects = _objects(idf, 'Timestep')
    timesteps = _integer(_field(timesteps_objects[0], 'Number_of_Timesteps_per_Hour'), 6) if timesteps_objects else 6
    all_intervals = _intervals(sizing + runs, timesteps)
    variables, uncounted, detailed = _variable_series(idf)
    report_meters, all_meters = _meter_series(idf)
    eso_series = {frequency: variables[frequency] + report_meters[frequency] for frequency in FREQUENCIES}

    controls = _objects(idf, 'OutputControl:Files')
    control = controls[0] if controls else None
    eso_on = _yes(_field(control, 'Output_ESO') if control else '', True)
    mtr_on = _yes(_field(control, 'Output_MTR') if control else '', True)
    # With 'Output CSV', EnergyPlus writes the CSV files itself, with the run periods only; otherwise ReadVarsESO
    # writes them from the ESO and MTR files, with the sizing periods too
    csv_direct = _yes(_field(control, 'Output_CSV') if control else '', False)
    csv_intervals = _intervals(runs, timesteps) if csv_direct else all_intervals

    size = SimulationSize(series={frequency: eso_series[frequency] + all_meters[frequency] - report_meters[frequency]
                                  for frequency in FREQUENCIES})
    environments = len(sizing) + len(runs)
    if eso_on:
        size.eso = _report_file(eso_series, all_intervals, environments)
    if eso_on or csv_direct:
        size.csv, size.csv_values = _csv_file(eso_series, csv_intervals, _CSV_VARIABLE_COLUMN)
    if mtr_on:
        size.mtr = _report_file(all_meters, all_intervals, environments) if any(all_meters.values()) else _ESO_FIXED
    if (mtr_on or csv_direct) and any(all_meters.values()):
        size.meter_csv = _csv_file(all_meters, csv_intervals, _CSV_METER_COLUMN)[0]

    zones = _count(idf, 'Zone')
    tables = _tables(idf, zones)
    size.other = _OTHER_FIXED + _OTHER_PER_ZONE * zones + tables
    sqlite = _objects(idf, 'Output:SQLite')
    if sqlite:
        values = sum((eso_series[frequency] + all_meters[frequency]) * all_intervals[frequency]
                     for frequency in FREQUENCIES)
        stamps = sum(all_intervals[frequency] for frequency in FREQUENCIES
                     if eso_series[frequency] or all_meters[frequency])
        with_tables = 'tabular' in _field(sqlite[0], 'Option_Type').lower()
        size.sql = _SQL_FIXED + values * _SQL_VALUE + stamps * _SQL_STAMP + (tables if with_tables else 0)

    if uncounted:
        size.notes.append(f'the keys of the variables {uncounted}, requested with the key *, were counted as one '
                          f'each')
    if _count_starting(idf, 'HVACTemplate:'):
        size.notes.append('the model has HVACTemplate objects, so the keys of the variables of the HVAC objects they '
                          'stand for (coils, fans...) were not counted')
    if detailed:
        size.notes.append('the variables reported at each HVAC timestep (Detailed) were counted at each zone timestep, '
                          'so their size may be larger')
    for debug in _objects(idf, 'Output:EnergyManagementSystem'):
        if _field(debug, 'EMS_Runtime_Language_Debug_Output_Level').lower() == 'verbose':
            size.notes.append('the EDD file is not included: with EMS Runtime Language Debug Output Level Verbose '
                              '(Output:EnergyManagementSystem, debug_ems=True), it has each line of the EMS programs '
                              'that runs, and it can take gigabytes')
    return size
