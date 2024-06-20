*****************
API Documentation
*****************

Sending the Development Header
==============================

To prevent tracking of API calls during tests and development, use the
"X-Integreat-Development" header. Example:

::

   curl -H "X-Integreat-Development: true"  \
   https://cms.integreat-app.de/testumgebung/de/wp-json/extensions/v3/pages



.. _api_regions:

Regions
=======

REQUEST
~~~~~~~

Get all regions

.. code:: http

   GET /api/v3/regions/ HTTP/2

Deprecated url:

.. code:: http

    GET /wp-json/extensions/v3/sites/regions/ HTTP/2

RESPONSE
~~~~~~~~

.. code:: javascript

   [
     {
       "id": Number,                    // id of region
       "name": String,                  // prefix + name of region
       "path": String,                  // path to site (without host)
       "live": Boolean,                 // determines if the region is live or hidden
       "prefix": String | null,         // prefix of region name, e.g. "Stadt"
       "name_without_prefix": String,   // region name without prefix
       "plz": Number | null,            // plz (Postleitzahl/ZIP) of region
       "extras": Boolean,               // true if at least one extra is enabled
       "events": Boolean,               // true if events are enabled
       "pois": Boolean,                 // true if points of interest are enabled
       "push_notifications": Boolean,   // true if push-notifications are enabled
       "longitude": Number | null,      // longitude of the geographic center of the region
       "latitude": Number | null,       // latitude of the geographic center of the region
       "bounding_box": [                // The bounding box of the region, containing two coordinates
            [Number, Number], [Number, Number]
        ],
       "aliases": {                     // value can also be NULL
           "<alias>": {                 // name of a region alias (smaller municipality within a region)
               "longitude": Number,     // longitude of the geographic center of the region alias
               "latitude": Number,      // latitude of the geographic center of the region alias
           } | null,
           ...
        }
       "tunews": Boolean,               // true if TüNews are enabled
       "external_news": Boolean,       // true if external news provider are enabled
       "languages": [
         {
            "id": Number,
            "code": String,              // language-code, e.g. "de" or "en"
            "bcp47_tag": String,
            "native_name": String,
            "dir": String                // reading direction {"ltr"|"rtl"}
         },
         ...
        ],
        "is_chat_enabled": Boolean,     // whether the Integreat Chat is enabled for the region
     },
     ...
   ]

REQUEST
~~~~~~~

Get a single region by slug:

.. code:: http

   GET /api/v3/regions/{region_slug}/ HTTP/2

Deprecated url:

.. code:: http

    GET /wp-json/extensions/v3/sites/regions/{region_slug}/ HTTP/2

RESPONSE
~~~~~~~~

A single object following the layout of :ref:`api_regions`


Social Media
============

Get social media headers for a frontend url

REQUEST
~~~~~~~

Get the social media headers for a frontend url.
The absolute url is the `path to resource <https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/What_is_a_URL#path_to_resource>`_ of the frontent url

.. code:: http

   GET /api/v3/social/{absolute_url}/ HTTP/2

.. code:: http

   GET /api/v3/social/ HTTP/2

RESPONSE
~~~~~~~~

Rendered HTML that contains social media headers describing the object of the given url.
Please keep in mind that the response contains partial ``<html>`` and ``<head>`` tags to allow the response to contain a language attribute in the root tag.
This needs to be equalized in the server-side include e.g. as follows:

.. code:: html

    <!-- Nginx Server Side Include template for dynamic social media previews -->
    <!--# if expr="$render_title = yes" -->
    <!--# include virtual="/proxy/socialmeta/$request_uri" -->
    <!--# else -->
    <html>
        <head>
    <!--# endif -->


Languages
=========

Get all available languages of a region
(this endpoint is deprecated, you can directly use the ``languages`` attribute of the region response)

REQUEST
~~~~~~~

.. code:: http

    GET /api/v3/{region_slug}/languages/ HTTP/2

Deprecated url:

.. code:: http

   GET /{region_slug}/de/wp-json/extensions/v3/languages/ HTTP/2

RESPONSE
~~~~~~~~

.. code:: javascript

   [
     {
       "id": Number,
       "code": String,                // language-code, e.g. "de" or "en"
       "bcp47_tag": String,
       "native_name": String,
       "dir": String                  // reading direction {"ltr"|"rtl"}
     },
     ...
   ]


Offers / Extras
===============

Get all enabled offers (also called extras) for a specific region

