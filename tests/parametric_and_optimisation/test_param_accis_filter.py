"""Tests for drop_invalid_param_combinations, which removes the rows of a full-set plan of the predefined models
that the ACCIS cannot simulate.

Each rule is checked when the plan has its columns. Before, a missing column (or a comfort_standard without valid
categories and comfort modes in the table, such as 99) skipped all the remaining rules of the row, so a plan
without category kept every row, including invalid comfort modes and ventilation_control 1 with hvac_mode 0.
"""
import pandas as pd

from accim.parametric_and_optimisation.funcs_for_besos.param_accis import drop_invalid_param_combinations


def test_each_rule_is_checked_when_the_plan_has_its_columns():
    plan = pd.DataFrame({
        'comfort_standard': [1, 1, 1, 99, 99],
        'comfort_mode': [3, 3, 7, 3, 3],
        'hvac_mode': [2, 0, 2, 2, 0],
        'ventilation_control': [0, 1, 0, 0, 1],
    })

    cleaned = drop_invalid_param_combinations(plan)

    # Without category: row 1 has ventilation_control 1 with hvac_mode 0, row 2 a comfort mode that comfort_standard 1 does not have,
    # and row 4 (comfort_standard 99, not in the table) ventilation_control 1 with hvac_mode 0
    assert list(cleaned.index) == [0, 3]
    assert list(cleaned.columns) == list(plan.columns)


def test_rules_of_the_categories_and_the_offsets():
    plan = pd.DataFrame({
        'comfort_standard': [1, 1, 2, 22, 22, 22],
        'category': [3, 80, 80, 2, 2, 2],
        'comfort_mode': [3, 3, 3, 0, 3, 0],
        'hvac_mode': [2, 2, 2, 2, 2, 0],
        'ventilation_setpoint_offset': [0, 0, 0, 0, 0, 1],
    })

    cleaned = drop_invalid_param_combinations(plan)

    # Row 1: category 80 is not a category of comfort_standard 1; row 4: INT ISO7730 only has comfort_mode 0 (its setpoints do not
    # depend on it); row 5: ventilation_setpoint_offset with hvac_mode 0 (the plan has no ventilation_control)
    assert list(cleaned.index) == [0, 2, 3]


def test_esp_cte_has_no_categories_nor_comfort_modes():
    # As in accim 0.x, the rows of comfort_standard 0 are dropped when the plan has category or comfort_mode (its setpoints do not
    # depend on them), so a plan with comfort_standard 0 must not have these columns
    with_cat = pd.DataFrame({'comfort_standard': [0, 0, 1], 'category': [1, 2, 1]})
    without_cat = pd.DataFrame({'comfort_standard': [0, 1], 'hvac_mode': [2, 2]})

    assert list(drop_invalid_param_combinations(with_cat).index) == [2]
    assert list(drop_invalid_param_combinations(without_cat).index) == [0, 1]
