from zipfile import ZipFile
from bs4 import BeautifulSoup, NavigableString, Tag
import os
import uuid
import shutil

from django.utils.text import slugify

from cms.models import Page, PageTranslation

XLIFF_TAG = 'xliff'
XLIFF_SRC_LANG_ATTRIBUTE_NAME = 'srcLang'
XLIFF_TRG_LANG_ATTRIBUTE_NAME = 'trgLang'

PAGE_XLIFF_TEMPLATE = '''
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.0" srcLang="{src_lang}" trgLang="{trg_lang}">
    <page id="{page_id}">
        {title}
        {text}
    </page>
</xliff>
'''
PAGE_TAG = 'page'
PAGE_TITLE_TAG = 'page-title'
PAGE_TITLE_BEGIN_TAG = '<page-title>'
PAGE_TITLE_END_TAG = '</page-title>'
PAGE_TITLE_TEMPLATE = '''<page-title>{0}</page-title>'''

PAGE_TEXT_TAG = 'page-text'
PAGE_TEXT_BEGIN_TAG = '<page-text>'
PAGE_TEXT_END_TAG = '</page-text>'
PAGE_TEXT_TEMPLATE = '<page-text>{0}</page-text>'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLIFFS_DIR = os.path.join(BASE_DIR, 'xliffs')

TRANSLATION_UNIT_TEMPLATE = '''
    <unit>
        <segment>
            <source>{0}</source>
            <target>{1}</target>
        </segment>
    </unit>
'''
ENGLISH_LANGUAGE_CODE = 'en-us'

class XliffValidationException(Exception):
    pass


class PageXliff:
    def __init__(self, page_id, language_code, title, text):
        self.page_id = page_id
        self.language_code = language_code
        self.title = title
        self.text =text


