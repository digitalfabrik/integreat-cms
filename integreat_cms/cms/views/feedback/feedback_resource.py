from typing import Any

from django.utils.translation import gettext_lazy as _
from import_export import fields, resources
from import_export.widgets import DateWidget

from ...models import Feedback


# pylint: disable=too-few-public-methods
class FeedbackResource(resources.ModelResource):
    """
    This is the Resource class that connects to the django-import-export library
    """

    category = fields.Field(
        column_name=_("Category"),
        attribute="category",
    )

    referring_to = fields.Field(
        column_name=_("Feedback on"),
        attribute="object_name",
    )

    language_name = fields.Field(
        column_name=_("Language"),
        attribute="language__translated_name",
    )

    rating = fields.Field(column_name=_("Rating"), attribute="get_rating_display")

    read_by_username = fields.Field(
        column_name=_("Read by"), attribute="read_by__full_user_name"
    )

    comment = fields.Field(column_name=_("Comment"), attribute="comment")

    created_date = fields.Field(
        column_name=_("Date"),
        attribute="created_date",
        widget=DateWidget(format="%d.%m.%Y %H:%M"),
    )

    # pylint: disable=useless-parent-delegation
    def get_instance(self, *args: Any, **kwargs: Any) -> Any:
        """
        See :meth:`import_export.resources.Resource.get_instance`
        """
        return super().get_instance(*args, **kwargs)

    def import_data(self, *args: Any, **kwargs: Any) -> Any:
        """
        See :meth:`import_export.resources.Resource.import_data`
        """
        return super().import_data(*args, **kwargs)

    def import_row(self, *args: Any, **kwargs: Any) -> Any:
        """
        See :meth:`import_export.resources.Resource.import_row`
        """
        return super().import_row(*args, **kwargs)

    def save_instance(self, *args: Any, **kwargs: Any) -> Any:
        """
        See :meth:`import_export.resources.Resource.save_instance`
        """
        return super().save_instance(*args, **kwargs)

    class Meta:
        """
        Meta class of feedback resource
        """

        model = Feedback
        # if we don't define the empty fields all fields are created in the default way additionally to our custom way
        fields = ()
