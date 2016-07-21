from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from localflavor.us.us_states import US_STATES
from django.utils.safestring import mark_safe
import json
from sundog import constants, utils
from sundog.models import CAMPAIGN_SOURCES_CHOICES

register = template.Library()


@register.filter(name='times')
def times(number):
    return range(number)


@register.filter(name='currency') 
def currency(dollars):
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
    return field.as_widget(attrs={"class":css})


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


@register.filter(name='priorityColor')
def priority_color(priority):
    listp = [i[1] for i in constants.PRIORITY_COLOR_CHOICES if i[0] == priority]
    if priority is not None and listp:
        return listp[0]
    else:
        return 'text-default'


@register.filter(name='priorityName')
def priority_name(priority):
    listp = [i[1] for i in constants.PRIORITY_CHOICES if i[0] == priority]
    if priority is not None and listp:
        return listp[0]
    else:
        return 'No priority'


@register.filter(name='formatDatetime')
def format_datetime(datetime):
    if datetime is None:
        return ''
    else:
        return utils.format_date(datetime)


@register.filter(name='formatDatetimeTz')
def format_datetime_tz(datetime, user_id):
    if datetime is None:
        return ''
    else:
        return utils.format_date(utils.set_date_to_user_timezone(datetime, user_id))


@register.filter(name='paginatorRange')
def paginator_range(paginator, page_number):
    len_range = len(paginator.page_range)
    if len_range<8:
        return paginator.page_range
    else:
        page_index = paginator.page_range.index(page_number)
        result = page_index//8
        first_number = 8*result
        last_number = 8 + (8*result)
        last_number = last_number if last_number<=len_range else len_range
        return paginator.page_range[first_number:last_number]


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name='media_type')
def times(media_type):
    media_label = ''
    for media_data in CAMPAIGN_SOURCES_CHOICES:
        if media_data[0] == media_type:
            media_label = media_data[1]
    return media_label


@register.filter(name='multiply')
def multiply(value, arg):
    return value * arg
    

@register.filter(name='minus')
def minus(value, arg):
    return value - arg


@register.filter()
def get_sort_class(sort, label):
    return sort['class'] if sort['name'] == label else 'sorting'

