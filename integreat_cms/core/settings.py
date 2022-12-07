"""
Django settings for ``integreat-cms``.

This file only contains the options which deviate from the default values.
For the full list of settings and their values, see :doc:`django:ref/settings`.

For production use, some of the settings can be set with environment variables
(use the prefix ``INTEGREAT_CMS_``) or via the config file `/etc/integreat-cms.ini`.
See :doc:`/prod-server` for details.
"""
import os
from distutils.util import strtobool
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from ..nominatim_api.utils import BoundingBox
from .logging_formatter import ColorFormatter, RequestFormatter


###################
# CUSTOM SETTINGS #
###################

#: Build paths inside the project like this: ``os.path.join(BASE_DIR, ...)``
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The URL to our webapp. This is used for urls in the ``sitemap.xml``
#: (see :mod:`~integreat_cms.sitemap` for more information).
WEBAPP_URL = os.environ.get("INTEGREAT_CMS_WEBAPP_URL", "https://integreat.app")

#: The URL to the Matomo statistics server.
MATOMO_URL = os.environ.get(
    "INTEGREAT_CMS_MATOMO_URL", "https://statistics.integreat-app.de"
)

#: Enable tracking of API requests in Matomo
MATOMO_TRACKING = bool(
    strtobool(os.environ.get("INTEGREAT_CMS_MATOMO_TRACKING", "False"))
)

#: The slug for the legal notice (see e.g. :class:`~integreat_cms.cms.models.pages.imprint_page_translation.ImprintPageTranslation`)
IMPRINT_SLUG = "imprint"

#: The slug of the region "Testumgebung" - prevent sending PNs to actual users in development in
#: :func:`~integreat_cms.firebase_api.firebase_api_client.FirebaseApiClient.send_pn`

TEST_REGION_SLUG = "testumgebung"

#: URL to the Integreat Website
WEBSITE_URL = os.environ.get("INTEGREAT_CMS_WEBSITE_URL", "https://integreat-app.de")

#: An alias of :attr:`~integreat_cms.core.settings.WEBAPP_URL`.
#: Used by `django-linkcheck <https://github.com/DjangoAdminHackers/django-linkcheck#site_domain-and-linkcheck_site_domains>`_
#: to determine whether a link is internal.
SITE_DOMAIN = WEBAPP_URL

#: URLs to the Integreat blog
BLOG_URLS = {
    "en": f"{WEBSITE_URL}/en/blog/",
    "de": f"{WEBSITE_URL}/blog/",
}

#: The blog URL to use when the blog is not available in the requested language
DEFAULT_BLOG_URL = BLOG_URLS["en"]

#: URL to the Integreat wiki
WIKI_URL = os.environ.get("INTEGREAT_CMS_WIKI_URL", "https://wiki.integreat-app.de")

#: RSS feed URLs to the Integreat blog
RSS_FEED_URLS = {
    "en": f"{WEBSITE_URL}/en/feed/",
    "de": f"{WEBSITE_URL}/feed/",
}

#: The RSS feed URL to use when the feed is not available in the requested language
DEFAULT_RSS_FEED_URL = RSS_FEED_URLS["en"]

#: How many days of chat history should be shown
AUTHOR_CHAT_HISTORY_DAYS = 30

#: The time span up to which recurrent events should be returned by the api
API_EVENTS_MAX_TIME_SPAN_DAYS = 31

#: The company operating this CMS
COMPANY = os.environ.get("INTEGREAT_CMS_COMPANY", "Tür an Tür – Digitalfabrik gGmbH")

#: The URL to the company's website
COMPANY_URL = os.environ.get(
    "INTEGREAT_CMS_COMPANY_URL", "https://tuerantuer.de/digitalfabrik/"
)

#: The available inbuilt brandings of the CMS
AVAILABLE_BRANDINGS = ["integreat", "malte", "aschaffenburg"]

#: The branding of the CMS
BRANDING = os.environ.get("INTEGREAT_CMS_BRANDING", "integreat")

if BRANDING not in AVAILABLE_BRANDINGS:
    raise ImproperlyConfigured(
        f"The branding {BRANDING!r} is not supported, must be one of {AVAILABLE_BRANDINGS}."
    )

