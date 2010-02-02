from templateresponse import TemplateResponse


def home(request):
    return TemplateResponse(request, 'home.html', {
        'moose': True,
    })
