from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)

from django.db.models import (
    BooleanField,
    EmailField,
    IntegerField,
    Model,
)

from sundog.util.models import (
    DomainNameField,
    LongCharField,
    PasswordField,
)


class Sender(Model):

    name = LongCharField(unique=True)
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

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            'emarketing.senders.edit',
            args=[
                self.id,
            ]
        )

