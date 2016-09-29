import copy

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from sundog.models import MyFile, Contact, ClientType, FileStatusHistory, FileStatus, FileAccessHistory, FileStatusStat, SundogDocument, Tag, FileImportHistory, \
    Stage, Status
from django.contrib.auth.models import User, Permission
from django.db.models import Q
import logging
from sundog import messages
from sundog import constants
from xlrd import open_workbook, xldate_as_tuple
from django.core.cache import cache
from decimal import Decimal
from datetime import datetime, timedelta
from sundog import utils
from django_auth_app.enums import US_STATES

#initialize logger
logger = logging.getLogger(__name__)


# def get_areas_by_state(state_id):
#     results = None
#     try:
#         results = AreaOfInterest.objects.filter(state=state_id)
#
#     except Exception as e:
#         logger.error(messages.ERROR_GET_AREAS % state_id)
#         logger.error(e)
#
#     return results
#
#
# def get_communities_by_area(area_id):
#     results = None
#     try:
#         results = CommunityOfInterest.objects.filter(area=area_id)
#
#     except Exception as e:
#         logger.error(messages.ERROR_GET_COMMUNITIES % area_id)
#         logger.error(e)
#
#     return results

@transaction.atomic
def reorder_stages(new_order_list):
    stages = {x.stage_id: x for x in list(Stage.objects.all())}
    order = 1
    for new_stage in new_order_list:
        stage = stages[new_stage]
        stage.order = order
        stage.save()
        order += 1


@transaction.atomic
def reorder_status(new_order_list, stage_id):
    statuses = {x.status_id: x for x in list(Status.objects.filter(stage__stage_id=stage_id))}
    order = 1
    for new_status in new_order_list:
        status = statuses[new_status]
        status.order = order
        status.save()
        order += 1


def get_impersonable_users(user_id):
    if not user_id:
        return []
    return User.objects.all().exclude(id=user_id)


def get_user_status_permissions(user):
    try:
        permission_prefix = 'sundog.' + constants.STATUS_CODENAME_PREFIX
        status_name_prefix = 'Can use status '
        all_user_perms = user.get_all_permissions()
        all_status_perms = Permission.objects.filter(codename__in=[x.split(".")[1] for x in all_user_perms
                                                                   if x.startswith(permission_prefix)])
        return [status.name.replace(status_name_prefix, "").upper() for status in list(all_status_perms)]
    except Exception as e:
        if user is not None:
            logger.error(messages.ERROR_GET_STATUS_PERMISSIONS % user.username)
        else:
            logger.error(messages.ERROR_USER_NONE)
        logger.error(e)
        return None


def get_files_by_user(user, from_admin=False):
    results = None
    try:
        if user.is_superuser:
            if from_admin:
                results = MyFile.objects.all()
            else:
                results = MyFile.objects.filter(active=True)
        else:
            # filter file for status permission
            permissions_name_array = get_user_status_permissions(user)

            # filter permission to view all files or only files where the user is participant
            if user.has_perm('sundog.view_all_files'):
                if from_admin:
                    results = MyFile.objects.filter(current_status__name__in=permissions_name_array)
                else:
                    results = MyFile.objects.filter(active=True, current_status__name__in=permissions_name_array)
            else:
                if from_admin:
                    results = MyFile.objects.filter(current_status__name__in=permissions_name_array,
                                                    participants__id=user.id)
                else:
                    results = MyFile.objects.filter(active=True, current_status__name__in=permissions_name_array,
                                                    participants__id=user.id)
    except Exception as e:
        logger.error(messages.ERROR_GET_FILES)
        logger.error(e)

    return results


def get_status_list_by_user(user, from_admin=False):
    results = None
    try:
        if user.is_superuser:
            if from_admin:
                results = FileStatus.objects.all().order_by('order', 'name')
            else:
                results = FileStatus.objects.filter(active=True).order_by('order', 'name')
        else:
            permissions_status_list = get_user_status_permissions(user)
            if from_admin:
                results = FileStatus.objects.filter(name__in=copy.copy(permissions_status_list)).order_by('order', 'name')
            else:
                results = FileStatus.objects.filter(active=True, name__in=copy.copy(permissions_status_list)).order_by('order', 'name')
    except Exception as e:
        logger.error(messages.ERROR_GET_FILES_STATUS)
        logger.error(e)

    return results


