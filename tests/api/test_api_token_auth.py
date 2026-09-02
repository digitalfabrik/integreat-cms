from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test.client import RequestFactory

from integreat_cms.api.decorators import api_token_required
from integreat_cms.cms.models import ApiToken

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest


@api_token_required()
def _protected_view(request: HttpRequest, *_args: Any, **_kwargs: Any) -> JsonResponse:
    """
    A minimal view used to exercise the authentication decorator.

    :param request: The current request
    :return: The username of the authenticated user
    """
    return JsonResponse({"user": request.user.username})


@api_token_required("cms.change_region")
def _permission_protected_view(
    _request: HttpRequest,
    *_args: Any,
    **_kwargs: Any,
) -> JsonResponse:
    """
    A minimal view which additionally requires a permission.

    :return: A static success response
    """
    return JsonResponse({"status": "ok"})


@pytest.mark.django_db
def test_api_token_required_accepts_valid_token(load_test_data: None) -> None:
    """
    A valid bearer token authenticates the request and updates the last usage.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    user = get_user_model().objects.get(username="root")
    token, plaintext = ApiToken.create_token(user, "CRM")
    assert token.last_usage is None

    request = RequestFactory().get(
        "/",
        headers={"authorization": f"Bearer {plaintext}"},
    )
    response = _protected_view(request)

    assert response.status_code == 200
    assert json.loads(response.content) == {"user": "root"}
    token.refresh_from_db()
    assert token.last_usage is not None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "header",
    [
        None,
        "",
        "Bearer",
        "Bearer ",
        "Bearer invalid.token",
        "Basic some-token",
    ],
)
def test_api_token_required_rejects_invalid_tokens(
    load_test_data: None,
    header: str | None,
) -> None:
    """
    Missing, malformed and unknown tokens are rejected with 403.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param header: The value of the ``Authorization`` header
    """
    headers = {} if header is None else {"authorization": header}
    request = RequestFactory().get("/", headers=headers)
    response = _protected_view(request)

    assert response.status_code == 403


@pytest.mark.django_db
def test_api_token_required_rejects_inactive_user(load_test_data: None) -> None:
    """
    A token of a deactivated user must not authenticate anymore.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    user = get_user_model().objects.get(username="root")
    _token, plaintext = ApiToken.create_token(user, "CRM")
    user.is_active = False
    user.save()

    request = RequestFactory().get(
        "/",
        headers={"authorization": f"Bearer {plaintext}"},
    )
    response = _protected_view(request)

    assert response.status_code == 403


@pytest.mark.django_db
def test_api_token_required_enforces_permission(load_test_data: None) -> None:
    """
    A token only grants the permissions of its user, so a user without the required permission
    is rejected while a privileged user passes.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    unprivileged = get_user_model().objects.filter(is_superuser=False).first()
    _token, unprivileged_plaintext = ApiToken.create_token(unprivileged, "CRM")
    request = RequestFactory().get(
        "/",
        headers={"authorization": f"Bearer {unprivileged_plaintext}"},
    )
    assert _permission_protected_view(request).status_code == 403

    root = get_user_model().objects.get(username="root")
    _root_token, root_plaintext = ApiToken.create_token(root, "CRM")
    request = RequestFactory().get(
        "/",
        headers={"authorization": f"Bearer {root_plaintext}"},
    )
    assert _permission_protected_view(request).status_code == 200
