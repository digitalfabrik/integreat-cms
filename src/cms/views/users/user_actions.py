from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from ...decorators import staff_required


@staff_required
@login_required
@permission_required("cms.manage_admin_users", raise_exception=True)
def delete_user(request, user_id):

    get_user_model().objects.get(id=user_id).delete()

    messages.success(request, _("User was successfully deleted"))

    return redirect("users")
