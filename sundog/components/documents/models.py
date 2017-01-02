from django.contrib.auth.models import User

from django.db.models import (
    DateTimeField,
    ForeignKey,
    Model,
    SET_NULL,
)

from django.urls import reverse
from multiselectfield import MultiSelectField

from sundog.components.documents.enums import (
    DOCUMENT_TYPE_CHOICES,
    DOCUMENT_STATE_CHOICES,
)

from sundog.util.models import LongCharField
from tinymce.models import HTMLField


class Document(Model):

    created_at = DateTimeField(
        auto_now_add=True,
    )

    created_by = ForeignKey(
        to=User,
        on_delete=SET_NULL,
        blank=True,
        null=True,
    )

    title = LongCharField()

    TYPE_CHOICES = DOCUMENT_TYPE_CHOICES
    TYPE_CHOICES_DICT = dict(DOCUMENT_TYPE_CHOICES)
    type = LongCharField(
        choices=TYPE_CHOICES,
    )

    STATE_CHOICES = DOCUMENT_STATE_CHOICES
    STATE_CHOICES_DICT = {
        key: value
        for group, choices in DOCUMENT_STATE_CHOICES
        for key, value in choices
    }
    state = MultiSelectField(
        choices=STATE_CHOICES,
        # FIXME: Work around stupid arbitrary length limits with a very large
        # stupid arbitrary length limit.  A proper fix would require a modified
        # form of the MultiSelectField class based on LongCharField, which could
        # be accomplished easily by forking the django-multiselectfield project
        # and having it depend on a new small package holding the LongCharField
        # definition.
        max_length=2**20,
    )

    template_body = HTMLField()

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            viewname='documents.edit',
            kwargs={
                'pk': self.id,
            },
        )
