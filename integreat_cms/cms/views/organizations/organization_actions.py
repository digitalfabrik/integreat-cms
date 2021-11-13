import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect

from ...decorators import permission_required
from ...models import Organization

logger = logging.getLogger(__name__)


@require_POST
@login_required
@permission_required("cms.delete_organization")
def delete(request, organization_id):
    """
    Deletes a single organization and updates all corresponding pages and users

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param organization_id: Internal id of the organization to be deleted
    :type organization_id: int

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    organization = get_object_or_404(Organization, id=organization_id)
    organization.delete()

    logger.info("%r deleted by %r", organization, request.user)

    messages.success(request, _("Organization was succesfully deleted"))
    return redirect("organizations")
