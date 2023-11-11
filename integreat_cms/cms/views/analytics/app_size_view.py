from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.views.generic import TemplateView

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class AppSizeView(TemplateView):
    """
    View to calculate the current size of the content, that's been send via the API.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "analytics/app_size.html"

    # pylint: disable=fixme
    def get_context_data(self, **kwargs: Any) -> dict:
        r"""
        Extend context by app size

        :param \**kwargs: The supplied keyword arguments
        :return: The context dictionary
        """
        context = super().get_context_data(**kwargs)

        # TODO: Implement correct calculation.
        app_size_total = 0

        context.update({"current_menu_item": "app_size", "app_size": app_size_total})
        return context
