from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ...decorators import region_permission_required
from ...models import Document, Region


@login_required
@region_permission_required
def delete_file(request, document_id, region_slug):
    region = Region.objects.get(slug=region_slug)

    if request.method == 'POST':
        document = Document.objects.get(pk=document_id)
        document.delete()

    return redirect('media', **{'region_slug': region.slug})