def get_stages_by_type(type):
    return Stage.objects.filter(stage__type=type)


def get_default_status():
    value = cache.get('default_status_id')
    if value is not None:
        return value
    try:
        value = FileStatus.objects.filter(active=True).order_by('order', 'name')[:1].get().status_id
        cache.set('default_status_id', value, constants.CACHE_IMPORT_EXPIRATION)
    except Exception as e:
        pass
    return value


def get_file_by_id_for_user(file_id, user):
    try:
        results = MyFile.objects.get(file_id=file_id)
        # check if the user has permissions for this file
        if not user.is_superuser:
            status_permission = 'sundog.' + results.current_status.get_permission_codename()
            if status_permission not in user.get_all_permissions():
                return "Unavailable"
            else:
                if not user.has_perm('sundog.view_all_files'):
                    if user not in results.participants.all():
                        return "Unavailable"
        save_access_file_history(file_id, user)
        return results
    except Exception as e:
        logger.error(messages.ERROR_GET_FILE % (file_id, user.username if user else "None user"))
        logger.error(e)
        return None


def create_access_file_history(file_id, user):
    try:
        FileAccessHistory.objects.create(file_id=file_id, user_id=user.id, time=datetime.now())

    except Exception as e:
        logger.error(messages.ERROR_SAVE_FILE_ACCESS_HISTORY % (file_id, user.username if user else "None user"))
        logger.error(e)


def create_file_permission(file):
    try:
        content_type = ContentType.objects.get(app_label=MyFile._meta.app_label, model=MyFile._meta.model_name)
        Permission.objects.create(codename=file.get_permission_codename(),
                                  name=file.get_permission_name(),
                                  content_type=content_type)
    except Exception as e:
        logger.error(messages.ERROR_CREATE_FILE_PERMISSION % file.file_id)
        logger.error(e)


def save_access_file_history(file_id, user):
    access_history = None
    try:
        access_history = FileAccessHistory.objects.get(file_id=file_id, user_id=user.id)
    except:
        create_access_file_history(file_id, user)
    if access_history:
        access_history.time = datetime.now()
        access_history.save()


def get_access_file_history(user):
    results = None
    try:
        if not user.is_superuser:
            # filter file for status permission
            permissions_name_array = get_user_status_permissions(user)
            if user.has_perm('sundog.view_all_files'):
                results = FileAccessHistory.objects.filter(user_id=user.id,
                                                           file__current_status__name__in=permissions_name_array)\
                                                   .order_by('-time')[:10]
            else:
                results = FileAccessHistory.objects.filter(user_id=user.id,
                                                           file__participants__id=user.id,
                                                           file__current_status__name__in=permissions_name_array)\
                                                   .order_by('-time')[:10]
        else:
            results = FileAccessHistory.objects.filter(user_id=user.id).order_by('-time')[:10]

    except Exception as e:
        if user is not None:
            logger.error(messages.ERROR_GET_FILE_ACCESS_HISTORY % user.username)
        else:
            logger.error(messages.ERROR_USER_NONE)
        logger.error(e)
    return results


def get_file_documents(file_id):
    results = None
    try:
        results = SundogDocument.objects.filter(file__file_id=file_id)

    except Exception as e:
        logger.error(messages.ERROR_GET_DOCUMENTS % file_id)
        logger.error(e)

    return results


def get_participants_options(file_id, current_status, current_participants):
    results = None
    try:

        perm = Permission.objects.get(codename=current_status.get_permission_codename())
        ids = list(map(lambda x: x.id, current_participants)) if current_participants else []
        results = User.objects.exclude(id__in=ids).filter(Q(groups__permissions=perm) | Q(user_permissions=perm) | Q(is_superuser=True)).distinct()

    except Exception as e:
        logger.error(messages.ERROR_GET_PARTICIPANT_OPTIONS % file_id)
        logger.error(e)

    return results


