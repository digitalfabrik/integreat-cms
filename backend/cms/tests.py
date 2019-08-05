import os
import re

from zipfile import ZipFile
from bs4 import BeautifulSoup

from django.test import TestCase
from django.contrib.auth.models import User

from .models import Region
from .models import Page
from .models import Language
from .views.regions.region_form import RegionForm
from .views.pages.page_form import PageForm
from .views.languages.language_form import LanguageForm
from .views.language_tree.language_tree_node_form import LanguageTreeNodeForm
from .views.utils.tree_utils import POSITION_CHOICES
from .page_xliff_converter import PageXliffConverter, XliffValidationException, PageXliffHelper, XLIFFS_DIR


# pylint: disable=R0902
class SetupClass(TestCase):
    @staticmethod
    def create_region(region_data):
        region_form = RegionForm(region_data)
        region_form.is_valid()
        region_form.save_region()
        return Region.objects.get(slug=region_data['name'])

    @staticmethod
    def create_language(language_data):
        language_form = LanguageForm(language_data)
        language_form.is_valid()
        language_form.save_language()
        return Language.objects.get(name=language_data['name'])

    @staticmethod
    def create_language_tree_node(language_tree_node_data, region_slug=None):
        language_tree_node_form = LanguageTreeNodeForm(data=language_tree_node_data,
                                                       region_slug=region_slug)
        language_tree_node_form.is_valid()
        return language_tree_node_form.save_language_node()

    @staticmethod
    # pylint: disable=R0913
    def create_page(page_data, user, region_slug, language_code,
                    page_id=None, publish=False, archived=False):
        # TODO: fix form usage to page_form and page_translation_form
        page_form = PageForm(
            page_data,
            page_id=page_id,
            publish=publish,
            archived=archived,
            region_slug=region_slug,
            language_code=language_code,
            user=user
        )
        if page_form.is_valid():
            return page_form.save()
        return None

    def setUp(self):
        self.user = User.objects.create_user('test', 'test@integreat.com', 'test')
        self.region = self.create_region({
            'name': 'demo',
            'events_enabled': True,
            'push_notifications_enabled': True,
            'push_notification_channels': 'channel1 channel2',
            'latitude': 10.0,
            'longitude': 20.0,
            'postal_code': '10000',
            'admin_mail': 'admin@integreat.com',
            'statistics_enabled': False,
            'matomo_url': '',
            'matomo_token': '',
            'matomo_ssl_verify': True,
            'status': Region.ACTIVE,
        })

        self.english = self.create_language({
            'name': 'English',
            'code': 'en-us',
            'text_direction': 'ltr'
        })

        self.deutsch = self.create_language({
            'name': 'Deutsch',
            'code': 'de-de',
            'text_direction': 'ltr'
        })

        self.arabic = self.create_language({
            'name': 'Arabic',
            'code': 'ar-ma',
            'text_direction': 'rtl'
        })

        self.english_node = self.create_language_tree_node(
            language_tree_node_data={
                'language': self.english.id,
                'parent': None,
                'active': True
            }, region_slug='demo'
        )

        self.deutsch_node = self.create_language_tree_node(
            language_tree_node_data={
                'language': self.deutsch.id,
                'parent': self.english_node.id,
                'active': True,
            }, region_slug='demo')

        self.arabic_node = self.create_language_tree_node(
            language_tree_node_data={
                'language': self.arabic.id,
                'parent': self.english_node.id,
                'active': True
            }, region_slug='demo')

        self.page_tunews = self.create_page(
            page_data={
                'title': 'big news',
                'text': '''
                    <p>First Layer</p>
                    <div style="width: 100%;background: #0079ad;text-align: center">
                        hello world
                        <a href="http://tunewsinternational.com/">international test</a>
                        2019-04-05 11:53:44
                    </div>
                ''',
                'status': 'reviewed',
                'position': POSITION_CHOICES[0][0],
                'parent': None,
                'icon': None,
                'public': True
            },
            user=self.user,
            region_slug='demo',
            language_code='en-us',
            publish=True
        )

        self.page_slot_one = self.create_page(
            page_data={
                'title': 'Slot1',
                'text': '''
                <p>Slot 1</p>
                <div style="width: 100%;background: #0079ad;text-align: center">
                    E-news No: 12345 - 
                    <a href="http://tunewsinternational.com/">TüNews INTERNATIONAL</a> 
                    - 2019-04-05 11:53:44
                </div>''',
                'status': 'reviewed',
                'position': POSITION_CHOICES[0][0],
                'parent': self.page_tunews.id,
                'icon': None,
                'public': True
            },
            user=self.user,
            region_slug='demo',
            language_code='en-us',
            publish=True
        )

        self.create_page(
            page_data={
                'title': 'Schlitz1',
                'text': 'zweite Schicht Schlitz eins',
                'status': 'reviewed',
                'position': POSITION_CHOICES[0][0],
                'parent': self.page_tunews.id,
                'icon': None,
                'public': True
            },
            user=self.user,
            page_id=self.page_slot_one.id,
            region_slug='demo',
            language_code='de-de',
            publish=True
        )

        self.page_slot_two = self.create_page(
            page_data={
                'title': 'Slot2',
                'text': 'second layer slot two',
                'status': 'reviewed',
                'position': POSITION_CHOICES[1][0],
                'parent': self.page_tunews.id,
                'icon': None,
                'public': True
            },
            user=self.user,
            region_slug='demo',
            language_code='en-us',
            publish=True
        )

        self.page_tunews_two = self.create_page(
            page_data={
                'title': 'Tunews two',
                'text': 'first layer',
                'status': 'reviewed',
                'position': POSITION_CHOICES[0][0],
                'parent': None,
                'icon': None,
                'public': True
            },
            user=self.user,
            region_slug='demo',
            language_code='en-us',
            publish=True
        )


