from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    DateTimeField,
    ForeignKey,
    Model,
    SET_NULL,
)
from django.urls import reverse
from multiselectfield import MultiSelectField
from settings import MEDIA_PRIVATE
from sundog.components.documents.context_resolver import render
from sundog.components.documents.enums import (
    TYPE_CHOICES,
    TYPE_CHOICES_DICT,
    STATE_CHOICES,
    STATE_CHOICES_DICT,
)
from sundog.media import S3PrivateFileField
from sundog.models import Contact
from sundog.util.models import LongCharField
from tinymce.models import HTMLField


class Document(Model):

    TYPE_CHOICES = TYPE_CHOICES
    TYPE_CHOICES_DICT = TYPE_CHOICES_DICT
    STATE_CHOICES = STATE_CHOICES
    STATE_CHOICES_DICT = STATE_CHOICES_DICT

    title = LongCharField()
    created_at = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(to=User, on_delete=SET_NULL, blank=True, null=True)
    type = LongCharField(choices=TYPE_CHOICES)

    # FIXME: Work around stupid arbitrary length limits with a very large stupid
    # arbitrary length limit.  A proper fix would require a modified form of the
    # MultiSelectField class based on LongCharField, which could be accomplished
    # easily by forking the django-multiselectfield project and having it depend
    # on a new small package holding the LongCharField definition.
    state = MultiSelectField(choices=STATE_CHOICES, max_length=2**20)

    template_body = HTMLField()

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'documents.edit',
            args=[
                self.id,
            ]
        )

    def render(
        self,
        context={},
    ):
        return render(
            template=self.template_body,
            context=context,
        )


def generated_document_filename(instance, filename):
    return '{base}generated_documents/{identifier}/{filename}'.format(
        base=MEDIA_PRIVATE,
        identifier=instance.contact.contact_id,
        filename=filename,
    )


class GeneratedDocument(Model):
    contact = ForeignKey(
        to=Contact,
        on_delete=CASCADE,
        related_name='generated_documents',
    )
    title = LongCharField()
    content = S3PrivateFileField(upload_to=generated_document_filename)
    created_at = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(
        to=User,
        blank=True,
        null=True,
        on_delete=SET_NULL,
        related_name='generated_documents',
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

    def get_absolute_url(self):
        return self.content.url

    def render(
        self,
        context={},
    ):
        return render(
            template=self.template.template_body,
            context={
                'contact': self.contact,
                **context,
            },
        )
