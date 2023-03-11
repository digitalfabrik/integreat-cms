********************************
Debugging (Django Debug Toolbar)
********************************

We use the :doc:`django-debug-toolbar:index` to debug the CMS.
When :setting:`django:DEBUG` is ``True``, on every HTML page a sidebar is rendered which contains
additional information about the current request, e.g. code execution times, database queries and profiling info.

When the sidebar is collapsed, you can show it by clicking on the "DJDT" button somewhere along the right edge of the screen:

.. image:: images/django-debug-toolbar.png
   :alt: DJDT sidebar

In order to use this for JSON views, you have to append ``?debug`` to the URL, e.g.::

    http://localhost:8000/api/augsburg/de/pages?debug

(See :class:`~integreat_cms.api.middleware.json_debug_toolbar_middleware.JsonDebugToolbarMiddleware` for reference.)
