Changelog
=========

UNRELEASED
----------


2023.1.2
--------

* [ :github:`#1968 <issues/1968>` ] Fix media library permissions for observer
* [ :github:`#1883 <issues/1883>` ] Introduce new status for automatic translations
* [ :github:`#1993 <issues/1993>` ] Skip duplicate page translations in XLIFF file
* [ :github:`#1769 <issues/1769>` ] Evenly distribute page, event and poi form sidebar boxes
* [ :github:`#2033 <issues/2033>` ] Add user setting to optionally enable the automatic distribution of sidebar boxes
* [ :github:`#1876 <issues/1876>` ] Make items in the sidebar of poi and event form toggleable
* [ :github:`#2023 <issues/2023>` ] Rephrase texts in text understandability-box
* [ :github:`#1552 <issues/1552>` ] Make slugfield scrollable
* [ :github:`#2008 <issues/2008>` ] Fix end date of recurring events in API
* [ :github:`#1954 <issues/1954>` ] Fix RTL text direction in PDF export
* [ :github:`#1883 <issues/1883>` ] Add icon and color to POI Category


2023.1.1
--------

* [ :github:`#2003 <issues/2003>` ] Fix HIX widget


2023.1.0
--------

* [ :github:`#1876 <issues/1876>` ] Make sidebar boxes on page form collapsible and save status as cookie
* [ :github:`#1345 <issues/1345>` ] Track DeepL API usage by regions
* [ :github:`#1695 <issues/1695>` ] Treat URLs with broken hash anchors as valid in link checker
* [ :github:`#1969 <issues/1969>` ] Hide edit link button in content forms for users without edit permission


2022.12.3
---------

* [ :github:`#1772 <issues/1772>` ] Fix hidden languages being listed in fallback translation text on the API endpoint
* [ :github:`#1945 <issues/1945>` ] Make message and button in list and form of page/event/poi uniform for observer users
* [ :github:`#1957 <issues/1957>` ] Add keyboard shortcuts for icons in the editor
* [ :github:`#1900 <issues/1900>` ] Exclude users without view_page permission from page-specific permissions
* [ :github:`#1956 <issues/1956>` ] Add Amharic fonts and fix PDF export in Amharic
* [ :github:`#1906 <issues/1906>` ] Fix link escape in message in imprint form
* [ :github:`#1983 <issues/1983>` ] Fix broken page form ordering box
* [ :github:`#1978 <issues/1978>` ] Fix PDF export for Greek


2022.12.2
---------

* [ :github:`#686 <issues/686>` ] Improve page filter
* [ :github:`#1132 <issues/1132>` ] Add TOTP 2-factor authentication
* [ :github:`#1884 <issues/1884>` ] Add support for passwordless authentication


2022.12.1
---------

* [ :github:`#1756 <issues/1756>` ] Add media library, content-edit-lock and diff-view to imprint sbs-view
* [ :github:`#1870 <issues/1870>` ] Fix copy source content in imprint sbs-view
* [ :github:`#1950 <issues/1950>` ] Fix long loading time of page tree


2022.12.0
---------

* [ :github:`#1701 <issues/1701>` ] Fix malformed CSV export on weekly statistics report
* [ :github:`#1886 <issues/1886>` ] Fix push notification character counter
* [ :github:`#1912 <issues/1912>` ] Fix alignment of page permission button
* [ :github:`#1892 <issues/1892>` ] Fix copy short url button in page tree
* [ :github:`#1890 <issues/1890>` ] Add hint about icon aspect ratio to location form
* [ :github:`#1889 <issues/1889>` ] Make translation status independent from publishing status
* [ :github:`#1494 <issues/1494>` ] Add a role without page editing permissions
* [ :github:`#1914 <issues/1914>` ] Always uncheck minor edit field by default
* [ :github:`#1934 <issues/1934>` ] Make sure translations are never a minor version after XLIFF import
* [ :github:`#1864 <issues/1864>` ] Fix possibility to mark page as up-to-date without performing changes
* [ :github:`#1885 <issues/1885>` ] Fix ongoing translation cancel button
* [ :github:`#1942 <issues/1942>` ] Fix auto save functionality
* [ :github:`#1922 <issues/1922>` ] Fix html escape in xliff import error message


2022.11.4
---------

