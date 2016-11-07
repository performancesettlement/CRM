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

    def phone_parts(prefix, number):
        return {
            prefix + 'PHONE_AREA': d(lambda: number[0:2]),
            prefix + 'PHONE_PRE': d(lambda: number[3:5]),
            prefix + 'PHONE_SUFF': d(lambda: number[6:]),
        }

    today = date.today()

    return {
        # Contact identification:
        'ID': contact.pk,
        'CUSTOMERID': contact.pk,

        # Applicant information:
        'FIRSTNAME': contact.first_name,
        'LASTNAME': contact.last_name,
        'MIDDLENAME': contact.middle_name,
        'FULLNAME': '{first_name} {last_name}'.format(
            first_name=contact.first_name or '',
            last_name=contact.last_name or '',
        ),
        'PHONE': contact.phone_number,
        'PHONE2': contact.work_phone,
        'PHONE3': contact.mobile_number,
        **phone_parts('HOME', contact.phone_number),
        **phone_parts('WORK', contact.work_phone),
        **phone_parts('CELL', contact.mobile_number),
        'EMAIL': contact.email,
        # 'FAX': ,  # TODO: Fax
        'ADDRESS': contact.address_1,
        'ADDRESS2': contact.address_2,
        'CITY': contact.city,
        'STATE': contact.state,
        'STATEFULL': get_enum_name(
            code=contact.state,
            names=US_STATES,
        ),
        'ZIP': contact.zip_code,
        'FULLADDRESS': (
            '{address_1}, {address_2}, {city} {state} {zip_code}'.format(
                address_1=contact.address_1 or '',
                address_2=contact.address_2 or '',
                city=contact.city or '',
                state=contact.state or '',
                zip_code=contact.zip_code or '',
            )
        ),
        'SSN': contact.identification,
        # 'ENCSSN': ,  # TODO: Contact's Encrypted Social Security Number
        **{
            'SSN' + str(n):
                d(lambda: contact.identification[n])
            for n in range(1, 10)
        },
        'DOB': str(contact.birth_date),

        # Co-applicant information:
        'COFIRSTNAME': contact.co_applicant_first_name,
        'COLASTNAME': contact.co_applicant_last_name,
        'COMIDDLENAME': contact.co_applicant_middle_name,
        'COFULLNAME': '{first_name} {last_name}'.format(
            first_name=contact.co_applicant_first_name,
            last_name=contact.co_applicant_last_name,
        ),
        'COPHONE': contact.co_applicant_phone_number,
        'COPHONE2': contact.co_applicant_work_phone,
        'COPHONE3': contact.co_applicant_mobile_number,
        **phone_parts('COHOME', contact.co_applicant_phone_number),
        **phone_parts('COWORK', contact.co_applicant_work_phone),
        **phone_parts('COCELL', contact.co_applicant_mobile_number),
        'COEMAIL': contact.co_applicant_email,
        # 'COFAX': ,  # TODO: Fax
        'COADDRESS': contact.co_applicant_address_1,
        'COADDRESS2': contact.co_applicant_address_2,
        'COCITY': contact.co_applicant_city,
        'COSTATE': contact.co_applicant_state,
        'COSTATEFULL': get_enum_name(
            code=contact.co_applicant_state,
            names=US_STATES,
        ),
        'COZIP': contact.co_applicant_zip_code,
        'COFULLADDRESS': (
            '{address_1}, {address_2}, {city} {state} {zip_code}'.format(
                address_1=contact.co_applicant_address_1,
                address_2=contact.co_applicant_address_2,
                city=contact.co_applicant_city,
                state=contact.co_applicant_state,
                zip_code=contact.co_applicant_zip_code,
            )
        ),
        'COSSN': contact.co_applicant_identification,
        # 'COENCSSN': ,  # TODO: Contact's Encrypted Social Security Number
        **{
            'COSSN' + str(n):
                d(lambda: contact.co_applicant_identification[n])
            for n in range(1, 10)
        },
        'CODOB': str(contact.co_applicant_birth_date),

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
        contact,
        context={},
    ):
        return HTML(
            string=render(
                template=self.template_body,
                context={
                    **contact_context(contact),
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
        document,
        contact,
        context={},
    ):
        return HTML(
            string=render(
                template=document.template_body,
                context={
                    **contact_context(self.contact),
                    **context,
                },
            ),
        )
