import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from ...decorators import permission_required
from ...forms import PageForm
from ...models import Page, Region, User

logger = logging.getLogger(__name__)


@require_POST
@permission_required("cms.change_page")
@permission_required("cms.grant_page_permissions")
# pylint: disable=unused-argument
def grant_page_permission_ajax(request: HttpRequest, region_slug: str) -> HttpResponse:
    """
    Grant a user editing or publishing permissions on a specific page object

    :param request: The current request
    :param region_slug: The slug of the current region

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to grant page permissions

    :return: The rendered page permission table
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = get_permission(data)
        page = Page.objects.get(id=data.get("page_id"))
        user = get_user_model().objects.get(id=data.get("user_id"))

        log_permission_request(request, user, permission, page, grant=True)

        ensure_page_specific_permissions_enabled(page.region)
        ensure_user_has_correct_permissions(request, page, user)

        permission_message = permission.grant_permission(user, page)
    except PermissionDenied as e:
        logger.exception(e)
        permission_message = PermissionMessage(
            "An error has occurred. Please contact an administrator.",
            MessageLevel.ERROR,
        )
    if permission_message:
        logger.debug(permission_message.message)
    return __render_response(request, page, permission_message)


@require_POST
@permission_required("cms.change_page")
@permission_required("cms.grant_page_permissions")
# pylint: disable=unused-argument
def revoke_page_permission_ajax(request: HttpRequest, region_slug: str) -> HttpResponse:
    """
    Remove a page permission for a given user and page

    :param request: The current request
    :param region_slug: The slug of the current region

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to revoke page permissions

    :return: The rendered page permission table
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = get_permission(data)
        page = Page.objects.get(id=data.get("page_id"))
        user = get_user_model().objects.get(id=data.get("user_id"))

        log_permission_request(request, user, permission, page, grant=False)

        ensure_page_specific_permissions_enabled(page.region)
        ensure_user_has_correct_permissions(request, page, user)

        permission_message = permission.revoke_permission(user, page)
    except PermissionDenied as e:
        logger.exception(e)
        permission_message = PermissionMessage(
            _("An error has occurred. Please contact an administrator."),
            MessageLevel.ERROR,
        )
    logger.debug(permission_message)

    return __render_response(request, page, permission_message)


class MessageLevel(StrEnum):
    """
    Enum for different level tags of a message
    """

    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class PermissionMessage:
    """
    Saves message and level_tag of the return message
    """

    def __init__(
        self,
        message: str,
        level_tag: MessageLevel,
    ):
        self.message = message
        self.level_tag = level_tag


class AbstractPagePermission(ABC):
    """
    An abstract class to handle page permissions
    """

    def __init__(self, permission: str):
        self.permission = permission

    @property
    @abstractmethod
    def grant_success_message(self) -> str:
        """
        Success message for granting a permission

        :return: success message
        """

    @property
    @abstractmethod
    def revoke_success_message(self) -> str:
        """
        Success message for revoking a permission

        :return: success message
        """

    @property
    @abstractmethod
    def revoke_with_no_effect_success_message(self) -> str:
        """
        Success message for granting a permission without effect

        :return: success message
        """

    def grant_permission(self, user: User, page: Page) -> PermissionMessage:
        """
        Grant the permission

        :param user: User the permission is changed for
        :param page: Page the permission is changed for

        :return: Response message
        """
        if not user.has_perm("cms.view_page"):
            return PermissionMessage(
                _(
                    "Page-specific permissions cannot be granted to users "
                    "who do not have permission to view pages (e.g event managers)."
                ),
                MessageLevel.WARNING,
            )

        message = self.build_grant_message(user, page)
        self.save_grant_permission(user, page)
        return message

    def revoke_permission(self, user: User, page: Page) -> PermissionMessage:
        """
        Revoke the permission

        :param user: User the permission is changed for
        :param page: Page the permission is changed for

        :return: Response message
        """
        self.save_revoke_permission(user, page)
        return self.build_revoke_message(user, page)

    def build_grant_message(self, user: User, page: Page) -> PermissionMessage:
        """
        Build the success message when granting a permission

        :param user: user that is granted a permission
        :param page: page the user is granted the permission for

        :return: message with level_tag
        """
        if user.has_perm(self.permission, page):
            message = _(
                'Information: The user "{}" has this permission already.'
            ).format(user.full_user_name)
            level_tag = MessageLevel.INFO
        else:
            message = self.grant_success_message.format(user.full_user_name)
            level_tag = MessageLevel.SUCCESS
        return PermissionMessage(message, level_tag)

    def build_revoke_message(self, user: User, page: Page) -> PermissionMessage:
        """
        Build the response message after revoking

        :param user: User the permission is changed for
        :param page: Page the permission is changed for

        :return: permission message
        """
        if user.has_perm(self.permission, page):
            message = self.revoke_with_no_effect_success_message.format(
                user.full_user_name
            )
            level_tag = MessageLevel.INFO
        else:
            message = self.revoke_success_message.format(user.full_user_name)
            level_tag = MessageLevel.SUCCESS
        return PermissionMessage(message, level_tag)

    @abstractmethod
    def save_grant_permission(self, user: User, page: Page) -> None:
        """
        Grant the permission and save changes

        :param user: User the permission should be changed for
        :param page: Page the permission should be changed for
        """

    @abstractmethod
    def save_revoke_permission(self, user: User, page: Page) -> None:
        """
        Revoke the permission and save changes

        :param user: User the permission should be changed for
        :param page: Page the permission should be changed for
        """


