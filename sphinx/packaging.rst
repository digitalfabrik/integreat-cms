*********
Packaging
*********

.. highlight:: bash

.. Attention::

    This guide is not the final packaging workflow and will probably change in the near future.


Create debian package
=====================

Packaging for Debian can be done with setuptools::

    pip3 install stdeb --user
    python3 setup.py --command-packages=stdeb.command bdist_deb

The project requires the package python3-django-widget-tweaks which has to be built manually::

    git clone git@github.com:jazzband/django-widget-tweaks.git
    cd django-widget-tweaks
    pip3 install stdeb
    python3 setup.py --command-packages=stdeb.command bdist_deb

Then install both packages with gdebi::

    apt install gdebi postgresql
    gdebi django-widget-tweaks/deb_dist/python3-django-widget-tweaks_1.4.3-1_all.deb
    gdebi |github-repository|/deb_dist/python3-integreat-cms_0.0.13-1_all.deb

In the end, create a PostgreSQL user and database and adjust the ``/usr/lib/python3/dist-packages/core/settings.py``.

.. Note::

    In some cases, you can just use the developer tool :github-source:`dev-tools/package.sh`::

        ./dev-tools/package.sh
