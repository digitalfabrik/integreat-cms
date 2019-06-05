from bs4 import BeautifulSoup, NavigableString
import re


class PageXliffConverter:

    @staticmethod
    def find_html_contents(html):
        contents = []
        if html:
            bs = BeautifulSoup(html, "html.parser")

            contents = list(bs.stripped_strings)

        return contents

    @staticmethod
    def replace_contents_to_xliff_units(source_html, source_target_contents):
        template = '''
        <unit>
            <segment >
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
        source_contents = self.find_html_contents(source_html)
        target_contents = self.find_html_contents(target_html)

        if len(source_contents) != len(target_contents):
            target_contents = [''] * len(source_contents)

        source_target_contents = zip(source_contents, target_contents)

        return self.replace_contents_to_xliff_units(source_html, source_target_contents)

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

    def page_to_xliff(self, page):
        pass

    def xliff_to_page(self, xliff):
        pass
