from datatableview import Datatable, DisplayColumn, DateColumn
from datatableview.helpers import through_filter
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from settings import SHORT_DATETIME_FORMAT
from sundog.models import SettlementOffer
from sundog.routing import decorate_view, route
from sundog.templatetags.my_filters import currency, percent
from sundog.util.views import SundogDatatableView


@route(r'^settlements/?$', name='settlements_list')
@decorate_view(login_required)
class SettlementsList(SundogDatatableView):
    template_name = 'settlement/settlements_list.html'

    model = SettlementOffer

    searchable_columns = [
        'contact_name',
    ]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_page'] = 'settlements'
        return context

    def get_queryset(self):
        return SettlementOffer.objects.prefetch_related('enrollment') \
            .prefetch_related('enrollment__contact').prefetch_related('debt').prefetch_related('negotiator').all()

    class datatable_class(Datatable):
        contact_name = DisplayColumn(
            label='Contact Name',
            processor=lambda instance, *_, **__: instance.enrollment.contact.full_name_straight,
        )

        creditor = DisplayColumn(
            label='Creditor',
            processor=lambda instance, *_, **__: instance.debt.owed_to().name,
        )

        created_by = DisplayColumn(
            label='Created By',
            processor=lambda instance, *_, **__: instance.negotiator.get_full_name(),
        )

        negotiator = DisplayColumn(
            label='Negotiator',
            processor=lambda instance, *_, **__: instance.negotiator.get_full_name() if instance.negotiator else '',
        )

        offer_made_by = DisplayColumn(
            label='Offer Made By',
            processor=lambda instance, *_, **__: instance.made_by_label,
        )

        offer_status = DisplayColumn(
            label='Offer Status',
            processor=lambda instance, *_, **__: instance.status_label,
        )

        offer_valid_until = DateColumn(
            label='Offer Valid Until',
            source=None,
            processor=lambda instance, *_, **__: (
                date(instance.valid_until, arg=SHORT_DATETIME_FORMAT), ''
                if getattr(instance, 'settlement_offer', None) and instance.valid_until else '', '',
            )
        )

        amt_at_settlement = DisplayColumn(
            label='Amt At Settlement',
            processor=lambda instance, *_, **__: currency(instance.debt.current_debt_amount),
        )

        settlement_ant = DisplayColumn(
            label='Settlement Amt',
            processor=lambda instance, *_, **__: currency(instance.offer_amount),
        )

        gateway = DisplayColumn(
            label='Gateway',
            processor=lambda instance, *_, **__: instance.enrollment.custodial_account_label,
        )

        third_party = DisplayColumn(
            label='Third Party',
            processor=lambda instance, *_, **__: instance.debt.debt_buyer.name if instance.debt.debt_buyer else '',
        )

        settlement_percent = DisplayColumn(
            label='Settlement %',
            processor=lambda instance, *_, **__: percent(instance.get_offer_percentage()),
        )

        client_balance = DisplayColumn(
            label='Client Balance',
            processor=lambda instance, *_, **__: currency(instance.enrollment.contact.client_balance()),
        )

        original_debt_amt = DisplayColumn(
            label='Original Debt Amt',
            processor=lambda instance, *_, **__: currency(instance.debt_amount),
        )

        actions = DisplayColumn(
            label='',
            processor=(
                lambda instance, *_, **__:
                render_to_string(
                    template_name='settlement/partials/settlement_actions_template.html',
                    context={
                        'debt_id': instance.debt.debt_id,
                        'contact_id': instance.enrollment.contact.contact_id,
                    },
                )
            ),
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = [
                'contact_name',
                'creditor',
                'created_at',
                'created_by',
                'updated_at',
                'negotiator',
                'offer_made_by',
                'offer_status',
                'offer_valid_until',
                'amt_at_settlement',
                'settlement_ant',
                'gateway',
                'third_party',
                'settlement_percent',
                'client_balance',
                'original_debt_amt',
                'actions'
            ]

            ordering = [
                '-created_at',
            ]

            processors = {
                'created_at': through_filter(date, arg=SHORT_DATETIME_FORMAT),
                'updated_at': through_filter(date, arg=SHORT_DATETIME_FORMAT),
            }


@route(r'^settlements/readyToSettle?$', name='ready_to_settle')
@decorate_view(login_required)
class ReadyToSettleList(SundogDatatableView):
    template_name = 'settlement/ready_to_settle.html'

    model = SettlementOffer

    searchable_columns = [
        'contact_name',
    ]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_page'] = 'settlements'
        return context

    def get_queryset(self):
        return SettlementOffer.objects.prefetch_related('enrollment') \
            .prefetch_related('enrollment__contact').prefetch_related('debt').prefetch_related('negotiator').all()

    class datatable_class(Datatable):
        settlement_commitment = DisplayColumn(
            label='Settlement Commitment',
            processor=lambda instance, *_, **__: '',
        )
        applicant_name = DisplayColumn(
            label='Applicant Name',
            processor=lambda instance, *_, **__: '',
        )
        current_amount = DisplayColumn(
            label='Current Amount',
            processor=lambda instance, *_, **__: '',
        )
        balance = DisplayColumn(
            label='Balance',
            processor=lambda instance, *_, **__: '',
        )
        pending_balance = DisplayColumn(
            label='Pending Balance',
            processor=lambda instance, *_, **__: '',
        )

        actions = DisplayColumn(
            label='',
            processor=(
                lambda instance, *_, **__:
                render_to_string(
                    template_name='settlement/partials/settlement_actions_template.html',
                    context={
                        'debt_id': instance.debt.debt_id,
                        'contact_id': instance.enrollment.contact.contact_id,
                    },
                )
            ),
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = [
                'settlement_commitment',
                'applicant_name',
                'current_amount',
                'balance',
                'pending_balance',
                'actions',
            ]

            ordering = []

            processors = {}
