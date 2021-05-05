from django.db.models import Q, OuterRef, Subquery
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.base import RedirectView

from linkcheck.models import Link
from backend.settings import PER_PAGE

from ...models.pages.page_translation import PageTranslation
from ...models.events.event_translation import EventTranslation
from ...models.pois.poi_translation import POITranslation


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
        First filters all links by region
        Next filters by links state and counts the number of links per group
        Finally annotates queryset by the content_type title

        :return: The QuerySet of the filtered links
        :rtype: ~django.db.models.query.QuerySet
        """
        region_slug = self.kwargs.get("region_slug")
        link_filter = self.kwargs.get("link_filter")
        qset = Link.objects.filter(
            Q(page_translations__page__region__slug=region_slug)
            | Q(event_translations__event__region__slug=region_slug)
            | Q(poi_translations__poi__region__slug=region_slug)
        )
        qset = qset.order_by("-url__last_checked")
        valid_links = qset.filter(ignore=False, url__status__exact=True)
        unchecked_links = qset.filter(ignore=False, url__last_checked__exact=None)
        ignored_links = qset.filter(ignore=True)
        invalid_links = qset.filter(ignore=False, url__status__exact=False)
        self.extra_context.update(
            {
                "link_filter": link_filter,
                "number_valid": valid_links.count(),
                "number_invalid": invalid_links.count(),
                "number_unchecked": unchecked_links.count(),
                "number_ignored": ignored_links.count(),
            }
        )
        if link_filter == "valid":
            result = valid_links
        elif link_filter == "unchecked":
            result = unchecked_links
        elif link_filter == "ignored":
            result = ignored_links
        else:
            result = invalid_links
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
