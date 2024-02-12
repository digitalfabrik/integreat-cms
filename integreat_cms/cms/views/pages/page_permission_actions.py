import json
import logging
from abc import ABC, abstractmethod

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
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to grant page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
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
        permission_message = {
            "message": "An error has occurred. Please contact an administrator.",
            "level_tag": "error",
        }
    if permission_message:
        logger.debug(permission_message["message"])
    return __render_response(request, page, permission_message)


@require_POST
@permission_required("cms.change_page")
@permission_required("cms.grant_page_permissions")
# pylint: disable=unused-argument
def revoke_page_permission_ajax(request: HttpRequest, region_slug: str) -> HttpResponse:
    """
    Remove a page permission for a given user and page

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to revoke page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
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
        permission_message = {
            "message": _("An error has occurred. Please contact an administrator."),
            "level_tag": "error",
        }

    logger.debug(permission_message)

    return __render_response(request, page, permission_message)


class AbstractPagePermission(ABC):
    """
    An abstract class to handle page permissions
    """

    def __init__(self, permission):
        self.permission = permission

    @property
    @abstractmethod
    def grant_success_message(self):
        """
        Success message for granting a permission
        :return: success message
        :rtype: str
        """

    @property
    @abstractmethod
    def revoke_success_message(self):
        """
        Success message for revoking a permission
        :return: success message
        :rtype: str
        """

    @property
    @abstractmethod
    def revoke_with_no_effect_success_message(self):
        """
        Success message for granting a permission without effect
        :return: success message
        :rtype: str
        """

    def grant_permission(self, user, page):
        """
        Grant the permission
        :param user: User the permission is changed for
        :type user: User

        :param page: Page the permission is changed for
        :type page: Page

        :return: Response message
        :rtype: {message: str, level_tag: str}
        """
        if not user.has_perm("cms.view_page"):
            return {
                "message": _(
                    "Page-specific permissions cannot be granted to users "
                    "who do not have permission to view pages (e.g event managers)."
                ),
                "level_tag": "warning",
            }
        message = self.build_grant_message(user, page)
        self.save_grant_permission(user, page)
        return message

    def revoke_permission(self, user, page):
        """
        Revoke the permission
        :param user: User the permission is changed for
        :type user: User

        :param page: Page the permission is changed for
        :type page: Page

        :return: Response message
        :rtype: {message: str, level_tag: str}
        """
        self.save_revoke_permission(user, page)
        return self.build_revoke_message(user, page)

    def build_grant_message(self, user, page):
        """
        Build the success message when granting a permission

        :param user: user that is granted a permission
        :type user: User

        :param page: page the user is granted the permission for
        :type page: Page

        :return: message with level_tag
        :rtype: {message: str, level_tag: str}
        """
        if user.has_perm(self.permission, page):
            message = _(
                'Information: The user "{}" has this permission already.'
            ).format(user.full_user_name)
            level_tag = "info"
        else:
            message = self.grant_success_message.format(user.full_user_name)
            level_tag = "success"
        return {"message": message, "level_tag": level_tag}

    def build_revoke_message(self, user, page):
        """
        Build the response message after revoking
        :param user: User the permission is changed for
        :type user: User

        :param page: Page the permission is changed for
        :type page: Page

        :return: message with level_tag
        :rtype: {message: str, level_tag: str}
        """
        if user.has_perm(self.permission, page):
            message = self.revoke_with_no_effect_success_message.format(
                user.full_user_name
            )
            level_tag = "info"
        else:
            message = self.revoke_success_message.format(user.full_user_name)
            level_tag = "success"
        return {"message": message, "level_tag": level_tag}

    @abstractmethod
    def save_grant_permission(self, user, page):
        """
        Grant the permission and save changes

        :param user: User the permission should be changed for
        :type user: User

        :param page: Page the permission should be changed for
        :type page: Page
        """

    @abstractmethod
    def save_revoke_permission(self, user, page) -> None:
        """
        Revoke the permission and save changes

        :param user: User the permission should be changed for
        :type user: User

        :param page: Page the permission should be changed for
        :type page: Page
        """


class EditPagePermission(AbstractPagePermission):
    """
    Implementation of AbstractPagePermission for editing page permissions
    """

    def __init__(self):
        super().__init__("cms.change_page_object")

    grant_success_message = _('Success: The user "{}" can now edit this page.')
    revoke_success_message = _('Success: The user "{}" cannot edit this page anymore.')
    revoke_with_no_effect_success_message = _(
        'Information: The user "{}" has been removed from the authors of '
        "this page, but has the implicit permission to edit this page anyway."
    )

    def save_grant_permission(self, user, page) -> None:
        page.authors.add(user)
        page.save()

    def save_revoke_permission(self, user, page) -> None:
        if user in page.authors.all():
            page.authors.remove(user)
            page.save()


class PublishPagePermission(AbstractPagePermission):
    """
    Implementation of AbstractPagePermission for publishing page permissions
    """

    def __init__(self):
        super().__init__("cms.publish_page_object")

    grant_success_message = _('Success: The user "{}" can now publish this page.')
    revoke_success_message = _(
        'Success: The user "{}" cannot publish this page anymore.'
    )
    revoke_with_no_effect_success_message = _(
        'Information: The user "{}" has been removed from the editors of '
        "this page, but has the implicit permission to publish this page anyway."
    )

    def save_grant_permission(self, user, page) -> None:
        page.editors.add(user)
        page.save()

    def save_revoke_permission(self, user, page) -> None:
        if user in page.editors.all():
            page.editors.remove(user)
            page.save()


def __render_response(request, page, permission_message):
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
    request: HttpRequest, user: User, permission: AbstractPagePermission, page, grant
) -> None:
    """
    Logging for page permission request
    :param request: Request
    :type request: ~django.http.HttpRequest

    :param user: user that should be granted or revoked a permission
    :type user: User

    :param permission: permission that should be granted or revoked
    :type permission:

    :param page: page for which the permission should be granted or revoked
    :type page:

    :param grant: if the permission is granted or revoked
    :type grant: bool
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
    :type region: Region

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
    :type request: HttpRequest

    :param page: page the permission should be changed for
    :type page: Page

    :param user: user the permission should be changed for
    :type user: User

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


def get_permission(data) -> AbstractPagePermission:
    """
    Gets the Permission object for the requested permission
    :param data: Request data
    :type data: any

    :raises ~django.core.exceptions.PermissionDenied: If unknown page permissions should be changed

    :return: Permission object
    :rtype: AbstractPagePermission
    """
    permission = data.get("permission")
    if permission == "edit":
        return EditPagePermission()
    if permission == "publish":
        return PublishPagePermission()
    logger.warning("Error: The permission %r is not supported", permission)
    raise PermissionDenied
