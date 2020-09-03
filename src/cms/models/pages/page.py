import logging

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language

from mptt.models import MPTTModel, TreeForeignKey

from ..regions.region import Region
from ...constants import status

logger = logging.getLogger(__name__)


class Page(MPTTModel):
    """
    Data model representing a page.

    :param id: The database id of the page
    :param icon: The title image of the page
    :param archived: Whether or not the page is archived
    :param mirrored_page_first: If ``mirrored_page`` is not ``None``, this field determines whether the live content is
                                embedded before the content of this page or after.
    :param created_date: The date and time when the page was created
    :param last_updated: The date and time when the page was last updated

    Fields inherited from the MPTT model (see :doc:`models` for more information):

    :param tree_id: The id of this page tree (all pages of one page tree share this id)
    :param lft: The left neighbour of this page
    :param rght: The right neighbour of this page
    :param level: The depth of the page node. Root pages are level `0`, their immediate children are level `1`, their
                  immediate children are level `2` and so on...

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
    archived = models.BooleanField(default=False)
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
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def depth(self):
        """
        Counts how many ancestors the page has. If the page is the root page, its depth is `0`.

        :return: The depth of this page in its page tree
        :rtype: str
        """
        return len(self.get_ancestors())

    @property
    def languages(self):
        """
        This property returns a list of all :class:`~cms.models.languages.language.Language` objects, to which a page
        translation exists.

        :return: list of all :class:`~cms.models.languages.language.Language` a page is translated into
        :rtype: list [ ~cms.models.languages.language.Language ]
        """
        page_translations = self.translations.prefetch_related("language").all()
        languages = []
        for page_translation in page_translations:
            if page_translation.language not in languages:
                languages.append(page_translation.language)
        return languages

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
            super()
            .get_siblings(include_self=include_self)
            .filter(region=self.region)
        )

    def get_translation(self, language_code):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~cms.models.languages.language.Language` code.

        :param language_code: The code of the desired :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The page translation in the requested :class:`~cms.models.languages.language.Language` or :obj:`None`
                 if no translation exists
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.translations.filter(language__code=language_code).first()

    def get_first_translation(self, priority_language_codes=None):
        """
        Helper function for page labels, second level paths etc. where the ancestor translation might not exist
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the first requested :class:`~cms.models.languages.language.Language` code that matches.
        So a lower list index means a higher priority.

        :param language_code: A list of :class:`~cms.models.languages.language.Language` codes, defaults to ``None``
        :type language_code: list [ str ], optional

        :return: The first page translation which matches one of the :class:`~cms.models.languages.language.Language`
                 given or :obj:`None` if no translation exists
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        # Taking [] directly as default parameter would be dangerous because it is mutable
        if not priority_language_codes:
            priority_language_codes = []
        for language_code in priority_language_codes + ["en-us", "de-de"]:
            if self.translations.filter(language__code=language_code).exists():
                return self.translations.filter(language__code=language_code).first()
        return self.translations.first()

    def get_public_translation(self, language_code):
        """
        This function retrieves the newest public translation of a page.

        :param language_code: The code of the requested :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The public translation of a page
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.translations.filter(
            language__code=language_code, status=status.PUBLIC,
        ).first()

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

    def get_absolute_url(self):
        """
        This helper function returns the absolute url to the editing form of a page

        :return: The absolute url of a page form
        :rtype: str
        """
        return reverse(
            "edit_page",
            kwargs={
                "page_id": self.id,
                "region_slug": self.region.slug,
                "language_code": self.region.default_language.code,
            },
        )

    @staticmethod
    def get_archived(region_slug):
        """
        This function returns all archived pages of the requested region

        :param region_slug: The slug of the requested :class:`~cms.models.regions.region.Region`
        :type region_slug: str

        :return: All archived pages of this region
        :rtype: ~django.db.models.query.QuerySet
        """
        return Page.objects.filter(archived=True, region__slug=region_slug)

    @staticmethod
    def archived_count(region_slug):
        """
        Count how many archived pages exist in one :class:`~cms.models.regions.region.Region`

        :param region_slug: The slug of the requested :class:`~cms.models.regions.region.Region`
        :type region_slug: str

        :return: Amount of archived pages in requested :class:`~cms.models.regions.region.Region`
        :rtype: int
        """
        return Page.objects.filter(archived=True, region__slug=region_slug).count()

    @classmethod
    def get_tree(cls, region_slug, archived=False):
        """
        Get all pages of one specific :class:`~cms.models.regions.region.Region` (either all archived or all not
        archived ones) together with its tree relations

        :param region_slug: slug of the :class:`~cms.models.regions.region.Region` the page belongs to
        :type region_slug: str

        :param archived: whether or not archived pages should be returned, defaults to ``False``
        :type archived: bool, optional

        :return: A :class:`~django.db.models.query.QuerySet` of either archived or not archived pages in the requested
                 :class:`~cms.models.regions.region.Region`
        :rtype: ~django.db.models.query.QuerySet
        """
        return (
            cls.objects.all()
            .prefetch_related("translations")
            .filter(region__slug=region_slug, archived=archived)
        )

    def best_language_title(self):
        """
        This function tries to determine which title to be used for a page. The first priority is the current backend
        language. If no translation is present in this language, the fallback is the region's default language.

        :return: The "best" title for showing pages in the backend
        :rtype: str
        """
        page_translation = self.translations.filter(language__code=get_language())
        if not page_translation:
            alt_code = self.region.default_language.code
            page_translation = self.translations.filter(language__code=alt_code)
        return page_translation.first().title

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <Page object at 0xDEADBEEF>

        :return: The string representation of the page with information about the most important fields (useful for
                 debugging purposes)
        :rtype: str
        """
        if self.id:
            first_translation = self.get_first_translation()
            if first_translation:
                return f"(id: {self.id}, slug: {first_translation.slug} ({first_translation.language.code}))"
            return f"(id: {self.id})"
        return super().__str__()

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
