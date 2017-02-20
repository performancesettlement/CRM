from django.contrib.auth.models import User

from django.db.models import (
    CASCADE,
    DateTimeField,
    FloatField,
    ForeignKey,
    OneToOneField,
    SET_NULL,
)

from django.urls import reverse
from sundog.components.contacts.data_sources.fields.models import Field
from sundog.models import TrackedAbstractBase
from sundog.util.models import LongCharField


class Replacement(TrackedAbstractBase):

    created_at = DateTimeField(
        auto_now_add=True,
    )

    created_by = ForeignKey(
        to=User,
        on_delete=SET_NULL,
        blank=True,
        null=True,
    )

    field = OneToOneField(
        to=Field,
        related_name='replacement',
        on_delete=CASCADE,
    )

    min_value = FloatField(
        blank=True,
        null=True,
    )

    max_value = FloatField(
        blank=True,
        null=True,
    )

    replace_value = LongCharField(
        blank=True,
        null=True,
    )

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return f'{self.field} replacement'

    def get_absolute_url(self):
        return reverse(
            viewname='contacts.data_sources.replacements.edit',
            kwargs={
                'data_source_id': self.field.data_source.pk,
                'pk': self.id,
            }
        )
