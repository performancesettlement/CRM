from allauth.compat import render_to_string
from datatableview import Datatable, DisplayColumn, TextColumn
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import date
from sundog.models import Debt, Contact
from sundog.routing import decorate_view, route
from sundog.templatetags.my_filters import currency
from sundog.util.views import SundogDatatableView


@route(r'^contact/(?P<contact_id>\d+)/creditors/$', name='contact_debts')
@decorate_view(login_required)
class ContactDebtList(SundogDatatableView):
    template_name = 'contact/contact_debts.html'

    model = Debt

    searchable_columns = []

    def get_context_data(self, *args, **kwargs):
        context = super(ContactDebtList, self).get_context_data(*args, **kwargs)
        contact = Contact.objects.get(contact_id=self.kwargs['contact_id'])
        context['menu_page'] = 'contacts'
        context['contact'] = contact
        return context

    def get_queryset(self):
        return Debt.objects.filter(contact__contact_id=self.kwargs['contact_id'])

    class datatable_class(Datatable):
        creditor = TextColumn(
            label='Collection',
            source='original_creditor__name',
        )

        collection = TextColumn(
            label='Collection',
            source='debt_buyer__name',
        )

        account = TextColumn(
            label='Account',
            source='original_creditor_account_number',
        )

        account_type = TextColumn(
            label='Type',
            source='account_type',
            processor=lambda instance, *_, **__: instance.account_type_label if instance.account_type else '',
        )

        current_debt_amount = TextColumn(
            label='Current Debt Amount',
            source='current_debt_amount',
        )

        whose_debt = TextColumn(
            label='Whose Debt',
            source='whose_debt',
            processor=lambda instance, *_, **__: instance.whose_debt_label if instance.whose_debt else '',
        )

        current_payment = TextColumn(
            label='Current Payment',
            source='current_payment',
            processor=lambda instance, *_, **__: currency(instance.current_payment),
        )

        last_payment_date = TextColumn(
            label='Last Payment',
            source='current_payment',
            processor=lambda instance, *_, **__: date(instance.current_payment, 'SHORT_DATE_FORMAT'),
        )

        notes = DisplayColumn(
            label='Notes',
            processor=lambda instance, *_, **__: instance.notes_count(),
        )

        enrolled = DisplayColumn(
            label='Enrolled',
            processor=(
                lambda instance, *_, **__:
                render_to_string(
                    template_name='contact/partials/debts/enrolled_checkbox.html',
                    context={
                        'debt': instance,
                    },
                )
            ),
        )

        actions = DisplayColumn(
            label='',
            processor=(
                lambda instance, *_, **__:
                render_to_string(
                    template_name='contact/partials/debts/debt_actions.html',
                    context={
                        'debt_id': instance.debt_id,
                        'contact_id': instance.contact.contact_id,
                    },
                )
            ),
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = [
                'creditor',
                'collection',
                'account',
                'account_type',
                'current_debt_amount',
                'whose_debt',
                'current_payment',
                'last_payment_date',
                'enrolled',
                'actions',
            ]

            ordering = []

            processors = {}
