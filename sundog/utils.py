import os
from decimal import Decimal
import pytz
from django_auth_app.services import get_user_timezone
import settings
import hashlib


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
