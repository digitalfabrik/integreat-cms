from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import models
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from integreat_cms.cms.models import FidoKey

from ...decorators import permission_required
from ...forms import UserFilterForm

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_user"), name="dispatch")
class UserListView(TemplateView):
    """
    View for listing all users (admin users and region users)
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/user_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "users"}

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render user list

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        users = (
            get_user_model()
            .objects.select_related("organization")
            .annotate(
                has_fido_keys=models.Exists(
                    FidoKey.objects.filter(user=models.OuterRef("pk"))
                )
            )
            .prefetch_related("groups__role")
            .order_by("username")
        )

        # Initialize user filter form
        filter_form = UserFilterForm(data=request.GET)

        # Filter users according to given filters, if any
        users = filter_form.apply(users)

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(users, chunk_size)
        chunk = request.GET.get("page")
        user_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "users": user_chunk,
                "filter_form": filter_form,
            },
        )
