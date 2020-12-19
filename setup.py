#!/usr/bin/env python3
""" Setup.py """

import os
import sys

from setuptools import find_packages, setup

# Add source directory to PATH variable to enable import of version number
sys.path.append(os.path.abspath("src"))
# pylint: disable=wrong-import-position
from backend.settings import VERSION

setup(
    name="integreat-cms",
    version=VERSION,
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    scripts=["src/integreat-cms-cli"],
    data_files=[
        (f"lib/integreat-{root}", [os.path.join(root, f) for f in files])
        for root, _, files in os.walk("src/cms/templates/")
    ]
    + [
        (f"lib/integreat-{root}", [os.path.join(root, f) for f in files])
        for root, _, files in os.walk("src/cms/static/")
    ]
    + [("usr/lib/systemd/system/", ["systemd/integreat-cms@.service"])],
    install_requires=[
        "cffi",
        "Django~=2.2.13",
        "django-cors-headers",
        "django-filer",
        "django-mptt",
        "django-widget-tweaks",
        "feedparser",
        "idna",
        "lxml",
        "psycopg2-binary",
        "python-dateutil",
        "requests",
        "rules",
        "six",
        "webauthn",
        "xhtml2pdf",
    ],
    author="Integreat App Project",
    author_email="info@integreat-app.de",
    description="Content Management System for the Integreat App",
    license="GPL-2.0-or-later",
    keywords="Django Integreat CMS",
    url="http://github.com/Integreat/",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
    ],
)
