#!/usr/bin/env python3
""" Setup.py """

from setuptools import find_packages, setup

from integreat_cms.backend.settings import VERSION


package_name = "integreat-cms"
package_dir = "integreat_cms"

setup(
    name=package_name,
    version=VERSION,
    packages=find_packages(),
    include_package_data=True,
    scripts=[f"{package_dir}/integreat-cms-cli"],
    data_files=[
        ("etc/apache2/site-available", ["example-configs/apache2-integreat-vhost.conf"])
    ],
    install_requires=[
        "aiohttp",
        "argon2-cffi",
        "bcrypt",
        "cffi",
        "Django>=3.2,<4.0",
        "django-cacheops",
        "django-cors-headers",
        "django-linkcheck",
        "django-mptt",
        "django-redis",
        "django-widget-tweaks",
        "django-webpack-loader",
        "feedparser",
        "idna",
        "lxml",
        "Pillow",
        "psycopg2-binary",
        "python-dateutil",
        "python-magic",
        "requests",
        "rules",
        "six",
        "webauthn==0.4.7",
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
