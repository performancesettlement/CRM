from datetime import date
from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    DateTimeField,
    ForeignKey,
    Model,
    SET_NULL,
)
from django.urls import reverse
from django.utils.dateformat import format
from django_auth_app.enums import US_STATES
from multiselectfield import MultiSelectField
from pystache import render
from settings import MEDIA_PRIVATE
from sundog.components.documents.enums import (
    TYPE_CHOICES,
    TYPE_CHOICES_DICT,
    STATE_CHOICES,
    STATE_CHOICES_DICT,
)
from sundog.media import S3PrivateFileField
from sundog.models import ACCOUNT_TYPE_CHOICES, Contact
from sundog.utils import LongCharField
from sundog.utils import (
    catching,
    const,
    get_enum_name,
)
from tinymce.models import HTMLField
from weasyprint import HTML


def contact_context(contact):

    # Default to empty string if computation throws
    def d(computation):
        return catching(
            computation=computation,
            exception=Exception,
            catcher=const(''),
        )

    def applicant_information(prefix='', attribute_prefix=''):
        def get_attribute(attribute):
            return getattr(
                contact,
                attribute_prefix + attribute,
                '',
            )

        def phone_parts(prefix, number):
            return {
                prefix + 'PHONE_AREA': d(lambda: number[0:3]),
                prefix + 'PHONE_PRE': d(lambda: number[3:6]),
                prefix + 'PHONE_SUFF': d(lambda: number[6:]),
            }

        return {
            prefix + key: value
            for key, value in {
                'FIRSTNAME': get_attribute('first_name'),
                'LASTNAME': get_attribute('last_name'),
                'MIDDLENAME': get_attribute('middle_name'),
                'FULLNAME': '{first_name} {last_name}'.format(
                    first_name=get_attribute('first_name'),
                    last_name=get_attribute('last_name'),
                ),
                'PHONE': get_attribute('phone_number'),
                'PHONE2': get_attribute('work_phone'),
                'PHONE3': get_attribute('mobile_number'),
                **phone_parts('HOME', get_attribute('phone_number')),
                **phone_parts('WORK', get_attribute('work_phone')),
                **phone_parts('CELL', get_attribute('mobile_number')),
                'EMAIL': get_attribute('email'),
                # 'FAX': ,  # TODO: Fax
                'ADDRESS': get_attribute('address_1'),
                'ADDRESS2': get_attribute('address_2'),
                'CITY': get_attribute('city'),
                'STATE': get_attribute('state'),
                'STATEFULL': get_enum_name(
                    code=get_attribute('state'),
                    names=US_STATES,
                ),
                'ZIP': get_attribute('zip_code'),
                'FULLADDRESS': (
                    '{address_1}, {address_2}, {city} {state} {zip_code}'
                    .format(
                        address_1=get_attribute('address_1'),
                        address_2=get_attribute('address_2'),
                        city=get_attribute('city'),
                        state=get_attribute('state'),
                        zip_code=get_attribute('zip_code'),
                    )
                ),
                'SSN': contact.identification,
                # 'ENCSSN': ,  # TODO: Contact's Encrypted Social Security Number  # noqa
                **{
                    'SSN' + str(n + 1):
                        d(
                            lambda:
                            get_attribute('identification')
                            .replace('-', '')
                            [n]
                        )
                    for n in range(0, 9)
                },
                'DOB': format(get_attribute('birth_date'), 'm/d/Y'),
            }.items()
        }

    today = date.today()

    return {
        # Contact identification:
        'ID': contact.pk,
        'CUSTOMERID': contact.pk,

        # Applicant and co-applicant information:
        **applicant_information(),
        **applicant_information(prefix='CO', attribute_prefix='co_applicant_'),

        # Bank account information:
        'NAMEONACCT': d(lambda: contact.bank_account.name_on_account),
        'BANKNAME': d(lambda: contact.bank_account.bank_name),
        'BANKADDRESS': d(lambda: contact.bank_account.address),
        'BANKCITY': d(lambda: contact.bank_account.city),
        'BANKSTATE': d(lambda: contact.bank_account.state),
        'BANKZIP': d(lambda: contact.bank_account.zip_code),
        'BANKPHONE': d(lambda: contact.bank_account.phone),
        'ACCTTYPE': d(
            lambda: get_enum_name(
                code=contact.bank_account.account_type,
                names=ACCOUNT_TYPE_CHOICES,
            )
        ),
        'ACCOUNTNUM': d(lambda: contact.bank_account.account_number),
        'ROUTINGNUM': d(lambda: contact.bank_account.routing_number),
        # 'ACCOUNTNUM_ENC': d(lambda: contact.bank_account.account_number),  # TODO: Encrypted Account Number  # noqa
        # 'ROUTINGNUM_ENC': d(lambda: contact.bank_account.routing_number),  # TODO: Encrypted Routing Number  # noqa

        # General purpose tags:
        'FILETYPE': 'Debt Settlement',
        # 'LASTNOTE': contact.,  # TODO: Populates the last note made on the Client Dashboard  # noqa
        # 'ALLNOTES': contact.,  # TODO: Populates the all notes made on the Client Dashboard  # noqa
        # 'ALLHISTORY': contact.,  # TODO: Populates a table with the History Notes from the Client Dashboard  # noqa
        'DATE': format(today, 'M m, Y'),
        'MONTH': format(today, 'F'),
        'DAY': format(today, 'jS'),
        'YEAR': format(today, 'Y'),
        # 'URL': contact.url,  # TODO: Web Address (will be hyperlinked on Client Dashboard)  # noqa
        # 'COMMENTS': contact.,  # TODO: Populates information saved on the system field "Comments"  # noqa
        # 'CONTACT_STATUS': contact.,  # TODO: Workflow Status
        # 'CONTACT_STAGE': contact.,  # TODO: Workflow Stage
        # 'ENROLLED_DATE': contact.,  # TODO: Date the client was Enrolled
        # 'GRADUATED_DATE': contact.,  # TODO: Date Client was Graduated
        'CREATED_DATE': format(contact.created_at, 'M m, Y'),
        # 'CAMPAIGN': contact.,  # TODO: Campaign Contact is Assigned To
        # 'DATASOURCE': contact.,  # TODO: Data Source Contact Was Created From  # noqa
        # 'GATEWAY_ID': contact.,  # TODO: Payment Gateway ID Number from Enrollment Details  # noqa
        # 'COMPANYLOGO': contact.,  # TODO: Populates the logo for the company  # noqa
    }


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
        return HTML(
            string=render(
                template=self.template_body,
                context={
                    **contact_context(context['contact']),
                    **context,
                },
            ),
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

    def get_absolute_url(self):
        return self.content.url

    def render(
        self,
        context={},
    ):
        return HTML(
            string=render(
                template=self.template.template_body,
                context={
                    **contact_context(self.contact),
                    **context,
                },
            ),
        )
