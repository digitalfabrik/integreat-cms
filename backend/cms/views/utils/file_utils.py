from ...models import DocumentForm


def save_file(request):
    status = 0
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            status = 1
    else:
        form = DocumentForm()

    return {'form': form, 'status': status}