class LanguageTreeNodeTestCase(SetupClass):
    def test_node_region(self):
        self.assertEqual(self.english_node.region, self.region)

    def test_parent_node(self):
        self.assertEqual(self.deutsch_node.parent, self.english_node)


class PageFormTestCase(SetupClass):
    def test_page(self):
        self.assertEqual(len(self.page_tunews.languages), 1)
        self.assertEqual(len(self.page_slot_one.languages), 2)
        self.assertEqual(len(self.page_slot_two.languages), 1)

        self.assertIsNone(self.page_tunews.get_translation('de-de'))
        self.assertIsNotNone(self.page_slot_one.get_translation('de-de'))

    def test_pages(self):
        pages = Page.get_tree(region_slug=self.region.slug)
        self.assertEqual(len(pages), 4)


EXPECT_PAGE_TUNEWS_XLIFF = '''
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.0" srcLang="en-us" trgLang="de-de">
    <page id="1">
        <page-title>
            <unit>
                <segment >
                    <source>big news</source>
                    <target></target>
                </segment>
            </unit>
        </page-title>  
        <page-text>       
            <p>
                <unit>
                <segment >
                    <source>First Layer</source>
                    <target></target>
                    </segment>
                </unit>
            </p>
            <div style="width: 100%;background: #0079ad;text-align: center">
                <unit>
                    <segment>
                    <source>hello world</source>
                    <target></target>
                    </segment>
                </unit>
                <a href="http://tunewsinternational.com/">
                    <unit>
                        <segment >
                        <source>international test</source>
                        <target></target>
                        </segment>
                    </unit>
                </a>
                <unit>
                    <segment>
                    <source>2019-04-05 11:53:44</source>
                    <target></target>
                    </segment>
                </unit>
            </div>
        </page-text>     
    </page>
</xliff>
'''

TEXT_HTML = '''
<page-text>
<p>Slot 1</p>
<div style="width: 100%;background: #0079ad;text-align: center">
    E-news No: 12345 - 
    <a href="http://tunewsinternational.com/">international test</a> 
    - 2019-04-05 11:53:44
</div>
</page-text>
'''