#: The default bounding box for regions with indistinct borders
DEFAULT_BOUNDING_BOX = BoundingBox(
    latitude_min=47.3024876979,
    latitude_max=54.983104153,
    longitude_min=5.98865807458,
    longitude_max=15.0169958839,
)

#: The default timeout in seconds for retrieving external APIs etc.
DEFAULT_REQUEST_TIMEOUT = int(
    os.environ.get("INTEGREAT_CMS_DEFAULT_REQUEST_TIMEOUT", 10)
)


##############################################################
# Firebase Push Notifications (Firebase Cloud Messaging FCM) #
##############################################################

#: FCM API Url
FCM_URL = "https://fcm.googleapis.com/fcm/send"

#: Authentication token for the Firebase API. This needs to be set for a correct usage of the messages feature.
FCM_KEY = os.environ.get("INTEGREAT_CMS_FCM_KEY")

#: Whether push notifications via Firebase are enabled.
#: This is ``True`` if :attr:`~integreat_cms.core.settings.FCM_KEY` is set, ``False`` otherwise.
FCM_ENABLED = bool(FCM_KEY)

#: The available push notification channels
FCM_CHANNELS = (("news", _("News")),)

#: How many days push notifications are shown in the apps
FCM_HISTORY_DAYS = 28


###########
# GVZ API #
###########

#: Whether or not the GVZ (Gemeindeverzeichnis) API is enabled. This is used to automatically import coordinates and
#: region aliases (see :mod:`~integreat_cms.gvz_api` for more information).
GVZ_API_ENABLED = True

#: The URL to our GVZ (Gemeindeverzeichnis) API. This is used to automatically import coordinates and region aliases
#: (see :mod:`~integreat_cms.gvz_api` for more information).
GVZ_API_URL = "https://gvz.integreat-app.de"


#################
# Nominatim API #
#################

#: Whether or not the Nominatim API for OpenStreetMap queries is enabled.
#: This is used to automatically derive coordinates from addresses.
NOMINATIM_API_ENABLED = bool(
    strtobool(os.environ.get("INTEGREAT_CMS_NOMINATIM_API_ENABLED", "True"))
)

#: The URL to our Nominatim API.
#: This is used to automatically derive coordinates from addresses.
NOMINATIM_API_URL = os.environ.get(
    "INTEGREAT_CMS_NOMINATIM_API_URL", "http://nominatim.maps.tuerantuer.org/nominatim/"
)


###############
# TEXTLAB API #
###############

#: URL to the Textlab API
TEXTLAB_API_URL = os.environ.get(
    "INTEGREAT_CMS_TEXTLAB_API_URL", "https://textlab.online/api/"
)

#: Key for the Textlab API
TEXTLAB_API_KEY = os.environ.get("INTEGREAT_CMS_TEXTLAB_API_KEY")

#: Whether the Textlab API is enabled.
#: This is ``True`` if :attr:`~integreat_cms.core.settings.TEXTLAB_API_KEY` is set, ``False`` otherwise.
TEXTLAB_API_ENABLED = bool(TEXTLAB_API_KEY)

#: Username for the Textlab API
TEXTLAB_API_USERNAME = os.environ.get("INTEGREAT_CMS_TEXTLAB_API_USERNAME", "Integreat")

#: Which language slugs are allowed for the Textlab API
TEXTLAB_API_LANGUAGES = ["de"]


############
# WEBAUTHN #
############

#: Needed for `webauthn <https://pypi.org/project/webauthn/>`__
#: (this is a setting in case the application runs behind a proxy).
#: Used in the following views:
#:
#: - :class:`~integreat_cms.cms.views.settings.mfa.register_user_mfa_key_view.RegisterUserMfaKeyView`
#: - :class:`~integreat_cms.cms.views.authentication.mfa.mfa_verify_view.MfaVerifyView`
BASE_URL = os.environ.get("INTEGREAT_CMS_BASE_URL", "http://localhost:8000")

