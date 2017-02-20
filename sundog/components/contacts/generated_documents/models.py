from django.contrib.auth.models import User

from django.db.models import (
    CASCADE,
    DateTimeField,
    ForeignKey,
    SET_NULL,
)

from settings import MEDIA_PRIVATE
from sundog.components.documents.render import render
from sundog.components.documents.models import Document
from sundog.media import S3PrivateFileField
from sundog.models import (
    Contact,
    TrackedAbstractBase,
)
from sundog.util.models import LongCharField


def generated_document_filename(instance, filename):
    return (
        f'{MEDIA_PRIVATE}'
        f'generated_documents'
        f'/{instance.contact.contact_id}'
        f'/{filename}'
    )


class GeneratedDocument(TrackedAbstractBase):

    created_at = DateTimeField(
        auto_now_add=True,
    )

    created_by = ForeignKey(
        to=User,
        blank=True,
        null=True,
        on_delete=SET_NULL,
        related_name='generated_documents',
    )

    contact = ForeignKey(
        to=Contact,
        on_delete=CASCADE,
        related_name='generated_documents',
    )

    title = LongCharField()

    content = S3PrivateFileField(
        upload_to=generated_document_filename,
    )

    template = ForeignKey(
        to=Document,
        blank=True,
        null=True,
        on_delete=SET_NULL,
        related_name='generated_documents',
    )

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return self.content.url
