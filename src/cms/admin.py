"""
File routing to the admin region
"""


from django.contrib import admin

from .models import ChatMessage
from .models import Configuration
from .models import Event
from .models import EventTranslation
from .models import Offer
from .models import OfferTemplate
from .models import Language
from .models import LanguageTreeNode
from .models import Organization
from .models import Page
from .models import PageTranslation
from .models import POI
from .models import POITranslation
from .models import PushNotificationChannel
from .models import Region
from .models import RecurrenceRule
from .models import UserMfa
from .models import UserProfile
from .models import EventFeedback
from .models import EventListFeedback
from .models import ImprintPageFeedback
from .models import MapFeedback
from .models import OfferFeedback
from .models import OfferListFeedback
from .models import PageFeedback
from .models import POIFeedback
from .models import RegionFeedback
from .models import SearchResultFeedback
from .models import ImprintPage
from .models import ImprintPageTranslation

admin.site.register(ChatMessage)
admin.site.register(Configuration)
admin.site.register(Event)
admin.site.register(EventTranslation)
admin.site.register(Offer)
admin.site.register(OfferTemplate)
admin.site.register(Language)
admin.site.register(LanguageTreeNode)
admin.site.register(Organization)
admin.site.register(Page)
admin.site.register(PageTranslation)
admin.site.register(POI)
admin.site.register(POITranslation)
admin.site.register(PushNotificationChannel)
admin.site.register(Region)
admin.site.register(RecurrenceRule)
admin.site.register(UserMfa)
admin.site.register(UserProfile)
admin.site.register(EventFeedback)
admin.site.register(EventListFeedback)
admin.site.register(ImprintPageFeedback)
admin.site.register(MapFeedback)
admin.site.register(OfferFeedback)
admin.site.register(OfferListFeedback)
admin.site.register(PageFeedback)
admin.site.register(POIFeedback)
admin.site.register(RegionFeedback)
admin.site.register(SearchResultFeedback)
admin.site.register(ImprintPage)
admin.site.register(ImprintPageTranslation)
