"""Tests for accim.sim.prompts, the questions that AddAccis asks when some arguments are missing.

Ported from the tests of the branch refactor/sim-v1 (tests/sim/test_prompts.py, for collect_basic_inputs):
scripted answers, and a question asked again after an invalid answer. In accim 1.0.0, the questions are asked by
ask_model_arguments and ask_generation_arguments, which take the function that asks them (``input`` by default)
and return the arguments with the names of accim 1.0.0. The supply air method of the existing HVAC systems, the
empty setpoint accuracy and the name suffix are tested in test_addaccis_arguments.py.
"""
import pytest

from accim.sim import prompts
from accim.sim.generation import GenerationArguments


class _Script:
    """Answers the questions in order, checking that each question has the expected text."""

    def __init__(self, steps):
        self.steps = list(steps)
        self.questions = []

    def __call__(self, question=''):
        assert self.steps, f'Unexpected question: {question!r}'
        expected, answer = self.steps.pop(0)
        assert expected in question, f'Expected a question with {expected!r}, got {question!r}'
        self.questions.append(question)
        return answer


def _confirmed(*steps):
    """Each answer followed by 'y' to the question that confirms it."""
    return [step for (expected, answer) in steps for step in ((expected, answer), ('Are you sure', 'y'))]


VRF_MODEL_ANSWERS = [
    ('Enter the ScriptType', 'vrf_mm'),
    ('Enter the SupplyAirTempInputMethod', 'supply air temperature'),
    ('keep the existing outputs', 'false'),
    ('Enter the Output type', 'standard'),
    ('Enter the Output frequencies', 'hourly'),
    ('generate a dataframe', 'false'),
    ('Enter the EnergyPlus version', 'auto'),
    ('Enter the Temperature Control method', 'temperature'),
]
VRF_MODEL_ARGUMENTS = {
    'script_type': 'vrf_mm',
    'supply_air_temp_input_method': 'supply air temperature',
    'keep_existing_outputs': False,
    'output_type': 'standard',
    'output_frequencies': ['hourly'],
    'make_outputs_dataframe': False,
    'energyplus_version': 'auto',
    'setpoint_type': 'temperature',
}


def test_ask_model_arguments_of_a_vrf_system():
    script = _Script(VRF_MODEL_ANSWERS)

    assert prompts.ask_model_arguments(ask=script) == VRF_MODEL_ARGUMENTS
    assert script.steps == []


def test_ask_model_arguments_of_the_existing_hvac_systems():
    # The existing HVAC systems have no supply air temperature input method
    script = _Script([
        ('Enter the ScriptType', 'ex_mm'),
        ('keep the existing outputs', 'TRUE'),
        ('Enter the Output type', 'detailed'),
        ('Enter the Output frequencies', 'hourly runperiod'),
        ('generate a dataframe', 'true'),
        ('Enter the EnergyPlus version', '9.6'),
        ('Enter the Temperature Control method', 'pmv'),
    ])

    assert prompts.ask_model_arguments(ask=script) == {
        'script_type': 'ex_mm',
        'supply_air_temp_input_method': None,
        'keep_existing_outputs': True,
        'output_type': 'detailed',
        'output_frequencies': ['hourly', 'runperiod'],
        'make_outputs_dataframe': True,
        'energyplus_version': '9.6',
        'setpoint_type': 'pmv',
    }
    assert script.steps == []


@pytest.mark.parametrize('index, invalid, again', [
    (0, 'vrf', 'ScriptType was not correct'),
    (1, 'supply air', 'SupplyAirTempInputMethod was not correct'),
    (2, 'no', 'The answer you entered is not valid. Do you want to keep the existing outputs'),
    (3, 'full', 'Output type was not correct'),
    (4, 'hourly weekly', 'Some of the Output frequencies are not correct'),
    (5, 'yes', 'The answer you entered is not valid. Do you want to generate a dataframe'),
    (6, '8.9', 'EnergyPlus version was not correct'),
    (7, 'adaptive', 'Temperature Control method was not correct'),
], ids=list(VRF_MODEL_ARGUMENTS))
def test_ask_model_arguments_asks_again_after_an_invalid_answer(index, invalid, again):
    expected, answer = VRF_MODEL_ANSWERS[index]
    script = _Script(VRF_MODEL_ANSWERS[:index] + [(expected, invalid), (again, answer)]
                     + VRF_MODEL_ANSWERS[index + 1:])

    assert prompts.ask_model_arguments(ask=script) == VRF_MODEL_ARGUMENTS
    assert script.steps == []


