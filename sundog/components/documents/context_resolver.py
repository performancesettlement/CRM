from datetime import date
from django.db.models import Sum
from django.template.loader import render_to_string
from django.utils.dateformat import format
from django_auth_app.enums import US_STATES
from pystache.defaults import TAG_ESCAPE
from pystache.renderengine import context_get
from pystache.renderer import Renderer
from re import match

from sundog.models import (
    ACCOUNT_TYPE_CHOICES,
    ACTIVITY_TYPE_CHOICES,
    EMPLOYMENT_STATUS_CHOICES,
    HARDSHIPS_CHOICES,
    NOTE_TYPE_CHOICES,
)

from sundog.util.functional import defaulting
from sundog.utils import get_enum_name


class Alias:
    def __init__(self, tag):
        self.tag = tag


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


# This caches computed values to improve rendering speed on repeated uses of a
# template, and yields the specified default value (the empty string by default)
# if the computation throws an exception.  It works somewhat like a thunk for
# deferred evaluation.
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


# Phone number tags follow a common pattern, so abstract them out to avoid some
# code repetition.
def phone_parts(phone_tag_prefix, number):
    return {
        phone_tag_prefix + 'PHONE_AREA': d(lambda: number[0:3]),
        phone_tag_prefix + 'PHONE_PRE': d(lambda: number[3:6]),
        phone_tag_prefix + 'PHONE_SUFF': d(lambda: number[6:]),
    }


# Some groups of tags follow a common pattern and differ only in a prefix
# applied to the tag names.  This simplifies application of the tag name prefix.
def prefix_tags(tag_prefix, tags):
    return {
        tag_prefix + key: value
        for key, value in tags.items()
    }


# This function abstracts away most of the tags specifications for applicant
# information.  This is helpful since they have to be implemented for the main
# applicant and the co-applicant alike, and they differ only in the presence of
# an attribute prefix and a tag prefix, which is handled with the prefix_tags
# function.  The main applicant carries an empty prefix on access to the
# corresponding attributes in the contact model instance, while the co-applicant
# uses the co_applicant_ prefix for all relevant contact fields.  This is dealt
# with by accessing attributes using the passed get_attr function, which would
# be applicant_attr or co_applicant_attr as defined above.  Tag names themselves
# follow a similar pattern: main applicant information tags carry no specific
# prefix, but co-applicant information tags carry the CO prefix; this tag prefix
# must be applied to the return value of this function using the prefix_tags
# helper function.
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
        'INITIAL': d(lambda: get_attr('first_name')()[0]),
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
                '{address_1}, {address_2}, {city} {state} {zip_code}'
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
            # This generates all of the individual SSN digit tag specifications.
            # Note the loop variable n is passed as a parameter to a lambda
            # instead of just used directly as Python loops do not bind a
            # separate variable for each loop iteration; as the variable is
            # shared and mutated to increment it in-place after each iteration,
            # and the computation on the variable is deferred, this is necessary
            # to prevent all of the SSN digit tags referring to the last digit.
            # See longer example in http://stackoverflow.com/a/19837590/1392731
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


# Some applicant and co-applicant information tags use different prefixes, so
# they have to be generated separately.  This function includes the tags
# prefixed with CF: for applicant custom field information and CCF: for
# co-applicant custom field information.
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

        'Employer': get_attr('employer'),
        'Position': get_attr('position'),
        'Length of Employment': get_attr('length_of_employment'),

    }


