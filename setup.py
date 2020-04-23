#!/usr/bin/env python3
""" Setup.py """

import os
import sys

from setuptools import find_packages, setup

# Add source directory to PATH variable to enable import of version number
sys.path.append(os.path.abspath('src'))
# pylint: disable=wrong-import-position
from backend.settings import VERSION

# pylint: disable=bad-continuation
setup(
    name='integreat_cms',
    version=VERSION,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    scripts=['src/integreat-cms-cli'],
    data_files=[('lib/integreat-{}'.format(root), [os.path.join(root, f) for f in files])
                for root, dirs, files in os.walk('src/cms/templates/')] +
               [('lib/integreat-{}'.format(root), [os.path.join(root, f) for f in files])
                for root, dirs, files in os.walk('src/cms/static/')] +
               [('usr/lib/systemd/system/', ['systemd/integreat-cms@.service'])],
    install_requires=[
        'beautifulsoup4',
        'cffi',
        'Django~=2.2.10',
        'django-cors-headers',
        'django-filer',
        'django-mptt',
        'django-widget-tweaks',
        'idna',
        'lxml',
        'psycopg2-binary',
        'python-dateutil',
        'requests',
        'rules',
        'six',
        'webauthn',
    ],
    extras_require={
        'dev': [
            'django-compressor',
            'django-compressor-toolkit',
            'packaging',
            'pylint',
            'pylint-django',
            'pylint_runner',
            'sphinx',
            'sphinxcontrib-django',
            'sphinx_rtd_theme',
        ]
    },
    author='Integreat App Project',
    author_email='info@integreat-app.de',
    description='Content Management System for the Integreat App',
    license='GPL-2.0-or-later',
    keywords='Django Integreat CMS',
    url='http://github.com/Integreat/',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.7',
    ]
)