#: Needed for `webauthn <https://pypi.org/project/webauthn/>`__
#: (this is a setting in case the application runs behind a proxy).
#: Used in the following views:
#:
#: - :class:`~integreat_cms.cms.views.settings.mfa.get_mfa_challenge_view.GetMfaChallengeView`
#: - :class:`~integreat_cms.cms.views.settings.mfa.register_user_mfa_key_view.RegisterUserMfaKeyView`
#: - :class:`~integreat_cms.cms.views.authentication.mfa.mfa_assert_view.MfaAssertView`
#: - :class:`~integreat_cms.cms.views.authentication.mfa.mfa_verify_view.MfaVerifyView`
HOSTNAME = urlparse(BASE_URL).hostname


########################
# DJANGO CORE SETTINGS #
########################

#: A boolean that turns on/off debug mode (see :setting:`django:DEBUG`)
#:
#: .. warning::
#:     Never deploy a site into production with :setting:`DEBUG` turned on!
DEBUG = bool(strtobool(os.environ.get("INTEGREAT_CMS_DEBUG", "False")))

#: Enabled applications (see :setting:`django:INSTALLED_APPS`)
INSTALLED_APPS = [
    # Installed custom apps
    "integreat_cms.cms",
    "integreat_cms.deepl_api",
    "integreat_cms.firebase_api",
    "integreat_cms.gvz_api",
    "integreat_cms.matomo_api",
    "integreat_cms.nominatim_api",
    "integreat_cms.summ_ai_api",
    "integreat_cms.textlab_api",
    "integreat_cms.linkcheck.apps.ModifiedLinkcheckConfig",
    # Installed Django apps
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    # Installed third-party-apps
    "corsheaders",
    "rules.apps.AutodiscoverRulesConfig",
    "treebeard",
    "webpack_loader",
    "widget_tweaks",
    "polymorphic",
]

# Install cacheops only if redis cache is available
if "INTEGREAT_CMS_REDIS_CACHE" in os.environ:
    INSTALLED_APPS.append("cacheops")

# The default Django Admin application and debug toolbar will only be activated if the system is in debug mode.
if DEBUG:
    INSTALLED_APPS.append("django.contrib.admin")
    # Comment out the following line if you want to disable the Django debug toolbar
    INSTALLED_APPS.append("debug_toolbar")

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
    "integreat_cms.core.middleware.RegionMiddleware",
    "integreat_cms.core.middleware.AccessControlMiddleware",
    "integreat_cms.core.middleware.TimezoneMiddleware",
]

# The Django debug toolbar middleware will only be activated if the debug_toolbar app is installed
if "debug_toolbar" in INSTALLED_APPS:
    # The debug toolbar middleware should be put first (see :doc:`django-debug-toolbar:installation`)
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    MIDDLEWARE.append("integreat_cms.api.middleware.JsonDebugToolbarMiddleware")

#: Default URL dispatcher (see :setting:`django:ROOT_URLCONF`)
ROOT_URLCONF = "integreat_cms.core.urls"

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
                "integreat_cms.core.context_processors.version_processor",
                "integreat_cms.core.context_processors.settings_processor",
                "integreat_cms.core.context_processors.constants_processor",
            ],
            "debug": DEBUG,
        },
    },
]

#: WSGI (Web Server Gateway Interface) config (see :setting:`django:WSGI_APPLICATION`)
WSGI_APPLICATION = "integreat_cms.core.wsgi.application"


############
# DATABASE #
############

#: A dictionary containing the settings for all databases to be used with this Django installation
#: (see :setting:`django:DATABASES`)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("INTEGREAT_CMS_DB_NAME", "integreat"),
        "USER": os.environ.get("INTEGREAT_CMS_DB_USER", "integreat"),
        "PASSWORD": os.environ.get(
            "INTEGREAT_CMS_DB_PASSWORD", "password" if DEBUG else ""
        ),
        "HOST": os.environ.get("INTEGREAT_CMS_DB_HOST", "localhost"),
        "PORT": os.environ.get("INTEGREAT_CMS_DB_PORT", "5432"),
    }
}

#: Default primary key field type to use for models that don’t have a field with
#: :attr:`primary_key=True <django.db.models.Field.primary_key>`. (see :setting:`django:DEFAULT_AUTO_FIELD`)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


############
# SECURITY #
############

