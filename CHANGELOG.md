UNRELEASED
----------

* [ [#1162](https://github.com/digitalfabrik/integreat-cms/issues/1162) ] Allow management role to delete imprint
* [ [#765](https://github.com/digitalfabrik/integreat-cms/issues/765) ] Add extended view tests
* [ [#765](https://github.com/digitalfabrik/integreat-cms/issues/765) ] Add tests of form submissions
* [ [#1163](https://github.com/digitalfabrik/integreat-cms/issues/1163) ] Fix error when editor creates new page
* [ [#1165](https://github.com/digitalfabrik/integreat-cms/issues/1165) ] Fix bulk action button for sub pages
* [ [#1173](https://github.com/digitalfabrik/integreat-cms/issues/1173) ] Fix bug where unused location is preselected for new event
* [ [#1166](https://github.com/digitalfabrik/integreat-cms/issues/1166) ] Fix creation of location from event form
* [ [#1172](https://github.com/digitalfabrik/integreat-cms/issues/1172) ] Fix filtering for locations in event list
* [ [#1185](https://github.com/digitalfabrik/integreat-cms/issues/1185) ] Fix feedback API
* [ [#1188](https://github.com/digitalfabrik/integreat-cms/issues/1188) ] Fix error in broken link checker


2022.2.0-beta
-------------

* [ [#1065](https://github.com/digitalfabrik/integreat-cms/issues/1065) ] Fix APIv3 single page endpoint for multiple translation versions
* [ [#1077](https://github.com/digitalfabrik/integreat-cms/issues/1077) ] Fix error when deleting a poi that is used by an event
* [ [#844](https://github.com/digitalfabrik/integreat-cms/issues/844) ] Add tutorial to page tree view
* [ [#1030](https://github.com/digitalfabrik/integreat-cms/issues/1030) ] Fix layout of language tabs in forms
* [ [#1017](https://github.com/digitalfabrik/integreat-cms/issues/1017) ] Add support for Python 3.9
* [ [#19](https://github.com/digitalfabrik/integreat-cms/issues/19) ] Add APIv3 parents/ancestors endpoint
* [ [#1023](https://github.com/digitalfabrik/integreat-cms/issues/1023) ] Add API tests
* [ [#943](https://github.com/digitalfabrik/integreat-cms/issues/943) ] Improve performance of feedback list
* [ [#1088](https://github.com/digitalfabrik/integreat-cms/issues/1088) ] Replace django-mptt by django-treebeard
* [ [#943](https://github.com/digitalfabrik/integreat-cms/issues/943) ] Improve performance of page tree, event and POI lists
* [ [#943](https://github.com/digitalfabrik/integreat-cms/issues/943) ] Improve performance of page, event and POI API endpoints
* [ [#642](https://github.com/digitalfabrik/integreat-cms/issues/642) ] Add database migrations
* [ [#1103](https://github.com/digitalfabrik/integreat-cms/issues/1103) ] Add bulk actions for events and POIs
* [ [#943](https://github.com/digitalfabrik/integreat-cms/issues/943) ] Improve performance of content forms
* [ [#943](https://github.com/digitalfabrik/integreat-cms/issues/943) ] Improve performance of translation coverage view
* [ [#1134](https://github.com/digitalfabrik/integreat-cms/issues/1134) ] Support legacy XLIFF export for MemoQ WPML filter
* [ [#943](https://github.com/digitalfabrik/integreat-cms/issues/943) ] Improve performance of content searches
* [ [#1101](https://github.com/digitalfabrik/integreat-cms/issues/1101) ] Fetch subpages of page tree gradually
* [ [#1143](https://github.com/digitalfabrik/integreat-cms/issues/1143) ] Hide "Responsible organization" field in page form if no organizations exist
* [ [#1151](https://github.com/digitalfabrik/integreat-cms/issues/1151) ] Add possibility to delete languages
* [ [#1106](https://github.com/digitalfabrik/integreat-cms/issues/1106) ] Add possibility to delete offer templates


2021.12.0-beta
--------------

* [ [#943](https://github.com/digitalfabrik/integreat-cms/issues/943) ] Improve performance of region list
* [ [#1031](https://github.com/digitalfabrik/integreat-cms/issues/1031) ] Fix duplicating pages of deleted authors
* [ [#1028](https://github.com/digitalfabrik/integreat-cms/issues/1028) ] Fix page permissions
* [ [#1048](https://github.com/digitalfabrik/integreat-cms/issues/1048) ] Show recurrence in event list
* [ [#992](https://github.com/digitalfabrik/integreat-cms/issues/992) ] Only show upcoming events per default
* [ [#1044](https://github.com/digitalfabrik/integreat-cms/issues/1044) ] Allow configuration via /etc/integreat-cms.ini
* [ [#1044](https://github.com/digitalfabrik/integreat-cms/issues/1044) ] Fix dependency versions for production setup
* [ [#968](https://github.com/digitalfabrik/integreat-cms/issues/968) ] Fully functional media library in selection window
* [ [#1029](https://github.com/digitalfabrik/integreat-cms/issues/1029) ] Align language flags and translation status icons
* [ [#1062](https://github.com/digitalfabrik/integreat-cms/issues/1062) ] Fix error when replacing media files without thumbnail
* [ [#931](https://github.com/digitalfabrik/integreat-cms/issues/931) ] Add search function for media library


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
