********
Glossary
********


User management
===============

* Superuser/Superadmin:

    User with unrestricted access to all backend functionality, including the Django Admin backend.
    Only developers should be granted this role.

* Staff:

    Staff members of Integreat with access to multiple regions and access to administrative functionality.
    These users should handle all organizational tasks and should be able to manage regions, languages and other users.

* Region User:

    These users are external collaborators who manage the content of a single region.
    Typically these are officials of an administrative division responsible for informing newcomers in their region.


Content Types
=============

Information is stored in different forms.
translated into multiple languages.

* Page:

    A :class:`~cms.models.pages.page.Page` contains (more or less static) information about a specific topic.

* Event:

    An :class:`~cms.models.events.event.Event` contains information about time, location and purpose of an event.

* POI (Point of Interest):

    A :class:`~cms.models.pois.poi.POI` contains information about interesting places including address and coordinates.


Backend
=======

* Slug:

    Unique identifier consisting from only alphanumeric characters, hyphens and underscores.

* Dashboard:

    Start page for all users with tiles which give an overview over most important topics
