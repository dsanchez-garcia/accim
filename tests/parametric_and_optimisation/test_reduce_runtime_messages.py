"""Tests for the messages printed by accim.utils.reduce_runtime and modify_timesteps.

The shading calculation update frequency is given in days, but the number of timesteps per hour
and the maximum figures in shadow overlap calculations have no unit. Before, the messages of
these two settings also said "days".
"""
from types import SimpleNamespace

from accim.utils import modify_timesteps, reduce_runtime


def _fake_idf():
    return SimpleNamespace(idfobjects={
        'Building': [SimpleNamespace(Solar_Distribution='FullExterior')],
        'Runperiod': [SimpleNamespace(Begin_Month=1, Begin_Day_of_Month=1, End_Month=12, End_Day_of_Month=31)],
        'ShadowCalculation': [SimpleNamespace(
            Shading_Calculation_Update_Frequency=20,
            Maximum_Figures_in_Shadow_Overlap_Calculations=15000,
        )],
        'Timestep': [SimpleNamespace(Number_of_Timesteps_per_Hour=6)],
    })


def test_reduce_runtime_messages_give_each_setting_its_own_unit(capsys):
    idf = _fake_idf()

    reduce_runtime(
        idf_object=idf,
        shading_calculation_update_frequency=30,
        maximum_figures_in_shadow_overlap_calculations=200,
        timesteps=2,
        runperiod_end_month=12,
        runperiod_end_day_of_month=31,
    )

    lines = capsys.readouterr().out.splitlines()
    assert ('Shading Calculation Update Frequency was previously set to 20 days, '
            'and it has been modified to 30 days.') in lines
    assert ('Maximum Figures in Shadow Overlap Calculations was previously set to 15000, '
            'and it has been modified to 200.') in lines
    assert 'Number of Timesteps per Hour was previously set to 6, and it has been modified to 2.' in lines
    assert idf.idfobjects['Timestep'][0].Number_of_Timesteps_per_Hour == 2
    assert idf.idfobjects['ShadowCalculation'][0].Maximum_Figures_in_Shadow_Overlap_Calculations == 200


def test_modify_timesteps_message_has_no_unit(capsys):
    idf = _fake_idf()

    modify_timesteps(idf_object=idf, timesteps=4)

    lines = capsys.readouterr().out.splitlines()
    assert lines == ['Number of Timesteps per Hour was previously set to 6, and it has been modified to 4.']
    assert idf.idfobjects['Timestep'][0].Number_of_Timesteps_per_Hour == 4
