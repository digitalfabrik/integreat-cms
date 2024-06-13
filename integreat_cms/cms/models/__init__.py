"""
This package contains all data models of the Integreat CMS.
Please refer to :mod:`django.db.models` for general information about Django models.
"""

from __future__ import annotations

from .chat.attachment_map import AttachmentMap
from .chat.chat_message import ChatMessage
from .chat.user_chat import ABTester, UserChat
from .events.event import Event
from .events.event_translation import EventTranslation
from .events.recurrence_rule import RecurrenceRule
from .feedback.event_feedback import EventFeedback
from .feedback.event_list_feedback import EventListFeedback
from .feedback.feedback import Feedback
from .feedback.imprint_page_feedback import ImprintPageFeedback
from .feedback.map_feedback import MapFeedback
from .feedback.offer_feedback import OfferFeedback
from .feedback.offer_list_feedback import OfferListFeedback
from .feedback.page_feedback import PageFeedback
from .feedback.poi_feedback import POIFeedback
from .feedback.region_feedback import RegionFeedback
from .feedback.search_result_feedback import SearchResultFeedback
from .languages.language import Language
from .languages.language_tree_node import LanguageTreeNode
from .media.directory import Directory
from .media.media_file import MediaFile
from .offers.offer_template import OfferTemplate
from .pages.imprint_page import ImprintPage
from .pages.imprint_page_translation import ImprintPageTranslation
from .pages.page import Page
from .pages.page_translation import PageTranslation
from .poi_categories.poi_category import POICategory
from .poi_categories.poi_category_translation import POICategoryTranslation
from .pois.poi import POI
from .pois.poi_translation import POITranslation
from .push_notifications.push_notification import PushNotification
from .push_notifications.push_notification_translation import (
    PushNotificationTranslation,
)
from .regions.region import Region
from .users.organization import Organization
from .users.role import Role
from .users.user import User
from .users.user_fido_key import FidoKey
