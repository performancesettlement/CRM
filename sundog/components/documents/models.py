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
from re import match
from settings import MEDIA_PRIVATE
from sundog.components.documents.enums import (
    TYPE_CHOICES,
    TYPE_CHOICES_DICT,
    STATE_CHOICES,
    STATE_CHOICES_DICT,
)
from sundog.media import S3PrivateFileField
from sundog.models import (
    ACCOUNT_TYPE_CHOICES,
    ACTIVITY_TYPE_CHOICES,
    Contact,
    DEPENDANTS_CHOICES,
    EMPLOYMENT_STATUS_CHOICES,
    HARDSHIPS_CHOICES,
    MARITAL_STATUS_CHOICES,
    NOTE_TYPE_CHOICES,
    RESIDENTIAL_STATUS_CHOICES,
)
from sundog.utils import LongCharField
from sundog.utils import (
    defaulting,
    get_enum_name,
)
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


class RenderRaw:
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


def render(template, context):
    return (
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
    )


class DocumentRenderer(Renderer):

    # These three method overrides ensure that templates returning a RenderRaw
    # instance do not turn into HTML-escaped content, but are instead
    # interpreted literally in the resulting document HTML.  This allows certain
    # specific tags to generate complex HTML content.

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

    # Unfortunately, pystache provides no in-class or parameter mechanisms to
    # specify non-default delimiters for rendering.  One workaround could be to
    # prepend a Set Delimiter tag to the template string prior to the call to
    # the render function, but that approach is undesirable as changing the
    # template string may produce incorrect input positions in template syntax
    # error messages.  Sadly, overriding this method means copying some code
    # from the pystache source.
    def _render_string(self, template, *context, **kwargs):
        template = self._to_unicode_hard(template)

        def render_func(engine, stack):
            return engine.render(
                template,
                stack,
                delimiters=('{', '}'),
            )

        return self._render_final(render_func, *context, **kwargs)

    # Some template tags have to be generated from arbitrarily large data sets
    # in the database, so it's best to override the context resolution function
    # and generate those tags on demand with simulated lazy evaluation.
    def _make_resolve_context(self):
        # These variables will be used in the context resolver function as a
        # cache of the contact pulled from the database and the (rather large)
        # dictionary of tag rendering functions, which serves in turn as storage
        # for the cached rendered values of each document tag after its first
        # usage.  These should improve rendering performance for documents that
        # use a single tag multiple times.
        contact = None
        tags = None

        # To get consistent dates in the generated document, this queries the
        # system date only once and uses it throughout the document in all tags
        # involving the current time.
        today = date.today()

        # This caches computed values to improve rendering speed on repeated
        # uses of a template, and yields the specified default value (the empty
        # string by default) if the computation throws an exception.  It works
        # somewhat like a thunk for deferred evaluation.
        def d(computation, value=''):
            # Local variable for cached computation result storage:
            value = None

            # The actual function to be returned.  Note that you need to
            # evaluate the return value of d(), namely this function, in order
            # to get the results of the specified computation, as Python has no
            # practical mechanism for implicit lazy evaluation.
            def thunk():
                nonlocal value
                value = value or defaulting(
                    computation=computation,
                    value='',
                )
                return value

            return thunk

        # The actual context resolver used to render pystache templates:
        def contact_context_resolver(context, name):
            nonlocal contact
            nonlocal tags

            # Get the contact once from the database:
            contact = contact or context_get(context, 'contact')

            # Thunk for extraction of a contact attribute.  Some template tags
            # follow a very similar pattern except for using one of several
            # different prefixes on the attribute name they extract from the
            # contact, so this function provides an additional parameter for the
            # attribute prefix to help reduce code duplication in such cases.
            def contact_attr(attribute, attribute_prefix=''):
                return d(
                    lambda: getattr(
                        contact,
                        attribute_prefix + attribute,
                        '',
                    ),
                )

            applicant_attr = contact_attr

            # This partially applies the contact_attr function to the
            # co-applicant's attribute prefix.
            def co_applicant_attr(attribute):
                return contact_attr(
                    attribute=attribute,
                    attribute_prefix='co_applicant_',
                )

            # Phone number tags follow a common pattern, so abstract them out to
            # reduce some code repetition.
            def phone_parts(phone_tag_prefix, number):
                return {
                    phone_tag_prefix + 'PHONE_AREA': d(lambda: number[0:3]),
                    phone_tag_prefix + 'PHONE_PRE': d(lambda: number[3:6]),
                    phone_tag_prefix + 'PHONE_SUFF': d(lambda: number[6:]),
                }

            # Some groups of tags follow a common pattern and differ only in a
            # prefix applied to the tag names.  This simplifies application of
            # that tag name prefix.
            def prefix_tags(tag_prefix, tags):
                return {
                    tag_prefix + key: value
                    for key, value in tags.items()
                }

            # This function abstracts away most of the tags specifications for
            # applicant information.  This is helpful since they have to be
            # implemented for the main applicant and the co-applicant alike, and
            # they differ only in the presence of an attribute prefix and a tag
            # prefix, which is handled with the prefix_tags function.  The main
            # applicant carries an empty prefix on access to the corresponding
            # attributes in the contact model instance, while the co-applicant
            # uses the co_applicant_ prefix for all relevant contact fields.
            # This is handled by accessing attributes using the passed get_attr
            # function, which would be applicant_attr or co_applicant_attr as
            # defined above.  Tag names themselves follow a similar pattern:
            # main applicant information tags carry no specific prefix, but
            # co-applicant information tags carry the CO prefix; this tag prefix
            # must be applied to the return value of this function using the
            # prefix_tags helper function.
            def basic_applicant_tags(get_attr):
                return {
                    'FIRSTNAME': get_attr('first_name'),
                    'LASTNAME': get_attr('last_name'),
                    'MIDDLENAME': get_attr('middle_name'),
                    'FULLNAME': d(
                        lambda: (
                            '{first_name} {last_name}'.format(
                                first_name=get_attr('first_name')(),
                                last_name=get_attr('last_name')(),
                            )
                        ),
                    ),
                    'PHONE': get_attr('phone_number'),
                    'PHONE2': get_attr('work_phone'),
                    'PHONE3': get_attr('mobile_number'),
                    **phone_parts('HOME', get_attr('phone_number')()),
                    **phone_parts('WORK', get_attr('work_phone')()),
                    **phone_parts('CELL', get_attr('mobile_number')()),
                    'EMAIL': get_attr('email'),
                    'ADDRESS': get_attr('address_1'),
                    'ADDRESS2': get_attr('address_2'),
                    'CITY': get_attr('city'),
                    'STATE': get_attr('state'),
                    'STATEFULL': d(
                        lambda: get_enum_name(
                            code=get_attr('state')(),
                            names=US_STATES,
                        ),
                    ),
                    'ZIP': get_attr('zip_code'),
                    'FULLADDRESS': d(
                        lambda: (
                            '{address_1}, {address_2}, {city} {state}'
                            ' {zip_code}'
                            .format(
                                address_1=get_attr('address_1')(),
                                address_2=get_attr('address_2')(),
                                city=get_attr('city')(),
                                state=get_attr('state')(),
                                zip_code=get_attr('zip_code')(),
                            )
                        ),
                    ),
                    'SSN': get_attr('identification'),
                    **{
                        # This generates all of the individual SSN digit tag
                        # specifications.  Note the loop variable n is passed as
                        # a parameter to a lambda instead of just used directly
                        # as Python loops do not bind a separate variable for
                        # each loop iteration; as the variable is shared and
                        # mutated to increment it in-place after each iteration,
                        # and the computation on the variable is deferred, this
                        # is necessary to prevent all of the SSN digit tags
                        # referring to the last digit.  See a longer example in
                        # http://stackoverflow.com/a/19837590/1392731
                        'SSN' + str(n + 1): (
                            lambda n: d(
                                lambda: (
                                    get_attr('identification')()
                                    .replace('-', '')
                                    [n]
                                ),
                            )
                        )(n)
                        for n in range(0, 9)
                    },
                    'DOB': d(
                        lambda: format(
                            get_attr('birth_date')(),
                            'm/d/Y',
                        ),
                    ),
                }

            # Some main applicant and co-applicant information tags use a different
            # prefix, so they have to be generated separately.
            def extra_applicant_tags(get_attr):
                return {
                    'Marital Status': d(
                        lambda: get_enum_name(
                            code=get_attr('marital_status')(),
                            names=US_STATES,
                        ),
                    ),

                    'Employment Status': d(
                        lambda: get_enum_name(
                            code=get_attr('employment_status')(),
                            names=EMPLOYMENT_STATUS_CHOICES,
                        ),
                    ),

                    # 'CF:Employer': ,  # TODO: Name of Employer  # noqa
                    # 'CCF:Employer': ,  # TODO: Name of Employer  # noqa
                    # 'CF:Position': ,  # TODO: Occupation  # noqa
                    # 'CCF:Position': ,  # TODO: Occupation  # noqa
                    # 'CF:Length of Employment': ,  # TODO: Length of Employment  # noqa
                    # 'CCF:Length of Employment': ,  # TODO: Length of Employment  # noqa

                    # 'CF:Length of Employment': ,  # TODO: Length of Employment  # noqa
                    # 'CCF:Length of Employment': ,  # TODO: Length of Employment  # noqa

                }

            # This is the actual dictionary of static document tags.  Each
            # implemented tag will have an entry here, except for those whose
            # names include some identifier or variable that cannot be known
            # statically, such as the TRANSX tags where X stands for a
            # transaction identifier to be looked up in the database.  The
            # dictionary of document tags is computed only once on the first use
            # of the context resolution function, and individual tags defined
            # within it cache their evaluation results.
            tags = tags or {

                # General document system tags:
                'PAGEBREAK': d(
                    lambda: RenderRaw(
                        text='<div class="page-break"></div>',
                    ),
                ),

                # Contact identification:
                'ID': contact_attr('pk'),
                'CUSTOMERID': d(
                    lambda: (
                        'PER-{pk}'.format(
                            pk=contact_attr('pk')(),
                        )
                    ),
                ),

                # Applicant information:
                **basic_applicant_tags(get_attr=applicant_attr),
                **extra_applicant_tags(get_attr=applicant_attr),

                # Co-applicant information:
                **prefix_tags('CO', basic_applicant_tags(co_applicant_attr)),
                **prefix_tags('C', extra_applicant_tags(co_applicant_attr)),

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
                                'types': dict(NOTE_TYPE_CHOICES),
                            },
                        ),
                    ),
                ),
                'ALLHISTORY': d(
                    lambda: RenderRaw(
                        text=render_to_string(
                            template_name='sundog/documents/tags/allnotes.html',
                            context={
                                'notes': contact.activities.all(),
                                'types': dict(ACTIVITY_TYPE_CHOICES),
                            },
                        ),
                    ),
                ),
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
                # 'ANDCOFULLNAME': ,
                # 'DATE:m/d/Y||{DEBIT_DATE}': ,
                # 'DraftSchedule': ,
                # 'DebtPayGateway': ,
                # CF:Creditor Name

                'CF:Residential Status': d(
                    lambda: get_enum_name(
                        code=contact_attr('residential_status')(),
                        names=US_STATES,
                    ),
                ),

                'CF:Dependents (total for both applicants)': (
                    contact_attr('dependants')
                ),

                'CF:3RD PARTY SPEAKER FULL NAME': (
                    contact_attr('third_party_speaker_full_name')
                ),

                'CF:3RD PARTY SPEAKER LAST 4 OF SSN': (
                    contact_attr('third_party_speaker_last_4_of_ssn')
                ),

                'CF:Hardships': d(
                    lambda: get_enum_name(
                        code=contact_attr('hardships')(),
                        names=HARDSHIPS_CHOICES,
                    ),
                ),

                'CF:Hardship Description': contact_attr('hardship_description'),

                # TODO: {if '{CF:Hardships}' == 'Death In Family'}■{else}◻{endif}  # noqa

                'NETINCOME': d(lambda: contact.incomes.take_home_pay),
                'TOTALINCOME': d(lambda: contact.incomes.total()),

                'OTHERINCOME': d(
                    lambda: (
                        contact.incomes.total() -
                        contact.incomes.take_home_pay
                    )
                ),

                'MORTGAGE': d(lambda: contact.expenses.rent),
                'UTILITIES': d(lambda: contact.expenses.utilities),
                'TRANSPORTATION': d(lambda: contact.expenses.transportation),
                'INSURANCE': d(lambda: contact.expenses.insurance_premiums),
                'FOOD': d(lambda: contact.expenses.food),
                'TELEPHONE': d(lambda: contact.expenses.telephone),
                'MEDICALBILLS': d(lambda: contact.expenses.medical_bills),
                'BACKTAXES': d(lambda: contact.expenses.back_taxes),
                'STUDENTLOANS': d(lambda: contact.expenses.student_loans),
                'ALIMONYSUPPORT': d(lambda: contact.expenses.child_support),
                'CHILDCARE': d(lambda: contact.expenses.child_care),
                'MISCOTHER': d(lambda: contact.expenses.other_expenses),

            }

            # Return immediately if the requested tag is present in the cached
            # tag dictionary.  This will always be the case for static tags.
            # Dynamic tags will also return through this code path if they have
            # been rendered previously, as their result is cached in the tag
            # dictionary.
            if name in tags:
                return tags[name]()

            # Check whether the tag name to resolve matches the pattern for
            # document inclusion tags.  If so, render the referred document and
            # store the result in the cached tag dictionary before returning it.
            document_tag = match(
                pattern=r'^\s*doc:(?P<document_id>\d+)\s*$',
                string=name,
            )
            if document_tag:
                # Yield the empty string if the document does not exist.
                result = ''
                try:
                    result = RenderRaw(
                        text=(
                            Document
                            .objects
                            .get(
                                pk=document_tag.group('document_id'),
                            )
                            .render(
                                # The context passed to this function is an
                                # instance of the pystache.context.ContextStack
                                # class, and the Document model render method
                                # expects a simple dictionary.  This flattens
                                # the ContextStack into a simple dictionary
                                # following the resolution order used by the
                                # ContextStack itself when resolving keys, so it
                                # should not alter rendering behavior.
                                {
                                    key: value
                                    for item in reversed(context._stack)
                                    for key, value in item.items()
                                },
                            )
                        ),
                    )
                except Document.DoesNotExist:
                    pass
                tags[name] = lambda: result
                return result

            # 'TRANSX': d(lambda: contact.),  # TODO: Transaction Amount (Replace 'X' with transaction number. Ex. {TRANS1}, {TRANS2}...)  # noqa
            # 'TRANSX_DATE': d(lambda: contact.),  # TODO: Transaction Date (Replace 'X' with transaction number. Ex. {TRANS1}, {TRANS2}...)  # noqa
            # 'PM1_DATE': ,  # Date of First Debit

            return ''

        return contact_context_resolver
