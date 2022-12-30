UNRELEASED
----------

* Fix APIv3 single page endpoint for multiple translation versions
* Fix error when deleting a poi that is used by an event
* Add tutorial to page tree view
* Fix layout of language tabs in forms
* Add support for Python 3.9
* Add APIv3 parents/ancestors endpoint
* Add API tests
* Improve performance of feedback list
* Replace django-mptt by django-treebeard
* Improve performance of page tree, event and POI lists
* Improve performance of page, event and POI API endpoints


2021.12.0-beta
--------------

* Improve performance of region list
* Fix duplicating pages of deleted authors
* Fix page permissions
* Show recurrence in event list
* Only show upcoming events per default
* Allow configuration via /etc/integreat-cms.ini
* Fix dependency versions for production setup
* Fully functional media library in selection window
* Align language flags and translation status icons
* Fix error when replacing media files without thumbnail
* Add search function for media library


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