REQUEST
~~~~~~~

The language slug, if specified, will be ignored

.. code:: http

    GET /api/v3/{region_slug}/{offers/extras}/ HTTP/2

Deprecated url:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/{offers/extras}/ HTTP/2

RESPONSE
~~~~~~~~

.. code:: javascript

   [
     {
       "name": String,         // name of offer
       "alias": String,        // alias (slug) of offer
       "url": String,          // url to offer
       "post": Object | null,  // post-data (key & value pairs) for url (if needed) as json-object
       "thumbnail": String,    // url of thumbnail
     },
     ...
   ]


.. _api_pages:

Pages
=====

Get all non-archived pages of a region

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/pages/ HTTP/2

Deprecated url:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/pages/ HTTP/2


RESPONSE
~~~~~~~~

.. code:: javascript

   [
      {
         "id": Number,                 // The id of the page
         "url": String,                // The url of the page
         "path": String,               // The path to the page, without host
         "title": String,              // The title of the page
         "modified_gmt": String,       // Deprecated field
         "last_updated": String,       // When the page translation was last updated, in ISO 8601
         "excerpt": String,            // An excerpt from the page translation content
         "content": String,            // The full content
         "parent": {                   // The parent of this page
            "id": Number,              // The id of the parent
            "url": String | null,      // The url field of the page
            "path": String | null,     // The path field of the parent
         },
         "order": Number,              // The order of the page (Left edge indicator of the mptt model)
         "available_languages": [      // A list with all languages of this page
            "<language_slug>": {
               "id": Number,           // The id of the translation
               "url": String,          // The path field of the translation
               "path": String,         // The path field of the translation
            },
            ...
         ],
         "thumbnail": String | null,   // The thumbnail url of this page
         "organization": {             // The organization of the page, if any
               "id": Number,           // The id of the organization
               "slug": String,         // The slug of the organization
               "name": String,         // The name of the organization
               "logo": String,         // The icon url of the organization
               "website": String,      // The url of the organization website
         } | null,
         "hash": null,                 // Currently always null
         "embedded_offers": [           // A (possibly empty) list of embedded offers
              {
                "name": String,        // name of offer
                "alias": String,       // alias (slug) of offer
                "url": String,         // url to offer
                "post": Object | null, // post-data (key & value pairs) for url (if needed) as json-object
                "thumbnail": String,   // url of thumbnail
              },
                ...
        ],
      },
      ...
   ]



Locations
=========

Get all location translations of a region

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/locations/ HTTP/2

Deprecated url:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/locations/ HTTP/2


RESPONSE
~~~~~~~~

.. code:: javascript

   [
      {
         "id": Number,                   // The id of this location
         "url": String,                  // The url of this location
         "path": String,                 // The path of this location, without host
         "title": String,                // The title of this location
         "modified_gmt": String,         // Deprecated field
         "last_updated": String,         // When the location translation was last updated, in ISO 8601
         "meta_description": String,     // The meta description of this location
         "excerpt": String,              // An excerpt from the content of the location
         "content": String,              // The content of the location
         "appointment_url": String | null,// The URL to where an appointment can be made
         "available_languages": [        // The translations of this location
            "<language_slug>": {
               "id": Number,             // The id of the translation
               "url": String,            // The path field of the translation
               "path": String,           // The path field of the translation
            },
            ...
         ],
         "icon": String | null,          // the url to the icon for this location
         "thumbnail": String | null,     // The thumbnail url for this location
         "website": String | null,       // The website for this location
         "email": String | null,         // The email for this location
         "phone_number": String | null,  // The phone number for this location
         "category": {                   // The category of this location
            "id": Number,                // The id of the category
            "name": String,              // The translated name of the category
            "color": String | null,      // The color of the category, in the format #RRGGBB
            "icon": String | null,       // The icon name of the category
            "icon_url": String,          // The url of the icon
         },
         "temporarily_closed": Boolean,  // Whether this location is temporarily closed
         "opening_hours": [              // The opening hours for the location
            {                            // The opening hours for day 0 (Monday)
               "allDay": Boolean,        // Whether the location is all day open
               "closed": Boolean,        // Whether the location is all day closed
               "appointmentOnly": Boolean,// Whether the location is accessible by prior appointment only
               "timeSlots": [            // If allDay and closed are false, the timeslots for this day, when the location is open
                  {
                     "start": String,    // The start time of the timeslot, in the format `HH:MM`, 24 Hour time
                     "end": String,      // The end time of the timeslot
                  },
                  ...
               ],
            },
            ...
         ] | null,
         "location": {                   // The the location for this location translation
            "id": Number | null,         // The id of this location
            "name": String | null,       // The name of this location
            "address": String | null,    // The address of this location
            "town": String | null,       // The town of this location
            "state": null,               // Currently always null
            "postcode": String | null,   // The postcode of this location
            "region": null,              // Currently always null
            "country": String | null,    // The country of this location
            "latitude": Number | null,   // The latitude of this location
            "longitude": Number | null,  // The longitude of this location
         },
         "hash": null,                   // Currently always null
         "organization": {               // The organization of the location, if any
               "id": Number,             // The id of the organization
               "slug": String,           // The slug of the organization
               "name": String,           // The name of the organization
               "logo": String,           // The icon url of the organization
               "website": String,        // The url of the organization website
         } | null,
         "barrier_free": Boolean,        // Whether this location is barrier free
      },
      ...
   ]