TARGET_TEXT_HTML = '''
<page-text>
<p>Schlitz 1</p>
<div style="width: 100%;background: #0079ad;text-align: center">
    E-news No: 12345 - 
    <a href="http://tunewsinternational.com/">internationaler Test</a> 
    - 2019-04-05 11:53:44
</div>
</page-text>
'''

TEXT_XLIFF = '''
<page-text>
<p>
    <unit>
    <segment >
        <source>Slot 1</source>
        <target></target>
        </segment>
    </unit>
</p>
<div style="width: 100%;background: #0079ad;text-align: center">
    <unit>
        <segment>
        <source>E-news No: 12345 -</source>
        <target></target>
        </segment>
    </unit>
    <a href="http://tunewsinternational.com/">
        <unit>
            <segment >
            <source>international test</source>
            <target></target>
            </segment>
        </unit>
    </a>
    <unit>
        <segment>
        <source>- 2019-04-05 11:53:44</source>
        <target></target>
        </segment>
    </unit>
</div> 
</page-text>
'''

SOURCE_TARGET_TEXT_XLIFF = '''
<page-text>
<p>
    <unit>
    <segment >
        <source>Slot 1</source>
        <target>Schlitz 1</target>
        </segment>
    </unit>
</p>
<div style="width: 100%;background: #0079ad;text-align: center">
    <unit>
        <segment>
        <source>E-news No: 12345 -</source>
        <target>E-news No: 12345 -</target>
        </segment>
    </unit>
    <a href="http://tunewsinternational.com/">
        <unit>
            <segment >
            <source>international test</source>
            <target>internationaler Test</target>
            </segment>
        </unit>
    </a>
    <unit>
        <segment>
        <source>- 2019-04-05 11:53:44</source>
        <target>- 2019-04-05 11:53:44</target>
        </segment>
    </unit>
</div> 
</page-text>
'''

DUPLICATE_ELEMENTS_TEXT_HMLT = '''
<page-text>
<div>
    <h2>testing</h2>
    hello world
</div>
<ul>
    <li>123</li>
    <li>123</li>
    <li>1234</li>
    <li>1234</li>
    <li>123</li>
    <li>12341234</li>
    <li>123</li>
</ul>
</page-text>
'''

EXPECT_DUPLICATE_ELEMENTS_TEXT_XLIFF = '''
<page-text>
  <div>
    <h2>
      <unit>
          <segment>
              <source>testing</source>
              <target></target>
          </segment>
      </unit>
    </h2>
    <unit>
      <segment>
          <source>hello world</source>
          <target></target>
      </segment>
    </unit>
  </div>
  <ul>
      <li>
          <unit>
              <segment>
                  <source>123</source>
                  <target></target>
              </segment>
          </unit>
      </li>
      <li>
          <unit>
              <segment>
                  <source>123</source>
                  <target></target>
              </segment>
          </unit>
      </li>
      <li>
          <unit>
              <segment>
                  <source>1234</source>
                  <target></target>
              </segment>
          </unit>
      </li>
      <li>
          <unit>
              <segment>
                  <source>1234</source>
                  <target></target>
              </segment>
          </unit>
      </li>
      <li>
          <unit>
              <segment>
                  <source>123</source>
                  <target></target>
              </segment>
          </unit>
      </li>
      <li>
          <unit>
              <segment>
                  <source>12341234</source>
                  <target></target>
              </segment>
          </unit>
      </li>
      <li>
          <unit>
              <segment>
                  <source>123</source>
                  <target></target>
              </segment>
          </unit>
      </li>
  </ul>
</page-text>
'''

