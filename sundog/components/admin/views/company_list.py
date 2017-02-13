from datatableview import Datatable, DisplayColumn, TextColumn, BooleanColumn
from django.contrib.auth.context_processors import PermWrapper
from django.contrib.auth.decorators import permission_required
from django.template.loader import render_to_string
from sundog.constants import ADMIN_ACCESS_TAB
from sundog.models import Company
from sundog.routing import route, decorate_view
from sundog.util.permission import get_permission_codename
from sundog.util.views import SundogDatatableView


@route(r'^companies/?$', name='company_list')
@decorate_view(permission_required(get_permission_codename(ADMIN_ACCESS_TAB), 'forbidden'))
class CompanyList(SundogDatatableView):
    template_name = 'admin/company_list.html'

    model = Company

    searchable_columns = [
        'name',
    ]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_page'] = 'admin'
        return context

    def get_queryset(self):
        return Company.objects.prefetch_related('users').prefetch_related('contacts') \
            .prefetch_related('parent_company').all()

    class datatable_class(Datatable):

        active = BooleanColumn(
            label='Active',
            source='active',
            processor=lambda instance, *_, **__: '<span class="glyphicon glyphicon-asterisk' + (' green' if instance.active else ' red') + '"></span>',
        )
        type = DisplayColumn(
            label='Type',
            source='type',
            processor=lambda instance, *_, **__: instance.type_label if instance.type else '',
        )
        parent = TextColumn(
            label='Parent',
            source='parent_company__name',
            processor=lambda instance, *_, **__: instance.parent_company.name if instance.parent_company else '',
        )
        users = DisplayColumn(
            label='Users',
            processor=lambda instance, *_, **__: len(instance.users.all()),
        )
        contacts = DisplayColumn(
            label='Contacts',
            processor=lambda instance, *_, **__: len(instance.contacts.all()),
        )
        enrolled = DisplayColumn(
            label='Enrolled',
            processor=lambda instance, *_, **__: len(instance.get_enrolled()),
        )

        actions = DisplayColumn(
            label='',
            processor=(
                lambda instance, *_, **kwargs:
                render_to_string(
                    template_name='admin/partials/company_actions_template.html',
                    context={
                        'company_id': instance.company_id,
                        'perms': PermWrapper(kwargs['view'].request.user),
                    },
                )
            ),
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = [
                'active',
                'company_id',
                'name',
                'parent',
                'city',
                'email',
                'phone',
                'type',
                'users',
                'contacts',
                'enrolled',
            ]

            ordering = ['name']