Location Categories
===================

Get all location categories

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/location-categories/ HTTP/2

Deprecated url:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/location-categories/ HTTP/2


RESPONSE
~~~~~~~~

.. code:: javascript

   [
      {
         "id": Number,        // The id of the category
         "name": String,      // The translated name of the category
         "color": String,     // The color of the category, in the format #RRGGBB
         "icon": String,      // The icon name of the category
         "icon_url": String,  // The url of the icon
      },
      ...
   ]


Events
======

Get events for this region

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/events/ HTTP/2

Deprecated url:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/events/ HTTP/2


RESPONSE
~~~~~~~~

.. code:: javascript

   [
      {
         "id": Number | null,               // The id of this event, null if this is a recurrence of an event
         "url": String,                     // The url of this event
         "path": String,                    // The path of this event, without host
         "title": String,                   // The title of this event
         "modified_gmt": String,            // Deprecated field
         "last_updated": String,            // When the event translation was last updated, in ISO 8601
         "excerpt": String,                 // An excerpt from the content of the event
         "content": String,                 // The content of the event
         "available_languages": [           // The translations of this event
            "<language_slug>": {
               "id": Number | null,           // The id of the translation
               "url": String,                 // The path field of the translation
               "path": String,                // The path field of the translation
            },
            ...
         ],
         "thumbnail": String | null,        // The url to the thumbnail for this event
         "location": {                      // The the location for this event translation
            "id": Number | null,            // The id of this location
            "name": String | null,          // The name of this location
            "address": String | null,       // The address of this location
            "town": String | null,          // The town of this location
            "state": null,                  // Currently always null
            "postcode": String | null,      // The postcode of this location
            "region": null,                 // Currently always null
            "country": String | null,       // The country of this location
            "latitude": Number | null,      // The latitude of this location
            "longitude": Number | null,     // The longitude of this location
         },
         "location_url": String | null,     // The url to the location for this event translation
         "event": {
            "id": Number | null,            // The id of this event. Null if this is a recurrence of an event
            "start": String,                // The start date&time of this event
            "start_date": String,           // Deprecated field
            "start_time": String,           // Deprecated field
            "end": String,                  // The end date&time of this event
            "end_date": String,             // Deprecated field
            "end_time": String,             // Deprecated field
            "all_day": Boolean,             // Whether this event is active the entire day
            "recurrence_id": Number | null, // The id of the recurrence rule of this event
            "timezone": String,             // The timezone of this event, e.g. Europe/Berlin
         },
         "hash": null,                      // Currently always null
         "recurrence_rule": String | null,  // The recurrence rule as an ical_rrule string (See https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html)
      },
      ...
   ]


Single Page
===========

Get a single page translation

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/page/?id={page_id} HTTP/2


.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/page/?url={page_url} HTTP/2


Deprecated urls:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/page/?id={page_id} HTTP/2

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/page/?url={page_url} HTTP/2


RESPONSE
~~~~~~~~

A single object following the layout of :ref:`api_pages`


Page Children
=============

Get the child pages of a specific page, or the child pages for all root pages in the region.
If the id and url parameters are left out, the page children of all root pages will be returned.
If the depth parameter is left out, only the direct children (depth 1) will be returned

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/children/?id={page_id}&depth={depth} HTTP/2


.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/children/?url={page_url}&depth={depth} HTTP/2


