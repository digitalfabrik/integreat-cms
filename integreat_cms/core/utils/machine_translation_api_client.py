"""
This module contains utilities for machine translation API clients
"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MachineTranslationApiClient(ABC):
    """
    A base class for API clients interacting with machine translation APIs
    """

    #: The current request
    #:
    #: :type: ~django.http.HttpRequest
    request = None
    #: The current region
    #:
    #: :type: ~integreat_cms.cms.models.regions.region.Region
    region = None
    #: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
    #: subclass of the current content type
    #:
    #: :type: ~django.forms.models.ModelFormMetaclass
    form_class = None

    def __init__(self, request, form_class):
        """
        Constructor initializes the class variables

        :param region: The current region
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :param form_class: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
                           subclass of the current content type
        :type form_class: ~django.forms.models.ModelFormMetaclass
        """
        self.request = request
        self.region = request.region
        self.form_class = form_class

    @abstractmethod
    def translate_queryset(self, queryset, language_slug):
        """
        Translate a given queryset into one specific language.
        Needs to be implemented by subclasses of MachineTranslationApiClient.

        :param queryset: The QuerySet of content objects to translate
        :type queryset: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]

        :param language_slug: The target language slug to translate into
        :type language_slug: str
        """

    def translate_object(self, obj, language_slug):
        """
        This function translates one content object

        :param obj: The content object
        :type obj: ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel

        :param language_slug: The target language slug
        :type language_slug: str
        """
        return self.translate_queryset([obj], language_slug)

    def __str__(self):
        """
        :return: A readable string representation of the machine translation API client
        :rtype: str
        """
        return type(self).__name__

    def __repr__(self):
        """
        :return: The canonical string representation of the machine translation API client
        :rtype: str
        """
        class_name = type(self).__name__
        return f"<{class_name} (request: {self.request!r}, region: {self.region!r}, form_class: {self.form_class})>"
