"""
URLconf for public views of the cms package. These urls are whitelisted and excluded from the
:mod:`~integreat_cms.core.middleware.access_control_middleware.AccessControlMiddleware`.
Views which should have login protection go into :mod:`~integreat_cms.cms.urls.protected`.

Since urls of this module have an individual namespace (see :attr:`~integreat_cms.cms.urls.public.app_name`), this
namespace needs to be appended on any ``{% url %}`` tags in templates or calls of ``reverse()`` or ``redirect()`` in the
views, e.g.:

* ``{% url 'public:login' %}``
* ``redirect("public:login")``
* ``reverse_lazy("public:login")``
"""
from django.conf import settings
from django.urls import include, path
from django.views.generic import RedirectView

from ..views import (
    authentication,
    dashboard,
    error_handler,
    imprint,
    pages,
)


#: The namespace for this URL config (see :attr:`django.urls.ResolverMatch.app_name`)
app_name = "public"

#: The extra context passed to auth views
auth_context = {
    "COMPANY": settings.COMPANY,
    "COMPANY_URL": settings.COMPANY_URL,
}

#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    path("", dashboard.RegionSelection.as_view(), name="region_selection"),
    path(
        "s/",
        include(
            [
                path(
                    "p/<int:short_url_id>/",
                    pages.expand_page_translation_id,
                    name="expand_page_translation_id",
                ),
                path(
                    "i/<int:imprint_translation_id>/",
                    imprint.expand_imprint_translation_id,
                    name="expand_imprint_translation_id",
                ),
            ]
        ),
    ),
    path(
        "login/",
        include(
            [
                path(
                    "",
                    authentication.LoginView.as_view(extra_context=auth_context),
                    name="login",
                ),
                path(
                    "mfa/",
                    include(
                        [
                            path(
                                "",
                                authentication.MfaLoginView.as_view(),
                                name="login_mfa",
                            ),
                            path(
                                "assert/",
                                authentication.MfaAssertView.as_view(),
                                name="login_mfa_assert",
                            ),
                            path(
                                "verify/",
                                authentication.MfaVerifyView.as_view(),
                                name="login_mfa_verify",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "logout/",
        authentication.LogoutView.as_view(extra_context=auth_context),
        name="logout",
    ),
    path(
        "reset-password/",
        include(
            [
                path(
                    "",
                    authentication.PasswordResetView.as_view(
                        extra_context=auth_context,
                        extra_email_context={
                            "COMPANY": settings.COMPANY,
                            "BRANDING": settings.BRANDING,
                        },
                    ),
                    name="password_reset",
                ),
                path(
                    "<uidb64>/<token>/",
                    authentication.PasswordResetConfirmView.as_view(
                        extra_context=auth_context
                    ),
                    name="password_reset_confirm",
                ),
            ]
        ),
    ),
    path(
        "activate-account/<uidb64>/<token>/",
        authentication.AccountActivationView.as_view(extra_context=auth_context),
        name="activate_account",
    ),
    path(
        "wiki/",
        RedirectView.as_view(url=settings.WIKI_URL),
        name="wiki_redirect",
    ),
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=f"/static/logos/{settings.BRANDING}/{settings.BRANDING}-icon.svg"
        ),
    ),
]

# Add test views for "pretty" error pages in debug mode
if settings.DEBUG:
    urlpatterns += [
        path(
            "400/",
            error_handler.handler400,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            error_handler.handler403,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            error_handler.handler404,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", error_handler.handler500),
    ]
