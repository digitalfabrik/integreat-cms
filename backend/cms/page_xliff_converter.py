from zipfile import ZipFile
from bs4 import BeautifulSoup, NavigableString
import re
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
    def _find_html_contents(html):
        contents = []
        if html:
            bs = BeautifulSoup(html, "html.parser")

            contents = list(bs.stripped_strings)

        return contents

    @staticmethod
    def _replace_html_contents_to_xliff_units(source_html, source_target_contents):
        template = '''
        <unit>
            <segment>
                <source>{0}</source>
                <target>{1}</target>
            </segment>
        </unit>
        '''
        result = source_html
        for st_content in source_target_contents:
            result = re.sub(r'\s*({0})\s*'.format(re.escape(st_content[0])),
                            template.format(st_content[0], st_content[1]), result)

        return result

    def html_to_xliff(self, source_html,  target_html=None):
        source_contents = self._find_html_contents(source_html)
        target_contents = self._find_html_contents(target_html)

        if len(source_contents) != len(target_contents):
            target_contents = [''] * len(source_contents)

        source_target_contents = zip(source_contents, target_contents)

        return self._replace_html_contents_to_xliff_units(source_html, source_target_contents)

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
        with open(file_path, 'w') as file:
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
    def _delete_file(file_path):
        folder = os.path.dirname(file_path)
        files = os.listdir(folder)
        if len(files) == 1 and os.path.join(folder, files[0]) == file_path:
            shutil.rmtree(folder)

    def export_page_xliffs_to_zip(self, page):
        zip_file_path = None
        if page and len(page.site.languages) > 1:
            page_translations = list(page.page_translations.all())

            site_default_language = page.site.default_language
            languages = page.site.languages

            source_page_translation = page.get_translation(site_default_language.code)
            if not source_page_translation:
                source_page_translation = page_translations[0]
            source_page_language = source_page_translation.language

            xliff_files = []
            for language in languages:
                if language.code != source_page_language.code:
                    xliff_files.append(self.export_page_translation_xliff(source_page_translation, language.code))

            zip_file_name = "page_{0}.zip".format(page.id)
            zip_file_path = os.path.join(XLIFFS_DIR, 'pages', str(uuid.uuid4()), zip_file_name)
            self._create_zip_file(xliff_files, zip_file_path)

            # delete xliff files after created zip file
            [self._delete_file(xliff_file) for xliff_file in xliff_files]

        return zip_file_path

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
                elif len(page.languages) > 0:
                    target_language = None
                    for language in page.site.languages:
                        if page_xliff.language_code == language.code:
                            target_language = language
                            break
                    if target_language:
                        slug = slugify(page_xliff.title)
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
            with open(file_path, 'r') as f:
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
                    with zip_file.open(file_name) as f:
                        xliff_content = f.read()
                        page_xliff = self.converter.xliff_to_page_xliff(xliff_content)
                        if page_xliff:
                            results.append((file_name, self.save_page_xliff(page_xliff, user),))
                        else:
                            results.append((file_name, False,))
        return results