EXPECT_TRANSLATED_PAGE_TUNEWS_XLIFF = '''
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.0" srcLang="en-us" trgLang="de-de">
    <page id="1">
        <page-title>
            <unit>
                <segment state="translated">
                    <source>big news</source>
                    <target>Große Neuigkeiten</target>
                </segment>
            </unit>
        </page-title>  
        <page-text>       
            <p>
                <unit>
                <segment state="translated">
                    <source>First Layer</source>
                    <target>Erste Ebene</target>
                    </segment>
                </unit>
            </p>
            <div style="width: 100%;background: #0079ad;text-align: center">
                <unit>
                    <segment state="translated">
                    <source>hello world</source>
                    <target>Hallo Welt</target>
                    </segment>
                </unit>
                <a href="http://tunewsinternational.com/">
                    <unit>
                        <segment state="translated">
                        <source>international test</source>
                        <target>Internationaler Test</target>
                        </segment>
                    </unit>
                </a>
                <unit>
                    <segment state="translated">
                    <source>2019-04-05 11:53:44</source>
                    <target>2019-04-05 11:53:44</target>
                    </segment>
                </unit>
            </div>
        </page-text>     
    </page>
</xliff>
'''


class PageXliffConverterTestCase(SetupClass):
    def setUp(self):
        super().setUp()
        self.converter = PageXliffConverter()

    def _equals(self, source_content, expect_content):
        source_bs = BeautifulSoup(source_content, 'xml')
        expect_bs = BeautifulSoup(expect_content, 'xml')
        self.assertEqual(source_bs.prettify(), expect_bs.prettify())

    def test_html_to_xliff(self):
        xliff = self.converter.html_to_xliff(TEXT_HTML)
        self._equals(xliff, TEXT_XLIFF)

        source_target_xliff = self.converter.html_to_xliff(TEXT_HTML, TARGET_TEXT_HTML)
        self._equals(source_target_xliff, SOURCE_TARGET_TEXT_XLIFF)

        xliff = self.converter.html_to_xliff(DUPLICATE_ELEMENTS_TEXT_HMLT)
        self._equals(xliff, EXPECT_DUPLICATE_ELEMENTS_TEXT_XLIFF)

    def test_xliff_to_html(self):
        target_html = self.converter.xliff_to_html(SOURCE_TARGET_TEXT_XLIFF, target=True)
        source_html = self.converter.xliff_to_html(SOURCE_TARGET_TEXT_XLIFF, target=False)
        self._equals(target_html, TARGET_TEXT_HTML)
        self._equals(source_html, TEXT_HTML)

    def test_page_translation_to_xliff(self):
        source_translation_page = self.page_tunews.get_translation(language_code='en-us')
        page_tunews_xliff = self.converter.page_translation_to_xliff(source_translation_page,
                                                                     target_language_code='de-de')

        self._equals(re.sub(r'<page id="\d+">', '<page id="1">', page_tunews_xliff),
                     re.sub(r'<page id="\d+">', '<page id="1">', EXPECT_PAGE_TUNEWS_XLIFF))

    def test_xliff_to_page_xliff(self):
        source_translation_page = self.page_tunews.get_translation(language_code='en-us')
        page_tunews_xliff = self.converter.page_translation_to_xliff(source_translation_page,
                                                                     target_language_code='de-de')

        page_xliff = self.converter.xliff_to_page_xliff(page_tunews_xliff)
        self.assertEqual(int(page_xliff.page_id), source_translation_page.page.id)
        self.assertEqual(page_xliff.language_code, 'de-de')
        self.assertEqual(page_xliff.title, '')
        self.assertEqual(page_xliff.text, '')

        page_xliff = self.converter.xliff_to_page_xliff(page_tunews_xliff, target=False)
        self.assertEqual(int(page_xliff.page_id), source_translation_page.page.id)
        self.assertEqual(page_xliff.language_code, 'en-us')
        self.assertEqual(page_xliff.title, source_translation_page.title)
        self._equals(page_xliff.text, source_translation_page.text)

    def test_translated_xliff_to_page_xliff(self):
        page_xliff = self.converter.xliff_to_page_xliff(EXPECT_TRANSLATED_PAGE_TUNEWS_XLIFF)
        self.assertEqual(int(page_xliff.page_id), 1)
        self.assertEqual(page_xliff.language_code, 'de-de')
        self.assertEqual(page_xliff.title, 'Große Neuigkeiten')
        self._equals(page_xliff.text,
                     '''<p>Erste Ebene</p>
                        <div style="width: 100%;background: #0079ad;text-align: center">
                        Hallo Welt
                        <a href="http://tunewsinternational.com/">international test</a>
                        2019-04-05 11:53:44
                        </div>
                        ''')

    def test_xliff_to_page_exception(self):
        with self.assertRaises(XliffValidationException) as context:
            self.converter.xliff_to_page_xliff('''
                <invalid>testing</invalid>
            ''')

        self.assertTrue('cannot find xliff tag or srcLang and trgLang not exists.' in str(context.exception))


