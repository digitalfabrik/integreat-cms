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
        "cffi==1.11.5",
        "Django==1.11.20",
        "django-mptt==0.9.1",
        "django-widget-tweaks==1.4.3",
        "djangorestframework==3.9.4",
        "drf-yasg==1.15.0",
        "idna==2.6",
        "psycopg2-binary==2.7.5",
        "python-dateutil==2.7.5",
        "rules==2.0.1",
        "six==1.11.0",
        "pylint==2.2.2",
        "pylint-django==2.0.4",
        "pylint_runner==0.5.4",
        "requests==2.21.0",
        "django-filer==1.5.0",
        "beautifulsoup4==4.7.1",
        "lxml==4.3.3",
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
