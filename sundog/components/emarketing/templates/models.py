from django.contrib.auth.models import User

from django.db.models import (
    DateTimeField,
    ForeignKey,
    Model,
    SET_NULL,
    TextField,
)

from django.urls import reverse

from sundog.components.emarketing.templates.enums import CATEGORY_CHOICES

from sundog.util.models import (
    LongCharField,
)

from tinymce.models import HTMLField


class EmailTemplate(Model):

    CATEGORY_CHOICES = CATEGORY_CHOICES
    CATEGORY_CHOICES_DICT = dict(CATEGORY_CHOICES)

    created_at = DateTimeField(
        auto_now_add=True,
    )

    created_by = ForeignKey(
        to=User,
        on_delete=SET_NULL,
        blank=True,
        null=True,
    )

    campaign_title = LongCharField(
        unique=True,
    )

    email_subject = LongCharField()

    category = LongCharField(
        choices=CATEGORY_CHOICES,
    )

    html_template = HTMLField()

    text_template = TextField(
        blank=True,
        null=True,
    )

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.campaign_title

    def get_absolute_url(self):
        return reverse(
            viewname='emarketing.templates.edit',
            kwargs={
                'pk': self.id,
            },
        )
