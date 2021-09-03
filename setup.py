#!/usr/bin/env python3
""" Setup.py """

from setuptools import find_packages, setup


package_name = "integreat-cms"
package_dir = "integreat_cms"
version = "2021.11.0-beta"


def readme():
    """
    Read the readme file which is intended for the description on PyPI

    :return: The contents of the readme file
    :rtype: str
    """
    with open(f"{package_dir}/README.md", mode="r", encoding="utf8") as f:
        return f.read()


setup(
    name=package_name,
    version=version,
    packages=find_packages(),
    include_package_data=True,
    scripts=[f"{package_dir}/integreat-cms-cli"],
    install_requires=[
        "aiohttp",
        "argon2-cffi",
        "bcrypt",
        "cffi",
        "Django>=3.2,<4.0",
        "django-cacheops",
        "django-cors-headers",
        "django-debug-toolbar",
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
    long_description=readme(),
    long_description_content_type="text/markdown",
    license="GPL-2.0-or-later",
    keywords="Django Integreat CMS",
    url="http://github.com/Integreat/",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
    ],
)
