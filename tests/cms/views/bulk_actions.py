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
    deletable: list[int]
    undeletable: list[list[int]]


def assert_bulk_delete(
    test_model: type[Model],
    instance_ids: BulkActionIDs,
    url: str,
    role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
    fail_reasons: list[str],
) -> None:
    """
    Helper Function to Test whether bulk deleting of content_type works as expected
    """
    client, role = role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    flat_undeletable_ids = [
        object_id for sublist in instance_ids["undeletable"] for object_id in sublist
    ]
    all_selected_ids = instance_ids["deletable"] + flat_undeletable_ids

    deletable_instances_names = iter_to_string(
        test_model.objects.filter(id__in=instance_ids["deletable"])
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
        if len(instance_ids["deletable"]) > 1:
            assert (
                html.escape(
                    f"The following {model_name_plural} were successfully deleted: {deletable_instances_names}"
                )
                in redirect_page
            )
            assert_message_in_log(
                f"SUCCESS  The following {model_name_plural} were successfully deleted: {deletable_instances_names}",
                caplog,
            )
        elif len(instance_ids["deletable"]) == 1:
            assert (
                html.escape(
                    f"{model_name} {deletable_instances_names} was successfully deleted."
                )
                in redirect_page
            )
            assert_message_in_log(
                f"SUCCESS  {model_name} {deletable_instances_names} was successfully deleted.",
                caplog,
            )

        if len(flat_undeletable_ids) > 1:
            for index, sublist in enumerate(instance_ids["undeletable"]):
                undeletable_sub_instances_names = iter_to_string(
                    test_model.objects.filter(id__in=sublist)
                )
                if len(sublist) == 1:
                    assert (
                        html.escape(
                            f"{model_name} {undeletable_sub_instances_names} could not be deleted, because {fail_reasons[index]}"
                        )
                        in redirect_page
                    )
                    assert_message_in_log(
                        f"ERROR    {model_name} {undeletable_sub_instances_names} could not be deleted, because {fail_reasons[index]}",
                        caplog,
                    )
                elif len(sublist) > 1:
                    print(
                        html.escape(
                            f"The following {model_name_plural} could not be deleted: {undeletable_sub_instances_names}, because {fail_reasons[index]}"
                        )
                    )
                    assert (
                        html.escape(
                            f"The following {model_name_plural} could not be deleted: {undeletable_sub_instances_names}, because {fail_reasons[index]}"
                        )
                        in redirect_page
                    )
                    assert_message_in_log(
                        f"ERROR    The following {model_name_plural} could not be deleted: {undeletable_sub_instances_names}, because {fail_reasons[index]}",
                        caplog,
                    )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert response.headers.get("location") == f"{settings.LOGIN_URL}?next={url}"
    else:
        assert response.status_code == 403
