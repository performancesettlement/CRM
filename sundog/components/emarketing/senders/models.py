from django.contrib.auth.models import User

from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)

from django.db.models import (
    BooleanField,
    DateTimeField,
    EmailField,
    ForeignKey,
    IntegerField,
    SET_NULL,
)

from django.urls import reverse
from sundog.models import TrackedAbstractBase
from sundog.util.models import (
    DomainNameField,
    LongCharField,
    PasswordField,
)


class Sender(TrackedAbstractBase):

    created_at = DateTimeField(
        auto_now_add=True,
    )

    created_by = ForeignKey(
        to=User,
        on_delete=SET_NULL,
        blank=True,
        null=True,
    )

    name = LongCharField(
        unique=True,
    )

    sender_address = EmailField()
    reply_address = EmailField()
    bounce_address = EmailField()

    smtp_server = DomainNameField(
        verbose_name='SMTP server',
    )

    smtp_port = IntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(65535),
        ],
        blank=True,
        null=True,
        verbose_name='SMTP port',
    )

    smtp_username = LongCharField(
        blank=True,
        null=True,
        verbose_name='SMTP username',
    )

    smtp_password = PasswordField(
        blank=True,
        null=True,
        verbose_name='SMTP password',
    )

    smtp_require_tls = BooleanField(
        default=False,
        verbose_name='require SSL/TLS for SMTP',
    )

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            viewname='emarketing.senders.edit',
            kwargs={
                'pk': self.id,
            },
        )
