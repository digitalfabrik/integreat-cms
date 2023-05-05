from rest_framework import generics, serializers

from ...cms.constants import postal_code
from ..utils import ReadOnlyModelSerializer


def get_url(offer, region):
    """
    The offer should inherit the slug property from its template. This is the url to an API endpoint in most cases.
    Some offers depend on the location which is realized by adding the postal code of the current region to the
    request. If the offer template indicates that the postal code should be used as ``GET``-parameter, the class
    attribute ``use_postal_code`` has to be set to ``postal_code.GET`` (see :mod:`~integreat_cms.cms.constants.postal_code`) and
    the url has to end with the name of the required parameter-name, e.g. ``https://example.com/api?location=``.

    :param offer: one offer (formerly extra)
    :type offer: ~integreat_cms.cms.models.offers.offer_template.OfferTemplate

    :param region: current region object
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :return: The url of an offer
    :rtype: str
    """
    if offer.use_postal_code == postal_code.GET:
        return offer.url + region.postal_code
    return offer.url


def get_post_data(offer, region):
    """
    In case the url expects additional post data, it is stored inside the ``post_data``-dict. Some offers depend on
    the location which is realized by adding the postal code of the current region to the request. If the offer
    template indicates that the postal code should be used as ``GET``-parameter, the class attribute
    ``use_postal_code`` has to be set to ``postal_code.POST`` (see :mod:`~integreat_cms.cms.constants.postal_code`) and then the
    key ``search-plz`` is automatically added to the post data. In case a third party service needs a different
    format, it has to be hard-coded here or we need other changes to the offer model.

    :param offer: one offer (formerly extra)
    :type offer: ~integreat_cms.cms.models.offers.offer_template.OfferTemplate

    :param region: current region object
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :return: The post data of the offer's url
    :rtype: dict
    """
    post_data = offer.post_data
    if offer.use_postal_code == postal_code.POST:
        post_data.update({"search-plz": region.postal_code})
    if not post_data:
        return None
    return post_data


class OfferSerializer(ReadOnlyModelSerializer):
    name = serializers.CharField()
    alias = serializers.SlugField()
    url = serializers.CharField()
    post = serializers.CharField()
    thumbnail = serializers.CharField()

    def to_representation(self, offer):
        """
        Converts the offer instance into a dictionary.
        Custom implementation, since `url` and `post` require special handling.
        """
        region = self.context["region"]
        return {
            "name": offer.name,
            "alias": offer.slug,
            "url": get_url(offer, region),
            "post": get_post_data(offer, region),
            "thumbnail": offer.thumbnail,
        }


class OfferView(generics.ListAPIView):
    serializer_class = OfferSerializer

    def get_serializer_context(self):
        if self.request:
            return {"region": self.request.region}
        return {}

    def get_queryset(self):
        return self.request.region.offers.all()