* [ :github:`#1616 <issues/1616>` ] Add buttons to expand and copy truncated search feedback
* [ :github:`#1832 <issues/1832>` ] Add opening hours for locations
* [ :github:`#1502 <issues/1502>` ] Hide links on archived pages in broken link checker
* [ :github:`#1791 <issues/1791>` ] Render live content in pdfs
* [ :github:`#1869 <issues/1869>` ] Fix error in imprint side by side view
* [ :github:`#1786 <issues/1786>` ] Remove textblock option in editor, add button to clear all formatting
* [ :github:`#1788 <issues/1788>` ] Fix broken translation status of events & locations if only minor public versions exists
* [ :github:`#1688 <issues/1688>` ] Specify protected pages when trying to delete regions


2022.11.3
---------

* [ :github:`#1827 <issues/1827>` ] Make Multi-language-XLIFF export popup scrollable
* [ :github:`#1844 <issues/1844>` ] Use gender sensitive language in user form
* [ :github:`#1521 <issues/1521>` ] Show warning when user entered slug got changed
* [ :github:`#1807 <issues/1807>` ] Remove short description field from POI form
* [ :github:`#522 <issues/522>` ] Add region setting to activate SEO section, add SEO section to POI form
* [ :github:`#1858 <issues/1858>` ] Enable submitting feedback about fallback translations of recurring events
* [ :github:`#1865 <issues/1865>` ] Fix TextLab HIX widget for non-staff users


2022.11.2
---------

* [ :github:`#1843 <issues/1843>` ] Fix region selection after login


2022.11.1
---------

* [ :github:`#1840 <issues/1840>` ] Fix statistics widget on dashboard


2022.11.0
---------

* [ :github:`#1333 <issues/1333>` ] Mark external links with special class
* [ :github:`#1718 <issues/1718>` ] Enable submitting feedback about fallback translations of events and pois
* [ :github:`#1793 <issues/1793>` ] Fix sending feedback for recurring events
* [ :github:`#1717 <issues/1717>` ] Provide fallback translations for imprint feedbacks
* [ :github:`#1513 <issues/1513>` ] Fix link scanning when cloning regions
* [ :github:`#1816 <issues/1816>` ] Make menu sidebar responsive
* [ :github:`#1746 <issues/1746>` ] Hide analytics section (partially) for author, editor and event manager
* [ :github:`#1035 <issues/1035>` ] Enable setting POI position via drag & drop on map
* [ :github:`#1456 <issues/1456>` ] Use gender sensitive language
* [ :github:`#1806 <issues/1806>` ] Mark POI category as not visible in app


2022.10.2
---------

* [ :github:`#1808 <issues/1808>` ] Improve calculation of HIX values via Textlab
* [ :github:`#1800 <issues/1800>` ] Exclude archived pages from PDF exports
* [ :github:`#1802 <issues/1802>` ] Reenable table of contents and page numbers in PDFs
* [ :github:`#1350 <issues/1350>` ] Various small PDF export improvements
* [ :github:`#1777 <issues/1777>` ] Fix autocompleting POI address for non-staff users
* [ :github:`#1749 <issues/1749>` ] Fix region deletion error if media library has nested structure
* [ :github:`#1170 <issues/1170>` ] Add map preview on POI form
* [ :github:`#1579 <issues/1579>` ] Fix auto-filling of coordinates for multiple street numbers
* [ :github:`#1767 <issues/1767>` ] Revert statistics calculation to original & add online downloads column


2022.10.1
---------

* [ :github:`#1759 <issues/1759>` ] Add line break between images in PDF exports
* [ :github:`#1537 <issues/1537>` ] Fix broken inline icons in PDF exports
* [ :github:`#951 <issues/951>` ] Add possibility to create categories for POIs
* [ :github:`#1742 <issues/1742>` ] Add last modified date to media sidebar
* [ :github:`#1703 <issues/1703>` ] Remove pending account activation warning when user form is submitted with errors
* [ :github:`#1684 <issues/1684>` ] Set filesize limit for uploads to 3MB
* [ :github:`#1000 <issues/1000>` ] Auto-complete address and coordinates of locations
* [ :github:`#1434 <issues/1434>` ] Add display of HIX values to nudge users to write easier texts
* [ :github:`#1770 <issues/1770>` ] Fix error in SUMM.AI translation if paragraph contains only special characters
* [ :github:`#1710 <issues/1710>` ] Add spacing to sidebar to improve view on small screens
* [ :github:`#1526 <issues/1526>`] Fix sending push notifications in one language
* [ :github:`#1630 <issues/1630>`] Fix not recognized sent status of push notifications
* [ :github:`#1683 <issues/1683>` ] Improve organization management


