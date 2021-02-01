from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.shortcuts import get_object_or_404

from ...constants import region_status, administrative_division
from ..languages.language import Language


class Region(models.Model):
    """
    Data model representing region.

    :param id: The database id of the region
    :param common_id: The `community identification number
                      <https://en.wikipedia.org/wiki/Community_Identification_Number>`_ of the region (public unique IDs
                      like `Gemeindeschlüssel <https://de.wikipedia.org/wiki/Amtlicher_Gemeindeschl%C3%BCssel>`_ in
                      Germany)
    :param name: The name of the region
    :param slug: The slug of the region (unique string identifier without spaces and special characters)
    :param status: The status of the region  (choices: :mod:`cms.constants.region_status`)
    :param administrative_division: The `administrative division
                                    <https://en.wikipedia.org/wiki/Administrative_division>`_ of the region (choices:
                                    :mod:`cms.constants.administrative_division`)
    :param aliases: The aliases of the region (e.g. smaller municipalities in that area)
    :param events_enabled: Whether or not events are enabled in the region
    :param push_notifications_enabled: Whether or not push notifications are enabled in the region
    :param push_notification_channels: If push notifications are enabled, this field contains an array of strings which
                                       denote the push notification channels of the region
    :param latitude: The latitude coordinate of an approximate center of the region
    :param longitude: The longitude coordinate of an approximate center of the region
    :param postal_code: The postal code of the region
    :param admin_mail: The email address of the region's administrator
    :param statistics_enabled: Whether or not statistics are enabled for the region
    :param matomo_url: If statistics are enabled, this contains the matomo url of the region
    :param matomo_token: If statistics are enabled, this contains the secret matomo access token of the region
    :param matomo_ssl_verify: If statistics are enabled, this field denotes whether matomo should use ssl
    :param page_permissions_enabled: Whether or not page-specific permissions_are enabled for this region. This adds the
                                     possibility to add single users to the ``editors`` or ``publishers`` of a
                                     :class:`~cms.models.pages.page.Page` which grants them the permissions on the
                                     object-instances.
    :param created_date: The date and time when the region was created
    :param last_updated: The date amd time when the region was last updated

    Reverse relationships:

    :param users: The user profiles of all users of this region
    :param language_tree_nodes: All language tree nodes of this region
    :param pages: The pages of this region
    :param events: The events of this region
    :param pois: The pois of this region
    :param offers: The offers of this region
    :param push_notifications: All push notifications of this region
    :param feedback: Feedback to this region
    :param event_list_feedback: Feedback to the events of this region
    :param offer_list_feedback: Feedback to the offers of this region
    """

    name = models.CharField(max_length=200)
    common_id = models.CharField(
        max_length=48, blank=True
    )  # Public unique IDs like German Gemeindeschluessel
    slug = models.SlugField(max_length=200, unique=True, blank=True, allow_unicode=True)
    status = models.CharField(
        max_length=8, choices=region_status.CHOICES, default=region_status.HIDDEN
    )

    administrative_division = models.CharField(
        max_length=24,
        choices=administrative_division.CHOICES,
        default=administrative_division.RURAL_DISTRICT,
    )
    aliases = models.TextField(blank=True)

    events_enabled = models.BooleanField(default=True)
    push_notifications_enabled = models.BooleanField(default=True)
    push_notification_channels = ArrayField(models.CharField(max_length=60), blank=True)

    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    postal_code = models.CharField(max_length=10)

    admin_mail = models.EmailField()

    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    statistics_enabled = models.BooleanField(default=False)
    matomo_url = models.CharField(max_length=150, blank=True, default="")
    matomo_token = models.CharField(max_length=150, blank=True, default="")
    matomo_ssl_verify = models.BooleanField(default=True)

    page_permissions_enabled = models.BooleanField(default=False)

    icon = models.ImageField(blank=True, null=True, upload_to="regions/%Y/%m/%d")

    chat_enabled = models.BooleanField(
        default=True,
        verbose_name="Author chat enabled",
        help_text="Whether or not the author chat is enabled in this region",
    )

    @property
    def languages(self):
        """
        This property returns a QuerySet of all :class:`~cms.models.languages.language.Language` objects which have a
        :class:`~cms.models.languages.language_tree_node.LanguageTreeNode` which belongs to this region.

        :return: A QuerySet of all :class:`~cms.models.languages.language.Language` object instances of a region
        :rtype: ~django.db.models.query.QuerySet [ ~cms.models.languages.language.Language ]
        """
        return Language.objects.filter(language_tree_nodes__region=self)

    @property
    def default_language(self):
        """
        This property returns the language :class:`~cms.models.languages.language.Language` which corresponds to the
        root :class:`~cms.models.languages.language_tree_node.LanguageTreeNode` of this region.

        :return: The root :class:`~cms.models.languages.language.Language` of a region
        :rtype: ~cms.models.languages.language.Language
        """
        tree_root = self.language_tree_nodes.filter(level=0).first()
        return tree_root.language if tree_root else None

    @classmethod
    def get_current_region(cls, request):
        """
        This class method returns the current region based on the current request and is used in
        :func:`backend.context_processors.region_slug_processor`

        :return: The root :class:`~cms.models.languages.language.Language` of a region
        :rtype: ~cms.models.languages.language.Language
        """
        # if rendered url is edit_region, the region slug originates from the region form.
        if (
            not hasattr(request, "resolver_match")
            or request.resolver_match.url_name == "edit_region"
        ):
            return None
        region_slug = request.resolver_match.kwargs.get("region_slug")
        if not region_slug:
            return None
        return get_object_or_404(cls, slug=region_slug)

    @property
    def archived_pages(self):
        """
        This property returns a QuerySet of all archived pages and their descendants of this region.

        :return: A QuerySet of all archived pages of this region
        :rtype: ~mptt.querysets.TreeQuerySet [ ~cms.models.pages.page.Page ]
        """
        # Queryset of explicitly archived pages
        explicitly_archived_pages = self.pages.filter(explicitly_archived=True)
        # Multiple order_by clauses are not allowed in sql queries, so to make combined queries with union() work,
        # we have to remove ordering from the input querysets and apply the default ordering to the resulting queryset.
        explicitly_archived_pages = explicitly_archived_pages.order_by()
        # List of QuerySets of descendants of archived pages
        implicitly_archived_pages = [
            page.get_descendants().order_by() for page in explicitly_archived_pages
        ]
        # Merge explicitly and implicitly archived pages
        archived_pages = explicitly_archived_pages.union(*implicitly_archived_pages)
        # Order the resulting :class:`~mptt.querysets.TreeQuerySet` to restore the tree-structure which is required for
        # the custom template tag "recursetree" of django-mptt (see :doc:`django-mptt:templates`)
        return archived_pages.order_by("tree_id", "lft")

    @property
    def non_archived_pages(self):
        """
        This property returns a QuerySet of all non-archived pages of this region.
        A page is considered as "non-archived" if its ``explicitly_archived`` property is ``False`` and all of the
        page's ancestors are not archived as well.

        :return: A QuerySet of all non-archived pages of this region
        :rtype: ~mptt.querysets.TreeQuerySet [ ~cms.models.pages.page.Page ]
        """
        # Multiple order_by clauses are not allowed in sql queries, so to make combined queries with difference() work,
        # we have to remove ordering from the input querysets and apply the default ordering to the resulting queryset.
        archived_pages = self.archived_pages.order_by()
        # Exclude archived pages from all pages
        non_archived_pages = self.pages.difference(archived_pages)
        # Order the resulting TreeQuerySet to restore the tree-structure which is required for  the custom template tag
        # "recursetree" of django-mptt (see :doc:`django-mptt:templates`)
        return non_archived_pages.order_by("tree_id", "lft")

    def get_pages(self, archived):
        """
        This method returns either all archived or all non-archived pages of this region.
        To retrieve all pages independently from their archived-state, use the reverse foreign key ``region.pages``.

        :param archived: Whether or not only archived pages should be returned
        :type archived: bool

        :return: Either the archived or the non-archived pages of this region
        :rtype: ~mptt.querysets.TreeQuerySet [ ~cms.models.pages.page.Page ]
        """
        if archived:
            return self.archived_pages
        return self.non_archived_pages

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <Region object at 0xDEADBEEF>

        :return: The string representation (in this case the name) of the region
        :rtype: str
        """
        return self.name

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
        permissions = (("manage_regions", "Can manage regions"),)
