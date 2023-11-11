from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.test.client import Client

from ..utils import check_view_status_code
from ..view_config import PARAMETRIZED_VIEWS

if TYPE_CHECKING:
    from typing import Any

    from _pytest.logging import LogCaptureFixture


@pytest.mark.django_db
@pytest.mark.parametrize("view_name,kwargs,post_data,roles", PARAMETRIZED_VIEWS[6::16])
def test_view_status_code_6(
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    view_name: str,
    kwargs: dict[str, Any],
    post_data: dict[str, Any] | str,
    roles: list[str],
) -> None:
    check_view_status_code(login_role_user, caplog, view_name, kwargs, post_data, roles)
