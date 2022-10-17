import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import UserFilterForm

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

    def get(self, request, *args, **kwargs):
        r"""
        Render user list

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        users = (
            get_user_model()
            .objects.select_related("organization")
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
