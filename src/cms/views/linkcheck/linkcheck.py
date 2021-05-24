from django.db.models import OuterRef, Subquery
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.base import RedirectView

from backend.settings import PER_PAGE

from ...models.pages.page_translation import PageTranslation
from ...models.events.event_translation import EventTranslation
from ...models.pois.poi_translation import POITranslation
from ...utils.filter_links import filter_links

# pylint: disable=too-many-ancestors
class LinkListView(ListView):
    """
    View for retrieving a list of links grouped by their state
    """

    template_name = "linkcheck/links_by_filter.html"
    context_object_name = "filtered_links"
    paginate_by = PER_PAGE
    extra_context = {"current_menu_item": "linkcheck"}

    def get_queryset(self):
        """
        Selects all links for the current region
        Finally annotates queryset by the content_type title

        :return: The QuerySet of the filtered links
        :rtype: ~django.db.models.query.QuerySet
        """
        region_slug = self.kwargs.get("region_slug")
        link_filter = self.kwargs.get("link_filter")
        filtered_dict = filter_links(region_slug)
        self.extra_context.update(
            {
                "link_filter": link_filter,
                "number_valid": filtered_dict.get("valid_links").count(),
                "number_invalid": filtered_dict.get("invalid_links").count(),
                "number_unchecked": filtered_dict.get("unchecked_links").count(),
                "number_ignored": filtered_dict.get("ignored_links").count(),
            }
        )
        if link_filter == "valid":
            result = filtered_dict.get("valid_links")
        elif link_filter == "unchecked":
            result = filtered_dict.get("unchecked_links")
        elif link_filter == "ignored":
            result = filtered_dict.get("ignored_links")
        else:
            result = filtered_dict.get("invalid_links")
        page_translation = PageTranslation.objects.filter(id=OuterRef("object_id"))
        event_translation = EventTranslation.objects.filter(id=OuterRef("object_id"))
        poi_translation = POITranslation.objects.filter(id=OuterRef("object_id"))
        page_links = result.filter(content_type__model="pagetranslation").annotate(
            title=Subquery(page_translation.values("title")[:1])
        )
        event_links = result.filter(content_type__model="eventtranslation").annotate(
            title=Subquery(event_translation.values("title")[:1])
        )
        poi_links = result.filter(content_type__model="poitranslation").annotate(
            title=Subquery(poi_translation.values("title")[:1])
        )
        return page_links.union(event_links, poi_links)


class LinkListRedirectView(RedirectView):
    """
    View for redirecting to main page of the broken link checker
    """

    def get_redirect_url(self, *args, **kwargs):
        """
        Retrieve url for redirection

        :return: url to redirect to
        :rtype: str
        """
        kwargs.update({"link_filter": "invalid"})
        return reverse("linkcheck", kwargs=kwargs)
