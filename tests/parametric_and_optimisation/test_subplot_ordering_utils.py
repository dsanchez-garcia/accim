import pytest

from accim.parametric_and_optimisation.utils import resolve_subplot_orders


def test_resolve_subplot_orders_custom_accepts_partial_dimensions():
    resolved = resolve_subplot_orders(
        dimension_values={
            'row': ['office', 'residential'],
            'col': ['seville', 'sydney'],
        },
        mode='custom',
        custom={'col': ['sydney', 'seville']},
    )

    assert resolved['col'] == ['sydney', 'seville']
    assert resolved['row'] == ['office', 'residential']


def test_resolve_subplot_orders_custom_invalid_dimension_still_raises():
    with pytest.raises(ValueError, match='includes dimensions not active'):
        resolve_subplot_orders(
            dimension_values={'col': ['seville', 'sydney']},
            mode='custom',
            custom={'row': ['office', 'residential']},
        )

