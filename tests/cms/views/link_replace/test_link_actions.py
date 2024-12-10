from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.test.client import Client
from django.urls import reverse
from linkcheck import listeners
from linkcheck.listeners import enable_listeners
from linkcheck.models import Link, Url

from integreat_cms.cms.models import Region
from integreat_cms.cms.utils.linkcheck_utils import filter_urls
from tests.conftest import ANONYMOUS, EDITOR, MANAGEMENT, STAFF_ROLES
from tests.utils import assert_message_in_log

# ----------- Test for url replace -----------#
# Url to be replaced
# This URL is used once in region Nürnberg and three times in Augsburg
# If bulk action is conducted in the network management, all of them must be affected,
# while only three of them if done in the broken link list of Augsburg
OLD_URL = "https://integreat.app/augsburg/de/willkommen/"
# Url to replace with
NEW_URL = "https://integreat.app/augsburg/de/this-is-new-url/"
# Parameters for test
# (
# <network management or region>,
# <number of links with url=OLD_URL before successful search&replace>,
# <number of links with url=OLD_URL after successful search&replace>
# )
url_replace_parameters = [("network_management", 4, 0), ("augsburg", 4, 1)]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", url_replace_parameters)
def test_url_replace(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: tuple[str, int, int],
) -> None:
    """
    Test whether link replacement in the network management per pencil icon in the column "options" work correctly.
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user
    region, before, after = parameter

    url_object = Url.objects.filter(url=OLD_URL).first()

    assert Link.objects.filter(url=url_object).count() == before
    assert not Link.objects.filter(url__url=NEW_URL).exists()

    kwargs = {
        "url_filter": "valid",
        "url_id": url_object.id,
    }
    if not region == "network_management":
        kwargs.update(
            {
                "region_slug": region,
            }
        )

    action_url = reverse(
        "edit_url",
        kwargs=kwargs,
    )
    with enable_listeners():
        response = client.post(
            action_url,
            data={
                "url": NEW_URL,
            },
        )

    entitled_roles = (
        STAFF_ROLES
        if region == "network_management"
        else STAFF_ROLES + [MANAGEMENT, EDITOR]
    )

    if role in entitled_roles:
        assert response.status_code == 302

        assert_message_in_log(
            "SUCCESS  URL was successfully replaced",
            caplog,
        )

        assert Link.objects.filter(url__url=OLD_URL).count() == after
        # assert Link.objects.filter(url__url=NEW_URL).count() == before - after

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={action_url}"
        )
        assert Link.objects.filter(url__url=OLD_URL).count() == before
        assert not Link.objects.filter(url__url=NEW_URL).exists()
    else:
        assert response.status_code == 403
        assert Link.objects.filter(url__url=OLD_URL).count() == before
        assert not Link.objects.filter(url__url=NEW_URL).exists()


# ----------- Test for search&replace -----------#
# string to be replaced
SEARCH = "/augsburg/de/willkommen/"
# string that appear after search&replace
REPLACE = "/i/am/replaced/"
# This URL is used once in region Nürnberg and three times in Augsburg
# If bulk action is conducted in the network management, all of them must be affected,
# while only three of them if done in the broken link list of Augsburg
SEARCH_REPLACE_TARGET_URL = "https://integreat.app/augsburg/de/willkommen/"
TARGET_URL_AFTER_REPLACE = "https://integreat.app/i/am/replaced/"
# Parameters for test
# (
# <network management or region>,
# <number of links with url=SEARCH_REPLACE_TARGET_URL before successful search&replace>,
# <number of links with url=SEARCH_REPLACE_TARGET_URL which must stay unchanged after successful search&replace>
# )
search_replace_parameters = [("network_management", 4, 0), ("augsburg", 4, 1)]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", search_replace_parameters)
def test_search_and_replace_links(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: tuple[str, int, int],
) -> None:
    """
    Test whether search & replace (on the upper right corner) is working correctly.
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user
    region, before, after = parameter

    target_url_object = Url.objects.filter(url=SEARCH_REPLACE_TARGET_URL).first()
    assert target_url_object

    assert Link.objects.filter(url=target_url_object).count() == before

    kwargs = {}
    if not region == "network_management":
        kwargs.update(
            {
                "region_slug": region,
            }
        )

    action_url = reverse(
        "search_and_replace_link",
        kwargs=kwargs,
    )

    with enable_listeners():
        response = client.post(
            action_url,
            data={
                "search": SEARCH,
                "replace": REPLACE,
                "link_types": ["internal"],
            },
        )

    entitled_roles = (
        STAFF_ROLES
        if region == "network_management"
        else STAFF_ROLES + [MANAGEMENT, EDITOR]
    )

    if role in entitled_roles:
        assert response.status_code == 302

        assert_message_in_log(
            "SUCCESS  Links were replaced successfully.",
            caplog,
        )

        assert Link.objects.filter(url__url=SEARCH_REPLACE_TARGET_URL).count() == after
        # assert (
        #    Link.objects.filter(url__url=TARGET_URL_AFTER_REPLACE).count()
        #    == before - after
        # )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={action_url}"
        )
        assert Link.objects.filter(url__url=SEARCH_REPLACE_TARGET_URL).count() == before
        assert Link.objects.filter(url__url=TARGET_URL_AFTER_REPLACE).count() == 0

    else:
        assert response.status_code == 403
        assert Link.objects.filter(url__url=SEARCH_REPLACE_TARGET_URL).count() == before
        assert Link.objects.filter(url__url=TARGET_URL_AFTER_REPLACE).count() == 0


