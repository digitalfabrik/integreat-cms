import pytest

from integreat_cms.cms.utils.round_hix_score import round_hix_score

raw_hix_expected_rounding = [
    (14.995187697427333, 15.00),
    (15.002092699342697, 15.00),
    (9.72960372960373, 9.73),
    (12.474861615283503, 12.47),
]


# pylint:disable=redefined-outer-name
@pytest.mark.django_db
@pytest.mark.parametrize("raw_hix_expected_rounding", raw_hix_expected_rounding)
def test_rounded_hix_value(raw_hix_expected_rounding: tuple[float, float]) -> None:
    """
    Test to check HIX scores are rounded correctly
    """

    raw_hix, expected_rounding = raw_hix_expected_rounding

    assert round_hix_score(raw_hix) == expected_rounding
