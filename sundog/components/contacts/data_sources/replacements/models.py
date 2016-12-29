from django.contrib.auth.models import User

from django.db.models import (
    CASCADE,
    DateTimeField,
    FloatField,
    ForeignKey,
    Model,
    SET_NULL,
)

from django.urls import reverse
from sundog.components.contacts.data_sources.fields.models import Field
from sundog.util.models import LongCharField


class Replacement(Model):

    created_at = DateTimeField(
        auto_now_add=True,
    )

    created_by = ForeignKey(
        to=User,
        on_delete=SET_NULL,
        blank=True,
        null=True,
    )

    field = ForeignKey(
        Field,
        on_delete=CASCADE,
        related_name='data_sources',
        unique=True,
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
        return self.name

    def get_absolute_url(self):
        return reverse(
            'contacts.data_sources.replacements.edit',
            args=[
                self.id,
            ]
        )