# ----------- Test for bulk action ignore/unignore -----------#
# Url to use for test
# This URL is used once in region Nürnberg and three times in Augsburg.
# If bulk action is conducted in the network management, all of them must be affected,
# while only three of them if done in the broken link list of Augsburg
IGNORE_UNIGNORE_TARGET_URL = "https://integreat.app/augsburg/de/willkommen/"

# Parameters for test
# (
# <action>,
# <network management or region>,
# (<number of links with ignore=True before successful action>, <number of links with ignore=False before successful action>),
# (<number of links with ignore=True after successful action>, <number of links with ignore=False> after successful action)
# )
ignore_unignore_parameters = [
    ("ignore", "network_management", (0, 4), (4, 0)),
    ("ignore", "augsburg", (0, 4), (3, 1)),
    ("unignore", "network_management", (4, 0), (0, 4)),
    ("unignore", "augsburg", (4, 0), (1, 3)),
]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", ignore_unignore_parameters)
def test_bulk_ignore_unignore_links(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: tuple[str, str, tuple[int, int], tuple[int, int]],
) -> None:
    """
    Test whether bulk action ignore/unignore is working correctly.
    """
    settings.LANGUAGE_CODE = "en"

    client, role = login_role_user

    action, region, before, after = parameter

    target_url_object = Url.objects.filter(url=IGNORE_UNIGNORE_TARGET_URL).first()
    assert target_url_object

    target_links = Link.objects.filter(url__url=target_url_object)

    # Flip the value when testing "unignore" action and test it in the same way with "ignore" action
    if action == "unignore":
        target_links.update(ignore=True)

    assert target_links.filter(ignore=True).count() == before[0]
    assert target_links.filter(ignore=False).count() == before[1]

    kwargs = {"url_filter": "valid"}
    if not region == "network_management":
        kwargs.update(
            {
                "region_slug": region,
            }
        )

    action_url = reverse(
        "linkcheck",
        kwargs=kwargs,
    )
    response = client.post(
        action_url,
        data={
            "selected_ids[]": [target_url_object.id],
            "action": action,
        },
    )

    entitled_roles = (
        STAFF_ROLES
        if region == "network_management"
        else STAFF_ROLES + [MANAGEMENT, EDITOR]
    )

    if role in entitled_roles:
        assert response.status_code == 302
        if action == "ignore":
            assert_message_in_log(
                "SUCCESS  Links were successfully marked as verified",
                caplog,
            )
        else:
            assert_message_in_log(
                "SUCCESS  Verification was revoked for the links",
                caplog,
            )
        assert target_links.filter(ignore=True).count() == after[0]
        assert target_links.filter(ignore=False).count() == after[1]

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={action_url}"
        )
        assert target_links.filter(ignore=True).count() == before[0]
        assert target_links.filter(ignore=False).count() == before[1]
    else:
        assert response.status_code == 403
        assert target_links.filter(ignore=True).count() == before[0]
        assert target_links.filter(ignore=False).count() == before[1]


# ----------- Test for bulk recheck -----------#
# Url to use for test
# This URL is "unchecked" and used once in region Nürnberg and once in Augsburg.
RECHECK_TARGET_URL = "https://integreat.app"

# Parameters for test
# <network management or region>
recheck_parameters = ["network_management", "augsburg"]

# As there is only one single ULR object for each URL and they are global (not region bounded),
# bulk recheck affects all the links with the selected URLs, regardless of which region they belong to.


@pytest.mark.django_db
@pytest.mark.parametrize("region", recheck_parameters)
def test_bulk_recheck_links(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    region: str,
) -> None:
    """
    Test whether bulk action recheck is working correctly.
    """
    settings.LANGUAGE_CODE = "en"

    client, role = login_role_user

    target_url_object = Url.objects.filter(url=RECHECK_TARGET_URL).first()
    assert target_url_object

    region_slug = region if not region == "network_management" else None
    unchecked_url, _ = filter_urls(region_slug, "unchecked")
    assert len(unchecked_url) == 1

    kwargs = {"url_filter": "unchecked"}
    if not region == "network_management":
        kwargs.update(
            {
                "region_slug": region,
            }
        )

    action_url = reverse(
        "linkcheck",
        kwargs=kwargs,
    )
    response = client.post(
        action_url,
        data={
            "selected_ids[]": [target_url_object.id],
            "action": "recheck",
        },
    )

    entitled_roles = (
        STAFF_ROLES
        if region == "network_management"
        else STAFF_ROLES + [MANAGEMENT, EDITOR]
    )
    unchecked_url, _ = filter_urls(region_slug, "unchecked")

    if role in entitled_roles:
        assert response.status_code == 302
        assert_message_in_log(
            "SUCCESS  Links were successfully checked",
            caplog,
        )
        assert len(unchecked_url) == 0

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={action_url}"
        )
        assert len(unchecked_url) == 1

    else:
        assert response.status_code == 403
        assert len(unchecked_url) == 1
