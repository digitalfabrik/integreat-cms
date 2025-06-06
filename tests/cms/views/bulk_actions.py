import html
from typing import TypedDict

from _pytest.logging import LogCaptureFixture
from django.db.models import Model
from django.test.client import Client
from pytest_django.fixtures import SettingsWrapper

from integreat_cms.cms.utils.stringify_list import iter_to_string
from tests.conftest import (
    ANONYMOUS,
    HIGH_PRIV_STAFF_ROLES,
)
from tests.utils import assert_message_in_log


class BulkActionIDs(TypedDict):
    allowed: list[int]
    not_allowed: list[list[int]]


def bulk_delete(
    test_model: type[Model],
    instance_ids: BulkActionIDs,
    url: str,
    role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
    fail_reasons: list[str],
) -> None:
    """
    Helper Function totTest whether bulk deleting of content_type works as expected
    """
    client, role = role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    flat_not_allowed_ids = [
        object_id for sublist in instance_ids["not_allowed"] for object_id in sublist
    ]
    all_selected_ids = instance_ids["allowed"] + flat_not_allowed_ids

    allowed_instances_names = iter_to_string(
        test_model.objects.filter(id__in=instance_ids["allowed"])
    )
    not_allowed_instances_names = iter_to_string(
        test_model.objects.filter(id__in=flat_not_allowed_ids)
    )
    response = client.post(
        url,
        data={"selected_ids[]": all_selected_ids},
    )
    model_name = test_model._meta.verbose_name.title()
    model_name_plural = test_model._meta.verbose_name_plural

    if role in HIGH_PRIV_STAFF_ROLES:
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        redirect_page = client.get(redirect_url).content.decode("utf-8")
        if len(instance_ids["allowed"]) > 1:
            assert (
                html.escape(
                    f"The following {model_name_plural} were successfully deleted: {allowed_instances_names}"
                )
                in redirect_page
            )
            assert_message_in_log(
                f"SUCCESS  The following {model_name_plural} were successfully deleted: {allowed_instances_names}",
                caplog,
            )
        elif len(instance_ids["allowed"]) == 1:
            assert (
                html.escape(
                    f"{model_name} {allowed_instances_names} was successfully deleted."
                )
                in redirect_page
            )
            assert_message_in_log(
                f"SUCCESS  {model_name} {allowed_instances_names} was successfully deleted.",
                caplog,
            )

        if len(flat_not_allowed_ids) > 1:
            assert (
                html.escape(
                    f"The following {model_name_plural} could not be deleted: {not_allowed_instances_names}"
                )
                in redirect_page
            )
            assert_message_in_log(
                f"ERROR    The following {model_name_plural} could not be deleted: {not_allowed_instances_names}",
                caplog,
            )
        elif len(flat_not_allowed_ids) == 1:
            for index, sublist in enumerate(instance_ids["not_allowed"]):
                if flat_not_allowed_ids[0] in sublist:
                    idx = index
            assert (
                html.escape(
                    f"{model_name} {not_allowed_instances_names} cannot be deleted, because {fail_reasons[idx]}"
                )
                in redirect_page
            )
            assert_message_in_log(
                f"ERROR    {model_name} {not_allowed_instances_names} cannot be deleted, because {fail_reasons[idx]}",
                caplog,
            )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert response.headers.get("location") == f"{settings.LOGIN_URL}?next={url}"
    else:
        assert response.status_code == 403
