"""
Django settings for ``integreat-cms``.

This file only contains the options which deviate from the default values.
For the full list of settings and their values, see :doc:`django:ref/settings`.

For production use, the following settings can be set with environment variables (use the prefix ``DJANGO_``):

* :attr:`~backend.settings.SECRET_KEY`
* :attr:`~backend.settings.DEBUG`
* :attr:`~backend.settings.ALLOWED_HOSTS` via :attr:`~backend.settings.BASE_URL`
* :attr:`~backend.settings.WEBAPP_URL`
* :attr:`~backend.settings.BASE_URL`
* :attr:`~backend.settings.WEBAPP_URL`
* :attr:`~backend.settings.STATIC_ROOT`
* :attr:`~backend.settings.MEDIA_ROOT`
* :attr:`~backend.settings.DATABASES` settings:

    * ``DJANGO_DB_HOST``
    * ``DJANGO_DB_NAME``
    * ``DJANGO_DB_PASSWORD``
    * ``DJANGO_DB_USER``
    * ``DJANGO_DB_PORT``

"""
import os
import urllib

###################
# CUSTOM SETTINGS #
###################


#: Build paths inside the project like this: ``os.path.join(BASE_DIR, ...)``
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Version number
VERSION = "0.0.14"

if "DJANGO_WEBAPP_URL" in os.environ:
    WEBAPP_URL = os.environ["DJANGO_WEBAPP_URL"]
else:
    #: The URL to our webapp. This is used for urls in the ``sitemap.xml`` (see :mod:`sitemap` for more information).
    WEBAPP_URL = "https://integreat.app"

#: The slug for the legal notice (see e.g. :class:`~cms.models.pages.imprint_page_translation.ImprintPageTranslation`)
IMPRINT_SLUG = "imprint"

#: The ID of the region "Testumgebung" - prevent sending PNs to actual users in development in
#: :func:`~cms.views.push_notifications.push_notification_sender.PushNotificationSender.send_pn`
TEST_BLOG_ID = 154

#: RSS feed URLs to the Integreat blog
RSS_FEED_URLS = {
    "en-us": "https://integreat-app.de/en/feed/",
    "de-de": "https://integreat-app.de/feed/",
    "home-page": "https://integreat-app.de/",
}

#: How many days of chat history should be shown
AUTHOR_CHAT_HISTORY_DAYS = 30

###########
# GVZ API #
###########


#: Whether or not the GVZ (Gemeindeverzeichnis) API is enabled. This is used to automatically import coordinates and
#: region aliases (see :mod:`gvz_api` for more information).
GVZ_API_ENABLED = True

#: The URL to our GVZ (Gemeindeverzeichnis) API. This is used to automatically import coordinates and region aliases
#: (see :mod:`gvz_api` for more information).
GVZ_API_URL = "https://gvz.integreat-app.de/api"


############
# WEBAUTHN #
############

if "DJANGO_BASE_URL" in os.environ:
    HOSTNAME = urllib.parse.urlparse(os.environ["DJANGO_BASE_URL"]).netloc
    BASE_URL = os.environ["DJANGO_BASE_URL"]
else:
    #: Needed for `webauthn <https://pypi.org/project/webauthn/>`__ (this is a setting in case the application runs behind a proxy).
    #: Used in the following views:
    #:
    #: - :func:`~cms.views.settings.mfa.mfa.register_mfa_key`
    #: - :func:`~cms.views.authentication.authentication_actions.mfaVerify`
    BASE_URL = "http://localhost:8000"
    #: Needed for `webauthn <https://pypi.org/project/webauthn/>`__ (this is a setting in case the application runs behind a proxy).
    #: Used in the following views:
    #:
    #: - :class:`~cms.views.settings.mfa.mfa.GetChallengeView`
    #: - :func:`~cms.views.settings.mfa.mfa.register_mfa_key`
    #: - :func:`~cms.views.authentication.authentication_actions.makeWebauthnUsers`
    #: - :func:`~cms.views.authentication.authentication_actions.mfaVerify`
    HOSTNAME = "localhost"


########################
# DJANGO CORE SETTINGS #
########################


if "DJANGO_DEBUG" in os.environ:
    DEBUG = bool(os.environ["DJANGO_DEBUG"])
else:
    #: A boolean that turns on/off debug mode (see :setting:`django:DEBUG`)
    #:
    #: .. warning::
    #:     Never deploy a site into production with :setting:`DEBUG` turned on!
    DEBUG = True

