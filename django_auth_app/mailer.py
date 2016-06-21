import settings
from django.core.mail import send_mail
from django.core.mail.message import EmailMessage
from django.template.context import Context
from django.template.loader import get_template

"""
def send_activation_email(email,username,activation_key):
    
    email_subject = 'Account confirmation'
    email_body = "Hey %s, thanks for signing up. To activate your account, click this link within \
    48 hours %ssite/accounts/confirm/%s/" % (username, settings.SITE_DOMAIN, activation_key)

    send_mail(email_subject, email_body, settings.NO_REPLY_EMAIL_ADDRESS,
        [email], fail_silently=False)
"""
"""
def send_recover_email(email,username,recover_key):

    email_subject = 'Recover password'
    email_body = "Hey %s, to recover your account, click this link within \
    48 hours %ssite/accounts/new_password/%s/" % (username, settings.SITE_DOMAIN, recover_key)

    send_mail(email_subject, email_body, settings.NO_REPLY_EMAIL_ADDRESS,
        [email], fail_silently=False)
"""

def send_template_email(subject, template_name, template_dict, to_email_list, from_email=settings.NO_REPLY_EMAIL_ADDRESS, attachments=[]):
    template = get_template(template_name)
    context = Context(template_dict)
    email = EmailMessage(subject, template.render(context), from_email, to_email_list)
    for attachment in attachments:
        email.attach_file(attachment)
    email.content_subtype = 'html'
    email.send()
