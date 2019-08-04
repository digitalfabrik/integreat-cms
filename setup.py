#!/usr/bin/env python3

import os
from setuptools import find_packages, setup

setup(
    name="integreat_cms",
    version="0.0.13",
    packages=find_packages("backend"),
    package_dir={'':'backend'},
    include_package_data=True,
    scripts=['backend/integreat-cms'],
    data_files= [("lib/integreat-{}".format(root), [os.path.join(root, f) for f in files])
                 for root, dirs, files in os.walk('backend/cms/templates/')] +
                [("lib/integreat-{}".format(root), [os.path.join(root, f) for f in files])
                 for root, dirs, files in os.walk('backend/cms/static/')] +
                [('usr/lib/systemd/system/', ['systemd/integreat-cms@.service'])],
    install_requires=[
        "beautifulsoup4==4.8.0",
        "cffi==1.12.3",
        "Django==1.11.20",
        "django-filer==1.5.0",
        "django-mptt==0.9.1",
        "django-widget-tweaks==1.4.3",
        "djangorestframework==3.9.4",
        "drf-yasg==1.16.1",
        "idna==2.6",
        "lxml==4.3.3",
        "psycopg2-binary==2.8.3",
        "pylint==2.3.1",
        "pylint-django==2.0.11",
        "pylint_runner==0.5.4",
        "python-dateutil==2.8.0",
        "requests==2.22.0",
        "rules==2.0.1",
        "six==1.11.0",
    ],
    author="Integreat App Project",
    author_email="info@integreat-app.de",
    description="Content Management System for the Integreat App",
    license="GPL-2.0-or-later",
    keywords="Django Integreat CMS",
    url="http://github.com/Integreat/",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