#: This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe
#: web server configurations (see :setting:`django:ALLOWED_HOSTS` and :ref:`django:host-headers-virtual-hosting`)
ALLOWED_HOSTS = [HOSTNAME, ".localhost", "127.0.0.1", "[::1]"] + [
    x.strip()
    for x in os.environ.get("INTEGREAT_CMS_ALLOWED_HOSTS", "").splitlines()
    if x
]

#: A list of IP addresses, as strings, that allow the :func:`~django.template.context_processors.debug` context
#: processor to add some variables to the template context.
INTERNAL_IPS = ["localhost", "127.0.0.1"]

#: The secret key for this particular Django installation (see :setting:`django:SECRET_KEY`)
#:
#: .. warning::
#:     Provide a key via the environment variable ``INTEGREAT_CMS_SECRET_KEY`` in production and keep it secret!
SECRET_KEY = os.environ.get("INTEGREAT_CMS_SECRET_KEY", "dummy" if DEBUG else "")

#: A dotted path to the view function to be used when an incoming request is rejected by the CSRF protection
#: (see :setting:`django:CSRF_FAILURE_VIEW`)
CSRF_FAILURE_VIEW = "integreat_cms.cms.views.error_handler.csrf_failure"


################
# CORS HEADERS #
################

#: Allow access to all domains by setting the following variable to ``True``
#: (see `django-cors-headers/ <https://pypi.org/project/django-cors-headers/>`__)
CORS_ORIGIN_ALLOW_ALL = True

#: Extend default headers with development header to differentiate dev traffic in statistics
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

#: The model to use to represent a User (see :setting:`django:AUTH_USER_MODEL` and :ref:`django:auth-custom-user`)
AUTH_USER_MODEL = "cms.User"

#: A list of authentication backend classes (as strings) to use when attempting to authenticate a user
#: (see :setting:`django:AUTHENTICATION_BACKENDS` and :ref:`django:authentication-backends`)
AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",  # Object-based permission checks
    "django.contrib.auth.backends.ModelBackend",  # Login via username
    "integreat_cms.core.authentication_backends.EmailAuthenticationBackend",  # Login via email
)

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "integreat_cms.cms.auth.WPBCryptPasswordHasher",
]


#: The list of validators that are used to check the strength of user’s passwords
#: (see :setting:`django:AUTH_PASSWORD_VALIDATORS` and :ref:`django:password-validation`)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

#: The URL where requests are redirected for login (see :setting:`django:LOGIN_URL`)
LOGIN_URL = "/login/"

#: The URL where requests are redirected after login (see :setting:`django:LOGIN_REDIRECT_URL`)
LOGIN_REDIRECT_URL = "/"

#: The URL where requests are redirected after logout (see :setting:`django:LOGOUT_REDIRECT_URL`)
LOGOUT_REDIRECT_URL = "/login/"


###########
# LOGGING #
###########

#: The log level for integreat-cms django apps
LOG_LEVEL = os.environ.get("INTEGREAT_CMS_LOG_LEVEL", "DEBUG" if DEBUG else "INFO")

#: The log level for the syslog
SYS_LOG_LEVEL = "INFO"

#: The log level for dependencies
DEPS_LOG_LEVEL = os.environ.get(
    "INTEGREAT_CMS_DEPS_LOG_LEVEL", "INFO" if DEBUG else "WARN"
)

#: The file path of the logfile. Needs to be writable by the application.
LOGFILE = os.environ.get(
    "INTEGREAT_CMS_LOGFILE", os.path.join(BASE_DIR, "integreat-cms.log")
)

