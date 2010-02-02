from templateresponse import TemplateResponse


def home(request):
    return TemplateResponse(request, 'sixaphone/home.html', {
        'moose': True,
    })
