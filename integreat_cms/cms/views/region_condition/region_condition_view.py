from __future__ import annotations

import logging

from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_region"), name="dispatch")
class RegionConditionView(TemplateView):
    """
    View to analyze the condition of all regions
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "region_condition/region_condition.html"

    extra_context = {"current_menu_item": "region_condition"}
