from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone

from ...constants import postal_code


class OfferTemplate(models.Model):
    """
    The OfferTemplate model is used to store templates of offers which can be activated for specific regions. The
    information stored in an offer template is global, so if you need parameters, which depend on local information
    of a region, it has to be added to the :class:`~cms.models.offers.offer.Offer` model.

    :param id: The database id of the offer template
    :param name: The name of the offer template
    :param slug: The slug of the offer template
    :param thumbnail: The thumbnail url of the offer template
    :param url: The url of the offer template. This will be an external api endoint in most cases.
    :param post_data: If additional post data is required for retrieving the url, it has to be stored in this dict.
    :param use_postal_code: If and how the postal code should be injected in the url or post data (choices:
                            :mod:`cms.constants.postal_code`)

    Reverse relationships:

    :param offers: All offers which use this template
    """

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    thumbnail = models.URLField(max_length=250)
    url = models.URLField(max_length=250)
    post_data = JSONField(max_length=250, default=dict, blank=True)
    use_postal_code = models.CharField(max_length=4, choices=postal_code.CHOICES, default=postal_code.NONE)

    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <OfferTemplate object at 0xDEADBEEF>

        :return: The string representation (in this case the name) of the offer template
        :rtype: str
        """
        return self.name

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_offer_templates', 'Can manage offer templates'),
        )