class PageXliffHelperTest(SetupClass):
    def setUp(self):
        super().setUp()
        self.page_xliff_helper = PageXliffHelper()

    def test_export_page_translation_xliff(self):
        source_translation_page = self.page_tunews.get_translation(language_code='en-us')
        page_tunews_xliff = self.page_xliff_helper.converter.page_translation_to_xliff(source_translation_page,
                                                                                       target_language_code='de-de')
        file_path = self.page_xliff_helper.export_page_translation_xliff(source_translation_page,
                                                                         target_language_code='de-de')

        with open(file_path, 'r') as file:
            file_xliff_content = file.read()

        self.assertEqual(page_tunews_xliff, file_xliff_content)

    def test_export_page_xliffs_to_zip(self):
        zip_file_path = self.page_xliff_helper.export_page_xliffs_to_zip(self.page_tunews)
        expect_name_list = ['page_{0}_en-us_de-de.xliff'.format(self.page_tunews.id),
                            'page_{0}_en-us_ar-ma.xliff'.format(self.page_tunews.id),
                            ]
        self.assertTrue(os.path.isfile(zip_file_path))
        with ZipFile(zip_file_path, 'r') as zip_file:
            name_list = zip_file.namelist()
            self.assertEqual(len(name_list), 2)
            for name in expect_name_list:
                self.assertTrue(name in name_list)

    def test_import_xliff_file(self):
        source_translation_page = self.page_tunews.get_translation(language_code='en-us')
        file_path = self.page_xliff_helper.export_page_translation_xliff(source_translation_page,
                                                                         target_language_code='de-de')
        result = self.page_xliff_helper.import_xliff_file(file_path, self.user)

        self.assertFalse(result)
        self.assertIsNone(self.page_tunews.get_translation(language_code='de-de'))

    def test_import_xliffs_zip_file(self):
        zip_file_path = self.page_xliff_helper.export_page_xliffs_to_zip(self.page_tunews)
        results = self.page_xliff_helper.import_xliffs_zip_file(zip_file_path, self.user)

        expect_resutls = [
            ('page_{0}_en-us_de-de.xliff'.format(self.page_tunews.id), False),
            ('page_{0}_en-us_ar-ma.xliff'.format(self.page_tunews.id), False)
        ]
        for result in expect_resutls:
            self.assertTrue(result in results)

    def test_import_xliff_file_translated(self):
        xliff_content = re.sub(r'<page id="\d+">',
                               '<page id="{0}">'.format(self.page_tunews.id),
                               EXPECT_TRANSLATED_PAGE_TUNEWS_XLIFF)

        file_path = os.path.join(XLIFFS_DIR, 'test', 'page_{0}_en-us_de-de.xliff'.format(self.page_tunews.id))
        PageXliffHelper.save_file(xliff_content, file_path)

        result = self.page_xliff_helper.import_xliff_file(file_path, self.user)

        self.assertTrue(result)
        self.assertIsNotNone(self.page_tunews.get_translation(language_code='de-de'))
