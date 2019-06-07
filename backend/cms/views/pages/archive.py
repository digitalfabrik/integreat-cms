"""
Functionality for providing archive with all pages
"""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.views.generic import TemplateView

from ...models import Page, Site, Language
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class ArchivedPagesView(TemplateView):
	template_name = 'pages/archive.html'
	base_context = {'current_menu_item': 'pages'}

	def get(self, request, *args, **kwargs):
		# current site
		site_slug = kwargs.get('site_slug')
		site = Site.objects.get(slug=site_slug)

		# current language
		language_code = kwargs.get('language_code', None)
		if language_code:
			language = Language.objects.get(code=language_code)
		elif site.default_language:
			return redirect('pages', **{
				'site_slug': site_slug,
				'language_code': site.default_language.code,
			})

		# all archived pages of the current site in the current language
		pages = Page.get_archived(site_slug)
		
		# all other languages of current site
		languages = site.languages

		return render(
			request,
			self.template_name,
			{
				**self.base_context,
				'pages': pages,
				'language': language,
				'languages': languages,
			}
		)
