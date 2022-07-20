****************
Testing (Pytest)
****************


We use :doc:`pytest <pytest:index>` to validate that the functionality of the cms works as expected.

In addition, we use the following plugins:

* :doc:`pytest-cov <pytest-cov:index>`: This plugin produces coverage reports.
* :doc:`pytest-django <pytest-django:index>`: Provide a few helpers for Django
* :doc:`pytest-xdist:index`: Enable distributing tests across multiple CPUs to speed up test execution

For more information, see :doc:`django:topics/testing/index` and :doc:`django:topics/testing/overview`.

For reference of our test framework and test cases, see :mod:`tests`.


Coverage
========

After each run, the test coverage is uploaded to `CodeClimate <https://codeclimate.com/github/digitalfabrik/integreat-cms>`__ (see :ref:`circleci-upload-test-coverage`).


Test API with WebApp
====================

To test the API in the web app with a different CMS server, open the JavaScript console of the web app and execute::

    window.localStorage.setItem('api-url', 'https://cms-test.integreat-app.de')