class PageXliffConverter:
    @staticmethod
    def _add_navigable_string_to_empty_tag(soup):
        for el in list(soup.descendants):
            if type(el) == Tag and len(list(el.children)) == 0 and el.name not in ('br',):
                el.append(NavigableString(' '))

    @staticmethod
    def _replace_all_navigable_strings(soup):
        for el in list(soup.descendants):
            if type(el) == NavigableString:
                el.replaceWith(NavigableString('###'))


    @staticmethod
    def _trim_tag_navigable_string(element):
        for child in list(element.children):
            if type(child) == NavigableString:
                child.replaceWith(NavigableString(child.string.strip()))

    @staticmethod
    def _trim_unit_source_target_tag_navigable_string(source_data):
        bs = BeautifulSoup(source_data, 'xml')
        elements = []
        elements.extend(list(bs.find_all('source')))
        elements.extend(list(bs.find_all('target')))
        for element in elements:
            PageXliffConverter._trim_tag_navigable_string(element)

        return str(bs.find())

    @staticmethod
    def _compare_structure_and_return_source_target(source, target):
        if target is None:
            return False, source, target

        source_soup = BeautifulSoup(source, 'xml')
        target_soup = BeautifulSoup(target, 'xml')
        source_prettify = source_soup.prettify()
        target_prettify = target_soup.prettify()
        PageXliffConverter._add_navigable_string_to_empty_tag(source_soup)
        PageXliffConverter._add_navigable_string_to_empty_tag(target_soup)
        PageXliffConverter._replace_all_navigable_strings(source_soup)
        PageXliffConverter._replace_all_navigable_strings(target_soup)

        comparing_source = source_soup.prettify()
        comparing_target = target_soup.prettify()

        return comparing_source == comparing_target, source_prettify, target_prettify

    @staticmethod
    def _replace_navigable_string_with_unit(ns_element, source, target=''):
        if source:
            unit = TRANSLATION_UNIT_TEMPLATE.format(source, target)
            temp_soup = BeautifulSoup(unit, 'xml')
            ns_element.replaceWith(temp_soup.find())

    @staticmethod
    def _replace_source_target_unit(source_element, target_element):
        source_children = list(source_element.children)
        target_children = list(target_element.children)
        tag_elements = []
        for source_child, target_child in zip(source_children, target_children):
            if type(source_child) == NavigableString and type(target_child) == NavigableString:
                PageXliffConverter._replace_navigable_string_with_unit(
                    source_child, source_child.string.strip(), target_child.string.strip())
            else:
                tag_elements.append((source_child, target_child,))

        for source_tag, target_tag in tag_elements:
            PageXliffConverter._replace_source_target_unit(source_tag, target_tag)

    @staticmethod
    def _replace_source_unit(element):
        children = list(element.children)
        tag_elements = []
        for child in children:
            if type(child) == NavigableString:
                PageXliffConverter._replace_navigable_string_with_unit(child, child.string.strip())
            else:
                tag_elements.append(child)

        for tag in tag_elements:
            PageXliffConverter._replace_source_unit(tag)

    def html_to_xliff(self, source,  target=None):
        compare_result, compare_source, compare_target = self._compare_structure_and_return_source_target(
            source=source,
            target=target
        )
        source_soup = BeautifulSoup(compare_source, 'xml')
        if compare_result:
            target_soup = BeautifulSoup(compare_target, 'xml')
            self._replace_source_target_unit(source_soup, target_soup)
        else:
            self._replace_source_unit(source_soup)
        result = self._trim_unit_source_target_tag_navigable_string(source_soup.find().prettify())
        result = result.replace('<target/>', '<target></target>').replace('<source/>', '<source></source>')
        return result

    def xliff_to_html(self, xliff, target=True):
        bs = BeautifulSoup(xliff, "xml")
        elements = bs.find_all('unit')
        content_tag = 'target'
        if not target:
            content_tag = 'source'

        for element in elements:
            content_element = element.find(content_tag)
            if content_element:
                element.replace_with(NavigableString(content_element.get_text()))

        result = bs.prettify()

        return result.replace('<?xml version="1.0" encoding="utf-8"?>', '')

    def page_translation_to_xliff(self, source_translation_page, target_language_code):
        result = ""
        source_language_code = source_translation_page.language.code
        if source_translation_page and source_language_code != target_language_code:
            target_translation_page = source_translation_page.page.get_translation(target_language_code)
            if target_translation_page:
                title = self.html_to_xliff(
                    PAGE_TITLE_TEMPLATE.format(source_translation_page.title),
                    PAGE_TITLE_TEMPLATE.format(target_translation_page.title)
                )
                text = self.html_to_xliff(
                    PAGE_TEXT_TEMPLATE.format(source_translation_page.text),
                    PAGE_TEXT_TEMPLATE.format(target_translation_page.text)
                )
            else:
                title = self.html_to_xliff(
                    PAGE_TITLE_TEMPLATE.format(source_translation_page.title)
                )
                text = self.html_to_xliff(
                    PAGE_TEXT_TEMPLATE.format(source_translation_page.text)
                )

            result = PAGE_XLIFF_TEMPLATE.format(src_lang=source_language_code,
                                                trg_lang=target_language_code,
                                                page_id=source_translation_page.page.id,
                                                title=title,
                                                text=text)
        return result

    def xliff_to_page_xliff(self, xliff, target=True):
        bs = BeautifulSoup(xliff, 'xml')
        xliff_element = bs.find(XLIFF_TAG)
        page_xliff = None
        error_messages = []
        if xliff_element and 'srcLang' in xliff_element.attrs and 'trgLang' in xliff_element.attrs:
            language_code = xliff_element['srcLang']
            if target:
                language_code = xliff_element['trgLang']
            page_element = xliff_element.find(PAGE_TAG)
            if page_element and 'id' in page_element.attrs:
                page_id = page_element['id']
                title_element = page_element.find(PAGE_TITLE_TAG)
                text_element = page_element.find(PAGE_TEXT_TAG)

                if title_element and text_element:
                    title = self.xliff_to_html(title_element.prettify(), target=target)
                    title = title.replace(PAGE_TITLE_BEGIN_TAG, '').replace(PAGE_TITLE_END_TAG, '').strip()

                    text = self.xliff_to_html(text_element.prettify(), target=target)
                    temp_bs = BeautifulSoup(text, 'xml')
                    temp_strings = list(temp_bs.stripped_strings)
                    if len(temp_strings):
                        text = text.replace(PAGE_TEXT_BEGIN_TAG, '').replace(PAGE_TEXT_END_TAG, '').strip()
                    else:
                        text = ''
                    page_xliff = PageXliff(page_id=page_id, language_code=language_code, title=title, text=text)
                else:
                    error_messages.append('cannot find page title or text tag')

            else:
                error_messages.append('cannot find page tag or page id not exists.')
        else:
            error_messages.append('cannot find xliff tag or srcLang and trgLang not exists.')

        if len(error_messages):
            raise XliffValidationException('\n'.join(error_messages))

        return page_xliff