#: Enabled applications (see :setting:`django:INSTALLED_APPS`)
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

#: Activated middlewares (see :setting:`django:MIDDLEWARE`)
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

#: Default URL dispatcher (see :setting:`django:ROOT_URLCONF`)
ROOT_URLCONF = "backend.urls"

#: Config for HTML templates (see :setting:`django:TEMPLATES`)
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

#: WSGI (Web Server Gateway Interface) config (see :setting:`django:WSGI_APPLICATION`)
WSGI_APPLICATION = "backend.wsgi.application"

#: The backend to use for sending emails (see :setting:`django:EMAIL_BACKEND` and :doc:`django:topics/email`)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


############
# DATABASE #
############


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
    #: A dictionary containing the settings for all databases to be used with this Django installation
    #: (see :setting:`django:DATABASES`)
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

#: Directory for initial database contents (see :setting:`django:FIXTURE_DIRS`)
FIXTURE_DIRS = (os.path.join(BASE_DIR, "cms/fixtures/"),)


############
# SECURITY #
############

if "DJANGO_BASE_URL" in os.environ:
    ALLOWED_HOSTS = [urllib.parse.urlparse(os.environ["DJANGO_BASE_URL"]).netloc]
else:
    #: This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe web
    #: server configurations (see :setting:`django:ALLOWED_HOSTS` and :ref:`django:host-headers-virtual-hosting`)
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]


if "DJANGO_SECRET_KEY" in os.environ:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
else:
    #: The secret key for this particular Django installation (see :setting:`django:SECRET_KEY`)
    #:
    #: .. warning::
    #:     Change the key in production and keep it secret!
    SECRET_KEY = "-!v282$zj815_q@htaxcubylo)(l%a+k*-xi78hw*#s2@i86@_"

#: A dotted path to the view function to be used when an incoming request is rejected by the CSRF protection
#: (see :setting:`django:CSRF_FAILURE_VIEW`)
CSRF_FAILURE_VIEW = "cms.views.error_handler.csrf_failure"


################
# CORS HEADERS #
################


#: Allow access to all domains by setting the following variable to ``True``
#: (see `django-cors-headers/ <https://pypi.org/project/django-cors-headers/>`__)
CORS_ORIGIN_ALLOW_ALL = True

#: Extend default headers with development header to differenciate dev traffic in statistics
#: (see `django-cors-headers/ <https://pypi.org/project/django-cors-headers/>`__)
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


##################
# AUTHENTICATION #
##################


#: A list of authentication backend classes (as strings) to use when attempting to authenticate a user
#: (see :setting:`django:AUTHENTICATION_BACKENDS` and :ref:`django:authentication-backends`)
AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",  # this is default
)

#: The list of validators that are used to check the strength of user’s passwords
#: (see :setting:`django:AUTH_PASSWORD_VALIDATORS` and :ref:`django:password-validation`)
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

#: The URL where requests are redirected for login (see :setting:`django:LOGIN_URL`)
LOGIN_URL = "/login"

#: The URL where requests are redirected after login (see :setting:`django:LOGIN_REDIRECT_URL`)
LOGIN_REDIRECT_URL = "/"

#: The URL where requests are redirected after logout (see :setting:`django:LOGOUT_REDIRECT_URL`)
LOGOUT_REDIRECT_URL = "/login"


###########
# LOGGING #
###########


#: Logging configuration dictionary (see :setting:`django:LOGGING`)
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


########################
# INTERNATIONALIZATION #
########################


#: A list of all available languages (see :setting:`django:LANGUAGES` and :doc:`topics/i18n/index`)
LANGUAGES = (
    ("en-us", "English"),
    ("de-de", "Deutsch"),
)

#: A list of directories where Django looks for translation files
#: (see :setting:`django:LOCALE_PATHS` and :doc:`topics/i18n/index`)
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

#: A string representing the language code for this installation
#: (see :setting:`django:LANGUAGE_CODE` and :doc:`topics/i18n/index`)
LANGUAGE_CODE = "de-de"

#: A string representing the time zone for this installation
#: (see :setting:`django:TIME_ZONE` and :doc:`topics/i18n/index`)
TIME_ZONE = "UTC"

#: A boolean that specifies whether Django’s translation system should be enabled
#: (see :setting:`django:USE_I18N` and :doc:`topics/i18n/index`)
USE_I18N = True

