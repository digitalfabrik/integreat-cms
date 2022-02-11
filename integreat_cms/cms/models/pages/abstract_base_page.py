import logging

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ..abstract_content_model import AbstractContentModel


logger = logging.getLogger(__name__)


class AbstractBasePage(AbstractContentModel):
    """
    Abstract base class for page and imprint page models.
    """

    explicitly_archived = models.BooleanField(
        default=False,
        verbose_name=_("explicitly archived"),
        help_text=_("Whether or not the page is explicitly archived"),
    )

    @cached_property
    def archived(self):
        """
        This is an alias of ``explicitly_archived``. Used for hierarchical pages to implement a more complex notion of
        explicitly and implicitly archived pages (see :func:`~integreat_cms.cms.models.pages.page.Page.archived`).

        :return: Whether or not this page is archived
        :rtype: bool
        """
        return self.explicitly_archived

    class Meta:
        #: This model is an abstract base class
        abstract = True
