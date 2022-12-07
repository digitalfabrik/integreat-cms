**********************************
Integreat Django CMS documentation
**********************************

This is the developer documentation for the Integreat Django backend.

For general help with the Django framework, please refer to the :doc:`django:index`.


First Steps
===========

.. toctree::
    :caption: First Steps
    :hidden:

    installation
    dev-server
    tutorials
    dev-tools
    troubleshooting

* :doc:`installation`: Installation guide
* :doc:`dev-server`: Run local development server
* :doc:`tutorials`: Step-by-step guides
* :doc:`dev-tools`: Scripts for developers
* :doc:`troubleshooting`: General problem solving guide


Project Architecture / Reference
================================

.. toctree::
    :caption: Reference
    :hidden:

    ref/integreat_cms
    ref/tests

* :doc:`ref/integreat_cms`: The main package of the integreat-cms with the following sub-packages:

  - :doc:`ref/integreat_cms.api`: This app provides wrapper functions around all API routes and classes mapping the cms models to API JSON responses.
  - :doc:`ref/integreat_cms.cms`: This app contains all database models, views, forms and templates forming the content management system for backend users.
  - :doc:`ref/integreat_cms.core`: This is the project’s main app which contains all configuration files.
  - :doc:`ref/integreat_cms.firebase_api`: This app provides wrapper functions around the Firebase API to send push notifications.
  - :doc:`ref/integreat_cms.gvz_api`: This app provides wrapper functions around our Gemeindeverzeichnis API to automatically import coordinates and region aliases.
  - :doc:`ref/integreat_cms.nominatim_api`: This app provides wrapper functions around our Nominatim API to automatically import region bounding boxes.
  - :doc:`ref/integreat_cms.sitemap`: This app dynamically generates a sitemap.xml for the webapp.
  - :doc:`ref/integreat_cms.summ_ai_api`: This app provides wrapper functions around the SUMM.AI API for automatic translations into Easy German.
  - :doc:`ref/integreat_cms.xliff`: This app allows (de-)serialization of translations from/to XLIFF (XML Localization Interchange File Format) for standardised exchange with translation agencies.

* :doc:`ref/tests`: This app contains all tests to verify integreat-cms works as intended

To better understand the overall intention it might also be helpful to look at the `wiki for municipalities (GER) <https://wiki.integreat-app.de/>`_ that teaches how to use our CMS.


.. toctree::
    :caption: Extended Reference
    :hidden:

    ref-ext/integreat_cms
    ref-ext/tests


Basic Concepts
==============

.. toctree::
    :caption: Basic Concepts
    :hidden:

    virtualenv
    internationalization
    frontend-bundling
    testing
    documentation
    continuous-integration

* :doc:`virtualenv`: Virtual Python environment and Pipenv
* :doc:`internationalization`: Multi-language support for the backend UI
* :doc:`frontend-bundling`: Work on frontend assets
* :doc:`testing`: How to test this application
* :doc:`documentation`: This Sphinx documentation
* :doc:`continuous-integration`: Continuous Integration and Delivery with CircleCI


Deployment
==========

.. toctree::
    :caption: Deployment
    :hidden:

    packaging
    prod-server
    changelog

* :doc:`packaging`: Create an easy installable package
* :doc:`prod-server`: Run the production server
* :doc:`changelog`: The release history including all relevant changes


Contributing
============

.. toctree::
    :caption: Contributing
    :hidden:

    issue-reporting
    pull-request-review-guide
    code-style
    git-flow
    code-of-conduct

* :doc:`issue-reporting`: Rug Reporting and Feature Request Guidelines
* :doc:`pull-request-review-guide`: Tips for reviewing pull requests
* :doc:`code-style`: Coding Conventions
* :doc:`git-flow`: GitHub Workflow model
* :doc:`code-of-conduct`: Contributor Covenant Code of Conduct


Indices
=======

.. toctree::
    :caption: Indices
    :hidden:

    Glossary <https://wiki.tuerantuer.org/glossary>

* `Glossary <https://wiki.tuerantuer.org/glossary>`_: List of terms and definitions
* :ref:`Full Index <genindex>`: List of all documented classes, functions and attributes
* :ref:`Python Module Index <modindex>`: List of all python modules in this project
* :ref:`search`: Search documentation
