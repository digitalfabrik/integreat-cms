"""
This module contains helpers for the translation process.
"""
import logging
import re

from django.utils.html import format_html, format_html_join
from django.utils.text import format_lazy

from ..constants import machine_translation_permissions as mt_perms

logger = logging.getLogger(__name__)


def gettext_many_lazy(*strings):
    r"""
    This function is a wrapper for :func:`django.utils.text.format_lazy` for the special case that the given strings
    should be concatenated with a space in between. This is useful for splitting lazy translated strings by sentences
    which improves the translation memory.

    :param \*strings: A list of lazy translated strings which should be concatenated
    :type \*strings: list

    :return: A lazy formatted string
    :rtype: str
    """
    fstring = ("{} " * len(strings)).strip()
    return format_lazy(fstring, *strings)


def translate_link(message, attributes):
    """
    Translate a link with keeping the HTML tags and still escaping all unknown parts of the message

    :param message: The translated message that contains the link placeholder ``<a>{link_text}</a>``
    :type message: str

    :param attributes: A dictionary of attributes for the link
    :type attributes: dict

    :return: A correctly escaped formatted string with the translated message and the HTML link
    :rtype: str
    """
    # Split the message at the link text
    before, link_text, after = re.split(r"<a>(.+)</a>", str(message))
    # Format the HTML
    return format_html(
        "{}<a {}>{}</a>{}",
        before,
        format_html_join(" ", "{}='{}'", attributes.items()),
        link_text,
        after,
    )


def mt_to_lang_is_permitted(region, target_lang_slug):
    """
    Checks if translation into a given language is allowed

    :param region: the region attempting to machine translate
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :param target_lang_slug: slug of the MT target language
    :type target_lang_slug: str

    :return: if the translation is permitted
    :rtype: bool
    """
    target_lang = region.language_node_by_slug[target_lang_slug]

    if target_lang.is_root():
        logger.debug(
            "Machine translations are disabled for the default language %r in %r.",
            target_lang,
            region,
        )
        return False

    if not target_lang.machine_translation_enabled:
        logger.debug(
            "Machine translations are disabled for %r in %r.", target_lang, region
        )
        return False

    return True


def mt_is_permitted(region, user, content_type, target_lang_slug=None):
    """
    Checks if a machine translation is permitted, i.e. if for the
    given region, MT of the given content type is allowed and
    MT into the target language is enabled for the requesting user.

    :param region: the region attempting to machine translate
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :param user: the user requesting the translation
    :type user: ~django.contrib.auth.models.User

    :param content_type: type of content which would be translated
    :type content_type: ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel

    :param target_lang_slug: slug of the MT target language
    :type target_lang_slug: str

    :return: if the translation is permitted
    :rtype: bool
    """
    permission_settings = {
        "events": (region.machine_translate_events, "cms.change_event"),
        "pages": (region.machine_translate_pages, "cms.change_page"),
        "pois": (region.machine_translate_pois, "cms.change_poi"),
    }

    mt_perms_setting, required_perm = permission_settings[content_type]

    if mt_perms_setting == mt_perms.NO_ONE:
        logger.debug(
            "Machine translations are disabled for content type %r in %r.",
            content_type,
            region,
        )
        return False

    mt_perm = "cms.manage_translations"
    if mt_perms_setting == mt_perms.MANAGERS and not user.has_perm(mt_perm):
        logger.debug(
            "Machine translations are only enabled for content type %r in %r for users with the permission %r.",
            content_type,
            region,
            mt_perm,
        )
        return False

    if not user.has_perm(required_perm):
        logger.debug(
            "Machine translations are only enabled for content type %r in %r for users with the permission %r.",
            content_type,
            region,
            required_perm,
        )
        return False

    return (
        mt_to_lang_is_permitted(region, target_lang_slug) if target_lang_slug else True
    )
