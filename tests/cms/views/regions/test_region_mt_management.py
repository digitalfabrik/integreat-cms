from __future__ import annotations

import pytest

from integreat_cms.cms.constants import months
from integreat_cms.cms.models import Region

REGION_SLUG = "augsburg"

parameters = [
    (months.JANUARY, False, None, 50000),
    (months.MAY, False, None, 50000),
    (months.JANUARY, True, months.APRIL, 800000),
    (months.FEBRUARY, True, months.MAY, 800000),
    (months.OCTOBER, True, months.JANUARY, 800000),
    (months.NOVEMBER, True, months.FEBRUARY, 800000),
    (months.JANUARY, True, None, 1050000),
    (months.MARCH, True, None, 1050000),
]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", parameters)
def test_region_mt_budget_calc(
    test_data_db_snapshot: None,
    db_snapshot: None,
    parameter: tuple[int, bool, int, int],
) -> None:
    """
    Test MT budget of a region is being calculated as expected, including mid year start and add-on package
    """
    mt_renewal_month, mt_addon_booked, mt_midyear_start_month, budget = parameter
    region = Region.objects.filter(slug=REGION_SLUG).first()

    region.mt_renewal_month = mt_renewal_month
    region.mt_addon_booked = mt_addon_booked
    region.mt_midyear_start_month = mt_midyear_start_month

    assert region.mt_budget == budget