Deprecated urls:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/children/?id={page_id}&depth={depth} HTTP/2

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/children/?url={page_url}&depth={depth} HTTP/2

RESPONSE
~~~~~~~~

Returns a list of pages, as defined at :ref:`api_pages`.
This contains the queried page(s).


Page Parents
============

Get all parents for a specific page

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/parents/?id={page_id} HTTP/2


.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/parents/?url={page_url} HTTP/2


Deprecated urls:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/parents/?id={page_id} HTTP/2

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/parents/?url={page_url} HTTP/2

RESPONSE
~~~~~~~~

Returns a list of pages, as defined at :ref:`api_pages`.
This does not contain the queried page.


PDF
===

Export page translations as pdf.
If the url parameter is left out, a pdf containing all root pages of the region will be returned

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/pdf/?url={page_url} HTTP/2

Deprecated urls:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/pdf/?url={page_url} HTTP/2

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/ig-mpdf/v1/pdf/?url={page_url} HTTP/2


RESPONSE
~~~~~~~~

A redirect to the pdf url


FCM
===

Get all sent push notifications for this region

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/fcm/ HTTP/2

Deprecated url:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/fcm/ HTTP/2

RESPONSE
~~~~~~~~

.. code:: javascript

   {
      "id": String,            // The id of the push notification translation
      "title": String,         // The title of the push notification in the given language
      "message": String,       // The message of the push notification in the given language
      "timestamp": String,     // Deprecated field
      "last_updated": String,  // The date&time when the push notification was last updated
      "channel": String,       // The channel the push notification was sent to (e.g. "News")
      "available_languages": [           // The available languages of the push notification
            "<language_slug>": {
               "id": Number | null,           // The id of the translation
            },
            ...
         ]
   }


Imprint / Disclaimer
====================

Get the imprint (Also named disclaimer) for the given region in the given language

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{language_slug}/{imprint,disclaimer}/ HTTP/2

Deprecated url:

.. code:: http

   GET /{region_slug}/{language_slug}/wp-json/extensions/v3/{imprint,disclaimer}/ HTTP/2

Response
~~~~~~~~

.. code:: javascript

   {
      "id": Number              // The id of the imprint
      "url": String,            // The url of the imprint
      "path": String,           // The path to the imprint, without host
      "title": String,          // The title of the imprint
      "modified_gmt": String,   // Deprecated field
      "last_updated": String,   // When the imprint translation was last updated, in ISO 8601
      "excerpt": String,        // An excerpt from the imprint content
      "content": String,        // The full content
      "parent": null,           // Currently always null
      "available_languages": [  // A list with all languages of this imprint
         "<language_slug>": {
            "id": Number,       // The id of the translation
            "url": String,      // The path field of the translation
            "path": String,     // The path field of the translation
         },
         ...
      ],
      "thumbnail": null,       // Currently always null
      "hash": null,            // Currently always null
   }


Push Page Content
=================

Update a page translation

REQUEST
~~~~~~~

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/pushpage HTTP/2
   Content-Type: application/json

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/pushpage HTTP/2
   Content-Type: application/json

Body:

.. code:: javascript

   {
      "token": "<Token for the page translation>",
      "content": "<The content to be pushed>",
   }

Response
~~~~~~~~

.. code:: javascript

   {
      "status": String // "success", "error", "denied"
   }


Feedback
========

Legacy-Endpoint for Page/Event/Disclaimer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a legacy endpoint. Use the endpoints for page, event, imprint
page resp. Feedback about a single page, event or imprint (also
called "disclaimer")

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "permalink": String | null,      // permalink of the page/event (required)
      "comment": String,               // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null,  // up- or downvote (either comment or rating is required)
      "category": String | null,       // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Categories
~~~~~~~~~~

Feedback for regions

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/categories HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/categories HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "comment": String,               // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null,  // up- or downvote (either comment or rating is required)
      "category": String | null,       // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Page
~~~~

Feedback about a single page

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/page HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/page HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "slug": String | null,           // slug of the page (required)
      "comment": String,               // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null,  // up- or downvote (either comment or rating is required)
      "category": String | null,       // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

POI
~~~

Feedback about a point of interest

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/poi HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/poi HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "slug": String | null,           // slug of the event (required)
      "comment": String,               // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null,  // up- or downvote (either comment or rating is required)
      "category": String | null,       // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Event
~~~~~

