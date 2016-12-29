from django.contrib.auth.models import User
from django.db.models import (
    DateTimeField,
    ForeignKey,
    Model,
    SET_NULL,
)
from settings import MEDIA_PRIVATE
from sundog.components.files.enums import (
    TYPE_CHOICES,
    TYPE_CHOICES_DICT,
)
from sundog.media import S3PrivateFileField
from sundog.util.models import LongCharField


def file_filename(instance, filename):
    return '{base}files/{identifier}/{filename}'.format(
        base=MEDIA_PRIVATE,
        identifier=instance.created_by.pk,
        filename=filename,
    )


class File(Model):

    created_at = DateTimeField(
        auto_now_add=True,
    )

    created_by = ForeignKey(
        to=User,
        on_delete=SET_NULL,
        blank=True,
        null=True,
    )

    TYPE_CHOICES = TYPE_CHOICES
    TYPE_CHOICES_DICT = TYPE_CHOICES_DICT
    type = LongCharField(
        choices=TYPE_CHOICES,
    )

    title = LongCharField()

    filename = LongCharField()

    content = S3PrivateFileField(
        upload_to=file_filename,
    )

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return self.content.url
