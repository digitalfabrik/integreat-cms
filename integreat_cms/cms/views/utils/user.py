from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from integreat_cms.cms.models.users.user import User

from ...models import Page


def get_pages_observer_has_access_to(user: User) -> list:
    """
    This function checks which pages a user of a region has access to.

    :param user: The user for which the access rights are checked
    """
    if user is None:
        return []

    pages_user_has_access_to = (
        Page.objects.prefetch_related("authors", "editors")
        .filter(Q(authors=user) | Q(editors=user))
        .distinct()
    )

    access_data = []
    for page in pages_user_has_access_to:
        roles = []
        if user in page.authors.all():
            roles.append(_("Author"))
        if user in page.editors.all():
            roles.append(_("Editor"))
        access_data.append(
            {"page": page, "roles": ", ".join(str(role) for role in roles)}
        )
    return access_data
