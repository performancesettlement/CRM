from datetime import date
from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    DateTimeField,
    ForeignKey,
    Model,
    SET_NULL,
    Sum,
)
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.dateformat import format
from django_auth_app.enums import US_STATES
from multiselectfield import MultiSelectField
from pystache.defaults import TAG_ESCAPE
from pystache.renderengine import context_get
from pystache.renderer import Renderer
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
    defaulting,
    get_enum_name,
)
from tinymce.models import HTMLField
from weasyprint import HTML


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


class RenderRaw:
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


def render(template, context):
    return HTML(
        string=(
            DocumentRenderer(
                escape=lambda s:
                    s.text
                    if isinstance(s, RenderRaw)
                    else TAG_ESCAPE(s)
            )
            .render(
                template=template,
                **context,
            )
        ),
    )


class DocumentRenderer(Renderer):

    def _escape_to_unicode(self, s):
        return (
            s.text
            if isinstance(s, RenderRaw)
            else super()._escape_to_unicode(s)
        )

    def _to_unicode_soft(self, s):
        return (
            s
            if isinstance(s, RenderRaw)
            else super()._to_unicode_soft(s)
        )

    def str_coerce(self, s):
        return (
            s
            if isinstance(s, RenderRaw)
            else super().str_coerce(s)
        )

    def _make_resolve_context(self):
        contact = None
        tags = None

        today = date.today()

        # Thunk for computation returning default value on evaluation exception:
        def d(computation, value=''):
            value = None

            def thunk():
                nonlocal value
                value = value or defaulting(
                    computation=computation,
                    value='',
                )
                return value

            return thunk

        def contact_context_resolver(context, name):
            nonlocal contact
            nonlocal tags

            contact = contact or context_get(context, 'contact')

            # Thunk for extraction of a contact attribute:
            def contact_attr(attribute, attribute_prefix=''):
                return d(
                    lambda: getattr(
                        contact,
                        attribute_prefix + attribute,
                        '',
                    ),
                )

            def applicant_information(prefix='', attribute_prefix=''):

                # Partially apply contact_attr to the current attribute prefix:
                def contact_attr_(attribute):
                    return contact_attr(
                        attribute,
                        attribute_prefix=attribute_prefix,
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
                        'FIRSTNAME': contact_attr_('first_name'),
                        'LASTNAME': contact_attr_('last_name'),
                        'MIDDLENAME': contact_attr_('middle_name'),
                        'FULLNAME': d(
                            lambda: '{first_name} {last_name}'.format(
                                first_name=contact_attr_('first_name')(),
                                last_name=contact_attr_('last_name')(),
                            ),
                        ),
                        'PHONE': contact_attr_('phone_number'),
                        'PHONE2': contact_attr_('work_phone'),
                        'PHONE3': contact_attr_('mobile_number'),
                        **phone_parts('HOME', contact_attr_('phone_number')()),
                        **phone_parts('WORK', contact_attr_('work_phone')()),
                        **phone_parts('CELL', contact_attr_('mobile_number')()),
                        'EMAIL': contact_attr_('email'),
                        'ADDRESS': contact_attr_('address_1'),
                        'ADDRESS2': contact_attr_('address_2'),
                        'CITY': contact_attr_('city'),
                        'STATE': contact_attr_('state'),
                        'STATEFULL': d(
                            lambda: get_enum_name(
                                code=contact_attr_('state')(),
                                names=US_STATES,
                            ),
                        ),
                        'ZIP': contact_attr_('zip_code'),
                        'FULLADDRESS': d(
                            lambda: (
                                '{address_1}, {address_2}, {city} {state}'
                                ' {zip_code}'
                                .format(
                                    address_1=contact_attr_('address_1')(),
                                    address_2=contact_attr_('address_2')(),
                                    city=contact_attr_('city')(),
                                    state=contact_attr_('state')(),
                                    zip_code=contact_attr_('zip_code')(),
                                )
                            ),
                        ),
                        'SSN': contact_attr_('identification'),
                        **{
                            'SSN' + str(n + 1): (
                                lambda n:
                                    d(
                                        lambda: (
                                            contact_attr_('identification')()
                                            .replace('-', '')
                                            [n]
                                        ),
                                    )
                            )(n)
                            for n in range(0, 9)
                        },
                        'DOB': d(
                            lambda: format(
                                contact_attr_('birth_date')(),
                                'm/d/Y',
                            ),
                        ),
                    }.items()
                }

            tags = tags or {
                # General document system tags:
                'PAGEBREAK': d(
                    lambda: RenderRaw(
                        text='<div class="page-break"></div>',
                    ),
                ),
                # TODO: doc:DOC_ID

                # Contact identification:
                'ID': contact_attr('pk'),
                'CUSTOMERID': contact_attr('pk'),

                # Applicant and co-applicant information:
                **applicant_information(),
                **applicant_information(
                    prefix='CO',
                    attribute_prefix='co_applicant_',
                ),

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
                    ),
                ),
                'ACCOUNTNUM': d(lambda: contact.bank_account.account_number),
                'ROUTINGNUM': d(lambda: contact.bank_account.routing_number),

                # General purpose tags:
                'FILETYPE': d(lambda: 'Debt Settlement'),  # Not per-enrollment?
                'LASTNOTE': d(lambda: contact.notes.latest()),
                'ALLNOTES': d(
                    lambda: RenderRaw(
                        text=render_to_string(
                            template_name='sundog/documents/tags/allnotes.html',
                            context={
                                'notes': contact.notes.all(),
                            },
                        ),
                    ),
                ),
                # 'ALLHISTORY': lambda: contact.,  # TODO: Populates a table with the History Notes from the Client Dashboard  # noqa
                'DATE': d(lambda: format(today, 'M m, Y')),
                'MONTH': d(lambda: format(today, 'F')),
                'DAY': d(lambda: format(today, 'jS')),
                'YEAR': d(lambda: format(today, 'Y')),
                'CONTACT_STATUS': d(lambda: contact.status.name),
                'CONTACT_STAGE': d(lambda: contact.stage.name),
                # 'ENROLLED_DATE': d(lambda: contact.),  # TODO: Date the client was Enrolled  # noqa
                # 'GRADUATED_DATE': d(lambda: contact.),  # TODO: Date Client was Graduated  # noqa
                'CREATED_DATE': d(lambda: format(contact.created_at, 'M m, Y')),
                # 'CAMPAIGN': d(lambda: contact.),  # TODO: Campaign Contact is Assigned To  # noqa
                'DATASOURCE': d(lambda: contact.lead_source.name),
                # 'GATEWAY_ID': d(lambda: contact.),  # TODO: Payment Gateway ID Number from Enrollment Details  # noqa
                # 'COMPANYLOGO': d(lambda: contact.),  # TODO: Populates the logo for the company  # noqa

                # Transaction information:
                # Payment: incoming draft from a client
                # Transaction: draft or anything outgoing, like payments disbursed to creditor or fees transferred to PerfSett  # noqa
                # 'TRANSX': d(lambda: contact.),  # TODO: Transaction Amount (Replace 'X' with transaction number. Ex. {TRANS1}, {TRANS2}...)  # noqa
                # 'TRANSX_DATE': d(lambda: contact.),  # TODO: Transaction Date (Replace 'X' with transaction number. Ex. {TRANS1}, {TRANS2}...)  # noqa
                # 'LASTTRANS_TRANSID': d(lambda: contact.),  # TODO: Last Transaction ID  # noqa
                # 'LASTTRANS_ADDITIONAL': d(lambda: contact.),  # TODO: Last Transaction Additional Information  # noqa
                # 'LASTTRANS_AMOUNT': d(lambda: contact.),  # TODO: Last Transaction Amount  # noqa
                # 'LASTTRANS_DATE': d(lambda: contact.),  # TODO: Last Transaction Date  # noqa
                # 'LASTTRANS_MEMO': d(lambda: contact.),  # TODO: Last Transaction Memo  # noqa
                # 'NEXTPAYMENT_AMOUNT': d(lambda: contact.),  # TODO: Next Transaction Amount  # noqa
                # 'NEXTPAYMENT_DATE': d(lambda: contact.),  # TODO: Next Transaction Date  # noqa
                # 'NEXTPAYMENT_TYPE': d(lambda: contact.),  # TODO: Next Transaction Type (ACH or CC)  # noqa
                'NUM_PAYMENTS_MADE': d(
                    lambda: sum(
                        enrollment
                        .payments
                        .count()
                        for enrollment in contact.enrollments.all()
                    ),
                ),
                'NUM_PAYMENTS_LEFT': d(
                    lambda: sum(
                        enrollment
                        .payments
                        .filter(cleared_date__isnull=True)
                        .count()
                        for enrollment in contact.enrollments.all()
                    ),
                ),
                'SUM_PAYMENTS_CLEARED': d(
                    lambda: sum(
                        enrollment
                        .payments
                        .filter(cleared_date__isnull=True)
                        .aggregate(Sum('amount'))
                        for enrollment in contact.enrollments.all()
                    ),
                ),
                # 'SUM_FEES_CLEARED': ,  # TODO: Sum Total of ACH / Fee Credits Cleared  # noqa
                'SUM_PAYMENTS': d(
                    lambda: sum(
                        enrollment
                        .payments
                        .aggregate(Sum('amount'))
                        for enrollment in contact.enrollments.all()
                    ),
                ),

                # TODO:
                # 'PM1_DATE': ,  # Date of First Debit
                # 'ANDCOFULLNAME': ,
                # 'CF:3RD PARTY SPEAKER FULL NAME': ,
                # 'CF:3RD PARTY SPEAKER LAST 4 OF SSN': ,
                # 'DATE:m/d/Y||{DEBIT_DATE}': ,
                # 'DraftSchedule': ,
                # 'DebtPayGateway': ,
                # 'doc:1676': ,
                # {if '{CF:Hardships}' == 'Death In Family'}■{else}◻{endif}
                # CF:Hardship Description
                # CF:Creditor Name

                # 'CF:Marital Status': ,  # TODO: Marital Status (Married, Separated etc.)  # noqa
                # 'CCF:Marital Status': ,  # TODO: Marital Status (Married, Separated etc.)  # noqa
                # 'CF:Residential Status': ,  # TODO: Homeowner or Renter  # noqa
                # 'CF:Dependents (total for both applicants)': ,  # TODO: Number of Dependents  # noqa
                # 'CF:Employment Status': ,  # TODO: Employment Status (Unemployed, Retired etc.)  # noqa
                # 'CCF:Employment Status': ,  # TODO: Employment Status (Unemployed, Retired etc.)  # noqa
                # 'CF:Position': ,  # TODO: Occupation  # noqa
                # 'CCF:Position': ,  # TODO: Occupation  # noqa
                # 'CF:Employer': ,  # TODO: Name of Employer  # noqa
                # 'CCF:Employer': ,  # TODO: Name of Employer  # noqa
                # 'CF:Length of Employment': ,  # TODO: Length of Employment  # noqa
                # 'CCF:Length of Employment': ,  # TODO: Length of Employment  # noqa

                # 'NETINCOME': ,  # TODO: Take Home Pay  # noqa
                # 'OTHERINCOME': ,  # TODO: Other (rental income, alimony/support, government assistance etc.)  # noqa
                # 'TOTALINCOME': ,  # TODO: TOTAL COMBINED INCOME  # noqa

                # 'MORTGAGE': ,  # TODO: Rent or Mortgage (include 2ND mortgage or lot rent for mobile homes)  # noqa
                # 'UTILITIES': ,  # TODO: Utilities (electricity, gas, water, sewer)  # noqa
                # 'TRANSPORTATION': ,  # TODO: Transportation (including car payments, tolls, gas, repairs, bus, etc.)  # noqa
                # 'INSURANCE': ,  # TODO: Insurance premiums (auto, life, health, etc.)  # noqa
                # 'FOOD': ,  # TODO: Groceries  # noqa
                # 'TELEPHONE': ,  # TODO: Telephone (home, mobile, etc.)  # noqa
                # 'MEDICALBILLS': ,  # TODO: Medical expenses (out of pocket)  # noqa
                # 'BACKTAXES': ,  # TODO: Taxes (not deducted from your wages or included in home mortgage payments)  # noqa
                # 'STUDENTLOANS': ,  # TODO: Student Loans  # noqa
                # 'ALIMONYSUPPORT': ,  # TODO: Alimony & child support  # noqa
                # 'CHILDCARE': ,  # TODO: Childcare  # noqa
                # 'MISCOTHER': ,  # TODO: Other  # noqa
            }

            return (
                tags[name]()
                if name in tags
                else ''
            )

        return contact_context_resolver