def get_participants_options_by_file(file, current_participants):
    results = None
    try:
        perm = Permission.objects.get(codename=file.get_permission_codename())
        ids = list(map(lambda x: x.id, current_participants)) if current_participants else []
        results = User.objects.exclude(id__in=ids).filter(Q(groups__permissions=perm) | Q(user_permissions=perm) | Q(is_superuser=True)).distinct()

    except Exception as e:
        logger.error(messages.ERROR_GET_PARTICIPANT_OPTIONS % file.file_id)
        logger.error(e)

    return results


def get_users_by_ids(ids):
    results = None
    try:
        results = User.objects.filter(id__in=ids)
    except Exception as e:
        logger.error(messages.ERROR_GET_USERS_BY_IDS % str(ids))
        logger.error(e)
    return results


def get_completed_by_file_status(status_id):
    result = 0
    try:
        status = FileStatus.objects.get(status_id=status_id)
        if status and status.related_percent:
            result = status.related_percent
    except Exception as e:
        logger.error(messages.ERROR_GET_COMPLETED_BY_STATUS % status_id)
        logger.error(e)
    return result


def check_client_type_exists(name):
    if name is None:
        return None
    name_key = 'client_type_' + name.lower().replace(" ", "_")
    value = cache.get(name_key)
    if value is not None:
        return value
    try:
        value = ClientType.objects.get(name=name).client_type_id
        cache.set(name_key, value, constants.CACHE_IMPORT_EXPIRATION)
    except Exception as e:
        logger.error(messages.CHECK_MODEL_EXISTS_IN_DB % ('client type', name))
        logger.error(e)
    return value


def check_client_exists(name, client_id):
    if name is None:
        return None
    name_key = 'client_' + name.lower().replace(" ", "_")
    value = cache.get(name_key)
    if value is not None and value == client_id:
        return None
    else:
        if value is not None:
            return value
        try:
            value = Contact.objects.get(name=name).client_id
            cache.set(name_key, value, constants.CACHE_IMPORT_EXPIRATION)
            if value == client_id:
                return None
            else:
                return value
        except Exception as e:
            logger.error(messages.CHECK_MODEL_EXISTS_IN_DB % ('client', name))
            logger.error(e)


def check_client_exists_by_identification(ident, client_id):
    if ident is None:
        return None
    ident_key = 'client_ident_' + ident.lower().replace(" ", "_")
    value = cache.get(ident_key)
    if value is not None and value == client_id:
        return None
    else:
        if value is not None:
            return value
        try:
            value = Contact.objects.get(identification=ident).client_id
            cache.set(ident_key, value, constants.CACHE_IMPORT_EXPIRATION)
            if value == client_id:
                return None
            else:
                return value
        except Exception as e:
            logger.error(messages.CHECK_MODEL_EXISTS_IN_DB % ('client', ident))
            logger.error(e)


def check_status_exists(status_name):
    if status_name is None:
        return None
    status_name_key = 'status_' + status_name.lower().replace(" ", "_")
    value = cache.get(status_name_key)
    if value is not None:
        return value
    try:
        value = FileStatus.objects.get(name=status_name).status_id
        cache.set(status_name_key, value, constants.CACHE_IMPORT_EXPIRATION)
    except Exception as e:
        logger.error(messages.CHECK_MODEL_EXISTS_IN_DB % ('status', status_name))
        logger.error(e)
    return value


def check_username_exists(username):
    if username is None:
        return None
    username_key = 'username_' + username.lower().replace(" ", "_")
    value = cache.get(username_key)
    if value is not None:
        return value
    try:
        value = User.objects.get(username=username)
        cache.set(username_key, value, constants.CACHE_IMPORT_EXPIRATION)
    except Exception as e:
        logger.error(messages.CHECK_MODEL_EXISTS_IN_DB % ('username', username))
        logger.error(e)
    return value


def check_tag_exists(tag_name):
    if tag_name is None:
        return None
    tag_name_key = 'tag_' + tag_name.lower().replace(" ", "_")
    value = cache.get(tag_name_key)
    if value is not None:
        return value
    try:
        value = Tag.objects.get(name=tag_name)
        cache.set(tag_name_key, value, constants.CACHE_IMPORT_EXPIRATION)
    except Exception as e:
        logger.error(messages.CHECK_MODEL_EXISTS_IN_DB % ('tag', tag_name))
        logger.error(e)
    return value