Feedback about an event

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/event HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/event HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "slug": String | null,           // slug of the event (required)
      "comment": String,               // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null,  // up- or downvote (either comment or rating is required)
      "category": String | null,       // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Events
~~~~~~

Feedback about the event list (E.g. missing events)

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/events HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/events HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "slug": String | null,           // slug of the event (required)
      "comment": String,               // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null,  // up- or downvote (either comment or rating is required)
      "category": String | null,       // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Imprint Page
~~~~~~~~~~~~

Feedback about an imprint page

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/imprint-page HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/imprint-page HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "comment": String,               // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null,  // up- or downvote (either comment or rating is required)
      "category": String | null,       // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Map
~~~

Feedback about the map (E.g. missing points of interest)

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/map HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/map HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "comment": String,               // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null,  // up- or downvote (either comment or rating is required)
      "category": String | null,       // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Search
~~~~~~

Feedback about a search result

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/search HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/search HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "query": String,                 // query string of the search you want to comment on (required)
      "comment": String,               // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null,  // up- or downvote (either comment or rating is required)
      "category": String | null,       // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Offers
~~~~~~

Feedback about the offer list (E.g. missing offers)

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/{offers,extras} HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/{offers,extras} HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "comment": String,              // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null, // up- or downvote (either comment or rating is required)
      "category": String | null,      // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Offer
~~~~~

Feedback to a specific offer (also called "extra")

REQUEST
^^^^^^^

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/feedback/{offer,extra} HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Deprecated url:

.. code:: http

   POST /{region_slug}/{language_slug}/wp-json/extensions/v3/feedback/{offer,extra} HTTP/2
   Content-Type: multipart/form-data or application/x-www-form-urlencoded

Body:

.. code:: javascript

   {
      "slug": String,                 // slug of the extra you want to comment on (required)
      "comment": String,              // your message (either comment or rating is required)
      "rating": 'up' | 'down' | null, // up- or downvote (either comment or rating is required)
      "category": String | null,      // comment category ("Technisches Feedback" or null; any other string is treated like null)
   }

Chat
====

This endpoint provides chat functionality for Integreat app users.

REQUEST
~~~~~~~

.. code:: http

   GET /api/v3/{region_slug}/{device_id}/is_chat_enabled/ HTTP/2

RESPONSE
~~~~~~~~

.. code:: javascript

   {
      "is_chat_enabled": Boolean,   // whether chat functionality is enabled for the requesting user
   }

REQUEST
~~~~~~~

.. code:: http

    GET /api/v3/{region_slug}/{language_slug}/chat/{device_id}/ HTTP/2

.. code:: http

    GET /api/v3/{region_slug}/{language_slug}/chat/{device_id}/{attachment_id}/ HTTP/2

.. code:: http

   POST /api/v3/{region_slug}/{language_slug}/chat/{device_id}/ HTTP/2
   Content-Type: multipart/formdata

Body:

.. code:: javascript

   {
      "message": String,               // message the user wishes to send (required)
      "force_new": Boolean,            // whether to force a new chat instead of continuing existing  (optional)
   }


RESPONSE
~~~~~~~~

The response to ``POST``-ing to the endpoint is a single object representing
the message as it is stored in Zammad.

.. code:: javascript

   {
      "id": Number,                    // message id
      "body": String,                  // the actual message content
      "user_is_author": Boolean,       // true if the user sent the message, false otherwise
      "attachments": [],               // will always be an empty list
   }

The response to ``GET``-ing the endpoint without an ``attachment_id`` is a list containing all chat messages.

.. code:: javascript

   {
      "messages" : [                   // A list containing the chat messages
         "id": Number,                 // message id
         "body": String,               // the actual HTML-formatted message content
         "user_is_author": Boolean,    // true if the user sent the message, false otherwise
         "attachments": [              // A list containing attachments. Will be sent even if empty
            {
               "filename": String,     // The name of the file. May be empty
               "size": String,         // The size of the file in kilobytes as a string. May be empty
               "Content-Type": String, // The mimetype of the file. May be empty
               "id": String,           // A 64-character UID. Only field guaranteed to exist
            },
         ],
      ],
   }

In case an error occurs during communication with the Zammad backend,
it will be passed along in the following format, together with a matching HTTP status code.

.. code:: javascript

   {
      "error": String,                // error message
   }

The response to ``GET``-ing the endpoint with an ``attachment_id`` is either the (binary) file or an error in the format specified above.
