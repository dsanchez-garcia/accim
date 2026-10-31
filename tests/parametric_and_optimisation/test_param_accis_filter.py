"""Tests for drop_invalid_param_combinations, which removes the rows of a full-set plan of the predefined models
that the ACCIS cannot simulate.

Each rule is checked when the plan has its columns. Before, a missing column (or a ComfStand without valid
categories and comfort modes in the table, such as 99) skipped all the remaining rules of the row, so a plan
without CAT kept every row, including invalid comfort modes and VentCtrl 1 with HVACmode 0.
"""
import pandas as pd

from accim.parametric_and_optimisation.funcs_for_besos.param_accis import drop_invalid_param_combinations


def test_each_rule_is_checked_when_the_plan_has_its_columns():
    plan = pd.DataFrame({
        'ComfStand': [1, 1, 1, 99, 99],
        'ComfMod': [3, 3, 7, 3, 3],
        'HVACmode': [2, 0, 2, 2, 0],
        'VentCtrl': [0, 1, 0, 0, 1],
    })

    cleaned = drop_invalid_param_combinations(plan)

    # Without CAT: row 1 has VentCtrl 1 with HVACmode 0, row 2 a comfort mode that ComfStand 1 does not have,
    # and row 4 (ComfStand 99, not in the table) VentCtrl 1 with HVACmode 0
    assert list(cleaned.index) == [0, 3]
    assert list(cleaned.columns) == list(plan.columns)


def test_rules_of_the_categories_and_the_offsets():
    plan = pd.DataFrame({
        'ComfStand': [1, 1, 2, 22, 22, 22],
        'CAT': [3, 80, 80, 2, 2, 2],
        'ComfMod': [3, 3, 3, 0, 3, 0],
        'HVACmode': [2, 2, 2, 2, 2, 0],
        'VSToffset': [0, 0, 0, 0, 0, 1],
    })

    cleaned = drop_invalid_param_combinations(plan)

    # Row 1: CAT 80 is not a category of ComfStand 1; row 4: INT ISO7730 only has ComfMod 0 (its setpoints do not
    # depend on it); row 5: VSToffset with HVACmode 0 (the plan has no VentCtrl)
    assert list(cleaned.index) == [0, 2, 3]


def test_esp_cte_has_no_categories_nor_comfort_modes():
    # As in accim 0.x, the rows of ComfStand 0 are dropped when the plan has CAT or ComfMod (its setpoints do not
    # depend on them), so a plan with ComfStand 0 must not have these columns
    with_cat = pd.DataFrame({'ComfStand': [0, 0, 1], 'CAT': [1, 2, 1]})
    without_cat = pd.DataFrame({'ComfStand': [0, 1], 'HVACmode': [2, 2]})

    assert list(drop_invalid_param_combinations(with_cat).index) == [2]
    assert list(drop_invalid_param_combinations(without_cat).index) == [0, 1]
