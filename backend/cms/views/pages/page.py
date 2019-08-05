"""

Returns:
    [type]: [description]
"""
import os
import uuid
import json
import logging

from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.views.static import serve

from .page_form import PageForm, PageTranslationForm
from ...models import Page, PageTranslation, Region, Language
from ...page_xliff_converter import PageXliffHelper, XLIFFS_DIR
from ...decorators import region_permission_required


logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class PageView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.view_pages'
    raise_exception = True

    template_name = 'pages/page.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get('region_slug'))

        language = Language.objects.get(code=kwargs.get('language_code'))

        # get page and translation objects if they exist
        page = Page.objects.filter(id=kwargs.get('page_id')).first()
        page_translation = PageTranslation.objects.filter(
            page=page,
            language=language,
        ).first()

        page_form = PageForm(
            instance=page,
            region=region,
            language=language,
        )
        page_translation_form = PageTranslationForm(
            instance=page_translation,
        )

        return render(request, self.template_name, {
            **self.base_context,
            'page_form': page_form,
            'page_translation_form': page_translation_form,
            'page': page,
            'language': language,
            'languages': region.languages,
        })

    # pylint: disable=R0912
    def post(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get('region_slug'))
        language = Language.objects.get(code=kwargs.get('language_code'))

        page_instance = Page.objects.filter(id=kwargs.get('page_id')).first()
        page_translation_instance = PageTranslation.objects.filter(
            page=page_instance,
            language=language,
        ).first()

        if not request.user.has_perm('cms.edit_page', page_instance):
            raise PermissionDenied

        page_form = PageForm(
            request.POST,
            instance=page_instance,
            region=region,
            language=language,
        )
        page_translation_form = PageTranslationForm(
            request.POST,
            instance=page_translation_instance,
            region=region,
            language=language,
        )

        if page_translation_form.data.get('public') and 'public' in page_translation_form.changed_data:
            if not request.user.has_perm('cms.publish_page', page_instance):
                raise PermissionDenied

        # TODO: error handling
        if page_form.is_valid() and page_translation_form.is_valid():

            page = page_form.save()
            page_translation = page_translation_form.save(
                page=page,
                user=request.user,
            )

            if page_form.has_changed() or page_translation_form.has_changed():
                published = page_translation.public and 'public' in page_translation_form.changed_data
                if page_form.data.get('submit_archive'):
                    # archive button has been submitted
                    messages.success(request, _('Page was successfully archived.'))
                elif not page_instance:
                    if published:
                        messages.success(request, _('Page was successfully created and published.'))
                    else:
                        messages.success(request, _('Page was successfully created.'))
                elif not page_translation_instance:
                    if published:
                        messages.success(request, _('Translation was successfully created and published.'))
                    else:
                        messages.success(request, _('Translation was successfully created.'))
                else:
                    if published:
                        messages.success(request, _('Translation was successfully published.'))
                    else:
                        messages.success(request, _('Translation was successfully saved.'))
            else:
                messages.info(request, _('No changes detected.'))

            return redirect('edit_page', **{
                'page_id': page.id,
                'region_slug': region.slug,
                'language_code': language.code,
            })

        messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            **self.base_context,
            'page_form': page_form,
            'page_translation_form': page_translation_form,
            'page': page_instance,
            'language': language,
            'languages': region.languages,
        })


@login_required
@region_permission_required
def archive_page(request, page_id, region_slug, language_code):
    page = Page.objects.get(id=page_id)

    if not request.user.has_perm('cms.edit_page', page):
        raise PermissionDenied

    page.public = False
    page.archived = True
    page.save()

    messages.success(request, _('Page was successfully archived.'))

    return redirect('pages', **{
                'region_slug': region_slug,
                'language_code': language_code,
    })


@login_required
@region_permission_required
def restore_page(request, page_id, region_slug, language_code):
    page = Page.objects.get(id=page_id)

    if not request.user.has_perm('cms.edit_page', page):
        raise PermissionDenied

    page.archived = False
    page.save()

    messages.success(request, _('Page was successfully restored.'))

    return redirect('pages', **{
                'region_slug': region_slug,
                'language_code': language_code,
    })


@login_required
@region_permission_required
@permission_required('cms.view_pages', raise_exception=True)
def view_page(request, page_id, region_slug, language_code):
    template_name = 'pages/page_view.html'
    page = Page.objects.get(id=page_id)

    page_translation = page.get_translation(language_code)

    return render(
        request,
        template_name,
        {
            "page_translation": page_translation
        }
    )


@login_required
@region_permission_required
@permission_required('cms.view_pages', raise_exception=True)
def download_page_xliff(request, page_id, region_slug, language_code):
    page = Page.objects.get(id=page_id)
    page_xliff_helper = PageXliffHelper()
    page_xliff_zip_file = page_xliff_helper.export_page_xliffs_to_zip(page)
    if page_xliff_zip_file and page_xliff_zip_file.startswith(XLIFFS_DIR):
        response = serve(request, page_xliff_zip_file.split(XLIFFS_DIR)[1], document_root=XLIFFS_DIR)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(page_xliff_zip_file.split(os.sep)[-1])
        return response
    raise Http404