class PageXliffHelper:
    def __init__(self, converter=None):
        if converter:
            self.converter = converter
        else:
            self.converter = PageXliffConverter()

    @staticmethod
    def save_file(content, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def export_page_translation_xliff(self, source_translation_page, target_language_code, filename=None):

        if not filename:
            filename = 'page_{0}_{1}_{2}.xliff'.format(source_translation_page.page.id,
                                                       source_translation_page.language.code,
                                                       target_language_code)

        file_path = None

        xliff_content = self.converter.page_translation_to_xliff(source_translation_page, target_language_code)

        if xliff_content:
            file_path = os.path.join(XLIFFS_DIR, str(uuid.uuid4()), filename)
            self.save_file(xliff_content, file_path)

        return file_path

    @staticmethod
    def _create_zip_file(source_file_paths, zip_file_path):
        os.makedirs(os.path.dirname(zip_file_path), exist_ok=True)
        with ZipFile(zip_file_path, 'w') as zip_file:
            for file_path in source_file_paths:
                if os.path.isfile(file_path):
                    file_name = file_path.split(os.sep)[-1]
                    zip_file.write(file_path, arcname=file_name)

    @staticmethod
    def delete_tmp_in_xliff_folder(file_path):
        if file_path.startswith(XLIFFS_DIR):
            folder = os.path.dirname(file_path)
            files = os.listdir(folder)
            if len(files) == 1 and os.path.join(folder, files[0]) == file_path:
                shutil.rmtree(folder)

    @staticmethod
    def _get_xliff_directions(languages, default_language):
        source_target_langs = []
        english_language = None
        for language in languages:
            if language.code == ENGLISH_LANGUAGE_CODE:
                english_language = language
                break

        if default_language.code == ENGLISH_LANGUAGE_CODE or not english_language:
            for language in languages:
                if language != default_language:
                    source_target_langs.append((default_language.code, language.code,))
        else:
            for language in languages:
                if language != default_language:
                    if language.code == ENGLISH_LANGUAGE_CODE:
                        source_target_langs.append((default_language.code, ENGLISH_LANGUAGE_CODE,))
                    else:
                        source_target_langs.append((ENGLISH_LANGUAGE_CODE, language.code,))

        return source_target_langs


    def export_page_xliffs_to_zip(self, page):
        zip_file_path = None
        xliff_files = []
        if page and len(page.site.languages) > 1:
            page_translations = list(page.page_translations.all())
            language_page_translation_map = {}
            for page_translation in page_translations:
                language_page_translation_map[page_translation.language.code] = page_translation

            default_language = page.site.default_language
            if not default_language or default_language.code not in language_page_translation_map:
                default_language = page_translations[0].language
                source_page_translation = page_translations[0]
            elif default_language.code in language_page_translation_map:
                source_page_translation = language_page_translation_map[default_language.code]

            xliff_directions = self._get_xliff_directions(page.site.languages, default_language)

            for source_language_code, target_language_code in xliff_directions:
                if source_language_code in language_page_translation_map:
                    xliff_files.append(
                        self.export_page_translation_xliff(language_page_translation_map[source_language_code],
                                                           target_language_code))
                elif target_language_code != source_page_translation.language.code:
                    xliff_files.append(
                        self.export_page_translation_xliff(source_page_translation, target_language_code))

            zip_file_name = "page_{0}.zip".format(page.id)
            zip_file_path = os.path.join(XLIFFS_DIR, 'pages', str(uuid.uuid4()), zip_file_name)
            self._create_zip_file(xliff_files, zip_file_path)

            # delete xliff files after created zip file
            [self.delete_tmp_in_xliff_folder(xliff_file) for xliff_file in xliff_files]

        return zip_file_path

    @staticmethod
    def _get_page_translation_slug(title):
        slug = slugify(title)
        if PageTranslation.objects.filter(slug=slug).exists():
            old_slug = slug
            i = 1
            while True:
                i += 1
                slug = old_slug + '-' + str(i)
                if not PageTranslation.objects.filter(slug=slug).exists():
                    break

        return slug

    @staticmethod
    def save_page_xliff(page_xliff, user):
        result = False
        try:
            if page_xliff.page_id and page_xliff.title and page_xliff.text and page_xliff.language_code:
                page = Page.objects.get(id=int(page_xliff.page_id))
                page_translation = page.get_translation(page_xliff.language_code)
                if page_translation:
                    page_translation.title = page_xliff.title
                    page_translation.text = page_xliff.text
                    page_translation.slug = PageXliffHelper._get_page_translation_slug(page_xliff.title)

                elif len(page.languages) > 0:
                    target_language = None
                    for language in page.site.languages:
                        if page_xliff.language_code == language.code:
                            target_language = language
                            break
                    if target_language:
                        slug = PageXliffHelper._get_page_translation_slug(page_xliff.title)
                        source_page_translation = list(page.page_translations.all())[0]
                        page_translation = PageTranslation.objects.create(
                            slug=slug,
                            title=page_xliff.title,
                            text=page_xliff.text,
                            status=source_page_translation.status,
                            language=target_language,
                            public=source_page_translation.public,
                            page=page,
                            creator=user
                        )

                if page_translation:
                    page_translation.save()
                    result = True

        except Exception as ex:
            pass

        return result

    def import_xliff_file(self, file_path, user):
        result = False
        if file_path.startswith(XLIFFS_DIR) and file_path.endswith(('.xlf', '.xliff')) and os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                xliff_content = f.read()
                page_xliff = self.converter.xliff_to_page_xliff(xliff_content)
                if page_xliff:
                    result = self.save_page_xliff(page_xliff, user)

        return result

    def import_xliffs_zip_file(self, zip_file_path, user):
        results = []

        if zip_file_path.startswith(XLIFFS_DIR) and zip_file_path.endswith('.zip') and os.path.isfile(zip_file_path):
            with ZipFile(zip_file_path, 'r') as zip_file:
                for file_name in zip_file.namelist():
                    if file_name.endswith(('.xliff', '.xlf',)):
                        with zip_file.open(file_name) as f:
                            try:
                                xliff_content = f.read()
                                page_xliff = self.converter.xliff_to_page_xliff(xliff_content)
                                if page_xliff:
                                    results.append((file_name, self.save_page_xliff(page_xliff, user),))
                                else:
                                    results.append((file_name, False,))
                            except XliffValidationException as ex:
                                results.append((file_name, False,))
        return results
