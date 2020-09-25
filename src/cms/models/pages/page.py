import logging

from mptt.models import MPTTModel, TreeForeignKey

from django.conf import settings
from django.db import models

from .abstract_base_page import AbstractBasePage
from ..regions.region import Region

logger = logging.getLogger(__name__)


class Page(MPTTModel, AbstractBasePage):
    """
    Data model representing a page.

    :param id: The database id of the page
    :param icon: The title image of the page
    :param mirrored_page_first: If ``mirrored_page`` is not ``None``, this field determines whether the live content is
                                embedded before the content of this page or after.

    Fields inherited from the MPTT model (see :doc:`models` for more information):

    :param tree_id: The id of this page tree (all pages of one page tree share this id)
    :param lft: The left neighbour of this page
    :param rght: The right neighbour of this page
    :param level: The depth of the page node. Root pages are level `0`, their immediate children are level `1`, their
                  immediate children are level `2` and so on...

    Fields inherited from the :class:`~cms.models.pages.abstract_base_page.AbstractBasePage` model:

    :param archived: Whether or not the page is archived
    :param created_date: The date and time when the page was created
    :param last_updated: The date and time when the page was last updated

    Relationship fields:

    :param parent: The parent page of this page (related name: ``children``)
    :param region: The region to which the page belongs (related name: ``pages``)
    :param mirrored_page: If the page embeds live content from another page, it is referenced here.
    :param editors: A list of users who have the permission to edit this specific page (related name:
                    ``editable_pages``). Only has effect if these users do not have the permission to edit pages anyway.
    :param publishers: A list of users who have the permission to publish this specific page (related name:
                       ``publishable_pages``). Only has effect if these users do not have the permission to publish
                       pages anyway.

    Reverse relationships:

    :param children: The children of this page
    :param translations: The translations of this page
    :param feedback: The feedback to this page
    """

    parent = TreeForeignKey(
        "self", blank=True, null=True, related_name="children", on_delete=models.PROTECT
    )
    icon = models.ImageField(blank=True, null=True, upload_to="pages/%Y/%m/%d")
    region = models.ForeignKey(Region, related_name="pages", on_delete=models.CASCADE)
    mirrored_page = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT
    )
    mirrored_page_first = models.BooleanField(default=True, null=True, blank=True)
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="editable_pages", blank=True
    )
    publishers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="publishable_pages", blank=True
    )

    @property
    def depth(self):
        """
        Counts how many ancestors the page has. If the page is the root page, its depth is `0`.

        :return: The depth of this page in its page tree
        :rtype: str
        """
        return len(self.get_ancestors())

    def get_previous_sibling(self, *filter_args, **filter_kwargs):
        # Only consider siblings from this region
        filter_kwargs["region"] = self.region
        return super().get_previous_sibling(*filter_args, **filter_kwargs)

    def get_next_sibling(self, *filter_args, **filter_kwargs):
        # Only consider siblings from this region
        filter_kwargs["region"] = self.region
        return super().get_next_sibling(*filter_args, **filter_kwargs)

    def get_siblings(self, include_self=False):
        # Return only siblings from the same region
        return (
            super().get_siblings(include_self=include_self).filter(region=self.region)
        )

    def get_mirrored_text(self, language_code):
        """
        Mirrored content always includes the live content from another page. This content needs to be added when
        delivering content to end users.

        :param language_code: The code of the requested :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The content of a mirrored page
        :rtype: str
        """
        if self.mirrored_page:
            return self.mirrored_page.get_translation(language_code).text
        return None

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple

        :param permissions: The custom permissions for this model
        :type permissions: tuple
        """

        default_permissions = ()
        permissions = (
            ("view_pages", "Can view pages"),
            ("edit_pages", "Can edit pages"),
            ("publish_pages", "Can publish pages"),
            ("grant_page_permissions", "Can grant page permissions"),
        )