2022.10.0
---------

* [ :github:`#1734 <issues/1734>` ] Increase timeout for SUMM.AI API client


2022.9.5
--------

* [ :github:`#1720 <issues/1720>` ] Fix translation of empty tags with SUMM.AI API for Easy German


2022.9.4
--------

* [ :github:`#1653 <issues/1653>` ] Create new versions even if content did not change to preserve translation status
* [ :github:`#1450 <issues/1450>` ] Add API from SUMM.AI to create easy-understable German
* [ :github:`#1532 <issues/1532>` ] Fix PDF table of contents in cyrillic alphabets


2022.9.3
--------

* [ :github:`#1705 <issues/1705>` ] Fix error messages in event validation


2022.9.2
--------

* [ :github:`#1011 <issues/1011>` ] Use ISO format for datetime objects/fields
* [ :github:`#1599 <issues/1599>` ] Exclude automatic saves and pending reviews from XLIFF export


2022.9.1
--------

* [ :github:`#1470 <issues/1470>` ] Add non-political flags for Arabic and Farsi
* [ :github:`#1678 <issues/1678>` ] Fix error when creating new page translations


2022.9.0
--------

* [ :github:`#1664 <issues/1664>` ] Fix media library and content edit lock in sbs view
* [ :github:`#1660 <issues/1660>` ] Fix moving pages to the root level from the page form
* [ :github:`#1566 <issues/1566>` ] Manage organizations per region
* [ :github:`#1440 <issues/1440>` ] Add missing word count to translation coverage report
* [ :github:`#1596 <issues/1596>` ] Ignore default language in translation report
* [ :github:`#1607 <issues/1607>` ] Count words of source translation in translation report
* [ :github:`#1674 <issues/1674>` ] Improve language tree node creation
* [ :github:`#1591 <issues/1591>` ] Add bulk actions for language tree nodes
* [ :github:`#1673 <issues/1673>` ] Add possibility to reject pending reviews and discard auto saves
* [ :github:`#1640 <issues/1640>` ] Update author when restoring old versions
* [ :github:`#1583 <issues/1583>` ] Only enable the chat for staff and management roles
* [ :github:`#1647 <issues/1647>` ] Give service team delete permissions for regions and push notifications


2022.8.3
--------

* [ :github:`#1635 <issues/1635>` ] Show Matomo actions in statistics instead of visitors
* [ :github:`#1449 <issues/1449>` ] Show diff to last source version in side-by-side view
* [ :github:`#1656 <issues/1656>` ] Only validate event duration if dates are valid
* [ :github:`#1638 <issues/1638>` ] Change help text of visibility for language nodes
* [ :github:`#1615 <issues/1615>` ] Streamline navbar structure and remove analytics dashboard


2022.8.2
--------

* [ :github:`#1649 <issues/1649>` ] Make UI languages configurable


2022.8.1
--------

* [ :github:`#1628 <issues/1628>` ] Add Dutch UI language
* [ :github:`#1549 <issues/1549>` ] Add multilingual XLIFF export
* [ :github:`#1636 <issues/1636>` ] Improve XLIFF export error messages


2022.8.0
--------

* [ :github:`#1390 <issues/1390>` ] Move files via drag and drop
* [ :github:`#1606 <issues/1606>` ] Remove warning at POI contacts
* [ :github:`#1571 <issues/1571>` ] Show offline downloads in statistics
* [ :github:`#1464 <issues/1464>` ] Fix status of translation with only minor public version
* [ :github:`#1623 <issues/1623>` ] Fix imprint publish/update button
* [ :github:`#1534 <issues/1534>` ] Invalidate cache after moving nodes
* [ :github:`#1535 <issues/1535>` ] Fix event api performance
* [ :github:`#1604 <issues/1604>` ] Show no broken links from restored versions


2022.7.0
--------

* [ :github:`#1528 <issues/1528>` ] Fix list view layouts for long titles
* [ :github:`#1510 <issues/1510>` ] Limit event duration to 7 days
* [ :github:`#1512 <issues/1512>` ] Deliver location names in the api in the default language only
* [ :github:`#1581 <issues/1581>` ] Improve wording of minor edit label
* [ :github:`#1580 <issues/1580>` ] Improve user list
* [ :github:`#1504 <issues/1504>` ] Keep filters on pagination
* [ :github:`#1585 <issues/1585>` ] Hide news after 28 days
* [ :github:`#1600 <issues/1600>` ] Improve XLIFF export bulk option description
* [ :github:`#1511 <issues/1511>` ] Fix PDF generation for long filenames


