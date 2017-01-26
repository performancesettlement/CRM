from django.core.validators import (
    _lazy_re_compile,
    RegexValidator,
    URLValidator,
)

from django.forms import CharField, PasswordInput
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext as _
from re import IGNORECASE


validate_url = URLValidator()


# This will hopefully be merged into Django at some point; see the pull request
# at https://github.com/django/django/pull/7300
@deconstructible
class DomainNameValidator(RegexValidator):
    message = _('Enter a valid domain name value.')
    regex = _lazy_re_compile(
        r'(?:' +
        URLValidator.ipv4_re + '|' +
        URLValidator.ipv6_re + '|' +
        URLValidator.host_re + ')',
        IGNORECASE
    )


validate_domain_name = DomainNameValidator()


class PasswordField(CharField):
    widget = PasswordInput
