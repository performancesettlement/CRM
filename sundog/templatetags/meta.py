from django.template import Library


register = Library()


@register.simple_tag
def model_verbose_name(model):
    return model._meta.verbose_name.title()
