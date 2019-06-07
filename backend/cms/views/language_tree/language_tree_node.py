"""

Returns:
    [type]: [description]
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from .language_tree_node_form import LanguageTreeNodeForm
from ...models import Language, LanguageTreeNode, Site
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class LanguageTreeNodeView(TemplateView):
    template_name = 'language_tree/tree_node.html'
    base_context = {'current_menu_item': 'language_tree'}

    def get(self, request, *args, **kwargs):
        language_tree_node_id = self.kwargs.get('language_tree_node_id')
        # limit possible parents to nodes of current region
        parent_queryset = Site.get_current_site(request).language_tree_nodes
        # limit possible languages to those which are not yet included in the tree
        language_queryset = Language.objects.exclude(
            language_tree_nodes__in=parent_queryset.exclude(id=language_tree_node_id)
        )
        if language_tree_node_id:
            language_tree_node = LanguageTreeNode.objects.get(id=language_tree_node_id)
            children = language_tree_node.get_descendants(include_self=True)
            parent_queryset = parent_queryset.difference(children)
            form = LanguageTreeNodeForm(initial={
                'language': language_tree_node.language,
                'parent': language_tree_node.parent,
                'active': language_tree_node.active,
            })
        else:
            form = LanguageTreeNodeForm()
        form.fields['parent'].queryset = parent_queryset
        form.fields['language'].queryset = language_queryset
        return render(request, self.template_name, {
            'form': form, **self.base_context})

    def post(self, request, site_slug, language_tree_node_id=None):
        # TODO: error handling
        form = LanguageTreeNodeForm(data=request.POST, site_slug=site_slug)
        if form.is_valid():
            if language_tree_node_id:
                form.save_language_node(
                    language_tree_node_id=language_tree_node_id,
                )
                messages.success(request, _('Language tree node was saved successfully.'))
            else:
                language_tree_node = form.save_language_node()
                messages.success(request, _('Language tree node was created successfully.'))
                return redirect('edit_language_tree_node', **{
                    'language_tree_node_id': language_tree_node.id,
                    'site_slug': site_slug,
                })
            # TODO: improve messages
        else:
            messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            'form': form, **self.base_context})
