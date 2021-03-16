from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .offer_template import OfferTemplate
from ..regions.region import Region
from ...constants import postal_code


class Offer(models.Model):
    """
    The offer model is used to activate an :class:`~cms.models.offers.offer_template.OfferTemplate` for a specific
    :class:`~cms.models.regions.region.Region`. Integreat offers are extended features apart from pages and events and
    are usually offered by a third party. In most cases, the url is an external API endpoint which the frontend apps can
    query and render the results inside the Integreat app.
    The sole existence of an offer object instance means that it is activated, and if there is no object for a
    region/template-combination, it is deactivated.
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name=_("region"),
    )
    template = models.ForeignKey(
        OfferTemplate,
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name=_("template"),
    )
    created_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True, verbose_name=_("modification date")
    )

    @property
    def slug(self):
        """
        The offer should inherit the slug property from its template

        :return: The slug of an offer
        :rtype: str
        """
        return self.template.slug

    @property
    def name(self):
        """
        The offer should inherit the name property from its template

        :return: The name of an offer
        :rtype: str
        """
        return self.template.name

    @property
    def thumbnail(self):
        """
        The offer should inherit the thumbnail property from its template

        :return: The thumbnail url of an offer
        :rtype: str
        """
        return self.template.thumbnail

    @property
    def url(self):
        """
        The offer should inherit the slug property from its template. This is the url to an API endpoint in most cases.
        Some offers depend on the location which is realized by adding the postal code of the current region to the
        request. If the offer template indicates that the postal code should be used as ``GET``-parameter, the class
        attribute ``use_postal_code`` has to be set to ``postal_code.GET`` (see :mod:`cms.constants.postal_code`) and
        the url has to end with the name of the required parameter-name, e.g. ``https://example.com/api?location=``.

        :return: The url of an offer
        :rtype: str
        """
        if self.template.use_postal_code == postal_code.GET:
            return self.template.url + self.region.postal_code
        return self.template.url

    @property
    def post_data(self):
        """
        In case the url expects additional post data, it is stored inside the ``post_data``-dict. Some offers depend on
        the location which is realized by adding the postal code of the current region to the request. If the offer
        template indicates that the postal code should be used as ``GET``-parameter, the class attribute
        ``use_postal_code`` has to be set to ``postal_code.POST`` (see :mod:`cms.constants.postal_code`) and then the
        key ``search-plz`` is automatically added to the post data. In case a third party service needs a different
        format, it has to be hard-coded here or we need other changes to the offer model.

        :return: The post data of the offer's url
        :rtype: dict
        """
        post_data = self.template.post_data
        if self.template.use_postal_code == postal_code.POST:
            post_data.update({"search-plz": self.region.postal_code})
        return post_data

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Offer object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the offer
        :rtype: str
        """
        return self.name

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Offer: Offer object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the offer
        :rtype: str
        """
        return f"<Offer (id: {self.id}, region: {self.region.slug}, slug: {self.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("offer")
        #: The plural verbose name of the model
        verbose_name_plural = _("offers")
        #: There cannot be two offers with the same region and template
        unique_together = (
            (
                "region",
                "template",
            ),
        )
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (("manage_offers", "Can manage offers"),)
