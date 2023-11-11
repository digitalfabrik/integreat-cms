"""
Forms for creating and modifying database objects.
Please refer to :mod:`django.forms` for general information about Django forms (see also: :doc:`django:topics/forms/index`).
"""

from __future__ import annotations

from .chat.chat_message_form import ChatMessageForm
from .events.event_filter_form import EventFilterForm
from .events.event_form import EventForm
from .events.event_translation_form import EventTranslationForm
from .events.recurrence_rule_form import RecurrenceRuleForm
from .feedback.admin_feedback_filter_form import AdminFeedbackFilterForm
from .feedback.region_feedback_filter_form import RegionFeedbackFilterForm
from .imprint.imprint_translation_form import ImprintTranslationForm
from .language_tree.language_tree_node_form import LanguageTreeNodeForm
from .languages.language_form import LanguageForm
from .linkcheck.link_replace_form import LinkReplaceForm
from .media.create_directory_form import CreateDirectoryForm
from .media.directory_form import DirectoryForm
from .media.media_file_form import MediaFileForm
from .media.media_move_form import MediaMoveForm
from .media.replace_media_file_form import ReplaceMediaFileForm
from .media.upload_media_file_form import UploadMediaFileForm
from .object_search_form import ObjectSearchForm
from .offer_templates.offer_template_form import OfferTemplateForm
from .organizations.organization_form import OrganizationForm
from .pages.page_filter_form import PageFilterForm
from .pages.page_form import PageForm
from .pages.page_translation_form import PageTranslationForm
from .poi_categories.poi_category_form import POICategoryForm
from .poi_categories.poi_category_translation_form import (
    poi_category_translation_formset_factory,
    POICategoryTranslationForm,
)
from .pois.poi_form import POIForm
from .pois.poi_translation_form import POITranslationForm
from .push_notifications.push_notification_form import PushNotificationForm
from .push_notifications.push_notification_translation_form import (
    PushNotificationTranslationForm,
)
from .regions.region_form import RegionForm
from .roles.group_form import GroupForm
from .roles.role_form import RoleForm
from .statistics.statistics_filter_form import StatisticsFilterForm
from .translations.translations_management_form import TranslationsManagementForm
from .users.authentication_form import AuthenticationForm
from .users.password_reset_form import CustomPasswordResetForm
from .users.region_user_form import RegionUserForm
from .users.user_email_form import UserEmailForm
from .users.user_filter_form import UserFilterForm
from .users.user_form import UserForm
from .users.user_password_form import UserPasswordForm
from .users.user_preferences_form import UserPreferencesForm
