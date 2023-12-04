from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.test.client import Client
from django.urls import reverse

from ...utils import assert_no_error_messages
from .view_config import PARAMETRIZED_PUBLIC_VIEWS

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture

    from .view_config import PostData, ViewNameStr


@pytest.mark.django_db
@pytest.mark.parametrize("view_name,post_data", PARAMETRIZED_PUBLIC_VIEWS)
def test_public_view_status_code(
    load_test_data: None,
    caplog: LogCaptureFixture,
    view_name: ViewNameStr,
    post_data: PostData,
) -> None:
    """
    This test checks whether the given view return the correct status code for anonymous users

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param caplog: The :fixture:`caplog` fixture
    :param view_name: The identifier of the view
    :param post_data: The post data for this view
    """
    client = Client()
    url = reverse(view_name)
    response = client.post(url, data=post_data) if post_data else client.get(url)
    print(response.headers)
    assert_no_error_messages(caplog)
    if post_data:
        # Post-views should redirect after a successful operation
        assert response.status_code == 302
    else:
        # Get-views should return 200
        assert response.status_code == 200