# Build the actual dictionary of static document tags.  Each implemented tag
# will have an entry here, except for those whose names include some identifier
# or variable that cannot be known statically, such as the TRANSX tags where X
# stands for a transaction identifier to be looked up in the database.
def static_tags(
    today,
    contact,
    contact_attr,
    applicant_attr,
    co_applicant_attr,

    # Ignore extra local variables passed from the context lookup function:
    *args,
    **kwargs
):
    return {

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

        'CF:SSN1': lambda: Alias('SSN'),
        'CF:SSN2': lambda: Alias('COSSN'),

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
        today = date.today()  # Used through locals()  # noqa

        # The actual context resolver used to render pystache templates:
        def contact_context_resolver(context, original_name):
            nonlocal contact
            nonlocal tags
            nonlocal today

            # Tag name matching should be case insensitive, so we immediately
            # lowercase the requested tag name.  All tag lookup operations
            # should either be case-insensitive or casefold to lowercase.  This
            # also removes extra whitespace around the tag.
            name = original_name.strip().lower()

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

            applicant_attr = contact_attr  # Used through locals()  # noqa

            # This partially applies the contact_attr function to the
            # co-applicant's attribute prefix.
            def co_applicant_attr(attribute):
                return contact_attr(
                    attribute=attribute,
                    attribute_prefix='co_applicant_',
                )

            # The dictionary of document tags is computed only once on the first
            # use of the context resolution function, and individual tags
            # defined within it cache their evaluation results.
            tags = tags or {
                # Tag name matching should be case-insensitive, so this function
                # will make all tag keys lowercase.  For this to work, tag names
                # specified in document templates should also be lowercased
                # before attempting lookup in the tag dictionary.
                key.lower(): value
                # Pass all local variables to the tag dictionary builder:
                for key, value in static_tags(**locals()).items()
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
                pattern=r'^doc:(?P<document_id>\d+)$',
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

        # Some tags are actually aliases for other tags.  This function computes
        # the tag and checks whether its value indicates the requested tag is an
        # alias, and if it is, it calls the context resolution function again
        # with the tag name specified by the alias.
        # FIXME: Aliases should get cached.
        def follow_alias(context, name, path=[]):
            if name in path:
                raise Exception(  # FIXME: write custom exception class
                    'Alias loop in document tag {name}; path is {path}'
                    .format(
                        name=name,
                        path=path,
                    )
                )

            value = contact_context_resolver(context, name)

            return (
                follow_alias(
                    context=context,
                    name=value.tag,
                    path=path + [name],
                )
                if isinstance(value, Alias)
                else value
            )

        # The actual context resolver is the alias-following function:
        return follow_alias


# Import this at the end to avoid import loop issues:
from sundog.components.documents.models import Document  # noqa


# TODO:
# {CF:CFLN Settlement 6 Creditor & Last 4 of Acct#:}
# {CF:*Eppsbal}
# {CF:*Eppsbal Last Updated}
# {CF:*First Payment Cleared}
# {CF:*Last Payment Cleared}
# {CF:*Lead Source* }
# {CF:*Trust Account Provider}
# {CF:3rd Party Speaker Full Name}
# {CF:3rd Party Speaker Last 4 of SSN}
# {CF:Adjusted Gross Income}
# {CF:Adjusted Gross Income (Spouse)}
# {CF:Alias}
# {CF:Appointment Date}
# {CF:Appointment Time}
# {CF:ATC}
# {CF:ATC Sent To All Creditors}
# {CF:Authorization Form On File}
# {CF:Best Time to Contact (PST - 2 hour block)}
# {CF:Call}
# {CF:Call Center Representative}
# {CF:Cancellation Letter Sent}
# {CF:CC Debt Amount}
# {CF:CFLN Settlement 1 Creditor &amp; Last 4 of Acct#:}
# {CF:CFLN Settlement 1 Date}
# {CF:CFLN Settlement 2 Creditor &amp; Last 4 of Acct#:}
# {CF:CFLN Settlement 2 Date}
# {CF:CFLN Settlement 3 Creditor &amp; Last 4 of Acct#:}
# {CF:CFLN Settlement 3 Date}
# {CF:CFLN Settlement 4 Creditor &amp; Last 4 of Acct#:}
# {CF:CFLN Settlement 4 Date}
# {CF:CFLN Settlement 5 Creditor &amp; Last 4 of Acct#:}
# {CF:CFLN Settlement 5 Date}
# {CF:CFLN Settlement 6 Date}
# {CF:CFLN Settlement 7 Creditor &amp; Last 4 of Acct#:}
# {CF:CFLN Settlement 7 Date}
# {CF:Change Contact Info Requested}
# {CF:Client had delinquent accounts in program when enrolled?}
# {CF:Co-Applicant}
# {CF:Consolidations}
# {CF:Consolidations Prior}
# {CF:Contact Info Updated}
# {CF:Creditor Account Num}
# {CF:Creditor Name}
# {CF:Current Status of Loans}
# {CF:De-Enrolled Date}
# {CF:Dependents (total for both applicants)}
# {CF:DL Number}
# {CF:DL State}
# #{CF:Employer}
# {CF:Employer Address}
# {CF:Employer Address2}
# {CF:Employer City}
# {CF:Employer State}
# {CF:Employer Zip}
# #{CF:Employment Status}
# {CF:Family Size}
# {CF:File Taxes}
# {CF:Filing Status}
# {CF:Fremont Group POA On File?}
# {CF:Goal Once Debt Free}
# {CF:Graduation Letter Sent}
# {CF:Hardship Description}
# {CF:Hardship Notification Letters Sent}
# {CF:Hardships}
# {CF:HNL}
# {CF:HS}
# {CF:I&amp;E}
# {CF:Income Year}
# {CF:Kill Date}
# {CF:Kill Reason}
# {CF:Last Congratulatons Letter Sent}
# {CF:Last MAR Completed}
# {CF:Last NSF Letter Sent}
# {CF:Last NSF Letter Sent Type}
# {CF:Last Paused Letter Sent}
# {CF:Last Retention Letter Sent}
# {CF:Last Settlement Authorization Needed Letter Sent}
# {CF:Last Settlement Authorization Needed Letter Sent Type}
# {CF:Last Settlement Completed}
# {CF:Last Settlement Review}
# {CF:Last UC Correspondence Sent To Client}
# {CF:Lead Debt Amount}
# #{CF:Lead Source}
# {CF:Lead Type}
# #{CF:Length of Employment}
# {CF:Loan Type}
# {CF:Maiden Name}
# {CF:MAR Due}
# {CF:MAR Time}
# {CF:MAR Type}
# {CF:Marital Status}
# {CF:Notarized ATC On File?}
# {CF:Number of Accounts Reviewed}
# {CF:Other Debt}
# {CF:Pay Frequency}
# {CF:PIN Number}
# {CF:PIN Requested}
# #{CF:Position}
# {CF:Previous Name}
# {CF:REF1 Address}
# {CF:REF1 City}
# {CF:REF1 Name}
# {CF:REF1 Phone}
# {CF:REF1 Relationship}
# {CF:REF1 State}
# {CF:REF1 Zip}
# {CF:REF2 Address}
# {CF:REF2 City}
# {CF:REF2 Name}
# {CF:REF2 Phone}
# {CF:REF2 Relationship}
# {CF:REF2 State}
# {CF:REF2 Zip}
# {CF:Referred By}
# {CF:Represen}
# #{CF:Residential Status}
# {CF:S1 Date}
# {CF:Salesman Email Address}
# {CF:Salesman Name}
# {CF:Salesman Phone Number}
# {CF:Sett 1 Date Revenue Earned This Month}
# {CF:Sett 1 Original Creditor and Last 4}
# {CF:Sett 1 Revenue Earned This Month}
# {CF:Sett 2 Date Revenue Earned This Month}
# {CF:Sett 2 Original Creditor and Last 4}
# {CF:Sett 2 Revenue Earned This Month}
# {CF:Sett 3 Date Revenue Earned This Month}
# {CF:Sett 3 Original Creditor and Last 4}
# {CF:Sett 3 Revenue Earned This Month}
# {CF:Sett 4 Date Revenue Earned This Month}
# {CF:Sett 4 Original Creditor and Last 4}
# {CF:Sett 4 Revenue Earned This Month}
# {CF:Sett 5 Date Revenue Earned This Month}
# {CF:Sett 5 Original Creditor and Last 4}
# {CF:Sett 5 Revenue Earned This Month}
# {CF:Special Note 1}
# {CF:Special Note 2}
# {CF:Special Note 3}
# {CF:Special Note 4}
# {CF:Spouse Indebtedness Amount}
# {CF:Spouse Pay Frequency}
# #{CF:SSN1}
# #{CF:SSN2}
# {CF:Student Debt}
# {CF:STUDENT LOANS CONSOLIDATED?}
# {CF:STUDENT LOANS?}
# {CF:Suffix}
# {CF:TAX ISSUES?}
# {CF:Taxable Income}
# {CF:Total Debt Amount}
# {CF:Transferred?}
# {CF:Unit(s)}
# {CF:Unknown Creditor 1}
# {CF:Unknown Creditor 2}
# {CF:Unknown Creditor 3}
# {CF:Unknown Creditor 4}
# {CF:Unknown Creditor 5}
# {CF:Using AGI Form}
# {CF:Wages Garnished}
# {CF:WC Completed}
# {CF:WC Due}
# {CF:WC Time}
# {CF:Welcome Call Date}
