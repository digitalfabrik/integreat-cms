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
from django.conf.urls import include, url
from django.views.generic import RedirectView

from ..views import (
    authentication,
    dashboard,
    imprint,
    pages,
)

#: The namespace for this URL config (see :attr:`django.urls.ResolverMatch.app_name`)
app_name = "public"

#: The url patterns of this module (see :doc:`topics/http/urls`)
urlpatterns = [
    url(r"^$", dashboard.RegionSelection.as_view(), name="region_selection"),
    url(
        r"^s/",
        include(
            [
                url(
                    r"^p/(?P<short_url_id>[0-9]+)$",
                    pages.expand_page_translation_id,
                    name="expand_page_translation_id",
                ),
                url(
                    r"^i/(?P<imprint_translation_id>[0-9]+)$",
                    imprint.expand_imprint_translation_id,
                    name="expand_imprint_translation_id",
                ),
            ]
        ),
    ),
    url(
        r"^login/",
        include(
            [
                url(r"^$", authentication.LoginView.as_view(), name="login"),
                url(
                    r"^mfa/",
                    include(
                        [
                            url(
                                r"^$",
                                authentication.MfaLoginView.as_view(),
                                name="login_mfa",
                            ),
                            url(
                                r"^assert$",
                                authentication.MfaAssertView.as_view(),
                                name="login_mfa_assert",
                            ),
                            url(
                                r"^verify$",
                                authentication.MfaVerifyView.as_view(),
                                name="login_mfa_verify",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    url(r"^logout/$", authentication.LogoutView.as_view(), name="logout"),
    url(
        r"^reset-password/",
        include(
            [
                url(
                    r"^$",
                    authentication.PasswordResetView.as_view(),
                    name="password_reset",
                ),
                url(
                    r"^(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
                    authentication.PasswordResetConfirmView.as_view(),
                    name="password_reset_confirm",
                ),
            ]
        ),
    ),
    url(
        r"^activate-account/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
        authentication.AccountActivationView.as_view(),
        name="activate_account",
    ),
    url(
        r"^wiki",
        RedirectView.as_view(url=settings.WIKI_URL),
        name="wiki_redirect",
    ),
    url(
        r"^favicon\.ico$", RedirectView.as_view(url="/static/images/integreat-icon.png")
    ),
]
