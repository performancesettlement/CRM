from datatableview import Datatable
from datatableview.columns import BooleanColumn, DateColumn, TextColumn
from datatableview.helpers import make_processor
from django.contrib.auth.context_processors import PermWrapper
from django.contrib.auth.models import User
from django.template.defaultfilters import date
from settings import SHORT_DATETIME_FORMAT
from sundog.constants import CONTACT_ACCESS_TAB
from sundog.routing import route
from sundog.util.permission import require_permission
from sundog.util.views import SundogDatatableView, template_column


@route(
    regex=r'^user/?$',
    name='users_list',
)
@require_permission(CONTACT_ACCESS_TAB)
class UsersList(SundogDatatableView):
    template_name = 'admin/users_list.html'

    model = User

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
            User
            .objects
            .prefetch_related('groups')
            .prefetch_related('groups__extension')
            .prefetch_related('userprofile')
            .prefetch_related('userprofile__company')
            .all()
        )

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name='admin/partials/user_actions_template.html',
            context_builder=lambda **kwargs: {
                'perms': PermWrapper(kwargs['view'].request.user),
            },
        )

        active = template_column(
            column_class=BooleanColumn,
            label='Active',
            source='is_active',
            template_name='sundog/admin/users/list/active.html',
        )

        company = TextColumn(
            label='Company',
            source='userprofile__company__name',
        )

        # FIXME: This could be a sortable CompoundColumn if the full name was
        # computed here instead of in the get_full_name method.
        full_name = TextColumn(
            label='Full Name',
            source='get_full_name',
        )

        last_login = DateColumn(
            label='Last Login',
            processor=make_processor(
                date,
                arg=SHORT_DATETIME_FORMAT,
            ),
            source='userprofile__last_login',
        )

        role = TextColumn(
            label='Role',
            source='groups__name',
            processor=lambda instance, *_,  **__: ', '.join(
                group.name
                for group in instance.groups.all()
            ),
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = '''
                active
                username
                full_name
                email
                role
                company
                last_login
                actions
            '''.split()

            ordering = '''
                name
            '''.split()