#: Logging configuration dictionary (see :setting:`django:LOGGING`)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "()": RequestFormatter,
            "format": "{asctime} \x1b[1m{levelname}\x1b[0m {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "console-colored": {
            "()": ColorFormatter,
            "format": "{asctime} {levelname} {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "logfile": {
            "()": RequestFormatter,
            "format": "{asctime} {levelname:7} {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "syslog": {
            "format": "INTEGREAT CMS - {levelname}: {message}",
            "style": "{",
        },
        "email": {
            "format": "Date and time: {asctime}\nSeverity: {levelname}\nLogger: {name}\nMessage: {message}\nFile: {funcName}() in {pathname}:{lineno}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "console-colored": {
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "console-colored",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "filename": LOGFILE,
            "formatter": "logfile",
        },
        "authlog": {
            "filters": ["require_debug_false"],
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",
            "facility": "auth",
            "formatter": "syslog",
        },
        "syslog": {
            "filters": ["require_debug_false"],
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",
            "facility": "syslog",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "formatter": "email",
        },
    },
    "loggers": {
        # Loggers of integreat-cms django apps
        "integreat_cms": {
            "handlers": ["console-colored", "logfile"],
            "level": LOG_LEVEL,
        },
        # Syslog for authentication
        "auth": {
            "handlers": ["console", "logfile", "authlog", "syslog"],
            "level": SYS_LOG_LEVEL,
        },
        # Loggers of dependencies
        "aiohttp.client": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "deepl": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "django": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "geopy": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "linkcheck": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "PIL": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "requests": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "rules": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "urllib3": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "xhtml2pdf": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
    },
}


##########
# EMAILS #
##########

if DEBUG:
    #: The backend to use for sending emails (see :setting:`django:EMAIL_BACKEND` and :doc:`django:topics/email`)
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

#: Default email address to use for various automated correspondence from the site manager(s)
#: (see :setting:`django:DEFAULT_FROM_EMAIL`)
DEFAULT_FROM_EMAIL = os.environ.get(
    "INTEGREAT_CMS_SERVER_EMAIL", "keineantwort@integreat-app.de"
)

#: The email address that error messages come from, such as those sent to :attr:`~integreat_cms.core.settings.ADMINS`.
#: (see :setting:`django:SERVER_EMAIL`)
SERVER_EMAIL = os.environ.get(
    "INTEGREAT_CMS_SERVER_EMAIL", "keineantwort@integreat-app.de"
)

#: A list of all the people who get code error notifications. When :attr:`~integreat_cms.core.settings.DEBUG` is ``False``,
#: Django emails these people the details of exceptions raised in the request/response cycle.
ADMINS = [("Integreat Helpdesk", "tech@integreat-app.de")]

#: The host to use for sending email (see :setting:`django:EMAIL_HOST`)
EMAIL_HOST = os.environ.get("INTEGREAT_CMS_EMAIL_HOST", "localhost")

#: Password to use for the SMTP server defined in :attr:`~integreat_cms.core.settings.EMAIL_HOST`
#: (see :setting:`django:EMAIL_HOST_PASSWORD`). If empty, Django won’t attempt authentication.
EMAIL_HOST_PASSWORD = os.environ.get("INTEGREAT_CMS_EMAIL_HOST_PASSWORD")

#: Username to use for the SMTP server defined in :attr:`~integreat_cms.core.settings.EMAIL_HOST`
#: (see :setting:`django:EMAIL_HOST_USER`). If empty, Django won’t attempt authentication.
EMAIL_HOST_USER = os.environ.get("INTEGREAT_CMS_EMAIL_HOST_USER", SERVER_EMAIL)

#: Port to use for the SMTP server defined in :attr:`~integreat_cms.core.settings.EMAIL_HOST`
#: (see :setting:`django:EMAIL_PORT`)
EMAIL_PORT = int(os.environ.get("INTEGREAT_CMS_EMAIL_PORT", 587))

#: Whether to use a TLS (secure) connection when talking to the SMTP server.
#: This is used for explicit TLS connections, generally on port 587.
#: (see :setting:`django:EMAIL_USE_TLS`)
EMAIL_USE_TLS = bool(strtobool(os.environ.get("INTEGREAT_CMS_EMAIL_USE_TLS", "True")))

#: Whether to use an implicit TLS (secure) connection when talking to the SMTP server.
#: In most email documentation this type of TLS connection is referred to as SSL. It is generally used on port 465.
#: (see :setting:`django:EMAIL_USE_SSL`)
EMAIL_USE_SSL = bool(strtobool(os.environ.get("INTEGREAT_CMS_EMAIL_USE_SSL", "False")))


########################
# INTERNATIONALIZATION #
########################

#: A list of all available languages with locale files for translated strings
AVAILABLE_LANGUAGES = {
    "de": _("German"),
    "en": _("English"),
    "nl": _("Dutch"),
}

#: The default UI languages
DEFAULT_LANGUAGES = ["de", "en"]

