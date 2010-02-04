from django.conf import settings


def typekit(request):
    try:
        return {'typekit_code': settings.TYPEKIT_CODE}
    except AttributeError:
        return {}
