import os
import uuid
import datetime
import difflib

from zipfile import ZipFile
from lxml import etree
from django.utils.text import slugify

from .models import Page, PageTranslation, Language


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLIFFS_DIR = os.path.join(BASE_DIR, "xliffs")


class TranslationXliffConverter:  # pylint: disable=R0902
    """
    Class to handle transition between XLIFF 2.0 XML files and PageTranslation model
    """

    PAGE_XLIFF_TEMPLATE = (
        b'<?xml version="1.0" encoding="utf-8" standalone="no"?>'
        b'<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.0"><file></file></xliff>'
    )

    def __init__(self, src_lang=None, tgt_lang=None, xliff_code=None):
        """
        Builds an LXML ETree from either the template or xliff_code parameter

        :param src_lang: source language of translation
        :type src_lang: ~cms.models.languages.language.Language

        :param tgt_lang: target language of translation
        :type tgt_lang: ~cms.models.languages.language.Language

        :param xliff_code: XML Code of XLIFF file to import
        :type xliff_code: str
        """
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.elem_files = None
        self.elem_title = None
        self.elem_content = None
        self.elem_trans_version = None
        self.page_id = None

        if xliff_code is None:
            self.xliff = etree.fromstring(self.PAGE_XLIFF_TEMPLATE)
            self.add_language_attributes()
        else:
            self.xliff = etree.fromstring(xliff_code)
        self.parse_xliff_meta()
        self.parse_xliff_content()

    def parse_xliff_meta(self):
        """
        Get meta information from XLIFF file
        """
        file_elements = self.xliff.xpath(
            "//x:file", namespaces={"x": "urn:oasis:names:tc:xliff:document:2.0"}
        )
        if len(file_elements) == 1:
            self.elem_file = file_elements[0]

        if self.tgt_lang is None:
            tgt_langs = Language.objects.filter(slug=self.xliff.attrib["trgLang"])
            if len(tgt_langs) == 1:
                self.tgt_lang = tgt_langs[0]

        if self.src_lang is None:
            src_langs = Language.objects.filter(slug=self.xliff.attrib["srcLang"])
            if len(src_langs) == 1:
                self.src_lang = src_langs[0]

        if self.elem_file is not None and "original" in self.elem_file.attrib:
            self.page_id = int(self.elem_file.attrib["original"])

    def validate_meta_info(self):
        """
        Validate if XLIFF meta information is present

        :return: all required meta data (languages, page id, file element) available
        :rtype: bool
        """
        if (
            self.elem_file is None
            or self.tgt_lang is None
            or self.src_lang is None
            or self.page_id is None
        ):
            return False
        return True

    def parse_xliff_content(self):
        """
        Extract content elements from xliff
        """
        namespaces = {"x": "urn:oasis:names:tc:xliff:document:2.0"}

        xpath_title = '//x:file/x:unit[@id="title"]/x:segment/x:target'
        xpath_content = '//x:file/x:unit[@id="content"]/x:segment/x:target'
        xpath_trans_version = '//x:file/x:notes/x:note[@id="tgt_version"]'

        elem_title = self.xliff.xpath(xpath_title, namespaces=namespaces)
        if len(elem_title) == 1:
            self.elem_title = elem_title[0]
        elem_content = self.xliff.xpath(xpath_content, namespaces=namespaces)
        if len(elem_content) == 1:
            self.elem_content = elem_content[0]
        elem_trans_version = self.xliff.xpath(
            xpath_trans_version, namespaces=namespaces
        )
        if len(elem_trans_version) == 1:
            self.elem_trans_version = elem_trans_version[0]

    def validate_content(self):
        """
        Validate if content data is present

        :return: content and title elements are available
        :rtype: bool
        """
        if (
            self.elem_title is None
            or self.elem_content is None
            or self.elem_trans_version is None
        ):
            return False
        return True

    def add_language_attributes(self):
        """
        If possible, add the srcLang and trgLang attributes to the xliff element

        :return: language attributes were added
        :rtype: bool
        """
        if self.src_lang is not None and self.tgt_lang is not None:
            self.xliff.attrib["srcLang"] = self.src_lang.slug
            self.xliff.attrib["trgLang"] = self.tgt_lang.slug
            return True
        return False

    def translation_to_xliff(self, page_id, src_trans, tgt_trans, xliff_id):
        """
        Create a XLIFF that contains a page translation
        Add origin attribute with page id as value to file element. as this id is unique
        across all regions, it can be used to import a XLIFF file.

        :param page_id: the id of the page to which the translation is related
        :type page_id: int

        :param src_trans: source language page translation
        :type src_trans: ~cms.models.pages.page_translation.PageTranslation

        :param tgt_trans: target language page translation
        :type tgt_trans: ~cms.models.pages.page_translation.PageTranslation

        :param xliff_id: XLIFF ID
        :type xliff_id: str

        :return: UTF-8 encoded XML
        :rtype: str
        """
        self.elem_file.attrib["original"] = str(page_id)
        notes = {
            "translation_id": xliff_id,
            "source_slug": src_trans.slug,
            "src_version": src_trans.version,
            "tgt_version": tgt_trans.version,
            "page_id": page_id,
        }
        self.add_notes(notes)
        self.add_translation_unit("title", src_trans.title, tgt_trans.title)
        self.add_translation_unit("content", src_trans.text, tgt_trans.text)
        return self.get_xml().decode("utf-8")

    def add_notes(self, notes):
        """
        Add notes section with additional information to XLIFF

        :param notes: key-value-pairs of notes
        :type notes: dict
        """
        notes_element = etree.SubElement(self.elem_file, "notes")

        for item in notes:
            note = etree.SubElement(notes_element, "note")
            note.attrib["id"] = item
            note.text = str(notes[item])

    def add_translation_unit(self, unit_id, source_text, target_text):
        """
        Add a translation unit to the file element

        :param unit_id: value for the unit id attribute
        :type unit_id: str

        :param source_text: source text to be translated
        :type source_text: str

        :param target_text: already available translation
        :type target_text: str
        """
        unit = etree.SubElement(self.elem_file, "unit")
        unit.attrib["id"] = unit_id
        segment = etree.SubElement(unit, "segment")
        source = etree.SubElement(segment, "source")
        source.text = etree.CDATA(source_text)
        target = etree.SubElement(segment, "target")
        target.text = etree.CDATA(target_text)

    def xliff_to_translation_data(self):
        """
        Read a XLIFF file that contains a page translation

        :return: if successful, the content for the translation
        :rtype: dict or None
        """
        if not self.validate_content() or not self.validate_meta_info():
            return None

        return {
            "title": self.elem_title.text,
            "content": self.elem_content.text,
            "page_id": self.page_id,
            "tgt_lang_slug": self.tgt_lang.slug,
            "src_lang_slug": self.src_lang.slug,
            "tgt_version": self.elem_trans_version.text,
        }

    def get_xml(self):
        """
        Turn LXML Element Tree to readable XML code

        :return: pretty printed XML source code
        :rtype: str
        """
        return etree.tostring(self.xliff, pretty_print=True)


