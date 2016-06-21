import settings
from django.core.mail import send_mail


def send_activation_email(email,username,activation_key):
    print "%saccounts/confirm/%s/" % (settings.SITE_DOMAIN, activation_key)

def send_recover_email(email,username,recover_key):
    print "%saccounts/new_password/%s/" % (settings.SITE_DOMAIN, recover_key)