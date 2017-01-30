from django.contrib.auth.models import User, Permission
from django.core.cache import cache
from django.db import transaction
import logging
from sundog import constants, messages
from sundog.models import Contact, Stage, Status


logger = logging.getLogger(__name__)


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
    statuses = {
        x.status_id: x
        for x in (
            Status
            .objects
            .filter(
                stage__stage_id=stage_id,
            )
        )
    }
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
        all_status_perms = (
            Permission
            .objects
            .filter(
                codename__in=[
                    x.split('.')[1]
                    for x in all_user_perms
                    if x.startswith(permission_prefix)
                ],
            )
        )
        return [
            status.name.replace(status_name_prefix, '').upper()
            for status in list(all_status_perms)
        ]
    except Exception as e:
        if user is not None:
            logger.error(messages.ERROR_GET_STATUS_PERMISSIONS % user.username)
        else:
            logger.error(messages.ERROR_USER_NONE)
        logger.error(e)
        return None


def get_stages_by_type(type):
    return Stage.objects.filter(stage__type=type)


def get_users_by_ids(ids):
    results = None
    try:
        results = User.objects.filter(id__in=ids)
    except Exception as e:
        logger.error(messages.ERROR_GET_USERS_BY_IDS % str(ids))
        logger.error(e)
    return results


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