#: A boolean that specifies if localized formatting of data will be enabled by default or not
#: (see :setting:`django:USE_L10N` and :doc:`topics/i18n/index`)
USE_L10N = True

#: A boolean that specifies if datetimes will be timezone-aware by default or not
#: (see :setting:`django:USE_TZ` and :doc:`topics/i18n/index`)
USE_TZ = True


################
# STATIC FILES #
################


if "DJANGO_STATIC_PARENT" in os.environ:
    STATIC_ROOT = os.environ["DJANGO_STATIC_ROOT"]
else:
    #: The absolute path to the directory where :mod:`django.contrib.staticfiles` will collect static files for deployment
    #: (see :setting:`django:STATIC_ROOT` and :doc:`Managing static files <django:howto/static-files/index>`)
    STATIC_ROOT = os.path.join(BASE_DIR, "cms/static/")

#: URL to use when referring to static files located in :setting:`STATIC_ROOT`
#: (see :setting:`django:STATIC_URL` and :doc:`Managing static files <django:howto/static-files/index>`)
STATIC_URL = "/static/"

#: This setting defines the additional locations the staticfiles app will traverse
#: (see :setting:`django:STATICFILES_DIRS` and :doc:`Managing static files <django:howto/static-files/index>`)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "../node_modules"),
]

#: The list of finder backends that know how to find static files in various locations
#: (see :setting:`django:STATICFILES_FINDERS`)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

#: URL that handles the media served from :setting:`MEDIA_ROOT` (see :setting:`django:MEDIA_URL`)
MEDIA_URL = "/media/"


if "DJANGO_MEDIA_PARENT" in os.environ:
    MEDIA_ROOT = os.environ["DJANGO_MEDIA_ROOT"]
else:
    #: Absolute filesystem path to the directory that will hold user-uploaded files (see :setting:`django:MEDIA_ROOT`)
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")


#: Defines the path element common to all canonical file URLs. (see :doc:`Django Filer Settings<django-filer:settings>`)
FILER_CANONICAL_URL = "media/"


#########
# CACHE #
#########


#: Configuration for PDF cache (see :setting:`django:CACHES`)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(STATIC_ROOT, "CACHE/django_cache"),
    }
}


##############
# COMPRESSOR #
##############


#: Boolean that decides if compression will happen (see :attr:`django-compressor:django.conf.settings.COMPRESS_ENABLED`)
COMPRESS_ENABLED = False

#: Boolean that decides if compression should be done outside of the request/response loop
#: (see :attr:`django-compressor:django.conf.settings.COMPRESS_OFFLINE` and :ref:`django-compressor:offline_compression`)
COMPRESS_OFFLINE = True

#: A list of filters that will be applied to CSS (see :attr:`django-compressor:django.conf.settings.COMPRESS_CSS_FILTERS`)
COMPRESS_CSS_FILTERS = [
    "compressor.filters.css_default.CssAbsoluteFilter",
    "compressor.filters.cssmin.CSSMinFilter",
    "compressor.filters.template.TemplateFilter",
]

#: A list of filters that will be applied to javascript
#: (see :attr:`django-compressor:django.conf.settings.COMPRESS_JS_FILTERS`)
COMPRESS_JS_FILTERS = [
    "compressor.filters.jsmin.JSMinFilter",
]

#: An iterable of two-tuples whose first item is the mimetype of the files or hunks you want to compile with the command
#: or filter specified as the second item (see :attr:`django-compressor:django.conf.settings.COMPRESS_PRECOMPILERS`)
COMPRESS_PRECOMPILERS = (
    ("module", "compressor_toolkit.precompilers.ES6Compiler"),
    ("css", "compressor_toolkit.precompilers.SCSSCompiler"),
)

#: Command that will be executed to transform ES6 into ES5 code (see
#: `django-compressor-toolkit <https://github.com/kottenator/django-compressor-toolkit>`__)
COMPRESS_ES6_COMPILER_CMD = 'export NODE_PATH="{paths}" && {browserify_bin} "{infile}" -o "{outfile}" -t [ "{node_modules}/babelify" --presets [ @babel/preset-env ] --plugins [ @babel/plugin-transform-runtime ] ]'


###################
# EASY THUMBNAILS #
###################

#: Whether thumbnails should be stored in high resolution (used by :doc:`easy-thumbnails:index`)
THUMBNAIL_HIGH_RESOLUTION = True
