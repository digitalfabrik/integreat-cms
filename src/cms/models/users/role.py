from django.contrib.auth.models import Group
from django.db import models
from django.utils.functional import cached_property
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from ...constants import role_names


class Role(models.Model):
    """
    Meta information about the default Django auth group model
    """

    #: Manage choices in :mod:`cms.constants.role_names`
    name = models.CharField(
        max_length=50,
        choices=role_names.CHOICES,
        verbose_name=_("name"),
    )
    group = models.OneToOneField(
        Group,
        unique=True,
        on_delete=models.CASCADE,
        related_name="role",
        verbose_name=_("Django auth group"),
    )
    staff_role = models.BooleanField(
        default=False,
        verbose_name=_("staff role"),
        help_text=_("Whether or not this role is designed for staff members"),
    )

    @cached_property
    def english_name(self):
        """
        This returns the english name of a role which is used for logging

        :return: The english name of the role
        :rtype: str
        """
        with translation.override("en"):
            return self.get_name_display()

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Role object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the role
        :rtype: str
        """
        return self.get_name_display()

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Role: Role object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the role
        :rtype: str
        """
        return f"<Role (id: {self.id}, name: {self.english_name}{', staff role' if self.staff_role else ''})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("role")
        #: The plural verbose name of the model
        verbose_name_plural = _("roles")
        #: The default permissions for this model
        default_permissions = ()
