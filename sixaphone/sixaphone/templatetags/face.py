from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter(name='numerify')
@stringfilter
def numerify(value):
    return str(sum(map(lambda x: int(x, 16), value)) % 6 + 1)