2022.6.3
--------

* [ :github:`#1561 <issues/1561>` ] Rename location contact labels
* [ :github:`#1567 <issues/1567>` ] Hide organization field in user form
* [ :github:`#1563 <issues/1563>` ] Fix permission checks in side-by-side view


2022.6.2
--------

* [ :github:`#1445 <issues/1445>` ] Allow only users with publish permission to unpublish page
* [ :github:`#1497 <issues/1497>` ] Set older versions to draft when saved as draft
* [ :github:`#1550 <issues/1550>` ] Fix status change when restoring revisions
* [ :github:`#1509 <issues/1509>` ] Support legacy sitemap URL patterns
* [ :github:`#742 <issues/742>` ] Make bounding box configurable per region
* [ :github:`#742 <issues/742>` ] Automatically fetch region bounding boxes from Nominatim API
* [ :github:`#1517 <issues/1517>` ] Set all pages to draft when duplicating regions


2022.6.1
--------

* [ :github:`#1516 <issues/1516>` ] Fix save buttons alignment
* [ :github:`#1520 <issues/1520>` ] Fix button name in side-by-side view
* [ :github:`#1502 <issues/1502>` ] Do not check links in archived pages
* [ :github:`#1258 <issues/1258>` ] Add possibility to mark pages as up-to-date
* [ :github:`#1539 <issues/1539>` ] Urlencode permalinks when copying to clipboard
* [ :github:`#1542 <issues/1542>` ] Fix short url copy button


2022.6.0
--------

* [ :github:`#1501 <issues/1501>` ] Remove formatting when content is pasted into tinymce editor
* [ :github:`#1514 <issues/1514>` ] Fix format of region aliases in API
* [ :github:`#1503 <issues/1503>` ] Fix expanding feedback not working


2022.5.4
--------

* [ :github:`#1454 <issues/1454>` ] Enable recurring events for non-expert users
* [ :github:`#1416 <issues/1416>` ] Hide staff users from region user list
* [ :github:`#1483 <issues/1483>` ] Add filters to admin user list
* [ :github:`#1001 <issues/1001>` ] Deliver missing translations in default language for events and locations
* [ :github:`#1411 <issues/1411>` ] Indicate fallback translations for imprint


2022.5.3
--------

* [ :github:`#1460 <issues/1460>` ] Only show status in broken link checker for expert users
* [ :github:`#742 <issues/742>` ] Add default bounding box to region API
* [ :github:`#1406 <issues/1406>` ] Hide sub-headings in PDF table of contents
* [ :github:`#1478 <issues/1478>` ] Fix bug where page with archived sibling cannot be saved
* [ :github:`#1452 <issues/1452>` ] Only allow users of the same region for page-specific-permissions
* [ :github:`#1481 <issues/1481>` ] Support last week for monthly recurring events
* [ :github:`#1487 <issues/1487>` ] Invalidate cache of related objects when languages are changed


2022.5.2
--------

* [ :github:`#1471 <issues/1471>` ] Add statistic settings to region form again
* [ :github:`#1473 <issues/1473>` ] Fix offers compatibility with web app
* [ :github:`#1476 <issues/1476>` ] Fix error when importing legacy XLIFF files from WordPress
* [ :github:`#1462 <issues/1462>` ] Set default value of POI visible on map to false
* [ :github:`#1475 <issues/1475>` ] Add minor edit setting for events and locations


2022.5.1
--------

