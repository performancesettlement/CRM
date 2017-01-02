from django.template import Library
from django.urls import reverse


register = Library()


@register.inclusion_tag(
    'sundog/templatetags/action.html',
    takes_context=True,
)
def action(
    context,
    viewname,
    glyphicon,
    label=None,
    extra_attributes='',
    fm=False,
    **kwargs
):
    instance = context['instance']
    label = label or type(instance)._meta.verbose_name.title()
    return {
        **locals(),
        'class': viewname.replace('.', '-'),
        'url': reverse(viewname=viewname, kwargs=kwargs),
    }


@register.inclusion_tag(
    'sundog/templatetags/action.html',
    takes_context=True,
)
def action_delete(
    context,
    viewname,
    label=None,
    extra_attributes='',
    **kwargs
):
    instance = context['instance']
    label = label or type(instance)._meta.verbose_name.title()
    return action(
        glyphicon='trash',
        label=f'Delete {label}',
        fm='delete',
        **{
            key: value
            for key, value in locals().items()
            if key not in [
                'instance',
                'kwargs',
                'label',
            ]
        },
        **kwargs,
    )


@register.inclusion_tag(
    'sundog/templatetags/action.html',
    takes_context=True,
)
def action_quick_edit(
    context,
    viewname,
    label=None,
    extra_attributes='',
    **kwargs
):
    instance = context['instance']
    label = label or type(instance)._meta.verbose_name.title()
    return action(
        glyphicon='pencil',
        label=f'Quick Edit {label}',
        fm='update',
        **{
            key: value
            for key, value in locals().items()
            if key not in [
                'instance',
                'kwargs',
                'label',
            ]
        },
        **kwargs,
    )


@register.inclusion_tag(
    'sundog/templatetags/action.html',
    takes_context=True,
)
def action_edit(
    context,
    viewname,
    label=None,
    extra_attributes='',
    **kwargs
):
    instance = context['instance']
    label = label or type(instance)._meta.verbose_name.title()
    return action(
        glyphicon='arrow-right',
        label=f'Edit {label}',
        **{
            key: value
            for key, value in locals().items()
            if key not in [
                'instance',
                'kwargs',
                'label',
            ]
        },
        **kwargs,
    )