def upload_import_file(import_excel, user, impersonator_user=None):
    errors = []
    try:
        book = open_workbook(file_contents=import_excel.read())
        # get the first worksheet
        first_sheet = book.sheet_by_index(0)
        # validate headers
        num_cols = first_sheet.ncols
        headers = constants.IMPORT_FILE_EXCEL_HEADERS
        headers_len = len(headers)
        if num_cols != headers_len:
            errors.append(messages.ERROR_VALIDATE_NUMBER_HEADERS % (headers_len, num_cols))
        for column in range(0, len(headers)):
            try:
                file_cell = first_sheet.cell(0, column)
                if str(file_cell.value).upper().strip() == headers[column]:
                    continue
            except:
                pass
            errors.append(messages.ERROR_VALIDATE_IMPORT_HEADER % headers[column])
        # validate columns
        files = []
        default_status = get_default_status()
        if not default_status:
            errors.append(messages.ERROR_GET_IMPORT_DEFAULT_STATUS)
        if first_sheet.nrows < 2:
            errors.append(messages.ERROR_FILE_IMPORT_NO_ROWS)
        else:
            for row_idx in range(1, first_sheet.nrows):
                new_file = MyFile()
                # description column
                file_cell = first_sheet.cell(row_idx, 0)
                if file_cell.value:
                    new_file.description = str(file_cell.value).upper().strip()
                else:
                    errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_NOT_EMPTY % (row_idx, 'description'))
                # status column
                file_cell = first_sheet.cell(row_idx, 1)
                if file_cell.value:
                    status_id = check_status_exists(str(file_cell.value).upper().strip())
                    if not status_id:
                        status_id = default_status
                    new_file.current_status_id = status_id
                else:
                    errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_NOT_EMPTY % (row_idx, 'status'))
                # client column
                file_cell = first_sheet.cell(row_idx, 2)
                if file_cell.value:
                    client_id = check_client_exists(str(file_cell.value).upper().strip(), None)
                    if not client_id:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_EXISTS_DB % (row_idx, 'client'))
                    else:
                        new_file.client_id = client_id
                else:
                    errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_NOT_EMPTY % (row_idx, 'client'))
                # priority column
                file_cell = first_sheet.cell(row_idx, 3)
                if file_cell.value:
                    try:
                        priority = str(file_cell.value).strip().lower()
                        tuple_priority = [x[0] for x in constants.PRIORITY_CHOICES if x[1].lower() == priority]
                    except:
                        tuple_priority = None

                    if tuple_priority:
                        new_file.priority = tuple_priority[0]
                    else:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_EXISTS_DB % (row_idx, 'priority'))
                # quoted price column
                file_cell = first_sheet.cell(row_idx, 4)
                if file_cell.value:
                    try:
                        price = Decimal(file_cell.value)
                    except:
                        price = None
                    if price is not None and price >= 0:
                        new_file.quoted_price = price
                    else:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_VALID_TYPE % (row_idx, 'quoted price', 'number'))
                # quoted date column
                file_cell = first_sheet.cell(row_idx, 5)
                if file_cell.value:
                    try:
                        date_tuple = xldate_as_tuple(file_cell.value, book.datemode)
                        date = datetime(*date_tuple)
                    except Exception as e:
                        date = None
                    if date:
                        new_file.quoted_date = date
                    else:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_VALID_TYPE % (row_idx, 'quoted date', 'date'))
                # invoice price column
                file_cell = first_sheet.cell(row_idx, 6)
                if file_cell.value:
                    try:
                        price = Decimal(file_cell.value)
                    except:
                        price = None
                    if price is not None and price >= 0:
                        new_file.invoice_price = price
                    else:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_VALID_TYPE % (row_idx, 'invoice price', 'number'))
                # invoice date column
                file_cell = first_sheet.cell(row_idx, 7)
                if file_cell.value:
                    try:
                        date_tuple = xldate_as_tuple(file_cell.value, book.datemode)
                        date = datetime(*date_tuple)
                    except:
                        date = None
                    if date:
                        new_file.invoice_date = date
                    else:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_VALID_TYPE % (row_idx, 'invoice date', 'date'))
                # user columns
                for column in range(8, 10):
                    file_cell = first_sheet.cell(row_idx, column)
                    if file_cell.value:
                        user_name = check_username_exists(str(file_cell.value).strip().lower())
                        if user_name:
                            new_file.add_temp_users(user_name)
                        else:
                            errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_EXISTS_DB % (row_idx, 'participant'))
                # tag columns
                for column in range(10, 15):
                    file_cell = first_sheet.cell(row_idx, column)
                    if file_cell.value:
                        tag = check_tag_exists(str(file_cell.value).upper().strip())
                        if tag:
                            new_file.add_temp_tags(tag)
                        else:
                            errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_EXISTS_DB % (row_idx, 'tag'))
                files.append(new_file)
        # if no errors
        if not errors:
            # save import history
            save_import_history(import_excel, user, impersonator_user)
            # save to db
            for my_file in files:
                my_file.stamp_created_values(user)
                my_file.save()
                content_type = ContentType.objects.get(app_label=MyFile._meta.app_label, model=MyFile._meta.model_name)
                Permission.objects.create(codename=my_file.get_permission_codename(),
                                          name=my_file.get_permission_name(),
                                          content_type=content_type)
                file_status = FileStatusHistory()
                file_status.create_new_file_status_history(None, my_file.current_status, user, impersonator_user)
                my_file.file_status_history.add(file_status)
                if my_file.get_temp_tags():
                    my_file.tags.add(*my_file.get_temp_tags())
                if my_file.get_temp_users():
                    my_file.participants.add(*my_file.get_temp_users())
                my_file.save()
    except IndexError as ie:
        logger.error(messages.ERROR_IMPORT_FILE % user.username if user else "None user")
        logger.error(ie)
    except Exception as e:
        logger.error(messages.ERROR_IMPORT_FILE % user.username if user else "None user")
        logger.error(e)

        errors.append(e.args)
    return errors


