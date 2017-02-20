from django.contrib.auth.models import User

from django.db.models import (
    BooleanField,
    DateTimeField,
    ForeignKey,
    ManyToManyField,
    SET_NULL,
    UUIDField,
)

from django.urls import reverse
from random import choice

from sundog.components.contacts.data_sources.enums import (
    DATA_SOURCE_FILE_TYPE_CHOICES,
    DATA_SOURCE_TYPE_CHOICES,
)

from sundog.components.emarketing.templates.models import EmailTemplate

from sundog.models import (
    Campaign,
    Company,
    Contact,
    DEBT_SETTLEMENT,
    Stage,
    TrackedAbstractBase,
)

from sundog.util.models import LongCharField
from uuid import uuid4


class DataSource(TrackedAbstractBase):

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
        to=Stage,
        related_name='data_sources',
        blank=True,
        null=True,
    )

    campaign = ForeignKey(
        to=Campaign,
        related_name='data_sources',
        blank=True,
        null=True,
    )

    assignment_enabled = BooleanField(default=True)
    public = BooleanField(default=False)

    assigned_to = ManyToManyField(
        User,
        related_name='assigned_data_sources',
    )

    notification = ForeignKey(
        to=EmailTemplate,
        related_name='data_sources_notification',
        blank=True,
        null=True,
    )

    key = UUIDField(
        default=uuid4,
        editable=False,
    )

    username = LongCharField(
        blank=True,
        null=True,
    )

    password = LongCharField(
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
            to=Company,
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
            to=User,
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

    def post_url(self):
        return reverse(
            viewname='contacts.data_sources.post',
            kwargs={
                'pk': self.id,
                'key': self.key.hex,
            },
        )

    def import_contact(self, data):
        # FIXME: this works even if the request is missing form fields

        contact = Contact(
            **{
                field.maps_to: value
                for field in self.fields.all()
                for value in [data.get(field.name)]
                if value
            },
        )

        if self.assignment_enabled:
            choices = self.assigned_to.all()
            if choices:
                contact.assigned_to = choice(choices)

            for field in '''
                company
                marketing_company
                servicing_company
                law_firm
                lead_vendor
                partner
            '''.split():
                assigned_company = getattr(self, field, None)
                if assigned_company:
                    setattr(contact, field, assigned_company)

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
                assigned_user = getattr(self, field, None)
                if assigned_user:
                    setattr(contact, field, assigned_user)

        contact.save()