* [ :github:`#1409 <issues/1409>` ] Fix automatic filling of region coordinates
* [ :github:`#1407 <issues/1407>` ] Add location setting to region model
* [ :github:`#1417 <issues/1417>` ] Don't show fallback text for empty pages if there are no alternatives
* [ :github:`#1418 <issues/1418>` ] Strip HTML entities in excerpt field in the API
* [ :github:`#1402 <issues/1402>` ] Also duplicate imprints for new regions
* [ :github:`#1408 <issues/1408>` ] Remove duplication of push API tokens for pages during duplication process
* [ :github:`#1404 <issues/1404>` ] Fix performance issue for select all on huge page trees
* [ :github:`#1403 <issues/1403>` ] Fix problem with cache when removing language in a region
* [ :github:`#1401 <issues/1401>` ] Support WordPress slugs by applying slugify on API parameters
* [ :github:`#1413 <issues/1413>` ] Fix change of pagination size in broken link checker
* [ :github:`#1422 <issues/1422>` ] Keep pagination settings in broken link checker when performing replacement
* [ :github:`#1405 <issues/1405>` ] Show same URLs only once in broken link checker
* [ :github:`#1438 <issues/1438>` ] Fix error in page form when page-specific permissions are enabled
* [ :github:`#1292 <issues/1292>` ] Add multi-file upload via drag and drop
* [ :github:`#1442 <issues/1442>` ] Add author role (formerly organizer)
* [ :github:`#1461 <issues/1461>` ] Display warning on leaving page after editing a page description
* [ :github:`#1283 <issues/1283>` ] Remove archived pages from several settings/options


2022.5.0
--------

* [ :github:`#1369 <issues/1369>` ] Add contenthash to CSS files for correct cache handling
* [ :github:`#1046 <issues/1046>` ] Show number of selected items in lists and page tree
* [ :github:`#1000 <issues/1000>` ] Automatically derive location coordinates from address
* [ :github:`#1180 <issues/1180>` ] Make coordinates optional for locations not on map
* [ :github:`#1380 <issues/1380>` ] Fix url resolving for regions with non-ascii slugs
* [ :github:`#726 <issues/726>` ] Add additional fields to location model
* [ :github:`#1351 <issues/1351>` ] Fix empty slugs when new translations are imported via XLIFF
* [ :github:`#1311 <issues/1311>` ] Fix last_updated field when cloning regions
* [ :github:`#1384 <issues/1384>` ] Remove phone numbers and email addresses from invalid links
* [ :github:`#1350 <issues/1350>` ] Fix legacy media urls in PDF export
* [ :github:`#1388 <issues/1388>` ] Remove additional event handlers for selection count
* [ :github:`#1038 <issues/1038>` ] Rename location not on map attribute
* [ :github:`#1389 <issues/1389>` ] Change media library upload paths
* [ :github:`#1371 <issues/1371>` ] Show fallback text for empty pages
* [ :github:`#1056 <issues/1056>` ] Enhance page preview feature
* [ :github:`#1387 <issues/1387>` ] Fix error when previewing a non-existing page translation


2022.4.2
--------

* [ :github:`#1366 <issues/1366>` ] Fix monthly recurring events on mondays
* [ :github:`#1365 <issues/1365>` ] Add timezone setting to region model
* [ :github:`#1093 <issues/1093>` ] Add Malte and Aschaffenburg brandings


2022.4.1
--------

* [ :github:`#1354 <issues/1354>` ] Fix order of root pages
* [ :github:`#1353 <issues/1353>` ] Add tunews setting to region model
* [ :github:`#1328 <issues/1328>` ] Fix missing entries in broken link checker
* [ :github:`#1289 <issues/1289>` ] Prevent submitting feedback for a non-existent imprint
* [ :github:`#1359 <issues/1359>` ] Cascade delete imprint feedback when imprint is deleted
* [ :github:`#1350 <issues/1350>` ] Fix font support of PDF export
* [ :github:`#1349 <issues/1349>` ] Fix network error when downloading PDF files


2022.4.0
--------

* [ :github:`#1319 <issues/1319>` ] Fix error on Imprint API
* [ :github:`#1104 <issues/1104>` ] Add automatic translations via DeepL API
* [ :github:`#1024 <issues/1024>` ] Add URL search-replace for linkchecker
* [ :github:`#1177 <issues/1177>` ] Add content locking mechanism
* [ :github:`#1255 <issues/1255>` ] Check only the latest versions of translations for broken links
* [ :github:`#1054 <issues/1054>` ] Provide fallback translations for mirrored pages
* [ :github:`#1198 <issues/1198>` ] Check availability for DeepL bulk actions
* [ :github:`#1293 <issues/1293>` ] Enable login via email address
* [ :github:`#1327 <issues/1327>` ] Fix page PDF export
* [ :github:`#1226 <issues/1226>` ] Fix page tree fields cache invalidation
* [ :github:`#1325 <issues/1325>` ] Fix error when deleting a page which was embedded as live content


2022.3.6
--------

* [ :github:`#1314 <issues/1314>` ] Fix layout of media library on small screens


