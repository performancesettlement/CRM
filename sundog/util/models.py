from django.db.models import CharField
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms import URLField as URLFormField
from django.utils.translation import ugettext as _
from sundog.util.forms import validate_domain_name, validate_url


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

    # Restore method removed in https://github.com/django/django/pull/5093/commits/770449e24b3b0fa60d870bc3404961ddca754c3b  # noqa
    def get_flatchoices(
        self,
        include_blank=True,
        blank_choice=BLANK_CHOICE_DASH,
    ):
        """
        Returns flattened choices with a default blank choice included.
        """
        first_choice = blank_choice if include_blank else []
        return first_choice + list(self.flatchoices)


class URLField(LongCharField):
    default_validators = [validate_url]
    description = _("URL")

    def formfield(self, **kwargs):
        # As with CharField, this will cause URL validation to be performed
        # twice.
        defaults = {
            'form_class': URLFormField,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


class DomainNameField(LongCharField):
    default_validators = [validate_domain_name]
