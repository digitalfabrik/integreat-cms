from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.http import JsonResponse
from django.views.decorators.http import require_POST

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

from ...constants import translation_status
from ...models.pages.page import Page
from ...utils.content_edit_lock import get_locking_user, lock_content, unlock_content

logger = logging.getLogger(__name__)

#: `edit_lock_key` types this heartbeat also knows how to check machine
#: translation progress for - currently pages only (see the model class name
#: `edit_lock_key` uses, e.g. `type(self).__name__` for a `Page`).
MT_SUPPORTED_LOCK_TYPES = {"Page": Page}


def _get_active_child_mt_task_id(page: Page, language_slug: str) -> str | None:
    """
    Check whether this page currently has a machine translation running into
    one of its child languages in the tree (i.e. triggered from this very
    language via the "auto-translate" checkboxes below the form). Checking
    any one child is enough, since a single trigger covers all its target
    languages with the same Celery task.

    Deliberately does not filter children by `language_node.mt_provider` the
    way `MachineTranslationForm` does when building its checkboxes: that
    filter answers "what could a user choose to trigger right now" (gating
    new actions), whereas this answers "is something already triggered still
    running" - which only depends on whether the lock exists, not on whether
    the current provider config would still permit starting a new one today.

    :param page: The page being edited
    :param language_slug: The language currently being edited (the potential source)
    :return: The id of the running task, or ``None`` if none is active
    """
    region = page.region
    parent_node = region.language_node_by_slug.get(language_slug)
    if parent_node is None:
        return None
    for language_node in region.language_tree:
        if language_node.parent_id == parent_node.id and (
            task_id := page.get_machine_translation_task_id(language_node.slug)
        ):
            return task_id
    return None


def _get_machine_translation_status(
    id_: int | str | None, type_: str, language_slug: str | None
) -> dict[str, Any]:
    """
    :param id_: The id of the content object being edited
    :param type_: The `edit_lock_key` type of the content object (e.g. "Page")
    :param language_slug: The slug of the language currently being edited
    :return: A dict with two keys: ``currentlyInMachineTranslation`` (whether
        that specific object/language is currently being machine-translated -
        not whether *any* language of it is, since editing one language
        shouldn't be blocked by MT running on another) and
        ``activeChildTranslationTaskId`` (the id of a task translating this
        same object from this language into one of its children, if any)
    """
    default = {
        "currentlyInMachineTranslation": False,
        "activeChildTranslationTaskId": None,
    }
    if not language_slug or (model := MT_SUPPORTED_LOCK_TYPES.get(type_)) is None:
        return default
    content_object = model.objects.filter(id=id_).first()
    if content_object is None:
        return default
    return {
        "currentlyInMachineTranslation": (
            content_object.get_translation_state(language_slug)
            == translation_status.MACHINE_TRANSLATION_IN_PROGRESS
        ),
        "activeChildTranslationTaskId": _get_active_child_mt_task_id(
            content_object, language_slug
        ),
    }


@require_POST
def content_edit_lock_heartbeat(
    request: HttpRequest,
    region_slug: str | None = None,
) -> JsonResponse:
    """
    This function handles heartbeat requests.
    When a heartbeat is received, this function tries to extend the lock for a user
    who is editing some content.

    :param request: The current request
    :return: Json object containing `success: true` if the lock could be acquired
    """
    body = json.loads(request.body.decode("utf-8"))
    id_, type_ = json.loads(body["key"])

    if body["force"] and (locking_user := get_locking_user(id_, type_)):
        logger.debug(
            "User %r took control over %s with id %s from %r",
            request.user,
            type_,
            id_,
            locking_user,
        )
        unlock_content(id_, type_, locking_user)

    success = lock_content(id_, type_, request.user)
    locking_user = request.user if success else get_locking_user(id_, type_)
    if TYPE_CHECKING:
        assert locking_user
    return JsonResponse(
        {
            "success": success,
            "lockingUser": locking_user.full_user_name,
            **_get_machine_translation_status(id_, type_, body.get("languageSlug")),
        },
    )


@require_POST
def content_edit_lock_release(
    request: HttpRequest,
    region_slug: str | None = None,
) -> JsonResponse:
    """
    This function handles unlock requests

    :param request: The current request
    :return: Json object containing `success: true` if the content object could be unlocked
    """
    body = json.loads(request.POST.get("body"))
    id_, type_ = body

    success = unlock_content(id_, type_, request.user)
    return JsonResponse({"success": success})
