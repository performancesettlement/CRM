from django.contrib.auth.models import User

from django.db.models import (
    CASCADE,
    DateTimeField,
    ForeignKey,
    Model,
    SET_NULL,
)

from django.urls import reverse

from sundog.components.contacts.data_sources.fields.enums import (
    FIELD_MAPS_TO_CHOICES,
)

from sundog.components.contacts.data_sources.models import DataSource
from sundog.util.models import LongCharField


class Field(Model):

    created_at = DateTimeField(
        auto_now_add=True,
    )

    created_by = ForeignKey(
        to=User,
        on_delete=SET_NULL,
        blank=True,
        null=True,
    )

    data_source = ForeignKey(
        to=DataSource,
        on_delete=CASCADE,
        related_name='fields',
    )

    name = LongCharField()

    MAPS_TO_CHOICES = FIELD_MAPS_TO_CHOICES
    MAPS_TO_CHOICES_DICT = dict(FIELD_MAPS_TO_CHOICES)
    maps_to = LongCharField(
        choices=MAPS_TO_CHOICES,
    )

    class Meta:
        get_latest_by = 'created_at'

        unique_together = (
            (
                'data_source',
                'maps_to',
            ),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            viewname='contacts.data_sources.fields.edit',
            kwargs={
                'data_source_id': self.data_source.pk,
                'pk': self.id,
            },
        )