def upload_import_client(import_excel, user, impersonator_user=None):
    errors = []
    try:
        book = open_workbook(file_contents=import_excel.read())
        # get the first worksheet
        first_sheet = book.sheet_by_index(0)
        # validate headers
        num_cols = first_sheet.ncols
        headers = constants.IMPORT_CLIENT_EXCEL_HEADERS
        headers_len = len(headers)
        if num_cols != headers_len:
            errors.append(messages.ERROR_VALIDATE_NUMBER_HEADERS % (headers_len, num_cols))
        for column in range(0, len(headers)):
            try:
                file_cell = first_sheet.cell(0, column)
                if str(file_cell.value).upper().strip() == headers[column]:
                    continue
            except:
                pass
            errors.append(messages.ERROR_VALIDATE_IMPORT_HEADER % headers[column])
        # validate columns
        clients = []
        if first_sheet.nrows < 2:
            errors.append(messages.ERROR_FILE_IMPORT_NO_ROWS)
        else:
            for row_idx in range(1, first_sheet.nrows):
                new_client = Contact()
                # client type column
                file_cell = first_sheet.cell(row_idx, 0)
                if file_cell.value:
                    client_type_id = check_client_type_exists(str(file_cell.value).upper().strip())
                    if not client_type_id:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_EXISTS_DB % (row_idx, 'client type'))
                    else:
                        new_client.client_type_id = client_type_id
                else:
                    errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_NOT_EMPTY % (row_idx, 'client type'))
                # client name column
                file_cell = first_sheet.cell(row_idx, 1)
                if file_cell.value:
                    cell_name = str(file_cell.value).upper().strip()
                    client_id = check_client_exists(cell_name, None)
                    if client_id or [x for x in clients if x.name == cell_name]:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_UNIQUE % (row_idx, 'client name'))
                    else:
                        new_client.first_name = cell_name
                else:
                    errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_NOT_EMPTY % (row_idx, 'client name'))
                # client identification column
                file_cell = first_sheet.cell(row_idx, 2)
                if file_cell.value:
                    cell_ident = str(file_cell.value).upper().strip()
                    client_ident = check_client_exists_by_identification(cell_ident, None)
                    if client_ident or [x for x in clients if x.identification == cell_ident]:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_UNIQUE % (row_idx, 'identification'))
                    else:
                        new_client.identification = cell_ident
                else:
                    errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_NOT_EMPTY % (row_idx, 'identification'))
                # email column
                file_cell = first_sheet.cell(row_idx, 3)
                if file_cell.value:
                    new_client.email = str(file_cell.value)
                # phone column
                file_cell = first_sheet.cell(row_idx, 4)
                if file_cell.value:
                    new_client.phone_number = str(file_cell.value)
                # mobile column
                file_cell = first_sheet.cell(row_idx, 5)
                if file_cell.value:
                    new_client.mobile_number = str(file_cell.value)
                # country column
                file_cell = first_sheet.cell(row_idx, 6)
                if file_cell.value:
                    new_client.country = str(file_cell.value)
                # state column
                file_cell = first_sheet.cell(row_idx, 7)
                if file_cell.value:
                    cell_state = str(file_cell.value).upper().strip()
                    state_tuple = [x[0] for x in US_STATES if x[0] == cell_state or x[1].upper() == cell_state]
                    if state_tuple:
                        new_client.state = state_tuple[0]
                    else:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_EXISTS_DB % (row_idx, 'state'))
                # city column
                file_cell = first_sheet.cell(row_idx, 8)
                if file_cell.value:
                    new_client.city = str(file_cell.value)
                # zip code column
                file_cell = first_sheet.cell(row_idx, 9)
                if file_cell.value:
                    new_client.zip_code = str(file_cell.value)
                # address column
                file_cell = first_sheet.cell(row_idx, 10)
                if file_cell.value:
                    new_client.address = str(file_cell.value)
                # related user column
                file_cell = first_sheet.cell(row_idx, 11)
                if file_cell.value:
                    user_name = check_username_exists(str(file_cell.value).strip().lower())
                    if user_name:
                        new_client.related_user = user_name
                    else:
                        errors.append(messages.ERROR_VALIDATE_IMPORT_CELL_EXISTS_DB % (row_idx, 'username'))
                clients.append(new_client)
        # if no errors
        if not errors:
            # save import history
            save_import_history(import_excel, user, impersonator_user)
            # save to db
            Contact.objects.bulk_create(clients)

    except IndexError as ie:
        logger.error(messages.ERROR_IMPORT_CLIENTS % user.username if user else "None user")
        logger.error(ie)
    except Exception as e:
        logger.error(messages.ERROR_IMPORT_CLIENTS % user.username if user else "None user")
        logger.error(e)
        errors.append(e.args)
    return errors


