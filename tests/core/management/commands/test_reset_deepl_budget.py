from datetime import datetime
from unittest.mock import patch

import pytest
from django.core.management.base import CommandError

from integreat_cms.cms.models import Region

from ..utils import get_command_output


# pylint: disable=too-few-public-methods
class datetime_not_first_day:
    """
    Fake datetime object where now() is never the first day of the month
    """

    @classmethod
    def now(cls):
        """
        generate a date with day=2

        :returns: a date which is never the 1st day of the month
        :rtype: datetime.datetime
        """
        real_now = datetime.now()
        return real_now.replace(day=2)


@patch("datetime.datetime", datetime_not_first_day)
def test_not_first_day():
    """
    Ensure that the command will not run when it's not the 1st day of the month without --force
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("reset_deepl_budget"))
        assert (
            str(exc_info.value)
            == "It is not the 1st day of the month. If you want to reset DeepL budget despite that, run the command with --force"
        )


# pylint: disable=unused-argument
@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_reset_deepl_budget(load_test_data_transactional):
    """
    Ensure that DeepL budget gets reset successfully
    """

    current_month = datetime.now().month - 1

    region1 = Region.objects.create(
        slug="deepl_test_1",
        deepl_renewal_month=current_month,
        deepl_midyear_start_month=current_month + 1,
        deepl_budget_used=42,
    )
    region2 = Region.objects.create(
        slug="deepl_test_2",
        deepl_renewal_month=current_month + 1,
        deepl_midyear_start_month=current_month + 1,
        deepl_budget_used=42,
    )

    out, err = get_command_output("reset_deepl_budget", "--force")
    region1.refresh_from_db()
    region2.refresh_from_db()
    assert "✔ DeepL budget has been reset." in out
    assert not err
    assert (
        not region1.deepl_budget_used
    ), "The DeepL budget of region 1 should have been reset to 0."
    assert (
        region2.deepl_budget_used == 42
    ), "The DeepL budget of region 2 should remain unchanged."
    assert (
        region1.deepl_midyear_start_month is None
    ), "The midyear start month of region 1 should have been reset to None."
    assert (
        region2.deepl_midyear_start_month == current_month + 1
    ), "The midyear start month of region 2 should not have been reset to None."
