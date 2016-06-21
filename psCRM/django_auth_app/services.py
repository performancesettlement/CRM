__author__ = 'Gaby'
from models import UserProfile
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
import logging
import messages
import hashlib
import random
import datetime

#initialize logger
logger = logging.getLogger(__name__)


def get_user_profile(user_id):

    try:
        result = UserProfile.objects.get(related_user__id=user_id)
        return result
    except Exception, e:
        logger.info(messages.ERROR_GET_PROFILE % user_id)
        #create the user if it does not exists
        try:
            user = get_user(user_id)
            user_profile = UserProfile()
            user_profile.first_name = user.first_name
            user_profile.last_name = user.last_name
            user_profile.related_user = user
            user_profile.save()
            return user_profile

        except Exception, e:
            logger.error(messages.ERROR_CREATE_PROFILE % user_id)
            logger.error(e)
            return None


def get_user(user_id):
    result = None
    try:
        result = User.objects.get(id=user_id)

    except Exception, e:
        logger.error(messages.ERROR_GET_USER % user_id)
        logger.error(e)

    return result


def update_user_password(user_profile, password):
    try:
        #update password
        user = user_profile.related_user
        password = password
        user.password = make_password(password, salt=None, hasher='default')
        user.is_active = True
        user.save()

        #erase recover key info
        user_profile.recover_key = None
        user_profile.recover_key_expires = None
        user_profile.save()

    except Exception, e:
        logger.error(messages.ERROR_UPDATE_PASSWORD % user_profile.related_user.id
                     if user_profile and hasattr(user_profile, 'related_user') and user_profile.related_user.id else "Unknown")
        logger.error(e)


def set_user_recover_key(user):
    try:
        #generate a recover token
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        recover_key = hashlib.sha1(salt + user.email).hexdigest()
        recover_key_expires = datetime.datetime.today() + datetime.timedelta(2)

        #set the recover information
        profile = get_user_profile(user.id)

        profile.recover_key = recover_key
        profile.recover_key_expires = recover_key_expires
        profile.save()

        return recover_key
    except Exception, e:
        logger.error(messages.ERROR_GET_RECOVER_KEY % user.id)
        logger.error(e)
        return None


def get_user_timezone(user_id):
    tz = None
    try:
        user_profile = get_user_profile(user_id)
        tz = user_profile.timezone
    except:
        pass
    return tz


def set_user_timezone(timezone, user_id):
    try:
        user_profile = get_user_profile(user_id)
        user_profile.timezone = timezone
        user_profile.save()
    except Exception, e:
        logger.error(messages.ERROR_SET_USER_TIMEZONE % user_id)
        logger.error(e)


def create_customer_group(user):
    try:
        group = Group.objects.create(name='Customer')

    except Exception, e:
        logger.error(messages.ERROR_CREATE_CUSTOMER_GROUP % user.username)
        logger.error(e)
        return None
    # TODO: add default permissions to group customer
    return group


def set_customer_group_to_user(user):
    try:
        group = Group.objects.get(name='Customer')
    except:
        group = create_customer_group(user)

    if group:
        try:
            group.user_set.add(user)
            group.save()
        except Exception, e:
            logger.error(messages.ERROR_ADD_CUSTOMER_GROUP % user.username)
            logger.error(e)

