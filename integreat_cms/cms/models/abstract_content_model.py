from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import get_language, ugettext_lazy as _
from django.utils import timezone

from ..constants import status
from .regions.region import Region


class ContentQuerySet(models.QuerySet):
    """
    This queryset provides the option to prefetch translations for content objects
    """

    def prefetch_translations(self):
        """
        Get the queryset including the custom attribute ``prefetched_translations`` which contains the latest
        translations of each content object in each language

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        TranslationModel = self.model.get_translation_model()
        foreign_field = TranslationModel.foreign_field() + "_id"
        return self.prefetch_related(
            models.Prefetch(
                "translations",
                queryset=TranslationModel.objects.order_by(
                    foreign_field, "language_id", "-version"
                )
                .distinct(foreign_field, "language_id")
                .select_related("language"),
                to_attr="prefetched_translations",
            )
        )

    def prefetch_public_translations(self):
        """
        Get the queryset including the custom attribute ``prefetched_public_translations`` which contains the latest
        public translations of each content object in each language

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        TranslationModel = self.model.get_translation_model()
        foreign_field = TranslationModel.foreign_field() + "_id"
        return self.prefetch_related(
            models.Prefetch(
                "translations",
                queryset=TranslationModel.objects.filter(status=status.PUBLIC)
                .order_by(foreign_field, "language_id", "-version")
                .distinct(foreign_field, "language_id")
                .select_related("language"),
                to_attr="prefetched_public_translations",
            )
        )


class AbstractContentModel(models.Model):
    """
    Abstract base class for all content models
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        verbose_name=_("region"),
    )
    created_date = models.DateTimeField(
        default=timezone.now, verbose_name=_("creation date")
    )

    #: Custom model manager for content objects
    objects = ContentQuerySet.as_manager()

    @cached_property
    def languages(self):
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects, to
        which a translation exists.

        :raises NotImplementedError: If the property is not implemented in the subclass
        """
        raise NotImplementedError

    def get_translation(self, language_slug):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~integreat_cms.cms.models.languages.language.Language` slug.

        :param language_slug: The slug of the desired :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        try:
            # Try to get the prefetched translations (which are already distinct per language)
            return next(
                (
                    translation
                    for translation in self.prefetched_translations
                    if translation.language.slug == language_slug
                )
            )
        except (AttributeError, StopIteration):
            # If the translations were not prefetched, query it from the database
            return (
                self.translations.filter(language__slug=language_slug)
                .select_related("language")
                .first()
            )

    def get_public_translation(self, language_slug):
        """
        This function retrieves the newest public translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        try:
            # Try to get the prefetched translations (which are already distinct per language)
            return next(
                (
                    translation
                    for translation in self.prefetched_public_translations
                    if translation.language.slug == language_slug
                )
            )
        except (AttributeError, StopIteration):
            # If the translations were not prefetched or the latest version was not public, query it from the database
            return (
                self.translations.filter(
                    language__slug=language_slug,
                    status=status.PUBLIC,
                )
                .select_related("language")
                .first()
            )

    @cached_property
    def backend_translation(self):
        """
        This function returns the translation of this content object in the current backend language.

        :return: The backend translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.translations.filter(language__slug=get_language()).first()

    @cached_property
    def default_translation(self):
        """
        This function returns the translation of this content object in the region's default language.
        Since a content object can only be created by creating a translation in the default language, this is guaranteed
        to return a page translation.

        :return: The default translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.translations.filter(language=self.region.default_language).first()

    @cached_property
    def best_translation(self):
        """
        This function returns the translation of this content object in the current backend language and if it doesn't
        exist, it provides a fallback to the translation in the region's default language.

        :return: The "best" translation of a content object for displaying in the backend
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.backend_translation or self.default_translation

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``AbstractContentModel object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the content object
        :rtype: str
        """
        return self.best_translation.title

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<AbstractContentModel: AbstractContentModel object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the content object
        :rtype: str
        """
        class_name = type(self).__name__
        return f"<{class_name} (id: {self.id}, region: {self.region.slug}, slug: {self.best_translation.slug})>"

    class Meta:
        #: This model is an abstract base class
        abstract = True
