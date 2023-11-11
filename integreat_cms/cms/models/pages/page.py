from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cacheops import invalidate_model, invalidate_obj
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link
from treebeard.ns_tree import NS_NodeQuerySet

from ...utils.translation_utils import gettext_many_lazy as __
from ..abstract_content_model import ContentQuerySet
from ..abstract_tree_node import AbstractTreeNode
from ..decorators import modify_fields
from .abstract_base_page import AbstractBasePage
from .page_translation import PageTranslation

if TYPE_CHECKING:
    from typing import Any, Iterator

    from django.db.models.base import ModelBase
    from django.utils.safestring import SafeString

logger = logging.getLogger(__name__)


class PageQuerySet(NS_NodeQuerySet, ContentQuerySet):
    """
    Custom queryset for pages to inherit methods from both querysets for tree nodes and content objects
    """

    def cache_tree(
        self, archived: bool | None = None, language_slug: str | None = None
    ) -> list[Page]:
        """
        Caches a page tree queryset in a python data structure.

        :param archived: Whether the pages should be limited to either archived  or non-archived pages.
                         If not passed or ``None``, both archived and non-archived pages are returned.
        :param language_slug: Code to identify the desired language (optional, requires ``archived`` to be ``False``)
        :raises ValueError: Indicates that the combination of parameters is not supported.

        :return: A list of pages with cached children, descendants and ancestors and a list of all skipped pages
        """
        if language_slug is not None and archived is not False:
            raise ValueError(
                "archived must be False in order to filter for public translations by language_slug"
            )
        result: dict[int, Page] = {}
        skipped_pages: list[Page] = []
        for page in (
            self.prefetch_translations()
            .prefetch_public_translations()
            .order_by("tree_id", "lft")
        ):
            # pylint: disable=protected-access
            page._cached_ancestors = []
            page._cached_descendants = []
            page._cached_children = []
            # Determine whether the page should be included in the result
            # pylint: disable=too-many-boolean-expressions
            if (
                # If page is explicitly archived, include it only when archive is either True or None
                (page.explicitly_archived and archived is not False)
                # If page is not explicitly archived, two cases are possible:
                or (
                    not page.explicitly_archived
                    and (
                        # If the page is a root page, include it only when archive is either False or None
                        (not page.parent_id and not archived)
                        # Alternatively, include it if its parent is in the result
                        or (page.parent_id in result)
                    )
                    # If the page is not archived, we may want to check if a translation exists for a given language
                    and (
                        language_slug is None
                        or page.get_public_translation(language_slug)
                    )
                )
            ):
                if page.parent_id in result:
                    # Cache the page as child of the parent page
                    # pylint: disable=protected-access
                    result[page.parent_id]._cached_children.append(page)
                    result[page.parent_id]._cached_descendants.append(page)
                    # Cache the parent page as ancestor of the current page
                    page._cached_ancestors.extend(
                        result[page.parent_id]._cached_ancestors
                    )
                    page._cached_ancestors.append(result[page.parent_id])
                    # Cache the current page as descendant of the parent's page ancestors
                    for ancestor in result[page.parent_id]._cached_ancestors:
                        if ancestor.id in result:
                            result[ancestor.id]._cached_descendants.append(page)
                    # Set the relative depth to the relative depth of the parent + 1
                    page._relative_depth = result[page.parent_id].relative_depth + 1
                else:
                    # Set the relative depth to 1
                    page._relative_depth = 1
                result[page.id] = page
            else:
                # Keep track of all skipped pages
                skipped_pages.append(page)
        logger.debug("Cached result: %r", result)
        logger.debug("Skipped pages: %r", skipped_pages)
        return list(result.values())


# pylint: disable=too-few-public-methods
class PageManager(models.Manager):
    """
    Custom manager for pages to inherit methods from both managers for tree nodes and content objects
    """

    def get_queryset(self) -> PageQuerySet:
        """
        Sets the custom queryset as the default.

        :return: The sorted queryset
        """
        return PageQuerySet(self.model).order_by("tree_id", "lft")