2022.3.5
--------

* [ :github:`#1301 <issues/1301>` ] Fix order of push notifications
* [ :github:`#1296 <issues/1296>` ] Fix page tree after resetting filters
* [ :github:`#1282 <issues/1282>` ] Fix feedback cache invalidation
* [ :github:`#1305 <issues/1305>` ] Fix deletion of media files and directories
* [ :github:`#1195 <issues/1195>` ] Insert full images into content instead of thumbnails
* [ :github:`#1181 <issues/1181>` ] Scroll media library and sidebar independently of each other
* [ :github:`#1279 <issues/1279>` ] Fix error in news form when submitted without data
* [ :github:`#1055 <issues/1055>` ] Add bulk actions for archiving/restoring pages, events and locations


2022.3.4
--------

* [ :github:`#1108 <issues/1108>` ] Support SVG images in PDF export
* [ :github:`#1284 <issues/1284>` ] Inherit status of new translations from source language on XLIFF import
* [ :github:`#1047 <issues/1047>` ] Provide option to only export public versions as XLIFF
* [ :github:`#973 <issues/973>` ] Support BCP tags for XLIFF import/export
* [ :github:`#1281 <issues/1281>` ] Prevent the same push notification from being sent multiple times
* [ :github:`#760 <issues/760>` ] Enable linking of push notifications to local news in native apps
* [ :github:`#1158 <issues/1158>` ] Prefetch subpages in advance
* [ :github:`#1052 <issues/1052>` ] Select all subpages when checking parent page
* [ :github:`#1004 <issues/1004>` ] Add button to expand/collapse all pages


2022.3.3
--------

* [ :github:`#1271 <issues/1271>` ] Fix feedback API endpoint
* [ :github:`#1099 <issues/1099>` ] Add push content API
* [ :github:`#1277 <issues/1277>` ] Fix change detection for XLIFF import
* [ :github:`#1276 <issues/1276>` ] Allow importing unchanged XLIFF files


2022.3.2
--------

* [ :github:`#1269 <issues/1269>` ] Fix fcm endpoint JSON format


2022.3.1
--------

* [ :github:`#1267 <issues/1267>` ] Fix push notifications attribute name in API


2022.3.0
--------

* [ :github:`#1086 <issues/1086>` ] Provide correct URL for POI
* [ :github:`#1247 <issues/1247>` ] Update translation status on source status changes
* [ :github:`#1251 <issues/1251>` ] Fix change detection in page form
* [ :github:`#1260 <issues/1260>` ] Fix Firebase messaging
* [ :github:`#1259 <issues/1259>` ] Fix cloning of regions


2022.2.4
--------

* [ :github:`#1227 <issues/1227>` ] Correct URL and Path field in imprint API
* [ :github:`#1222 <issues/1222>` ] Fix missing translations and archived pages in API
* [ :github:`#1131 <issues/1131>` ] Flush Cache of related objects when changing a tree
* [ :github:`#1242 <issues/1242>` ] Add setting to activate Matomo tracking
* [ :github:`#1197 <issues/1197>` ] Fix calculation of translation status


2022.2.3
--------

* [ :github:`#1223 <issues/1223>` ] Remove icon from imprint API
* [ :github:`#1224 <issues/1224>` ] Fix PDF export API


2022.2.2
--------

* [ :github:`#1214 <issues/1214>` ] Fix API return format of event location
* [ :github:`#1218 <issues/1218>` ] Fix saving of first root node
* [ :github:`#1215 <issues/1215>` ] Use canonical Enter / Shift+Enter behavior in TinyMCE
* [ :github:`#1221 <issues/1221>` ] Disable pagination on language tree


2022.2.1
--------

First stable release of the new content management system for the Integreat app

