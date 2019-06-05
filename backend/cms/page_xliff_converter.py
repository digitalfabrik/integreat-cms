from bs4 import BeautifulSoup, NavigableString
import re

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