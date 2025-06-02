from __future__ import annotations

import pytest

from integreat_cms.cms.constants import months
from integreat_cms.cms.models import Region

REGION_SLUG = "augsburg"

parameters = [
    (months.JANUARY, 50000, None, 50000),
    (months.MAY, 50000, None, 50000),
    (months.JANUARY, 1000000, months.APRIL, 750000),
    (months.FEBRUARY, 1000000, months.MAY, 750000),
    (months.OCTOBER, 1000000, months.JANUARY, 750000),
    (months.NOVEMBER, 1000000, months.FEBRUARY, 750000),
    (months.JANUARY, 1000000, None, 1000000),
    (months.MARCH, 1000000, None, 1000000),
]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", parameters)
def test_region_mt_budget_calc(
    load_test_data: None,
    parameter: tuple[int, int, int, int],
) -> None:
    """
    Test MT budget of a region is being calculated as expected, including mid year start and add-on package
    """
    mt_renewal_month, mt_budget_booked, mt_midyear_start_month, budget = parameter
    region = Region.objects.filter(slug=REGION_SLUG).first()

    region.mt_budget_booked = mt_budget_booked
    region.mt_renewal_month = mt_renewal_month
    region.mt_midyear_start_month = mt_midyear_start_month

    assert region.mt_budget == budget
