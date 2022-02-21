"""
Override the app config of the linkcheck app
"""
from linkcheck.apps import LinkcheckConfig


class ModifiedLinkcheckConfig(LinkcheckConfig):
    """
    Use the legacy field for automatic primary keys
    """

    default_auto_field = "django.db.models.AutoField"