class EditPagePermission(AbstractPagePermission):
    """
    Implementation of AbstractPagePermission for editing page permissions
    """

    def __init__(self) -> None:
        super().__init__("cms.change_page_object")

    grant_success_message = _('Success: The user "{}" can now edit this page.')
    revoke_success_message = _('Success: The user "{}" cannot edit this page anymore.')
    revoke_with_no_effect_success_message = _(
        'Information: The user "{}" has been removed from the authors of '
        "this page, but has the implicit permission to edit this page anyway."
    )

    def save_grant_permission(self, user: User, page: Page) -> None:
        page.authors.add(user)
        page.save()

    def save_revoke_permission(self, user: User, page: Page) -> None:
        if user in page.authors.all():
            page.authors.remove(user)
            page.save()


class PublishPagePermission(AbstractPagePermission):
    """
    Implementation of AbstractPagePermission for publishing page permissions
    """

    def __init__(self) -> None:
        super().__init__("cms.publish_page_object")

    grant_success_message = _('Success: The user "{}" can now publish this page.')
    revoke_success_message = _(
        'Success: The user "{}" cannot publish this page anymore.'
    )
    revoke_with_no_effect_success_message = _(
        'Information: The user "{}" has been removed from the editors of '
        "this page, but has the implicit permission to publish this page anyway."
    )

    def save_grant_permission(self, user: User, page: Page) -> None:
        page.editors.add(user)
        page.save()

    def save_revoke_permission(self, user: User, page: Page) -> None:
        if user in page.editors.all():
            page.editors.remove(user)
            page.save()


def __render_response(
    request: HttpRequest, page: Page, permission_message: PermissionMessage
) -> HttpResponse:
    return render(
        request,
        "pages/_page_permission_table.html",
        {
            "page": page,
            "page_form": PageForm(
                instance=page,
                additional_instance_attributes={
                    "region": page.region,
                },
            ),
            "permission_message": permission_message,
        },
    )


def log_permission_request(
    request: HttpRequest,
    user: User,
    permission: AbstractPagePermission,
    page: Page,
    grant: bool,
) -> None:
    """
    Logging for page permission request

    :param request: Request
    :param user: user that should be granted or revoked a permission
    :param permission: permission that should be granted or revoked
    :param page: page for which the permission should be granted or revoked
    :param grant: if the permission is granted or revoked
    """
    logger.debug(
        "[AJAX] %r wants to %r %r the permission to %s %r",
        request.user,
        "grant" if grant else "revoke",
        user,
        permission,
        page,
    )


def ensure_page_specific_permissions_enabled(region: Region) -> None:
    """
    Ensure the page permission is enabled

    :param region: The region the page permission should be enabled for

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region
    """
    if not region.page_permissions_enabled:
        raise PermissionDenied(f"Page permissions are not activated for {region!r}")


def ensure_user_has_correct_permissions(
    request: HttpRequest, page: Page, user: User
) -> None:
    """
    Ensure the user has correct permissions

    :param request: request
    :param page: page the permission should be changed for
    :param user: user the permission should be changed for

    :raises ~django.core.exceptions.PermissionDenied: If the user does not have the permission to grant page permissions
    """
    if not (request.user.is_superuser or request.user.is_staff):
        if page.region not in request.user.regions.all():
            logger.warning(
                "Error: %r cannot grant permissions for %r",
                request.user,
                page.region,
            )
            raise PermissionDenied
        if page.region not in user.regions.all():
            logger.warning(
                "Error: %r cannot receive permissions for %r",
                user,
                page.region,
            )
            raise PermissionDenied


def get_permission(data: Any) -> AbstractPagePermission:
    """
    Gets the Permission object for the requested permission

    :param data: Request data

    :raises ~django.core.exceptions.PermissionDenied: If unknown page permissions should be changed

    :return: Permission object
    """
    permission = data.get("permission")
    if permission == "edit":
        return EditPagePermission()
    if permission == "publish":
        return PublishPagePermission()
    logger.warning("Error: The permission %r is not supported", permission)
    raise PermissionDenied