@pytest.mark.parametrize('empty', ['', '   '])
def test_an_empty_answer_to_the_output_frequencies_is_asked_again(empty):
    # Before, an empty answer was valid and gave no output frequencies ([])
    index = 4
    expected, answer = VRF_MODEL_ANSWERS[index]
    script = _Script(VRF_MODEL_ANSWERS[:index] + [(expected, empty), ('Some of the Output frequencies', answer)]
                     + VRF_MODEL_ANSWERS[index + 1:])

    assert prompts.ask_model_arguments(ask=script)['output_frequencies'] == ['hourly']
    assert script.steps == []


MIXED_MODE_STEPS = _confirmed(
    ('Enter the Comfort Standard numbers', '1 2'),
    ('):', '1 80'),
    ('Enter the Comfort Mode numbers', '0 3'),
    ('Enter the setpoint accuracy number', '1000'),
    ('CAT cooling offset modifier', '1'),
    ('CAT heating offset modifier', '-1'),
    # Static setpoints of EN16798-1 and ASHRAE 55 (ComfMod 0) need the cooling season
    ('start of the cooling season', '01/06'),
    ('end of the cooling season', '273'),
    ('Enter the HVAC Mode numbers', '0 2'),
    ('Enter the Ventilation Control numbers', '0 2'),
    # Ventilation controls 2 and 3 use the opening factor of the windows
    ('maximum temperature difference number', '5'),
    ('minimum temperature difference number', '2'),
    ('multiplier number', '0.5'),
    ('Enter the VSToffset numbers', '0 1'),
    ('Enter the MinOToffset numbers', ''),
    ('Enter the MaxWindSpeed numbers', '10'),
    ('ASTtol value from', '0.1'),
    ('ASTtol value to', '0.3'),
    ('ASTtol value steps', ''),
)
MIXED_MODE_ARGUMENTS = dict(
    comfort_standard=[1, 2], category=[1, 80], comfort_mode=[0, 3], setpoint_accuracy=1000, category_cooling_offset=1, category_heating_offset=-1,
    cooling_season_start=152, cooling_season_end=273, hvac_mode=[0, 2], ventilation_control=[0, 2], opening_factor_max_temp_diff=5,
    opening_factor_min_temp_diff=2, min_opening_factor=0.5, ventilation_setpoint_offset=[0, 1], min_outdoor_temp_offset=[50], max_wind_speed=[10],
    setpoint_tolerance_start=0.1, setpoint_tolerance_end=0.3, setpoint_tolerance_step=0.1,
    custom_slope=0, custom_intercept=0, custom_cooling_offset=0, custom_heating_offset=0, custom_cooling_upper_limit=0,
    custom_cooling_lower_limit=0, custom_heating_upper_limit=0, custom_heating_lower_limit=0,
)


def test_ask_generation_arguments_of_a_mixed_mode_model():
    script = _Script(MIXED_MODE_STEPS)

    args = prompts.ask_generation_arguments('vrf_mm', ask=script)

    assert args == MIXED_MODE_ARGUMENTS
    assert script.steps == []
    # The answers are the arguments of the output IDFs
    assert GenerationArguments(**args).tolerances() == pytest.approx([0.1, 0.2, 0.3])