def save_import_history(import_excel, user, impersonator_user=None):
    try:
        dt_now = datetime.now()
        import_path = utils.import_file_path(import_excel.name, dt_now, user.id)
        checksum = utils.md5_for_file(import_excel.chunks())
        import_history = FileImportHistory(import_file_path=import_path, import_checksum=checksum, import_time=dt_now,
                                           impersonated_by=impersonator_user)
        import_history.user_full_name = user.get_full_name()
        import_history.user_username = user.username
        import_history.save()
        utils.save_import_file(import_excel, import_path)
    except Exception as e:
        logger.error(messages.ERROR_SAVE_FILE_IMPORT_HISTORY % user.username if user else "None user")
        logger.error(e)


def check_file_history_checksum(checksum):
    result = False
    try:
        FileImportHistory.objects.get(import_checksum=checksum)
        result = True
    except:
        pass
    return result


def get_files_by_status_count(user):
    result = None
    date_a_week_ago = datetime.now() - timedelta(days=7)
    try:
        result = FileStatusStat.objects.filter(date_stat__gt=date_a_week_ago).order_by("date_stat")
    except Exception as e:
        logger.error(messages.ERROR_SAVE_FILE_IMPORT_HISTORY % user.username if user else "None user")
        logger.error(e)
    return result