class PageXliffHelper:
    """
    Wrapper and helper methods for reading/writing XLIFF files and saving PageTranslation
    """

    def __init__(self, src_lang=None, tgt_lang=None):
        """
        :param src_lang: source language of translation
        :type src_lang: ~cms.models.languages.language.Language

        :param tgt_lang: target language of translation
        :type tgt_lang: ~cms.models.languages.language.Language
        """
        if src_lang is not None:
            self.src_lang = src_lang
        if tgt_lang is not None:
            self.tgt_lang = tgt_lang

    @staticmethod
    def save_file(content, file_path):
        """
        Write text to file

        :param content: content of file
        :type content: str

        :param file_path: path to newly created file
        :type file_path: str
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

    def export_page_translation_xliff(self, page):
        """
        Create XLIFF file for source page translation and target language

        :param page: page of translation that should be exported
        :type page: ~cms.models.pages.page.Page

        :return: file path to XLIFF file
        :rtype: str or None
        """
        converter = TranslationXliffConverter(self.src_lang, self.tgt_lang)

        src_trans = PageTranslation.objects.filter(
            page=page, language=self.src_lang
        ).first()
        if not src_trans:
            return None
        tgt_trans = PageTranslation.objects.filter(
            page=page, language=self.tgt_lang
        ).first()
        if not tgt_trans:
            tgt_trans = PageTranslation(
                title="",
                text="",
                status=src_trans.status,
                language=self.tgt_lang,
                page=page,
            )

        region_slug = page.region.slug
        slug = src_trans.slug

        # properties that make a translation unique: page id, target language, source version
        xliff_id = (
            self.tgt_lang.slug + "_" + str(page.id) + "_" + str(src_trans.version)
        )

        filename = f"{region_slug}_{self.src_lang.slug}__{xliff_id}__{slug}.xliff"
        xliff_content = converter.translation_to_xliff(
            page.id, src_trans, tgt_trans, xliff_id
        )

        if xliff_content:
            file_path = os.path.join(XLIFFS_DIR, str(uuid.uuid4()), filename)
            self.save_file(xliff_content, file_path)
            return file_path
        return None

    @staticmethod
    def _create_zip_file(source_file_paths, zip_file_path):
        """
        Create zip file from list of source files

        :param source_file_paths: list of files to be zipped
        :type source_file_paths: list

        :param zip_file_path: path to zipped file
        :type zip_file_path: str
        """
        os.makedirs(os.path.dirname(zip_file_path), exist_ok=True)
        with ZipFile(zip_file_path, "w") as zip_file:
            for file_path in source_file_paths:
                if os.path.isfile(file_path):
                    file_name = file_path.split(os.sep)[-1]
                    zip_file.write(file_path, arcname=file_name)

    def pages_to_zipped_xliffs(self, region, pages):
        """
        Export a list of page IDs to a zip file containing XLIFFs for a specified target language

        :param region: region from which the XLIFFs should be exported
        :type region: ~cms.models.regions.region.Region

        :param pages: list of pages which should be translated
        :type pages: list [ ~cms.models.pages.page.Page ]

        :return: The path of the generated zip file
        :rtype: str
        """
        xliff_paths = []
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        zip_name = (
            f"{region.slug}_{timestamp}_{self.src_lang.slug}_{self.tgt_lang.slug}.zip"
        )
        for page in pages:
            xliff_path = self.export_page_translation_xliff(page)
            if xliff_path is not None:
                xliff_paths.append(xliff_path)
        zip_path = os.path.join(XLIFFS_DIR, str(uuid.uuid4()), zip_name)
        self._create_zip_file(xliff_paths, zip_path)
        return zip_path

    @staticmethod
    def _get_page_translation_slug(title):
        """
        Create slug (readable unique identifier) for page translation from title

        :param title: title of page translation
        :type title: str

        :return: slug
        :rtype: str
        """
        slug = slugify(title)
        if PageTranslation.objects.filter(slug=slug).exists():
            old_slug = slug
            i = 1
            while True:
                i += 1
                slug = old_slug + "-" + str(i)
                if not PageTranslation.objects.filter(slug=slug).exists():
                    break
        return slug

    @staticmethod
    def save_page_translation(trans_fields, user):
        """
        Save XLIFF input to page translation

        :param trans_fields: translated fields extracted from XLIFF file
        :type trans_fields: dict

        :param user: author of translations
        :type user: ~django.contrib.auth.models.User

        :return: failure/success for each page or overall failed
        :rtype: list or bool
        """
        page = Page.objects.filter(id=int(trans_fields["page_id"])).first()
        tgt_lang = Language.objects.filter(slug=trans_fields["tgt_lang_slug"]).first()
        src_lang = Language.objects.filter(slug=trans_fields["src_lang_slug"]).first()
        if tgt_lang is None or src_lang is None or page is None:
            return False
        tgt_trans = PageTranslation.objects.filter(page=page, language=tgt_lang).first()
        src_trans = PageTranslation.objects.filter(page=page, language=src_lang).first()
        if src_trans is None:
            return False
        if tgt_trans is None:
            tgt_trans = PageTranslation(language=tgt_lang, page=page, version=0)
        else:
            tgt_trans.version = tgt_trans.version + 1
        tgt_trans.creator = user
        tgt_trans.title = trans_fields["title"]
        tgt_trans.text = trans_fields["content"]
        tgt_trans.slug = PageXliffHelper._get_page_translation_slug(tgt_trans.title)
        tgt_trans.currently_in_translation = False
        if tgt_trans.save():
            return True
        return False

    def import_xliff_files(self, xliff_paths, user):
        """
        Import single (usually translated) XLIFF file and
        save to page translation.

        :param xliff_paths: paths to XLIFF files
        :type xliff_paths: list [ str ]

        :param user: author of page
        :type user: int

        :return: failure/success
        :rtype: bool
        """
        result = []
        for xliff_path in xliff_paths:
            if (
                xliff_path.startswith(XLIFFS_DIR)
                and xliff_path.endswith((".xlf", ".xliff"))
                and os.path.isfile(xliff_path)
            ):
                with open(xliff_path, "r", encoding="utf-8") as f:
                    xliff_content = f.read()
                    converter = TranslationXliffConverter(xliff_code=xliff_content)
                    trans_fields = converter.xliff_to_translation_data()
                    if trans_fields is not None:
                        result.append(
                            (xliff_path, self.save_page_translation(trans_fields, user))
                        )
                    else:
                        result.append((xliff_path, False))
        return result

    @staticmethod
    def extract_zip_file(zip_file_path):
        """
        Extract zip file and return file paths of content

        :param zip_file_path: path to zip file
        :type zip_file_path: str

        :return: list of filenames
        :rtype: list
        """
        file_paths = []
        with ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(os.path.dirname(zip_file_path))
            for file_name in zip_ref.namelist():
                file_paths.append(
                    os.path.join(os.path.dirname(zip_file_path), file_name)
                )
        return file_paths

    def generate_xliff_import_diff(self, xliff_paths):
        """
        Generate diff between XLIFF content and current translation content

        :param xliff_paths: list of paths to XLIFF files
        :type xliff_paths: [ str ]

        :return: dictionaries containing diffs between XLIFF and current translation versions or an error message
        :rtype: list [ dict ]
        """
        results = []
        for xliff_path in xliff_paths:
            if xliff_path.endswith((".xlf", ".xliff")) and os.path.isfile(xliff_path):
                with open(xliff_path, "r", encoding="utf-8") as f:
                    xliff_content = f.read()
                    converter = TranslationXliffConverter(xliff_code=xliff_content)
                    trans_fields = converter.xliff_to_translation_data()
                    if trans_fields is None:
                        continue
                    diff = self.generate_translation_diff(
                        trans_fields, os.path.basename(xliff_path)
                    )
                    if diff is None:
                        results.append(
                            {
                                "error": True,
                                "page_id": trans_fields["page_id"],
                                "title": trans_fields["title"],
                                "tgt_lang_slug": trans_fields["tgt_lang_slug"],
                            }
                        )
                    else:
                        results.append(diff)
        return results

    @staticmethod
    def generate_translation_diff(trans_fields, xliff_name):
        """
        Generate diff to current translation from translation fields dictionary

        :param trans_fields: content extracted from XLIFF
        :type trans_fields: dict

        :param xliff_name: file name of XLIFF
        :type xliff_name: str

        :return: dictionary containing diff between XLIFF and current translation version
        :rtype: dict
        """
        page = Page.objects.filter(id=int(trans_fields["page_id"])).first()
        tgt_lang = Language.objects.filter(slug=trans_fields["tgt_lang_slug"]).first()
        if tgt_lang is None or page is None:
            return None
        tgt_trans = PageTranslation.objects.filter(page=page, language=tgt_lang).first()
        if tgt_trans is None:
            tgt_trans = PageTranslation()
            tgt_trans.title = ""
            tgt_trans.text = ""

        old_lines_content = tgt_trans.text.splitlines()
        new_lines_content = trans_fields["content"].splitlines()
        result_diff = {
            "title": tgt_trans.title,
            "title_diff": "\n".join(
                difflib.unified_diff(
                    [tgt_trans.title],
                    [trans_fields["title"]],
                    "cms",
                    "xliff",
                    lineterm="",
                )
            ),
            "content_diff": "\n".join(
                difflib.unified_diff(
                    old_lines_content, new_lines_content, "cms", "xliff", lineterm=""
                )
            ),
            "current_version_newer": tgt_trans.version
            > int(trans_fields["tgt_version"]),
            "xliff_name": xliff_name,
        }
        return result_diff

    @staticmethod
    # pylint: disable=unused-argument
    def post_translation_state(pages, language_slug, translation_state):
        """Update translation state according to parameter

        :param pages: list of pages
        :type pages: list
        :param language_slug: language slug of translation
        :type language_slug: str
        :param translation_state: value to set for currently_in_translation
        :type translation_state: bool
        """
        for page in pages:
            if language_slug in [language.slug for language in page.languages]:
                PageTranslation.objects.filter(
                    page__id=page.id, language__slug=language_slug
                ).update(currently_in_translation=translation_state)
