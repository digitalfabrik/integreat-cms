"""
This module contains labels for the choices regarding the position of embedding live content
"""
from django.utils.translation import gettext_lazy as _


CHOICES = (
    (True, _("Embed mirrored page before this page")),
    (False, _("Embed mirrored page after this page")),
)
