from datetime import datetime
from decimal import Decimal
from django.db.models import CharField
from django.http import Http404
from django.utils.html import strip_tags
from django_auth_app.services import get_user_timezone

import hashlib
import os
import pytz
import settings
import uuid


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
    return os.path.join(settings.PROJECT_ROOT, 'import', 'history', str(user_id), file_name+file_extension)


def format_date(date):
    return date.strftime("%b. %d, %Y, %I:%M %p")


def utc_to_local(utc_dt, timezone):
    local_tz = pytz.timezone(timezone)
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt) # .normalize might be unnecessary


def set_date_to_user_timezone(date, user_id):
    local_date = date
    user_tz = get_user_timezone(user_id)
    if user_tz:
        local_date = utc_to_local(date, user_tz)

    return local_date


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


def format_price(price):
    return str(price.quantize(TWO_PLACES))


def get_now(timezone=pytz.utc):
    now = datetime.utcnow()
    now = now.replace(tzinfo=timezone)
    return now


def hash_password(bank_account):
    salt = uuid.uuid4().hex
    password = bank_account.account_number
    bank_account.account_number = hashlib.sha512((password + salt).encode('utf-8')).hexdigest()
    bank_account.account_number_salt = salt
    bank_account.account_number_last_4_digits = password[-4:]


def get_form_errors(form):
    form_errors = []
    for field in form:
        if field.errors:
            for field_error in field.errors:
                error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                form_errors.append(error)
    for non_field_error in form.non_field_errors():
        form_errors.append(non_field_error)
    return form_errors


def get_data(prefix, post_data):
    data = {}
    for data_key in post_data.keys():
        if data_key.startswith(prefix + '-') and post_data[data_key]:
            data[data_key] = post_data[data_key]
    if not data:
        data = None
    return data


def const(x, *_, **__):
    return lambda *_, **__: x


# From https://djangosnippets.org/snippets/2328/
class LongCharField(CharField):
    "A basically unlimited-length CharField."
    description = "Unlimited-length string"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = int(1e9)  # Satisfy management validation.
        # Don't add max-length validator like CharField does.
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        # This has no function, since this value is used as a lookup in
        # db_type().  Put something that isn't known by Django so it
        # raises an error if it's ever used.
        return 'LongCharField'

    def db_type(self, connection):
        return 'text'

    def formfield(self, **kwargs):
        # Don't pass max_length to form field like CharField does.
        return super().formfield(**kwargs)