def test_ask_generation_arguments_of_the_custom_comfort_model():
    script = _Script(_confirmed(
        ('Enter the Comfort Standard numbers', '99'),
        ('m coefficient', '0.31'),
        ('n coefficient', '17.8'),
        ('offset from neutral temperature for the heating setpoint', '-3.5'),
        ('offset from neutral temperature for the cooling setpoint', '3.5'),
        ('cooling setpoint applicability lower limit', '10'),
        ('cooling setpoint applicability upper limit', '33.5'),
        ('heating setpoint applicability lower limit', '10'),
        ('heating setpoint applicability upper limit', '33.5'),
        ('):', '80'),
        ('Enter the Comfort Mode numbers', '3'),
        ('Enter the setpoint accuracy number', ''),
        ('CAT cooling offset modifier', ''),
        ('CAT heating offset modifier', ''),
        ('ASTtol value from', ''),
        ('ASTtol value to', ''),
        ('ASTtol value steps', ''),
    ))

    args = prompts.ask_generation_arguments('vrf_ac', ask=script)

    assert script.steps == []
    assert (args['comfort_standard'], args['category'], args['comfort_mode']) == ([99], [80], [3])
    assert (args['custom_slope'], args['custom_intercept'], args['custom_heating_offset'], args['custom_cooling_offset'],
            args['custom_cooling_lower_limit'], args['custom_cooling_upper_limit'], args['custom_heating_lower_limit'],
            args['custom_heating_upper_limit']) == (0.31, 17.8, -3.5, 3.5, 10, 33.5, 10, 33.5)
    # Fully air-conditioned, with the defaults of the questions left empty
    assert (args['hvac_mode'], args['ventilation_control']) == ([0], [0])
    assert (args['setpoint_accuracy'], args['category_cooling_offset'], args['category_heating_offset']) == (10000, 0, 0)
    assert (args['cooling_season_start'], args['cooling_season_end']) == (121, 274)


def _replace(steps, expected, *new_steps):
    """The steps with the step of the question with the expected text replaced by new steps."""
    index = next(i for i, (text, _) in enumerate(steps) if text == expected)
    return steps[:index] + list(new_steps) + steps[index + 1:]


@pytest.mark.parametrize('question, new_steps, message', [
    ('Enter the Comfort Standard numbers',
     [('Enter the Comfort Standard numbers', '1 23'), ('Enter the Comfort Standard numbers', '1 2')],
     'Comfort Standard numbers are not correct'),
    ('):', [('):', '1 4'), ('Enter the Category numbers', '1 80')], 'Category numbers are not correct'),
    ('Enter the Comfort Mode numbers',
     [('Enter the Comfort Mode numbers', '0 2.5'), ('Enter the Comfort Mode numbers', '0 3')],
     'Comfort Mode numbers are not correct'),
    ('Enter the setpoint accuracy number',
     [('Enter the setpoint accuracy number', '-5'), ('Enter the setpoint accuracy number', '1000')],
     'The setpoint accuracy number is not correct'),
    ('CAT heating offset modifier',
     [('CAT heating offset modifier', '2'), ('CAT heating offset modifier', '-1')],
     'The CATheatOffset must not be larger than the CATcoolOffset'),
    ('start of the cooling season',
     [('start of the cooling season', '31/02'), ('start of the cooling season', '152')],
     'The date is not correct'),
    ('Enter the HVAC Mode numbers', [('Enter the HVAC Mode numbers', '3'), ('Enter the HVACmode numbers', '0 2')],
     'HVACmode numbers are not correct'),
    ('minimum temperature difference number',
     [('minimum temperature difference number', '5'), ('minimum temperature difference number', '2')],
     'The minimum temperature difference number is not correct'),
], ids=['comfort_standard', 'category', 'comfort_mode', 'setpoint_accuracy', 'category_heating_offset', 'cooling_season_start', 'hvac_mode',
        'opening_factor_min_temp_diff'])
def test_ask_generation_arguments_asks_again_after_an_invalid_answer(capsys, question, new_steps, message):
    script = _Script(_replace(MIXED_MODE_STEPS, question, *new_steps))

    assert prompts.ask_generation_arguments('vrf_mm', ask=script) == MIXED_MODE_ARGUMENTS
    assert script.steps == []
    assert message in capsys.readouterr().out


def test_ask_generation_arguments_asks_again_when_the_numbers_are_not_confirmed():
    steps = list(MIXED_MODE_STEPS)
    steps[1:2] = [('Are you sure', 'n'), ('Enter the Comfort Standard numbers', '1 2'), ('Are you sure', '')]
    script = _Script(steps)

    assert prompts.ask_generation_arguments('vrf_mm', ask=script) == MIXED_MODE_ARGUMENTS
    assert script.steps == []
    assert script.questions[0] != script.questions[2]
