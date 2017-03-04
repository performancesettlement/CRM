from datatableview import Datatable
from datatableview.columns import BooleanColumn, DisplayColumn, TextColumn
from django.contrib.auth.context_processors import PermWrapper
from sundog.constants import ADMIN_ACCESS_TAB
from sundog.models import Company
from sundog.routing import route
from sundog.util.permission import require_permission
from sundog.util.views import SundogDatatableView, template_column


@route(
    regex=r'^companies/?$',
    name='company_list',
)
@require_permission(ADMIN_ACCESS_TAB)
class CompanyList(SundogDatatableView):
    template_name = 'admin/company_list.html'

    model = Company

    searchable_columns = '''
        name
    '''.split()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'menu_page': 'admin',
        }

    def get_queryset(self):
        return (
            Company
            .objects
            .prefetch_related('users')
            .prefetch_related('contacts')
            .prefetch_related('parent_company')
            .all()
        )

    class datatable_class(Datatable):

        active = template_column(
            column_class=BooleanColumn,
            label='Active',
            source='active',
            template_name='sundog/admin/companies/list/active.html',
        )

        type = DisplayColumn(
            label='Type',
            source='type',
            processor=lambda instance, *_, **__: (
                instance.type_label
                if instance.type
                else ''
            ),
        )

        parent = TextColumn(
            label='Parent',
            source='parent_company__name',
            processor=lambda instance, *_, **__: (
                instance.parent_company.name
                if instance.parent_company
                else ''
            ),
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

        actions = template_column(
            label='Actions',
            template_name='admin/partials/company_actions_template.html',
            context_builder=lambda **kwargs: {
                'perms': PermWrapper(kwargs['view'].request.user),
            },
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = '''
                active
                company_id
                name
                parent
                city
                email
                phone
                type
                users
                contacts
                enrolled
            '''.split()

            ordering = '''
                name
            '''.split()
