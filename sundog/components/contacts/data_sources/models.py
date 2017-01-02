from django.contrib.auth.models import User

from django.db.models import (
    BooleanField,
    DateTimeField,
    ForeignKey,
    ManyToManyField,
    Model,
    SET_NULL,
)

from django.urls import reverse

from sundog.components.contacts.data_sources.enums import (
    DATA_SOURCE_FILE_TYPE_CHOICES,
    DATA_SOURCE_TYPE_CHOICES,
)

from sundog.components.emarketing.templates.models import EmailTemplate

from sundog.models import (
    Campaign,
    Company,
    DEBT_SETTLEMENT,
    Stage,
)

from sundog.util.models import LongCharField


class DataSource(Model):

    created_at = DateTimeField(
        auto_now_add=True,
    )

    created_by = ForeignKey(
        to=User,
        on_delete=SET_NULL,
        related_name='created_data_sources',
        blank=True,
        null=True,
    )

    name = LongCharField(
        unique=True,
    )

    TYPE_CHOICES = DATA_SOURCE_TYPE_CHOICES
    TYPE_CHOICES_DICT = dict(DATA_SOURCE_TYPE_CHOICES)
    type = LongCharField(
        choices=TYPE_CHOICES,
    )

    FILE_TYPE_CHOICES = DATA_SOURCE_FILE_TYPE_CHOICES
    FILE_TYPE_CHOICES_DICT = dict(DATA_SOURCE_FILE_TYPE_CHOICES)
    file_type = LongCharField(
        choices=FILE_TYPE_CHOICES,
        default=DEBT_SETTLEMENT,
    )

    status = ForeignKey(
        Stage,
        related_name='data_sources',
        blank=True,
        null=True,
    )

    campaign = ForeignKey(
        Campaign,
        related_name='data_sources',
        blank=True,
        null=True,
    )

    enabled = BooleanField(default=True)
    public = BooleanField(default=False)
    assigned_to = ManyToManyField(
        User,
        related_name='assigned_data_sources',
    )

    notification = ForeignKey(
        EmailTemplate,
        related_name='data_sources_notification',
        blank=True,
        null=True,
    )

    # Company assignment:
    for field in '''
        company
        marketing_company
        servicing_company
        law_firm
        lead_vendor
        partner
    '''.split():
        vars()[field] = ForeignKey(
            Company,
            related_name='data_sources_' + field,
            blank=True,
            null=True,
        )
    del field

    # Role assignment:
    for field in '''
        negotiator
        sales_manager
        client_services_representative
        sales
        processor
        sales_lns
        supervisor
        attorney
        lendstreet
        manager
        abe
    '''.split():
        vars()[field] = ForeignKey(
            User,
            related_name='data_sources_' + field,
            blank=True,
            null=True,
        )
    del field

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            viewname='contacts.data_sources.edit',
            kwargs={
                'pk': self.id,
            },
        )