#: The list of languages which are available in the UI
#: (see :setting:`django:LANGUAGES` and :doc:`django:topics/i18n/index`)
LANGUAGES = [
    (language, AVAILABLE_LANGUAGES[language])
    for language in filter(
        None,
        (
            language.strip()
            for language in os.environ.get(
                "INTEGREAT_CMS_LANGUAGES", "\n".join(DEFAULT_LANGUAGES)
            ).splitlines()
        ),
    )
]

#: A list of directories where Django looks for translation files
#: (see :setting:`django:LOCALE_PATHS` and :doc:`django:topics/i18n/index`)
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

#: A string representing the language slug for this installation
#: (see :setting:`django:LANGUAGE_CODE` and :doc:`django:topics/i18n/index`)
LANGUAGE_CODE = os.environ.get("INTEGREAT_CMS_LANGUAGE_CODE", "de")

#: A string representing the time zone for this installation
#: (see :setting:`django:TIME_ZONE` and :doc:`django:topics/i18n/index`)
TIME_ZONE = "UTC"

#: A string representing the time zone that is used for rendering
CURRENT_TIME_ZONE = os.environ.get("INTEGREAT_CMS_CURRENT_TIME_ZONE", "Europe/Berlin")

#: A boolean that specifies whether Django’s translation system should be enabled
#: (see :setting:`django:USE_I18N` and :doc:`django:topics/i18n/index`)
USE_I18N = True

#: A boolean that specifies if localized formatting of data will be enabled by default or not
#: (see :setting:`django:USE_L10N` and :doc:`django:topics/i18n/index`)
USE_L10N = True

#: A boolean that specifies if datetimes will be timezone-aware by default or not
#: (see :setting:`django:USE_TZ` and :doc:`django:topics/i18n/index`)
USE_TZ = True


##########################
# AUTOMATIC TRANSLATIONS #
##########################

#: Authentication token for the DeepL API. If not set, automatic translations via DeepL are disabled
DEEPL_AUTH_KEY = os.environ.get("INTEGREAT_CMS_DEEPL_AUTH_KEY")

#: Whether automatic translations via DeepL are enabled.
#: This is ``True`` if :attr:`~integreat_cms.core.settings.DEEPL_AUTH_KEY` is set, ``False`` otherwise.
DEEPL_ENABLED = bool(DEEPL_AUTH_KEY)


#########################
# SUMM.AI - EASY GERMAN #
#########################

#: The URL to our SUMM.AI API for automatic translations from German into Easy German
SUMM_AI_API_URL = os.environ.get(
    "INTEGREAT_CMS_SUMM_AI_API_URL", "https://backend.summ-ai.com/translate/v1/"
)

#: Authentication token for SUMM.AI,
#: If not set, automatic translations to easy german are disabled
SUMM_AI_API_KEY = os.environ.get("INTEGREAT_CMS_SUMM_AI_API_KEY")

#: Whether SUMM.AI is enabled or not
#: This is ``True`` if SUMM_AI_API_KEY is set, ``False`` otherwise.
SUMM_AI_ENABLED = bool(SUMM_AI_API_KEY)

#: Whether requests to the SUMM.AI are done with the ``is_test`` flag
SUMM_AI_TEST_MODE = strtobool(
    os.environ.get("INTEGREAT_CMS_SUMM_AI_TEST_MODE", str(DEBUG))
)

#: The timeout in minutes for requests to the SUMM.AI API
SUMM_AI_TIMEOUT = 10

#: The language slugs for German
SUMM_AI_GERMAN_LANGUAGE_SLUG = os.environ.get(
    "INTEGREAT_CMS_SUMM_AI_GERMAN_LANGUAGE_SLUG", "de"
)

#: The language slug for Easy German
SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG = os.environ.get(
    "INTEGREAT_CMS_SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG", "de-si"
)

#: The separator which is used to split compound words, e.g. Bundes-Kanzler (hyphen) or Bundes·kanzler (interpunct)
SUMM_AI_SEPARATOR = os.environ.get("INTEGREAT_CMS_SUMM_AI_SEPARATOR", "hyphen")

#: All plain text fields of the content models which should be translated
SUMM_AI_TEXT_FIELDS = ["meta_description"]

