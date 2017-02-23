from decimal import Decimal
import decimal
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from localflavor.us.us_states import US_STATES
from django.utils.safestring import mark_safe
import json
from sundog import utils


register = template.Library()


@register.filter(name='currency')
def currency(number):
    dollars = Decimal(number or 0).quantize(Decimal('.01'))
    if dollars is None:
        return "N/A"
    else:
        return "$%s" % str(intcomma(dollars, True))


@register.filter(name='percent')
def percent(number):
    if number is None:
        return "N/A"
    else:
        return "%s" % str(number) + '%'


@register.filter(name='addcss')
def addcss(field, css):
    return field.as_widget(attrs={"class": css})


@register.filter(name='stateName')
def statename(statecod):
    state_name = [tuple[1] for tuple in US_STATES if tuple[0] == statecod]
    return state_name[0]


@register.filter
def jsonify(jlist):
    if jlist:
        return mark_safe(json.dumps(jlist))
    else:
        return 'null'


@register.filter(name='formatDatetime')
def format_datetime(datetime):
    if datetime is None:
        return ''
    else:
        return utils.format_date(datetime)


@register.filter(name='paginatorRange')
def paginator_range(paginator, page_number):
    len_range = len(paginator.page_range)
    if len_range < 8:
        return paginator.page_range
    else:
        page_index = paginator.page_range.index(page_number)
        result = page_index // 8
        first_number = 8 * result
        last_number = 8 + (8 * result)
        last_number = last_number if last_number <= len_range else len_range
        return paginator.page_range[first_number:last_number]


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name='multiply')
def multiply(value, arg):
    return Decimal(value) * Decimal(arg)


@register.filter(name='divide')
def divide(value, arg):
    return Decimal(value) / Decimal(arg)


@register.filter(name='minus')
def minus(value, arg):
    return value - arg


@register.filter(name='get_sort_class')
def get_sort_class(sort, label):
    return sort['class'] if sort['name'] == label else 'sorting'


@register.filter(name='cut_string_at')
def cut_string_at(text, max=100):
    cut_text = text[:100] + '...' if len(text) > max else text
    return cut_text
