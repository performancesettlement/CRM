from datetime import datetime, timedelta
from decimal import Decimal
import decimal
from django.http import Http404
from django.utils.html import strip_tags
from sundog.constants import SHORT_DATE_FORMAT

import calendar
import hashlib
import os
import pytz
import settings


def get_or_404(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return Http404(
            '{model_name} not found'
            .format(
                model_name=classmodel.__name__,
            )
        )


def import_file_path(f_name, date_time, user_id):
    file_name, file_extension = os.path.splitext(f_name)
    file_name += date_time.strftime("_%Y-%m-%d_%H-%M-%S")
    return os.path.join(
        settings.PROJECT_ROOT,
        'import',
        'history',
        str(user_id),
        file_name + file_extension
    )


def format_date(date):
    return date.strftime("%b. %d, %Y, %I:%M %p")


def utc_to_local(utc_dt, timezone):
    local_tz = pytz.timezone(timezone)
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)  # .normalize might be unnecessary


def save_import_file(f, file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def md5_for_file(chunks):
    md5 = hashlib.md5()
    for data in chunks:
        md5.update(data)
    return md5.hexdigest()

TWO_PLACES = Decimal('0.01')
FOUR_PLACES = Decimal('0.0001')


def roundup_places(number, places=TWO_PLACES):
    return number.quantize(places)


def format_price(price):
    return str(roundup_places(price))


def get_data(prefix, post_data):
    data = {}
    for data_key in post_data.keys():
        if data_key.startswith(prefix + '-') and post_data[data_key]:
            data[data_key] = post_data[data_key]
    if not data:
        data = None
    return data


def get_enum_name(code, names, default=''):
    return (
        str(
            next(
                (
                    name
                    for code_, name in names
                    if code_ == code
                ),
                default,
            ),
        )
        if code
        else default
    )


def get_form_errors(form):
    return [
        "{title}: {field_error}".format(
            title=strip_tags(
                field
                .html_name
                .replace("_", " ")
                .title()
            ),
            field_error=field_error,
        )
        for field in form
        if field.errors
        for field_error in field.errors
    ] + [
        non_field_error
        for non_field_errors in [form.non_field_errors()]
        if non_field_errors
        for non_field_error in non_field_errors
    ]


def to_int(string, default=-1):
    try:
        result = int(string)
    except:
        result = default
    return result


def add_months(date, months):
    if months != 0:
        month = date.month - 1 + months
        year = int(date.year + month / 12)
        month = month % 12 + 1
        day = min(date.day, calendar.monthrange(year, month)[1])
        return datetime(year, month, day)
    else:
        return date


def get_debts_ids(data):
    debt_ids = data.get('debt_ids')
    if debt_ids:
        debt_ids = [int(debt_id) for debt_id in debt_ids.split(',')]
    return debt_ids


def get_fees_values(data):
    fee_values = []
    fee_index = 1
    found = True
    while found:
        found = False
        for key, value in data.items():
            if key.startswith('id_' + str(fee_index)):
                fee_values.append(value)
                fee_index += 1
                found = True
                break
        if not found:
            break
    return fee_values


def get_payments_data(data, starting_index=3):
    found = True
    index = starting_index
    payments = []
    while found:
        prefix = str(index)
        found = False
        payment_data = get_data(prefix, data)
        if payment_data:
            found = True
            date = datetime.strptime(
                payment_data.pop(prefix + '-date'),
                SHORT_DATE_FORMAT
            ).replace(tzinfo=pytz.utc)
            amount = Decimal(payment_data.pop(prefix + '-amount'))
            payment = {
                'date': date,
                'amount': amount
            }
            for key, value in payment_data.items():
                fee_name = key.replace(prefix + '-', '')
                fee_value = Decimal(value)
                payment[fee_name] = fee_value
            payments.append(payment)
            index += 1
    return payments


def get_forms(data, form_class, prefix=1, instances=None, until=None):
    forms = []
    while True:
        form_data = get_data(str(prefix), data)
        if form_data:
            kwargs = {'prefix': prefix}
            if instances:
                got_ids = [value for key, value in form_data.items() if '_id' in key]
                entity_id = int(got_ids[0]) if got_ids else None
                if entity_id:
                    instances_ids = [instance.pk for instance in instances]
                    try:
                        i = instances_ids.index(entity_id)
                    except ValueError:
                        i = -1
                    if i >= 0:
                        instance = instances.pop(i)
                        kwargs['instance'] = instance
            forms.append(form_class(form_data, **kwargs))
            prefix += 1
        else:
            break
        if until and until < prefix:
            break
    return forms, instances


def get_next_work_date(date):
    week_day = date.weekday()
    if week_day in [5, 6]:
        date += timedelta(days=7 - week_day)
    return date


def get_date_from_str(date_str):
    return (
        datetime
        .strptime(
            date_str,
            SHORT_DATE_FORMAT,
        ).replace(
            tzinfo=pytz.utc,
        )
    )


def get_dti(incomes, expenses):
    if incomes:
        return (expenses * Decimal('100') / incomes).quantize(Decimal('.01'), rounding=decimal.ROUND_UP)
    else:
        return Decimal('0.00')