#: All HTML fields of the content models which should be translated
SUMM_AI_HTML_FIELDS = ["content"]

#: All fields of the content models which should not be translated, but inherited from the source translation
SUMM_AI_INHERITED_FIELDS = ["title"]

#: Translate all <p> and <li> tags
SUMM_AI_HTML_TAGS = ["p", "li"]


################
# STATIC FILES #
################

#: This setting defines the additional locations the :mod:`django.contrib.staticfiles` app will traverse to collect
#: static files for deployment or to serve them during development (see :setting:`django:STATICFILES_DIRS` and
#: :doc:`Managing static files <django:howto/static-files/index>`).
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static/dist")]

#: The absolute path to the output directory where :mod:`django.contrib.staticfiles` will put static files for
#: deployment (see :setting:`django:STATIC_ROOT` and :doc:`Managing static files <django:howto/static-files/index>`)
#: In debug mode, this is not required since :mod:`django.contrib.staticfiles` can directly serve these files.
STATIC_ROOT = os.environ.get("INTEGREAT_CMS_STATIC_ROOT")

#: URL to use in development when referring to static files located in :setting:`STATICFILES_DIRS`
#: (see :setting:`django:STATIC_URL` and :doc:`Managing static files <django:howto/static-files/index>`)
STATIC_URL = "/static/"

#: The list of finder backends that know how to find static files in various locations
#: (see :setting:`django:STATICFILES_FINDERS`)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)


#################
# MEDIA LIBRARY #
#################

#: URL that handles the media served from :setting:`MEDIA_ROOT` (see :setting:`django:MEDIA_URL`)
MEDIA_URL = "/media/"

#: Absolute filesystem path to the directory that will hold user-uploaded files (see :setting:`django:MEDIA_ROOT`)
MEDIA_ROOT = os.environ.get("INTEGREAT_CMS_MEDIA_ROOT", os.path.join(BASE_DIR, "media"))

#: The maximum size of media images in pixels (larger images will automatically be resized)
MEDIA_OPTIMIZED_SIZE = 3000

#: The maximum size of media thumbnails in pixels
MEDIA_THUMBNAIL_SIZE = 300

#: Whether thumbnails should be cropped (resulting in square thumbnails regardless of the aspect ratio of the image)
MEDIA_THUMBNAIL_CROP = False

#: Enables the possibility to upload further file formats (e.g. DOC, GIF).
LEGACY_FILE_UPLOAD = bool(
    strtobool(os.environ.get("INTEGREAT_CMS_LEGACY_FILE_UPLOAD", "False"))
)

#: The maximum size of media files in bytes
MEDIA_MAX_UPLOAD_SIZE = int(
    os.environ.get("INTEGREAT_CMS_MEDIA_MAX_UPLOAD_SIZE", 3 * 1024 * 1024)
)


#########
# CACHE #
#########

#: Configuration for caches (see :setting:`django:CACHES` and :doc:`django:topics/cache`).
#: Use a ``LocMemCache`` for development and a ``RedisCache`` whenever available.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

# Use RedisCache when activated
if bool(strtobool(os.environ.get("INTEGREAT_CMS_REDIS_CACHE", "False"))):
    unix_socket = os.environ.get("INTEGREAT_CMS_REDIS_UNIX_SOCKET")
    if unix_socket:
        # Use unix socket if available (and also tell cacheops about it)
        redis_location = f"unix://{unix_socket}?db=0"
        CACHEOPS_REDIS = f"unix://{unix_socket}?db=1"
    else:
        # If not, fall back to normal TCP connection
        redis_location = "redis://127.0.0.1:6379/0"
    CACHES["default"] = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_location,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # Don't throw exceptions when redis is not available
        },
    }

#: Default cache timeout for cacheops
CACHEOPS_DEFAULTS = {"timeout": 60 * 60}

#: Which database tables should be cached
CACHEOPS = {
    "auth.*": {"ops": "all"},
    "cms.*": {"ops": "all"},
    "linkcheck.*": {"ops": "all"},
    "*.*": {},
}

#: Degrade gracefully on redis fail
CACHEOPS_DEGRADE_ON_FAILURE = True


##############
# PAGINATION #
##############