@login_required
@region_permission_required
@permission_required('cms.edit_pages', raise_exception=True)
def upload_page(request, region_slug, language_code):
    if request.method == 'POST' and 'xliff_file' in request.FILES:
        page_xliff_helper = PageXliffHelper()
        xliff_file = request.FILES['xliff_file']
        if xliff_file and  xliff_file.name.endswith(('.zip', '.xliff', '.xlf')):
            filename = xliff_file.name
            file_path = os.path.join(XLIFFS_DIR, 'upload', str(uuid.uuid4()), filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as upload_file:
                for chunk in xliff_file.chunks():
                    upload_file.write(chunk)
            if filename.endswith('.zip'):
                page_xliff_helper.import_xliffs_zip_file(file_path, request.user)
            else:
                page_xliff_helper.import_xliff_file(file_path, request.user)

            page_xliff_helper.delete_tmp_in_xliff_folder(file_path)

    return redirect('pages', **{
                'region_slug': region_slug,
                'language_code': language_code,
    })


@login_required
@region_permission_required
@permission_required('cms.edit_pages', raise_exception=True)
@permission_required('cms.grant_page_permissions', raise_exception=True)
def grant_page_permission_ajax(request):

    data = json.loads(request.body.decode('utf-8'))
    permission = data.get('permission')
    page_id = data.get('page_id')
    user_id = data.get('user_id')

    logger.info(
        'Ajax call: The user %s wants to grant the permission to %s page with id %s to user with id %s.',
        request.user.username,
        permission, page_id, user_id
    )

    page = Page.objects.get(id=page_id)
    user = get_user_model().objects.get(id=user_id)

    if not request.user.has_perm('cms.grant_page_permissions'):
        logger.info(
            'Error: The user %s does not have the permission to grant page permissions.',
            request.user.username
        )
        raise PermissionDenied

    if not (request.user.is_superuser or request.user.is_staff):
        # additional checks if requesting user is no superuser or staff
        if page.region not in request.user.profile.regions:
            # requesting user can only grant permissions for pages of his region
            logger.info(
                'Error: The user %s cannot grant permissions for region %s.',
                request.user.username,
                page.region.name
            )
            raise PermissionDenied
        if page.region not in user.profile.regions:
            # user can only receive permissions for pages of his region
            logger.info(
                'Error: The user %s cannot receive permissions for region %s.',
                user.username,
                page.region.name
            )
            raise PermissionDenied

    if permission == 'edit':
        # check, if the user already has this permission
        if user.has_perm('cms.edit_page', page):
            message = _('Information: The user {user} has this permission already.').format(
                user=user.username
            )
            level_tag = 'info'
        else:
            # else grant the permission by adding the user to the editors of the page
            page.editors.add(user)
            page.save()
            message = _('Success: The user {user} can now edit this page.').format(
                user=user.username
            )
            level_tag = 'success'
    elif permission == 'publish':
        # check, if the user already has this permission
        if user.has_perm('cms.publish_page', page):
            message = _('Information: The user {user} has this permission already.').format(
                user=user.username
            )
            level_tag = 'info'
        else:
            # else grant the permission by adding the user to the publishers of the page
            page.publishers.add(user)
            page.save()
            message = _('Success: The user {user} can now publish this page.').format(
                user=user.username
            )
            level_tag = 'success'
    else:
        logger.info(
            'Error: The permission %s is not supported.',
            permission
        )
        raise PermissionDenied

    logger.info(message)

    return render(request, 'pages/_page_permission_table.html', {
        'page': page,
        'page_form': PageForm(instance=page),
        'permission_message': {
            'message': message,
            'level_tag': level_tag
        }
    })


@login_required
@region_permission_required
@permission_required('cms.edit_pages', raise_exception=True)
@permission_required('cms.grant_page_permissions', raise_exception=True)
def revoke_page_permission_ajax(request):

    data = json.loads(request.body.decode('utf-8'))
    permission = data.get('permission')
    page_id = data.get('page_id')
    page = Page.objects.get(id=page_id)
    user = get_user_model().objects.get(id=data.get('user_id'))

    logger.info(
        'Ajax call: The user %s wants to revoke the permission to %s page with id %s from user %s.',
        request.user.username,
        permission,
        page_id,
        user.username
    )

    if not request.user.has_perm('cms.grant_page_permissions'):
        logger.info(
            'Error: The user %s does not have the permission to revoke page permissions.',
            request.user.username
        )
        raise PermissionDenied

    if not (request.user.is_superuser or request.user.is_staff):
        # additional checks if requesting user is no superuser or staff
        if page.region not in request.user.profile.regions:
            # requesting user can only revoke permissions for pages of his region
            logger.info(
                'Error: The user %s cannot revoke permissions for region %s.',
                request.user.username, page.region.name
            )
            raise PermissionDenied

    if permission == 'edit':
        if user in page.editors.all():
            # revoke the permission by removing the user to the editors of the page
            page.editors.remove(user)
            page.save()
        # check, if the user has this permission anyway
        if user.has_perm('cms.edit_page', page):
            message = _('Information: The user {user} has been removed from the editors of this page, '
                        'but has the implicit permission to edit this page anyway.').format(
                            user=user.username
                        )
            level_tag = 'info'
        else:
            message = _('Success: The user {user} cannot edit this page anymore.').format(
                user=user.username
            )
            level_tag = 'success'
    elif permission == 'publish':
        if user in page.publishers.all():
            # revoke the permission by removing the user to the publishers of the page
            page.publishers.remove(user)
            page.save()
        # check, if the user already has this permission
        if user.has_perm('cms.publish_page', page):
            message = _('Information: The user {user} has been removed from the publishers of this page, '
                        'but has the implicit permission to publish this page anyway.').format(
                            user=user.username
                        )
            level_tag = 'info'
        else:
            message = _('Success: The user {user} cannot publish this page anymore.').format(
                user=user.username
            )
            level_tag = 'success'
    else:
        logger.info(
            'Error: The permission %s is not supported.',
            permission
        )
        raise PermissionDenied

    logger.info(message)

    return render(request, 'pages/_page_permission_table.html', {
        'page': page,
        'page_form': PageForm(instance=page),
        'permission_message': {
            'message': message,
            'level_tag': level_tag
        }
    })