@modify_fields(parent={"verbose_name": _("parent page")})
class Page(AbstractTreeNode, AbstractBasePage):
    """
    Data model representing a page.
    """

    icon = models.ForeignKey(
        "cms.MediaFile",
        verbose_name=_("icon"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
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
    authors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="editable_pages",
        verbose_name=_("authors"),
        help_text=__(
            _("A list of users who have the permission to edit this specific page."),
            _(
                "Only has effect if these users do not have the permission to edit pages anyway."
            ),
        ),
    )
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="publishable_pages",
        verbose_name=_("editors"),
        help_text=__(
            _("A list of users who have the permission to publish this specific page."),
            _(
                "Only has effect if these users do not have the permission to publish pages anyway."
            ),
        ),
    )
    organization = models.ForeignKey(
        "cms.Organization",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("responsible organization"),
        help_text=_(
            "This allows all members of the organization to edit and publish this page."
        ),
    )
    api_token = models.CharField(
        blank=True,
        max_length=36,
        verbose_name=_("API access token"),
        help_text=_("API token to allow writing content to translations."),
    )
    hix_ignore = models.BooleanField(
        default=False,
        verbose_name=_("Ignore HIX value"),
        help_text=_("This allows to ignore HIX value for this specific page."),
    )
    embedded_offers = models.ManyToManyField(
        "cms.OfferTemplate",
        blank=True,
        verbose_name=_("page based offer"),
        help_text=_(
            "Select an offer provider whose offers should be displayed on this page."
        ),
    )

    #: Custom model manager to inherit methods from tree manager as well as the custom content queryset
    objects = PageManager()

    @staticmethod
    def get_translation_model() -> ModelBase:
        """
        Returns the translation model of this content model

        :return: The class of translations
        """
        return PageTranslation

    @cached_property
    def explicitly_archived_ancestors(self) -> list[Page]:
        """
        This returns all of the page's ancestors which are archived.

        :return: The list of archived ancestors
        """

        return [
            ancestor
            for ancestor in self.get_cached_ancestors()
            if ancestor.explicitly_archived
        ]

    @cached_property
    def implicitly_archived(self) -> bool:
        """
        This checks whether one of the page's ancestors is archived which means that this page is implicitly archived as well.

        :return: Whether or not this page is implicitly archived
        """
        return bool(self.explicitly_archived_ancestors)

    @cached_property
    def archived(self) -> bool:
        """
        A hierarchical page is archived either explicitly if ``explicitly_archived=True`` or implicitly if one of its
        ancestors is explicitly archived.

        :return: Whether or not this page is archived
        """
        return self.explicitly_archived or self.implicitly_archived

    def get_non_archived_children(self) -> Iterator[Page]:
        """
        This method returns all children of this page that are neither explicitly archived nor implicitly archived

        :return: The non-archived children
        """
        # Keep track of archived parents to exclude their implicitly archived children
        archived_parents = set()

        for child_page in Page.get_tree(parent=self):
            # Check if page is either explicitly archived or has an archived ancestor in the list
            if (
                child_page.explicitly_archived
                or child_page.parent_id in archived_parents
            ):
                archived_parents.add(child_page.id)
            else:
                yield child_page

    @classmethod
    def get_root_pages(cls, region_slug: str) -> PageQuerySet:
        """
        Gets all root pages

        :param region_slug: Slug defining the region
        :return: All root pages i.e. pages without parents
        """
        return cls.get_region_root_nodes(region_slug=region_slug)

    def get_mirrored_page_translation(self, language_slug: str) -> Any | None:
        """
        Mirrored content always includes the live content from another page. This content needs to be added when
        delivering content to end users.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: The content of a mirrored page
        """
        if self.mirrored_page:
            return self.mirrored_page.get_public_translation(language_slug)
        return None

    @cached_property
    def relative_depth(self) -> int:
        """
        The relative depth inside a cached tree structure. This is relevant for archived pages, where even sub-pages
        should be displayed as root-pages if their parents are not archived.

        :return: The relative depth of this node inside its queryset
        """
        if hasattr(self, "_relative_depth"):
            return self._relative_depth
        return self.depth

    def move(self, target: Page, pos: str | None = None) -> None:
        """
        Moving tree nodes potentially causes changes to the fields tree_id, lft and rgt in :class:`~treebeard.ns_tree.NS_Node`
        so the cache of page translations has to be cleared, because of it's relation to :class:`~integreat_cms.cms.models.pages.page.Page`

        :param target: The target node which determines the new position
        :param pos: The new position of the page relative to the target
                    (choices: :mod:`~integreat_cms.cms.constants.position`)
        :raises ~treebeard.exceptions.InvalidPosition: If the node is moved to another region
        """
        super().move(target, pos)
        invalidate_model(PageTranslation)

    def archive(self) -> None:
        """
        Archives the page and removes all links of this page and all its subpages from the linkchecker
        """
        # Delete related link objects as they are no longer required and set mirrored page to None
        for child_page in Page.get_tree(parent=self).exclude(explicitly_archived=True):
            Link.objects.filter(page_translation__page=child_page).delete()
            if child_page.mirrored_page:
                child_page.mirrored_page = None
                child_page.save()
                invalidate_obj(child_page)

        self.explicitly_archived = True
        self.mirrored_page = None
        self.save()
        invalidate_obj(self)

    def restore(self) -> None:
        """
        Restores the page and adds all links of this page and its now non-archived subpages back
        """
        self.explicitly_archived = False
        self.save()

        if not self.implicitly_archived:
            # Restore related link objects
            for child_page in self.get_non_archived_children():
                for translation in child_page.translations.distinct(
                    "page__pk", "language__pk"
                ):
                    # The post_save signal will create link objects from the content
                    translation.save(update_timestamp=False)

    def __str__(self) -> SafeString:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Page object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the page
        """
        return self.best_translation.path()

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Page: Page object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the page
        """
        parent_str = f", parent: {self.parent_id}" if self.parent_id else ""
        region_str = f", region: {self.region.slug}" if self.region else ""
        slug_str = (
            f", slug: {self.best_translation.slug}" if self.best_translation else ""
        )
        return f"<Page (id: {self.id}{parent_str}{region_str}{slug_str})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page")
        #: The plural verbose name of the model
        verbose_name_plural = _("pages")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "pages"
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The custom permissions for this model
        permissions = (
            ("publish_page", "Can publish page"),
            ("grant_page_permissions", "Can grant page permission"),
        )
