# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Questions that :class:`accim.sim.accis.AddAccis` asks when some arguments are missing."""

from typing import Callable, Dict, Optional

from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS
from accim.sim.arguments import OUTPUT_FREQUENCIES, OUTPUT_TYPES, SCRIPT_TYPES, SUPPLY_AIR_TEMP_INPUT_METHODS, \
    SETPOINT_TYPES, to_day_of_year
from accim.sim.standards import COMFORT_STANDARDS

__all__ = ['ask_generation_arguments', 'ask_model_arguments']

_SETPOINT_TABLE = ('Please refer to the full list of setpoint temperatures at https://htmlpreview.github.io/?'
                   'https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html')
_SURE_NUMBERS = '          Are you sure the numbers are correct? [y or [] / n]: '
_SURE_NUMBER = '          Are you sure the number is correct? [y or [] / n]: '
_CATEGORY_NAMES = {1: '1 = CAT I / CAT A;', 2: '2 = CAT II / CAT B;', 3: '3 = CAT III / CAT C;',
                   80: '80 = 80% ACCEPT;', 85: '85 = 85% ACCEPT;', 90: '90 = 90% ACCEPT;'}
_COMFORT_MODES = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]


def _ask_until_valid(ask: Callable[[str], str], prompt: str, retry: str, valid: Callable[[str], bool]) -> str:
    answer = ask(prompt)
    while not valid(answer):
        answer = ask(retry)
    return answer


def ask_model_arguments(ask: Optional[Callable[[str], str]] = None) -> Dict:
    """Ask the arguments of the models: script type, outputs, EnergyPlus version and temperature control.

    :param ask: The function that asks each question and returns the answer (by default, ``input``).
    """
    ask = ask or input
    print(
        '\nNow, you are going to be asked to enter some information for different arguments '
        'to generate the output IDFs with adaptive setpoint temperatures. '
        '\nIf you are not sure about how to use these parameters, please take a look at the documentation in the '
        'following link: '
        '\nhttps://accim.readthedocs.io/en/master/4_detailed%20use.html'
        '\n\nPlease, enter the following information:'
    )
    script_types = ('for VRFsystem with full air-conditioning mode: vrf_ac;\n'
                    'for VRFsystem with mixed-mode: vrf_mm;\n'
                    'for ExistingHVAC with mixed mode: ex_mm;\n'
                    'for ExistingHVAC with full air-conditioning mode: ex_ac\n')
    args = {'script_type': _ask_until_valid(
        ask, f'\nEnter the ScriptType (\n{script_types}): ',
        '    ScriptType was not correct.     Enter the ScriptType (\n    '
        + script_types.replace('\n', '\n    ').rstrip(' ') + '    ): ',
        lambda a: a in SCRIPT_TYPES)}
    args['supply_air_temp_input_method'] = None
    if args['script_type'].startswith('vrf'):
        methods = ('for Supply Air Temperature: supply air temperature;\n'
                   'for Temperature Difference: temperature difference;\n): ')
        args['supply_air_temp_input_method'] = _ask_until_valid(
            ask, f'\nEnter the SupplyAirTempInputMethod (\n{methods}',
            f'    SupplyAirTempInputMethod was not correct.     Enter the SupplyAirTempInputMethod (\n{methods}',
            lambda a: a in SUPPLY_AIR_TEMP_INPUT_METHODS)
    args['keep_existing_outputs'] = _ask_until_valid(
        ask, '\nDo you want to keep the existing outputs (true or false)?: ',
        'The answer you entered is not valid. Do you want to keep the existing outputs (true or false)?: ',
        lambda a: a.lower() in ('true', 'false')).lower() == 'true'
    args['output_type'] = _ask_until_valid(
        ask, '\nEnter the Output type (standard, simplified, detailed or custom): ',
        '   Output type was not correct. Please, enter the Output type (standard, simplified, detailed or custom): ',
        lambda a: a.lower() in OUTPUT_TYPES)
    # At least one frequency (before, an empty answer gave no frequencies)
    args['output_frequencies'] = _ask_until_valid(
        ask, '\nEnter the Output frequencies separated by space (timestep, hourly, daily, monthly, runperiod): ',
        'Some of the Output frequencies are not correct. Please, enter the Output frequencies again separated by '
        'space (timestep, hourly, daily, monthly, runperiod): ',
        lambda a: bool(a.split()) and all(f.lower() in OUTPUT_FREQUENCIES for f in a.split())).split()
    args['make_outputs_dataframe'] = _ask_until_valid(
        ask, '\nDo you want to generate a dataframe to see all outputs? (true or false): ',
        'The answer you entered is not valid. Do you want to generate a dataframe to see all outputs? '
        '(true or false):',
        lambda a: a.lower() in ('true', 'false')).lower() == 'true'
    versions = f'{SUPPORTED_ENERGYPLUS_VERSIONS[0]} to {SUPPORTED_ENERGYPLUS_VERSIONS[-1]}, or auto'
    args['energyplus_version'] = _ask_until_valid(
        ask, f'\nEnter the EnergyPlus version ({versions}): ',
        f'    EnergyPlus version was not correct. Please, enter the EnergyPlus version ({versions}): ',
        lambda a: a in SUPPORTED_ENERGYPLUS_VERSIONS or a.lower() == 'auto')
    args['setpoint_type'] = _ask_until_valid(
        ask, '\nEnter the Temperature Control method (temperature or pmv): ',
        '  Temperature Control method was not correct. Please, enter the Temperature Control method '
        '(temperature or pmv): ',
        lambda a: a in SETPOINT_TYPES)
    return args


