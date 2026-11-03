"""Tests for drop_invalid_param_combinations, which removes the rows of a full-set plan of the predefined models
that the ACCIS cannot simulate, or that would repeat a simulation.

Each rule is checked when the plan has its columns. Before, a missing column (or a comfort_standard without valid
categories and comfort modes in the table, such as 99) skipped all the remaining rules of the row, so a plan
without category kept every row, including invalid comfort modes and ventilation_control 1 with hvac_mode 0.
"""
import pandas as pd

from accim.parametric_and_optimisation.funcs_for_besos.param_accis import drop_invalid_param_combinations
from accim.parametric_and_optimisation.utils import make_all_combinations


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

    # Row 1: category 80 is not a category of comfort_standard 1; rows 3 and 5: INT ISO7730 keeps only the first comfort
    # mode of the plan (3), since its setpoints do not depend on it; row 5 also has ventilation_setpoint_offset with
    # hvac_mode 0 (the plan has no ventilation_control)
    assert list(cleaned.index) == [0, 2, 4]


def test_esp_cte_and_int_iso7730_keep_one_row_for_each_combination_of_the_other_parameters():
    # The setpoints of ESP CTE depend neither on the category nor on the comfort mode, and those of INT ISO7730 not on
    # the comfort mode: their rows keep the first value of these parameters in the plan. Before, the rows of ESP CTE
    # were dropped when the plan had category or comfort_mode, and those of INT ISO7730 kept only comfort_mode 0
    plan = make_all_combinations({'comfort_standard': [1, 0, 22], 'category': [2, 1, 3], 'comfort_mode': [3, 0],
                                  'hvac_mode': [0, 2]})

    cleaned = drop_invalid_param_combinations(plan)

    by_standard = {standard: rows for standard, rows in cleaned.groupby('comfort_standard')}
    assert len(by_standard[1]) == 3 * 2 * 2
    assert by_standard[0][['category', 'comfort_mode', 'hvac_mode']].values.tolist() == [[2, 3, 0], [2, 3, 2]]
    assert sorted(by_standard[22][['category', 'hvac_mode']].values.tolist()) == [[1, 0], [1, 2], [2, 0], [2, 2],
                                                                                  [3, 0], [3, 2]]
    assert set(by_standard[22]['comfort_mode']) == {3}


def test_esp_cte_without_category_or_comfort_mode_in_the_plan():
    with_cat = pd.DataFrame({'comfort_standard': [0, 0, 1], 'category': [1, 2, 1]})
    without_cat = pd.DataFrame({'comfort_standard': [0, 1], 'hvac_mode': [2, 2]})

    assert list(drop_invalid_param_combinations(with_cat).index) == [0, 2]
    assert list(drop_invalid_param_combinations(without_cat).index) == [0, 1]
