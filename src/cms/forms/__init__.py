"""
Forms for creating and modifying database objects.
Please refer to :mod:`django.forms` for general information about Django forms (see also: :doc:`topics/forms/index`).
"""

from .chat.chat_message_form import ChatMessageForm

from .events.event_filter_form import EventFilterForm
from .events.event_form import EventForm
from .events.event_translation_form import EventTranslationForm
from .events.recurrence_rule_form import RecurrenceRuleForm

from .feedback.admin_feedback_filter_form import AdminFeedbackFilterForm
from .feedback.region_feedback_filter_form import RegionFeedbackFilterForm

from .imprint.imprint_translation_form import ImprintTranslationForm

from .languages.language_form import LanguageForm
from .language_tree.language_tree_node_form import LanguageTreeNodeForm

from .media.upload_media_file_form import UploadMediaFileForm
from .media.media_file_form import MediaFileForm
from .media.create_directory_form import CreateDirectoryForm
from .media.directory_form import DirectoryForm

from .offer_templates.offer_template_form import OfferTemplateForm

from .organizations.organization_form import OrganizationForm

from .pages.page_filter_form import PageFilterForm
from .pages.page_form import PageForm
from .pages.page_translation_form import PageTranslationForm

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

from .users.authentication_form import AuthenticationForm
from .users.region_user_form import RegionUserForm
from .users.user_email_form import UserEmailForm
from .users.user_form import UserForm
from .users.user_password_form import UserPasswordForm