def _ask_list(ask, prompt: str, retry: str, convert: Callable, choices=None, default: Optional[list] = None,
              invalid_message: str = '') -> list:
    """Ask a list of numbers until it is valid, and then until the user confirms it."""
    def read(text):
        while True:
            try:
                values = [convert(v) for v in ask(text).split()]
            except ValueError:
                values = None
            if values == [] and default is not None:
                return list(default)
            if values and (choices is None or all(v in choices for v in values)):
                return values
            print(invalid_message)
            text = retry

    values = read(prompt)
    while ask(_SURE_NUMBERS) == 'n':
        values = read(retry)
    return values


def _ask_number(ask, prompt: str, retry: str, default: Optional[float] = None,
                valid: Callable[[float], bool] = lambda v: True, invalid_message: str = '') -> float:
    """Ask a number until it is valid (an empty answer is the default), and then until the user confirms it."""
    def read(text):
        while True:
            try:
                value = float(ask(text))
            except ValueError:
                if default is None:
                    print(invalid_message)
                    text = retry
                    continue
                value = default
            if valid(value):
                return value
            print(invalid_message)
            text = retry

    value = read(prompt)
    while ask(_SURE_NUMBER) == 'n':
        value = read(retry)
    return value


def _ask_day(ask, prompt: str, retry: str) -> int:
    def read(text):
        while True:
            try:
                return to_day_of_year(ask(text).strip())
            except ValueError:
                print('          The date is not correct. It must be a numeric date format dd/mm or the day of the '
                      'year. Please enter the value again.')
                text = retry

    day = read(prompt)
    while ask(_SURE_NUMBER) == 'n':
        day = read(retry)
    return day


