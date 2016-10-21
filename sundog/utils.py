import calendar
from datetime import datetime, timedelta
import os
from decimal import Decimal
import uuid
from django.utils.html import strip_tags
import pytz
from django_auth_app.services import get_user_timezone
import settings
import hashlib
from sundog.constants import SHORT_DATE_FORMAT


def document_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/documents/<related_file_id>/<filename>
    return os.path.join('documents', str(instance.file.file_id), filename)


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


def to_int(string, default=-1):
    try:
        result = int(string)
    except:
        result = default
    return result


def add_months(date, months):
    month = date.month - 1 + months
    year = int(date.year + month / 12)
    month = month % 12 + 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day)


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
            number = payment_data[prefix + '-number']
            date = datetime.strptime(payment_data[prefix + '-date'], SHORT_DATE_FORMAT)
            amount = Decimal(payment_data[prefix + '-amount'])
            payment = {'number': number, 'date': date, 'amount': amount}
            payments.append(payment)
            index += 1
    return payments


def get_next_work_date(date):
    week_day = date.weekday()
    if week_day in [5, 6]:
        date += timedelta(days=7 - week_day)
    return date