* [ :github:`#1162 <issues/1162>` ] Allow management role to delete imprint
* [ :github:`#765 <issues/765>` ] Add extended view tests
* [ :github:`#765 <issues/765>` ] Add tests of form submissions
* [ :github:`#1163 <issues/1163>` ] Fix error when editor creates new page
* [ :github:`#1165 <issues/1165>` ] Fix bulk action button for sub pages
* [ :github:`#1173 <issues/1173>` ] Fix bug where unused location is preselected for new event
* [ :github:`#1166 <issues/1166>` ] Fix creation of location from event form
* [ :github:`#1172 <issues/1172>` ] Fix filtering for locations in event list
* [ :github:`#1184 <issues/1184>` ] Allow user to embed live content from current region
* [ :github:`#1185 <issues/1185>` ] Fix feedback API
* [ :github:`#1188 <issues/1188>` ] Fix error in broken link checker
* [ :github:`#1179 <issues/1179>` ] Disable browser cache of page tree
* [ :github:`#1190 <issues/1190>` ] Add possibility to set custom region prefix
* [ :github:`#1164 <issues/1164>` ] Fix possibility to cancel translation process
* [ :github:`#1175 <issues/1175>` ] Don't show empty tag if the page has subpages
* [ :github:`#1200 <issues/1200>` ] Fix parent page select input
* [ :github:`#1196 <issues/1196>` ] Track API requests with Matomo
* [ :github:`#1209 <issues/1209>` ] Support legacy PDF API
* [ :github:`#1212 <issues/1212>` ] Only show xliff export option for expert users
* [ :github:`#988 <issues/988>` ] Add browser warning when leaving unsaved forms
* [ :github:`#1208 <issues/1208>` ] Allow editor role to publish events
* [ :github:`#1208 <issues/1208>` ] Hide feedback and imprint for editor and event manager role


2022.2.0-beta
-------------

* [ :github:`#1065 <issues/1065>` ] Fix APIv3 single page endpoint for multiple translation versions
* [ :github:`#1077 <issues/1077>` ] Fix error when deleting a poi that is used by an event
* [ :github:`#844 <issues/844>` ] Add tutorial to page tree view
* [ :github:`#1030 <issues/1030>` ] Fix layout of language tabs in forms
* [ :github:`#1017 <issues/1017>` ] Add support for Python 3.9
* [ :github:`#19 <issues/19>` ] Add APIv3 parents/ancestors endpoint
* [ :github:`#1023 <issues/1023>` ] Add API tests
* [ :github:`#943 <issues/943>` ] Improve performance of feedback list
* [ :github:`#1088 <issues/1088>` ] Replace django-mptt by django-treebeard
* [ :github:`#943 <issues/943>` ] Improve performance of page tree, event and POI lists
* [ :github:`#943 <issues/943>` ] Improve performance of page, event and POI API endpoints
* [ :github:`#642 <issues/642>` ] Add database migrations
* [ :github:`#1103 <issues/1103>` ] Add bulk actions for events and POIs
* [ :github:`#943 <issues/943>` ] Improve performance of content forms
* [ :github:`#943 <issues/943>` ] Improve performance of translation coverage view
* [ :github:`#1134 <issues/1134>` ] Support legacy XLIFF export for MemoQ WPML filter
* [ :github:`#943 <issues/943>` ] Improve performance of content searches
* [ :github:`#1101 <issues/1101>` ] Fetch subpages of page tree gradually
* [ :github:`#1143 <issues/1143>` ] Hide "Responsible organization" field in page form if no organizations exist
* [ :github:`#1151 <issues/1151>` ] Add possibility to delete languages
* [ :github:`#1106 <issues/1106>` ] Add possibility to delete offer templates


2021.12.0-beta
--------------

* [ :github:`#943 <issues/943>` ] Improve performance of region list
* [ :github:`#1031 <issues/1031>` ] Fix duplicating pages of deleted authors
* [ :github:`#1028 <issues/1028>` ] Fix page permissions
* [ :github:`#1048 <issues/1048>` ] Show recurrence in event list
* [ :github:`#992 <issues/992>` ] Only show upcoming events per default
* [ :github:`#1044 <issues/1044>` ] Allow configuration via /etc/integreat-cms.ini
* [ :github:`#1044 <issues/1044>` ] Fix dependency versions for production setup
* [ :github:`#968 <issues/968>` ] Fully functional media library in selection window
* [ :github:`#1029 <issues/1029>` ] Align language flags and translation status icons
* [ :github:`#1062 <issues/1062>` ] Fix error when replacing media files without thumbnail
* [ :github:`#931 <issues/931>` ] Add search function for media library


2021.11.0-beta
--------------

Initial pre-release of the new content management system for the Integreat app with, among others, the following features:

* Provide multilingual information for newcomers
* Regionally separated areas to support local integration experts
* Content management for pages, events and locations
* User management
* 2-factor-authentication
* Media library
* Integreat APIv3
* Statistics integration for Matomo
* PDF export
* XLIFF import/export
* Push notifications
* Auto saving
* Versioning system for pages
* Broken link checker