def ask_generation_arguments(script_type: str, ask: Optional[Callable[[str], str]] = None) -> Dict:
    """Ask the arguments of the output IDFs: comfort models, HVAC modes, ventilation and tolerances.

    :param script_type: The script type, whose mixed mode (natural ventilation) needs more arguments.
    :param ask: The function that asks each question and returns the answer (by default, ``input``).
    """
    ask = ask or input
    print('The information you will be required to enter below will be used to generate the customised output IDFs:')
    standards = ''.join(f'{s.title};\n' for s in COMFORT_STANDARDS.values()).replace('1 = INT EN16798;',
                                                                                     '1 = INT EN16798-1;')
    args: Dict = {}
    args['comfort_standard'] = _ask_list(
        ask, f'Enter the Comfort Standard numbers separated by space (\n{standards}{_SETPOINT_TABLE}\n): ',
        '     Enter the Comfort Standard numbers separated by space: ', int, choices=list(COMFORT_STANDARDS),
        invalid_message='          Comfort Standard numbers are not correct. Please enter the numbers again.')

    custom = {'custom_slope': 0, 'custom_intercept': 0, 'custom_heating_offset': 0, 'custom_cooling_offset': 0,
              'custom_cooling_lower_limit': 0, 'custom_cooling_upper_limit': 0, 'custom_heating_lower_limit': 0,
              'custom_heating_upper_limit': 0}
    if 99 in args['comfort_standard']:
        print('\nYou have requested the use of a custom comfort model. Please enter the following data necessary '
              'to build the custom comfort model:')
        questions = [
            ('custom_slope', 'Enter the m coefficient (slope) of comfort model linear regression (mx+n) '
                             '(any number greater than 0): ', lambda v: v >= 0),
            ('custom_intercept', 'Enter the n coefficient of comfort model linear regression (mx+n): ',
             lambda v: True),
            ('custom_heating_offset', 'Enter the offset from neutral temperature for the heating setpoint (value '
                                      'will be summed, therefore, it should be negative): ', lambda v: v <= 0),
            ('custom_cooling_offset', 'Enter the offset from neutral temperature for the cooling setpoint (value '
                                      'will be summed, therefore, it should be positive): ', lambda v: v >= 0),
            ('custom_cooling_lower_limit',
             'Enter the value for the cooling setpoint applicability lower limit (ACSTall): ', lambda v: True),
            ('custom_cooling_upper_limit',
             'Enter the value for the cooling setpoint applicability upper limit (ACSTaul): ', lambda v: True),
            ('custom_heating_lower_limit',
             'Enter the value for the heating setpoint applicability lower limit (AHSTall): ', lambda v: True),
            ('custom_heating_upper_limit',
             'Enter the value for the heating setpoint applicability upper limit (AHSTaul): ', lambda v: True),
        ]
        for name, text, valid in questions:
            custom[name] = _ask_number(ask, '\n' + text, '          ' + text, valid=valid,
                                       invalid_message='          The number you entered is not allowed.')
    args.update(custom)

    print('\n')
    available_categories = []
    for number in args['comfort_standard']:
        standard = COMFORT_STANDARDS[number]
        print(f'For the comfort standard {standard.title}, the available categories you can choose are: ')
        for category, description in (standard.categories or {'n/a': 'n/a'}).items():
            print(f'{category} = {description}')
        available_categories += list(standard.categories)
    print('Enter the Category numbers separated by space (')
    for category, name in _CATEGORY_NAMES.items():
        if category in available_categories:
            print(name)
    print(_SETPOINT_TABLE)
    args['category'] = _ask_list(ask, '):', 'Enter the Category numbers separated by space: ', int,
                                 choices=list(_CATEGORY_NAMES),
                                 invalid_message='          Category numbers are not correct. Please enter the '
                                                 'numbers again.')
    print('\n')
    for number in args['comfort_standard']:
        standard = COMFORT_STANDARDS[number]
        print(f'For the comfort standard {standard.title}, the available ComfMods you can choose are: ')
        for mode, description in (standard.comfort_modes or {'n/a': 'n/a'}).items():
            print(f'{mode} = {description}')
    args['comfort_mode'] = _ask_list(
        ask, f'Enter the Comfort Mode numbers separated by space (\n0 or 0.X = Static;\n1, 1.X, 2, 3 = Adaptive;\n'
             f'{_SETPOINT_TABLE}\n): ',
        '     Enter the Comfort Mode numbers separated by space: ', float, choices=_COMFORT_MODES,
        invalid_message='          Comfort Mode numbers are not correct. Please enter the numbers again.')

    args['setpoint_accuracy'] = _ask_number(
        ask, '\nEnter the setpoint accuracy number (any number greater than 0, if omitted will be 10000): ',
        '      Enter the setpoint accuracy number (any number greater than 0, if omitted will be 10000): ',
        default=10000, valid=lambda v: v > 0,
        invalid_message='          The setpoint accuracy number is not correct. It must be a number greater than 0. '
                        'Please enter the number again.')
    args['category_cooling_offset'] = _ask_number(
        ask, '\nEnter the number for the CAT cooling offset modifier (value will be summed to the ACST, '
             'if omitted will be 0): ',
        '\n        Enter the number for the CAT cooling offset modifier (value will be summed to the ACST, '
        'if omitted will be 0): ', default=0.0)
    args['category_heating_offset'] = _ask_number(
        ask, '\nEnter the number for the CAT heating offset modifier (value will be summed to the AHST, '
             'if omitted will be 0): ',
        '\n        Enter the number for the CAT heating offset modifier (value will be summed to the AHST, '
        'if omitted will be 0): ', default=0.0, valid=lambda v: v <= args['category_cooling_offset'],
        invalid_message=f'          The CATheatOffset must not be larger than the CATcoolOffset '
                        f'({args["category_cooling_offset"]}), which will probably lead to an error in the '
                        f'EnergyPlus simulation.')

    if (any(n in (1, 2) for n in args['comfort_standard']) and 0 in args['comfort_mode']) \
            or 22 in args['comfort_standard']:
        args['cooling_season_start'] = _ask_day(
            ask, '\nEnter the start of the cooling season in numeric date format dd/mm or the day of the year: ',
            'Enter the start of the cooling season in numeric date format dd/mm or the day of the year: ')
        args['cooling_season_end'] = _ask_day(
            ask, '\nEnter the end of the cooling season in numeric date format dd/mm or the day of the year: ',
            'Enter the end of the cooling season in numeric date format dd/mm or the day of the year: ')
    else:
        args['cooling_season_start'], args['cooling_season_end'] = 121, 274

    if script_type.endswith('_mm'):
        args['hvac_mode'] = _ask_list(
            ask, '\nEnter the HVAC Mode numbers separated by space (\n0 = Fully Air-conditioned;\n'
                 '1 = Naturally ventilated;\n2 = Mixed Mode;\n): ',
            '     Enter the HVACmode numbers separated by space: ', int, choices=[0, 1, 2],
            invalid_message='          HVACmode numbers are not correct. Please enter the numbers again.')
        args['ventilation_control'] = _ask_list(
            ask, '\nEnter the Ventilation Control numbers separated by space (\n'
                 'If HVACmode = 1:\n'
                 '   0 = Ventilates above neutral temperature;\n'
                 '   1 = Ventilates above upper comfort limit;\n'
                 'If HVACmode = 2:\n'
                 '   0 = Ventilates above neutral temperature and fully opens doors and windows;\n'
                 '   1 = Ventilates above lower comfort limit and fully opens doors and windows;\n'
                 '   2 = Ventilates above neutral temperature and opens doors and windows based on the customised '
                 'venting opening factor;\n'
                 '   3 = Ventilates above lower comfort limit and opens doors and windows based on the customised '
                 'venting opening factor;\n): ',
            '     Enter the Ventilation Control numbers separated by space: ', int, choices=[0, 1, 2, 3],
            invalid_message='          Ventilation Control numbers are not correct. Please enter the numbers again.')
        if any(v in (2, 3) for v in args['ventilation_control']):
            args['opening_factor_max_temp_diff'] = _ask_number(
                ask, 'Enter the maximum temperature difference number for Ventilation Opening Factor '
                     '(any number larger than 0): ',
                '         Enter the maximum temperature difference number for Ventilation Opening Factor '
                '(any number larger than 0): ', valid=lambda v: v > 0,
                invalid_message='          The maximum temperature difference number is not correct. It must be a '
                                'number larger than 0. Please enter the number again.')
            args['opening_factor_min_temp_diff'] = _ask_number(
                ask, 'Enter the minimum temperature difference number for Ventilation Opening Factor (any number '
                     'larger than 0 and smaller than the maximum temperature difference number): ',
                '         Enter the minimum temperature difference number for Ventilation Opening Factor (any number '
                'larger than 0 and smaller than the maximum temperature difference number): ',
                valid=lambda v: 0 < v < args['opening_factor_max_temp_diff'],
                invalid_message='          The minimum temperature difference number is not correct. It must be a '
                                'number larger than 0 and smaller than the maximum temperature difference number. '
                                'Please enter the number again.')
            args['min_opening_factor'] = _ask_number(
                ask, 'Enter the multiplier number for Ventilation Opening Factor (any number between 0 and 1): ',
                '         Enter the multiplier number for modulating the Ventilation Opening Factor '
                '(any number between 0 and 1): ', valid=lambda v: 0 <= v <= 1,
                invalid_message='          The multiplier number is not correct. It must be a number between 0 '
                                'and 1. Please enter the number again.')
        else:
            args.update(opening_factor_max_temp_diff=6, opening_factor_min_temp_diff=1, min_opening_factor=0.25)
        for name, text, default in (('ventilation_setpoint_offset', 'VSToffset', 0.0),
                                    ('min_outdoor_temp_offset', 'MinOToffset', 50.0),
                                    ('max_wind_speed', 'MaxWindSpeed', 50.0)):
            omitted = int(default) if default == int(default) else default
            args[name] = _ask_list(
                ask, f'\nEnter the {text} numbers separated by space (if omitted, will be {omitted}): ',
                f'     Enter the {text} numbers separated by space (if omitted, will be {omitted}): ', float,
                default=[default], invalid_message=f'          {text} numbers are not correct.')
    else:
        args.update(hvac_mode=[0], ventilation_control=[0], opening_factor_max_temp_diff=1,
                    opening_factor_min_temp_diff=0, min_opening_factor=0, ventilation_setpoint_offset=[0],
                    min_outdoor_temp_offset=[0], max_wind_speed=[0])

    for name, text in (('setpoint_tolerance_start', '\nEnter the ASTtol value from (if omitted, will be 0.1): '),
                       ('setpoint_tolerance_end', 'Enter the ASTtol value to (if omitted, will be 0.1): '),
                       ('setpoint_tolerance_step', 'Enter the ASTtol value steps (if omitted, will be 0.1): ')):
        args[name] = _ask_number(ask, text, '     ' + text.lstrip('\n'), default=0.1)
    return args
