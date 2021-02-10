import logging

from mptt.models import MPTTModel, TreeForeignKey

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .abstract_base_page import AbstractBasePage
from ..regions.region import Region
from ..users.organization import Organization
from ...utils.translation_utils import ugettext_many_lazy as __

logger = logging.getLogger(__name__)


class Page(MPTTModel, AbstractBasePage):
    """
    Data model representing a page.
    """

    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
        verbose_name=_("parent page"),
    )
    icon = models.ImageField(
        null=True,
        blank=True,
        upload_to="pages/%Y/%m/%d",
        verbose_name=_("thumbnail icon"),
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="pages",
        verbose_name=_("region"),
    )
    mirrored_page = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="mirroring_pages",
        verbose_name=_("mirrored page"),
        help_text=_(
            "If the page embeds live content from another page, it is referenced here."
        ),
    )
    mirrored_page_first = models.BooleanField(
        default=True,
        null=True,
        blank=True,
        verbose_name=_("Position of mirrored page"),
        help_text=_(
            "If a mirrored page is set, this field determines whether the live content is embedded before the content of this page or after."
        ),
    )
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="editable_pages",
        verbose_name=_("editors"),
        help_text=__(
            _("A list of users who have the permission to edit this specific page."),
            _(
                "Only has effect if these users do not have the permission to edit pages anyway."
            ),
        ),
    )
    publishers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="publishable_pages",
        verbose_name=_("publishers"),
        help_text=__(
            _("A list of users who have the permission to publish this specific page."),
            _(
                "Only has effect if these users do not have the permission to publish pages anyway."
            ),
        ),
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pages",
        verbose_name=_("responsible organization"),
        help_text=_(
            "This allows all members of the organization to edit and publish this page."
        ),
    )

    @property
    def explicitly_archived_ancestors(self):
        """
        This returns all of the page's ancestors which are archived.

        :return: The QuerySet of archived ancestors
        :rtype: ~mptt.querysets.TreeQuerySet [ ~cms.models.pages.page.Page ]
        """
        return self.get_ancestors().filter(explicitly_archived=True)

    @property
    def implicitly_archived(self):
        """
        This checks whether one of the page's ancestors is archived which means that this page is implicitly archived as well.

        :return: Whether or not this page is implicitly archived
        :rtype: bool
        """
        return self.explicitly_archived_ancestors.exists()

    @property
    def archived(self):
        """
        A hierarchical page is archived either explicitly if ``explicitly_archived=True`` or implicitly if one of its
        ancestors is explicitly archived.

        :return: Whether or not this page is archived
        :rtype: bool
        """
        return self.explicitly_archived or self.implicitly_archived

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

    def get_mirrored_page(self, language_code):
        """
        Mirrored content always includes the live content from another page. This content needs to be added when
        delivering content to end users.

        :param language_code: The code of the requested :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The content of a mirrored page
        :rtype: str
        """
        if self.mirrored_page:
            return self.mirrored_page.get_public_translation(language_code)
        return None

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page")
        #: The plural verbose name of the model
        verbose_name_plural = _("pages")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (
            ("view_pages", "Can view pages"),
            ("edit_pages", "Can edit pages"),
            ("publish_pages", "Can publish pages"),
            ("grant_page_permissions", "Can grant page permissions"),
        )
