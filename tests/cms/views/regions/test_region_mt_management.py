from __future__ import annotations

import pytest

from integreat_cms.cms.models import Region

REGION_SLUG = "augsburg"

#: Tuples of booked budget, cumulative adjustment and the resulting total budget
parameters = [
    (50000, 0, 50000),
    (1000000, 0, 1000000),
    # A positive adjustment tops the booked budget up
    (1000000, 250000, 1250000),
    (50000, 1, 50001),
    # A negative adjustment reduces it
    (1000000, -250000, 750000),
    # The budget never becomes negative, even if more is subtracted than booked
    (50000, -50000, 0),
    (50000, -1000000, 0),
]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", parameters)
def test_region_mt_budget_calc(
    load_test_data: None,
    parameter: tuple[int, int, int],
) -> None:
    """
    Test that the MT budget is the booked budget plus the cumulative adjustment

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param parameter: The booked budget, the adjustment and the expected total budget
    """
    mt_budget_booked, mt_budget_adjustment, budget = parameter
    region = Region.objects.filter(slug=REGION_SLUG).first()

    region.mt_budget_booked = mt_budget_booked
    region.mt_budget_adjustment = mt_budget_adjustment

    assert region.mt_budget == budget
