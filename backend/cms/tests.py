from django.test import TestCase

from cms.models import Page, Language
from cms.views.general import POSITION_CHOICES
from .views.regions.region_form import RegionForm
from .views.pages.page_form import PageForm
from .views.languages.language_form import LanguageForm
from .views.language_tree.language_tree_node_form import LanguageTreeNodeForm
from .models.site import Site
from django.contrib.auth.models import User
from cms.page_xliff_converter import PageXliffConverter
from bs4 import BeautifulSoup


class SetupClass(TestCase):
    @staticmethod
    def create_region(region_data):
        region_form = RegionForm(region_data)
        region_form.is_valid()
        region_form.save_region()
        return Site.objects.get(slug=region_data['name'])

    @staticmethod
    def create_language(language_data):
        language_form = LanguageForm(language_data)
        language_form.is_valid()
        language_form.save_language()
        return Language.objects.get(name=language_data['name'])

    @staticmethod
    def create_language_tree_node(language_tree_node_data, site_slug=None):
        language_tree_node_form = LanguageTreeNodeForm(data=language_tree_node_data,
                                                       site_slug=site_slug)
        language_tree_node_form.is_valid()
        return language_tree_node_form.save_language_node()

    @staticmethod
    def create_page(page_data, user, site_slug, language_code,
                    page_id=None, publish=False, archived=False):
        page_form = PageForm(page_data, user=user)
        page_form.is_valid()
        return page_form.save_page(site_slug=site_slug,
                                   language_code=language_code,
                                   page_id=page_id,
                                   publish=publish,
                                   archived=archived)

    def setUp(self):
        self.user = User.objects.create_user('test', 'test@integreat.com', 'test')
        self.site = self.create_region({
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
            'status': Site.ACTIVE,
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
            }, site_slug='demo'
        )

        self.deutsch_node = self.create_language_tree_node(
            language_tree_node_data={
                'language': self.deutsch.id,
                'parent': self.english_node.id,
                'active': True,
            }, site_slug='demo')

        self.arabic_node = self.create_language_tree_node(
            language_tree_node_data={
                'language': self.arabic.id,
                'parent': self.english_node.id,
                'active': True
            }, site_slug='demo')

        self.page_tunews = self.create_page(
            page_data={
                'title': 'Tunews',
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
            site_slug='demo',
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
            site_slug='demo',
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
            site_slug='demo',
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
            site_slug='demo',
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
            site_slug='demo',
            language_code='en-us',
            publish=True
        )


class LanguageTreeNodeTestCase(SetupClass):
    def test_node_site(self):
        self.assertEqual(self.english_node.site, self.site)

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
        pages = Page.get_tree(site_slug=self.site.slug)
        self.assertEqual(len(pages), 4)


EXPECT_PAGE_TUNEWS__XLIFF = '''
<?xml version="1.0"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.0" srcLang="en-us" trgLang="de-de">
    <page id="2">
        <title>
            <unit>
                <segment >
                    <source>Tunews</source>
                    <target></target>
                </segment>
            </unit>
        </title>  
        <text>       
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
        </text>     
    </page>
</xliff>
'''

TEXT_HTML = '''
<text>
<p>Slot 1</p>
<div style="width: 100%;background: #0079ad;text-align: center">
    E-news No: 12345 - 
    <a href="http://tunewsinternational.com/">international test</a> 
    - 2019-04-05 11:53:44
</div>
</text>
'''

TARGET_TEXT_HTML = '''
<text>
<p>Schlitz 1</p>
<div style="width: 100%;background: #0079ad;text-align: center">
    E-news No: 12345 - 
    <a href="http://tunewsinternational.com/">internationaler Test</a> 
    - 2019-04-05 11:53:44
</div>
</text>
'''

TEXT_XLIFF = '''
<text>
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
</text>
'''

SOURCE_TARGET_TEXT_XLIFF = '''
<text>
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
</text>
'''


class PageXliffConverterTestCase(SetupClass):
    def setUp(self):
        super().setUp()
        self.converter = PageXliffConverter()

    def _equals(self, source_content, expect_content):
        source_bs = BeautifulSoup(source_content, 'xml')
        expect_bs = BeautifulSoup(expect_content, 'xml')
        self.assertEqual(source_bs.prettify(formatter="minimal"), expect_bs.prettify(formatter="minimal"))

    def test_html_to_xliff(self):
        xliff = self.converter.html_to_xliff(TEXT_HTML)
        self._equals(xliff, TEXT_XLIFF)

        source_target_xliff = self.converter.html_to_xliff(TEXT_HTML, TARGET_TEXT_HTML)
        self._equals(source_target_xliff, SOURCE_TARGET_TEXT_XLIFF)

    def test_xliff_to_html(self):
        target_html = self.converter.xliff_to_html(SOURCE_TARGET_TEXT_XLIFF, target=True)
        source_html = self.converter.xliff_to_html(SOURCE_TARGET_TEXT_XLIFF, target=False)
        self._equals(target_html, TARGET_TEXT_HTML)
        self._equals(source_html, TEXT_HTML)

    def test_page_to_xliff(self):
        pass


    def test_xliff_to_page(self):
        pass