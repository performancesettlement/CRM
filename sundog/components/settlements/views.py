from datatableview import Datatable
from datatableview.columns import DisplayColumn, DateColumn, TextColumn
from datatableview.helpers import format_date, make_processor, through_filter
from django.contrib.auth.context_processors import PermWrapper
from django.template.defaultfilters import date
from django.urls import reverse
from settings import SHORT_DATETIME_FORMAT
from sundog.constants import SETTLEMENT_ACCESS_TAB
from sundog.models import SettlementOffer
from sundog.routing import route
from sundog.templatetags.my_filters import currency, percent
from sundog.util.permission import require_permission

from sundog.util.views import (
    SundogDatatableView,
    format_column,
    template_column,
)


@route(
    regex=r'^settlements/?$',
    name='settlements_list',
)
@require_permission(SETTLEMENT_ACCESS_TAB)
class SettlementsList(SundogDatatableView):
    model = SettlementOffer

    searchable_columns = '''
        contact_name
    '''.split()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'breadcrumbs': [
                ('Settlements', reverse('settlements_list')),
            ],
            'menu_page': 'settlements',
        }

    def get_queryset(self):
        return (
            SettlementOffer
            .objects
            .prefetch_related('enrollment')
            .prefetch_related('enrollment__contact')
            .prefetch_related('debt')
            .prefetch_related('negotiator')
            .all()
        )

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name='settlement/list/actions.html',
            context_builder=lambda instance, **kwargs: {
                'contact_id': instance.enrollment.contact.contact_id,
                'debt_id': instance.debt.debt_id,
                'perms': PermWrapper(kwargs['view'].request.user),
            },
        )

        amount_at_settlement = TextColumn(
            label='Amount at settlement',
            source='debt__current_debt_amount',
        )

        client_balance = TextColumn(
            label='Client balance',
            processor=make_processor(currency),
            source='enrollment__contact__client_balance',
        )

        # FIXME: Same as next column Negotiator?
        created_by = DisplayColumn(
            label='Created by',
            processor=lambda instance, *_, **__: (
                instance.negotiator.get_full_name()
            ),
        )

        contact_name = TextColumn(
            label='Contact name',
            source='enrollment__contact__full_name_straight',
        )

        creditor = DisplayColumn(
            label='Creditor',
            processor=lambda instance, *_, **__: (
                instance.debt.owed_to().name
            ),
        )

        gateway = TextColumn(
            label='Gateway',
            source='enrollment__custodial_account_label',
        )

        offer_made_by = TextColumn(
            label='Offer made by',
            source='made_by_label',
        )

        offer_status = TextColumn(
            label='Offer status',
            source='status_label',
        )

        offer_valid_until = DateColumn(
            label='Offer valid until',
            source='valid_until',
            processor=format_date(SHORT_DATETIME_FORMAT),
        )

        settlement_amount = TextColumn(
            label='Settlement amount',
            source='offer_amount',
        )

        settlement_percent = TextColumn(
            label='Settlement %',
            processor=make_processor(percent),
            source='get_offer_percentage',
        )

        third_party = TextColumn(
            label='Third party',
            source='debt__debt_buyer__name',
        )

        original_debt_amount = TextColumn(
            label='Original debt amount',
            processor=make_processor(currency),
            source='debt_amount',
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = '''
                contact_name
                creditor
                created_at
                created_by
                updated_at
                negotiator
                offer_made_by
                offer_status
                offer_valid_until
                amount_at_settlement
                settlement_amount
                gateway
                third_party
                settlement_percent
                client_balance
                original_debt_amount
                actions
            '''.split()

            ordering = '''
                -created_at
            '''.split()

            processors = {
                'created_at': through_filter(date, arg=SHORT_DATETIME_FORMAT),
                'updated_at': through_filter(date, arg=SHORT_DATETIME_FORMAT),
            }


@route(
    regex=r'^settlements/readyToSettle?$',
    name='ready_to_settle',
)
class ReadyToSettleList(SundogDatatableView):
    template_name = 'settlement/ready_to_settle.html'

    model = SettlementOffer

    searchable_columns = '''
        contact_name
    '''.split()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_page'] = 'settlements'
        return context

    def get_queryset(self):
        return (
            SettlementOffer
            .objects
            .prefetch_related('enrollment')
            .prefetch_related('enrollment__contact')
            .prefetch_related('debt')
            .prefetch_related('negotiator')
            .all()
        )

    class datatable_class(Datatable):

        # TODO: Implement these columns.
        settlement_commitment = format_column('Settlement Commitment')
        applicant_name = format_column('Applicant Name')
        current_amount = format_column('Current Amount')
        balance = format_column('Balance')
        pending_balance = format_column('Pending Balance')

        actions = template_column(
            label='Actions',
            template_name='settlement/list/actions.html',
            context_builder=lambda instance, **kwargs: {
                'contact_id': instance.enrollment.contact.contact_id,
                'debt_id': instance.debt.debt_id,
            },
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = '''
                settlement_commitment
                applicant_name
                current_amount
                balance
                pending_balance
                actions
            '''.split()
