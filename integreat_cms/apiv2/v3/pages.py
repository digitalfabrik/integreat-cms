import logging

from django.conf import settings
from django.http import Http404
from django.urls import resolve
from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework import generics, serializers

from ..utils import ReadOnlyModelSerializer

logger = logging.getLogger(__name__)


# TODO: Add Matomo tracking
class PageTranslationSerializer(ReadOnlyModelSerializer):
    id = serializers.IntegerField()
    url = serializers.CharField()
    path = serializers.CharField()
    title = serializers.CharField()
    modified_gmt = serializers.TimeField(help_text="Deprecated")
    last_updated = serializers.TimeField()
    excerpt = serializers.CharField()
    content = serializers.CharField()
    parent = serializers.JSONField()
    order = serializers.IntegerField()
    available_languages = serializers.JSONField()
    thumbnail = serializers.CharField()
    organization = serializers.CharField()
    hash = serializers.IntegerField(allow_null=True)

    def to_representation(self, page_translation):
        """
        Converts the instance into a dictionary.

        :param page_translation: single page translation object
        :type page_translation: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

        :raises ~django.http.Http404: HTTP status 404 if a parent is archived

        :return: data necessary for API
        :rtype: dict
        """
        fallback_parent = {
            "id": 0,
            "url": None,
            "path": None,
        }

        parent_page = page_translation.page.cached_parent
        if parent_page and not parent_page.explicitly_archived:
            if parent_public_translation := parent_page.get_public_translation(
                page_translation.language.slug
            ):
                parent_absolute_url = parent_public_translation.get_absolute_url()
                parent = {
                    "id": parent_page.id,
                    "url": settings.BASE_URL + parent_absolute_url,
                    "path": parent_absolute_url,
                }
                # use left edge indicator of mptt model for ordering of child pages
                order = page_translation.page.lft
            else:
                logger.info(
                    "The parent %r of %r does not have a public translation in %r",
                    parent_page,
                    page_translation.page,
                    page_translation.language,
                )
                raise Http404("No Page matches the given url or id.")
        else:
            parent = fallback_parent
            # use tree id of mptt model for ordering of root pages
            order = page_translation.page.tree_id

        organization = page_translation.page.organization
        absolute_url = page_translation.get_absolute_url()
        return {
            "id": page_translation.id,
            "url": settings.BASE_URL + absolute_url,
            "path": absolute_url,
            "title": page_translation.title,
            "modified_gmt": page_translation.combined_last_updated,  # deprecated field in the future
            "last_updated": timezone.localtime(page_translation.combined_last_updated),
            "excerpt": strip_tags(page_translation.combined_text),
            "content": page_translation.combined_text,
            "parent": parent,
            "order": order,
            "available_languages": page_translation.available_languages_dict,
            "thumbnail": page_translation.page.icon.url
            if page_translation.page.icon
            else None,
            "organization": {
                "id": organization.id,
                "slug": organization.slug,
                "name": organization.name,
                "logo": organization.icon.url if organization.icon else None,
            }
            if organization
            else None,
            "hash": None,
        }


class PageView(generics.ListAPIView):
    """
    Returns all pages in the current language and region.
    """

    serializer_class = PageTranslationSerializer

    def get_queryset(self):
        request = self.request
        resolver_match = resolve(request.path)
        language_slug = resolver_match.kwargs.get("language_slug")
        region = request.region
        region.get_language_or_404(language_slug, only_active=True)
        pages = (
            region.pages.select_related("organization")
            .filter(explicitly_archived=False)
            .cache_tree(archived=False, language_slug=language_slug)
        )
        translations = (page.get_public_translation(language_slug) for page in pages)
        return (translation for translation in translations if translation)
