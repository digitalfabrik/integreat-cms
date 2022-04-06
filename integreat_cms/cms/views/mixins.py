"""
This module contains mixins for our views
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.utils.translation import ugettext as _
from django.urls import reverse


class RegionPermissionRequiredMixing(UserPassesTestMixin):
    """
    A mixin that can be used for class-based views that require that the user is has access to the current region of this request
    """

    def test_func(self):
        """
        The test the user has to pass

        :return: Whether the user has passed the test
        :rtype: bool
        """
        # Superusers and staff have permissions for all regions
        return (
            self.request.user.is_superuser
            or self.request.user.is_staff
            or self.request.region in self.request.user.regions.all()
        )


class ModelTemplateResponseMixin(TemplateResponseMixin):
    """
    A mixin that can be used to render a template of a model (e.g. list or form)
    """

    @property
    def template_name(self):
        """
        Return the template name to be used for the request.

        :return: The template to be rendered
        :rtype: str
        """
        model_name = self.model._meta.model_name
        return f"{model_name}s/{model_name}{self.template_name_suffix}.html"


# pylint: disable=too-few-public-methods
class ModelConfirmationContextMixin(ContextMixin):
    """
    A mixin that can be used to inject confirmation text into a template of a model (e.g. list or form)
    """

    def get_context_data(self, **kwargs):
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this {}"
                ).format(self.model._meta.verbose_name),
                "delete_dialog_text": _("This cannot be reversed."),
            }
        )
        return context


class ContentEditLockMixin(ContextMixin):
    """
    A mixin that provides some variables required for the content edit lock
    """

    #: The reverse name of the url of the associated list view
    back_url_name = None

    def get_context_data(self, **kwargs):
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "back_url": reverse(
                    self.back_url_name,
                    kwargs={
                        "region_slug": kwargs["region_slug"],
                        "language_slug": kwargs["language_slug"],
                    },
                )
            }
        )
        return context