#: Number of entries displayed per pagination chunk
#: see :class:`~django.core.paginator.Paginator`
PER_PAGE = 16


####################
# DJANGO LINKCHECK #
####################

#: Disable linkcheck listeners e.g. when the fixtures are loaded
LINKCHECK_DISABLE_LISTENERS = bool(
    strtobool(os.environ.get("INTEGREAT_CMS_LINKCHECK_DISABLE_LISTENERS", "False"))
)

#: The maximum length of URLs which can be checked. Longer URLs will be silently ignored.
LINKCHECK_MAX_URL_LENGTH = 1024

#: URL types that are not supposed to be shown in the link list (e.g. phone numbers and emails)
LINKCHECK_IGNORED_URL_TYPES = [
    "mailto",
    "phone",
    "anchor",
]

#: Whether archived pages should be ignored for linkcheck scan.
#: Since this causes a lot of overhead, only use this for the findlinks management command::
#:
#:    $ INTEGREAT_CMS_LINKCHECK_EXCLUDE_ARCHIVED_PAGES=1 integreat-cms-cli findlinks
LINKCHECK_EXCLUDE_ARCHIVED_PAGES = bool(
    strtobool(os.environ.get("INTEGREAT_CMS_LINKCHECK_EXCLUDE_ARCHIVED_PAGES", "False"))
)


#################
# INTERNAL URLS #
#################

#: The URLs which are treated as internal in TinyMCE custom link plugin
INTERNAL_URLS = (
    ALLOWED_HOSTS
    + [WEBAPP_URL, WEBSITE_URL]
    + [
        x.strip()
        for x in os.environ.get("INTEGREAT_CMS_INTERNAL_URLS", "").splitlines()
        if x
    ]
)


#########################
# DJANGO WEBPACK LOADER #
#########################

#: Overwrite default bundle directory
WEBPACK_LOADER = {
    "DEFAULT": {
        "BUNDLE_DIR_NAME": "",
        "STATS_FILE": os.path.join(BASE_DIR, "webpack-stats.json"),
    }
}


########################
# DJANGO DEBUG TOOLBAR #
########################

#: This setting specifies the full Python path to each panel that you want included in the toolbar.
#:  (see :doc:`django-debug-toolbar:configuration`)
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
]


##############
# PDF EXPORT #
##############

#: The directory where PDF files are stored
PDF_ROOT = os.environ.get("INTEGREAT_CMS_PDF_ROOT", os.path.join(BASE_DIR, "pdf"))

#: The URL path where PDF files are served for download
PDF_URL = "/pdf/"


#######################
# XLIFF SERIALIZATION #
#######################

#: A dictionary of modules containing serializer definitions (provided as strings),
#: keyed by a string identifier for that serialization type (see :setting:`django:SERIALIZATION_MODULES`).
SERIALIZATION_MODULES = {
    "xliff": "integreat_cms.xliff.generic_serializer",
    "xliff-1.2": "integreat_cms.xliff.xliff1_serializer",
    "xliff-2.0": "integreat_cms.xliff.xliff2_serializer",
}

#: The xliff version to be used for exports
XLIFF_EXPORT_VERSION = os.environ.get("INTEGREAT_CMS_XLIFF_EXPORT_VERSION", "xliff-1.2")

#: The default fields to be used for the XLIFF serialization
XLIFF_DEFAULT_FIELDS = ("title", "content")

#: A mapping for changed field names to preserve backward compatibility after a database field was renamed
XLIFF_LEGACY_FIELDS = {"body": "content"}

#: The directory where xliff files are stored
XLIFF_ROOT = os.environ.get("INTEGREAT_CMS_XLIFF_ROOT", os.path.join(BASE_DIR, "xliff"))

#: The directory to which xliff files should be uploaded (this should not be reachable by the webserver)
XLIFF_UPLOAD_DIR = os.path.join(XLIFF_ROOT, "upload")

#: The directory from which xliff files can be downloaded (this should be publicly available under the url specified in
#: :attr:`~integreat_cms.core.settings.XLIFF_URL`)
XLIFF_DOWNLOAD_DIR = os.path.join(XLIFF_ROOT, "download")

#: The URL path where XLIFF files are served for download
XLIFF_URL = "/xliff/"
