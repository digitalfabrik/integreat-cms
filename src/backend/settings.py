"""
Django settings for backend project.

For more information on this file, see :doc:`topics/settings`.
For the full list of settings and their values, see :doc:`ref/settings`.

For production use, the following settings can be set with environment variables:
* SECRET_KEY
* DEBUG
* ALLOWED_HOSTS via BASE_URL
* WEBAPP_URL
* BASE_URL
* WEBAPP_URL
* STATIC_ROOT
* MEDIA_ROOT
* Database settings

Our custom settings
===================

.. setting:: WEBAPP_URL

``WEBAPP_URL``
--------------

Default: ``https://integreat.app``

The URL to our webapp. This is used for urls in the ``sitemap.xml`` (see :mod:`sitemap` for more information).

.. setting:: GVZ_API_URL

``GVZ_API_URL``
--------------

Default: ``https://gvz.integreat-app.de/api/``

The URL to our GVZ (Gemeindeverzeichnis) API. This is used to automatically import coordinates and region aliases (see
:mod:`gvz_api` for more information).

.. setting:: GVZ_API_ENABLED

``GVZ_API_ENABLED``
--------------

Default: ``True``

Whether or not the GVZ (Gemeindeverzeichnis) API is enabled (see :mod:`gvz_api` for more information).
"""
import os
import urllib

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Version number
VERSION = "0.0.14"

#: How many days of chat history should be shown
AUTHOR_CHAT_HISTORY_DAYS = 30

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
if "DJANGO_SECRET_KEY" in os.environ:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
else:
    SECRET_KEY = "-!v282$zj815_q@htaxcubylo)(l%a+k*-xi78hw*#s2@i86@_"

# SECURITY WARNING: don't run with debug turned on in production!
if "DJANGO_DEBUG" in os.environ:
    DEBUG = bool(os.environ["DJANGO_DEBUG"])
else:
    DEBUG = True

if "DJANGO_BASE_URL" in os.environ:
    ALLOWED_HOSTS = [urllib.parse.urlparse(os.environ["DJANGO_BASE_URL"]).netloc]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

if "DJANGO_BASE_URL" in os.environ:
    HOSTNAME = urllib.parse.urlparse(os.environ["DJANGO_BASE_URL"]).netloc
    BASE_URL = os.environ["DJANGO_BASE_URL"]
else:
    BASE_URL = "http://localhost:8000"
    HOSTNAME = "localhost"

if "DJANGO_WEBAPP_URL" in os.environ:
    WEBAPP_URL = os.environ["DJANGO_WEBAPP_URL"]
else:
    WEBAPP_URL = "https://integreat.app"

# Custom slugs
IMPRINT_SLUG = "imprint"

# Application definition

INSTALLED_APPS = [
    "cms.apps.CmsConfig",
    "gvz_api.apps.GvzApiConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "compressor",
    "compressor_toolkit",
    "corsheaders",
    "widget_tweaks",
    "easy_thumbnails",
    "filer",
    "mptt",
    "rules.apps.AutodiscoverRulesConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"
THUMBNAIL_HIGH_RESOLUTION = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "backend.context_processors.region_slug_processor",
            ],
            "debug": DEBUG,
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

if (
    "DJANGO_DB_HOST" in os.environ
    and "DJANGO_DB_NAME" in os.environ
    and "DJANGO_DB_PASSWORD" in os.environ
    and "DJANGO_DB_USER" in os.environ
    and "DJANGO_DB_PORT" in os.environ
):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ["DJANGO_DB_NAME"],
            "USER": os.environ["DJANGO_DB_USER"],
            "PASSWORD": os.environ["DJANGO_DB_PASSWORD"],
            "HOST": os.environ["DJANGO_DB_HOST"],
            "PORT": os.environ["DJANGO_DB_PORT"],
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "integreat",
            "USER": "integreat",
            "PASSWORD": "password",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }

# Directory for initial database contents

FIXTURE_DIRS = (os.path.join(BASE_DIR, "cms/fixtures/"),)

# Authentication backends

AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",  # this is default
)


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGES = (
    ("en-us", "English"),
    ("de-de", "Deutsch"),
)

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

LANGUAGE_CODE = "de-de"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "../node_modules"),
]
STATIC_URL = "/static/"
if "DJANGO_STATIC_PARENT" in os.environ:
    STATIC_ROOT = os.environ["DJANGO_STATIC_ROOT"]
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "cms/static/")

# Caches

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(STATIC_ROOT, "CACHE/django_cache"),
    }
}

# Login
LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login"

# Miscellaneous
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CSRF_FAILURE_VIEW = "cms.views.error_handler.csrf_failure"

MEDIA_URL = "/media/"
if "DJANGO_MEDIA_PARENT" in os.environ:
    MEDIA_ROOT = os.environ["DJANGO_MEDIA_ROOT"]
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
FILER_CANONICAL_URL = "media/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "INTEGREAT CMS - %(levelname)s: %(message)s",
        },
        "console": {
            "format": "%(asctime)s INTEGREAT CMS - %(levelname)s: %(message)s",
            "datefmt": "%b %d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "console"},
        "authlog": {
            "level": "INFO",
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",
            "facility": "auth",
            "formatter": "default",
        },
        "syslog": {
            "level": "INFO",
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",
            "facility": "syslog",
            "formatter": "default",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARN",
            "propagate": True,
        },
        "api": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "backend": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "cms": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "gvz_api": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "sitemap": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "rules": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "auth": {
            "handlers": ["console", "authlog", "syslog"],
            "level": "INFO",
        },
    },
}

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

COMPRESS_CSS_FILTERS = [
    "compressor.filters.css_default.CssAbsoluteFilter",
    "compressor.filters.cssmin.CSSMinFilter",
    "compressor.filters.template.TemplateFilter",
]
COMPRESS_JS_FILTERS = [
    "compressor.filters.jsmin.JSMinFilter",
]
COMPRESS_PRECOMPILERS = (
    ("module", "compressor_toolkit.precompilers.ES6Compiler"),
    ("css", "compressor_toolkit.precompilers.SCSSCompiler"),
)
COMPRESS_ES6_COMPILER_CMD = 'export NODE_PATH="{paths}" && {browserify_bin} "{infile}" -o "{outfile}" -t [ "{node_modules}/babelify" --presets [ @babel/preset-env ] --plugins [ @babel/plugin-transform-runtime ] ]'
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = True

# GVZ (Gemeindeverzeichnis) API URL
GVZ_API_URL = "https://gvz.integreat-app.de/api"
GVZ_API_ENABLED = True

# Allow access to all domains by setting the following variable to TRUE
CORS_ORIGIN_ALLOW_ALL = True

# Extend default headers with development header to differenciate dev traffic in statistics
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-integreat-development",
]

TEST_BLOG_ID = 154

# RSS feed urls
RSS_FEED_URLS = {
    "en-us": "https://integreat-app.de/en/feed/",
    "de-de": "https://integreat-app.de/feed/",
    "home-page": "https://integreat-app.de/",
}
